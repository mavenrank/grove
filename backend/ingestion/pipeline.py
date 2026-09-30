"""Ingestion pipeline: discover → extract → classify → normalize → validate → organize → pack.

Design (handoff §13):
  - source material is untrusted input: size limits, temp-dir processing, no macros
  - every record keeps slide-level provenance
  - output is reviewable JSON (drafts) — nothing becomes a release without
    explicit human approval (`--approve`, see cli.py)
  - extraction is delegated to the format-adapter registry (extractors.py);
    classification is deterministic; LLM assistance would slot in as an
    optional enrichment step between normalize and validate (not in this build)

This module holds stage logic only — argument parsing and the command entry
point live in cli.py.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import ACTIVE_BUCKETS, classify_title
from .extractors import ExtractionContext, get_extractor
from .organize import organize_all

MAX_FILE_BYTES = 200 * 1024 * 1024  # 200 MB per source file

WS = re.compile(r"\s+")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def slugify(text: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return re.sub(r"-{2,}", "-", text)[:80]


class Pipeline:
    def __init__(self, source_dir: Path, work_dir: Path, verbose: bool = False) -> None:
        self.source_dir = source_dir
        self.work_dir = work_dir
        self.verbose = verbose
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.media_dir = self.work_dir / "media"
        self.media_dir.mkdir(exist_ok=True)
        self.ctx = ExtractionContext(media_dir=self.media_dir, source_dir=self.source_dir)

    # ------------------------------------------------------------------
    # Stage 1: discover
    # ------------------------------------------------------------------
    def discover(self) -> list[Path]:
        files: list[Path] = []
        for pattern in ("**/*.pptx", "**/*.pdf", "**/*.docx"):
            files.extend(self.source_dir.glob(pattern))
        # skip macOS AppleDouble debris ('._foo.pptx') and hidden files
        files = [f for f in sorted(set(files))
                 if not f.name.startswith((".", "._"))
                 and f.stat().st_size <= MAX_FILE_BYTES
                 and get_extractor(f.suffix) is not None]
        return files

    # ------------------------------------------------------------------
    # Stage 2: extract (via the format-adapter registry)
    # ------------------------------------------------------------------
    def extract(self, path: Path) -> tuple[list[dict[str, Any]], dict[int, list[str]]]:
        adapter = get_extractor(path.suffix)
        if adapter is None:  # discover() filters these; belt-and-braces
            raise ValueError(f"no extractor for {path.suffix}")
        return adapter(path, self.ctx)

    # ------------------------------------------------------------------
    # Stage 3: classify + normalize
    # ------------------------------------------------------------------
    def normalize(self, files: list[Path]) -> dict[str, Any]:
        decks: list[dict[str, Any]] = []
        skipped: list[dict[str, str]] = []
        media_index: dict[str, dict[int, list[str]]] = {}
        for path in files:
            rel = path.relative_to(self.source_dir) if self.source_dir in path.parents else path
            size = path.stat().st_size
            try:
                slides, media_map = self.extract(path)
            except Exception as exc:  # untrusted input: never crash the run
                skipped.append({"file": str(rel), "reason": f"extract failed: {exc}"})
                continue
            deck_id = slugify(rel.stem)
            if media_map:
                media_index[deck_id] = media_map

            title = path.stem
            # strip leading numeric ordering ("12-Name-2023") for classification
            m = re.match(r"^\d+\s*[-_. ]+(.*)$", title)
            classify_against = m.group(1) if m else title
            m2 = re.match(r"^(\d+)[-_. ]*(.*)$", classify_against)
            if m2 and m2.group(2):
                classify_against = m2.group(2)
            # underscores are not word separators for classification purposes
            classify_against = classify_against.replace("_", " ")
            skill_id, status = classify_title(classify_against)

            decks.append({
                "deck_id": deck_id,
                "source_file": path.name,
                "source_path": str(rel).replace("\\", "/"),
                "source_hash": sha256_file(path),
                "bytes": size,
                "kind": path.suffix.lower().lstrip("."),
                "title": title,
                "classify_key": classify_against,
                "skill_id": skill_id,
                "status": status,
                "slide_count": len(slides),
                "slides": slides,
            })
        return {
            "run_at": now_iso(),
            "source_dir": str(self.source_dir),
            "file_count": len(files),
            "decks": decks,
            "skipped": skipped,
            "media_index": media_index,
        }

    # ------------------------------------------------------------------
    # Stage 4: validate
    # ------------------------------------------------------------------
    def validate(self, catalog: dict[str, Any]) -> dict[str, Any]:
        """Dedupe identical captures (the corpus keeps several takes of one deck),
        then report real problems. Duplicates are annotated, not failures."""
        problems: list[str] = []
        warnings: list[str] = []
        seen_hashes: dict[str, str] = {}
        dup_count = 0

        for deck in catalog["decks"]:
            did = deck["deck_id"]
            h = deck["source_hash"]
            if h in seen_hashes:
                deck["duplicate_of"] = seen_hashes[h]
                dup_count += 1
                continue
            seen_hashes[h] = did
            if not deck["slides"]:
                warnings.append(f"{did}: no extractable slide text")
            if deck["status"] == "active" and deck["skill_id"].split(".")[0] not in ACTIVE_BUCKETS:
                problems.append(f"{did}: active status but non-active bucket skill {deck['skill_id']}")

        unique = [d for d in catalog["decks"] if "duplicate_of" not in d]
        return {
            "validated_at": now_iso(),
            "ok": not problems,
            "problems": problems,
            "warnings": warnings,
            "counts": {
                "decks": len(catalog["decks"]),
                "unique": len(unique),
                "duplicates": dup_count,
                "active": sum(1 for d in unique if d["status"] == "active"),
                "deferred": sum(1 for d in unique if d["status"] == "deferred"),
                "empty": sum(1 for d in unique if not d["slides"]),
            },
        }

    # ------------------------------------------------------------------
    # Stage 5: organize — learning segments, verified questions, flashcards
    # ------------------------------------------------------------------
    def _template_media(self, catalog: dict[str, Any]) -> set[str]:
        """Image ids that appear in 3+ distinct source files are provider
        template assets (logos, backgrounds, contact icons) — not teaching
        content. Teaching images are unique to the decks that teach them."""
        freq: dict[str, set[str]] = {}
        media_index = catalog.get("media_index", {})
        for deck in catalog["decks"]:
            if "duplicate_of" in deck:
                continue
            for mids in media_index.get(deck["deck_id"], {}).values():
                for mid in mids:
                    freq.setdefault(mid, set()).add(deck["source_hash"])
        return {mid for mid, sources in freq.items() if len(sources) >= 3}

    def organize(self, catalog: dict[str, Any]) -> dict[str, Any]:
        """Turn explanation slides into learning material, question slides +
        speaker notes into verified question records, and formula lines into
        flashcard drafts — grouped per skill."""
        organized = organize_all(catalog, catalog.get("media_index", {}),
                                 template_media=self._template_media(catalog))
        organized["organized_at"] = now_iso()
        return organized

    # ------------------------------------------------------------------
    # Stage 6: pack (explicit approval required)
    # ------------------------------------------------------------------
    def pack(self, catalog: dict[str, Any], report: dict[str, Any],
             organized: dict[str, Any], version: str, approved: bool) -> dict[str, Any]:
        concepts = organized["concepts"] if approved else []
        flashcards = organized["flashcards"] if approved else []
        question_pool = organized["question_pool"] if approved else []
        media_ids = sorted({m["image_id"] for c in concepts for m in c.get("media", [])})
        return {
            "release_id": "grove-ingested",
            "version": version,
            "generated_at": now_iso(),
            "approved": approved,
            "source": f"ingested from {self.source_dir.name}",
            # absolute root so the app can offer 'open source deck' locally
            "source_root": str(self.source_dir.resolve()),
            "concepts": concepts,
            "flashcards": flashcards,
            "question_pool": question_pool,  # for review + future question import
            "families": [],     # backend built-in generator allowlist is authoritative here
            "media_ids": media_ids,
            "source_refs": [
                {
                    "deck_id": d["deck_id"],
                    "source_file": d["source_file"],
                    "source_path": d["source_path"],
                    "source_hash": d["source_hash"],
                    "slide_count": d["slide_count"],
                    "skill_id": d["skill_id"],
                    "status": d["status"],
                }
                for d in catalog["decks"]
                if "duplicate_of" not in d
            ],
            "stats": {**report["counts"], **organized["stats"]},
        }

    # ------------------------------------------------------------------
    # Runs
    # ------------------------------------------------------------------
    def run_all(self) -> int:
        files = self.discover()
        if self.verbose:
            print(f"discovered {len(files)} files under {self.source_dir}")
        catalog = self.normalize(files)
        report = self.validate(catalog)
        organized = self.organize(catalog)

        catalog_path = self.work_dir / "catalog.json"
        catalog_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")
        report_path = self.work_dir / "validation-report.json"
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        drafts_path = self.work_dir / "content-drafts.json"
        drafts_path.write_text(json.dumps(organized, indent=2, ensure_ascii=False), encoding="utf-8")

        stats = organized["stats"]
        print(f"catalog    -> {catalog_path}  ({report['counts']['decks']} decks, "
              f"{report['counts']['unique']} unique)")
        print(f"  active   -> {report['counts']['active']}  deferred -> {report['counts']['deferred']}")
        print(f"report     -> {report_path}  (ok={report['ok']})")
        print(f"organized  -> {drafts_path}")
        print(f"  skills   -> {stats['skills']}  concepts -> {stats['concepts']}")
        print(f"  learning -> {stats.get('learning_segments', 0)} segments  "
              f"flashcards -> {stats['flashcards']}")
        print(f"  questions-> {stats['questions_total']} total, "
              f"{stats['questions_verified']} verified from speaker notes")
        if report["problems"]:
            for p in report["problems"][:10]:
                print(f"  PROBLEM: {p}", file=sys.stderr)
        return 0 if report["ok"] else 1

    def run_pack(self, version: str, approve: bool) -> int:
        catalog_path = self.work_dir / "catalog.json"
        if not catalog_path.exists():
            print("no catalog.json in work dir; run `grove-ingest run` first", file=sys.stderr)
            return 2
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        report = self.validate(catalog)
        organized = self.organize(catalog)
        pack = self.pack(catalog, report, organized, version, approve)
        stats = pack["stats"]
        print(f"  concepts -> {len(pack['concepts'])}  flashcards -> {len(pack['flashcards'])}  "
              f"questions -> {len(pack['question_pool'])}")
        print(f"  media    -> {len(pack['media_ids'])} slide images")

        packs_dir = self.work_dir / "packs"
        packs_dir.mkdir(exist_ok=True)
        pack_path = packs_dir / f"grove-ingested-{version}.json"
        pack_path.write_text(json.dumps(pack, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"pack -> {pack_path}")
        print(f"  approved: {approve}")
        print(f"  concepts included: {len(pack['concepts'])}")
        print(f"  source refs preserved: {len(pack['source_refs'])}")
        if not approve:
            print("  (draft pack: pass --approve after human review to include concepts)")
        return 0
