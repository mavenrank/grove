"""Opt-in read-only draft lessons. No activation, progress writes or source execution."""
import json
import re

from fastapi import APIRouter, HTTPException, Response

from ..config import settings
from ..lesson_media import asset_filename, verified_image
from ..lessons import LessonBundle, LessonPreviewOut

router = APIRouter(prefix="/content/lesson-previews")


def load_bundle() -> LessonBundle:
    if settings.lesson_preview_dir is None:
        raise HTTPException(status_code=404, detail="lesson previews are not enabled")
    root = settings.lesson_preview_dir.resolve()
    path = root / "lesson-bundle.json"
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 2 * 1024 * 1024:
            raise ValueError("preview bundle missing or outside supported size")
        raw = json.loads(path.read_text(encoding="utf-8"))
        if raw.get("approved") is not False or type(raw.get("bundle_schema_version")) is not int:
            raise ValueError("preview bundle must be explicitly unapproved")
        return LessonBundle.model_validate(raw)
    except (ValueError, OSError, TypeError, KeyError) as exc:
        raise HTTPException(status_code=409, detail="draft preview bundle is invalid; rebuild it") from exc


def find_lesson(bundle: LessonBundle, lesson_id: str):
    if re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", lesson_id):
        for lesson in bundle.lessons:
            if lesson.id == lesson_id:
                return lesson
    raise HTTPException(status_code=404, detail="lesson preview not found")


@router.get("")
def list_previews():
    bundle = load_bundle()
    return {"draft_only": True, "lessons": [{"id": l.id, "title": l.title} for l in bundle.lessons]}


@router.get("/{lesson_id}", response_model=LessonPreviewOut)
def lesson_preview(lesson_id: str, response: Response):
    bundle = load_bundle()
    response.headers["Cache-Control"] = "no-store"
    return LessonPreviewOut(lesson=find_lesson(bundle, lesson_id), catalog_sha256=bundle.catalog_sha256)


@router.get("/{lesson_id}/media/{image_id}")
def preview_media(lesson_id: str, image_id: str):
    bundle = load_bundle()
    lesson = find_lesson(bundle, lesson_id)
    asset = next((a for a in lesson.assets if a.image_id == image_id), None)
    if asset is None:
        raise HTTPException(status_code=404, detail="image is not attached to this lesson preview")
    root = settings.lesson_preview_dir.resolve() / "media"
    try:
        data = verified_image(root / asset_filename(asset), asset, root)
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=409, detail="preview image missing or changed; rebuild the draft") from exc
    return Response(content=data, media_type=asset.mime,
                    headers={"Cache-Control": "private, max-age=3600, immutable", "X-Content-Type-Options": "nosniff"})
