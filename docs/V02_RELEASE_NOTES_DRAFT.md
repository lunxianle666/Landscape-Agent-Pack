# v0.2.0-rc1 release notes draft — unpublished

Status: **local review candidate; formal publication NOT READY**.

Real AutoCAD fixture -> geometry QA -> PDF plot -> SketchUp native DWG import
-> SKP save/File New/disk reopen/readback now passes on Windows with AutoCAD
2025 and SketchUp Pro 2023 23.0.367. Client rejects invalid responses, bounds
waiting, and retains uncertain mutation outcomes without replay. Chinese
workspace and output names were exercised. See V02_ACCEPTANCE_REPORT.md.

WorkBuddy candidate source is unavailable and review remains DEFER. Formal
design review, arbitrary production drawings, cross-machine installation,
unpatched Ringo and cross-version support are not certified. The published
v0.1.0-beta remains the stable baseline; no new release/tag has been created.

Rebuild from this integration checkout after staging all intended source files:

```powershell
py -3.12 -B installer/build-manifest.py --version v0.2.0-rc1
py -3.12 -B installer/verify-rules.py --root .
py -3.12 -B installer/build-v02-candidate.py outputs/<fresh-build-directory>
```

Manifest generation is a release-author operation, never a repair for failed
installed integrity. The explicit version and tracked file list prevent old
beta labeling and inclusion of runs/private configuration. The ZIP has fixed
timestamps/order and hashes of actual file bytes; repeat builds on this checkout
must have identical SHA256. Cross-machine line-ending normalization is not
certified. Candidate creation does not publish or install it.
