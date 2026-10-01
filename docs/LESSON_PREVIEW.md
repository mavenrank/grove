# Ordered lesson and source-image previews

This is a private draft/review path for #4/#6/#7/#8/#10/#38, supported by the #36 bench. It carries ordered teaching material and original figures through compilation, API delivery and a learner-facing preview. It does not approve/import a replacement release or record learner progress. UI/curriculum approval is pending at this checkpoint.

## Contract and source checks

Lesson schema 1 defines ordered sections (`overview`, `baseline`, `recognition`, `shortcut`) containing text, actual formula relations with conditions, method steps, worked examples and figures. Examples can attach prompt/solution figures. Each figure has its own source/deck hash, original slide/notes surface, shape/block identity, role, caption, alt text and review status. Shared assets retain a full byte hash, JPEG/PNG MIME type and dimensions. Asset reuse does not merge source occurrences.

The compiler checks citations against the current catalog and source bytes. Original JPEG/PNG bytes are copied unchanged; `normalized_preview` explicitly selects the extractor's JPEG alternative. Full hashes, actual format/dimensions, size bounds and complete asset references are checked. A cropped, rotated or grouped image is refused until a reviewed source-region renderer can preserve its intended appearance. Separate PowerPoint labels/arrows need that future path too.

Exact-shape decoration exclusions require freshly validated source-review annotations. They affect only selection in this draft, preserve reasons/evidence and cannot remove another use of the same image or clear publication blockers. Other images on cited slides remain `not_selected_needs_review`. This decision inventory covers cited slides, not every image in the complete corpus.

## Compile a new draft

Run from `backend` with the existing Python environment (`python-pptx`/Pillow installed). Use a current catalog, its original source root, the extractor's media directory and a reviewed authoring plan. Plan JSON has exactly `lesson_plan_version: 1`, `lessons: [...]` and `exclude_review_ids: [...]`; lessons remain `review_status: "draft"`. The current private pilot plan is `.local/audit/wave5-lesson-plan.json`.

```powershell
grove-ingest lesson-drafts `
  --source "$env:GROVE_SOURCE_DIR" `
  --catalog ../.local/catalog.json `
  --plan ../.local/lesson-plan.json `
  --media-root ../.local/extracted/media `
  --output ../.local/new-lesson-preview
```

When exclusions are requested, also provide `--review-manifest`, `--visual-report` and `--evidence-root`. The catalog must contain every source referenced by those review annotations. Output must be fresh/empty and unable to overwrite source/media/evidence roots. Failure can leave private review artifacts; retry in a new directory. Success writes `lesson-bundle.json` (`approved: false`) and verified `media/`. There is no approve/import flag.

The installed `grove-ingest` entry point and `python -m ingestion.cli` are equivalent. The two real pilots use the all-Learn catalog for review validation and freshly rechecked Cubes/SDT media; 43 fresh native slides match the previous snapshot exactly.

## Run an isolated review server

Use separate directories so application bootstrap cannot touch the live database. From `backend`, in one terminal:

```powershell
$env:GROVE_DATA_DIR = '../.local/review-state/data'
$env:GROVE_CONTENT_DIR = '../.local/review-state/content'
$env:GROVE_MEDIA_DIR = '../.local/review-state/media'
$env:GROVE_LESSON_PREVIEW_DIR = '../.local/new-lesson-preview'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8002
```

From `frontend`, in another terminal:

```powershell
$env:GROVE_REVIEW_API_TARGET = 'http://127.0.0.1:8002'
npm run dev -- --host 127.0.0.1 --port 5175 --strictPort
```

Open `/learn-preview/<lesson-id>`. The Vite proxy forwards requests to the isolated backend; its default remains port 8001. `GROVE_LESSON_PREVIEW_DIR` is unset by default, producing 404 for preview routes. Image decoding is loaded only when checking an image. The preview index/details/media routes are read-only; invalid bundles or missing/changed images fail explicitly, and metadata is uncached. Media is tied to the selected lesson and verified before delivery. Do not enable this private draft path on a public deployment.

## Current review checkpoint

Private evidence: `.local/audit/wave5-lesson-preview/`. Review server state: `wave5-preview-state/` beside it. The frontend source is intentionally uncommitted until the user reviews:

- [Cubes source figure](http://127.0.0.1:5175/learn-preview/cubes-source-figure): original transparent 300×176 PNG, Face/Edge/Vertex visible on white, source caption, inline placement and keyboard-accessible enlarge/zoom. This is a figure pilot, not the complete painted-cubes curriculum.
- [Speed–Distance–Time baseline](http://127.0.0.1:5175/learn-preview/speed-distance-time-baseline): basic relation, three unknown configurations, compatible-unit conditions, five method steps, given/target separation and worked 720 km/h reasoning. The source's erroneous multiplication line is not taught; correct reciprocal reasoning is independently checked. Pattern recognition, specialized shortcuts and the rest of the topic remain pending.

Review clarity of the method, image readability/enlargement and phone layout. Desktop and 390px checks passed, including zoom/Escape/focus return and no horizontal overflow. A deliberately absent private image produced visible failure/retry with caption/source retained; the compiled bundle was restored byte-for-byte afterwards.

Verification: 274 backend tests, TypeScript/Vite build, all 78 source hashes, 43 fresh native slide comparisons, 11 current review annotations, unchanged source PNG through API, and the frozen live 0.3.5 payload checked using read-only SQLite. Evidence: `wave5-integrity-check.json` and `wave5-{cube,sdt}-{desktop,mobile}.jpg` in the private audit directory. The runner cannot honor standard service for GPT-6-Luna reviewers, so necessary source inspection was direct; no priority reviewer was substituted.

## Remaining publication work

Normal pack/import reconstruction still follows the existing reviewed organizer and JPEG-only installation contract. A private bundle cannot be used as a learner release. Before activation, implement reviewed lesson authoring/reconstruction, PNG installation/version retention, complete source/semantic review and activation/rollback checks, then review a versioned candidate. The old Learn pages continue to read release 0.3.5.

Other open items: a hybrid figure with separate labels/arrows, source-region rendering and variants, figure placement within an individual solution step, discoverable historical asset usage, complete topic curriculum and full-corpus semantic coverage. A dedicated asset-manager screen remains deferred until this workflow shows it is needed. #35 cold-start and #37 legacy explanation formatting remain at the tail of the backlog.
