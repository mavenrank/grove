"""Same-version changes must fail without altering saved release meaning."""
import json

import pytest

from app.db import db, import_release


def test_identical_retry_is_idempotent_despite_json_key_order(fresh_db):
    assert import_release("sample", "1", {"a": 1, "b": 2}, {"title": "Lesson", "items": [1, 2]})
    assert not import_release("sample", "1", {"b": 2, "a": 1}, {"items": [1, 2], "title": "Lesson"})
    with db.read() as conn:
        assert conn.execute("SELECT count(*) FROM content_releases").fetchone()[0] == 1


@pytest.mark.parametrize("change", ["manifest", "payload"])
def test_conflict_rolls_back_and_new_version_preserves_old_release(fresh_db, change):
    manifest, payload = {"generated_at": "original"}, {"title": "Original lesson"}
    assert import_release("sample", "1", manifest, payload)
    with pytest.raises(ValueError, match="immutable release conflict"):
        import_release("sample", "1", {"generated_at": "different"} if change == "manifest" else manifest,
                       {"title": "Changed lesson"} if change == "payload" else payload)
    assert import_release("sample", "2", manifest, {"title": "New lesson"})
    with db.read() as conn:
        rows = conn.execute("SELECT version, manifest, payload FROM content_releases ORDER BY version").fetchall()
    assert len(rows) == 2
    assert json.loads(rows[0]["manifest"]) == manifest
    assert json.loads(rows[0]["payload"]) == payload
