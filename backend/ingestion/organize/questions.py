"""Question-slide parsing: prompt, options, notes-confirmed answer."""
from __future__ import annotations

import re
from typing import Any

from .text import OPTION_LETTERS, QUESTION_PROMPT_SPLIT, clean_lines

# Explicit note labels only: a reference to "option B" inside prose is not a
# key. Source decks use parentheses, arrows and private-font/replacement glyphs.
NOTE_ANSWER_LABEL = re.compile(
    r"^[^\S\r\n]*(?:(?:the|correct)[^\S\r\n]+)?(?:answer|option)\b"
    r"(?:[^\S\r\n]+is\b)?[^\S\r\n]*(?:[:=\-][^\S\r\n]*)*(?:option\b)?"
    r"(?:[^\S\r\n]|[:=\-\u2010-\u2015\u2190-\u21ff\ufffd\uf000-\uf8ff])*"
    r"[(\[]?[^\S\r\n]*([A-Z])\b[^\S\r\n]*[)\]]?[^\S\r\n]*[.:;-]?",
    re.I | re.M,
)
MULTIPLE_NOTE_LABELS = re.compile(r"^[^\S\r\n]*(?:[/,&]|\b(?:or|and)\b)[^\S\r\n]*[(\[]?[^\S\r\n]*[A-Z]\b", re.I)


def parse_notes_answer(notes: str) -> tuple[str | None, str, list[dict], list[dict]]:
    """Recover explicit same-slide keys, keeping conflicts blocked (#7).

    A label is source evidence, never independent mathematical verification.
    Raw notes remain on the question. Removing label spans preserves text that
    precedes a label and prevents Option(A) from leaving a dangling parenthesis.
    """
    normalized = notes.replace("\v", "\n")
    matches = list(NOTE_ANSWER_LABEL.finditer(normalized))
    evidence = [{"label": m.group(1).lower(), "text": m.group(0), "span": list(m.span())} for m in matches]
    labels = {m.group(1).lower() for m in matches}
    ambiguous = any(MULTIPLE_NOTE_LABELS.match(normalized[m.end():].split("\n", 1)[0]) for m in matches)
    issues = []
    if len(labels) > 1 or ambiguous:
        issues.append({"code": "notes_answer_ambiguous", "severity": "review",
                       "message": "Speaker notes contain conflicting or multiple answer labels"})
    explanation = normalized
    for match in reversed(matches):
        explanation = explanation[:match.start()] + explanation[match.end():]
    answer = next(iter(labels)) if len(labels) == 1 and not issues else None
    return answer, clean_explanation(explanation) if matches else "", issues, evidence


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
    labels: list[str] = []
    inline_flags: list[bool] = []
    for ln in lines:
        m = QUESTION_PROMPT_SPLIT.match(ln)
        if m:
            letters_seen = True
            labels.append(m.group(1).lower())
            inline_flags.append(bool(m.group(2).strip()))
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

    notes = slide.get("notes") or ""
    answer, explanation, review_issues, answer_evidence = parse_notes_answer(notes)
    if (labels != list(OPTION_LETTERS[:len(labels)]) or len(option_values) != len(labels)
            or (any(inline_flags) and not all(inline_flags))):
        review_issues.append({"code": "option_mapping_ambiguous", "severity": "review",
                              "message": "Option labels/values are missing, duplicated, reordered or mixed"})
    if answer and answer not in options:
        review_issues.append({"code": "answer_outside_options", "severity": "review",
                              "message": f"Notes answer {answer!r} is absent from the parsed options"})
        answer = None
    elif not answer and not any(i["code"] == "notes_answer_ambiguous" for i in review_issues):
        review_issues.append({"code": "answer_missing", "severity": "review",
                              "message": "No matching answer label in this slide's notes"})
    if review_issues:
        answer = None

    return {
        "prompt": prompt,
        "options": options,
        "answer": answer,          # None → unverified, review only
        "explanation": explanation,
        "notes_raw": notes,
        "answer_evidence": answer_evidence,
        "answer_status": "notes_confirmed" if answer else "needs_review",
        "issues": review_issues,
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
