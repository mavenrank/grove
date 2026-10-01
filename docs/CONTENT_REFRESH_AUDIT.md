# Speed Distance Time: stored-release and source audit

Audit date: 30 September 2026. Trigger: the user's screenshot showed a placeholder summary, two incomplete formula prompts and no worked examples in Learn.

## Confirmed release state

The live API and the database agree. The active immutable release is `grove-ingested` **0.3.5**, generated at `2026-09-20T11:24:01.753572+00:00` and imported at `2026-09-20T11:24:02.169273+00:00`. Its Speed Distance Time concept stores:

- A generic draft summary based on one explanation slide.
- Formula strings `Speed = ?` and `Average speed over equal distances at speeds a and b`.
- Zero worked examples, zero media and zero learning segments.
- One source citation with 18 slides.

The application reads this stored release. Updating extraction code does not rebuild or replace it. The existing catalog was produced on 21 September and has no extraction-version marker. The wave-2 evidence extractor was implemented on 30 September and has not been imported as a new release. The visible topic is stale relative to those code changes, and incomplete even by the earlier draft's own summary. This is not evidence of a browser cache problem.

The cited Time Speed And Distance source PPT exists. Its SHA-256 remains `d1b52da4a68f8e3eeb89c99054a96f53ea3d204ddff8d9bc7acbedd2ea1654fa`, exactly matching the active release's citation. The original teaching source has not changed since that import.

## Targeted draft rerun already completed

Re-extracted that source with the current pipeline into a separate directory, without `--approve` or import:

`.local/audit/speed-distance-time-review/`

All **18** slide positions survive. There are **15** native-text question candidates, three other candidate slides, 20 picture occurrences and five distinct preview images. The slide content modes are one image-only cover and 17 hybrid slides; these counts include branding, not just meaningful teaching diagrams. The newly retained picture evidence includes provider logos and a tiny `2/3` crop. Its coordinates place it partly above the top edge of slide 3, separate from the native question prompt, so it must not automatically replace the prompt's `5/3` value.

The draft remains blocked from approval. It reports unresolved image/drawing meaning, a placeholder summary and missing parsed answer labels for all 15 questions. No active release, learner result or original source file was rewritten.

Files in that private review directory: `comparison.json`, `slides.json`, `catalog.json`, `validation-report.json`, `content-drafts.json`, `arithmetic-review.json` and original/preview media. The first trace script completed those files before a console Unicode-printing error; the saved UTF-8 audit was read separately and the remaining slides were inspected. That console failure did not invalidate the draft extraction.

## Why a rerun alone is insufficient

1. **Answer-note format mismatch.** Slides 3–7 contain explicit labels written as `Option D`, `Option B`, `Option(C)`, `Option A` and `Option(A)`. The current parser recognizes `Answer…`, so it misses all five. Slide 14 contains a worked solution without an explicit answer label. Other slides have blank notes or instructions such as `View -> Notes Page`. These states require separate handling; OCR is not the primary cause of the missing examples in this deck.
2. **Flashcard fronts become lesson formulas.** `assemble_concepts` copies authored card fronts into the concept's `formulas`, rather than the actual relation/answer stored on the backs. Re-running the same organizer still produces `Speed = ?`. This is a transformation bug, not newly supplied lesson content.
3. **The public contract drops new evidence.** `ConceptOut` has no learning-segment field. `ConceptExampleOut` has no example-media/block fields. The Concept page renders only its existing summary, formula, gallery and example sections. Even a newly imported pack carrying richer draft blocks would lose those fields at the API boundary or never display them until that contract/rendering work is implemented.
4. **Source quality problems exist too.** Some notes/choices are wrong or ambiguous. They must be quarantined or corrected in a reviewed derived record, with the original preserved. Blindly copying source notes or regenerating a pack would propagate them.
5. **Reviewed exclusions are required.** Most pictures in this particular deck are logos. Wave 2 deliberately retained them rather than guessing. A reviewed source-hash-scoped template/decoration policy must remove irrelevant assets from the lesson without reintroducing automatic repeated-image deletion.

## Independent arithmetic review

