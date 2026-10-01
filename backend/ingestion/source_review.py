"""Snapshot-scoped review annotations. Validation never changes publication gates."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

from .pipeline import now_iso, sha256_file
from .visual_report import render_source_reviews

DECISIONS = {"decoration_candidate", "confirm_visual_text", "flag_source_error",
             "flag_source_ambiguity", "flag_ocr_error", "confirm_answer_derivation"}
REQUIRED = {"review_id", "deck_id", "source_path", "source_hash", "slide_id", "slide_number",
            "surface", "target", "decision", "reason", "reviewer", "observed", "evidence"}
OPTIONAL = {"shape_id", "block_sha256", "proposed"}


def object_sha256(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def contained_file(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("evidence/source path must be relative")
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("evidence/source missing or outside its root")
    return path


def decision_key(record: dict) -> str:
    return json.dumps([record.get(k) for k in ("deck_id", "source_hash", "slide_number", "surface",
                                              "target", "shape_id", "decision")], sort_keys=True)


def run_source_reviews(catalog: dict, source: Path, visual_path: Path, manifest: dict,
                       evidence_root: Path, output: Path) -> dict:
    """Accept only traceable annotations; both accepted and rejected records stay unapproved."""
    source, evidence_root, output = source.resolve(), evidence_root.resolve(), output.resolve()
    if (output in (source, evidence_root) or source in output.parents
            or output in evidence_root.parents or (output.exists() and any(output.iterdir()))):
        raise ValueError("use a new/empty review directory that cannot replace sources/evidence")
    if (set(manifest) != {"review_schema_version", "records"} or type(manifest["review_schema_version"]) is not int
            or manifest["review_schema_version"] != 1 or not isinstance(manifest["records"], list)
            or not 1 <= len(manifest["records"]) <= 5000
            or any(not isinstance(r, dict) for r in manifest["records"])):
        raise ValueError("invalid review manifest version/records")
    visual_path = visual_path.resolve()
    visual_bytes = visual_path.read_bytes()
    visual = json.loads(visual_bytes)
    if (visual.get("visual_schema_version") != 1 or visual.get("approved") is not False
            or Path(visual["source_root"]).resolve() != source):
        raise ValueError("visual report must be an unapproved snapshot of this source root")
    records = manifest["records"]
    # Reject every duplicate/conflicting entry rather than allowing first-record-wins.
    ids = Counter(json.dumps(r.get("review_id"), sort_keys=True) for r in records)
    keys = Counter(decision_key(r) for r in records)
    report = {"review_schema_version": 1, "created_at": now_iso(), "approved": False,
              "annotation_only": True, "source_root": str(source), "evidence_root": str(evidence_root),
              "catalog_sha256": object_sha256(catalog), "manifest_sha256": object_sha256(manifest),
              "visual_report_sha256": hashlib.sha256(visual_bytes).hexdigest(), "records": []}
    hashes: dict[Path, str] = {}

    def verified(path: Path, expected: str) -> None:
        if (not isinstance(expected, str) or len(expected) != 64
                or any(c not in "0123456789abcdef" for c in expected)):
            raise ValueError("invalid SHA-256")
        if path not in hashes:
            hashes[path] = sha256_file(path)
        if hashes[path] != expected:
            raise ValueError("source/evidence hash changed")

    verified(visual_path.resolve(), report["visual_report_sha256"])

    for record in records:
        result = {"record": record, "status": "rejected"}
        report["records"].append(result)
        try:
            if not REQUIRED <= set(record) or set(record) - REQUIRED - OPTIONAL:
                raise ValueError("unexpected or missing review fields")
            for field in REQUIRED - {"slide_number", "evidence"} | ({"proposed"} & set(record)):
                if not isinstance(record[field], str) or not record[field].strip() or len(record[field]) > 10_000:
                    raise ValueError("review text must be nonempty and bounded: " + field)
            if (record["decision"] not in DECISIONS or record["surface"] not in {"slide", "notes"}
                    or record["target"] not in {"slide", "shape"} or type(record["slide_number"]) is not int):
                raise ValueError("invalid decision/surface/target/position")
            if ids[json.dumps(record["review_id"], sort_keys=True)] != 1 or keys[decision_key(record)] != 1:
                raise ValueError("duplicate ID or conflicting decisions for this target")
            decks = [d for d in catalog["decks"] if d["deck_id"] == record["deck_id"]]
            if len(decks) != 1:
                raise ValueError("unknown/ambiguous source deck")
            deck = decks[0]
            if (deck["source_path"] != record["source_path"] or deck["source_hash"] != record["source_hash"]):
                raise ValueError("review targets a different source snapshot")
            verified(contained_file(source, record["source_path"]), record["source_hash"])
            slides = [s for s in deck["slides"] if s["slide_number"] == record["slide_number"]]
            if len(slides) != 1 or slides[0]["slide_id"] != record["slide_id"]:
                raise ValueError("unknown/ambiguous slide snapshot")
            slide = slides[0]
            if record["target"] == "shape":
                if type(record.get("shape_id")) is not int:
                    raise ValueError("shape target requires an integer shape ID")
                blocks = slide["blocks" if record["surface"] == "slide" else "notes_blocks"]
                selected = [b for b in blocks if b["shape_id"] == record["shape_id"]]
                if (len(selected) != 1 or selected[0]["surface"] != record["surface"]
                        or object_sha256(selected[0]) != record.get("block_sha256")):
                    raise ValueError("unknown/ambiguous/changed shape evidence")
            elif {"shape_id", "block_sha256"} & set(record):
                raise ValueError("slide target cannot carry shape fields")
            if record["decision"] == "decoration_candidate" and record["target"] != "shape":
                raise ValueError("decoration must target one source shape; blanket exclusion is forbidden")
            evidence = record["evidence"]
            if not isinstance(evidence, list) or not 1 <= len(evidence) <= 16:
                raise ValueError("review requires bounded evidence references")
            kinds = set()
            for item in evidence:
                if not isinstance(item, dict) or set(item) != {"kind", "path", "sha256"}:
                    raise ValueError("invalid evidence fields")
                path = contained_file(evidence_root, item["path"])
                verified(path, item["sha256"])
                kind = item["kind"]
                if kind == "rendered_slide":
                    matches = [(d, s) for d in visual["decks"] if d["status"] == "rendered"
                               for s in d["slides"] if (visual_path.parent / s["file"]).resolve() == path]
                    if len(matches) != 1:
                        raise ValueError("frame missing/ambiguous in visual report")
                    vd, vs = matches[0]
                    if (vd["deck_id"] != deck["deck_id"] or vd["source_path"] != deck["source_path"]
                            or vd["source_hash"] != deck["source_hash"]
                            or vs["slide_id"] != slide["slide_id"] or vs["slide_number"] != slide["slide_number"]
                            or vs["sha256"] != item["sha256"]):
                        raise ValueError("frame belongs to a different source/slide snapshot")
                elif kind == "native_catalog":
                    if json.loads(path.read_text(encoding="utf-8")) != catalog:
                        raise ValueError("native evidence belongs to a different catalog")
                elif kind != "supporting":
                    raise ValueError("unknown evidence kind")
                kinds.add(kind)
            if "rendered_slide" not in kinds or (record["surface"] == "notes" and "native_catalog" not in kinds):
                raise ValueError("review requires the exact whole frame; notes also require native catalog evidence")
            result.update(status="accepted_annotation", native_issues=slide.get("issues", []),
                          publication_effect="none; source/OCR/answer claims still need semantic verification")
        except (ValueError, OSError, KeyError, TypeError) as exc:
            result["problem"] = str(exc)
    # Recheck dependencies before recording acceptance, including changes during the run.
    for path, expected in hashes.items():
        if not path.is_file() or sha256_file(path) != expected:
            raise ValueError("source/evidence changed during review validation")
    report["counts"] = {status: sum(r["status"] == status for r in report["records"])
                        for status in ("accepted_annotation", "rejected")}
    output.mkdir(parents=True, exist_ok=True)
    (output / "source-review-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    (output / "source-review-report.html").write_text(render_source_reviews(report, output), encoding="utf-8")
    return report
