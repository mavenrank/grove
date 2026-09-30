"""Relation families: blood relations, syllogisms, directions."""
from __future__ import annotations

import math
import random
from typing import Any

from .registry import family
from .helpers import int_q, mcq

_RELATION_PUZZLES = [
    ("Pointing to a photograph, a man said, \"She is the daughter of my grandfather's only son.\" How is she related to him?", "His sister", ["His daughter", "His cousin", "His niece"]),
    ("A is B's brother. C is A's mother. D is C's father. How is A related to D?", "Grandson", ["Son", "Grandfather", "Nephew"]),
    ("X is the mother of Y. Y is the brother of Z. Z is the daughter of W. How is W related to Y?", "Father", ["Uncle", "Brother", "Son"]),
    ("M is the son of N. N is the sister of O. O is the daughter of P. How is M related to P?", "Grandson", ["Son", "Nephew", "Cannot be determined"]),
]

_SYLLOGISM_PUZZLES = [
    ("All roses are flowers. Some flowers fade quickly. Which conclusion follows?", "Some roses may fade quickly", ["All roses fade quickly", "No rose fades quickly", "All flowers are roses"]),
    ("All pens are books. All books are shelves. Which conclusion follows?", "All pens are shelves", ["All shelves are pens", "Some shelves are not books", "No pen is a shelf"]),
    ("Some cats are black. All black things absorb heat. Which conclusion follows?", "Some cats absorb heat", ["All cats absorb heat", "No cat absorbs heat", "All black things are cats"]),
    ("No fish can fly. All birds can fly. Which conclusion follows?", "No bird is a fish", ["Some fish are birds", "All birds are fish", "Some birds are fish"]),
]


@family("relations.simple", "logic.rel.blood_relations")
def relations_simple(rng, difficulty):
    idx = rng.randrange(len(_RELATION_PUZZLES))
    if difficulty == "transfer":
        idx = (idx + 1) % len(_RELATION_PUZZLES)
    prompt, correct, ds = _RELATION_PUZZLES[idx]
    return mcq(rng, prompt, correct, ds, "Trace the family tree step by step from the statements.")


@family("syllogism.basic", "logic.rel.syllogisms")
def syllogism_basic(rng, difficulty):
    idx = rng.randrange(len(_SYLLOGISM_PUZZLES))
    if difficulty == "transfer":
        idx = (idx + 1) % len(_SYLLOGISM_PUZZLES)
    prompt, correct, ds = _SYLLOGISM_PUZZLES[idx]
    return mcq(rng, prompt, correct, ds, "Apply standard syllogism rules; do not overstate the premises.")


_TRIPLES = [(3, 4, 5), (6, 8, 10), (9, 12, 15), (12, 16, 20), (15, 20, 25), (30, 40, 50), (60, 80, 100)]


@family("directions.triples", "logic.rel.directions")
def directions_triples(rng, difficulty):
    a, b, c = _TRIPLES[rng.randrange(len(_TRIPLES))]
    a, b, c = a * 10, b * 10, c * 10
    if difficulty == "direct":
        return int_q(rng, f"A person walks {a} m north, then {b} m east. How far is the person from the starting point (in m)?",
                     c, f"Net displacement = √({a}² + {b}²) = {c} m.")
    south = rng.randint(1, a // 10) * 10
    dy, dx = a - south, b
    ans = math.isqrt(dx * dx + dy * dy)
    if ans * ans != dx * dx + dy * dy:  # fall back to a guaranteed triple
        dy, dx = a, b
        ans = c
        prompt = f"A person walks {a} m north, then {b} m east. How far is the person from the starting point (in m)?"
        return int_q(rng, prompt, ans, f"Net displacement = √({a}² + {b}²) = {ans} m.")
    return int_q(rng, f"A person walks {a} m north, then {b} m east, then {south} m south. How far is the person from the starting point (in m)?",
                 ans, f"Net: {dx} m east, {dy} m north → √({dx}² + {dy}²) = {ans} m.")
