# Grove — Changelog

All notable changes to Grove are documented here. Dates use 2026-09-19 (single build day).
Product decisions follow `GROVE_HANDOFF.md`; supersessions are recorded in its §27 addendum.

---

## [0.3.8] — 2026-09-21

### Plugin & adapter architecture (deep refactor, no behavior change)

Turned the two biggest extension surfaces into registries so future question
types and source formats are *registrations*, not core edits.

**Question-family plugin registry** (`app/content_engine/families/`)
- `generators.py` (598 lines) decomposed into `registry.py` (public API:
  `family` decorator, `register_family`, `generate_question`,
  `family_skill_map`), `helpers.py` (option-building), and nine domain plugin
  modules: `numbers`, `frp`, `averages`, `timeworkspeed`, `algebra`, `series`,
  `relations`, `arrangements`, `coding` — all 34 families register at import.
- `generators.py` remains as a deprecation shim (old imports keep working).
- `releases.py` slimmed (bootstrap data moved to `bootstrap_release.py`) and
  gained `family_skill_map()` — the single adapter `evidence.py`/`history.py`
  use for family→skill joins (was re-derived inline in three places).

**Source-format extractor registry** (`ingestion/extractors.py`)
- `Pipeline.extract` now delegates to adapters registered by file extension
  (`.pptx` deep extractor, `.pdf`/`.docx` placeholders); discovery filters on
  registered adapters. New formats (PDF text, OCR) = one decorated function.
- Extraction context (`ctx.media_dir`, `ctx.save_media`) passed to adapters;
  media persistence moved out of the pipeline loop into the context.
- CLI (`argparse`/`main`) moved out of `pipeline.py` into `cli.py`
  (`grove-ingest` entry point already pointed there).

**Frontend**
- `useApiData<T>(fetcher)` hook (`api/hooks.ts`): centralizes the cached-read
  plumbing (loading/error/SWR version) previously copy-pasted per page;
  migrated Overview, Learn, Flashcards, TestSetup, TestDetail, History.
- Route-level code splitting: every page in `App.tsx` is `React.lazy`; the
  lockdown runner stays eager. Main bundle 384 → 342 kB gzip 120 → 111 kB,
  with per-route chunks (2–11 kB each).

**Verification**: 27 backend tests pass; `grove-ingest run` over the real
corpus produces byte-identical stats (84 active decks, 27 concepts, 97
flashcards, 220 segments); `tsc` clean; Vite production build passes with the
new chunk graph.

---

## [0.3.7] — 2026-09-21

### Codebase modularization (no behavior change)

Structural refactor for maintainability: every oversized module became a
package of single-responsibility modules, each fronted by a facade so all
historical import paths keep working. Zero API, schema or behavior changes.

**Backend**
- `app/main.py` (449 lines) → slim composition root (~50 lines) + `app/routers/`:
  `content.py` (taxonomy/concepts/flashcards/media/source-open), `tests.py`
  (test lifecycle), `misc.py` (release/history/insights/admin), `requests.py`
  (inbound request models). Response models remain in `schemas.py`.
- `app/engine.py` (523) → `app/engine/` package: `errors.py`, `planning.py`
  (seeded planning), `creation.py` (question materialization), `runtime.py`
  (serving/dwell/marks/answering), `scoring.py` (atomic finalization).
- `app/db.py` (404) → `app/db/` package: `schema.py` (DDL), `connection.py`
  (Database + singleton), `timeutil.py`, `releases.py`, `sessions.py`,
  `activity.py`. `from app import db as dbmod` still works (facade).
- `ingestion/organize.py` (566) → `ingestion/organize/` package: `text.py`
  (hygiene + code detection), `labels.py` (citation names), `questions.py`,
  `gates.py` (anti-junk formula/definition gates), `flashcards.py`,
  `concepts.py`.
- New `docs/ARCHITECTURE.md` documenting the full module map and invariants.

