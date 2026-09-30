"""Deterministic AutoCAD PDF plotting for automation-owned documents.

One request configures one layout and produces one new artifact. PlotToFile is a
single state-changing call: uncertain outcomes are inspected, never replayed.
"""
from dataclasses import dataclass
from pathlib import Path
import re
import time

from landscape_agent_pack.result import Result
from .core import dynamic, numbers

PAPER_MM = {"A4": (297.0, 210.0), "A3": (420.0, 297.0),
            "A2": (594.0, 420.0), "A1": (841.0, 594.0)}
PLOT_TYPES = {"extents": 1, "window": 4, "layout": 5}
PDF_PC3_PREFERENCE = ("AutoCAD PDF (General Documentation).pc3",
                      "DWG To PDF.pc3", "AutoCAD PDF (High Quality Print).pc3",
                      "AutoCAD PDF (Smallest File).pc3",
                      "AutoCAD PDF (Web and Mobile).pc3")


@dataclass(frozen=True)
class PlotRequest:
    output_path: str
    paper: str = "A4"
    orientation: str = "landscape"
    area: str = "extents"
    layout_name: str = "Model"
    window: tuple[tuple[float, float], tuple[float, float]] | None = None
    scale: str = "fit"  # fit or 1:50, 1:100, 1:200, 1:N
    center: bool = True
    style_sheet: str = "monochrome.ctb"
    preferred_device: str | None = None
    allow_device_fallback: bool = True
    overwrite: bool = False  # True is intentionally rejected for owned artifacts.
    timeout_s: float = 60.0
    poll_s: float = 0.25
    stable_polls: int = 3

    def validate(self):
        if self.paper not in PAPER_MM or self.orientation not in {"portrait", "landscape"}:
            raise ValueError("Unsupported paper or orientation")
        if self.area not in PLOT_TYPES:
            raise ValueError("Unsupported plot area")
        if self.area == "window":
            if not self.window or len(self.window) != 2 or any(len(p) != 2 for p in self.window):
                raise ValueError("Window plot requires two XY corners")
            if not (self.window[1][0] > self.window[0][0] and self.window[1][1] > self.window[0][1]):
                raise ValueError("Window bounds must increase")
        if self.area == "layout" and self.layout_name.casefold() == "model":
            raise ValueError("Layout plot requires a named paper-space layout")
        if self.scale != "fit" and not re.fullmatch(r"1:(?:[1-9]\d*)(?:\.\d+)?", self.scale):
            raise ValueError("Scale must be fit or 1:positive denominator")
        if self.timeout_s <= 0 or self.poll_s <= 0 or self.stable_polls < 2:
            raise ValueError("Invalid bounded wait configuration")
        if self.overwrite:
            raise ValueError("Overwriting plot artifacts is prohibited")
        if Path(self.output_path).suffix.lower() != ".pdf":
            raise ValueError("Plot output must be PDF")


def discover_pdf_devices(layout):
    layout.RefreshPlotDeviceInfo()
    names = [str(x) for x in layout.GetPlotDeviceNames()]
    return [x for x in names if x.lower().endswith(".pc3") and "pdf" in x.lower()]


def select_pdf_device(devices, preferred=None, allow_fallback=True):
    by_lower = {d.casefold(): d for d in devices}
    if preferred:
        found = by_lower.get(preferred.casefold())
        if found:
            return found
        if not allow_fallback:
            raise LookupError(f"CONFIGURATION_REQUIRED: preferred PDF PC3 unavailable: {preferred}")
    for name in PDF_PC3_PREFERENCE:
        if name.casefold() in by_lower:
            return by_lower[name.casefold()]
    if devices:
        return sorted(devices, key=str.casefold)[0]
    raise LookupError("CONFIGURATION_REQUIRED: no AutoCAD PDF PC3 available")


def select_media(media_names, paper, orientation):
    width, height = PAPER_MM[paper]
    if orientation == "portrait":
        width, height = height, width
    matches = []
    for name in media_names:
        s = str(name)
        found = re.search(r"\((\d+(?:\.\d+)?)_x_(\d+(?:\.\d+)?)_MM\)", s, re.I)
        if found and abs(float(found[1])-width) < 0.6 and abs(float(found[2])-height) < 0.6:
            matches.append(s)
    matches.sort(key=lambda s: (0 if s.startswith("ISO_") else 1,
                                1 if "expand" in s.lower() or "full" in s.lower() else 0, len(s)))
    if not matches:
        raise LookupError(f"CONFIGURATION_REQUIRED: {paper} {orientation} media unavailable")
    return matches[0]


def wait_for_pdf(path, *, timeout_s, poll_s, stable_polls):
    deadline = time.monotonic() + timeout_s
    last = -1
    stable = 0
    while time.monotonic() < deadline:
        size = path.stat().st_size if path.is_file() else 0
        stable = stable + 1 if size > 0 and size == last else 0
        if stable >= stable_polls:
            return size
        last = size
        time.sleep(poll_s)
    raise TimeoutError(f"TIMEOUT: PDF not stable within {timeout_s}s: {path}")


