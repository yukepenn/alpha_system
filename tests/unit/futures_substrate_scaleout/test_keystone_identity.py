from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from alpha_system.core.value_store import (
    ValueStoreFormat,
    load_parquet_values,
    read_parquet_manifest,
)
from alpha_system.data.foundation.datasets import (
    CoverageReport,
    DataQualityReport,
    DatasetVersion,
    ReportStatus,
    compute_quality_report_hash,
)
from alpha_system.features import consumption
from alpha_system.features.contracts import FeatureSetSpec
from alpha_system.features.engine import (
    FeatureMaterializationInputs,
    build_feature_materialization_plan,
    materialize_features,
)
from alpha_system.features.families.ohlcv import (
    OHLCVFeatureName,
    build_ohlcv_feature_definition,
)
from alpha_system.features.store import FeatureStore
from alpha_system.governance.duplicate_exposure import (
    ExposureCheckResult,
    ExposureRegistryStatus,
)
from alpha_system.governance.feature_lock_validation import (
    FeatureLockValidationError,
    validate_feature_locks,
)
from alpha_system.governance.feature_request import (
    FeatureRequest,
    FeatureRequestApprovalStatus,
    create_feature_request,
)
from alpha_system.governance.label_spec import LabelSpec, create_label_spec
from alpha_system.governance.study_input_pack import StudyInputPack
from alpha_system.labels.engine import (
    LabelMaterializationInputs,
    build_label_materialization_plan,
    materialize_labels,
)
from alpha_system.labels.families.fixed_horizon import (
    FixedHorizonLabelName,
    build_fixed_horizon_label_definition,
)
from alpha_system.labels.registry import LabelRegistry
from alpha_system.runtime.entry_contract import (
    RuntimeEntryRequest,
    RuntimeEntryStatus,
    evaluate_runtime_entry_request,
)
from alpha_system.runtime.input_resolver import (
    FeatureLabelPackResolver,
    resolve_runtime_input_pack,
)

ALPHA_SPEC_REF = "aspec_af848bc999a4c4b11a421bd0"
STUDY_SPEC_REF = "sspec_438ceffd40855205de5497f0"
HASH_0 = "0" * 64
HASH_1 = "1" * 64
HASH_2 = "2" * 64
REQUIRED_VALUE_FIELDS = {
    "value_store_format",
    "parquet_path",
    "value_content_hash",
    "value_schema_version",
}


