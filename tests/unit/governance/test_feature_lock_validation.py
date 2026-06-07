"""Tests for fail-closed feature-pack lock validation against a registry."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from alpha_system.core.value_store import ValueStoreFormat
from alpha_system.data.foundation.datasets import (
    CoverageReport,
    DataQualityReport,
    ReportStatus,
)
from alpha_system.cli.seed_pack import (
    SeedPackConfig,
    parse_seed_pack_config,
    run_seed_feature_pack,
)
from alpha_system.governance.feature_lock_validation import (
    FeatureLockValidationError,
    extract_feature_version_ids,
    validate_feature_locks,
)

DATASET_ID = "dsv_lock_validation_fixture_v1"
WINDOW_START = "2024-01-02T14:30:00+00:00"
WINDOW_END = "2024-01-02T15:30:00+00:00"
_MISSING_LOCK = "fver_" + ("0" * 64)


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
                "feature_set_id": "fset_lock_validation",
                "feature_set_version": "v1",
                "alpha_spec_id": "aspec_af848bc999a4c4b11a421bd0",
                "features": [
                    {"name": "returns", "window_length": 1, "horizon": 1},
                    {"name": "rolling_volatility", "window_length": 5},
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
    passing = {"count": 0, "status": ReportStatus.PASSING.value, "blocking": False}
    coverage_summary = {
        "status": ReportStatus.PASSING.value,
        "blocking": False,
        "expected_count": 1,
        "observed_count": 1,
        "missing_count": 0,
    }
    partition_summary = dict(coverage_summary)
    partition_summary["missing_interval_count"] = 0
    partition_summary["incomplete_chunk_count"] = 0
    quality = DataQualityReport(
        quality_report_id=f"qr_{config.dataset_version_id}",
        dataset_version_id=config.dataset_version_id,
        gap_summary=dict(passing),
        duplicate_summary=dict(passing),
        non_monotonic_summary=dict(passing),
        ohlc_errors=dict(passing),
        zero_negative_price_errors=dict(passing),
        zero_volume_anomalies=dict(passing),
        dst_anomalies=dict(passing),
        session_coverage=dict(passing),
        roll_discontinuities=dict(passing),
        provider_error_summary=dict(passing),
        bbo_missing_metric=dict(passing),
        abnormal_spread_summary=dict(passing),
        status=ReportStatus.PASSING,
    )
    coverage = CoverageReport(
        coverage_report_id=f"cr_{config.dataset_version_id}",
        dataset_version_id=config.dataset_version_id,
        symbol_coverage=dict(coverage_summary),
        contract_coverage=dict(coverage_summary),
        session_coverage=dict(coverage_summary),
        partition_coverage=partition_summary,
        missing_intervals=(),
        incomplete_chunks=(),
    )
    return quality, coverage


def _registered_locks(tmp_path: Path) -> tuple[Path, list[str]]:
    summary = run_seed_feature_pack(
        _config(),
        alpha_data_root=tmp_path / "alpha_data",
        canonical_root=tmp_path / "unused_canonical",
        datasets_registry_path=tmp_path / "registry" / "datasets.sqlite",
        bar_rows=_bar_rows(),
        quality_coverage_builder=_synthetic_quality_coverage,
        value_store_format=ValueStoreFormat.JSONL,
    )
    registry_path = tmp_path / "alpha_data" / "registry" / "features.sqlite"
    return registry_path, list(summary["feature_version_ids"])


def test_extract_feature_version_ids_from_mappings_and_strings() -> None:
    locks = [{"feature_version_id": "fver_" + "a" * 64}, "fver_" + "b" * 64]
    assert extract_feature_version_ids(locks) == (
        "fver_" + "a" * 64,
        "fver_" + "b" * 64,
    )


def test_extract_rejects_missing_or_malformed_ids() -> None:
    with pytest.raises(FeatureLockValidationError):
        extract_feature_version_ids([{"not_a_version": "x"}])
    with pytest.raises(FeatureLockValidationError):
        extract_feature_version_ids(["not-a-fver"])


def test_all_present_locks_validate_ok(tmp_path: Path) -> None:
    registry_path, version_ids = _registered_locks(tmp_path)
    locks = [{"feature_version_id": version_id} for version_id in version_ids]
    report = validate_feature_locks(locks, registry_path=registry_path)
    assert report.ok
    assert report.stale_lock_ids == ()
    assert len(report.resolutions) == len(version_ids)
    assert all(resolution.resolved for resolution in report.resolutions)


def test_one_missing_lock_fails_closed_with_clear_message(tmp_path: Path) -> None:
    registry_path, version_ids = _registered_locks(tmp_path)
    locks = [{"feature_version_id": version_ids[0]}, {"feature_version_id": _MISSING_LOCK}]
    with pytest.raises(FeatureLockValidationError) as excinfo:
        validate_feature_locks(locks, registry_path=registry_path)
    assert _MISSING_LOCK in str(excinfo.value)
    assert "stale" in str(excinfo.value).lower()
