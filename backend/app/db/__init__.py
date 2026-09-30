"""SQLite persistence for Grove.

Decomposed modules:
  schema     — DDL (two logical stores: content + runtime)
  connection — thread-safe Database wrapper + the `db` singleton
  timeutil   — utcnow / iso / parse_iso helpers
  releases   — content-store queries (immutable releases)
  sessions   — runtime-store queries (sessions, questions, scores, events)
  activity   — runtime-store queries (flashcard + concept activity)

This module is a facade: `from . import db` (or `from app import db`) keeps
working, and every historical `db.X` attribute resolves here.
"""
from .connection import Database, db
from .schema import SCHEMA_SQL
from .timeutil import iso, parse_iso, utcnow
from .releases import import_release, latest_release
from .sessions import (
    count_unanswered,
    create_session,
    finalize_session,
    get_question_row,
    get_score,
    get_session,
    insert_events,
    list_questions,
    set_mark,
    set_session_state,
    submit_answer,
)
from .activity import (
    all_schedule,
    get_schedule_rows,
    insert_flashcard_review,
    recent_flashcard_reviews,
    upsert_schedule,
)

__all__ = [
    "Database", "db", "SCHEMA_SQL", "utcnow", "iso", "parse_iso",
    "import_release", "latest_release",
    "create_session", "get_session", "get_question_row", "list_questions",
    "count_unanswered", "get_score", "set_session_state", "submit_answer",
    "set_mark", "finalize_session", "insert_events",
    "insert_flashcard_review", "recent_flashcard_reviews",
    "get_schedule_rows", "upsert_schedule", "all_schedule",
]
