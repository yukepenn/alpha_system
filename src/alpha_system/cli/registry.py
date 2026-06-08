"""Registry CLI commands."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from alpha_system.core.registry import inspect_registry_status
from alpha_system.data.foundation.datasets import (
    inventory_dataset_acceptance_locks,
    render_dataset_acceptance_summary,
    resolve_dataset_acceptance_lock,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.experiments.audit import registry_status_audit_summary


DEFAULT_REGISTRY_PATH = Path("metadata/registry.sqlite3")


def _parse_minimal_yaml_value(value: str) -> str:
    stripped = value.strip()
    if stripped.startswith(("'", '"')) and stripped.endswith(("'", '"')):
        return stripped[1:-1]
    return stripped


def _load_registry_path_from_config(path: str | Path) -> Path:
    config_path = Path(path)
    for raw_line in config_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        if key.strip() == "registry_path":
            return Path(_parse_minimal_yaml_value(value))
    msg = f"registry_path not found in config {config_path}"
    raise ValueError(msg)


def _status_registry_path(args: argparse.Namespace) -> Path:
    if args.registry_path is not None:
        return Path(args.registry_path)
    if args.config is not None:
        return _load_registry_path_from_config(args.config)
    return DEFAULT_REGISTRY_PATH


def run_status(args: argparse.Namespace) -> int:
    """Run the read-only registry status command."""
    try:
        registry_path = _status_registry_path(args)
    except OSError as exc:
        print(f"registry status error: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"registry status error: {exc}", file=sys.stderr)
        return 2

    status = inspect_registry_status(registry_path)
    payload = status.to_dict()
    hardening_summary = (
        registry_status_audit_summary(registry_path) if status.exists else _empty_hardening_summary()
    )
    payload.update(hardening_summary)
    if args.json:
        print(json.dumps(payload, sort_keys=True, indent=2))
    else:
        present = sum(1 for present_flag in status.required_tables.values() if present_flag)
        total = len(status.required_tables)
        schema_version = (
            "none" if status.schema_version is None else str(status.schema_version)
        )
        print(f"Registry: {status.registry_path}")
        print(f"Exists: {'yes' if status.exists else 'no'}")
        print(f"Local-only path: {'yes' if status.local_only else 'no'}")
        print(
            "Schema version: "
            f"{schema_version} (latest {status.latest_migration_version})"
        )
        print(f"Migrations current: {'yes' if status.migrations_current else 'no'}")
        print(f"Required tables: {present}/{total} present")
        if status.missing_tables:
            print(f"Missing tables: {', '.join(status.missing_tables)}")
        audit_summary = hardening_summary["audit"]
        if audit_summary.get("skipped"):
            print(f"Audit: skipped ({audit_summary.get('error', 'unavailable')})")
        else:
            print(
                "Audit findings: "
                f"{audit_summary.get('finding_count', 0)} "
                f"({'clean' if audit_summary.get('clean') else 'attention required'})"
            )
        failed_summary = hardening_summary["failed_runs"]
        print(f"Failed runs visible: {failed_summary['count']}")
        promotion_summary = hardening_summary["promotion_decisions"]
        print(
            "Promotion approvals without review: "
            f"{promotion_summary['approval_without_review']}"
        )
        print(f"Status: {'OK' if status.valid else 'INVALID'}")

    if not status.valid:
        print(f"registry status invalid: {status.status_message}", file=sys.stderr)
        return 2
    return 0


def run_dataset_acceptance_inventory(args: argparse.Namespace) -> int:
    """Run the read-only DatasetVersion acceptance inventory command."""

    try:
        policy = _load_json_mapping(args.config, "dataset acceptance policy")
        inventory = inventory_dataset_acceptance_locks(
            args.registry_path,
            policy=policy,
        )
        if args.summary_out:
            summary_path = Path(args.summary_out)
            summary_path.parent.mkdir(parents=True, exist_ok=True)
            summary_path.write_text(
                render_dataset_acceptance_summary(inventory),
                encoding="utf-8",
            )
    except (OSError, ValueError, DataFoundationValidationError) as exc:
        print(f"dataset acceptance inventory error: {exc}", file=sys.stderr)
        return 2

    payload = _dataset_acceptance_inventory_payload(inventory)
    if args.json:
        print(json.dumps(payload, sort_keys=True, indent=2))
    else:
        print("Dataset acceptance inventory")
        print(f"Policy: {inventory.policy_id}")
        print(f"Locked DatasetVersions: {len(inventory.locks)}")
        for state, count in inventory.state_counts.items():
            print(f"{state}: {count}")
        print(
            "Expected matrix complete: "
            f"{'yes' if inventory.complete_expected_matrix else 'no'}"
        )
    return 0


def run_dataset_acceptance_show(args: argparse.Namespace) -> int:
    """Resolve one persisted DatasetVersion acceptance-lock."""

    try:
        lock = resolve_dataset_acceptance_lock(
            args.registry_path,
            args.dataset_version_id,
        )
    except (OSError, ValueError, DataFoundationValidationError) as exc:
        print(f"dataset acceptance show error: {exc}", file=sys.stderr)
        return 2
    if lock is None:
        print("dataset acceptance lock not found", file=sys.stderr)
        return 2

    payload = dict(lock.to_mapping())
    if args.json:
        print(json.dumps(payload, sort_keys=True, indent=2))
    else:
        print(f"DatasetVersion: {lock.dataset_version_id}")
        print(f"State: {lock.state.value}")
        print(f"Policy: {lock.policy_id}")
        print(f"Blocking reasons: {len(lock.blocking_reasons)}")
        print(f"Warnings: {len(lock.warning_reasons)}")
    return 0


def _empty_hardening_summary() -> dict[str, object]:
    return {
        "audit": {
            "clean": False,
            "finding_count": 0,
            "skipped": True,
            "error": "missing registry database",
        },
        "failed_runs": {"count": 0, "run_ids": []},
        "promotion_decisions": {"approval_without_review": 0},
    }


def _load_json_mapping(path: str | Path, object_name: str) -> dict[str, object]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(value, str) or not isinstance(value, dict):
        msg = f"{object_name} JSON root must be a mapping"
        raise ValueError(msg)
    return value


def _dataset_acceptance_inventory_payload(inventory: object) -> dict[str, object]:
    locks = getattr(inventory, "locks")
    return {
        "policy_id": getattr(inventory, "policy_id"),
        "policy_hash": getattr(inventory, "policy_hash"),
        "state_counts": dict(getattr(inventory, "state_counts")),
        "lock_count": len(locks),
        "complete_expected_matrix": getattr(inventory, "complete_expected_matrix"),
        "missing_expected_versions": [
            dict(item) for item in getattr(inventory, "missing_expected_versions")
        ],
        "duplicate_expected_versions": [
            dict(item) for item in getattr(inventory, "duplicate_expected_versions")
        ],
        "locks": [
            {
                "dataset_version_id": lock.dataset_version_id,
                "state": lock.state.value,
                "schema_id": lock.coverage_report.get("schema_id"),
                "year": lock.coverage_report.get("year"),
                "blocking_reason_count": len(lock.blocking_reasons),
                "warning_reason_count": len(lock.warning_reasons),
            }
            for lock in locks
        ],
    }


def register_subparser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    registry_parser = subparsers.add_parser(
        "registry",
        help="Inspect the local metadata registry.",
    )
    registry_subparsers = registry_parser.add_subparsers(dest="registry_command")
    status_parser = registry_subparsers.add_parser(
        "status",
        help="Report local metadata registry status without creating it.",
    )
    status_parser.add_argument(
        "--registry-path",
        help="Path to the SQLite registry database to inspect.",
    )
    status_parser.add_argument(
        "--config",
        help="Tiny YAML config containing a registry_path value.",
    )
    status_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON status summary.",
    )
    status_parser.set_defaults(handler=run_status)

    acceptance_parser = registry_subparsers.add_parser(
        "dataset-acceptance",
        help="Inspect DatasetVersion acceptance-locks in a local registry.",
    )
    acceptance_subparsers = acceptance_parser.add_subparsers(
        dest="dataset_acceptance_command"
    )
    inventory_parser = acceptance_subparsers.add_parser(
        "inventory",
        help="Inventory in-scope DatasetVersions and compute value-free locks.",
    )
    inventory_parser.add_argument(
        "--registry-path",
        required=True,
        help="Local SQLite DatasetVersion registry path.",
    )
    inventory_parser.add_argument(
        "--config",
        required=True,
        help="JSON acceptance policy under configs/data/dataset_acceptance.",
    )
    inventory_parser.add_argument(
        "--summary-out",
        help="Optional value-free Markdown summary output path.",
    )
    inventory_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON inventory summary.",
    )
    inventory_parser.set_defaults(handler=run_dataset_acceptance_inventory)

    show_parser = acceptance_subparsers.add_parser(
        "show",
        help="Show one persisted DatasetVersion acceptance-lock by exact id.",
    )
    show_parser.add_argument(
        "--registry-path",
        required=True,
        help="Local SQLite DatasetVersion registry path.",
    )
    show_parser.add_argument(
        "--dataset-version-id",
        required=True,
        help="Exact DatasetVersion id to resolve. No fuzzy fallback is used.",
    )
    show_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the persisted lock as JSON.",
    )
    show_parser.set_defaults(handler=run_dataset_acceptance_show)
