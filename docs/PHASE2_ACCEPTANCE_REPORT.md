# Phase 2 AutoCAD Core + QA Foundation acceptance

Date: 2026-09-25. Branch: `codex/v0.2-integration`. Base/unchanged main and `v0.1.0-beta`: `d3295bf58402e84c09800460d86ab74dd9f9a342`.

## Outcome

**Phase 2 mandatory scope: PASS.** Final isolated live run: `runs/phase2-445f0898969e/phase2-result.json` and `.md`, 13/13 mandatory checks PASS, process exit 0. Python unit tests: 8/8 PASS. Existing release smoke unit tests: 19/19 PASS. Existing manifest integrity check: `FINAL: PASS`. Tests used Python 3.12.10, ezdxf 1.4.4, AutoCAD 2025 `25.0s (LMS Tech)` and pywin32 in an already running empty-document AutoCAD instance. No A/B/C source file, WorkBuddy candidate or v0.1.0-beta tag was modified.

The final run created unique temporary DWG/DXF artifacts under ignored `runs/`. It exercised Line, closed Polyline, Circle, three Arc orientations, Text, MText, aligned Dimension, three Layers, named DIMSTYLE, DWG Save/Close/Reopen, DWG SaveAs, DXF SaveAs/Close/Reopen and offline QA. Arc endpoints were read back from real COM objects and exact bounding boxes from the reopened DXF. DIMSTYLE was read back from the reopened DWG, including anonymous dimension-block text height. An injected bad DXF with zero line, tiny line and open polyline caused the expected QA FAIL. A separate required `NOT_EXECUTED` probe produced `REVIEW_REQUIRED`, exit 1 in JSON and Markdown.

Earlier development runs under separate `runs/phase2-*` paths exposed two problems and remain as evidence: `DIMANNO` was not writable by `SetVariable` in this AutoCAD 2025 instance (it is now verified as a read-only effective value after `CopyFrom`), and a transient `<unknown>.Count` error occurred when reading a freshly reopened DXF. The retry is now bounded and confined to idempotent reads; `Documents.Open`, entity creation, SaveAs and Close are not retried automatically. One failed run left its automation-owned dirty test document open for inspection; it was then closed by exact identity after confirming it was the sole test drawing. No AutoCAD process was killed. Final run completed and left zero documents open.

## Five blockers

| Blocker | Resolution and evidence |
|---|---|
| AddArc | Public angle contract in degrees; single conversion to radians in `cad/angles.py`; COM call in `cad/core.py`. Unit tests 0→90, 90→180, 350→10, positive CCW direction, endpoints and exact bbox. Live COM endpoint and reopened DXF bbox checks passed. Full circle rejected in favour of Circle. |
| DXF SaveAs | `DocumentSession` tracks source/current/requested path, name, format, dirty/ownership/opened state; `SaveAs` refreshes and checks active identity. Live DWG→Save/SaveAs DWG→SaveAs DXF→Close→DXF reopen passed. |
| NOT_EXECUTED | Shared aggregate makes mandatory NOT_EXECUTED/SKIPPED `REVIEW_REQUIRED`, exit 1. JSON/Markdown/console and regression probe use one status. Empty mandatory check set also cannot PASS. |
| DIMSTYLE | Deterministic model-space mm at 1:100 profile, `CopyFrom`, immediate readback, then disk DWG reopen readback of DIMTXT/ASZ/EXO/EXE/GAP/DEC/LFAC/DIMSCALE/DIMANNO/DIMSAH/DIMTXSTY/DIMBLK/DIMLUNIT and actual `*D` text height. Other versions not tested. |
| Process Kill | Full repository and candidate references inventoried in `PHASE2_AUTOCAD_CORE.md`. No kill implementation imported; current Core has no kill API. Ownership must be proven before Close; unknown ownership yields manual intervention, never global taskkill. |

## Scope boundaries and residual risks

- This is one machine/version acceptance, not a cross-version guarantee. Other AutoCAD COM versions, fonts, PC3 drivers and client integrations remain untested.
- Retry timeout bounds repeated, returned COM busy errors. A single COM call that never returns cannot be interrupted safely in this same Python process; future process-isolated control needs separate ownership-aware design. This limitation was not triggered in the final test.
- Plot/PDF execution and actual visual QA remain outside Phase 2 mandatory scope and are **NOT_EXECUTED**. They are not included in the 13-check live acceptance and cannot be cited as passed.
- CAD→SketchUp Bridge, SketchUp Automation and A/B/C full-chain regression were not started.
- `DocumentSession` requires an explicit isolated workspace and refuses an existing document collection. No scoped PID termination is implemented; an unresponsive owned process would require manual handling until a future, separately evidenced design exists.
- Geometry QA is a minimal objective DXF framework. It does not yet certify all splines, hatch topology, nested blocks, all duplicate orientations, visual quality or project-specific design intent.

Phase 2 entry criteria for the next phase are met **within this bounded scope**. Release readiness remains unassessed; no GitHub release or tag action was performed.
