"""Delivery gate with real synthetic DXF/PDF files and simulated COM evidence."""
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import ezdxf
import pymupdf

from landscape_agent_pack.cad.delivery import DeliveryEvidence, validate_delivery
from landscape_agent_pack.cad.geometry_qa import GeometryProfile
from landscape_agent_pack.cad.pdf_qa import PDFProfile, inspect_pdf
from landscape_agent_pack.result import Result


class DeliveryEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(self.enterContext(TemporaryDirectory()))
        root = self.base / "交付 样例"
        root.mkdir()
        self.dwg, self.dxf, self.pdf = (root / name for name in ("图.dwg", "图.dxf", "图.pdf"))
        self.dwg.write_bytes(b"DWG size sentinel, not an AutoCAD file" * 40)
        doc = ezdxf.new(units=4)
        doc.modelspace().add_line((0, 0), (1000, 0))
        doc.saveas(self.dxf)
        with pymupdf.open() as pdf:
            page = pdf.new_page(width=297 * 72 / 25.4, height=210 * 72 / 25.4)
            page.draw_rect((50, 60, 200, 180), fill=(0, 0, 0))
            page.insert_text((80, 220), "Synthetic fixture")
            pdf.save(self.pdf)
        self.snapshot = {"saved": True, "full_name": str(self.dwg), "entities": 1, "insunits": 4}
        self.evidence = DeliveryEvidence(
            str(root), str(self.dwg), str(self.dxf),
            tuple(map(str, (self.dwg, self.dxf, self.pdf, root / "future-report.json"))),
            self.snapshot, self.snapshot.copy(), True, True, True,
            (self.plot(self.pdf),), (self.inspect(self.pdf),),
        )

    @staticmethod
    def plot(path):
        result = Result("synthetic-plot", "Simulated plot", output={"pdf": str(path)})
        result.add("WRITTEN", "Plot completed", True, "PASS")
        return result

    @staticmethod
    def inspect(path):
        return inspect_pdf(path, PDFProfile("A4", "landscape", min_bytes=0, require_vectors=True))

    def validate(self, evidence=None):
        return validate_delivery(evidence or self.evidence, GeometryProfile(expected_entity_count=1))

    def assert_failed(self, evidence, check):
        result = self.validate(evidence)
        self.assertEqual(result.status, "FAIL")
        self.assertIn(check, {c.id for c in result.checks if c.status == "FAIL"})
        return result

    def test_scoped_synthetic_delivery_keeps_visual_review_pending(self):
        result = self.validate()
        self.assertEqual(self.evidence.pdf_results[0].status, "PASS")
        self.assertEqual(result.status, "PASS_WITH_WARNINGS")
        expected_artifacts = {str(path.resolve()) for path in (self.dwg, self.dxf, self.pdf)}
        self.assertEqual(set(result.artifacts), expected_artifacts)
        self.assertIn("VISUAL_QA", {c.id for c in result.checks if c.status == "NOT_EXECUTED"})

    def test_external_pdf_never_counts_as_coverage_or_artifact(self):
        external = self.base / "其他 图.pdf"
        external.write_bytes(self.pdf.read_bytes())
        expected = (str(self.dwg), str(self.dxf), str(self.pdf), str(external))
        changed = replace(self.evidence, expected_outputs=expected,
                          plot_results=(self.plot(external),), pdf_results=(self.inspect(external),))
        result = self.assert_failed(changed, "PDF_COVERAGE")
        self.assertIn("OUTPUT_SCOPE", {c.id for c in result.checks if c.status == "FAIL"})
        self.assertNotIn(str(external.resolve()), result.artifacts)

    def test_duplicate_or_missing_result_rows_do_not_cover_two_plots(self):
        for extra in (self.plot(self.pdf), Result("missing-path", "Plot", checks=self.plot(self.pdf).checks)):
            with self.subTest(extra=extra.task_id):
                changed = replace(self.evidence, plot_results=(self.plot(self.pdf), extra),
                                  pdf_results=(self.inspect(self.pdf), self.inspect(self.pdf)))
                self.assert_failed(changed, "PDF_COVERAGE")

    def test_two_incomplete_snapshots_do_not_match(self):
        incomplete = {"saved": True, "full_name": str(self.dwg)}
        self.assert_failed(replace(self.evidence, saved_snapshot=incomplete,
                                  reopened_snapshot=incomplete.copy()), "REOPEN_CONTENT")

    def test_missing_required_artifact_and_undeclared_output(self):
        self.pdf.unlink()
        self.assert_failed(self.evidence, "PDF_COVERAGE")
        (self.dwg.parent / "unexpected.txt").write_bytes(b"extra")
        self.assert_failed(self.evidence, "KNOWN_OUTPUTS")
        self.assert_failed(replace(self.evidence, expected_outputs=(str(self.dwg),)), "REQUIRED_OUTPUTS")
