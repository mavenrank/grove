# Grove fix log and review checkpoints

## Checkpoint 1 — 30 September 2026

The first implementation batch is ready for review and remains **uncommitted and unstaged**. It touches six issue groups: #18, #26, #27, #28, #7 and #30. Several groups have broader remaining scope; this is not a claim that six complete product initiatives are finished. The exact completed tasks are checked in `REMEDIATION_TODO.md`.

Git is local on `main`, with source baseline `1bc58c8` and no remote. The baseline excludes the learner database, source-derived media, generated ingestion packs, dependencies, environment files and local tool metadata. It preserves application source, not a backup of the learner's content and progress.

### #18 — known generator errors corrected; complete semantic audit remains open

Percentage questions now retain exact fractional results, including 12% of 160 = 19.2. Simple-interest questions retain the exact currency amount rather than rounding to whole rupees without instruction. The ordering puzzle asks for the uniquely fixed second person; the old “cannot be second” question admitted several correct choices. Circular seating descriptions now actually start at P, and inward-facing left uses the next clockwise seat.

The registry rejects invalid prompt/explanation strings, wrong option counts, duplicate options and invalid answer indexes before materializing a session. These checks prove structure, not mathematical correctness. Independent Decimal, permutation and spatial-vector checks verify the corrected families. The structural survey checks every registered family across three difficulty labels and 30 seeds for reproducibility.

Files: `backend/app/content_engine/families/{frp,averages,arrangements,registry}.py`, `backend/tests/test_generator_correctness.py`.

Remaining: independent semantic oracles for other families; reviewed handling of historical attempts containing faulty questions. Stored historical questions and scores are not rewritten. Corrections apply to newly generated sessions.

### #26 — atomic expiry, answering and finalization implemented

Question serving, marks, answers, dwell and events now recheck ownership, session state and deadline inside the write transaction. Submitted sessions reject new interactions with 409; expired sessions reject them with 410. Lazy expiry stores its score before returning an error, including when the first late request is an answer. The deadline is closed at equality, not only after it has passed.

Answer choice and correctness are written together. Finalization reads answers, computes its score and stores the terminal transition under the same SQLite transaction. An independent process/wrapper cannot slip an answer between score calculation and state change. Failed answer/receipt writes and failed score inserts roll back completely. Duplicate manual finish still returns `already_finalized`; finishing a stored expired session returns its frozen result.

Files: `backend/app/engine/{runtime,scoring}.py`, `backend/app/db/{connection,sessions}.py`, `backend/app/routers/tests.py`, `backend/tests/test_runtime_integrity.py`.

Verification: both answer-first and finish-first interleavings use separate Database wrappers with independent Python locks. SQLite blocks the competing writer, and the final stored score agrees with the accepted answers. Terminal interaction retries leave questions, timing, scores, events and receipts unchanged.

