"""Data CLI command group."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from alpha_system.data.cli_validation import (
    DEFAULT_SCHEMA_ID,
    run_build_bars_command,
    run_cli_with_error_handling,
    run_validate_command,
)
from alpha_system.data.foundation.datasets import (
    inventory_dataset_acceptance_locks,
    persist_dataset_acceptance_locks,
    render_dataset_acceptance_summary,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError


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


def _load_data_inventory_tool() -> Any:
    """Import the repo-local ``tools.frontier.data_inventory`` module.

    The canonical reader lives under ``tools/frontier`` (the inventory/coverage
    reporting family, alongside ``status_doctor``), which is not on the package
    install path. Insert the repo root on ``sys.path`` exactly like
    ``tools/hooks/canary_runner`` does, then import.
    """

    repo_root = Path(__file__).resolve().parents[3]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from tools.frontier import data_inventory  # noqa: PLC0415

    return data_inventory


def run_data_inventory(args: argparse.Namespace) -> int:
    """Run ``alpha data inventory`` (on-disk materialized data-existence truth)."""

    tool = _load_data_inventory_tool()
    return tool.run_inventory(
        data_root=args.data_root,
        nonempty_only=not args.include_empty,
        check_config=not args.no_config_check,
        emit_json=args.json,
    )


def run_accept_datasets(args: argparse.Namespace) -> int:
    """Run ``alpha data accept-datasets``."""

    try:
        policy = _load_json_mapping(args.config, "dataset acceptance policy")
        inventory = inventory_dataset_acceptance_locks(
            args.registry_path,
            policy=policy,
        )
        persist_dataset_acceptance_locks(args.registry_path, inventory)
        if args.summary_out:
            summary_path = Path(args.summary_out)
            summary_path.parent.mkdir(parents=True, exist_ok=True)
            summary_path.write_text(
                render_dataset_acceptance_summary(inventory, persisted=True),
                encoding="utf-8",
            )
    except (OSError, ValueError, DataFoundationValidationError) as exc:
        print(f"dataset acceptance error: {exc}", file=sys.stderr)
        return 2

    payload = {
        "command": "data accept-datasets",
        "registry_path": str(args.registry_path),
        "policy_id": inventory.policy_id,
        "policy_hash": inventory.policy_hash,
        "lock_count": len(inventory.locks),
        "state_counts": dict(inventory.state_counts),
        "complete_expected_matrix": inventory.complete_expected_matrix,
        "summary_out": args.summary_out,
    }
    if args.json:
        print(json.dumps(payload, sort_keys=True, indent=2))
    else:
        print("Dataset acceptance locks persisted")
        print(f"Policy: {inventory.policy_id}")
        print(f"Locked DatasetVersions: {len(inventory.locks)}")
        for state, count in inventory.state_counts.items():
            print(f"{state}: {count}")
        print(
            "Expected matrix complete: "
            f"{'yes' if inventory.complete_expected_matrix else 'no'}"
        )
    return 0


def _load_json_mapping(path: str | Path, object_name: str) -> dict[str, object]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(value, str) or not isinstance(value, dict):
        msg = f"{object_name} JSON root must be a mapping"
        raise ValueError(msg)
    return value


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

    accept_parser = data_subparsers.add_parser(
        "accept-datasets",
        help="Persist DatasetVersion acceptance-locks in a local registry.",
    )
    accept_parser.add_argument(
        "--registry-path",
        required=True,
        help="Local SQLite DatasetVersion registry path.",
    )
    accept_parser.add_argument(
        "--config",
        required=True,
        help="JSON acceptance policy under configs/data/dataset_acceptance.",
    )
    accept_parser.add_argument(
        "--summary-out",
        help="Optional value-free Markdown summary output path.",
    )
    accept_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON summary.",
    )
    accept_parser.set_defaults(handler=run_accept_datasets)

    inventory_parser = data_subparsers.add_parser(
        "inventory",
        help=(
            "Report the canonical on-disk materialized data inventory "
            "(data-existence source of truth) and flag config-vs-disk "
            "acceptance-lock disagreements."
        ),
    )
    inventory_parser.add_argument(
        "--data-root",
        help=(
            "Explicit data root. Default resolution: ALPHA_DATA_ROOT env, then "
            "frontier.yaml data_root, then ~/alpha_data/alpha_system."
        ),
    )
    inventory_parser.add_argument(
        "--include-empty",
        action="store_true",
        help="Include zero-byte/empty values.parquet entries.",
    )
    inventory_parser.add_argument(
        "--no-config-check",
        action="store_true",
        help="Skip the config-vs-disk acceptance-lock disagreement cross-check.",
    )
    inventory_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON report.",
    )
    inventory_parser.set_defaults(handler=run_data_inventory)
