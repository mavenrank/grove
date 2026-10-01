# Whole-slide source inspection

`grove-ingest visuals` renders selected original PPTX slide positions into a new inspection directory. It does not edit the native catalog, approve knowledge or import a learner release. Notes text/pictures remain separate evidence in the extraction catalog; these frames depict the slide surface only.

The optional local adapter requires Windows and desktop PowerPoint. It opens an inspection copy read-only, without a presentation window, with macros disabled. An existing PowerPoint process causes a clear refusal so the tool cannot close or change the user's presentation session. Active/embedded payloads and external linked content are outside this pilot; passive hyperlink relationships are retained but not followed. Unsupported sources are recorded as blocked rather than silently omitted.

The adapter uses Microsoft's documented [Presentations.Open](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.presentations.open), [Slide.Export](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.slide.export) and [AutomationSecurity](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.application.automationsecurity). A subprocess timeout is reported as blocked; it can leave an Office process needing to exit before a retry. The tool does not terminate arbitrary Office processes.

From the backend directory:

```powershell
.\.venv\Scripts\python.exe -B -X utf8 -m ingestion.cli visuals --catalog <reviewed-work>\catalog.json --source <source-root> --output <new-visual-directory> --deck <catalog-deck-id>
```

Repeat `--deck` for another deck. Repeat `--slide` to select original positions; omit it for all slides in the selected decks. `--width` defaults to 1600 (800–3200 allowed). The batch is capped at 200 positions. Source hash/containment, count/positions, PNG format/dimensions and rendered-file hashes are checked. Original source bytes and catalog data remain unchanged. `visual-report.json` contains source and slide IDs, native text/issues, adapter/Office/OS versions and local PNG paths. All outputs are private source-derived material and stay outside Git.

The first real pilot rendered all **106 positions** from painted Cubes (25), Syllogisms (36), Clocks (27) and Speed Distance Time (18), with unchanged source hashes. Output: `.local/audit/wave4-whole-slides/visual-report.json`. Fifteen fixture tests cover source preservation, invalid plans, external links, wrong render positions/counts/paths/dimensions and timeouts.

Directly viewed Speed Distance Time slides 3 and 17. Slide 3 shows 5/3 hours in the main prompt, confirming the pilot's 720 km/h calculation; a small clipped fraction at the top is separate source artwork. Slide 17 visibly prints “45th” in both slowdown clauses. That is a source ambiguity, rather than evidence that native extraction removed a slash. These observations do not resolve the source's answer/rounding/choice errors recorded in `CONTENT_REFRESH_AUDIT.md`.

Offline Windows OCR was separately probed on four of those slides. It read substantial text but missed some A/C option labels and preserved the ambiguous “45th.” OCR remains a candidate with no fabricated confidence and no automatic override of native text. The integrated candidate/review stages are described below.

## Offline OCR candidates

The separate enrichment command consumes a verified visual report and writes a fresh candidate report. It does not rerender, replace native text, solve diagrams, change the catalog or approve knowledge:

```powershell
.\.venv\Scripts\python.exe -B -X utf8 -m ingestion.cli ocr --visual-report <visual-directory>\visual-report.json --output <new-ocr-directory> --language en-US
```