Remaining related work: client pending-save/finish recovery (#25), exact client timing (#22), session resume (#30) and versioned metadata (#31). A test can still remain active in storage until an interaction/finish observes its elapsed deadline; scheduled expiry and client recovery are not part of this batch.

### #27 — persisted answer retry receipts implemented; client ordering and telemetry remain open

An answer request may supply an idempotency key. The key, exact request and original accepted response are stored atomically with the answer. Repeating the same request returns the original response without changing the answer timestamp, correctness or current choice. Reusing a key with a different option, position or ticket returns `idempotency_conflict`.

Receipts survive reopening the database. An identical accepted retry can retrieve its receipt after ticket rotation, expiry or submission; this is acknowledgement of a previous write and does not permit a new answer after finalization. Ownership is checked before receipt access. New answer intents need new keys, and keys must be 1–128 characters. Requests without keys keep the existing API compatibility.

Files: `backend/app/db/schema.py`, `backend/app/engine/runtime.py`, `backend/app/routers/requests.py`, `backend/tests/test_runtime_integrity.py`.

Remaining: wire stable per-intent keys and a save queue into the browser (#25); order different answer intents so a delayed older request cannot overwrite a newer choice; event/dwell identifiers and deduplication; receipt retention. Returning the original receipt includes its original remaining-question count, not a newly computed progress snapshot.

### #28 — active-test history bypass closed; full isolation policy remains open

Detailed history now requires both a submitted/expired state and a stored score. Active and cancelled sessions, and expired sessions with no score, return 409 `not_finalized` without exposing the question list or metadata. Finalized history and missing-session 404 behaviour continue to work. The compact history list remains available.

Files: `backend/app/history.py`, `backend/app/routers/misc.py`, `backend/tests/test_runtime_integrity.py`.

Remaining: learning/card/source-open routes, multi-tab policy and cached browser navigation. Until the UI recovery work (#29), opening an unfinished test's detail route can show the generic error; a failed cached request can also require a page reload after the test finishes. Review that learner experience in the later UI batch.

### #7 — pack approval validation bypass closed; complete publication gate remains open

An approved pack requires a successful supplied report and a fresh validation of the actual catalog. A failed or stale success report cannot authorize an invalid catalog. The CLI returns a clear nonzero error before writing a publishable pack. Unapproved drafts remain available for inspection.

Files: `backend/ingestion/pipeline.py`, `backend/tests/test_approval_gate.py`.

Remaining: strict import schemas, per-record review state, OCR confidence gates, answer verification, media checks and publication quality criteria. The current validator itself is narrow; a passing report does not prove a lesson is complete. A manually fabricated approved pack can still bypass this pack-stage protection through the current import CLI. That import boundary is explicitly pending, not silently treated as solved.

### #30 — connection integrity and cross-process locking implemented; recovery remains open

Every SQLite connection enables foreign keys. Write transactions acquire `BEGIN IMMEDIATE` before reading mutable state, so serialization works across independent database wrappers and processes, in addition to the existing in-process lock. Orphan inserts are rejected.

The new `answer_receipts` table is additive and created with `IF NOT EXISTS` during normal initialization. A disposable database shaped like the baseline was reopened: existing session/question data survived, the missing table was created, and the foreign-key check remained clean. Restart the backend to initialize this table before trying keyed answer requests against an already-running server without reload.

Files: `backend/app/db/{connection,schema}.py`, `backend/tests/test_runtime_integrity.py`.

Remaining: versioned migrations, a read-only audit of historical integrity, explicit repair policy, backup/restore and active-session recovery. Enabling foreign keys does not repair older orphan records. No corpus reimport or direct learner-record repair was performed in this batch.

## Verification

- Full backend suite: **70 passed**, including **31 new regression cases**. Two existing dependency deprecation warnings remain (Starlette/httpx and AnyIO); there were no application test failures in the final run.
- Tests used fresh temporary data/content/media locations and a unique pytest temporary directory, with bytecode and pytest cache writes disabled.
- Numeric oracle checks cover 300 seeds per corrected numerical family and each of three difficulty labels. Ordering covers 100 seeds for each nondirect label; seating covers 300 spatial cases.
- Existing security, content, ingestion, SRS and end-to-end test-loop checks continue to pass.
- Git whitespace validation passed. No frontend source was changed; frontend build verification was not repeated for this backend-only batch.

Reproduce from `backend/` in PowerShell with the existing virtual environment:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$testRuntimeRoot = Join-Path $env:TEMP ('grove-check-' + [guid]::NewGuid())
$env:GROVE_DATA_DIR = Join-Path $testRuntimeRoot 'data'
$env:GROVE_CONTENT_DIR = Join-Path $testRuntimeRoot 'content'
$env:GROVE_MEDIA_DIR = Join-Path $testRuntimeRoot 'media'
& '.\.venv\Scripts\python.exe' -B -m pytest -q -p no:cacheprovider --basetemp (Join-Path $testRuntimeRoot 'pytest')
```

Run that command in a separate test terminal so the temporary environment settings do not carry over into the regular application server.

## What to review now

1. Review the batch order in `REMEDIATION_TODO.md`: ingestion is next, followed by the baseline → pattern → shortcut curriculum and bounded coverage/generation models.
2. Review the intended test behaviour: active detailed history is unavailable, and terminal tests reject new interactions. A receipt for a previously accepted answer may still be acknowledged without changing results.
3. Review the corrected ordering/seating questions and the decision to retain precise numerical answers. These changes affect new questions; previous attempts retain their original material.

The batch stops here before a fix commit. The next ingestion checkpoint should compare representative text-only, image-only and hybrid slides with their extracted drafts before changing the database's active release. The later curriculum/UI checkpoint should present one complete pilot topic and runnable screens, then stop before committing for the user's review.

## UI startup repair — 30 September 2026

User-reported blocker: the Overview crashed with `Tooltip must be used within TooltipProvider`. The application root now wraps every route in Radix's `TooltipProvider`, so shared metric tooltips have the required context. `index.html` now declares `/favicon.svg`, and the new public SVG is served successfully instead of relying on a missing default icon.

Files: `frontend/src/main.tsx`, `frontend/index.html`, `frontend/public/favicon.svg`. This restores startup; the broader responsive UI work in #33 remains open.

Verification: reproduced the tooltip error in the browser before the change, then reloaded and confirmed the populated Overview renders with no new browser errors. TypeScript no-emit checking and a production Vite build passed. The declared favicon and proxied API health both return HTTP 200. Screenshot: `<source-dir>`.

The working app is open at http://localhost:5173/ for review. These UI changes remain unstaged and uncommitted, as requested; the earlier batch is also still uncommitted.

### Deferred observation #35 — Learn cold-start delay

The user reported slow Learn navigation, then clarified that it no longer occurs and may have been a cold start. Added #35 as a tentative item at the end of the backlog, to revisit after the main reviewed fixes. A local inspection saw a roughly 280 KB full-concept listing and a roughly 150 ms API sample; neither proves the reported hang's cause. Exploratory performance edits were confined to a scratch staging copy and discarded there. No Learn endpoint, cache, lesson or image-loading implementation was changed in Grove. The tooltip-provider/favicon repair remains the only UI implementation change from this turn and is uncommitted.

## Wave 2 — ingestion evidence and responsive sidebar, 30 September 2026

This checkpoint touches six issue groups: #1, #4, #6, #7, #8 and the requested sidebar portion of #33. These are partial fixes, not closure of the complete ingestion or UI architecture. All source changes, including wave 1 and the startup repair, remain unstaged and uncommitted on baseline `1bc58c8`. No remote is configured.

### #1 — native structure survives extraction

Each PPTX slide now retains typed text/table/image/group/unsupported blocks, shape IDs, source order, projected group coordinates, rotation and an explicit top-left reading-order heuristic. Text blocks retain paragraphs, indentation, runs, bold/italic and superscript baseline attributes. Tables retain rows/cells, merge metadata and column widths. Notes keep line breaks. Empty slides remain numbered catalog records instead of disappearing.

Unknown drawing objects, rotated/flipped groups, native Office Math and extraction failures produce source-specific review items. The extractor does not claim to interpret those objects. Logical reading order across overlapping or multiple columns still needs review; group bounds with rotation/flip are explicitly unresolved.

Files: `backend/ingestion/{extract,extractors,pipeline}.py`.

### #4 — hybrid context remains connected in drafts

Learning segments retain their raw blocks/text alongside normalized text, notes and media IDs. Question candidates and worked-example candidates retain the same slide's positioned blocks, media IDs, answer status and deck/path/hash/slide provenance. Question media also reaches the concept's media inventory rather than disappearing from worked examples. Unparseable question slides remain visible in the review report with their source evidence.

This establishes same-slide context. It does not infer which arrow or diagram label belongs to a value, combine continued slides, recover OCR text or change the current Concept UI to render a reconstructed problem. No new content release was imported.

Files: `backend/ingestion/organize/{concepts,questions}.py`.

### #6 — fewer silent omissions, more visible decisions

The first slide is no longer excluded solely because of its position. A cover candidate requires short title/subtitle placeholders without formulas, images, tables or unresolved shapes. Whole-slide ceremony matches replace broad substring filtering. Repeated images are retained and reported for review rather than automatically deleted after appearing in three sources.

The old minimum byte/dimension image gates are removed: a thin compressed formula picture survives. Delivery previews remain bounded; original image bytes are retained privately as hash-named work-directory evidence, alongside crop metadata and original/preview sizes. Decode/byte/pixel/output-limit failures are reported. Existing caps still require configuration work; the report exposes their current values.

Every source slide has an organization outcome/reason, including duplicate/deferred sources. Discovery records hidden and oversized/unreadable-source exclusions and accepts uppercase extensions. `review-report.json` lists skipped sources, slide decisions, unresolved review, repeated media and presentation truncations. Full formula/code/example candidates survive their display limits; full formula/card mining rejection reasons remain open. A summary no longer uses flashcard formula-noise rules that rejected normal prose containing semicolons.

Files: extraction, pipeline and concept organizer modules.

### #7 — unresolved drafts cannot pass pack approval

Approval revalidates and reorganizes the actual catalog. It rejects legacy catalogs without the new evidence, empty active content, generic draft summaries, unresolved images/drawings/equations, failed question parsing, missing answers, malformed option mappings and notes answers outside the parsed choices. Matching notes answers carry `notes_confirmed` status; they have not been independently solved. The old `questions_verified` statistic remains a compatibility alias, with an explicit `questions_notes_confirmed` statistic and corrected CLI wording.

`ok` reports structural extraction/validation success; `ready_for_approval` also requires resolved organization quality. Thus a draft run can exit successfully and remain blocked from approval. Passing a stripped or stale content-drafts object cannot bypass this boundary.

Remaining: independently verified answers, strict import schemas (a fabricated approved JSON pack still needs an import-boundary guard), reviewed overrides/waivers and a practical human review workflow. The current flags are deliberately conservative: provider logos and decorative drawings can enter the review queue until identified explicitly. They are not all teaching diagrams. Existing catalogs must be re-extracted into a separate work directory before another approved pack is built; the active app release is untouched.

### #8 — source identities and media evidence no longer collide by stem

Deck IDs now include a hash of the normalized relative path. Source edits preserve that path identity, while slide/block IDs include the content snapshot hash. Same filenames in two directories cannot overwrite each other's media index. Revalidation clears/recomputes duplicate markers and rejects duplicate identities.

Normalization rejects sources resolving outside the corpus root and detects a source changing during extraction. Pack validation checks referenced delivery images exist, match their content-hash IDs and agree with the slide's media evidence. Missing/corrupt images are hard failures. Originals remain private review files; the media-import/install and relocated-source policies still need work.

### #33 — responsive, resizable sidebar ready for user review

Added a shadcn-style SidebarProvider/Sidebar/Header/Content/Footer/Inset/Menu/Rail/Trigger composition using Radix Dialog, Slot and the existing TooltipProvider. This is adapted source, based on the [official Radix sidebar composition](https://ui.shadcn.com/docs/components/radix/sidebar), with Grove's forest/paper/gold palette, grouped navigation, selected-route treatment and a skip-to-content link.

| App width | Initial navigation | Expanded width |
|---|---|---|
| Below 768 px | Closed drawer | Up to 288 px, leaving 48 px outside |
| 768–1023 px | 64 px icon rail | 208 px |
| 1024–1439 px | Expanded | 240 px |
| 1440 px and above | Expanded | 264 px |

Desktop/tablet expansion and widths are remembered separately per breakpoint. Dragging the edge grip resizes within 184 px and the smaller of 320 px or one third of the viewport. Arrow keys adjust 8 px (24 px with Shift), Home/End choose bounds and double-click restores the breakpoint default. The toggle and Ctrl/Cmd+B switch expanded/rail modes; editing fields keep their normal shortcut behaviour. Mobile navigation uses a focused modal drawer, Escape/backdrop/close control and automatic closing after navigation, returning focus to the trigger.

Files: `frontend/src/components/ui/sidebar.tsx`, `frontend/src/layout.tsx`, `frontend/src/index.css`, frontend package/lock files. Test/Results routes retain their existing dedicated layout. No Learn fetching or caching changes were introduced for deferred observation #35.

### Verification and source evidence

- Full backend suite: **94 passed**, including **24 new ingestion regression cases**. Two existing dependency deprecation warnings remain. Tests use disposable data/content/media directories.
- Synthetic decks verify first-slide teaching content, covers, empty slides, table cells, grouped steps, notes, superscript formatting, unresolved native math, thin images/crops, reused diagrams, hybrid questions, source collisions/revisions, invalid answers, parse failures, uppercase extensions, unsupported formats, missing/corrupt/mismatched media, stale catalogs, placeholder summaries and truncation evidence.
- A separate draft-only dry run re-extracted three existing decks: Word Group Categorization (36 slides), Data Arrangements (36) and Data Interpretation (34). All 106 original slide positions survived. New records include previously filtered small assets, so the deck selected for its old native-text records also proved to contain pictures. The new mode counts include provider/template images; they do not measure OCR coverage or meaningful diagram counts.
- That real-source report stays blocked: unresolved visual/drawing evidence, 33 unparsed question slides, 26 ambiguous option mappings and one placeholder topic summary. These are review findings, not automatic repairs of the answers. Source copies, the active release and learner results were not rewritten.
- Draft comparison and catalog: `<source-dir>`. Originals and normalized preview files are in its `media/` directory. This is scratch review output outside the tracked application source.
- Frontend TypeScript/production build passed. Browser checks at 360, 900, 1200 and 1600 px showed no Learn horizontal overflow. Pointer drag changed 240 → 280 px and survived reload; keyboard bounds/reset and Ctrl+B toggle passed. Mobile Escape and navigation close returned focus; the drawer hid the page from accessibility while open.
- Desktop/mobile review screenshots: `<source-dir>`. Temporary viewport overrides were reset. No new Grove browser errors were observed during these checks; historical errors belong to the other app on port 5173.
- Git whitespace validation passed; HEAD remains the baseline, with no staged changes or remote.

### Review checkpoint

Grove is running at http://localhost:5174/ because another local application currently owns 5173; the backend runs at 8001. Review the sidebar's visual spacing, mobile drawer, tablet rail and desktop grip/toggle. The rest of the responsive page/runner audit is still open.

Also review the conservative ingestion policy: source evidence is retained, but unresolved image meaning and ambiguous question mapping block future pack approval. OCR/diagram interpretation and reviewed template exclusions are the next ingestion work. Current learner content is unchanged. Stop here before a fix commit, as requested; #35 remains a tentative item at the end.

## User approval and local commit checkpoint — 30 September 2026

The user acknowledged the sidebar and both remediation waves, then explicitly requested committing those changes. This supersedes the earlier uncommitted-review checkpoint. Commit the approved runtime/generator, ingestion and frontend/documentation changes locally. No remote, push or content-release replacement is authorized by this approval.

The user also reported the empty Speed Distance Time lesson and requested a trace from the displayed release to the actual PPT, a draft-only rerun where needed, and a source-versus-pipeline-versus-UI review before refreshed publication. Those findings belong to the next checkpoint rather than being inferred from the screenshot alone.

## Committed work and stale-content investigation — 30 September 2026

Approved local commits: `91467d8` (runtime/generators), `b580d9f` (ingestion), `54430ae` (startup/sidebar/docs). Staged whitespace checks passed after trimming two extra audit-document end lines. The source snapshot still has no remote. The approved code is unchanged from the 94-passing-test and successful frontend-build checkpoint; no redundant application test rerun was needed for these documentation-only additions.

The reported Speed Distance Time topic is the stored `grove-ingested` 0.3.5 release, generated/imported on 20 September. Its live API matches its saved payload: placeholder summary, zero examples/media/segments, and authored flashcard fronts incorrectly reused as formula text. The cited 18-slide source exists and its hash matches the release. Code updates have not refreshed this immutable data.

A read-only database trace and isolated, unapproved PPT extraction recovered 15 native question candidates across all 18 slides. Five explicit `Option` note labels are missed by the `Answer`-only parser; another native solution has no label. Direct image inspection showed provider logos dominate this deck's picture count. Independent arithmetic found a notes substitution error on slide 3, distance-question choices in minutes on slide 12, an unstated rounding convention on slide 16 and a native slowdown-fraction formatting ambiguity on slide 17.

The current Concept public schemas/rendering do not carry the new learning segments or example media/blocks. A rerun plus immediate import therefore would not repair this page. Whole-slide rendering also remains unverified: the bundled importer failed on notes-image relationships and then rejected a notes-free inspection copy. Original slide/media bytes and source files were preserved; native text, notes, positions and individual images were checked directly.

Detailed evidence, independently derived values and rerun checkpoints are in `CONTENT_REFRESH_AUDIT.md`. Next wave: #2, #4, #6, #7, #8, #10, with this topic as the pilot and a full-corpus draft run after representative pilots pass. No new lesson, UI change, replacement release or learner-data modification was published in this investigation.

Persisted the user's exact slide-review delegation policy in `AGENTS.md` and `SOURCE_REVIEW_PROTOCOL.md`. The available runner cannot select standard service and advertises priority, so no subagent was launched against the user's restriction. Direct inspection was necessary for this source discrepancy. #35 remains deferred.

## Pipeline tracking and small commits — 30 September 2026

Added #36 for a repeatable audit of every existing Learn topic against fresh source evidence, within the existing pipeline wave (#2/#4/#6/#7/#8/#10). Added #37 for explanation punctuation/paragraph quality at the tail of the backlog. Findings will distinguish source defects, pipeline losses, public-contract losses and uncertain review clues; the bench cannot approve/import releases.

The user explicitly requested frequent small commits. Persisted that instruction in `AGENTS.md` and the working agreement. Backend/tooling/documentation chunks can be committed after verification; substantial UI/curriculum changes still require concrete user review. This chunk changes tracking only; whitespace/diff review is sufficient verification. No application code or stored content changed.

## #36 — repeatable all-Learn source audit

Added grove-ingest audit with read-only SQLite/frozen JSON input, fresh-directory protection, source containment, independent PPTX slide/native-run checks, public-schema comparison and escaped reports. Every topic/source/slide/outcome is traceable. Unsupported PDFs, missing answers, failed parsing, dropped fields, placeholder summaries and formatting clues are visible. No approval/import path exists.

Ran all 27 stored topics / 78 citations: 47 PPTs with 1,214 slides plus 31 unextracted PDF records. Source hashes match; no cited source was missing. Structural validation passes; semantic approval is blocked. Findings are review clues/evidence, not 4,038 independently incorrect facts. See PIPELINE_TEST_BENCH.md for scope, counts and rerun command.

Six new tests passed, covering database/source byte preservation, independent slide/text loss, topic accounting, path boundaries, stable IDs and HTML escaping. Full visual/mathematical checking and substantive lesson reconstruction remain open.

## #7 — explicit notes-label recovery

Added line-scoped, case-insensitive Answer/Option parsing with parentheses, arrows/private glyphs and Unicode horizontal spaces. Each key retains its matched text/span plus raw notes; label removal preserves solution text before/after it. Conflicting/multiple keys, out-of-choice labels and malformed choices remain blocked. Notes confirmation is still distinct from independent answer verification.

The bench exposed a character-class mistake and a nonbreaking-space regression during development; tests caught the former and the before/after source comparison caught the latter. Both were repaired before commitment. Twenty-one targeted regression cases pass. Across identical source hashes, notes-confirmed candidates rise 407 → 499; missing labels fall 273 → 149, with no old key changed/lost. All five explicit Speed Distance Time labels agree with the independently derived pilot answers. Source errors/uncertainties documented in CONTENT_REFRESH_AUDIT.md remain unresolved.

The bench chunk passed the full 100-test suite. The notes chunk adds 21 tests. Source material, current release 0.3.5 and learner history remain unchanged; no UI/curriculum release was published.

## #2/#4/#6/#7/#8 — retain notes assets and Office branch evidence

Independent source inspection found 141 picture occurrences on notes pages across 24 PPTs. Added revision-3 extraction of notes blocks/text/pictures with private originals, distinct source/slide/notes/shape IDs, slide-versus-solution media roles, and explicit notes-page furniture records. Legacy revision-2 catalogs now require re-extraction before approval. Questions/examples/learning segments retain their own notes context; unknown diagram/object meaning remains blocked.

AlternateContent raw XML/native runs are preserved because python-pptx's shape iterator omits those branches. This captures Clock slide 6's “minutes” run without choosing a rendered equation branch. The final missing notes image is Data Interpretation 2 slide 3's static embedded-Word-object preview; only its image relationship is read, without accessing/executing the object payload. The bench checks its expected count independently and labels notes assets separately in the report.

Directly viewed the source-derived cube diagram on Cubes slide 8's notes page and representative provider assets. Source text also established that Syllogisms has teaching prose and split prompt/options slides, and that a cube/root arithmetic deck is misclassified as Pattern Completion. Added those cases to #4/#5. Corrected an earlier report narrative that conflated the nine no-example topics with the different nine placeholder-summary topics; machine reports already kept the separate per-topic facts.

Five new fixture tests plus the full backend suite pass: 126 tests, two existing dependency warnings. Application UI, active release and learner history are unchanged. No whole-slide visual/OCR or complete source-answer correctness claim is made.

## #4/#6/#7/#8 — explicit choices and adjacent question snapshots — 1 October 2026

The source bench showed A–E choice rows, shape-order differences and questions split across adjacent slides. Added explicit label mapping (including E), bounded unique row-centre pairing for unrotated separate boxes, and adjacent joins requiring one matching explicit question number. Missing/duplicate choices, competing rows, captions, groups/rotation and incomplete joins remain blocked. Positioned content cannot fall back to guessing by shape order. The legacy text-only adapter still accepts complete sequential bare-label lists.

Joined records retain both original source snapshots and blocks, choices/solution provenance, notes assets and an explicit continuation decision for the second slide. The input catalog remains unchanged. Source note labels mean notes-confirmed, not independently solved. Native inspection of Syllogisms slides 6–7 confirmed the matching Question 1, five choices and answer A; Word Group Categorization slide 7 includes the fifth choice Physics, which the A–D parser previously mishandled.

Eighteen new regression cases and 45 existing ingestion/notes cases pass (63 total). Comparing the same 78-source catalog with the final organizer gives 751 question candidates / 598 notes-confirmed, up from 720 / 499. No old confirmed key changed or disappeared. Twenty-two adjacent pairs are linked, including 15 Syllogisms questions. Parse failures fall 145 → 92; ambiguous choices 94 → 17. An overly strict row-height assumption was caught by the source comparison and corrected using bounded centres and additional regression checks before commitment.

The checked organizer snapshot is `<source-dir>`; earlier `learn-bench-choices*` reports are development snapshots. A complete report will follow the remaining wave changes. The 1,245 source records remain accounted for, with all raw slide boundaries retained. Active release 0.3.5, learner history and application presentation are unchanged.

## #5 — numeric cube/root classification — 1 October 2026

Native text in the Cubes and Cube Roots deck describes cubing two-digit numbers, while the separate Cubes deck contains painted-face/dice problems and solution diagrams. Added the specific cube/square-root title rule before generic spatial cubes. Bare/painted Cubes and Dice stay in reasoning; algorithm/deferred scope retains precedence. This is a bounded title correction, not a content-derived classification system or approval of every mixed deck.

Ten new classification cases and the existing ingestion cases pass. The affected real source will be traced in the final all-Learn report; current stored topics remain unchanged. General classification confidence, review overrides and multi-topic tagging stay open.

## #31 — immutable database release imports — 1 October 2026

The store previously returned “already present” for any payload reusing a release/version, silently hiding changed content. Imports now compare canonical manifest and payload inside the write transaction: an identical retry is idempotent; changed content raises an explicit conflict and requires a new version. Three regression cases verify key-order-independent retries, payload/manifest conflicts, rollback and preservation of the old release after importing a new version into a disposable database.

Candidate-file immutability follows in the pack boundary chunk. Pinning session generator/taxonomy/blueprint dependencies, runtime authored merges and historical reproduction remain open; this does not close #31.

## #7/#8/#31 — reviewed pack/import boundary — 1 October 2026

Added schema 1 for ingestion packs and typed concepts, segments, examples, cards, questions and source citations. Approval records extraction/organizer versions and catalog/draft digests. Import refuses legacy/truthy approvals, malformed fields, placeholders, invalid choices/citations/classifications, duplicate identities and mismatched media inventories. It requires the reviewed work catalog, current source hashes/path containment and a newly validated/reorganized matching pack; rehashing edited content alone cannot bypass that comparison.

Media installation preflights JPEG existence/hash/size/dimensions/decode and existing-file identity. Atomic exclusive files preserve installed assets and candidate packs; private originals are not installed. Same-content candidate retries retain the original bytes/timestamps, while changed versions fail. SQLite writes happen after verified installation. Digests are local review provenance, not signatures or independent source verification. Valid unused assets may remain after filesystem/database failure and can be reused; separate activation/rollback and cleanup remain open.

Twenty-three import regression cases cover malformed approved JSON, successful/idempotent disposable import, changed source/catalog/content, missing/malformed reviewed work, immutable candidates, missing/corrupted media and non-JPEG bytes with a valid hash. The final full backend suite passes 180 tests, with two existing dependency deprecations. See `CONTENT_IMPORT.md` for compatibility and the future publication procedure.

## Pipeline wave checkpoint — 1 October 2026

Final report: `<source-dir>`. All 27 existing Learn topics, 78 unchanged source snapshots and 1,245 records are accounted for. Independent notes-picture counts still match 141/141. The arithmetic cube/root source is now classified under Numbers; the distinct painted-cube source stays in reasoning.

Compared with the preceding committed bench: question candidates 720 → 751, notes-confirmed 499 → 598, unparsed slides 145 → 92 and ambiguous choices 94 → 17. All 499 previously confirmed keys survive unchanged; 22 adjacent prompt/choice pairs retain their distinct source boundaries. Missing recognized notes keys remain 150; two out-of-choice labels and the remaining ambiguities need review. The higher public-field-loss count reflects more recovered examples/contexts hitting the unchanged API schema, not proof of complete delivery.

This wave touches six groups (#4/#5/#6/#7/#8/#31), with bounded partial fixes rather than closing every group. OCR/full-slide rendering, PDF extraction, reviewed decoration/source-answer decisions, actual formula content and the lesson API/UI remain publication prerequisites. The final live database check used read-only SQLite and confirmed active release 0.3.5 is identical to the frozen payload. No learner history, source bytes, UI or replacement lesson release was changed. #35 and #37 remain deferred. No priority-only slide reviewer was used against the user's standard-service restriction.

## #2/#3/#4/#8 — native whole-slide inspection — 1 October 2026

The bundled importer had failed on these decks. A runtime probe found installed PowerPoint 16.0 and Windows English OCR. Added an optional read-only PowerPoint renderer: fresh bounded outputs, inspection copy, disabled macros, no presentation window, no existing user Office session, active/external-linked package exclusions, subprocess timeout and independent source/count/position/PNG checks. Source and raw catalog bytes remain intact; rendering cannot approve/import content.

Fifteen fixture cases pass. The real CLI rendered all 106 slide positions across Cubes/Syllogisms/Clocks/Speed Distance Time, preserving source hashes. Direct image inspection confirmed 5/3 hours in the SDT slide 3 prompt and literal “45th” in slide 17, narrowing the latter to a source ambiguity. A four-slide offline OCR probe read substantial content but missed choice labels, so integration will retain explicit uncertainty rather than replace native evidence.

See `VISUAL_SOURCE_REVIEW.md` for runtime requirements, scope, commands, Microsoft API references and the private output location. Notes assets, unresolved visual/math meaning, image-led knowledge extraction, PDF support and reviewed learner delivery remain open. No original PPT, stored release or learner history changed; no priority-only reviewer was launched.

## #2/#4/#7/#8 — offline OCR candidate enrichment — 1 October 2026

Added a separate Windows OCR stage over verified native-render frames. It preserves native text and source/frame hashes, captures word rectangles/text angle, records runtime/OS/language versions and leaves unavailable confidence null. Result identity, bounds, source/frame changes, runtime failure and missing language remain explicit blocked cases. Escaped local HTML shows whole slides beside native/OCR candidates and heuristic disagreements; it cannot approve/import content.

Twelve new fixture cases and the fifteen renderer cases pass. Real offline en-US OCR produced 106/106 pilot candidates with unchanged source/frame/native-report bytes. It recovered Face and Edge inside the Cubes slide 3 diagram, which native text omits, but missed Vertex, mishandled Clock slide 6's 65 5/11 and missed choice labels on 11 frames. The earlier claim that OCR recovered Vertex was corrected after checking the exact OCR output. The 103 token disagreements include furniture/layout differences and are not 103 independently wrong facts.

Report: `<source-dir>`. This supplies usable image-text candidates and inspection context, not complete lesson extraction or diagram/mathematical verification. Source-scoped review annotations follow in the next bounded chunk; learner content remains unchanged.

## #3/#6/#7/#8 — source-scoped review bench — 1 October 2026

Added strict version-1 review annotations tied to current source hashes, original positions/slide IDs and optional exact surface/shape/block digests. Evidence paths/hashes must resolve inside the chosen private root and rendered frames must match the exact visual snapshot. Notes annotations additionally retain the native catalog. Duplicate/conflicting entries are all rejected; missing reasons, stale/ambiguous scope, blanket decoration and approval attempts are rejected. Final dependency checks catch changes during validation. The escaped HTML retains observed facts, separately proposed corrections, rejected reasons and unchanged native issues.

Acceptance validates traceability only: annotations cannot suppress unresolved flags, apply decoration exclusions, mutate extraction/organization, approve knowledge or import a release. Applying reviewed corrections/exclusions and public lesson delivery remain open. See `VISUAL_SOURCE_REVIEW.md` for the schema and CLI.

Eleven real pilot annotations pass. Directly inspected SDT 12/16 confirms that the wrong choice units and approximate 5.8 km already exist in the source. SDT 17's literal “45th” stays ambiguous. Source XML independently confirms SDT 3's notes incorrectly multiply by 5/3 while giving the correct 720 result. Independent fractions yield 10 km (slide 12), 35/6 km (slide 16) and 720/11 minutes for ideal-clock coincidence. Direct cube/clock observations distinguish native label omission from OCR misses. One FACE logo is recorded as an exact shape decoration candidate without excluding other occurrences. The first Syllogisms key A is independently supported by all 32 premise-satisfying models among 256 Venn-cell assignments; other keys remain unverified.

Private report: `<source-dir>`. Twenty-three new regression cases and all 27 renderer/OCR cases pass (50 targeted cases), including a source change during validation. The full backend suite passes 230 tests, with two existing dependency deprecations. The final independent integrity check rehashes all 78 native source snapshots, four inspection copies, all 106 frame/native-text/OCR associations and every annotation evidence reference. Read-only SQLite confirms active release 0.3.5 remains equal to the frozen payload; no PowerPoint process remains. Results: `wave4-integrity-check.json` in the private audit directory.

This completes the bounded visual/source-review wave across #2/#3/#4/#6/#7/#8, with #36 as supporting tooling; whole issue groups remain partial. The all-Learn native bench is unchanged because this wave adds separate inspection evidence rather than changing extraction/organization. Whole-corpus visual/OCR coverage, notes-page renders, diagram semantics, PDF support, semantic answer review and the reviewed lesson contract/curriculum/API/UI remain pending. #35/#37 stay deferred. No priority-only source reviewer was used.

## #38 — direct source-image reuse and management scope — 1 October 2026

Added the user's requirement to reuse teaching images directly, with a scalable asset/reference workflow for future topics. Code inspection confirms that private originals/normalized JPEGs, occurrence provenance, draft media links and verified import already exist. The public contract omits ordered segments and example image links; the current gallery lacks per-use figure context and silently hides failed media. Full OCR/diagram interpretation is not needed to display a reviewed source figure.

Scheduled the implementation with #4/#8 in the next lesson/media wave, before curriculum expansion. The checklist covers complete embedded images or rendered regions retaining separate labels/arrows, asset variants/identity, per-use provenance/captions/roles, reuse without losing context, historical version preservation, independently scoped review, end-to-end delivery and visible failures. Cubes slide 3 is the first figure pilot; SDT remains the baseline-method pilot. A separate asset-manager screen is deferred until the manifest/review workflow demonstrates a need. Substantial UI/curriculum changes retain the uncommitted user-review checkpoint.

This is a documentation-only scope commit; no source images, content pack, learner database or application behavior changed. Verification checks stable numbered headings/cross-references and Git whitespace/diff consistency; no new runtime tests are needed for this backlog update.

## #4/#7/#8/#38 — ordered lesson contract — 1 October 2026

Added strict lesson schema 1 with ordered stage sections, paragraphs, actual formula relations/conditions, worked steps/examples and figures. Asset identity follows full delivery hashes; each figure retains its own source/shape/block/original identity, role, caption and accessible description. One shared asset can serve several distinct lesson/example occurrences. Duplicate identities, missing/unused assets, unknown/private fields, blank descriptions and incomplete review are rejected. The existing Concept API carries an optional typed lesson without dropping these associations; legacy releases have no lesson field populated.

Pack validation accepts the optional contract but refuses a draft lesson even when the surrounding pack claims approval. Existing reviewed-work reconstruction remains required; this does not create a new activation path. Fourteen new contract/API regression cases plus the explicit draft-pack gate and existing content/import checks pass (43 targeted cases). No live source, learner release, curriculum content or UI changed. The next chunk compiles verified private draft bundles and serves isolated previews.

## #6/#7/#8/#38 — verified draft figures and shared media — 1 October 2026

Added `lesson-drafts` compilation into a fresh private bundle. Every citation matches the current source hash/original slide; every figure matches its exact surface/shape/full native-block digest and original-image hash. Supported original JPEG/PNG bytes are copied unchanged, including transparency; normalized JPEG is an explicit alternative. Assets carry full digest/format/dimensions and are shared without collapsing figure occurrences. Cropped/rotated/grouped shapes require a reviewed region render and are explicitly refused by this bounded adapter. All source/media dependencies are rehashed before outputs are saved.

Exact-shape decoration exclusions require fresh validation of source-review annotations. They apply only to this draft selection, retain reasons/hash/shape identities, and cannot remove another occurrence of the same image or clear native blockers. Unselected image occurrences remain visible as needs-review decisions. Raw extraction/catalogs and stored releases remain unchanged. Failure can leave private review artifacts in the attempted directory; use a new directory for retry.

Nineteen new compiler cases plus contract/source-review cases pass (56 targeted cases), covering original-byte preservation/shared uses, scoped exclusions, altered sources/blocks/assets, ambiguous identities, crop/rotation/group boundaries, missing/stale exclusion evidence and output refusal. Fresh native extraction of the two real pilots accounts for 43 slides and exactly matches prior blocks/notes/text/media/source identities. The real bundle compiles two private draft lessons. Cubes slide 3's original 300×176 PNG (`7b19b2828d36c129`) is delivered byte-for-byte, with Face/Edge/Vertex visible; SDT's candidate uses the independently checked 720 km/h reasoning. Candidate curriculum is pending learner review. Output: `<source-dir>`.

## #4/#7/#8/#38 — isolated read-only lesson preview API — 1 October 2026

Added explicit `GROVE_LESSON_PREVIEW_DIR` configuration, disabled by default. Preview routes expose only typed draft lesson data and validated JPEG/PNG bytes attached to that specific lesson; private source decisions stay in the bundle. Paths are constructed from typed content IDs, format/size/dimension/full-hash checks run before delivery, missing/altered data returns an explicit failure, and no route approves/imports or records learner progress. Existing release reads remain unchanged. Draft bundle metadata is uncached; asset bytes are content-addressed.

Ten new API cases plus compiler/contract/content checks pass (48 targeted cases), including disabled mode, exact figure/source preservation, lossless transparent PNG delivery, no effect on regular concepts, refused writes, unknown lesson/media, malformed/approved/duplicate bundles and changed/missing/incorrectly declared images. PNG is supported in isolated bundles; normal release import remains governed by its existing JPEG-only install/reconstruction contract until reviewed lesson activation is implemented. The learner preview is the next uncommitted review chunk.
