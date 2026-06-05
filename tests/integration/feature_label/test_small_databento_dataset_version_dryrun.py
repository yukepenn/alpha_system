from __future__ import annotations

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
from alpha_system.data.foundation.version_registry import persist_dataset_version
from alpha_system.features.engine import run_small_dataset_version_dry_run
from alpha_system.features.families.bbo import (
    BBOFeatureName,
    build_bbo_feature_definition,
)
from alpha_system.features.families.ohlcv import (
    OHLCVFeatureName,
    build_ohlcv_feature_definition,
)
from alpha_system.governance.duplicate_exposure import ExposureCheckResult, ExposureRegistryStatus
from alpha_system.governance.feature_request import (
    FeatureRequest,
    FeatureRequestApprovalStatus,
    create_feature_request,
)
from alpha_system.governance.label_spec import LabelSpec, create_label_spec
from alpha_system.labels.families.fixed_horizon import (
    FixedHorizonLabelName,
    build_fixed_horizon_label_definition,
)

ALPHA_SPEC_ID = "aspec_af848bc999a4c4b11a421bd0"
HASH_0 = "0" * 64
HASH_1 = "1" * 64
HASH_2 = "2" * 64
DATASET_ID = "dsv_databento_feature_label_dryrun_v1"


class EmptyRegistryReader:
    def read_factor_versions(self) -> list[dict[str, object]]:
        return []


