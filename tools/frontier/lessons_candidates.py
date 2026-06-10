"""Distill per-run friction signals into runs/<run_id>/LESSONS_CANDIDATES.md.

This closes the lessons flywheel: lessons flow INTO every Workflow 2 prompt
(ralph_driver.lessons_prompt_section), and this module makes friction flow OUT
of every run deterministically — no provider call, no cost, works on stopped
runs. The output is raw material, NOT lessons: at campaign closeout a human or
Claude promotes only validated entries into
`.claude/skills/project-skill/lessons.md` (project-skill quality gate), keeping
that file under the 12k-char prompt-injection cap.

Honors `workflow2.update_project_skill_lessons` in frontier.yaml (default on).
Output lives under `runs/**` and is therefore local-only by artifact policy.

Usage:
    python tools/frontier/lessons_candidates.py --run-id <RUN_ID>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_NAME = "LESSONS_CANDIDATES.md"
PASSING = {"PASS", "PASS_WITH_WARNINGS", "MERGED", "DONE"}

HEADER = """# Lessons Candidates (generated, local-only)

Raw friction signals from this run — repairs, non-PASS verdicts, warnings,
blocks. These are NOT lessons yet. At campaign closeout, promote only entries
validated by real work into `.claude/skills/project-skill/lessons.md` (which
the driver injects into every Workflow 2 prompt), and keep that file under the
12k-char injection cap by pruning lessons already encoded in code or guards.
"""


def enabled(root: Path = ROOT) -> bool:
    try:
        import yaml

        config = yaml.safe_load((root / "frontier.yaml").read_text(encoding="utf-8")) or {}
        return bool((config.get("workflow2") or {}).get("update_project_skill_lessons", True))
    except Exception:
        return True


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _string_items(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def phase_signals(phase: dict[str, Any], phase_dir: Path) -> list[str]:
    signals: list[str] = []
    status = str(phase.get("status") or "UNKNOWN")
    if status not in PASSING:
        reason = phase.get("status_reason")
        signals.append(f"Final status `{status}`" + (f" — {reason}" if reason else ""))

    repair_dir = phase_dir / "repair_attempts"
    if repair_dir.is_dir():
        attempts = [entry for entry in repair_dir.iterdir()]
        if attempts:
            signals.append(f"{len(attempts)} repair-attempt artifact(s) under `repair_attempts/`")

    verdict = _load_json(phase_dir / "verdict.json")
    verdict_value = str(verdict.get("verdict") or "")
    if verdict_value and verdict_value not in PASSING:
        signals.append(f"Review verdict `{verdict_value}`")
        # Findings on a passing review are supporting evidence, not friction;
        # only surface them when the verdict itself was not a pass.
        for finding in _string_items(verdict.get("findings")):
            signals.append(f"Review finding: {finding}")
    for warning in _string_items(verdict.get("warnings")):
        signals.append(f"Review warning: {warning}")

    done_check = _load_json(phase_dir / "done_check.json")
    done_value = str(done_check.get("verdict") or "")
    if done_value and done_value not in PASSING:
        signals.append(f"Done-check verdict `{done_value}`")
    for warning in _string_items(done_check.get("warnings")):
        signals.append(f"Done-check warning: {warning}")
    return signals


def render(state: dict[str, Any], run_dir: Path) -> str:
    lines = [HEADER]
    lines.append(f"Run: {state.get('run_id', run_dir.name)}")
    lines.append(f"Campaign: {state.get('campaign_id', 'unknown')}")
    lines.append("")
    any_signal = False
    for phase in state.get("phases", []):
        phase_id = str(phase.get("phase_id") or "UNKNOWN")
        signals = phase_signals(phase, run_dir / "phases" / phase_id)
        if not signals:
            continue
        any_signal = True
        lines.append(f"## {phase_id}")
        lines.append("")
        lines.extend(f"- {signal}" for signal in signals)
        lines.append("")
    if not any_signal:
        lines.append(
            "No friction signals recorded — all phases passed cleanly with no repairs or warnings."
        )
        lines.append("")
    return "\n".join(lines)


def write_for_run(run_dir: Path, state: dict[str, Any], root: Path = ROOT) -> Path | None:
    if not enabled(root):
        return None
    output = run_dir / OUTPUT_NAME
    output.write_text(render(state, run_dir), encoding="utf-8")
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args(argv)
    run_dir = ROOT / "runs" / args.run_id
    state = _load_json(run_dir / "state.json")
    if not state:
        print(f"No readable state.json under runs/{args.run_id}")
        return 1
    output = write_for_run(run_dir, state)
    if output is None:
        print("update_project_skill_lessons is disabled in frontier.yaml; nothing written.")
        return 0
    print(f"wrote {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
