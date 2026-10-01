# Whole-slide source inspection

`grove-ingest visuals` renders selected original PPTX slide positions into a new inspection directory. It does not edit the native catalog, approve knowledge or import a learner release. Notes text/pictures remain separate evidence in the extraction catalog; these frames depict the slide surface only.

The optional local adapter requires Windows and desktop PowerPoint. It opens an inspection copy read-only, without a presentation window, with macros disabled. An existing PowerPoint process causes a clear refusal so the tool cannot close or change the user's presentation session. Active/embedded payloads and external linked content are outside this pilot; passive hyperlink relationships are retained but not followed. Unsupported sources are recorded as blocked rather than silently omitted.

The adapter uses Microsoft's documented [Presentations.Open](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.presentations.open), [Slide.Export](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.slide.export) and [AutomationSecurity](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.application.automationsecurity). A subprocess timeout is reported as blocked; it can leave an Office process needing to exit before a retry. The tool does not terminate arbitrary Office processes.

From the backend directory:

```powershell
.\.venv\Scripts\python.exe -B -X utf8 -m ingestion.cli visuals --catalog <reviewed-work>\catalog.json --source <source-root> --output <new-visual-directory> --deck <catalog-deck-id>
```

Repeat `--deck` for another deck. Repeat `--slide` to select original positions; omit it for all slides in the selected decks. `--width` defaults to 1600 (800–3200 allowed). The batch is capped at 200 positions. Source hash/containment, count/positions, PNG format/dimensions and rendered-file hashes are checked. Original source bytes and catalog data remain unchanged. `visual-report.json` contains source and slide IDs, native text/issues, adapter/Office/OS versions and local PNG paths. All outputs are private source-derived material and stay outside Git.

The first real pilot rendered all **106 positions** from painted Cubes (25), Syllogisms (36), Clocks (27) and Speed Distance Time (18), with unchanged source hashes. Output: `<source-dir>`. Fifteen fixture tests cover source preservation, invalid plans, external links, wrong render positions/counts/paths/dimensions and timeouts.

Directly viewed Speed Distance Time slides 3 and 17. Slide 3 shows 5/3 hours in the main prompt, confirming the pilot's 720 km/h calculation; a small clipped fraction at the top is separate source artwork. Slide 17 visibly prints “45th” in both slowdown clauses. That is a source ambiguity, rather than evidence that native extraction removed a slash. These observations do not resolve the source's answer/rounding/choice errors recorded in `CONTENT_REFRESH_AUDIT.md`.

Offline Windows OCR was separately probed on four of those slides. It read substantial text but missed some A/C option labels and preserved the ambiguous “45th.” OCR remains a candidate with no fabricated confidence and no automatic override of native text. Integration, disagreement reporting and source-scoped review records follow in this wave.
