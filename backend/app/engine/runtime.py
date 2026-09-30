"""Serving questions and recording interaction timing (dwell, revisits, marks)."""
from __future__ import annotations

import json
import secrets
from typing import Any

from .. import db
from .errors import NotFoundError, TestFlowError
from .scoring import compute_score


def _ensure_active(session: Any) -> None:
    if session["state"] == "active":
        deadline = db.parse_iso(session["deadline_at"])
        if db.utcnow() > deadline:
            # expire lazily but store the partial score so history stays complete
            score = compute_score(session)
            db.finalize_session(session["id"], score, final_state="expired")
            raise TestFlowError("expired", "this test session has expired")
        return
    if session["state"] in ("submitted", "expired"):
        return  # terminal states are handled by callers that serve results
    raise TestFlowError("invalid_state", f"session is {session['state']}, not active")


def get_current_question(session_id: str, learner: str) -> dict[str, Any]:
    session = db.get_session(session_id)
    if session is None or session["learner"] != learner:
        raise NotFoundError("session not found")
    _ensure_active(session)

    # resume at the first unanswered question (learner moves via answers/review flow)
    rows = db.list_questions(session_id)
    current = next((r for r in rows if not r["answered"]), rows[-1] if rows else None)
    if current is None:
        raise NotFoundError("session has no questions")

    public = json.loads(current["public_json"])
    # ticket rotation: a fresh ticket per fetch prevents simple replay of answers
    new_ticket = secrets.token_urlsafe(24)
    public["ticket"] = new_ticket
    with db.db.write() as conn:
        conn.execute("UPDATE session_questions SET ticket=? WHERE session_id=? AND position=?",
                     (new_ticket, session_id, current["position"]))
    _stamp_question_shown(session_id, current["position"])
    return {
        "session_id": session_id,
        "position": current["position"],
        "total_questions": session["question_count"],
        **public,
    }


def get_question_at(session_id: str, position: int, learner: str) -> dict[str, Any]:
    """Navigation: fetch any question in the session (for revisit/mark-for-review UI).

    Still one allowlisted payload; still never includes the answer.
    """
    session = db.get_session(session_id)
    if session is None or session["learner"] != learner:
        raise NotFoundError("session not found")
    _ensure_active(session)
    row = db.get_question_row(session_id, position)
    if row is None:
        raise NotFoundError("question position not found")
    public = json.loads(row["public_json"])
    new_ticket = secrets.token_urlsafe(24)
    public["ticket"] = new_ticket
    with db.db.write() as conn:
        conn.execute("UPDATE session_questions SET ticket=? WHERE session_id=? AND position=?",
                     (new_ticket, session_id, position))
    _stamp_question_shown(session_id, position)
    return {
        "session_id": session_id,
        "position": position,
        "total_questions": session["question_count"],
        "answered": bool(row["answered"]),
        "marked": bool(row["marked"]),
        **public,
    }


def _stamp_question_shown(session_id: str, position: int) -> None:
    """First fetch opens the timing row; later fetches count as revisits."""
    now = db.iso(db.utcnow())
    with db.db.write() as conn:
        conn.execute(
            """
            INSERT INTO question_timing (session_id, position, first_shown_at, last_active_at)
            VALUES (?,?,?,?)
            ON CONFLICT(session_id, position) DO UPDATE SET
                revisit_count = revisit_count + 1,
                last_active_at = excluded.last_active_at
            """,
            (session_id, position, now, now),
        )


def record_dwell(session_id: str, position: int, learner: str, seconds: float,
                 kind: str = "active") -> None:
    """Store one client-reported active-dwell segment (handoff §8.7).

    Segments are additive: leaving a question and coming back later appends to
    the same row instead of restarting at zero. Values are clamped and only
    accepted while the session is active; they inform analytics, never score.
    """
    session = db.get_session(session_id)
    if session is None or session["learner"] != learner:
        raise NotFoundError("session not found")
    if session["state"] != "active":
        return  # late segments after finalization are discarded
    if kind not in ("active", "hidden", "unfocused"):
        kind = "active"
    seconds = max(0.0, min(float(seconds), 3600.0))
    row = db.get_question_row(session_id, position)
    if row is None:
        raise NotFoundError("question position not found")
    now = db.iso(db.utcnow())
    with db.db.write() as conn:
        conn.execute(
            "INSERT INTO question_dwell_segments (session_id, position, started_at, seconds, kind) VALUES (?,?,?,?,?)",
            (session_id, position, now, seconds, kind),
        )
        if kind == "active":
            conn.execute(
                """
                INSERT INTO question_timing (session_id, position, first_shown_at, last_active_at, dwell_seconds)
                VALUES (?,?,?,?,?)
                ON CONFLICT(session_id, position) DO UPDATE SET
                    dwell_seconds = dwell_seconds + excluded.dwell_seconds,
                    last_active_at = excluded.last_active_at
                """,
                (session_id, position, now, now, seconds),
            )


def mark_question(session_id: str, position: int, marked: bool, learner: str) -> None:
    session = db.get_session(session_id)
    if session is None or session["learner"] != learner:
        raise NotFoundError("session not found")
    _ensure_active(session)
    row = db.get_question_row(session_id, position)
    if row is None:
        raise NotFoundError("question position not found")
    db.set_mark(session_id, position, marked)
    if marked:
        # capture how much active time had elapsed when the learner gave up on
        # this question and flagged it for later (server-known dwell)
        with db.db.read() as conn:
            trow = conn.execute(
                "SELECT dwell_seconds FROM question_timing WHERE session_id=? AND position=?",
                (session_id, position),
            ).fetchone()
        elapsed = float(trow["dwell_seconds"]) if trow and trow["dwell_seconds"] is not None else 0.0
        with db.db.write() as conn:
            conn.execute(
                """
                UPDATE question_timing
                SET marked_after_seconds = ?, marked = 1
                WHERE session_id=? AND position=?
                  AND (marked_after_seconds IS NULL OR marked_after_seconds = 0)
                """,
                (elapsed, session_id, position),
            )


def submit_answer(session_id: str, position: int, ticket: str, option: str,
                  learner: str, idempotency_key: str | None = None) -> dict[str, Any]:
    session = db.get_session(session_id)
    if session is None or session["learner"] != learner:
        raise NotFoundError("session not found")
    if session["state"] == "submitted":
        raise TestFlowError("invalid_state", "session already finalized")
    _ensure_active(session)

    row = db.get_question_row(session_id, position)
    if row is None:
        raise NotFoundError("question position not found")
    if option not in ("a", "b", "c", "d"):
        raise TestFlowError("invalid_option", "unknown option id")
    if ticket != row["ticket"]:
        raise TestFlowError("stale_ticket", "question ticket does not match the current question")

    private = json.loads(row["question_json"])
    correct = private["correct_option"] == option

    db.submit_answer(session_id, position, option)
    # NOTE: correctness is recorded but never returned to the client.
    with db.db.write() as conn:
        conn.execute("UPDATE session_questions SET is_correct=? WHERE session_id=? AND position=?",
                     (1 if correct else 0, session_id, position))

    remaining = db.count_unanswered(session_id)
    return {"accepted": True, "remaining": remaining}
