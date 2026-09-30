"""Spaced-repetition scheduler for flashcards (SM-2-lite).

Design goals (in order):
  1. Meaningful grading — every rating produces a visible, real interval.
  2. Simple — three ratings (again / good / easy), not Anki's four-plus jargon.
  3. Deterministic and testable — the transition function is pure; persistence
     lives in `db.activity`.

State model per card (row in `flashcard_schedule`; absent row = new card):
  ease          — multiplier, clamped to [1.3, 2.8], starts at 2.5
  interval_days — current gap; 0 means "still learning" (minutes-scale)
  due_at        — ISO UTC; the card is due when this <= now
  reps / lapses — review count / times forgotten

Transitions:
  again — forgot:        ease −0.20, streak resets, due in 10 minutes
  good  — recalled:      first time 1 day, then interval × ease
  easy  — recalled fast: first time 4 days, then interval × ease × 1.3, ease +0.15
Intervals are capped at 180 days so a healthy card still shows up sometimes.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Any

from . import db
from .content_engine.releases import load_release

RATINGS = ("again", "good", "easy")

EASE_START, EASE_MIN, EASE_MAX = 2.5, 1.3, 2.8
AGAIN_MINUTES = 10
INTERVAL_CAP_DAYS = 180.0
STRONG_DAYS = 21.0  # at this interval a card counts as "strong"

_FIRST_GOOD_DAYS = 1.0
_FIRST_EASY_DAYS = 4.0


# ---------------------------------------------------------------------------
# Pure transition logic (unit-tested without any database)
# ---------------------------------------------------------------------------

def next_state(*, ease: float, interval_days: float, reps: int, lapses: int,
               rating: str) -> dict[str, Any]:
    """Compute the post-rating state. `due_at` is an ISO string; also returns
    `interval_minutes` (what the UI shows on the grading buttons)."""
    if rating not in RATINGS:
        raise ValueError(f"rating must be one of {RATINGS}")

    if rating == "again":
        ease2 = max(EASE_MIN, round(ease - 0.20, 2))
        return {
            "ease": ease2, "interval_days": 0.0, "reps": 0, "lapses": lapses + 1,
            "due_at": db.iso(db.utcnow() + timedelta(minutes=AGAIN_MINUTES)),
            "interval_minutes": float(AGAIN_MINUTES),
        }

    reps2 = reps + 1
    if rating == "good":
        interval = _FIRST_GOOD_DAYS if interval_days < 1 else min(interval_days * ease, INTERVAL_CAP_DAYS)
        ease2 = ease
    else:  # easy
        interval = _FIRST_EASY_DAYS if interval_days < 1 else min(interval_days * ease * 1.3, INTERVAL_CAP_DAYS)
        ease2 = min(EASE_MAX, round(ease + 0.15, 2))

    return {
        "ease": ease2, "interval_days": round(interval, 4), "reps": reps2, "lapses": lapses,
        "due_at": db.iso(db.utcnow() + timedelta(days=interval)),
        "interval_minutes": interval * 24 * 60,
    }


def label_interval(minutes: float) -> str:
    """Human interval: '10 min', '3 h', '2 d', '1 mo'."""
    if minutes < 60:
        return f"{max(1, round(minutes))} min"
    hours = minutes / 60
    if hours < 24:
        return f"{round(hours)} h"
    days = hours / 24
    if days < 30:
        return f"{round(days)} d"
    return f"{round(days / 30)} mo"


def card_state_name(state: dict[str, Any] | None) -> str:
    """new → learning → review → strong."""
    if state is None:
        return "new"
    if state["interval_days"] >= STRONG_DAYS:
        return "strong"
    if state["interval_days"] < 1:
        return "learning"
    return "review"


def is_due(state: dict[str, Any] | None) -> bool:
    if state is None:
        return True  # new cards are always due
    return db.parse_iso(state["due_at"]) <= db.utcnow()


def preview_intervals(state: dict[str, Any] | None) -> dict[str, str]:
    """What each grading button would schedule, from the card's current state."""
    base = state or {"ease": EASE_START, "interval_days": 0.0, "reps": 0, "lapses": 0}
    out: dict[str, str] = {}
    for rating in RATINGS:
        nxt = next_state(rating=rating, **{k: base[k] for k in ("ease", "interval_days", "reps", "lapses")})
        out[rating] = label_interval(nxt["interval_minutes"])
    return out


