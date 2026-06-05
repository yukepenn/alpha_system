"""Label CLI command group for local-only Feature/Label substrate tooling."""

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
from alpha_system.governance.study_input_pack import validate_study_input_pack
from alpha_system.labels.engine import (
    LabelMaterializationError,
    build_label_materialization_plan,
    resolve_label_materialization_dataset,
)
from alpha_system.labels.families.cost_adjusted import build_cost_adjusted_label_definition
from alpha_system.labels.families.event import build_event_label_definition
from alpha_system.labels.families.fixed_horizon import build_fixed_horizon_label_definition
from alpha_system.labels.families.path import build_path_label_definition
from alpha_system.labels.leakage_audit import (
    LabelLeakageAuditError,
    audit_registered_label,
)
from alpha_system.labels.registry import (
    LabelRegistryError,
    default_label_registry_path,
)
from alpha_system.labels.registry import (
    _record_from_json as _label_record_from_json,
)


class LabelCliError(ValueError):
    """Raised when the local label CLI fails closed."""


def run_list(args: argparse.Namespace) -> int:
    """Run ``alpha label list``."""

    return _run_with_error_handling(lambda: _emit_label_list(args))


def run_plan(args: argparse.Namespace) -> int:
    """Run ``alpha label plan``."""

    return _run_with_error_handling(lambda: _emit_label_plan(args, dry_run=False))


def run_materialize(args: argparse.Namespace) -> int:
    """Run ``alpha label materialize`` as a dry-run plan-only command."""

    return _run_with_error_handling(lambda: _emit_label_plan(args, dry_run=True))


def run_report(args: argparse.Namespace) -> int:
    """Run ``alpha label report``."""

    return _run_with_error_handling(lambda: _emit_label_report(args))


def run_leakage_audit(args: argparse.Namespace) -> int:
    """Run ``alpha label leakage-audit``."""

    return _run_with_error_handling(lambda: _emit_leakage_audit(args))


def run_input_pack(args: argparse.Namespace) -> int:
    """Run ``alpha label input-pack``."""

    return _run_with_error_handling(lambda: _emit_input_pack(args))


