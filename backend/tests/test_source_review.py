"""Review provenance cannot silently exclude content or waive approval blockers."""
from copy import deepcopy
import json

import pytest

from ingestion.pipeline import sha256_file
from ingestion.source_review import object_sha256, run_source_reviews


@pytest.fixture
def evidence(tmp_path):
    source, root = tmp_path / "source", tmp_path / "evidence"
    source.mkdir(); root.mkdir()
    original = source / "SPEED.pptx"
    original.write_bytes(b"source snapshot")
    frame = root / "slide-1.png"
    frame.write_bytes(b"rendered frame snapshot")
    block = {"shape_id": 9, "block_id": "speed:1:shape-9", "surface": "slide", "type": "image",
             "image_id": "provider", "bounds_emu": {"left": 10, "top": 20, "width": 200, "height": 100}}
    slide = {"slide_number": 1, "slide_id": "speed:1", "blocks": [block], "notes_blocks": [],
             "issues": [{"code": "visual_semantics_unresolved"}]}
    catalog = {"decks": [{"deck_id": "speed", "source_path": original.name, "source_hash": sha256_file(original),
                          "slides": [slide]}]}
    native = root / "catalog.json"
    native.write_text(json.dumps(catalog), encoding="utf-8")
    visual = {"visual_schema_version": 1, "approved": False, "source_root": str(source), "decks": [
        {"status": "rendered", "deck_id": "speed", "source_path": original.name, "source_hash": sha256_file(original),
         "slides": [{"slide_number": 1, "slide_id": "speed:1", "file": frame.name, "sha256": sha256_file(frame)}]}]}
    visual_path = root / "visual-report.json"
    visual_path.write_text(json.dumps(visual), encoding="utf-8")
    record = {"review_id": "speed-logo-1", "deck_id": "speed", "source_path": original.name,
              "source_hash": sha256_file(original), "slide_number": 1, "slide_id": "speed:1", "surface": "slide",
              "target": "shape", "shape_id": 9, "block_sha256": object_sha256(block),
              "decision": "decoration_candidate", "reviewer": "manual fixture reviewer",
              "reason": "Exact provider mark at bottom right.", "observed": "Provider logo; no question values.",
              "proposed": "Exclude this occurrence only after semantic review. <script>unsafe()</script>",
              "evidence": [{"kind": "rendered_slide", "path": frame.name, "sha256": sha256_file(frame)}]}
    return catalog, source, visual_path, {"review_schema_version": 1, "records": [record]}, root


def run(evidence, tmp_path):
    catalog, source, visual, manifest, root = evidence
    return run_source_reviews(catalog, source, visual, manifest, root, tmp_path / "review")


def test_annotation_preserves_native_issues_source_and_evidence(evidence, tmp_path):
    catalog, source, visual, manifest, root = evidence
    before = deepcopy((catalog, manifest))
    files = {p: p.read_bytes() for directory in (source, root) for p in directory.iterdir()}
    report = run(evidence, tmp_path)
    assert (catalog, manifest) == before and all(p.read_bytes() == value for p, value in files.items())
    assert report["approved"] is False and report["annotation_only"] is True
    assert report["counts"] == {"accepted_annotation": 1, "rejected": 0}
    assert report["records"][0]["native_issues"] == catalog["decks"][0]["slides"][0]["issues"]
    assert "none" in report["records"][0]["publication_effect"]
    html = (tmp_path / "review/source-review-report.html").read_text("utf-8")
    assert "<script>unsafe()" not in html and "&lt;script&gt;unsafe()" in html


@pytest.mark.parametrize("failure", ["source_changed", "stale_hash", "wrong_slide", "wrong_surface", "wrong_shape",
    "changed_block", "ambiguous_shape", "no_reason", "no_evidence", "frame_changed", "wrong_frame",
    "blanket_decoration", "absolute_path", "path_escape", "approve_field", "approve_decision", "boolean_position"])
