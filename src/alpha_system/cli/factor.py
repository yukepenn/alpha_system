"""Factor CLI command group."""

from __future__ import annotations

import argparse

from alpha_system.factors.validation import (
    DEFAULT_FACTOR_REGISTRY_PATH,
    run_cli_with_error_handling,
    run_factor_validate_command,
)


def run_validate(args: argparse.Namespace) -> int:
    """Run ``alpha factor validate``."""
    return run_cli_with_error_handling(
        lambda: run_factor_validate_command(
            spec_path=args.spec_path,
            registry_path=args.registry_path,
            code_paths=tuple(args.code_path or ()),
            validation_artifact_path=args.validation_artifact_path,
            summary_out=args.summary_out,
            used_fields=tuple(args.used_field or ()),
        ),
        emit_json=args.json,
    )


def register_subparser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the ``alpha factor`` command group."""
    factor_parser = subparsers.add_parser(
        "factor",
        help="Validate factor specifications and registry eligibility.",
    )
    factor_subparsers = factor_parser.add_subparsers(dest="factor_command")

    validate_parser = factor_subparsers.add_parser(
        "validate",
        help="Validate a FactorSpec and optional temp registry entry.",
    )
    validate_parser.add_argument(
        "spec_path",
        help="Path to a JSON FactorSpec config.",
    )
    validate_parser.add_argument(
        "--registry-path",
        default=DEFAULT_FACTOR_REGISTRY_PATH.as_posix(),
        help=(
            "Optional temp/local SQLite registry path for draft/candidate entry "
            f"(default: {DEFAULT_FACTOR_REGISTRY_PATH.as_posix()})."
        ),
    )
    validate_parser.add_argument(
        "--code-path",
        action="append",
        help="Optional factor code file or directory used to verify code_hash.",
    )
    validate_parser.add_argument(
        "--validation-artifact-path",
        help="Optional validation artifact reference override.",
    )
    validate_parser.add_argument(
        "--summary-out",
        help="Optional local-only .json or .md validation summary path.",
    )
    validate_parser.add_argument(
        "--used-field",
        action="append",
        help="Optional implementation input field to check against declarations.",
    )
    validate_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON console summary.",
    )
    validate_parser.set_defaults(handler=run_validate)
