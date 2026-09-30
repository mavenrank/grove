"""Escaped, self-contained inspection report; no remote assets or scripts."""
from __future__ import annotations

import html
import json
import re
from collections import Counter


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def render_report(report: dict) -> str:
    counts = report["counts"]
    parts = ["""<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Grove pipeline test bench</title><style>
body{font:16px/1.55 system-ui,sans-serif;max-width:1100px;margin:32px auto;padding:0 20px;color:#203427;background:#faf9f5}
a{color:#216347}h2{margin-top:40px}table{border-collapse:collapse;width:100%;font-size:14px}
td,th{padding:8px;text-align:left;border-bottom:1px solid #ddd;vertical-align:top}
details{margin:12px 0;padding:12px;border:1px solid #d4d9d3;background:white}
summary{cursor:pointer}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}
.note{color:#556257}.scroll{overflow-x:auto}code{overflow-wrap:anywhere}
</style><h1>Grove pipeline test bench</h1>"""]
    release = report["release"]
    parts.append(f"<p>{esc(release.get('release_id'))} v{esc(release.get('version'))} · {esc(report['generated_at'])}</p>")
    parts.append(f"<p>{counts['topics']} Learn topics · {counts['sources_extracted']} cited files · "
                 f"{counts['source_slides']} slide records · {counts['findings']} findings and review clues.</p>")
    parts.append("<p class='note'>Draft inspection only. The stored app release is unchanged. Counts include repeated "
                 "drawing flags and decoration; they are not counts of confirmed incorrect lessons. "
                 "Expand a finding for its source hash, slide, raw notes and evidence. Use browser Find to locate text.</p>")
    parts.append("<ul>" + "".join(f"<li>{esc(v)}</li>" for v in report["limitations"]) + "</ul>")
    parts.append("<h2>Finding categories</h2><div class='scroll'><table><tr><th>Code</th><th>Count</th></tr>")
    parts.extend(f"<tr><td><code>{esc(code)}</code></td><td>{count}</td></tr>"
                 for code, count in sorted(counts["codes"].items()))
    parts.append("</table></div><h2>All Learn topics</h2><div class='scroll'><table>"
                 "<tr><th>Topic</th><th>Cited/extracted sources</th><th>Slides</th>"
                 "<th>Examples stored → draft</th><th>Questions / notes-confirmed</th><th>Findings</th></tr>")
    per_topic = Counter(f["topic_id"] for f in report["findings"])
    for index, topic in enumerate(report["topics"]):
        parts.append(f"<tr><td><a href='#topic-{index}'>{esc(topic['title'])}</a></td>"
                     f"<td>{topic['sources_expected']} / {topic['sources_extracted']}</td><td>{topic['source_slides']}</td>"
                     f"<td>{topic['stored']['examples']} → {topic['draft']['examples']}</td>"
                     f"<td>{topic['question_candidates']} / {topic['notes_confirmed']}</td><td>{per_topic[topic['id']]}</td></tr>")
    parts.append("</table></div>")
    for index, topic in enumerate(report["topics"]):
        parts.append(f"<h2 id='topic-{index}'>{esc(topic['title'])}</h2>"
                     f"<pre>{esc(json.dumps(topic, indent=2, ensure_ascii=False))}</pre>")
        for finding in report["findings"]:
            if finding["topic_id"] != topic["id"]:
                continue
            src = finding.get("source") or {}
            slide = f" · slide {src['slide_number']}" if "slide_number" in src else ""
            parts.append(f"<details><summary>{esc(finding['stage'])} · {esc(finding['code'])}{esc(slide)} "
                         f"· {esc(finding['confidence'])}</summary><p>{esc(finding['message'])}</p>"
                         f"<pre>{esc(json.dumps(finding, indent=2, ensure_ascii=False))}</pre></details>")
    parts.append("<h2>Skipped sources / stage validation</h2><pre>" +
                 esc(json.dumps({"skipped_sources": report["skipped_sources"], "validation": report["validation"]},
                                indent=2, ensure_ascii=False)) + "</pre>")
    parts.append("<h2>All source slide evidence</h2><p class='note'>Native text and notes, with retained embedded "
                 "picture previews. These are crops/assets, not rendered whole slides. Positioned blocks are in catalog.json.</p>")
    for slide in report.get("slides", []):
        src = slide["source"]
        parts.append(f"<details><summary>{esc(src['source_path'])} · slide {slide['slide_number']} · {esc(slide['kind'])}"
                     f" · {esc(slide['mode'])}</summary><pre>{esc(json.dumps(slide, indent=2, ensure_ascii=False))}</pre>")
        for field, label in (("media_ids", "Slide"), ("notes_media_ids", "Speaker notes")):
            ids = slide.get(field, [])
            if ids:
                parts.append(f"<p>{label} embedded assets:</p>")
            for mid in ids:
                if re.fullmatch(r"[0-9a-f]{16}", mid):
                    parts.append(f"<a href='media/{mid}.jpg'><img src='media/{mid}.jpg' loading='lazy' "
                                 f"alt='{label} source asset {mid}' style='max-width:100%;max-height:260px'></a>")
        parts.append("</details>")
    parts.append("</html>")
    return "".join(parts)
