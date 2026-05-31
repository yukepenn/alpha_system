"""Frontier phase helper."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


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


def status() -> int:
    active = ROOT / "ACTIVE_CAMPAIGN.md"
    print(active.read_text(encoding="utf-8") if active.exists() else "No ACTIVE_CAMPAIGN.md found.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage Frontier phases.")
    subparsers = parser.add_subparsers(dest="command")
    new_parser = subparsers.add_parser("new", help="Create a draft phase spec.")
    new_parser.add_argument("--name", required=True)
    new_parser.add_argument("--lane", default="yellow")
    new_parser.add_argument("--campaign", default="MANUAL")
    subparsers.add_parser("status", help="Show active campaign.")
    workflow_parser = subparsers.add_parser("workflow1", help="Preview Workflow 1 phase execution.")
    workflow_parser.add_argument("--phase", required=True)
    review_parser = subparsers.add_parser("review", help="Preview review request.")
    review_parser.add_argument("--phase", required=True)
    args = parser.parse_args(argv)

    if args.command == "new":
        return new_phase(args.name, args.lane, args.campaign)
    if args.command == "status":
        return status()
    if args.command == "workflow1":
        print(f"Workflow 1 scaffold for phase {args.phase}.")
        return 0
    if args.command == "review":
        print(f"Review scaffold for phase {args.phase}.")
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
