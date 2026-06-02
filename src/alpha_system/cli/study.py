"""Study CLI command group for factor diagnostics."""

from __future__ import annotations

import argparse
import json
import sys

from alpha_system.research.diagnostics import DiagnosticsError, run_study
from alpha_system.research.study_config import StudyConfigError, load_study_config
from alpha_system.research.study_outputs import StudyOutputError


def run_study_cli(args: argparse.Namespace) -> int:
    """Run ``alpha study run``."""
    config_path = args.config or args.config_path
    if not config_path:
        print("study command error: provide a study config path", file=sys.stderr)
        return 2
    if args.config and args.config_path:
        print("study command error: provide either CONFIG_PATH or --config, not both", file=sys.stderr)
        return 2
    try:
        config = load_study_config(config_path).with_overrides(
            factor_version=args.factor_version,
            label_version=args.label_version,
            data_version=args.data_version,
            factor_values_path=args.factor_values_path,
            labels_path=args.labels_path,
            horizon_seconds=args.horizon_seconds,
            instruments=tuple(args.instrument or ()) or None,
            sessions=tuple(args.session_id or ()) or None,
            start_ts=args.start_ts,
            end_ts=args.end_ts,
            output_dir=args.output_dir,
            registry_path=args.registry_path,
            manifest_path=args.manifest_out,
            min_total=args.min_sample_size,
        )
        result = run_study(config)
    except (
        DiagnosticsError,
        StudyConfigError,
        StudyOutputError,
        OSError,
        ValueError,
    ) as exc:
        print(f"study command error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
        return 0

    summary = result.summary
    print("Study command: run")
    print(f"Study: {summary.study_id}")
    print(f"Factor: {summary.factor_id} {summary.factor_version}")
    print(f"Label: {summary.label_id} {summary.label_version}")
    print(f"Data version: {summary.data_version}")
    print(f"Samples: {summary.sample_size}")
    print(f"Warnings: {len(summary.warnings)}")
    print(f"Summary: {result.output_paths.summary_path}")
    print(f"Manifest: {result.output_paths.manifest_path}")
    if result.registry_path is not None:
        print(f"Registry: {result.registry_path}")
        print(f"Registry written: {'yes' if result.registry_written else 'no'}")
    return 0


def register_subparser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the ``alpha study`` command group."""
    study_parser = subparsers.add_parser(
        "study",
        help="Run Tier 0 factor diagnostics on versioned local inputs.",
    )
    study_subparsers = study_parser.add_subparsers(dest="study_command")

    run_parser = study_subparsers.add_parser(
        "run",
        help="Run factor diagnostics and write a local summary plus manifest.",
    )
    run_parser.add_argument(
        "config_path",
        nargs="?",
        help="Path to a JSON study config.",
    )
    run_parser.add_argument(
        "--config",
        help="Path to a JSON study config.",
    )
    run_parser.add_argument(
        "--factor-version",
        help="Override factor version from the config.",
    )
    run_parser.add_argument(
        "--label-version",
        help="Override label version from the config.",
    )
    run_parser.add_argument(
        "--data-version",
        help="Override data version from the config.",
    )
    run_parser.add_argument(
        "--factor-values-path",
        help="Override local JSONL factor values path.",
    )
    run_parser.add_argument(
        "--labels-path",
        help="Override local JSONL labels path.",
    )
    run_parser.add_argument(
        "--horizon-seconds",
        type=int,
        help="Optional label horizon selector in seconds.",
    )
    run_parser.add_argument(
        "--instrument",
        action="append",
        help="Optional instrument_id selector; repeat for multiple instruments.",
    )
    run_parser.add_argument(
        "--session-id",
        action="append",
        help="Optional session_id selector; repeat for multiple sessions.",
    )
    run_parser.add_argument(
        "--start-ts",
        help="Optional inclusive ISO-8601 event_ts start.",
    )
    run_parser.add_argument(
        "--end-ts",
        help="Optional inclusive ISO-8601 event_ts end.",
    )
    run_parser.add_argument(
        "--output-dir",
        help="Local-only output directory for diagnostic artifacts.",
    )
    run_parser.add_argument(
        "--registry-path",
        help="Optional temp/local SQLite registry path outside the repository.",
    )
    run_parser.add_argument(
        "--manifest-out",
        help="Optional local run manifest path.",
    )
    run_parser.add_argument(
        "--min-sample-size",
        type=int,
        help="Override minimum aligned sample-size warning threshold.",
    )
    run_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON console summary.",
    )
    run_parser.set_defaults(handler=run_study_cli)
