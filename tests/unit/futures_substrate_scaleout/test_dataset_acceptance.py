from __future__ import annotations

import json
import socket
from datetime import UTC, datetime
from pathlib import Path

import pytest

from alpha_system.core.hashing import hash_config
from alpha_system.data.foundation.datasets import (
    DATASET_ACCEPTANCE_REQUIRED_FIELD_GROUPS,
    CoverageReport,
    DataQualityReport,
    DatasetAcceptanceState,
    DatasetVersion,
    ReportStatus,
    _coverage_evidence_from_registry_metadata,
    build_dataset_acceptance_lock,
    compute_quality_report_hash,
    inventory_dataset_acceptance_locks,
    persist_dataset_acceptance_locks,
    resolve_dataset_acceptance_lock,
)
from alpha_system.data.foundation.version_registry import (
    persist_dataset_version,
    resolve_dataset_version,
)

FIXTURE_POLICY = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "futures_substrate_scaleout"
    / "dataset_acceptance"
    / "policy_minimal.json"
)
START_TS = datetime(2024, 1, 1, tzinfo=UTC)
END_TS = datetime(2025, 1, 1, tzinfo=UTC)
CREATED_AT = datetime(2026, 6, 7, 23, 52, 9, tzinfo=UTC)
LOCKED_AT = "2026-06-08T00:00:00+00:00"


def _policy() -> dict[str, object]:
    return json.loads(FIXTURE_POLICY.read_text(encoding="utf-8"))


def _quality_summary(sample_key: str) -> dict[str, object]:
    return {
        "count": 0,
        "status": ReportStatus.PASSING.value,
        "blocking": False,
        sample_key: [],
    }


def _quality_report(dataset_version_id: str) -> DataQualityReport:
    return DataQualityReport.from_mapping(
        {
            "quality_report_id": f"dqr_{dataset_version_id}",
            "dataset_version_id": dataset_version_id,
            "gap_summary": _quality_summary("sample_gaps"),
            "duplicate_summary": _quality_summary("sample_duplicates"),
            "non_monotonic_summary": _quality_summary("sample_pairs"),
            "ohlc_errors": _quality_summary("sample_errors"),
            "zero_negative_price_errors": _quality_summary("sample_errors"),
            "zero_volume_anomalies": _quality_summary("sample_anomalies"),
            "dst_anomalies": _quality_summary("sample_anomalies"),
            "session_coverage": _quality_summary("sample_sessions"),
            "roll_discontinuities": _quality_summary("sample_rolls"),
            "provider_error_summary": _quality_summary("sample_errors"),
            "bbo_missing_metric": _quality_summary("sample_missing_bbo"),
            "abnormal_spread_summary": _quality_summary("sample_spreads"),
            "status": ReportStatus.PASSING.value,
        }
    )


def _coverage_summary(**overrides: object) -> dict[str, object]:
    summary: dict[str, object] = {
        "status": ReportStatus.PASSING.value,
        "blocking": False,
        "expected_count": 1,
        "observed_count": 1,
        "missing_count": 0,
        "sample_buckets": [],
        "truncated": False,
    }
    summary.update(overrides)
    return summary


def _coverage_report(dataset_version_id: str) -> CoverageReport:
    return CoverageReport.from_mapping(
        {
            "coverage_report_id": f"covr_{dataset_version_id}",
            "dataset_version_id": dataset_version_id,
            "symbol_coverage": _coverage_summary(),
            "contract_coverage": _coverage_summary(),
            "session_coverage": _coverage_summary(),
            "partition_coverage": _coverage_summary(
                missing_interval_count=0,
                incomplete_chunk_count=0,
            ),
            "missing_intervals": [],
            "incomplete_chunks": [],
        }
    )


