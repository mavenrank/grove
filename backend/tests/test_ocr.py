"""OCR stays a traceable candidate, with no invented confidence or native edits."""
import json
from copy import deepcopy

import pytest
from PIL import Image

from ingestion.ocr import compare_text, run_ocr
from ingestion.pipeline import sha256_file


@pytest.fixture
def evidence(tmp_path):
    source, frames = tmp_path / "source", tmp_path / "frames"
    source.mkdir(); frames.mkdir()
    original = source / "SPEED.pptx"
    original.write_bytes(b"unchanged source snapshot")
    image = frames / "slide-1.png"
    Image.new("RGB", (800, 450), "white").save(image)
    visual = {"visual_schema_version": 1, "approved": False, "source_root": str(source), "decks": [
        {"status": "rendered", "deck_id": "speed", "source_path": original.name, "source_hash": sha256_file(original),
         "renderer": {"width": 800, "height": 450}, "slides": [
             {"slide_number": 1, "slide_id": "speed:1", "file": image.name, "sha256": sha256_file(image),
              "native_texts": ["Find distance = speed × time", "A) 12", "B) 6", "<script>bad()</script>"], "native_issues": []}]}]}
    (frames / "visual-report.json").write_text(json.dumps(visual))
    return visual, frames, original


def engine(job):
    value = json.loads(job.read_text())
    records = [{"id": image["id"], "status": "candidate", "text": "Find distance = speed × time B) 6",
                "text_angle": None, "lines": [{"text": "Find distance", "words": [
                    {"text": "Find", "box": {"x": 20.0, "y": 30.0, "width": 50.0, "height": 20.0}}]}]}
               for image in value["images"]]
    result = {"adapter": "windows-media-ocr", "adapter_revision": 1, "language": value["language"],
              "os_version": "test", "confidence": None, "results": records}
    with open(value["result"], "w", encoding="utf-8") as handle:
        json.dump(result, handle)


def test_native_and_ocr_remain_separate_and_html_is_escaped(evidence, tmp_path):
    visual, frames, original = evidence
    before = deepcopy(visual)
    source_bytes, report_bytes = original.read_bytes(), (frames / "visual-report.json").read_bytes()
    output = tmp_path / "ocr"
    result = run_ocr(visual, frames, output, runner=engine)
    assert visual == before and original.read_bytes() == source_bytes
    assert (frames / "visual-report.json").read_bytes() == report_bytes
    record = result["slides"][0]
    assert record["status"] == "candidate"
    assert result["confidence"] is None and result["approved"] is False
    assert record["native_texts"] != [record["ocr"]["text"]]
    assert {"code": "ocr_option_label_missing", "confidence": "heuristic", "labels": ["A"]} in record["review_clues"]
    html = (output / "ocr-report.html").read_text(encoding="utf-8")
    assert "<script>bad()" not in html and "&lt;script&gt;" in html


@pytest.mark.parametrize("failure", ["missing_id", "duplicate_id", "wrong_language", "confidence", "outside_box", "nan_box", "blocked"])
def test_invalid_runtime_output_never_becomes_a_candidate(evidence, tmp_path, failure):
    visual, frames, _ = evidence

    def invalid(job):
        engine(job)
        path = json.loads(job.read_text())["result"]
        with open(path, encoding="utf-8") as handle:
            value = json.load(handle)
        if failure == "missing_id":
            value["results"] = []
        elif failure == "duplicate_id":
            value["results"].append(deepcopy(value["results"][0]))
        elif failure == "wrong_language":
            value["language"] = "en-GB"
        elif failure == "confidence":
            value["confidence"] = 0.99
        elif failure == "outside_box":
            value["results"][0]["lines"][0]["words"][0]["box"]["x"] = 799
        elif failure == "nan_box":
            value["results"][0]["lines"][0]["words"][0]["box"]["x"] = float("nan")
        elif failure == "blocked":
            value["results"][0] = {"id": "0", "status": "blocked", "problem": "could not read"}
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(value, handle)

    result = run_ocr(visual, frames, tmp_path / "ocr", runner=invalid)
    assert result["slides"][0]["status"] == "blocked" and "ocr" not in result["slides"][0]


@pytest.mark.parametrize("failure", ["frame_changed", "source_changed", "path_escape"])
def test_changed_or_outside_evidence_never_reaches_ocr(evidence, tmp_path, failure):
    visual, frames, original = evidence
    if failure == "frame_changed":
        (frames / "slide-1.png").write_bytes(b"changed frame")
    elif failure == "source_changed":
        original.write_bytes(b"changed source")
    elif failure == "path_escape":
        visual["decks"][0]["slides"][0]["file"] = "../outside.png"
    result = run_ocr(visual, frames, tmp_path / "ocr", runner=lambda job: pytest.fail("must not invoke OCR"))
    assert result["slides"][0]["status"] == "blocked"


def test_empty_ocr_output_is_a_review_clue():
    assert any(c["code"] == "ocr_empty" for c in compare_text(["Distance = speed × time"], {"text": ""}))
