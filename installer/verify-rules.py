"""Read-only rule-loading verification for Landscape Agent Pack.

Run from anywhere; it locates the Pack root automatically (parent of this
installer/ directory). Does NOT modify anything, does NOT start AutoCAD or
SketchUp, does NOT install dependencies, does NOT touch the registry.

It proves the rule files exist and are readable so an Agent (or the user)
can show it actually has the rules on disk before drawing.

Exit code: 0 = all core rules present; 1 = a core rule is missing.
"""
import argparse
import sys
from pathlib import Path

# Source-tree checklist (default): full Pack repository.
CHECKS = [
    ("AGENT_CONTEXT.md", True, "AGENT_CONTEXT"),
    ("standards/landscape-workflow.md", True, "Landscape workflow"),
    ("standards/autocad-safety-rules.md", True, "AutoCAD rules"),
    ("guards/README.md", True, "Guard policy"),
    ("guards/creation_guard.py", True, "Guard code"),
    ("docs/LIMITATIONS.md", True, "Limitations"),
    ("docs/THREE_STEP_CHECK_CN.md", True, "Three-step check"),
    ("prompts/QUICK_PROMPTS_CN.md", True, "Prompt templates"),
    ("skills/sketchup-from-cad-landscape/SKILL.md", False, "SketchUp rules"),
]

# Packed checklist: minimal runtime rule set copied to <InstallRoot>\pack-rules.
PACKED_CHECKS = [
    ("AGENT_CONTEXT.md", True, "AGENT_CONTEXT"),
    ("standards/landscape-workflow.md", True, "Landscape workflow"),
    ("standards/autocad-safety-rules.md", True, "AutoCAD rules"),
    ("guards/README.md", True, "Guard policy"),
    ("docs/LIMITATIONS.md", True, "Limitations"),
    ("docs/THREE_STEP_CHECK_CN.md", True, "Three-step check"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None, help="Rule root to check (default: parent of this installer/ dir)")
    ap.add_argument("--packed", action="store_true", help="Check the minimal packed rule set (pack-rules dir)")
    args = ap.parse_args()

    root = Path(args.root) if args.root else Path(__file__).resolve().parent.parent
    checks = PACKED_CHECKS if args.packed else CHECKS
    print("Landscape Agent Pack Rule Check")
    print(f"root: {root}")

    fail = 0
    for rel, required, label in checks:
        p = root / rel
        readable = False
        try:
            readable = p.is_file() and bool(p.read_bytes())
        except OSError:
            readable = False
        if readable:
            status = "PASS" if required else "OPTIONAL"
        else:
            status = "MISSING" if required else "OPTIONAL"
            if required:
                fail += 1
        # Pad label to align PASS column
        print(f"{label:<20} {status}")

    print("-" * 32)
    print(f"FINAL: {'PASS' if fail == 0 else 'FAIL'}")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
