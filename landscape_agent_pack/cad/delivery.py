"""Final CAD delivery gate over observed artifacts and completed operations."""
from dataclasses import dataclass
from pathlib import Path

from landscape_agent_pack.result import Result
from .geometry_qa import GeometryProfile, analyze_dxf


@dataclass(frozen=True)
class DeliveryEvidence:
    workspace: str
    dwg_path: str
    dxf_path: str
    expected_outputs: tuple[str, ...]
    saved_snapshot: dict | None
    reopened_snapshot: dict | None
    close_completed: bool
    final_close_completed: bool
    dimstyle_verified: bool
    plot_results: tuple[Result, ...]
    pdf_results: tuple[Result, ...]
    pdf_required: bool = True
    open_automation_documents: int = 0
    overwritten_user_files: bool = False


def validate_delivery(evidence: DeliveryEvidence, geometry_profile: GeometryProfile,
                      *, task_id="cad-delivery"):
    root = Path(evidence.workspace).resolve(strict=True)
    result = Result(task_id, "CAD delivery validation", input={
        "workspace": str(root), "dwg": evidence.dwg_path, "dxf": evidence.dxf_path,
        "expected_outputs": list(evidence.expected_outputs)})
    dwg = Path(evidence.dwg_path).resolve()
    scoped = dwg.is_relative_to(root)
    result.add("DWG_SCOPE", "DWG inside owned workspace", True, "PASS" if scoped else "FAIL", actual=str(dwg))
    exists = dwg.is_file()
    result.add("DWG_EXISTS", "DWG exists", True, "PASS" if exists else "FAIL", actual=exists)
    size = dwg.stat().st_size if exists else 0
    result.add("DWG_NONEMPTY", "DWG has content", True, "PASS" if size > 1024 else "FAIL", actual=size)
    saved = bool(evidence.saved_snapshot and evidence.saved_snapshot.get("saved") and
                 evidence.saved_snapshot.get("full_name") and
                 Path(evidence.saved_snapshot["full_name"]).resolve() == dwg)
    result.add("SAVE", "DWG Save completed", True, "PASS" if saved else "FAIL",
               actual=evidence.saved_snapshot)
    result.add("CLOSE", "DWG Close completed", True,
               "PASS" if evidence.close_completed else "NOT_EXECUTED")
    reopened = bool(evidence.reopened_snapshot and evidence.reopened_snapshot.get("full_name") and
                    Path(evidence.reopened_snapshot["full_name"]).resolve() == dwg and
                    evidence.reopened_snapshot.get("saved"))
    result.add("REOPEN_IDENTITY", "DWG reopened from expected disk path", True,
               "PASS" if reopened else "NOT_EXECUTED", expected=str(dwg), actual=evidence.reopened_snapshot)
    if saved and reopened:
        same = all(evidence.saved_snapshot.get(k) == evidence.reopened_snapshot.get(k)
                   for k in ("entities", "insunits"))
        result.add("REOPEN_CONTENT", "Entity count and units persisted", True,
                   "PASS" if same else "FAIL", expected=evidence.saved_snapshot,
                   actual=evidence.reopened_snapshot)
    else:
        result.add("REOPEN_CONTENT", "Entity count and units persisted", True, "NOT_EXECUTED")
    dxf = Path(evidence.dxf_path).resolve()
    if dxf.is_relative_to(root) and dxf.is_file():
        geo = analyze_dxf(dxf, geometry_profile, task_id=task_id + "-geometry")
        result.output["geometry_qa"] = geo.to_dict()
        result.add("GEOMETRY_QA", "Phase 2 geometry QA", True,
                   "PASS" if geo.status == "PASS" else "FAIL", actual=geo.status)
    else:
        result.add("GEOMETRY_QA", "Phase 2 geometry QA", True, "NOT_EXECUTED",
                   actual=str(dxf))
    result.add("DIMSTYLE", "Persisted DIMSTYLE verified after reopen", True,
               "PASS" if evidence.dimstyle_verified else "NOT_EXECUTED")
    if evidence.pdf_required:
        plots_ok = bool(evidence.plot_results) and all(x.status == "PASS" for x in evidence.plot_results)
        pdfs_ok = len(evidence.pdf_results) == len(evidence.plot_results) and bool(evidence.pdf_results) and all(x.status in {"PASS", "PASS_WITH_WARNINGS"}
                                                   for x in evidence.pdf_results)
        plot_paths = {Path(x.output.get("pdf", "")).resolve() for x in evidence.plot_results if x.output.get("pdf")}
        qa_paths = {Path(x.input.get("path", "")).resolve() for x in evidence.pdf_results if x.input.get("path")}
        coverage_ok = bool(plot_paths) and plot_paths == qa_paths and all(p.is_file() for p in plot_paths)
        result.add("PLOT", "Required PDF plots executed", True,
                   "PASS" if plots_ok else "NOT_EXECUTED" if not evidence.plot_results else "FAIL",
                   actual=[x.status for x in evidence.plot_results])
        result.add("PDF_OBJECTIVE_QA", "Required PDF objective QA passed", True,
                   "PASS" if pdfs_ok else "NOT_EXECUTED" if not evidence.pdf_results else "FAIL",
                   actual=[x.status for x in evidence.pdf_results])
        result.add("PDF_COVERAGE", "Every plotted PDF was inspected and retained", True,
                   "PASS" if coverage_ok else "FAIL", expected=sorted(str(p) for p in plot_paths),
                   actual=sorted(str(p) for p in qa_paths))
    else:
        result.add("PLOT", "Optional PDF plot", False, "SKIPPED")
    result.add("FINAL_CLOSE", "Reopened DWG closed cleanly", True,
               "PASS" if evidence.final_close_completed else "NOT_EXECUTED")
    result.add("NO_DIRTY_DOCS", "No automation-owned documents open", True,
               "PASS" if evidence.open_automation_documents == 0 else "FAIL",
               expected=0, actual=evidence.open_automation_documents)
    actual_files = {p.resolve() for p in root.rglob("*") if p.is_file()}
    expected_files = {Path(p).resolve() for p in evidence.expected_outputs}
    unknown = sorted(str(p) for p in actual_files - expected_files)
    result.add("KNOWN_OUTPUTS", "Workspace contains only declared outputs", True,
               "PASS" if not unknown else "FAIL", actual=unknown)
    result.add("NO_OVERWRITE", "No user file overwritten", True,
               "FAIL" if evidence.overwritten_user_files else "PASS")
    result.add("VISUAL_QA", "Visual design review", False, "NOT_EXECUTED",
               message="Objective PDF checks do not establish visual design quality")
    result.artifacts = sorted(str(p) for p in expected_files if p.is_file())
    return result
