from __future__ import annotations

import json
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

HASH_0 = "0" * 64
HASH_1 = "1" * 64
HASH_2 = "2" * 64


def test_materialize_labels_writes_idempotent_local_jsonl(tmp_path: Path) -> None:
    dataset_id = "dsv_synthetic_label_materialize_integration"
    accepted = _accepted_version(dataset_id)
    definition = build_fixed_horizon_label_definition(
        FixedHorizonLabelName.FWD_RET_1M,
        _label_spec(),
        dataset_version_ids=(dataset_id,),
    )
    dry_run_plan = build_label_materialization_plan(
        (definition,),
        accepted,
        partition_id="development_partition",
        alpha_data_root=tmp_path,
        dry_run=True,
    )
    dry_run_inputs = LabelMaterializationInputs(
        accepted_version=accepted,
        bar_rows=_bar_rows(dataset_id),
    )

    dry_run = materialize_labels(dry_run_plan, dry_run_inputs, (definition,))

    assert dry_run.dry_run is True
    assert dry_run.records == ()
    assert not dry_run_plan.output_path.exists()

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

    first = materialize_labels(plan, inputs, (definition,))
    first_payload = plan.output_path.read_text(encoding="utf-8")
    second = materialize_labels(plan, inputs, (definition,))

    assert first.wrote_output is True
    assert second.wrote_output is False
    assert first.records == second.records
    assert first.record_count == 3
    assert plan.output_path.is_relative_to(tmp_path)
    assert plan.output_path.read_text(encoding="utf-8") == first_payload

    lines = [json.loads(line) for line in first_payload.splitlines()]
    assert lines[0]["record_type"] == "label_materialization_plan"
    assert lines[0]["plan"]["dataset_version_id"] == dataset_id
    value_lines = lines[1:]
    assert len(value_lines) == first.record_count
    assert all(line["record_type"] == "label_value" for line in value_lines)
    assert all(line["value"]["label_available_ts"] for line in value_lines)
    assert all(
        line["value"]["label_version_id"] == definition.label_version_id for line in value_lines
    )


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
        end_ts=_dt("2024-01-02T14:34:00+00:00"),
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