def _dataset_version(
    dataset_version_id: str = "dsv_acceptance_fixture_2024",
    *,
    start_ts: datetime = START_TS,
    end_ts: datetime = END_TS,
) -> DatasetVersion:
    quality_report = _quality_report(dataset_version_id)
    return DatasetVersion(
        dataset_version_id=dataset_version_id,
        source="dsrc_databento_historical",
        symbol_universe=("ES",),
        bar_size="1 min",
        what_to_show="TRADES",
        start_ts=start_ts,
        end_ts=end_ts,
        contract_universe=("contract_databento_es_v_0_front",),
        roll_policy_id="roll_cme_index_futures_quarterly",
        manifest_hash=hash_config({"manifest": dataset_version_id}),
        code_hash=hash_config({"code": "dataset_acceptance_fixture"}),
        config_hash=hash_config({"config": "dataset_acceptance_fixture"}),
        quality_report_hash=compute_quality_report_hash(quality_report),
        created_at=CREATED_AT,
    )


def _full_evidence(**overrides: object) -> dict[str, object]:
    evidence: dict[str, object] = {
        "evidence_source": "synthetic_unit_fixture",
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
            "present_field_groups": list(DATASET_ACCEPTANCE_REQUIRED_FIELD_GROUPS),
            "missing_field_groups": [],
        },
        "missingness_quality_flags": {
            "status": ReportStatus.PASSING.value,
            "quality_flag_fields_present": True,
            "missingness_flag_fields_present": True,
        },
        "continuous_provenance": {
            "status": ReportStatus.PASSING.value,
            "series_ids": ["ES.v.0"],
            "provider_continuous": True,
            "unadjusted": True,
        },
        "roll_metadata": {
            "status": ReportStatus.PASSING.value,
            "roll_policy_id": "roll_cme_index_futures_quarterly",
            "roll_boundary_evidence": "synthetic_present",
        },
    }
    evidence.update(overrides)
    return evidence


def _canonical_policy(root: Path, *, roll_metadata_required: bool = False) -> dict[str, object]:
    policy = _policy()
    policy["canonical_root"] = root.as_posix()
    policy["canonical_root_subpath"] = "."
    policy["canonical_partition_schemas"] = {"ohlcv_1m": "ohlcv_1m"}
    policy["roll_metadata_required"] = roll_metadata_required
    policy["row_count_warning_floor_ratio"] = 0.95
    policy["row_count_blocking_floor_ratio"] = 0.90
    policy["minute_coverage_warning_floor_ratio"] = 0.95
    policy["minute_coverage_blocking_floor_ratio"] = 0.90
    policy["trading_day_floor_ratio"] = 0.001
    policy["quality_flag_warning_ratio"] = 0.10
    return policy


