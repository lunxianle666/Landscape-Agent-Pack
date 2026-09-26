"""Create the isolated Phase 4 CAD fixture with real AutoCAD COM.

The script refuses an existing user document and never overwrites an output.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from landscape_agent_pack.cad.core import DocumentSession, connect


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(run):
    run = Path(run).resolve(strict=True)
    app = connect(allow_launch=True)
    if int(app.Documents.Count) == 1:
        doc = app.Documents.Item(0)
        # A newly launched, empty Drawing1 is owned by this invocation. Any
        # saved or nonempty document belongs to someone else and blocks work.
        if not str(doc.FullName) and int(doc.ModelSpace.Count) == 0 and str(doc.Name).lower().startswith("drawing"):
            doc.Close(False)
    if int(app.Documents.Count):
        raise RuntimeError("AutoCAD contains an existing document; fixture creation refused")
    session = DocumentSession.create(app, workspace_root=run)
    try:
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
        session.close()
        session = None
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
        if session is not None and session.opened_by_automation:
            session.refresh()
            if session.dirty:
                raise RuntimeError("Automation drawing left dirty; inspect before close")
            session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    print(json.dumps(build(parser.parse_args().run), ensure_ascii=False))
