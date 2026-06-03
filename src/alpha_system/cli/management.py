"""Management CLI command group."""

from __future__ import annotations

import argparse
import json
import sys

from alpha_system.experiments.management_grid import (
    ManagementGridConfigError,
    ManagementGridExpansionError,
    ManagementGridRunError,
    ManagementGridSpec,
    run_management_grid as execute_management_grid,
)
from alpha_system.experiments.management_outputs import ManagementOutputError
from alpha_system.management.validation import (
    ManagementValidationError,
    load_management_config,
    validate_management_config,
    write_validation_summary,
)


def run_management_grid(args: argparse.Namespace) -> int:
    """Run ``alpha management grid``."""
    config_path = args.config or args.config_path
    if not config_path:
        print("management command error: provide a management grid config path", file=sys.stderr)
        return 2
    if args.config and args.config_path:
        print("management command error: provide either CONFIG_PATH or --config, not both", file=sys.stderr)
        return 2
    try:
        payload = load_management_config(config_path)
        if args.validate_only or _validation_only_payload(payload):
            return _run_validation_only(args, payload)

        spec = ManagementGridSpec.from_mapping(payload).with_overrides(
            engine=args.engine,
            output_dir=args.output_dir,
            registry_path=args.registry_path,
            manifest_path=args.manifest_out,
            reference_fallback=False if args.no_reference_fallback else None,
        )
        result = execute_management_grid(spec)
    except (
        ManagementGridConfigError,
        ManagementGridExpansionError,
        ManagementOutputError,
        ManagementGridRunError,
        ManagementValidationError,
        OSError,
        ValueError,
    ) as exc:
        print(f"management command error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
        return 0

    print("Management command: grid")
    print("Mode: survivor-gated execution")
    print(f"Grid: {result.grid_id}")
    print(f"Candidate: {result.candidate_id}")
    print(f"Run: {result.run_id}")
    print(f"Combinations: {result.combination_count}")
    print(f"Completed: {result.completed_count}")
    print(f"Rejected: {result.rejected_count}")
    print(f"Leaderboard: {result.output_paths.leaderboard_path}")
    print(f"Manifest: {result.output_paths.manifest_path}")
    if result.registry_path is not None:
        print(f"Registry: {result.registry_path}")
        print(f"Registry written: {'yes' if result.registry_written else 'no'}")
    return 0


def _run_validation_only(args: argparse.Namespace, payload: dict) -> int:
    """Preserve explicit validation-only behavior for legacy management configs."""
    try:
        result = validate_management_config(payload)
        if not result.valid:
            print(f"management command error: {', '.join(result.errors)}", file=sys.stderr)
            return 2
        summary_path = None
        if args.summary_out:
            summary_path = write_validation_summary(args.summary_out, result)
    except (ManagementValidationError, OSError, ValueError) as exc:
        print(f"management command error: {exc}", file=sys.stderr)
        return 2

    if getattr(args, "json", False):
        print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
        return 0

    print("Management command: grid")
    print("Mode: validation only")
    print("Execution not run: no survivor-gated ASV1-P21 grid spec was provided")
    print(f"Management: {result.management_id}")
    print(f"Bounded grid: {'yes' if result.bounded_grid else 'no'}")
    print(f"Grid combinations: {result.grid_combinations}")
    if args.strategy_grid_ref:
        print(f"Strategy/grid reference: {args.strategy_grid_ref}")
    if args.registry_path:
        print(f"Registry metadata path: {args.registry_path}")
    if summary_path is not None:
        print(f"Validation summary: {summary_path.as_posix()}")
    return 0


def _validation_only_payload(payload: dict) -> bool:
    execution_keys = {"grid_id", "parameter_space", "survivors", "survivor_records"}
    return not any(key in payload for key in execution_keys)


def register_subparser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the ``alpha management`` command group."""
    management_parser = subparsers.add_parser(
        "management",
        help="Run survivor-gated bounded management grids.",
    )
    management_subparsers = management_parser.add_subparsers(dest="management_command")

    grid_parser = management_subparsers.add_parser(
        "grid",
        help="Run ASV1-P21 survivor-gated bounded management grids.",
        description=(
            "Run ASV1-P21 survivor-gated bounded management grids. Legacy "
            "management config shapes are validation-only and do not execute."
        ),
    )
    grid_parser.add_argument(
        "config_path",
        nargs="?",
        help="Path to a JSON management-grid config.",
    )
    grid_parser.add_argument(
        "--config",
        help="Path to a JSON management-grid config or legacy validation config.",
    )
    grid_parser.add_argument(
        "--strategy-grid-ref",
        help="Optional strategy/grid reference placeholder for validation metadata.",
    )
    grid_parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate config structure only; do not execute a management grid.",
    )
    grid_parser.add_argument(
        "--registry-path",
        help="Optional temp/local SQLite registry path outside the repository.",
    )
    grid_parser.add_argument(
        "--summary-out",
        help="Optional temp/local JSON path for a tiny validation summary.",
    )
    grid_parser.add_argument(
        "--output-dir",
        help="Optional local output directory for management-grid artifacts.",
    )
    grid_parser.add_argument(
        "--manifest-out",
        help="Optional local run manifest path.",
    )
    grid_parser.add_argument(
        "--engine",
        choices=("reference", "fast"),
        help="Engine selection; reference is default and fast is parity-gated.",
    )
    grid_parser.add_argument(
        "--no-reference-fallback",
        action="store_true",
        help="Fail closed when a fast-path request is not accelerated-certified.",
    )
    grid_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable command summary.",
    )
    grid_parser.set_defaults(handler=run_management_grid)
