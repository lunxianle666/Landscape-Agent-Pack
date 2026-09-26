# Phase 3 acceptance — CAD Plot, PDF QA and Delivery Validation

**Final status: PASS_WITH_WARNINGS.** The warning is the optional formal visual design review, explicitly `NOT_EXECUTED`; objective PDF QA was run and passed. This is an isolated AutoCAD 2025 personal-workflow acceptance, not a cross-version or public release certification.

## Final live evidence

- Workspace: `runs/phase3-f680a26c768c/` (Git ignored; no A/B/C project input).
- `phase3-result.json`: 24 mandatory checks `PASS`; 1 optional `VISUAL_QA` check `NOT_EXECUTED`; exit code 0.
- `delivery-result.json`: 16 mandatory checks `PASS`; 1 optional `VISUAL_QA` check `NOT_EXECUTED`.
- `visual-qa.json`: mandatory visual judgement `NOT_EXECUTED`, overall `REVIEW_REQUIRED` when considered alone.
- Seven live PDFs: A4 Window Fit, A3 Window Fit, A4 Extents Fit, A3 Extents 1:100, A4 Window 1:100, A4 named Layout Fit, and A4 fallback-device Window Fit. Each PDF has a machine-readable paired plot/PDF-QA JSON file.
- Actual device: `AutoCAD PDF (General Documentation).pc3`; media readback used ISO A4/A3 landscape, `monochrome.ctb`, millimetres, explicit area and scale. A deliberately nonexistent preferred PC3 fell back to the available Autodesk PDF device.
- PDF objective QA checked file existence/bytes, one-page count, MediaBox, width/height, orientation, nonwhite page, vectors and text extraction. All seven accepted PDFs passed mandatory objective checks.
- Independent 1:100 measurement of the 20 m model boundary in generated vector PDFs: 199.9615 mm (A3 Extents) and 199.9827 mm (A4 Window), within 1 mm of the expected 200 mm.
- DWG and DXF saved in the unique run workspace; DWG closed, reopened with the same absolute path/entity count/INSUNITS and verified DIMSTYLE, then closed. AutoCAD reported zero open documents after the run.
- Negative injections: invalid PC3 with fallback disabled, existing output sentinel, invalid output directory, and missing PDF all returned failure without a false pass or sentinel overwrite. A mandatory `NOT_EXECUTED` probe returned `REVIEW_REQUIRED` and nonzero exit.

## Additional checks

- Phase 2 and Phase 3 unit tests: 14/14 pass (`py -3.12 -B -m unittest discover -s tests/unit -p 'test_v0*.py' -v`).
- Existing v0.1 smoke unit tests: 19/19 pass.
- Existing public manifest verifier: `FINAL: PASS`; `installer/requirements.txt`, `manifest.json`, main and the `v0.1.0-beta` tag are unchanged.
- Earlier development runs in separate `runs/phase3-*` folders exposed COM argument errors for Window setup order and `SetLayoutsToPlot` array typing, and one named Layout centering issue. Those were fixed and rerun; the failed run records remain available. No global AutoCAD process termination was used. Dirty automation-owned test documents from those failed runs were saved and individually closed after path verification.

## Scope limits

A2/A1, portrait, 1:50, 1:200 and other AutoCAD versions are implemented in the API but were not live plotted. Formal visual design review remains `NOT_EXECUTED`. These limits explain the warning and should be carried into any future regression gate. No CAD→SketchUp Bridge or A/B/C project regression was started in Phase 3.

The PDF stability timeout starts after foreground `PlotToFile` returns; a COM call that blocks indefinitely remains an unresolved risk. AutoCAD 2025 did not exhibit that behavior in this acceptance. Future process-scoped supervision must not use a global AutoCAD kill.

## Decision

**GO_BRIDGE** for a separately scoped next phase, because the personal AutoCAD output chain now produces and checks PDFs, preserves files, and validates disk reopen. Retain the visual and software-version limitations in the next phase; this decision does not claim production release readiness.
