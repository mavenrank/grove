"""Content routes: taxonomy, concepts, flashcards, media, source-open."""
from __future__ import annotations

import base64
import os
import re
import subprocess
from typing import Any

from fastapi import APIRouter, HTTPException

from .. import db, history, srs
from ..config import settings
from ..content_engine.releases import load_release
from ..schemas import (
    BucketOut, ConceptOut, EventsAcceptedOut, FlashcardDeckOut, FlashcardOut,
    FlashcardReviewOut, FlashcardSessionCardOut, FlashcardSkillStatsOut,
    MediaOut, TaxonomyOut,
)
from .requests import ConceptViewIn, FlashcardReviewIn, FlashcardViewIn, SourceOpenIn

router = APIRouter(prefix="/api")


def _taxonomy_payload() -> list[dict[str, Any]]:
    from ..content_engine.taxonomy import BUCKETS
    return [
        {"id": b.id, "name": b.name,
         "topics": [
             {"id": t.id, "name": t.name,
              "skills": [{"id": s.id, "name": s.name} for s in t.skills]}
             for t in b.topics
         ]}
        for b in BUCKETS
    ]


@router.get("/content/taxonomy", response_model=TaxonomyOut)
def taxonomy() -> TaxonomyOut:
    return TaxonomyOut(buckets=[BucketOut(**b) for b in _taxonomy_payload()])


@router.get("/content/concepts", response_model=list[ConceptOut])
def concepts() -> list[ConceptOut]:
    rel = load_release()
    return [ConceptOut(**c) for c in rel.get("concepts", [])]


@router.get("/content/concepts/{concept_id}", response_model=ConceptOut)
def concept_detail(concept_id: str) -> ConceptOut:
    rel = load_release()
    for c in rel.get("concepts", []):
        if c["id"] == concept_id:
            return ConceptOut(**c)
    raise HTTPException(status_code=404, detail="concept not found")


@router.post("/source/open")
def source_open(body: SourceOpenIn) -> dict[str, Any]:
    """QOL for local review: reveal an ingested source deck in File Explorer.

    Single-learner localhost product, so this is a deliberate convenience;
    it validates the path against the release's source_root and never
    executes anything — it only asks the OS file manager to select the file.
    """
    if not settings.enable_source_open:
        raise HTTPException(status_code=403, detail="source opening is disabled")
    rel = load_release()
    source_root = rel.get("source_root")
    if not source_root:
        raise HTTPException(status_code=409, detail="no source root in this release")
    requested = os.path.normpath(os.path.abspath(body.source_path))
    root = os.path.normpath(os.path.abspath(source_root))
    if not requested.startswith(root + os.sep) and requested != root:
        raise HTTPException(status_code=403, detail="path outside the ingested source root")
    if not os.path.exists(requested):
        raise HTTPException(status_code=404, detail="source file not found on disk")
    try:
        if os.name == "nt":
            subprocess.Popen(["explorer", "/select,", requested])
        elif os.name == "posix":
            folder = requested if os.path.isdir(requested) else os.path.dirname(requested)
            try:
                subprocess.Popen(["open", folder])  # macOS
            except FileNotFoundError:
                subprocess.Popen(["xdg-open", folder])  # Linux
        else:
            raise HTTPException(status_code=501, detail="unsupported platform")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"could not open explorer: {exc}") from exc
    return {"opened": requested}


@router.get("/media/{image_id}", response_model=MediaOut)
def media(image_id: str) -> MediaOut:
    """Serve an ingested slide image (read-only, no personalization)."""
    if not re.fullmatch(r"[0-9a-f]{16}", image_id):
        raise HTTPException(status_code=404, detail="media not found")
    path = settings.media_dir / f"{image_id}.jpg"
    if not path.exists():
        raise HTTPException(status_code=404, detail="media not found")
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return MediaOut(image_id=image_id, mime="image/jpeg", data_base64=data)


@router.get("/content/flashcards", response_model=list[FlashcardOut])
def flashcards() -> list[FlashcardOut]:
    rel = load_release()
    return [FlashcardOut(**fc) for fc in rel.get("flashcards", [])]


@router.post("/flashcard-reviews", response_model=FlashcardReviewOut)
def flashcard_review(body: FlashcardReviewIn) -> FlashcardReviewOut:
    """Grade a card: schedules the next review and records the event."""
    rel = load_release()
    known = {fc["id"] for fc in rel.get("flashcards", [])}
    if body.flashcard_id not in known:
        raise HTTPException(status_code=404, detail="flashcard not found in this release")
    try:
        rating = body.normalized_rating()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    nxt = srs.rate_flashcard(body.flashcard_id, rating)
    db.insert_flashcard_review(body.flashcard_id, rel.get("release_id", "grove-bootstrap"),
                               rel.get("version", "0.0.0"), "again" if rating == "again" else "remember")
    return FlashcardReviewOut(accepted=1, due_at=nxt["due_at"], interval_days=nxt["interval_days"])


@router.get("/flashcards/session", response_model=list[FlashcardSessionCardOut])
def flashcard_session(limit: int = 20, topic: str | None = None) -> list[FlashcardSessionCardOut]:
    """A bounded review session: due cards (most overdue first) then new ones."""
    if not (1 <= limit <= 50):
        raise HTTPException(status_code=422, detail="limit must be 1..50")
    rel = load_release()
    cards = srs.session_cards(rel.get("flashcards", []), limit=limit, topic_id=topic)
    return [FlashcardSessionCardOut(**c) for c in cards]


@router.get("/flashcards/decks", response_model=list[FlashcardDeckOut])
def flashcard_decks() -> list[FlashcardDeckOut]:
    """Per-topic decks with due/new/strong counts for the deck grid."""
    from ..content_engine.taxonomy import BUCKETS
    topic_map = {
        s.id: (t.id, t.name, b.name)
        for b in BUCKETS for t in b.topics for s in t.skills
    }
    return [FlashcardDeckOut(**d) for d in srs.topic_decks(topic_map)]


@router.post("/flashcard-views", response_model=EventsAcceptedOut)
def flashcard_views(body: FlashcardViewIn) -> EventsAcceptedOut:
    """Record that the learner looked at these cards (deduped per card)."""
    rel = load_release()
    release_id = rel.get("release_id", "grove-bootstrap")
    version = rel.get("version", "0.0.0")
    known = {fc["id"]: fc.get("skill_id", "unknown") for fc in rel.get("flashcards", [])}
    n = 0
    for fid in body.flashcard_ids:
        skill_id = known.get(fid)
        if skill_id is None:
            continue  # never record views for unknown card ids
        history.record_flashcard_view(fid, skill_id, release_id, version)
        n += 1
    return EventsAcceptedOut(accepted=n)


@router.get("/flashcards/stats", response_model=list[FlashcardSkillStatsOut])
def flashcard_stats() -> list[FlashcardSkillStatsOut]:
    from ..evidence import flashcard_skill_stats
    return [FlashcardSkillStatsOut(**s) for s in flashcard_skill_stats()]


@router.post("/concept-views", response_model=EventsAcceptedOut)
def concept_view(body: ConceptViewIn) -> EventsAcceptedOut:
    history.record_concept_view(body.concept_id, body.title)
    return EventsAcceptedOut(accepted=1)
