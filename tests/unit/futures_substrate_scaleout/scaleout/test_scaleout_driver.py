from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

import alpha_system.features.scaleout.driver as scaleout_driver
from alpha_system.data.foundation.datasets import (
    CoverageReport,
    DataQualityReport,
    DatasetAcceptanceInventory,
    DatasetVersion,
    ReportStatus,
    build_dataset_acceptance_lock,
    compute_dataset_acceptance_policy_hash,
    compute_quality_report_hash,
    persist_dataset_acceptance_locks,
)
from alpha_system.data.foundation.version_registry import persist_dataset_version
from alpha_system.features.scaleout import (
    MaterializedUnitEvidence,
    load_scaleout_config,
    run_scaleout,
)

DATASET_ID_2024 = "dsv_databento_ohlcv_05404069799decb0"
HASH_0 = "0" * 64
HASH_1 = "1" * 64
HASH_2 = "2" * 64


def test_base_ohlcv_plan_uses_acceptance_summary_and_excludes_blocked_2018() -> None:
    config = load_scaleout_config()

    units = run_scaleout(config, rollout="full-window").records

    assert len(units) == 24
    assert {record.unit.year for record in units} == set(range(2019, 2027))
    assert {record.unit.symbol for record in units} == {"ES", "NQ", "RTY"}
    assert all(record.status == "planned" for record in units)
    assert all(record.unit.acceptance_state_source == "acceptance_summary" for record in units)
    assert all(record.unit.dataset_version_id != "dsv_databento_ohlcv_321568572236ef4a" for record in units)


