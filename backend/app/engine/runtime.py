"""Transactional question serving, answering and interaction recording."""
from __future__ import annotations

import json
import secrets
import sqlite3
from contextlib import contextmanager
from typing import Any, Iterator

from .. import db
from .errors import NotFoundError, TestFlowError
from .scoring import compute_score


def _owned_session(conn: sqlite3.Connection, session_id: str, learner: str) -> sqlite3.Row:
    session = conn.execute("SELECT * FROM test_sessions WHERE id=?", (session_id,)).fetchone()
    if session is None or session["learner"] != learner:
        raise NotFoundError("session not found")
    return session


def _active_error(conn: sqlite3.Connection, session: sqlite3.Row) -> TestFlowError | None:
    if session["state"] == "active":
        if db.utcnow() < db.parse_iso(session["deadline_at"]):
            return None
        score = compute_score(session, conn)
        db.finalize_session(session["id"], score, "expired", conn=conn)
        return TestFlowError("expired", "this test session has expired")
    if session["state"] == "expired":
        return TestFlowError("expired", "this test session has expired")
    return TestFlowError("invalid_state", f"session is {session['state']}, not active")


@contextmanager
def _active_session(session_id: str, learner: str) -> Iterator[tuple[sqlite3.Connection, sqlite3.Row]]:
    with db.db.write() as conn:
        session = _owned_session(conn, session_id, learner)
        error = _active_error(conn, session)
        if error is None:
            yield conn, session
    # Raising inside the transaction would roll back lazy expiry (#26).
    if error is not None:
        raise error


def _question(conn: sqlite3.Connection, session_id: str, position: int) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM session_questions WHERE session_id=? AND position=?",
                       (session_id, position)).fetchone()
    if row is None:
        raise NotFoundError("question position not found")
    return row


def _serve(conn: sqlite3.Connection, session: sqlite3.Row, row: sqlite3.Row) -> dict[str, Any]:
    session_id, position = session["id"], row["position"]
    public = json.loads(row["public_json"])
    new_ticket = secrets.token_urlsafe(24)
    public["ticket"] = new_ticket
    conn.execute("UPDATE session_questions SET ticket=? WHERE session_id=? AND position=?",
                 (new_ticket, session_id, position))
    now = db.iso(db.utcnow())
    conn.execute(
        """INSERT INTO question_timing (session_id, position, first_shown_at, last_active_at)
           VALUES (?,?,?,?)
           ON CONFLICT(session_id, position) DO UPDATE SET
             revisit_count = revisit_count + 1, last_active_at = excluded.last_active_at""",
        (session_id, position, now, now),
    )
    return {"session_id": session_id, "total_questions": session["question_count"],
            **public, "position": position, "answered": bool(row["answered"]),
            "marked": bool(row["marked"])}


def get_current_question(session_id: str, learner: str) -> dict[str, Any]:
    with _active_session(session_id, learner) as (conn, session):
        rows = conn.execute("SELECT * FROM session_questions WHERE session_id=? ORDER BY position",
                            (session_id,)).fetchall()
        current = next((r for r in rows if not r["answered"]), rows[-1] if rows else None)
        if current is None:
            raise NotFoundError("session has no questions")
        return _serve(conn, session, current)


def get_question_at(session_id: str, position: int, learner: str) -> dict[str, Any]:
    with _active_session(session_id, learner) as (conn, session):
        return _serve(conn, session, _question(conn, session_id, position))


