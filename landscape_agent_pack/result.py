"""Shared machine-readable result contract. Missing mandatory work never passes."""
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import json

CHECK_STATUSES = {"PASS", "FAIL", "WARN", "NOT_EXECUTED", "ERROR", "SKIPPED", "MANUAL_INTERVENTION_REQUIRED"}


def now():
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Check:
    id: str
    name: str
    mandatory: bool
    status: str
    expected: object = None
    actual: object = None
    message: str = ""

    def __post_init__(self):
        if self.status not in CHECK_STATUSES:
            raise ValueError(f"Unknown check status: {self.status}")


def aggregate(checks):
    mandatory = [c for c in checks if c.mandatory]
    if any(c.status in {"FAIL", "ERROR"} for c in mandatory):
        return "FAIL"
    if any(c.status == "MANUAL_INTERVENTION_REQUIRED" for c in mandatory):
        return "MANUAL_INTERVENTION_REQUIRED"
    if any(c.status in {"NOT_EXECUTED", "SKIPPED"} for c in mandatory):
        return "REVIEW_REQUIRED"
    if any(c.status in {"WARN", "FAIL", "ERROR", "NOT_EXECUTED", "SKIPPED", "MANUAL_INTERVENTION_REQUIRED"} for c in checks):
        return "PASS_WITH_WARNINGS"
    return "PASS" if mandatory else "REVIEW_REQUIRED"


@dataclass
class Result:
    task_id: str
    operation: str
    input: dict = field(default_factory=dict)
    output: dict = field(default_factory=dict)
    checks: list[Check] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    software: str = ""
    software_version: str = ""
    environment: dict = field(default_factory=dict)
    metrics: dict = field(default_factory=dict)
    started_at: str = field(default_factory=now)
    finished_at: str = ""

    @property
    def status(self):
        state = aggregate(self.checks)
        if self.errors and state not in {"FAIL", "MANUAL_INTERVENTION_REQUIRED"}:
            return "FAIL"
        if self.warnings and state == "PASS":
            return "PASS_WITH_WARNINGS"
        return state

    @property
    def exit_code(self):
        return 0 if self.status in {"PASS", "PASS_WITH_WARNINGS"} else 1

    def add(self, id, name, mandatory, status, expected=None, actual=None, message=""):
        self.checks.append(Check(id, name, mandatory, status, expected, actual, message))

    def finish(self):
        self.finished_at = now()

    def to_dict(self):
        return {**asdict(self), "status": self.status, "exit_code": self.exit_code}

    def write(self, json_path, md_path):
        self.finish()
        j, m = Path(json_path), Path(md_path)
        j.parent.mkdir(parents=True, exist_ok=True)
        m.parent.mkdir(parents=True, exist_ok=True)
        j.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        lines = [f"# {self.operation}", "", f"Task: `{self.task_id}`", f"Status: **{self.status}**", f"Exit code: `{self.exit_code}`", "", "| Check | Mandatory | Status | Message |", "|---|---|---|---|"]
        for c in self.checks:
            lines.append(f"| {c.id} {c.name} | {c.mandatory} | {c.status} | {c.message.replace('|', '/').replace(chr(10), ' ')} |")
        lines += ["", "## Warnings", ""] + [f"- {x}" for x in self.warnings]
        lines += ["", "## Errors", ""] + [f"- {x}" for x in self.errors]
        m.write_text("\n".join(lines) + "\n", encoding="utf-8")
