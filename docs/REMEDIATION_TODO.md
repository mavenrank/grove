# Grove remediation checklist

This is the implementation backlog for the original 34 issues, tentative observation #35, source-to-lesson test bench #36, deferred explanation formatting #37 and source-image reuse/management #38 identified in the architecture audit and the user's ingestion, curriculum, coverage and question-generation observations. Issue numbers stay stable; they are identifiers, not a priority ranking. Read `ISSUE_INVENTORY.md` for the evidence and `ARCHITECTURE_AUDIT.md` for the architecture comparison.

## Working agreement

- Work locally in `.`; no remote or publishing.
- Preserve the existing application in baseline commit `1bc58c8`.
- Record each change, its verification and remaining scope in `FIX_LOG.md`.
- Commit small tested chunks as they are completed, with issue references. Backend/tooling/documentation work can be committed as it progresses; substantial UI/curriculum changes retain the review checkpoint.
- Stop after a batch touching five or six issue groups for review. A partial fix does not close a whole issue group.
- UI, curriculum presentation and other substantial learner-facing changes stay uncommitted until the user reviews them. Stop with a runnable preview, specific review prompts and an explanation of what changed.
- Use disposable databases and synthetic source files for verification. Never rewrite the learner's existing results or silently reimport the corpus.
- Checkboxes mean implemented and verified; blank items remain open. Historical generated questions remain immutable; generator corrections apply to new tests.

## Batch plan

1. Trustworthiness: #18 generator errors, #26 atomic finalization, #27 answer retries, #28 history isolation, #7 validation approval gate, #30 connection integrity. Leave changes uncommitted at checkpoint 1.
2. Ingestion: #1–8, with representative text-only, image-only and hybrid source fixtures; review extraction evidence before importing any replacement release.
3. Curriculum: #9–14 and #24. Present one pilot topic (calendar or speed/time/distance) for review before expanding its UI or regenerating cards.
4. Coverage and generation: #15–21 and #31. Approve a bounded topic model and pilot generators before calling anything complete.
5. Runtime and learner experience: remaining #22–30, #32–34. Review timing, answer saving, recovery and responsive screens together.

Checkpoint 2 (30 September 2026): partial fixes for #1, #4, #6, #7, #8 plus the requested sidebar work in #33. The user acknowledged the changes and explicitly authorized local commits on 30 September. OCR/diagram interpretation, strict import schemas and curriculum work remain open; #35 stays deferred to the end. See `FIX_LOG.md` for tests, sample evidence and review prompts.

Approved code checkpoints are now committed locally: runtime/generators `91467d8`, ingestion `b580d9f`, and sidebar/docs `54430ae`. The empty Speed Distance Time page was traced to stored release 0.3.5 from 20 September. A fresh targeted draft recovered 15 question candidates but exposed notes-format, source-answer, formula and public-contract gaps. See `CONTENT_REFRESH_AUDIT.md`.

## Source-to-lesson reliability: ongoing publication prerequisites

Six issue groups: #2, #4, #6, #7, #8, #10. Use Speed Distance Time as the first failing-topic pilot. The following checks are required before any replacement release:

Supporting #36 belongs to this pipeline wave: first audit all existing Learn topics and source refs, then use the observed failures for bounded pipeline fixes. Add formatting clues to #37 without bringing UI polish ahead of ingestion correctness.

- [x] Trace the live topic to the active stored release, timestamps, original PPT, source hash and slide count.
- [x] Run the topic into a fresh, unapproved work directory and compare the resulting candidates with native source text, notes and embedded media.
- [x] Independently calculate the 15 native questions and record bad/ambiguous source choices without altering originals or learner data.
- [x] #7: parse explicit `Answer`/`Option` variants, Unicode spaces/glyphs and parenthesized labels; preserve raw notes and block conflicting labels/ambiguous choices.
- [ ] #7: independently verify recovered source answers beyond the five explicit Speed Distance Time labels checked in the pilot; do not equate notes confirmation with correct mathematics.
- [ ] #6: add source-hash-scoped, reviewable exclusions for provider logos, covers, ceremony and decoration. Resolve conservative wave-2 flags without blanket deletion.
- [x] #2: select a working whole-slide render/OCR path, record adapter versions and uncertain output, and inspect tiny math/image-led pilot failures. The supported local PowerPoint/Windows OCR alternative handles 106 pilot positions; fraction/label misses remain explicit review items and full-corpus/platform coverage stays open.
- [ ] #4: design a versioned lesson contract carrying ordered content and attached example media; verify source → draft → API → rendered lesson completeness.
- [x] #2/#4/#6/#8: preserve speaker-note picture/text/branch evidence separately from question-slide assets, identify notes-page furniture, and independently compare source/retained picture counts. Interpretation and delivery remain open.
- [ ] #10: write a Speed Distance Time baseline-method pilot with actual relations, units, given/target identification and worked reasoning. Replace formula question fronts with reviewed formula content.
- [ ] #7/#8: enforce import schema/review/media checks, immutable candidate versions and rollback/activation checks before refreshed publication.
- [ ] Re-extract the complete corpus into a separate draft directory after the pilots pass, and account for every source/slide/loss.
- [ ] Compare a runnable pilot against reviewed source evidence and stop uncommitted for the user's curriculum/UI review before release activation.

Slide review may use the user-approved GPT-6-Luna/max/standard-only configuration when the runner can honor it. Priority is explicitly excluded. See `AGENTS.md` and `SOURCE_REVIEW_PROTOCOL.md`; direct inspection is the fallback when necessary. No replacement content release has been imported.

