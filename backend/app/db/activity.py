"""Runtime-store queries: flashcard reviews and views, concept views."""
from __future__ import annotations

import sqlite3
from typing import Any

from .connection import db
from .timeutil import iso, utcnow


def insert_flashcard_review(session_key: str, release_id: str, release_version: str, action: str) -> None:
    with db.write() as conn:
        conn.execute(
            """
            INSERT INTO flashcard_reviews (session_key, release_id, release_version, action, reviewed_at)
            VALUES (?,?,?,?,?)
            """,
            (session_key, release_id, release_version, action, iso(utcnow())),
        )


def recent_flashcard_reviews(limit: int = 20) -> list[sqlite3.Row]:
    with db.read() as conn:
        rows = conn.execute(
            "SELECT * FROM flashcard_reviews ORDER BY reviewed_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return rows


# --- SRS schedule state (one row per reviewed card; absent row = new card) ---


def get_schedule_rows(flashcard_ids: list[str]) -> dict[str, sqlite3.Row]:
    if not flashcard_ids:
        return {}
    placeholders = ",".join("?" for _ in flashcard_ids)
    with db.read() as conn:
        rows = conn.execute(
            f"SELECT * FROM flashcard_schedule WHERE flashcard_id IN ({placeholders})",
            flashcard_ids,
        ).fetchall()
    return {r["flashcard_id"]: r for r in rows}


def upsert_schedule(flashcard_id: str, *, ease: float, interval_days: float,
                    due_at: str, reps: int, lapses: int) -> None:
    with db.write() as conn:
        conn.execute(
            """
            INSERT INTO flashcard_schedule
                (flashcard_id, ease, interval_days, due_at, reps, lapses, last_rated_at)
            VALUES (?,?,?,?,?,?,?)
            ON CONFLICT(flashcard_id) DO UPDATE SET
                ease = excluded.ease,
                interval_days = excluded.interval_days,
                due_at = excluded.due_at,
                reps = excluded.reps,
                lapses = excluded.lapses,
                last_rated_at = excluded.last_rated_at
            """,
            (flashcard_id, ease, interval_days, due_at, reps, lapses, iso(utcnow())),
        )


def all_schedule() -> dict[str, dict[str, Any]]:
    with db.read() as conn:
        rows = conn.execute("SELECT * FROM flashcard_schedule").fetchall()
    return {
        r["flashcard_id"]: {
            "ease": r["ease"], "interval_days": r["interval_days"], "due_at": r["due_at"],
            "reps": r["reps"], "lapses": r["lapses"],
        }
        for r in rows
    }
