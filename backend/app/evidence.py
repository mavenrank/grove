"""Skill evidence: status assignment and timing context (handoff §9).

The handoff's evidence statuses (unseen, insufficient_evidence, developing,
slow_but_accurate, inaccurate, inconsistent, strong, needs_review) are the
underlying model. The UI additionally groups them into a four-step practice
banding so a learner always has a simple next action:

    strong            → keep it warm
    on_track          → keep practising
    needs_practice    → review the concept before the next test
    weak              → relearn from the Learn module first
    low_evidence      → not enough comparable attempts yet
    unseen            → no attempts at all

Status is descriptive evidence, never a permanent aptitude label; it is
recomputed on demand and only from finalized sessions.
"""
from __future__ import annotations

import json
import sqlite3
from typing import Any

from . import db
from .content_engine.releases import family_skill_map
from .content_engine.taxonomy import skill_name, topic_of_skill

MIN_ATTEMPTS = 5  # handoff §9: fewer than five comparable attempts → low evidence

UI_GROUPS: dict[str, str] = {
    "strong": "strong",
    "slow_but_accurate": "on_track",
    "developing": "needs_practice",
    "inconsistent": "needs_practice",
    "inaccurate": "weak",
    "needs_review": "weak",
    "insufficient_evidence": "low_evidence",
    "unseen": "unseen",
}

UI_GROUP_LABELS: dict[str, str] = {
    "strong": "Strong",
    "on_track": "On track",
    "needs_practice": "Needs practice",
    "weak": "Weak — relearn first",
    "low_evidence": "Not enough evidence",
    "unseen": "Not started",
}


def status_for(accuracy: float | None, median_s: float | None, personal_baseline_s: float | None,
               consistency: float | None, attempts: int) -> str:
    """Handoff §9 status rules, in words:

      - few attempts            → insufficient_evidence
      - repeated wrong answers  → inaccurate
      - correct but slow        → slow_but_accurate
      - erratic consistency     → inconsistent
      - correct + efficient     → strong
      - the rest                → developing
    """
    if attempts == 0:
        return "unseen"
    if attempts < MIN_ATTEMPTS or accuracy is None:
        return "insufficient_evidence"
    if accuracy < 0.5:
        return "inaccurate"
    slow = (personal_baseline_s is not None and median_s is not None
            and median_s > personal_baseline_s * 1.5)
    if accuracy >= 0.8 and slow:
        return "slow_but_accurate"
    if accuracy >= 0.8 and (consistency is None or consistency >= 0.6):
        return "strong"
    if accuracy >= 0.8:
        return "inconsistent"
    return "developing"


def _per_skill_timing(conn: sqlite3.Connection) -> dict[str, dict[str, list[float]]]:
    """Dwell seconds per skill, joined from timings + question plans."""
    rows = conn.execute(
        """
        SELECT q.family_id, q.is_correct, t.dwell_seconds
        FROM session_questions q
        JOIN test_sessions s ON s.id = q.session_id
        LEFT JOIN question_timing t ON t.session_id = q.session_id AND t.position = q.position
        WHERE s.state IN ('submitted', 'expired')
        """
    ).fetchall()
    from .content_engine.releases import load_release
    family_skill = family_skill_map()
    out: dict[str, dict[str, list[float]]] = {}
    for r in rows:
        skill = family_skill.get(r["family_id"])
        if not skill:
            continue
        bucket = out.setdefault(skill, {"dwell": [], "correct_dwell": []})
        if r["dwell_seconds"] is not None and r["dwell_seconds"] > 0:
            bucket["dwell"].append(float(r["dwell_seconds"]))
            if r["is_correct"] == 1:
                bucket["correct_dwell"].append(float(r["dwell_seconds"]))
    return out


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    vs = sorted(values)
    n = len(vs)
    mid = n // 2
    return vs[mid] if n % 2 else (vs[mid - 1] + vs[mid]) / 2


