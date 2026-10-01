# Pipeline test bench (#36)

The bench compares every stored Learn topic with fresh extraction of its cited sources. It does not approve/import, alter sources, or open the learner database for writing. Use it during #1–8/#10; keep formatting #37 deferred.

From Grove's backend directory, in PowerShell:

~~~powershell
.\.venv\Scripts\python.exe -B -X utf8 -m ingestion.cli audit --database ..\data\grove.db --source "$env:GROVE_SOURCE_DIR" --work ../.local/audit/learn-bench-new --media ..\content\media
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

Baseline: grove-ingested 0.3.5 from 20 September. Report: .local/audit/learn-bench-before/bench-report.html.

All **27 topics / 78 cited files** were accounted for: **47 PPTs / 1,214 slide positions**, plus **31 PDF placeholder records** (not extracted pages). No missing/changed-hash citation. Four old slide counts differ. Structural validation passed; approval remains blocked.

Nine stored topics have **no examples**: Pattern Completion, Directions, Syllogisms, Profit Loss, Calendars, Clocks, Relative Speed, Speed Distance Time and Time Work. A different set of nine has **placeholder summaries** in both stored and fresh content: Analogies, Equations, Averages, Profit Loss, Percentages, Clocks, Relative Speed, Speed Distance Time and Time Work. Syllogisms has native teaching prose; its question prompts and choices are on different slides, so the current single-slide parser produces no examples. Pattern Completion includes quantitative cube/root teaching misclassified by the broad filename rule. Findings include 145 unparsed question slides, 94 ambiguous option mappings and 273 parsed questions lacking recognized notes answers. Categories overlap and are not independently confirmed source errors.

All 27 fresh topics retain segments omitted by the public schema. Eight stored topics have recall questions in formula lists. Thirty formatting clues (7 delimiter imbalances / 23 long paragraphs) belong to deferred #37. Visual/vector flags include artwork; their counts do not measure teaching-image loss.

Six regression cases cover topic accounting/stable IDs, independent text/slide loss, read-only release selection, real PPT extraction/source preservation, path boundaries and HTML escaping. Full visual/mathematical review remains open. Independent Speed Distance Time calculations are in CONTENT_REFRESH_AUDIT.md.

## #7 notes-label improvement

Tested after-report: .local/audit/learn-bench-notes-reviewed/bench-report.html. The same frozen release and all 78 source hashes were used. Notes-confirmed candidates increased **407 → 499**, with no previously recognized key changed/lost. Parsed questions missing recognized keys fell **273 → 149**; 32 of the recovered labels still have ambiguous choices and cannot become examples. Total question candidates stay 720; 145 question-parse failures and 94 ambiguous mappings remain.

Speed Distance Time recovers its five explicit keys (slides 3–7), matching the pilot's independent calculations. Eight topics now have more draft example candidates than the stored lesson; summaries, visual interpretation and delivery contracts remain unresolved. Higher overall finding counts can reflect more surfaced draft examples hitting the unchanged public schema, not worsening extraction.

Twenty-one notes regression cases cover real label/glyph/nonbreaking-space variants, conflicting or multiple labels, incidental prose, out-of-choice keys, preservation of surrounding solution text, and choice ambiguity. Intermediate development reports learn-bench-notes and learn-bench-notes-fixed are superseded by learn-bench-notes-reviewed; they are not evidence for the tested outcome.

## #2/#4/#6/#8 speaker-note assets and hidden Office branches

The independent package inspection found 141 notes picture occurrences across 24 of the 47 PPTs. Previously only notes text was extracted. Extraction revision 3 now keeps notes text/blocks, normalized picture previews/private originals and source/slide/notes/shape IDs, with separate question-slide and solution-note image roles. Explicit notes-page slide thumbnail/number/header/footer/date placeholders remain represented as furniture. Alternate Office branches retain raw XML/native runs and remain unresolved review items.

One notes picture is the static preview of an embedded Word object in Data Interpretation 2, slide 3. The preview can be retained without reading/executing the embedded object. Its meaning and the Office branch remain unverified. The final bench independently counts expected versus retained notes pictures. Revision-2 catalogs must be re-extracted before approval; the stored 0.3.5 release is untouched.

Direct asset inspection confirmed a useful painted-cube diagram on Cubes slide 8's notes page; two sampled Clock/Syllogism assets were provider artwork, illustrating why image count alone is not content coverage. Native Clock slide 6's missing “minutes” run resides in AlternateContent and is now retained as branch evidence rather than silently omitted. This does not reconstruct its equation or establish the rendered branch.

