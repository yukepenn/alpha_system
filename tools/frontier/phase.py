"""Frontier phase helper.

``workflow1`` is the minimal-real Workflow 1 runner: it resolves the approved
phase spec, refuses template/draft specs, executes the spec's ``## Validation``
commands, and records results under ``runs/wf1/<PHASE>/`` (local-only, never
committed). ``--stage review-gate`` checks for a committed reviewer verdict.
``review`` does not pretend to review: it prints the review contract and exits
nonzero because reviews are produced by the frontier-review skill / reviewer
agent, not by this CLI.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Template markers emitted by `phase.py new`. A spec still carrying any of
# these has not been authored/approved and must not drive Workflow 1.
PLACEHOLDER_MARKERS = (
    "Define the purpose before execution",
    "TBD",
)
PASSING_VERDICTS = {"PASS", "PASS_WITH_WARNINGS"}


def phase_slug(name: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in name).strip("-") or "phase"


def new_phase(name: str, lane: str, campaign: str) -> int:
    phase_id = f"P{datetime.now(UTC).strftime('%H%M%S')}_{phase_slug(name).upper().replace('-', '_')}"
    spec_dir = ROOT / "specs" / campaign
    spec_dir.mkdir(parents=True, exist_ok=True)
    spec_path = spec_dir / f"{phase_id}-{phase_slug(name)}.md"
    spec_path.write_text(
        "\n".join(
            [
                "---",
                f"campaign_id: {campaign}",
                f"phase_id: {phase_id}",
                f"lane: {lane}",
                "status: draft",
                "---",
                "",
                f"# {phase_id}: {name}",
                "",
                "## Purpose",
                "",
                "Define the purpose before execution.",
                "",
                "## Scope",
                "",
                "- TBD",
                "",
                "## Validation",
                "",
                "- `python tools/verify.py --smoke`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"Created {spec_path.relative_to(ROOT)}")
    return 0


def parse_frontmatter(text: str) -> dict[str, str]:
    """Parse the simple ``key: value`` YAML frontmatter block (stdlib-only)."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fields: dict[str, str] = {}
    for line in text[3:end].splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def find_spec(phase: str, root: Path = ROOT) -> Path | None:
    """Resolve the spec file under ``specs/**`` whose frontmatter phase_id matches."""
    specs_dir = root / "specs"
    if not specs_dir.is_dir():
        return None
    for path in sorted(specs_dir.rglob("*.md")):
        if parse_frontmatter(_read_text(path)).get("phase_id") == phase:
            return path
    return None


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def validation_commands(text: str) -> list[str]:
    """Extract backtick-quoted commands from the spec's ``## Validation`` section."""
    commands: list[str] = []
    in_validation = False
    for line in text.splitlines():
        if line.startswith("## "):
            in_validation = line.strip().lower() == "## validation"
            continue
        if in_validation:
            match = re.search(r"`([^`]+)`", line)
            if match:
                commands.append(match.group(1))
    return commands


def run_validation(phase: str, spec_path: Path, text: str, root: Path = ROOT) -> int:
    commands = validation_commands(text)
    if not commands:
        print(f"Spec {spec_path.relative_to(root)} has no '## Validation' commands; nothing to gate on.")
        return 2
    out_dir = root / "runs" / "wf1" / phase
    out_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, object]] = []
    for command in commands:
        print(f"[wf1:{phase}] $ {command}", flush=True)
        started = time.monotonic()
        argv = shlex.split(command)
        if argv:
            argv[0] = str(Path(argv[0]).expanduser())
        try:
            # Stream output directly to the operator's terminal; record the verdict.
            exit_code = subprocess.run(argv, cwd=root, check=False).returncode if argv else 127
        except OSError as exc:
            print(f"[wf1:{phase}] command failed to start: {exc}", flush=True)
            exit_code = 127
        duration = round(time.monotonic() - started, 3)
        results.append({"command": command, "exit_code": exit_code, "duration_seconds": duration})
        print(f"[wf1:{phase}] exit={exit_code} duration={duration}s", flush=True)
    ok = all(r["exit_code"] == 0 for r in results)
    payload = {
        "phase_id": phase,
        "spec_path": str(spec_path.relative_to(root)),
        "generated_at": datetime.now(UTC).isoformat(),
        "ok": ok,
        "results": results,
    }
    (out_dir / "validation.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = [
        f"# Workflow 1 validation: {phase}",
        "",
        f"- Spec: `{payload['spec_path']}`",
        f"- Generated: {payload['generated_at']}",
        f"- Overall: {'PASS' if ok else 'FAIL'}",
        "",
        "| command | exit | duration (s) |",
        "| --- | --- | --- |",
    ]
    lines += [f"| `{r['command']}` | {r['exit_code']} | {r['duration_seconds']} |" for r in results]
    (out_dir / "validation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Recorded results to {out_dir.relative_to(root)}/validation.json (local-only; never commit runs/).")
    if not ok:
        print(f"Workflow 1 validation FAILED for {phase}.")
        return 1
    print(f"Workflow 1 validation passed for {phase}.")
    return 0


