"""Deterministic model-space millimetre dimension profile and COM readback."""
from dataclasses import dataclass

from .core import dynamic
from .retry import read_with_retry


@dataclass(frozen=True)
class DimStyleProfile:
    name: str = "LAP-V02-MM-100"
    text_style: str = "LAP-TEXT"
    font: str = "SimSun"
    drawing_units: str = "mm"
    plot_scale: float = 100.0
    paper_text_mm: float = 2.5
    paper_arrow_mm: float = 1.8
    paper_extension_offset_mm: float = 2.0
    paper_extension_extend_mm: float = 1.2
    paper_text_gap_mm: float = 0.4
    decimal_places: int = 0
    linear_factor: float = 1.0
    arrow_block: str = ""  # AutoCAD default closed filled arrow

    def variables(self):
        if self.drawing_units != "mm" or self.plot_scale <= 0:
            raise ValueError("Current profile requires model-space millimetres and positive plot scale")
        s = self.plot_scale
        return {"DIMTXT": self.paper_text_mm * s,
                "DIMASZ": self.paper_arrow_mm * s,
                "DIMEXO": self.paper_extension_offset_mm * s,
                "DIMEXE": self.paper_extension_extend_mm * s,
                "DIMGAP": self.paper_text_gap_mm * s,
                "DIMDEC": self.decimal_places,
                "DIMLFAC": self.linear_factor,
                "DIMSCALE": 1.0,
                "DIMANNO": 0,
                "DIMSAH": 0,
                "DIMBLK": self.arrow_block,
                "DIMTXSTY": self.text_style,
                "DIMLUNIT": 2}


def configure_dimstyle(session, profile=DimStyleProfile()):
    """Persist variables into a named style, then read actual Document values."""
    doc = session.doc
    if int(doc.GetVariable("INSUNITS")) != 4:
        raise ValueError("DIMSTYLE profile requires INSUNITS=4")
    try:
        style = dynamic(read_with_retry(lambda: doc.TextStyles.Item(profile.text_style), session.policy))
    except Exception:
        style = dynamic(doc.TextStyles.Add(profile.text_style))
    style.SetFont(profile.font, False, False, 134, 0)
    try:
        dim = dynamic(read_with_retry(lambda: doc.DimStyles.Item(profile.name), session.policy))
    except Exception:
        dim = dynamic(doc.DimStyles.Add(profile.name))
    doc.ActiveDimStyle = dim
    expected = profile.variables()
    for name, value in expected.items():
        # DIMANNO is derived from the active style on AutoCAD 2025 and rejects
        # SetVariable; verify the effective value after CopyFrom instead.
        if name == "DIMANNO":
            continue
        try:
            doc.SetVariable(name, value)
        except Exception as exc:
            raise RuntimeError(f"SetVariable({name}={value!r}) failed") from exc
    dim.CopyFrom(doc)
    doc.ActiveDimStyle = dim
    actual = {name: read_with_retry(lambda name=name: doc.GetVariable(name), session.policy) for name in expected}
    mismatches = {name: {"expected": expected[name], "actual": actual[name]}
                  for name in expected if (str(expected[name]).casefold() != str(actual[name]).casefold()
                  and not (isinstance(expected[name], (int, float)) and isinstance(actual[name], (int, float))
                           and abs(float(expected[name])-float(actual[name])) < 1e-6))}
    if str(doc.ActiveDimStyle.Name) != profile.name:
        mismatches["ActiveDimStyle"] = {"expected": profile.name, "actual": str(doc.ActiveDimStyle.Name)}
    if mismatches:
        raise RuntimeError(f"Actual AutoCAD DIMSTYLE readback mismatch: {mismatches}")
    return {"name": profile.name, "font": profile.font, "expected": expected, "actual": actual,
            "parameter_classes": {"drawing_unit_dependent": ["INSUNITS", "DIMLFAC", "DIMLUNIT"],
                                  "scale_dependent": ["DIMTXT", "DIMASZ", "DIMEXO", "DIMEXE", "DIMGAP"],
                                  "fixed_standard": ["DIMDEC", "DIMSCALE", "DIMANNO", "DIMSAH", "DIMTXSTY", "DIMBLK"]}}


def verify_dimstyle(session, profile=DimStyleProfile()):
    """Read persisted style after a disk reopen, including rendered dimension block."""
    doc = session.doc
    expected = profile.variables()
    if str(doc.ActiveDimStyle.Name) != profile.name:
        raise RuntimeError(f"ActiveDimStyle mismatch: {doc.ActiveDimStyle.Name}")
    actual = {key: read_with_retry(lambda key=key: doc.GetVariable(key), session.policy) for key in expected}
    for key, value in expected.items():
        if isinstance(value, (int, float)):
            if abs(float(actual[key]) - float(value)) > 1e-6:
                raise RuntimeError(f"Persisted {key} mismatch: {actual[key]} vs {value}")
        elif str(actual[key]).casefold() != str(value).casefold():
            raise RuntimeError(f"Persisted {key} mismatch: {actual[key]} vs {value}")
    heights = []
    for i in range(int(read_with_retry(lambda: doc.Blocks.Count, session.policy))):
        block = doc.Blocks.Item(i)
        if not str(block.Name).startswith("*D"):
            continue
        for j in range(int(block.Count)):
            ent = block.Item(j)
            if ent.ObjectName in ("AcDbText", "AcDbMText"):
                heights.append(float(ent.Height))
    if not heights or not any(abs(h - expected["DIMTXT"]) < 1e-6 for h in heights):
        raise RuntimeError(f"No persisted dimension text at expected height {expected['DIMTXT']}: {heights}")
    return {"variables": actual, "anonymous_block_text_heights": heights}