# ---------------------------------------------------------------------------
# Persistence-backed operations
# ---------------------------------------------------------------------------

def rate_flashcard(flashcard_id: str, rating: str) -> dict[str, Any]:
    """Apply a rating and persist the new state. Returns the resulting state."""
    with db.db.read() as conn:
        row = conn.execute(
            "SELECT * FROM flashcard_schedule WHERE flashcard_id = ?", (flashcard_id,)
        ).fetchone()
    current = {
        "ease": row["ease"], "interval_days": row["interval_days"],
        "reps": row["reps"], "lapses": row["lapses"],
    } if row else {"ease": EASE_START, "interval_days": 0.0, "reps": 0, "lapses": 0}

    nxt = next_state(rating=rating, **current)
    db.upsert_schedule(
        flashcard_id,
        ease=nxt["ease"], interval_days=nxt["interval_days"], due_at=nxt["due_at"],
        reps=nxt["reps"], lapses=nxt["lapses"],
    )
    return nxt


def schedule_for(card_ids: list[str]) -> dict[str, dict[str, Any]]:
    return db.get_schedule_rows(card_ids)


def session_cards(cards: list[dict[str, Any]], *, limit: int,
                  topic_id: str | None = None,
                  sched_override: dict[str, dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Build a review session from release cards: due cards first (most
    overdue first), then never-reviewed cards, capped at `limit`.

    Every returned card carries `state`, `due`, `reps` and `intervals`
    (the per-rating schedule previews the UI shows on its buttons).

    `topic_id` filters to the skills of one topic; None means all topics.
    `sched_override` exists for tests to inject schedule state without a DB.
    """
    if topic_id is not None:
        from .content_engine.taxonomy import BUCKETS
        skill_ids = {s.id for b in BUCKETS for t in b.topics if t.id == topic_id for s in t.skills}
        cards = [c for c in cards if c.get("skill_id") in skill_ids]
    sched = sched_override if sched_override is not None else schedule_for([c["id"] for c in cards])
    due, fresh = [], []
    for card in cards:
        state = sched.get(card["id"])
        entry = {**card, "state": card_state_name(state), "due": is_due(state),
                 "reps": state["reps"] if state else 0,
                 "intervals": preview_intervals(state)}
        if state is None:
            fresh.append(entry)
        elif is_due(state):
            due.append(entry)
    due.sort(key=lambda c: sched[c["id"]]["due_at"])
    session = (due + fresh)[:limit]
    # session cards are the ones being served now — they're all "due" to review
    for entry in session:
        entry["due"] = True
    return session


def topic_decks(topic_map: dict[str, tuple[str, str, str]]) -> list[dict[str, Any]]:
    """Per-topic flashcard decks with SRS counts.

    `topic_map` maps skill_id → (topic_id, topic_name, bucket_name).
    """
    rel = load_release()
    cards = rel.get("flashcards", [])
    sched = schedule_for([c["id"] for c in cards])

    decks: dict[str, dict[str, Any]] = {}
    for card in cards:
        key = topic_map.get(card.get("skill_id", ""))
        if key is None:
            continue
        topic_id, topic_name, bucket_name = key
        deck = decks.setdefault(topic_id, {
            "topic_id": topic_id, "topic_name": topic_name, "bucket_name": bucket_name,
            "total_cards": 0, "due_cards": 0, "new_cards": 0, "strong_cards": 0,
        })
        deck["total_cards"] += 1
        state = sched.get(card["id"])
        if state is None:
            deck["new_cards"] += 1
        else:
            if is_due(state):
                deck["due_cards"] += 1
            if state["interval_days"] >= STRONG_DAYS:
                deck["strong_cards"] += 1

    out = sorted(decks.values(), key=lambda d: (d["bucket_name"], d["topic_name"]))
    for deck in out:
        deck["coverage"] = round(deck["strong_cards"] / deck["total_cards"], 4) if deck["total_cards"] else None
    return out
