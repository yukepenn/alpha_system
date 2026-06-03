"""Strategy grid CLI command group."""

from __future__ import annotations

import argparse
import json
import sys

from alpha_system.experiments.grid import GridExpansionError
from alpha_system.experiments.grid_config import (
    GridConfigError,
    load_grid_spec,
    parse_version_overrides,
)
from alpha_system.experiments.grid_outputs import GridOutputError
from alpha_system.experiments.runner import GridRunError, run_grid


def run_grid_cli(args: argparse.Namespace) -> int:
    """Run ``alpha grid run``."""
    config_path = args.config or args.config_path
    if not config_path:
        print("grid command error: provide a grid config path", file=sys.stderr)
        return 2
    if args.config and args.config_path:
        print("grid command error: provide either CONFIG_PATH or --config, not both", file=sys.stderr)
        return 2
    try:
        spec = load_grid_spec(config_path).with_overrides(
            strategy_spec=args.strategy_spec,
            management_spec=args.management_spec,
            portfolio_spec=args.portfolio_spec,
            execution_config=args.execution_config,
            data_version=args.data_version,
            factor_versions=parse_version_overrides(
                args.factor_version,
                field_name="--factor-version",
            ),
            label_versions=parse_version_overrides(
                args.label_version,
                field_name="--label-version",
            ),
            engine=args.engine,
            output_dir=args.output_dir,
            registry_path=args.registry_path,
            manifest_path=args.manifest_out,
        )
        result = run_grid(spec)
    except (
        GridConfigError,
        GridExpansionError,
        GridOutputError,
        GridRunError,
        OSError,
        ValueError,
    ) as exc:
        print(f"grid command error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
        return 0

    print("Grid command: run")
    print(f"Grid: {result.grid_id}")
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


def register_subparser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the ``alpha grid`` command group."""
    grid_parser = subparsers.add_parser(
        "grid",
        help="Run bounded local strategy grids on declared versioned inputs.",
    )
    grid_subparsers = grid_parser.add_subparsers(dest="grid_command")

    run_parser = grid_subparsers.add_parser(
        "run",
        help="Run a bounded local strategy/factor/execution/risk/management grid.",
    )
    run_parser.add_argument(
        "config_path",
        nargs="?",
        help="Path to a JSON grid config.",
    )
    run_parser.add_argument(
        "--config",
        help="Path to a JSON grid config.",
    )
    run_parser.add_argument(
        "--strategy-spec",
        help="Declared strategy spec path or identifier recorded for reproducibility.",
    )
    run_parser.add_argument(
        "--management-spec",
        help="Declared management spec path or identifier recorded for reproducibility.",
    )
    run_parser.add_argument(
        "--portfolio-spec",
        help="Declared portfolio spec path or identifier recorded for reproducibility.",
    )
    run_parser.add_argument(
        "--data-version",
        help="Override required data version.",
    )
    run_parser.add_argument(
        "--factor-version",
        action="append",
        help="Declared factor version as factor_id=version; repeat for multiple factors.",
    )
    run_parser.add_argument(
        "--label-version",
        action="append",
        help="Declared label version as label_id=version; repeat for multiple labels.",
    )
    run_parser.add_argument(
        "--execution-config",
        help="Path to reference execution config JSON/YAML.",
    )
    run_parser.add_argument(
        "--engine",
        choices=("reference", "fast"),
        help="Engine selection; reference is default and fast is parity-gated.",
    )
    run_parser.add_argument(
        "--registry-path",
        help="Optional temp/local SQLite registry path outside the repository.",
    )
    run_parser.add_argument(
        "--output-dir",
        help="Optional local output directory for grid artifacts.",
    )
    run_parser.add_argument(
        "--manifest-out",
        help="Optional local run manifest path.",
    )
    run_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON console summary.",
    )
    run_parser.set_defaults(handler=run_grid_cli)
