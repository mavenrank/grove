"""Pydantic response models.

Public models are explicit allowlists (handoff §8.6): we build them field by
field; nothing from a database row or a private question dict is ever passed
through directly.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PublicOption(BaseModel):
    id: str
    text: str


class QuestionOut(BaseModel):
    """The ONLY question shape the client ever sees. No answer fields exist here."""

    session_id: str
    ticket: str
    position: int
    total_questions: int
    prompt: str
    options: list[PublicOption]
    expires_at: str
    answered: bool = False
    marked: bool = False


class SessionCreatedOut(BaseModel):
    session_id: str
    question_count: int
    duration_seconds: int
    deadline_at: str
    blueprint_version: str
    release_version: str


class AnswerAcceptedOut(BaseModel):
    accepted: bool
    remaining: int


class MarkedOut(BaseModel):
    marked: bool


class EventsAcceptedOut(BaseModel):
    accepted: int


class ScoreOut(BaseModel):
    total_questions: int
    correct: int
    incorrect: int
    unanswered: int
    accuracy: float


class PerQuestionResult(BaseModel):
    position: int
    family_id: str
    skill_id: str
    bucket_id: str | None = None
    topic_id: str | None = None
    topic_name: str | None = None
    difficulty: str
    answered: bool
    chosen: str | None
    correct_option: str | None
    is_correct: bool
    explanation: str
    marked: bool
    dwell_seconds: float | None = None
    revisit_count: int = 0
    answer_changed: bool = False
    marked_after_seconds: float | None = None


class ResultOut(BaseModel):
    session_id: str
    state: str
    submitted_at: str | None
    score: ScoreOut
    per_question: list[PerQuestionResult]
    release_version: str
    blueprint_version: str


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------

class FormulaOut(BaseModel):
    text: str


class ConceptSummaryOut(BaseModel):
    id: str
    title: str
    skill_id: str


class ConceptExampleOut(BaseModel):
    prompt: str
    options: dict[str, str] = {}
    answer: str | None = None
    explanation: str = ""
    source: dict[str, Any] | None = None


class ConceptMediaOut(BaseModel):
    image_id: str
    source: dict[str, Any] | None = None


class ConceptCodeBlockOut(BaseModel):
    language: str
    code: str
    source: dict[str, Any] | None = None


class ConceptOut(BaseModel):
    id: str
    skill_id: str
    title: str
    summary: str
    formulas: list[str] = []
    code_blocks: list[ConceptCodeBlockOut] = []
    examples: list[ConceptExampleOut] = []
    media: list[ConceptMediaOut] = []
    common_mistakes: list[str] = []
    related_families: list[str] = []
    source_decks: list[dict[str, Any]] = []


class MediaOut(BaseModel):
    image_id: str
    mime: str
    data_base64: str


class FlashcardOut(BaseModel):
    id: str
    skill_id: str
    front: str
    back: str
    kind: str = "rule"
    source: dict[str, Any] | None = None


class FlashcardIntervalsOut(BaseModel):
    """What each grading button schedules, humanized ('10 min', '2 d')."""

    again: str
    good: str
    easy: str


class FlashcardSessionCardOut(FlashcardOut):
    state: str          # new | learning | review | strong
    due: bool
    reps: int
    intervals: FlashcardIntervalsOut


class FlashcardReviewOut(BaseModel):
    accepted: int
    due_at: str
    interval_days: float


class FlashcardDeckOut(BaseModel):
    topic_id: str
    topic_name: str
    bucket_name: str
    total_cards: int
    due_cards: int
    new_cards: int
    strong_cards: int
    coverage: float | None = None


class FlashcardSkillStatsOut(BaseModel):
    skill_id: str
    skill_name: str
    topic_id: str | None = None
    topic_name: str | None = None
    total_cards: int
    seen_cards: int
    coverage: float | None = None


class TopicSkillOut(BaseModel):
    id: str
    name: str


class TopicOut(BaseModel):
    id: str
    name: str
    skills: list[TopicSkillOut] = []


class BucketOut(BaseModel):
    id: str
    name: str
    topics: list[TopicOut]


class TaxonomyOut(BaseModel):
    buckets: list[BucketOut]


# ---------------------------------------------------------------------------
# History & insights
# ---------------------------------------------------------------------------

class HistoryTestOut(BaseModel):
    session_id: str
    submitted_at: str | None
    created_at: str
    state: str
    question_count: int
    duration_seconds: int | None = None
    correct: int | None = None
    accuracy: float | None = None


class TestDetailQuestionOut(BaseModel):
    position: int
    prompt: str
    options: dict[str, str]
    family_id: str
    skill_id: str
    skill_name: str
    bucket_id: str
    topic_id: str
    topic_name: str
    difficulty: str
    concept_id: str
    answered: bool
    chosen: str | None = None
    correct_option: str | None = None
    is_correct: bool | None = None
    explanation: str | None = None
    marked: bool
    dwell_seconds: float | None = None
    personal_median_seconds: float | None = None
    pace_vs_personal: float | None = None
    revisit_count: int = 0
    marked_after_seconds: float | None = None
    marked_at_view: bool = False


class TestDetailOut(BaseModel):
    session_id: str
    state: str
    created_at: str
    submitted_at: str | None
    question_count: int
    duration_seconds: int
    release_version: str
    blueprint_version: str
    finalized: bool
    score: ScoreOut | None = None
    questions: list[TestDetailQuestionOut]


class HistoryLearningOut(BaseModel):
    concept_id: str
    title: str
    viewed_at: str


class HistoryFlashcardOut(BaseModel):
    flashcard_id: str
    action: str
    reviewed_at: str


class HistoryOut(BaseModel):
    tests: list[HistoryTestOut]
    learning: list[HistoryLearningOut]
    flashcards: list[HistoryFlashcardOut]


class SkillInsightOut(BaseModel):
    skill_id: str
    skill_name: str
    topic_id: str | None = None
    topic_name: str | None = None
    concept_id: str
    attempts: int
    correct: int
    accuracy: float | None
    median_dwell_seconds: float | None = None
    marked_rate: float | None = None
    status: str
    ui_group: str


class InsightsOut(BaseModel):
    skills: list[SkillInsightOut]


class HealthOut(BaseModel):
    status: str
    app: str
    version: str


class ReleaseInfoOut(BaseModel):
    release_id: str
    version: str
    generated_at: str | None
    source: str | None
    concept_count: int
    flashcard_count: int
    family_count: int
