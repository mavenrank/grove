"""Session creation: materialize the plan into server-held questions."""
from __future__ import annotations

import json
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any

from .. import db
from ..config import settings
from ..content_engine.deterministic import make_rng
from ..content_engine.families import generate_question
from ..content_engine.releases import load_release
from .errors import TestFlowError
from .planning import plan_session


def create_session(question_count: int, learner: str,
                   duration_minutes: int | None = None) -> dict[str, Any]:
    if question_count not in settings.allowed_question_counts:
        raise TestFlowError("invalid_question_count", "question count must be one of "
                            f"{settings.allowed_question_counts}")
    release = load_release()
    release_id = release.get("release_id", "grove-bootstrap")
    release_version = release.get("version", "0.0.0")

    seed = secrets.token_hex(16)
    session_id = str(uuid.uuid4())
    # Custom duration is server-owned: default is 1 min/question; a custom
    # value (minutes) is clamped to sane bounds so the deadline stays real.
    duration = question_count * settings.seconds_per_question
    if duration_minutes is not None:
        duration = max(60, min(int(duration_minutes) * 60, 3 * 60 * 60))

    plan = plan_session(question_count, seed)

    with db.db.write() as conn:  # transactional: session + questions together
        now = db.utcnow()
        deadline = now.timestamp() + duration
        now_iso, deadline_iso = db.iso(now), db.iso(datetime.fromtimestamp(deadline, timezone.utc))

        conn.execute(
            """
            INSERT INTO test_sessions
              (id, learner, state, question_count, duration_seconds, seed,
               blueprint_version, release_id, release_version,
               created_at, started_at, deadline_at, expires_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (session_id, learner, "active", question_count, duration, seed,
             settings.blueprint_version, release_id, release_version,
             now_iso, now_iso, deadline_iso, deadline_iso),
        )
        for position, item in enumerate(plan):
            # family id in the allowlist equals the generator family id
            q = generate_question(item["family_id"], item["difficulty"],
                                  (seed, session_id, position))
            options = q["options"]
            answer_index = q["answer_index"]
            perm = list(range(len(options)))
            prng = make_rng("permute", seed, session_id, position)
            prng.shuffle(perm)
            public_options = [{"id": oid, "text": options[perm[i]]}
                              for i, oid in enumerate(["a", "b", "c", "d"][: len(options)])]
            correct_option = ["a", "b", "c", "d"][perm.index(answer_index)] if answer_index in perm else "a"

            public_payload = {
                "ticket": secrets.token_urlsafe(24),
                "position": position,
                "prompt": q["prompt"],
                "options": public_options,
                "expires_at": deadline_iso,
            }
            private_payload = {
                "family_id": q["family_id"],
                "skill_id": q["skill_id"],
                "difficulty": q["difficulty"],
                "prompt": q["prompt"],
                "options": public_options,
                "correct_option": correct_option,
                "explanation": q["explanation"],
            }
            conn.execute(
                """
                INSERT INTO session_questions
                  (session_id, position, ticket, family_id, question_ref,
                   question_json, public_json, answered, marked)
                VALUES (?,?,?,?,?,?,?,0,0)
                """,
                (session_id, position, public_payload["ticket"], q["family_id"],
                 f"{q['family_id']}@{position}", json.dumps(private_payload),
                 json.dumps(public_payload)),
            )

    return {
        "session_id": session_id,
        "question_count": question_count,
        "duration_seconds": duration,
        "deadline_at": deadline_iso,
        "blueprint_version": settings.blueprint_version,
        "release_id": release_id,
        "release_version": release_version,
    }
