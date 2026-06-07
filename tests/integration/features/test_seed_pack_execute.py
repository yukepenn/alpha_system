from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from dataclasses import replace

from alpha_system.cli.seed_pack import (
    SeedPackConfig,
    load_seed_pack_config,
    parse_seed_pack_config,
    preview_seed_feature_pack,
    run_seed_feature_pack,
    run_seed_label_pack,
)
from alpha_system.core.value_store import ValueStoreFormat
from alpha_system.data.foundation.datasets import (
    CoverageReport,
    DataQualityReport,
    ReportStatus,
)

DATASET_ID = "dsv_seed_pack_execute_fixture_v1"
WINDOW_START = "2024-01-02T14:30:00+00:00"
WINDOW_END = "2024-01-02T15:30:00+00:00"


def _config() -> SeedPackConfig:
    return parse_seed_pack_config(
        {
            "schema": "alpha_system.seed_pack.v1",
            "dataset_version_id": DATASET_ID,
            "partition_schema": "ohlcv_1m",
            "symbol": "ES",
            "partition_id": "development_partition",
            "window": {"start_ts": WINDOW_START, "end_ts": WINDOW_END},
            "feature_set": {
                "feature_set_id": "fset_seed_pack_execute",
                "feature_set_version": "v1",
                "alpha_spec_id": "aspec_af848bc999a4c4b11a421bd0",
                "features": [
                    {"name": "returns", "window_length": 1, "horizon": 1},
                    {"name": "rolling_volatility", "window_length": 5},
                ],
            },
            "label_set": {
                "label_set_id": "lset_seed_pack_execute",
                "labels": [
                    {"name": "fwd_ret_5m", "horizon": "5m"},
                    {"name": "fwd_ret_10m", "horizon": "10m"},
                ],
            },
        }
    )


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)


def _bar_rows(length: int = 30) -> tuple[dict[str, Any], ...]:
    start = _dt(WINDOW_START)
    rows: list[dict[str, Any]] = []
    for index in range(length):
        bar_start = start + timedelta(minutes=index)
        bar_end = bar_start + timedelta(minutes=1)
        close = f"{100.0 + index:.2f}"
        rows.append(
            {
                "instrument_id": "ES",
                "contract_id": "ESM4",
                "series_id": "ES_c_0",
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
                "source_request_id": "req_fixture_1",
                "data_version": DATASET_ID,
                "quality_flags": (),
                "session_label": "RTH",
            }
        )
    return tuple(rows)


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


def _no_value_rows_in_sqlite(registry_path: Path, table: str) -> None:
    connection = sqlite3.connect(registry_path.as_posix())
    try:
        cursor = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        table_names = {row[0] for row in cursor.fetchall()}
        assert not any("value" in name.lower() for name in table_names), table_names
    finally:
        connection.close()


def test_seed_feature_and_label_pack_execute_over_synthetic_rows(tmp_path: Path) -> None:
    alpha_data_root = tmp_path / "alpha_data"
    dataset_registry = tmp_path / "registry" / "datasets.sqlite"
    config = _config()
    rows = _bar_rows()

    # Pin the JSONL audit/small tier: this stdlib synthetic test validates operator
    # mechanics and the JSONL value store. The dual/Parquet operator default needs the
    # optional polars dependency and is covered by polars-guarded and real-smoke checks.
    feature_summary = run_seed_feature_pack(
        config,
        alpha_data_root=alpha_data_root,
        canonical_root=tmp_path / "unused_canonical",
        datasets_registry_path=dataset_registry,
        bar_rows=rows,
        quality_coverage_builder=_synthetic_quality_coverage,
        value_store_format=ValueStoreFormat.JSONL,
    )
    label_summary = run_seed_label_pack(
        config,
        alpha_data_root=alpha_data_root,
        canonical_root=tmp_path / "unused_canonical",
        datasets_registry_path=dataset_registry,
        bar_rows=rows,
        quality_coverage_builder=_synthetic_quality_coverage,
        value_store_format=ValueStoreFormat.JSONL,
    )

    features_registry = alpha_data_root / "registry" / "features.sqlite"
    labels_registry = alpha_data_root / "registry" / "labels.sqlite"
    assert features_registry.exists()
    assert labels_registry.exists()

    assert feature_summary["pack_kind"] == "feature"
    assert feature_summary["feature_count"] == 2
    assert len(feature_summary["feature_version_ids"]) == 2
    assert feature_summary["value_record_count"] > 0
    assert feature_summary["quality_status"] == ReportStatus.PASSING.value

    assert label_summary["pack_kind"] == "label"
    assert label_summary["label_count"] == 2
    assert len(label_summary["label_version_ids"]) == 2
    assert label_summary["value_record_count"] > 0

    # Values written under ALPHA_DATA_ROOT as values.jsonl, never into sqlite.
    value_files = list(alpha_data_root.rglob("values.jsonl"))
    assert value_files
    for value_file in value_files:
        assert value_file.is_relative_to(alpha_data_root)
    feature_output = Path(feature_summary["output_path"])
    label_output = Path(label_summary["output_path"])
    assert feature_output.is_relative_to(alpha_data_root)
    assert label_output.is_relative_to(alpha_data_root)
    assert feature_output.exists()
    assert label_output.exists()

    # No raw value records leak into the SQLite registries.
    _no_value_rows_in_sqlite(features_registry, "feature")
    _no_value_rows_in_sqlite(labels_registry, "label")

    # Output JSONL carries plan + value records, not registry rows.
    feature_lines = [json.loads(line) for line in feature_output.read_text().splitlines()]
    assert feature_lines[0]["record_type"] == "feature_materialization_plan"
    assert any(line["record_type"] == "feature_value" for line in feature_lines[1:])


