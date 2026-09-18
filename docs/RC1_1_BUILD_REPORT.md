# RC1.1 review build

Verdict: READY_FOR_GITHUB_REVIEW. This is a local review candidate, not a published GitHub Release.

## Creation false errors
AutoCAD MCP Pro 1.5.1 creates each entity successfully, then reads entity.Color while building its response. On this AutoCAD 2025 generated COM wrapper, the exposed property key is lowercase color. The same handle returns 256 via generated lowercase color and dynamic Color; generated uppercase Color raises an attribute error. This is a response extraction failure after the mutation, not failed creation. Original errors and MCP isError=true remain in tests/evidence/creation-reproduction.json. Upstream code was read only; no source copy, modification, fork or cache reset.

| Case | Entity count | Handle | Guard result |
|---|---|---|---|
| Line | 0 -> 1 | 7F | SUCCESS_WITH_FALSE_ERROR |
| Polyline | 0 -> 1 | 7F | SUCCESS_WITH_FALSE_ERROR |
| Circle | 0 -> 1 | 7F | SUCCESS_WITH_FALSE_ERROR |
| Text | 0 -> 1 | 7F | SUCCESS_WITH_FALSE_ERROR |
| Block | 0 -> 1 | 83 | SUCCESS_WITH_FALSE_ERROR |
| Hatch | 0 -> 1 | 7F | SUCCESS_WITH_FALSE_ERROR |
| Dimension | 0 -> 1 | 7F | SUCCESS_WITH_FALSE_ERROR |

## Guard
Own implementation snapshots the authorized document and ModelSpace, invokes creation once, then reads count, new handles, existing-entity stability and requested key geometry. Exactly one matching new entity plus an upstream error yields SUCCESS_WITH_FALSE_ERROR. Session/operation-ID replay returns cached evidence with zero mutation calls. Uncertain outcomes require review and prohibit automatic retries. All seven live replay checks and eleven automated decision/document-safety tests passed.

Guard must be explicitly called; direct upstream MCP calls bypass it. Replay prevention is in-process, not persistent across restarts. Hatch coverage is a simple rectangular boundary; rotated dimension coverage verifies measurement, rotation, normal and text projection, not full endpoint/style semantics. No general drawing correctness guarantee is made.

## Clean installation
A cache-free archive was extracted into a new directory with a separate fresh Python venv and isolated Skill target. The default installer installed the pinned upstream package from PyPI, generated local MCP fragments, completed handshake/discovery, created a closed 1000 x 500 mm rectangle and diameter 200 mm circle, saved AC1032 DWG, closed, reopened and verified two entities, coordinates, area, perimeter, circle and INSUNITS=4. Both creation errors were retained and classified by Guard; operation-ID replay added no entities. Close can also return an RPC error after closing: document disappearance was checked without repeating the close mutation. No existing drawing was closed or modified.

SketchUp: SKIPPED_NOT_RUNNING. It was not started or connected. Optional skipping does not fail the AutoCAD main chain. No Layout, PDF, screenshots or complex landscape drawing tests were run.

## Publication boundary
Original 88 protected files remain unchanged. autocad-dwg-redraw source is excluded for lack of confirmed licensing; its directory contains only our provenance note. AutoCAD MCP Pro and Ringo source are not bundled. No software binaries, Python environment, site-packages, node_modules, caches, local configs, tokens, user-name paths or test DWGs are included. Dependency license metadata is an inventory, not blanket legal approval; dependencies are installed separately and resolver versions may drift. Existing historical PARTIAL/WARNING evidence remains historical.

Public evidence is tests/evidence/creation-reproduction.json and rc1.1-summary.json. Raw installer logs, configurations, absolute paths and DWG are private review artifacts. Final archive contents and checksum inventory are verified after the privacy scan. Archive SHA256 is provided beside the ZIP to avoid self-referential checksums.
