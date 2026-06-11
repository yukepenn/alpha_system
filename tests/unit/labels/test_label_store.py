from __future__ import annotations

import sqlite3
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from alpha_system.core.value_store import ValueStoreFormat, ValueStoreHandle
from alpha_system.data.foundation.datasets import (
    CoverageReport,
    DataQualityReport,
    DatasetVersion,
    ReportStatus,
    compute_quality_report_hash,
)
from alpha_system.features import consumption
from alpha_system.governance.label_spec import LabelSpec, create_label_spec
from alpha_system.governance.serialization import canonical_serialize
from alpha_system.labels.engine import (
    LabelMaterializationInputs,
    LabelMaterializationResult,
    build_label_materialization_plan,
    materialize_labels,
)
from alpha_system.labels.families.fixed_horizon import (
    FixedHorizonLabelName,
    build_fixed_horizon_label_definition,
)
from alpha_system.labels.registry import (
    PROHIBITED_LABEL_REGISTRY_STATES,
    LabelRegistry,
    LabelRegistryError,
    LabelRegistryLifecycleState,
)
from alpha_system.labels.version import LabelLineageRecord

HASH_0 = "0" * 64
HASH_1 = "1" * 64
HASH_2 = "2" * 64


def test_registration_fails_closed_without_engine_result_or_available_ts(
    tmp_path: Path,
) -> None:
    registry = LabelRegistry(tmp_path / "labels.sqlite")
    result, definition = _materialization_result(tmp_path, "dsv_synthetic_label_store_fail")

    with pytest.raises(LabelRegistryError, match="LabelMaterializationResult"):
        registry.register_materialized_label(
            object(),  # type: ignore[arg-type]
            label_contract=definition.contract,
            label_version=definition.version,
        )

    with pytest.raises(LabelRegistryError, match="dry-run"):
        registry.register_materialized_label(
            replace(result, dry_run=True, records=()),
            label_contract=definition.contract,
            label_version=definition.version,
        )

    corrupt_record = result.records[0]
    object.__setattr__(corrupt_record, "label_available_ts", None)
    corrupt_result = replace(result, records=(corrupt_record,))
    with pytest.raises(LabelRegistryError, match="label_available_ts"):
        registry.register_materialized_label(
            corrupt_result,
            label_contract=definition.contract,
            label_version=definition.version,
        )

    assert registry.count_label_records() == 0


def test_successful_registration_resolves_by_version_and_lineage(
    tmp_path: Path,
) -> None:
    registry = LabelRegistry(tmp_path / "labels.sqlite")
    result, definition = _materialization_result(tmp_path, "dsv_synthetic_label_store_ok")
    lineage = LabelLineageRecord(
        label_version=definition.version,
        label_contract=definition.contract,
        label_spec_id=definition.contract.label_spec_id,
        contract_provenance={"phase": "FLF-P22", "fixture": "unit"},
    )

    record = registry.register_materialized_label(
        result,
        label_contract=definition.contract,
        label_version=definition.version,
        lineage=lineage,
    )

    assert record.label_version == definition.version
    assert record.lineage == lineage
    assert record.value_record_count == 3
    assert record.first_label_available_ts == _dt("2024-01-02T14:32:01+00:00")
    assert record.last_label_available_ts == _dt("2024-01-02T14:34:01+00:00")
    assert record.exposure_status == "NO_FINDINGS"
    assert hash(record)

    resolved = registry.resolve_label(definition.label_version_id)
    assert resolved is not None
    assert resolved.label_version == definition.version
    assert resolved.lineage.label_spec_id == definition.contract.label_spec_id
    assert registry.resolve_lineage(definition.label_version_id) == lineage

    duplicate = registry.register_materialized_label(
        result,
        label_contract=definition.contract,
        label_version=definition.version,
        lineage=lineage,
    )
    assert duplicate.label_version_id == record.label_version_id
    assert registry.count_label_records() == 1


