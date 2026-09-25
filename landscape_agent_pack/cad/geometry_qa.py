"""Offline, parameterized DXF geometry QA. Checks report coverage explicitly."""
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import math

import ezdxf
from ezdxf import bbox

from landscape_agent_pack.result import Result


@dataclass(frozen=True)
class GeometryProfile:
    tiny_segment_threshold: float = 0.1
    duplicate_tolerance: float = 1e-5
    allowed_bbox: tuple[float, float, float, float] | None = None
    required_layers: tuple[str, ...] = ()
    allowed_layers: tuple[str, ...] | None = None
    closed_layers: tuple[str, ...] = ()
    expected_entity_count: int | None = None
    empty_layer_policy: str = "WARN"


def _rounded(values, tolerance):
    return tuple(round(float(v) / tolerance) for v in values)


def _signature(e, tolerance):
    kind = e.dxftype()
    layer = e.dxf.layer
    if kind == "LINE":
        a, b = _rounded(e.dxf.start, tolerance), _rounded(e.dxf.end, tolerance)
        return kind, layer, *sorted((a, b))
    if kind == "CIRCLE":
        return kind, layer, _rounded(e.dxf.center, tolerance), round(e.dxf.radius / tolerance)
    if kind == "LWPOLYLINE":
        points = tuple(_rounded(p, tolerance) for p in e.get_points("xy"))
        return kind, layer, bool(e.closed), points
    return None


def analyze_dxf(path, profile: GeometryProfile, *, task_id="geometry-qa"):
    result = Result(task_id, "CAD geometry QA", input={"dxf": str(path), "profile": vars(profile)}, software="ezdxf", software_version=ezdxf.__version__)
    if profile.tiny_segment_threshold <= 0 or profile.duplicate_tolerance <= 0 or profile.empty_layer_policy not in {"PASS", "WARN", "FAIL"}:
        raise ValueError("Invalid geometry QA profile")
    try:
        doc = ezdxf.readfile(str(path))
        entities = list(doc.modelspace())
    except Exception as exc:
        result.add("DXF_READ", "DXF is readable", True, "FAIL", actual=str(exc))
        return result
    result.add("DXF_READ", "DXF is readable", True, "PASS", actual=str(Path(path).resolve()))
    result.add("NONEMPTY", "ModelSpace contains entities", True, "PASS" if entities else "FAIL", actual=len(entities))
    types = Counter(e.dxftype() for e in entities)
    layers = Counter(e.dxf.layer for e in entities)
    polylines = [e for e in entities if e.dxftype() == "LWPOLYLINE"]
    result.metrics = {"entity_count": len(entities), "entity_types": dict(types), "layer_counts": dict(layers),
                      "open_polylines": sum(not e.closed for e in polylines),
                      "closed_polylines": sum(bool(e.closed) for e in polylines)}
    if entities:
        all_bounds = bbox.extents(entities)
        if all_bounds.has_data:
            result.metrics["model_bbox"] = [all_bounds.extmin.x, all_bounds.extmin.y,
                                            all_bounds.extmax.x, all_bounds.extmax.y]
    if profile.expected_entity_count is None:
        result.add("ENTITY_COUNT", "Entity count", False, "PASS", actual=len(entities))
    else:
        result.add("ENTITY_COUNT", "Entity count", True, "PASS" if len(entities) == profile.expected_entity_count else "FAIL", expected=profile.expected_entity_count, actual=len(entities))
    missing = sorted(set(profile.required_layers) - set(layers))
    unexpected = sorted(set(layers) - set(profile.allowed_layers)) if profile.allowed_layers is not None else []
    empty = sorted(name for name in profile.required_layers if name in doc.layers and layers[name] == 0)
    result.add("REQUIRED_LAYERS", "Required layers have entities", True, "FAIL" if missing else "PASS", expected=profile.required_layers, actual=dict(layers), message=f"missing: {missing}")
    result.add("UNEXPECTED_LAYERS", "Unexpected layers", profile.allowed_layers is not None, "FAIL" if unexpected else "PASS", actual=unexpected)
    result.add("EMPTY_LAYERS", "Empty required layers", False, profile.empty_layer_policy if empty else "PASS", actual=empty)
    zero, tiny, degenerate, open_required, duplicates, bad_arcs, unbounded, unknown_extents = ([] for _ in range(8))
    seen = {}
    bounds = profile.allowed_bbox
    for e in entities:
        kind = e.dxftype()
        handle = e.dxf.handle
        signature = _signature(e, profile.duplicate_tolerance)
        if signature is not None:
            if signature in seen:
                duplicates.append({"handle": handle, "same_as": seen[signature]})
            else:
                seen[signature] = handle
        if kind == "LINE":
            length = (e.dxf.end - e.dxf.start).magnitude
            if length <= profile.duplicate_tolerance:
                zero.append(handle)
            elif length < profile.tiny_segment_threshold:
                tiny.append({"handle": handle, "length": length})
        elif kind == "LWPOLYLINE":
            points = list(e.get_points("xy"))
            if len(points) < 2 or (e.closed and len(points) < 3):
                degenerate.append({"handle": handle, "reason": "insufficient vertices"})
            if e.dxf.layer in profile.closed_layers and not e.closed:
                open_required.append(handle)
            pairs = list(zip(points, points[1:] + (points[:1] if e.closed else [])))
            for a, b in pairs:
                length = math.dist(a, b)
                if length <= profile.duplicate_tolerance:
                    degenerate.append({"handle": handle, "reason": "zero segment"})
                elif length < profile.tiny_segment_threshold:
                    tiny.append({"handle": handle, "length": length})
            if e.closed and len({_rounded(p, profile.duplicate_tolerance) for p in points}) < 3:
                degenerate.append({"handle": handle, "reason": "closed with fewer than 3 unique vertices"})
        elif kind == "ARC":
            if not math.isfinite(e.dxf.radius) or e.dxf.radius <= 0 or not math.isfinite(e.dxf.start_angle) or not math.isfinite(e.dxf.end_angle):
                bad_arcs.append(handle)
        elif kind == "CIRCLE" and (not math.isfinite(e.dxf.radius) or e.dxf.radius <= 0):
            bad_arcs.append(handle)
        if bounds:
            try:
                ext = bbox.extents([e])
                if not ext.has_data:
                    unknown_extents.append(handle)
                elif ext.extmin.x < bounds[0] or ext.extmin.y < bounds[1] or ext.extmax.x > bounds[2] or ext.extmax.y > bounds[3]:
                    unbounded.append({"handle": handle, "bbox": [ext.extmin.x, ext.extmin.y, ext.extmax.x, ext.extmax.y]})
            except Exception:
                unknown_extents.append(handle)
    for id, name, problems, mandatory in [
        ("ZERO_LINE", "Zero length lines", zero, True),
        ("TINY_SEGMENT", "Tiny segments", tiny, True),
        ("DEGENERATE_POLYLINE", "Degenerate polylines", degenerate, True),
        ("OPEN_REQUIRED", "Required closed polylines", open_required, bool(profile.closed_layers)),
        ("DUPLICATE_GEOMETRY", "Duplicate geometry", duplicates, True),
        ("ARC_SANITY", "Arc and circle sanity", bad_arcs, True),
        ("COORDINATE_RANGE", "Coordinate range", unbounded, bounds is not None),
        ("EXTENT_COVERAGE", "Bounding box coverage", unknown_extents, bounds is not None),
    ]:
        result.add(id, name, mandatory, "FAIL" if problems else "PASS", actual=problems)
    return result
