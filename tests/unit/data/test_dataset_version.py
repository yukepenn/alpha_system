from __future__ import annotations

import json
from dataclasses import fields, replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from alpha_system.core.hashing import hash_config
from alpha_system.data.foundation.datasets import (
    DATASET_VERSION_FIELDS,
    CoverageReport,
    DataQualityReport,
    DatasetVersion,
    compute_quality_report_hash,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError

FIXTURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "data"
    / "synthetic_quality_coverage_inputs.json"
)

START_TS = datetime(2026, 6, 1, 14, 30, tzinfo=UTC)
END_TS = datetime(2026, 6, 1, 14, 33, tzinfo=UTC)
CREATED_AT = datetime(2026, 6, 3, 21, 52, 49, tzinfo=UTC)


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


def _quality_report(dataset_version_id: str = "dsv_synthetic_v1") -> DataQualityReport:
    return DataQualityReport.from_canonical_bars(
        quality_report_id="dqr_synthetic_clean",
        dataset_version_id=dataset_version_id,
        bars=_bars(),
    )


def _coverage_report(dataset_version_id: str = "dsv_synthetic_v1") -> CoverageReport:
    return CoverageReport.from_canonical_bars(
        coverage_report_id="covr_synthetic_clean",
        dataset_version_id=dataset_version_id,
        bars=_bars(),
        expected_intervals=_expected_intervals(),
    )


def _manifest_hash() -> str:
    return hash_config({"manifest_id": "hrm_synthetic_es_h5_manifest_v1"})


def _version_values(**overrides: object) -> dict[str, object]:
    quality_report = _quality_report()
    values: dict[str, object] = {
        "dataset_version_id": "dsv_synthetic_v1",
        "source": "dsrc_ibkr_historical",
        "symbol_universe": ("ES", "NQ"),
        "bar_size": "1 min",
        "what_to_show": "TRADES",
        "start_ts": START_TS.isoformat(),
        "end_ts": END_TS.isoformat(),
        "contract_universe": ("fcr_synthetic_es_h5", "fcr_synthetic_nq_h5"),
        "roll_policy_id": "roll_policy_volume_open_interest",
        "manifest_hash": _manifest_hash(),
        "code_hash": hash_config({"code_paths": ("src/alpha_system/data/foundation",)}),
        "config_hash": hash_config({"bar_size": "1 min", "what_to_show": "TRADES"}),
        "quality_report_hash": compute_quality_report_hash(quality_report),
        "created_at": CREATED_AT.isoformat(),
    }
    values.update(overrides)
    return values


def _dataset_version(**overrides: object) -> DatasetVersion:
    return DatasetVersion.from_mapping(_version_values(**overrides))


def test_dataset_version_exposes_exact_required_fields() -> None:
    version = _dataset_version(symbol_universe=("es", "nq"), what_to_show="trades")

    assert tuple(field.name for field in fields(DatasetVersion)) == DATASET_VERSION_FIELDS
    assert set(version.to_mapping()) == set(DATASET_VERSION_FIELDS)
    assert version.symbol_universe == ("ES", "NQ")
    assert version.what_to_show == "TRADES"
    assert version.reproducibility_hashes == {
        "manifest_hash": version.manifest_hash,
        "code_hash": version.code_hash,
        "config_hash": version.config_hash,
        "quality_report_hash": version.quality_report_hash,
    }


def test_dataset_version_from_mapping_fails_closed_on_missing_extra_or_blank_id() -> None:
    values = _version_values()

    missing = dict(values)
    missing.pop("manifest_hash")
    with pytest.raises(DataFoundationValidationError, match="missing required fields"):
        DatasetVersion.from_mapping(missing)

    with pytest.raises(DataFoundationValidationError, match="unsupported fields"):
        DatasetVersion.from_mapping({**values, "coverage_report_id": "covr_loose"})

    with pytest.raises(DataFoundationValidationError, match="non-empty string"):
        DatasetVersion.from_mapping({**values, "dataset_version_id": "   "})


def test_dataset_version_rejects_reversed_or_naive_timestamps() -> None:
    with pytest.raises(DataFoundationValidationError, match="end_ts"):
        _dataset_version(end_ts="2026-05-31T00:00:00+00:00")

    with pytest.raises(DataFoundationValidationError, match="timezone-aware"):
        _dataset_version(start_ts="2026-06-01T14:30:00")


