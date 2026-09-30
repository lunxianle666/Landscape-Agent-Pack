# v0.2 RC2 acceptance — 2026-09-30

**PASS_WITH_WARNINGS / MERGE_READY candidate**, limited to the tested native
CAD reference workflow. Baseline: `fc9b21f1228021a29c6097576081b5df7eaa592f`,
branch `codex/v0.2-integration`. Bridge core has no diff against that baseline.
No main merge, remote push, tag or GitHub release; RC1 is retained.

## WorkBuddy

Verified archive source recovered; usable HANDOFF_TO_CODEX.md remains absent.
See [source review](V02_WORKBUDDY_REVIEW.md): COM DUPLICATE, geometry QA REJECT,
sheetset DEFER, visual QA ACCEPT_WITH_CHANGES. No candidate skill copied in.

## Production CAD and persistence

Formal DWGs were copied to isolated `runs/rc2-acceptance/{A,B,C}`. Final
reproducible imports: `production-rerun/{A,B,C}`. Source DXF numeric QA, real
PDF plot, native DWG import, SKP save, File New, disk reopen and readback all
executed. Source hashes checked before/after and unchanged.

| Drawing | Source entities | SU edges / faces / components | Samples | Result |
|---|---:|---|---:|---|
| A-01 街角口袋公园 景观总平面图 | 392 | 6655 / 0 / 1 | 18723 | PASS_WITH_WARNINGS |
| B-01 咸宁现代居住区中庭 景观总平面图 | 117 | 5917 / 0 / 17 | 7575 | PASS_WITH_WARNINGS |
| C-01 滨水湿地公园 景观总平面图 | 249 | 3777 / 7 / 1 | 5502 | PASS_WITH_WARNINGS |

B covers medium complexity with 16 block references; A the largest entity
count and detailed curves; C the largest extents and seven wide polylines.
Entity counts are not expected to match between formats. Input INSUNITS=4,
actual SU units code=2 (mm). Actual native world-space bounds in mm:
A [-3500,-6500,0,51000,29000,0], B [-110,-110,0,44110,30110,0],
C [-16000,-23500,0,128000,78000,0]. B source bounds include omitted annotation
extents; this difference is disclosed, not called coordinate drift.

Formal source SHA256:

- A: `ecfa7ae940010b7e8d773bc3c3f1b93f5176bcb5db2b798205a7241f275714f2`
- B: `a6609f9b9b84231aec98c80fbd5f17eb5ecb57443bf36fc3fc5bf9e15e4a09c1`
- C: `149d0d2b8366565091c14f122aeb753ae43c76fe4ead301c91cf2f2593c3185b`

A/B maximum sampled source-to-native-edge distance: 0.642496/0.856661 mm,
within declared 1 mm tolerance. C raw maximum 1500 mm on 18 wide-polyline
centerline segments remains a warning. Import represents these as contours:
120 independent boundary samples match within 1.5e-11 mm; ordinary C samples
within 2.94e-11 mm. All three before/after edge readbacks have zero measured
coordinate change at 1e-6 mm persistence tolerance; counts/tags/metadata pass.

| Entity / capability | Support judgement |
|---|---|
| LINE, straight zero-width LWPOLYLINE | SUPPORTED within tested native reference geometry |
| CIRCLE, ARC, bulged LWPOLYLINE | PARTIALLY_SUPPORTED: sampled tessellated edges pass; analytic semantics lost |
| INSERT | PARTIALLY_SUPPORTED: tested nested instances/world transforms retained; block-attribute semantics not proved |
| Straight constant-width LWPOLYLINE | PARTIALLY_SUPPORTED: contours match; original centerline/width semantics lost |
| TEXT, MTEXT, DIMENSION, HATCH | UNSUPPORTED as preserved CAD semantics; incidental imported graphics are not semantic support |
| SPLINE, ELLIPSE, proxy/XREF, variable/curved widths, arbitrary 3D objects | UNSUPPORTED by this acceptance contract; no production support evidence |

Sampling is one-way against actual native edges. Coincident edges can mask
missing coincident entities. No bijection, complete topology/closed-region or
global Hausdorff proof. No finished 3D landscape model is promised. Ordinary
supported-geometry outliers fail the new harness; width loss never gets PASS.

## Actual visual QA

CAD PDF rasters and SU top views inspected for A/B/C; C axon also inspected.
No blank output, extreme scale, huge drift, new obvious fragmentation or major
loss of supported outlines observed. Existing source overlaps remain. CAD
aggregate **VISUAL_PASS_WITH_WARNINGS** (A/C individually VISUAL_PASS; B
Model-space plot excludes its paper-space title). SU **VISUAL_PASS_WITH_WARNINGS**:
annotation/hatch loss is visible; these are native references, not finished 3D.
Technical transfer review does not constitute independent design approval.

