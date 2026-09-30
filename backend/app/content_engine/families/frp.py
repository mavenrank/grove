"""Fractions, ratios and percentage families."""
from __future__ import annotations

import random
from typing import Any

from .registry import family
from .helpers import int_q, mcq, nearby_1dp


@family("percent.of", "quant.frp.percentages")
def percent_of(rng, difficulty):
    pct = rng.choice([5, 12, 15, 20, 25, 35, 45, 60, 75]) if difficulty == "direct" else rng.choice([12, 18, 35, 45, 65, 85])
    val = rng.choice([120, 160, 200, 240, 300, 360, 420, 480])
    answer = pct * val / 100
    prompt = f"What is {pct}% of {val}?"
    explanation = f"{pct}% of {val} = {pct}/100 × {val} = {answer:g}."
    if answer.is_integer():
        return int_q(rng, prompt, int(answer), explanation)
    return mcq(rng, prompt, f"{answer:g}", nearby_1dp(rng, answer), explanation)


@family("percent.change", "quant.frp.percent_change")
def percent_change(rng, difficulty):
    old = rng.randint(40, 400)
    new = int(old * rng.uniform(0.4, 1.8)) if difficulty == "transfer" else old + rng.choice([-1, 1]) * rng.randint(5, old // 2)
    if new == old:  # guard the degenerate 0% case
        new = old + max(5, old // 10) * rng.choice([-1, 1])
    change = round((new - old) / old * 100, 1)
    sign = "increase" if change >= 0 else "decrease"
    answer = f"{abs(change)}% {sign}"
    base = abs(round(change))
    ds: list[str] = []
    for cand in (base + 1, base + 2, base + 5, base + 7, base + 11):
        s = f"{cand}% {sign}"
        if s != answer and s not in ds:
            ds.append(s)
    return mcq(rng, f"A quantity changes from {old} to {new}. What is the percentage change?",
               answer, ds[:3], f"Change = ({new} − {old})/{old} × 100 = {change}% → {sign}.")


@family("ratio.split", "quant.frp.ratios")
def ratio_split(rng, difficulty):
    parts = [rng.randint(2, 9), rng.randint(2, 9), rng.randint(2, 9)]
    unit = rng.randint(6, 30)
    total = sum(parts) * unit
    idx = rng.randint(0, 2)
    letters = ["A", "B", "C"]
    return int_q(rng,
                 f"An amount of {total} is divided among A, B, and C in the ratio {parts[0]}:{parts[1]}:{parts[2]}. What is {letters[idx]}'s share?",
                 parts[idx] * unit,
                 f"Total parts = {sum(parts)}; one part = {total}/{sum(parts)} = {unit}; {letters[idx]} gets {parts[idx]} × {unit} = {parts[idx] * unit}.")


@family("fractions.compare", "quant.frp.fractions")
def fractions_compare(rng, difficulty):
    for _ in range(20):
        fracs = [(rng.randint(2, 9), rng.randint(10, 20)) for _ in range(4)]
        fracs = [(a, b) for (a, b) in fracs if a < b]
        vals = [a / b for (a, b) in fracs]
        if len(fracs) == 4 and len(set(vals)) == 4:
            break
    label = "smallest" if difficulty == "direct" else "largest"
    pick = min if label == "smallest" else max
    best = vals.index(pick(vals))
    opts = [f"{a}/{b}" for (a, b) in fracs]
    return mcq(rng, f"Which fraction is the {label}?", opts[best], [o for o in opts if o != opts[best]],
               f"{opts[best]} ≈ {vals[best]:.3f} is the {label} of the four.")
