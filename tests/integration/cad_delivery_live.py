"""Phase 3 live acceptance on a unique, automation-owned test drawing only."""
import json
import sys
import traceback
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from landscape_agent_pack.result import Result
from landscape_agent_pack.cad.core import DocumentSession, connect, dynamic, point
from landscape_agent_pack.cad.annotation import configure_dimstyle, verify_dimstyle
from landscape_agent_pack.cad.plot import PlotRequest, plot_pdf
from landscape_agent_pack.cad.pdf_qa import PDFProfile, inspect_pdf
from landscape_agent_pack.cad.visual_qa import visual_qa_not_executed
from landscape_agent_pack.cad.delivery import DeliveryEvidence, validate_delivery
from landscape_agent_pack.cad.geometry_qa import GeometryProfile


def mark(result, id, status, actual=None, message=""):
    check = next(c for c in result.checks if c.id == id)
    check.status, check.actual, check.message = status, actual, message


def main():
    run = ROOT / "runs" / ("phase3-" + uuid.uuid4().hex[:12])
    run.mkdir(parents=True, exist_ok=False)
    result = Result(run.name, "Phase 3 CAD delivery live acceptance",
                    input={"workspace": str(run)}, output={"workspace": str(run)}, software="AutoCAD")
    ids = ["PREFLIGHT", "BUILD", "DIMSTYLE", "DWG_SAVE", "A4_LANDSCAPE", "A3_LANDSCAPE",
           "FIT", "SCALE_100", "WINDOW", "EXTENTS", "LAYOUT", "DEVICE_FALLBACK", "PDF_QA", "INVALID_PC3",
           "EXISTING_OUTPUT", "INVALID_PATH", "MISSING_PDF", "DXF_EXPORT",
           "DWG_CLOSE", "DWG_REOPEN", "DIMSTYLE_REOPEN", "FINAL_CLOSE",
           "DELIVERY", "MANDATORY_NOT_EXECUTED"]
    for id in ids:
        result.add(id, id.replace("_", " ").title(), True, "NOT_EXECUTED")
    session = None
    expected = set()
    plot_results = []
    pdf_results = []
    saved = reopened = None
    first_close = final_close = dim_ok = False
    try:
        import pythoncom
        pythoncom.CoInitialize()
        app = connect(allow_launch=False)
        result.software_version = str(app.Version)
        if int(app.Documents.Count) != 0:
            raise RuntimeError(f"Preflight blocked: {app.Documents.Count} existing AutoCAD documents")
        mark(result, "PREFLIGHT", "PASS", {"version": result.software_version, "open_documents": 0})
        session = DocumentSession.create(app, workspace_root=run)
        session.set_units_mm()
        for layer in ("L-SITE", "L-TEXT", "L-DIMS"):
            session.ensure_layer(layer)
        style = configure_dimstyle(session)
        mark(result, "DIMSTYLE", "PASS", style)
        session.polyline([(0, 0), (20000, 0), (20000, 12000), (0, 12000)], "L-SITE", closed=True)
        session.line((1000, 2000), (18000, 2000), "L-SITE")
        session.circle((5000, 6000), 1500, "L-SITE")
        session.arc((14000, 6500), 2000, 20, 160, "L-SITE")
        session.mtext("LAP PHASE 3 | A4/A3 | 1:100", (1000, 10800), 18000, 350, "L-TEXT")
        session.dim_aligned((0, 0), (20000, 0), (10000, -700), "L-DIMS")
        doc = session.doc
        sheet = dynamic(doc.Layouts.Add("LAP-SHEET"))
        doc.ActiveLayout = sheet
        ps = doc.PaperSpace
        viewports = [ps.Item(i) for i in range(int(ps.Count)) if ps.Item(i).ObjectName == "AcDbViewport"]
        if len(viewports) >= 2:
            viewports[-1].Delete()  # remove only the new layout's floating model viewport
        doc.PaperSpace.AddLine(point(20, 20), point(270, 20)).Layer = "L-SITE"
        doc.PaperSpace.AddText("LAP LAYOUT TEST", point(30, 170), 6).Layer = "L-TEXT"
        mark(result, "BUILD", "PASS", session.snapshot())
        dwg = run / "delivery-test.dwg"
        expected.add(dwg)
        session.save_as(dwg, format="dwg")
        session.save()
        mark(result, "DWG_SAVE", "PASS", session.snapshot())

        specs = [
            ("a4-window-fit.pdf", "A4", "window", "fit", "Model"),
            ("a3-window-fit.pdf", "A3", "window", "fit", "Model"),
            ("a4-extents-fit.pdf", "A4", "extents", "fit", "Model"),
            ("a3-extents-100.pdf", "A3", "extents", "1:100", "Model"),
            ("a4-window-100.pdf", "A4", "window", "1:100", "Model"),
            ("a4-layout-fit.pdf", "A4", "layout", "fit", "LAP-SHEET"),
            ("a4-fallback-fit.pdf", "A4", "window", "fit", "Model"),
        ]
        for filename, paper, area, scale, layout_name in specs:
            target = run / filename
            request = PlotRequest(str(target), paper=paper, area=area, scale=scale,
                                  layout_name=layout_name,
                                  preferred_device="NO_SUCH_PLOTTER.pc3" if "fallback" in filename else None,
                                  window=((-2500, -2500), (24000, 15000)) if area == "window" else None)
            plotted = plot_pdf(session, request, task_id=run.name + "-" + filename)
            plot_results.append(plotted)
            if plotted.status != "PASS":
                raise AssertionError(f"Plot {filename}: {plotted.to_dict()}")
            expected.add(target)
            qa = inspect_pdf(target, PDFProfile(paper, "landscape", require_vectors=True),
                             task_id=run.name + "-qa-" + filename)
            pdf_results.append(qa)
            if qa.status not in {"PASS", "PASS_WITH_WARNINGS"}:
                raise AssertionError(f"PDF QA {filename}: {qa.to_dict()}")
            report = run / (target.stem + "-qa.json")
            report.write_text(json.dumps({"plot": plotted.to_dict(), "pdf_qa": qa.to_dict()},
                                         ensure_ascii=False, indent=2), encoding="utf-8")
            expected.add(report)
        for id, pred in {
            "A4_LANDSCAPE": lambda p: p["paper"] == "A4",
            "A3_LANDSCAPE": lambda p: p["paper"] == "A3",
            "FIT": lambda p: p["scale"] == "fit",
            "SCALE_100": lambda p: p["scale"] == "1:100",
            "WINDOW": lambda p: p["area"] == "window",
            "EXTENTS": lambda p: p["area"] == "extents",
            "LAYOUT": lambda p: p["area"] == "layout",
            "DEVICE_FALLBACK": lambda p: p["preferred_device"] == "NO_SUCH_PLOTTER.pc3" and p["allow_device_fallback"],
        }.items():
            matched = [p for p in (x.input for x in plot_results) if pred(p)]
            mark(result, id, "PASS" if matched else "FAIL", actual=len(matched))
        import pymupdf
        measured = {}
        for filename in ("a3-extents-100.pdf", "a4-window-100.pdf"):
            with pymupdf.open(run / filename) as pdf:
                widths = [item["rect"].width * 25.4 / 72.0 for item in pdf[0].get_drawings()]
                measured[filename] = max(widths)
        if not all(abs(x - 200.0) < 1.0 for x in measured.values()):
            mark(result, "SCALE_100", "FAIL", measured, "20 m boundary must plot at 200 mm")
        else:
            mark(result, "SCALE_100", "PASS", measured)
        mark(result, "PDF_QA", "PASS", actual=[q.metrics for q in pdf_results])

        bad = plot_pdf(session, PlotRequest(str(run / "invalid-pc3.pdf"),
                    preferred_device="NO_SUCH_PLOTTER.pc3", allow_device_fallback=False))
        mark(result, "INVALID_PC3", "PASS" if bad.status == "FAIL" and not (run / "invalid-pc3.pdf").exists() else "FAIL",
             actual=bad.to_dict())
        sentinel = run / "existing.pdf"
        sentinel.write_bytes(b"DO-NOT-OVERWRITE")
        expected.add(sentinel)
        old = sentinel.read_bytes()
        bad = plot_pdf(session, PlotRequest(str(sentinel)))
        mark(result, "EXISTING_OUTPUT", "PASS" if bad.status == "FAIL" and sentinel.read_bytes() == old else "FAIL",
             actual=bad.to_dict())
        bad = plot_pdf(session, PlotRequest(str(run / "missing-directory" / "invalid.pdf")))
        mark(result, "INVALID_PATH", "PASS" if bad.status == "FAIL" else "FAIL", actual=bad.to_dict())
        missing = inspect_pdf(run / "never-generated.pdf", PDFProfile("A4", "landscape"))
        mark(result, "MISSING_PDF", "PASS" if missing.status == "FAIL" else "FAIL", actual=missing.to_dict())

        session.save()
        saved = session.snapshot()
        dxf = run / "delivery-test.dxf"
        expected.add(dxf)
        session.save_as(dxf, format="dxf")
        mark(result, "DXF_EXPORT", "PASS", session.snapshot())
        session.close()
        session = None
        first_close = True
        mark(result, "DWG_CLOSE", "PASS")
        session = DocumentSession.open(app, dwg, workspace_root=run)
        reopened = session.snapshot()
        mark(result, "DWG_REOPEN", "PASS" if reopened["full_name"] == str(dwg.resolve()) and
             reopened["entities"] == saved["entities"] else "FAIL", reopened)
        dim_verify = verify_dimstyle(session)
        dim_ok = True
        mark(result, "DIMSTYLE_REOPEN", "PASS", dim_verify)
        session.close()
        session = None
        final_close = True
        mark(result, "FINAL_CLOSE", "PASS", {"open_documents": int(app.Documents.Count)})
        # AutoCAD may create a DWG backup during the second Save; declare that
        # known artifact by its exact filename, without blessing unknown files.
        backup = run / "delivery-test.bak"
        if backup.is_file():
            expected.add(backup)
        expected.update((run / "phase3-result.json", run / "phase3-result.md",
                         run / "delivery-result.json", run / "delivery-result.md",
                         run / "visual-qa.json", run / "visual-qa.md"))
        geometry = GeometryProfile(required_layers=("L-SITE", "L-TEXT", "L-DIMS"),
                                   expected_entity_count=saved["entities"],
                                   allowed_bbox=(-4000, -4000, 26000, 17000))
        delivery = validate_delivery(DeliveryEvidence(str(run), str(dwg), str(dxf),
            tuple(str(p) for p in expected), saved, reopened, first_close, final_close,
            dim_ok, tuple(plot_results), tuple(pdf_results), open_automation_documents=int(app.Documents.Count)),
            geometry, task_id=run.name + "-delivery")
        delivery.write(run / "delivery-result.json", run / "delivery-result.md")
        mark(result, "DELIVERY", "PASS" if delivery.status in {"PASS", "PASS_WITH_WARNINGS"} else "FAIL",
             delivery.to_dict())
        visual = visual_qa_not_executed(task_id=run.name, design_intent="Test drawing on A4/A3",
                                         checklist=["clipping", "text legibility", "dimension placement"])
        visual.write(run / "visual-qa.json", run / "visual-qa.md")
        result.output["visual_qa_status"] = visual.status
        result.add("VISUAL_QA", "Visual design review", False, "NOT_EXECUTED",
                   message="Interface defined; no formal visual judgement performed")
        probe = Result(run.name + "-missing", "Mandatory missing probe")
        probe.add("REQUIRED", "Required check", True, "NOT_EXECUTED")
        mark(result, "MANDATORY_NOT_EXECUTED", "PASS" if probe.status == "REVIEW_REQUIRED" and probe.exit_code == 1 else "FAIL",
             {"status": probe.status, "exit_code": probe.exit_code})
        result.output["delivery_status"] = delivery.status
        result.output["pdf_device"] = plot_results[0].output.get("device")
    except Exception as exc:
        result.errors.append(f"{type(exc).__name__}: {exc}")
        (run / "traceback.txt").write_text(traceback.format_exc(), encoding="utf-8")
        pending = next((c for c in result.checks if c.status == "NOT_EXECUTED"), None)
        if pending:
            mark(result, pending.id, "FAIL", message=f"Stopped: {exc}")
    finally:
        if session is not None and session.opened_by_automation:
            try:
                session.refresh()
                if session.dirty:
                    result.warnings.append("Owned drawing remains dirty; manual inspection required")
                else:
                    session.close()
            except Exception as exc:
                result.warnings.append(f"Owned drawing cleanup needs inspection: {exc}")
        result.artifacts = [str(p) for p in run.iterdir() if p.is_file()]
        result.write(run / "phase3-result.json", run / "phase3-result.md")
    return result, run


if __name__ == "__main__":
    outcome, folder = main()
    print(json.dumps({"status": outcome.status, "exit_code": outcome.exit_code,
                      "run": str(folder), "errors": outcome.errors}, ensure_ascii=False))
    raise SystemExit(outcome.exit_code)
