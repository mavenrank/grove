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
