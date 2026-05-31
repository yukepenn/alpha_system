"""Frontier campaign helper."""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def new_campaign(campaign_id: str) -> int:
    campaign_dir = ROOT / "campaigns" / campaign_id
    campaign_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "GOAL.md": f"# {campaign_id} Goal\n\n## Mission\n\nTBD\n",
        "PHASE_PLAN.md": "# Phase Plan\n\n## P01\n\n- Lane: yellow\n- Purpose: TBD\n",
        "campaign.yaml": (
            f"campaign_id: \"{campaign_id}\"\n"
            "workflow: \"workflow2\"\n"
            "driver: \"ralph_frontier_strict\"\n"
            "default_lane: \"yellow\"\n"
            "automation:\n"
            "  auto_generate_phase_specs: true\n"
            "  auto_execute: true\n"
            "  auto_repair: true\n"
            "  auto_review: true\n"
            "  auto_pr: true\n"
            "  auto_merge: true\n"
            "  strict_micro_loop: true\n"
            "  ralph_required: true\n"
        ),
        "ACCEPTANCE.md": "# Acceptance\n\n- TBD\n",
        "RISK_REGISTER.md": "# Risk Register\n\n| Risk | Impact | Mitigation | Status |\n| --- | --- | --- | --- |\n",
        "RUNBOOK.md": "# Runbook\n\n## Commands\n\n- `python tools/verify.py --all`\n",
    }
    for name, content in files.items():
        path = campaign_dir / name
        if not path.exists():
            path.write_text(content, encoding="utf-8")
    print(f"Created or updated campaign scaffold at {campaign_dir.relative_to(ROOT)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage Frontier campaigns.")
    subparsers = parser.add_subparsers(dest="command")
    new_parser = subparsers.add_parser("new", help="Create a campaign scaffold.")
    new_parser.add_argument("--campaign-id", required=True)
    args = parser.parse_args(argv)

    if args.command == "new":
        return new_campaign(args.campaign_id)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