def skill_evidence(limit: int = 200) -> list[dict[str, Any]]:
    """Per-skill evidence rows with status, UI group, and Learn link target."""
    with db.db.read() as conn:
        rows = conn.execute(
            """
            SELECT q.family_id, q.is_correct, q.marked
            FROM session_questions q
            JOIN test_sessions s ON s.id = q.session_id
            WHERE s.state IN ('submitted', 'expired')
            """
        ).fetchall()
        timing = _per_skill_timing(conn)

        # personal pace baseline: median dwell of correct answers across all skills
        all_correct = [t for b in timing.values() for t in b["correct_dwell"]]
        baseline = _median(all_correct)

        from .content_engine.releases import load_release
        release = load_release()
        family_skill = family_skill_map()

        agg: dict[str, dict[str, Any]] = {}
        for r in rows:
            skill = family_skill.get(r["family_id"])
            if not skill:
                continue
            a = agg.setdefault(skill, {"attempts": 0, "correct": 0, "marked": 0,
                                       "dwell": [], "correct_dwell": [], "streak": [], "last3": []})
            a["attempts"] += 1
            if r["is_correct"] is not None and r["is_correct"] == 1:
                a["correct"] += 1
                a["streak"].append(1)
                a["last3"].append(1)
            else:
                a["streak"].append(0)
                a["last3"].append(0)
            if r["marked"]:
                a["marked"] += 1

    out: list[dict[str, Any]] = []
    for skill_id in set(agg) | set(timing):
        a = agg.get(skill_id, {"attempts": 0, "correct": 0, "marked": 0,
                               "streak": [], "last3": []})
        t = timing.get(skill_id, {"dwell": [], "correct_dwell": []})
        attempts = a["attempts"]
        accuracy = (a["correct"] / attempts) if attempts else None
        consistency = None
        if attempts >= 2:
            last3 = a["last3"][-3:]
            consistency = sum(last3) / len(last3)
        median_dwell = _median(t["dwell"])
        status = status_for(accuracy, median_dwell, baseline, consistency, attempts)
        topic = topic_of_skill(skill_id)
        out.append({
            "skill_id": skill_id,
            "skill_name": skill_name(skill_id),
            "topic_id": topic.id if topic else None,
            "topic_name": topic.name if topic else None,
            "concept_id": f"concept.{skill_id}",
            "attempts": attempts,
            "correct": a["correct"],
            "accuracy": round(accuracy, 4) if accuracy is not None else None,
            "median_dwell_seconds": round(median_dwell, 1) if median_dwell is not None else None,
            "marked_rate": round(a["marked"] / attempts, 4) if attempts else None,
            "status": status,
            "ui_group": UI_GROUPS.get(status, "low_evidence"),
        })
    group_rank = {"weak": 0, "needs_practice": 1, "low_evidence": 2, "on_track": 3,
                  "unseen": 4, "strong": 5}
    out.sort(key=lambda x: (group_rank.get(x["ui_group"], 9), -(x["attempts"])))
    return out[:limit]


def flashcard_skill_stats() -> list[dict[str, Any]]:
    """Flashcard coverage per skill: total cards vs how many the learner has seen."""
    from .content_engine.releases import load_release
    release = load_release()
    totals: dict[str, int] = {}
    for fc in release.get("flashcards", []):
        totals[fc.get("skill_id", "unknown")] = totals.get(fc.get("skill_id", "unknown"), 0) + 1
    with db.db.read() as conn:
        rows = conn.execute(
            "SELECT skill_id, COUNT(DISTINCT flashcard_id) AS seen FROM flashcard_views GROUP BY skill_id"
        ).fetchall()
    seen = {r["skill_id"]: r["seen"] for r in rows}
    out = []
    for skill_id, total in sorted(totals.items()):
        s = seen.get(skill_id, 0)
        topic = topic_of_skill(skill_id)
        out.append({
            "skill_id": skill_id,
            "skill_name": skill_name(skill_id),
            "topic_id": topic.id if topic else None,
            "topic_name": topic.name if topic else None,
            "total_cards": total,
            "seen_cards": s,
            "coverage": round(s / total, 4) if total else None,
        })
    return out