def test_keystone_identity_preflight_parquet_registry_and_resolver_fail_closed(
    tmp_path: Path,
) -> None:
    pytest.importorskip("polars")
    dataset_id = "dsv_synthetic_keystone_p04"
    accepted = _accepted_version(dataset_id)

    feature_request = _approved_request(OHLCVFeatureName.RETURNS)
    feature_definition = build_ohlcv_feature_definition(
        OHLCVFeatureName.RETURNS,
        feature_request,
        _EmptyRegistryReader(),
        dataset_version_ids=(dataset_id,),
        reset_on_session=False,
    )
    feature_set = FeatureSetSpec(
        feature_set_id="feature_set_keystone_p04",
        feature_set_version="v1",
        features=(feature_definition.spec,),
    )
    feature_plan = build_feature_materialization_plan(
        feature_set,
        accepted,
        partition_id="development_partition",
        alpha_data_root=tmp_path,
    )
    feature_inputs = FeatureMaterializationInputs(
        accepted_version=accepted,
        bar_rows=_bar_rows(dataset_id, length=3),
    )

    feature_preview = materialize_features(
        feature_plan,
        feature_inputs,
        (feature_definition,),
        dry_run=True,
        value_store_format=ValueStoreFormat.PARQUET,
    )
    feature_result = materialize_features(
        feature_plan,
        feature_inputs,
        (feature_definition,),
        value_store_format=ValueStoreFormat.PARQUET,
    )

    assert feature_preview.plan.to_dict() == feature_result.plan.to_dict()
    assert feature_result.value_store_handle is not None
    feature_parquet = Path(feature_result.value_store_handle.parquet_path or "")
    assert feature_parquet.exists()
    assert load_parquet_values(feature_parquet) == [
        record.to_dict() for record in feature_result.records
    ]
    assert read_parquet_manifest(feature_parquet)["content_hash"] == (
        feature_result.value_store_handle.content_hash
    )

    feature_store = FeatureStore.from_alpha_data_root(tmp_path)
    feature_record = feature_store.register_materialized_feature(
        feature_result,
        feature_spec=feature_definition.spec,
        feature_version=feature_definition.version,
        feature_request=feature_request,
    )

    label_definition = build_fixed_horizon_label_definition(
        FixedHorizonLabelName.FWD_RET_1M,
        _fixed_label_spec(),
        dataset_version_ids=(dataset_id,),
    )
    label_preview_plan = build_label_materialization_plan(
        (label_definition,),
        accepted,
        partition_id="development_partition",
        instrument_ids=("ES",),
        alpha_data_root=tmp_path,
        dry_run=True,
    )
    label_plan = build_label_materialization_plan(
        (label_definition,),
        accepted,
        partition_id="development_partition",
        instrument_ids=("ES",),
        alpha_data_root=tmp_path,
    )
    label_inputs = LabelMaterializationInputs(
        accepted_version=accepted,
        bar_rows=_bar_rows(dataset_id, length=4),
    )

    label_preview = materialize_labels(
        label_preview_plan,
        label_inputs,
        (label_definition,),
        value_store_format=ValueStoreFormat.PARQUET,
    )
    label_result = materialize_labels(
        label_plan,
        label_inputs,
        (label_definition,),
        value_store_format=ValueStoreFormat.PARQUET,
    )

    assert label_preview.plan.label_version_ids == label_result.plan.label_version_ids
    assert label_preview.planned_label_count == label_result.planned_label_count
    assert label_result.value_store_handle is not None
    label_parquet = Path(label_result.value_store_handle.parquet_path or "")
    assert label_parquet.exists()
    assert load_parquet_values(label_parquet) == [
        record.to_dict() for record in label_result.records
    ]
    assert read_parquet_manifest(label_parquet)["content_hash"] == (
        label_result.value_store_handle.content_hash
    )

    label_registry = LabelRegistry.from_alpha_data_root(tmp_path)
    label_record = label_registry.register_materialized_label(
        label_result,
        label_contract=label_definition.contract,
        label_version=label_definition.version,
    )

    _assert_registry_value_metadata(feature_record.to_dict()["materialization"])
    _assert_registry_value_metadata(label_record.to_dict()["materialization"])
    assert feature_record.feature_version_id == feature_plan.feature_version_ids[0]
    assert label_record.label_version_id == label_plan.label_version_ids[0]
    assert feature_record.dataset_version_id == label_record.dataset_version_id == dataset_id
    assert feature_record.parquet_path == feature_parquet.as_posix()
    assert label_record.parquet_path == label_parquet.as_posix()
    assert feature_record.value_content_hash == feature_result.value_store_handle.content_hash
    assert label_record.value_content_hash == label_result.value_store_handle.content_hash

    assert REQUIRED_VALUE_FIELDS.issubset(
        _sqlite_columns(feature_store.registry.registry_path, "feature_registry_records")
    )
    assert REQUIRED_VALUE_FIELDS.issubset(
        _sqlite_columns(label_registry.registry_path, "label_registry_records")
    )

    feature_lock = {
        "feature_version_id": feature_record.feature_version_id,
        "dataset_version_id": feature_record.dataset_version_id,
        "partition_id": feature_record.partition_id,
    }
    lock_report = validate_feature_locks(
        (feature_lock,),
        registry_path=feature_store.registry.registry_path,
    )
    assert lock_report.ok is True
    assert lock_report.resolutions[0].feature_version_id == feature_record.feature_version_id

    resolved = _resolve_runtime(
        feature_record.feature_version_id,
        label_record.label_version_id,
        dataset_version=accepted.dataset_version,
        feature_store=feature_store,
        label_registry=label_registry,
        expected_feature_request_id=feature_record.feature_request_id,
        expected_label_spec_id=label_record.label_spec_id,
    )
    assert resolved.status is RuntimeEntryStatus.INPUTS_RESOLVED
    assert resolved.input_pack is not None
    assert resolved.input_pack.feature_packs[0].feature_version_id == (
        feature_record.feature_version_id
    )
    assert resolved.input_pack.label_packs[0].label_version_id == label_record.label_version_id
    assert resolved.input_pack.dataset_version_id == dataset_id

    stale_feature_id = "fver_" + "f" * 64
    with pytest.raises(FeatureLockValidationError, match="stale feature-pack lock"):
        validate_feature_locks(
            ({"feature_version_id": stale_feature_id},),
            registry_path=feature_store.registry.registry_path,
        )
    stale_feature = _resolve_runtime(
        stale_feature_id,
        label_record.label_version_id,
        dataset_version=accepted.dataset_version,
        feature_store=feature_store,
        label_registry=label_registry,
        expected_feature_request_id=feature_record.feature_request_id,
        expected_label_spec_id=label_record.label_spec_id,
    )
    assert stale_feature.status is RuntimeEntryStatus.INPUTS_BLOCKED
    assert "feature_pack_not_found" in _reason_codes(stale_feature)

    with pytest.raises(FeatureLockValidationError, match="malformed"):
        validate_feature_locks(
            ("returns",),
            registry_path=feature_store.registry.registry_path,
        )
    fuzzy_feature = _resolve_runtime(
        "returns",
        label_record.label_version_id,
        dataset_version=accepted.dataset_version,
        feature_store=feature_store,
        label_registry=label_registry,
        expected_feature_request_id=feature_record.feature_request_id,
        expected_label_spec_id=label_record.label_spec_id,
    )
    assert fuzzy_feature.status is RuntimeEntryStatus.INPUTS_BLOCKED
    assert "invalid_feature_pack_ref" in _reason_codes(fuzzy_feature)

    stale_label = _resolve_runtime(
        feature_record.feature_version_id,
        "lver_" + "e" * 64,
        dataset_version=accepted.dataset_version,
        feature_store=feature_store,
        label_registry=label_registry,
        expected_feature_request_id=feature_record.feature_request_id,
        expected_label_spec_id=label_record.label_spec_id,
    )
    assert stale_label.status is RuntimeEntryStatus.INPUTS_BLOCKED
    assert "label_pack_not_found" in _reason_codes(stale_label)

    fuzzy_label = _resolve_runtime(
        feature_record.feature_version_id,
        "fwd_ret_1m",
        dataset_version=accepted.dataset_version,
        feature_store=feature_store,
        label_registry=label_registry,
        expected_feature_request_id=feature_record.feature_request_id,
        expected_label_spec_id=label_record.label_spec_id,
    )
    assert fuzzy_label.status is RuntimeEntryStatus.INPUTS_BLOCKED
    assert "invalid_label_pack_ref" in _reason_codes(fuzzy_label)


