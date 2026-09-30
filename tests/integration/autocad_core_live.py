"""Phase 2 isolated AutoCAD 2025 acceptance; never closes pre-existing documents."""
import argparse
import json
import math
import sys
import uuid
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from landscape_agent_pack.result import Result
from landscape_agent_pack.cad.core import DocumentSession, connect
from landscape_agent_pack.cad.annotation import configure_dimstyle, verify_dimstyle
from landscape_agent_pack.cad.angles import arc_endpoints, arc_bbox
from landscape_agent_pack.cad.geometry_qa import GeometryProfile, analyze_dxf

CHECKS = [
    ("NEW_DWG", "New automation-owned document"),
    ("CREATE_ENTITIES", "Line Polyline Circle Arc Text MText Dimension"),
    ("ARC_DIRECTION", "Arc endpoints and positive CCW direction"),
    ("LAYER", "Layer creation and readback"),
    ("DIMSTYLE", "Persisted DIMSTYLE and actual Document readback"),
    ("DWG_SAVE", "Initial DWG SaveAs and Save"),
    ("DWG_REOPEN", "DWG close and reopen"),
    ("DWG_SAVE_AS", "DWG SaveAs to new path"),
    ("DXF_SAVE_AS", "DXF SaveAs and identity refresh"),
    ("DXF_REOPEN", "DXF close and reopen"),
    ("GEOMETRY_QA", "Offline DXF geometry QA"),
    ("QA_FAULTS", "Injected tiny/open/zero geometry detected"),
    ("NOT_EXECUTED", "Mandatory missing check blocks PASS"),
]


