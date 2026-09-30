"""Release info, history, insights and admin status routes."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from .. import evidence, history
from ..content_engine.releases import load_release
from ..schemas import (
    HistoryFlashcardOut, HistoryLearningOut, HistoryOut, HistoryTestOut,
    InsightsOut, ReleaseInfoOut, SkillInsightOut, TestDetailOut,
)

router = APIRouter(prefix="/api")


@router.get("/release", response_model=ReleaseInfoOut)
def release_info() -> ReleaseInfoOut:
    rel = load_release()
    return ReleaseInfoOut(
        release_id=rel.get("release_id", "grove-bootstrap"),
        version=rel.get("version", "0.0.0"),
        generated_at=rel.get("generated_at"),
        source=rel.get("source"),
        concept_count=len(rel.get("concepts", [])),
        flashcard_count=len(rel.get("flashcards", [])),
        family_count=len(rel.get("families", [])),
    )


@router.get("/history", response_model=HistoryOut)
def get_history() -> HistoryOut:
    return HistoryOut(
        tests=[HistoryTestOut(**t) for t in history.recent_tests()],
        learning=[HistoryLearningOut(**x) for x in history.recent_learning()],
        flashcards=[HistoryFlashcardOut(**x) for x in history.recent_flashcards()],
    )


@router.get("/history/tests/{session_id}", response_model=TestDetailOut)
def history_test_detail(session_id: str) -> TestDetailOut:
    detail = history.test_detail(session_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="test not found")
    return TestDetailOut(**detail)


@router.get("/insights", response_model=InsightsOut)
def insights() -> InsightsOut:
    return InsightsOut(skills=[SkillInsightOut(**s) for s in evidence.skill_evidence()])


@router.get("/admin/status")
def admin_status() -> dict[str, Any]:
    rel = load_release()
    return {
        "release": {
            "release_id": rel.get("release_id"),
            "version": rel.get("version"),
            "source": rel.get("source"),
            "approved": rel.get("approved", True),
        },
        "ingestion": {
            "public_upload_enabled": False,
            "write_operations": "disabled",
            "pipeline": "grove-ingest CLI only",
        },
        "counts": {
            "concepts": len(rel.get("concepts", [])),
            "flashcards": len(rel.get("flashcards", [])),
            "families": len(rel.get("families", [])),
        },
    }
