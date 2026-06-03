"""Management CLI command group."""

from __future__ import annotations

import argparse
import json
import sys

from alpha_system.management.validation import (
    ManagementValidationError,
    load_management_config,
    validate_management_config,
    write_validation_summary,
)


def run_management_grid(args: argparse.Namespace) -> int:
    """Run ``alpha management grid`` in validation-only mode."""
    if not args.config:
        print("management command error: provide --config for validation", file=sys.stderr)
        return 2
    try:
        payload = load_management_config(args.config)
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

    if args.json:
        print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
        return 0

    print("Management command: grid")
    print("Mode: validation only")
    print("Execution deferred to: ASV1-P21")
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


def register_subparser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the ``alpha management`` command group."""
    management_parser = subparsers.add_parser(
        "management",
        help="Validate reviewed position-management configs.",
    )
    management_subparsers = management_parser.add_subparsers(dest="management_command")

    grid_parser = management_subparsers.add_parser(
        "grid",
        help="Validate bounded management-grid definitions; execution is deferred to ASV1-P21.",
        description=(
            "Validate bounded management-grid definitions. Survivor-based "
            "management-grid execution is deferred to ASV1-P21."
        ),
    )
    grid_parser.add_argument(
        "--config",
        help="Path to a JSON or small YAML management config.",
    )
    grid_parser.add_argument(
        "--strategy-grid-ref",
        help="Optional strategy/grid reference placeholder for validation metadata.",
    )
    grid_parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate only; management-grid execution is not available in this phase.",
    )
    grid_parser.add_argument(
        "--registry-path",
        help="Optional registry path used only as validation metadata.",
    )
    grid_parser.add_argument(
        "--summary-out",
        help="Optional temp/local JSON path for a tiny validation summary.",
    )
    grid_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable validation summary.",
    )
    grid_parser.set_defaults(handler=run_management_grid)
