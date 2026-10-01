# Grove — Architecture

A single-learner, localhost-first aptitude practice app. Two deployable units,
both inside this repo:

```
grove/
├── backend/            uv-managed Python 3.12 · FastAPI · SQLite (WAL)
│   ├── app/            the API + test engine + persistence
│   ├── ingestion/      PPTX corpus → reviewable JSON → content packs (CLI)
│   └── tests/          pytest suite
├── frontend/           bun + Vite · React 19 · TypeScript · Tailwind
│   └── src/            SPA (pages, test runner, API client, UI primitives)
└── docs/               this file, plus handoff/scope notes
```

## Backend (`backend/app`)

Small modules with one responsibility each; `main.py` is only a composition
root. Facade `__init__.py` files keep historical import paths working.

```
app/
├── main.py                 composition root: app + middleware + include_router
├── config.py               env-driven settings (GROVE_* vars)
├── security.py             rate limiting, security headers, learner identity
├── schemas.py              response models — the outbound allowlist (§8.6)
├── routers/                HTTP layer, no business logic
│   ├── requests.py         request-body models — the inbound allowlist
│   ├── content.py          taxonomy, concepts, flashcards, media, source-open
│   ├── tests.py            test lifecycle: create/serve/answer/mark/dwell/finish
│   └── misc.py             release info, history, insights, admin status
├── engine/                 server-authoritative test engine (§8.3–8.7)
│   ├── errors.py           TestFlowError / NotFoundError protocol errors
│   ├── planning.py         seeded, reproducible (family, difficulty) planning
│   ├── creation.py         materializes questions; answers stay server-held
│   ├── runtime.py          question serving, tickets, dwell, mark-for-review
│   └── scoring.py          atomic finalization + score computation
├── db/                     SQLite persistence
│   ├── schema.py           DDL (content store + runtime store)
│   ├── connection.py       thread-safe Database wrapper + `db` singleton
│   ├── timeutil.py         utcnow / iso / parse_iso
│   ├── releases.py         immutable content-release queries
│   ├── sessions.py         sessions, questions, scores, events
│   └── activity.py         flashcard/concept views + reviews
├── content_engine/         deterministic content generation from packs
│   ├── releases.py         pack loading/import + family_skill_map adapter
│   ├── bootstrap_release.py the built-in out-of-the-box pack (data only)
│   ├── families/           QUESTION-FAMILY PLUGIN REGISTRY (see below)
│   │   ├── registry.py     register_family / family decorator / lookups
│   │   ├── helpers.py      option-building utilities (mcq, int_q, near-misses)
│   │   └── numbers, frp, averages, timeworkspeed, algebra,
│   │       series, relations, arrangements, coding   (built-in plugins)
│   ├── taxonomy.py         buckets → topics → skills (handoff §10)
│   └── deterministic.py    SHA-256-seeded RNG (reproducibility)
├── evidence.py             skill evidence → strong/needs-practice statuses
└── history.py              test/learning/flashcard history + test detail
```

**Invariants worth preserving**

- The client never receives an answer field: `QuestionOut` has none, and
  correctness is computed only in `engine/`.
- All randomness goes through `content_engine/deterministic.py` (SHA-256
  seeding); a session seed reproduces its plan forever.
- Finalization is atomic and single-shot (`db.finalize_session`).
- `schemas.py` builds every response field by field — no raw DB rows or
  private dicts pass through.

## Ingestion (`backend/ingestion`) — CLI, not part of the API

```
ingestion/
├── cli.py           argparse + command dispatch (`grove-ingest` entry point)
├── pipeline.py      stage logic: discover → extract → normalize → validate → organize → pack
├── extractors.py    FORMAT-ADAPTER REGISTRY (see extension points below)
├── extract.py       python-pptx slide parsing, classification, image media
├── config.py         classification rules (buckets/topics/skills, deferrals)
├── authored_cards.py hand-written formula/rule/approach cards per skill
└── organize/         slides → the three content streams (§13)
    ├── text.py       line hygiene + code detection
    ├── labels.py     "Percentages 1" from corpus slugs (citations)
    ├── questions.py  question-slide parsing (answers confirmed from notes)
    ├── gates.py      anti-junk gates for mined formulas/definitions
    ├── flashcards.py card drafting (authored first, mined gap-fillers)
    └── concepts.py   concept assembly + per-skill grouping
```

