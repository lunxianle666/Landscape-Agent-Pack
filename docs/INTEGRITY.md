# Source and installed-rule integrity contract

## Snapshot identity and documentation maintenance

The official v0.2.0 tag resolves to `ac378d84ce4bbb9489ee4664b0db3e498e0359fa`.
Its [published ZIP and checksum](https://github.com/lunxianle666/Landscape-Agent-Pack/releases/tag/v0.2.0)
remain fixed. Later main/PR documentation snapshots have their own file hashes;
the retained `release_version: v0.2.0` identifies the code baseline, not byte
identity with the original archive. Record the Git commit when citing a snapshot.
Do not mix its manifest with another checkout or the published ZIP.

For authorized source maintenance, stage all intended files (including new docs),
then run the existing maintainer tools:

```powershell
py -3.12 -B installer/build-manifest.py --version v0.2.0
py -3.12 -B installer/verify-rules.py --root .
```

Commit the updated `manifest.json` and `SHA256SUMS.txt` with the documentation.
All tracked files remain covered; mandatory critical files and tamper/deletion
rejection remain unchanged. This operation does not publish a release, rebuild
official assets or justify regenerating a downloaded failing manifest. Do not
distribute a post-release docs snapshot under the existing official ZIP name.

## Verification and installer behavior

Run `python installer/verify-rules.py` before installation. Installed rules: `python installer/verify-rules.py --root <installation>/pack-rules --packed`.

The release manifest records schema, version, relative path, SHA-256, type, critical flag and required directories. Missing/malformed manifest, omitted mandatory rules, missing directories, missing files, unreadable files, and hash mismatches fail closed. Output names the failed path and reason; exit 1 is failure. Extra unrelated files are ignored. Installation refuses a failed source check; diagnostics propagate installed integrity failures to their summary and exit status.

The installed rule manifest uses release hashes, not hashes of potentially modified destination content. A corrupt existing installation is preserved, not silently repaired on repeat install. Different installed versions require a separate installation root. Identical Skills are reused; differing user Skills are preserved, with the candidate staged separately and explicitly marked for manual review. Installed rule manifests currently cover the six runtime rule documents; source manifests additionally cover Skills, guards, installer, and config examples. Generated client config fragments contain machine-specific values and are local artifacts, not public release files.

This is integrity detection, not signed provenance: coordinated malicious replacement of files, verifier and manifest is outside its trust boundary. A trusted externally obtained ZIP digest is required. `build-manifest.py` is a maintainer build tool only, never an installation repair command.

Installer writes only its runtime, staged Skill, rules and evidence/config fragments. It never replaces client config. Failure retains those paths for diagnosis and prints possible writes; automatic transaction rollback is not yet implemented. No automated client merge or reload is claimed. Review and back up client config before manual merge; do not overwrite the entire file. Fresh Windows, elevation mismatches, nonstandard Python discovery and offline dependency installation remain release gates.
