"""Real corpus label variants and unsafe/conflicting notes keys."""
import pytest

from ingestion.organize.questions import parse_question_slide


def parse(notes, text="Find the distance travelled.\nA) 12 km\nB) 10 km\nC) 8 km\nD) 6 km"):
    return parse_question_slide({"deck_id": "speed", "slide_number": 3, "source_file": "speed.pptx",
                                 "texts": [text], "notes": notes})


@pytest.mark.parametrize("notes,label", [
    ("Option�D\nExplanation: divide the distance by time", "d"),
    ("Option(C)\nMultiply the units consistently", "c"),
    ("option b\nUse equal distances", "b"),
    ("Correct Answer: (A)\nReasoning here", "a"),
    ("The answer is: B\nReasoning here", "b"),
    ("Answer is option C. Reasoning here", "c"),
    ("For image View→ Notes page\nOption a\nUse the arrangement", "a"),
    ("Option\uf0e0B\nUse the diagram", "b"),
    ("Option\u00a0D\nDistance divided by time", "d"),
    ("Answer :\u00a0A\nExplanation here", "a"),
])
def test_explicit_source_label_variants_remain_notes_confirmed(notes, label):
    question = parse(notes)
    assert question["answer"] == label
    assert question["answer_status"] == "notes_confirmed"
    assert question["notes_raw"] == notes
    assert question["answer_evidence"][0]["label"] == label
    assert not question["explanation"].startswith(")")


@pytest.mark.parametrize("notes", ["Answer: A\nOption B", "Option A or B", "Option (A)/(B)", "Answer A, B"])
def test_conflicting_keys_cannot_become_examples(notes):
    question = parse(notes)
    assert question["answer"] is None
    assert "notes_answer_ambiguous" in {i["code"] for i in question["issues"]}


@pytest.mark.parametrize("notes", [
    "Compare option B with option C before calculating.",
    "The answer can be found by dividing distance by time.",
    "Option Because the units agree", "View -> Notes page",
])
def test_prose_and_missing_labels_do_not_invent_keys(notes):
    question = parse(notes)
    assert question["answer"] is None
    assert question["answer_status"] == "needs_review"


def test_label_removal_keeps_preceding_and_following_solution_lines():
    question = parse("First compute distance.\nOption(A)\nThen verify the units.")
    assert question["explanation"] == "First compute distance.\n\nThen verify the units."
    assert question["notes_raw"].startswith("First compute")


def test_repeated_same_key_is_not_conflict_but_outside_choice_stays_blocked():
    assert parse("Answer: A\nOption(A)")["answer"] == "a"
    outside = parse("Option F\nReasoning here")
    assert outside["answer"] is None
    assert "answer_outside_options" in {i["code"] for i in outside["issues"]}


def test_recognized_notes_cannot_override_ambiguous_slide_choices():
    question = parse("Option B", "Find the distance travelled.\nA) 12 km\nC) 10 km")
    assert question["answer"] is None
    assert "option_mapping_ambiguous" in {i["code"] for i in question["issues"]}
