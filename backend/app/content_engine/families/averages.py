"""Averages, mixtures and finance families."""
from __future__ import annotations

import math
import random
from typing import Any

from .registry import family
from .helpers import int_q, mcq, nearby_1dp, nearby_ints


@family("averages.missing", "quant.avg.averages")
def averages_missing(rng, difficulty):
    n = rng.randint(5, 8) if difficulty == "direct" else rng.randint(9, 12)
    values = [rng.randint(10, 90) for _ in range(n - 1)]
    avg = rng.randint(30, 80)
    missing = avg * n - sum(values)
    return int_q(rng,
                 f"The average of {n} numbers is {avg}. {n - 1} of them are {', '.join(map(str, values))}. What is the missing number?",
                 missing,
                 f"Required total = {avg} × {n} = {avg * n}; given sum = {sum(values)}; missing = {missing}.")


@family("averages.weighted", "quant.avg.averages")
def averages_weighted(rng, difficulty):
    n1, n2 = rng.randint(10, 40), rng.randint(10, 40)
    a1, a2 = rng.randint(40, 70), rng.randint(55, 95)
    ans = round((n1 * a1 + n2 * a2) / (n1 + n2), 1)
    return mcq(rng,
               f"A group of {n1} students averages {a1} marks and another group of {n2} students averages {a2} marks. What is the combined average (to 1 dp if needed)?",
               f"{ans:g}" if ans != int(ans) else int(ans),
               nearby_1dp(rng, ans) if ans != int(ans) else nearby_ints(rng, int(ans)),
               f"({n1}×{a1} + {n2}×{a2})/({n1}+{n2}) = {ans}.")


@family("mixtures.alligation", "quant.avg.mixtures")
def mixtures_alligation(rng, difficulty):
    c1 = rng.randint(10, 40)          # cheap solution
    c2 = rng.randint(55, 89)          # dear solution — bands guarantee a wide gap
    target = rng.randint(c1 + 3, c2 - 3)
    d1, d2 = c2 - target, target - c1
    g = math.gcd(d1, d2)
    a, b = d1 // g, d2 // g
    answer = f"{a}:{b}"
    ds = [f"{b}:{a}"]
    for da, db in ((2, 1), (1, 2), (3, 1), (1, 3)):
        cand = f"{a + da}:{b + db}"
        if cand != answer and cand not in ds:
            ds.append(cand)
    return mcq(rng,
               f"In what ratio must a solution costing Rs.{c1}/litre be mixed with one costing Rs.{c2}/litre to obtain a mixture costing Rs.{target}/litre?",
               answer, ds,
               f"Ratio = ({c2}-{target}):({target}-{c1}) = {d1}:{d2} = {answer}.")


@family("profit_loss.basic", "quant.avg.profit_loss")
def profit_loss_basic(rng, difficulty):
    cost = rng.randint(120, 900)
    pct = rng.choice([10, 15, 20, 25]) if difficulty == "direct" else rng.choice([10, 15, 20, 25, -10, -15, -20])
    sell = round(cost * (100 + pct) / 100, 2)
    kind = "profit" if pct > 0 else "loss"
    amount = round(cost * abs(pct) / 100, 2)
    answer = f"{kind} of ₹{amount:g}"
    wrong_kind = f"{'loss' if pct > 0 else 'profit'} of ₹{amount:g}"
    ds = [wrong_kind, f"{kind} of ₹{amount + rng.randint(5, 40):g}", "no profit, no loss"]
    ds = [d for d in ds if d != answer]
    return mcq(rng, f"An item bought for ₹{cost} is sold for ₹{sell:g}. What is the result?",
               answer, ds[:3],
               f"{'Profit' if pct > 0 else 'Loss'} = {abs(pct)}% of cost = ₹{amount:g}.")


@family("interest.simple", "quant.avg.simple_interest")
def simple_interest(rng, difficulty):
    p = rng.randint(1000, 20000)
    r = rng.choice([4, 5, 6, 7, 8, 10, 12])
    t = rng.randint(2, 6) if difficulty == "direct" else rng.choice([7, 9, 10])
    return int_q(rng, f"Find the simple interest on ₹{p} at {r}% per annum for {t} years.",
                 p * r * t // 100 if (p * r * t) % 100 == 0 else round(p * r * t / 100),
                 f"SI = PRT/100 = {p}×{r}×{t}/100 = {round(p * r * t / 100):g}.")


@family("interest.compound", "quant.avg.compound_interest")
def compound_interest(rng, difficulty):
    p = rng.choice([4000, 5000, 8000, 10000, 12500, 20000])
    r = rng.choice([5, 10, 20])
    t = 2 if difficulty == "direct" else 3
    amount = p * ((100 + r) / 100) ** t
    ci = round(amount - p, 2)
    return mcq(rng, f"Find the compound interest on ₹{p} at {r}% per annum for {t} years (annual compounding).",
               f"{ci:g}", [f"{round(ci + s, 2):g}" for s in (25, 50, 75)],
               f"Amount = {p}×(1+{r}/100)^{t} = {round(amount, 2)}; CI = {ci:g}.")
