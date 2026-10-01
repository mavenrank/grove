"""Opt-in whole-slide inspection; never rewrites catalogs or approves lessons."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from .pipeline import now_iso, sha256_file

MAX_SLIDES = 200
MAX_PART_BYTES = 8 * 1024 * 1024


def render_preflight(path: Path) -> None:
    """Block active/link-dependent packages before opening them in Office."""
    with zipfile.ZipFile(path) as package:
        if len(package.infolist()) > 20_000:
            raise ValueError("package part limit")
        for item in package.infolist():
            name = item.filename.casefold()
            if "vbaproject" in name or name.startswith(("ppt/activex/", "ppt/embeddings/")):
                raise ValueError("active/embedded payload is outside the native renderer pilot")
            if not name.endswith(".rels"):
                continue
            if item.file_size > MAX_PART_BYTES:
                raise ValueError("relationship part limit")
            for rel in ET.fromstring(package.read(item)):
                kind = rel.attrib.get("Type", "").rsplit("/", 1)[-1]
                if kind in {"oleObject", "control"}:
                    raise ValueError("active object relationship is outside the native renderer pilot")
                if rel.attrib.get("TargetMode") == "External" and kind != "hyperlink":
                    raise ValueError("external linked content is outside the native renderer pilot")


def invoke_renderer(job: Path) -> None:
    if os.name != "nt":
        raise ValueError("powerpoint-com requires Windows and installed desktop PowerPoint")
    powershell = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    result = subprocess.run([str(powershell), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                             "-File", str(Path(__file__).with_name("native_render.ps1")), "-JobPath", str(job)],
                            capture_output=True, text=True, timeout=120, creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode:
        raise ValueError("native renderer failed: " + result.stderr[-2500:])


def run_visuals(catalog: dict, source: Path, output: Path, deck_ids: list[str],
                slide_numbers: list[int] | None = None, width: int = 1600, runner=invoke_renderer) -> dict:
    """Render selected original snapshots into a fresh source-contained report."""
    source, output = source.resolve(), output.resolve()
    if not 800 <= width <= 3200:
        raise ValueError("render width must be 800–3200 pixels")
    if output == source or source in output.parents or (output.exists() and any(output.iterdir())):
        raise ValueError("use a new/empty visual directory outside the source corpus")
    selected = [d for d in catalog["decks"] if d["deck_id"] in deck_ids]
    if not deck_ids or len(selected) != len(set(deck_ids)):
        raise ValueError("select known catalog deck IDs")
    if any(Path(d["source_path"]).suffix.lower() != ".pptx" for d in selected):
        raise ValueError("native renderer pilot accepts PPTX sources only")
    plans = []
    for deck in selected:
        path = (source / deck["source_path"]).resolve()
        if not path.is_relative_to(source) or not path.is_file() or sha256_file(path) != deck["source_hash"]:
            raise ValueError("source missing, outside root or changed: " + deck["source_path"])
        numbers = sorted(set(slide_numbers or range(1, deck["slide_count"] + 1)))
        if not numbers or any(type(n) is not int or n < 1 or n > deck["slide_count"] for n in numbers):
            raise ValueError("requested slide is outside the source snapshot")
        plans.append((deck, path, numbers))
    if sum(len(numbers) for _, _, numbers in plans) > MAX_SLIDES:
        raise ValueError(f"select at most {MAX_SLIDES} slide positions per visual batch")
    output.mkdir(parents=True, exist_ok=True)
    report = {"visual_schema_version": 1, "created_at": now_iso(), "source_root": str(source),
              "scope": "whole slides only; notes assets remain separate", "approved": False, "decks": []}
    for index, (deck, path, numbers) in enumerate(plans):
        directory = output / f"deck-{index + 1}"
        directory.mkdir()
        record = {"deck_id": deck["deck_id"], "source_path": deck["source_path"], "source_hash": deck["source_hash"],
                  "selected_slides": numbers, "slides": [], "status": "blocked", "directory": directory.name}
        report["decks"].append(record)
        try:
            render_preflight(path)
            copy = directory / "inspection-copy.pptx"
            shutil.copyfile(path, copy)
            if sha256_file(copy) != deck["source_hash"]:
                raise ValueError("source changed while preparing inspection copy")
            job = directory / "job.json"
            job.write_text(json.dumps({"source": str(copy), "output": str(directory), "slides": numbers,
                                       "width": width}), encoding="utf-8")
            runner(job)
            metadata = json.loads((directory / "renderer.json").read_text(encoding="utf-8-sig"))
            if (metadata.get("adapter") != "powerpoint-com" or metadata.get("adapter_revision") != 1
                    or metadata["width"] != width or metadata["slide_count"] != deck["slide_count"]
                    or [s["slide_number"] for s in metadata["slides"]] != numbers):
                raise ValueError("renderer positions/count disagree with the catalog")
            from PIL import Image
            for rendered in metadata["slides"]:
                number = rendered["slide_number"]
                expected = f"slide-{number}.png"
                if rendered["file"] != expected:
                    raise ValueError("renderer returned an unexpected file path")
                image = directory / expected
                if image.is_symlink():
                    raise ValueError("rendered evidence must not be a symlink")
                with Image.open(image) as img:
                    if img.format != "PNG" or img.size != (metadata["width"], metadata["height"]) or max(img.size) > 4096:
                        raise ValueError("invalid rendered frame dimensions/format")
                    img.verify()
                native = next(s for s in deck["slides"] if s["slide_number"] == number)
                record["slides"].append({"slide_number": number, "slide_id": native["slide_id"],
                                         "file": f"{directory.name}/{expected}", "sha256": sha256_file(image),
                                         "native_texts": native["texts"], "native_issues": native.get("issues", [])})
            if sha256_file(path) != deck["source_hash"]:
                raise ValueError("source changed during rendering")
            record.update(status="rendered", renderer=metadata)
        except (ValueError, OSError, KeyError, zipfile.BadZipFile, ET.ParseError, subprocess.SubprocessError) as exc:
            record.update(status="blocked", problem=str(exc), slides=[])
        (output / "visual-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report
