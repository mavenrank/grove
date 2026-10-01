"""Text hygiene shared by every organizer: furniture removal, code detection."""
from __future__ import annotations

import re

QUESTION_PROMPT_SPLIT = re.compile(r"^\s*([A-Ea-e])\s*[).:]\s*(.*)$")
ANSWER_IN_NOTES = re.compile(r"Answer\s*(?:is)?\s*[:\-]?\s*([A-Ea-e])\b\.?(.*)", re.S)
FORMULA_LINE = re.compile(r"[=×÷±√]|%\s*of\b|\bper cent\b|\bpercentage\b", re.I)
DEFINITION_LINE = re.compile(r"\b(is|are|means|refers to|called|defined as)\b", re.I)
OPTION_LETTERS = ("a", "b", "c", "d", "e")

TITLE_NOISE = re.compile(
    r"topic/course|sub-topic|course\s*file|faculty|vit\b|session\s*\d|page\s*\d",
    re.I,
)
# Slide furniture that adds no teaching value.
BOILERPLATE_EXACT = {
    "thank you", "thank you!", "thanks", "any questions", "questions?",
    "q&a", "summary", "agenda", "objectives", "conclusion",
}

# ---------------------------------------------------------------------------
# Code-block detection: keep code AS CODE (formatted, labelled) instead of
# dropping it or letting it pollute formulas.
# ---------------------------------------------------------------------------
CODE_LANG_HINTS: list[tuple[str, re.Pattern]] = [
    ("python", re.compile(r"^\s*(def |class |import \w|from \w+ import|print\(|elif |self\.)", re.M)),
    ("java", re.compile(r"(public\s+(static\s+)?(class|void|int|double)|System\.out|Scanner\s|ArrayList<|HashMap<)")),
    ("c", re.compile(r"(#include\s*<|printf\(|scanf\(|int main\s*\()")),
    ("cpp", re.compile(r"(std::|cout\s*<<|cin\s*>>|#include\s*<bits|vector<)")),
    ("sql", re.compile(r"\b(select\b.+\bfrom\b|insert\s+into|create\s+table)", re.I)),
    ("pseudo", re.compile(r"\b(for each|repeat until|while true|if .* then\b)")),
]

CODE_LINE_STRONG = re.compile(
    r"(^\s*(for|while|if|else|elif|switch|case|return|def|class|print)\b[^a-z]{0,3}|[;{}]\s*$|"
    r"\b(int|char|float|double|long|void|bool|static|public|private|new)\s+\w|"
    r"==|!=|<=|>=|\+\+|--|\+=|System\.|cout|printf|Scanner|ArrayList|\w+\(.*\)\s*\{)",
)


def detect_code_language(code: str) -> str:
    for lang, pat in CODE_LANG_HINTS:
        if pat.search(code):
            return lang
    return "text"


def looks_like_code(text: str) -> bool:
    """A text frame is a code block if most of its lines look like source."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if len(lines) < 2:
        return False
    codey = sum(1 for ln in lines if CODE_LINE_STRONG.search(ln))
    return codey / len(lines) >= 0.6


def clean_lines(texts: list[str]) -> list[str]:
    out = []
    for t in texts:
        for line in t.splitlines():
            line = line.strip()
            if not line or TITLE_NOISE.search(line):
                continue
            if line.lower().strip(" .!") in BOILERPLATE_EXACT:
                continue
            out.append(line)
    return out