## Completed wave: choices and imports — 1 October 2026

Six issue groups: #4, #5, #6, #7, #8, #31, informed by #36. Keep the remaining publication prerequisites above open.

- [x] #4/#6/#7/#8: parse explicit A–E choices without renumbering them; match separate boxes only on unique unrotated rows. Incomplete, duplicate and unattached values remain review items.
- [x] #4/#8: join adjacent question prompts and choices only with one matching explicit question number; retain both source snapshots, blocks, notes assets, solution citations and original slide decisions.
- [x] #5: separate explicitly named cube/root arithmetic from painted-cube/dice reasoning and verify the affected source drafts. Ambiguous/multi-topic titles and content-derived mapping still require review.
- [x] #7/#8: add a versioned pack/import contract with review provenance, typed records and verified media delivery; reject malformed approved JSON before database writes. Semantic review, public lesson delivery and activation/rollback remain open.
- [x] #31: reject changed content under an existing release/version, including the candidate pack on disk; keep identical retries idempotent. Historical generator/session pinning remains open.
- [x] Run the final all-Learn bench and backend suite, record counts/limitations, and commit each tested chunk locally. No learner release activation or substantial UI/curriculum changes in this wave.

## Completed wave: visual extraction and source review — 1 October 2026

Six issue groups: #2, #3, #4, #6, #7, #8, supported by #36. Preserve native extraction and current learner content while adding independently inspectable visual evidence.

- [x] #2/#3/#4/#8: add an opt-in local whole-slide renderer, preserve original positions/source hashes and record adapter versions/failures. Render the four text/image/hybrid pilots into a separate directory.
- [x] #2/#4/#7: add offline OCR candidates with word boxes, runtime/language provenance and explicit unknown confidence; keep native text and OCR disagreements separately reviewable. Candidates do not override native evidence or clear approval blockers.
- [x] #6/#7/#8: record source-hash/slide/shape-scoped review decisions with reason and evidence. Reject stale/ambiguous decisions; do not let review annotations bypass publication gates. Eleven pilot annotations pass; applying reviewed exclusions/corrections remains open.
- [x] #3/#7: directly compare selected rendered diagrams/math with their native/notes evidence and record source defects separately from extraction defects. Cube labels, Clock fractions, SDT choices/notes/ambiguities and one independently solved Syllogisms pair are recorded; diagram relationship semantics remain open.
- [x] Extend the bench with visual evidence/review findings, verify source/candidate integrity and commit each bounded tested chunk. Companion visual/OCR/source-review reports cover 106 pilot positions; full backend suite passes 230. Whole-corpus OCR/diagram interpretation and public lesson delivery remain open.

Next bounded wave: start #38 source-image reuse with #4/#8 ordered lesson/media delivery, including the Cubes slide 3 figure pilot. Apply reviewed decoration/correction decisions through an explicit draft-only organizer contract; carry ordered teaching/formulas/example media into a versioned lesson contract; build one reviewed Speed Distance Time baseline-method pilot. Direct teaching-image delivery does not depend on complete automatic diagram interpretation, but relevance/legibility and the surrounding lesson still require review. Substantial curriculum/API/UI delivery must stop for learner review before commitment/activation. Resolve remaining semantic blockers rather than globally clearing visual flags. No replacement release is approved by this plan.

## Current wave: ordered lessons and source figures — 1 October 2026

Six groups: #4/#6/#7/#8/#10/#38, supported by #36. Backend/tooling can be committed in small chunks; substantial curriculum/UI remains uncommitted for the user's concrete review.

- [x] #4/#7/#8/#38: define schema-1 ordered lesson sections, text/formula/steps/examples and source-scoped figures, shared typed assets, captions/alt text and legacy API compatibility. Reject invalid associations and draft lessons in approved packs.
- [x] #6/#7/#8/#38: compile a fresh draft-only lesson/media bundle from exact catalog/source/shape evidence, validate media bytes/dimensions/references and record occurrence-scoped decoration candidates without changing raw extraction or publication blockers. Original JPEG/PNG and normalized JPEG are supported; cropped/rotated/grouped region rendering remains open.
- [x] #4/#8/#38: add a disabled-by-default read-only preview API that preserves lesson/figure associations and serves validated static source images; do not import or activate a learner release. Missing/changed bundles/assets return explicit failures; live PNG release installation remains separate publication work.
- [ ] #10/#38: prepare source-compared Cubes and SDT baseline-method candidates with independent worked reasoning; keep curriculum drafts pending learner review.
- [ ] #4/#38: provide the runnable ordered-lesson/inline-figure preview, readable image enlargement and explicit failed-image states. Leave substantial learner-facing changes uncommitted.
- [ ] Run source → fresh extraction → draft bundle → API → browser checks, full backend tests/frontend build, update evidence and stop at the review checkpoint.

## 1. Preserve native-text structure

Status: native structure/evidence implemented in wave 2; logical reading order and source review remain open. Main files: `backend/ingestion/extract.py`, `extractors.py`, `organize/concepts.py`. Depends on #8 provenance.

- [x] Build synthetic fixtures with tables, equation ambiguity, superscript formatting, numbered steps, text boxes, grouped shapes and speaker notes.
- [x] Extract typed blocks, IDs, coordinates, source text and an explicit top/left reading-order heuristic. Preserve original shape order; logical multi-column order is still unverified.
- [x] Preserve table cells, merges and row/column relationships in raw blocks. Semantic lesson/title/decoration review remains open.
- [x] Retain raw blocks alongside normalized text so organization decisions can be audited.
- [x] Report unsupported objects, native Office Math and extraction losses; retain empty slide records.
- [ ] Verify a text-led topic against its slides: formulas, worked steps, examples and units must survive.

