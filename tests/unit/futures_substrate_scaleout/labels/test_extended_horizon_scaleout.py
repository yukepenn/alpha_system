from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from alpha_system.cli.seed_pack import (
    SeedPackConfig,
    parse_seed_pack_config,
    run_seed_label_pack,
)
from alpha_system.core.value_store import ValueStoreFormat
from alpha_system.data.foundation.datasets import (
    CoverageReport,
    DataQualityReport,
    ReportStatus,
)
from alpha_system.features.input_views import OHLCVInputRow, OHLCVInputView
from alpha_system.governance.label_spec import create_label_spec
from alpha_system.labels.families.fixed_horizon import (
    FixedHorizonLabelName,
    build_fixed_horizon_label_definition,
    compute_fixed_horizon_label,
    compute_horizon_overlap_metadata,
)
from alpha_system.labels.registry import LabelRegistry


DATASET_ID = "dsv_futsub_p17_synthetic"
WINDOW_START = "2024-01-02T14:30:00+00:00"
WINDOW_END = "2024-01-02T16:45:00+00:00"


def test_extended_horizon_parquet_registry_fields_and_label_available_ts(
    tmp_path: Path,
) -> None:
    pytest.importorskip("polars")  # seed label-pack materialization hits the polars data layer
    config = _seed_config()

    summary = run_seed_label_pack(
        config,
        alpha_data_root=tmp_path / "alpha_data",
        canonical_root=tmp_path / "unused_canonical",
        datasets_registry_path=tmp_path / "registry" / "datasets.sqlite",
        bar_rows=_bar_rows(config, length=135),
        quality_coverage_builder=_synthetic_quality_coverage,
        value_store_format=ValueStoreFormat.PARQUET,
        output_namespace="labels/materialized/futures_substrate_scaleout_v1/extended_horizon",
    )

    assert summary["value_store"] == ValueStoreFormat.PARQUET.value
    handle = summary["value_store_handle"]
    assert handle["format"] == ValueStoreFormat.PARQUET.value
    assert Path(handle["parquet_path"]).exists()
    assert summary["value_record_count"] > 0

    registry = LabelRegistry.from_alpha_data_root(tmp_path / "alpha_data")
    label_version_id = summary["label_version_ids"][0]
    record = registry.resolve_label(label_version_id)
    assert record is not None
    assert record.label_version_id == label_version_id
    assert record.dataset_version_id == DATASET_ID
    assert record.value_store_format == ValueStoreFormat.PARQUET.value
    assert record.parquet_path == handle["parquet_path"]
    assert record.value_content_hash == handle["content_hash"]
    assert record.value_schema_version == handle["schema_version"]
    assert record.first_label_available_ts > record.first_event_ts

    metadata = record.label_contract.contract_metadata.to_dict()
    overlap = metadata["horizon_overlap_metadata"]
    assert overlap["metadata_version"] == "horizon_overlap_metadata_v1"
    assert overlap["horizon_minutes"] == 60
    assert overlap["rows_are_independent"] is False


def test_extended_horizon_guard_drops_roll_and_maintenance_crossings() -> None:
    definition = _definition(FixedHorizonLabelName.FWD_RET_240M)

    roll_source_ts = _dt("2024-03-07T23:45:00+00:00")
    assert (
        compute_fixed_horizon_label(
            definition,
            OHLCVInputView(
                (
                    _row(roll_source_ts, contract_id="ESM4", close=Decimal("100")),
                    _row(
                        roll_source_ts + timedelta(minutes=240),
                        contract_id="ESM4",
                        close=Decimal("101"),
                    ),
                )
            ),
        )
        == ()
    )

    maintenance_source_ts = _dt("2024-01-02T21:45:00+00:00")
    assert (
        compute_fixed_horizon_label(
            definition,
            OHLCVInputView(
                (
                    _row(maintenance_source_ts, contract_id="ESH4", close=Decimal("100")),
                    _row(
                        maintenance_source_ts + timedelta(minutes=240),
                        contract_id="ESH4",
                        close=Decimal("101"),
                    ),
                )
            ),
        )
        == ()
    )


def test_extended_horizon_overlap_metadata_reports_effective_samples_below_rows() -> None:
    metadata = compute_horizon_overlap_metadata(
        FixedHorizonLabelName.FWD_RET_240M,
        raw_row_count=480,
    )

    payload = metadata.to_dict()
    assert payload["metadata_version"] == "horizon_overlap_metadata_v1"
    assert payload["horizon_minutes"] == 240
    assert payload["raw_row_count"] == 480
    assert payload["effective_sample_count"] == 2
    assert payload["effective_sample_count"] < payload["raw_row_count"]
    assert payload["rows_are_independent"] is False


