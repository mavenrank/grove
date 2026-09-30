"""Question-family registry — the backend's plugin point for question types.

A **family** is one deterministic generator of practice questions. Anything
that can produce this shape can be a family:

    {prompt, options[4], answer_index, explanation}

Invariants (handoff §11): exactly one correct answer; distractors distinct;
no degenerate cases; deterministic under the same seed. The correct option is
always at index 0 at generation time; the engine permutes per session seed.
Nothing here is ever serialized directly to the client.

**Adding a family** (no core changes needed):

    from app.content_engine.families.registry import family

    @family("myplugin.thing", "quant.numbers.arithmetic")
    def thing(rng, difficulty):
        return {"prompt": "...", "options": ["42", "1", "2", "3"],
                "answer_index": 0, "explanation": "42."}

Built-in families live in sibling modules and register at import time
(`families/__init__.py` loads them). External plugins can call
`register_family` programmatically — e.g. from an entry-point-loaded module —
without touching core code.
"""
from __future__ import annotations

import random
from collections.abc import Callable
from typing import Any

Question = dict[str, Any]

FAMILIES: dict[str, Callable[[random.Random, str], Question]] = {}
FAMILY_SKILLS: dict[str, str] = {}


def register_family(family_id: str, skill_id: str,
                    fn: Callable[[random.Random, str], Question]) -> None:
    """Programmatic registration — the adapter seam for external plugins."""
    if family_id in FAMILIES:
        raise ValueError(f"family {family_id} already registered")
    FAMILIES[family_id] = fn
    FAMILY_SKILLS[family_id] = skill_id


def family(family_id: str, skill_id: str):
    """Decorator form used by the built-in family modules."""
    def deco(fn: Callable[[random.Random, str], Question]):
        def wrapper(rng: random.Random, difficulty: str) -> Question:
            q = fn(rng, difficulty)
            q["family_id"] = family_id
            q["skill_id"] = skill_id
            q["difficulty"] = difficulty
            return q
        register_family(family_id, skill_id, wrapper)
        return wrapper
    return deco


def generate_question(family_id: str, difficulty: str, rng_seed_parts: tuple) -> Question:
    from ..deterministic import make_rng
    fn = FAMILIES.get(family_id)
    if fn is None:
        raise KeyError(f"unknown family {family_id}")
    return fn(make_rng(*rng_seed_parts), difficulty)


def all_family_ids() -> list[str]:
    return sorted(FAMILIES.keys())


def family_skill_map() -> dict[str, str]:
    """family_id → skill_id for every registered family."""
    return dict(FAMILY_SKILLS)
