"""Organize extracted slides into Grove's three content streams (handoff §13):

    explanation slides → LEARNING   (concept sections: text, images, formulas)
    question slides    → QUESTIONS  (prompt, options, answer + explanation from notes)
    formula/rule lines → FLASHCARDS (concept recall, never test questions)

Decomposed modules:
  text       — shared regexes, line cleanup, code detection
  labels     — human deck labels for citations
  questions  — question-slide parsing (prompt/options/answer from notes)
  gates      — formula/definition mining gates (anti-junk)
  flashcards — card drafting (authored first, mined gap-fillers)
  concepts   — concept assembly and per-skill grouping

Every record keeps provenance (deck, slide number) so a reviewer can jump back
to the original slide. Question records without a notes-confirmed answer are
kept for review but never become teaching examples.
"""
from .labels import short_deck_label
from .questions import clean_explanation, parse_question_slide
from .text import (
    ANSWER_IN_NOTES,
    BOILERPLATE_EXACT,
    DEFINITION_LINE,
    FORMULA_LINE,
    OPTION_LETTERS,
    QUESTION_PROMPT_SPLIT,
    TITLE_NOISE,
    clean_lines,
    detect_code_language,
    looks_like_code,
)
from .gates import (
    DEFINITION_EQ,
    FORMULA_EQ,
    NOISE_TOKENS,
    PURE_MATH_LHS,
    clean_definition_line,
    clean_formula_line,
    concept_formula,
    formula_lhs_is_general,
)
from .flashcards import draft_flashcards
from .concepts import assemble_concepts, organize_all, organize_deck

__all__ = [
    "short_deck_label", "parse_question_slide", "clean_explanation",
    "ANSWER_IN_NOTES", "BOILERPLATE_EXACT", "DEFINITION_LINE", "FORMULA_LINE",
    "OPTION_LETTERS", "QUESTION_PROMPT_SPLIT", "TITLE_NOISE", "clean_lines",
    "detect_code_language", "looks_like_code",
    "DEFINITION_EQ", "FORMULA_EQ", "NOISE_TOKENS", "PURE_MATH_LHS",
    "clean_definition_line", "clean_formula_line", "concept_formula",
    "formula_lhs_is_general",
    "draft_flashcards", "assemble_concepts", "organize_all", "organize_deck",
]
