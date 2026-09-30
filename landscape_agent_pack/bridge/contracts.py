"""Immutable Phase 4 Bridge input; no silent unit conversion or overwrite."""
from dataclasses import asdict, dataclass, field
from pathlib import Path
import hashlib
import math


@dataclass(frozen=True)
class BridgeRequest:
    workspace: str
    source_cad: str
    source_format: str
    source_units: str
    source_insunits: int
    expected_su_units: str
    startup_model: str
    output_skp: str
    source_sha256: str
    bridge_mode: str = "MIXED_Z"
    tag_handling: str = "PRESERVE_CAD_LAYERS"
    preserve_origin: bool = True
    merge_coplanar_faces: bool = False
    import_materials: bool = False
    coordinate_tolerance_mm: float = 0.1
    bbox_tolerance_mm: float = 0.1
    curve_tolerance_mm: float = 1.0
    expected_layers: tuple[str, ...] = field(default_factory=tuple)

    def validate(self):
        root = Path(self.workspace).resolve(strict=True)
        source = Path(self.source_cad).resolve(strict=True)
        startup = Path(self.startup_model).resolve(strict=True)
        output = Path(self.output_skp).resolve()
        for p in (source, startup, output):
            if not p.is_relative_to(root):
                raise ValueError(f"Bridge path escapes isolated workspace: {p}")
        if self.source_format not in {"dwg", "dxf"} or source.suffix.lower() != "." + self.source_format:
            raise ValueError("Source format must match a DWG or DXF extension")
        if startup.suffix.lower() != ".skp" or output.suffix.lower() != ".skp":
            raise ValueError("Startup and output must be SKP")
        if output.exists():
            raise FileExistsError(f"Refusing existing SKP: {output}")
        if not output.parent.is_dir():
            raise FileNotFoundError(output.parent)
        if self.source_units != "mm" or self.source_insunits != 4 or self.expected_su_units != "mm":
            raise ValueError("Phase 4 requires verified CAD millimetres and target millimetres")
        if self.bridge_mode not in {"PLANAR_2D", "MIXED_Z"}:
            raise ValueError("Bridge mode must explicitly describe Z support")
        if self.tag_handling != "PRESERVE_CAD_LAYERS" or not self.preserve_origin:
            raise ValueError("Phase 4 requires preserved CAD layers and origin")
        if not all(math.isfinite(v) and v > 0 for v in (
                self.coordinate_tolerance_mm, self.bbox_tolerance_mm, self.curve_tolerance_mm)):
            raise ValueError("Tolerances must be finite and positive")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if digest.casefold() != self.source_sha256.casefold():
            raise ValueError("CAD source hash mismatch")
        if self.source_format == "dxf":
            import ezdxf
            doc = ezdxf.readfile(source)
            if int(doc.header.get("$INSUNITS", -1)) != 4:
                raise ValueError("DXF $INSUNITS is not millimetres")
        return self

    def to_dict(self):
        return asdict(self)