def test_registry_backfills_old_rows_and_persists_parquet_metadata(tmp_path: Path) -> None:
    source_registry = LabelRegistry(tmp_path / "source.sqlite")
    old_result, old_definition = _materialization_result(
        tmp_path,
        "dsv_synthetic_label_store_old_row",
    )
    old_record = source_registry.register_materialized_label(
        old_result,
        label_contract=old_definition.contract,
        label_version=old_definition.version,
    )
    old_payload = old_record.to_dict()
    for key in (
        "value_store_format",
        "parquet_path",
        "value_content_hash",
        "value_schema_version",
    ):
        old_payload["materialization"].pop(key, None)

    registry_path = tmp_path / "old_labels.sqlite"
    with sqlite3.connect(registry_path) as connection:
        connection.execute(
            """
            CREATE TABLE label_registry_records (
                label_version_id TEXT PRIMARY KEY,
                label_id TEXT NOT NULL,
                label_spec_id TEXT NOT NULL,
                lifecycle_state TEXT NOT NULL,
                materialization_plan_id TEXT NOT NULL,
                dataset_version_id TEXT NOT NULL,
                partition_id TEXT NOT NULL,
                materialization_output_path TEXT NOT NULL,
                value_record_count INTEGER NOT NULL,
                first_event_ts TEXT NOT NULL,
                last_event_ts TEXT NOT NULL,
                first_label_available_ts TEXT NOT NULL,
                last_label_available_ts TEXT NOT NULL,
                exposure_status TEXT NOT NULL,
                registered_at TEXT NOT NULL,
                metadata_json TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO label_registry_records (
                label_version_id,
                label_id,
                label_spec_id,
                lifecycle_state,
                materialization_plan_id,
                dataset_version_id,
                partition_id,
                materialization_output_path,
                value_record_count,
                first_event_ts,
                last_event_ts,
                first_label_available_ts,
                last_label_available_ts,
                exposure_status,
                registered_at,
                metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                old_record.label_version_id,
                old_record.label_id,
                old_record.label_spec_id,
                old_record.lifecycle_state.value,
                old_record.materialization_plan_id,
                old_record.dataset_version_id,
                old_record.partition_id,
                old_record.materialization_output_path,
                old_record.value_record_count,
                old_record.first_event_ts.isoformat(),
                old_record.last_event_ts.isoformat(),
                old_record.first_label_available_ts.isoformat(),
                old_record.last_label_available_ts.isoformat(),
                old_record.exposure_status,
                old_record.registered_at.isoformat(),
                canonical_serialize(old_payload),
            ),
        )

    registry = LabelRegistry(registry_path)
    loaded_old = registry.resolve_label(old_record.label_version_id)
    assert loaded_old is not None
    assert loaded_old.value_store_format == "jsonl"
    assert loaded_old.parquet_path is None

    new_result, new_definition = _materialization_result(
        tmp_path,
        "dsv_synthetic_label_store_parquet_row",
    )
    parquet_path = tmp_path / "labels" / "values.parquet"
    handle = ValueStoreHandle(
        format=ValueStoreFormat.PARQUET,
        jsonl_path=None,
        parquet_path=parquet_path.as_posix(),
        value_count=new_result.record_count,
        content_hash="sha256:" + "2" * 64,
        schema_version="schema.v1",
        dataset_version_id=new_result.plan.dataset_version_id,
        set_id="lset_fixture",
        partition_id=new_result.plan.partition_id,
        min_event_ts="2024-01-02T14:31:00+00:00",
        max_event_ts="2024-01-02T14:33:00+00:00",
        min_available_ts="2024-01-02T14:32:01+00:00",
        max_available_ts="2024-01-02T14:34:01+00:00",
    )
    new_record = registry.register_materialized_label(
        replace(new_result, output_path=parquet_path, value_store_handle=handle),
        label_contract=new_definition.contract,
        label_version=new_definition.version,
    )

    loaded_new = registry.resolve_label(new_record.label_version_id)
    assert loaded_new is not None
    assert loaded_new.value_store_format == "parquet"
    assert loaded_new.parquet_path == parquet_path.as_posix()
    assert loaded_new.value_content_hash == handle.content_hash
    assert loaded_new.value_schema_version == "schema.v1"


def test_duplicate_exposure_is_recorded_and_deprecation_preserves_lineage(
    tmp_path: Path,
) -> None:
    registry = LabelRegistry(tmp_path / "labels.sqlite")
    first_result, first_definition = _materialization_result(
        tmp_path,
        "dsv_synthetic_label_store_duplicate_a",
    )
    second_result, second_definition = _materialization_result(
        tmp_path,
        "dsv_synthetic_label_store_duplicate_b",
    )
    first = registry.register_materialized_label(
        first_result,
        label_contract=first_definition.contract,
        label_version=first_definition.version,
    )

    second = registry.register_materialized_label(
        second_result,
        label_contract=second_definition.contract,
        label_version=second_definition.version,
    )

    assert second.exposure_status == "DUPLICATE_RECORDED"
    assert second.exposure_report.duplicate_label_version_ids == (first.label_version_id,)
    assert registry.count_label_records() == 2

    deprecation = registry.deprecate_label(
        second.label_version_id,
        reason="synthetic fixture retirement",
        deprecated_by="FLF-P22 unit test",
        deprecated_at=_dt("2024-01-03T00:00:00+00:00"),
    )
    deprecated = registry.resolve_label(second.label_version_id)

    assert deprecation.label_version_id == second.label_version_id
    assert deprecated is not None
    assert deprecated.lifecycle_state is LabelRegistryLifecycleState.DEPRECATED
    assert deprecated.lineage == second.lineage
    assert registry.resolve_deprecation(second.label_version_id) == deprecation
    assert registry.is_deprecated(second.label_version_id) is True

    assert PROHIBITED_LABEL_REGISTRY_STATES.isdisjoint(
        {state.value for state in LabelRegistryLifecycleState}
    )
    with pytest.raises(LabelRegistryError, match="prohibited"):
        replace(first, lifecycle_state="TRADABLE")


def test_label_exposure_view_ignores_deprecated_rows_but_raw_reads_keep_them(
    tmp_path: Path,
) -> None:
    registry = LabelRegistry(tmp_path / "labels.sqlite")
    first_result, first_definition = _materialization_result(
        tmp_path,
        "dsv_synthetic_label_store_deprecated_guard_a",
    )
    second_result, second_definition = _materialization_result(
        tmp_path,
        "dsv_synthetic_label_store_deprecated_guard_b",
    )
    third_result, third_definition = _materialization_result(
        tmp_path,
        "dsv_synthetic_label_store_registered_guard_c",
    )
    first = registry.register_materialized_label(
        first_result,
        label_contract=first_definition.contract,
        label_version=first_definition.version,
    )
    registry.deprecate_label(
        first.label_version_id,
        reason="P200000 synthetic supersession",
        deprecated_by="P200000 unit test",
        deprecated_at=_dt("2024-01-03T00:00:00+00:00"),
    )

    raw_records = registry.read_label_records()
    assert len(raw_records) == 1
    assert raw_records[0].label_version_id == first.label_version_id
    assert raw_records[0].lifecycle_state is LabelRegistryLifecycleState.DEPRECATED
    assert registry.read_label_versions() == []

    second = registry.register_materialized_label(
        second_result,
        label_contract=second_definition.contract,
        label_version=second_definition.version,
    )

    assert second.exposure_status == "NO_FINDINGS"
    assert second.exposure_report.registry_entries_checked == 0
    assert registry.count_label_records() == 2

    third = registry.register_materialized_label(
        third_result,
        label_contract=third_definition.contract,
        label_version=third_definition.version,
    )

    assert third.exposure_status == "DUPLICATE_RECORDED"
    assert third.exposure_report.registry_entries_checked == 1
    assert third.exposure_report.duplicate_label_version_ids == (
        second.label_version_id,
    )
    assert (
        first.label_version_id
        not in third.exposure_report.duplicate_label_version_ids
    )
    assert {record.label_version_id for record in registry.read_label_records()} == {
        first.label_version_id,
        second.label_version_id,
        third.label_version_id,
    }


def _materialization_result(
    tmp_path: Path,
    dataset_id: str,
) -> tuple[LabelMaterializationResult, object]:
    accepted = _accepted_version(dataset_id)
    definition = build_fixed_horizon_label_definition(
        FixedHorizonLabelName.FWD_RET_1M,
        _label_spec(),
        dataset_version_ids=(dataset_id,),
    )
    plan = build_label_materialization_plan(
        (definition,),
        accepted,
        partition_id="development_partition",
        alpha_data_root=tmp_path,
    )
    inputs = LabelMaterializationInputs(
        accepted_version=accepted,
        bar_rows=_bar_rows(dataset_id),
    )
    return materialize_labels(plan, inputs, (definition,)), definition


def _label_spec() -> LabelSpec:
    return create_label_spec(
        horizon="1m",
        path_rules={
            "path": "trade_price_forward_return",
            "horizon_minutes": 1,
            "terminal_rule": "exact event_ts row at fixed forward horizon",
        },
        cost_model={
            "model": "gross_unadjusted_forward_return",
            "adjustment_scope": "not_applied_in_fixed_horizon_family",
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
    )


def _accepted_version(dataset_id: str) -> consumption.AcceptedDatasetVersion:
    quality_report = _quality_report(dataset_id)
    return consumption.AcceptedDatasetVersion(
        registry_path="synthetic_registry.sqlite",
        dataset_version=_dataset_version(dataset_id, quality_report=quality_report),
        lifecycle_state="VERSIONED",
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
        end_ts=_dt("2024-01-02T14:35:00+00:00"),
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
    return {"status": ReportStatus.PASSING.value, "count": 0, "blocking": False, "notes": []}


def _coverage_summary(*, include_partition_counts: bool = False) -> dict[str, object]:
    payload: dict[str, object] = {
        "status": ReportStatus.PASSING.value,
        "blocking": False,
        "expected_count": 4,
        "observed_count": 4,
        "missing_count": 0,
        "coverage_ratio": 1.0,
    }
    if include_partition_counts:
        payload["partition_counts"] = {"development_partition": 4}
        payload["missing_interval_count"] = 0
        payload["incomplete_chunk_count"] = 0
    return payload


def _bar_rows(dataset_id: str) -> tuple[dict[str, object], ...]:
    start = _dt("2024-01-02T14:30:00+00:00")
    return tuple(
        _bar_row(dataset_id, start + timedelta(minutes=index), close=Decimal("100") + index)
        for index in range(4)
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


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
