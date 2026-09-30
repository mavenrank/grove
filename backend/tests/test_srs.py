"""SRS scheduler: pure-transition tests (no database) plus a rate round-trip."""
from __future__ import annotations

import pytest

from app import srs
from app.db.timeutil import parse_iso


def st(ease=2.5, interval=0.0, reps=0, lapses=0):
    return {"ease": ease, "interval_days": interval, "reps": reps, "lapses": lapses}


class TestTransitions:
    def test_again_resets_and_shows_minutes(self):
        nxt = srs.next_state(rating="again", **st(interval=10.0, reps=5, lapses=1))
        assert nxt["interval_days"] == 0.0
        assert nxt["reps"] == 0                 # streak resets
        assert nxt["lapses"] == 2
        assert nxt["interval_minutes"] == 10.0
        assert srs.label_interval(nxt["interval_minutes"]) == "10 min"
        assert parse_iso(nxt["due_at"]) > parse_iso(__import__("app.db", fromlist=["iso"]).iso(parse_iso("2000-01-01T00:00:00+00:00")))

    def test_again_eases_down_with_floor(self):
        nxt = srs.next_state(rating="again", **st(ease=1.35))
        assert nxt["ease"] == srs.EASE_MIN      # clamped, never below 1.3

    def test_good_first_review_is_one_day(self):
        nxt = srs.next_state(rating="good", **st())
        assert nxt["interval_days"] == 1.0
        assert nxt["reps"] == 1

    def test_good_multiplies_by_ease(self):
        nxt = srs.next_state(rating="good", **st(interval=2.0))
        assert nxt["interval_days"] == pytest.approx(2.0 * 2.5)

    def test_easy_first_review_is_four_days(self):
        nxt = srs.next_state(rating="easy", **st())
        assert nxt["interval_days"] == 4.0

    def test_easy_raises_ease_with_ceiling(self):
        nxt = srs.next_state(rating="easy", **st(ease=2.75, interval=10.0))
        assert nxt["ease"] == srs.EASE_MAX
        assert nxt["interval_days"] == pytest.approx(10.0 * 2.75 * 1.3)

    def test_interval_capped_at_180_days(self):
        nxt = srs.next_state(rating="good", **st(ease=2.8, interval=170.0))
        assert nxt["interval_days"] == srs.INTERVAL_CAP_DAYS

    def test_invalid_rating_rejected(self):
        with pytest.raises(ValueError):
            srs.next_state(rating="hard", **st())


class TestLabels:
    def test_human_intervals(self):
        assert srs.label_interval(0.5) == "1 min"
        assert srs.label_interval(10) == "10 min"
        assert srs.label_interval(60 * 3) == "3 h"
        assert srs.label_interval(60 * 24 * 2) == "2 d"
        assert srs.label_interval(60 * 24 * 45) == "2 mo"  # 45 d -> 2 mo (banker's round: 1.5 -> 2)


class TestCardStates:
    def test_state_names(self):
        assert srs.card_state_name(None) == "new"
        assert srs.card_state_name({"interval_days": 0.0}) == "learning"
        assert srs.card_state_name({"interval_days": 3.0}) == "review"
        assert srs.card_state_name({"interval_days": 30.0}) == "strong"

    def test_preview_for_new_card(self):
        p = srs.preview_intervals(None)
        assert p == {"again": "10 min", "good": "1 d", "easy": "4 d"}


class TestSessionOrdering:
    def test_due_first_then_new_capped(self):
        from datetime import timedelta
        now = srs.db.utcnow()
        cards = [{"id": f"c{i}", "skill_id": "s"} for i in range(5)]
        sched = {
            "c1": {"ease": 2.5, "interval_days": 1.0, "reps": 1, "lapses": 0,
                   "due_at": srs.db.iso(now - timedelta(days=2))},   # most overdue
            "c0": {"ease": 2.5, "interval_days": 1.0, "reps": 1, "lapses": 0,
                   "due_at": srs.db.iso(now - timedelta(days=1))},
            "c4": {"ease": 2.5, "interval_days": 5.0, "reps": 2, "lapses": 0,
                   "due_at": srs.db.iso(now + timedelta(days=3))},   # future: excluded
        }
        session = srs.session_cards(cards, sched_override=sched, limit=3)
        assert [c["id"] for c in session] == ["c1", "c0", "c2"]
        assert all(c["due"] for c in session)
        assert session[0]["intervals"]["good"] == "2 d"  # 1d * ease 2.5 = 2.5d, round-half-even
