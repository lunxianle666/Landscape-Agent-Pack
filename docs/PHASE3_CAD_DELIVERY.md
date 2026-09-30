# Phase 3 CAD Plot, PDF QA and Delivery Validation

Development branch: `codex/v0.2-integration`. The public v0.1.0-beta installer and tag are unchanged.

## Boundaries and modules

| Module | Input and responsibility | Output |
|---|---|---|
| `cad/plot.py` | Immutable `PlotRequest`, owned `DocumentSession`, one new PDF path. Discover Autodesk PDF PC3 devices, choose media, set plot state explicitly, execute one `PlotToFile`, wait for stable output. | Unified `Result` with actual device/media/style/units/scale. |
| `cad/pdf_qa.py` | PDF path and `PDFProfile`. Inspect MediaBox, page count, size, orientation, rasterized nonwhite fraction, optional vectors and text. | Unified objective QA `Result`; it does not assess design quality. |
| `cad/visual_qa.py` | Future inputs: rendered page, screenshot, design intent and visual checklist. | Mandatory `NOT_EXECUTED` until a formal visual reviewer runs. |
| `cad/delivery.py` | Saved/reopened snapshots, DXF geometry profile, dimension verification evidence, plot/PDF results and workspace output manifest. | Final delivery gate with mandatory checks and optional visual `NOT_EXECUTED`. |

`requirements-v02-dev.txt` pins the tested Windows development environment. PyMuPDF is used for PDF parsing and small grayscale renders. Its distribution license must be reviewed before it becomes a public package dependency; this Phase 3 code is not part of the v0.1.0-beta installer.

## Plot contract

Paper: A4, A3, A2, A1. Orientation: portrait or landscape, selected by exact canonical ISO dimensions. Area: Extents, Window, Layout. `Window` requires explicit increasing XY corners; `Layout` requires a named paper-space layout. Scale: `fit` or `1:N` with positive denominator, including 1:50, 1:100 and 1:200. A request also names plot style, preferred PC3, fallback behavior, centering, timeout, poll interval and new output PDF path. Overwrite is rejected. All output paths must remain under `DocumentSession.workspace_root`.

Device discovery enumerates PC3 names containing PDF on the current layout. A preferred device is honored when present; otherwise a compatible AutoCAD PDF PC3 is selected if fallback is enabled. No PDF PC3 or missing media/style returns `FAIL` with `CONFIGURATION_REQUIRED`. The selected device/media/style/scale and AutoCAD readback are included in the result. The chosen device is passed to `PlotToFile`; `BACKGROUNDPLOT=0` is set for foreground plotting. The call is never blindly replayed after uncertainty. A bounded wait requires the PDF to exist and hold a stable nonzero size for multiple polls. Timeout returns `FAIL / TIMEOUT`.

The timeout bounds **file completion after `PlotToFile` returns**. A synchronous COM call that itself hangs cannot safely be interrupted by this module. It requires process-scoped supervision in a future phase; no global AutoCAD termination is allowed.

PDF objective QA opens the generated file and checks the actual page MediaBox in millimetres against a requested paper size, orientation and tolerance; each page must contain nonwhite pixels. Vector paths and extractable text are reported separately. A missing or unreadable PDF fails. A successful objective check does not imply successful visual design review.

The delivery gate requires the DWG under the owned workspace, nonempty on disk, a saved snapshot, close/reopen, matching reopened path/entity count/units, Phase 2 DXF Geometry QA, persisted DIMSTYLE evidence, all required plots and a corresponding PDF QA for every plotted PDF, a clean final close, zero open automation documents, only declared output files, and no overwritten user files. Its optional `VISUAL_QA` check remains `NOT_EXECUTED`, so a successful objective delivery is `PASS_WITH_WARNINGS`.

## Reproduce on this machine

With AutoCAD 2025 running and **zero open drawings**:

```powershell
py -3.12 -B -m unittest discover -s tests/unit -p 'test_v0*.py' -v
py -3.12 -B tests/integration/cad_delivery_live.py
```

Each live run creates `runs/phase3-<id>/` and no project drawing is opened. The runner makes a new three-layer test DWG, saves it, plots model and named layout PDFs, inspects PDFs, injects four failure cases, exports a DXF, closes/reopens the DWG, verifies dimension variables, closes again, and writes unified JSON/Markdown reports. It refuses to start if any AutoCAD document is already open. On an abnormal exit, it never globally kills AutoCAD or silently discards a dirty test drawing.

The A4/A3 landscape, Window/Extents, Fit/1:100, named Layout and device fallback paths have live AutoCAD 2025 acceptance. A2/A1 and portrait are supported by the API and canonical media selector but have **not** been live plotted in Phase 3. Other AutoCAD versions are untested.

## API references

- [Autodesk PlotToFile and foreground plotting](https://help.autodesk.com/cloudhelp/2016/CHS/AutoCAD-ActiveX/files/GUID-85A6B1AF-80AA-4F56-8305-6EFD4A4D8CF8.htm)
- [Autodesk RefreshPlotDeviceInfo](https://help.autodesk.com/cloudhelp/2015/DEU/AutoCAD-ActiveX/files/GUID-1E8879B2-E616-4436-9356-15D0D6A3F0E9.htm)
- [Autodesk custom and standard scales](https://help.autodesk.com/cloudhelp/2021/ENU/AutoCAD-ActiveX/files/GUID-D881B237-0040-4A7C-99D5-E82FA8B1EFE0.htm)
- [Autodesk Window plot bounds](https://help.autodesk.com/cloudhelp/2024/DEU/AutoCAD-ActiveX-Reference/files/GUID-C2F875C1-C95A-4B6E-849A-79B03BCA4666.htm)
