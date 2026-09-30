"""Server-authoritative test engine.

Decomposed modules:
  errors   — TestFlowError / NotFoundError protocol exceptions
  planning — seeded, reproducible (family, difficulty) planning
  creation — session + question materialization (answers stay server-held)
  runtime  — question serving, dwell segments, mark-for-review, answering
  scoring  — atomic finalization, score computation, result payloads

The client can only ever influence *what it sends*; it can never influence
*what is correct* or *what the score is*.
"""
from .errors import NotFoundError, TestFlowError
from .planning import plan_session
from .creation import create_session
from .runtime import (
    get_current_question,
    get_question_at,
    mark_question,
    record_dwell,
    record_events,
    submit_answer,
)
from .scoring import compute_score, finish_session, get_result

__all__ = [
    "NotFoundError", "TestFlowError", "plan_session", "create_session",
    "get_current_question", "get_question_at", "mark_question", "record_dwell",
    "submit_answer", "record_events", "compute_score", "finish_session", "get_result",
]
