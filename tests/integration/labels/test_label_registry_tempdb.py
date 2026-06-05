from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from alpha_system.data.foundation.datasets import (
    CoverageReport,
    DataQualityReport,
    DatasetVersion,
    ReportStatus,
    compute_quality_report_hash,
)
from alpha_system.features import consumption
from alpha_system.governance.label_spec import LabelSpec, create_label_spec
from alpha_system.labels.engine import (
    LabelMaterializationInputs,
    build_label_materialization_plan,
    materialize_labels,
)
from alpha_system.labels.families.fixed_horizon import (
    FixedHorizonLabelName,
    build_fixed_horizon_label_definition,
)
from alpha_system.labels.registry import (
    DEFAULT_LABEL_REGISTRY_RELATIVE_PATH,
    LabelRegistry,
    LabelRegistryLifecycleState,
)

HASH_0 = "0" * 64
HASH_1 = "1" * 64
HASH_2 = "2" * 64


def test_label_registry_tempdb_persist_resolve_deprecate_round_trip(
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "labels.sqlite"
    registry = LabelRegistry(registry_path)
    result, definition = _materialization_result(tmp_path, "dsv_synthetic_label_registry_tempdb")

    persisted = registry.register_materialized_label(
        result,
        label_contract=definition.contract,
        label_version=definition.version,
        registry_metadata={"fixture": "synthetic tempdb"},
    )
    resolved = LabelRegistry(registry_path).resolve_label(definition.label_version_id)

    assert registry_path.exists()
    assert registry_path.is_relative_to(tmp_path)
    assert persisted.label_version == definition.version
    assert resolved is not None
    assert resolved.label_version == definition.version
    assert resolved.lineage.label_spec_id == definition.contract.label_spec_id
    assert resolved.first_label_available_ts == _dt("2024-01-02T14:32:01+00:00")
    assert resolved.registry_metadata.to_dict() == {"fixture": "synthetic tempdb"}

    deprecation = registry.deprecate_label(
        definition.label_version_id,
        reason="synthetic tempdb retirement",
        deprecated_by="FLF-P22 integration test",
        deprecated_at=_dt("2024-01-04T00:00:00+00:00"),
    )
    deprecated = LabelRegistry(registry_path).resolve_label(definition.label_version_id)

    assert deprecation.label_version_id == definition.label_version_id
    assert deprecated is not None
    assert deprecated.lifecycle_state is LabelRegistryLifecycleState.DEPRECATED
    assert deprecated.lineage.label_version == persisted.lineage.label_version

    with sqlite3.connect(registry_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            )
        }
        registry_rows = connection.execute(
            "SELECT count(*) FROM label_registry_records"
        ).fetchone()[0]
        lineage_rows = connection.execute(
            "SELECT count(*) FROM label_lineage_records"
        ).fetchone()[0]
        deprecation_rows = connection.execute(
            "SELECT count(*) FROM label_deprecation_records"
        ).fetchone()[0]

    assert "label_values" not in tables
    assert registry_rows == 1
    assert lineage_rows == 1
    assert deprecation_rows == 1


def test_default_label_registry_path_uses_alpha_data_root(tmp_path: Path) -> None:
    alpha_data_root = tmp_path / "alpha_data"
    registry = LabelRegistry.from_alpha_data_root(alpha_data_root)

    assert registry.registry_path == alpha_data_root / DEFAULT_LABEL_REGISTRY_RELATIVE_PATH
    assert registry.registry_path.exists()


def _materialization_result(tmp_path: Path, dataset_id: str):
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
