"""Ingestion pipeline for Grove: PPTX/PDF source material → reviewable JSON → content packs.

Flow (handoff §13):
    discover → extract (python-pptx, provenance preserved)
             → classify (rule-based bucket/topic/skill)
             → normalize (JSON records)
             → validate (schema, duplicates, active-bucket checks)
             → pack (immutable content pack, after human review)
             → import (into the backend SQLite store)
"""
from .pipeline import Pipeline  # noqa: F401
