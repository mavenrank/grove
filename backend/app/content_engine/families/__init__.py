"""Question-family plugins package.

`registry.py` holds the registration API; sibling modules are the built-in
family plugins, auto-loaded below at import time. External code can add more
families at runtime via `registry.register_family` without touching core.
"""
from .registry import (  # noqa: F401
    FAMILIES,
    FAMILY_SKILLS,
    all_family_ids,
    family,
    family_skill_map,
    generate_question,
    register_family,
)

# Built-in family plugins — import order = registration order, grouped by
# domain so each module stays small and independently reviewable.
from . import numbers, frp, averages, timeworkspeed, algebra, series, relations, arrangements, coding  # noqa: E402,F401
