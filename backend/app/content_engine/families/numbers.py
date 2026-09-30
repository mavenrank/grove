"""Number families: arithmetic, divisibility, factors, HCF/LCM, power cycles."""
from __future__ import annotations

import math
import random
from typing import Any

from .registry import family
from .helpers import int_q


@family("arith.multiply", "quant.numbers.arithmetic")
def arith_multiply(rng, difficulty):
    if difficulty == "direct":
        a, b = rng.randint(6, 19), rng.randint(6, 19)
    elif difficulty == "multi_step":
        a, b = rng.randint(21, 49), rng.randint(11, 29)
    else:
        a, b = rng.randint(53, 99), rng.randint(53, 99)
    return int_q(rng, f"What is {a} × {b}?", a * b, f"{a} × {b} = {a * b}.")


@family("arith.series_sum", "quant.numbers.arithmetic")
def arith_series_sum(rng, difficulty):
    start, d = rng.randint(1, 20), rng.randint(2, 9)
    n = rng.randint(5, 8) if difficulty == "direct" else rng.randint(9, 15)
    total = n * (2 * start + (n - 1) * d) // 2
    return int_q(rng,
                 f"Find the sum of the first {n} terms of the arithmetic sequence starting at {start} with common difference {d}.",
                 total, f"Sum = n/2 × (2a + (n−1)d) = {total}.")


@family("divisibility.remainder", "quant.numbers.divisibility")
def divisibility_remainder(rng, difficulty):
    mod = rng.choice([7, 9, 11, 13]) if difficulty == "direct" else rng.choice([17, 19, 23, 29])
    quotient, rem = rng.randint(20, 150), rng.randint(1, mod - 1)
    n = mod * quotient + rem
    return int_q(rng, f"What is the remainder when {n} is divided by {mod}?", rem,
                 f"{n} = {mod} × {quotient} + {rem}, so the remainder is {rem}.")


@family("divisibility.count", "quant.numbers.divisibility")
def divisibility_count(rng, difficulty):
    d = rng.choice([3, 4, 6, 8])
    limit = rng.randint(900, 2000) if difficulty == "transfer" else rng.randint(200, 900)
    return int_q(rng, f"How many positive integers up to {limit} are divisible by {d}?", limit // d,
                 f"⌊{limit}/{d}⌋ = {limit // d}.")


@family("factors.count", "quant.numbers.factors_multiples")
def factors_count(rng, difficulty):
    base = rng.choice([12, 18, 24, 36, 48, 60, 72, 90, 96])
    n = base * (rng.choice([1, 2]) if difficulty == "direct" else rng.choice([2, 3, 5]))
    divisors = sum(2 if i * i < n else (1 if i * i == n else 0) for i in range(1, math.isqrt(n) + 1) if n % i == 0)
    return int_q(rng, f"How many positive divisors does {n} have?", divisors,
                 f"{n} has {divisors} positive divisors.")


@family("hcf_lcm.basic", "quant.numbers.hcf_lcm")
def hcf_lcm_basic(rng, difficulty):
    a, b = rng.randint(12, 60), rng.randint(12, 60)
    g = math.gcd(a, b)
    want_lcm = difficulty != "direct"
    label = "LCM" if want_lcm else "HCF (GCD)"
    answer = a * b // g if want_lcm else g
    return int_q(rng, f"What is the {label} of {a} and {b}?", answer,
                 f"{label}({a}, {b}) = {answer}.")


@family("numbers.power_cycle", "quant.numbers.power_cycles")
def power_cycle(rng, difficulty):
    base, mod = rng.choice([2, 3, 7, 8, 12, 17]), rng.choice([4, 5, 9, 10])
    exp = rng.randint(3, 12) if difficulty == "direct" else rng.randint(10, 300)
    return int_q(rng, f"What is the remainder when {base}^{exp} is divided by {mod}?", pow(base, exp, mod),
                 f"{base}^{exp} mod {mod} follows a power cycle; the remainder is {pow(base, exp, mod)}.")
