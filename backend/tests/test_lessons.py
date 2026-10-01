"""Ordered teaching figures survive the API without weakening release approval."""
from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.lessons import Lesson
from app.schemas import ConceptOut


def lesson_fixture():
    source = {"deck_id": "cubes", "source_file": "Cubes.pptx", "source_path": "Cubes.pptx",
              "source_hash": "a" * 64, "slide_id": "cubes@aaaaaaaaaaaaaaaa:slide-3", "slide_number": 3}
    figure = {"type": "figure", "id": "cube-face-edge-vertex", "image_id": "b" * 16,
              "source": source, "shape_id": 10, "block_sha256": "c" * 64, "original_sha256": "b" * 64,
              "representation": "original_image", "role": "teaching_diagram", "caption": "Face, edge and vertex",
              "alt": "A cube with arrows identifying a face, an edge and a vertex.", "review_status": "candidate"}
    return {"schema_version": 1, "id": "cubes-pilot", "title": "Read a cube diagram",
            "introduction": "Use the labelled source diagram.", "review_status": "draft",
            "assets": [{"image_id": "b" * 16, "sha256": "b" * 64, "mime": "image/png", "width": 300, "height": 176}],
            "sections": [{"id": "parts", "title": "Parts of a cube", "stage": "overview", "blocks": [
                {"type": "text", "id": "read-labels", "paragraphs": ["Read the three labels."], "sources": [source]}, figure]}]}


def test_ordered_figure_and_source_survive_public_api(client, monkeypatch):
    from app.routers import content
    lesson = lesson_fixture()
    concept = {"id": "concept.cubes", "skill_id": "logic.cubes", "title": "Cubes", "summary": "Teaching material", "lesson": lesson}
    monkeypatch.setattr(content, "load_release", lambda: {"concepts": [concept]})
    result = client.get("/api/content/concepts/concept.cubes")
    assert result.status_code == 200
    assert result.json()["lesson"] == Lesson.model_validate(lesson).model_dump()
    figure = result.json()["lesson"]["sections"][0]["blocks"][1]
    assert figure["source"]["slide_number"] == 3 and figure["shape_id"] == 10
    assert figure["alt"] and figure["caption"]
    assert ConceptOut(id="legacy", skill_id="logic.cubes", title="Legacy", summary="Old release").lesson is None


def test_one_asset_supports_separate_occurrences_and_example_figures():
    lesson = lesson_fixture()
    figure = deepcopy(lesson["sections"][0]["blocks"][1])
    figure["id"] = "example-diagram"
    figure["role"] = "example_prompt"
    figure["source"]["slide_number"] = 4
    figure["source"]["slide_id"] = "cubes@aaaaaaaaaaaaaaaa:slide-4"
    lesson["sections"][0]["blocks"].append({"type": "example", "id": "example", "prompt": "Locate an edge.",
        "givens": ["Labelled cube"], "target": "The edge", "steps": [{"title": "Read", "text": "Follow the edge arrow."}],
        "result": "Edge", "verification": "unverified", "sources": [figure["source"]], "figures": [figure]})
    result = Lesson.model_validate(lesson)
    assert len(result.assets) == 1
    assert result.sections[0].blocks[1].source.slide_number != result.sections[0].blocks[2].figures[0].source.slide_number


@pytest.mark.parametrize("failure", ["asset_identity", "duplicate_asset", "missing_asset", "unused_asset", "duplicate_block",
                                    "duplicate_figure", "blank_alt", "invalid_type", "unsupported_mime", "private_field",
                                    "reviewed_candidate", "unknown_version"])
def test_invalid_lessons_are_rejected(failure):
    lesson = lesson_fixture()
    figure = lesson["sections"][0]["blocks"][1]
    if failure == "asset_identity": lesson["assets"][0]["sha256"] = "d" * 64
    elif failure == "duplicate_asset": lesson["assets"].append(deepcopy(lesson["assets"][0]))
    elif failure == "missing_asset": lesson["assets"] = []
    elif failure == "unused_asset": figure["image_id"] = "e" * 16
    elif failure == "duplicate_block": figure["id"] = "read-labels"
    elif failure == "duplicate_figure": lesson["sections"][0]["blocks"].append(deepcopy(figure))
    elif failure == "blank_alt": figure["alt"] = " "
    elif failure == "invalid_type": figure["type"] = "raw-html"
    elif failure == "unsupported_mime": lesson["assets"][0]["mime"] = "image/svg+xml"
    elif failure == "private_field": figure["notes_raw"] = "Private extraction notes"
    elif failure == "reviewed_candidate": lesson["review_status"] = "reviewed"
    elif failure == "unknown_version": lesson["schema_version"] = 2
    with pytest.raises(ValidationError): Lesson.model_validate(lesson)