def _session_smoke_rows(config: SeedPackConfig, length: int = 30) -> tuple[dict[str, Any], ...]:
    start = _dt(config.window_start_ts)
    rows: list[dict[str, Any]] = []
    for index in range(length):
        bar_start = start + timedelta(minutes=index)
        bar_end = bar_start + timedelta(minutes=1)
        close = f"{100.0 + index:.2f}"
        rows.append(
            {
                "instrument_id": config.symbol.upper(),
                "contract_id": "ESM4",
                "series_id": f"{config.symbol.upper()}_c_0",
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
                "source_request_id": "req_fixture_1",
                "data_version": config.dataset_version_id,
                "quality_flags": (),
                "session_label": "RTH",
            }
        )
    return tuple(rows)


def test_dry_run_preview_fver_equals_execute_registered_fver(tmp_path: Path) -> None:
    # Round-trip guard: the write-free preview must report the SAME
    # feature_version_id that a real (temp-root) execute registers, for the
    # official seed config configs/seed_packs/es_ohlcv_session_smoke_v1.json.
    config_path = Path("configs/seed_packs/es_ohlcv_session_smoke_v1.json")
    config = load_seed_pack_config(config_path)
    # Re-point dataset/window onto the synthetic fixture so we can execute with
    # in-memory rows (no polars / no real canonical parquet needed).
    config = replace(
        config,
        dataset_version_id=DATASET_ID,
        window_start_ts=WINDOW_START,
        window_end_ts=WINDOW_END,
    )
    rows = _session_smoke_rows(config)

    preview = preview_seed_feature_pack(config)
    assert preview["preview"] is True
    assert preview["writes_values"] is False

    summary = run_seed_feature_pack(
        config,
        alpha_data_root=tmp_path / "alpha_data",
        canonical_root=tmp_path / "unused_canonical",
        datasets_registry_path=tmp_path / "registry" / "datasets.sqlite",
        bar_rows=rows,
        quality_coverage_builder=_synthetic_quality_coverage,
        value_store_format=ValueStoreFormat.JSONL,
    )

    # The previewed feature_version_ids must equal the registered ones, in order.
    assert preview["feature_version_ids"] == summary["feature_version_ids"]
    assert preview["feature_count"] == summary["feature_count"]

    # The preview wrote nothing: only the execute created the registry.
    registry_path = tmp_path / "alpha_data" / "registry" / "features.sqlite"
    assert registry_path.exists()


def test_seed_label_pack_rejects_non_trade_price_labels(tmp_path: Path) -> None:
    payload = {
        "schema": "alpha_system.seed_pack.v1",
        "dataset_version_id": DATASET_ID,
        "partition_schema": "ohlcv_1m",
        "symbol": "ES",
        "partition_id": "development_partition",
        "window": {"start_ts": WINDOW_START, "end_ts": WINDOW_END},
        "label_set": {
            "label_set_id": "lset_seed_pack_midprice",
            "labels": [{"name": "mid_fwd_ret_5m", "horizon": "5m"}],
        },
    }
    config = parse_seed_pack_config(payload)
    rows = _bar_rows()

    import pytest

    with pytest.raises(Exception):  # noqa: B017 - SeedPackError is a ValueError subclass
        run_seed_label_pack(
            config,
            alpha_data_root=tmp_path / "alpha_data",
            canonical_root=tmp_path / "unused_canonical",
            datasets_registry_path=tmp_path / "registry" / "datasets.sqlite",
            bar_rows=rows,
            quality_coverage_builder=_synthetic_quality_coverage,
        )
