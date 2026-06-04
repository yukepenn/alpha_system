from __future__ import annotations

import json
from dataclasses import fields
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from alpha_system.data.foundation.datasets import (
    DATA_QUALITY_REPORT_FIELDS,
    DataQualityReport,
    ReportStatus,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError

FIXTURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "data"
    / "synthetic_quality_coverage_inputs.json"
)


def _fixture() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _bars() -> list[dict[str, object]]:
    fixture = _fixture()
    bars = fixture["bars"]
    assert isinstance(bars, list)
    return [dict(bar) for bar in bars]


def _clean_report(**overrides: object) -> DataQualityReport:
    values = {
        "quality_report_id": "dqr_synthetic_clean",
        "dataset_version_id": "dsv_synthetic_v1",
        "bars": _bars(),
    }
    values.update(overrides)
    return DataQualityReport.from_canonical_bars(**values)


def test_data_quality_report_exposes_exact_required_fields() -> None:
    report = _clean_report()

    assert tuple(field.name for field in fields(DataQualityReport)) == DATA_QUALITY_REPORT_FIELDS
    assert set(report.to_mapping()) == set(DATA_QUALITY_REPORT_FIELDS)
    assert report.status is ReportStatus.PASSING
    assert not report.blocks_versioning


def test_data_quality_report_construction_fails_closed_on_missing_extra_or_raw_dump() -> None:
    report_mapping = dict(_clean_report().to_mapping())

    missing = dict(report_mapping)
    del missing["gap_summary"]
    with pytest.raises(DataFoundationValidationError, match="missing required fields"):
        DataQualityReport.from_mapping(missing)

    with pytest.raises(DataFoundationValidationError, match="unsupported fields"):
        DataQualityReport.from_mapping({**report_mapping, "raw_bars": []})

    raw_dump = dict(report_mapping)
    raw_dump["gap_summary"] = {
        **dict(raw_dump["gap_summary"]),
        "sample_intervals": (_bars()[0],),
    }
    with pytest.raises(DataFoundationValidationError, match="raw or full canonical bar"):
        DataQualityReport.from_mapping(raw_dump)


def test_data_quality_report_rejects_status_that_hides_blockers() -> None:
    report_mapping = dict(_clean_report().to_mapping())
    report_mapping["gap_summary"] = {
        "count": 1,
        "status": "BLOCKING",
        "blocking": True,
        "sample_intervals": (),
        "truncated": False,
    }
    report_mapping["status"] = "PASSING"

    with pytest.raises(DataFoundationValidationError, match="status must be BLOCKING"):
        DataQualityReport.from_mapping(report_mapping)


def test_silent_gaps_duplicate_and_non_monotonic_timestamps_block() -> None:
    gap_report = _clean_report(bars=(_bars()[0], _bars()[2]))
    duplicate_report = _clean_report(bars=(_bars()[0], _bars()[0]))
    non_monotonic_report = _clean_report(bars=(_bars()[1], _bars()[0]))

    assert gap_report.status is ReportStatus.BLOCKING
    assert gap_report.gap_summary["count"] == 1
    assert duplicate_report.status is ReportStatus.BLOCKING
    assert duplicate_report.duplicate_summary["count"] == 1
    assert non_monotonic_report.status is ReportStatus.BLOCKING
    assert non_monotonic_report.non_monotonic_summary["count"] == 1


def test_ohlc_and_zero_negative_price_defects_block() -> None:
    ohlc_bar = _bars()[0]
    ohlc_bar["high"] = "4999.00"
    ohlc_report = _clean_report(bars=(ohlc_bar,))

    price_bar = _bars()[0]
    price_bar["open"] = "0"
    price_report = _clean_report(bars=(price_bar,))

    assert ohlc_report.status is ReportStatus.BLOCKING
    assert ohlc_report.ohlc_errors["count"] >= 1
    assert price_report.status is ReportStatus.BLOCKING
    assert price_report.zero_negative_price_errors["count"] == 1


def test_zero_volume_anomaly_warns_without_implying_acceptance() -> None:
    zero_volume_bar = _bars()[0]
    zero_volume_bar["volume"] = "0"
    report = _clean_report(bars=(zero_volume_bar,))

    assert report.status is ReportStatus.WARNING
    assert report.zero_volume_anomalies["count"] == 1
    assert not report.blocks_versioning


def test_dst_and_session_coverage_anomalies_block() -> None:
    dst_bar = _bars()[0]
    chicago = ZoneInfo("America/Chicago")
    dst_bar.update(
        {
            "bar_start_ts": datetime(2026, 3, 8, 1, 59, tzinfo=chicago),
            "bar_end_ts": datetime(2026, 3, 8, 3, 0, tzinfo=chicago),
            "event_ts": datetime(2026, 3, 8, 3, 0, tzinfo=chicago),
            "available_ts": datetime(2026, 3, 8, 3, 0, 5, tzinfo=chicago),
            "ingested_at": datetime(2026, 3, 8, 8, 1, tzinfo=UTC),
        }
    )
    dst_report = _clean_report(bars=(dst_bar,))
    session_report = _clean_report(expected_sessions=("ETH", "RTH"))

    assert dst_report.status is ReportStatus.BLOCKING
    assert dst_report.dst_anomalies["count"] == 1
    assert session_report.status is ReportStatus.BLOCKING
    assert session_report.session_coverage["missing_expected_sessions"] == ("RTH",)


def test_roll_discontinuities_block_unless_documented() -> None:
    rolled_bars = _bars()
    rolled_bars[2]["contract_id"] = "fut_es_202609"

    blocking_report = _clean_report(bars=rolled_bars)
    documented_report = _clean_report(
        bars=rolled_bars,
        roll_transitions=(
            {
                "from_contract": "fut_es_202606",
                "to_contract": "fut_es_202609",
                "effective_ts": rolled_bars[2]["bar_start_ts"],
            },
        ),
    )

    assert blocking_report.status is ReportStatus.BLOCKING
    assert blocking_report.roll_discontinuities["count"] == 1
    assert documented_report.roll_discontinuities["count"] == 0
    assert documented_report.status is ReportStatus.PASSING


def test_provider_errors_are_aggregated_and_block() -> None:
    report = _clean_report(
        provider_errors=(
            {
                "error_code": "162",
                "resolution": "INCOMPLETE_RESPONSE_RECORDED",
                "retryable": True,
                "chunk_id": "hchunk_synth_missing",
            },
        )
    )

    assert report.status is ReportStatus.BLOCKING
    assert report.provider_error_summary["count"] == 1
    assert report.provider_error_summary["by_code"] == {"162": 1}
