"""Objective, machine-readable PDF inspection; no visual design judgement."""
from dataclasses import dataclass
from pathlib import Path

from landscape_agent_pack.result import Result
from .plot import PAPER_MM


@dataclass(frozen=True)
class PDFProfile:
    paper: str
    orientation: str
    page_count: int = 1
    min_bytes: int = 1000
    dimension_tolerance_mm: float = 1.0
    min_nonwhite_fraction: float = 0.0002
    require_vectors: bool = False


def inspect_pdf(path, profile: PDFProfile, *, task_id="pdf-qa"):
    result = Result(task_id, "PDF objective QA", input={"path": str(path), "profile": vars(profile)})
    p = Path(path)
    if profile.paper not in PAPER_MM or profile.orientation not in {"portrait", "landscape"}:
        raise ValueError("Invalid PDF profile")
    exists = p.is_file()
    result.add("PDF_EXISTS", "PDF exists", True, "PASS" if exists else "FAIL", actual=exists)
    if not exists:
        return result
    size = p.stat().st_size
    result.add("PDF_SIZE", "PDF byte size", True, "PASS" if size >= profile.min_bytes else "FAIL",
               expected=f">={profile.min_bytes}", actual=size)
    try:
        import pymupdf
        pdf = pymupdf.open(str(p))
    except Exception as exc:
        result.add("PDF_OPEN", "PDF is readable", True, "FAIL", actual=str(exc))
        return result
    try:
        count = len(pdf)
        result.add("PAGE_COUNT", "Expected page count", True, "PASS" if count == profile.page_count else "FAIL",
                   expected=profile.page_count, actual=count)
        widths = []
        heights = []
        media_boxes = []
        nonwhite = []
        vector_counts = []
        text_counts = []
        for page in pdf:
            box = page.mediabox
            media_boxes.append([box.x0, box.y0, box.x1, box.y1])
            widths.append(box.width * 25.4 / 72.0)
            heights.append(box.height * 25.4 / 72.0)
            pix = page.get_pixmap(matrix=pymupdf.Matrix(0.5, 0.5), colorspace=pymupdf.csGRAY, alpha=False)
            samples = pix.samples
            nonwhite.append(sum(v < 245 for v in samples) / max(1, len(samples)))
            vector_counts.append(len(page.get_drawings()))
            text_counts.append(len(page.get_text().strip()))
        expected_w, expected_h = PAPER_MM[profile.paper]
        if profile.orientation == "portrait":
            expected_w, expected_h = expected_h, expected_w
        dims_ok = bool(widths) and all(abs(w-expected_w) <= profile.dimension_tolerance_mm and
                                      abs(h-expected_h) <= profile.dimension_tolerance_mm
                                      for w, h in zip(widths, heights))
        result.add("MEDIA_BOX", "Valid PDF MediaBox", True,
                   "PASS" if media_boxes and all(b[2] > b[0] and b[3] > b[1] for b in media_boxes) else "FAIL",
                   actual=media_boxes)
        result.add("PAGE_DIMENSIONS", "Expected paper width and height", True, "PASS" if dims_ok else "FAIL",
                   expected=[expected_w, expected_h], actual=list(zip(widths, heights)))
        orientation_ok = bool(widths) and all((w > h) == (profile.orientation == "landscape")
                                             for w, h in zip(widths, heights))
        result.add("ORIENTATION", "Expected orientation", True, "PASS" if orientation_ok else "FAIL",
                   expected=profile.orientation, actual=list(zip(widths, heights)))
        ink_ok = bool(nonwhite) and all(x >= profile.min_nonwhite_fraction for x in nonwhite)
        result.add("NONBLANK", "Rendered page has nonwhite content", True,
                   "PASS" if ink_ok else "FAIL", expected=f">={profile.min_nonwhite_fraction}", actual=nonwhite)
        result.add("VECTOR_CONTENT", "PDF vector paths", profile.require_vectors,
                   "PASS" if vector_counts and all(x > 0 for x in vector_counts) else "FAIL", actual=vector_counts)
        result.add("TEXT_CONTENT", "Extractable text characters", False,
                   "PASS" if text_counts and all(x > 0 for x in text_counts) else "WARN", actual=text_counts)
        result.metrics = {"bytes": size, "page_count": count, "widths_mm": widths,
                          "heights_mm": heights, "mediabox_pt": media_boxes,
                          "nonwhite_fraction": nonwhite, "vector_count": vector_counts,
                          "text_character_count": text_counts}
        result.artifacts.append(str(p.resolve()))
    except Exception as exc:
        result.add("PDF_INSPECTION", "PDF inspection completed", True, "FAIL", actual=str(exc))
    finally:
        pdf.close()
    return result