def plot_pdf(session, request: PlotRequest, *, task_id="cad-plot"):
    result = Result(task_id, "CAD PDF plot", input=vars(request).copy(), software="AutoCAD COM")
    stage = "validate"
    try:
        request.validate()
        output = session._target(request.output_path)
        doc = session.doc
        session._require_idle(doc)
        names = [str(doc.Layouts.Item(i).Name) for i in range(int(doc.Layouts.Count))]
        if request.layout_name not in names:
            raise ValueError(f"Layout absent: {request.layout_name}")
        stage = "layout"
        layout = dynamic(doc.Layouts.Item(request.layout_name))
        doc.ActiveLayout = layout
        stage = "device-discovery"
        devices = discover_pdf_devices(layout)
        device = select_pdf_device(devices, request.preferred_device, request.allow_device_fallback)
        stage = "device-configuration"
        layout.ConfigName = device
        layout.RefreshPlotDeviceInfo()
        stage = "media-selection"
        media = select_media(layout.GetCanonicalMediaNames(), request.paper, request.orientation)
        stage = "style-selection"
        styles = [str(x) for x in layout.GetPlotStyleTableNames()]
        style = next((s for s in styles if s.casefold() == request.style_sheet.casefold()), None)
        if style is None:
            raise LookupError(f"CONFIGURATION_REQUIRED: plot style unavailable: {request.style_sheet}")
        # Every field is set, so prior GUI plot state cannot silently control this run.
        stage = "media-configuration"
        layout.CanonicalMediaName = media
        layout.PaperUnits = 1  # acMillimeters
        layout.PlotRotation = 0  # orientation comes from selected canonical media
        stage = "plot-area"
        if request.area == "window":
            layout.SetWindowToPlot(numbers(request.window[0]), numbers(request.window[1]))
        layout.PlotType = PLOT_TYPES[request.area]
        stage = "plot-style-and-scale"
        if request.area != "layout":
            layout.CenterPlot = bool(request.center)
        stage = "plot-style"
        layout.PlotWithPlotStyles = True
        layout.StyleSheet = style
        stage = "plot-scale"
        if request.scale == "fit":
            layout.UseStandardScale = True
            layout.StandardScale = 0  # acScaleToFit
        else:
            layout.UseStandardScale = False
            layout.SetCustomScale(1.0, float(request.scale.split(":", 1)[1]))
        stage = "regeneration"
        doc.SetVariable("BACKGROUNDPLOT", 0)
        doc.Regen(1)
        stage = "readback"
        actual = {"device": str(layout.ConfigName), "media": str(layout.CanonicalMediaName),
                  "style": str(layout.StyleSheet), "paper_units": int(layout.PaperUnits),
                  "plot_type": int(layout.PlotType), "scale": request.scale,
                  "use_standard_scale": bool(layout.UseStandardScale),
                  "standard_scale": int(layout.StandardScale),
                  "custom_scale": [float(x) for x in layout.GetCustomScale()],
                  "center_plot": bool(layout.CenterPlot) if request.area != "layout" else None,
                  "orientation": request.orientation, "area": request.area,
                  "layout": request.layout_name, "available_pdf_devices": devices}
        if actual["device"].casefold() != device.casefold() or actual["media"] != media or \
           actual["plot_type"] != PLOT_TYPES[request.area] or actual["paper_units"] != 1 or \
           actual["style"].casefold() != style.casefold():
            raise RuntimeError(f"AutoCAD plot configuration readback mismatch: {actual}")
        if request.scale == "fit":
            if not actual["use_standard_scale"] or actual["standard_scale"] != 0:
                raise RuntimeError(f"Fit scale readback mismatch: {actual}")
        else:
            ratio = actual["custom_scale"][0] / actual["custom_scale"][1]
            expected_ratio = 1.0 / float(request.scale.split(":", 1)[1])
            if actual["use_standard_scale"] or abs(ratio-expected_ratio) > 1e-8:
                raise RuntimeError(f"Custom scale readback mismatch: {actual}")
        if request.area != "layout" and actual["center_plot"] != request.center:
            raise RuntimeError(f"Center plot readback mismatch: {actual}")
        result.output = {"pdf": str(output), **actual}
        result.add("CONFIGURATION", "Plot configuration readback", True, "PASS", actual=actual)
        stage = "plot-execution"
        plotter = dynamic(doc.Plot)
        stage = "quiet-error-mode"
        plotter.QuietErrorMode = True
        stage = "set-layouts-to-plot"
        import pythoncom
        from win32com.client import VARIANT
        plotter.SetLayoutsToPlot(VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_BSTR,
                                         [request.layout_name]))
        stage = "plot-to-file"
        outcome = bool(plotter.PlotToFile(str(output), device))
        result.add("PLOT_EXECUTED", "AutoCAD PlotToFile returned success", True,
                   "PASS" if outcome else "FAIL", actual=outcome)
        if not outcome:
            return result
        stage = "bounded-wait"
        size = wait_for_pdf(output, timeout_s=request.timeout_s, poll_s=request.poll_s,
                            stable_polls=request.stable_polls)
        result.add("PDF_STABLE", "PDF exists with stable size", True, "PASS", actual=size)
        result.artifacts.append(str(output))
    except Exception as exc:
        result.add("PLOT_ERROR", "Plot execution", True, "FAIL", actual=type(exc).__name__, message=f"{stage}: {exc}")
        result.errors.append(f"{stage}: {exc}")
    return result
