"""Authored flashcards: general formulas and approach/mindset cards per skill.

Mined slide text is example-specific by nature ("3 green lights = 60 kmph");
these cards are the canonical, reviewable layer the learner actually wants to
rehearse:

  1. the general formula for formulaic skills, and
  2. how to approach the problem type (the mindset), plus durable rules of thumb.

Everything here is hand-authored, reviewable content — no extraction heuristics.
Mined cards are only added when they pass strict generality gates and never
duplicate an authored front.
"""

from __future__ import annotations

# skill_id -> list of (kind, front, back)
# kinds: "formula" | "approach" | "rule"
AUTHORED_CARDS: dict[str, list[tuple[str, str, str]]] = {
    # ------------------------------------------------------------------ quant
    "quant.numbers.arithmetic": [
        ("approach", "How do you solve a remainder problem with pairwise coprime moduli?",
         "Use the Chinese Remainder Theorem: write the number as N = k·M + r, satisfy each modulus one at a time, then combine."),
        ("rule", "Number of factors of N = p^a · q^b · …",
         "Multiply the exponents-plus-one: (a+1)(b+1)…"),
        ("rule", "Sum of factors of N = p^a · q^b",
         "(p^(a+1) − 1)/(p − 1) × (q^(b+1) − 1)/(q − 1)"),
    ],
    "quant.numbers.divisibility": [
        ("rule", "Divisibility test for 3 and 9",
         "Sum the digits; divisible by 3 if the sum is, by 9 if the sum is."),
        ("rule", "Divisibility test for 11",
         "Difference of alternating digit sums is 0 or a multiple of 11."),
    ],
    "quant.numbers.factors_multiples": [
        ("formula", "Number of factors of N = p^a · q^b · …?",
         "(a + 1)(b + 1)… — add one to each prime exponent, then multiply."),
        ("formula", "Number of ways to express N as a product of two factors?",
         "Number of factors ÷ 2 (round up if N is a perfect square)."),
    ],
    "quant.numbers.hcf_lcm": [
        ("formula", "HCF × LCM = ?",
         "Product of the two numbers (valid for exactly two numbers)."),
        ("approach", "How do you find the HCF of two numbers quickly?",
         "Euclidean algorithm: replace the larger number with larger mod smaller; the last non-zero remainder is the HCF."),
        ("rule", "HCF of fractions",
         "HCF of numerators ÷ LCM of denominators."),
        ("rule", "LCM of fractions",
         "LCM of numerators ÷ HCF of denominators."),
    ],
    "quant.numbers.power_cycles": [
        ("approach", "How do you find the last digit of a^b?",
         "Find the cycle length of the last digit of a (at most 4), then use b mod cycle-length; map remainder 0 to the last element of the cycle."),
        ("approach", "How do you find the remainder of a^b ÷ n?",
         "Find the remainder cycle of powers of a mod n, then reduce the exponent modulo the cycle length."),
    ],
    "quant.numbers.crypt_arithmetic": [
        ("approach", "How do you attack a crypt-arithmetic puzzle (e.g. SEND + MORE = MONEY)?",
         "Column-by-column from the units: write each column's sum-and-carry equation, assign distinct digits, use leading letters ≠ 0, and test carries systematically."),
        ("rule", "First constraint to place in any letter puzzle",
         "Leading letters cannot be zero; carries are bounded by the number of addends."),
    ],
    "quant.frp.percentages": [
        ("formula", "x% of N = ?",
         "(x/100) × N"),
        ("formula", "% Increase = (New Value − Initial Value) / Initial Value × 100",
         "Increase arrow: New − Initial on top; the base is ALWAYS the initial value."),
        ("formula", "% Decrease = (Initial Value − New Value) / Initial Value × 100",
         "Decrease arrow: Initial − New on top; the base is ALWAYS the initial value."),
        ("formula", "Percentage change = ?",
         "(new − old)/old × 100 — the base is always the ORIGINAL value."),
        ("formula", "Successive changes of a% then b% = ?",
         "a + b + ab/100 (net effect of both changes)."),
        ("rule", "A price rises x% then falls x% — net effect?",
         "Always a net decrease of x²/100 % (never zero)."),
        ("rule", "If a price rises by 1/n, consumption must fall by 1/(n+1) to keep spending equal.",
         "Fraction-change pairing: +1/n up → −1/(n+1) down."),
        ("approach", "What is the safest mindset for percentage-change problems?",
         "Assume a base of 100 (or the stated original), track each step arithmetically, and compare against the original — never against the intermediate value."),
    ],
    "quant.frp.ratios": [
        ("formula", "One part of a total T split in ratio a : b : c",
         "T / (a + b + c); shares are a·k, b·k, c·k."),
        ("formula", "Proportion check: a/b = c/d is equivalent to",
         "a·d = b·c (cross-multiplication)."),
        ("approach", "Mindset for ratio problems",
         "Convert everything to 'parts'. Find the value of one part first, then scale every share from it."),
    ],
    "quant.frp.proportions": [
        ("rule", "Direct variation",
         "y = kx — both rise and fall together."),
        ("rule", "Inverse variation",
         "xy = k — one rises as the other falls."),
    ],
    "quant.frp.fractions": [
        ("rule", "Fast fraction comparison a/b vs c/b' (same numerator)",
         "Same numerator: larger denominator is the smaller fraction."),
        ("rule", "Fast fraction comparison (different numerators)",
         "Cross-multiply: a/b vs c/d → compare ad vs bc."),
    ],
    "quant.frp.percent_change": [
        ("formula", "Percent change = ?",
         "(new − old)/old × 100"),
        ("rule", "Successive a% and b% changes combine as",
         "a + b + ab/100 (signs included)."),
    ],
    "quant.avg.averages": [
        ("formula", "Average = ?",
         "Sum of values / count; Sum = average × count."),
        ("formula", "Weighted average of groups (nᵢ items at average aᵢ)",
         "Σ(nᵢ·aᵢ) / Σnᵢ"),
        ("approach", "Mindset for 'missing value' average problems",
         "Total = average × count. Subtract the known sum from the required total; the gap is the missing value."),
    ],
    "quant.avg.mixtures": [
        ("formula", "Alligation: ratio of quantities at prices p₁ (cheaper) and p₂ (dearer) to get mean m",
         "(p₂ − m) : (m − p₁) — distances from the mean, crossed."),
        ("approach", "Mindset for mixture problems",
         "Track ONE conserved quantity (usually the solute). Write quantity before = quantity after, and solve."),
    ],
    "quant.avg.profit_loss": [
        ("formula", "Profit % = ?",
         "Profit/CP × 100 (base is always COST price)."),
        ("formula", "Loss % = ?",
         "Loss/CP × 100"),
        ("formula", "SP with x% profit = ?",
         "CP × (1 + x/100)"),
        ("rule", "Two items sold at the same SP with +x% and −x% — net result?",
         "Always a net loss of x²/100 %."),
    ],
    "quant.avg.simple_interest": [
        ("formula", "Simple Interest = ?",
         "P·R·T / 100 — interest is computed on the original principal only."),
        ("formula", "Amount with simple interest",
         "A = P + SI = P(1 + RT/100)"),
    ],
    "quant.avg.compound_interest": [
        ("formula", "Compound amount after T years",
         "A = P(1 + R/100)^T; CI = A − P."),
        ("rule", "CI vs SI for the same P, R, 2 years",
         "CI − SI = P(R/100)²."),
    ],
    "quant.tws.time_work": [
        ("formula", "Two workers together (alone in a h and b h)",
         "ab/(a + b) hours — rates add: 1/a + 1/b."),
        ("formula", "Rate of work",
         "Rate = 1/time; Work = rate × time."),
        ("approach", "Mindset for time-and-work problems",
         "Convert every actor to a per-day rate (job/day). Add rates for 'together', subtract for 'leaves', and invert the final rate into time."),
    ],
    "quant.tws.pipes_cisterns": [
        ("formula", "Tank filled by inlet a h and emptied by outlet b h",
         "Net rate = 1/a − 1/b; time to fill = 1 / net rate."),
    ],
    "quant.tws.speed_distance_time": [
        ("formula", "Speed = ?",
         "Distance / Time (keep units consistent)."),
        ("formula", "Average speed over equal distances at speeds a and b",
         "2ab/(a + b) — the harmonic mean, NOT the arithmetic mean."),
    ],
    "quant.tws.relative_speed": [
        ("formula", "Relative speed, opposite directions",
         "Sum of speeds."),
        ("formula", "Relative speed, same direction",
         "Difference of speeds."),
        ("rule", "Train crossing a platform/pole",
         "Distance = train length (+ platform length for a platform)."),
    ],
    "quant.alg.ages": [
        ("formula", "Age after n years / n years ago (current age X)",
         "X + n / X − n; 'n times the age' = nX."),
        ("approach", "Mindset for ages problems",
         "Set the current age as a variable, express every statement as an equation, and remember ratios shift over time — only equations hold."),
    ],
    "quant.alg.equations": [
        ("approach", "Mindset for word problems leading to equations",
         "Name the unknown explicitly, translate each sentence into one equation, solve, and sanity-check the answer against the wording."),
    ],
    "quant.alg.data_interpretation": [
        ("approach", "Mindset for data-sufficiency statements",
         "Test each statement ALONE first, then together; answer the sufficiency question, not the value question."),
    ],
    "quant.misc.clocks": [
        ("formula", "Angle between the hands at H:M",
         "|30H − 5.5M| degrees."),
        ("rule", "The hands coincide how often in 12 hours?",
         "11 times (every 65 5/11 minutes)."),
    ],
    "quant.misc.calendars": [
        ("rule", "Odd days concept",
         "Remainder days after complete weeks; 100 years have 5 odd days, 200 have 3, 300 have 1, 400 have 0."),
        ("rule", "Leap year check",
         "Divisible by 4, except century years which must be divisible by 400."),
        ("approach", "Mindset for day-of-the-week problems",
         "Count odd days from a known anchor (e.g. 01-01-0001 = Monday in the standard convention), add the target year's odd days including leap Februaries."),
    ],
    # ------------------------------------------------------------------ logic
    "logic.pat.number_series": [
        ("approach", "What is the checking order for a number series?",
         "1) differences, 2) ratios, 3) alternating rules, 4) second differences, 5) squares/cubes/primes nearby."),
        ("rule", "Arithmetic series: tₙ and Sₙ",
         "tₙ = a + (n−1)d; Sₙ = n/2 (2a + (n−1)d)."),
        ("rule", "Geometric series: tₙ",
         "tₙ = a·r^(n−1)."),
    ],
    "logic.pat.letter_series": [
        ("approach", "Mindset for letter series",
         "Convert letters to positions (A=1 … Z=26) and look for numeric patterns in the positions, including skips and reversals."),
    ],
    "logic.pat.pattern_completion": [
        ("approach", "Mindset for cube/dice problems",
         "Track painted faces by position: corners have 3 painted faces, edges 2, face-centres 1; use n³−(n−2)³ for 'at least one painted face'."),
    ],
    "logic.rel.blood_relations": [
        ("approach", "What is the best first step for blood-relation questions?",
         "Draw a small family tree generation by generation while reading; never assume gender unless stated."),
        ("rule", "Decoding 'my grandfather's only son'",
         "= my father (an only son has no brothers)."),
    ],
    "logic.rel.directions": [
        ("approach", "Mindset for direction-sense problems",
         "Sketch as you read; fix North at the top, track turns as 90° left/right, and use Pythagoras for the final shortest distance."),
        ("rule", "Sun-based direction anchor",
         "Sunrise shadow points West; the sun sets in the West."),
    ],
    "logic.rel.syllogisms": [
        ("approach", "Mindset for syllogisms",
         "Draw Venn diagrams for the premises and check the conclusion against EVERY valid diagram; a conclusion must hold in all of them."),
        ("rule", "'Some A are B' implies",
         "'Some B are A' — and nothing stronger."),
    ],
    "logic.rel.analogies": [
        ("approach", "Mindset for analogy problems",
         "Name the exact relationship (type-of, part-of, tool-for, opposite, cause-effect), then apply the SAME relationship in the same order."),
    ],
    "logic.rel.inequalities": [
        ("approach", "Mindset for inequality puzzles (A > B ≥ C)",
         "Build a single chain symbol by symbol; a definite conclusion needs a strict > (or <) somewhere on the path between the two subjects."),
    ],
    "logic.arr.seating": [
        ("approach", "Mindset for circular seating (facing centre)",
         "Left of X is clockwise for centre-facing (anti-clockwise for outward); fix one person first, place constraints relative to them."),
        ("approach", "Mindset for linear seating",
         "Decide left/right reference (viewer's vs subject's) once, then place fixed-point people first and float the rest."),
    ],
    "logic.arr.ordering": [
        ("approach", "Mindset for order-and-ranking",
         "Position from left + position from right − 1 = total (when the person is counted once); overlaps matter in vertical stacks."),
    ],
    "logic.arr.grouping": [
        ("approach", "Mindset for grouping/constraint puzzles",
         "Build a grid of entities × attributes, fill definite clues first, and treat 'not' clues as walls; eliminate case-by-case."),
    ],
    "logic.arr.data_arrangements": [
        ("approach", "Mindset for data-arrangement puzzles",
         "Fix the most-constrained entity first, propagate forced placements, and bifurcate only when stuck — keep both cases until one dies."),
    ],
    "logic.code.coding_decoding": [
        ("approach", "How do you crack a coding-decoding pair?",
         "Compare word and code letter-by-letter: look for constant shifts, position swaps, or substitutions; then apply the discovered rule to the probe word."),
        ("rule", "Caesar shift decoding",
         "letter → letter + k (mod 26); test small k values (±1…±4) first."),
    ],
    "logic.code.symbol_substitution": [
        ("approach", "Mindset for symbol-substitution codes",
         "Build the symbol→letter table from the given pair, then translate the probe strictly through the table (never guess untabled symbols)."),
    ],
    "logic.code.classification": [
        ("approach", "Mindset for odd-one-out",
         "Find the property shared by most options (vowel-count, squares, primes, letter positions); the odd one lacks it — check the second-best property before answering."),
    ],
    "logic.inf.assumptions": [
        ("approach", "Mindset for statement–assumption questions",
         "An assumption is something the argument NEEDS to be true; test 'if this were false, would the argument collapse?'"),
    ],
    "logic.inf.conclusions": [
        ("approach", "Mindset for statement–conclusion questions",
         "Judge only what the statement strictly supports — probable ≠ true; reject anything needing outside knowledge."),
    ],
    "logic.inf.arguments": [
        ("approach", "Mindset for cause-and-effect questions",
         "Two correlated facts: ask which precedes, which is more plausible as a driver, and whether a third factor could cause both."),
    ],
}


def authored_flashcards(skill_id: str) -> list[dict]:
    """Return the authored cards for a skill (empty list if none)."""
    return [
        {"kind": kind, "front": front, "back": back}
        for kind, front, back in AUTHORED_CARDS.get(skill_id, [])
    ]
