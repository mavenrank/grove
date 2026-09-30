"""Security boundary tests (handoff §18 security test list)."""
from __future__ import annotations

import time

from app import db as dbmod


def test_no_answer_key_in_public_question(client, session_factory):
    s = session_factory(5)
    q = client.get(f"/api/test-sessions/{s['session_id']}/question").json()
    blob = str(q).lower()
    for forbidden in ("correct", "answer_index", "explanation", "is_correct",
                      "answer_hash", "grading", "difficulty", "family_id", "skill_id"):
        assert forbidden not in blob, f"leaked: {forbidden}"


def test_no_answer_key_across_all_positions(client, session_factory):
    s = session_factory(10)
    for pos in range(10):
        q = client.get(f"/api/test-sessions/{s['session_id']}/question/{pos}").json()
        blob = str(q).lower()
        assert "explanation" not in blob
        assert "correct" not in blob


def test_expiry_rejects_answers_and_finalizes(client, session_factory):
    s = session_factory(5)
    sid = s["session_id"]
    q = client.get(f"/api/test-sessions/{sid}/question/0").json()

    # force expiry by backdating the deadline
    with dbmod.db.write() as conn:
        conn.execute("UPDATE test_sessions SET deadline_at='2000-01-01T00:00:00+00:00', expires_at='2000-01-01T00:00:00+00:00' WHERE id=?", (sid,))

    r = client.post(f"/api/test-sessions/{sid}/answer", params={"position": 0},
                    json={"ticket": q["ticket"], "option": "a"})
    assert r.status_code == 410
    assert r.json()["detail"] == "expired"

    fin = client.post(f"/api/test-sessions/{sid}/finish")
    assert fin.status_code == 200
    assert fin.json()["state"] == "expired"
    assert fin.json()["score"]["correct"] + fin.json()["score"]["incorrect"] + fin.json()["score"]["unanswered"] == 5


def test_rate_limit_session_creation(client, fresh_db):
    codes = []
    for _ in range(20):
        r = client.post("/api/test-sessions", json={"question_count": 5})
        codes.append(r.status_code)
        if r.status_code in (429, 503):
            break
    assert 429 in codes, f"session creation should be rate limited, got {codes}"


def test_no_store_on_personalized_routes(client, session_factory):
    s = session_factory(5)
    r = client.get(f"/api/test-sessions/{s['session_id']}/question")
    assert r.headers.get("cache-control") == "no-store"
    h = client.get("/api/history")
    assert h.headers.get("cache-control") == "no-store"


def test_security_headers_present(client):
    r = client.get("/api/health")
    assert r.headers.get("x-content-type-options") == "nosniff"
    assert (r.headers.get("x-frame-options") or "").lower() == "deny"


def test_events_payload_sanitized(client, session_factory):
    s = session_factory(5)
    huge = "x" * 5000
    r = client.post(f"/api/test-sessions/{s['session_id']}/events", json={
        "events": [{"type": "question_shown", "position": 0, "payload": {"note": huge}}]
    })
    assert r.status_code == 200
    with dbmod.db.read() as conn:
        row = conn.execute(
            "SELECT payload FROM client_events WHERE session_id=? ORDER BY id DESC LIMIT 1",
            (s["session_id"],),
        ).fetchone()
    import json
    payload = json.loads(row["payload"])
    assert len(payload["note"]) <= 512
