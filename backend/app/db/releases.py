"""Content-store queries: immutable published releases."""
from __future__ import annotations

import json
import sqlite3
from typing import Any

from .connection import db
from .timeutil import iso, utcnow


def import_release(release_id: str, version: str, manifest: dict[str, Any], payload: dict[str, Any]) -> bool:
    """Import an immutable release. Returns False if this version already exists."""
    with db.write() as conn:
        existing = conn.execute(
            "SELECT 1 FROM content_releases WHERE release_id=? AND version=?",
            (release_id, version),
        ).fetchone()
        if existing:
            return False
        conn.execute(
            "INSERT INTO content_releases (release_id, version, created_at, manifest, payload) VALUES (?,?,?,?,?)",
            (release_id, version, iso(utcnow()), json.dumps(manifest), json.dumps(payload)),
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
