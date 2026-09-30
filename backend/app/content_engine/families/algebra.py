"""Algebra and ages families."""
from __future__ import annotations

import random
from typing import Any

from .registry import family
from .helpers import int_q


@family("ages.simple", "quant.alg.ages")
def ages_simple(rng, difficulty):
    age, k = rng.randint(8, 40), rng.randint(2, 4)
    parent = age * k
    if difficulty == "direct":
        return int_q(rng, f"A father is {k} times as old as his son, who is {age} years old. How old is the father?",
                     parent, f"Father = {k} × {age} = {parent}.")
    years = rng.randint(3, 12)
    return int_q(rng,
                 f"A father is {k} times as old as his son. In {years} years, the father will be {parent + years} years old. How old is the son now?",
                 age,
                 f"Father now = {parent + years} − {years} = {parent}; son = {parent}/{k} = {age}.")


@family("equations.linear", "quant.alg.equations")
def equations_linear(rng, difficulty):
    if difficulty == "direct":
        x, a, b = rng.randint(3, 25), rng.randint(2, 9), rng.randint(5, 60)
        return int_q(rng, f"Solve for x: {a}x + {b} = {a * x + b}", x,
                     f"{a}x = {a * x + b} − {b} = {a * x}; x = {x}.")
    # a x − c = rhs + d x  ⇒  (a−d)x = rhs + c
    a, d = sorted(rng.sample(range(2, 12), 2))
    x = rng.randint(4, 20)
    c, rhs = rng.randint(1, 30), rng.randint(1, 40)
    return int_q(rng, f"Solve for x: {a}x − {c} = {rhs} + {d}x", x,
                 f"({a}−{d})x = {rhs} + {c} = {(a - d) * x}; x = {x}.")