The table follows physical slide positions, not the deck's occasionally reordered `Question N` labels. Values were recalculated from the extracted givens with exact fractions. This is draft arithmetic verification; it does not authorize publication or substitute for unresolved visual/wording review.

| Slide | Problem | Derived answer | Matching source choice | Review finding |
|---|---|---|---|---|
| 3 | Aeroplane over equal distance | 720 km/h | D | Notes end with `1200 × 5/3 = 720`; the correct substitution multiplies by `3/5`. Earlier distance/time line and final value agree with 720. |
| 4 | Bus stoppages per elapsed hour | 10 minutes | B | Native notes give the same result. |
| 5 | Wheel revolution difference | 1200 ft | C | `D/40 − D/48 = 5`. |
| 6 | Walking faster over equal time | 50 km | A | `D/10 = (D + 20)/14`. |
| 7 | Equal-distance average speed | 48 km/h | A | Harmonic mean of 40 and 60. |
| 8 | Reduced walking speed and lateness | 40 minutes | B | `(7/5 − 1)T = 16`. |
| 9 | Two drivers, distance and time difference | 15 km/h | C | Positive root of `180/v − 180/(v + 5) = 3`. |
| 10 | Walking early/late | 7 km | C | `D/3 − D/4 = 35/60`. |
| 11 | Speed change over fixed distance | 64 minutes | A | `80 × 100/125`. |
| 12 | Office travel early/late | 10 km | None | Choices are 64/80/60/55 **minutes**, apparently copied from slide 11. They cannot answer the distance question. |
| 13 | Moving listener and sound interval | 59.4 km/h | B | `330 × (630/600 − 1)` m/s, converted to km/h. |
| 14 | Cycling two sides of a square | 4 km² | D | Distance in half an hour is 4 km, giving side 2 km. Notes agree but lack an explicit answer label. |
| 15 | Cycling and two arrival times | 12 km/h | B | Distance is 60 km; noon travel time is 5 h. |
| 16 | Walking to the station early/late | 35/6 km | A after rounding | Option 5.8 km requires a nearest-tenth rounding convention that the prompt does not state. |
| 17 | Car slowdown and delays at two breakpoints | 120 km | B | Delay ratio gives `(D − 30)/(D − 48) = 45/36`. Native text renders the slowdown as `45th`; its intended fraction needs formatting/visual review. The distance follows without choosing that fraction. |

Whole-slide rendering was attempted with the bundled presentation renderer, but import failed while resolving an image in the notes part. A separate inspection copy with notes links removed preserved all slide/media bytes; the renderer still rejected its package XML. Full-slide visual fidelity is therefore **not verified** in this checkpoint. Original native text, notes, shape positions and extracted images were inspected directly. The rendering failure is a tooling limitation to resolve before approving uncertain visual/fraction cases, not proof that PowerPoint cannot open the source.

## Refresh schedule and next wave

- **Now:** targeted draft rerun and source comparison. This audit has completed that step for the failing Speed Distance Time topic.
- **During the next reliability wave:** fix notes parsing/answer verification, review provider assets, establish image interpretation where needed, carry lesson content through the public contract, and build one source-grounded Speed Distance Time lesson with actual formulas and worked steps.
- **After those pilots pass:** run the whole corpus into a new draft work directory, inventory all omissions and unresolved cases, and compare representative text/image/hybrid topics with source evidence.
- **After candidate review and import checks pass:** create a new immutable release version and install referenced media, then compare the API/UI with the reviewed candidate before replacing the active learning release. A full rerun should not overwrite the current work directory or auto-import a release.

The next review wave focuses on six issue groups: **#2** image interpretation, **#4** lesson/API/visual context, **#6** reviewed exclusions and loss reporting, **#7** notes/answer/import quality, **#8** source/media delivery and refresh integrity, and **#10** a usable baseline-method pilot lesson. Full diagram relationship extraction (#3) and the larger flashcard redesign (#13) remain separate follow-on work. Tentative Learn performance item #35 remains deferred.

The user's allowed reviewer configuration is recorded in `AGENTS.md` and `SOURCE_REVIEW_PROTOCOL.md`: GPT-6-Luna, max reasoning, standard service only. The available runner advertises priority and cannot select standard; no subagents were launched against that constraint. Necessary inspection and arithmetic checks were performed directly.