def test_invalid_scopes_are_rejected_without_approving(evidence, tmp_path, failure):
    catalog, source, visual, manifest, root = evidence
    r = manifest["records"][0]
    if failure == "source_changed":
        (source / "SPEED.pptx").write_bytes(b"changed")
    elif failure == "stale_hash": r["source_hash"] = "a" * 64
    elif failure == "wrong_slide": r["slide_id"] = "speed:2"
    elif failure == "wrong_surface": r["surface"] = "notes"
    elif failure == "wrong_shape": r["shape_id"] = 10
    elif failure == "changed_block": r["block_sha256"] = "b" * 64
    elif failure == "ambiguous_shape": catalog["decks"][0]["slides"][0]["blocks"] *= 2
    elif failure == "no_reason": r["reason"] = " "
    elif failure == "no_evidence": r["evidence"] = []
    elif failure == "frame_changed": (root / "slide-1.png").write_bytes(b"changed")
    elif failure == "wrong_frame":
        value = json.loads(visual.read_text("utf-8")); value["decks"][0]["slides"][0]["slide_id"] = "speed:2"
        visual.write_text(json.dumps(value), encoding="utf-8")
    elif failure == "blanket_decoration":
        r["target"] = "slide"; del r["shape_id"]; del r["block_sha256"]
    elif failure == "absolute_path": r["evidence"][0]["path"] = str(root / "slide-1.png")
    elif failure == "path_escape":
        outside = tmp_path / "outside.png"; outside.write_bytes(b"outside")
        r["evidence"][0].update(path="../outside.png", sha256=sha256_file(outside))
    elif failure == "approve_field": r["approved"] = True
    elif failure == "approve_decision": r["decision"] = "approve"
    elif failure == "boolean_position": r["slide_number"] = True
    report = run(evidence, tmp_path)
    assert report["counts"] == {"accepted_annotation": 0, "rejected": 1}
    assert report["approved"] is False and report["records"][0]["problem"]
    assert "<a href=" not in (tmp_path / "review/source-review-report.html").read_text("utf-8")


@pytest.mark.parametrize("conflict", ["duplicate_id", "different_reason_same_scope"])
def test_all_conflicting_records_are_rejected(evidence, tmp_path, conflict):
    manifest = evidence[3]
    other = deepcopy(manifest["records"][0])
    if conflict == "different_reason_same_scope":
        other.update(review_id="different-id", reason="Contradictory reasoning")
    manifest["records"].append(other)
    assert run(evidence, tmp_path)["counts"] == {"accepted_annotation": 0, "rejected": 2}


def test_notes_need_native_evidence_and_remain_separate(evidence, tmp_path):
    catalog, _, _, manifest, root = evidence
    slide = catalog["decks"][0]["slides"][0]
    notes = {"shape_id": 9, "surface": "notes", "type": "text", "text": "Wrong source multiplication"}
    slide["notes_blocks"] = [notes]
    r = manifest["records"][0]
    r.update(surface="notes", decision="flag_source_error", block_sha256=object_sha256(notes))
    report = run(evidence, tmp_path)
    assert report["counts"]["rejected"] == 1
    native = root / "catalog.json"
    native.write_text(json.dumps(catalog), encoding="utf-8")
    r["evidence"].append({"kind": "native_catalog", "path": native.name, "sha256": sha256_file(native)})
    report = run_source_reviews(catalog, evidence[1], evidence[2], manifest, root, tmp_path / "notes-review")
    assert report["counts"]["accepted_annotation"] == 1
    assert slide["blocks"][0]["type"] == "image" and slide["notes_blocks"][0] == notes


def test_invalid_manifest_and_nonempty_outputs_refuse_to_overwrite(evidence, tmp_path):
    catalog, source, visual, manifest, root = evidence
    with pytest.raises(ValueError):
        run_source_reviews(catalog, source, visual, {**manifest, "approved": True}, root, tmp_path / "review")
    with pytest.raises(ValueError):
        run_source_reviews(catalog, source, visual, manifest, root, source)
    run(evidence, tmp_path)
    with pytest.raises(ValueError): run(evidence, tmp_path)


def test_source_change_during_validation_prevents_report_acceptance(evidence, tmp_path, monkeypatch):
    import ingestion.source_review as review
    original = evidence[1] / "SPEED.pptx"
    real_sha = review.sha256_file
    changed = False

    def change_after_initial_hash(path):
        nonlocal changed
        digest = real_sha(path)
        if path == original and not changed:
            path.write_bytes(b"source changed after initial hash")
            changed = True
        return digest

    monkeypatch.setattr(review, "sha256_file", change_after_initial_hash)
    with pytest.raises(ValueError, match="changed during review"):
        run(evidence, tmp_path)
    assert not (tmp_path / "review").exists()
