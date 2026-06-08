"""CLI for local-only scaleout materialization orchestration."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from alpha_system.features.scaleout import (
    DEFAULT_SCALEOUT_CONFIG,
)
from alpha_system.features.scaleout.driver import (
    ScaleoutError,
    load_scaleout_config,
    render_scaleout_summary_markdown,
    run_scaleout,
)


def run_feature_pack(args: argparse.Namespace) -> int:
    """Run ``alpha scaleout feature-pack``."""

    try:
        config = load_scaleout_config(args.config)
        summary = run_scaleout(
            config,
            alpha_data_root=args.alpha_data_root,
            dataset_registry_path=args.dataset_registry,
            canonical_root=args.canonical_root,
            rollout=args.rollout,
            execute=args.execute,
            bounded_year=args.bounded_year,
        )
        if args.summary_out:
            path = Path(args.summary_out)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(render_scaleout_summary_markdown(summary), encoding="utf-8")
        if args.json:
            print(json.dumps(summary.to_dict(), sort_keys=True, indent=2))
        else:
            _emit_text(summary.to_dict())
        return 0 if summary.failed_count == 0 else 2
    except (OSError, ScaleoutError, ValueError) as exc:
        print(f"scaleout command error: {exc}", file=sys.stderr)
        return 2


def register_subparser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the ``alpha scaleout`` command group."""

    scaleout_parser = subparsers.add_parser(
        "scaleout",
        help="Plan or execute governed local-only materialization scaleout.",
    )
    scaleout_subparsers = scaleout_parser.add_subparsers(dest="scaleout_command")

    feature_parser = scaleout_subparsers.add_parser(
        "feature-pack",
        help="Plan or execute governed FeaturePack scaleout.",
    )
    feature_parser.add_argument(
        "--config",
        default=DEFAULT_SCALEOUT_CONFIG,
        help="Feature scaleout config path.",
    )
    feature_parser.add_argument(
        "--execute",
        action="store_true",
        help="Write Parquet values, ledger entries, and registry metadata.",
    )
    feature_parser.add_argument(
        "--rollout",
        choices=("bounded-real", "full-window", "bounded-then-full"),
        default="bounded-then-full",
        help="Rollout mode; default validates bounded-real before full expansion.",
    )
    feature_parser.add_argument(
        "--bounded-year",
        type=int,
        default=None,
        help="Accepted full year used for bounded-real rollout.",
    )
    feature_parser.add_argument(
        "--alpha-data-root",
        help="Local data root for values, registry, ledger, and checkpoints.",
    )
    feature_parser.add_argument(
        "--dataset-registry",
        help="Local DatasetVersion registry path; required with --execute.",
    )
    feature_parser.add_argument(
        "--canonical-root",
        help="Canonical Parquet root; defaults below ALPHA_DATA_ROOT.",
    )
    feature_parser.add_argument(
        "--summary-out",
        help="Optional value-free Markdown summary output path.",
    )
    feature_parser.add_argument("--json", action="store_true", help="Emit JSON.")
    feature_parser.set_defaults(handler=run_feature_pack)


def _emit_text(payload: dict[str, object]) -> None:
    print("Scaleout feature-pack")
    print(f"Campaign: {payload['campaign_id']}")
    print(f"Phase: {payload['phase_id']}")
    print(f"Family: {payload['family']}")
    print(f"Rollout: {payload['rollout']}")
    print(f"Dry run: {'yes' if payload['dry_run'] else 'no'}")
    print(f"Accepted units: {payload['accepted_unit_count']}")
    print(f"Bounded units: {payload['bounded_unit_count']}")
    print(f"Planned: {payload['planned_count']}")
    print(f"Completed: {payload['completed_count']}")
    print(f"Skipped: {payload['skipped_count']}")
    print(f"Failed: {payload['failed_count']}")


__all__ = ["register_subparser", "run_feature_pack"]
