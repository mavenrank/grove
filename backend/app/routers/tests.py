"""Test-lifecycle routes: create, serve, answer, mark, dwell, finish."""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from .. import db, engine
from ..config import settings
from ..schemas import (
    AnswerAcceptedOut, EventsAcceptedOut, MarkedOut, QuestionOut,
    ResultOut, SessionCreatedOut,
)
from .requests import AnswerIn, CreateSessionIn, DwellIn, EventsIn, MarkIn

router = APIRouter(prefix="/api")


def _learner(request: Request) -> str:
    return settings.default_learner


@router.post("/test-sessions", response_model=SessionCreatedOut, status_code=201)
def create_session(body: CreateSessionIn, request: Request) -> SessionCreatedOut:
    try:
        result = engine.create_session(
            body.question_count,
            _learner(request),
            duration_minutes=body.duration_minutes,
        )
    except engine.TestFlowError as exc:
        raise HTTPException(status_code=422, detail=exc.code) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="no approved content release loaded") from exc
    return SessionCreatedOut(**result)


@router.get("/test-sessions/{session_id}/question", response_model=QuestionOut)
def current_question(session_id: str, request: Request) -> QuestionOut:
    try:
        q = engine.get_current_question(session_id, _learner(request))
    except engine.NotFoundError:
        raise HTTPException(status_code=404, detail="session not found") from None
    except engine.TestFlowError as exc:
        status = 410 if exc.code == "expired" else 409
        raise HTTPException(status_code=status, detail=exc.code) from None
    return QuestionOut(**q)


@router.get("/test-sessions/{session_id}/question/{position}", response_model=QuestionOut)
def question_at(session_id: str, position: int, request: Request) -> QuestionOut:
    try:
        q = engine.get_question_at(session_id, position, _learner(request))
    except engine.NotFoundError:
        raise HTTPException(status_code=404, detail="not found") from None
    except engine.TestFlowError as exc:
        status = 410 if exc.code == "expired" else 409
        raise HTTPException(status_code=status, detail=exc.code) from None
    return QuestionOut(**q)


@router.post("/test-sessions/{session_id}/answer", response_model=AnswerAcceptedOut)
def answer_question(session_id: str, position: int, body: AnswerIn, request: Request) -> AnswerAcceptedOut:
    try:
        result = engine.submit_answer(session_id, position, body.ticket, body.option,
                                      _learner(request), body.idempotency_key)
    except engine.NotFoundError:
        raise HTTPException(status_code=404, detail="not found") from None
    except engine.TestFlowError as exc:
        status = 410 if exc.code == "expired" else 409
        raise HTTPException(status_code=status, detail=exc.code) from None
    return AnswerAcceptedOut(**result)


@router.post("/test-sessions/{session_id}/mark/{position}", response_model=MarkedOut)
def mark_question(session_id: str, position: int, body: MarkIn, request: Request) -> MarkedOut:
    try:
        engine.mark_question(session_id, position, body.marked, _learner(request))
    except engine.NotFoundError:
        raise HTTPException(status_code=404, detail="not found") from None
    except engine.TestFlowError as exc:
        status = 410 if exc.code == "expired" else 409
        raise HTTPException(status_code=status, detail=exc.code) from None
    return MarkedOut(marked=body.marked)


@router.post("/test-sessions/{session_id}/events", response_model=EventsAcceptedOut)
def submit_events(session_id: str, body: EventsIn, request: Request) -> EventsAcceptedOut:
    session = db.get_session(session_id)
    if session is None or session["learner"] != _learner(request):
        raise HTTPException(status_code=404, detail="session not found")
    rows = []
    server_time = db.iso(db.utcnow())
    for ev in body.events:
        payload_json = _safe_payload(ev.payload)
        rows.append((session_id, ev.position, ev.type, ev.client_time, server_time, payload_json))
    accepted = db.insert_events(rows)
    return EventsAcceptedOut(accepted=accepted)


@router.post("/test-sessions/{session_id}/dwell", response_model=EventsAcceptedOut)
def submit_dwell(session_id: str, body: DwellIn, request: Request) -> EventsAcceptedOut:
    """Client-side active dwell for one question (additive segments)."""
    try:
        engine.record_dwell(session_id, body.position, _learner(request), body.seconds, body.kind)
    except engine.NotFoundError:
        raise HTTPException(status_code=404, detail="session not found") from None
    return EventsAcceptedOut(accepted=1)


@router.post("/test-sessions/{session_id}/finish", response_model=ResultOut)
def finish(session_id: str, request: Request) -> ResultOut:
    try:
        result = engine.finish_session(session_id, _learner(request))
    except engine.NotFoundError:
        raise HTTPException(status_code=404, detail="session not found") from None
    except engine.TestFlowError as exc:
        status = 410 if exc.code == "expired" else 409
        raise HTTPException(status_code=status, detail=exc.code) from None
    return ResultOut(**result)


@router.get("/test-sessions/{session_id}/result", response_model=ResultOut)
def get_result(session_id: str, request: Request) -> ResultOut:
    try:
        result = engine.get_result(session_id, _learner(request))
    except engine.NotFoundError:
        raise HTTPException(status_code=404, detail="session not found") from None
    except engine.TestFlowError as exc:
        raise HTTPException(status_code=409, detail=exc.code) from None
    return ResultOut(**result)


def _safe_payload(payload: dict[str, Any]) -> str:
    cleaned: dict[str, Any] = {}
    for k, v in list(payload.items())[:32]:
        if not isinstance(k, str) or len(k) > 64:
            continue
        if isinstance(v, (str, int, float, bool)) or v is None:
            cleaned[k[:64]] = v if (v is None or isinstance(v, bool) or
                                    (isinstance(v, (int, float)) and abs(v) < 1e15) or
                                    (isinstance(v, str) and len(v) <= 512)) else (str(v)[:512])
        else:
            cleaned[k[:64]] = str(v)[:256]
    return json.dumps(cleaned)
