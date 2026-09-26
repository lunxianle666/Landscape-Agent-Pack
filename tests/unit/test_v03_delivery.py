import tempfile
import unittest
from pathlib import Path

from landscape_agent_pack.cad.plot import PlotRequest, select_pdf_device, select_media, wait_for_pdf
from landscape_agent_pack.cad.pdf_qa import PDFProfile, inspect_pdf
from landscape_agent_pack.cad.visual_qa import visual_qa_not_executed
from landscape_agent_pack.result import Result


class PlotContractTests(unittest.TestCase):
    def test_preferred_and_fallback_devices(self):
        devices = ["DWG To PDF.pc3", "AutoCAD PDF (General Documentation).pc3"]
        self.assertEqual(select_pdf_device(devices, "DWG To PDF.pc3"), "DWG To PDF.pc3")
        self.assertEqual(select_pdf_device(devices, "missing.pc3"), "AutoCAD PDF (General Documentation).pc3")
        with self.assertRaises(LookupError):
            select_pdf_device(devices, "missing.pc3", False)
        with self.assertRaises(LookupError):
            select_pdf_device([])

    def test_canonical_media_orientation(self):
        media = ["ISO_A4_(210.00_x_297.00_MM)", "ISO_A4_(297.00_x_210.00_MM)",
                 "ISO_A2_(594.00_x_420.00_MM)", "ISO_A1_(841.00_x_594.00_MM)"]
        self.assertEqual(select_media(media, "A4", "landscape"), media[1])
        self.assertEqual(select_media(media, "A4", "portrait"), media[0])
        self.assertEqual(select_media(media, "A2", "landscape"), media[2])
        self.assertEqual(select_media(media, "A1", "landscape"), media[3])
        with self.assertRaises(LookupError):
            select_media(media, "A3", "landscape")

    def test_invalid_request_and_overwrite_fail_closed(self):
        with self.assertRaises(ValueError):
            PlotRequest("x.pdf", area="window").validate()
        with self.assertRaises(ValueError):
            PlotRequest("x.pdf", overwrite=True).validate()
        with self.assertRaises(ValueError):
            PlotRequest("x.pdf", scale="0:100").validate()

    def test_bounded_wait_times_out(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(TimeoutError):
                wait_for_pdf(Path(root) / "absent.pdf", timeout_s=0.01,
                             poll_s=0.002, stable_polls=2)

    def test_pdf_missing_and_blank_fail(self):
        import pymupdf
        with tempfile.TemporaryDirectory() as root:
            p = Path(root) / "blank.pdf"
            self.assertEqual(inspect_pdf(p, PDFProfile("A4", "landscape")).status, "FAIL")
            doc = pymupdf.open()
            doc.new_page(width=297*72/25.4, height=210*72/25.4)
            doc.save(p)
            doc.close()
            qa = inspect_pdf(p, PDFProfile("A4", "landscape", min_bytes=0))
            self.assertEqual(qa.status, "FAIL")
            self.assertEqual(next(c.status for c in qa.checks if c.id == "NONBLANK"), "FAIL")

    def test_visual_and_mandatory_missing_never_pass(self):
        self.assertEqual(visual_qa_not_executed(task_id="test").status, "REVIEW_REQUIRED")
        probe = Result("test", "probe")
        probe.add("MISSING", "required", True, "NOT_EXECUTED")
        self.assertEqual((probe.status, probe.exit_code), ("REVIEW_REQUIRED", 1))


if __name__ == "__main__":
    unittest.main()
