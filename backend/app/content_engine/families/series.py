"""Series families: arithmetic, geometric, alternating, letters."""
from __future__ import annotations

import random
import string
from typing import Any

from .registry import family
from .helpers import int_q, mcq


@family("series.arith_next", "logic.pat.number_series")
def series_arith_next(rng, difficulty):
    start, d = rng.randint(2, 30), rng.randint(3, 15)
    n = rng.randint(5, 6) if difficulty == "direct" else rng.randint(7, 9)
    terms = [start + d * i for i in range(n)]
    answer = start + d * n
    return int_q(rng, "What comes next? " + ", ".join(map(str, terms)) + ", …", answer,
                 f"Common difference is {d}; next term = {terms[-1]} + {d} = {answer}.")


@family("series.geo_next", "logic.pat.number_series")
def series_geo_next(rng, difficulty):
    start, r = rng.randint(2, 6), rng.choice([2, 3])
    n = rng.randint(4, 5) if difficulty == "direct" else rng.randint(6, 7)
    terms = [start * r ** i for i in range(n)]
    answer = start * r ** n
    return int_q(rng, "What comes next? " + ", ".join(map(str, terms)) + ", …", answer,
                 f"Each term is multiplied by {r}; next = {terms[-1]} × {r} = {answer}.")


@family("series.alternating", "logic.pat.number_series")
def series_alternating(rng, difficulty):
    a0, add1, add2 = rng.randint(3, 20), rng.randint(2, 9), rng.randint(10, 25)
    # two interleaved arithmetic chains: even positions +add1, odd positions +add2
    terms = [a0, a0 + add2]
    for i in range(2, 5 if difficulty == "direct" else 7):
        if i % 2 == 0:
            terms.append(a0 + (i // 2) * add1)
        else:
            terms.append(a0 + add2 + (i // 2) * add2)
    next_i = len(terms)
    answer = a0 + (next_i // 2) * add1 if next_i % 2 == 0 else a0 + add2 + (next_i // 2) * add2
    return int_q(rng, "What comes next? " + ", ".join(map(str, terms)) + ", …", answer,
                 f"Two interleaved sequences (+{add1} and +{add2}); next term is {answer}.")


@family("series.letters", "logic.pat.letter_series")
def series_letters(rng, difficulty):
    step = rng.randint(1, 4) if difficulty == "direct" else rng.randint(2, 5)
    start, n = rng.randint(0, 12), 4
    idxs = [(start + step * i) % 26 for i in range(n)]
    terms = [string.ascii_uppercase[i] for i in idxs]
    nxt = (start + step * n) % 26
    answer = string.ascii_uppercase[nxt]
    ds = [string.ascii_uppercase[(nxt + k) % 26] for k in (1, 2, -1)]
    ds = [d for d in ds if d != answer]
    return mcq(rng, "What letter comes next? " + ", ".join(terms) + ", …", answer, ds,
               f"Each step moves +{step} letters; next is {answer}.")
