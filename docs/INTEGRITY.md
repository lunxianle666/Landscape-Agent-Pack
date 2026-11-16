# Source and installed-rule integrity contract

## Snapshot identity and candidate packaging

The official v0.2.0 tag resolves to `ac378d84ce4bbb9489ee4664b0db3e498e0359fa`.
Its published ZIP and checksum belong to that snapshot. The integrated source
has its own version, `v0.2.1-dev`, and its own manifest and ZIP name.
Record the Git commit when citing or packaging a snapshot. See the
[published Release](https://github.com/lunxianle666/Landscape-Agent-Pack/releases/tag/v0.2.0).

Stage all intended source files, generate the candidate manifest and stage the
two resulting files with the source changes:

```powershell
py -3.12 -B installer/build-manifest.py --version v0.2.1-dev
py -3.12 -B installer/verify-rules.py --root .
git add -- manifest.json SHA256SUMS.txt
```

After committing, run `py -3.12 -B installer/build-v02-candidate.py outputs/v021-dev-build`
with a fresh output path. Compare two builds, the SHA-256 sidecar, and all
archive members with the committed Git tree. Obtain a new trusted copy when
installation verification fails.

## Verification and installer behavior

Run `python installer/verify-rules.py` before installation. Installed rules: `python installer/verify-rules.py --root <installation>/pack-rules --packed`.

The release manifest records schema, version, relative path, SHA-256, type, critical flag and required directories. Missing/malformed manifest, omitted mandatory rules, missing directories, missing files, unreadable files, and hash mismatches fail closed. Output names the failed path and reason; exit 1 is failure. Extra unrelated files are ignored. Installation refuses a failed source check; diagnostics propagate installed integrity failures to their summary and exit status.

The installed rule manifest uses release hashes, not hashes of potentially modified destination content. A corrupt existing installation is preserved, not silently repaired on repeat install. Different installed versions require a separate installation root. Identical Skills are reused; differing user Skills are preserved, with the candidate staged separately and explicitly marked for manual review. Installed rule manifests currently cover the six runtime rule documents; source manifests additionally cover Skills, guards, installer, and config examples. Generated client config fragments contain machine-specific values and are local artifacts, not public release files.

This is integrity detection, not signed provenance: coordinated malicious replacement of files, verifier and manifest is outside its trust boundary. A trusted externally obtained ZIP digest is required. `build-manifest.py` is a maintainer build tool only, never an installation repair command.

Installer writes only its runtime, staged Skill, rules and evidence/config fragments. It never replaces client config. Failure retains those paths for diagnosis and prints possible writes; automatic transaction rollback is not yet implemented. No automated client merge or reload is claimed. Review and back up client config before manual merge; do not overwrite the entire file. Fresh Windows, elevation mismatches, nonstandard Python discovery and offline dependency installation remain release gates.