def test_small_databento_dataset_version_dry_run_uses_registry_and_writes_local_values(
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "registry" / "datasets.sqlite"
    alpha_data_root = tmp_path / "alpha_data"
    quality_report = _quality_report(DATASET_ID)
    coverage_report = _coverage_report(DATASET_ID)
    dataset_version = _dataset_version(DATASET_ID, quality_report=quality_report)
    persist_dataset_version(
        registry_path,
        dataset_version,
        quality_report=quality_report,
        coverage_report=coverage_report,
        source_manifest={"manifest_hash": dataset_version.manifest_hash},
        code_hash=dataset_version.code_hash,
        config_hash=dataset_version.config_hash,
    )

    feature_definitions = (
        build_ohlcv_feature_definition(
            OHLCVFeatureName.RETURNS,
            _approved_feature_request("returns", ("canonical_ohlcv",), ("close",)),
            EmptyRegistryReader(),
            dataset_version_ids=(DATASET_ID,),
            reset_on_session=False,
        ),
        build_bbo_feature_definition(
            BBOFeatureName.MISSING_BBO_FLAG,
            _approved_feature_request(
                "missing_bbo_flag",
                ("canonical_bbo",),
                ("quality_flags",),
            ),
            EmptyRegistryReader(),
            dataset_version_ids=(DATASET_ID,),
        ),
    )
    label_definitions = (
        build_fixed_horizon_label_definition(
            FixedHorizonLabelName.MID_FWD_RET_1M,
            _fixed_label_spec(),
            dataset_version_ids=(DATASET_ID,),
        ),
    )

    summary = run_small_dataset_version_dry_run(
        registry_path=registry_path,
        dataset_version_id=DATASET_ID,
        lifecycle_state="VERSIONED",
        quality_report=quality_report,
        coverage_report=coverage_report,
        source_manifest={"manifest_hash": dataset_version.manifest_hash},
        code_hash=dataset_version.code_hash,
        config_hash=dataset_version.config_hash,
        partition_id="development_partition",
        alpha_data_root=alpha_data_root,
        feature_definitions=feature_definitions,
        label_definitions=label_definitions,
        bar_rows=_bar_rows(DATASET_ID, length=4),
        bbo_rows=_bbo_rows(DATASET_ID, length=4),
        dense_grid_bar_rows=(_dense_no_trade_row(DATASET_ID),),
        instrument_ids=("ES",),
    )

    payload = summary.to_dict()
    assert payload["status"] == "COMPLETED"
    assert payload["dataset_version_id"] == DATASET_ID
    assert payload["source"] == "dsrc_databento_historical"
    assert payload["partition_id"] == "development_partition"
    assert payload["canonical_bar_rows"] == 4
    assert payload["canonical_bbo_rows"] == 4
    assert payload["dense_grid_bar_rows"] == 1
    assert payload["synthetic_no_trade_rows"] == 1
    assert payload["missing_bbo_rows"] == 1
    assert payload["bbo_quarantined_rows"] == 0
    assert payload["feature_count"] == 2
    assert payload["feature_value_count"] > 0
    assert payload["label_count"] == 1
    assert payload["label_value_count"] > 0
    assert payload["quality_status"] == ReportStatus.WARNING.value
    assert payload["coverage_status"] == ReportStatus.PASSING.value
    assert payload["feature_output_under_alpha_data_root"] is True
    assert payload["label_output_under_alpha_data_root"] is True
    assert set(payload) == {
        "status",
        "dataset_version_id",
        "source",
        "lifecycle_state",
        "partition_id",
        "symbols",
        "sessions",
        "counts_by_symbol",
        "counts_by_session",
        "canonical_bar_rows",
        "canonical_bbo_rows",
        "dense_grid_bar_rows",
        "synthetic_no_trade_rows",
        "missing_bbo_rows",
        "bbo_quarantined_rows",
        "feature_count",
        "feature_value_count",
        "label_count",
        "label_value_count",
        "quality_status",
        "coverage_status",
        "quality_blocking",
        "coverage_blocking",
        "feature_output_under_alpha_data_root",
        "label_output_under_alpha_data_root",
        "warnings",
    }
    assert "value" not in payload
    assert list(alpha_data_root.rglob("values.jsonl"))


def _dataset_version(dataset_id: str, *, quality_report: DataQualityReport) -> DatasetVersion:
    return DatasetVersion(
        dataset_version_id=dataset_id,
        source="dsrc_databento_historical",
        symbol_universe=("ES",),
        bar_size="1 min",
        what_to_show="TRADES_AND_BBO",
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
        bbo_missing_metric=_metric_summary(count=1, status=ReportStatus.WARNING),
        abnormal_spread_summary=_passing_summary(),
        status=ReportStatus.WARNING,
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


def _metric_summary(*, count: int, status: ReportStatus) -> dict[str, object]:
    return {"count": count, "status": status.value, "blocking": False}


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


def _approved_feature_request(
    token: str,
    input_views: tuple[str, ...],
    fields: tuple[str, ...],
) -> FeatureRequest:
    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    return create_feature_request(
        alpha_spec_id=ALPHA_SPEC_ID,
        requested_inputs=[f"dry_run_{token}"],
        formula_sketch={
            "exposure_family": f"dry_run_{token}",
            "inputs": list(input_views),
            "operation": token,
            "window": 1,
        },
        availability_assumptions={
            "timing": "synthetic canonical rows expose available_ts after bar end"
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": list(fields),
            "source": "tiny synthetic canonical mappings only",
        },
        approval_status=FeatureRequestApprovalStatus.APPROVED,
    )


def _fixed_label_spec() -> LabelSpec:
    return create_label_spec(
        horizon="1m",
        path_rules={
            "path": "midprice_forward_return",
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
            "label_ids": [FixedHorizonLabelName.MID_FWD_RET_1M.value],
            "aliases": ["mid_forward_return_1m"],
            "transforms": ["label(mid_fwd_ret_1m)"],
        },
        leakage_checks=["label_as_feature", "availability_time"],
    )


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
        "source": "dsrc_databento_historical",
        "source_request_id": "req_fixture_1",
        "data_version": dataset_id,
        "quality_flags": (),
        "session_label": "RTH",
    }


def _bbo_rows(dataset_id: str, *, length: int) -> tuple[dict[str, object], ...]:
    start = _dt("2024-01-02T14:30:00+00:00")
    return tuple(
        _missing_bbo_row(dataset_id, start + timedelta(minutes=index))
        if index == 1
        else _bbo_row(dataset_id, start + timedelta(minutes=index), mid=Decimal("100") + index)
        for index in range(length)
    )


def _bbo_row(dataset_id: str, start: datetime, *, mid: Decimal) -> dict[str, object]:
    end = start + timedelta(minutes=1)
    bid = mid - Decimal("0.25")
    ask = mid + Decimal("0.25")
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
        "ask_size": "12",
        "mid": str(mid),
        "spread": str(ask - bid),
        "source": "dsrc_databento_historical",
        "source_request_id": "req_fixture_1",
        "data_version": dataset_id,
        "quality_flags": (),
        "session_label": "RTH",
        "spread_ticks": "2",
        "microprice": str(mid),
        "bid_order_count": 1,
        "ask_order_count": 1,
    }


def _missing_bbo_row(dataset_id: str, start: datetime) -> dict[str, object]:
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
        "bid": "0",
        "ask": "0",
        "bid_size": "0",
        "ask_size": "0",
        "mid": "0",
        "spread": "0",
        "source": "dsrc_databento_historical",
        "source_request_id": "req_fixture_1",
        "data_version": dataset_id,
        "quality_flags": ("missing_bbo",),
        "session_label": "RTH",
        "spread_ticks": "0",
        "microprice": "0",
        "bid_order_count": 0,
        "ask_order_count": 0,
    }


def _dense_no_trade_row(dataset_id: str) -> dict[str, object]:
    start = _dt("2024-01-02T14:34:00+00:00")
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
        "open": "103",
        "high": "103",
        "low": "103",
        "close": "103",
        "volume": "0",
        "source": "dsrc_databento_historical",
        "source_request_id": "req_fixture_1",
        "data_version": dataset_id,
        "quality_flags": ("no_trade",),
        "session_label": "RTH",
        "has_trade": False,
        "synthetic": True,
        "fill_method": "previous_close",
        "provider_bar_ref": None,
    }


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
