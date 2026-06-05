"""Feature CLI command group for local-only Feature/Label substrate tooling."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from alpha_system.data.foundation.datasets import (
    CoverageReport,
    DataQualityReport,
    DatasetPartitionPlan,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.features.contracts import FeatureSetSpec
from alpha_system.features.engine import (
    FeatureMaterializationError,
    build_feature_materialization_plan,
    resolve_feature_materialization_dataset,
)
from alpha_system.features.registry import (
    FeatureRegistryError,
    default_feature_registry_path,
)
from alpha_system.features.registry import (
    _record_from_json as _feature_record_from_json,
)
from alpha_system.features.reports import (
    FeatureCoverageReport,
    FeatureQualityReport,
    FeatureReportError,
)
from alpha_system.governance.serialization import JsonValue


class FeatureCliError(ValueError):
    """Raised when the local feature CLI fails closed."""


def run_list(args: argparse.Namespace) -> int:
    """Run ``alpha feature list``."""

    return _run_with_error_handling(lambda: _emit_feature_list(args))


def run_plan(args: argparse.Namespace) -> int:
    """Run ``alpha feature plan``."""

    return _run_with_error_handling(lambda: _emit_feature_plan(args, dry_run=False))


def run_materialize(args: argparse.Namespace) -> int:
    """Run ``alpha feature materialize`` as a dry-run plan-only command."""

    return _run_with_error_handling(lambda: _emit_feature_plan(args, dry_run=True))


def run_report(args: argparse.Namespace) -> int:
    """Run ``alpha feature report``."""

    return _run_with_error_handling(lambda: _emit_feature_report(args))


def run_duplicate_audit(args: argparse.Namespace) -> int:
    """Run ``alpha feature duplicate-audit``."""

    return _run_with_error_handling(lambda: _emit_duplicate_audit(args))


def register_subparser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the ``alpha feature`` command group."""

    feature_parser = subparsers.add_parser(
        "feature",
        help="Inspect and plan local-only feature substrate actions.",
    )
    feature_subparsers = feature_parser.add_subparsers(dest="feature_command")

    list_parser = feature_subparsers.add_parser(
        "list",
        help="List registered local feature metadata.",
    )
    _add_registry_arguments(list_parser)
    list_parser.add_argument("--json", action="store_true", help="Emit JSON.")
    list_parser.set_defaults(handler=run_list)

    plan_parser = feature_subparsers.add_parser(
        "plan",
        help="Build a local feature materialization plan without writing values.",
    )
    _add_registry_arguments(plan_parser)
    _add_feature_set_arguments(plan_parser)
    _add_dataset_arguments(plan_parser)
    plan_parser.add_argument("--json", action="store_true", help="Emit JSON.")
    plan_parser.set_defaults(handler=run_plan)

    materialize_parser = feature_subparsers.add_parser(
        "materialize",
        help="Build a dry-run feature materialization plan; values are not written.",
    )
    _add_registry_arguments(materialize_parser)
    _add_feature_set_arguments(materialize_parser)
    _add_dataset_arguments(materialize_parser)
    materialize_parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Plan only; this is the default and only CLI mode.",
    )
    materialize_parser.add_argument("--json", action="store_true", help="Emit JSON.")
    materialize_parser.set_defaults(handler=run_materialize, dry_run=True)

    report_parser = feature_subparsers.add_parser(
        "report",
        help="Render local feature quality and coverage reports.",
    )
    _add_registry_arguments(report_parser)
    report_parser.add_argument("--feature-version-id", required=True)
    report_parser.add_argument(
        "--kind",
        choices=("quality", "coverage", "both"),
        default="both",
    )
    report_parser.add_argument("--json", action="store_true", help="Emit JSON.")
    report_parser.set_defaults(handler=run_report)

    duplicate_parser = feature_subparsers.add_parser(
        "duplicate-audit",
        help="Render duplicate and equivalent exposure registry evidence.",
    )
    _add_registry_arguments(duplicate_parser)
    duplicate_parser.add_argument("--feature-version-id")
    duplicate_parser.add_argument("--json", action="store_true", help="Emit JSON.")
    duplicate_parser.set_defaults(handler=run_duplicate_audit)


