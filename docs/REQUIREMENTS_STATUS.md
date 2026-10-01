# Current implementation and acceptance gaps

Updated October 1, 2026. This records current code/evidence and the user's active
requests. It does not reinstate the old handoff/scope as current requirements.
The detailed [tracker](REMEDIATION_TODO.md) owns acceptance criteria and subtasks.

Review acknowledgement applies to the concrete change shown. It does not establish
full semantic coverage, authorize release activation or close its parent issue.
This cleanup closes **no issue groups**. #26 and #36 retain their existing
implemented states; that is not a new closure decision.

| Current outcome | Implementation/evidence | Remaining work and issue IDs |
|---|---|---|
| Sources and project ownership | Grove app and support records; hash-verified relocation | Recovery/version documentation remains #34 |
| Native PPT ingestion | Positioned text/media/notes and source provenance; notes/choice fixes | Tables, other representations, losses and complete semantic review #1/#5/#6/#7 |
| Image-only and hybrid sources | Whole-slide renderer, offline OCR, reviewed source decisions and private figure previews | Diagram relationships, source-region rendering and generalized delivery #2/#3/#4/#38 |
| Publication approval | Strict reviewed-work schemas, source/media validation and immutable import/candidates | Semantic review, reviewed lesson reconstruction, PNG installation, activation/rollback #7/#8/#31/#38 |
| Current Learn content | Stored 0.3.5 remains unchanged, 27 concepts and 97 cards | Placeholder/incomplete teaching content needs reviewed replacement #4/#10/#13 |
| Source-to-lesson bench | All stored Learn topics and 78 cited files accounted for; stable anomaly evidence | Detection is implemented; resolving findings and full-corpus meaning remains #1–8/#10 |
| Baseline method | Private Speed–Distance–Time pilot includes relations, units, givens/target and worked reasoning; presentation acknowledged | Complete curriculum, problem-type links, method evidence and normal release publication #9/#10/#24 |
| Recognition and shortcuts | Ordered contract can represent stages | Reviewed patterns, conditions and problem-specific shortcuts #11/#12 |
| Flashcards and mastery | Existing review/scheduling works | Method-oriented cards and separation of recall from solving mastery #13/#14 |
| Coverage and unknowns | Bounded SDT examples demonstrate several targets | Topic-domain model, solvability and taught/assessed coverage #9/#15/#16 |
| Generated variants | Deterministic authored families; known errors corrected, structural safeguards | Independent validation across all families, realistic constraints and repetition control #17/#18/#19 |
| Assessment targeting | Existing mixed blueprint and generated selection | Focused topic/problem-type blueprints and reviewed source-question adapter #20/#21 |
| Backend attempt lifecycle | Session ownership, stored deadlines, transactional answering/expiry/finalization; approved 91467d8 | UI saving/recovery is separate #25; telemetry/order reliability #27 |
| Answer-save reliability | Backend idempotency receipts exist | Frontend receipt use, correct stale_ticket handling, request ordering and visible recovery #25/#27 |
| Timing and evidence | Events/dwell stored; basic skill evidence/history | Dwell duplicates/loss, comparable skill/family/difficulty baselines and complete evidence signals #22/#23 |
| Isolation and recovery | Safe question schema, terminal-result checks and chromeless runner | Learning API/cache isolation, failure recovery and invalidation #28/#29 |
| Historical reproducibility | Original stored questions and immutable database release payloads preserved | Runtime authored merges, generator/taxonomy/blueprint pinning #31 |
| Database recovery | Foreign keys per connection and transactional locks implemented | Verified backup/restore, migrations and recovery procedures #30 |
| Learner navigation | Startup tooltip fix and responsive/resizable sidebar approved; bounded figure preview acknowledged | Wider screen/language/dashboard/link work #24/#32/#33 |
| Deferred observations | Cold-start is tentative; legacy formatting findings inventoried | #35 and #37 remain at the end of main remediation |

## Verification boundaries

The previous full backend checkpoint recorded 274 passing tests. This cleanup
reran the TypeScript/Vite build for the previously acknowledged preview. It checks
links/paths, syntax of corrected private helpers, preserved file hashes and tracker
state; it does not claim a fresh full backend run, complete source verification or
production readiness.

Source review constraints remain GPT-6-Luna/max/standard only when available.
No reviewer was launched, corpus rerun, original source edited, learner history
rewritten or replacement release imported by this cleanup.