Additional A2 isolated PDFs use A/B 1:100 and C 1:250. Actual PDF boundary-vector
lengths: 359.9815/439.9915/287.9937 mm versus 360/440/288 mm expected. Initial
line-only extraction falsely selected shortened dimension lines for B/C;
retained diagnostics document correction to PDF quad boundary edges.
Numeric QA and visual QA remain separate. `{A,B,C}/{cad,sketchup}-visual-review.json`
bind viewed raster and source artifact SHA256. Private project files/config
remain in ignored runs and are excluded from the candidate.

## Cold restart

Python clients closed; clean owned model confirmed before graceful Sketchup.quit.
Old PID 27788 exited, no SketchUp process/9876 listener remained. New PID 30080
started with isolated authenticated config and process-local trusted Ruby.
Bridge startup log: Ringo 1.3.2/protocol 3; new instance
`424795bb-a414-4990-87e8-05dbf8a8a07b`, localhost 9876 owned by 30080.
Reconnect and new fixture save/close/reopen/readback: PASS, Phase4 16 checks.
Evidence: `cold-restart-final.json`, `cold-e2e/phase4-result.json`, token-free
bridge event log. Codex desktop itself was not restarted: this proves Python
test-client and SU process restart, not desktop discovery/config reload.

## Fresh environment

**PARTIAL_FRESH_ENV**: new `D:/lap-rc2-fresh-20260930/venv`, clean local
`checkout-rc2`, temporary config and new Python client processes. Same existing
licensed AutoCAD/SketchUp and compatible local Ringo; no pristine-machine or
unmodified-upstream-plugin installation claim.

RC1 clean clone exposed EOL conversion breaking 57 hashes, missing mcp dev
dependency, and a full-chain assumption that runs already exists. Minimal fixes:
.gitattributes preserves exact committed bytes, mcp/numpy pinned, missing parent
created. Integrity rejection is unchanged. Clean RC2 clone integrity PASS;
24 unit/19 smoke PASS; fresh AutoCAD MCP discovery, creation, duplicate prevention,
DWG save/close/reopen and existing-document protection PASS. Fresh minimum full
chain PASS_WITH_WARNINGS solely for its unreviewed visual placeholder. Evidence:
`fresh-environment.json`, `fresh-live-smoke`. INSTALL_WINDOWS now provides exact
source workflow commands and states licensed/plugin prerequisites.

## Regression and Phase3 warning reassessment

| Gate | Result / local evidence |
|---|---|
| Phase2 | PASS, runs/phase2-1137d7bc81c7, 13 checks |
| Phase3 numerical/lifecycle/failure | PASS, runs/phase3-2973c500e89c, 24 required checks |
| Phase3 reviewed | PASS, phase3-reviewed-result.json, all seven PDF rasters inspected |
| Phase4 | PASS, 16 checks in cold-e2e and latest full chain |
| Fixture full chain reviewed | PASS, runs/全链路-c1d13d3cb185/full-chain-reviewed-result.json |
| Production full chain | PASS_WITH_WARNINGS A/B/C; semantic warnings retained |
| Unit / Smoke | PASS, 24 / 19 tests, source and clean clone |
| Fresh live MCP smoke | PASS; SU independently verified by fresh full chain |
| Failure cases | PASS: auth/protocol/timeout/disconnect tests; actual expired deadline, invalid Ruby, closed endpoint, uncertain mutation timeout/recovery; PC3/path/overwrite/blank PDF |

Raw Phase3/full-chain reports remain PASS_WITH_WARNINGS with NOT_EXECUTED
placeholders. Separate reviewed results bind actual viewed images and retain
all other checks/warnings. No raw warning deleted. Fresh run retains its own
unreviewed placeholder. Visual review cannot remove semantic production warnings.

## Packaging and remaining scope

Only v0.2.0-rc2 is built in new `outputs/v02-rc2-build-{01,02}` directories.
Manifest-only sorted ZIP/fixed timestamps, independent extraction integrity,
tamper rejection and critical deletion rejection are mandatory. Actual hash and
byte equality are recorded in package-result.json and local packaging-summary.
RC1 is untouched. Candidate is for merge review; publication remains unperformed.

Remaining: unsupported CAD semantics, sampled geometry coverage, pristine-machine
and upstream-plugin installation, Codex desktop reload/discovery. Cross-version
compatibility remains outside requested scope. Missing usable WorkBuddy handoff
does not erase recovered source review. No unresolved mandatory runtime FAIL.
