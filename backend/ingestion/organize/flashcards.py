"""Flashcard drafting: authored cards first, strictly-gated mined gap-fillers."""
from __future__ import annotations

import re
from typing import Any

from .gates import NOISE_TOKENS, clean_definition_line, clean_formula_line, formula_lhs_is_general

FORMULA_FOR = re.compile(r"formula\s+for\s+([^=*:]+?)\s*=\s*(.+)", re.I)


def draft_flashcards(skill_id: str, segments: list[dict[str, Any]],
                     verified_questions: list[dict[str, Any]] | None = None,
                     max_cards: int = 16) -> list[dict[str, Any]]:
    """Formula/rule recall cards — never test questions, never code fragments.

    Sources, in priority order:
      0. authored cards (general formulas, rules of thumb, approach/mindset)
      1. "Formula for X = Y" patterns mined from verified question explanations
         (the speaker notes often state the rule before applying it)
      2. clean formula lines on explanation slides (strict shape: term = value)
      3. clean definition sentences (a short named term + is/are/refers to)
    """
    cards: list[dict[str, Any]] = []
    seen_fronts: set[str] = set()

    def add(front: str, back: str, source: dict[str, Any], kind: str | None = None) -> None:
        front, back = front.strip(), back.strip()
        if len(front) < 3 or len(back) < 3:
            return
        key = front.lower()
        if key in seen_fronts:
            return
        seen_fronts.add(key)
        cards.append({
            "id": f"fc.{skill_id}.{len(cards) + 1}",
            "skill_id": skill_id,
            "kind": kind,
            "front": front,
            "back": back,
            "source": source,
        })

    # 0. AUTHORED cards first: the canonical general formulas and
    # approach/mindset cards for this skill (hand-reviewable, never mined).
    from ..authored_cards import authored_flashcards
    for card in authored_flashcards(skill_id):
        add(card["front"], card["back"], {"authored": True}, kind=card["kind"])

    # 1. mine worked-solution explanations for stated formulas
    #    (strict: general-sounding rule names only)
    for q in verified_questions or []:
        expl = q.get("explanation") or ""
        m = FORMULA_FOR.search(expl)
        if m:
            rule_name = m.group(1).strip().rstrip(": ")
            rule_body = m.group(2).strip()
            if (rule_name and len(rule_name) <= 60
                    and not NOISE_TOKENS.search(rule_name + rule_body)
                    and formula_lhs_is_general(rule_name)):
                add(f"Formula: {rule_name} = ?", rule_body, q["source"], kind="formula")
        if len(cards) >= max_cards:
            break

    # 2. clean formula lines from explanation slides
    if len(cards) < max_cards:
        for seg in segments:
            for line in seg["texts"]:
                cleaned = clean_formula_line(line)
                if cleaned:
                    lhs, full = cleaned
                    add(f"{lhs} = ?", full, seg["source"], kind="formula")
                if len(cards) >= max_cards:
                    break
            if len(cards) >= max_cards:
                break

    # 3. clean definition sentences from explanation slides
    if len(cards) < max_cards:
        for seg in segments:
            for line in seg["texts"]:
                cleaned = clean_definition_line(line)
                if cleaned:
                    term, full = cleaned
                    add(f"Define: {term} = ?", full, seg["source"], kind="rule")
                if len(cards) >= max_cards:
                    break
            if len(cards) >= max_cards:
                break
    return cards
