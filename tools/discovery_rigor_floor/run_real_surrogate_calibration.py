#!/usr/bin/env python3
"""Coordinator tool for real-data dependence-preserving surrogate calibration."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from alpha_system.core.value_store import ValueStoreFormat, load_parquet_values
from alpha_system.governance.serialization import deserialize
from alpha_system.governance.study_spec import StudySpec, generate_study_spec_id, validate_study_spec
from alpha_system.governance.surrogate_run import (
    CALIBRATION_BLOCKED,
    LEAKAGE_BLOCKED,
    ZERO_PASS_MET,
    SurrogateCalibrationReport,
    SurrogateGateStatus,
    SurrogatePerturbationType,
    calibrate_surrogate_fdr,
    render_value_free_calibration_report,
    require_isolated_namespace,
)
from alpha_system.governance.validation import GovernanceValidationError, ValidationIssue
from alpha_system.runtime.input_resolver import FeatureLabelPackResolver, RuntimeInputResolverError


PERTURBATION_CONFIGS: tuple[SurrogatePerturbationType, ...] = (
    SurrogatePerturbationType.TRADE_DATE_BLOCK_SHUFFLE,
    SurrogatePerturbationType.TRADE_DATE_BLOCK_BOOTSTRAP,
)
SUPPORTED_FORWARD_HORIZONS: dict[str, tuple[int, str]] = {
    "1m": (60, "forward_return_1m"),
    "3m": (180, "forward_return_3m"),
    "5m": (300, "forward_return_5m"),
    "10m": (600, "forward_return_10m"),
    "30m": (1800, "forward_return_30m"),
}
PARTITION_RE = re.compile(r"^(?P<symbol>[A-Z0-9]+)_(?P<year>\d{4})_")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = run_real_surrogate_calibration(
            study_spec_path=args.study_spec,
            alpha_data_root=args.alpha_data_root,
            runs_per_config=args.runs_per_config,
            base_seed=args.base_seed,
            namespace=args.namespace,
            report_out=args.report_out,
        )
    except (
        GovernanceValidationError,
        RuntimeInputResolverError,
        OSError,
        ValueError,
    ) as exc:
        print(json.dumps(_error_payload(exc), sort_keys=True, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["accepted"] else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run real-data surrogate calibration in an isolated namespace. "
            "The report is value-free and contains ids, counts, seeds, and verdicts only."
        )
    )
    parser.add_argument("--study-spec", required=True, help="Committed re-locked StudySpec JSON.")
    parser.add_argument("--alpha-data-root", required=True, help="Local alpha data root.")
    parser.add_argument(
        "--runs-per-config",
        type=int,
        required=True,
        help="Declared K seeded runs per perturbation configuration.",
    )
    parser.add_argument("--base-seed", type=int, required=True, help="Base non-negative seed.")
    parser.add_argument(
        "--namespace",
        required=True,
        help="Existing isolated scratch namespace for local-only staged values and runs.",
    )
    parser.add_argument("--report-out", required=True, help="Value-free Markdown report path.")
    return parser


def run_real_surrogate_calibration(
    *,
    study_spec_path: str | Path,
    alpha_data_root: str | Path,
    runs_per_config: int,
    base_seed: int,
    namespace: str | Path,
    report_out: str | Path,
    resolver: FeatureLabelPackResolver | None = None,
) -> dict[str, Any]:
    """Resolve locked packs, run K per block-null config, and write one report."""

    active_namespace = require_isolated_namespace(namespace)
    active_runs_per_config = _positive_int(runs_per_config, "runs_per_config")
    active_base_seed = _non_negative_int(base_seed, "base_seed")
    study_spec = _load_study_spec(study_spec_path)
    scope = study_spec.dataset_scope
    horizon_text, horizon_seconds, label_type = _declared_primary_horizon(scope)
    label_lock = _select_label_lock(scope, horizon_text)
    feature_lock = _select_feature_lock(scope, label_lock)
    active_resolver = resolver or FeatureLabelPackResolver(alpha_data_root=alpha_data_root)
    resolved = _resolve_records(
        active_resolver,
        feature_lock=feature_lock,
        label_lock=label_lock,
    )

    input_dir = active_namespace / "real_surrogate_inputs" / study_spec.study_spec_id
    input_dir.mkdir(parents=True, exist_ok=True)
    data_version = f"surrogate:{label_lock['dataset_version_id']}"
    factor_values_path = _materialize_factor_jsonl(
        resolved["feature_record"],
        input_dir / "factor-values.jsonl",
        data_version=data_version,
    )
    labels_path = _materialize_label_jsonl(
        resolved["label_record"],
        input_dir / "labels.jsonl",
        data_version=data_version,
        horizon_seconds=horizon_seconds,
        label_type=label_type,
    )
    surrogate_spec = _surrogate_study_spec(
        study_spec,
        feature_record=resolved["feature_record"],
        label_record=resolved["label_record"],
        factor_values_path=factor_values_path,
        labels_path=labels_path,
        data_version=data_version,
        horizon_seconds=horizon_seconds,
        label_type=label_type,
    )

    reports: list[SurrogateCalibrationReport] = []
    for config_index, perturbation_type in enumerate(PERTURBATION_CONFIGS):
        reports.append(
            calibrate_surrogate_fdr(
                (surrogate_spec,),
                run_budget=active_runs_per_config,
                base_seed=active_base_seed + config_index * active_runs_per_config,
                namespace=active_namespace,
                perturbation_type=perturbation_type,
            )
        )
    report = _combine_reports(reports)
    output = Path(report_out).expanduser().resolve(strict=False)
    _reject_production_registry_report_path(output, Path(alpha_data_root).expanduser())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        _render_real_report(
            report,
            study_spec=study_spec,
            runs_per_config=active_runs_per_config,
            horizon_text=horizon_text,
            label_lock=label_lock,
            feature_lock=feature_lock,
            namespace=active_namespace,
        ),
        encoding="utf-8",
    )
    return {
        "status": "ok" if report.accepted else "blocked",
        "accepted": report.accepted,
        "study_spec_id": study_spec.study_spec_id,
        "surrogate_study_spec_id": surrogate_spec.study_spec_id,
        "declared_runs_per_config": active_runs_per_config,
        "perturbation_configs": [item.value for item in PERTURBATION_CONFIGS],
        "threshold_verdict": report.threshold_verdict,
        "run_count": report.run_count,
        "error_count": report.error_count,
        "gate_pass_count": report.gate_pass_count,
        "report_path": output.as_posix(),
    }


def _load_study_spec(path: str | Path) -> StudySpec:
    value = deserialize(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise GovernanceValidationError(
            ValidationIssue(
                field="study_spec",
                code="invalid_study_spec_type",
                message="StudySpec file must contain a JSON object",
                expected="StudySpec mapping",
                actual=type(value).__name__,
            )
        )
    return validate_study_spec(value)


def _declared_primary_horizon(scope: Mapping[str, Any]) -> tuple[str, int, str]:
    declared = scope.get("declared_primary_horizon")
    text = declared if isinstance(declared, str) else ""
    candidates = [match.group(0) for match in re.finditer(r"\d+m", text)]
    primary_horizons = scope.get("primary_horizons")
    if isinstance(primary_horizons, Sequence) and not isinstance(primary_horizons, str):
        candidates.extend(str(item) for item in primary_horizons)
    for candidate in candidates:
        normalized = candidate.strip().lower()
        if normalized in SUPPORTED_FORWARD_HORIZONS:
            seconds, label_type = SUPPORTED_FORWARD_HORIZONS[normalized]
            return normalized, seconds, label_type
    raise GovernanceValidationError(
        ValidationIssue(
            field="dataset_scope.declared_primary_horizon",
            code="unsupported_primary_horizon_for_surrogate_runner",
            message=(
                "real surrogate calibration runner supports the existing diagnostics "
                "forward-return horizons"
            ),
            expected=", ".join(sorted(SUPPORTED_FORWARD_HORIZONS)),
            actual=text or "missing",
        )
    )


def _select_label_lock(scope: Mapping[str, Any], horizon_text: str) -> Mapping[str, Any]:
    locks = _mapping_sequence(scope.get("label_pack_locks"), "label_pack_locks")
    suffix = f"fwd_ret_{horizon_text}"
    candidates = [
        lock
        for lock in locks
        if str(lock.get("label_id", "")).endswith(suffix)
        or str(lock.get("partition", "")).endswith(suffix)
    ]
    if not candidates:
        raise GovernanceValidationError(
            ValidationIssue(
                field="dataset_scope.label_pack_locks",
                code="primary_horizon_label_pack_not_found",
                message="StudySpec must lock a label pack for the declared primary horizon",
                expected=suffix,
                actual=f"{len(locks)} label locks",
            )
        )
    return sorted(
        candidates,
        key=lambda lock: (
            str(lock.get("partition", "")),
            str(lock.get("label_version_id", "")),
        ),
    )[0]


def _select_feature_lock(
    scope: Mapping[str, Any],
    label_lock: Mapping[str, Any],
) -> Mapping[str, Any]:
    locks = _mapping_sequence(scope.get("feature_pack_locks"), "feature_pack_locks")
    label_partition = str(label_lock.get("partition", ""))
    label_match = PARTITION_RE.match(label_partition)
    candidates = locks
    if label_match is not None:
        symbol = label_match.group("symbol")
        year = label_match.group("year")
        expected_partition = f"{symbol}_{year}_full_year"
        candidates = [lock for lock in locks if str(lock.get("partition")) == expected_partition]
    if not candidates:
        raise GovernanceValidationError(
            ValidationIssue(
                field="dataset_scope.feature_pack_locks",
                code="matching_feature_pack_not_found",
                message="StudySpec must lock at least one feature pack for the label partition",
                expected="feature pack for the label symbol/year",
                actual=f"{len(locks)} feature locks",
            )
        )
    return sorted(candidates, key=_feature_lock_sort_key)[0]


def _resolve_records(
    resolver: FeatureLabelPackResolver,
    *,
    feature_lock: Mapping[str, Any],
    label_lock: Mapping[str, Any],
) -> dict[str, Any]:
    resolver.resolve_label_packs(
        (str(label_lock["label_version_id"]),),
        expected_dataset_version_id=str(label_lock["dataset_version_id"]),
        expected_label_spec_ids=(str(label_lock["label_spec_id"]),),
        partition_id=str(label_lock["partition"]),
    )
    resolver.resolve_feature_packs(
        (str(feature_lock["feature_version_id"]),),
        expected_dataset_version_id=str(feature_lock["dataset_version_id"]),
        expected_feature_request_ids=(str(feature_lock["feature_request_id"]),),
        partition_id=str(feature_lock["partition"]),
    )
    label_record = resolver.label_registry.resolve_registered_label(
        str(label_lock["label_version_id"])
    )
    feature_record = resolver.feature_store.resolve_registered_feature(
        str(feature_lock["feature_version_id"])
    )
    if label_record is None or feature_record is None:
        raise GovernanceValidationError(
            ValidationIssue(
                field="runtime_resolver",
                code="resolved_pack_record_missing",
                message="resolved pack handle must have a registered registry record",
                expected="feature and label registry records",
                actual=f"feature={feature_record is not None}, label={label_record is not None}",
            )
        )
    return {"feature_record": feature_record, "label_record": label_record}


def _materialize_factor_jsonl(record: Any, path: Path, *, data_version: str) -> Path:
    rows = _load_value_rows(record)
    converted: list[dict[str, Any]] = []
    counters: dict[tuple[str, str], int] = {}
    numeric_count = 0
    for row in rows:
        event_ts = _iso_text(row.get("event_ts"), "event_ts")
        entity_id = _text(row.get("entity_id"), "entity_id")
        trade_date = event_ts[:10]
        key = (entity_id, trade_date)
        bar_index = counters.get(key, 0)
        counters[key] = bar_index + 1
        value = row.get("value")
        numeric_value = value if _is_number(value) else None
        if numeric_value is not None:
            numeric_count += 1
        converted.append(
            {
                "factor_id": record.feature_spec.feature_id,
                "factor_version": record.feature_version_id,
                "instrument_id": entity_id,
                "event_ts": event_ts,
                "available_ts": _iso_text(row.get("available_ts"), "available_ts"),
                "session_id": _session_id(entity_id, event_ts),
                "bar_index": bar_index,
                "value": value,
                "normalized_value": numeric_value,
                "quality_flags": _quality_flags(row.get("quality_flags")),
                "data_version": data_version,
                "compute_version": "real_surrogate_calibration_bridge_v1",
            }
        )
    if numeric_count == 0:
        raise GovernanceValidationError(
            ValidationIssue(
                field="feature_pack",
                code="non_numeric_feature_pack_for_surrogate",
                message="surrogate diagnostics require a numeric feature value pack",
                expected="at least one numeric feature value",
                actual=record.feature_version_id,
            )
        )
    return _write_jsonl(path, converted)


def _materialize_label_jsonl(
    record: Any,
    path: Path,
    *,
    data_version: str,
    horizon_seconds: int,
    label_type: str,
) -> Path:
    rows = _load_value_rows(record)
    converted: list[dict[str, Any]] = []
    for row in rows:
        event_ts = _iso_text(row.get("event_ts"), "event_ts")
        horizon_end_ts = _iso_text(row.get("horizon_end_ts"), "horizon_end_ts")
        label_available_ts = _iso_text(
            row.get("label_available_ts"),
            "label_available_ts",
        )
        entity_id = _text(row.get("entity_id"), "entity_id")
        converted.append(
            {
                "label_id": label_type,
                "instrument_id": entity_id,
                "event_ts": event_ts,
                "horizon": horizon_seconds,
                "label_type": label_type,
                "value": row.get("value"),
                "path_metadata": {
                    "session_id": _session_id(entity_id, event_ts),
                    "label_version": record.label_version_id,
                    "horizon_end_ts": horizon_end_ts,
                    "required_future_bars": 1,
                    "observed_future_bars": 1,
                },
                "data_version": data_version,
                "label_available_ts": label_available_ts,
            }
        )
    return _write_jsonl(path, converted)


def _surrogate_study_spec(
    study_spec: StudySpec,
    *,
    feature_record: Any,
    label_record: Any,
    factor_values_path: Path,
    labels_path: Path,
    data_version: str,
    horizon_seconds: int,
    label_type: str,
) -> StudySpec:
    payload = study_spec.to_dict()
    payload["dataset_scope"] = {
        **payload["dataset_scope"],
        "surrogate_fdr": {
            "factor_id": feature_record.feature_spec.feature_id,
            "factor_version": feature_record.feature_version_id,
            "label_id": label_type,
            "label_version": label_record.label_version_id,
            "data_version": data_version,
            "factor_values_path": factor_values_path.as_posix(),
            "labels_path": labels_path.as_posix(),
            "horizon_seconds": horizon_seconds,
            "sample_size_thresholds": {"min_total": 30},
            "diagnostic_types": ["directional"],
            "bucket_count": 2,
        },
    }
    payload["study_spec_id"] = generate_study_spec_id(payload)
    return validate_study_spec(payload)


def _combine_reports(reports: Sequence[SurrogateCalibrationReport]) -> SurrogateCalibrationReport:
    rows = tuple(row for report in reports for row in report.per_run)
    run_count = len(rows)
    error_count = sum(1 for row in rows if row["gate_status"] == SurrogateGateStatus.ERROR.value)
    gate_pass_count = sum(1 for row in rows if row.get("passed") is True)
    pass_rate = 0.0 if run_count == 0 else gate_pass_count / run_count
    if gate_pass_count > 0:
        verdict = LEAKAGE_BLOCKED
    elif error_count > 0:
        verdict = CALIBRATION_BLOCKED
    else:
        verdict = ZERO_PASS_MET
    return SurrogateCalibrationReport(
        run_count=run_count,
        error_count=error_count,
        gate_pass_count=gate_pass_count,
        gate_pass_rate=pass_rate,
        threshold_verdict=verdict,
        per_run=rows,
    )


def _render_real_report(
    report: SurrogateCalibrationReport,
    *,
    study_spec: StudySpec,
    runs_per_config: int,
    horizon_text: str,
    label_lock: Mapping[str, Any],
    feature_lock: Mapping[str, Any],
    namespace: Path,
) -> str:
    header = [
        f"# Real-Data Surrogate Calibration: {study_spec.study_spec_id}",
        "",
        "This coordinator report is value-free: it records ids, run counts, seeds, "
        "gate outcomes, and the declared threshold only. It contains no label, "
        "feature, return, diagnostic, signal, or cost values.",
        "",
        "## Scope",
        "",
        f"- Declared K per perturbation config: {runs_per_config}",
        "- Bound statement: zero passes in K bounds false-pass rate at about 3/K at 95%.",
        f"- Declared primary horizon used for this run: `{horizon_text}`.",
        f"- Perturbation configs: {', '.join(item.value for item in PERTURBATION_CONFIGS)}.",
        f"- Resolved label version: `{label_lock['label_version_id']}`.",
        f"- Resolved feature version: `{feature_lock['feature_version_id']}`.",
        f"- Isolated namespace: `{namespace.as_posix()}`.",
        "",
    ]
    rendered = render_value_free_calibration_report(
        report,
        title=f"Surrogate Calibration Counts: {study_spec.study_spec_id}",
    )
    return "\n".join(header) + rendered.split("\n", 1)[1]


def _load_value_rows(record: Any) -> list[dict[str, Any]]:
    value_format = ValueStoreFormat(str(record.value_store_format))
    if value_format is ValueStoreFormat.PARQUET:
        if not record.parquet_path:
            raise ValueError("registered Parquet value store is missing parquet_path")
        return load_parquet_values(record.parquet_path)
    path = Path(record.materialization_output_path)
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(dict(row), sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    return path


def _reject_production_registry_report_path(path: Path, alpha_data_root: Path) -> None:
    registry_root = alpha_data_root.expanduser().resolve(strict=False) / "registry"
    try:
        path.resolve(strict=False).relative_to(registry_root)
    except ValueError:
        return
    raise GovernanceValidationError(
        ValidationIssue(
            field="report_out",
            code="production_registry_report_forbidden",
            message="real surrogate calibration reports must not be written under registry paths",
            expected="value-free report outside ALPHA_DATA_ROOT/registry",
            actual=path.as_posix(),
        )
    )


def _feature_lock_sort_key(lock: Mapping[str, Any]) -> tuple[int, str, str]:
    feature_id = str(lock.get("feature_id", ""))
    score = 0
    if "session_id" in feature_id or feature_id.endswith("_id"):
        score -= 10
    if any(
        token in feature_id
        for token in (
            "minutes",
            "flag",
            "ratio",
            "count",
            "volume",
            "price",
            "return",
            "volatility",
            "delta",
            "spread",
        )
    ):
        score += 5
    return (-score, str(lock.get("partition", "")), str(lock.get("feature_version_id", "")))


def _mapping_sequence(value: Any, field_name: str) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, Sequence) or isinstance(value, str):
        raise GovernanceValidationError(
            ValidationIssue(
                field=f"dataset_scope.{field_name}",
                code="invalid_lock_collection",
                message=f"{field_name} must be a list of lock mappings",
                expected="list of mappings",
                actual=type(value).__name__,
            )
        )
    output: list[Mapping[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise GovernanceValidationError(
                ValidationIssue(
                    field=f"dataset_scope.{field_name}[{index}]",
                    code="invalid_lock_type",
                    message="lock entries must be mappings",
                    expected="mapping",
                    actual=type(item).__name__,
                )
            )
        output.append(item)
    return tuple(output)


def _session_id(entity_id: str, event_ts: str) -> str:
    return f"{entity_id}:{event_ts[:10]}:surrogate"


def _quality_flags(value: Any) -> list[str]:
    if isinstance(value, Sequence) and not isinstance(value, str):
        return [str(item) for item in value]
    return []


def _iso_text(value: Any, field_name: str) -> str:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise ValueError(f"{field_name} must be datetime or ISO-8601 text")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _positive_int(value: Any, field_name: str) -> int:
    active = _non_negative_int(value, field_name)
    if active <= 0:
        raise ValueError(f"{field_name} must be positive")
    return active


def _non_negative_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be a non-negative integer")
    try:
        active = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a non-negative integer") from exc
    if active < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")
    return active


def _error_payload(exc: BaseException) -> dict[str, Any]:
    if isinstance(exc, GovernanceValidationError):
        issues = [issue.to_dict() for issue in exc.issues]
    elif isinstance(exc, RuntimeInputResolverError):
        issues = [exc.reason.to_dict()]
    else:
        issues = [
            {
                "field": "run_real_surrogate_calibration",
                "code": "real_surrogate_calibration_error",
                "message": str(exc),
                "expected": "valid local real-data calibration inputs",
                "actual": type(exc).__name__,
            }
        ]
    return {
        "command": "run_real_surrogate_calibration",
        "status": "rejected",
        "error_type": type(exc).__name__,
        "issues": issues,
    }


if __name__ == "__main__":
    raise SystemExit(main())