def _write_canonical_ohlcv_fixture(root: Path, dataset_version_id: str) -> None:
    polars = pytest.importorskip("polars")
    rows = [
        {
            "instrument_id": "ES",
            "contract_id": "contract_databento_es_v_0_front",
            "series_id": "ES.v.0",
            "bar_start_ts": "2024-01-01T23:00:00+00:00",
            "bar_end_ts": "2024-01-01T23:01:00+00:00",
            "event_ts": "2024-01-01T23:01:00+00:00",
            "available_ts": "2024-01-01T23:01:01+00:00",
            "ingested_at": "2024-01-01T23:01:02+00:00",
            "open": "1",
            "high": "1",
            "low": "1",
            "close": "1",
            "volume": "1",
            "source": "dsrc_databento_historical",
            "source_request_id": "req_fixture",
            "data_version": dataset_version_id,
            "quality_flags": [],
            "session_label": "ETH",
        },
        {
            "instrument_id": "ES",
            "contract_id": "contract_databento_es_v_0_front",
            "series_id": "ES.v.0",
            "bar_start_ts": "2024-01-01T23:01:00+00:00",
            "bar_end_ts": "2024-01-01T23:02:00+00:00",
            "event_ts": "2024-01-01T23:02:00+00:00",
            "available_ts": "2024-01-01T23:02:01+00:00",
            "ingested_at": "2024-01-01T23:02:02+00:00",
            "open": "1",
            "high": "1",
            "low": "1",
            "close": "1",
            "volume": "1",
            "source": "dsrc_databento_historical",
            "source_request_id": "req_fixture",
            "data_version": dataset_version_id,
            "quality_flags": [],
            "session_label": "ETH",
        },
    ]
    partition = root / dataset_version_id / "schema=ohlcv_1m" / "root=ES"
    partition.mkdir(parents=True)
    part_path = partition / "part-00000.parquet"
    polars.DataFrame(rows).write_parquet(part_path.as_posix())
    (root / dataset_version_id / "manifest.json").write_text(
        json.dumps(
            {
                "schema": "alpha_system.databento.canonical_manifest.v1",
                "data_version": dataset_version_id,
                "dataset": "GLBX.MDP3",
                "partition_schema": "ohlcv_1m",
                "storage_format": "parquet",
                "row_count": len(rows),
                "paths": [part_path.as_posix()],
                "request_spec_hash": hash_config({"request": "fixture"}),
                "source_manifest_hash": hash_config({"source": "fixture"}),
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _registry_with_dataset(tmp_path: Path) -> Path:
    registry_path = tmp_path / "registry" / "datasets.sqlite"
    dataset_version = _dataset_version()
    quality_report = _quality_report(dataset_version.dataset_version_id)
    coverage_report = _coverage_report(dataset_version.dataset_version_id)
    persist_dataset_version(
        registry_path,
        dataset_version,
        quality_report=quality_report,
        coverage_report=coverage_report,
        source_manifest={"manifest_hash": dataset_version.manifest_hash},
        code_hash=dataset_version.code_hash,
        config_hash=dataset_version.config_hash,
    )
    return registry_path


def test_dataset_acceptance_three_state_mapping() -> None:
    dataset_version = _dataset_version()

    accepted = build_dataset_acceptance_lock(
        dataset_version,
        policy=_policy(),
        coverage_evidence=_full_evidence(),
        locked_at=LOCKED_AT,
    )
    warned = build_dataset_acceptance_lock(
        dataset_version,
        policy=_policy(),
        coverage_evidence=_full_evidence(
            gap_coverage={
                "status": ReportStatus.WARNING.value,
                "gap_count": 0,
                "reason": "synthetic warning threshold",
            }
        ),
        locked_at=LOCKED_AT,
    )
    blocked = build_dataset_acceptance_lock(
        dataset_version,
        policy=_policy(),
        coverage_evidence=_full_evidence(
            required_field_presence={
                "status": ReportStatus.BLOCKING.value,
                "present_field_groups": ["canonical_timestamps"],
                "missing_field_groups": ["available_ts"],
            }
        ),
        locked_at=LOCKED_AT,
    )

    assert accepted.state is DatasetAcceptanceState.ACCEPTED
    assert warned.state is DatasetAcceptanceState.ACCEPTED_WITH_WARNINGS
    assert blocked.state is DatasetAcceptanceState.BLOCKED


def test_canonical_acceptance_evidence_computes_required_dimensions(tmp_path: Path) -> None:
    dataset_version = _dataset_version()
    canonical_root = tmp_path / "canonical"
    _write_canonical_ohlcv_fixture(canonical_root, dataset_version.dataset_version_id)

    evidence = _coverage_evidence_from_registry_metadata(
        dataset_version,
        {
            "continuous_provenance": {
                "provider_continuous": True,
                "front_month": True,
                "unadjusted": True,
                "not_roll_truth": True,
            },
            "partition_contamination_metadata": {"purpose": "data_qa_coverage_inspection"},
        },
        policy=_canonical_policy(canonical_root),
        schema_id="ohlcv_1m",
    )

    assert evidence["row_count_sanity"]["status"] == ReportStatus.PASSING.value
    assert evidence["gap_coverage"]["status"] == ReportStatus.PASSING.value
    assert evidence["required_field_presence"]["status"] == ReportStatus.PASSING.value
    assert evidence["missingness_quality_flags"]["status"] == ReportStatus.PASSING.value
    assert evidence["continuous_provenance"]["status"] == ReportStatus.PASSING.value
    assert evidence["roll_metadata"]["status"] == ReportStatus.PASSING.value
    assert evidence["row_count_sanity"]["manifest_row_count"] == 2

    lock = build_dataset_acceptance_lock(
        dataset_version,
        policy=_canonical_policy(canonical_root),
        coverage_evidence=evidence,
        locked_at=LOCKED_AT,
    )
    assert lock.state is DatasetAcceptanceState.ACCEPTED


def test_roll_metadata_deferred_by_policy_warns_without_blocking(tmp_path: Path) -> None:
    dataset_version = _dataset_version()
    canonical_root = tmp_path / "canonical"
    _write_canonical_ohlcv_fixture(canonical_root, dataset_version.dataset_version_id)

    evidence = _coverage_evidence_from_registry_metadata(
        dataset_version,
        {
            "continuous_provenance": {
                "provider_continuous": True,
                "front_month": True,
                "unadjusted": True,
                "not_roll_truth": True,
            },
        },
        policy=_canonical_policy(canonical_root, roll_metadata_required=True),
        schema_id="ohlcv_1m",
    )
    lock = build_dataset_acceptance_lock(
        dataset_version,
        policy=_canonical_policy(canonical_root, roll_metadata_required=True),
        coverage_evidence=evidence,
        locked_at=LOCKED_AT,
    )

    assert evidence["roll_metadata"]["roll_boundary_evidence"] == "deferred_pending_FUTSUB_P03"
    assert lock.state is DatasetAcceptanceState.ACCEPTED_WITH_WARNINGS
    assert not lock.blocking_reasons


def test_partial_year_maps_to_accepted_with_warnings() -> None:
    policy = _policy()
    policy["expected_years"] = [2026]
    policy["partial_year_end_ts"] = {"2026": "2026-06-01T00:00:00+00:00"}
    policy["roll_metadata_required"] = False

    lock = build_dataset_acceptance_lock(
        _dataset_version(
            "dsv_acceptance_fixture_2026",
            start_ts=datetime(2026, 1, 1, tzinfo=UTC),
            end_ts=datetime(2026, 6, 1, tzinfo=UTC),
        ),
        policy=policy,
        coverage_evidence=_full_evidence(),
        schema_id="ohlcv_1m",
        year=2026,
        locked_at=LOCKED_AT,
    )

    assert lock.state is DatasetAcceptanceState.ACCEPTED_WITH_WARNINGS
    assert any("partial-year" in reason for reason in lock.warning_reasons)


def test_missing_coverage_never_silently_accepts() -> None:
    evidence = _full_evidence()
    evidence.pop("row_count_sanity")

    lock = build_dataset_acceptance_lock(
        _dataset_version(),
        policy=_policy(),
        coverage_evidence=evidence,
        locked_at=LOCKED_AT,
    )

    assert lock.state is DatasetAcceptanceState.BLOCKED
    assert any("row-count" in reason for reason in lock.blocking_reasons)
    assert lock.state is not DatasetAcceptanceState.ACCEPTED


def test_acceptance_inventory_persists_lock_without_network(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls: list[object] = []

    def fail_network(*args: object, **kwargs: object) -> object:
        calls.append((args, kwargs))
        raise AssertionError("network access is forbidden")

    monkeypatch.setattr(socket, "create_connection", fail_network)
    registry_path = _registry_with_dataset(tmp_path)

    inventory = inventory_dataset_acceptance_locks(
        registry_path,
        policy=_policy(),
        locked_at=LOCKED_AT,
    )
    assert len(inventory.locks) == 1
    assert inventory.locks[0].state is DatasetAcceptanceState.BLOCKED

    persist_dataset_acceptance_locks(registry_path, inventory)
    resolved_lock = resolve_dataset_acceptance_lock(
        registry_path,
        "dsv_acceptance_fixture_2024",
    )
    resolved_version = resolve_dataset_version(
        registry_path,
        "dsv_acceptance_fixture_2024",
    )

    assert resolved_lock is not None
    assert resolved_lock.state is DatasetAcceptanceState.BLOCKED
    assert resolved_version is not None
    assert calls == []
