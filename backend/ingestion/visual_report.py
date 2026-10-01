"""Escaped private review page; all visual/native/OCR evidence stays separate."""
import html
import json
import os
from pathlib import Path


def render_ocr_report(report: dict, output: Path) -> str:
    esc = lambda value: html.escape(str(value), quote=True)
    cards = []
    for slide in report["slides"]:
        image = (Path(report["frames_root"]) / slide["file"]).resolve()
        relative = os.path.relpath(image, output).replace("\\", "/")
        ocr = slide.get("ocr", {})
        cards.append(f'<section><h2>{esc(Path(slide["source_path"]).name)} · slide {slide["slide_number"]}</h2>'
                     f'<p>{esc(slide["status"])} · {esc(slide["slide_id"])}<br>Source SHA: {esc(slide["source_hash"])}</p>'
                     f'<img loading="lazy" src="{esc(relative)}" alt="Original rendered slide {slide["slide_number"]}">'
                     f'<div class="columns"><div><h3>Native text</h3><pre>{esc(chr(10).join(slide["native_texts"]))}</pre></div>'
                     f'<div><h3>OCR candidate · confidence unavailable</h3><pre>{esc(ocr.get("text", slide.get("problem", "")))}</pre></div></div>'
                     f'<details><summary>Review differences and word boxes</summary><pre>{esc(json.dumps(slide.get("review_clues", []), indent=2, ensure_ascii=False))}</pre>'
                     f'<pre>{esc(json.dumps(ocr.get("lines", []), indent=2, ensure_ascii=False))}</pre></details></section>')
    return ('<!doctype html><html lang="en"><meta charset="utf-8"><title>Grove visual source review</title>'
            '<style>body{max-width:1250px;margin:32px auto;padding:0 20px;font:16px system-ui;background:#f7f7f3;color:#20362a}'
            'section{background:white;padding:20px;margin:24px 0;border:1px solid #ddd}img{width:100%;height:auto}'
            'pre{white-space:pre-wrap;overflow-wrap:anywhere}.columns{display:grid;grid-template-columns:1fr 1fr;gap:24px}'
            'h2{font-size:19px;overflow-wrap:anywhere}@media(max-width:700px){.columns{grid-template-columns:1fr}}</style>'
            '<h1>Grove visual source review</h1><p>Original frames, native extraction and offline OCR candidates. '
            'Differences are review clues; OCR does not verify answers or diagram relationships. No content approved/imported.</p>'
            f'<p>{len(report["slides"])} selected frames · {len(report["blocked_decks"])} blocked decks · '
            f'language {esc(report["language"])}</p>' + ''.join(cards) + '</html>')


def render_source_reviews(report: dict, output: Path) -> str:
    esc = lambda value: html.escape(str(value), quote=True)
    cards = []
    for result in report["records"]:
        r = result["record"]
        links = []
        # Only validated paths become clickable links or frames.
        if result["status"] == "accepted_annotation":
            for item in r["evidence"]:
                path = (Path(report["evidence_root"]) / item["path"]).resolve()
                relative = os.path.relpath(path, output).replace("\\", "/")
                links.append(f'<p><a href="{esc(relative)}">{esc(item["kind"])}: {esc(item["path"])}</a></p>')
                if item["kind"] == "rendered_slide":
                    links.append(f'<img loading="lazy" src="{esc(relative)}" alt="Reviewed source slide">')
        cards.append(f'<section><h2>{esc(r.get("review_id", "Invalid record"))} · {esc(result["status"])}</h2>'
                     f'<p>{esc(r.get("source_path", ""))} · slide {esc(r.get("slide_number", ""))} · '
                     f'{esc(r.get("surface", ""))} / {esc(r.get("target", ""))} {esc(r.get("shape_id", ""))}<br>'
                     f'Source SHA: {esc(r.get("source_hash", ""))}</p><h3>{esc(r.get("decision", ""))}</h3>'
                     f'<p>{esc(r.get("reason", ""))}</p><h3>Observed evidence</h3><pre>{esc(r.get("observed", ""))}</pre>'
                     f'<h3>Proposed interpretation/correction · unapproved</h3><pre>{esc(r.get("proposed", "None"))}</pre>'
                     f'<p>Reviewer: {esc(r.get("reviewer", ""))}</p><p>{esc(result.get("problem", result.get("publication_effect", "")))}</p>'
                     f'<details><summary>Native issues retained</summary><pre>{esc(json.dumps(result.get("native_issues", []), indent=2))}</pre></details>'
                     + ''.join(links) + '</section>')
    return ('<!doctype html><html lang="en"><meta charset="utf-8"><title>Grove source review annotations</title>'
            '<style>body{max-width:1100px;margin:32px auto;padding:0 20px;font:16px system-ui;background:#f7f7f3;color:#20362a}'
            'section{background:white;padding:20px;margin:24px 0;border:1px solid #ddd}img{width:100%;height:auto}'
            'pre{white-space:pre-wrap;overflow-wrap:anywhere}p,h2{overflow-wrap:anywhere}</style>'
            '<h1>Grove source review annotations</h1><p>Acceptance checks provenance and evidence integrity. '
            'It does not verify claims, hide native issues, approve knowledge or import a release.</p>'
            f'<p>{esc(report["counts"])}</p>' + ''.join(cards) + '</html>')
