"""Draft figure selection retains source context and original image bytes."""
from copy import deepcopy
import hashlib
import json

import pytest
from PIL import Image

from app.lesson_media import asset_filename
from app.lessons import LessonAsset
from ingestion.lesson_drafts import compile_lessons
from ingestion.pipeline import sha256_file
from ingestion.source_review import object_sha256


@pytest.fixture
def evidence(tmp_path):
    source, media, frames = tmp_path / "source", tmp_path / "media", tmp_path / "frames"
    for root in (source, media, frames): root.mkdir()
    original = source / "CUBES.pptx"
    original.write_bytes(b"immutable source snapshot")
    image = media / "image.png"
    Image.new("RGBA", (300, 176), (255, 255, 255, 0)).save(image)
    image_hash = sha256_file(image)
    image.rename(media / f"original-{image_hash}.bin")
    source_hash = sha256_file(original)
    citation = {"deck_id": "cubes", "source_file": original.name, "source_path": original.name, "source_hash": source_hash,
                "slide_id": f"cubes@{source_hash[:16]}:slide-3", "slide_number": 3, "surface": "slide"}
    block = {"shape_id": 10, "block_id": citation["slide_id"] + ":shape-10", "surface": "slide", "type": "image",
             "source_hash": image_hash, "original_file": f"original-{image_hash}.bin", "image_id": "e" * 16,
             "crop": {"left": 0, "right": 0, "top": 0, "bottom": 0}, "rotation": 0, "group_path": []}
    logo = {**block, "shape_id": 9, "block_id": citation["slide_id"] + ":shape-9"}
    slide = {"slide_id": citation["slide_id"], "slide_number": 3, "blocks": [block, logo], "notes_blocks": [],
             "texts": ["Cubes"], "issues": [{"code": "visual_semantics_unresolved", "severity": "review"}]}
    catalog = {"decks": [{**{k: citation[k] for k in ("deck_id", "source_file", "source_path", "source_hash")}, "slides": [slide]}]}
    asset = {"image_id": image_hash[:16], "sha256": image_hash, "mime": "image/png", "width": 300, "height": 176}
    figure = {"type": "figure", "id": "cube-diagram", "image_id": image_hash[:16], "source": citation,
              "shape_id": 10, "block_sha256": object_sha256(block), "original_sha256": image_hash,
              "representation": "original_image", "role": "teaching_diagram", "caption": "Cube parts",
              "alt": "A labelled cube diagram.", "review_status": "candidate"}
    lesson = {"schema_version": 1, "id": "cubes", "title": "Cubes", "introduction": "Read the diagram.",
              "review_status": "draft", "assets": [asset], "sections": [
                  {"id": "parts", "title": "Parts", "stage": "overview", "blocks": [figure]}]}
    plan = {"lesson_plan_version": 1, "lessons": [lesson], "exclude_review_ids": []}
    frame = frames / "slide-3.png"
    Image.new("RGB", (800, 450), "white").save(frame)
    visual = {"visual_schema_version": 1, "approved": False, "source_root": str(source), "decks": [
        {"status": "rendered", "deck_id": "cubes", "source_path": original.name, "source_hash": source_hash,
         "slides": [{"slide_number": 3, "slide_id": citation["slide_id"], "file": frame.name, "sha256": sha256_file(frame)}]}]}
    visual_path = frames / "visual-report.json"
    visual_path.write_text(json.dumps(visual))
    review = {"review_schema_version": 1, "records": [{"review_id": "logo", "deck_id": "cubes", "source_path": original.name,
        "source_hash": source_hash, "slide_id": citation["slide_id"], "slide_number": 3, "surface": "slide", "target": "shape",
        "shape_id": 9, "block_sha256": object_sha256(logo), "decision": "decoration_candidate", "reviewer": "fixture reviewer",
        "reason": "One source occurrence, not a shared-asset-wide exclusion.", "observed": "Provider furniture at one position.",
        "evidence": [{"kind": "rendered_slide", "path": "frames/slide-3.png", "sha256": sha256_file(frame)}]}]}
    return plan, catalog, source, media, review, visual_path


def compile_fixture(evidence, tmp_path):
    plan, catalog, source, media, review, visual = evidence
    return compile_lessons(plan, catalog, source, media, tmp_path / "compiled", review, visual, tmp_path)


