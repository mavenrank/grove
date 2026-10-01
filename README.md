# Grove

A local, single-learner aptitude and reasoning practice application.

Grove combines Learn, flashcard review, server-generated tests and activity history.
Frontend and backend live here.

Current work is indexed in [docs/WORK_INDEX.md](docs/WORK_INDEX.md); acceptance
criteria and remaining work are in [docs/REMEDIATION_TODO.md](docs/REMEDIATION_TODO.md).
GROVE_HANDOFF.md and GROVE_SCOPE.md were committed in baseline **1bc58c8** on
30 September 2026. They are historical planning references, not current scope.

## Repository layout

~~~text
grove/
├── backend/
│   ├── app/                  API, test engine, database and content engine
│   ├── ingestion/            private grove-ingest CLI
│   ├── tests/                runtime, security and ingestion checks
│   └── ingestion-work/       ignored earlier extraction output
├── frontend/src/
│   ├── pages/                learning, reviews, tests, history and draft previews
│   ├── runner/               test runner
│   └── api/                  typed client, cache and telemetry
├── docs/                     maintained guides, tracker and work records
├── data/                     ignored runtime database (grove.db)
├── content/media/            ignored installed delivery images
└── .local/                   ignored audit evidence, drafts and archives
~~~

## Local startup

The current backend default is **8001**. Vite uses **5173**, proxying /api to
http://127.0.0.1:8001. The earlier standard backend port is 8000; 8001 is the
documented temporary override. Match the frontend proxy when changing ports.

From backend:

~~~powershell
uv sync
uv run grove-serve
~~~

From frontend:

~~~powershell
bun install
bun run dev
~~~

Open <http://localhost:5173>. Isolated lesson review uses 8002/5175;
see [LESSON_PREVIEW.md](docs/LESSON_PREVIEW.md). The backend disables draft preview
access unless explicitly configured.

Settings in backend/app/config.py accept GROVE_ environment variables, including
GROVE_PORT, GROVE_DATA_DIR, GROVE_CONTENT_DIR and GROVE_MEDIA_DIR. The current
default database is grove/data/grove.db. Environment-file lookup uses the process
working directory; start the backend from backend.

## Verification

From backend:

~~~powershell
uv run pytest -q
~~~

From frontend:

~~~powershell
bun run build
~~~

The frontend build includes TypeScript checking. The last full backend checkpoint
recorded 274 passing tests; current output determines the current count. The
approved preview was built again during the October 1 cleanup.

## Sources, pipeline and releases

The private CLI preserves provenance and creates reviewable drafts. PPTX native
extraction, whole-slide inspection and optional OCR are available. Image/diagram
interpretation and PDF extraction remain incomplete. Structural validation does
not establish semantic correctness.

From backend, select a fresh work directory for each extraction:

~~~powershell
uv run grove-ingest run --source "$env:GROVE_SOURCE_DIR" --work ../.local/audit/new-content-review
~~~

See [PIPELINE_TEST_BENCH.md](docs/PIPELINE_TEST_BENCH.md) for the all-Learn comparison,
and [CONTENT_IMPORT.md](docs/CONTENT_IMPORT.md) for reviewed pack/import commands.
Approval requires source review and a new immutable version. Import currently
activates the latest release; separate activation/rollback and recovery remain open.

The last read-only audit confirmed grove-ingested **0.3.5**, imported September 20,
with **27 concepts and 97 flashcards**. This legacy content has known teaching gaps.
New ordered lessons and figures remain private draft previews.

## Assessment boundaries

Question responses use learner-safe schemas. Selection, deadlines, answer validation
and scoring are server-owned. Answers use rotating tickets; finalization is
transactional. Learner-state responses use Cache-Control: no-store.

Answer-save recovery, timing accuracy, comprehensive learning/test isolation,
generator dependency pinning and backup/restore remain unfinished. See the tracker.

## Version labels

Application metadata reports 0.1.0; earlier changelog milestones use a separate
sequence. Content release 0.3.5, pack schema 1, extraction revision 3 and organizer
revision 1 identify different things. This cleanup does not bump or roll back
them. Consolidating application version labels remains #34.