def review_gate(phase: str, campaign_id: str, root: Path = ROOT) -> int:
    verdict_path = root / "reviews" / campaign_id / f"{phase}-verdict.json"
    if not verdict_path.exists():
        print(
            f"Review gate FAILED: {verdict_path.relative_to(root)} is missing. "
            "Reviews are produced by the frontier-review skill / reviewer agent."
        )
        return 2
    try:
        verdict = json.loads(verdict_path.read_text(encoding="utf-8")).get("verdict")
    except (OSError, ValueError):
        verdict = None
    if verdict not in PASSING_VERDICTS:
        print(
            f"Review gate FAILED: {verdict_path.relative_to(root)} has verdict "
            f"{verdict!r}; need PASS or PASS_WITH_WARNINGS from the frontier-review skill."
        )
        return 2
    print(f"Review gate passed for {phase}: verdict={verdict}.")
    return 0


def workflow1(phase: str, stage: str, root: Path = ROOT) -> int:
    spec_path = find_spec(phase, root)
    if spec_path is None:
        print(f"No spec under specs/** declares phase_id {phase}. Author/approve the spec first.")
        return 2
    text = _read_text(spec_path)
    frontmatter = parse_frontmatter(text)
    if stage == "review-gate":
        campaign_id = frontmatter.get("campaign_id", "MANUAL")
        return review_gate(phase, campaign_id, root)
    found = [marker for marker in PLACEHOLDER_MARKERS if marker in text]
    if found:
        print(
            f"Spec {spec_path.relative_to(root)} still contains template placeholders "
            f"({', '.join(found)}); author it before running Workflow 1."
        )
        return 2
    status_value = frontmatter.get("status", "")
    if not status_value or status_value == "draft":
        print(
            f"Spec {spec_path.relative_to(root)} has status {status_value or '<missing>'!s}; "
            "Workflow 1 requires a coordinator-approved spec (status in_progress or later)."
        )
        return 2
    return run_validation(phase, spec_path, text, root)


def review_contract(phase: str) -> int:
    print(f"Review contract for phase {phase}:")
    print("  inputs : AGENTS.md, frontier.yaml, the phase spec, the git diff,")
    print("           the handoff, and recorded validation output")
    print(f"  outputs: reviews/<CAMPAIGN_ID>/{phase}-review.md")
    print(f"           reviews/<CAMPAIGN_ID>/{phase}-verdict.json")
    print("  verdict: PASS | PASS_WITH_WARNINGS | REWORK | BLOCKED")
    print("review is produced by the frontier-review skill / reviewer agent, not this CLI")
    return 1


def status() -> int:
    # Delegate to the single authoritative status reader. The committed
    # ACTIVE_CAMPAIGN.md pointer lags a running campaign (see CRITICAL.md /
    # "Live status authority"), so status_doctor — which reconciles live run
    # state — is the canonical source rather than a second, weaker reader.
    from tools.frontier.status_doctor import main as status_doctor_main

    return status_doctor_main([])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage Frontier phases.")
    subparsers = parser.add_subparsers(dest="command")
    new_parser = subparsers.add_parser("new", help="Create a draft phase spec.")
    new_parser.add_argument("--name", required=True)
    new_parser.add_argument("--lane", default="yellow")
    new_parser.add_argument("--campaign", default="MANUAL")
    subparsers.add_parser("status", help="Show authoritative live status (delegates to status_doctor).")
    workflow_parser = subparsers.add_parser(
        "workflow1", help="Run Workflow 1 for a phase: spec gating + spec validation commands."
    )
    workflow_parser.add_argument("--phase", required=True)
    workflow_parser.add_argument(
        "--stage",
        choices=["validate", "review-gate"],
        default="validate",
        help="validate: run the spec's Validation commands; review-gate: require a committed reviewer verdict.",
    )
    review_parser = subparsers.add_parser(
        "review", help="Print the review contract (reviews are produced by the frontier-review skill)."
    )
    review_parser.add_argument("--phase", required=True)
    args = parser.parse_args(argv)

    if args.command == "new":
        return new_phase(args.name, args.lane, args.campaign)
    if args.command == "status":
        return status()
    if args.command == "workflow1":
        return workflow1(args.phase, args.stage)
    if args.command == "review":
        return review_contract(args.phase)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
