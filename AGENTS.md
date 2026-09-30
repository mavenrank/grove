# Grove working instructions

- Keep Git local. Do not add a remote or push without the user's request.
- Work in reviewable waves of five or six issue groups. Record evidence, tests and remaining scope in `docs/FIX_LOG.md` and `docs/REMEDIATION_TODO.md`.
- Substantial UI or curriculum presentation changes must remain uncommitted until the user reviews the concrete result. Approval for the September 30 runtime/ingestion/sidebar waves has already been given and those changes were committed.
- Use fresh draft work directories and disposable test databases. Do not overwrite the learner's existing results or silently import a replacement content release.
- For incomplete/wrong lessons, read `docs/SOURCE_REVIEW_PROTOCOL.md` and compare the stored release, original PPT, extraction draft and API/UI before declaring a fix.
- The user authorizes source-slide reviewers using **gpt-6-luna**, **max reasoning**, **standard service only**, explicitly **not priority**. Use subagents when useful and only when the runner can honor those settings. Do not substitute priority or a different model/effort. If standard service cannot be selected or verified, inspect the necessary evidence directly and report the limitation.
- Keep tentative Learn cold-start observation #35 deferred until after the main reviewed fixes unless a new reproducible failure changes the evidence.