Latest report: .local/audit/learn-bench-final/bench-report.html. Five additional fixture tests cover role separation, notes-only teaching images, furniture decisions, hidden branch evidence, legacy approval and static object previews. Full visual/answer verification, reviewed template exclusions, cross-slide question linking, OCR/PDF extraction, actual formula text and public lesson delivery remain open.

Final source comparison: **141 expected / 141 retained notes pictures**, unchanged source hashes, no missing native-run finding, and 47 explicit unresolved Office-branch findings. Question candidates remain 720 / 499 notes-confirmed; all 27 topics and 78 citations are accounted for. Meaning, layout, copied source-answer errors and the 145 failed question parses are not solved by retaining evidence.

## Adjacent questions, explicit choices and classification — 1 October 2026

Latest tested report: `.local/audit/learn-bench-wave3-final/bench-report.html`. The same 27 topics / 78 source snapshots / 1,245 records remain accounted for; source hashes/counts and 141 notes picture occurrences are unchanged. One classification change separates numeric Cubes and Cube Roots from spatial painted cubes.

| Organizer result | Previous committed bench | This wave |
|---|---:|---:|
| Question candidates | 720 | 751 |
| Notes-confirmed keys | 499 | 598 |
| Unparsed question slides | 145 | 92 |
| Ambiguous choice mappings | 94 | 17 |
| Explicit adjacent prompt/choice pairs | 0 | 22 |

All previously recognized keys survive unchanged. Split records preserve prompt and solution-slide snapshots, raw blocks and notes assets. Row matching requires unique positioned unrotated boxes; no guessing fallback for incomplete native layouts. A–E labels keep their actual keys rather than being renumbered. Missing notes labels (150), out-of-choice labels (2), residual mappings and source-answer/visual meaning remain review work.

Development reports `learn-bench-choices` and `learn-bench-choices-reviewed` are superseded by `learn-bench-wave3-final`; the checked organizer snapshot recorded the final parser before the classification change. Public field loss still affects all 27 concepts. No refreshed release has been imported. The strict local pack/import boundary is documented in `CONTENT_IMPORT.md`; visual/source review and public lesson delivery remain prerequisites.

## Visual/source-review companion — 1 October 2026

The native all-Learn report above stays the baseline for all 27 topics/78 sources. Optional companion stages in `VISUAL_SOURCE_REVIEW.md` add complete original slide frames, separate offline OCR text/word boxes and snapshot-scoped review annotations, without rewriting that catalog or learner content.

- `.local/audit/wave4-whole-slides/visual-report.json`: 106/106 rendered original positions across four text/image/hybrid pilots; source hashes preserved.
- `.local/audit/wave4-ocr-pilots/ocr-report.html`: 106 OCR candidates, 103 heuristic token disagreements, 11 missing-option-label clues. No inferred OCR accuracy score or fabricated confidence.
- `.local/audit/wave4-source-review/source-review-report.html`: 11 traceable annotations, exact whole-frame links, native issues, observations versus proposed corrections, calculation/OCR evidence and links back to the native bench. Acceptance checks integrity, not semantic truth or publication readiness.

Observed failures include native omission of cube-diagram labels, OCR omission of Vertex, loss of Clock's mixed-fraction numerator and source-level bad units/approximation/ambiguous “45th.” SDT's notes also contain a wrong multiplication line despite a correct answer. One Syllogisms key is independently solved and a provider-logo occurrence is scoped to one source shape. These records do not automatically alter lessons or remove conservative blockers.

Twenty-three review, fifteen renderer and twelve OCR regression cases pass; the full backend suite passes 230 tests. Full-corpus visual/OCR coverage, semantic enrichment and ordered public lesson delivery remain future work. Original source/native evidence and active release 0.3.5 remain unchanged.

## Ordered lesson/source-figure companion — 1 October 2026

`LESSON_PREVIEW.md` documents the private draft compiler, isolated read-only API and two runnable review pilots. The original Cubes PNG preserves Face/Edge/Vertex through browser display; SDT adds an independently checked baseline-method candidate. The all-Learn native baseline remains unchanged. Final evidence is `.local/audit/wave5-integrity-check.json`: 78 unchanged sources, 43 unchanged fresh native slides, 11 current annotations, two API-preserved drafts and unchanged frozen live release 0.3.5. Full backend tests pass 274; frontend build and desktop/390px/missing-image checks pass. UI/curriculum await user review, and full-corpus semantic review/normal PNG lesson publication remain open.
