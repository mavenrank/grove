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

Nine stored topics have **no examples**: Pattern Completion, Directions, Syllogisms, Profit Loss, Calendars, Clocks, Relative Speed, Speed Distance Time and Time Work. A different set of nine has **placeholder summaries** in both stored and fresh content: Analogies, Equations, Averages, Profit Loss, Percentages, Clocks, Relative Speed, Speed Distance Time and Time Work. Syllogisms has native teaching prose; its question prompts and choices are on different slides, so the current single-slide parser produces no examples. Pattern Completion includes quantitative cube/root teaching misclassified by the broad filename rule. Findings include 145 unparsed question slides, 94 ambiguous option mappings and 273 parsed questions lacking recognized notes answers. Categories overlap and are not independently confirmed source errors.

All 27 fresh topics retain segments omitted by the public schema. Eight stored topics have recall questions in formula lists. Thirty formatting clues (7 delimiter imbalances / 23 long paragraphs) belong to deferred #37. Visual/vector flags include artwork; their counts do not measure teaching-image loss.

Six regression cases cover topic accounting/stable IDs, independent text/slide loss, read-only release selection, real PPT extraction/source preservation, path boundaries and HTML escaping. Full visual/mathematical review remains open. Independent Speed Distance Time calculations are in CONTENT_REFRESH_AUDIT.md.

## #7 notes-label improvement

Tested after-report: <source-dir> The same frozen release and all 78 source hashes were used. Notes-confirmed candidates increased **407 → 499**, with no previously recognized key changed/lost. Parsed questions missing recognized keys fell **273 → 149**; 32 of the recovered labels still have ambiguous choices and cannot become examples. Total question candidates stay 720; 145 question-parse failures and 94 ambiguous mappings remain.

Speed Distance Time recovers its five explicit keys (slides 3–7), matching the pilot's independent calculations. Eight topics now have more draft example candidates than the stored lesson; summaries, visual interpretation and delivery contracts remain unresolved. Higher overall finding counts can reflect more surfaced draft examples hitting the unchanged public schema, not worsening extraction.

Twenty-one notes regression cases cover real label/glyph/nonbreaking-space variants, conflicting or multiple labels, incidental prose, out-of-choice keys, preservation of surrounding solution text, and choice ambiguity. Intermediate development reports learn-bench-notes and learn-bench-notes-fixed are superseded by learn-bench-notes-reviewed; they are not evidence for the tested outcome.

## #2/#4/#6/#8 speaker-note assets and hidden Office branches

The independent package inspection found 141 notes picture occurrences across 24 of the 47 PPTs. Previously only notes text was extracted. Extraction revision 3 now keeps notes text/blocks, normalized picture previews/private originals and source/slide/notes/shape IDs, with separate question-slide and solution-note image roles. Explicit notes-page slide thumbnail/number/header/footer/date placeholders remain represented as furniture. Alternate Office branches retain raw XML/native runs and remain unresolved review items.

One notes picture is the static preview of an embedded Word object in Data Interpretation 2, slide 3. The preview can be retained without reading/executing the embedded object. Its meaning and the Office branch remain unverified. The final bench independently counts expected versus retained notes pictures. Revision-2 catalogs must be re-extracted before approval; the stored 0.3.5 release is untouched.

Direct asset inspection confirmed a useful painted-cube diagram on Cubes slide 8's notes page; two sampled Clock/Syllogism assets were provider artwork, illustrating why image count alone is not content coverage. Native Clock slide 6's missing “minutes” run resides in AlternateContent and is now retained as branch evidence rather than silently omitted. This does not reconstruct its equation or establish the rendered branch.

Latest report: <source-dir> Five additional fixture tests cover role separation, notes-only teaching images, furniture decisions, hidden branch evidence, legacy approval and static object previews. Full visual/answer verification, reviewed template exclusions, cross-slide question linking, OCR/PDF extraction, actual formula text and public lesson delivery remain open.

Final source comparison: **141 expected / 141 retained notes pictures**, unchanged source hashes, no missing native-run finding, and 47 explicit unresolved Office-branch findings. Question candidates remain 720 / 499 notes-confirmed; all 27 topics and 78 citations are accounted for. Meaning, layout, copied source-answer errors and the 145 failed question parses are not solved by retaining evidence.
