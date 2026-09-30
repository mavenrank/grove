"""Read-only source -> draft -> public-contract audit (#36).

Never approves/imports. Successful extraction is not semantic review. The scope
is all stored Learn topics and their citations, rather than the entire corpus.
"""
from __future__ import annotations

import hashlib
import json
import posixpath
import re
import sqlite3
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from .pipeline import Pipeline, now_iso, sha256_file

NS = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main",
      "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}


def read_release(database: Path) -> tuple[dict, dict]:
    """Same latest-row selection as the app, without opening its writable DB."""
    with sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM content_releases ORDER BY created_at DESC, version DESC LIMIT 1").fetchone()
    if row is None:
        raise ValueError("No stored release; provide a release JSON snapshot instead")
    return json.loads(row["payload"]), {"release_id": row["release_id"], "version": row["version"],
                                       "imported_at": row["created_at"]}


def pptx_probe(path: Path) -> list[dict]:
    """Independent package-level slide order/count/native-run oracle.

    Checks native text only. Cannot prove image, drawing or equation meaning.
    Uses presentation relationships so orphan slide files aren't counted.
    """
    with zipfile.ZipFile(path) as package:
        presentation = ET.fromstring(package.read("ppt/presentation.xml"))
        rels = ET.fromstring(package.read("ppt/_rels/presentation.xml.rels"))
        targets = {r.attrib["Id"]: r.attrib["Target"] for r in rels}
        slides = []
        for position, element in enumerate(presentation.findall("p:sldIdLst/p:sldId", NS), 1):
            target = targets[element.attrib[f"{{{NS['r']}}}id"]]
            part = target.lstrip("/") if target.startswith("/") else posixpath.normpath("ppt/" + target)
            root = ET.fromstring(package.read(part))
            slides.append({"slide_number": position,
                           "native_runs": [e.text for e in root.findall(".//a:t", NS) if e.text and e.text.strip()],
                           "picture_shapes": len(root.findall(".//p:pic", NS))})
        return slides


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def source_key(value: str) -> str:
    return value.replace("\\", "/").casefold()


def metrics(concept: dict | None) -> dict:
    concept = concept or {}
    return {field: len(concept.get(field, [])) for field in
            ("formulas", "examples", "media", "learning_segments", "code_blocks")}


