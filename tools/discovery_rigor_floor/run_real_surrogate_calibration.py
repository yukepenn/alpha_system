#!/usr/bin/env python3
"""Coordinator tool for real-data dependence-preserving surrogate calibration."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from alpha_system.core.value_store import ValueStoreFormat, load_parquet_values
from alpha_system.governance.detection_statistic import (
    TRUE_ALPHA_DETECTION_THRESHOLD_ABS_PEARSON_IC,
    evaluate_detection_statistic,
)
from alpha_system.governance.serialization import deserialize
from alpha_system.governance.study_spec import (
    StudySpec,
    generate_study_spec_id,
    validate_study_spec,
)
from alpha_system.governance.surrogate_run import (
    SURROGATE_FALSE_PASS_BOUND_STATEMENT,
    SurrogateCalibrationReport,
    SurrogateGateStatus,
    SurrogatePerturbationType,
    SurrogateStudyRun,
    calibrate_surrogate_fdr,
    render_value_free_calibration_report,
    require_isolated_namespace,
    study_config_for_surrogate_scope,
    surrogate_calibration_report_from_rows,
)
from alpha_system.governance.feature_lock_validation import (
    ValueStoreContentHashVerification,
    verify_registered_value_store_content_hash,
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
SUPPORT_FEATURE_FAMILIES = frozenset({"base_ohlcv", "session_calendar_maintenance"})


@dataclass(frozen=True, slots=True)
class _MaterializedPack:
    path: Path
    source_path: str
    expected_content_hash: str
    actual_content_hash: str
    total_rows: int
    staged_rows: int
    off_grid_event_ts_count: int = 0


@dataclass(frozen=True, slots=True)
class _StagingProvenance:
    factor_id: str
    runtime_factor_id: str
    feature_version_id: str
    label_id: str
    label_version_id: str
    feature_partition: str
    label_partition: str
    feature_rows_total: int
    feature_rows_staged: int
    label_rows_total: int
    label_rows_staged: int
    off_grid_label_event_ts_count: int
    feature_source_path: str
    label_source_path: str


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
            rescore_existing=args.rescore_existing,
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
    parser.add_argument(
        "--rescore-existing",
        action="store_true",
        help=(
            "Re-score existing namespace seed outputs instead of resolving packs "
            "and re-running surrogate studies."
        ),
    )
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
    rescore_existing: bool = False,
) -> dict[str, Any]:
    """Resolve locked packs, run K per block-null config, and write one report."""

    active_namespace = require_isolated_namespace(namespace)
    active_runs_per_config = _positive_int(runs_per_config, "runs_per_config")
    active_base_seed = _non_negative_int(base_seed, "base_seed")
    study_spec = _load_study_spec(study_spec_path)
    scope = study_spec.dataset_scope
    horizon_text, horizon_seconds, label_type = _declared_primary_horizon(scope)
    label_locks = _select_label_locks(scope, horizon_text)
    declared_feature_family = _declared_feature_family(scope)
    declared_factor_ids = _declared_factor_ids(
        scope,
        declared_feature_family=declared_feature_family,
    )
    expected_sub_config_count = _expected_sub_config_count(
        scope,
        label_locks=label_locks,
        declared_feature_family=declared_feature_family,
    )
    if rescore_existing:
        report = _rescore_existing_report(
            active_namespace,
            study_spec=study_spec,
            runs_per_config=active_runs_per_config,
            base_seed=active_base_seed,
            surrogate_spec_count=expected_sub_config_count,
        )
        _write_real_report(
            report,
            report_out=report_out,
            alpha_data_root=alpha_data_root,
            study_spec=study_spec,
            runs_per_config=active_runs_per_config,
            horizon_text=horizon_text,
            declared_feature_family=declared_feature_family,
            declared_factor_ids=declared_factor_ids,
            label_locks=label_locks,
            staging_provenance=(),
            namespace=active_namespace,
        )
        return _result_payload(
            report,
            study_spec=study_spec,
            surrogate_study_spec_id=_surrogate_study_spec_id_from_report(
                report,
                fallback=study_spec.study_spec_id,
            ),
            runs_per_config=active_runs_per_config,
            report_out=report_out,
            alpha_data_root=alpha_data_root,
            declared_factor_ids=declared_factor_ids,
            staged_label_pack_count=len(label_locks),
        )

    active_resolver = resolver or FeatureLabelPackResolver(alpha_data_root=alpha_data_root)
    input_root = active_namespace / "real_surrogate_inputs" / study_spec.study_spec_id
    input_root.mkdir(parents=True, exist_ok=True)
    surrogate_specs: list[StudySpec] = []
    staging_provenance: list[_StagingProvenance] = []
    for label_lock in label_locks:
        feature_locks = _declared_feature_locks_for_label(
            scope,
            label_lock=label_lock,
            declared_feature_family=declared_feature_family,
        )
        for feature_lock in feature_locks:
            resolved = _resolve_records(
                active_resolver,
                feature_lock=feature_lock,
                label_lock=label_lock,
            )
            input_dir = (
                input_root
                / _path_token(str(label_lock["partition"]))
                / _path_token(str(feature_lock["feature_id"]))
            )
            input_dir.mkdir(parents=True, exist_ok=True)
            data_version = (
                f"surrogate:{label_lock['dataset_version_id']}:{label_lock['partition']}"
            )
            factor_values = _materialize_factor_jsonl(
                resolved["feature_record"],
                input_dir / "factor-values.jsonl",
                data_version=data_version,
                feature_lock=feature_lock,
            )
            labels = _materialize_label_jsonl(
                resolved["label_record"],
                input_dir / "labels.jsonl",
                data_version=data_version,
                horizon_seconds=horizon_seconds,
                label_type=label_type,
                label_lock=label_lock,
            )
            surrogate_spec = _surrogate_study_spec(
                study_spec,
                feature_record=resolved["feature_record"],
                label_record=resolved["label_record"],
                factor_values_path=factor_values.path,
                labels_path=labels.path,
                data_version=data_version,
                horizon_seconds=horizon_seconds,
                label_type=label_type,
            )
            runtime_factor_id = _runtime_factor_id(
                surrogate_spec,
                seed=active_base_seed,
                labels_path=labels.path,
                output_dir=input_dir / "runtime_factor_probe",
            )
            factor_id = _lock_text(feature_lock, "feature_id", "feature lock")
            if runtime_factor_id != factor_id:
                raise GovernanceValidationError(
                    ValidationIssue(
                        field="dataset_scope.surrogate_fdr.factor_id",
                        code="runtime_factor_id_mismatch",
                        message=(
                            "calibration staging factor_id must match the "
                            "study runtime StudyConfig.factor_id construction path"
                        ),
                        expected=factor_id,
                        actual=runtime_factor_id,
                    )
                )
            surrogate_specs.append(surrogate_spec)
            staging_provenance.append(
                _StagingProvenance(
                    factor_id=factor_id,
                    runtime_factor_id=runtime_factor_id,
                    feature_version_id=_lock_text(
                        feature_lock,
                        "feature_version_id",
                        "feature lock",
                    ),
                    label_id=label_type,
                    label_version_id=_lock_text(
                        label_lock,
                        "label_version_id",
                        "label lock",
                    ),
                    feature_partition=_lock_text(feature_lock, "partition", "feature lock"),
                    label_partition=_lock_text(label_lock, "partition", "label lock"),
                    feature_rows_total=factor_values.total_rows,
                    feature_rows_staged=factor_values.staged_rows,
                    label_rows_total=labels.total_rows,
                    label_rows_staged=labels.staged_rows,
                    off_grid_label_event_ts_count=labels.off_grid_event_ts_count,
                    feature_source_path=factor_values.source_path,
                    label_source_path=labels.source_path,
                )
            )
    if not surrogate_specs:
        raise GovernanceValidationError(
            ValidationIssue(
                field="dataset_scope.feature_pack_locks",
                code="no_declared_factor_sub_configs",
                message="declared factor derivation produced no surrogate sub-configs",
                expected="one or more declared factor locks matching label partitions",
                actual="0",
            )
        )

    reports: list[SurrogateCalibrationReport] = []
    seed_block_size = len(surrogate_specs) * active_runs_per_config
    for config_index, perturbation_type in enumerate(PERTURBATION_CONFIGS):
        reports.append(
            calibrate_surrogate_fdr(
                tuple(surrogate_specs),
                run_budget=active_runs_per_config,
                base_seed=active_base_seed + config_index * seed_block_size,
                namespace=active_namespace,
                perturbation_type=perturbation_type,
            )
        )
    report = _combine_reports(reports)
    _write_real_report(
        report,
        report_out=report_out,
        alpha_data_root=alpha_data_root,
        study_spec=study_spec,
        runs_per_config=active_runs_per_config,
        horizon_text=horizon_text,
        declared_feature_family=declared_feature_family,
        declared_factor_ids=declared_factor_ids,
        label_locks=label_locks,
        staging_provenance=tuple(staging_provenance),
        namespace=active_namespace,
    )
    return _result_payload(
        report,
        study_spec=study_spec,
        surrogate_study_spec_id=surrogate_specs[0].study_spec_id,
        runs_per_config=active_runs_per_config,
        report_out=report_out,
        alpha_data_root=alpha_data_root,
        surrogate_study_spec_ids=tuple(spec.study_spec_id for spec in surrogate_specs),
        declared_factor_ids=declared_factor_ids,
        staged_label_pack_count=len(label_locks),
    )


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


def _select_label_locks(
    scope: Mapping[str, Any],
    horizon_text: str,
) -> tuple[Mapping[str, Any], ...]:
    locks = _mapping_sequence(scope.get("label_pack_locks"), "label_pack_locks")
    suffix = f"fwd_ret_{horizon_text}"
    candidates = tuple(
        lock
        for lock in locks
        if str(lock.get("label_id", "")).endswith(suffix)
        or str(lock.get("partition", "")).endswith(suffix)
    )
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
    _require_unique_lock_ids(
        candidates,
        lock_id_field="label_version_id",
        field="dataset_scope.label_pack_locks",
        code="duplicate_primary_horizon_label_lock",
    )
    return candidates


def _declared_feature_family(scope: Mapping[str, Any]) -> str:
    locks = _mapping_sequence(scope.get("feature_pack_locks"), "feature_pack_locks")
    candidate_families = _unique_in_order(
        _lock_text(lock, "feature_family", "feature lock")
        for lock in locks
        if not _support_feature_family(_lock_text(lock, "feature_family", "feature lock"))
    )
    if len(candidate_families) != 1:
        raise GovernanceValidationError(
            ValidationIssue(
                field="dataset_scope.feature_pack_locks",
                code=(
                    "declared_factor_family_missing"
                    if not candidate_families
                    else "declared_factor_family_ambiguous"
                ),
                message=(
                    "StudySpec must expose exactly one non-support feature family "
                    "for real surrogate calibration"
                ),
                expected="one non-support feature_family",
                actual=", ".join(candidate_families) if candidate_families else "none",
            )
        )
    return candidate_families[0]


def _declared_factor_ids(
    scope: Mapping[str, Any],
    *,
    declared_feature_family: str,
) -> tuple[str, ...]:
    locks = _mapping_sequence(scope.get("feature_pack_locks"), "feature_pack_locks")
    factor_ids = _unique_in_order(
        _lock_text(lock, "feature_id", "feature lock")
        for lock in locks
        if _lock_text(lock, "feature_family", "feature lock") == declared_feature_family
    )
    if not factor_ids:
        raise GovernanceValidationError(
            ValidationIssue(
                field="dataset_scope.feature_pack_locks",
                code="declared_factor_lock_missing",
                message="declared feature family must contain at least one factor lock",
                expected=f"feature_family={declared_feature_family}",
                actual="0 locks",
            )
        )
    return factor_ids


def _expected_sub_config_count(
    scope: Mapping[str, Any],
    *,
    label_locks: Sequence[Mapping[str, Any]],
    declared_feature_family: str,
) -> int:
    return sum(
        len(
            _declared_feature_locks_for_label(
                scope,
                label_lock=label_lock,
                declared_feature_family=declared_feature_family,
            )
        )
        for label_lock in label_locks
    )


def _declared_feature_locks_for_label(
    scope: Mapping[str, Any],
    *,
    label_lock: Mapping[str, Any],
    declared_feature_family: str,
) -> tuple[Mapping[str, Any], ...]:
    locks = _mapping_sequence(scope.get("feature_pack_locks"), "feature_pack_locks")
    label_partition = str(label_lock.get("partition", ""))
    label_match = PARTITION_RE.match(label_partition)
    expected_partition = ""
    if label_match is not None:
        symbol = label_match.group("symbol")
        year = label_match.group("year")
        expected_partition = f"{symbol}_{year}_full_year"
    candidates = tuple(
        lock
        for lock in locks
        if _lock_text(lock, "feature_family", "feature lock") == declared_feature_family
        and (not expected_partition or str(lock.get("partition")) == expected_partition)
    )
    if not candidates:
        raise GovernanceValidationError(
            ValidationIssue(
                field="dataset_scope.feature_pack_locks",
                code="matching_feature_pack_not_found",
                message=(
                    "StudySpec must lock declared feature-family packs for the "
                    "label partition"
                ),
                expected=f"feature_family={declared_feature_family} partition={expected_partition}",
                actual=f"{len(locks)} feature locks",
            )
        )
    feature_ids = _unique_in_order(
        _lock_text(lock, "feature_id", "feature lock") for lock in candidates
    )
    output: list[Mapping[str, Any]] = []
    for feature_id in feature_ids:
        matches = tuple(
            lock
            for lock in candidates
            if _lock_text(lock, "feature_id", "feature lock") == feature_id
        )
        if len(matches) != 1:
            raise GovernanceValidationError(
                ValidationIssue(
                    field="dataset_scope.feature_pack_locks",
                    code="ambiguous_declared_factor_lock",
                    message=(
                        "declared factor must resolve to exactly one feature lock "
                        "for each label partition"
                    ),
                    expected=(
                        f"one lock for feature_id={feature_id} "
                        f"partition={expected_partition or label_partition}"
                    ),
                    actual=f"{len(matches)} locks",
                )
            )
        output.append(matches[0])
    return tuple(output)


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
    _assert_record_matches_lock(
        feature_record,
        feature_lock,
        version_field="feature_version_id",
        pack_kind="feature",
    )
    _assert_record_matches_lock(
        label_record,
        label_lock,
        version_field="label_version_id",
        pack_kind="label",
    )
    _assert_feature_record_factor(feature_record, feature_lock)
    return {"feature_record": feature_record, "label_record": label_record}


def _materialize_factor_jsonl(
    record: Any,
    path: Path,
    *,
    data_version: str,
    feature_lock: Mapping[str, Any],
) -> _MaterializedPack:
    rows, verification = _load_value_rows(
        record,
        pack_kind="feature",
        version_id=_lock_text(feature_lock, "feature_version_id", "feature lock"),
    )
    staged_rows = _filter_rows_by_version(
        rows,
        expected_version=_lock_text(feature_lock, "feature_version_id", "feature lock"),
        row_version_field="feature_version_id",
        pack_kind="feature",
    )
    converted: list[dict[str, Any]] = []
    counters: dict[tuple[str, str], int] = {}
    numeric_count = 0
    for row in staged_rows:
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
                "factor_id": _lock_text(feature_lock, "feature_id", "feature lock"),
                "factor_version": _lock_text(
                    feature_lock,
                    "feature_version_id",
                    "feature lock",
                ),
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
    output = _write_jsonl(path, converted)
    return _MaterializedPack(
        path=output,
        source_path=verification.path,
        expected_content_hash=verification.expected_content_hash,
        actual_content_hash=verification.actual_content_hash,
        total_rows=len(rows),
        staged_rows=len(staged_rows),
    )


def _materialize_label_jsonl(
    record: Any,
    path: Path,
    *,
    data_version: str,
    horizon_seconds: int,
    label_type: str,
    label_lock: Mapping[str, Any],
) -> _MaterializedPack:
    rows, verification = _load_value_rows(
        record,
        pack_kind="label",
        version_id=_lock_text(label_lock, "label_version_id", "label lock"),
    )
    staged_rows = _filter_rows_by_version(
        rows,
        expected_version=_lock_text(label_lock, "label_version_id", "label lock"),
        row_version_field="label_version_id",
        pack_kind="label",
    )
    converted: list[dict[str, Any]] = []
    for row in staged_rows:
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
    output = _write_jsonl(path, converted)
    return _MaterializedPack(
        path=output,
        source_path=verification.path,
        expected_content_hash=verification.expected_content_hash,
        actual_content_hash=verification.actual_content_hash,
        total_rows=len(rows),
        staged_rows=len(staged_rows),
        off_grid_event_ts_count=_off_grid_event_ts_count(staged_rows),
    )


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
    return surrogate_calibration_report_from_rows(rows)


def _rescore_existing_report(
    namespace: Path,
    *,
    study_spec: StudySpec,
    runs_per_config: int,
    base_seed: int,
    surrogate_spec_count: int,
) -> SurrogateCalibrationReport:
    rows: list[dict[str, Any]] = []
    seed_block_size = surrogate_spec_count * runs_per_config
    for config_index, perturbation_type in enumerate(PERTURBATION_CONFIGS):
        for spec_index in range(surrogate_spec_count):
            for run_index in range(runs_per_config):
                seed = (
                    base_seed
                    + config_index * seed_block_size
                    + spec_index * runs_per_config
                    + run_index
                )
                rows.append(
                    _rescore_existing_seed(
                        namespace,
                        study_spec=study_spec,
                        perturbation_type=perturbation_type,
                        seed=seed,
                    )
                )
    return surrogate_calibration_report_from_rows(rows)


def _rescore_existing_seed(
    namespace: Path,
    *,
    study_spec: StudySpec,
    perturbation_type: SurrogatePerturbationType,
    seed: int,
) -> dict[str, Any]:
    seed_dir = namespace / f"seed_{seed}"
    summary_path = seed_dir / "study_outputs" / "diagnostic_summary.json"
    try:
        surrogate_run = _load_optional_surrogate_run(seed_dir)
        if surrogate_run is not None:
            if surrogate_run.seed != seed:
                raise ValueError("surrogate run record seed does not match seed directory")
            if surrogate_run.perturbation_type is not perturbation_type:
                raise ValueError(
                    "surrogate run record perturbation_type does not match rescore grid"
                )
        if not summary_path.is_file():
            raise FileNotFoundError(summary_path.as_posix())
        summary = _load_diagnostic_summary_mapping(summary_path)
        statistic = evaluate_detection_statistic(
            summary,
            threshold_abs_pearson_ic=TRUE_ALPHA_DETECTION_THRESHOLD_ABS_PEARSON_IC,
        )
        eligibility_clean = _eligibility_clean_from_summary(summary)
    except (OSError, ValueError) as exc:
        return _rescore_error_row(
            study_spec,
            perturbation_type=perturbation_type,
            seed=seed,
            exc=exc,
        )

    statistic_passed = statistic.detected
    return {
        "study_spec_id": (
            surrogate_run.original_study_spec_id
            if surrogate_run is not None
            else study_spec.study_spec_id
        ),
        "perturbation_type": (
            surrogate_run.perturbation_type.value
            if surrogate_run is not None
            else perturbation_type.value
        ),
        "seed": seed,
        "surrogate_id": surrogate_run.surrogate_id if surrogate_run is not None else "",
        "gate_status": (
            SurrogateGateStatus.PASSED.value
            if statistic_passed
            else SurrogateGateStatus.BLOCKED.value
        ),
        "passed": statistic_passed,
        "statistic_passed": statistic_passed,
        "eligibility_clean": eligibility_clean,
        "reason_code": None if statistic_passed else "UNDERPOWERED",
    }


def _load_optional_surrogate_run(seed_dir: Path) -> SurrogateStudyRun | None:
    record_dir = seed_dir / "surrogate_runs"
    if not record_dir.exists():
        return None
    records = sorted(record_dir.glob("*.json"))
    if not records:
        return None
    if len(records) > 1:
        raise ValueError(f"expected one surrogate run record under {record_dir}")
    return SurrogateStudyRun.from_canonical_json(records[0].read_text(encoding="utf-8"))


def _load_diagnostic_summary_mapping(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError("diagnostic_summary.json root must be a JSON object")
    if not isinstance(value.get("diagnostics"), Mapping):
        raise ValueError("diagnostic_summary.json requires diagnostics mapping")
    if not isinstance(value.get("warnings"), list):
        raise ValueError("diagnostic_summary.json requires warnings list")
    return value


def _eligibility_clean_from_summary(summary: Mapping[str, Any]) -> bool:
    warnings = summary.get("warnings")
    if not isinstance(warnings, list):
        raise ValueError("diagnostic_summary.json requires warnings list")
    return len(warnings) == 0


def _rescore_error_row(
    study_spec: StudySpec,
    *,
    perturbation_type: SurrogatePerturbationType,
    seed: int,
    exc: BaseException,
) -> dict[str, Any]:
    return {
        "study_spec_id": study_spec.study_spec_id,
        "perturbation_type": perturbation_type.value,
        "seed": seed,
        "surrogate_id": "",
        "gate_status": SurrogateGateStatus.ERROR.value,
        "passed": False,
        "statistic_passed": False,
        "eligibility_clean": False,
        "reason_code": None,
        "error_type": type(exc).__name__,
    }


def _surrogate_study_spec_id_from_report(
    report: SurrogateCalibrationReport,
    *,
    fallback: str,
) -> str:
    for row in report.per_run:
        if not row.get("surrogate_id"):
            continue
        value = row.get("study_spec_id")
        if isinstance(value, str) and value:
            return value
    for row in report.per_run:
        value = row.get("study_spec_id")
        if isinstance(value, str) and value:
            return value
    return fallback


def _write_real_report(
    report: SurrogateCalibrationReport,
    *,
    report_out: str | Path,
    alpha_data_root: str | Path,
    study_spec: StudySpec,
    runs_per_config: int,
    horizon_text: str,
    declared_feature_family: str,
    declared_factor_ids: Sequence[str],
    label_locks: Sequence[Mapping[str, Any]],
    staging_provenance: Sequence[_StagingProvenance],
    namespace: Path,
) -> Path:
    output = Path(report_out).expanduser().resolve(strict=False)
    _reject_production_registry_report_path(output, Path(alpha_data_root).expanduser())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        _render_real_report(
            report,
            study_spec=study_spec,
            runs_per_config=runs_per_config,
            horizon_text=horizon_text,
            declared_feature_family=declared_feature_family,
            declared_factor_ids=declared_factor_ids,
            label_locks=label_locks,
            staging_provenance=staging_provenance,
            namespace=namespace,
        ),
        encoding="utf-8",
    )
    return output


def _result_payload(
    report: SurrogateCalibrationReport,
    *,
    study_spec: StudySpec,
    surrogate_study_spec_id: str,
    runs_per_config: int,
    report_out: str | Path,
    alpha_data_root: str | Path,
    surrogate_study_spec_ids: Sequence[str] = (),
    declared_factor_ids: Sequence[str] = (),
    staged_label_pack_count: int = 0,
) -> dict[str, Any]:
    output = Path(report_out).expanduser().resolve(strict=False)
    _reject_production_registry_report_path(output, Path(alpha_data_root).expanduser())
    surrogate_ids = tuple(surrogate_study_spec_ids) or (surrogate_study_spec_id,)
    return {
        "status": "ok" if report.accepted else "blocked",
        "accepted": report.accepted,
        "study_spec_id": study_spec.study_spec_id,
        "surrogate_study_spec_id": surrogate_study_spec_id,
        "surrogate_study_spec_ids": list(surrogate_ids),
        "surrogate_study_spec_count": len(surrogate_ids),
        "declared_factor_ids": list(declared_factor_ids),
        "declared_factor_count": len(declared_factor_ids),
        "staged_label_pack_count": staged_label_pack_count,
        "declared_runs_per_config": runs_per_config,
        "perturbation_configs": [item.value for item in PERTURBATION_CONFIGS],
        "threshold_verdict": report.threshold_verdict,
        "run_count": report.run_count,
        "error_count": report.error_count,
        "gate_pass_count": report.gate_pass_count,
        "statistic_pass_count": report.statistic_pass_count,
        "eligibility_clean_count": report.eligibility_clean_count,
        "report_path": output.as_posix(),
    }


def _render_real_report(
    report: SurrogateCalibrationReport,
    *,
    study_spec: StudySpec,
    runs_per_config: int,
    horizon_text: str,
    declared_feature_family: str,
    declared_factor_ids: Sequence[str],
    label_locks: Sequence[Mapping[str, Any]],
    staging_provenance: Sequence[_StagingProvenance],
    namespace: Path,
) -> str:
    label_versions = _unique_in_order(
        _lock_text(lock, "label_version_id", "label lock") for lock in label_locks
    )
    off_grid_count = sum(item.off_grid_label_event_ts_count for item in staging_provenance)
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
        f"- Bound statement: {SURROGATE_FALSE_PASS_BOUND_STATEMENT}.",
        f"- Declared primary horizon used for this run: `{horizon_text}`.",
        f"- Perturbation configs: {', '.join(item.value for item in PERTURBATION_CONFIGS)}.",
        "- Runtime factor derivation path: "
        "`alpha_system.governance.surrogate_run.study_config_for_surrogate_scope` "
        "-> `StudyConfig.from_mapping`.",
        f"- Declared feature family: `{declared_feature_family}`.",
        f"- Declared factor count: {len(declared_factor_ids)}.",
        f"- Declared factors: {_inline_code_list(declared_factor_ids)}.",
        f"- Declared label pack count: {len(label_locks)}.",
        f"- Declared label versions: {_inline_code_list(label_versions)}.",
        f"- Staged surrogate sub-config count: {len(staging_provenance)}.",
        f"- Off-grid locked label event_ts count: {off_grid_count}.",
        f"- Isolated namespace: `{namespace.as_posix()}`.",
        "",
        "## Staging Provenance",
        "",
    ]
    if staging_provenance:
        header.extend(
            [
                "| Factor | Runtime Factor | Feature Version | Label Version | "
                "Feature Partition | Label Partition | Feature Rows | Label Rows | "
                "Off-Grid Label event_ts |",
                "|---|---|---|---|---|---|---:|---:|---:|",
            ]
        )
        for item in staging_provenance:
            header.append(
                "| `{factor_id}` | `{runtime_factor_id}` | `{feature_version_id}` | "
                "`{label_version_id}` | `{feature_partition}` | `{label_partition}` | "
                "{feature_rows_staged}/{feature_rows_total} | "
                "{label_rows_staged}/{label_rows_total} | "
                "{off_grid_label_event_ts_count} |".format(
                    factor_id=item.factor_id,
                    runtime_factor_id=item.runtime_factor_id,
                    feature_version_id=item.feature_version_id,
                    label_version_id=item.label_version_id,
                    feature_partition=item.feature_partition,
                    label_partition=item.label_partition,
                    feature_rows_staged=item.feature_rows_staged,
                    feature_rows_total=item.feature_rows_total,
                    label_rows_staged=item.label_rows_staged,
                    label_rows_total=item.label_rows_total,
                    off_grid_label_event_ts_count=item.off_grid_label_event_ts_count,
                )
            )
    else:
        header.append("- No values were staged; `--rescore-existing` mode only rescored outputs.")
    header.append("")
    rendered = render_value_free_calibration_report(
        report,
        title=f"Surrogate Calibration Counts: {study_spec.study_spec_id}",
    )
    return "\n".join(header) + rendered.split("\n", 1)[1]


def _load_value_rows(
    record: Any,
    *,
    pack_kind: str,
    version_id: str,
) -> tuple[list[dict[str, Any]], ValueStoreContentHashVerification]:
    verification = verify_registered_value_store_content_hash(
        record,
        pack_kind=pack_kind,
        version_id=version_id,
    )
    value_format = ValueStoreFormat(str(record.value_store_format))
    if value_format in (ValueStoreFormat.PARQUET, ValueStoreFormat.DUAL) and record.parquet_path:
        if not record.parquet_path:
            raise ValueError("registered Parquet value store is missing parquet_path")
        return load_parquet_values(record.parquet_path), verification
    path = Path(record.materialization_output_path)
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ], verification


def _filter_rows_by_version(
    rows: Sequence[Mapping[str, Any]],
    *,
    expected_version: str,
    row_version_field: str,
    pack_kind: str,
) -> list[dict[str, Any]]:
    staged: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        actual_version = row.get(row_version_field)
        if not isinstance(actual_version, str) or not actual_version.strip():
            raise GovernanceValidationError(
                ValidationIssue(
                    field=f"{pack_kind}_pack.rows[{index}].{row_version_field}",
                    code="value_row_version_field_missing",
                    message=(
                        "value-store rows must carry their version id so staging can "
                        "filter a multi-version pack"
                    ),
                    expected=row_version_field,
                    actual=(
                        type(actual_version).__name__
                        if actual_version is not None
                        else "missing"
                    ),
                )
            )
        if actual_version.strip() == expected_version:
            staged.append(dict(row))
    if not staged:
        raise GovernanceValidationError(
            ValidationIssue(
                field=f"{pack_kind}_pack.{row_version_field}",
                code="locked_value_rows_not_found",
                message="value store contains no rows for the locked version id",
                expected=expected_version,
                actual=f"{len(rows)} total rows",
            )
        )
    return staged


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


def _lock_text(lock: Mapping[str, Any], key: str, label: str) -> str:
    value = lock.get(key)
    if not isinstance(value, str) or not value.strip():
        raise GovernanceValidationError(
            ValidationIssue(
                field=f"{label}.{key}",
                code="missing_lock_field",
                message="lock entry is missing a required text field",
                expected=key,
                actual=type(value).__name__ if value is not None else "missing",
            )
        )
    return value.strip()


def _require_unique_lock_ids(
    locks: Sequence[Mapping[str, Any]],
    *,
    lock_id_field: str,
    field: str,
    code: str,
) -> None:
    seen: set[str] = set()
    duplicates: list[str] = []
    for lock in locks:
        lock_id = _lock_text(lock, lock_id_field, "lock")
        if lock_id in seen:
            duplicates.append(lock_id)
        seen.add(lock_id)
    if duplicates:
        raise GovernanceValidationError(
            ValidationIssue(
                field=field,
                code=code,
                message="declared lock collection contains duplicate version ids",
                expected="unique lock ids",
                actual=", ".join(duplicates),
            )
        )


def _support_feature_family(feature_family: str) -> bool:
    return (
        feature_family in SUPPORT_FEATURE_FAMILIES
        or feature_family.startswith("session_calendar")
    )


def _unique_in_order(values: Sequence[str] | Any) -> tuple[str, ...]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value)
        if text in seen:
            continue
        seen.add(text)
        output.append(text)
    return tuple(output)


def _assert_record_matches_lock(
    record: Any,
    lock: Mapping[str, Any],
    *,
    version_field: str,
    pack_kind: str,
) -> None:
    checks = (
        (version_field, version_field),
        ("dataset_version_id", "dataset_version_id"),
        ("partition_id", "partition"),
    )
    for record_attr, lock_key in checks:
        actual = getattr(record, record_attr, None)
        expected = _lock_text(lock, lock_key, f"{pack_kind} lock")
        if actual != expected:
            raise GovernanceValidationError(
                ValidationIssue(
                    field=f"{pack_kind}_record.{record_attr}",
                    code="resolved_record_lock_mismatch",
                    message=(
                        "resolved registry record must match the StudySpec lock "
                        "before staging"
                    ),
                    expected=expected,
                    actual=str(actual),
                )
            )


def _assert_feature_record_factor(record: Any, feature_lock: Mapping[str, Any]) -> None:
    feature_spec = getattr(record, "feature_spec", None)
    actual = getattr(feature_spec, "feature_id", None)
    expected = _lock_text(feature_lock, "feature_id", "feature lock")
    if actual != expected:
        raise GovernanceValidationError(
            ValidationIssue(
                field="feature_record.feature_spec.feature_id",
                code="resolved_feature_factor_mismatch",
                message="resolved feature record must match the declared factor lock",
                expected=expected,
                actual=str(actual),
            )
        )


def _runtime_factor_id(
    study_spec: StudySpec,
    *,
    seed: int,
    labels_path: Path,
    output_dir: Path,
) -> str:
    scope = study_spec.dataset_scope.get("surrogate_fdr")
    if not isinstance(scope, Mapping):
        raise GovernanceValidationError(
            ValidationIssue(
                field="dataset_scope.surrogate_fdr",
                code="missing_surrogate_scope_after_staging",
                message="staged surrogate StudySpec must carry surrogate_fdr scope",
                expected="mapping",
                actual=type(scope).__name__,
            )
        )
    return study_config_for_surrogate_scope(
        study_spec,
        scope=scope,
        seed=seed,
        shuffled_labels_path=labels_path,
        output_dir=output_dir,
    ).factor_id


def _off_grid_event_ts_count(rows: Sequence[Mapping[str, Any]]) -> int:
    count = 0
    for row in rows:
        event_ts = _iso_text(row.get("event_ts"), "event_ts")
        parsed = datetime.fromisoformat(event_ts.replace("Z", "+00:00"))
        if parsed.second != 0 or parsed.microsecond != 0:
            count += 1
    return count


def _path_token(value: str) -> str:
    token = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")
    if not token:
        raise ValueError("path token cannot be empty")
    return token


def _inline_code_list(values: Sequence[str]) -> str:
    if not values:
        return "`none`"
    return ", ".join(f"`{value}`" for value in values)


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
