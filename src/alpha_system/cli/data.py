"""Data CLI command group."""

from __future__ import annotations

import argparse

from alpha_system.data.cli_validation import (
    DEFAULT_SCHEMA_ID,
    run_build_bars_command,
    run_cli_with_error_handling,
    run_validate_command,
)


def run_validate(args: argparse.Namespace) -> int:
    """Run ``alpha data validate``."""
    return run_cli_with_error_handling(
        lambda: run_validate_command(
            config_path=args.config,
            input_path=args.input,
            schema_id=args.schema_id,
            calendar_id=args.calendar_id,
            registry_path=args.registry_path,
            summary_out=args.summary_out,
        ),
        emit_json=args.json,
    )


def run_build_bars(args: argparse.Namespace) -> int:
    """Run ``alpha data build-bars``."""
    return run_cli_with_error_handling(
        lambda: run_build_bars_command(
            input_path=args.input,
            instrument_config_path=args.instrument_config,
            calendar_config_path=args.calendar_config,
            output_path=args.output,
            data_version=args.data_version,
            registry_path=args.registry_path,
            validation_config_path=args.validation_config,
        ),
        emit_json=args.json,
    )


def register_subparser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the ``alpha data`` command group."""
    data_parser = subparsers.add_parser(
        "data",
        help="Validate and build local-only canonical data fixtures.",
    )
    data_subparsers = data_parser.add_subparsers(dest="data_command")

    validate_parser = data_subparsers.add_parser(
        "validate",
        help="Validate local canonical 1-minute bars.",
    )
    validate_parser.add_argument(
        "--config",
        required=True,
        help="Validation config path with latency and optional calendar_config.",
    )
    validate_parser.add_argument(
        "--input",
        required=True,
        help="Local CSV dataset or tiny fixture path to validate.",
    )
    validate_parser.add_argument(
        "--schema-id",
        default=DEFAULT_SCHEMA_ID,
        help=f"Schema identifier to report (default: {DEFAULT_SCHEMA_ID}).",
    )
    validate_parser.add_argument(
        "--calendar-id",
        help="Expected calendar identifier when config supplies calendar_config.",
    )
    validate_parser.add_argument(
        "--registry-path",
        help="Optional temp/local SQLite registry path for a dataset-version entry.",
    )
    validate_parser.add_argument(
        "--summary-out",
        help="Optional local-only .json, .md, or .csv validation summary path.",
    )
    validate_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON console summary.",
    )
    validate_parser.set_defaults(handler=run_validate)

    build_parser = data_subparsers.add_parser(
        "build-bars",
        help="Build local-only canonical 1-minute bars from allowed fixtures.",
    )
    build_parser.add_argument(
        "--input",
        required=True,
        help="Allowed tiny synthetic fixture input path.",
    )
    build_parser.add_argument(
        "--instrument-config",
        required=True,
        help="Local instrument config path for the build.",
    )
    build_parser.add_argument(
        "--calendar-config",
        required=True,
        help="Local JSON calendar config path for session assignment.",
    )
    build_parser.add_argument(
        "--output",
        required=True,
        help="Local-only output path under a data directory.",
    )
    build_parser.add_argument(
        "--data-version",
        required=True,
        help="Canonical data_version to stamp on built bars.",
    )
    build_parser.add_argument(
        "--registry-path",
        help="Optional temp/local SQLite registry path for a dataset-version entry.",
    )
    build_parser.add_argument(
        "--validation-config",
        help="Optional validation config path with latency and fixture policy overrides.",
    )
    build_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON console summary.",
    )
    build_parser.set_defaults(handler=run_build_bars)
