"""Gates that decide which mined lines may become formulas / rules / cards.

Code fragments, example-specific narratives and context-free fragments must
never reach a learner-facing formula, flashcard or concept section.
"""
from __future__ import annotations

import re

# Code fragments and narrative debris that must never become a flashcard.
NOISE_TOKENS = re.compile(
    r"if\s*\(|for\s*\(|while\s*\(|\belse\b|Scanner|String\s|new\s|return\b|System\.|import\s|"
    r"public\s|void\s|class\s|\.get|\bint\b|\bchar\b|\bfloat\b|\bdouble\b|\blong\b|\bbool\b|"
    r"==|;|\{|\}|\.length\(|\.append\(|\bcout\b|\bcin\b|printf|scanf|#include|\blis\b|\blds\b|"
    r"\bhence\b|in this case|…|\.\.\.",
    re.I,
)
# A clean formula line: term-ish LHS, then '=', then a value.
# (ASCII / . + - included: '1/2 = 50%', 'x + y = 10', '0.5 = 50%')
FORMULA_EQ = re.compile(r"^([A-Za-z0-9 ⁄/.+×÷%√()²³'\-]{3,60}?)\s*=\s*(.{3,120})$")
# A definable term: 'X is/are/refers to/is called/is defined as ...'
DEFINITION_EQ = re.compile(r"^([A-Z][A-Za-z0-9 %⁄×÷()\-]{2,40}?)\s+(is|are|refers to|is called|is defined as)\s+(.{25,})$")

# Example-specific left-hand sides mix digits with prose ("3 green lights =");
# genuinely general math facts are either pure math ("1/2 = 50%") or word terms.
PURE_MATH_LHS = re.compile(r"^[\d\s⁄/×÷%√().²³+-]+$")


def formula_lhs_is_general(lhs: str) -> bool:
    """True if an LHS reads like a general rule, not one puzzle's mapping."""
    lhs = lhs.strip()
    has_digit = any(ch.isdigit() for ch in lhs)
    has_alpha = any(ch.isalpha() for ch in lhs)
    if has_digit and has_alpha:
        return False  # '3 green lights = 60 kmph' — one puzzle's mapping
    if has_digit and not has_alpha:
        # pure-math fact is fine only when it is an actual relation (1/2, x²),
        # not a bare number assigned a value ('1 = 100 %')
        return bool(re.search(r"[⁄/×÷%√^]", lhs))
    # one-word alpha LHS ('Quotient = ?', 'Max = ?') are context-free fragments;
    # the authored card library covers the genuine one-word formulas
    if has_alpha and " " not in lhs:
        return False
    return True


def clean_formula_line(line: str) -> tuple[str, str] | None:
    """Return (front, back) for a genuine formula line, else None.

    Rejects code fragments ('if(n = ...'), example-specific narratives
    ('In this case, N = ...'), and truncated bullets ('... = ?…').
    """
    line = re.sub(r"\s+", " ", line).strip()
    if NOISE_TOKENS.search(line):
        return None
    m = FORMULA_EQ.match(line)
    if not m:
        return None
    lhs, rhs = m.group(1).strip(), m.group(2).strip()
    if not formula_lhs_is_general(lhs):
        return None
    if lhs.lower().startswith(("in ", "the ", "this ", "his ", "her ", "their ", "all ", "some ", "it ", "and ", "or ", "so ",
                               "if ", "for ", "while ", "int ", "else ", "case ", "switch ", "return ", "void ", "print ",
                               "to ", "we ", "then ", "now ", "here ", "there ", "given ", "using ", "let ")):
        return None
    if lhs.endswith((",", "(", ":", ";", "?")) or rhs.endswith((",", "(", ";")):
        return None
    # fragment of code or a list item like '1) x = ...'
    if re.match(r"^\d+[).:]\s*", lhs):
        return None
    return lhs, line


def concept_formula(line: str) -> str | None:
    """A math-shaped rule line, fit to display under 'Formulas & rules'.

    Stricter than the raw '='-contains heuristic: rejects prose sentences that
    merely mention an equation ('The code starts with x = 1 and increments…'),
    code input literals ('num= [5, 7]'), numbered walkthrough steps, backticked
    fragments, and chained worked arithmetic ('M = 105, M/m = 35') that belongs
    to a worked example, not to the rule itself.
    """
    line = re.sub(r"\s+", " ", line).strip()
    if "`" in line or any(ch in line for ch in "[]{}"):
        return None
    if line.count("=") >= 2:  # chained calculation → example material
        return None
    cleaned = clean_formula_line(line)
    if not cleaned:
        return None
    return cleaned[1]


def clean_definition_line(line: str) -> tuple[str, str] | None:
    """Return (term, full_line) for a clean definition sentence, else None."""
    line = re.sub(r"\s+", " ", line).strip()
    if NOISE_TOKENS.search(line) or not (40 <= len(line) <= 220):
        return None
    m = DEFINITION_EQ.match(line)
    if not m:
        return None
    term = m.group(1).strip()
    if term.count(" ") > 4 or term.endswith((",", "(", ":")):
        return None
    # narrative subjects ('The nodes are sorted...', 'If ages are...') are not concepts
    if re.match(r"^(the|a|an|this|that|these|those|such|all|some|any|it|there|his|her|their|our|we|they|hence|so|if|what|when|where|why|how|which|whose)\b",
                term, re.I):
        return None
    return term, line
