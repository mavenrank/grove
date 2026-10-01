# Local content pack boundary

Pack schema 1 records extraction revision 3, organizer revision 1, catalog/draft digests, operator approval and a content digest. Concepts, examples, segments, cards, questions and citations have typed schemas. Native shape dictionaries remain evidence rather than interpreted facts.

Create a fresh work directory, run ingestion, and inspect `review-report.json`, the source slides and the bench. `--approve` requires successful current validation and no unresolved extraction/organization review items; it regenerates the draft before creating the pack. Notes-confirmed keys still require independent answer review. Digests identify the local reviewed inputs; they are not signatures or proof of source correctness. The reviewed work directory is a trusted local input.

From the backend directory, after the required source/curriculum review:

```powershell
.\.venv\Scripts\python.exe -B -m ingestion.cli pack --source <source-root> --work <reviewed-work> --version <new-version> --approve
.\.venv\Scripts\python.exe -B -m ingestion.cli import --work <same-reviewed-work> --pack <reviewed-work>\packs\grove-ingested-<new-version>.json
```

These commands are instructions for future reviewed publication. No refreshed learner release was imported during the October 1 wave. Existing stored 0.3.5 remains readable. Legacy JSON without the new evidence/schema is refused for new imports; re-extract and review it rather than adding an approval flag.

Import checks the schema, digest, unique identities, classification/citation allowlist, slide snapshots, choice keys and media inventory. It verifies the current original source hashes and resolved path containment, then revalidates/reorganizes the work catalog and compares the resulting pack. Edited JSON cannot gain review status by merely recalculating its digest.

Delivery JPEGs are preflighted for existence, size, dimensions, actual JPEG structure and content identity before installation. Existing assets must match exactly. Files are installed atomically without replacing existing files; private originals remain in the draft directory. A filesystem/database failure can leave valid unused assets, which a retry can reuse; it does not publish a release before installation completes. SQLite insertion is transactional. The app currently selects the latest imported release, so importing is activation. Separate reviewed activation, rollback and cleanup procedures remain open.

Candidate files preserve their first timestamps/bytes on identical retries. Different content under the same candidate version is rejected. The database similarly accepts identical payload/manifest retries and rejects changed same-version data. Choose a new version for changed content. Session generator/taxonomy/blueprint pinning and runtime authored-content merges remain separate #31 work.

Source visuals/OCR, PDF extraction, source-answer defects, actual lesson formulas and the public API/UI retaining ordered content still need work before a refreshed corpus is suitable for learning. This boundary improves structural integrity and reproducibility; those semantic/delivery requirements remain in the tracker.