Acceptance: fixture assertions and a manually compared source sample demonstrate structure preservation; extraction failures remain visible.

## 2. Extract knowledge from image-led slides

Status: local whole-slide inspection, separate offline OCR candidates and review annotations implemented; image knowledge integration and semantic review remain open. Depends on #1, #7, #8.

- [ ] Identify slides with useful images but insufficient native text; record image-only versus mixed content.
- [x] Render the complete slide using an opt-in local PowerPoint adapter; keep original extraction crops/positions and source/slide/frame hashes. Four pilots (106 positions) pass; notes-page rendering, other platforms/active packages and full-corpus coverage remain open.
- [x] Add an optional offline Windows OCR adapter, with installed-language/runtime requirements and OS/adapter versions; no API charge/network service. Cross-platform adapters and math/diagram semantic enrichment remain open.
- [ ] Extract image text with confidence and bounding boxes, then recover formulas and worked steps with slide context.
- [x] Store uncertain output as separate OCR/review drafts with unknown confidence, native disagreements and word boxes; never silently promote OCR guesses to facts. Reviewed lesson enrichment remains open.
- [ ] Add fixtures for tiny text, mathematical notation, scans, rotated text and screenshots.
- [ ] Measure missed teaching content on actual image-led topics; review the extracted lesson before release.

Acceptance: image-only teaching slides yield traceable lesson content or an explicit blocked review item, rather than a decorative image with an empty summary.

## 3. Interpret diagrams and visual relationships

Status: source-level observations are traceable in the visual/review bench; structured diagram interpretation remains open. Depends on #2 and #16.

- [ ] Define structured representations for clock hands, train movement, seating/ordering diagrams and labelled geometry.
- [ ] Preserve arrows, orientation, labels, axes, relative positions and units.
- [ ] Separate directly observed diagram facts from inferred facts and confidence.
- [ ] Attach every relationship to the source slide or crop that supports it.
- [ ] Require expert/manual verification of a pilot diagram type before using it in curriculum or answer keys.
- [ ] Test inward/outward seating, clockwise/counterclockwise orientation and ambiguous visual layouts.

Acceptance: the extracted relationship graph reproduces the verified example's reasoning; unresolved ambiguity blocks publication.

## 4. Combine text and images on hybrid slides

Status: same-slide evidence and bounded adjacent Question-number joins implemented; semantic interpretation/general continuations remain open. Depends on #1–3.

- [x] Model each slide as ordered, positioned text/table/image blocks with crop metadata and unresolved drawing references.
- [x] Keep those blocks, image IDs, notes answers and revision provenance together in question/worked-example drafts. This is a same-slide association, not proof of each diagram's meaning.
- [ ] Link a question to its diagram, table, given values and notes answer.
- [ ] Deduplicate native/OCR text while retaining source attribution and disagreements.
- [ ] Group adjacent slides when a worked problem continues across them; retain original boundaries.
- [x] Pilot Syllogisms prompts on one slide with options/notes answers on the next. Match explicit question identifiers and block ambiguous continuations; do not infer absent options or conflate two questions. Original boundaries, role-specific citations and notes assets survive; more general continuations remain open.
- [ ] Flag orphan diagrams and unattached numeric values for review.
- [ ] Compare hybrid lesson output with whole-slide renders, including multi-column layouts.

Acceptance: a hybrid problem retains enough connected information to solve it; its answer is never attached to the wrong figure.

## 5. Improve topic classification

Status: numeric root title correction implemented; general content-derived classification remains open. Main file: `backend/ingestion/config.py`.

