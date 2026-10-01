"""Native rendering must remain bounded, source-preserving inspection evidence."""
import json
import subprocess
import zipfile
from copy import deepcopy

import pytest
from PIL import Image

from ingestion.pipeline import sha256_file
from ingestion.visuals import render_preflight, run_visuals


@pytest.fixture
def source_catalog(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    path = source / "SPEED.pptx"
    with zipfile.ZipFile(path, "w") as package:
        package.writestr("ppt/_rels/presentation.xml.rels", '<Relationships/>')
    catalog = {"decks": [{"deck_id": "speed", "source_path": path.name, "source_hash": sha256_file(path),
                          "slide_count": 2, "slides": [{"slide_number": n, "slide_id": f"snapshot:{n}",
                                                          "texts": ["Distance = Speed × Time"], "issues": []}
                                                         for n in (1, 2)]}]}
    return source, path, catalog


def render(job_path):
    job = json.loads(job_path.read_text())
    output = job_path.parent
    for number in job["slides"]:
        Image.new("RGB", (job["width"], 450), "white").save(output / f"slide-{number}.png")
    metadata = {"adapter": "powerpoint-com", "adapter_revision": 1, "slide_count": 2,
                "width": job["width"], "height": 450,
                "slides": [{"slide_number": n, "file": f"slide-{n}.png"} for n in job["slides"]]}
    (output / "renderer.json").write_text(json.dumps(metadata))


def test_rendered_frame_is_traceable_and_does_not_change_source_or_catalog(source_catalog, tmp_path):
    source, path, catalog = source_catalog
    original_bytes, original_catalog = path.read_bytes(), deepcopy(catalog)
    output = tmp_path / "visuals"
    report = run_visuals(catalog, source, output, ["speed"], [2], 800, render)
    record = report["decks"][0]
    assert record["status"] == "rendered"
    assert record["slides"][0]["sha256"] == sha256_file(output / record["slides"][0]["file"])
    assert record["slides"][0]["slide_id"] == "snapshot:2"
    assert report["approved"] is False
    assert catalog == original_catalog and path.read_bytes() == original_bytes
    assert (output / "visual-report.json").is_file()


@pytest.mark.parametrize("failure", ["count", "position", "path", "dimensions", "timeout", "source_change"])
def test_failed_renderer_evidence_is_blocked(source_catalog, tmp_path, failure):
    source, path, catalog = source_catalog

    def bad_runner(job):
        if failure == "timeout":
            raise subprocess.TimeoutExpired("renderer", 120)
        render(job)
        metadata_path = job.parent / "renderer.json"
        metadata = json.loads(metadata_path.read_text())
        if failure == "count":
            metadata["slide_count"] = 3
        elif failure == "position":
            metadata["slides"][0]["slide_number"] = 2
        elif failure == "path":
            metadata["slides"][0]["file"] = "../outside.png"
        elif failure == "dimensions":
            Image.new("RGB", (20, 20)).save(job.parent / "slide-1.png")
        elif failure == "source_change":
            path.write_bytes(b"changed during rendering")
        metadata_path.write_text(json.dumps(metadata))

    report = run_visuals(catalog, source, tmp_path / "failed-visuals", ["speed"], [1], 800, bad_runner)
    assert report["decks"][0]["status"] == "blocked"
    assert report["decks"][0]["slides"] == []


@pytest.mark.parametrize("failure", ["changed", "outside_source", "existing_output", "outside_slide", "unknown_deck"])
def test_invalid_plan_never_invokes_office(source_catalog, tmp_path, failure):
    source, path, catalog = source_catalog
    output, numbers, ids = tmp_path / "visuals", [1], ["speed"]
    if failure == "changed":
        path.write_bytes(b"changed source")
    elif failure == "outside_source":
        catalog["decks"][0]["source_path"] = "../outside.pptx"
    elif failure == "existing_output":
        output.mkdir()
        (output / "keep.txt").write_text("existing inspection")
    elif failure == "outside_slide":
        numbers = [3]
    elif failure == "unknown_deck":
        ids = ["unknown"]
    with pytest.raises(ValueError):
        run_visuals(catalog, source, output, ids, numbers, 800,
                    lambda job: pytest.fail("Office must not be invoked for invalid plans"))


@pytest.mark.parametrize("kind", ["oleObject", "image", "hyperlink"])
def test_external_content_is_rejected_except_passive_hyperlinks(tmp_path, kind):
    path = tmp_path / "linked.pptx"
    with zipfile.ZipFile(path, "w") as package:
        package.writestr("ppt/slides/_rels/slide1.xml.rels",
                         f'<Relationships><Relationship Type="https://example.test/{kind}" TargetMode="External" Target="https://example.test/"/></Relationships>')
    if kind == "hyperlink":
        render_preflight(path)
    else:
        with pytest.raises(ValueError):
            render_preflight(path)
