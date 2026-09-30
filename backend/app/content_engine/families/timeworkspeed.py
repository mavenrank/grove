"""Time, work and speed families."""
from __future__ import annotations

import random
from typing import Any

from .registry import family
from .helpers import int_q, mcq, nearby_1dp, nearby_ints


@family("time_work.together", "quant.tws.time_work")
def time_work_together(rng, difficulty):
    pool = [6, 8, 10, 12, 15, 20, 24, 30]
    a, b = sorted(rng.sample(pool, 2))
    ans = round(a * b / (a + b), 2)
    return mcq(rng,
               f"A can finish a job in {a} hours and B can finish the same job in {b} hours. Working together, how many hours will they take (2 dp)?",
               f"{ans:g}" if ans != int(ans) else int(ans),
               nearby_1dp(rng, ans) if ans != int(ans) else nearby_ints(rng, int(ans)),
               f"Combined rate = 1/{a} + 1/{b}; time = {a}×{b}/({a}+{b}) = {ans:g} hours.")


_HARMONIC_PAIRS = [(20, 30, 24), (30, 60, 40), (40, 60, 48), (20, 60, 30), (30, 120, 48), (60, 120, 80), (24, 48, 32), (36, 45, 40)]


@family("speed.harmonic", "quant.tws.speed_distance_time")
def speed_harmonic(rng, difficulty):
    s1, s2, ans = _HARMONIC_PAIRS[rng.randrange(len(_HARMONIC_PAIRS))]
    return int_q(rng,
                 f"A car covers a distance at {s1} km/h and returns over the same route at {s2} km/h. What is its average speed for the whole trip?",
                 ans,
                 f"Average = 2·{s1}·{s2}/({s1}+{s2}) = {ans} km/h (harmonic mean, equal distances).")


@family("speed.basic", "quant.tws.speed_distance_time")
def speed_basic(rng, difficulty):
    speed, hours = rng.choice([30, 40, 45, 50, 60, 72, 80]), rng.randint(2, 6)
    return int_q(rng, f"A vehicle travels at {speed} km/h for {hours} hours. How far does it travel?",
                 speed * hours, f"Distance = {speed} × {hours} = {speed * hours} km.")
