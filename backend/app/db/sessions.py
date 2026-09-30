"""Runtime-store queries: sessions, questions, answers, scores."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Any

from .connection import db
from .timeutil import iso, utcnow


def create_session(
    *,
    session_id: str,
    learner: str,
    question_count: int,
    duration_seconds: int,
    seed: str,
    blueprint_version: str,
    release_id: str,
    release_version: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or utcnow()
    deadline = now + timedelta(seconds=duration_seconds)
    with db.write() as conn:
        conn.execute(
            """
            INSERT INTO test_sessions
              (id, learner, state, question_count, duration_seconds, seed,
               blueprint_version, release_id, release_version,
               created_at, started_at, deadline_at, expires_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                session_id, learner, "active", question_count, duration_seconds, seed,
                blueprint_version, release_id, release_version,
                iso(now), iso(now), iso(deadline), iso(deadline),
            ),
        )
    return {
        "id": session_id,
        "state": "active",
        "started_at": iso(now),
        "deadline_at": iso(deadline),
    }


def get_session(session_id: str) -> sqlite3.Row | None:
    with db.read() as conn:
        return conn.execute("SELECT * FROM test_sessions WHERE id=?", (session_id,)).fetchone()


def get_question_row(session_id: str, position: int) -> sqlite3.Row | None:
    with db.read() as conn:
        return conn.execute(
            "SELECT * FROM session_questions WHERE session_id=? AND position=?",
            (session_id, position),
        ).fetchone()


def list_questions(session_id: str) -> list[sqlite3.Row]:
    with db.read() as conn:
        return conn.execute(
            "SELECT * FROM session_questions WHERE session_id=? ORDER BY position",
            (session_id,),
        ).fetchall()


def count_unanswered(session_id: str) -> int:
    with db.read() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM session_questions WHERE session_id=? AND answered=0",
            (session_id,),
        ).fetchone()
    return row["n"] if row else 0


def get_score(session_id: str) -> sqlite3.Row | None:
    with db.read() as conn:
        return conn.execute("SELECT * FROM score_summaries WHERE session_id=?", (session_id,)).fetchone()


def set_session_state(session_id: str, state: str, *, extra: dict[str, Any] | None = None) -> None:
    with db.write() as conn:
        if extra:
            sets = ", ".join(f"{k}=?" for k in extra)
            conn.execute(
                f"UPDATE test_sessions SET state=?, {sets} WHERE id=?",
                (state, *extra.values(), session_id),
            )
        else:
            conn.execute("UPDATE test_sessions SET state=? WHERE id=?", (state, session_id))


def submit_answer(session_id: str, position: int, option: str) -> None:
    with db.write() as conn:
        conn.execute(
            """
            UPDATE session_questions
            SET answered=1, answer_option=?, answered_at=?
            WHERE session_id=? AND position=?
            """,
            (option, iso(utcnow()), session_id, position),
        )


def set_mark(session_id: str, position: int, marked: bool) -> None:
    with db.write() as conn:
        conn.execute(
            "UPDATE session_questions SET marked=? WHERE session_id=? AND position=?",
            (1 if marked else 0, session_id, position),
        )


def finalize_session(
    session_id: str,
    score: dict[str, Any],
    final_state: str = "submitted",
) -> dict[str, Any] | None:
    """Atomically finalize a session (submitted or expired) and persist the score.

    Returns None if the session was already terminal (duplicate finalization).
    """
    assert final_state in ("submitted", "expired")
    with db.write() as conn:
        row = conn.execute("SELECT state FROM test_sessions WHERE id=?", (session_id,)).fetchone()
        if row is None:
            return None
        if row["state"] in ("submitted", "expired"):
            return None
        now = utcnow()
        conn.execute(
            "UPDATE test_sessions SET state=?, submitted_at=? WHERE id=?",
            (final_state, iso(now), session_id),
        )
        conn.execute(
            """
            INSERT INTO score_summaries
              (session_id, total_questions, correct, incorrect, unanswered, accuracy,
               duration_seconds, finalized_at, per_question, release_version,
               blueprint_version, seed)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                session_id, score["total_questions"], score["correct"], score["incorrect"],
                score["unanswered"], score["accuracy"], score["duration_seconds"],
                iso(now), json.dumps(score["per_question"]),
                score["release_version"], score["blueprint_version"], score["seed"],
            ),
        )
    return score


def insert_events(rows: list[tuple[str, int | None, str, float | None, str, str]]) -> int:
    with db.write() as conn:
        conn.executemany(
            """
            INSERT INTO client_events
              (session_id, position, event_type, client_time, server_time, payload)
            VALUES (?,?,?,?,?,?)
            """,
            rows,
        )
    return len(rows)
