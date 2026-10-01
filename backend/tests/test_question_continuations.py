"""Observed A–E rows and split Syllogisms: no silent mapping/provenance loss."""
from copy import deepcopy

import pytest

from ingestion.organize.concepts import organize_deck, assemble_concepts
from ingestion.organize.questions import parse_question_slide


def slide(number, texts, **kwargs):
    return {"slide_number": number, "slide_id": f"snapshot:{number}", "kind": "question",
            "texts": texts, "notes": "", "blocks": [], "notes_blocks": [],
            "deck_id": "deck", "source_file": "SYLLOGISMS.pptx", **kwargs}


def block(text, x, y, number):
    return {"type": "text", "text": text, "block_id": f"snapshot:2:{number}",
            "bounds_emu": {"left": x, "top": y, "width": 60 if len(text) < 3 else 500, "height": 50},
            "group_path": [], "rotation": 0}


def choices():
    labels = [f"{letter})" for letter in "ABCDE"]
    values = ["Only (1) follows", "Only (2) follows", "Either follows", "Neither follows", "Both follow"]
    blocks = [block(label, 100, i * 100 + 200, i) for i, label in enumerate(labels)]
    blocks += [block(value, 200, i * 100 + 200, i + 10) for i, value in enumerate(values)]
    return slide(2, labels + values + ["Question 1"], blocks=blocks,
                 notes="Answer: A\nOnly conclusion 1 follows.", notes_media_ids=["diagram"],
                 notes_blocks=[{"block_id": "snapshot:2:notes:1", "type": "image", "image_id": "diagram"}])


def deck(first, second):
    return {"deck_id": "deck", "source_file": "SYLLOGISMS.pptx", "source_path": "SYLLOGISMS.pptx",
            "source_hash": "hash", "slide_count": 2, "slides": [first, second]}


def test_fifth_option_and_reordered_explicit_labels_keep_actual_keys():
    q = parse_question_slide(slide(1, ["Question 1", "Find the correct conclusion from these statements.",
                                      "B) second", "A) first", "C) third", "D) fourth", "E) fifth"], notes="Answer: E"))
    assert q["answer"] == "e" and q["options"] == {"b": "second", "a": "first", "c": "third", "d": "fourth", "e": "fifth"}
    assert not q["issues"]


@pytest.mark.parametrize("options", ["A) first\nB) second\nE)", "A) first\nA) second", "A) first\nC) third",
                                    "A)\nB) second\nfirst", "A) first\nB) second\nUnattached caption"])
def test_incomplete_or_unattached_choices_remain_blocked(options):
    q = parse_question_slide(slide(1, ["Find the correct conclusion from these statements.", options], notes="Answer: A"))
    assert q["answer"] is None
    assert "option_mapping_ambiguous" in {item["code"] for item in q["issues"]}
    assert "E)" not in q["options"].values()


def test_split_question_keeps_two_original_snapshots_and_notes_provenance():
    source = deck(slide(1, ["Question 1", "Some actors are singers. All singers are dancers. Which conclusions follow?"]), choices())
    before = deepcopy(source)
    org = organize_deck(source, {})
    assert source == before
    assert len(org["questions"]) == 1
    q = org["questions"][0]
    assert q["answer"] == "a" and q["options"]["e"] == "Both follow"
    assert [part["slide_number"] for part in q["source_parts"]] == [1, 2]
    assert q["answer_evidence"][0]["source"]["slide_number"] == 2
    assert q["notes_media_ids"] == ["diagram"]
    assert [item["outcome"] for item in org["decisions"]] == ["question_candidate", "question_continuation"]
    concept = assemble_concepts("logic.rel.syllogisms", [source], [org])
    assert concept["examples"][0]["source_parts"] == q["source_parts"]
    assert concept["media"][0]["source"]["slide_number"] == 2
    assert concept["media"][0]["source"]["surface"] == "notes"


def test_existing_geometry_cannot_fall_back_to_guessing_shape_order():
    source = choices()
    source["texts"].insert(0, "Which conclusion follows from the statements?")
    source["blocks"][0]["rotation"] = 90
    q = parse_question_slide(source)
    assert q["answer"] is None
    assert "option_mapping_ambiguous" in {item["code"] for item in q["issues"]}


def test_different_box_heights_with_matching_row_centres_are_supported():
    source = choices()
    source["texts"].insert(0, "Which conclusion follows from the statements?")
    source["blocks"].insert(0, block("Which conclusion follows from the statements?", 100, 0, 90))
    for value in source["blocks"][6:]:
        value["bounds_emu"]["top"] += 18
        value["bounds_emu"]["height"] = 30
    q = parse_question_slide(source)
    assert q["answer"] == "a"


@pytest.mark.parametrize("failure", ["missing_id", "different_id", "duplicate_id", "not_adjacent", "extra_prompt",
                                    "extra_row", "overlap", "rotation", "prompt_notes"])
def test_ambiguous_continuation_is_not_joined(failure):
    first = slide(1, ["Question 1", "Some actors are singers. Which conclusions follow?"])
    second = choices()
    if failure == "missing_id":
        first["texts"].pop(0)
    elif failure == "different_id":
        second["texts"][-1] = "Question 2"
    elif failure == "duplicate_id":
        second["texts"].append("Question 1")
    elif failure == "not_adjacent":
        second["slide_number"] = 3
    elif failure == "extra_prompt":
        second["blocks"].append(block("Find the value in this NEW question.", 200, 0, 80))
    elif failure == "extra_row":
        second["blocks"].append(block("Unattached value", 200, 900, 80))
    elif failure == "overlap":
        second["blocks"].append(block("Competing value", 210, 200, 80))
    elif failure == "rotation":
        second["blocks"][0]["rotation"] = 90
    elif failure == "prompt_notes":
        first["notes"] = "Answer: B"
    org = organize_deck(deck(first, second), {})
    assert all(item["outcome"] != "question_continuation" for item in org["decisions"])
    assert all(not q.get("source_parts") for q in org["questions"])
