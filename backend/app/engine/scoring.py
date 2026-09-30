"""Scoring and finalization: compute the score server-side, atomically."""
from __future__ import annotations

import json
from typing import Any

from .. import db
from .errors import NotFoundError, TestFlowError


def compute_score(session: Any) -> dict[str, Any]:
    rows = db.list_questions(session["id"])
    with db.db.read() as conn:
        timing_rows = conn.execute(
            "SELECT * FROM question_timing WHERE session_id=?", (session["id"],)
        ).fetchall()
    timing = {t["position"]: t for t in timing_rows}
    per_question = []
    correct = 0
    answered = 0
    for row in rows:
        private = json.loads(row["question_json"])
        got = row["answer_option"]
        is_correct = row["is_correct"] if got is not None else None
        if got is not None:
            answered += 1
            if is_correct:
                correct += 1
        t = timing.get(row["position"])
        from ..content_engine.taxonomy import topic_of_skill
        skill_id = private["skill_id"]
        topic = topic_of_skill(skill_id)
        per_question.append({
            "position": row["position"],
            "family_id": row["family_id"],
            "skill_id": skill_id,
            "bucket_id": (topic.id.split(".")[0] if topic else skill_id.split(".")[0]),
            "topic_id": topic.id if topic else skill_id.rsplit(".", 1)[0],
            "topic_name": topic.name if topic else skill_id.replace(".", " "),
            "difficulty": private["difficulty"],
            "answered": got is not None,
            "chosen": got,
            "correct_option": private["correct_option"],
            "is_correct": bool(is_correct) if got is not None else False,
            "explanation": private["explanation"],
            "marked": bool(row["marked"]),
            "dwell_seconds": round(float(t["dwell_seconds"]), 1) if t and t["dwell_seconds"] is not None else None,
            "revisit_count": int(t["revisit_count"]) if t else 0,
            "answer_changed": bool(t["answer_changed"]) if t else False,
            "marked_after_seconds": (round(float(t["marked_after_seconds"]), 1)
                                      if t and t["marked_after_seconds"] is not None else None),
        })
    total = session["question_count"]
    return {
        "total_questions": total,
        "correct": correct,
        "incorrect": answered - correct,
        "unanswered": total - answered,
        "accuracy": round(correct / total, 4) if total else 0.0,
        "duration_seconds": session["duration_seconds"],
        "per_question": per_question,
        "release_version": session["release_version"],
        "blueprint_version": session["blueprint_version"],
        "seed": session["seed"],
    }


def finish_session(session_id: str, learner: str) -> dict[str, Any]:
    session = db.get_session(session_id)
    if session is None or session["learner"] != learner:
        raise NotFoundError("session not found")

    deadline = db.parse_iso(session["deadline_at"])
    if session["state"] == "submitted":
        # duplicate finalization is rejected (handoff §8.5)
        raise TestFlowError("already_finalized", "this session has already been finalized")
    if session["state"] == "expired":
        existing = db.get_score(session_id)
        if existing is None:
            raise TestFlowError("invalid_state", "expired session has no stored score")
        return _result_payload(session_id)
    if session["state"] != "active":
        raise TestFlowError("invalid_state", f"cannot finish a session in state {session['state']}")

    if db.utcnow() > deadline:
        # deadline passed before submission: finalize as expired with partial score
        score = compute_score(session)
        if db.finalize_session(session_id, score, final_state="expired") is None:
            raise TestFlowError("finalize_failed", "could not finalize session")
        return _result_payload(session_id)

    score = compute_score(session)
    if db.finalize_session(session_id, score) is None:
        raise TestFlowError("finalize_failed", "could not finalize session")
    return _result_payload(session_id)


def _result_payload(session_id: str) -> dict[str, Any]:
    session = db.get_session(session_id)
    score_row = db.get_score(session_id)
    if score_row is None:
        raise NotFoundError("score not found")
    per_question = json.loads(score_row["per_question"])
    return {
        "session_id": session_id,
        "state": session["state"],
        "submitted_at": session["submitted_at"],
        "score": {
            "total_questions": score_row["total_questions"],
            "correct": score_row["correct"],
            "incorrect": score_row["incorrect"],
            "unanswered": score_row["unanswered"],
            "accuracy": score_row["accuracy"],
        },
        "per_question": per_question,
        "release_version": score_row["release_version"],
        "blueprint_version": score_row["blueprint_version"],
    }


def get_result(session_id: str, learner: str) -> dict[str, Any]:
    session = db.get_session(session_id)
    if session is None or session["learner"] != learner:
        raise NotFoundError("session not found")
    if session["state"] not in ("submitted", "expired"):
        raise TestFlowError("not_finalized", "results are only available after finalization")
    if db.get_score(session_id) is None:
        raise TestFlowError("not_finalized", "results are only available after finalization")
    return _result_payload(session_id)
