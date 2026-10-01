> Entries #1–34 preserve the historical audit before baseline 925ef53 and batch 1; #35–38 are subsequent user requirements. Current implementation status and fixes are recorded in [REMEDIATION_TODO.md](REMEDIATION_TODO.md) and [FIX_LOG.md](FIX_LOG.md).

# Grove issue inventory

Updated: 1 October 2026.

38 tracked issue groups, including tentative observation #35, the source bench #36, deferred formatting #37 and source-image reuse #38, numbered without a priority ranking. This inventory combines the user's ingestion, learning-method, retention, coverage and generation requirements with the earlier architecture audit. It records analysis and requirements; implementation changes are tracked in the remediation checklist and fix log.

The current app has useful foundations: native-text extraction, source provenance, authored approach/formula cards, deterministic generators, a scheduling mechanism, and server-side scoring. None of those alone establishes reliable curriculum coverage or learner mastery.

One correction to the fixed-pool impression: tests currently use seeded generator families. The 720 imported source question records are a separate pool that is not used by the test engine. The needed work concerns breadth, constraints, validation and integration as well as randomness.

## 1. Native-text extraction loses structure

**Current implementation and gap:** Grove recursively collects text frames, which is its strongest extraction path. It does not preserve slide layout, table cells, reading order, or relationships between definitions, formulas, assumptions and worked steps. The user's approximate 95% impression has not been measured against a reviewed extraction benchmark.

**Work needed:** Create a structured slide record with ordered blocks, tables, equations, notes and source locations. Evaluate accuracy and completeness on representative decks.

## 2. Image-based teaching is not converted into usable knowledge

**Current implementation and gap:** Some picture blobs are extracted and displayed, but there is no OCR or visual interpretation stage. Formulas or explanations inside images therefore do not become searchable concepts, flashcards or usable question templates. Showing an image and understanding its content are separate capabilities.

**Work needed:** Preserve the source image and derive reviewed text/equations with confidence and provenance. Route unreadable material for review rather than publishing an empty lesson.

## 3. Diagrams and drawn objects have no semantic representation

**Current implementation and gap:** The extractor handles picture objects and text frames, but does not understand shapes, arrows, spatial relationships, clock hands, train diagrams or arrangement constraints. A list of labels cannot express those relationships; OCR alone also cannot establish them.

**Work needed:** Support complete slide rendering and structured diagram facts where needed. Keep diagrams linked to lessons, worked examples and assessment items, including learner-safe media delivery.

## 4. Hybrid slides lose the connection between text and images

**Current implementation and gap:** Mixed slides become separate text lists and media IDs. The pipeline does not establish that a caption describes a particular diagram, that an equation belongs to a particular worked step, or that an image contains the missing part of a question.

**Work needed:** Combine native text, notes, image-derived material and layout into one ordered representation. Deduplicate overlapping extraction while retaining text-to-figure associations.

## 5. Topic classification relies too heavily on filenames

**Current implementation and gap:** Classification uses title regexes and usually assigns an entire deck to one skill. Broad or misleading filenames can misclassify material, and decks teaching several problem types are flattened into one bucket of content.

**Work needed:** Classify at slide/block and problem-family level, permit multiple declared learning targets, and record confidence and review decisions. Keep source taxonomy IDs stable.

## 6. Content can disappear silently during extraction and organization

**Current implementation and gap:** Images are filtered by byte size/dimensions, first slides are assumed to be covers, frequently reused images are treated as templates, and content is capped at 12 formulas, 20 examples and eight code blocks per concept. These rules can remove useful material. The existing catalog is a record of retained extraction, not an inventory of everything omitted.

**Work needed:** Produce a loss report for every source/slide/block: kept, filtered, unparsed, truncated, deferred or awaiting review, with a reason. Check omitted material before release.

## 7. Approval does not establish content quality

**Current implementation and gap:** The earlier isolated check produced an approved pack despite failed validation. Import mainly trusts an approved flag; speaker-note answer labels are treated as verified without an independent correctness check. Nine current concept summaries retain instructions to refine the draft.

**Work needed:** Validate strict content schemas, stop on failed checks, and track item-level review/corrections. Do not publish placeholders or treat a source's answer label as mathematical proof.

## 8. Source identity, citations and media installation are fragile

