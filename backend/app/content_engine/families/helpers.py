"""Shared option-building helpers for family generators.

Every family must emit exactly four options: the answer plus three distinct,
plausible distractors. These helpers guarantee distinctness deterministically.
"""
from __future__ import annotations

import random
from typing import Any


def nearby_ints(rng: random.Random, answer: int, count: int = 3, max_frac: float = 0.2) -> list[int]:
    """Distinct near-miss integers, positive when the answer is positive."""
    out: list[int] = []
    seen = {answer}
    delta = max(2, int(abs(answer) * max_frac))
    floor = 1 if answer > 0 else -(10 ** 9)
    tries = 0
    while len(out) < count and tries < 200:
        tries += 1
        cand = answer + rng.randint(1, delta) * rng.choice([-1, 1])
        if cand != answer and cand not in seen and cand >= floor:
            out.append(cand)
            seen.add(cand)
    while len(out) < count:  # deterministic fallback
        cand = answer + len(out) + 1
        if cand in seen:
            cand = answer - len(out) - 1
        out.append(cand)
        seen.add(cand)
    return out


def nearby_1dp(rng: random.Random, answer: float, count: int = 3) -> list[str]:
    """Distinct one-decimal near-misses for decimal answers."""
    out: list[str] = []
    seen = {round(answer, 1)}
    steps = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    rng.shuffle(steps)
    for s in steps:
        if len(out) == count:
            break
        for sign in (-1, 1):
            cand = round(answer + sign * s, 1)
            if cand not in seen and cand > 0:
                out.append(f"{cand:.1f}")
                seen.add(cand)
                break
    fallback = 1.0
    while len(out) < count:  # deterministic fallback when steps ran dry
        cand = round(answer + fallback + len(out) * 0.5, 1)
        if cand not in seen and cand > 0:
            out.append(f"{cand:.1f}")
            seen.add(cand)
        fallback += 1.0
    return out[:count]


def mcq(rng: random.Random, prompt: str, answer: Any, distractors: list[Any], explanation: str) -> dict[str, Any]:
    """Exactly four options: the answer + the first three unique distractors."""
    seen = {str(answer)}
    uniq: list[str] = []
    for d in distractors:
        s = str(d)
        if s not in seen:
            uniq.append(s)
            seen.add(s)
    if len(uniq) < 3:
        raise ValueError(f"generator produced <3 unique distractors: {prompt[:60]}")
    options = [str(answer)] + uniq[:3]
    return {"prompt": prompt, "options": options, "answer_index": 0, "explanation": explanation}


def int_q(rng: random.Random, prompt: str, answer: int, explanation: str) -> dict[str, Any]:
    return mcq(rng, prompt, answer, nearby_ints(rng, answer), explanation)
