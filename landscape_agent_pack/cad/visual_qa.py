"""Explicit handoff boundary for future visual review of rendered sheets."""
from landscape_agent_pack.result import Result
from pathlib import Path
import hashlib


def visual_qa_not_executed(*, task_id, rendered_page=None, screenshot=None,
                           design_intent=None, checklist=None):
    result = Result(task_id, "CAD visual QA", input={
        "rendered_page": str(rendered_page) if rendered_page else None,
        "screenshot": str(screenshot) if screenshot else None,
        "design_intent": design_intent,
        "checklist": checklist or [],
    })
    result.add("VISUAL_QA", "Visual judgement", True, "NOT_EXECUTED",
               message="No visual judgement was performed")
    return result


def visual_qa_reviewed(*, task_id, evidence, reviewer, observations, warnings=()):
    """Record an actual review; never infer visual success from numeric checks.

    Each evidence row binds the source artifact and the viewed raster by SHA256.
    Observations must contain explicit booleans for every requested checklist item.
    This recorder verifies provenance, not the reviewer's visual judgement.
    """
    if not reviewer or not evidence or not observations:
        raise ValueError('Reviewer, evidence and explicit observations are required')
    for row in evidence:
        for kind in ('artifact', 'image'):
            path = Path(row[kind]).resolve(strict=True)
            if hashlib.sha256(path.read_bytes()).hexdigest() != row[kind + '_sha256']:
                raise ValueError('Changed visual evidence: ' + str(path))
    if any(type(value) is not bool for value in observations.values()):
        raise ValueError('Every visual observation must be an explicit boolean')
    result = Result(task_id, 'Recorded visual review', input={
        'reviewer': reviewer, 'evidence': evidence, 'observations': observations})
    result.add('VISUAL_QA', 'Reviewed raster evidence', True,
               'PASS' if all(observations.values()) else 'FAIL')
    result.warnings.extend(warnings)
    result.output['visual_status'] = ('VISUAL_FAIL' if not all(observations.values()) else
                                     'VISUAL_PASS_WITH_WARNINGS' if warnings else 'VISUAL_PASS')
    return result
