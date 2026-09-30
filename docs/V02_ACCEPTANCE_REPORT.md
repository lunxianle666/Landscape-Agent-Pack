# v0.2 integration acceptance — 2026-09-30

**Runtime result: PASS_WITH_WARNINGS. Formal publication decision: NOT READY.**
Phase 4's native fixture and disk persistence are now accepted on this machine.
WorkBuddy source review remains DEFER because the handoff is absent. Main,
stable beta tag and published release were not modified.

## Root cause and changes

Current ECONNREFUSED was caused by no running SketchUp/listener. Starting an
owned SKP and allowing the installed Ringo extension to finish loading restored
authenticated protocol 3 communication. The earlier WIP had imported CAD but
had no complete save/reopen acceptance path. Its old process exit before Save
has no available causal evidence; it is not retrospectively diagnosed.

Added `bridge/client.py` for bounded JSON-RPC, authentication, framing,
request/response identity and uncertain mutation outcomes; `persistence.rb`
for safe Save/File New/Open; `validation.py` for fixture geometry/curve and
disk persistence checks. Bridge tolerances reject NaN/Infinity; fixture
preflight uses existing bounded COM read retry. Phase 2/3 core was not rewritten.
Geometry validation uses explicit exceptions and remains enabled with Python -O.

A development run incorrectly assumed File New creates a new Ruby Model object.
SketchUp 2023 reused the wrapper/model_id, despite clearing the actual model.
Closure now checks empty path and disappearance of CAD_REFERENCE. Another
development regression called an unsupported discard_changes argument; this
was corrected by saving plot settings to a new owned DWG copy before closing.
Both failed runs and their artifacts remain preserved. A 0.1-second timeout
initially expired during a normal server read; the negative test now establishes
the session first and times out a deliberately slow read-only Ruby operation.

## Actual tests and evidence

| Scope | Result | Evidence under local ignored runs/ |
|---|---|---|
| Phase 2 real AutoCAD | PASS, 13 mandatory checks | phase2-7675b3f07354/phase2-result.json |
| Phase 3 real PDF delivery | PASS_WITH_WARNINGS, 24 mandatory checks | phase3-1cb8d9b34fb2/phase3-result.json |
| Initial Phase 4 accepted fixture | PASS, native geometry + SKP disk readback | phase4-d3c2562c69cf/phase4-result.json |
| Single-source full chain with live failures | PASS_WITH_WARNINGS | 全链路-4ff86059f4c4/full-chain-result.json |
| Final full chain after explicit validation hardening | PASS_WITH_WARNINGS | 全链路-823b93eb130a/full-chain-result.json |
| Unit tests | 21 PASS (14 existing + 7 bridge) | tests/unit/ |
| Existing smoke regression | 19 PASS (includes 8 integrity mutations) | tests/smoke/ |
| Beta manifest before documentation edits | FINAL: PASS | verified during recovery/regression |

AutoCAD actually launched through COM, created DWG/DXF and reopened DWG;
SketchUp actually launched with the owned template copy. Ringo TCP communication
performed handshake and authenticated requests/responses with recorded request
IDs in rpc-history.json; neither token nor Ruby source is in that history.
Native DefinitionList#import created CAD_REFERENCE with actual CAD layer Tags.
SKP was saved under a Chinese filename in a Chinese directory, model cleared
using File New, reopened from disk, then read numerically. This is clean model
reopen rather than a SketchUp process restart.

Fixture: 8 CAD entities: 3 lines (one at Z=1200), an open polyline, two closed
rectangles, circle and arc. SU: one root native component, 147 edges, 96-edge
circle, 38-edge arc. BBox approximately [0,0,0]–[13000,5000,1200] mm; four CAD
Tags retained. Display units mm. Key-coordinate error 9.094947017729282e-13 mm;
circle chord deviation 0.40155939272574415 mm; arc 0.5167925164038252 mm, under
declared 1.0 mm curve tolerance. Reopened edge-coordinate change 0.0 mm;
edge counts, Tags, transforms, source markers and curve types/counts unchanged.

Real failures: non-listening bound TCP endpoint -> connection refusal; illegal
Ruby code parameter -> -32602; expired request -> -32003; real Ruby sleep(0.8)
with 0.3-second client timeout -> bounded TimeoutError, followed by successful
model read. Unit-only failure transport tests additionally prove mutation
timeout/mismatched response -> OutcomeUnknown with exactly one submission.
Unit transport tests are not used to certify SketchUp modeling.

PDF and SU exported PNGs were actually inspected. The fixture PDF shows the
expected rectangles, circle, arc and open/control lines without apparent crop;
SU image shows native planar geometry plus the raised line. This is fixture
visibility inspection; formal landscape drawing/design review remains optional
NOT_EXECUTED, preserving Phase 3/full-chain warnings.

## Packaging and governance

Current branch manifest is generated explicitly as v0.2.0-rc1 over Git-tracked
files. Runtime evidence/config/secrets are excluded. The stable beta's manifest
and artifacts remain in its unchanged Git tag. Candidate ZIP rebuilds are
deterministic, independently extracted and integrity-checked; content tamper
and critical-file deletion must fail. Package reports/checksums are local under
outputs/v02-build-*/. No package or tag has been published.

## Remaining issues

- WorkBuddy handoff/candidate source missing: all four named capabilities DEFER;
  no candidate absorption or current source inventory completed.
- Formal design visual review NOT_EXECUTED; fixture visibility is not that review.
- Pristine Ringo/cross-machine installer/client reload, other AutoCAD/SU versions,
  DXF native import, arbitrary CAD/splines/blocks/topology and A/B/C production
  regression remain unverified. Native reference creation is the accepted scope.
- Native import/COM can block within desktop software. A Python timeout bounds
  waiting but cannot safely force-cancel running Ruby or COM. No global kill.

The runtime chain is suitable for continued integration review; this report
does not authorize merging main or publishing a formal v0.2 release.
