"""Offline OCR enrichment candidates; disagreements stay separate from facts."""
from __future__ import annotations

import json
import math
import os
import re
import subprocess
from pathlib import Path

from .pipeline import now_iso, sha256_file
from .visuals import MAX_SLIDES


def invoke_ocr(job: Path) -> None:
    if os.name != "nt":
        raise ValueError("windows-media-ocr requires Windows with the selected OCR language installed")
    powershell = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    result = subprocess.run([str(powershell), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                             "-File", str(Path(__file__).with_name("windows_ocr.ps1")), "-JobPath", str(job)],
                            capture_output=True, text=True, timeout=180, creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode:
        raise ValueError("OCR runtime failed: " + result.stderr[-2500:])


def compare_text(native: list[str], ocr: dict) -> list[dict]:
    """These are heuristic differences, never evidence that either side is true."""
    tokenize = lambda value: set(re.findall(r"\w+|[×÷=√/±]", value.casefold()))
    native_tokens, ocr_tokens = tokenize("\n".join(native)), tokenize(ocr["text"])
    clues = []
    if native_tokens - ocr_tokens or ocr_tokens - native_tokens:
        clues.append({"code": "native_ocr_disagreement", "confidence": "heuristic",
                      "native_only": sorted(native_tokens - ocr_tokens), "ocr_only": sorted(ocr_tokens - native_tokens)})
    labels = lambda value: set(re.findall(r"(?:^|\s)([A-E])\s*[).:]", value, re.I | re.M))
    missing = {v.upper() for v in labels("\n".join(native))} - {v.upper() for v in labels(ocr["text"])}
    if missing:
        clues.append({"code": "ocr_option_label_missing", "confidence": "heuristic", "labels": sorted(missing)})
    if not ocr["text"].strip():
        clues.append({"code": "ocr_empty", "confidence": "observed"})
    return clues


def validate_candidate(value: dict, width: int, height: int) -> None:
    if (not isinstance(value.get("text"), str) or not isinstance(value.get("lines"), list)
            or len(value["text"]) > 100_000):
        raise ValueError("invalid OCR text/lines")
    angle = value.get("text_angle")
    if angle is not None and (type(angle) not in (int, float) or not math.isfinite(angle)):
        raise ValueError("invalid OCR text angle")
    for line in value["lines"]:
        if not isinstance(line.get("text"), str) or not isinstance(line.get("words"), list):
            raise ValueError("invalid OCR line")
        for word in line["words"]:
            box = word["box"]
            if not isinstance(word.get("text"), str) or any(type(box[k]) not in (int, float) or not math.isfinite(box[k]) for k in ("x", "y", "width", "height")):
                raise ValueError("invalid OCR word box")
            if min(box.values()) < 0 or box["x"] + box["width"] > width + 1 or box["y"] + box["height"] > height + 1:
                raise ValueError("OCR box is outside its source frame")


def run_ocr(visual: dict, frames: Path, output: Path, language: str = "en-US", runner=invoke_ocr) -> dict:
    frames, output = frames.resolve(), output.resolve()
    source = Path(visual["source_root"]).resolve()
    if visual.get("visual_schema_version") != 1 or visual.get("approved") is not False:
        raise ValueError("provide an unapproved schema-1 visual report")
    if (output == frames or frames in output.parents or output == source or source in output.parents
            or (output.exists() and any(output.iterdir()))):
        raise ValueError("use a new/empty OCR directory outside visual/source inputs")
    if not re.fullmatch(r"[a-z]{2,3}-[A-Z]{2}", language):
        raise ValueError("use an explicit OCR language tag such as en-US")
    selected = [(d, s) for d in visual["decks"] if d["status"] == "rendered" for s in d["slides"]]
    if len(selected) > MAX_SLIDES:
        raise ValueError("OCR slide batch limit")
    output.mkdir(parents=True, exist_ok=True)
    report = {"ocr_schema_version": 1, "created_at": now_iso(), "approved": False, "language": language,
              "visual_report_sha256": sha256_file(frames / "visual-report.json"), "frames_root": str(frames),
              "source_root": str(source), "confidence": None, "confidence_source": "not exposed by Windows.Media.Ocr",
              "slides": [], "blocked_decks": [d for d in visual["decks"] if d["status"] != "rendered"]}
    jobs = []
    for index, (deck, slide) in enumerate(selected):
        record = {**slide, "source_path": deck["source_path"], "source_hash": deck["source_hash"],
                  "deck_id": deck["deck_id"], "id": str(index), "status": "blocked"}
        report["slides"].append(record)
        try:
            original = (source / deck["source_path"]).resolve()
            path = (frames / slide["file"]).resolve()
            if (not original.is_relative_to(source) or sha256_file(original) != deck["source_hash"]
                    or not path.is_relative_to(frames) or sha256_file(path) != slide["sha256"]):
                raise ValueError("source/frame changed or outside its evidence root")
            jobs.append({"id": str(index), "file": str(path), "width": deck["renderer"]["width"],
                         "height": deck["renderer"]["height"]})
        except (ValueError, OSError) as exc:
            record["problem"] = str(exc)
    if jobs:
        job = output / "ocr-job.json"
        result_path = output / "ocr-runtime.json"
        job.write_text(json.dumps({"language": language, "images": jobs, "result": str(result_path)}), encoding="utf-8")
        try:
            runner(job)
            result = json.loads(result_path.read_text(encoding="utf-8-sig"))
            if (result["adapter"] != "windows-media-ocr" or result["adapter_revision"] != 1
                    or result["language"] != language or result.get("confidence") is not None):
                raise ValueError("unexpected OCR runtime/version/language/confidence")
            ids = [r["id"] for r in result["results"]]
            if sorted(ids) != sorted(j["id"] for j in jobs) or len(set(ids)) != len(ids):
                raise ValueError("OCR result IDs do not match selected source frames")
            report["runtime"] = {k: v for k, v in result.items() if k != "results"}
            by_id = {r["id"]: r for r in result["results"]}
            for planned in jobs:
                record = report["slides"][int(planned["id"])]
                candidate = by_id[planned["id"]]
                try:
                    if candidate["status"] != "candidate":
                        raise ValueError(candidate.get("problem", "OCR runtime blocked this frame"))
                    validate_candidate(candidate, planned["width"], planned["height"])
                    if (sha256_file(Path(planned["file"])) != record["sha256"]
                            or sha256_file(source / record["source_path"]) != record["source_hash"]):
                        raise ValueError("source/frame changed during OCR")
                    record.update(status="candidate", ocr=candidate, review_clues=compare_text(record["native_texts"], candidate))
                except (ValueError, OSError, KeyError, TypeError) as exc:
                    record.update(status="blocked", problem=str(exc))
        except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as exc:
            for planned in jobs:
                report["slides"][int(planned["id"])].update(status="blocked", problem=str(exc))
    (output / "ocr-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    from .visual_report import render_ocr_report
    (output / "ocr-report.html").write_text(render_ocr_report(report, output), encoding="utf-8")
    return report