The local [Windows OCR API](https://learn.microsoft.com/en-us/uwp/api/windows.media.ocr.ocrengine.trycreatefromuserprofilelanguages?view=winrt-20348) requires the selected language installed; the tested machine provides en-US/en-GB. The adapter is offline and records its revision, OS build, language and maximum image dimensions. The API supplies text/lines/word rectangles and text angle, without per-word confidence scores; confidence stays null. Missing language/runtime and source/frame/result-integrity problems produce explicit blocked records.

Source/frame hashes are checked before and after OCR. Word rectangles must be finite and inside the original pixel canvas. Native text and OCR remain separate. Differences, extra/missing tokens, empty output and missing option labels are heuristic review clues, not proof of errors or coverage. `ocr-report.html` exposes each whole frame, native text, OCR text, differences and word boxes; it uses escaped local content, no script or remote resources.

The real 106-frame pilot produced 106 candidates, 103 token-disagreement clues and 11 missing-option-label clues. Native Cubes slide 3 contains only “Cubes”; OCR recovers Face and Edge from the embedded diagram but misses Vertex and includes provider text FACE. Direct inspection sees all three teaching labels. Clock slide 6 visibly shows 65 5/11 minutes, while OCR loses the numerator. This demonstrates useful image text recovery alongside unresolved label/mathematical-notation failures. No accuracy percentage is inferred from successful OCR execution.

Output: `.local/audit/wave4-ocr-pilots/ocr-report.html`. Twelve OCR fixture cases plus fifteen renderer cases pass. Original source/frame/native-report hashes remain unchanged. Native equations, OCR corrections, diagram relationships and publication are still review work.

## Source-scoped review annotations

```powershell
.\.venv\Scripts\python.exe -B -X utf8 -m ingestion.cli review-sources --catalog <work>\catalog.json --source <source-root> --visual-report <visual-directory>\visual-report.json --manifest <review-manifest.json> --evidence-root <private-evidence-root> --output <new-review-directory>
```

The input is `{ "review_schema_version": 1, "records": [...] }`. Each record requires `review_id`, `deck_id`, `source_path`, `source_hash`, `slide_id`, `slide_number`, `surface` (`slide`/`notes`), `target` (`slide`/`shape`), `decision`, nonempty `reason`, `reviewer`, `observed` and `evidence`. Optional `proposed` keeps an interpretation/correction separate from observed source facts. A shape target also requires an integer `shape_id` and `block_sha256`, computed with `ingestion.source_review.object_sha256` over that complete native block. AlternateContent branch IDs are not integer shape targets; use a slide annotation while branch-specific review remains open.

Decisions are `decoration_candidate`, `confirm_visual_text`, `flag_source_error`, `flag_source_ambiguity`, `flag_ocr_error` and `confirm_answer_derivation`. Decoration must identify one exact shape; no blanket slide/image-ID exclusion is allowed. The validator does not apply exclusions or corrections to the organizer. That integration and semantic review are later work.

Evidence entries contain `kind`, relative `path` and full file `sha256`. Every record needs `rendered_slide` evidence that matches this source/slide snapshot in the visual report. Notes reviews additionally require `native_catalog` evidence equal to the supplied catalog, because a whole-slide frame does not render the notes page. `supporting` references can retain OCR reports, calculation results, adjacent frames or other context without claiming that the validator proves their contents. Paths/hashes are checked; source and evidence files are rechecked before the report is saved.

Unknown/ambiguous deck/slide/shape identities, stale source/block/frame hashes, missing reasons/evidence, path escapes, duplicate IDs and competing records for the same target/decision are rejected. All members of a conflicting set are rejected rather than picking the first. Unknown fields/approval decisions are refused. Exit status is 0 when all annotations are traceable, 1 for rejected records and 2 for invalid inputs. `source-review-report.json/html` retain rejected reasons and native issues; rejected evidence does not become clickable in HTML.

**Accepted annotation means provenance validation only.** The report is always unapproved, does not solve/verify claims automatically and has no publication effect. Digests do not authenticate a reviewer or prove that a manually supplied report is truthful. Existing pack/import gates still require their own reviewed work and semantic checks.

The first manifest has 11 annotations on seven original slide positions plus SDT slide 3's notes, across four source decks. Direct comparisons record the SDT bad choice units, unstated approximation and literal “45th”; Cubes' native/OCR label gaps; Clock's fraction loss; one exact provider-logo occurrence; the correct SDT 720 km/h result and incorrect multiplication in its original notes. The first Syllogisms prompt/options pair is independently checked by all 256 possible actor/singer/dancer Venn-cell occupancy assignments: 32 satisfy the premises, all support conclusion 1 and contradict conclusion 2, matching A. This verifies one additional key, not the remaining source pool.

Private manifest/calculation evidence: `.local/audit/wave4-review-manifest.json` and `wave4-independent-checks.json`. Companion bench: `wave4-source-review/source-review-report.html`, with links to the OCR report and existing all-Learn bench. Eleven annotations pass integrity checks. Twenty-three regression cases cover preservation, stale/ambiguous scopes, bad evidence, conflicting records, notes context, approval bypass attempts, mid-validation source changes and refusal to overwrite inputs. Sources, native catalogs and the learner release remain unchanged.
