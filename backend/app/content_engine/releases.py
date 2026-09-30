"""Content-release loading.

The backend serves only approved releases imported via `grove-ingest`.
If no release has been imported yet, a built-in bootstrap pack provides the
first concepts, flashcards, and family allowlist so the app works out of the box.
"""
from __future__ import annotations

import json
from typing import Any

from ..db import latest_release
from .families import family_skill_map
from .bootstrap_release import BOOTSTRAP_RELEASE

def load_release() -> dict[str, Any]:
    row = latest_release()
    if row is not None:
        payload = json.loads(row["payload"])
        payload = _merge_authored_content(payload)
        payload["_db_release_id"] = row["release_id"]
        return payload
    return _merge_authored_content(json.loads(json.dumps(BOOTSTRAP_RELEASE)))


def family_skill_map() -> dict[str, str]:
    """Adapter: family_id -> skill_id for the active release's allowlist.

    Single seam for evidence/history joins; plugin families register into the
    same registry this reads from.
    """
    return {f["family_id"]: f["skill_id"] for f in load_release().get("families", [])}


def _merge_authored_content(payload: dict[str, Any]) -> dict[str, Any]:
    """Merge the authored generator allowlist into any release payload.

    Ingested packs supply concepts/flashcards/media; the shipped deterministic
    families remain the reviewed question source for tests.
    """
    payload.setdefault("concepts", [])
    payload.setdefault("flashcards", [])
    payload.setdefault("questions", [])
    payload.setdefault("notes", [])
    payload["families"] = [dict(f) for f in BOOTSTRAP_RELEASE["families"]]
    for c in payload.get("concepts", []):
        _normalize_concept(c)
    return payload


def _normalize_concept(c: dict[str, Any]) -> None:
    """Give every concept the current public shape, regardless of pack vintage."""
    c.setdefault("summary", "")
    c.setdefault("examples", [])
    c.setdefault("media", [])
    c.setdefault("formulas", [])
    c.setdefault("code_blocks", [])
    c.setdefault("common_mistakes", [])
    c.setdefault("related_families", [])
    if "worked_example" in c and c["worked_example"]:
        c.setdefault("examples", [])
        if not c["examples"]:
            c["examples"] = [{
                "prompt": str(c["worked_example"])[:400],
                "options": {},
                "answer": None,
                "explanation": "",  # blank on purpose: no provenance to add
            }]
        c.pop("worked_example", None)
