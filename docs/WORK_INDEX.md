# Grove work index

Updated October 1, 2026 after the user's explicit resumption of local changes and commits.

## Authority and boundaries

Current user instructions and the maintained tracker govern current work.
The root GROVE_HANDOFF.md and GROVE_SCOPE.md were already committed in baseline
**925ef53** on September 30. They preserve earlier planning and are not current
scope or proof of completion. This cleanup does not reintroduce their requirements.

- App code, tooling, working documents and supporting audit evidence belong in Grove.
- Existing Aptitude material is left alone.
- Keep commits small and local; substantial new UI/curriculum presentation needs review.
- Review approval, verified implementation and issue closure are separate states.
- This cleanup closes no issues and does not import a replacement content release.
- #35 cold-start and #37 formatting remain at the tail of the backlog.

## Maintained records

| Record | Purpose |
|---|---|
| [REMEDIATION_TODO.md](REMEDIATION_TODO.md) | Stable issue IDs, verified subtasks and remaining acceptance criteria |
| [REQUIREMENTS_STATUS.md](REQUIREMENTS_STATUS.md) | Current implementation and acceptance gaps; not old scope reinstatement |
| [FIX_LOG.md](FIX_LOG.md) | Chronological changes, verification and checkpoint decisions |
| [ISSUE_INVENTORY.md](ISSUE_INVENTORY.md) | Findings; historical defects may have later fixes |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Implementation structure and operating commands |
| [ARCHITECTURE_AUDIT.md](ARCHITECTURE_AUDIT.md) | September 30 baseline audit |
| [CONTENT_REFRESH_AUDIT.md](CONTENT_REFRESH_AUDIT.md) | Stored Speed–Distance–Time versus source/draft comparison |
| [PIPELINE_TEST_BENCH.md](PIPELINE_TEST_BENCH.md) | All-Learn detection and per-wave reports |
| [VISUAL_SOURCE_REVIEW.md](VISUAL_SOURCE_REVIEW.md) | Whole-slide, OCR and source-review workflow |
| [SOURCE_REVIEW_PROTOCOL.md](SOURCE_REVIEW_PROTOCOL.md) | Verification and authorized reviewer constraints |
| [CONTENT_IMPORT.md](CONTENT_IMPORT.md) | Reviewed immutable pack/import boundary |
| [LESSON_PREVIEW.md](LESSON_PREVIEW.md) | Ordered lesson/figure pilots and remaining publication work |

## Each work wave and its evidence

Paths are relative to Grove. Private evidence is ignored by Git.

| Work | Commits | Documentation | Private evidence |
|---|---|---|---|
| Preserve existing application | 925ef53 | Baseline architecture audit | .local/audit/{backend,frontend,content}-observations.jsonl |
| Generator/runtime and retry guards | efa9dbd | Fix log checkpoint 1; #18/#26/#27/#28/#30 | .local/audit/audit_probe.py |
| Native ingestion and approval gate | f4eb461 | Fix log checkpoint 2 | .local/audit/wave2-real-samples/ |
| Startup and responsive sidebar | a5bcb29 | Fix log checkpoint 2; #33 | .local/audit/grove-sidebar-{desktop,mobile}.jpg |
| Trace stale speed lesson | 9e54efe | Content refresh audit | .local/audit/speed-distance-time-review/ |
| Bench, notes, choices and classification | 3022bdb, c648b5a, 1850f5c, 1b17c31, 9280af9 | Pipeline test bench; fix log | .local/audit/learn-bench-wave3-final/ |
| Immutable reviewed pack/import | f8240f4, d2069ff | Content import; #7/#8/#31 | Disposable checks recorded in fix log |
| Whole-slide, OCR and source decisions | 01df9a5, 06c2391, 197fa5d | Visual source review | .local/audit/wave4-{whole-slides,ocr-pilots,source-review}/ |
| Ordered lessons and original-image pilots | efec457, c081504, d423b86, ca99e24, 0f8de54 | Lesson preview; #4/#7/#8/#10/#38 | .local/audit/wave5-lesson-preview/, wave5-integrity-check.json, wave5-*-{desktop,mobile}.jpg |
| Current support paths and runbooks | 20fcba9 | README, work index and linked runbooks | .local/migration/cleanup-audit-2026-10-01.json |
| Relocate supporting files | f8798df (ignore rule only) | This index and cleanup checkpoint | .local/migration/aptitude-relocation-2026-10-01.json |

## Private support records

- .local/audit/: extraction snapshots, reports, pictures and draft bundles.
- .local/staging/: old staging copies; application code is in backend/frontend.
- .local/history/aptitude-import-2026-10-01/: four outdated untracked document copies, preserved byte-for-byte and excluded from commits at the user's request.
- .local/history/audit-helpers-before-path-cleanup-2026-10-01/: original one-off helpers before path correction.
- .local/migration/: original move manifest and subsequent cleanup/archive records.
- .local/audit/wave5-preview-state/: isolated review-server state; live state stays in data/grove.db.

Frozen JSON/reports retain their original metadata, including some old paths.
Follow the migration mappings; new runs use current paths and fresh output.
Historical helpers preserve earlier probes; use the supported backend CLI and
runbooks for new runs. Their originals are archived before path correction, and
corrected helpers refuse overwriting their existing recorded outputs.

The user acknowledged the bounded image/lesson presentation. It was committed as
**0f8de54** after a successful TypeScript/Vite build. This does not establish
full-topic correctness or approve publication of a replacement release.