**Current implementation and gap:** Source hashes and slide references are useful, but deck IDs based on filename stems collide. Two existing IDs represent distinct file hashes. Relative source paths are resolved against the wrong directory for source opening, and pack import does not install referenced media as one complete operation.

**Work needed:** Use stable source IDs, preserve page/region provenance and resolve known sources server-side. Package/install validated media alongside the release and report missing assets.

## 9. Topics are not decomposed into sufficiently precise problem types

**Current implementation and gap:** The taxonomy contains buckets, topics and skills, but a concept often aggregates a skill's entire deck collection. There is no curriculum structure for cases such as finding speed, finding duration, crossing a platform, opposite-direction trains or clock-angle variants.

**Work needed:** Define topic → skill → problem family → scenario/assumptions. Link each case to its methods, examples, recall cards and assessment coverage.

## 10. Stage 1: dependable baseline methods are not taught systematically

**Current implementation and gap:** Worked examples and some approach cards exist, but there is no guaranteed step-by-step baseline method per problem type. The learner can encounter a formula or shortcut without a complete method that remains usable when the trick is forgotten.

**Work needed:** Provide a transparent method with assumptions, units, steps, an example and common errors. Test that the learner can independently apply it before calling the case mastered.

## 11. Stage 2: pattern recognition is not a curriculum stage

**Current implementation and gap:** Some authored approach cards describe a mindset, but the model does not explicitly teach cues, underlying structure, misleading similarities or how to choose between methods.

**Work needed:** For each family, teach recognition cues and why they imply a method. Include nearby counterexamples where the same-looking cue requires a different approach.

## 12. Stage 3: shortcuts lack explicit applicability rules

**Current implementation and gap:** A few shortcuts are present as formula/rule/approach cards, but there is no structured shortcut entity linked to the exact cases where it works. A preferred calendar method cannot safely stand in for every calendar problem.

**Work needed:** Record shortcut preconditions, limitations, fallback method and worked examples. Choose a preferred method per subtype; evaluate the learner's accuracy and time before describing it as faster for them.

## 13. Flashcards do not fully serve the intended quick-review purpose

**Current implementation and gap:** The current section is primarily a due-card grading workflow. The content has formula/rule/approach kinds, which is useful, but no method-stage or problem-family links. It cannot reliably provide the requested compact review of what a topic is, how to recognize it, how to solve it and which shortcuts apply.

**Work needed:** Provide a topic/method review surface and small recall cards linked to baseline, recognition, formula, shortcut and mistake knowledge. Keep long explanations in Learn and make card context explicit.

## 14. Recall scheduling is being conflated with broader mastery

**Current implementation and gap:** Spaced-repetition scheduling exists and can help formula recall. Its card 'strong' state is based on review interval and self-grading, not demonstrated success on unfamiliar questions or correct method selection. The app has no progression through the requested method stages.

**Work needed:** Track recall and problem-solving evidence separately. Connect reviews to delayed recall, recognition and application practice, with stage-specific progress and review needs.

## 15. There is no explicit measure of curriculum coverage

**Current implementation and gap:** Counts of skills, concepts and cards do not show whether all agreed scenario types, givens/unknowns, assumptions, representations and methods are covered. Topics have open-ended numerical variations, so an absolute percentage of every possible question would be misleading.

**Work needed:** Define a reviewed coverage matrix against a bounded syllabus. Mark each case missing, extracted, drafted, reviewed, teachable and testable. Expose the denominator and gaps behind any coverage percentage.

## 16. Questions lack a model of givens, unknowns and solvability

**Current implementation and gap:** Generators currently return prompt/options/key/explanation; they do not expose a general internal model of variables, units, equations, givens and the requested quantity. Counting unknowns alone does not establish solvability: independent conditions and uniqueness also matter.

**Work needed:** Represent a family's mathematical model and admissible known/unknown configurations. For d = v × t, support asking for d, v or t where valid; for multi-variable cases verify enough independent constraints for a unique requested result.

## 17. Parameter variation does not systematically cover domain constraints

**Current implementation and gap:** Seeded number variation already exists, with some family-specific checks. There is no consistent contract for valid dates, units, denominator bounds, physical feasibility, discrete values, precision, ambiguous solutions or infeasible parameter combinations.

**Work needed:** Specify constraints per family and generate valid parameters by construction where possible. Validate real dates/leap years, units and scenario feasibility; retain deterministic seeds for reproduction.

