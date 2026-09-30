# v0.2 recovery audit — 2026-09-30

Read-only recovery was completed before source edits. Actual repository is
`C:\Users\33281\Documents\GitHub\Landscape-Agent-Pack`; the chat workspace is an
unrelated unborn `master` repository with untracked prior audit material.

- Initial branch: `codex/v0.2-integration`; working tree clean.
- Initial HEAD: `5ebc8d4d804b48b99e1ab11c23ae9048ae6fbaba`.
- Remote: `origin`, https://github.com/lunxianle666/Landscape-Agent-Pack.git.
- main and local beta tag: `d3295bf58402e84c09800460d86ab74dd9f9a342`.
- Tags: v0.1.0-beta, v0.1.0-rc1, v0.1.0-rc2. No tags changed.
- Recent history: 5ebc8d4, 2304b7c, 1410416, d3295bf, 5bd68c2,
  d3884c9, 81476b2, 4f61fe1, c714399, 107a400, 463fc30, 6a48b66.
- Existing tests: `tests/unit`, `tests/smoke`, `tests/integration`; historical
  reports: `docs/PHASE2_ACCEPTANCE_REPORT.md`, `PHASE3_ACCEPTANCE_REPORT.md`,
  `PHASE4_BRIDGE_WIP.md`; local ignored evidence in `runs/phase2-*`,
  `runs/phase3-*`, `runs/bridge-134445a11574` remains preserved.
- Phase 4 code initially contained contracts/errors and two Ruby modules, but
  no reusable Python transport or save/reopen acceptance runner.
- Real entry: AutoCAD COM fixture -> SketchUp `DefinitionList#import` ->
  native `CAD_REFERENCE`. Ringo JSON-RPC protocol 3 uses newline-delimited
  UTF-8, token authentication, deadlines and session model checks.
- Dependencies actually present: Python 3.12.10, pywin32 312, ezdxf 1.4.4,
  PyMuPDF 1.28.2, SketchUp 23.0.367 / Ruby 2.7.2, external Ringo 1.3.2.
  Installed Ringo has existing local compatibility patches; these were not
  modified or redistributed. Executables verified at local D: paths.
- Initially neither desktop application was running and 9876 was not listening.
  Actual MCP returned ECONNREFUSED. Opening a unique startup SKP and allowing
  startup to finish restored default profile/9876, Ruby capability and socket
  handshake. No reinstall, token disclosure or GUI bypass was used.

Differences from the brief: Phase 2's historical report says mandatory PASS,
with stated environment limitations; WorkBuddy candidate handoff directory is
absent. A filename search under Documents found no HANDOFF_TO_CODEX.md; the
old D:\WorkBuddy_Landscape_Autonomous_Lab path is also absent. Historical audit
recommendations do not establish current candidate acceptance.

The old process exit before SKP save has no preserved crash explanation.
Its causal origin remains unknown; the current successful run does not prove
why that old process exited. The observed current refusal was caused by the
absent process/listener, not an observed socket encoding or importer defect.
