from __future__ import annotations

import json
from pathlib import Path

import pytest

from alpha_system.core.hashing import hash_config
from alpha_system.core.registry import connect_registry
from alpha_system.data.foundation.datasets import (
    CoverageReport,
    DataQualityReport,
    DatasetVersion,
    compute_quality_report_hash,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.data.foundation.version_registry import (
    DATASET_VERSION_REGISTRY_METADATA_SCHEMA,
    persist_dataset_version,
    resolve_dataset_version,
)

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


def _quality_report(dataset_version_id: str = "dsv_registry_synthetic_v1") -> DataQualityReport:
    return DataQualityReport.from_canonical_bars(
        quality_report_id="dqr_registry_synthetic_clean",
        dataset_version_id=dataset_version_id,
        bars=_bars(),
    )


def _coverage_report(dataset_version_id: str = "dsv_registry_synthetic_v1") -> CoverageReport:
    return CoverageReport.from_canonical_bars(
        coverage_report_id="covr_registry_synthetic_clean",
        dataset_version_id=dataset_version_id,
        bars=_bars(),
        expected_intervals=_expected_intervals(),
    )


def _source_manifest(manifest_hash: str) -> dict[str, str]:
    return {"manifest_hash": manifest_hash}


def _version(**overrides: object) -> DatasetVersion:
    quality_report = _quality_report()
    values: dict[str, object] = {
        "dataset_version_id": "dsv_registry_synthetic_v1",
        "source": "dsrc_ibkr_historical",
        "symbol_universe": ("ES", "NQ"),
        "bar_size": "1 min",
        "what_to_show": "TRADES",
        "start_ts": "2026-06-01T14:30:00+00:00",
        "end_ts": "2026-06-01T14:33:00+00:00",
        "contract_universe": ("fcr_synthetic_es_h5", "fcr_synthetic_nq_h5"),
        "roll_policy_id": "roll_policy_volume_open_interest",
        "manifest_hash": hash_config({"manifest_id": "hrm_registry_synthetic_v1"}),
        "code_hash": hash_config({"code_paths": ("src/alpha_system/data/foundation",)}),
        "config_hash": hash_config({"bar_size": "1 min", "what_to_show": "TRADES"}),
        "quality_report_hash": compute_quality_report_hash(quality_report),
        "created_at": "2026-06-03T21:52:49+00:00",
    }
    values.update(overrides)
    return DatasetVersion.from_mapping(values)


def _persist(registry_path: Path, version: DatasetVersion) -> None:
    persist_dataset_version(
        registry_path,
        version,
        quality_report=_quality_report(version.dataset_version_id),
        coverage_report=_coverage_report(version.dataset_version_id),
        source_manifest=_source_manifest(version.manifest_hash),
        code_hash=version.code_hash,
        config_hash=version.config_hash,
    )


def test_dataset_version_round_trips_through_existing_registry_table(
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "registry.sqlite"
    version = _version()

    _persist(registry_path, version)
    loaded = resolve_dataset_version(registry_path, version.dataset_version_id)

    assert loaded == version

    with connect_registry(registry_path, read_only=True) as connection:
        row = connection.execute(
            """
            SELECT data_version, content_hash, config_hash, metadata_json
            FROM dataset_versions
            WHERE data_version = ?
            """,
            (version.dataset_version_id,),
        ).fetchone()

    assert row["data_version"] == version.dataset_version_id
    assert row["content_hash"] == version.manifest_hash
    assert row["config_hash"] == version.config_hash
    metadata = json.loads(str(row["metadata_json"]))
    assert metadata["schema"] == DATASET_VERSION_REGISTRY_METADATA_SCHEMA
    assert metadata["dataset_version"]["quality_report_hash"] == version.quality_report_hash


def test_duplicate_dataset_version_id_is_rejected_without_overwrite(
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    version = _version()

    _persist(registry_path, version)
    with pytest.raises(DataFoundationValidationError, match="already exists"):
        persist_dataset_version(
            registry_path,
            _version(source="dsrc_other_source", manifest_hash=hash_config({"other": "manifest"})),
            quality_report=_quality_report(),
            coverage_report=_coverage_report(),
            source_manifest=_source_manifest(hash_config({"other": "manifest"})),
            code_hash=version.code_hash,
            config_hash=version.config_hash,
        )

    assert resolve_dataset_version(registry_path, version.dataset_version_id) == version


def test_resolve_missing_dataset_version_returns_none(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.db"

    assert resolve_dataset_version(registry_path, "dsv_missing_v1") is None


def test_registry_resolution_fails_closed_on_misbound_row_metadata(
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "registry.sqlite"
    version = _version()
    _persist(registry_path, version)

    with connect_registry(registry_path) as connection:
        connection.execute(
            """
            UPDATE dataset_versions
            SET content_hash = ?
            WHERE data_version = ?
            """,
            (hash_config({"wrong": "manifest"}), version.dataset_version_id),
        )

    with pytest.raises(DataFoundationValidationError, match="mis-bound"):
        resolve_dataset_version(registry_path, version.dataset_version_id)


def test_registry_adapter_rejects_non_local_only_registry_path() -> None:
    version = _version()
    with pytest.raises(DataFoundationValidationError, match="local-only"):
        persist_dataset_version(
            "/tmp/registry.txt",
            version,
            quality_report=_quality_report(),
            coverage_report=_coverage_report(),
            source_manifest=_source_manifest(version.manifest_hash),
            code_hash=version.code_hash,
            config_hash=version.config_hash,
        )