def update(result, id, status, actual=None, message=""):
    check = next(c for c in result.checks if c.id == id)
    check.status, check.actual, check.message = status, actual, message


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-root", type=Path, default=ROOT / "runs")
    args = parser.parse_args()
    run = args.runs_root.resolve() / ("phase2-" + uuid.uuid4().hex[:12])
    run.mkdir(parents=True, exist_ok=False)
    result = Result(run.name, "Phase 2 AutoCAD Core live acceptance", input={"workspace": str(run)}, output={"workspace": str(run)}, software="AutoCAD")
    for id, name in CHECKS:
        result.add(id, name, True, "NOT_EXECUTED")
    session = None
    try:
        import pythoncom
        pythoncom.CoInitialize()
        app = connect(allow_launch=False)
        result.software_version = str(app.Version)
        result.environment = {"python": sys.version.split()[0], "progid": "AutoCAD.Application.25"}
        count = int(app.Documents.Count)
        if count:
            result.errors.append(f"Preflight blocked: {count} existing AutoCAD documents; no mutation attempted")
            return result, run
        session = DocumentSession.create(app, workspace_root=run)
        update(result, "NEW_DWG", "PASS", session.snapshot())
        session.set_units_mm()
        for layer in ("L-SITE", "L-TEXT", "L-DIMS"):
            session.ensure_layer(layer)
        update(result, "LAYER", "PASS", {"layers": [str(app.ActiveDocument.Layers.Item(x).Name) for x in ("L-SITE", "L-TEXT", "L-DIMS")]})
        style = configure_dimstyle(session)
        update(result, "DIMSTYLE", "PASS", style)
        session.line((0,0,0), (1000,0,0), "L-SITE")
        session.polyline([(0,0),(1000,0),(1000,500),(0,500)], "L-SITE", closed=True)
        session.circle((1500,250), 100, "L-SITE")
        arcs = []
        for start, end, center in ((0,90,(2000,0)), (90,180,(2400,0)), (350,10,(2800,0))):
            entity = session.arc(center, 100, start, end, "L-SITE")
            p, q = arc_endpoints(center, 100, start, end)
            actual_p, actual_q = tuple(entity.StartPoint[:2]), tuple(entity.EndPoint[:2])
            if math.dist(actual_p, p) > 1e-6 or math.dist(actual_q, q) > 1e-6:
                raise AssertionError(f"Arc {start}->{end} endpoint mismatch: {actual_p}, {actual_q}")
            arcs.append({"degrees": [start, end], "start": actual_p, "end": actual_q, "handle": str(entity.Handle)})
        update(result, "ARC_DIRECTION", "PASS", arcs)
        session.text("LAP Phase 2", (0,700), 250, "L-TEXT")
        session.mtext("测试 MText", (0,1100), 3000, 250, "L-TEXT")
        dim = session.dim_aligned((0,0),(1000,0),(500,-400), "L-DIMS")
        update(result, "CREATE_ENTITIES", "PASS", {"entities": session.snapshot()["entities"], "dimension_measurement": float(dim.Measurement)})
        dwg = run / "phase2-initial.dwg"
        session.save_as(dwg, format="dwg")
        session.save()
        update(result, "DWG_SAVE", "PASS", session.snapshot())
        original_count = session.snapshot()["entities"]
        session.close()
        session = DocumentSession.open(app, dwg, workspace_root=run)
        snap = session.snapshot()
        if snap["entities"] != original_count or snap["insunits"] != 4:
            raise AssertionError(f"DWG reopen mismatch: {snap}")
        snap["persisted_dimstyle"] = verify_dimstyle(session)
        update(result, "DWG_REOPEN", "PASS", snap)
        second = run / "phase2-save-as.dwg"
        session.save_as(second, format="dwg")
        update(result, "DWG_SAVE_AS", "PASS", session.snapshot())
        session.close()
        session = DocumentSession.open(app, second, workspace_root=run)
        dxf = run / "phase2-export.dxf"
        session.save_as(dxf, format="dxf")
        if session.format != "dxf" or Path(session.current_path) != dxf.resolve():
            raise AssertionError("SaveAs DXF did not refresh document identity")
        update(result, "DXF_SAVE_AS", "PASS", session.snapshot())
        session.close()
        session = DocumentSession.open(app, dxf, workspace_root=run)
        snap = session.snapshot()
        if snap["entities"] != original_count:
            raise AssertionError(f"DXF reopen count mismatch: {snap}")
        update(result, "DXF_REOPEN", "PASS", snap)
        session.close()
        session = None
        import ezdxf
        offline = ezdxf.readfile(dxf)
        from ezdxf import bbox as ezbbox
        dxf_arcs = list(offline.modelspace().query("ARC"))
        arc_count = len(dxf_arcs)
        if arc_count != 3:
            raise AssertionError(f"DXF ARC count mismatch: {arc_count}")
        for entity, (start, end, center) in zip(dxf_arcs, ((0,90,(2000,0)), (90,180,(2400,0)), (350,10,(2800,0)))):
            bb = ezbbox.extents([entity])
            actual = (bb.extmin.x, bb.extmin.y, bb.extmax.x, bb.extmax.y)
            expected = arc_bbox(center, 100, start, end)
            if max(abs(a-b) for a,b in zip(actual, expected)) > 1e-5:
                raise AssertionError(f"DXF arc bbox mismatch {start}->{end}: {actual} vs {expected}")
        qa = analyze_dxf(dxf, GeometryProfile(required_layers=("L-SITE", "L-TEXT", "L-DIMS"), allowed_bbox=(-1000,-1000,3500,1500), expected_entity_count=original_count), task_id=run.name)
        qa.write(run / "geometry-qa.json", run / "geometry-qa.md")
        if qa.status != "PASS":
            raise AssertionError(f"Geometry QA {qa.status}: {qa.to_dict()}")
        update(result, "GEOMETRY_QA", "PASS", {"status": qa.status, "arc_count": arc_count})
        # Fault injection uses a new synthetic DXF, never a user/project file.
        bad = ezdxf.new()
        bad.layers.new("L-SITE")
        bm = bad.modelspace()
        bm.add_line((0,0),(0,0),dxfattribs={"layer":"L-SITE"})
        bm.add_line((1,1),(1.01,1),dxfattribs={"layer":"L-SITE"})
        bm.add_lwpolyline([(2,2),(3,2)],dxfattribs={"layer":"L-SITE"})
        bad_path = run / "fault-injection.dxf"
        bad.saveas(bad_path)
        bad_qa = analyze_dxf(bad_path, GeometryProfile(closed_layers=("L-SITE",)), task_id=run.name + "-faults")
        bad_qa.write(run / "fault-qa.json", run / "fault-qa.md")
        detected = {c.id for c in bad_qa.checks if c.status == "FAIL"}
        if not {"ZERO_LINE", "TINY_SEGMENT", "OPEN_REQUIRED"} <= detected:
            raise AssertionError(f"Fault injection missed: {detected}")
        update(result, "QA_FAULTS", "PASS", sorted(detected))
        probe = Result(run.name + "-missing", "Mandatory NOT_EXECUTED probe")
        probe.add("MISSING", "Required unavailable check", True, "NOT_EXECUTED")
        probe.write(run / "missing-check.json", run / "missing-check.md")
        if probe.status != "REVIEW_REQUIRED" or probe.exit_code != 1:
            raise AssertionError("NOT_EXECUTED incorrectly passed")
        update(result, "NOT_EXECUTED", "PASS", {"probe_status": probe.status, "probe_exit_code": probe.exit_code})
    except Exception as exc:
        result.errors.append(f"{type(exc).__name__}: {exc}")
        (run / "traceback.txt").write_text(traceback.format_exc(), encoding="utf-8")
        pending = next((c for c in result.checks if c.status == "NOT_EXECUTED"), None)
        if pending:
            update(result, pending.id, "FAIL", message=f"Stopped here: {type(exc).__name__}: {exc}")
    finally:
        if session is not None and session.opened_by_automation:
            try:
                session.refresh()
                if session.dirty:
                    result.warnings.append("Owned document remains open and dirty; inspect manually; no discard/kill attempted")
                else:
                    session.close()
            except Exception as exc:
                result.warnings.append(f"Owned document cleanup needs manual inspection: {exc}")
        result.artifacts = [str(p) for p in run.iterdir() if p.is_file()]
        result.artifacts.extend([str(run / "phase2-result.json"), str(run / "phase2-result.md")])
        result.write(run / "phase2-result.json", run / "phase2-result.md")
    return result, run


if __name__ == "__main__":
    outcome, folder = main()
    print(json.dumps({"status": outcome.status, "exit_code": outcome.exit_code, "run": str(folder), "errors": outcome.errors}, ensure_ascii=False))
    raise SystemExit(outcome.exit_code)
