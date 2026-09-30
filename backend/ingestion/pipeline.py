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
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import ACTIVE_BUCKETS, classify_title
from .extractors import ExtractionContext, get_extractor
from .organize import organize_all

MAX_FILE_BYTES = 200 * 1024 * 1024  # 200 MB per source file
EXTRACTION_VERSION = 3  # speaker-note assets and AlternateContent branch evidence

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
        self.discovery_skips: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Stage 1: discover
    # ------------------------------------------------------------------
    def discover(self) -> list[Path]:
        files: list[Path] = []
        self.discovery_skips = []
        for path in sorted(self.source_dir.rglob("*")):
            if path.suffix.lower() not in {".pptx", ".pdf", ".docx"} or not path.is_file():
                continue
            rel = path.relative_to(self.source_dir)
            reason = None
            severity = "review"
            if any(part.startswith(".") for part in rel.parts):
                reason, severity = "hidden_source", "info"
            elif get_extractor(path.suffix) is None:
                reason = "adapter_missing"
            else:
                try:
                    if path.stat().st_size > MAX_FILE_BYTES:
                        reason = "source_byte_limit"
                except OSError:
                    reason = "source_unreadable"
            if reason:
                self.discovery_skips.append({"file": rel.as_posix(), "reason": reason, "severity": severity})
            else:
                files.append(path)
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
        skipped: list[dict[str, Any]] = list(self.discovery_skips)
        media_index: dict[str, dict[int, list[str]]] = {}
        for path in files:
            try:
                rel = path.resolve().relative_to(self.source_dir.resolve())
                size = path.stat().st_size
                if size > MAX_FILE_BYTES:
                    raise ValueError("source_byte_limit")
                source_hash = sha256_file(path)
                slides, media_map = self.extract(path)
                if sha256_file(path) != source_hash:
                    raise ValueError("source_changed_during_extraction")
            except Exception as exc:  # untrusted input: never crash the run
                skipped.append({"file": str(path.relative_to(self.source_dir)) if self.source_dir in path.parents else path.name,
                                "reason": f"extract failed: {exc}", "severity": "review"})
                continue
            identity = unicodedata.normalize("NFC", rel.as_posix()).casefold()
            # Path identity survives content edits; snapshot hash distinguishes
            # revisions. Identical stems in separate folders cannot overwrite.
            deck_id = f"{slugify(rel.stem)[:60] or 'source'}-{hashlib.sha256(identity.encode()).hexdigest()[:16]}"
            for slide in slides:
                slide_id = f"{deck_id}@{source_hash[:16]}:slide-{slide['slide_number']}"
                slide["slide_id"] = slide_id
                for block in slide.get("blocks", []):
                    block["block_id"] = f"{slide_id}:shape-{block['shape_id']}"
                for block in slide.get("notes_blocks", []):
                    block["block_id"] = f"{slide_id}:notes:shape-{block['shape_id']}"
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
                "source_hash": source_hash,
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
            "extraction_version": EXTRACTION_VERSION,
            "limits": {"source_bytes": MAX_FILE_BYTES, "image_bytes": 8 * 1024 * 1024,
                       "image_pixels": 25_000_000, "preview_dimension": 1400, "preview_bytes": 500 * 1024},
            "run_at": now_iso(),
            "source_dir": str(self.source_dir),
            "file_count": len(files) + len(self.discovery_skips),
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
        seen_ids: set[str] = set()
        checked_media: dict[str, bool] = {}
        review_items: list[dict[str, Any]] = []
        dup_count = 0

        for deck in catalog["decks"]:
            deck.pop("duplicate_of", None)  # repeat validation must be deterministic
        for skipped in catalog.get("skipped", []):
            if skipped.get("severity", "review") == "review":
                review_items.append({"code": "source_skipped", **skipped})
        if catalog.get("extraction_version") != EXTRACTION_VERSION and any(d["status"] == "active" for d in catalog["decks"]):
            review_items.append({"code": "catalog_reextract_required", "severity": "review",
                                 "message": "Legacy catalog lacks source-shape/loss evidence; re-extract before approval"})

        for deck in catalog["decks"]:
            did = deck["deck_id"]
            if did in seen_ids:
                problems.append(f"{did}: duplicate deck identity")
            seen_ids.add(did)
            h = deck["source_hash"]
            if h in seen_hashes:
                deck["duplicate_of"] = seen_hashes[h]
                dup_count += 1
                continue
            seen_hashes[h] = did
            if not deck["slides"]:
                warnings.append(f"{did}: no extractable slide text")
                if deck["status"] == "active":
                    review_items.append({"code": "empty_deck", "severity": "review", "deck_id": did,
                                         "message": "Active source has no extracted slides"})
            if deck["status"] == "active" and deck["skill_id"].split(".")[0] not in ACTIVE_BUCKETS:
                problems.append(f"{did}: active status but non-active bucket skill {deck['skill_id']}")
            if deck["status"] == "active":
                for slide in deck["slides"]:
                    if catalog.get("extraction_version") == EXTRACTION_VERSION:
                        slide_no = slide["slide_number"]
                        index = catalog.get("media_index", {}).get(did, {})
                        indexed = index.get(slide_no, index.get(str(slide_no), []))
                        if set(indexed) != set(slide.get("media_ids", [])):
                            problems.append(f"{did} slide {slide_no}: media index disagrees with slide evidence")
                    for item in slide.get("issues", []):
                        if item["severity"] == "review":
                            review_items.append({**item, "deck_id": did, "slide_id": slide.get("slide_id"),
                                                 "slide_number": slide.get("slide_number")})
                    for mid in slide.get("media_ids", []):
                        if mid not in checked_media:
                            media_path = self.media_dir / f"{mid}.jpg"
                            try:
                                checked_media[mid] = bool(re.fullmatch(r"[0-9a-f]{16}", mid) and media_path.is_file()
                                                          and sha256_file(media_path)[:16] == mid)
                            except OSError:
                                checked_media[mid] = False
                        if not checked_media[mid]:
                            problems.append(f"{did} slide {slide.get('slide_number')}: missing/invalid media {mid}")

        unique = [d for d in catalog["decks"] if "duplicate_of" not in d]
        if catalog.get("extraction_version") == EXTRACTION_VERSION:
            seen_reviews = {(i["code"], i.get("deck_id"), i.get("slide_number"), i.get("shape_id"), i.get("surface", "slide"))
                            for i in review_items}
            for item in self.organize(catalog)["review_issues"]:
                source = item.get("source", {})
                key = (item["code"], source.get("deck_id"), source.get("slide_number"), item.get("shape_id"), item.get("surface", "slide"))
                if item["severity"] == "review" and (key not in seen_reviews or item.get("skill_id")):
                    review_items.append(item)
                    seen_reviews.add(key)
        return {
            "validated_at": now_iso(),
            "ok": not problems,
            "problems": problems,
            "warnings": warnings,
            "review_items": review_items,
            "ready_for_approval": not problems and not review_items,
            "counts": {
                "decks": len(catalog["decks"]),
                "unique": len(unique),
                "duplicates": dup_count,
                "active": sum(1 for d in unique if d["status"] == "active"),
                "deferred": sum(1 for d in unique if d["status"] == "deferred"),
                "empty": sum(1 for d in unique if not d["slides"]),
                "sources_skipped": len(catalog.get("skipped", [])),
                "slides": sum(len(d["slides"]) for d in unique),
                "unresolved_review_items": len(review_items),
            },
        }

    # ------------------------------------------------------------------
    # Stage 5: organize — learning segments, verified questions, flashcards
    # ------------------------------------------------------------------
    def _repeated_media(self, catalog: dict[str, Any]) -> list[dict[str, Any]]:
        """Frequency is a review clue, never proof that an image is decoration."""
        freq: dict[str, set[str]] = {}
        media_index = catalog.get("media_index", {})
        for deck in catalog["decks"]:
            if "duplicate_of" in deck:
                continue
            for mids in media_index.get(deck["deck_id"], {}).values():
                for mid in mids:
                    freq.setdefault(mid, set()).add(deck["source_hash"])
        return [{"image_id": mid, "distinct_sources": len(sources), "action": "retained_for_review"}
                for mid, sources in sorted(freq.items()) if len(sources) >= 3]

    def organize(self, catalog: dict[str, Any]) -> dict[str, Any]:
        """Turn explanation slides into learning material, question slides +
        speaker notes into verified question records, and formula lines into
        flashcard drafts — grouped per skill."""
        organized = organize_all(catalog, catalog.get("media_index", {}))
        organized["repeated_media"] = self._repeated_media(catalog)
        for deck in catalog["decks"]:
            if deck["status"] == "active" and "duplicate_of" not in deck:
                continue
            for slide in deck["slides"]:
                organized["decisions"].append({
                    "source": {"deck_id": deck["deck_id"], "slide_id": slide.get("slide_id"),
                               "slide_number": slide.get("slide_number"), "source_hash": deck["source_hash"],
                               "source_path": deck.get("source_path")},
                    "outcome": "excluded", "reason": "duplicate_source" if "duplicate_of" in deck else "deferred_topic",
                    "duplicate_of": deck.get("duplicate_of"),
                })
        organized["organized_at"] = now_iso()
        return organized

    # ------------------------------------------------------------------
    # Stage 6: pack (explicit approval required)
    # ------------------------------------------------------------------
    def pack(self, catalog: dict[str, Any], report: dict[str, Any],
             organized: dict[str, Any], version: str, approved: bool) -> dict[str, Any]:
        # Approval cannot override failed validation or trust a stale report (#7).
        if approved:
            current_report = self.validate(catalog)
            if report.get("ok") is not True or current_report["ok"] is not True:
                problems = report.get("problems", []) + current_report["problems"]
                raise ValueError("cannot approve a pack with validation failures: "
                                 + "; ".join(dict.fromkeys(problems)))
            # Regenerate the actual draft at this boundary. Stripping a saved
            # review report or passing stale organized content cannot bypass it.
            organized = self.organize(catalog)
            unresolved = current_report["review_items"] + [i for i in organized["review_issues"] if i["severity"] == "review"]
            if unresolved:
                codes = sorted({i["code"] for i in unresolved})
                raise ValueError("cannot approve a pack with unresolved review items: " + ", ".join(codes))
            if not organized["concepts"]:
                raise ValueError("cannot approve a pack without active learning content")
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
        review_path = self.work_dir / "review-report.json"
        review_path.write_text(json.dumps({
            "extraction_version": catalog["extraction_version"], "limits": catalog["limits"],
            "skipped_sources": catalog["skipped"], "slide_decisions": organized["decisions"],
            "ready_for_approval": report["ready_for_approval"],
            "validation_review": report["review_items"], "organization_review": organized["review_issues"],
            "repeated_media": organized["repeated_media"],
            "truncations": [{"concept_id": c["id"], **item} for c in organized["concepts"] for item in c["truncations"]],
        }, indent=2, ensure_ascii=False), encoding="utf-8")

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
              f"{stats['questions_notes_confirmed']} notes-confirmed (not independently solved)")
        print(f"review     -> {review_path}  (ready_for_approval={report['ready_for_approval'] and not stats['unresolved_review_items']})")
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
        try:
            pack = self.pack(catalog, report, organized, version, approve)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
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
