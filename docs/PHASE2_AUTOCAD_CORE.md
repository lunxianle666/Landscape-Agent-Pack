# Phase 2 AutoCAD Core and QA Foundation

Development branch: `codex/v0.2-integration`, based on `v0.1.0-beta` commit `d3295bf58402e84c09800460d86ab74dd9f9a342`. This document describes development code only; the v0.1.0-beta release remains unchanged.

## Modules and boundaries

| Module | Responsibility |
|---|---|
| `landscape_agent_pack/result.py` | Agent-independent JSON/Markdown contract and status aggregation. |
| `cad/retry.py` | Bounded retry for idempotent COM reads, with busy/disconnected error classification. Never retry Add/Open/SaveAs/Close. |
| `cad/core.py` | Single COM connection and owned `DocumentSession`; unit, layer, entity, save/export and reopen primitives. |
| `cad/angles.py` | Public Arc angles in degrees; one conversion to radians at COM boundary. Positive CCW sweep across zero; use Circle for a full circle. |
| `cad/annotation.py` | Parameterized, persisted model-space millimetre DIMSTYLE profile and post-reopen readback. |
| `cad/geometry_qa.py` | Objective DXF statistics and configurable anomaly checks. No aesthetic judgment. |

This is a Phase 2 foundation, not a full landscape drawing or CAD→SketchUp system. Plot and PDF objective/visual QA interfaces are deferred; they are **NOT_EXECUTED**, not passed.

## Result contract

Every report has `task_id`, `operation`, `status`, timestamps, `input`, `output`, `checks`, `warnings`, `errors`, `artifacts`, `software`, `software_version`, `environment`, and `metrics`. Each check has `id`, `name`, `mandatory`, `status`, `expected`, `actual`, and `message`.

Check statuses: `PASS`, `FAIL`, `WARN`, `NOT_EXECUTED`, `ERROR`, `SKIPPED`, `MANUAL_INTERVENTION_REQUIRED`. Aggregate: mandatory FAIL/ERROR → FAIL; mandatory manual intervention → MANUAL_INTERVENTION_REQUIRED; mandatory NOT_EXECUTED/SKIPPED → REVIEW_REQUIRED; other warnings/incomplete optional checks → PASS_WITH_WARNINGS; all mandatory PASS → PASS. Zero mandatory checks cannot PASS. JSON, Markdown, console summary and exit code use this same aggregate function.

Top-level `errors` force FAIL and top-level `warnings` turn an otherwise PASS result into PASS_WITH_WARNINGS.

## Lifecycle and ownership

`DocumentSession.create/open` requires an existing explicit `workspace_root` and an empty document collection; `open` accepts only files under that root. All outputs must be new paths under it. `source_path`, `current_path`, `requested_output_path`, name, format, dirty state, ownership and opened-by-automation state are tracked separately. `SaveAs` refreshes metadata and checks the current path; subsequent `Save` is only allowed for a current DWG. A DXF SaveAs is a format/path transition, so the test closes it and reopens the DXF from disk. Close only accepts a clean automation-owned document. Mutations refuse a nonzero `CMDACTIVE` state. A failed creation is uncertain and cannot be replayed without inspection.

The test refuses to mutate when AutoCAD already has any document open. On failure it leaves a dirty owned document open for inspection; it does not discard unsaved content to improve test status. Every run gets `runs/phase2-<unique-id>/`, which is excluded from Git and contains DWG, DXF and reports.

## Process termination audit

Searched repository for `taskkill`, `acad.exe`, `kill process`, `terminate process`, `os.kill`, `.kill(`, `Stop-Process`, `TerminateProcess`, and subprocess calls. The v0.1.0-beta repository has **no AutoCAD kill call**. `installer/environment_probe.py` references `acad.exe` only to discover running processes and installed paths. `tests/smoke/acceptance_v2.py` uses `subprocess.run` for child tests, without killing AutoCAD.

WorkBuddy candidate references global AutoCAD kill in `KNOWN_ISSUES.md:61`, `skills/autocad-com-automation/SKILL.md:251`, the frozen v1 Skill at line 251, and `skills/landscape-sheetset-pipeline/SKILL.md:25`. These are not imported. Phase 2 Core has no process-termination API. Recovery levels: (1) normal COM close after save; (2) close a verified automation-owned document only; (3) a future scoped process termination may be designed only with separately recorded PID, launch/ownership evidence, reason, timeout, action and outcome; (4) if ownership is unknown, report `MANUAL_INTERVENTION_REQUIRED`. No global `taskkill /IM acad.exe /F` or equivalent is allowed.

## DIMSTYLE and version scope

`DimStyleProfile` is explicitly model-space, drawing in millimetres at 1:100. Model values for DIMTXT/ASZ/EXO/EXE/GAP are derived from paper millimetres × scale. `DIMLFAC=1`, `DIMLUNIT=2`, `DIMSCALE=1`, `DIMDEC=0`, `DIMTXSTY=LAP-TEXT`, default closed-filled `DIMBLK=''` with `DIMSAH=0`, non-annotative `DIMANNO=0`. AutoCAD 2025 rejects `SetVariable(DIMANNO,0)`; it is verified as an effective read-only value after `CopyFrom`. A reopened DWG is checked for all variables and actual dimension anonymous-block text height. Other AutoCAD versions need their own acceptance run; no cross-version claim is made.

## Reproduce the isolated acceptance

With AutoCAD 2025 already running and **no drawings open**, and Python 3.12 with pywin32/ezdxf:

```powershell
py -3.12 -B -m unittest discover -s tests/unit -p 'test_v02_core.py' -v
py -3.12 -B tests/integration/autocad_core_live.py
```

The live runner writes a unique `runs/phase2-*/phase2-result.json` and `.md`; it exercises real COM Line/Polyline/Circle/Arc/Text/MText/Dimension, layers, DIMSTYLE, DWG Save/Close/Reopen/SaveAs, DXF SaveAs/Close/Reopen, offline geometry QA, fault injection and mandatory NOT_EXECUTED semantics. It does not touch A/B/C or call SketchUp. A missing bridge or blocked environment is not a PASS.
