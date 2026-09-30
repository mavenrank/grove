"""Regression checks for transaction, retry and history boundaries (#26–30)."""
from __future__ import annotations

import json
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from contextlib import contextmanager

import pytest

from app import db, engine
from app.config import settings
from app.engine import runtime, scoring


def _answer(client, sid, q, option="a", key=None):
    return client.post(f"/api/test-sessions/{sid}/answer", params={"position": q["position"]},
                       json={"ticket": q["ticket"], "option": option, "idempotency_key": key})


def _snapshot(sid):
    with db.db.read() as conn:
        return {table: [tuple(r) for r in conn.execute(f"SELECT * FROM {table} WHERE session_id=?", (sid,))]
                for table in ("session_questions", "question_timing", "question_dwell_segments",
                              "score_summaries", "answer_receipts", "client_events")}


@pytest.mark.parametrize("terminal", ["submitted", "expired"])
def test_terminal_sessions_reject_all_new_interactions(client, session_factory, terminal):
    sid = session_factory()["session_id"]
    q = client.get(f"/api/test-sessions/{sid}/question/0").json()
    assert _answer(client, sid, q, "b").status_code == 200
    if terminal == "expired":
        with db.db.write() as conn:
            conn.execute("UPDATE test_sessions SET deadline_at='2000-01-01T00:00:00+00:00' WHERE id=?", (sid,))
        # First late answer must persist expiry, not roll it back.
        assert _answer(client, sid, q, "d").status_code == 410
    else:
        assert client.post(f"/api/test-sessions/{sid}/finish").status_code == 200
    before = _snapshot(sid)
    code = 410 if terminal == "expired" else 409
    for _ in range(2):
        responses = [
            _answer(client, sid, q, "d"),
            client.get(f"/api/test-sessions/{sid}/question"),
            client.get(f"/api/test-sessions/{sid}/question/0"),
            client.post(f"/api/test-sessions/{sid}/mark/0", json={"marked": True}),
            client.post(f"/api/test-sessions/{sid}/dwell", json={"position": 0, "seconds": 20}),
            client.post(f"/api/test-sessions/{sid}/events", json={"events": [{"type": "heartbeat"}]}),
        ]
        assert all(r.status_code == code for r in responses)
    assert _snapshot(sid) == before
    result = client.get(f"/api/test-sessions/{sid}/result").json()
    assert result["state"] == terminal
    assert result["per_question"][0]["chosen"] == "b"


def test_deadline_boundary_is_expired(client, session_factory, monkeypatch):
    sid = session_factory()["session_id"]
    deadline = db.parse_iso(db.get_session(sid)["deadline_at"])
    monkeypatch.setattr(db, "utcnow", lambda: deadline)
    assert client.get(f"/api/test-sessions/{sid}/question").status_code == 410
    assert db.get_session(sid)["state"] == "expired"
    assert db.get_score(sid) is not None


@pytest.mark.parametrize("state", ["active", "cancelled", "expired"])
def test_unfinalized_history_is_blocked(client, session_factory, state):
    sid = session_factory()["session_id"]
    with db.db.write() as conn:
        conn.execute("UPDATE test_sessions SET state=? WHERE id=?", (state, sid))
    r = client.get(f"/api/history/tests/{sid}")
    assert r.status_code == 409
    assert r.json() == {"detail": "not_finalized"}


def test_finalized_history_is_available(client, session_factory):
    sid = session_factory()["session_id"]
    assert client.post(f"/api/test-sessions/{sid}/finish").status_code == 200
    r = client.get(f"/api/history/tests/{sid}")
    assert r.status_code == 200
    assert r.json()["finalized"] is True
    assert len(r.json()["questions"]) == 5
    assert client.get("/api/history/tests/missing").status_code == 404


def test_answer_retries_survive_changes_rotation_reopen_and_finish(client, session_factory):
    sid = session_factory()["session_id"]
    q = client.get(f"/api/test-sessions/{sid}/question/0").json()
    first = _answer(client, sid, q, "a", "request-1")
    assert first.status_code == 200
    before = _snapshot(sid)
    assert _answer(client, sid, q, "a", "request-1").json() == first.json()
    assert _snapshot(sid) == before
    assert _answer(client, sid, q, "b", "request-1").json()["detail"] == "idempotency_conflict"
    q2 = client.get(f"/api/test-sessions/{sid}/question/0").json()
    assert _answer(client, sid, q2, "b", "request-2").status_code == 200
    assert _answer(client, sid, q, "a", "request-1").json() == first.json()
    assert db.get_question_row(sid, 0)["answer_option"] == "b"
    db.db.__init__(db.db.path)  # Reopen the existing disposable DB; receipts are persistent.
    assert client.post(f"/api/test-sessions/{sid}/finish").status_code == 200
    before = _snapshot(sid)
    assert _answer(client, sid, q, "a", "request-1").json() == first.json()
    assert _snapshot(sid) == before
    assert _answer(client, sid, q2, "d", "new-after-finish").status_code == 409
    with pytest.raises(engine.NotFoundError):
        engine.submit_answer(sid, 0, q["ticket"], "a", "different-learner", "request-1")