def test_dataset_version_rejects_missing_or_malformed_hashes() -> None:
    with pytest.raises(DataFoundationValidationError, match="manifest_hash"):
        _dataset_version(manifest_hash="")

    with pytest.raises(DataFoundationValidationError, match="quality_report_hash"):
        _dataset_version(quality_report_hash="abc123")


def test_dataset_version_lifecycle_gate_accepts_bound_inputs() -> None:
    quality_report = _quality_report()
    coverage_report = _coverage_report()
    version = _dataset_version()
    source_manifest = {"manifest_hash": version.manifest_hash}

    assert (
        version.require_lifecycle_prerequisites(
            "VERSIONED",
            quality_report=quality_report,
            coverage_report=coverage_report,
            source_manifest=source_manifest,
            code_hash=version.code_hash,
            config_hash=version.config_hash,
        )
        is version
    )
    assert (
        version.require_lifecycle_prerequisites(
            "READY_FOR_RESEARCH",
            quality_report=quality_report,
            coverage_report=coverage_report,
            source_manifest=source_manifest,
            code_hash=version.code_hash,
            config_hash=version.config_hash,
        )
        is version
    )


def test_incomplete_or_misbound_hash_rejects_versioned_state() -> None:
    quality_report = _quality_report()
    coverage_report = _coverage_report()
    version = _dataset_version()

    with pytest.raises(DataFoundationValidationError, match="quality_report_hash"):
        replace(
            version,
            quality_report_hash=hash_config({"different": "quality-report"}),
        ).require_lifecycle_prerequisites(
            "VERSIONED",
            quality_report=quality_report,
            coverage_report=coverage_report,
            source_manifest={"manifest_hash": version.manifest_hash},
            code_hash=version.code_hash,
            config_hash=version.config_hash,
        )

    with pytest.raises(DataFoundationValidationError, match="manifest_hash"):
        version.require_lifecycle_prerequisites(
            "VERSIONED",
            quality_report=quality_report,
            coverage_report=coverage_report,
            source_manifest={"manifest_hash": hash_config({"different": "manifest"})},
            code_hash=version.code_hash,
            config_hash=version.config_hash,
        )

    with pytest.raises(DataFoundationValidationError, match="code_hash"):
        version.require_lifecycle_prerequisites(
            "VERSIONED",
            quality_report=quality_report,
            coverage_report=coverage_report,
            source_manifest={"manifest_hash": version.manifest_hash},
            code_hash=hash_config({"different": "code"}),
            config_hash=version.config_hash,
        )

    with pytest.raises(DataFoundationValidationError, match="config_hash"):
        version.require_lifecycle_prerequisites(
            "VERSIONED",
            quality_report=quality_report,
            coverage_report=coverage_report,
            source_manifest={"manifest_hash": version.manifest_hash},
            code_hash=version.code_hash,
            config_hash=hash_config({"different": "config"}),
        )

    with pytest.raises(DataFoundationValidationError, match="CoverageReport"):
        version.require_lifecycle_prerequisites(
            "VERSIONED",
            quality_report=quality_report,
            coverage_report=None,
            source_manifest={"manifest_hash": version.manifest_hash},
            code_hash=version.code_hash,
            config_hash=version.config_hash,
        )


def test_blocking_or_mismatched_reports_block_versioning() -> None:
    version = _dataset_version()
    blocking_quality = DataQualityReport.from_canonical_bars(
        quality_report_id="dqr_synthetic_blocking",
        dataset_version_id=version.dataset_version_id,
        bars=(_bars()[0], _bars()[2]),
    )
    mismatched_coverage = _coverage_report(dataset_version_id="dsv_other_v1")

    with pytest.raises(DataFoundationValidationError, match="blocking DataQualityReport"):
        version.require_lifecycle_prerequisites(
            "VERSIONED",
            quality_report=blocking_quality,
            coverage_report=_coverage_report(),
            source_manifest={"manifest_hash": version.manifest_hash},
            code_hash=version.code_hash,
            config_hash=version.config_hash,
        )

    with pytest.raises(DataFoundationValidationError, match="CoverageReport"):
        version.require_lifecycle_prerequisites(
            "READY_FOR_RESEARCH",
            quality_report=_quality_report(),
            coverage_report=mismatched_coverage,
            source_manifest={"manifest_hash": version.manifest_hash},
            code_hash=version.code_hash,
            config_hash=version.config_hash,
        )
