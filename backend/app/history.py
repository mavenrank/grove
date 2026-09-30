"""History and evidence queries (handoff §17 history endpoints).

The compact history list stays; a per-test detail query now exposes the
future-detailed-evidence view from §9: per-question active dwell, revisit
counts, marks, and the learner's personal median for the same skill+family
so "am I slow on this?" is answerable.
"""
from __future__ import annotations

import json
import sqlite3
from typing import Any

from . import db
from .content_engine.releases import family_skill_map
from .content_engine.taxonomy import skill_name, topic_of_skill
from .evidence import _median
from .engine.errors import TestFlowError


def recent_tests(limit: int = 50) -> list[dict[str, Any]]:
    with db.db.read() as conn:
        rows = conn.execute(
            """
            SELECT s.id AS session_id, s.created_at, s.submitted_at, s.state, s.question_count,
                   s.duration_seconds, sc.correct, sc.accuracy
            FROM test_sessions s
            LEFT JOIN score_summaries sc ON sc.session_id = s.id
            ORDER BY s.created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def test_detail(session_id: str) -> dict[str, Any] | None:
    """Everything the Test detail view needs, with answer release rules applied."""
    with db.db.read() as conn:
        s = conn.execute("SELECT * FROM test_sessions WHERE id=?", (session_id,)).fetchone()
        if s is None:
            return None
        score = conn.execute("SELECT * FROM score_summaries WHERE session_id=?", (session_id,)).fetchone()
        finalized = s["state"] in ("submitted", "expired") and score is not None
        # History must not bulk expose the contents of an active assessment (#28).
        if not finalized:
            raise TestFlowError("not_finalized", "test details are only available after finalization")

        rows = conn.execute(
            "SELECT * FROM session_questions WHERE session_id=? ORDER BY position",
            (session_id,),
        ).fetchall()
        timings = {
            t["position"]: t
            for t in conn.execute(
                "SELECT * FROM question_timing WHERE session_id=?", (session_id,)
            ).fetchall()
        }
        # personal medians per (skill, family) from ALL finalized sessions
        medians = _skill_family_medians(conn)

    family_skill = family_skill_map()
    per_question_json = json.loads(score["per_question"]) if score else []
    by_pos = {pq["position"]: pq for pq in per_question_json}

    questions: list[dict[str, Any]] = []
    for r in rows:
        private = json.loads(r["question_json"])
        skill_id = private["skill_id"]
        topic = topic_of_skill(skill_id)
        pq = by_pos.get(r["position"], {})
        t = timings.get(r["position"])
        dwell = float(t["dwell_seconds"]) if t and t["dwell_seconds"] is not None else None
        personal_median = medians.get((skill_id, r["family_id"]))
        answered = r["answered"] == 1
        # release policy: answers/explanations only after finalization (handoff §8.4)
        questions.append({
            "position": r["position"],
            "prompt": private["prompt"],
            "options": {o["id"]: o["text"] for o in private["options"]},
            "family_id": r["family_id"],
            "skill_id": skill_id,
            "skill_name": skill_name(skill_id),
            "bucket_id": (topic.id.split(".")[0] if topic else skill_id.split(".")[0]),
            "topic_id": topic.id if topic else skill_id.rsplit(".", 1)[0],
            "topic_name": topic.name if topic else skill_id.replace(".", " "),
            "difficulty": private["difficulty"],
            "concept_id": f"concept.{skill_id}",
            "answered": answered,
            "chosen": r["answer_option"] if finalized else None,
            "correct_option": (private.get("correct_option") if finalized else None),
            "is_correct": (bool(r["is_correct"]) if finalized and r["is_correct"] is not None else None),
            "explanation": private.get("explanation") if finalized else None,
            "marked": bool(r["marked"]),
            "dwell_seconds": round(dwell, 1) if dwell is not None else None,
            "personal_median_seconds": round(personal_median, 1) if personal_median else None,
            "pace_vs_personal": (round(dwell / personal_median, 2)
                                 if dwell and personal_median else None),
            "revisit_count": int(t["revisit_count"]) if t else 0,
            "marked_after_seconds": (round(float(t["marked_after_seconds"]), 1)
                                     if t and t["marked_after_seconds"] is not None else None),
            "marked_at_view": bool(pq.get("marked", r["marked"])),
        })

    return {
        "session_id": session_id,
        "state": s["state"],
        "created_at": s["created_at"],
        "submitted_at": s["submitted_at"],
        "question_count": s["question_count"],
        "duration_seconds": s["duration_seconds"],
        "release_version": s["release_version"],
        "blueprint_version": s["blueprint_version"],
        "finalized": finalized,
        "score": ({
            "total_questions": score["total_questions"],
            "correct": score["correct"],
            "incorrect": score["incorrect"],
            "unanswered": score["unanswered"],
            "accuracy": score["accuracy"],
        } if score else None),
        "questions": questions,
    }


def _skill_family_medians(conn: sqlite3.Connection) -> dict[tuple[str, str], float]:
    """Median active dwell per (skill, family) across all finalized sessions."""
    rows = conn.execute(
        """
        SELECT q.family_id, t.dwell_seconds
        FROM session_questions q
        JOIN test_sessions s ON s.id = q.session_id
        JOIN question_timing t ON t.session_id = q.session_id AND t.position = q.position
        WHERE s.state IN ('submitted', 'expired') AND t.dwell_seconds > 0
        """
    ).fetchall()
    family_skill = family_skill_map()
    buckets: dict[tuple[str, str], list[float]] = {}
    for r in rows:
        skill = family_skill.get(r["family_id"])
        if not skill:
            continue
        buckets.setdefault((skill, r["family_id"]), []).append(float(r["dwell_seconds"]))
    return {k: m for k, v in buckets.items() if (m := _median(v)) is not None}


def recent_flashcards(limit: int = 20) -> list[dict[str, Any]]:
    rows = db.recent_flashcard_reviews(limit)
    return [
        {
            "flashcard_id": r["session_key"],
            "action": r["action"],
            "reviewed_at": r["reviewed_at"],
        }
        for r in rows
    ]


def record_flashcard_view(flashcard_id: str, skill_id: str,
                          release_id: str, release_version: str) -> None:
    with db.db.write() as conn:
        conn.execute(
            """
            INSERT INTO flashcard_views (flashcard_id, skill_id, release_id, release_version, viewed_at)
            VALUES (?,?,?,?,?)
            """,
            (flashcard_id, skill_id, release_id, release_version, db.iso(db.utcnow())),
        )


def record_concept_view(concept_id: str, title: str) -> None:
    with db.db.write() as conn:
        conn.execute(
            "INSERT INTO concept_views (concept_id, title, viewed_at) VALUES (?,?,?)",
            (concept_id, title, db.iso(db.utcnow())),
        )


def recent_learning(limit: int = 20) -> list[dict[str, Any]]:
    with db.db.read() as conn:
        rows = conn.execute(
            "SELECT concept_id, title, viewed_at FROM concept_views ORDER BY viewed_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]
