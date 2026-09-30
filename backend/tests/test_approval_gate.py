"""Approval must not bypass catalog validation (#7)."""
import json

import pytest

from ingestion.pipeline import Pipeline


def _catalog(skill="other.algorithms"):
    return {"decks": [{"deck_id": "sample", "source_file": "sample.pptx",
                       "source_path": "sample.pptx", "source_hash": "abc",
                       "slide_count": 1, "slides": [{"texts": ["Sample lesson"]}],
                       "status": "active", "skill_id": skill}], "media_index": {}}


def _organized():
    return {"concepts": [], "flashcards": [], "question_pool": [], "stats": {}}


def test_failed_report_cannot_be_approved(tmp_path):
    p = Pipeline(tmp_path / "src", tmp_path / "work")
    catalog = _catalog()
    report = p.validate(catalog)
    assert report["ok"] is False
    with pytest.raises(ValueError, match="cannot approve"):
        p.pack(catalog, report, _organized(), "0.1.0", True)
    draft = p.pack(catalog, report, _organized(), "0.1.0", False)
    assert draft["approved"] is False and draft["concepts"] == []


def test_stale_success_flag_does_not_bypass_current_validation(tmp_path):
    p = Pipeline(tmp_path / "src", tmp_path / "work")
    catalog = _catalog("quant.frp.percentages")
    report = p.validate(catalog)
    catalog["decks"][0]["skill_id"] = "other.algorithms"
    with pytest.raises(ValueError, match="cannot approve"):
        p.pack(catalog, report, _organized(), "0.1.0", True)


def test_cli_pack_failure_writes_no_publishable_pack(tmp_path, monkeypatch, capsys):
    p = Pipeline(tmp_path / "src", tmp_path / "work")
    (p.work_dir / "catalog.json").write_text(json.dumps(_catalog()), encoding="utf-8")
    monkeypatch.setattr(p, "organize", lambda catalog: _organized())
    assert p.run_pack("0.1.0", approve=True) == 2
    assert "cannot approve" in capsys.readouterr().err
    assert not (p.work_dir / "packs/grove-ingested-0.1.0.json").exists()