**Frontend**
- `src/api.ts` (574) → `src/api/` package: `client.ts` (fetch + errors),
  `cache.ts` (SWR cache + invalidation + `useApiVersion`), `types.ts`,
  `endpoints.ts`, `telemetry.ts`. `@/api`-style imports unchanged (facade).
- `src/ui.tsx` (202) → split into `layout.tsx` (sidebar/nav/prefetch),
  `telemetry.tsx` (context), `components/ui/primitives.tsx` (Card/Button/etc.);
  `ui.tsx` remains as a re-export facade.

**Verification**: 27 backend tests pass; `bunx tsc -b` clean; production Vite
build passes; all 8 read endpoints smoke-tested 200 against a fresh DB.

---

## [0.3.6] — 2026-09-20

### Faster navigation: read cache + hover prefetch; shadcn spinner

**Frontend-only change — no release/pipeline changes.**

- `api.ts`: **stale-while-revalidate read cache**. Every read endpoint
  (taxonomy, concepts, concept detail, flashcards, stats, history, insights,
  result, test detail, media) serves cached data instantly on revisit and
  refreshes in the background when past its TTL. In-flight requests are
  deduped. Media is cached hard (10 min — immutable within a release).
- **Hover prefetch**: nav links warm their route's data on mouseenter/focus;
  concept links (Learn accordion, Overview, TestDetail, prev/next) prefetch
  the concept payload — clicking through Learn feels instant.
- **Targeted invalidation**: real mutations (test-session create/finish,
  flashcard review/view) drop only the affected reads. Telemetry, concept-view
  and source-open POSTs invalidate nothing — an earlier draft that cleared the
  whole cache on any POST was measured and fixed (navigation would refetch
  everything every time).
- `useApiVersion()`: pages subscribe to a version counter so background
  revalidations re-render with fresh data; Concept page deliberately does NOT
  subscribe (its view-recording POST would loop).
- **shadcn/ui default spinner** (`components/ui/spinner.tsx`): the canonical
  `Loader2Icon` + `animate-spin`, used by the shared `Loading` component —
  replaces the pulsing-text placeholder everywhere.
- `vite-env.d.ts` added for `import.meta.env` typing; the cache inspector
  (`window.__groveCache`) is dev-only (`import.meta.env.DEV`).

**Verified live**: within-TTL revisit = **zero API calls** (measured via
resource timing); stale revisit = instant cached render + one background
refresh; full page load = normal cold fetch. `tsc` clean, production build
passes.

---

## [0.3.5] — 2026-09-19

### Learn: slides promoted to the top, human citations, open-in-explorer everywhere

**Problems (from Percentages screenshots)**
1. The best teaching asset on the page — the "% Increase / % Decrease" formula
   card image — was buried at the bottom under "Teaching slides" while the
   generic list sat up top.
2. Every example repeated the raw corpus filename:
   `SOURCE: BSTS101P-E-VITDL-S2-...-054-PERCENTAGES-1-2023-04- · SLIDE 5`.
3. The per-example "open the source in file manager" idea didn't exist, and
   the single-concept API never returned `source_decks`, so the Sources card
   silently never rendered.

**Fixes**

- `authored_cards.py`: the formula-slide content is now authored as two
  general flashcards/formulas — `% Increase = (New Value − Initial Value) /
  Initial Value × 100` and the Decrease twin — so the slide's rule is both a
  flashcard and the first entries under "Formulas & rules".
- `organize.py`: new `short_deck_label()` derives learner-facing names from
  the corpus convention `<provider>__<course>__<NNN>__<TITLE>__<date>` →
  "Percentages 1". Attached to every question/example/media source
  (`deck_label`) and to concept `source_decks` (`short_name`).
- `schemas.py` + `main.py`: `ConceptOut.source_decks` exposed (was dropped by
  the response model at both concept endpoints).
- `Concept.tsx` rework:
  - **Formulas + Teaching slides now sit side-by-side at the top** (2-col on
    md+); the slide image is no longer buried at the bottom.
  - Every caption reads **"Percentages 1 · Slide 5"** with an inline **open**
    button that reveals that exact deck in File Explorer.
  - New **Citations** section at the bottom: `[1] Percentages 1 · 20 slides`
    with the full original filename and an Open button per source.