## 18. Question correctness and unique-answer validation are insufficient

**Current implementation and gap:** The earlier checks found 12% of 160 accepting 19 instead of 19.2, unrequested simple-interest rounding, and an ordering question with several correct options. Distinct option strings are not proof that precisely one option answers the question.

**Work needed:** Use independent solution checks, exact arithmetic/explicit rounding, and exhaustive or constraint-based checks for logic cases. Test distractors for semantic equivalence and accidental correctness before publication.

## 19. Randomness is too narrow to prevent repetitive practice

**Current implementation and gap:** Current tests use seeded generators, rather than only selecting static questions. Some families nevertheless have small fixed prompt pools or change only numbers; varying an operand is not the same as varying the problem's reasoning structure.

**Work needed:** Vary givens/unknowns, validated scenario structure and presentation within family contracts. Track recent exposure and equivalent instances while preserving reproducibility and deliberate spaced repetition.

## 20. The imported question pool is not connected to assessment

**Current implementation and gap:** The release contains 720 imported question records, including 447 with speaker-note answers, but tests use the 33 built-in eligible generator families. Extracted source questions do not automatically become approved static items or validated parameterized templates.

**Work needed:** Separate source records, reviewed static items and reviewed templates. Define an approval/conversion path into the assessment bank, with independent correctness and diagram support.

## 21. Test blueprints cannot focus practice on the missing or weak cases

**Current implementation and gap:** Setup primarily selects count and duration. The planner balances buckets and avoids repeated families where possible, but does not enforce its recorded distinct-skill set or expose focused skill/family/stage selection. Several difficulty labels do not correspond to a distinct method challenge.

**Work needed:** Provide server-owned fixed blueprints for a skill, family or method stage, with explicit coverage/difficulty quotas. Use these for focused retesting; adaptive testing can remain deferred.

## 22. Per-question timing is currently inaccurate

**Current implementation and gap:** The earlier controlled-clock reproduction showed that leaving a question posts its banked time and the next drain posts it again. Draining a hidden interval also clears the pause state, allowing later hidden time to count as active. Time-based diagnosis therefore rests on faulty observations.

**Work needed:** Consume each segment once, preserve focus/visibility state and deduplicate retries. Test navigation, revisits, overlapping pause events, submission and reconnect behavior.

## 23. The learner model omits or misuses important signals

**Current implementation and gap:** Skill timing is compared against a median across unrelated skills; detailed review omits difficulty from comparisons. Recent evidence is unordered, answer-change fields are not updated, normal cached revisits are not counted correctly, and marks/difficulty/trend do not fully affect status. Strong can be returned without timing evidence.

**Work needed:** Use chronologically ordered comparable attempts and explicit sample thresholds. Combine accuracy, prior pace, consistency, changes, marks, difficulty and trend, and explain missing evidence.

## 24. Weak-skill recommendations do not always lead to usable material

**Current implementation and gap:** Tests cover 28 of 44 declared skills. Nine tested skills lack a current concept, while eight concept skills lack an eligible test family. Generated Learn links can therefore lead to absent lessons, breaking the central improvement loop.

**Work needed:** Validate the concept/card/family links when publishing. Show learn/test availability explicitly and resolve real content IDs instead of constructing assumed links.

## 25. The answer UI can disagree with saved answers

**Current implementation and gap:** Answer selection updates the UI optimistically and suppresses most save failures. The stale-ticket recovery compares the wrong error code, and finalization does not wait for pending answer saves. A failed finish leaves the runner unable to retry normally.

**Work needed:** Track pending/saved/failed states, serialize revisions, retry safely and wait for acknowledged answers before finish. Preserve retryable submission state and lock answer changes while finishing.

## 26. Expiry and scoring transactions do not freeze a consistent attempt

**Current implementation and gap:** The earlier reproduction received 410 on the first late answer and 200 on retry, changing an expired attempt while the stored score remained unchanged. A controlled interleaving also wrote an answer after finalization. Separate checks/read/write transactions allow inconsistent terminal records.

**Work needed:** Reject all terminal mutations and atomically check/save answers. Compute/freeze the score in the protected finalization transaction, with regressions for expiry and concurrent operations.

## 27. Replay protection and telemetry reliability are incomplete

