"""One AutoCAD COM boundary for v0.2 CAD build, annotation and validation.

Only automation-owned documents may be mutated. A failed create is uncertain until
its postcondition is read; callers must not replay it automatically.
"""
from dataclasses import dataclass, field
from pathlib import Path
import math

from .angles import arc_angles_deg_to_com
from .retry import read_with_retry, RetryPolicy, hresult


class OwnershipError(RuntimeError):
    pass


class MutationUncertain(RuntimeError):
    pass


class CommandStillRunning(RuntimeError):
    pass


def _com():
    import pythoncom
    import win32com.client as win32
    return pythoncom, win32


def dynamic(obj):
    _, win32 = _com()
    return win32.dynamic.Dispatch(obj._oleobj_)


def point(x, y, z=0):
    pythoncom, win32 = _com()
    return win32.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(x), float(y), float(z)])


def numbers(values):
    pythoncom, win32 = _com()
    return win32.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(v) for v in values])


def connect(progid="AutoCAD.Application.25", *, allow_launch=False, policy=RetryPolicy()):
    _, win32 = _com()
    try:
        raw = read_with_retry(lambda: win32.GetActiveObject(progid), policy)
    except Exception as exc:
        # Only "no running object" authorizes launch. Busy/RPC failures must
        # not silently create another AutoCAD instance.
        if not allow_launch or hresult(exc) != -2147221021:
            raise
        raw = win32.Dispatch(progid)
    return dynamic(raw)


