"""Content-store queries: immutable published releases."""
from __future__ import annotations

import json
import sqlite3
from typing import Any

from .connection import db
from .timeutil import iso, utcnow


def import_release(release_id: str, version: str, manifest: dict[str, Any], payload: dict[str, Any]) -> bool:
    """Import once; identical retries return False, changed versions fail (#31)."""
    def canonical(value: dict) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

    manifest_json, payload_json = canonical(manifest), canonical(payload)
    with db.write() as conn:
        existing = conn.execute(
            "SELECT manifest, payload FROM content_releases WHERE release_id=? AND version=?",
            (release_id, version),
        ).fetchone()
        if existing:
            if (canonical(json.loads(existing["manifest"])) != manifest_json
                    or canonical(json.loads(existing["payload"])) != payload_json):
                raise ValueError(f"immutable release conflict: {release_id} v{version}; choose a new version")
            return False
        conn.execute(
            "INSERT INTO content_releases (release_id, version, created_at, manifest, payload) VALUES (?,?,?,?,?)",
            (release_id, version, iso(utcnow()), manifest_json, payload_json),
        )
    return True


def latest_release() -> sqlite3.Row | None:
    with db.read() as conn:
        row = conn.execute(
            """
            SELECT * FROM content_releases
            ORDER BY created_at DESC, version DESC
            LIMIT 1
            """
        ).fetchone()
    return row
