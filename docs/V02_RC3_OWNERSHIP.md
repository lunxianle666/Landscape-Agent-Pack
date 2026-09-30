# RC3 fixture document ownership safety

## Scope and root cause

RC2 source baseline: `3e13d8772c11c58c721c8711d84ce46b8acbbd22`.
The fixture previously dismissed a presumed default document using its empty
FullName, empty ModelSpace and Drawing name. Those properties do not establish
ownership; an existing document can contain PaperSpace entities.

RC3 removes that dismissal. Bridge, shared AutoCAD Core, persistence and
production import/validation implementations are unchanged. RC2 A/B/C production
evidence remains valid; those large tests were not repeated for this fixture fix.

## Ownership model

- Capture pre-test document references before fixture creation, using COM identity
  rather than names, paths or document indices as ownership evidence.
- Refuse fixture creation whenever an existing document is present, including an
  unsaved blank document or the default document of a newly launched application.
  The user must independently save/close existing documents before a live run.
- Record the exact successful `DocumentSession.create` result immediately, before
  fixture writes. The factory explicitly creates the fixture document.
- Before close, require the creation record, the original session/application,
  matching COM identity, absence from baseline, presence in the document collection
  and a clean document. ActiveDocument is only a shared-session safety check, never
  ownership evidence.
- On uncertain identity or dirty state, retain the document and report a cleanup
  warning. A factory exception without a successful creation record does not grant
  ownership over any resulting document.
- Verify that every baseline reference still exists after teardown. A same-name
  replacement is not accepted. Write `ownership-audit.json` in the isolated run.
- `connect(allow_launch=True)` may attach or launch. Neither process attachment nor
  process creation authorizes document cleanup; no application shutdown is added.

Invariant: **Existing pre-test documents survive fixture teardown.**

## Directed regression and live evidence

Ten unit regressions cover A–F plus dirty failure retention, changed references,
attempted baseline adoption and same-name baseline replacement detection.
Mixed-document teardown is exercised independently of the strict build entry
guard, which still refuses a nonempty baseline.

The isolated AutoCAD 2025 live check created eight fixture entities, saved DWG and
DXF, closed the owned document, reopened DWG and read eight entities with INSUNITS
4. A separately runner-created existing document with one PaperSpace line caused
fixture refusal; its COM identity and line handle survived. The runner then saved
and closed its own surrogate. Final document count was zero. No formal project
file was opened or changed.

Local evidence (excluded from Git and distribution):

- `runs/ownership-rc3-live/live-result.json`
- `runs/ownership-rc3-live/owned/ownership-audit.json`
- `runs/ownership-rc3-live/blocked/ownership-audit.json`
- `runs/ownership-rc3-acceptance/` for minimal regressions and merge pre-flight
- `outputs/v02-rc3-build-01/package-result.json` and independent build 02

RC3 uses its own manifest and archive. RC1/RC2 remain tied to their original source
snapshots; neither archive is overwritten or claimed to match the RC3 commit.
Packaging verifies extraction, tamper rejection and critical-file deletion
rejection, with two deterministic builds and exact Git blob correspondence.

This change does not expand CAD entity support, claim full semantic preservation,
upgrade PARTIAL_FRESH_ENV to fresh-machine validation or validate additional
AutoCAD/SketchUp versions. No merge, push, tag or GitHub Release is authorized.