def register_subparser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the ``alpha label`` command group."""

    label_parser = subparsers.add_parser(
        "label",
        help="Inspect and plan local-only label substrate actions.",
    )
    label_subparsers = label_parser.add_subparsers(dest="label_command")

    list_parser = label_subparsers.add_parser(
        "list",
        help="List registered local label metadata.",
    )
    _add_registry_arguments(list_parser)
    list_parser.add_argument("--json", action="store_true", help="Emit JSON.")
    list_parser.set_defaults(handler=run_list)

    plan_parser = label_subparsers.add_parser(
        "plan",
        help="Build a local label materialization plan without writing values.",
    )
    _add_label_definition_arguments(plan_parser)
    _add_dataset_arguments(plan_parser)
    plan_parser.add_argument("--json", action="store_true", help="Emit JSON.")
    plan_parser.set_defaults(handler=run_plan)

    materialize_parser = label_subparsers.add_parser(
        "materialize",
        help="Build a dry-run label materialization plan; values are not written.",
    )
    _add_label_definition_arguments(materialize_parser)
    _add_dataset_arguments(materialize_parser)
    materialize_parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Plan only; this is the default and only CLI mode.",
    )
    materialize_parser.add_argument("--json", action="store_true", help="Emit JSON.")
    materialize_parser.set_defaults(handler=run_materialize, dry_run=True)

    report_parser = label_subparsers.add_parser(
        "report",
        help="Render local label registry report summaries.",
    )
    _add_registry_arguments(report_parser)
    report_parser.add_argument("--label-version-id")
    report_parser.add_argument("--json", action="store_true", help="Emit JSON.")
    report_parser.set_defaults(handler=run_report)

    audit_parser = label_subparsers.add_parser(
        "leakage-audit",
        help="Render label leakage and availability audit summaries.",
    )
    _add_registry_arguments(audit_parser)
    audit_parser.add_argument("--label-version-id", required=True)
    audit_parser.add_argument(
        "--live-feature-references",
        help="Optional JSON list or mapping of live feature references.",
    )
    audit_parser.add_argument(
        "--label-value-records",
        help="Optional JSON list of local label value records for availability checks.",
    )
    audit_parser.add_argument("--json", action="store_true", help="Emit JSON.")
    audit_parser.set_defaults(handler=run_leakage_audit)

    pack_parser = label_subparsers.add_parser(
        "input-pack",
        help="Validate and render a StudySpec input-pack view.",
    )
    pack_parser.add_argument("--input-pack", required=True)
    pack_parser.add_argument("--json", action="store_true", help="Emit JSON.")
    pack_parser.set_defaults(handler=run_input_pack)


def _add_registry_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--registry-path",
        help="Local label registry SQLite path. Defaults to ALPHA_DATA_ROOT registry path.",
    )
    parser.add_argument(
        "--alpha-data-root",
        help="Local data root used to resolve the default registry path.",
    )


def _add_label_definition_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--label-family",
        required=True,
        choices=("fixed_horizon", "cost_adjusted", "path", "event"),
    )
    parser.add_argument("--label-name", required=True)
    parser.add_argument(
        "--label-spec",
        required=True,
        help="Local JSON governance LabelSpec consumed by the label family.",
    )
    parser.add_argument(
        "--instrument",
        action="append",
        help="Optional instrument selector; repeat for multiple instruments.",
    )
    parser.add_argument(
        "--price-field",
        help="Optional path-label price field override.",
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
    parser.add_argument("--alpha-data-root", required=True)
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
        LabelCliError,
        LabelLeakageAuditError,
        LabelMaterializationError,
        LabelRegistryError,
        OSError,
        json.JSONDecodeError,
        sqlite3.Error,
        ValueError,
    ) as exc:
        print(f"label command error: {exc}", file=sys.stderr)
        return 2


def _emit_label_list(args: argparse.Namespace) -> None:
    registry_path = _optional_label_registry_path(args)
    records = _label_records(registry_path) if registry_path is not None else ()
    payload = {
        "command": "label list",
        "registry_path": str(registry_path) if registry_path is not None else None,
        "record_count": len(records),
        "labels": [_label_record_summary(record) for record in records],
    }
    _emit(payload, emit_json=args.json)


def _emit_label_plan(args: argparse.Namespace, *, dry_run: bool) -> None:
    accepted_version = _resolve_accepted_dataset(args)
    definition = _build_label_definition(args)
    governance_metadata = _optional_json_mapping(args.governance_metadata, "governance_metadata")
    partition_plan = _optional_partition_plan(args.partition_plan)
    plan = build_label_materialization_plan(
        (definition,),
        accepted_version,
        partition_id=args.partition,
        instrument_ids=tuple(args.instrument or ()),
        alpha_data_root=args.alpha_data_root,
        governance_metadata=governance_metadata,
        partition_plan=partition_plan,
        dry_run=dry_run,
    )
    payload = {
        "command": "label materialize" if dry_run else "label plan",
        "dry_run": dry_run,
        "writes_values": False,
        "plan": plan.to_dict(),
    }
    _emit(payload, emit_json=args.json)


def _emit_label_report(args: argparse.Namespace) -> None:
    registry_path = _optional_label_registry_path(args)
    records = _label_records(registry_path) if registry_path is not None else ()
    if args.label_version_id:
        records = tuple(
            record for record in records if record.label_version_id == args.label_version_id
        )
        if not records:
            raise LabelCliError(
                f"label version not found in local registry: {args.label_version_id}"
            )
    payload = {
        "command": "label report",
        "registry_path": str(registry_path) if registry_path is not None else None,
        "record_count": len(records),
        "labels": [_label_report_summary(record) for record in records],
    }
    _emit(payload, emit_json=args.json)


def _emit_leakage_audit(args: argparse.Namespace) -> None:
    registry_path = _required_label_registry_path(args)
    record = _label_record_by_version(registry_path, args.label_version_id)
    live_feature_references = _optional_json_value(args.live_feature_references)
    label_value_records = _optional_json_records(args.label_value_records)
    report = audit_registered_label(
        record,
        live_feature_references=live_feature_references,
        label_value_records=label_value_records,
    )
    payload = {
        "command": "label leakage-audit",
        "label_version_id": record.label_version_id,
        "report": report.to_dict(),
    }
    _emit(payload, emit_json=args.json)


def _emit_input_pack(args: argparse.Namespace) -> None:
    pack = validate_study_input_pack(_read_json_mapping(args.input_pack, "study_input_pack"))
    payload = {
        "command": "label input-pack",
        "input_pack": pack.to_dict(),
        "feature_request_count": len(pack.feature_request_ids),
        "label_spec_count": len(pack.label_spec_ids),
        "dataset_scope_keys": sorted(pack.dataset_scope),
    }
    _emit(payload, emit_json=args.json)


def _resolve_accepted_dataset(args: argparse.Namespace) -> Any:
    quality_report = DataQualityReport.from_mapping(
        _read_json_mapping(args.quality_report, "quality_report")
    )
    coverage_report = CoverageReport.from_mapping(
        _read_json_mapping(args.coverage_report, "coverage_report")
    )
    source_manifest = _read_json_mapping(args.source_manifest, "source_manifest")
    return resolve_label_materialization_dataset(
        args.dataset_registry,
        args.dataset_version_id,
        lifecycle_state=args.lifecycle_state,
        quality_report=quality_report,
        coverage_report=coverage_report,
        source_manifest=source_manifest,
        code_hash=args.code_hash,
        config_hash=args.config_hash,
    )


def _build_label_definition(args: argparse.Namespace) -> Any:
    label_spec = _read_json_mapping(args.label_spec, "label_spec")
    dataset_version_ids = (args.dataset_version_id,)
    if args.label_family == "fixed_horizon":
        return build_fixed_horizon_label_definition(
            args.label_name,
            label_spec,
            dataset_version_ids=dataset_version_ids,
        )
    if args.label_family == "cost_adjusted":
        return build_cost_adjusted_label_definition(
            args.label_name,
            label_spec,
            dataset_version_ids=dataset_version_ids,
        )
    if args.label_family == "path":
        return build_path_label_definition(
            args.label_name,
            label_spec,
            dataset_version_ids=dataset_version_ids,
            price_field=args.price_field,
        )
    if args.label_family == "event":
        return build_event_label_definition(
            args.label_name,
            label_spec,
            dataset_version_ids=dataset_version_ids,
        )
    raise LabelCliError(f"unsupported label family: {args.label_family}")


def _optional_label_registry_path(args: argparse.Namespace) -> Path | None:
    if args.registry_path:
        path = Path(args.registry_path)
    else:
        try:
            path = default_label_registry_path(alpha_data_root=args.alpha_data_root)
        except LabelRegistryError as exc:
            if "ALPHA_DATA_ROOT is required" not in str(exc):
                raise
            return None
    return path if path.exists() else None


def _required_label_registry_path(args: argparse.Namespace) -> Path:
    path = _optional_label_registry_path(args)
    if path is None:
        raise LabelCliError("local label registry path is required and must exist")
    return path


def _label_records(registry_path: Path) -> tuple[Any, ...]:
    with _connect_readonly(registry_path) as connection:
        rows = connection.execute(
            """
            SELECT metadata_json
            FROM label_registry_records
            ORDER BY label_id, label_version_id
            """
        ).fetchall()
    return tuple(_label_record_from_json(str(row["metadata_json"])) for row in rows)


def _label_record_by_version(registry_path: Path, label_version_id: str) -> Any:
    with _connect_readonly(registry_path) as connection:
        row = connection.execute(
            """
            SELECT metadata_json
            FROM label_registry_records
            WHERE label_version_id = ?
            """,
            (label_version_id,),
        ).fetchone()
    if row is None:
        raise LabelCliError(f"label version not found in local registry: {label_version_id}")
    return _label_record_from_json(str(row["metadata_json"]))


def _connect_readonly(path: Path) -> sqlite3.Connection:
    if not path.exists():
        raise LabelCliError(f"local label registry does not exist: {path}")
    connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _label_record_summary(record: Any) -> dict[str, object]:
    return {
        "label_id": record.label_id,
        "label_version_id": record.label_version_id,
        "label_spec_id": record.label_spec_id,
        "dataset_version_id": record.dataset_version_id,
        "partition_id": record.partition_id,
        "lifecycle_state": record.lifecycle_state.value,
        "value_record_count": record.value_record_count,
        "exposure_status": record.exposure_status,
    }


def _label_report_summary(record: Any) -> dict[str, object]:
    return {
        **_label_record_summary(record),
        "materialization_plan_id": record.materialization_plan_id,
        "materialization_output_path": record.materialization_output_path,
        "first_event_ts": record.first_event_ts.isoformat(),
        "last_event_ts": record.last_event_ts.isoformat(),
        "first_label_available_ts": record.first_label_available_ts.isoformat(),
        "last_label_available_ts": record.last_label_available_ts.isoformat(),
        "exposure_report": record.exposure_report.to_dict(),
    }


def _optional_partition_plan(path: str | None) -> DatasetPartitionPlan | None:
    if not path:
        return None
    return DatasetPartitionPlan.from_mapping(_read_json_mapping(path, "partition_plan"))


def _optional_json_mapping(path: str | None, object_name: str) -> Mapping[str, Any]:
    if not path:
        return {}
    return _read_json_mapping(path, object_name)


def _optional_json_value(path: str | None) -> object:
    if not path:
        return ()
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _optional_json_records(path: str | None) -> Sequence[Mapping[str, Any]] | None:
    if not path:
        return None
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(value, Mapping):
        return (value,)
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise LabelCliError("label value records JSON root must be a list or mapping")
    records: list[Mapping[str, Any]] = []
    for item in value:
        if isinstance(item, str) or not isinstance(item, Mapping):
            raise LabelCliError("label value records must be mappings")
        records.append(item)
    return tuple(records)


def _read_json_mapping(path: str | Path, object_name: str) -> Mapping[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(value, str) or not isinstance(value, Mapping):
        raise LabelCliError(f"{object_name} JSON root must be a mapping")
    return value


def _emit(payload: Mapping[str, Any], *, emit_json: bool) -> None:
    if emit_json:
        print(json.dumps(payload, sort_keys=True, indent=2))
        return
    command = payload["command"]
    print(f"Label command: {command}")
    if "registry_path" in payload:
        print(f"Registry: {payload['registry_path'] or 'not configured'}")
    if "record_count" in payload:
        print(f"Registered labels: {payload['record_count']}")
    if "plan" in payload:
        plan = payload["plan"]
        if isinstance(plan, Mapping):
            print(f"Plan: {plan['plan_id']}")
            print(f"DatasetVersion: {plan['dataset_version_id']}")
            print(f"Partition: {plan['partition_id']}")
            print(f"Output path: {plan['output_path']}")
        print(f"Dry run: {'yes' if payload.get('dry_run') else 'no'}")
        print("Writes values: no")
    if "report" in payload:
        report = payload["report"]
        if isinstance(report, Mapping):
            print(f"Audit status: {report['status']}")
            print(f"Blocking findings: {report['blocking_finding_count']}")
            print(f"Non-blocking findings: {report['non_blocking_finding_count']}")
    if "input_pack" in payload:
        print(f"FeatureRequest handles: {payload['feature_request_count']}")
        print(f"LabelSpec handles: {payload['label_spec_count']}")
        print("Dataset scope keys: " + ", ".join(payload["dataset_scope_keys"]))
    labels = payload.get("labels")
    if isinstance(labels, Sequence) and not isinstance(labels, str):
        if not labels:
            print("No local label registry records found.")
        for item in labels:
            if isinstance(item, Mapping):
                print(
                    "{label_id} {label_version_id} "
                    "dataset={dataset_version_id} partition={partition_id} "
                    "state={lifecycle_state} exposure={exposure_status}".format(**item)
                )