def _add_registry_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--registry-path",
        help="Local feature registry SQLite path. Defaults to ALPHA_DATA_ROOT registry path.",
    )
    parser.add_argument(
        "--alpha-data-root",
        help="Local data root used to resolve the default registry and report value paths.",
    )


def _add_feature_set_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--feature-set-id",
        required=True,
        help="Registered FeatureSetSpec id to plan from the local feature registry.",
    )
    parser.add_argument(
        "--feature-set-version",
        required=True,
        help="Registered FeatureSetSpec version to plan from the local feature registry.",
    )


def _add_dataset_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--dataset-registry", required=True)
    parser.add_argument("--dataset-version-id", required=True)
    parser.add_argument(
        "--lifecycle-state",
        default="VERSIONED",
        help="Accepted DatasetVersion lifecycle state evidence.",
    )
    parser.add_argument("--quality-report", required=True)
    parser.add_argument("--coverage-report", required=True)
    parser.add_argument("--source-manifest", required=True)
    parser.add_argument("--code-hash", required=True)
    parser.add_argument("--config-hash", required=True)
    parser.add_argument("--partition", required=True)
    parser.add_argument(
        "--governance-metadata",
        help="Optional JSON mapping for locked-partition governance metadata.",
    )
    parser.add_argument(
        "--partition-plan",
        help="Optional JSON DatasetPartitionPlan used for partition gating.",
    )


def _run_with_error_handling(callback: Any) -> int:
    try:
        callback()
        return 0
    except (
        DataFoundationValidationError,
        FeatureCliError,
        FeatureMaterializationError,
        FeatureRegistryError,
        FeatureReportError,
        OSError,
        json.JSONDecodeError,
        sqlite3.Error,
        ValueError,
    ) as exc:
        print(f"feature command error: {exc}", file=sys.stderr)
        return 2


def _emit_feature_list(args: argparse.Namespace) -> None:
    registry_path = _optional_feature_registry_path(args)
    records = _feature_records(registry_path) if registry_path is not None else ()
    payload = {
        "command": "feature list",
        "registry_path": str(registry_path) if registry_path is not None else None,
        "record_count": len(records),
        "features": [_feature_record_summary(record) for record in records],
    }
    _emit(payload, emit_json=args.json)


def _emit_feature_plan(args: argparse.Namespace, *, dry_run: bool) -> None:
    feature_set = _feature_set_from_registry(args)
    accepted_version = _resolve_accepted_dataset(args)
    governance_metadata = _optional_json_mapping(args.governance_metadata, "governance_metadata")
    partition_plan = _optional_partition_plan(args.partition_plan)
    plan = build_feature_materialization_plan(
        feature_set,
        accepted_version,
        partition_id=args.partition,
        alpha_data_root=args.alpha_data_root,
        governance_metadata=governance_metadata,
        partition_plan=partition_plan,
    )
    payload = {
        "command": "feature materialize" if dry_run else "feature plan",
        "dry_run": dry_run,
        "writes_values": False,
        "plan": plan.to_dict(),
    }
    _emit(payload, emit_json=args.json)


def _emit_feature_report(args: argparse.Namespace) -> None:
    registry_path = _required_feature_registry_path(args)
    record = _feature_record_by_version(registry_path, args.feature_version_id)
    reports: dict[str, JsonValue] = {}
    if args.kind in {"quality", "both"}:
        quality = FeatureQualityReport.from_registry_record(
            record,
            alpha_data_root=args.alpha_data_root,
        )
        reports["quality"] = quality.to_dict()
    if args.kind in {"coverage", "both"}:
        coverage = FeatureCoverageReport.from_registry_record(
            record,
            alpha_data_root=args.alpha_data_root,
        )
        reports["coverage"] = coverage.to_dict()
    payload = {
        "command": "feature report",
        "feature_version_id": record.feature_version_id,
        "reports": reports,
    }
    _emit(payload, emit_json=args.json)


