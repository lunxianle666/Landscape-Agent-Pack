"""Create the isolated Phase 4 CAD fixture with real AutoCAD COM.

The script refuses an existing user document and never overwrites an output.
"""
import argparse
import hashlib
import json
import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from landscape_agent_pack.cad.core import DocumentSession, connect, OwnershipError
from landscape_agent_pack.cad.retry import read_with_retry


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def document_references(app):
    """Enumeration indices are used only to capture references, never ownership."""
    count = int(read_with_retry(lambda: app.Documents.Count))
    return tuple(read_with_retry(lambda i=i: app.Documents.Item(i)) for i in range(count))


def same_document(a, b):
    # COM wrappers can be reacquired after SaveAs; compare their COM identity.
    # In non-COM test doubles, require the identical object, not its name/path.
    if hasattr(a, '_oleobj_') and hasattr(b, '_oleobj_'):
        return a._oleobj_ == b._oleobj_
    return a is b


class FixtureDocuments:
    """Invocation-scoped creation record. Process attachment grants no ownership."""
    def __init__(self, app):
        self.app = app
        self.baseline = document_references(app)
        self.session = None
        self.owned_document = None
        self.closed = False

    def create(self, run):
        session = DocumentSession.create(self.app, workspace_root=run)
        # Record the exact factory result immediately, before any fixture writes.
        self.session = session
        self.owned_document = session.document_object
        self._prove_owned()
        return session

    def _prove_owned(self):
        if self.session is None or self.owned_document is None:
            raise OwnershipError('No successful fixture creation record')
        if self.session.app is not self.app or not self.session.opened_by_automation:
            raise OwnershipError('Fixture session identity/ownership changed')
        if any(same_document(self.owned_document, doc) for doc in self.baseline):
            raise OwnershipError('Factory returned a pre-existing document')
        if not same_document(self.session.document_object, self.owned_document):
            raise OwnershipError('Fixture document reference changed')
        if not any(same_document(self.owned_document, doc) for doc in document_references(self.app)):
            raise OwnershipError('Created fixture document is no longer present')

    def verify_baseline(self):
        current = document_references(self.app)
        if not all(any(same_document(old, doc) for doc in current) for old in self.baseline):
            raise OwnershipError('Existing pre-test documents did not survive fixture teardown')

    def close_owned(self):
        self._prove_owned()
        self.session.refresh()
        self._prove_owned()
        if self.session.dirty:
            raise OwnershipError('Owned fixture document is dirty; retained for inspection')
        self.session.close()
        self.closed = True
        self.verify_baseline()

    def cleanup(self):
        issues = []
        if self.session is not None and not self.closed:
            try:
                self.close_owned()
            except Exception as exc:
                issues.append(str(exc))  # Do not discard or guess a different target.
        baseline_survived = False
        try:
            self.verify_baseline()
            baseline_survived = True
        except Exception as exc:
            issues.append(str(exc))
        if self.owned_document is None:
            try:
                if any(not any(same_document(doc, old) for old in self.baseline)
                       for doc in document_references(self.app)):
                    issues.append('Unrecorded documents present; ownership unknown; retained')
            except Exception as exc:
                issues.append('Document inventory unavailable: ' + str(exc))
        return {'baseline_documents': len(self.baseline),
                'creation_recorded': self.owned_document is not None,
                'owned_document_closed': self.closed,
                'baseline_survived': baseline_survived,
                'cleanup_warnings': issues}


def build(run):
    run = Path(run).resolve(strict=True)
    app = connect(allow_launch=True)
    documents = FixtureDocuments(app)
    try:
        # Even a newly launched application's default document is unowned.
        if documents.baseline:
            raise OwnershipError('AutoCAD contains an existing document; fixture creation refused')
        session = documents.create(run)
        session.set_units_mm()
        for name in ("L-CONTROL", "L-HARDSCAPE", "L-PLANT", "L-WATER"):
            session.ensure_layer(name)
        entities = []
        def record(kind, entity):
            entities.append({"kind": kind, "handle": str(entity.Handle), "layer": str(entity.Layer)})
        record("LINE", session.line((0, 0, 0), (10000, 0, 0), "L-CONTROL"))
        record("LINE", session.line((10000, 0, 0), (10000, 5000, 0), "L-CONTROL"))
        record("LINE_Z1200", session.line((2500, 3500, 1200), (2500, 4500, 1200), "L-CONTROL"))
        record("LWPOLYLINE_OPEN", session.polyline([(2500, 3500), (4000, 4500), (5500, 4000)],
                                                     "L-CONTROL", closed=False))
        record("LWPOLYLINE_CLOSED", session.polyline([(1000, 500), (7000, 500), (7000, 2500), (1000, 2500)],
                                                       "L-HARDSCAPE", closed=True))
        record("CIRCLE", session.circle((3000, 3500, 0), 750, "L-PLANT"))
        record("ARC", session.arc((9000, 3000, 0), 1000, 200, 340, "L-WATER"))
        record("RECTANGLE", session.polyline([(11000, 1000), (13000, 1000), (13000, 3000), (11000, 3000)],
                                               "L-WATER", closed=True))
        dwg = run / "bridge-fixture.dwg"
        dxf = run / "bridge-fixture.dxf"
        session.save_as(dwg, format="dwg")
        session.save()
        dwg_snapshot = session.snapshot()
        session.save_as(dxf, format="dxf")
        documents.close_owned()
        import ezdxf
        offline = ezdxf.readfile(dxf)
        facts = {"dwg": str(dwg), "dxf": str(dxf), "insunits": int(offline.header.get("$INSUNITS", -1)),
                 "source_units": "mm", "entity_count": len(list(offline.modelspace())),
                 "entities": entities, "dwg_snapshot": dwg_snapshot,
                 "control_points_mm": {"P1": [0, 0, 0], "P2": [10000, 0, 0],
                                       "P3": [10000, 5000, 0], "P4": [2500, 3500, 0],
                                       "Z1": [2500, 3500, 1200], "Z2": [2500, 4500, 1200]},
                 "expected_bbox_mm": [0, 0, 0, 13000, 5000, 1200],
                 "circle": {"center": [3000, 3500, 0], "radius_mm": 750},
                 "arc": {"center": [9000, 3000, 0], "radius_mm": 1000,
                         "start_deg": 200, "end_deg": 340},
                 "layers": ["L-CONTROL", "L-HARDSCAPE", "L-PLANT", "L-WATER"],
                 "sha256": {"dwg": sha(dwg), "dxf": sha(dxf)}}
        target = run / "fixture-source.json"
        if target.exists():
            raise FileExistsError(target)
        target.write_text(json.dumps(facts, ensure_ascii=False, indent=2), encoding="utf-8")
        return facts
    finally:
        audit = documents.cleanup()
        try:
            with (run / 'ownership-audit.json').open('x', encoding='utf-8') as file:
                json.dump(audit, file, indent=2)
        except Exception as exc:
            warnings.warn('Ownership audit could not be written: ' + str(exc), RuntimeWarning)
        for issue in audit['cleanup_warnings']:
            warnings.warn('Fixture cleanup: ' + issue, RuntimeWarning)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    print(json.dumps(build(parser.parse_args().run), ensure_ascii=False))