def test_original_bytes_shared_usage_and_native_flags_are_preserved(evidence, tmp_path):
    plan, catalog, source, media, _, _ = evidence
    other = deepcopy(plan["lessons"][0]); other["id"] = "cubes-another-topic"
    other["sections"][0]["blocks"][0]["caption"] = "The same diagram in a different lesson"
    plan["lessons"].append(other)
    before = deepcopy((plan, catalog))
    files = {p: p.read_bytes() for root in (source, media) for p in root.iterdir()}
    result = compile_fixture(evidence, tmp_path)
    assert result["approved"] is False and (plan, catalog) == before
    assert all(p.read_bytes() == value for p, value in files.items())
    asset = LessonAsset.model_validate(plan["lessons"][0]["assets"][0])
    assert (tmp_path / "compiled/media" / asset_filename(asset)).read_bytes() == next(media.glob("*.bin")).read_bytes()
    assert len(list((tmp_path / "compiled/media").iterdir())) == 1
    assert len([d for d in result["source_decisions"] if d["outcome"] == "included_figure"]) == 2
    assert any(d["outcome"] == "not_selected_needs_review" for d in result["source_decisions"])


def test_decoration_excludes_one_occurrence_not_shared_image_id(evidence, tmp_path):
    evidence[0]["exclude_review_ids"] = ["logo"]
    result = compile_fixture(evidence, tmp_path)
    selected = [d for d in result["source_decisions"] if d["outcome"] == "included_figure"]
    excluded = [d for d in result["source_decisions"] if d["outcome"] == "excluded_from_this_draft"]
    assert selected[0]["shape_id"] == 10 and excluded[0]["shape_id"] == 9
    assert evidence[1]["decks"][0]["slides"][0]["issues"]


@pytest.mark.parametrize("failure", ["changed_source", "wrong_citation", "wrong_slide", "changed_block", "ambiguous_shape",
    "changed_original", "wrong_dimensions", "wrong_mime", "cropped", "rotated", "grouped", "reviewed_lesson",
    "stale_exclusion", "unrecognized_exclusion", "selected_exclusion", "source_path_escape"])
def test_invalid_evidence_never_builds_a_lesson_bundle(evidence, tmp_path, failure):
    plan, catalog, source, media, review, _ = evidence
    lesson = plan["lessons"][0]; figure = lesson["sections"][0]["blocks"][0]
    block = catalog["decks"][0]["slides"][0]["blocks"][0]
    if failure == "changed_source": (source / "CUBES.pptx").write_bytes(b"changed")
    elif failure == "wrong_citation": figure["source"]["source_file"] = "Another.pptx"
    elif failure == "wrong_slide": figure["source"]["slide_id"] = "wrong"
    elif failure == "changed_block": figure["block_sha256"] = "c" * 64
    elif failure == "ambiguous_shape": catalog["decks"][0]["slides"][0]["blocks"].append(deepcopy(block))
    elif failure == "changed_original": next(media.glob("*.bin")).write_bytes(b"changed")
    elif failure == "wrong_dimensions": lesson["assets"][0]["width"] = 299
    elif failure == "wrong_mime": lesson["assets"][0]["mime"] = "image/jpeg"
    elif failure in ("cropped", "rotated", "grouped"):
        if failure == "cropped": block["crop"]["left"] = .1
        elif failure == "rotated": block["rotation"] = 90
        else: block["group_path"] = [5]
        figure["block_sha256"] = object_sha256(block)
    elif failure == "reviewed_lesson": lesson["review_status"] = "reviewed"
    elif failure == "stale_exclusion":
        plan["exclude_review_ids"] = ["logo"]; review["records"][0]["source_hash"] = "c" * 64
    elif failure == "unrecognized_exclusion": plan["exclude_review_ids"] = ["missing"]
    elif failure == "selected_exclusion":
        plan["exclude_review_ids"] = ["logo"]; review["records"][0].update(shape_id=10, block_sha256=object_sha256(block))
    elif failure == "source_path_escape":
        outside = tmp_path / "outside.pptx"; outside.write_bytes((source / "CUBES.pptx").read_bytes())
        catalog["decks"][0]["source_path"] = "../outside.pptx"; figure["source"]["source_path"] = "../outside.pptx"
    with pytest.raises(ValueError): compile_fixture(evidence, tmp_path)
    assert not (tmp_path / "compiled/lesson-bundle.json").exists()


def test_fresh_output_required(evidence, tmp_path):
    compile_fixture(evidence, tmp_path)
    with pytest.raises(ValueError): compile_fixture(evidence, tmp_path)
