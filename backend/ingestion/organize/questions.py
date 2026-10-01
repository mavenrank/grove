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
QUESTION_ID = re.compile(r"^questions?\s*[:#]?\s*(\d+)\s*[.:]?\s*$", re.I)


def question_lines(slide: dict) -> list[str]:
    return [ln for ln in clean_lines(slide["texts"]) if not QUESTION_ID.fullmatch(ln)]


def question_id(slide: dict) -> str | None:
    ids = [m.group(1) for ln in clean_lines(slide["texts"]) if (m := QUESTION_ID.fullmatch(ln))]
    return ids[0] if len(ids) == 1 else None


def positioned_choices(slide: dict) -> list[str] | None:
    """Pair separate letter/value boxes only on unique, unrotated rows (#4).

    Preserve original blocks; this is a parsing view, not a new reading order.
    Mixed/grouped/overlapping or incomplete rows fall back to blocked parsing.
    """
    blocks = [b for b in slide.get("blocks", []) if b.get("type") == "text" and b.get("text", "").strip()]
    labels = [b for b in blocks if (m := QUESTION_PROMPT_SPLIT.fullmatch(b["text"].strip())) and not m.group(2)]
    if len(labels) < 2:
        return None
    pairs = []
    used = set()
    for label in labels:
        bounds = label.get("bounds_emu", {})
        if not bounds.get("height") or label.get("group_path") or label.get("rotation", 0) or label.get("bounds_missing"):
            return None
        candidates = []
        for index, value in enumerate(blocks):
            vb = value.get("bounds_emu", {})
            if (value in labels or QUESTION_ID.fullmatch(value["text"].strip())
                    or QUESTION_PROMPT_SPLIT.match(value["text"].strip()) or value.get("group_path")
                    or value.get("rotation", 0) or value.get("bounds_missing") or not vb.get("height")):
                continue
            if (vb["left"] >= bounds["left"] + bounds["width"]
                    and abs((vb["top"] + vb["height"] / 2) - (bounds["top"] + bounds["height"] / 2))
                    <= min(vb["height"], bounds["height"]) * 0.35):
                candidates.append((index, value))
        if len(candidates) != 1 or candidates[0][0] in used:
            return None
        index, value = candidates[0]
        used.add(index)
        pairs.append((label, value))
    # Anything else below the first option may be an unmatched choice/caption.
    # Refuse rather than silently dropping it from the parsing view.
    start = min(label["bounds_emu"]["top"] for label in labels)
    remaining = [b for i, b in enumerate(blocks) if b not in labels and i not in used
                 and not QUESTION_ID.fullmatch(b["text"].strip())]
    if any(b.get("bounds_emu", {}).get("top", start) >= start for b in remaining):
        return None
    prompt = [ln for b in remaining for ln in clean_lines([b["text"]])]
    return prompt + [f"{label['text'].strip()} {value['text'].strip()}" for label, value in pairs]


def split_question_view(prompt: dict, continuation: dict) -> dict | None:
    """Join adjacent, explicitly matching prompt/choices snapshots (#4/#8)."""
    marker = question_id(prompt)
    if (not marker or marker != question_id(continuation)
            or continuation["slide_number"] != prompt["slide_number"] + 1
            or prompt.get("notes", "").strip()):
        return None
    first = question_lines(prompt)
    second = positioned_choices(continuation) or question_lines(continuation)
    if (not first or any(QUESTION_PROMPT_SPLIT.match(ln) for ln in first)
            or not second or not all(QUESTION_PROMPT_SPLIT.match(ln) for ln in second)):
        return None
    return {**prompt, "texts": first + second, "blocks": [], "notes": continuation.get("notes", "")}


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

    Explicit A–E labels remain attached to their own values. Separate boxes
    use unique row coordinates when available; legacy ordered lists require
    complete sequential labels. Unattached values/missing labels stay blocked.
    """
    positioned = positioned_choices(slide)
    lines = positioned or question_lines(slide)

    prompt_lines: list[str] = []
    option_values: list[str] = []
    letters_seen = False
    labels: list[str] = []
    inline_flags: list[bool] = []
    options: dict[str, str] = {}
    unattached: list[str] = []
    for ln in lines:
        m = QUESTION_PROMPT_SPLIT.match(ln)
        if m:
            letters_seen = True
            labels.append(m.group(1).lower())
            inline_flags.append(bool(m.group(2).strip()))
            if m.group(2).strip():
                option_values.append(m.group(2).strip())
                options[m.group(1).lower()] = m.group(2).strip()
            continue
        if letters_seen:
            option_values.append(ln)
            unattached.append(ln)
        else:
            prompt_lines.append(ln)

    if not prompt_lines or not letters_seen:
        return None

    prompt = " ".join(prompt_lines).strip()
    if len(prompt) < 12 or len(labels) < 2:
        return None

    expected = list(OPTION_LETTERS[:len(labels)])
    ordered_separate = (not slide.get("blocks") and not any(inline_flags)
                        and labels == expected and len(unattached) == len(labels))
    if ordered_separate:
        options = dict(zip(labels, unattached))
        unattached = []

    notes = slide.get("notes") or ""
    answer, explanation, review_issues, answer_evidence = parse_notes_answer(notes)
    if (sorted(labels) != expected or len(set(labels)) != len(labels)
            or len(options) != len(labels) or unattached):
        review_issues.append({"code": "option_mapping_ambiguous", "severity": "review",
                              "message": "Option labels/values are missing, duplicated or unattached"})
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
        "unmapped_option_text": unattached,
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
