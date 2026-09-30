"""Question-slide parsing: prompt, options, notes-confirmed answer."""
from __future__ import annotations

import re
from typing import Any

from .text import ANSWER_IN_NOTES, OPTION_LETTERS, QUESTION_PROMPT_SPLIT, clean_lines


def parse_question_slide(slide: dict[str, Any]) -> dict[str, Any] | None:
    """Parse a question slide into {prompt, options, answer, explanation}.

    Layouts observed in the corpus:
      [prompt, "A)", "B)", "C)", "D)", "50%", "100%", ...]  letters then values
      [prompt, "A) 50%", "B) 100%", ...]                     inline values
    The answer + explanation come from the SAME slide's speaker notes.
    """
    lines = clean_lines(slide["texts"])
    # drop trailing "Question N" markers
    lines = [ln for ln in lines if not re.match(r"^questions?\s*\d*$", ln, re.I)]

    prompt_lines: list[str] = []
    option_values: list[str] = []
    letters_seen = False
    for ln in lines:
        m = QUESTION_PROMPT_SPLIT.match(ln)
        if m:
            letters_seen = True
            if m.group(2).strip():
                option_values.append(m.group(2).strip())
            continue
        if letters_seen:
            option_values.append(ln)
        else:
            prompt_lines.append(ln)

    if not prompt_lines or not letters_seen:
        return None

    prompt = " ".join(prompt_lines).strip()
    if len(prompt) < 12 or len(option_values) < 2:
        return None

    options: dict[str, str] = {}
    for i, val in enumerate(option_values[: len(OPTION_LETTERS)]):
        options[OPTION_LETTERS[i]] = val.strip()

    answer = None
    explanation = ""
    notes = slide.get("notes") or ""
    m = ANSWER_IN_NOTES.search(notes)
    if m:
        answer = m.group(1).lower()
        explanation = clean_explanation(m.group(2))

    return {
        "prompt": prompt,
        "options": options,
        "answer": answer,          # None → unverified, review only
        "explanation": explanation,
        "notes_raw": notes,
        "source": {"deck_id": slide["deck_id"], "slide_number": slide["slide_number"],
                   "source_file": slide["source_file"]},
    }


def clean_explanation(text: str) -> str:
    """Notes-derived explanation with dangling fragments removed.

    'Answer: B)' must not yield an explanation of ')'. A usable explanation
    needs real words; punctuation-only debris returns empty.
    """
    text = text.strip().lstrip(".—-:").strip()
    text = re.sub(r"(?:^|\s)[)\]}.:,;]+\s*$", "", text).strip()
    if sum(ch.isalnum() for ch in text) < 3:
        return ""
    return text
