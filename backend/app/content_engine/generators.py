"""Deprecated shim — the family registry moved to `families/`.

Historical import path kept working on purpose (`generate_question` was the
engine's seam into question generation). New code should import from
`app.content_engine.families` (or `families.registry` for the raw API).
"""
from .families import (  # noqa: F401
    FAMILIES,
    FAMILY_SKILLS,
    all_family_ids,
    family,
    family_skill_map,
    generate_question,
    register_family,
)
