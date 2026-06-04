from __future__ import annotations

import json
from dataclasses import fields
from pathlib import Path

import pytest

from alpha_system.data.foundation.datasets import (
    COVERAGE_REPORT_FIELDS,
    CoverageReport,
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
    bars = _fixture()["bars"]
    assert isinstance(bars, list)
    return [dict(bar) for bar in bars]


def _expected_intervals() -> list[dict[str, object]]:
    intervals = _fixture()["expected_intervals"]
    assert isinstance(intervals, list)
    return [dict(interval) for interval in intervals]


def _quality_report(**overrides: object) -> DataQualityReport:
    values = {
        "quality_report_id": "dqr_synthetic_clean",
        "dataset_version_id": "dsv_synthetic_v1",
        "bars": _bars(),
    }
    values.update(overrides)
    return DataQualityReport.from_canonical_bars(**values)


def _coverage_report(**overrides: object) -> CoverageReport:
    values = {
        "coverage_report_id": "covr_synthetic_clean",
        "dataset_version_id": "dsv_synthetic_v1",
        "bars": _bars(),
        "expected_intervals": _expected_intervals(),
    }
    values.update(overrides)
    return CoverageReport.from_canonical_bars(**values)


def test_coverage_report_exposes_exact_required_fields() -> None:
    report = _coverage_report()

    assert tuple(field.name for field in fields(CoverageReport)) == COVERAGE_REPORT_FIELDS
    assert set(report.to_mapping()) == set(COVERAGE_REPORT_FIELDS)
    assert report.coverage_status is ReportStatus.PASSING
    assert not report.blocks_versioning


def test_coverage_report_construction_fails_closed_on_missing_extra_or_raw_dump() -> None:
    report_mapping = dict(_coverage_report().to_mapping())

    missing = dict(report_mapping)
    del missing["partition_coverage"]
    with pytest.raises(DataFoundationValidationError, match="missing required fields"):
        CoverageReport.from_mapping(missing)

    with pytest.raises(DataFoundationValidationError, match="unsupported fields"):
        CoverageReport.from_mapping({**report_mapping, "quality_passed": True})

    raw_dump = dict(report_mapping)
    raw_dump["missing_intervals"] = ({**_bars()[0], "status": "BLOCKING"},)
    with pytest.raises(DataFoundationValidationError, match="raw or full canonical bar"):
        CoverageReport.from_mapping(raw_dump)


def test_coverage_alone_is_not_quality_and_requires_matching_quality_report() -> None:
    coverage = _coverage_report()
    quality = _quality_report()

    with pytest.raises(DataFoundationValidationError, match="coverage alone is not quality"):
        coverage.require_linked_quality_report(None)

    assert coverage.require_linked_quality_report(quality) is quality

    mismatched = _quality_report(
        quality_report_id="dqr_other_dataset",
        dataset_version_id="dsv_other_v1",
    )
    with pytest.raises(DataFoundationValidationError, match="dataset_version_id must match"):
        coverage.require_linked_quality_report(mismatched)


def test_missing_intervals_are_documented_and_block_versioning() -> None:
    coverage = _coverage_report(bars=(_bars()[0], _bars()[2]))

    assert coverage.coverage_status is ReportStatus.BLOCKING
    assert coverage.blocks_versioning
    assert len(coverage.missing_intervals) == 1
    assert coverage.partition_coverage["missing_interval_count"] == 1

    with pytest.raises(DataFoundationValidationError, match="blocking coverage"):
        coverage.require_linked_quality_report(_quality_report())


def test_undocumented_missing_coverage_fails_closed() -> None:
    report_mapping = dict(_coverage_report(bars=(_bars()[0], _bars()[2])).to_mapping())
    report_mapping["missing_intervals"] = ()

    with pytest.raises(DataFoundationValidationError, match="missing_interval_count"):
        CoverageReport.from_mapping(report_mapping)


def test_incomplete_chunks_are_aggregate_blockers() -> None:
    coverage = _coverage_report(
        incomplete_chunks=(
            {
                "chunk_id": "hchunk_synth_incomplete",
                "status": "INCOMPLETE",
                "start_ts": "2026-06-01T14:30:00+00:00",
                "end_ts": "2026-06-01T14:33:00+00:00",
                "reason": "synthetic_incomplete_chunk",
            },
        )
    )

    assert coverage.coverage_status is ReportStatus.BLOCKING
    assert coverage.partition_coverage["incomplete_chunk_count"] == 1
    assert coverage.incomplete_chunks[0]["chunk_id"] == "hchunk_synth_incomplete"


def test_blocking_quality_report_cannot_satisfy_coverage_linkage() -> None:
    coverage = _coverage_report()
    blocking_quality = _quality_report(bars=(_bars()[0], _bars()[2]))

    with pytest.raises(DataFoundationValidationError, match="blocking DataQualityReport"):
        coverage.require_linked_quality_report(blocking_quality)
