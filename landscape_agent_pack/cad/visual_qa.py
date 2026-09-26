"""Explicit handoff boundary for future visual review of rendered sheets."""
from landscape_agent_pack.result import Result


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
