from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

import alpha_system.labels.engine as label_engine
from alpha_system.data.foundation.datasets import (
    CoverageReport,
    DataQualityReport,
    DatasetPartitionPlan,
    DatasetVersion,
    ReportStatus,
    compute_quality_report_hash,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.governance.label_spec import LabelSpec, create_label_spec
from alpha_system.labels.engine import (
    LabelMaterializationError,
    LabelMaterializationInputs,
    build_label_materialization_plan,
    materialize_labels,
)
from alpha_system.labels.families.cost_adjusted import (
    CostAdjustedLabelName,
    build_cost_adjusted_label_definition,
)
from alpha_system.labels.families.event import (
    EventLabelName,
    build_event_label_definition,
)
from alpha_system.labels.families.fixed_horizon import (
    FixedHorizonLabelName,
    build_fixed_horizon_label_definition,
)
from alpha_system.labels.families.path import (
    PathLabelName,
    build_path_label_definition,
)
from alpha_system.labels.version import LabelValueRecord

HASH_0 = "0" * 64
HASH_1 = "1" * 64
HASH_2 = "2" * 64


def test_materializes_supported_label_families_idempotently(tmp_path: Path) -> None:
    dataset_id = "dsv_synthetic_label_engine"
    accepted = _accepted_version(dataset_id)
    definitions = _label_definitions(dataset_id)
    plan = build_label_materialization_plan(
        definitions,
        accepted,
        partition_id="development_partition",
        instrument_ids=("ES",),
        alpha_data_root=tmp_path,
    )
    inputs = LabelMaterializationInputs(
        accepted_version=accepted,
        bar_rows=_bar_rows(dataset_id, length=6),
        bbo_rows=_bbo_rows(dataset_id, length=6),
    )

    first = materialize_labels(plan, inputs, definitions)
    first_payload = plan.output_path.read_text(encoding="utf-8")
    second = materialize_labels(plan, inputs, definitions)

    assert first.dry_run is False
    assert first.wrote_output is True
    assert second.wrote_output is False
    assert first.records == second.records
    assert first.record_count > 0
    assert plan.output_path.is_relative_to(tmp_path)
    assert plan.output_path.read_text(encoding="utf-8") == first_payload
    assert {record.label_version_id for record in first.records} == set(plan.label_version_ids)
    assert all(record.label_available_ts >= record.horizon_end_ts for record in first.records)
    assert all(record.label_spec_id in plan.label_spec_ids for record in first.records)


def test_dry_run_plans_without_writing(tmp_path: Path) -> None:
    dataset_id = "dsv_synthetic_label_engine_dry_run"
    accepted = _accepted_version(dataset_id)
    definitions = (_fixed_definition(dataset_id),)
    plan = build_label_materialization_plan(
        definitions,
        accepted,
        partition_id="development_partition",
        alpha_data_root=tmp_path,
        dry_run=True,
    )
    inputs = LabelMaterializationInputs(
        accepted_version=accepted,
        bar_rows=_bar_rows(dataset_id, length=3),
    )

    result = materialize_labels(plan, inputs, definitions)

    assert result.dry_run is True
    assert result.records == ()
    assert result.wrote_output is False
    assert result.output_path is None
    assert result.planned_input_rows == 3
    assert result.planned_label_count == 1
    assert not plan.output_path.exists()


def test_missing_or_invalid_label_spec_fails_before_values(tmp_path: Path) -> None:
    accepted = _accepted_version("dsv_synthetic_label_engine_invalid_spec")

    with pytest.raises(LabelMaterializationError, match="approved governed"):
        build_label_materialization_plan(
            (object(),),  # type: ignore[arg-type]
            accepted,
            partition_id="development_partition",
            alpha_data_root=tmp_path,
        )

    with pytest.raises(ValueError, match="lspec_ binding"):
        build_fixed_horizon_label_definition(FixedHorizonLabelName.FWD_RET_1M, None)


def test_missing_label_available_ts_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset_id = "dsv_synthetic_label_engine_missing_availability"
    accepted = _accepted_version(dataset_id)
    definition = _fixed_definition(dataset_id)
    plan = build_label_materialization_plan(
        (definition,),
        accepted,
        partition_id="development_partition",
        alpha_data_root=tmp_path,
    )
    inputs = LabelMaterializationInputs(
        accepted_version=accepted,
        bar_rows=_bar_rows(dataset_id, length=3),
    )

    def corrupt_compute(*_args: object, **_kwargs: object) -> tuple[LabelValueRecord, ...]:
        event_ts = _dt("2024-01-02T14:31:00+00:00")
        record = LabelValueRecord(
            label_version_id=definition.label_version_id,
            entity_id="ES_c_0",
            event_ts=event_ts,
            horizon_end_ts=event_ts + timedelta(minutes=1),
            label_available_ts=event_ts + timedelta(minutes=1, seconds=1),
            value=0.01,
            label_contract=definition.contract,
        )
        object.__setattr__(record, "label_available_ts", None)
        return (record,)

    monkeypatch.setattr(label_engine, "compute_fixed_horizon_label", corrupt_compute)

    with pytest.raises(LabelMaterializationError, match="label_available_ts"):
        materialize_labels(plan, inputs, (definition,))


def test_locked_test_without_contamination_metadata_fails_closed(tmp_path: Path) -> None:
    dataset_id = "dsv_synthetic_label_engine_locked"
    accepted = _accepted_version(dataset_id)
    definition = _fixed_definition(dataset_id)

    with pytest.raises(DataFoundationValidationError, match="contamination metadata"):
        build_label_materialization_plan(
            (definition,),
            accepted,
            partition_id="locked_test_candidate",
            alpha_data_root=tmp_path,
            partition_plan=DatasetPartitionPlan.canonical(),
        )


def test_inadmissible_dataset_version_lifecycle_fails_closed(tmp_path: Path) -> None:
    dataset_id = "dsv_synthetic_label_engine_draft"
    accepted = _accepted_version(dataset_id, lifecycle_state="DRAFT")
    definition = _fixed_definition(dataset_id)

    with pytest.raises(LabelMaterializationError, match="DatasetVersion lifecycle_state"):
        build_label_materialization_plan(
            (definition,),
            accepted,
            partition_id="development_partition",
            alpha_data_root=tmp_path,
        )


def test_label_as_feature_attempt_fails_closed(tmp_path: Path) -> None:
    dataset_id = "dsv_synthetic_label_engine_label_as_feature"
    accepted = _accepted_version(dataset_id)
    definition = _fixed_definition(dataset_id)

    with pytest.raises(LabelMaterializationError, match="live feature"):
        build_label_materialization_plan(
            (definition,),
            accepted,
            partition_id="development_partition",
            alpha_data_root=tmp_path,
            feature_references=(
                {
                    "feature_id": definition.label_id,
                    "available_at": "2024-01-02T14:31:00+00:00",
                },
            ),
        )


def test_alpha_data_root_must_not_be_inside_repo() -> None:
    dataset_id = "dsv_synthetic_label_engine_repo_root"
    accepted = _accepted_version(dataset_id)
    definition = _fixed_definition(dataset_id)

    with pytest.raises(LabelMaterializationError, match="outside the repository"):
        build_label_materialization_plan(
            (definition,),
            accepted,
            partition_id="development_partition",
            alpha_data_root=Path.cwd(),
        )


def _label_definitions(dataset_id: str):
    return (
        _fixed_definition(dataset_id),
        build_cost_adjusted_label_definition(
            CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET,
            _cost_adjusted_spec(),
            dataset_version_ids=(dataset_id,),
        ),
        build_path_label_definition(
            PathLabelName.MFE,
            _path_spec(),
            dataset_version_ids=(dataset_id,),
        ),
        build_event_label_definition(
            EventLabelName.LIQUIDITY_QUALITY_FUTURE,
            _liquidity_event_spec(),
            dataset_version_ids=(dataset_id,),
        ),
    )


def _fixed_definition(dataset_id: str):
    return build_fixed_horizon_label_definition(
        FixedHorizonLabelName.FWD_RET_1M,
        _fixed_spec(),
        dataset_version_ids=(dataset_id,),
    )


def _fixed_spec() -> LabelSpec:
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


def _cost_adjusted_spec() -> LabelSpec:
    return create_label_spec(
        horizon="2m",
        path_rules={
            "path": "bbo_mid_forward_return",
            "terminal_rule": "exact event_ts match with valid BBO only",
            "horizon_steps": 2,
        },
        cost_model={
            "model": "spread_adjusted",
            "spread_adjustment": "half_spread_round_trip",
        },
        target_stop_rules={
            "target_rule": "disabled_for_cost_adjusted_fixture",
            "stop_rule": "disabled_for_cost_adjusted_fixture",
        },
        availability_time="2024-01-02T14:00:00+00:00",
        forbidden_feature_overlap={
            "label_ids": [CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET.value],
            "aliases": ["spread_adjusted_forward_return"],
            "transforms": ["label(spread_adjusted_fwd_ret)"],
        },
        leakage_checks=["label_as_feature", "availability_time"],
    )


def _path_spec() -> LabelSpec:
    return create_label_spec(
        horizon="2_trade_bars",
        path_rules={
            "path": "ohlcv_trade_truth_forward_path",
            "horizon_steps": 2,
            "price_field": "close",
            "direction": "long",
            "trade_truth_predicate": "alpha_system.features.semantics.is_real_trade_bar",
        },
        cost_model={"model": "gross_path_labels_unadjusted", "reason": "no cost adjustment"},
        target_stop_rules={
            "target_return": 0.02,
            "stop_return": -0.02,
            "same_bar_policy": "ambiguous",
            "direction": "long",
        },
        availability_time="2024-01-02T14:00:00+00:00",
        forbidden_feature_overlap={
            "label_ids": ["path_mfe"],
            "aliases": ["mfe"],
            "transforms": ["label(path_mfe)"],
        },
        leakage_checks=["label_as_feature", "availability_time"],
    )


def _liquidity_event_spec() -> LabelSpec:
    return create_label_spec(
        horizon="2m",
        path_rules={
            "path": "strategy_agnostic_event_outcome",
            "event_label": EventLabelName.LIQUIDITY_QUALITY_FUTURE.value,
            "horizon_steps": 2,
            "horizon_minutes": 2,
            "direction": "up",
        },
        cost_model={"model": "event_label_no_cost_adjustment", "reason": "classification label"},
        target_stop_rules={
            "max_mean_spread_bps": 200,
            "target_rule": "future mean spread threshold",
            "stop_rule": "not_used_for_liquidity_quality",
        },
        availability_time="2024-01-02T14:00:00+00:00",
        forbidden_feature_overlap={
            "label_ids": [EventLabelName.LIQUIDITY_QUALITY_FUTURE.value],
            "aliases": ["future_liquidity_quality"],
            "transforms": ["label(liquidity_quality_future)"],
        },
        leakage_checks=["label_as_feature", "availability_time"],
    )


def _accepted_version(
    dataset_id: str,
    *,
    lifecycle_state: str = "VERSIONED",
) -> label_engine.AcceptedDatasetVersion:
    quality_report = _quality_report(dataset_id)
    return label_engine.AcceptedDatasetVersion(
        registry_path="synthetic_registry.sqlite",
        dataset_version=_dataset_version(dataset_id, quality_report=quality_report),
        lifecycle_state=lifecycle_state,
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


def _bbo_rows(dataset_id: str, *, length: int) -> tuple[dict[str, object], ...]:
    start = _dt("2024-01-02T14:30:00+00:00")
    return tuple(
        _bbo_row(dataset_id, start + timedelta(minutes=index), mid=Decimal("100") + index)
        for index in range(length)
    )


def _bbo_row(dataset_id: str, start: datetime, *, mid: Decimal) -> dict[str, object]:
    end = start + timedelta(minutes=1)
    bid = mid - Decimal("0.5")
    ask = mid + Decimal("0.5")
    return {
        "instrument_id": "ES",
        "contract_id": "ESM4",
        "series_id": "ES_c_0",
        "bar_start_ts": start.isoformat(),
        "bar_end_ts": end.isoformat(),
        "event_ts": end.isoformat(),
        "available_ts": (end + timedelta(seconds=1)).isoformat(),
        "ingested_at": (end + timedelta(seconds=2)).isoformat(),
        "bid": str(bid),
        "ask": str(ask),
        "bid_size": "10",
        "ask_size": "10",
        "mid": str(mid),
        "spread": str(ask - bid),
        "source": "dsrc_synthetic_fixture",
        "source_request_id": "req_fixture_1",
        "data_version": dataset_id,
        "quality_flags": (),
        "session_label": "RTH",
    }


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