- [ ] Report filename classification separately from content-derived suggestions.
- [ ] Add explicit mappings for clocks, calendars, fractions and currently missed skills.
- [x] Correct the explicit cube/root arithmetic title mapping before the generic painted-cube/dice rule. Content-derived classification of ambiguous/multi-topic decks remains open.
- [ ] Allow multiple topic tags and a reviewed primary topic for multi-topic decks.
- [ ] Record confidence, unmatched files and conflicting evidence.
- [ ] Persist review overrides using stable source IDs (#8), independent of filenames.
- [ ] Recompute coverage only from reviewed mappings; test ambiguous names and renamed files.

Acceptance: useful decks do not disappear into a deferred bucket solely because their filename is unfamiliar.

## 6. Make filtering and truncation observable

Status: slide/media decisions and major truncations observable in wave 2; exact-shape decoration candidates are now reviewable, but applying them and complete formula/card rejection accounting remain open. Main files: `organize/gates.py`, `concepts.py`, `pipeline.py`, `source_review.py`.

- [ ] Record a reason for every omitted slide, image, formula, example and code block.
- [x] Replace unconditional first-slide-as-cover logic with short title-placeholder evidence; content/image-led first slides survive. Explicit reviewed overrides remain open.
- [x] Retain repeated images and list frequency as a review clue; never automatically treat repetition as decoration.
- [x] Retain small/thin compressed images; report decode and safety-limit failures with shape provenance.
- [x] Record slide outcomes, skipped-source reasons, visible extraction limits and formula/code/example truncations in `review-report.json`.
- [ ] Make size/dimension caps and per-topic content limits configurable and visible in reports.
- [x] Preserve full lesson blocks and formula/code/example candidate arrays before display limits; flashcard mining still needs complete candidate/rejection accounting.
- [ ] Add an extracted/retained/rejected count dashboard and fixtures for reused diagrams and content-heavy title slides.

Acceptance: a reviewer can account for every source slide and every truncation before approval.

## 7. Enforce content quality and approval gates

Status: validation/approval guards and schema-1 reviewed-work import boundary implemented; semantic verification and human review workflow remain open. Main files: `pipeline.py`, `cli.py`, `pack_contract.py`, `importing.py`. See `CONTENT_IMPORT.md`.

- [x] Prevent approval if validation fails; return a clear CLI error without creating a publishable pack.
- [x] Revalidate the supplied catalog at approval time rather than trusting a saved success flag.
- [x] Reorganize the current catalog at approval, rather than trusting edited/stale content drafts.
- [x] Block unresolved extraction, malformed option/notes-answer mappings, unparsed questions, placeholder summaries, missing/corrupt media and legacy catalogs without evidence. Draft extraction can still succeed while `ready_for_approval` is false.
- [x] Label matching notes answers as `notes_confirmed`, not independently solved. Math verification remains open; the old `questions_verified` statistic is kept as a compatibility alias.
- [x] Define versioned ingestion schemas for packs, concepts, cards and questions; validate them again on import against the reviewed catalog/current organizer. Public lesson/API contract remains open under #4/#10.
- [ ] Track review decisions and unresolved extraction/answer/provenance problems per record.
- [ ] Prevent empty, draft-only or incomplete lessons from being labelled ready without an explicit waiver.
- [ ] Add topic quality summaries: source coverage, unresolved media, verified examples and card applicability.
- [x] Test that malformed approved JSON cannot bypass the import gate, including truthy approval, missing provenance, inconsistent citations, placeholders, choices, identities and media.

Acceptance: approval expresses an auditable review decision and cannot override hard validation failures. Batch 1 only addresses the pack validation bypass.

## 8. Repair source identity, provenance and media delivery

Status: path/revision evidence and verified import media/source checks implemented; relocated-source handling and activation/recovery remain open. Main files: `pipeline.py`, extraction context, source-open routes and import CLI.

- [x] Replace stem-only deck IDs with a normalized relative-path hash; attach content hashes to slide/block revision IDs. Editing a source keeps its path identity; moving/renaming creates a new identity.
- [x] Preserve deck/path/hash/slide/shape/crop evidence on extracted and organized drafts, including mined-card source citations. Authored cards retain authored provenance.
- [ ] Preserve deck/slide/shape/crop provenance on every derived lesson, card and question.
- [x] Detect ID collisions, recompute duplicate annotations deterministically and preserve media associations for same-named files in separate folders.
- [x] Reject a normalized source resolving outside the corpus root; validate pack-stage media existence, content hash and agreement with slide evidence.
- [x] Validate source paths against the catalog allowlist on import, require normalized relative paths, and recheck resolved source containment/hashes (including paths resolving through symlinks).
- [x] Install and verify referenced delivery JPEGs as part of content import; preflight missing/corrupt/colliding files, retain existing assets and leave private originals in the work directory. Recovery from partial filesystem failure/activation remains open.
- [ ] Define behaviour after source folders move and distinguish source citations from local open actions.
- [ ] Test same filenames in different directories, renamed files, missing images and relocated sources.

Acceptance: every published record can be traced to the correct source and its displayed media exists.

## 9. Model granular problem types

Status: open. Depends on #5, #15, #16.

- [ ] Split broad skills into reviewed problem types with prerequisites and canonical IDs.
- [ ] Inventory source examples against those problem types, including trains crossing a platform versus one another.
- [ ] Attach concepts, cards and generator families to explicit problem types.
- [ ] Model prerequisite edges and exclude unsupported cycles.
- [ ] Establish a pilot topic taxonomy and review it with the learner before expansion.
- [ ] Migrate existing broad skill references without losing learning history.

Acceptance: a learner can identify exactly which problem type a lesson or question teaches.

## 10. Teach a baseline solving method

Status: open; curriculum/UI review required. Depends on #9.

- [ ] Define baseline steps: identify givens, identify target, choose relation, substitute units, solve and verify.
- [ ] Write one fully worked baseline example for each pilot problem type.
- [ ] Explain intermediate reasoning and assumptions rather than displaying only a formula or answer.
- [ ] Include common mistakes and a reasonableness check.
- [ ] Link baseline practice to the corresponding lesson and record method-level evidence.
- [ ] Review a runnable lesson prototype before committing learner-facing changes.

Acceptance: the learner can solve an unfamiliar instance using the baseline without memorizing the example.

## 11. Teach pattern recognition

Status: open; curriculum/UI review required. Depends on #10.

- [ ] Define discriminating cues for each problem type and explain why they indicate a method.
- [ ] Add contrasting examples that look similar but require different relations or assumptions.
- [ ] Provide classification practice before arithmetic practice.
- [ ] Separate cue recognition from speed and answer correctness in evidence.
- [ ] Link pattern lessons to the baseline they simplify.
- [ ] Review the pilot's pattern choices and wording with the learner.

Acceptance: the learner selects an appropriate method from problem structure, including counterexamples.

## 12. Teach shortcuts with applicability limits

Status: open; curriculum/UI review required. Depends on #10, #11, #16.

- [ ] Catalogue candidate shortcuts by problem type, prerequisites and assumptions.
- [ ] Select a reviewed primary fast method per supported case; document alternatives without overloading recall.
- [ ] Include when to use it, when it fails and the baseline fallback.
- [ ] Explain or derive the shortcut and include an unfamiliar worked example.
- [ ] Test boundary cases, such as leap years and calendar century transitions.
- [ ] Track speed improvements only after correctness and valid method selection.
- [ ] Review the calendar pilot before expanding the mastery curriculum.

Acceptance: shortcuts accelerate the right problem types and never imply universal applicability.

## 13. Restore flashcards as quick method review

Status: open; UI review required. Depends on #9–12.

- [ ] Define card types for recognition, baseline method, formula, pattern and shortcut applicability.
- [ ] Make cards concise but preserve units, assumptions, conditions and source references.
- [ ] Replace generic mined fragments with reviewed topic/problem-type cards.
- [ ] Offer a quick topic overview and direct links to a worked explanation.
- [ ] Deduplicate equivalent cards and retire broken cards while preserving review history.
- [ ] Review a sample deck and the card navigation before committing.

Acceptance: a short card session refreshes what the topic is and how to approach its supported problem types.

## 14. Separate recall from solving mastery

Status: open. Depends on #13, #23.

- [ ] Keep self-rated flashcard recall distinct from scored problem-solving evidence.
- [ ] Define recognition, method selection, baseline accuracy and shortcut fluency stages.
- [ ] Specify promotion criteria that require multiple unfamiliar variants and appropriate spacing.
- [ ] Detect forgetting using later retrieval rather than assuming one correct attempt means mastery.
- [ ] Support remedial lessons when method selection or accuracy regresses.
- [ ] Review labels and thresholds before displaying mastery claims.

Acceptance: a learner cannot gain solving mastery merely by clicking Remember on a card.

## 15. Measure bounded topic coverage

Status: open; review the scope definition. Depends on #9, #16.

- [ ] Define a finite, reviewed domain for each topic; avoid claims of covering every imaginable problem.
- [ ] Build a matrix of problem type, target unknown, givens, assumptions, method and difficulty.
- [ ] Map source examples, lessons, cards and generator families into cells.
- [ ] Distinguish missing, extracted, reviewed, taught and assessed coverage.
- [ ] Show counts with their denominator and unresolved mappings.
- [ ] Use coverage gaps to choose new curriculum and generators; do not infer coverage from raw question counts.
- [ ] Review the speed/time/distance and calendar matrices before rendering percentages.

Acceptance: coverage percentages are reproducible against an explicitly bounded curriculum.

## 16. Model givens, unknowns and solvability

Status: open. Depends on #9 and enables #15, #17.

- [ ] Represent variables, units, domains, equations, assumptions and target unknowns.
- [ ] Enumerate supported given/target combinations, starting with distance = speed × time.
- [ ] Use independent equations and constraints to detect underdetermined, inconsistent or multiple-solution cases.
- [ ] Extend the model to relative speed, train lengths/platforms and clock angles.
- [ ] Represent extra latent variables and branch choices rather than equating variable count with case count.
- [ ] Attach each valid case to one or more verified solution methods.
- [ ] Validate the pilot model with independent worked cases and review its boundaries.

Acceptance: the system can explain why a supported instance has a valid solution and which case it exercises.

## 17. Generate constrained dynamic variants

Status: open. Depends on #16, #18, #31.

- [ ] Define typed parameter domains with units and semantic roles, rather than replacing arbitrary numbers in prose.
- [ ] Encode date validity, leap years, positive quantities, nonzero denominators, feasible train lengths and angle bounds.
- [ ] Generate compatible givens from a solved latent state and recompute the answer independently.
- [ ] Vary the target unknown and problem wording only within validated cases.
- [ ] Persist seed, generator version and canonical parameter signature for reproducibility.
- [ ] Bound rejection sampling and report exhausted or unsupported cases.
- [ ] Test valid/invalid boundary values and compare many generated instances to an independent solver.

Acceptance: variants stay solvable and valid; February 30 and impossible numeric configurations cannot be emitted.

## 18. Correct and validate generated questions

Status: partially implemented in batch 1; awaiting review. Main files: `content_engine/families/*`.

- [x] Correct silent numeric rounding in percentage and simple-interest families.
- [x] Replace the ambiguous ordering question with a uniquely determined target.
- [x] Correct circular seating orientation and the stated starting person.
- [x] Reject structurally invalid generator output: missing prompt/explanation, wrong option count, duplicate options or invalid answer index.
- [x] Verify corrected families against Decimal arithmetic, permutation enumeration and spatial orientation checks over many seeds.
- [ ] Audit every remaining family with independent mathematical/logic oracles and boundary cases.
- [ ] Define a content incident policy for pre-existing faulty attempts; preserve historical keys and label any invalid evidence through a reviewed migration.

Acceptance: every enabled family produces one demonstrably correct option; batch 1 fixes known errors and structural safeguards without claiming the entire family library is verified.

## 19. Reduce repetition and answer memorization

Status: open. Depends on #17, #21, #31.

- [ ] Store canonical question signatures separately from displayed text and seeds.
- [ ] Track recent exposure per learner, problem type and parameter pattern.
- [ ] Avoid repeats within a test and apply a bounded recent-exposure window across tests.
- [ ] Balance family, target unknown, parameter ranges and wording diversity.
- [ ] Report pool exhaustion and explicitly choose whether a repeat is allowed.
- [ ] Verify that equivalent numeric/wording variants do not falsely inflate diversity.

Acceptance: variety is measured and deliberate; a new seed alone does not count as a new problem type.

## 20. Integrate reviewed source questions into assessments

Status: open. Depends on #7, #8, #18.

- [ ] Distinguish answer labels copied from notes from independently verified answer keys.
- [ ] Normalize imported question options, diagrams, units, explanations and provenance.
- [ ] Quarantine incomplete, ambiguous or unverifiable source questions.
- [ ] Map reviewed source questions to problem types and blueprint eligibility.
- [ ] Decide which source problems are fixed exemplars and which support validated parameterization.
- [ ] Add a reviewed pool adapter alongside generated families and pin its version per session.
- [ ] Compare source inclusion with the current unused pool; verify release and scoring isolation.

Acceptance: imported assessment questions are complete, reviewed and actually selected by an explicit blueprint.

## 21. Build focused assessment blueprints

Status: open; setup UI review required. Depends on #9, #15, #19, #20.

- [ ] Support topic/problem-type focus, prerequisites and assessment intent.
- [ ] Define quotas for difficulty, case coverage, baseline/pattern/shortcut objectives and total duration.
- [ ] Validate blueprint feasibility before starting a session.
- [ ] Expose unsupported coverage instead of silently filling with unrelated topics.
- [ ] Record the exact resolved plan and blueprint version per session.
- [ ] Test short tests, sparse topic pools and balanced long tests.
- [ ] Review the focused test setup and resulting question mix before committing UI changes.

Acceptance: selecting a topic produces an explainable assessment of that topic's supported cases.

## 22. Make timing accurate

Status: open; runner review required. Main file: `frontend/src/runner/TestRunner.tsx`.

- [ ] Separate accumulated totals from unsent dwell segments; consume each segment only once.
- [ ] Preserve hidden/unfocused state through flushes and distinguish visibility from window focus.
- [ ] Send stable segment identifiers and deduplicate them on the server (#27).
- [ ] Capture mark time accurately and distinguish revisits from ticket-refresh requests.
- [ ] Flush pending segments before finalization with bounded recovery behaviour.
- [ ] Use fake-clock tests for navigation, repeated flushes, hidden periods and finish races.
- [ ] Review timing summaries against a timed manual session before committing runner changes.

Acceptance: dwell totals match elapsed active time within a documented tolerance and never double count retries.

## 23. Improve learner evidence

Status: open. Depends on #14, #18, #19, #22, #31.

- [ ] Separate accuracy, speed, recall, coverage and method-selection evidence.
- [ ] Count only valid finalized attempts and distinguish unseen from weak skills.
- [ ] Include sample size and uncertainty in recommendations.
- [ ] Handle repeated questions, invalidated content and changing topic mappings explicitly.
- [ ] Define personal baseline windows and minimum evidence before pace comparisons.
- [ ] Link recommendations to specific remedial problem types and lessons.
- [ ] Verify aggregates against independent query fixtures and review learner-facing claims.

Acceptance: recommendations are supported by sufficient valid evidence and explain what remains unknown.

## 24. Repair concept, family and card links

Status: open. Depends on #8, #9, #31.

- [ ] Replace guessed `concept.{skill_id}` links with explicit catalog relations.
- [ ] Detect assessed skills without lessons and lessons without assessable families.
- [ ] Validate every concept/card/family reference before publishing a release.
- [ ] Resolve links against the session's pinned catalog rather than the latest release.
- [ ] Provide an honest unavailable state for missing remediation material.
- [ ] Test all published links and review navigation for a previously missing skill.

Acceptance: every remediation link either opens the correct versioned lesson or explicitly states that it is unavailable.

## 25. Make answer saving reliable

Status: open; runner UI review required. Depends on #26, #27.

- [ ] Track pending, confirmed and failed answer saves explicitly.
- [ ] Display recovery status and avoid silent optimistic success.
- [ ] Handle the API's actual `stale_ticket` error code and refresh safely.
- [ ] Prevent old requests from overwriting a newer choice; define answer revision ordering.
- [ ] Await pending saves before finishing and allow recovery from finish failures.
- [ ] Disable conflicting interactions while finalization is in progress.
- [ ] Test slow/offline networks, fast answer changes and deadline expiry; review these states before committing.

Acceptance: the learner can tell which answer the server saved and recover without losing or misreporting a choice.

## 26. Make expiry and finalization atomic

Status: implemented and verified in batch 1; awaiting review. Main files: engine runtime/scoring and database connections.

- [x] Recheck ownership, active state and deadline inside the write transaction.
- [x] Reject new question fetches, answers, marks, dwell and events after terminal state or expiry.
- [x] Persist lazy expiry before raising its error, including on repeated requests.
- [x] Save the selected answer and correctness together.
- [x] Compute the score and transition state in the same transaction that excludes concurrent writes.
- [x] Verify both answer-before-finish and finish-before-answer interleavings using independent database wrappers.
- [x] Check that failed operations roll back, duplicate finish stays rejected and stored score matches stored answers.

Acceptance: every stored score is a coherent snapshot of exactly the answers accepted before its terminal transition.

## 27. Make retries and telemetry idempotent

Status: partially implemented in batch 1; awaiting review. Depends on #26, #30.

- [x] Persist answer request receipts keyed by session and idempotency key in the answer transaction.
- [x] Return the original response for an identical retry; reject key reuse with changed position, ticket or option.
- [x] Support safe retrieval of an accepted receipt after ticket rotation or finalization without mutating answers.
- [x] Validate key size/nonemptiness and preserve ownership checks before receipt access.
- [x] Test retries after simulated response loss, later answer changes and database reopen.
- [ ] Wire stable per-intent keys and a recoverable answer save queue into the browser (#25).
- [ ] Add ordered answer revisions so different requests arriving late cannot overwrite newer intent.
- [ ] Add stable IDs and deduplication for events and dwell; define retention for receipts.

Acceptance: retries are safe; batch 1 addresses answer receipts, while telemetry deduplication and different-request ordering remain open.

## 28. Enforce assessment isolation on every surface

Status: partially implemented in batch 1; awaiting review. Main files: history routes, learning routes and frontend runner.

- [x] Reject detailed history access for active/cancelled sessions and terminal sessions without a stored score.
- [x] Verify history cannot bulk expose active questions, metadata, answers or explanations.
- [ ] Audit concepts, flashcards, insights and source-open routes against the intended active-test policy.
- [ ] Decide the local product boundary: accidental in-app access prevention versus stronger server-enforced learning locks.
- [ ] Remove cached learning views and direct-route escape paths during an active test.
- [ ] Test navigation, multiple tabs and browser back/forward under the agreed policy.
- [ ] Review runner restrictions before committing UI changes.

Acceptance: isolation applies to all agreed surfaces. Batch 1 closes the active-history bypass only.

## 29. Recover cache and route failures

Status: open. Main files: `frontend/src/api/cache.ts`, hooks and routes.

- [ ] Remove or replace failed in-flight promises so a transient failure does not poison the cache.
- [ ] Include resource keys and session IDs in hook dependencies.
- [ ] Invalidate history/evidence after tests, concept views and card reviews.
- [ ] Handle release-version changes and explicit refreshes coherently.
- [ ] Show retryable route errors and missing-content states.
- [ ] Test rejection-then-success and navigation between two resources without remounting.
- [ ] Review recovery UI before committing visible changes.

Acceptance: retry succeeds after transient failure and routes never show data for the previous resource.

## 30. Protect database integrity and recovery

Status: partially implemented in batch 1; awaiting review. Main files: `app/db/*`.

- [x] Enable SQLite foreign-key enforcement on every connection, including ordinary reads and writes.
- [x] Lock before reading mutable state in a write transaction; support multiple wrappers/processes with `BEGIN IMMEDIATE`.
- [x] Test orphan rejection, rollback and initialization against an existing database.
- [ ] Add versioned migrations with backups and explicit compatibility checks.
- [ ] Audit current stored foreign-key violations read-only before any repair; agree on remediation for historical records.
- [ ] Persist/recover the active session in the client and prevent duplicate creation on StrictMode/remount.
- [ ] Implement and verify backup/restore with SQLite-aware handling of WAL state.

Acceptance: writes respect relationships and recovery is verified. Batch 1 addresses connection enforcement and transactional locking, not migration/backup/session recovery.

## 31. Pin immutable assessment dependencies

Status: immutable candidate/database releases implemented; session/generator dependency pinning remains open. Depends on #8, #9, #17, #30.

- [ ] Pin generator implementation, taxonomy, blueprint, content and question-pool versions per session.
- [ ] Persist resolved metadata/method relations needed for future review.
- [ ] Prevent runtime merging of current generator allowlists from changing historical release meaning.
- [x] Reject same-version replacement packs with different content hashes, both candidate files and canonical database payloads/manifests; identical retries preserve the original.
- [ ] Reproduce a historical session after installing a new generator/catalog version.
- [ ] Establish a compatibility policy for archived generators and retired content.

Acceptance: history and scoring keep the meaning they had when the test was created.

## 32. Make dashboard metrics useful

Status: open; UI review required. Depends on #15, #23, #24.

- [ ] Define each metric, denominator, time window and empty-data behaviour.
- [ ] Separate attempted, mastered, covered and still-unseen problem types.
- [ ] Surface the next actionable lesson/practice recommendation with evidence.
- [ ] Reconcile overview totals with history and underlying query fixtures.
- [ ] Avoid extrapolating broad mastery from small sample counts.
- [ ] Review real and empty-state dashboards before committing.

Acceptance: visible numbers answer a learner question and agree with recorded evidence.

## 33. Review responsive UI and learner language

Status: open; mandatory uncommitted review checkpoint. Main files: frontend pages, layout and runner.

- [x] Add a Grove-styled shadcn/Radix sidebar composition with grouped navigation and a mobile drawer.
- [x] Use breakpoint defaults: drawer below 768 px; 64 px collapsed rail at 768–1023 px (208 px expanded); 240 px at 1024–1439 px; 264 px from 1440 px.
- [x] Add bounded pointer/keyboard resizing, reset and saved width/collapse preferences per breakpoint. Verify Escape focus return, navigation closing and Ctrl/Cmd+B support.
- [x] Verify sidebar/Learn layout at 360, 900, 1200 and 1600 px with no horizontal overflow. This does not close the audit of every page and runner state.
- [x] Leave the runnable sidebar preview uncommitted for the requested user review at checkpoint 2.

- [ ] Audit phone, tablet and desktop layouts, overflow, keyboard access and focus behaviour.
- [ ] Replace unexplained implementation terms with learner-facing concepts where needed.
- [ ] Design method stages and coverage views without overwhelming quick review.
- [ ] Verify loading, empty, saving, failed, expired and unavailable states.
- [ ] Check diagram/formula readability and long source-derived content.
- [ ] Provide a runnable preview with a short list of screens and interactions to review.
- [ ] Stop before committing until the user reviews the concrete UI changes.

Acceptance: the agreed screens work across target viewports and the user has reviewed their interaction and wording.

## 34. Align documentation and local version control

Status: local Git and remediation documents complete; setup/recovery documentation remains open.

- [x] Initialize local Git on `main` and preserve a source baseline without a remote.
- [x] Exclude learner databases, generated ingestion output, media, credentials, dependencies and tool metadata.
- [x] Keep the architecture audit, issue inventory, detailed checklist and fix log inside Grove.
- [ ] Correct stale README paths, ports, module layout and test counts against the implementation.
- [ ] Document local backup/restore, content approval/import and review checkpoints.
- [ ] Add issue-linked changelog entries after reviewed batches and keep historical scope decisions explicit.
- [ ] Commit approved implementation batches only after their verification and required review.

Acceptance: a fresh source checkout has accurate setup instructions, while private runtime state remains local and recoverable through documented steps.

## 35. Revisit possible cold-start delay in Learn

Status: tentative and deferred to the end of the main reviewed remediation work, at the user's request. Warm navigation no longer shows the reported delay. Do not prioritize or implement a performance redesign based on the initial observation alone.

- [ ] After the main fixes are reviewed and committed, compare cold startup with repeat navigation under the same conditions.
- [ ] If a meaningful delay reproduces, distinguish dev-server compilation, API work, JSON transfer, rendering, images and failed-cache recovery before choosing a fix.
- [ ] If measurements justify it, evaluate a summary-only concept index and loading lesson/media details when needed; coordinate with #29 cache recovery.
- [ ] Verify the chosen change against before/after measurements and preserve lesson counts, links and content availability.
- [ ] Leave any resulting UI changes uncommitted for review before accepting them.
- [ ] If the delay does not recur or is only an acceptable development cold start, close this observation without application changes.

Acceptance: either a reproducible bottleneck is measured and improved, or the tentative observation is documented as unconfirmed and closed without speculative changes.

## 36. Build the source-to-lesson test bench

Status: repeatable all-Learn bench implemented and rerun per pipeline wave; semantic completeness remains in #1–8 and #10.

- [x] Read the active release without modifying its database; inventory every existing Learn topic and source reference.
- [x] Re-extract referenced sources in a new draft directory; compare source hashes/counts, classification, retained blocks/media/notes and organization outcomes.
- [x] Produce a per-topic report and slide-level evidence for missing summaries/examples, malformed choices, missing/ambiguous notes answers, exclusions, truncation and API field loss.
- [x] Separate definite failures from heuristic review clues and unverified source/visual meaning; never describe notes-confirmed keys as independently solved.
- [x] Add regression fixtures for observed failures and record before/after audit counts with the same source hashes. Notes variants/conflicts now covered; visual/math completeness remains open under #2/#3/#7.
- [x] Document the CLI, output locations and rerun policy; never import or rewrite learner history through the bench.

Acceptance: every existing Learn topic is accounted for; a reviewer can trace each anomaly to a source snapshot and stage, and rerun the audit after a pipeline change.

## 37. Improve explanation formatting later

Status: deferred to the tail of the backlog by the user.

- [x] Inventory unmatched delimiters and long text with source citations in #36 (30 review clues). Deeper paragraph/list and dangling-fragment review remains open.
- [ ] Distinguish original punctuation from parser/summary truncation before changing it.
- [ ] Review paragraph, step and formula presentation after the main pipeline and curriculum fixes.
- [ ] Keep substantial learner-facing changes uncommitted until reviewed.

Acceptance: reviewed explanations are readable without dropping conditions, units or mathematical notation. Detection alone does not close this issue.

## 38. Reuse and manage source teaching images

Status: planned for the next lesson/media wave with #4/#8; prioritize before curriculum expansion, independently of complete OCR/diagram interpretation under #2/#3. Existing private originals/JPEGs, source occurrence metadata and verified import are foundations, not a completed figure workflow.

- [ ] Define typed figure blocks and explicit attachments to lesson segments, example prompts and solution steps. Keep the figure beside the content it supports, in reviewed reading order, instead of only in a concept-wide gallery.
- [ ] Prefer the original embedded image when it contains the complete teaching diagram. If captions, labels or arrows are separate PPT objects, preserve them with an appropriate rendered source region/figure; retain whole-frame evidence and do not silently crop away meaning.
- [ ] Define a reusable asset manifest with content hash, format/dimensions and delivery variants. Retain the private original; avoid unnecessary re-encoding and verify label/math readability and transparency where needed. Coordinate format support with the current JPEG-only pack/import/API contract.
- [ ] Store each use's source hash, slide/notes surface, shape/region, figure role, caption, accessible description and lesson placement. Share identical asset bytes across topics while retaining all usage/source associations; provider decoration decisions remain occurrence-scoped.
- [ ] Keep image relevance/legibility review distinct from OCR/relationship/answer verification. A reviewed source figure can teach directly without invented OCR text or solved geometry; unresolved derived claims still block their own publication.
- [ ] Version changed images/derivatives and references without overwriting assets used by old releases. Make review records and asset usage discoverable in the existing tooling; evaluate a dedicated management UI after the first real authoring workflow.
- [ ] Carry figure references through organizer draft → pack/media installation → API → Learn. Validate missing/wrong references and display a useful failure state instead of silently hiding a failed image.
- [ ] Add responsive, aspect-preserving display, lazy image loading, useful captions/alt text and an enlarge/zoom interaction for small labels. Stop with the runnable learner-facing preview uncommitted for user review.
- [ ] Extend #36 with the Cubes slide 3 pilot (Face/Edge/Vertex all visible), a hybrid figure with separate labels, reused assets with distinct contexts, missing media and changed-source/historical-reference cases. Check the actual displayed image against original source evidence before release.

Acceptance: an image-led lesson shows the complete readable source figure in the right teaching context, with a traceable managed asset and stable release reference. Adding another topic can reuse the same delivery/review path. OCR may remain incomplete without erasing the figure; inferred facts and answer keys require their own verification. The concrete UI/curriculum preview is reviewed before committing or activating a new lesson release.
