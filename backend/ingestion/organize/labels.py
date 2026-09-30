"""Learner-facing deck labels.

The corpus names files
  <provider>__<course-code>__<NNN>__<CONTENT_TITLE>__<date>[__PINNED].<ext>
Citations should read "Percentages 1 · Slide 5", not the whole slug.
"""
from __future__ import annotations

import re

_DATE_PART = re.compile(r"^\d{4}[-_]\d{2}([-_]\d{2})?$")


def short_deck_label(source_file: str) -> str:
    """Derive a human citation name from a corpus filename."""
    stem = re.sub(r"\.(pptx|pdf|docx)$", "", source_file, flags=re.I)
    parts = [p for p in stem.split("__") if p]
    if len(parts) >= 2:
        # the content title follows the last all-numeric ordering part
        title_idx = None
        for i, p in enumerate(parts):
            if p.strip().isdigit():
                title_idx = i + 1
        if title_idx is not None and title_idx < len(parts):
            title = parts[title_idx]
        else:
            title = next((p for p in reversed(parts) if not _DATE_PART.match(p)), parts[-1])
    else:
        title = stem
    words = [w for w in title.replace("_", " ").split() if w and not _DATE_PART.match(w)]
    label = " ".join(words).strip().title()
    if len(label) > 60:
        label = label[:57].rstrip() + "…"
    return label or stem[:60]
