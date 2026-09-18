# Tested environment and anonymized validation

This summary was checked against local execution reports and geometry-comparison JSON dated 2026-09-17. It contains selected observations, not raw private evidence. Packaging did not rerun desktop CAD/modeling tests. Readers cannot reproduce the private test fixtures from this repository alone; this release is a workflow Skill, not a benchmark harness.

## Environment

| Dependency | Observed setup |
| --- | --- |
| OS | Windows; exact OS build not recorded in the selected reports |
| AutoCAD | 2025; COM returned 25.0s |
| Python | 3.12.10 + pywin32; pywin32 version not recorded |
| SketchUp | Desktop 2023 / 23.0.367 |
| SketchUp Ruby | 2.7.2 |
| MCP bridge | Ringo-Sketchup-MCP 1.3.2 |
| Client | Codex CLI native MCP queries; exact Codex version not recorded |

AutoCAD automation required matching process elevation and the versioned `AutoCAD.Application.25` ProgID. Ruby evaluation was enabled temporarily for the tested SketchUp process; persistent enablement was not established.

The local Ringo Node MCP schema was adjusted from homogeneous tuple schemas to fixed-length arrays for vector/color inputs, keeping length and numeric constraints. This was a client-schema compatibility adjustment, not a replacement control layer. No patch is distributed here. Unmodified bridge/client combinations require their own pre-flight. A one-run CLI setting exposed deferred MCP tools during historical verification; desktop session hot reload was not proven. Do not blindly copy historical feature flags into newer clients.

## Earlier bounded checks

- Standard MCP created, inspected, saved, and reopened a 1000 × 500 × 300 mm solid Group with 6 faces and 12 edges.
- A synthetic five-object CAD plan was created/saved/reopened through COM, natively imported, retained as CAD_REFERENCE, modeled from imported edges, and saved/reopened.
- Maximum specified linear/bounding-box check error in that smaller test was `7.275957614183426e-12 mm`. Its 96-segment circle had continuous-boundary deviation `0.5354125236448226 mm`; overall rating remained WARNING.

## 30-case synthetic landscape stress test

This was deliberately constructed synthetic CAD, not a client, school, or internship project. Units were mm and mm². The reported 30 cases include valid geometry, curve regions, blocks, annotations, duplicate lines, gaps, short edges, Z contamination, conflicting semantics, self-intersection, and large-coordinate probes.

| Observation | Verified historical value |
| --- | --- |
| Region Groups in MODEL | 22 |
| Plant/furniture MODEL component instances | 19 |
| Maximum linear positioning error | 4.656612873077393e-10 mm |
| Maximum native sampled curve deviation | 8.457809239320008 mm |
| Maximum refined MODEL sampled curve deviation | 0.1990007735996025 mm |
| Maximum area percentage error | 0.035052716268204824% |
| Maximum absolute area difference | 3473.4488922059536 mm²; different object from percentage maximum |
| Recorded CLEAN operations | 18 |
| Recorded review events | 13; event count, not unique issue groups |
| Isolated invalid geometry | 1 |
| DWG and final SKP save/reopen | Passed within checked scope |
| RAW hash preservation | Passed |
| Overall historical status | PARTIAL |

Linear checks used 32 anchors and 496 relative vector/distance/angle comparisons, with block transforms checked separately. Nine cross-sections per tested curved road, wall, and spline walkway gave maximum width/thickness errors of approximately 0.1972, 0.1990, and 0.1620 mm respectively.

Curve comparisons used bidirectional sampling and a 0.002 mm sampling-reference tolerance. These are observed sampled deviations, not mathematically certified global error bounds. CAD_REFERENCE retained native import geometry; refinement changed MODEL only. Area used actual region/face areas, accounting for holes, rather than bounding-box area.

The importer omitted a 0.01 mm test line and annotations; tested longer short lines surviving does not establish a universal cutoff. Empty/annotation-only layers were not imported; subsequently supplied empty Tags were metadata additions. Known overlaps and unresolved scope kept the overall result PARTIAL. Historical WARNING ratings are preserved even where values satisfy this Skill's newer default area target.

## Compatibility scope

Other versions may work, but are untested by this evidence. Nonuniform/mirrored/dynamic or complex nested blocks, general spline self-intersection, arbitrary face overlap, dense patterned hatches, and arbitrary far coordinates were not established as reliable. All new projects require source-specific PRE-FLIGHT and validation.
