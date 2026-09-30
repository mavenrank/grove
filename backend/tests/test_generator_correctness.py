"""Independent numerical and logical oracles for known generator defects (#18)."""
from __future__ import annotations

import itertools
import math
import re
from decimal import Decimal

import pytest

from app.content_engine.families import all_family_ids, generate_question
from app.content_engine.families.registry import FAMILIES


@pytest.mark.parametrize("difficulty", ["direct", "reverse", "transfer"])
def test_percentage_and_interest_exact_answers(difficulty):
    fractional = set()
    for seed in range(300):
        for family_id in ("percent.of", "interest.simple"):
            q = generate_question(family_id, difficulty, ("numeric-oracle", seed))
            values = [Decimal(v) for v in re.findall(r"\d+", q["prompt"])]
            expected = math.prod(values) / Decimal(100)
            answers = [Decimal(o) for o in q["options"]]
            assert answers[q["answer_index"]] == expected
            assert answers.count(expected) == 1
            if expected != expected.to_integral_value():
                fractional.add(family_id)
    assert fractional == {"percent.of", "interest.simple"}


@pytest.mark.parametrize("difficulty", ["reverse", "transfer"])
def test_ordering_target_is_unique_under_all_permutations(difficulty):
    for seed in range(100):
        q = generate_question("arrangement.ordering", difficulty, ("ordering-oracle", seed))
        prompt = q["prompt"]
        people = re.search(r"Five friends — (.*?) —", prompt)[1].split(", ")
        first = re.search(r"(\w+) is ahead of everyone", prompt)[1]
        second, anchor = re.search(r"(\w+) is immediately behind (\w+)", prompt).groups()
        last = re.search(r"(\w+) is at the very back", prompt)[1]
        arrangements = [p for p in itertools.permutations(people)
                        if p[0] == first and p[-1] == last and p.index(second) == p.index(anchor) + 1]
        targets = {p[1] for p in arrangements}
        assert prompt.endswith("Who is second in the line?")
        assert targets == {q["options"][q["answer_index"]]}


def test_seating_matches_spatial_left_and_stated_anchor():
    for seed in range(300):
        q = generate_question("arrangement.seating", "direct", ("spatial-oracle", seed))
        around = re.search(r"Going clockwise from P: (.*?)\.", q["prompt"])[1].split(", ")
        assert around[0] == "P"
        subject = re.search(r"left of (\w+)\?", q["prompt"])[1]
        points = {name: (math.cos(math.pi / 2 - i * math.tau / 6),
                         math.sin(math.pi / 2 - i * math.tau / 6))
                  for i, name in enumerate(around)}
        x, y = points[subject]
        # Facing inward, rotate the inward vector (-x,-y) anticlockwise to get left.
        left = (y, -x)
        neighbor = max((p for p in around if p != subject),
                       key=lambda p: ((points[p][0] - x) * left[0] + (points[p][1] - y) * left[1])
                                     / math.hypot(points[p][0] - x, points[p][1] - y))
        assert q["options"][q["answer_index"]] == neighbor


def test_all_registered_families_have_valid_deterministic_shapes():
    # This checks structure/reproducibility; it is not a semantic audit of all families.
    for fid in all_family_ids():
        for difficulty in ("direct", "reverse", "transfer"):
            for seed in range(30):
                parts = ("structural-survey", seed)
                q = generate_question(fid, difficulty, parts)
                assert generate_question(fid, difficulty, parts) == q
                assert len(q["options"]) == len(set(q["options"])) == 4
                assert q["family_id"] == fid


@pytest.mark.parametrize("changes", [
    {"options": ["1", "2", "3"]}, {"options": ["1", "1", "3", "4"]},
    {"options": ["A", " a ", "3", "4"]}, {"answer_index": 4},
    {"answer_index": True}, {"prompt": ""}, {"explanation": ""},
])
def test_invalid_plugin_output_is_rejected(monkeypatch, changes):
    raw = {"prompt": "Example", "options": ["1", "2", "3", "4"],
           "answer_index": 0, "explanation": "Because."}
    raw.update(changes)
    monkeypatch.setitem(FAMILIES, "test.invalid", lambda rng, difficulty: dict(raw))
    with pytest.raises(ValueError, match="invalid question"):
        generate_question("test.invalid", "direct", ("plugin-test",))
