# Known limitations

- SketchUp native DWG import discretizes continuous curves. Excellent vertex or bounding-box agreement can coexist with unacceptable error between vertices.
- Very short edges may be dropped. A tested 0.01 mm line was lost; other surviving examples do not define a safe universal threshold. Critical missing boundaries require review or verified equivalent repair.
- Text/MText, dimensions, hatches, and empty/annotation-only layers may not survive import. Read design information in CAD; do not treat annotations or hatches as default face boundaries.
- DWG import may provide edges without faces. Validate topology before face creation, preserve holes, and distinguish actual imported Tags from later metadata additions.
- Ambiguous heights, wall centerlines, overlapping functional regions, suspected duplicate plants, and missing design intent require human review. Layer names alone are insufficient evidence.
- Spline parameters are not always accessible through COM. Control-point envelopes are not necessarily tight curve bounds; sampled curve error is not a certified global Hausdorff bound. Missing parameters block affected reconstruction.
- The stress test covered uniform scale and rotation, not general mirrored/nonuniform/dynamic or complex nested blocks. General curve self-intersection, all partial face overlaps, and patterned hatches were not comprehensively validated.
- The historical model had unresolved overlap/review items and an overall PARTIAL result. Lightweight planting/furniture placeholders are not detailed botanical or fabrication assets.
- AutoCAD COM is Windows-oriented and can require matching process permissions/versioned ProgIDs. This repository does not install desktop applications, resolve licensing, or supply a control bridge.
- The tested MCP setup included a local schema adjustment and temporary Ruby enablement. Bridge presence alone does not establish connection, importer availability, or authorized Ruby execution.
- MCP timeouts do not prove an operation failed to execute. Inspect actual state before retrying; stale session references must be refreshed.
- Each new DWG requires PRE-FLIGHT. Versions and configurations outside the observed environment are potentially compatible but untested. Save success alone is insufficient: reopen and compare.
- Default tolerances are acceptance targets, not unconditional output guarantees. Report measurement scope and uncertainty; keep useful checkpoints when required scope cannot pass.