@dataclass
class DocumentSession:
    app: object
    document_object: object
    source_path: str | None
    current_path: str | None
    requested_output_path: str | None
    current_document_name: str
    format: str
    dirty: bool
    ownership: str
    opened_by_automation: bool
    workspace_root: Path
    policy: RetryPolicy = field(default_factory=RetryPolicy)

    @classmethod
    def create(cls, app, *, workspace_root, ownership="automation", policy=RetryPolicy()):
        if ownership != "automation":
            raise OwnershipError("New document requires explicit automation ownership")
        if int(read_with_retry(lambda: app.Documents.Count, policy)) != 0:
            raise OwnershipError("Existing AutoCAD documents detected; refusing automation mutation")
        # Add/Open are state-changing and must never be blindly replayed.
        doc = dynamic(app.Documents.Add())
        root = Path(workspace_root).resolve(strict=True)
        session = cls(app, doc, None, None, None, "", "unsaved", True, ownership, True, root, policy)
        session.refresh()
        return session

    @classmethod
    def open(cls, app, path, *, workspace_root, ownership="automation", policy=RetryPolicy()):
        target = Path(path).resolve(strict=True)
        root = Path(workspace_root).resolve(strict=True)
        if ownership != "automation" or not target.is_relative_to(root):
            raise OwnershipError("Open requires an explicit automation workspace containing the file")
        if int(read_with_retry(lambda: app.Documents.Count, policy)) != 0:
            raise OwnershipError("Existing AutoCAD documents detected; refusing automation open")
        doc = dynamic(app.Documents.Open(str(target)))
        session = cls(app, doc, str(target), None, None, "", target.suffix.lower().lstrip("."), False, ownership, True, root, policy)
        session.refresh(expected=target)
        return session

    def refresh(self, expected=None):
        """Reacquire metadata after every SaveAs/Open; reject target switches."""
        doc = dynamic(self.document_object)
        active = dynamic(read_with_retry(lambda: self.app.ActiveDocument, self.policy))
        if active._oleobj_ != doc._oleobj_:
            raise OwnershipError("ActiveDocument switched; operation refused")
        self.document_object = doc
        self.current_document_name = str(read_with_retry(lambda: doc.Name, self.policy))
        full = str(read_with_retry(lambda: doc.FullName, self.policy))
        self.current_path = str(Path(full).resolve()) if Path(full).is_absolute() else None
        self.format = Path(full).suffix.lower().lstrip(".") if self.current_path else "unsaved"
        self.dirty = not bool(read_with_retry(lambda: doc.Saved, self.policy))
        if expected and (not self.current_path or Path(self.current_path) != Path(expected).resolve()):
            raise OwnershipError(f"Document identity mismatch: expected {expected}, actual {self.current_path}")
        return self

    @property
    def doc(self):
        if self.ownership != "automation" or not self.opened_by_automation:
            raise OwnershipError("Document is not automation-owned")
        self.refresh()
        return self.document_object

    def _target(self, path):
        target = Path(path).resolve()
        if not target.is_relative_to(self.workspace_root):
            raise OwnershipError(f"Output escapes automation workspace: {target}")
        if target.exists():
            raise FileExistsError(f"Refusing overwrite: {target}")
        if not target.parent.is_dir():
            raise FileNotFoundError(f"Output directory missing: {target.parent}")
        return target

    def _create_once(self, label, fn):
        doc = self.doc
        self._require_idle(doc)
        before = int(read_with_retry(lambda: doc.ModelSpace.Count, self.policy))
        try:
            entity = dynamic(fn(doc.ModelSpace))
        except Exception as exc:
            raise MutationUncertain(f"{label} may have created an entity; inspect handles before retry") from exc
        after = int(read_with_retry(lambda: doc.ModelSpace.Count, self.policy))
        if after != before + 1:
            raise MutationUncertain(f"{label} count delta {after-before}; inspect before retry")
        self.dirty = True
        return entity

    def _require_idle(self, doc):
        active = int(read_with_retry(lambda: doc.GetVariable("CMDACTIVE"), self.policy))
        if active:
            raise CommandStillRunning(f"AutoCAD command active ({active}); operation refused")

    def set_units_mm(self):
        doc = self.doc
        doc.SetVariable("INSUNITS", 4)
        doc.SetVariable("MEASUREMENT", 1)
        if int(read_with_retry(lambda: doc.GetVariable("INSUNITS"), self.policy)) != 4:
            raise RuntimeError("INSUNITS readback mismatch")

    def ensure_layer(self, name, *, color=7, lineweight=25):
        doc = self.doc
        existing = {str(read_with_retry(lambda i=i: doc.Layers.Item(i).Name, self.policy))
                    for i in range(int(read_with_retry(lambda: doc.Layers.Count, self.policy)))}
        if name in existing:
            layer = dynamic(read_with_retry(lambda: doc.Layers.Item(name), self.policy))
        else:
            layer = dynamic(doc.Layers.Add(name))
        layer.Color = color
        layer.Lineweight = lineweight
        if str(read_with_retry(lambda: layer.Name, self.policy)) != name:
            raise RuntimeError("Layer name readback mismatch")
        return layer

    def line(self, start, end, layer):
        ent = self._create_once("AddLine", lambda ms: ms.AddLine(point(*start), point(*end)))
        ent.Layer = layer
        return ent

    def polyline(self, points, layer, *, closed=False):
        if len(points) < 2:
            raise ValueError("Polyline needs at least 2 points")
        ent = self._create_once("AddLightWeightPolyline", lambda ms: ms.AddLightWeightPolyline(numbers(v for p in points for v in p)))
        ent.Closed = bool(closed)
        ent.Layer = layer
        return ent

    def circle(self, center, radius, layer):
        ent = self._create_once("AddCircle", lambda ms: ms.AddCircle(point(*center), float(radius)))
        ent.Layer = layer
        return ent

    def arc(self, center, radius, start_deg, end_deg, layer):
        start_rad, end_rad = arc_angles_deg_to_com(start_deg, end_deg)
        ent = self._create_once("AddArc", lambda ms: ms.AddArc(point(*center), float(radius), start_rad, end_rad))
        ent.Layer = layer
        return ent

    def text(self, value, location, height, layer):
        ent = self._create_once("AddText", lambda ms: ms.AddText(str(value), point(*location), float(height)))
        ent.Layer = layer
        return ent

    def mtext(self, value, location, width, height, layer):
        ent = self._create_once("AddMText", lambda ms: ms.AddMText(point(*location), float(width), str(value)))
        ent.Height = float(height)
        ent.Layer = layer
        return ent

    def dim_aligned(self, first, second, text_position, layer):
        ent = self._create_once("AddDimAligned", lambda ms: ms.AddDimAligned(point(*first), point(*second), point(*text_position)))
        ent.Layer = layer
        ent.Update()
        return ent

    def save(self):
        doc = self.doc
        self._require_idle(doc)
        if self.format != "dwg" or not self.current_path:
            raise OwnershipError("Save applies only to current DWG; use explicit SaveAs for other formats")
        if not Path(self.current_path).is_relative_to(self.workspace_root):
            raise OwnershipError("Current document is outside automation workspace")
        doc.Save()
        self.refresh(expected=self.current_path)
        if not Path(self.current_path).is_file():
            raise RuntimeError("DWG Save did not produce a file")

    def save_as(self, path, *, format):
        if format not in {"dwg", "dxf"}:
            raise ValueError("Only DWG and DXF outputs are supported")
        target = self._target(path)
        if target.suffix.lower() != "." + format:
            raise ValueError("Output extension and format differ")
        doc = self.doc
        self._require_idle(doc)
        self.requested_output_path = str(target)
        if format == "dwg":
            doc.SaveAs(str(target))
        else:
            doc.SaveAs(str(target), 13)  # AutoCAD AC1015 DXF enum; verify disk content separately.
        self.refresh(expected=target)
        if not target.is_file():
            raise RuntimeError(f"SaveAs did not produce {target}")
        return target

    def close(self):
        doc = self.doc
        self._require_idle(doc)
        if self.dirty:
            raise OwnershipError("Refusing to discard dirty automation document")
        name = self.current_document_name
        doc.Close(False)
        if any(str(read_with_retry(lambda i=i: self.app.Documents.Item(i).Name, self.policy)) == name
               for i in range(int(read_with_retry(lambda: self.app.Documents.Count, self.policy)))):
            raise RuntimeError(f"Owned document still open: {name}")
        self.opened_by_automation = False

    def snapshot(self):
        doc = self.doc
        return {"name": self.current_document_name, "full_name": self.current_path,
                "format": self.format, "saved": not self.dirty,
                "entities": int(read_with_retry(lambda: doc.ModelSpace.Count, self.policy)),
                "insunits": int(read_with_retry(lambda: doc.GetVariable("INSUNITS"), self.policy))}