def record_dwell(session_id: str, position: int, learner: str, seconds: float,
                 kind: str = "active") -> None:
    """Add a bounded segment only while active; client values never affect score."""
    with _active_session(session_id, learner) as (conn, session):
        _question(conn, session_id, position)
        kind = kind if kind in ("active", "hidden", "unfocused") else "active"
        seconds = max(0.0, min(float(seconds), 3600.0))
        now = db.iso(db.utcnow())
        conn.execute(
            "INSERT INTO question_dwell_segments (session_id, position, started_at, seconds, kind) VALUES (?,?,?,?,?)",
            (session_id, position, now, seconds, kind),
        )
        if kind == "active":
            conn.execute(
                """INSERT INTO question_timing (session_id, position, first_shown_at, last_active_at, dwell_seconds)
                   VALUES (?,?,?,?,?)
                   ON CONFLICT(session_id, position) DO UPDATE SET
                     dwell_seconds = dwell_seconds + excluded.dwell_seconds,
                     last_active_at = excluded.last_active_at""",
                (session_id, position, now, now, seconds),
            )


def record_events(session_id: str, learner: str,
                  rows: list[tuple[str, int | None, str, float | None, str, str]]) -> int:
    with _active_session(session_id, learner) as (conn, session):
        conn.executemany(
            "INSERT INTO client_events (session_id, position, event_type, client_time, server_time, payload) VALUES (?,?,?,?,?,?)",
            rows,
        )
    return len(rows)


def mark_question(session_id: str, position: int, marked: bool, learner: str) -> None:
    with _active_session(session_id, learner) as (conn, session):
        _question(conn, session_id, position)
        conn.execute("UPDATE session_questions SET marked=? WHERE session_id=? AND position=?",
                     (int(marked), session_id, position))
        # Preserve the first mark time, and reflect unmarking in the timing row.
        conn.execute(
            """UPDATE question_timing SET marked=?,
               marked_after_seconds = CASE WHEN ?=1 AND marked_after_seconds IS NULL
                                           THEN dwell_seconds ELSE marked_after_seconds END
               WHERE session_id=? AND position=?""",
            (int(marked), int(marked), session_id, position),
        )


def submit_answer(session_id: str, position: int, ticket: str, option: str,
                  learner: str, idempotency_key: str | None = None) -> dict[str, Any]:
    with db.db.write() as conn:
        session = _owned_session(conn, session_id, learner)
        if idempotency_key is not None:
            if not 1 <= len(idempotency_key) <= 128:
                raise TestFlowError("invalid_idempotency_key", "invalid answer retry key")
            receipt = conn.execute(
                "SELECT * FROM answer_receipts WHERE session_id=? AND idempotency_key=?",
                (session_id, idempotency_key),
            ).fetchone()
            if receipt is not None:
                if (receipt["position"], receipt["ticket"], receipt["option"]) != (position, ticket, option):
                    raise TestFlowError("idempotency_conflict", "answer retry key was already used for a different request")
                # A receipt can be read after finalization, but never rewrites an answer (#27).
                return json.loads(receipt["response_json"])
        error = _active_error(conn, session)
        if error is None:
            row = _question(conn, session_id, position)
            if option not in ("a", "b", "c", "d"):
                raise TestFlowError("invalid_option", "unknown option id")
            if ticket != row["ticket"]:
                raise TestFlowError("stale_ticket", "question ticket does not match the current question")
            correct = json.loads(row["question_json"])["correct_option"] == option
            now = db.iso(db.utcnow())
            conn.execute(
                """UPDATE session_questions SET answered=1, answer_option=?, is_correct=?, answered_at=?
                   WHERE session_id=? AND position=?""",
                (option, int(correct), now, session_id, position),
            )
            if row["answered"] and row["answer_option"] != option:
                conn.execute("UPDATE question_timing SET answer_changed=1 WHERE session_id=? AND position=?",
                             (session_id, position))
            remaining = conn.execute(
                "SELECT COUNT(*) FROM session_questions WHERE session_id=? AND answered=0", (session_id,),
            ).fetchone()[0]
            result = {"accepted": True, "remaining": remaining}
            if idempotency_key is not None:
                conn.execute(
                    """INSERT INTO answer_receipts
                       (session_id, idempotency_key, position, ticket, option, response_json, created_at)
                       VALUES (?,?,?,?,?,?,?)""",
                    (session_id, idempotency_key, position, ticket, option, json.dumps(result), now),
                )
    if error is not None:
        raise error
    return result
