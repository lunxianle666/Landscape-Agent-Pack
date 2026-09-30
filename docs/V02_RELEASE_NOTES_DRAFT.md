# Landscape Agent Pack v0.2.0 — final release notes

Status: local release preparation; remote publication not performed. The file
name is retained for existing links; this document supersedes the RC1 draft.

## Verified scope

On Windows with Python 3.12.10, AutoCAD 2025, SketchUp Pro 2023 23.0.367 and an
existing locally compatible Ringo 1.3.2, evidence covers:

- AutoCAD Core: explicit owned workspaces/documents, units, bounded COM reads,
  non-replayed writes and save/close/reopen/readback.
- Geometry QA and PDF plotting, including numerical and raster visual checks.
- CAD→SketchUp native DWG import with CAD_REFERENCE, geometry/unit/bounds checks,
  SKP persistence, save/close/disk reopen/readback and failure handling.
- A/B/C three real landscape projects: production full chains
  PASS_WITH_WARNINGS, with separate numeric QA and visual QA.
- Clean SketchUp process restart, Bridge initialization/reconnect and minimum
  E2E; this does not prove Codex desktop discovery/config reload.
- Document ownership safety: explicit fixture creation record and COM identity,
  pre-test baseline preservation, no default/empty-document auto-dismissal.
  Ten ownership tests and an isolated real PaperSpace-document protection check.
- Windows clean checkout, separate Python venv and temporary configuration:
  **PARTIAL_FRESH_ENV**, using existing licensed applications and compatible plugin.

Evidence: [RC2 acceptance](V02_RC2_ACCEPTANCE.md),
[RC3 ownership](V02_RC3_OWNERSHIP.md), [tested environment](TESTED_ENVIRONMENT.md).
Runtime/private production artifacts are excluded from the distribution.

## Capability boundaries

- TEXT / MTEXT / DIMENSION / HATCH do not guarantee complete CAD semantic
  preservation; native imported annotations/fills can be missing or reduced.
- Circle / Arc / bulged polyline use tessellated geometry / partial semantic
  support. Sampled numerical checks are not global topology or curve proofs.
- Wide-line centerline representation does not preserve complete width semantics.
- SPLINE / ELLIPSE / XREF / arbitrary 3D remain unverified and are not declared
  production-supported.
- This is not complete lossless CAD conversion or finished 3D landscape generation.
  CAD_REFERENCE is reference geometry. Technical visual QA is not design approval.
- No pristine-machine installation or all AutoCAD/SketchUp version compatibility
  claim. Unmodified upstream Ringo installation and cross-machine validation remain
  unverified; the pack does not distribute local plugin patches or licensed apps.
- Guard is an explicit call wrapper, not an automatic MCP interception layer.
  Manifest hashes provide integrity checks, not a cryptographic release signature.

## WorkBuddy final source review

| Candidate | Final decision |
|---|---|
| autocad-com-automation | DUPLICATE |
| cad-geometry-qa | REJECT |
| landscape-sheetset-pipeline | DEFER |
| landscape-visual-qa | ACCEPT_WITH_CHANGES |

Recovered candidate source was reviewed. No whole Skill was copied. Visual QA
adopts source-bound evidence and explicit observations, not arbitrary aesthetic
scores or automated design judgement. Sheetset implementation remains deferred.
Missing HANDOFF_TO_CODEX.md is historical provenance, not pending source review.
See [recovered source review](V02_WORKBUDDY_REVIEW.md).

## Official artifact and reproducibility

The release-author workflow runs on clean main after all intended files are staged:

```powershell
py -3.12 -B installer/build-manifest.py --version v0.2.0
py -3.12 -B installer/verify-rules.py --root .
# Run unit, smoke and ownership checks, then commit release preparation.
py -3.12 -B installer/build-v02-candidate.py outputs/v020-build-01
py -3.12 -B installer/build-v02-candidate.py outputs/v020-build-02
```

The existing builder filename is retained; it accepts explicit v0.2.0 metadata.
Official filename: `Landscape-Agent-Pack-v0.2.0.zip`, with `.zip.sha256` sidecar.
Build from the final release-prep commit, never by renaming RC3. Both builds must
be byte-identical and match that commit's tracked Git blobs. Sorted entries and
fixed timestamps make same-runtime builds deterministic. Independent extraction,
manifest checks, tamper rejection and critical-file deletion rejection are required.
Cross-machine archive/compressor determinism is not certified. RC1/RC2/RC3 remain
unchanged and tied to their original snapshots.

Manifest generation is a release-author operation, never a repair for downloaded
integrity failures. ZIP excludes runs, private credentials and production files.
Local preparation does not push, create a tag or publish a GitHub Release.
