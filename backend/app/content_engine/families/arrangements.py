"""Arrangement families: ordering and circular seating."""
from __future__ import annotations

import random
from typing import Any

from .registry import family
from .helpers import mcq


@family("arrangement.ordering", "logic.arr.ordering")
def arrangement_ordering(rng, difficulty):
    people = ["Amit", "Bina", "Chetan", "Divya", "Esha"]
    order = people[:]
    rng.shuffle(order)
    if difficulty == "direct":
        return mcq(rng, f"In a queue from front to back: {', '.join(order)}. Who is third from the front?",
                   order[2], [p for p in people if p != order[2]],
                   "Counting from the front, the third person is " + order[2] + ".")
    first, second, last = order[0], order[1], order[4]
    return mcq(rng,
               f"Five friends — {', '.join(people)} — stand in a line. {first} is ahead of everyone. {second} is immediately behind {first}. {last} is at the very back. Who is second in the line?",
               second, [p for p in people if p != second],
               f"{first} occupies the first position. {second} is immediately behind {first}, so {second} is second.")


@family("arrangement.seating", "logic.arr.seating")
def arrangement_seating(rng, difficulty):
    people = ["P", "Q", "R", "S", "T", "U"]
    around = people[:]
    rng.shuffle(around)
    start = around.index("P")
    around = around[start:] + around[:start]
    idx = rng.randrange(6)
    subject, neighbor = around[idx], around[(idx + 1) % 6]
    return mcq(rng,
               f"Six people {', '.join(people)} sit around a circular table facing the centre. Going clockwise from P: {', '.join(around)}. Who sits immediately to the left of {subject}?",
               neighbor, [p for p in people if p != neighbor],
               f"Facing the centre, a person's left is the next position clockwise: {neighbor}.")
