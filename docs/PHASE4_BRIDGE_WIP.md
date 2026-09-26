# Phase 4 CAD → SketchUp Bridge — WIP freeze

**Status: `EXPERIMENTAL / BLOCK_BRIDGE / NOT ACCEPTED`.** This commit preserves experimental source code. It does not certify the Bridge or change the Phase 2/3 stable checkpoint.

An isolated eight-entity millimetre DWG/DXF fixture was created under `runs/bridge-134445a11574/`. SketchUp 2023 actually imported the DWG through its native `Sketchup::DefinitionList#import` API during an exploratory call; the CAD was not redrawn in Python or Ruby. The pre-save snapshot observed SketchUp millimetre display units, a `CAD_REFERENCE` component, CAD layer names mapped to Tags, and a bounding box of approximately `[0, 0, 0]–[13000, 5000, 1200]` mm. Its Circle had 96 edges and Arc had 38 edges. The snapshot is an observation before persistence, not an acceptance result. The checked-in `native_import.rb` is WIP code and has not itself completed a full accepted run.

**Required acceptance remains incomplete:** SKP Save, graceful Close, Reopen, and numerical validation after Reopen were not executed. The SketchUp test process exited before saving the imported model; no imported SKP exists in the isolated run directory. Coordinate and curve errors after Reopen, DXF native import, failure injections, and a complete Bridge Result have not passed. Native import success alone cannot produce Phase 4 PASS.

The experiment files in `runs/`—DWG, DXF, template SKP copy, fixture JSON, probe snapshot, backup and logs—are Git ignored and are not part of this WIP commit. `main`, `v0.1.0-beta`, and the accepted Phase 2/3 code remain unchanged. Do not use this WIP as a production Bridge or proceed to SketchUp Build from it.