class _EmptyRegistryReader:
    def read_factor_versions(self) -> list[dict[str, object]]:
        return []


def _assert_registry_value_metadata(materialization: object) -> None:
    assert isinstance(materialization, dict)
    for field in REQUIRED_VALUE_FIELDS | {"dataset_version_id"}:
        assert materialization.get(field)
    assert materialization["value_store_format"] == ValueStoreFormat.PARQUET.value
    assert str(materialization["parquet_path"]).endswith("values.parquet")
    assert str(materialization["value_content_hash"]).startswith("sha256:")


def _resolve_runtime(
    feature_version_id: str,
    label_version_id: str,
    *,
    dataset_version: DatasetVersion,
    feature_store: FeatureStore,
    label_registry: LabelRegistry,
    expected_feature_request_id: str,
    expected_label_spec_id: str,
) -> Any:
    entry_result = evaluate_runtime_entry_request(
        RuntimeEntryRequest(
            alpha_spec_ref=ALPHA_SPEC_REF,
            study_spec_ref=STUDY_SPEC_REF,
            study_input_pack=StudyInputPack(
                feature_request_ids=[expected_feature_request_id],
                label_spec_ids=[expected_label_spec_id],
                alpha_spec_id=ALPHA_SPEC_REF,
                dataset_scope=_dataset_scope(dataset_version.dataset_version_id),
            ),
            target_dataset_version_id=dataset_version.dataset_version_id,
            dataset_scope=_dataset_scope(dataset_version.dataset_version_id),
            partition_scope={"partition_id": "development_partition"},
            expected_dataset_lifecycle_state="READY_FOR_RESEARCH",
            dataset_version_source_family="synthetic",
        )
    )
    assert entry_result.status is RuntimeEntryStatus.INPUTS_RESOLVED

    return resolve_runtime_input_pack(
        entry_result,
        registry_path="/tmp/alpha_system_keystone_fixture/datasets.sqlite",
        dataset_lifecycle_state="READY_FOR_RESEARCH",
        feature_pack_refs=(feature_version_id,),
        label_pack_refs=(label_version_id,),
        partition_scope={"partition_id": "development_partition"},
        session_scope={"session": "synthetic_rth"},
        feature_label_resolver=FeatureLabelPackResolver(
            feature_store=feature_store,
            label_registry=label_registry,
        ),
        dataset_version_resolver=lambda _path, _id: dataset_version,
    )


