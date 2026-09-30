"""Coding-decoding and classification families."""
from __future__ import annotations

import random
import string
from typing import Any

from .registry import family
from .helpers import mcq


@family("coding.shift", "logic.code.coding_decoding")
def coding_shift(rng, difficulty):
    k = rng.randint(1, 5) if difficulty == "direct" else rng.randint(3, 9)

    def enc(w: str) -> str:
        return "".join(string.ascii_uppercase[(string.ascii_uppercase.index(ch) + k) % 26] for ch in w)

    word = rng.choice(["GROVE", "FOREST", "ORCHARD", "GARDEN"])
    probe = rng.choice(["LEAF", "BRANCH", "ROOT", "SEED"])
    answer = enc(probe)
    ds = []
    for dk in (1, -1, 2):
        cand = "".join(string.ascii_uppercase[(string.ascii_uppercase.index(ch) + k + dk) % 26] for ch in probe)
        if cand != answer and cand not in ds:
            ds.append(cand)
    return mcq(rng, f"In a certain code, {word} is written as {enc(word)}. How is {probe} written in that code?",
               answer, ds, f"Each letter shifts +{k} positions; {probe} → {answer}.")


@family("coding.symbol", "logic.code.symbol_substitution")
def coding_symbol(rng, difficulty):
    words = ["CAT", "DOG", "SUN", "MAP", "PEN"]
    chosen = rng.sample(words, 4)
    symbols = rng.sample(["@", "#", "$", "%", "&", "*"], 4)
    mapping = dict(zip(chosen, symbols))
    word = chosen[rng.randrange(4)]
    answer = mapping[word]
    ds = [s for s in ["@", "#", "$", "%", "&", "*"] if s != answer][:3]
    return mcq(rng, "In a code language, " + ", ".join(f"{w} = {mapping[w]}" for w in chosen) + f". What is the code for {word}?",
               answer, ds, f"From the given mapping, {word} = {answer}.")


_ODD_ONE_OUT = [
    (["Rose", "Jasmine", "Marigold", "Sandalwood"], "Sandalwood", "Sandalwood is a tree; the others are flowers."),
    (["Triangle", "Square", "Pentagon", "Circle"], "Circle", "A circle has no straight sides or vertices."),
    (["Copper", "Iron", "Brass", "Silver"], "Brass", "Brass is an alloy; the rest are elements."),
    (["121", "144", "169", "200"], "200", "The others are perfect squares."),
    (["January", "April", "June", "September"], "January", "The others have 30 days."),
    (["Pace", "Speed", "Velocity", "Tempo"], "Tempo", "Tempo refers to music; the others are rates of motion."),
]


@family("classification.odd_one_out", "logic.code.classification")
def odd_one_out(rng, difficulty):
    opts, correct, expl = _ODD_ONE_OUT[rng.randrange(len(_ODD_ONE_OUT))]
    return mcq(rng, "Which is the odd one out?", correct, [o for o in opts if o != correct], expl)