- `api.ts`: `sourceCaption()` helper + `short_name` on `ConceptSourceDeck`.

**Result (release v0.3.5, imported and live)**
- Percentages: 1 teaching slide (the formula card) top-right beside 12
  formulas; 20 worked examples each captioned "Percentages 1 · Slide N" with
  open buttons; 4 citations with full filenames.
- Backend tests 27/27 green; `tsc` clean.

---

## [0.3.4] — 2026-09-19

### Learn page: killed the "unnecessary things" at the source

**Problems (from screenshots of the Arithmetic concept page)**
1. `Formulas & rules` showed code input literals (`num= [5, 7]`), narrative
   sentences ("The code starts with `x = 1` and increments…"), and numbered
   walkthrough steps — the concept collector used a weak
   `line contains "="` heuristic, far looser than the strict flashcard gate.
2. A worked example's explanation was literally `)` — the notes regex
   captured the closing paren of "Answer: B)" as the explanation.
3. The teaching-slides gallery showed provider logos (FACE), template
   backgrounds (purple Codemithra), and thank-you-slide contact icons — every
   picture on any slide was harvested, and title/ceremony slides were
   classified as "explanation".

**Fixes**

- `organize.py`
  - new `_concept_formula()` gate for the Learn "Formulas & rules" list:
    rejects backticks, `[ ] { }` literals, chained calculations (`a = b = 3`,
    which is worked-example material), numbered steps, and every narrative
    opener — the same strict shape the flashcard miner uses. ASCII `/ . + -`
    added to the formula charset so `1/2 = 50%` still passes.
  - concept formulas now start with the **authored** general formula/rule
    fronts (canonical formulas for the skill), then strictly-gated mined lines.
  - `_clean_explanation()`: explanations must contain real words; punctuation
    debris ("Answer: B)") is dropped, falling back to notes with the
    "Answer: X" prefix stripped.
- `extract.py`
  - slide classification now knows ceremony: "thank you" / contact / agenda
    slides → `other`; slide 1 of a multi-slide deck → `title` (provider
    covers in this corpus); a lone single slide is still content.
- `pipeline.py`
  - **template-image suppression**: an image appearing in 3+ distinct source
    files is a provider template asset (logos, backgrounds, icons), not
    teaching content — dropped everywhere (learning segments, questions, packs).

**Result (release v0.3.4, imported and live)**
- Arithmetic: formulas `num= [5, 7]`-style junk gone → the two authored
  factor-count rules; gallery 12 junk images → **1** (the actual CRT theorem
  slide, slide 4); the `)`-only explanation → the full LCM(a,b,c)+r solution.
- Whole release: pack media 22 → **9 real teaching images**; 0 junk formulas
  and 0 punctuation-only explanations across all 27 concepts; percentages and
  HCF/LCM kept everything good (verified no regressions).

---

## [0.3.2 / 0.3.3] — 2026-09-19

### Flashcards rebuilt around general formulas + approach/mindset

**Problem (from screenshots)**: cards like `3 green lights = ?` (one specific
puzzle's mapping, meaningless as recall) and `Quotient = ?` (a context-free
fragment) — mined slide text is example-specific by nature.

**Fix — two-layer card system**

