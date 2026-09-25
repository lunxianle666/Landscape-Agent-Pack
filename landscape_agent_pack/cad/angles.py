"""Public Arc input is degrees; AutoCAD COM receives radians exactly once."""
import math


def arc_angles_deg_to_com(start_deg: float, end_deg: float) -> tuple[float, float]:
    for value in (start_deg, end_deg):
        if not math.isfinite(value):
            raise ValueError("Arc angle must be finite degrees")
    start = math.radians(start_deg % 360.0)
    end = math.radians(end_deg % 360.0)
    if math.isclose(start, end, abs_tol=1e-12):
        raise ValueError("Coincident endpoints cannot represent a full circle; use Circle")
    return start, end


def arc_endpoints(center, radius, start_deg, end_deg):
    if radius <= 0 or not math.isfinite(radius):
        raise ValueError("Positive finite radius required")
    a, b = arc_angles_deg_to_com(start_deg, end_deg)
    return ((center[0] + radius * math.cos(a), center[1] + radius * math.sin(a)),
            (center[0] + radius * math.cos(b), center[1] + radius * math.sin(b)))


def arc_bbox(center, radius, start_deg, end_deg):
    """Exact XY bounding box of the positive CCW arc, including cardinal extrema."""
    a, b = arc_angles_deg_to_com(start_deg, end_deg)
    sweep = (b-a) % (2*math.pi)
    angles = [a, b]
    for cardinal in (0, math.pi/2, math.pi, 3*math.pi/2):
        if (cardinal-a) % (2*math.pi) <= sweep + 1e-12:
            angles.append(cardinal)
    points = [(center[0] + radius*math.cos(t), center[1] + radius*math.sin(t)) for t in angles]
    return min(p[0] for p in points), min(p[1] for p in points), max(p[0] for p in points), max(p[1] for p in points)
