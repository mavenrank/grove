# Pipeline test bench (#36)

The bench compares every stored Learn topic with fresh extraction of its cited sources. It does not approve/import, alter sources, or open the learner database for writing. Use it during #1–8/#10; keep formatting #37 deferred.

From Grove's backend directory, in PowerShell:

~~~powershell
.\.venv\Scripts\python.exe -B -X utf8 -m ingestion.cli audit --database ..\data\grove.db --source "$env:GROVE_SOURCE_DIR" --work <source-dir> --media ..\content\media
~~~

Use a **new or empty** work directory outside the corpus per snapshot. To replay frozen input, replace --database with --release followed by the release-snapshot.json path. For relocated sources supply --source; hashes identify source revisions. Optional --media checks whether stored lesson media exists.

Open bench-report.html. Topic links and expandable findings expose stage, confidence, source hash, slide and evidence. Its final section contains every extracted slide's native text/notes and embedded picture previews. These are **assets, not whole-slide renders**. Source text is HTML-escaped.

Outputs: release-snapshot.json, catalog.json (positioned blocks), content-drafts.json, validation-report.json, bench-report.json, bench-report.html and media/. Keep these local; they contain corpus material and are not committed code. Stable finding IDs support comparisons.

Exit 0 means structural validation completed without skips, **not** that review passed. Exit 1 means structural failures/skips; exit 2 means input/command failure. validation.ready_for_approval describes the existing pipeline gate, not completed semantic review.

## Coverage and limits

- All stored Learn topics and citations are accounted for. Uncited files/absent topics need the later full-corpus classification audit.
- An independent PPTX package reader checks slide order/count and native text runs. Run/layout differences are heuristic clues; equations, diagrams and picture meaning need visual review.
- Fresh/stored counts expose missing candidates. Public-schema serialization detects dropped segments/example context, but does not test browser rendering.
- Notes-confirmed keys are not independently solved. Failed question parsing and malformed options remain review blockers.
- Formatting/exclusion clues are separate from observed losses. Do not automatically balance mathematical delimiters or call repeated images logos.
- No OCR or whole-slide renderer is included. PDF/DOCX adapters remain explicit unsupported-content findings.

## First complete stored-topic audit — 30 September 2026

Baseline: grove-ingested 0.3.5 from 20 September. Report: <source-dir>

All **27 topics / 78 cited files** were accounted for: **47 PPTs / 1,214 slide positions**, plus **31 PDF placeholder records** (not extracted pages). No missing/changed-hash citation. Four old slide counts differ. Structural validation passed; approval remains blocked.

Nine stored topics have no examples and placeholder summaries: Pattern Completion, Directions, Syllogisms, Profit Loss, Calendars, Clocks, Relative Speed, Speed Distance Time and Time Work. Their fresh summaries are also placeholders. Findings include 145 unparsed question slides, 94 ambiguous option mappings and 273 parsed questions lacking recognized notes answers. Categories overlap and are not independently confirmed source errors.

All 27 fresh topics retain segments omitted by the public schema. Eight stored topics have recall questions in formula lists. Thirty formatting clues (7 delimiter imbalances / 23 long paragraphs) belong to deferred #37. Visual/vector flags include artwork; their counts do not measure teaching-image loss.

Six regression cases cover topic accounting/stable IDs, independent text/slide loss, read-only release selection, real PPT extraction/source preservation, path boundaries and HTML escaping. Full visual/mathematical review remains open. Independent Speed Distance Time calculations are in CONTENT_REFRESH_AUDIT.md.
