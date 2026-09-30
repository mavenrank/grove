# Grove

A lightweight, single-learner **aptitude and reasoning practice application**.

Grove implements the learning loop from `GROVE_HANDOFF.md`:

```text
approved content → learn a concept → take a focused test → score on the server
→ inspect simple history → return to a weak concept
```

This repository is a **monorepo** containing both halves of the application
(a deliberate update to the handoff's three-repo layout — see "Repository layout"
below). Learning data never lives in the app source; answer keys and scoring
live only on the backend; the browser can never compute its own score.

## Repository layout

```text
grove/
├── backend/          FastAPI + SQLite server (uv-managed, Python 3.12)
│   ├── app/                    application code
│   │   ├── content_engine/     taxonomy, deterministic generators, releases
│   │   ├── ingestion/          PPTX → JSON pipeline (grove-ingest CLI)
│   │   ├── main.py             API endpoints
│   │   ├── engine.py           test-session engine (planning, tickets, scoring)
│   │   ├── db.py               SQLite schema + store
│   │   └── security.py         headers, rate limits, body caps
│   ├── tests/                  pytest suite (security + loop + ingestion)
│   └── ingestion-work/         pipeline output (catalog, drafts, packs)
├── frontend/         React 19 + Vite + Tailwind 4 (bun-managed)
│   └── src/
│       ├── pages/              Overview, Learn, Concept, Flashcards,
│       │                       TestSetup, Results, History, Admin
│       ├── runner/             chrome-less server-authoritative test runner
│       ├── api.ts              typed client + telemetry buffer
│       └── ui.tsx              layout, primitives, telemetry context
├── GROVE_HANDOFF.md  canonical product handoff
└── GROVE_SCOPE.md    original scope ADR (historical)
```

## Quick start

Prerequisites: [uv](https://docs.astral.sh/uv/), [bun](https://bun.sh).

**1. Backend** (port **8000**, standard):

```bash
cd backend
uv sync
uv run grove-serve
```

**2. Frontend** (port **5173**, standard; proxies `/api` to :8000):

```bash
cd frontend
bun install
bun run dev
```

Open <http://localhost:5173>.

## Tests

```bash
cd backend && uv run pytest -q          # 27 tests: security, loop, ingestion
cd frontend && bunx tsc -b              # strict typecheck
```

Security tests assert the handoff §18 list: answer-key leakage, replayed
tickets, duplicate finalization, expiry, rate limits, `no-store` headers,
payload sanitization.

## Content ingestion pipeline

Your PPTX/PDF material is ingested by a private CLI (never via the learner
frontend), with provenance preserved per file and per slide:

```bash
cd backend

# 1. discover → extract → classify → normalize → validate
uv run grove-ingest run \
  --source "$env:GROVE_SOURCE_DIR" \
  --work ./ingestion-work

# 2. pack (JSON). Drafts carry NO concepts until you pass --approve.
uv run grove-ingest pack \
  --source "$env:GROVE_SOURCE_DIR" \
  --work ./ingestion-work --version 0.1.0            # draft
#    add --approve after human review                 # approved

# 3. import the approved pack into the backend store
uv run grove-ingest import --work ./ingestion-work \
  --pack ./ingestion-work/packs/grove-ingested-0.1.0.json
```

Current corpus result: **1024 decks discovered → 103 unique active-bucket
decks, 309 unique deferred (verbal/algorithms/soft-skills), 21 draft concepts**,
zero validation problems. Deferred material is preserved in the catalog but
never published — activating new buckets is an explicit product decision.

Pipeline outputs (all JSON, human-reviewable):

| File | Purpose |
|---|---|
| `ingestion-work/catalog.json` | every deck: hash, slides, classification |
| `ingestion-work/validation-report.json` | dedupe stats, problems, warnings |
| `ingestion-work/draft-concepts.json` | one draft concept per active skill |
| `ingestion-work/packs/*.json` | versioned, immutable content packs |

Classification maps deck titles onto the handoff §10 taxonomy
(`quant.numbers.hcf_lcm`, `logic.rel.blood_relations`, …). Unmatched material
falls back to `unclassified.deferred` rather than guessing.

## Security model (short version)

- Public question payloads are **explicit allowlists** — no `correct_option`,
  `explanation`, `difficulty`, `family_id`, or future questions ever leave the
  server before finalization.
- Answers are verified against **server-held state** with rotating one-time
  tickets; the client cannot choose its own score.
- Session lifecycle (`created → active → submitted/expired/cancelled`) is
  server-owned; duplicate finalization and post-deadline answers are rejected.
- Test responses use `Cache-Control: no-store`; security headers and rate
  limits are applied by middleware; event payloads are size-capped and sanitized.
- Client telemetry (visibility, focus, answer changes, marks) is stored as
  *observations* for personal analytics — never as scoring input.

See `GROVE_HANDOFF.md` §8, §18 for the full boundary and rationale.

## Decisions recorded here (superseding earlier notes)

1. **Monorepo**: frontend and backend live together in `grove/` (was: three repos).
2. **Standard ports**: backend `8000`, frontend `5173` (was: soft ports 8001/5175).
3. **Tooling as requested**: bun for the frontend, uv + soft-pinned Python 3.12
   for the backend.
