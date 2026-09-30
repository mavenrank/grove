"""Stage 3 loop: create → question → answer → events → finish → score."""
from __future__ import annotations


def test_create_session(session_factory):
    s = session_factory(5)
    assert s["question_count"] == 5
    assert s["duration_seconds"] == 300
    assert s["deadline_at"]


def test_question_payload_is_allowlisted(client, session_factory):
    s = session_factory(5)
    resp = client.get(f"/api/test-sessions/{s['session_id']}/question")
    assert resp.status_code == 200
    q = resp.json()
    # explicit allowlist: nothing else may leak (handoff §8.6)
    allowed = {"session_id", "ticket", "position", "total_questions", "prompt",
               "options", "expires_at", "answered", "marked"}
    assert set(q.keys()) == allowed
    for opt in q["options"]:
        assert set(opt.keys()) == {"id", "text"}
        assert opt["id"] in ("a", "b", "c", "d")


def test_full_loop_scores_correctly(client, session_factory):
    s = session_factory(5)
    sid = s["session_id"]
    correct_first_time = 0
    total = s["question_count"]

    for pos in range(total):
        q = client.get(f"/api/test-sessions/{sid}/question/{pos}").json()
        # probe: we can't know the right answer from the payload — submit 'a'
        r = client.post(f"/api/test-sessions/{sid}/answer",
                        params={"position": pos},
                        json={"ticket": q["ticket"], "option": "a", "idempotency_key": f"k{pos}"})
        assert r.status_code == 200, r.text

    ev = client.post(f"/api/test-sessions/{sid}/events", json={
        "events": [
            {"type": "question_shown", "position": 0, "client_time": 0.0, "payload": {}},
            {"type": "test_started", "client_time": 0.0, "payload": {}},
        ]
    })
    assert ev.status_code == 200 and ev.json()["accepted"] == 2

    fin = client.post(f"/api/test-sessions/{sid}/finish")
    assert fin.status_code == 200
    result = fin.json()
    assert result["score"]["total_questions"] == total
    assert result["score"]["correct"] + result["score"]["incorrect"] == total
    assert 0.0 <= result["score"]["accuracy"] <= 1.0
    for pq in result["per_question"]:
        assert set(pq.keys()) >= {"position", "answered", "is_correct", "chosen", "correct_option", "explanation"}


def test_duplicate_finalization_rejected(client, session_factory):
    s = session_factory(5)
    sid = s["session_id"]
    for pos in range(5):
        q = client.get(f"/api/test-sessions/{sid}/question/{pos}").json()
        client.post(f"/api/test-sessions/{sid}/answer", params={"position": pos},
                    json={"ticket": q["ticket"], "option": "b"})
    first = client.post(f"/api/test-sessions/{sid}/finish")
    assert first.status_code == 200
    second = client.post(f"/api/test-sessions/{sid}/finish")
    assert second.status_code == 409
    assert second.json()["detail"] == "already_finalized"


def test_answer_rejected_after_finalize(client, session_factory):
    s = session_factory(5)
    sid = s["session_id"]
    q = client.get(f"/api/test-sessions/{sid}/question").json()
    for pos in range(5):
        qq = client.get(f"/api/test-sessions/{sid}/question/{pos}").json()
        client.post(f"/api/test-sessions/{sid}/answer", params={"position": pos},
                    json={"ticket": qq["ticket"], "option": "a"})
    client.post(f"/api/test-sessions/{sid}/finish")
    late = client.post(f"/api/test-sessions/{sid}/answer", params={"position": 0},
                       json={"ticket": q["ticket"], "option": "b"})
    assert late.status_code == 409


def test_invalid_option_rejected(client, session_factory):
    s = session_factory(5)
    sid = s["session_id"]
    q = client.get(f"/api/test-sessions/{sid}/question").json()
    r = client.post(f"/api/test-sessions/{sid}/answer", params={"position": 0},
                    json={"ticket": q["ticket"], "option": "z"})
    assert r.status_code in (409, 422)


def test_stale_ticket_rejected(client, session_factory):
    s = session_factory(5)
    sid = s["session_id"]
    q1 = client.get(f"/api/test-sessions/{sid}/question").json()
    q2 = client.get(f"/api/test-sessions/{sid}/question").json()  # rotates the ticket
    r = client.post(f"/api/test-sessions/{sid}/answer", params={"position": q1["position"]},
                    json={"ticket": q1["ticket"], "option": "a"})
    assert r.status_code == 409
    r2 = client.post(f"/api/test-sessions/{sid}/answer", params={"position": q2["position"]},
                     json={"ticket": q2["ticket"], "option": "a"})
    assert r2.status_code == 200


def test_unknown_session_404(client):
    r = client.get("/api/test-sessions/nonexistent/question")
    assert r.status_code == 404


def test_events_bounded(client, session_factory):
    s = session_factory(5)
    sid = s["session_id"]
    big = [{"type": "heartbeat", "client_time": float(i), "payload": {}} for i in range(250)]
    r = client.post(f"/api/test-sessions/{sid}/events", json={"events": big})
    assert r.status_code == 422  # pydantic max_length guard


def test_result_before_finish_rejected(client, session_factory):
    s = session_factory(5)
    r = client.get(f"/api/test-sessions/{s['session_id']}/result")
    assert r.status_code == 409


def test_history_and_insights_after_finish(client, session_factory):
    s = session_factory(5)
    sid = s["session_id"]
    for pos in range(5):
        q = client.get(f"/api/test-sessions/{sid}/question/{pos}").json()
        client.post(f"/api/test-sessions/{sid}/answer", params={"position": pos},
                    json={"ticket": q["ticket"], "option": "a"})
    client.post(f"/api/test-sessions/{sid}/finish")
    client.post("/api/concept-views", json={"concept_id": "concept.percentages-basics", "title": "Percentages"})
    client.post("/api/flashcard-reviews", json={"flashcard_id": "fc.pct-1", "action": "remember"})

    h = client.get("/api/history")
    assert h.status_code == 200
    body = h.json()
    assert any(t["session_id"] == sid for t in body["tests"])
    assert any(l["concept_id"] == "concept.percentages-basics" for l in body["learning"])
    assert any(f["flashcard_id"] == "fc.pct-1" for f in body["flashcards"])

    ins = client.get("/api/insights")
    assert ins.status_code == 200
    skills = ins.json()["skills"]
    assert skills, "finalized session should produce skill evidence"
    total_attempts = sum(x["attempts"] for x in skills)
    assert total_attempts >= 5