def _approved_request(feature: OHLCVFeatureName) -> FeatureRequest:
    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    return create_feature_request(
        alpha_spec_id=ALPHA_SPEC_REF,
        requested_inputs=[f"keystone_{feature.value}"],
        formula_sketch={
            "exposure_family": f"keystone_{feature.value}",
            "inputs": ["canonical_ohlcv"],
            "operation": feature.value,
            "window": 1,
        },
        availability_assumptions={
            "timing": "tiny synthetic rows expose available_ts after event_ts"
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": ["close", "available_ts"],
            "source": "tiny synthetic P04 fixture rows only",
        },
        approval_status=FeatureRequestApprovalStatus.APPROVED,
    )


def _fixed_label_spec() -> LabelSpec:
    return create_label_spec(
        horizon="1m",
        path_rules={
            "path": "trade_price_forward_return",
            "horizon_minutes": 1,
            "terminal_rule": "exact event_ts row at fixed forward horizon",
        },
        cost_model={
            "model": "gross_unadjusted_forward_return",
            "adjustment_scope": "not_applied_in_p04_preflight",
        },
        target_stop_rules={
            "target_rule": "not_used_for_fixed_horizon_return",
            "stop_rule": "not_used_for_fixed_horizon_return",
        },
        availability_time="2024-01-02T14:00:00+00:00",
        forbidden_feature_overlap={
            "label_ids": [FixedHorizonLabelName.FWD_RET_1M.value],
            "aliases": ["forward_return_1m"],
            "transforms": ["label(fwd_ret_1m)"],
        },
        leakage_checks=["label_as_feature", "availability_time"],
        alpha_spec_id=ALPHA_SPEC_REF,
    )


def _accepted_version(dataset_id: str) -> consumption.AcceptedDatasetVersion:
    quality_report = _quality_report(dataset_id)
    return consumption.AcceptedDatasetVersion(
        registry_path="synthetic_registry.sqlite",
        dataset_version=_dataset_version(dataset_id, quality_report=quality_report),
        lifecycle_state="READY_FOR_RESEARCH",
        quality_report=quality_report,
        coverage_report=_coverage_report(dataset_id),
    )


def _dataset_version(dataset_id: str, *, quality_report: DataQualityReport) -> DatasetVersion:
    return DatasetVersion(
        dataset_version_id=dataset_id,
        source="dsrc_synthetic_fixture",
        symbol_universe=("ES",),
        bar_size="1 min",
        what_to_show="TRADES",
        start_ts=_dt("2024-01-02T14:30:00+00:00"),
        end_ts=_dt("2024-01-02T14:40:00+00:00"),
        contract_universe=("ESM4",),
        roll_policy_id="roll_policy_fixture",
        manifest_hash=HASH_0,
        code_hash=HASH_1,
        config_hash=HASH_2,
        quality_report_hash=compute_quality_report_hash(quality_report),
        created_at=_dt("2024-01-02T15:00:00+00:00"),
    )