def test_retry_key_cannot_change_question_or_ticket(client, session_factory):
    sid = session_factory()["session_id"]
    q0 = client.get(f"/api/test-sessions/{sid}/question/0").json()
    assert _answer(client, sid, q0, key="k").status_code == 200
    q1 = client.get(f"/api/test-sessions/{sid}/question/1").json()
    assert _answer(client, sid, q1, key="k").json()["detail"] == "idempotency_conflict"
    q0new = client.get(f"/api/test-sessions/{sid}/question/0").json()
    assert _answer(client, sid, q0new, key="k").json()["detail"] == "idempotency_conflict"
    assert _answer(client, sid, q0new, key="").status_code == 422


def test_failed_answer_and_receipt_roll_back_together(client, session_factory):
    sid = session_factory()["session_id"]
    q = client.get(f"/api/test-sessions/{sid}/question/0").json()
    with db.db.write() as conn:
        conn.execute("""CREATE TRIGGER fail_receipt BEFORE INSERT ON answer_receipts
                        BEGIN SELECT RAISE(ABORT, 'simulated storage failure'); END""")
    with pytest.raises(sqlite3.IntegrityError, match="simulated storage failure"):
        engine.submit_answer(sid, 0, q["ticket"], "a", settings.default_learner, "k")
    row = db.get_question_row(sid, 0)
    assert row["answered"] == 0 and row["answer_option"] is None and row["is_correct"] is None
    assert _snapshot(sid)["answer_receipts"] == []
    with db.db.write() as conn:
        conn.execute("DROP TRIGGER fail_receipt")
    assert _answer(client, sid, q, key="k").status_code == 200


def test_failed_finalization_rolls_back_state(client, session_factory):
    sid = session_factory()["session_id"]
    with db.db.write() as conn:
        conn.execute("""CREATE TRIGGER fail_score BEFORE INSERT ON score_summaries
                        BEGIN SELECT RAISE(ABORT, 'simulated score failure'); END""")
    with pytest.raises(sqlite3.IntegrityError, match="simulated score failure"):
        engine.finish_session(sid, settings.default_learner)
    assert db.get_session(sid)["state"] == "active"
    assert db.get_score(sid) is None
    with db.db.write() as conn:
        conn.execute("DROP TRIGGER fail_score")
    assert client.post(f"/api/test-sessions/{sid}/finish").status_code == 200


@pytest.mark.parametrize("winner", ["answer", "finish"])
def test_answer_finish_race_across_independent_database_wrappers(client, session_factory, monkeypatch, winner):
    sid = session_factory()["session_id"]
    q = client.get(f"/api/test-sessions/{sid}/question/0").json()
    private = json.loads(db.get_question_row(sid, 0)["question_json"])
    correct = private["correct_option"]
    stores = {op: db.Database(db.db.path) for op in ("answer", "finish")}
    local = threading.local()
    holding, release, competing = threading.Event(), threading.Event(), threading.Event()

    @contextmanager
    def independent_write():
        op = local.op
        if op != winner:
            competing.set()
        with stores[op].write() as conn:
            yield conn

    monkeypatch.setattr(db.db, "write", independent_write)
    original = runtime._question if winner == "answer" else scoring.compute_score

    def pause(*args, **kwargs):
        if local.op == winner:
            holding.set()
            assert release.wait(5), "test synchronization timed out"
        return original(*args, **kwargs)

    monkeypatch.setattr(runtime if winner == "answer" else scoring,
                        "_question" if winner == "answer" else "compute_score", pause)

    def run(op):
        local.op = op
        if op == "answer":
            return engine.submit_answer(sid, 0, q["ticket"], correct, settings.default_learner, "race")
        return engine.finish_session(sid, settings.default_learner)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(run, winner)
        try:
            assert holding.wait(5)
            other = "finish" if winner == "answer" else "answer"
            second = pool.submit(run, other)
            assert competing.wait(5)
            with pytest.raises(TimeoutError):
                second.result(timeout=0.1)  # The SQLite write lock must block the competing transaction.
        finally:
            release.set()
        first.result(timeout=5)
        if winner == "finish":
            with pytest.raises(engine.TestFlowError, match="not active"):
                second.result(timeout=5)
        else:
            second.result(timeout=5)
    stored = db.get_question_row(sid, 0)
    score = db.get_score(sid)
    assert score["correct"] == (1 if winner == "answer" else 0)
    assert score["unanswered"] == (4 if winner == "answer" else 5)
    assert bool(stored["answered"]) == (winner == "answer")


def test_connections_enforce_foreign_keys_and_existing_database_is_preserved(session_factory):
    sid = session_factory()["session_id"]
    before = _snapshot(sid)
    with db.db.read() as conn:
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    with pytest.raises(sqlite3.IntegrityError):
        with db.db.write() as conn:
            assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
            conn.execute("INSERT INTO client_events (session_id, event_type, server_time, payload) VALUES ('orphan','event','now','{}')")
    # Simulate a database from the baseline, which had no receipt table.
    with sqlite3.connect(db.db.path) as legacy:
        legacy.execute("DROP TABLE answer_receipts")
    reopened = db.Database(db.db.path)
    with reopened.read() as conn:
        assert conn.execute("SELECT COUNT(*) FROM answer_receipts").fetchone()[0] == 0
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    assert _snapshot(sid) == before