def _emit_duplicate_audit(args: argparse.Namespace) -> None:
    registry_path = _optional_feature_registry_path(args)
    records = _feature_records(registry_path) if registry_path is not None else ()
    if args.feature_version_id:
        records = tuple(
            record for record in records if record.feature_version_id == args.feature_version_id
        )
        if not records:
            raise FeatureCliError(
                f"feature version not found in local registry: {args.feature_version_id}"
            )
    payload = {
        "command": "feature duplicate-audit",
        "registry_path": str(registry_path) if registry_path is not None else None,
        "record_count": len(records),
        "features": [_duplicate_audit_summary(record) for record in records],
    }
    _emit(payload, emit_json=args.json)


def _feature_set_from_registry(args: argparse.Namespace) -> FeatureSetSpec:
    registry_path = _required_feature_registry_path(args)
    records = _feature_records_for_set(
        registry_path,
        args.feature_set_id,
        args.feature_set_version,
    )
    if not records:
        raise FeatureCliError(
            "registered FeatureSetSpec was not found in the local feature registry"
        )
    return FeatureSetSpec(
        feature_set_id=args.feature_set_id,
        feature_set_version=args.feature_set_version,
        features=tuple(record.feature_spec for record in records),
        metadata={"source": "local feature registry membership"},
    )


def _resolve_accepted_dataset(args: argparse.Namespace) -> Any:
    quality_report = DataQualityReport.from_mapping(
        _read_json_mapping(args.quality_report, "quality_report")
    )
    coverage_report = CoverageReport.from_mapping(
        _read_json_mapping(args.coverage_report, "coverage_report")
    )
    source_manifest = _read_json_mapping(args.source_manifest, "source_manifest")
    return resolve_feature_materialization_dataset(
        args.dataset_registry,
        args.dataset_version_id,
        lifecycle_state=args.lifecycle_state,
        quality_report=quality_report,
        coverage_report=coverage_report,
        source_manifest=source_manifest,
        code_hash=args.code_hash,
        config_hash=args.config_hash,
    )


def _optional_feature_registry_path(args: argparse.Namespace) -> Path | None:
    if args.registry_path:
        path = Path(args.registry_path)
    else:
        try:
            path = default_feature_registry_path(alpha_data_root=args.alpha_data_root)
        except FeatureRegistryError as exc:
            if "ALPHA_DATA_ROOT is required" not in str(exc):
                raise
            return None
    return path if path.exists() else None


def _required_feature_registry_path(args: argparse.Namespace) -> Path:
    path = _optional_feature_registry_path(args)
    if path is None:
        raise FeatureCliError("local feature registry path is required and must exist")
    return path


def _feature_records(registry_path: Path) -> tuple[Any, ...]:
    with _connect_readonly(registry_path) as connection:
        rows = connection.execute(
            """
            SELECT metadata_json
            FROM feature_registry_records
            ORDER BY feature_id, feature_version_id
            """
        ).fetchall()
    return tuple(_feature_record_from_json(str(row["metadata_json"])) for row in rows)


def _feature_records_for_set(
    registry_path: Path,
    feature_set_id: str,
    feature_set_version: str,
) -> tuple[Any, ...]:
    with _connect_readonly(registry_path) as connection:
        rows = connection.execute(
            """
            SELECT r.metadata_json
            FROM feature_set_memberships m
            JOIN feature_registry_records r
              ON r.feature_version_id = m.feature_version_id
            WHERE m.feature_set_id = ?
              AND m.feature_set_version = ?
            ORDER BY m.ordinal, m.feature_version_id
            """,
            (feature_set_id, feature_set_version),
        ).fetchall()
    return tuple(_feature_record_from_json(str(row["metadata_json"])) for row in rows)


