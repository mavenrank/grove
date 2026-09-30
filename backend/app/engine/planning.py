"""Session planning: a seeded, reproducible (family, difficulty) sequence."""
from __future__ import annotations

from typing import Any

from ..content_engine.deterministic import make_rng
from ..content_engine.releases import load_release

DIFFICULTY_MIX = {"direct": 0.5, "multi_step": 0.35, "transfer": 0.15}


def _pick_difficulty(rng, roll: float) -> str:
    if roll < DIFFICULTY_MIX["direct"]:
        return "direct"
    if roll < DIFFICULTY_MIX["direct"] + DIFFICULTY_MIX["multi_step"]:
        return "multi_step"
    return "transfer"


def plan_session(question_count: int, seed: str) -> list[dict[str, Any]]:
    """Select a balanced, reproducible set of (family, difficulty) pairs.

    Coverage policy (handoff §11 'initial coverage policy'):
      - both buckets represented when the count allows
      - minimum distinct skills
      - no repeated family within one session when avoidable
      - difficulty mix roughly 50/35/15
    """
    release = load_release()
    families = release.get("families") or []
    if not families:
        raise RuntimeError("content release has no approved question families")

    rng = make_rng("plan", seed)
    by_bucket: dict[str, list[dict[str, Any]]] = {}
    for f in families:
        bucket = f["skill_id"].split(".")[0]
        by_bucket.setdefault(bucket, []).append(f)
    buckets = sorted(by_bucket.keys())

    plan: list[dict[str, Any]] = []
    used_families: set[str] = set()
    used_skills: set[str] = set()

    for i in range(question_count):
        # alternate buckets to balance coverage
        bucket = buckets[i % len(buckets)] if len(buckets) > 1 else buckets[0]
        pool = [f for f in by_bucket[bucket] if f["family_id"] not in used_families]
        if not pool:
            pool = by_bucket[bucket]
        if not pool:
            pool = families
        pick = pool[rng.randrange(len(pool))]
        difficulty = _pick_difficulty(rng, rng.random())
        if difficulty not in pick.get("difficulties", ["direct"]):
            difficulty = pick["difficulties"][0]
        plan.append({"family_id": pick["family_id"], "difficulty": difficulty,
                     "skill_id": pick["skill_id"]})
        used_families.add(pick["family_id"])
        used_skills.add(pick["skill_id"])

    return plan
