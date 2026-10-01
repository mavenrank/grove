"""Preview reading is explicitly enabled and does not import or activate content."""
from copy import deepcopy
import json

import pytest

from app.config import settings
from app.lesson_media import asset_filename
from app.lessons import LessonAsset
from ingestion.lesson_drafts import compile_lessons
from test_lesson_drafts import evidence  # shared synthetic source/image fixture


def test_preview_disabled_by_default(client, monkeypatch):
    monkeypatch.setattr(settings, "lesson_preview_dir", None)
    assert client.get("/api/content/lesson-previews").status_code == 404


def test_bundle_to_api_to_original_png_is_lossless_and_read_only(client, monkeypatch, evidence, tmp_path):
    plan, catalog, source, media, _, _ = evidence
    output = tmp_path / "preview"
    bundle = compile_lessons(plan, catalog, source, media, output)
    monkeypatch.setattr(settings, "lesson_preview_dir", output)
    before = client.get("/api/content/concepts").json()
    index = client.get("/api/content/lesson-previews")
    assert index.json() == {"draft_only": True, "lessons": [{"id": "cubes", "title": "Cubes"}]}
    result = client.get("/api/content/lesson-previews/cubes")
    assert result.status_code == 200 and result.headers["cache-control"] == "no-store"
    assert result.json()["lesson"] == bundle["lessons"][0]
    assert result.json()["draft_only"] is True and "source_decisions" not in result.json()
    asset = LessonAsset.model_validate(bundle["lessons"][0]["assets"][0])
    image = client.get(f"/api/content/lesson-previews/cubes/media/{asset.image_id}")
    assert image.status_code == 200 and image.headers["content-type"] == "image/png"
    assert image.content == (output / "media" / asset_filename(asset)).read_bytes()
    assert client.get("/api/content/concepts").json() == before
    assert client.post("/api/content/lesson-previews/cubes", json={"approved": True}).status_code == 405
    assert client.get("/api/content/lesson-previews/unknown").status_code == 404
    assert client.get("/api/content/lesson-previews/cubes/media/" + "e" * 16).status_code == 404


@pytest.mark.parametrize("failure", ["changed_bytes", "missing_image", "invalid_mime", "changed_dimensions", "approved_bundle",
                                    "duplicate_lesson", "missing_bundle", "malformed_json"])
def test_preview_integrity_failure_is_explicit(client, monkeypatch, evidence, tmp_path, failure):
    plan, catalog, source, media, _, _ = evidence
    output = tmp_path / "preview"
    bundle = compile_lessons(plan, catalog, source, media, output)
    monkeypatch.setattr(settings, "lesson_preview_dir", output)
    path = output / "lesson-bundle.json"
    image_id = bundle["lessons"][0]["assets"][0]["image_id"]
    target = output / "media" / (image_id + ".png")
    if failure == "changed_bytes": target.write_bytes(b"changed")
    elif failure == "missing_image": target.unlink()
    elif failure == "invalid_mime": bundle["lessons"][0]["assets"][0]["mime"] = "image/jpeg"
    elif failure == "changed_dimensions": bundle["lessons"][0]["assets"][0]["width"] = 299
    elif failure == "approved_bundle": bundle["approved"] = True
    elif failure == "duplicate_lesson": bundle["lessons"].append(deepcopy(bundle["lessons"][0]))
    elif failure == "missing_bundle": path.unlink()
    elif failure == "malformed_json": path.write_text("{malformed")
    if failure not in ("missing_bundle", "malformed_json"):
        path.write_text(json.dumps(bundle))
    result = client.get(f"/api/content/lesson-previews/cubes/media/{image_id}")
    assert result.status_code == 409