def _feature_record_by_version(registry_path: Path, feature_version_id: str) -> Any:
    with _connect_readonly(registry_path) as connection:
        row = connection.execute(
            """
            SELECT metadata_json
            FROM feature_registry_records
            WHERE feature_version_id = ?
            """,
            (feature_version_id,),
        ).fetchone()
    if row is None:
        raise FeatureCliError(f"feature version not found in local registry: {feature_version_id}")
    return _feature_record_from_json(str(row["metadata_json"]))


def _connect_readonly(path: Path) -> sqlite3.Connection:
    if not path.exists():
        raise FeatureCliError(f"local feature registry does not exist: {path}")
    connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _feature_record_summary(record: Any) -> dict[str, JsonValue]:
    return {
        "feature_id": record.feature_spec.feature_id,
        "feature_version_id": record.feature_version_id,
        "feature_request_id": record.feature_request_id,
        "feature_set_id": record.feature_set_id,
        "feature_set_version": record.feature_set_version,
        "dataset_version_id": record.dataset_version_id,
        "partition_id": record.partition_id,
        "lifecycle_state": record.lifecycle_state.value,
        "value_record_count": record.value_record_count,
        "duplicate_exposure_status": record.duplicate_exposure_status,
    }


def _duplicate_audit_summary(record: Any) -> dict[str, JsonValue]:
    report = record.duplicate_exposure_report
    return {
        **_feature_record_summary(record),
        "duplicate_exposure_report": report.to_dict(),
        "blocking_finding_count": sum(
            1 for group in report.equivalent_feature_groups if group.is_blocking
        ),
        "equivalent_feature_group_count": len(report.equivalent_feature_groups),
    }


def _optional_partition_plan(path: str | None) -> DatasetPartitionPlan | None:
    if not path:
        return None
    return DatasetPartitionPlan.from_mapping(_read_json_mapping(path, "partition_plan"))


def _optional_json_mapping(path: str | None, object_name: str) -> Mapping[str, Any]:
    if not path:
        return {}
    return _read_json_mapping(path, object_name)


def _read_json_mapping(path: str | Path, object_name: str) -> Mapping[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(value, str) or not isinstance(value, Mapping):
        raise FeatureCliError(f"{object_name} JSON root must be a mapping")
    return value


def _emit(payload: Mapping[str, Any], *, emit_json: bool) -> None:
    if emit_json:
        print(json.dumps(payload, sort_keys=True, indent=2))
        return
    command = payload["command"]
    print(f"Feature command: {command}")
    if "registry_path" in payload:
        print(f"Registry: {payload['registry_path'] or 'not configured'}")
    if "record_count" in payload:
        print(f"Registered features: {payload['record_count']}")
    if "plan" in payload:
        plan = payload["plan"]
        if isinstance(plan, Mapping):
            print(f"Plan: {plan['plan_id']}")
            print(f"DatasetVersion: {plan['dataset_version_id']}")
            print(f"Partition: {plan['partition_id']}")
            print(f"Output path: {plan['output_path']}")
        print(f"Dry run: {'yes' if payload.get('dry_run') else 'no'}")
        print("Writes values: no")
    if "reports" in payload:
        reports = payload["reports"]
        if isinstance(reports, Mapping):
            for name, report in reports.items():
                if isinstance(report, Mapping):
                    blocking = report.get("blocking", ())
                    non_blocking = report.get("non_blocking", ())
                    print(f"{name}: blocking={len(blocking)} non_blocking={len(non_blocking)}")
    features = payload.get("features")
    if isinstance(features, Sequence) and not isinstance(features, str):
        if not features:
            print("No local feature registry records found.")
        for item in features:
            if isinstance(item, Mapping):
                print(
                    "{feature_id} {feature_version_id} "
                    "dataset={dataset_version_id} partition={partition_id} "
                    "state={lifecycle_state} duplicate={duplicate_exposure_status}".format(**item)
                )
