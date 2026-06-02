"""Factor CLI command group."""

from __future__ import annotations

import argparse
import sys

from alpha_system.factors.materialize import (
    FactorMaterializationError,
    materialize_factor_values,
    print_materialization_summary,
)
from alpha_system.factors.validation import (
    DEFAULT_FACTOR_REGISTRY_PATH,
    FactorValidationConfigError,
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


def run_materialize(args: argparse.Namespace) -> int:
    """Run ``alpha factor materialize``."""
    try:
        summary = materialize_factor_values(
            spec_path=args.spec_path,
            canonical_data_path=args.canonical_data_path,
            data_version=args.data_version,
            output_policy=args.output_policy,
            output_dir=args.output_dir,
            registry_path=args.registry_path,
            manifest_out=args.manifest_out,
            compute_version=args.compute_version,
            instrument_id=args.instrument,
            session_id=args.session_id,
            start_ts=args.start_ts,
            end_ts=args.end_ts,
        )
    except (
        FactorMaterializationError,
        FactorValidationConfigError,
        OSError,
        ValueError,
    ) as exc:
        print(f"factor command error: {exc}", file=sys.stderr)
        return 2
    print_materialization_summary(summary, emit_json=args.json)
    return 0


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

    materialize_parser = factor_subparsers.add_parser(
        "materialize",
        help="Compute and optionally persist eligible factor values locally.",
    )
    materialize_parser.add_argument(
        "spec_path",
        help="Path to a JSON FactorSpec config.",
    )
    materialize_parser.add_argument(
        "--canonical-data-path",
        required=True,
        help="Local .jsonl or .csv canonical 1-minute bar data path.",
    )
    materialize_parser.add_argument(
        "--dataset-version",
        help="Optional dataset version selector for caller logs; no remote lookup is performed.",
    )
    materialize_parser.add_argument(
        "--data-version",
        required=True,
        help="Required data_version expected on every selected canonical bar.",
    )
    materialize_parser.add_argument(
        "--instrument",
        help="Optional instrument_id filter.",
    )
    materialize_parser.add_argument(
        "--session-id",
        help="Optional session_id filter.",
    )
    materialize_parser.add_argument(
        "--start-ts",
        help="Optional inclusive event_ts start filter.",
    )
    materialize_parser.add_argument(
        "--end-ts",
        help="Optional inclusive event_ts end filter.",
    )
    materialize_parser.add_argument(
        "--output-policy",
        choices=("dry-run", "local-only-persist"),
        default="dry-run",
        help="Choose dry-run compute or local-only persistence.",
    )
    materialize_parser.add_argument(
        "--registry-path",
        help="Optional temp/local SQLite registry path outside the repository.",
    )
    materialize_parser.add_argument(
        "--output-dir",
        help="Optional temp/local factor store directory outside the repository.",
    )
    materialize_parser.add_argument(
        "--manifest-out",
        help="Optional temp/local run manifest path outside the repository.",
    )
    materialize_parser.add_argument(
        "--compute-version",
        default="factor_compute_sdk_mvp_v1",
        help="Compute version recorded in factor values and manifests.",
    )
    materialize_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON console summary.",
    )
    materialize_parser.set_defaults(handler=run_materialize)
