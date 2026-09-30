# v0.2 bridge architecture, installation and workflow

This integration adds an authenticated Python Ringo protocol 3 client around
the existing native CAD importer. It never redraws DWG from guessed geometry.
`contracts.py` validates isolated paths, source hash, mm units, origin and
finite positive tolerances. `native_import.rb` imports into an owned startup
SKP; `sketchup_session.rb` reads real nested edges/curves; `persistence.rb`
saves, executes File New, and reopens the on-disk SKP. `validation.py` checks
the explicit eight-entity fixture and before/after coordinates.

## Tested installation

Use an isolated Python 3.12 environment on Windows and install
`requirements-v02-dev.txt`. A licensed AutoCAD desktop and licensed SketchUp
Pro are required. Install/configure external Ringo separately and reload the
SketchUp plugin. LAP does not install or patch the plugin. The tested local
environment uses AutoCAD 2025 and SketchUp Pro 2023 23.0.367/Ringo 1.3.2.
Other machines, AutoCAD versions and a pristine upstream Ringo installation
remain untested.

The client reads an explicit `--config`, then `SKETCHUP_MCP_CONFIG`, otherwise
`%APPDATA%/RingoSketchUpMCP/config.json`. Port comes from configuration or
`SKETCHUP_PORT`; it is not hardcoded in the client. Do not expose config tokens.
Launch SketchUp with `SKETCHUP_ENABLE_RUBY_EVAL=1` only in the intended process
environment, or enable trusted Ruby in that existing bridge configuration.
Confirm bridge.status profile identity/port and model.get_info before mutation.

## Reproduction

In an empty AutoCAD document collection, with SketchUp displaying a unique,
saved, automation-owned startup SKP inside `runs/`, execute:

```powershell
py -3.12 -B tests/integration/bridge_fixture_cad.py runs/<unique-workspace>
py -3.12 -B tests/integration/bridge_live.py runs/<unique-workspace>
```

The workspace must contain `startup.skp`; inputs and output may not exist
outside that workspace. Existing outputs are rejected. For the same-source
CAD build/reopen, geometry QA, PDF plotting and SU persistence regression:

```powershell
py -3.12 -B tests/integration/full_chain_live.py <path-to-template.skp>
```

Full-chain startup switching is permitted only from a clean saved test model
under `runs/`; it refuses a dirty/non-test model. Every run has a fresh folder.
Real reports and artifacts remain locally under ignored runs; unit transport
servers test failure behavior only and are never SketchUp acceptance evidence.

## Troubleshooting and failure semantics

- ECONNREFUSED: verify process, real opened model, extension load and listener.
  Startup on this machine took several minutes. Do not reinstall or replay CAD
  mutations merely because the process initially has no listener.
- Unauthorized: check selected config/profile. Never print tokens or bypass
  authentication.
- Submitted mutation timeout/disconnect/protocol failure: OutcomeUnknown;
  inspect bridge status and actual model before any further mutation. No replay.
  Read-only calls have an absolute timeout; running Ruby cannot be force-cancelled.
- Save/Close/Open must run outside Ruby's default mutation transaction. They
  still count as mutations for transport uncertainty handling.
- File New in SketchUp 2023 reuses Model/object ID and Ringo model_id. Closure
  is verified by empty path and disappearance of CAD_REFERENCE, then exact
  disk reopen/path/readback. IDs alone cannot establish closure.
- A failed CAD plot leaves its owned dirty document for inspection. Successful
  full-chain plotting saves settings to a new copy, preserving input CAD hash.

## Supported and experimental scope

The real eight-entity mm DWG fixture, native tags, mixed Z, circle/arc
discretization, Chinese paths and SKP disk readback passed on this machine.
Circle/arc chord bounds are calculated for circular fixture segments; this is
not arbitrary spline, topology, global Hausdorff, nested-instance or structural
verification. CAD_REFERENCE is native imported edge geometry. No building
extrusion or inferred landscape design was added. DXF native import, arbitrary
large DWGs and cross-version/client matrices remain Experimental / NOT TESTED.
A/B/C production reference imports and technical visual transfer review are
accepted with semantic warnings in V02_RC2_ACCEPTANCE.md; this is not independent
design approval or complete topology verification.

Normal reopen is model-level File New plus disk open. A separate RC2 process
restart passed with a new SketchUp PID, listener and Bridge instance.
AutoCAD's same-process COM calls and native import can still block internally;
client timeout bounds waiting and retains uncertain outcomes, not safe force
termination. Other AutoCAD ProgIDs can be supplied to core.connect; the current
live acceptance scripts intentionally target the tested Application.25 profile.

Official File New/Open behavior: https://ruby.sketchup.com/Sketchup.