Output is an immutable **content pack** (JSON) that a human reviews and then
imports via `grove-ingest import`; the API never writes content.

## Extension points (plugins & adapters)

**1. Question families** — `app/content_engine/families/registry.py`:

```python
from app.content_engine.families.registry import family

@family("myplugin.thing", "quant.numbers.arithmetic")
def thing(rng, difficulty):
    return {"prompt": "…", "options": ["42", "1", "2", "3"],
            "answer_index": 0, "explanation": "…"}
```

Built-in families register at import (`families/__init__.py`); external code
can call `register_family(...)` programmatically — engine, planner and
allowlist all read the same registry, so nothing else changes.

**2. Source-format extractors** — `ingestion/extractors.py`:

```python
from .extractors import register_extractor

@register_extractor(".pdf")
def extract_pdf(path, ctx):        # ctx.media_dir, ctx.save_media(...)
    return slides, media_by_slide
```

`Pipeline.discover/extract` delegate entirely to this registry — adding a
format (real PDF text extraction, an OCR stage) never edits the pipeline.

**3. UI data hook** — `useApiData<T>(fetcher)` in `frontend/src/api/hooks.ts`
centralizes cached-read plumbing (loading/error/SWR-version); pages stay
declarative and mutations keep working through the same cache invalidation.

**4. Route chunks** — every page in `App.tsx` is `React.lazy`-loaded, so new
pages are new chunks by default; only `/tests/run` (the lockdown runner)
stays eager.

## Frontend (`frontend/src`)

```
src/
├── main.tsx, App.tsx     router setup (lazy route chunks) + chrome-less runner
├── layout.tsx            sidebar nav, hover prefetch, route guards
├── telemetry.tsx         TelemetryProvider/useTelemetry context
├── ui.tsx                facade re-export (legacy import path)
├── api.ts                facade re-export (legacy import path)
├── api/                  API client, decomposed
│   ├── client.ts         fetch wrapper, ApiError, invalidation hook
│   ├── cache.ts          stale-while-revalidate read cache + useApiVersion
│   ├── hooks.ts          useApiData — one hook for every cached read
│   ├── types.ts          response-model mirrors (no answer fields, ever)
│   ├── endpoints.ts      the `api` object (reads cached, mutations direct)
│   └── telemetry.ts      TestEvent types + bounded TelemetryBuffer
├── components/ui/        shadcn-style primitives
│   ├── spinner.tsx       Loader2Icon + animate-spin (shadcn default)
│   └── primitives.tsx    Card, Button, PageHeader, ErrorNote, Loading, …
├── pages/                one file per route
│   ├── Overview.tsx      statuses, streaks, insights
│   ├── Learn.tsx         bucket → topic accordion
│   ├── Concept.tsx       formulas, teaching slides, worked examples, citations
│   ├── Flashcards.tsx    topic/skill/kind selection + review loop
│   ├── TestSetup.tsx     count + custom duration (server-owned)
│   ├── TestDetail.tsx    per-question metrics, pace vs personal median
│   ├── History.tsx, Results.tsx, Admin.tsx
└── runner/TestRunner.tsx lockdown test UI (two-level timers, dwell tracking)
```

**Frontend invariants**

- Types in `api/types.ts` mirror the backend allowlists; the `Question` type
  has no answer fields by construction.
- Reads go through the SWR cache; mutations invalidate narrowly (see
  `api/cache.ts`); telemetry/view/source-open POSTs invalidate nothing.
- The test runner never trusts client time for scoring — deadlines come from
  the server; client dwell is analytics only.

## Running it

Two terminals (backend currently on the temporary port 8001):

```bash
cd backend && uv run grove-serve     # FastAPI on :8001
cd frontend && bun run dev           # Vite on :5173, proxies /api → :8001
```

Future reviewed publication (fresh work directory, source review and new version required; import activates content):

```bash
cd backend
uv run grove-ingest pack --source "$GROVE_SOURCE_DIR" \
    --work ../.local/audit/reviewed-work --version 0.x.y --approve
uv run grove-ingest import --work ../.local/audit/reviewed-work --pack ../.local/audit/reviewed-work/packs/grove-ingested-0.x.y.json
# then restart grove-serve
```
