"""Request-body models (the inbound half of the API allowlist)."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from ..config import settings


class CreateSessionIn(BaseModel):
    question_count: int = Field(ge=1, le=50)
    # Optional custom duration in minutes; the server clamps and owns the
    # final value (handoff §6.4: blueprint owns final values).
    duration_minutes: int | None = Field(default=None, ge=1, le=180)

    @field_validator("question_count")
    @classmethod
    def allowed(cls, v: int) -> int:
        if v not in settings.allowed_question_counts:
            raise ValueError(f"question count must be one of {settings.allowed_question_counts}")
        return v


class AnswerIn(BaseModel):
    ticket: str = Field(min_length=8, max_length=128)
    option: str = Field(min_length=1, max_length=1)
    idempotency_key: str | None = Field(default=None, max_length=128)


class MarkIn(BaseModel):
    marked: bool


class EventIn(BaseModel):
    position: int | None = Field(default=None, ge=0, le=1000)
    type: str = Field(min_length=1, max_length=64)
    client_time: float | None = None
    payload: dict[str, Any] = Field(default_factory=dict, max_length=64)


class EventsIn(BaseModel):
    events: list[EventIn] = Field(max_length=settings.max_events_per_batch)


class FlashcardReviewIn(BaseModel):
    """SRS grading: rating is the canonical field; the legacy two-button
    `action` still maps through (again→again, remember→good)."""

    flashcard_id: str = Field(min_length=1, max_length=128)
    rating: str | None = None
    action: str | None = None

    def normalized_rating(self) -> str:
        if self.rating is not None:
            if self.rating not in ("again", "good", "easy"):
                raise ValueError("rating must be 'again', 'good' or 'easy'")
            return self.rating
        if self.action == "again":
            return "again"
        if self.action == "remember":
            return "good"
        raise ValueError("provide rating ('again'|'good'|'easy') or legacy action")


class FlashcardViewIn(BaseModel):
    flashcard_ids: list[str] = Field(min_length=1, max_length=50)

    @field_validator("flashcard_ids")
    @classmethod
    def ids_bounded(cls, v: list[str]) -> list[str]:
        for x in v:
            if not (1 <= len(x) <= 128):
                raise ValueError("flashcard id out of bounds")
        return v


class DwellIn(BaseModel):
    position: int = Field(ge=0, le=1000)
    seconds: float = Field(ge=0, le=3600)
    kind: str = Field(default="active", max_length=16)


class SourceOpenIn(BaseModel):
    source_path: str = Field(min_length=1, max_length=512)


class ConceptViewIn(BaseModel):
    concept_id: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=200)