**Current implementation and gap:** The same ticket and idempotency key can save different options twice. Event batches and dwell segments have no stable deduplication IDs or dependable ordering; failed telemetry is dropped. Some timing fields are present without a complete derivation path.

**Work needed:** Define answer revision versus request replay, and use stable operation/event/segment IDs. Validate bounds and session phase, preserve ordering and report observation loss.

## 28. Test isolation is incomplete across routes and caches

**Current implementation and gap:** The runner removes navigation, but cached Learn content remains and learning endpoints remain available. Active history detail returns every test question and private metadata, although it withholds the actual answer values.

**Work needed:** Implement an explicit test-mode transition that clears/guards learning state and prevents in-flight reads from repopulating it. Release detailed question history only after finalization and retain minimal live question payloads.

## 29. Cache and route state do not recover reliably

**Current implementation and gap:** The earlier cache check showed an initial failed GET remaining as a rejected cached promise after the backend recovered. Data hooks ignore changing resource keys, and activity invalidation does not cover all affected history views.

**Work needed:** Evict failed reads, key fetches by resource identity, reject stale responses and invalidate dependent summaries. Make ordinary retry/navigation recover without a full reload.

## 30. Runtime persistence and recovery are unfinished

**Current implementation and gap:** Normal SQLite connections do not enable foreign keys, schema evolution lacks migrations, overdue sessions can stay active, and the runner has no proper resume/cancel path. Backup/restore covering both learner data and media is undocumented.

**Work needed:** Use connection-level integrity settings, versioned migrations, session reconciliation/recovery and tested backup/restore. One physical database can remain appropriate for the personal app.

## 31. Content releases do not fully pin historical behavior

**Current implementation and gap:** Loading a release overwrites its family list with today's bootstrap allowlist. Historical aggregates use current family mappings, generator/taxonomy revisions are unpinned, and pack files can be overwritten under an existing version. Registered families can also be excluded by the separate hardcoded allowlist.

**Work needed:** Pin content, taxonomy and generator revisions in a validated manifest. Reject conflicting version/hash imports and calculate historical evidence from the frozen question metadata.

## 32. Dashboard metrics are incomplete or misleading

**Current implementation and gap:** The streak is hardcoded to zero, focused time has been replaced by a count, and a capped history count is described as a total. Recent percentages are averaged without accounting for different question counts, and insufficient evidence can read as no weak areas.

**Work needed:** Define each metric and compute it from the appropriate complete/explicit window. Distinguish unassessed, insufficient evidence and demonstrated strength.

## 33. Small-screen and learner-facing presentation need repair

**Current implementation and gap:** The fixed-width sidebar and non-wrapping 20-question navigator are small-screen concerns. Several pages expose backend/handoff terminology and heavy explanatory or metric treatments that earlier product decisions sought to simplify.

**Work needed:** Verify real small-screen layouts and keyboard interaction. Keep the learning/method hierarchy understandable and show technical details only where they help the learner's next action.

## 34. Project tracking, versioning and documentation disagree

**Current implementation and gap:** The current Grove directory has no local Git history; old repos retain separate histories and changes. Changelog, package/API versions, README counts/ports, run commands and copied roadmap statuses disagree. Newly requested curriculum/coverage requirements are not yet recorded as product contracts.

**Work needed:** Reconcile one canonical scope and numbered backlog, retain the prior audit evidence, establish current Git/release tracking, and update working runbooks and behavioral checks.

## 35. Possible cold-start delay when opening Learn — tentative, deferred

**Current observation:** The user initially reported a long wait when opening Learn, then confirmed that subsequent navigation was fine and suggested it might have been a cold start. Do not treat this as a confirmed recurring hang.

**Inspection:** Learn's navigation currently fetches all 27 complete concepts (approximately 280 KB) and then uses only names and counts. One local API sample completed in approximately 150 ms. This identifies possible unnecessary work; it does not establish the cause of the user's earlier delay.

**Work needed, after the main reviewed fixes:** Compare cold startup with repeated navigation. Profile only if the delay is reproducible and meaningful. Consider a lightweight concept index, deferred lesson/media loading and cache recovery only when measurements justify the change. Keep this optional; no performance implementation was applied after the user's deferral.

## 36. Source-to-lesson regression test bench

**Request:** Audit every existing Learn element against its original presentation, distinguish source defects from extraction/organization/delivery losses, and use those cases to improve the pipeline. Track this work within #1–8 and #10 rather than starting a separate ingestion architecture.