- **Authored card library** (`backend/ingestion/authored_cards.py`): 67
  hand-written, reviewable cards across 40 skills, in three kinds:
  - `formula` — the general formulas (`HCF × LCM = product`,
    `Angle between hands = |30H − 5.5M|`, `Profit % = Profit/CP × 100`,
    `Average speed over equal distances = 2ab/(a+b)`);
  - `approach` — the mindset for the problem type ("checking order for a
    number series: differences → ratios → alternating → second differences →
    squares/cubes/primes", "blood relations: draw a family tree generation
    by generation", "syllogisms: conclusion must hold in EVERY valid Venn");
  - `rule` — durable facts and traps ("+x% then −x% is always a net
    x²/100 % loss", "100 years = 5 odd days").
- **Mined cards demoted to gap-fillers** with strict generality gates:
  - mixed digit+word LHS rejected (`3 green lights = …`);
  - one-word alpha LHS rejected (`Quotient = ?`, `Max = ?`) — the genuine
    one-word formulas are authored;
  - code fragments, narrative subjects, and truncated sentences already
    rejected (0.2.3).
- Authored fronts win deduplication, so mining can only add what the
  authored layer lacks.

**Result**: 36 haphazard cards → **88 structured cards**
(38 formula / 27 rule / 23 approach), zero screenshot offenders.

**UI**
- Card kind badge on the face (`formula` / `rule` / `approach`, colored).
- New kind filter chips (`all kinds / formulas / rules / approach & mindset`)
  alongside topic and skill selectors.
- Release v0.3.3 imported and served.

---

## [0.3.1] — 2026-09-19

### Learn polish (the "learning part" rework)

**Pipeline — normalization and content quality**

- **Deep deck inspection before fixing**: hand-audited representative decks
  (PERCENTAGES 1, NUMBERS 4 HCF/LCM, APPLICATIONS AND PRACTICE ON NUMBERS) to
  see exactly what the extractor captures. Findings: teaching content lives
  mostly in slide *images*; text frames are titles + fragment lines; some
  decks are Java/DP algorithm material that had misclassified into quant.
- **AppleDouble junk eliminated**: `._*` and hidden files (macOS metadata
  twins, ~64 phantom "decks") are now excluded at discovery. Active decks:
  148 → 84 (all real), deferred 264 → 210.
- **Boilerplate lines dropped**: `THANK YOU`, `Any questions`, bare `Q&A`,
  template `Topic/Course`/`VIT` furniture no longer reach summaries or formulas.
- **Code is structured, not smeared**: multi-line code frames are detected
  (`looks_like_code` — per-line code-shape ratio), language-tagged
  (java/python/c/cpp/sql/pseudo), and emitted as `code_blocks` with per-block
  source provenance. Code never pollutes `formulas` or `summary` again
  (Java `ArrayList`/`Scanner` fragments seen in screenshots came from
  strobogrammatic/DP algorithm decks — those are now correctly deferred:
  strobogrammatic, palindrome, fibonacci, LCS, huffman, anagram, etc.).
- **Concept sources carry absolute paths** (`source_path`) so the app can
  open the original deck locally.
- Pack **v0.3.0 / v0.3.1** imported (27 concepts, 34 flashcards, 447
  notes-verified questions preserved for review).

**Backend**

- New `POST /api/source/open` (QOL): reveals an ingested source deck in the
  OS file explorer (`explorer /select,` on Windows, `open`/`xdg-open`
  elsewhere). Guarded: path must be inside the release's `source_root`,
  missing files 404, traversal attempts 403, toggleable via
  `GROVE_ENABLE_SOURCE_OPEN` (verified: valid path opens Explorer,
  `C:\Windows\system32\cmd.exe` is rejected).
- `ConceptOut` gains `code_blocks: [{language, code, source}]`.
- Release normalizer backfills `code_blocks`/`source_decks.source_path` for
  older packs.

**Frontend — Learn**

- **Accordion layout** replaces the side-tree: buckets → topics as
  expandable rows (chevron, concept count), concepts listed inside with
  example/slide counts. First topic per bucket starts open.
- **Concept page navigation**: breadcrumb (Learn › Topic › Concept), header
  shows bucket · topic, `n of m` position among sibling concepts, and
  prev/next concept links at top *and* bottom of the page.
- **Code blocks**: dark `pre` panel with language label and one-click
  **Copy** button (copied-state check).
- **Sources card**: lists each source deck (name + slide count) with an
  **Open** button that opens it in File Explorer via the backend endpoint.
- Teaching slides, worked examples (answer highlighted + explanation +
  deck/slide provenance), formulas, and common-mistakes sections retained.

---

## [0.3.0] — 2026-09-19

### Ingestion correctness pass

- Crypt arithmetic moved under **Numbers** (standard syllabus placement), with
  its own skill `quant.numbers.crypt_arithmetic`.
- Algorithm/CS decks are deferred *before* aptitude rules run
  (`other.algorithms` first-match): subsequence/LCS, huffman, DP, complexity
  — these were polluting `logic.pat.number_series` and `logic.code.*`.
- `sequence` regex narrowed to `\bseries\b` so `SUBSEQUENCE` decks no longer
  classify as number series.
- Analogy, Clocks, Calendars mapped into the active taxonomy
  (`logic.rel.analogies`, `quant.misc.clocks`, `quant.misc.calendars`);
  `quant.tws` gains `pipes_cisterns` and `relative_speed` skills.
- Taxonomy endpoint now publishes **skills per topic**, so Learn/Flashcards
  group by exact membership instead of ID-prefix guessing (topic IDs like
  `quant.fractions_ratios_percentages` vs skills `quant.frp.*` never shared
  prefixes).

---

## [0.2.x] — 2026-09-19

### [0.2.4] — content quality

- Strobogrammatic/palindrome-style algorithm decks deferred (see 0.3.1 for
  the full list); arithmetic concept now teaches CRT/remainders instead of
  Java code.
- Summaries reject code-shaped and narrative-fragment text.

### [0.2.3] — flashcards rework

- **Flashcard generator rewritten** with strict quality gates
  (`_clean_formula_line`, `_clean_definition_line`, `NOISE_TOKENS`):
  cards are now genuine recall items (`age after n years = X + n`,
  `Compound Interest = Amount – Principal`, `Quotient = Number of weeks`,
  `Alligation is a rule that enables us to find the ratio…`) instead of
  code fragments (`if(n = ?`) and truncated `What does this mean: "…"?`
  definitions. 168 raw drafts → 36 clean cards.
- Definition mining rejects narrative subjects (the/a/if/what/…) and
  over-long terms.

### [0.2.2] — runner timing + history detail

- **Durable per-question dwell tracking** (`DwellTracker` in the runner):
  time accumulates per question across revisits — leaving a question banks
  its elapsed time and returning appends, never resets. Segments are POSTed
  to `POST /api/test-sessions/{id}/dwell` every 5 s, on navigation, on
  tab-hide, and at submit (serialized to preserve order).
- **Server-side timing tables**: `question_timing` (first_shown_at,
  dwell_seconds, revisit_count, marked_after_seconds, answer_changed) and
  `question_dwell_segments` (per-segment audit trail). `_stamp_question_shown`
  records first-view/revisits server-side.
- **Marked-for-review timing**: the server snapshots accumulated dwell at the
  moment a question is marked (`marked_after_seconds`) — "decided to come
  back later after N s" is now measurable.
- **Lockdown test mode**: context menu, text selection, and drag disabled;
  mouse-out near viewport top and tab-hide show a recorded-in-report notice;
  focus-loss is tracked as `focus_lost`/`focus_gained` telemetry events.
- **Single toggleable timer**: one control toggles *time left* ⇄ *time spent*
  (click, with label). Detailed per-question timing is deliberately hidden
  during the test and surfaces in history instead.
- **Test detail page** (`/tests/:sessionId`): every question shown with
  prompt, options, chosen vs correct highlighting, explanation, bucket →
  topic → skill labels, difficulty, time on question, **your median on this
  type** (personal median per skill+family across finalized sessions),
  pace-vs-median badge (slow-but-correct / fast-but-wrong), revisit count,
  marked-after time, and an **intelligent Learn link-out** to the matching
  concept.
- **Tests page** lists all taken tests under the setup card; clicking opens
  the detail view.
- **Skill evidence statuses** (handoff §9 implemented): `unseen`,
  `insufficient_evidence`, `developing`, `slow_but_accurate`, `inaccurate`,
  `inconsistent`, `strong`, `needs_review` — computed from accuracy, dwell
  vs personal median, and recent consistency (< 5 attempts → low evidence).
  UI shows a practice banding (Strong / On track / Needs practice /
  Weak — relearn / Low evidence / Not started) with Learn link-outs.
- New endpoints: `GET /api/history/tests/{id}`, `GET /api/flashcards/stats`,
  `POST /api/flashcard-views`; `ScoreOut` per-question results gain
  bucket/topic labels and timing fields.

### [0.2.1] — Learn content arrives

- Organizer: explanation slides → learning segments; question slides +
  **speaker notes** (the answer key: "Answer: C — …") → verified question
  records with worked solutions; formula lines → flashcard drafts.
- Concepts: `examples` (verified Q&A with explanations), `media` (slide
  images), per-example source provenance.
- Media pipeline: picture shapes extracted, hash-deduped, downscaled,
  JPEG-compressed to `content/media/`; served via `GET /api/media/{id}`
  (base64 JSON; 16-hex id validated).
- Pack v0.2.x imported: 27–29 concepts, notes-verified examples, slide media
  rendering in Learn.

### [0.2.0] — full pipeline over the real corpus

- `grove-ingest` CLI (`run` / `pack` / `import`): discover → deep-extract
  (grouped shapes, notes, images, slide classification) → classify
  (title rules, underscores handled) → dedupe (content-hash captures:
  PINNED/non-PINNED/E_OLDWIN variants) → validate → organize → pack
  (approval-gated) → import (immutable releases in SQLite).
- 1024 decks discovered → 412 unique → active/deferred split per bucket
  policy; unclassified material preserved as deferred, never silently
  dropped.
- Bootstrap release merge: ingested packs supply concepts/flashcards/media,
  the shipped 33 deterministic generator families remain the reviewed
  question source for tests.

---

## [0.1.0] — 2026-09-19

### Initial build (per GROVE_HANDOFF.md)

**Backend** — uv-managed Python 3.12 (soft-pinned), FastAPI + SQLite, port 8000.

- **Server-authoritative test engine**: seeded reproducible question plans
  across both buckets, one allowlisted public question at a time, rotating
  one-time tickets, server-side answer verification, atomic finalization;
  replay, duplicate-finalize, and expired-answer rejection.
- **33 deterministic question families** (arithmetic → power cycles →
  percentages → mixtures/alligation → time-work → series → blood relations →
  coding-decoding → seating…), exactly-4 unique options, fuzz-verified at
  3000 draws per family/difficulty.
- **Security middleware**: `Cache-Control: no-store` on personalized routes,
  security headers + CSP, fixed-window rate limits (stricter on session
  creation), request-body caps, event-payload sanitization.
- **27 tests** covering the handoff §18 security list (leakage, stale
  tickets, expiry, duplicate finalize, rate limits, oversized batches).
- Endpoints: taxonomy, concepts, flashcards, test lifecycle, events,
  history, insights, admin status (writes disabled).

**Ingestion pipeline** — python-pptx CLI with provenance-preserving
extraction, rule-based classification onto the handoff §10 taxonomy,
validation, and approval-gated packing; SQLite content store with immutable
release versions.

**Frontend** — bun + React 19 + Vite + Tailwind 4 + Radix tooltip, port 5173
(proxying `/api`): Overview, Learn (topic tree → concept pages), Flashcards
(reveal + again/remember), Test setup (5/10/15/20 → derived minutes),
chrome-less runner with countdown + mark-for-review + navigator + visibility
telemetry, Results with post-release review, compact History, Admin status.

**Decisions recorded** (handoff §27 addendum): monorepo layout, standard
ports 8000/5173 (supersede 8001/5175), deterministic generator families per
§11, runtime DB + media excluded from Git.

---

### Verification status at 0.3.1

- Backend: `uv run pytest` — 27 passed.
- Frontend: `bunx tsc -b` clean, `bun run build` succeeds.
- Live: backend on :8000 serving release `grove-ingested v0.3.1`
  (27 concepts / 34 flashcards / 33 families); frontend on :5173.
- Source-open endpoint verified with allow/block/missing-path cases.
- Learn accordion + concept navigation verified in the running preview.