def analyze(payload: dict, catalog: dict, drafts: dict, validation: dict,
            probes: dict[str, list[dict]], media_dir: Path | None = None) -> dict:
    """Pure comparison; findings include a stage and explicit confidence."""
    from app.schemas import ConceptOut

    findings: dict[str, dict] = {}
    topics = []
    by_path = {source_key(d["source_path"]): d for d in catalog["decks"]}
    by_skill = {c["skill_id"]: c for c in drafts["concepts"]}

    def add(topic: dict, code: str, stage: str, message: str, *, source: dict | None = None,
            evidence: Any = None, confidence: str = "observed", severity: str = "review"):
        record = {"topic_id": topic["id"], "code": code, "stage": stage, "severity": severity,
                  "confidence": confidence, "message": message, "source": source, "evidence": evidence}
        fid = hashlib.sha256(json.dumps(record, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:20]
        findings[fid] = {"id": fid, **record}

    for stored in payload.get("concepts", []):
        draft = by_skill.get(stored["skill_id"])
        refs = stored.get("source_decks", [])
        topic_decks = [by_path[source_key(r.get("source_path", ""))] for r in refs
                       if source_key(r.get("source_path", "")) in by_path]
        hashes = {d["source_hash"] for d in topic_decks}
        topic_questions = [q for q in drafts["question_pool"] if q["source"].get("source_hash") in hashes]
        topics.append({"id": stored["id"], "title": stored["title"], "skill_id": stored["skill_id"],
                       "sources_expected": len(refs), "sources_extracted": len(topic_decks),
                       "source_slides": sum(d["slide_count"] for d in topic_decks),
                       "stored": metrics(stored), "draft": metrics(draft),
                       "question_candidates": len(topic_questions),
                       "notes_confirmed": sum(bool(q["answer"]) for q in topic_questions),
                       "independently_verified_by_bench": 0,
                       "content_modes": dict(Counter(s.get("content_mode", "unknown") for d in topic_decks for s in d["slides"]))})
        if not refs:
            add(stored, "source_refs_absent", "stored", "No source deck refs; source comparison is unavailable")
        if not payload.get("extraction_version"):
            add(stored, "legacy_release_evidence", "stored", "Stored release lacks extraction revision metadata")
        if not stored.get("summary") or "Teaching material assembled from" in stored["summary"]:
            add(stored, "placeholder_summary", "stored", "Displayed summary supplies no substantive teaching content")
        if not stored.get("examples"):
            add(stored, "no_stored_examples", "stored", "No worked examples; inspect source/draft to establish why")
        formula_questions = [f for f in stored.get("formulas", []) if "?" in f]
        if formula_questions:
            add(stored, "formula_question_fronts", "stored", "Formula list contains recall prompts, not complete relations",
                evidence=formula_questions)
        if refs and not draft:
            add(stored, "no_draft_topic", "organize", "No draft under the stored skill; inspect classification/omissions")
        elif draft:
            if draft.get("summary_status") == "draft_placeholder":
                add(stored, "draft_placeholder_summary", "organize", "Fresh extraction still has no explanatory summary")
            for field in ("examples", "media", "learning_segments"):
                if len(draft.get(field, [])) > len(stored.get(field, [])):
                    add(stored, "draft_recovers_" + field, "stored", "Fresh draft has more candidates than the stored topic",
                        evidence={"stored": len(stored.get(field, [])), "draft": len(draft.get(field, []))})
            for truncation in draft.get("truncations", []):
                add(stored, "presentation_truncation", "organize", "Candidates exceed display limits", evidence=truncation)
            public = ConceptOut(**draft).model_dump()
            if draft.get("learning_segments") and "learning_segments" not in public:
                add(stored, "public_field_dropped", "public_contract", "Public schema omits retained learning segments",
                    evidence={"field": "learning_segments", "count": len(draft["learning_segments"])})
            for index, example in enumerate(draft.get("examples", [])):
                for field in ("blocks", "media_ids", "answer_status"):
                    if example.get(field) and field not in public["examples"][index]:
                        add(stored, "public_example_field_dropped", "public_contract", "Public schema omits example context/status",
                            source=example.get("source"), evidence={"field": field, "example_index": index})

        for ref in refs:
            key = source_key(ref.get("source_path", ""))
            deck = by_path.get(key)
            if not deck:
                add(stored, "source_unavailable", "source", "Source could not be extracted; see skipped sources", source=ref)
                continue
            source = {k: deck[k] for k in ("deck_id", "source_path", "source_hash")}
            if ref.get("source_hash") != deck["source_hash"]:
                add(stored, "source_revision_changed", "source", "Current source differs from stored snapshot", source=source,
                    evidence={"stored_hash": ref.get("source_hash")})
            if ref.get("slide_count") != deck["slide_count"]:
                add(stored, "stored_slide_count_changed", "source", "Stored and fresh slide counts differ", source=source,
                    evidence={"stored": ref.get("slide_count"), "fresh": deck["slide_count"]})
            if deck["skill_id"] != stored["skill_id"] or deck["status"] != "active":
                add(stored, "classification_changed", "organize", "Current mapping disagrees with stored topic", source=source,
                    evidence={"fresh_skill": deck["skill_id"], "status": deck["status"]})
            probe = probes.get(key)
            if probe is not None:
                if len(probe) != deck["slide_count"]:
                    add(stored, "source_slide_loss", "extract", "Package slide count disagrees with extraction",
                        source=source, severity="blocker")
                slides = {s["slide_number"]: s for s in deck["slides"]}
                for original in probe:
                    slide = slides.get(original["slide_number"], {})
                    joined = compact(" ".join(slide.get("texts", [])))
                    missing = [t for t in original["native_runs"] if compact(t) not in joined]
                    if missing:
                        add(stored, "native_text_loss", "extract", "Native runs absent from retained text; review run/layout boundaries",
                            source={**source, "slide_number": original["slide_number"]},
                            evidence=missing, confidence="heuristic")
            for slide in deck["slides"]:
                src = {**source, "slide_number": slide["slide_number"], "slide_id": slide.get("slide_id")}
                for item in slide.get("issues", []):
                    if item.get("severity") == "review":
                        add(stored, item["code"], "extract", item["message"], source=src, evidence=item)
        for question in topic_questions:
            for item in question.get("issues", []):
                if item.get("code") in {"visual_semantics_unresolved", "vector_semantics_unresolved"}:
                    continue
                add(stored, item["code"], "organize", item["message"], source=question["source"],
                    evidence={"prompt": question["prompt"], "options": question["options"],
                              "notes_raw": question.get("notes_raw", "")})
        for item in drafts.get("review_issues", []):
            src = item.get("source", {})
            if src.get("source_hash") in hashes and item["code"] == "question_parse_failed":
                add(stored, item["code"], "organize", item["message"], source=src, evidence=item)
        for decision in drafts.get("decisions", []):
            src = decision["source"]
            if src.get("source_hash") in hashes and decision["outcome"] in {"excluded", "needs_review"}:
                add(stored, "slide_" + decision["outcome"], "organize", "Slide not assembled; inspect recorded reason",
                    source=src, evidence=decision, confidence="heuristic", severity="clue")
        if media_dir is not None:
            for media in stored.get("media", []):
                mid = media["image_id"]
                if not re.fullmatch(r"[0-9a-f]{16}", mid) or not (media_dir / f"{mid}.jpg").is_file():
                    add(stored, "published_media_missing", "delivery", "Stored lesson references missing media",
                        source=media.get("source"), evidence={"image_id": mid})
        text_fields = [("summary", stored.get("summary", ""), None)]
        text_fields += [("example.explanation", e.get("explanation", ""), e.get("source")) for e in stored.get("examples", [])]
        for field, value, src in text_fields:
            if value.count("(") != value.count(")") or value.count("[") != value.count("]"):
                add(stored, "delimiter_imbalance", "formatting", "Unequal delimiters; inspect math/source before editing (#37)",
                    source=src, evidence={"field": field, "text": value}, confidence="heuristic", severity="clue")
            if len(value) > 500 and "\n" not in value:
                add(stored, "long_text_blob", "formatting", "Long paragraph needs later reading-quality review (#37)",
                    source=src, evidence={"field": field, "text": value}, confidence="heuristic", severity="clue")

    items = sorted(findings.values(), key=lambda f: (f["topic_id"], f["stage"], f["code"], f["id"]))
    evidence_slides = [{"source": {k: d[k] for k in ("deck_id", "source_path", "source_hash")},
                       "slide_number": s["slide_number"], "slide_id": s.get("slide_id"),
                       "kind": s["kind"], "mode": s.get("content_mode"), "texts": s["texts"],
                       "notes": s.get("notes", ""), "media_ids": s.get("media_ids", []),
                       "issues": s.get("issues", [])} for d in catalog["decks"] for s in d["slides"]]
    return {"bench_version": 1, "generated_at": now_iso(),
            "release": {"release_id": payload.get("release_id"), "version": payload.get("version"), "generated_at": payload.get("generated_at")},
            "scope": "All stored Learn topics and their cited sources; no release import",
            "limitations": ["No OCR, whole-slide rendering or automatic mathematical verification",
                            "Notes-confirmed answers remain unverified; visual flags include logos/decoration",
                            "Public-contract serialization is not a browser rendering test",
                            "Native-run, formatting and exclusion findings are review clues"],
            "topics": topics, "findings": items, "slides": evidence_slides,
            "counts": {"topics": len(topics), "sources_extracted": len(catalog["decks"]),
                       "source_slides": sum(d["slide_count"] for d in catalog["decks"]),
                       "findings": len(items), "codes": dict(Counter(f["code"] for f in items)),
                       "stages": dict(Counter(f["stage"] for f in items))},
            "validation": {"ok": validation["ok"], "ready_for_approval": validation["ready_for_approval"],
                           "problems": validation["problems"]},
            "skipped_sources": catalog.get("skipped", [])}


def run_bench(payload: dict, source: Path, work: Path, media_dir: Path | None = None) -> dict:
    """Extract cited Learn sources to a fresh directory; originals stay intact."""
    source = source.resolve()
    work = work.resolve()
    if work == source or source in work.parents:
        raise ValueError("Bench work directory must be outside the source corpus")
    if work.exists() and any(work.iterdir()):
        raise ValueError("Use a new or empty bench directory to avoid mixing snapshots")
    pipeline = Pipeline(source, work)
    paths: dict[str, Path] = {}
    for concept in payload.get("concepts", []):
        for ref in concept.get("source_decks", []):
            raw = ref.get("source_path", "")
            path = (source / raw).resolve()
            if not raw or not path.is_relative_to(source) or not path.is_file():
                pipeline.discovery_skips.append({"file": raw, "reason": "missing_or_outside_source_root", "severity": "review"})
            else:
                paths[source_key(raw)] = path
    catalog = pipeline.normalize(list(paths.values()))
    validation = pipeline.validate(catalog)
    drafts = pipeline.organize(catalog)
    probes = {}
    for deck in catalog["decks"]:
        key = source_key(deck["source_path"])
        path = source / deck["source_path"]
        if path.suffix.lower() == ".pptx":
            try:
                probes[key] = pptx_probe(path)
                if sha256_file(path) != deck["source_hash"]:
                    probes.pop(key, None)
                    catalog["skipped"].append({"file": key, "reason": "source_changed_during_probe", "severity": "review"})
            except (OSError, ValueError, KeyError, zipfile.BadZipFile, ET.ParseError) as exc:
                catalog["skipped"].append({"file": key, "reason": "independent_probe_failed: " + str(exc), "severity": "review"})
    report = analyze(payload, catalog, drafts, validation, probes, media_dir)
    report["source_root"] = str(source)
    report["source_snapshot"] = [{"source_path": d["source_path"], "source_hash": d["source_hash"],
                                  "slide_count": d["slide_count"]} for d in catalog["decks"]]
    for filename, data in (("release-snapshot.json", payload), ("catalog.json", catalog),
                           ("validation-report.json", validation), ("content-drafts.json", drafts), ("bench-report.json", report)):
        (work / filename).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    from .bench_report import render_report
    (work / "bench-report.html").write_text(render_report(report), encoding="utf-8")
    return report