**Work needed:** A repeatable, read-only release audit with fresh draft extraction; per-topic/source/slide findings; source hash and slide-count checks; retained/excluded/failed evidence; public-contract loss detection; representative regression fixtures and before/after comparisons. Explicitly report unreviewed visual meaning and answer correctness. Neither a successful extraction nor a notes label is proof of a correct lesson. Do not import a replacement release during the audit.

## 37. Explanation formatting and reading quality

**Request:** Track unmatched parentheses, dangling fragments, long text blobs and lost paragraph/list formatting in existing Learn explanations. Defer implementation to the tail of the backlog, after pipeline reliability and substantive curriculum work.

**Work needed:** Inventory suspicious text with slide citations, distinguish source punctuation from introduced truncation, and review readable paragraph/step/math presentation. Formatting heuristics are review clues, not automatic corrections to mathematical notation or source text. Coordinate with #1, #4, #10 and #33; leave UI changes uncommitted for review.

## 38. Reuse and manage source images as lesson content

**Request:** Preserve useful source images such as the labelled cube diagram and place them directly in the relevant lesson. Provide a repeatable way to manage and reuse these assets as more topics are added, rather than waiting for OCR/diagram interpretation to recover every detail.

**Current implementation and gap (1 October):** Extraction keeps private originals, normalized JPEG assets and source/slide/shape/crop evidence; verified pack import installs delivery media. The organizer retains segment/example media associations, but the public lesson contract drops ordered segments and example-level image links. Learn offers a separate concept image gallery, without figure roles, per-use captions/alt text or zoom; failed image reads currently disappear. This is incomplete image delivery/context, separate from the semantic extraction gaps in #2/#3.

**Work needed:** Add ordered figure blocks and example/step attachments to the lesson contract, reuse the embedded image when it contains the complete diagram, and use a source-region render when labels/arrows are separate source objects. Retain readable delivery variants, content-hash asset IDs and exact source/region provenance. Store captions, accessible descriptions, figure purpose and lesson placement per use; reuse shared asset bytes without collapsing their distinct source occurrences. Source revisions create new asset references while historical releases retain theirs. Validate every association through draft/pack/API/UI and expose missing media. Human-reviewed relevance/legibility permits direct image teaching; OCR-derived facts, mathematical keys and relationship graphs keep their own review requirements.

**Timing:** Start alongside #4/#8 in the next ordered-lesson/media wave, before expanding or publishing refreshed lessons. Use Cubes slide 3 as the first figure pilot and Speed Distance Time as the surrounding lesson-contract pilot. Automatic diagram interpretation (#3) can continue separately. A standalone asset-management screen is not required for the first implementation; manage the manifest/review records first, then assess that UI once there are real authoring needs. Substantial learner-facing changes retain the user's uncommitted review checkpoint.

## Evidence and scope

The earlier [architecture audit](../.local/history/aptitude-import-2026-10-01/GROVE_ARCHITECTURE_AUDIT.md) contains code references and isolated reproductions for the implementation defects. Its evidence scripts and outputs remain under [grove-audit](../.local/audit).

Additional inspection for this inventory covered `ingestion/extract.py`, `extractors.py`, `pipeline.py`, the organizer and mining gates, authored cards, and the public content schemas. No OCR/vision stage, table/layout preservation, or method-stage/coverage entities were found in those paths. The existing active-deck catalog contains 43 retained image-only slides, all classified as title slides. Whether these are genuinely covers requires visual review; the count does not include images already discarded by extraction filters and is not a measure of image-ingestion success.

The proposed baseline → recognition → shortcut curriculum and scenario/unknown coverage model are new product requirements. They should be recorded explicitly and implemented with the smallest useful data model. User accounts, mobile sync, psychometric calibration and a full CMS remain deferred.

Sources:

- [Extraction and image filtering](../backend/ingestion/extract.py).
- [Format adapters](../backend/ingestion/extractors.py).
- [Pipeline, classification, validation and packing](../backend/ingestion/pipeline.py).
- [Concept assembly](../backend/ingestion/organize/concepts.py).
- [Flashcard drafting](../backend/ingestion/organize/flashcards.py).
- [Authored methods/formulas](../backend/ingestion/authored_cards.py).
- [Learner-facing content schemas](../backend/app/schemas.py).