def _seed_config() -> SeedPackConfig:
    return parse_seed_pack_config(
        {
            "schema": "alpha_system.seed_pack.v1",
            "dataset_version_id": DATASET_ID,
            "partition_schema": "ohlcv_1m",
            "symbol": "ES",
            "partition_id": "ES_2024_fwd_ret_60m",
            "window": {"start_ts": WINDOW_START, "end_ts": WINDOW_END},
            "label_set": {
                "label_set_id": "lset_futsub_p17_extended_60m",
                "labels": [{"name": "fwd_ret_60m", "horizon": "60m"}],
            },
        }
    )


def _definition(name: FixedHorizonLabelName):
    horizon_minutes = int(name.value.removeprefix("fwd_ret_").removesuffix("m"))
    return build_fixed_horizon_label_definition(
        name,
        create_label_spec(
            horizon=f"{horizon_minutes}m",
            path_rules={
                "path": "trade_price_forward_return",
                "horizon_minutes": horizon_minutes,
                "terminal_rule": "synthetic extended fixed-horizon test terminal",
            },
            cost_model={
                "model": "gross_unadjusted_forward_return",
                "adjustment_scope": "not_applied_in_guard_test",
            },
            target_stop_rules={
                "target_rule": "not_used_for_extended_horizon_guard_test",
                "stop_rule": "not_used_for_extended_horizon_guard_test",
            },
            availability_time="2024-01-01T00:00:00+00:00",
            forbidden_feature_overlap={
                "label_ids": [name.value],
                "aliases": [f"synthetic_{name.value}"],
                "transforms": [f"label({name.value})"],
            },
            leakage_checks=["label_as_feature", "availability_time"],
        ),
        dataset_version_ids=(DATASET_ID,),
    )


def _bar_rows(config: SeedPackConfig, *, length: int) -> tuple[dict[str, Any], ...]:
    start = _dt(config.window_start_ts)
    rows: list[dict[str, Any]] = []
    for index in range(length):
        bar_start = start + timedelta(minutes=index)
        bar_end = bar_start + timedelta(minutes=1)
        close = f"{100.0 + index:.2f}"
        rows.append(
            {
                "instrument_id": config.symbol.upper(),
                "contract_id": "ESH4",
                "series_id": f"{config.symbol.upper()}_CONTINUOUS",
                "bar_start_ts": bar_start.isoformat(),
                "bar_end_ts": bar_end.isoformat(),
                "event_ts": bar_end.isoformat(),
                "available_ts": (bar_end + timedelta(seconds=1)).isoformat(),
                "ingested_at": (bar_end + timedelta(seconds=2)).isoformat(),
                "open": close,
                "high": close,
                "low": close,
                "close": close,
                "volume": "10",
                "source": "dsrc_databento_historical",
                "source_request_id": "req_futsub_p17_fixture",
                "data_version": config.dataset_version_id,
                "quality_flags": (),
                "session_label": "RTH",
            }
        )
    return tuple(rows)


def _row(
    event_ts: datetime,
    *,
    contract_id: str,
    close: Decimal,
) -> OHLCVInputRow:
    available = event_ts + timedelta(seconds=1)
    return OHLCVInputRow(
        instrument_id="ES",
        contract_id=contract_id,
        series_id="ES_CONTINUOUS",
        bar_start_ts=event_ts - timedelta(minutes=1),
        bar_end_ts=event_ts,
        event_ts=event_ts,
        available_ts=available,
        ingested_at=available + timedelta(seconds=1),
        open=close,
        high=close + Decimal("0.25"),
        low=close - Decimal("0.25"),
        close=close,
        volume=Decimal("10"),
        data_version=DATASET_ID,
        quality_flags=(),
        session_label="ETH",
    )


def _synthetic_quality_coverage(
    config: SeedPackConfig,
    rows: Any,
    *,
    repo_root: Any,
) -> tuple[DataQualityReport, CoverageReport]:
    quality = DataQualityReport(
        quality_report_id=f"qr_{config.dataset_version_id}",
        dataset_version_id=config.dataset_version_id,
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
    coverage = CoverageReport(
        coverage_report_id=f"cr_{config.dataset_version_id}",
        dataset_version_id=config.dataset_version_id,
        symbol_coverage=_coverage_summary(),
        contract_coverage=_coverage_summary(),
        session_coverage=_coverage_summary(),
        partition_coverage=_coverage_summary(include_partition_counts=True),
        missing_intervals=(),
        incomplete_chunks=(),
    )
    return quality, coverage


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


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