def test_bounded_execution_skips_completed_units_from_local_ledger(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = load_scaleout_config()
    registry_path = _registry_with_accepted_2024(tmp_path)
    alpha_data_root = tmp_path / "alpha_data"
    canonical_root = tmp_path / "canonical"
    calls: list[str] = []
    registry_records: dict[str, _FakeFeatureRecord] = {}

    class _FakeFeatureStore:
        def resolve_feature(self, feature_version_id: str) -> _FakeFeatureRecord | None:
            return registry_records.get(feature_version_id)

    monkeypatch.setattr(
        scaleout_driver.FeatureStore,
        "from_alpha_data_root",
        lambda _root: _FakeFeatureStore(),
    )

    def fake_executor(
        _config,
        unit,
        alpha_root: Path,
        _registry: Path,
        _canonical: Path,
    ) -> MaterializedUnitEvidence:
        calls.append(unit.unit_id)
        parquet_path = alpha_root / "fake_values" / f"{unit.unit_id}.parquet"
        parquet_path.parent.mkdir(parents=True, exist_ok=True)
        parquet_path.write_text("synthetic parquet placeholder\n", encoding="utf-8")
        feature_version_id = f"fver_{unit.unit_id.removeprefix('mbu_')}"
        content_hash = "sha256:" + "a" * 64
        registry_records[feature_version_id] = _FakeFeatureRecord(
            parquet_path=parquet_path.as_posix(),
            content_hash=content_hash,
            row_count=11,
        )
        return MaterializedUnitEvidence(
            parquet_path=parquet_path.as_posix(),
            content_hash=content_hash,
            row_count=11,
            feature_version_ids=(feature_version_id,),
        )

    first = run_scaleout(
        config,
        alpha_data_root=alpha_data_root,
        dataset_registry_path=registry_path,
        canonical_root=canonical_root,
        rollout="bounded-real",
        execute=True,
        unit_executor=fake_executor,
    )
    second = run_scaleout(
        config,
        alpha_data_root=alpha_data_root,
        dataset_registry_path=registry_path,
        canonical_root=canonical_root,
        rollout="bounded-real",
        execute=True,
        unit_executor=fake_executor,
    )

    assert first.completed_count == 3
    assert first.failed_count == 0
    assert second.skipped_count == 3
    assert second.completed_count == 0
    assert calls == [record.unit.unit_id for record in first.records]
    ledger = (
        alpha_data_root
        / "materialization/futures_substrate_scaleout_v1/checkpoints/features/base_ohlcv/completed_units.jsonl"
    )
    assert ledger.exists()
    assert len(ledger.read_text(encoding="utf-8").splitlines()) == 3


def test_force_recompute_bypasses_completed_unit_resume(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = load_scaleout_config()
    registry_path = _registry_with_accepted_2024(tmp_path)
    alpha_data_root = tmp_path / "alpha_data"
    canonical_root = tmp_path / "canonical"
    calls: list[str] = []
    registry_records: dict[str, _FakeFeatureRecord] = {}

    class _FakeFeatureStore:
        def resolve_feature(self, feature_version_id: str) -> _FakeFeatureRecord | None:
            return registry_records.get(feature_version_id)

    monkeypatch.setattr(
        scaleout_driver.FeatureStore,
        "from_alpha_data_root",
        lambda _root: _FakeFeatureStore(),
    )

    def fake_executor(
        _config,
        unit,
        alpha_root: Path,
        _registry: Path,
        _canonical: Path,
    ) -> MaterializedUnitEvidence:
        calls.append(unit.unit_id)
        parquet_path = alpha_root / "fake_values" / f"{unit.unit_id}.parquet"
        parquet_path.parent.mkdir(parents=True, exist_ok=True)
        parquet_path.write_text("synthetic parquet placeholder\n", encoding="utf-8")
        feature_version_id = f"fver_{unit.unit_id.removeprefix('mbu_')}"
        content_hash = "sha256:" + "b" * 64
        registry_records[feature_version_id] = _FakeFeatureRecord(
            parquet_path=parquet_path.as_posix(),
            content_hash=content_hash,
            row_count=17,
        )
        return MaterializedUnitEvidence(
            parquet_path=parquet_path.as_posix(),
            content_hash=content_hash,
            row_count=17,
            feature_version_ids=(feature_version_id,),
        )

    target = scaleout_driver.ScaleoutTarget(
        feature_ids=("returns",),
        symbols=("ES",),
        years=(2024,),
    )
    first = run_scaleout(
        config,
        alpha_data_root=alpha_data_root,
        dataset_registry_path=registry_path,
        canonical_root=canonical_root,
        rollout="bounded-real",
        execute=True,
        unit_executor=fake_executor,
        target=target,
    )
    second = run_scaleout(
        config,
        alpha_data_root=alpha_data_root,
        dataset_registry_path=registry_path,
        canonical_root=canonical_root,
        rollout="bounded-real",
        execute=True,
        unit_executor=fake_executor,
        target=target,
        force_recompute=True,
    )

    assert first.completed_count == 1
    assert first.skipped_count == 0
    assert first.force_recompute is False
    assert second.completed_count == 1
    assert second.skipped_count == 0
    assert second.force_recompute is True
    assert calls == [first.records[0].unit.unit_id, first.records[0].unit.unit_id]


class _FakeFeatureRecord:
    def __init__(self, *, parquet_path: str, content_hash: str, row_count: int) -> None:
        self.parquet_path = parquet_path
        self.value_content_hash = content_hash
        self.value_record_count = row_count
        self.producer_engine_id = "alpha_system.features.fast.pack_materializer.v1"


def _registry_with_accepted_2024(tmp_path: Path) -> Path:
    registry_path = tmp_path / "registry" / "datasets.sqlite"
    quality = _quality_report(DATASET_ID_2024)
    coverage = _coverage_report(DATASET_ID_2024)
    dataset_version = DatasetVersion(
        dataset_version_id=DATASET_ID_2024,
        source="dsrc_databento_historical",
        symbol_universe=("ES", "NQ", "RTY"),
        bar_size="1 min",
        what_to_show="TRADES",
        start_ts=datetime(2024, 1, 1, tzinfo=UTC),
        end_ts=datetime(2025, 1, 1, tzinfo=UTC),
        contract_universe=("ES", "NQ", "RTY"),
        roll_policy_id="roll_cme_index_futures_quarterly",
        manifest_hash=HASH_0,
        code_hash=HASH_1,
        config_hash=HASH_2,
        quality_report_hash=compute_quality_report_hash(quality),
        created_at=datetime(2026, 6, 8, tzinfo=UTC),
    )
    persist_dataset_version(
        registry_path,
        dataset_version,
        quality_report=quality,
        coverage_report=coverage,
        source_manifest={"manifest_hash": HASH_0},
        code_hash=HASH_1,
        config_hash=HASH_2,
    )
    policy = _acceptance_policy()
    lock = build_dataset_acceptance_lock(
        dataset_version,
        policy=policy,
        coverage_evidence=_acceptance_evidence(),
        schema_id="ohlcv_1m",
        year=2024,
        locked_at="2026-06-08T00:00:00+00:00",
    )
    inventory = DatasetAcceptanceInventory(
        policy_id="dataset_acceptance_futsub_p02_v1",
        policy_hash=compute_dataset_acceptance_policy_hash(policy),
        locks=(lock,),
        missing_expected_versions=(),
        duplicate_expected_versions=(),
    )
    persist_dataset_acceptance_locks(registry_path, inventory)
    return registry_path


def _quality_report(dataset_version_id: str) -> DataQualityReport:
    return DataQualityReport(
        quality_report_id=f"qr_{dataset_version_id}",
        dataset_version_id=dataset_version_id,
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


def _coverage_report(dataset_version_id: str) -> CoverageReport:
    return CoverageReport(
        coverage_report_id=f"cr_{dataset_version_id}",
        dataset_version_id=dataset_version_id,
        symbol_coverage=_coverage_summary(),
        contract_coverage=_coverage_summary(),
        session_coverage=_coverage_summary(),
        partition_coverage=_coverage_summary(),
        missing_intervals=(),
        incomplete_chunks=(),
    )


def _passing_summary() -> dict[str, object]:
    return {"count": 0, "status": ReportStatus.PASSING.value, "blocking": False}


def _coverage_summary() -> dict[str, object]:
    return {
        "status": ReportStatus.PASSING.value,
        "blocking": False,
        "expected_count": 1,
        "observed_count": 1,
        "missing_count": 0,
        "missing_interval_count": 0,
        "incomplete_chunk_count": 0,
    }


def _acceptance_policy() -> dict[str, object]:
    return {
        "policy_id": "dataset_acceptance_futsub_p02_v1",
        "expected_source": "dsrc_databento_historical",
        "expected_symbols": ["ES", "NQ", "RTY"],
        "expected_years": [2024],
        "expected_schemas": {
            "ohlcv_1m": {"bar_size": "1 min", "what_to_show": "TRADES"}
        },
        "partial_year_end_ts": {},
        "required_registry_metadata_keys": [],
        "canonical_partition_schemas": {"ohlcv_1m": "ohlcv_1m"},
        "row_count_warning_floor_ratio": 0.95,
        "row_count_blocking_floor_ratio": 0.90,
        "minute_coverage_warning_floor_ratio": 0.95,
        "minute_coverage_blocking_floor_ratio": 0.90,
        "trading_day_floor_ratio": 0.75,
        "quality_flag_warning_ratio": 0.10,
        "roll_metadata_required": False,
        "missing_evidence_policy": "BLOCKED",
    }


def _acceptance_evidence() -> dict[str, object]:
    return {
        "evidence_source": "synthetic_scaleout_unit_test",
        "row_count_sanity": {
            "status": ReportStatus.PASSING.value,
            "expected_bar_count": 1,
            "observed_bar_count": 1,
        },
        "gap_coverage": {
            "status": ReportStatus.PASSING.value,
            "gap_count": 0,
        },
        "required_field_presence": {
            "status": ReportStatus.PASSING.value,
            "present_field_groups": [
                "canonical_timestamps",
                "available_ts",
                "exchange_trade_date",
                "session_segment",
                "continuous_provenance",
                "roll_boundary_metadata",
                "quality_flags",
                "missingness_flags",
            ],
            "missing_field_groups": [],
        },
        "missingness_quality_flags": {
            "status": ReportStatus.PASSING.value,
            "quality_flag_fields_present": True,
            "missingness_flag_fields_present": True,
        },
        "continuous_provenance": {
            "status": ReportStatus.PASSING.value,
            "series_ids": ["ES.v.0", "NQ.v.0", "RTY.v.0"],
            "provider_continuous": True,
            "unadjusted": True,
        },
        "roll_metadata": {
            "status": ReportStatus.PASSING.value,
            "roll_policy_id": "roll_cme_index_futures_quarterly",
            "roll_boundary_evidence": "synthetic_present",
        },
    }