def _quality_report(dataset_id: str) -> DataQualityReport:
    return DataQualityReport(
        quality_report_id=f"qr_{dataset_id}",
        dataset_version_id=dataset_id,
        gap_summary=_passing_summary(),
        duplicate_summary=_passing_summary(),
        non_monotonic_summary=_passing_summary(),
        ohlc_errors=_passing_summary(),
        zero_negative_price_errors=_passing_summary(),
        zero_volume_anomalies=_passing_summary(),
        dst_anomalies=_passing_summary(),
        session_coverage=_passing_summary(),
        roll_discontinuities=_passing_summary(),
        provider_error_summary=_passing_summary(),
        bbo_missing_metric=_passing_summary(),
        abnormal_spread_summary=_passing_summary(),
        status=ReportStatus.PASSING,
    )


def _coverage_report(dataset_id: str) -> CoverageReport:
    return CoverageReport(
        coverage_report_id=f"cr_{dataset_id}",
        dataset_version_id=dataset_id,
        symbol_coverage=_coverage_summary(),
        contract_coverage=_coverage_summary(),
        session_coverage=_coverage_summary(),
        partition_coverage=_coverage_summary(include_partition_counts=True),
        missing_intervals=(),
        incomplete_chunks=(),
    )


def _passing_summary() -> dict[str, object]:
    return {"count": 0, "status": ReportStatus.PASSING.value, "blocking": False}


def _coverage_summary(*, include_partition_counts: bool = False) -> dict[str, object]:
    summary: dict[str, object] = {
        "status": ReportStatus.PASSING.value,
        "blocking": False,
        "expected_count": 1,
        "observed_count": 1,
        "missing_count": 0,
    }
    if include_partition_counts:
        summary["missing_interval_count"] = 0
        summary["incomplete_chunk_count"] = 0
    return summary


def _bar_rows(dataset_id: str, *, length: int) -> tuple[dict[str, object], ...]:
    start = _dt("2024-01-02T14:30:00+00:00")
    return tuple(
        _bar_row(dataset_id, start + timedelta(minutes=index), close=Decimal("100") + index)
        for index in range(length)
    )


def _bar_row(dataset_id: str, start: datetime, *, close: Decimal) -> dict[str, object]:
    end = start + timedelta(minutes=1)
    return {
        "instrument_id": "ES",
        "contract_id": "ESM4",
        "series_id": "ES_c_0",
        "bar_start_ts": start.isoformat(),
        "bar_end_ts": end.isoformat(),
        "event_ts": end.isoformat(),
        "available_ts": (end + timedelta(seconds=1)).isoformat(),
        "ingested_at": (end + timedelta(seconds=2)).isoformat(),
        "open": str(close),
        "high": str(close + Decimal("1")),
        "low": str(close - Decimal("1")),
        "close": str(close),
        "volume": "10",
        "source": "dsrc_synthetic_fixture",
        "source_request_id": "req_fixture_1",
        "data_version": dataset_id,
        "quality_flags": (),
        "session_label": "RTH",
    }


def _dataset_scope(dataset_id: str) -> dict[str, object]:
    return {
        "dataset_version_id": dataset_id,
        "instrument_universe": "ES only synthetic keystone fixture",
        "source": "tiny synthetic rows; no provider data",
        "time_range": "2024-01-02T14:30:00+00:00 to 2024-01-02T14:40:00+00:00",
    }


def _sqlite_columns(path: Path, table_name: str) -> set[str]:
    with sqlite3.connect(path) as connection:
        rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {str(row[1]) for row in rows}


def _reason_codes(result: Any) -> set[str]:
    return {reason.code for reason in result.reasons}


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
