import math
import sys
import tempfile
import unittest
from pathlib import Path

import ezdxf

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from landscape_agent_pack.result import Result
from landscape_agent_pack.cad.angles import arc_angles_deg_to_com, arc_endpoints, arc_bbox
from landscape_agent_pack.cad.annotation import DimStyleProfile
from landscape_agent_pack.cad.geometry_qa import GeometryProfile, analyze_dxf
from landscape_agent_pack.cad.retry import RetryPolicy, read_with_retry, ComBusyTimeout


class AngleTests(unittest.TestCase):
    def test_quadrants_and_cross_zero(self):
        for a, b, start, end in [
            (0, 90, (10, 0), (0, 10)),
            (90, 180, (0, 10), (-10, 0)),
            (350, 10, (10*math.cos(math.radians(350)), 10*math.sin(math.radians(350))),
             (10*math.cos(math.radians(10)), 10*math.sin(math.radians(10))))]:
            p, q = arc_endpoints((0, 0), 10, a, b)
            for actual, expected in zip(p + q, start + end):
                self.assertAlmostEqual(actual, expected, places=8)
            r, s = arc_angles_deg_to_com(a, b)
            self.assertAlmostEqual(r, math.radians(a))
            self.assertAlmostEqual(s, math.radians(b))
        # Positive CCW sweep across zero is 20 degrees.
        r, s = arc_angles_deg_to_com(350, 10)
        self.assertAlmostEqual((s-r) % (2*math.pi), math.radians(20))
        for actual, expected in zip(arc_bbox((0,0), 10, 0, 90), (0,0,10,10)):
            self.assertAlmostEqual(actual, expected, places=8)
        for actual, expected in zip(arc_bbox((0,0), 10, 90, 180), (-10,0,0,10)):
            self.assertAlmostEqual(actual, expected, places=8)
        cross = arc_bbox((0,0), 10, 350, 10)
        self.assertAlmostEqual(cross[2], 10, places=8)
        self.assertLess(cross[1], 0)
        self.assertGreater(cross[3], 0)

    def test_full_circle_requires_circle(self):
        with self.assertRaises(ValueError):
            arc_angles_deg_to_com(0, 360)


class ContractTests(unittest.TestCase):
    def test_mandatory_not_executed_never_passes(self):
        r = Result("x", "check")
        r.add("a", "executed", True, "PASS")
        r.add("b", "missing", True, "NOT_EXECUTED")
        self.assertEqual(r.status, "REVIEW_REQUIRED")
        self.assertEqual(r.exit_code, 1)
        with tempfile.TemporaryDirectory() as tmp:
            j, m = Path(tmp)/"report.json", Path(tmp)/"report.md"
            r.write(j, m)
            self.assertIn('"status": "REVIEW_REQUIRED"', j.read_text())
            self.assertIn('**REVIEW_REQUIRED**', m.read_text())

    def test_no_checks_is_not_pass(self):
        self.assertEqual(Result("x", "empty").status, "REVIEW_REQUIRED")

    def test_dimstyle_scaled_values(self):
        values = DimStyleProfile().variables()
        self.assertEqual(values["DIMTXT"], 250.0)
        self.assertEqual(values["DIMASZ"], 180.0)
        self.assertEqual(values["DIMEXO"], 200.0)
        self.assertEqual(values["DIMEXE"], 120.0)

    def test_busy_retry_bounded_and_nonbusy_raises(self):
        class Busy(Exception):
            hresult = -2147418111
        calls = []
        def f():
            calls.append(1)
            raise Busy("busy")
        with self.assertRaises(ComBusyTimeout):
            read_with_retry(f, RetryPolicy(max_attempts=2, delay=0, timeout=1))
        self.assertEqual(len(calls), 2)
        with self.assertRaises(ValueError):
            read_with_retry(lambda: (_ for _ in ()).throw(ValueError("bad")))


class GeometryTests(unittest.TestCase):
    def test_positive_and_fault_injection(self):
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp)/"good.dxf"
            doc = ezdxf.new()
            doc.layers.new("L-SITE")
            doc.modelspace().add_lwpolyline([(0,0),(10,0),(10,10),(0,10)], close=True, dxfattribs={"layer":"L-SITE"})
            doc.modelspace().add_arc((5,5), 3, start_angle=350, end_angle=10, dxfattribs={"layer":"L-SITE"})
            doc.saveas(good)
            p = GeometryProfile(required_layers=("L-SITE",), closed_layers=("L-SITE",), allowed_bbox=(-1,-1,12,12), expected_entity_count=2)
            r = analyze_dxf(good, p)
            self.assertEqual(r.status, "PASS", r.to_dict())
            doc.modelspace().add_line((1,1),(1,1),dxfattribs={"layer":"L-SITE"})
            doc.modelspace().add_line((2,2),(2.01,2),dxfattribs={"layer":"L-SITE"})
            doc.modelspace().add_lwpolyline([(1,1),(2,1)],dxfattribs={"layer":"L-SITE"})
            bad = Path(tmp)/"bad.dxf"
            doc.saveas(bad)
            b = analyze_dxf(bad, GeometryProfile(required_layers=("L-SITE",), closed_layers=("L-SITE",), allowed_bbox=(-1,-1,12,12), tiny_segment_threshold=0.1))
            self.assertEqual(b.status, "FAIL")
            ids = {c.id for c in b.checks if c.status == "FAIL"}
            self.assertTrue({"ZERO_LINE", "TINY_SEGMENT", "OPEN_REQUIRED"} <= ids, ids)

    def test_empty_model_cannot_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/"empty.dxf"
            ezdxf.new().saveas(p)
            self.assertEqual(analyze_dxf(p, GeometryProfile()).status, "FAIL")


if __name__ == "__main__":
    unittest.main()
