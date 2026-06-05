from __future__ import annotations

from datetime import UTC, datetime

import pytest

from alpha_system.data.foundation.datasets import (
    CoverageReport,
    DataQualityReport,
    DatasetPartitionPlan,
    DatasetVersion,
    ReportStatus,
    compute_quality_report_hash,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.features import (
    ACCEPTED_DATASET_VERSION_STATES,
    AcceptedDatasetVersion,
    canonical_bars_from_mappings,
    resolve_accepted_dataset_version,
)
from alpha_system.features import consumption

HASH_0 = "0" * 64
HASH_1 = "1" * 64
HASH_2 = "2" * 64


def test_import_succeeds() -> None:
    assert "VERSIONED" in ACCEPTED_DATASET_VERSION_STATES
    assert "READY_FOR_RESEARCH" in ACCEPTED_DATASET_VERSION_STATES
    assert AcceptedDatasetVersion is consumption.AcceptedDatasetVersion
    assert callable(resolve_accepted_dataset_version)


def test_admissible_version_resolves_and_reconstructs_canonical_records(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset_id = "dsv_databento_ohlcv_fixture_v1"
    quality_report = _quality_report(dataset_id)
    coverage_report = _coverage_report(dataset_id)
    version = _dataset_version(
        dataset_id,
        source="dsrc_databento_glbx_mdp3",
        quality_report=quality_report,
    )
    calls: list[tuple[object, object]] = []

    def fake_resolve(registry_path: object, dataset_version_id: object) -> DatasetVersion:
        calls.append((registry_path, dataset_version_id))
        return version

    monkeypatch.setattr(consumption, "resolve_dataset_version", fake_resolve)

    accepted = resolve_accepted_dataset_version(
        "synthetic_registry.sqlite",
        dataset_id,
        lifecycle_state="READY_FOR_RESEARCH",
        quality_report=quality_report,
        coverage_report=coverage_report,
        source_manifest={"manifest_hash": version.manifest_hash},
        code_hash=version.code_hash,
        config_hash=version.config_hash,
    )

    assert calls == [("synthetic_registry.sqlite", dataset_id)]
    assert accepted.dataset_version_id == dataset_id
    assert accepted.source == "dsrc_databento_glbx_mdp3"

    bars = accepted.canonical_bars_from_mappings(
        [_bar_mapping(dataset_id)],
        partition_id="development_partition",
        purpose="feature_input",
    )
    bbos = accepted.canonical_bbos_from_mappings(
        [_bbo_mapping(dataset_id)],
        partition_id="development_partition",
        purpose="feature_input",
    )
    dense_bars = accepted.dense_grid_bars_from_mappings(
        [_dense_bar_mapping(dataset_id)],
        partition_id="development_partition",
        purpose="feature_input",
    )

    assert bars[0].data_version == dataset_id
    assert bbos[0].data_version == dataset_id
    assert dense_bars[0].data_version == dataset_id


def test_missing_version_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    dataset_id = "dsv_databento_ohlcv_missing_v1"
    quality_report = _quality_report(dataset_id)
    coverage_report = _coverage_report(dataset_id)

    def fake_resolve(registry_path: object, dataset_version_id: object) -> None:
        return None

    monkeypatch.setattr(consumption, "resolve_dataset_version", fake_resolve)

    with pytest.raises(DataFoundationValidationError, match="not found"):
        resolve_accepted_dataset_version(
            "synthetic_registry.sqlite",
            dataset_id,
            lifecycle_state="VERSIONED",
            quality_report=quality_report,
            coverage_report=coverage_report,
            source_manifest={"manifest_hash": HASH_0},
            code_hash=HASH_1,
            config_hash=HASH_2,
        )


def test_inadmissible_lifecycle_state_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset_id = "dsv_databento_ohlcv_quality_checked_v1"
    quality_report = _quality_report(dataset_id)
    coverage_report = _coverage_report(dataset_id)
    version = _dataset_version(dataset_id, quality_report=quality_report)
    monkeypatch.setattr(consumption, "resolve_dataset_version", lambda *_: version)

    with pytest.raises(DataFoundationValidationError, match="lifecycle_state"):
        resolve_accepted_dataset_version(
            "synthetic_registry.sqlite",
            dataset_id,
            lifecycle_state="QUALITY_CHECKED",
            quality_report=quality_report,
            coverage_report=coverage_report,
            source_manifest={"manifest_hash": version.manifest_hash},
            code_hash=version.code_hash,
            config_hash=version.config_hash,
        )


def test_blocking_quality_or_coverage_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    quality_blocked_id = "dsv_databento_ohlcv_quality_blocked_v1"
    blocking_quality = _quality_report(quality_blocked_id, blocking=True)
    quality_blocked_version = _dataset_version(
        quality_blocked_id,
        quality_report=blocking_quality,
    )
    monkeypatch.setattr(
        consumption,
        "resolve_dataset_version",
        lambda *_: quality_blocked_version,
    )

    with pytest.raises(DataFoundationValidationError, match="blocking DataQualityReport"):
        resolve_accepted_dataset_version(
            "synthetic_registry.sqlite",
            quality_blocked_id,
            lifecycle_state="VERSIONED",
            quality_report=blocking_quality,
            coverage_report=_coverage_report(quality_blocked_id),
            source_manifest={"manifest_hash": quality_blocked_version.manifest_hash},
            code_hash=quality_blocked_version.code_hash,
            config_hash=quality_blocked_version.config_hash,
        )

    coverage_blocked_id = "dsv_databento_ohlcv_coverage_blocked_v1"
    passing_quality = _quality_report(coverage_blocked_id)
    coverage_blocked_version = _dataset_version(
        coverage_blocked_id,
        quality_report=passing_quality,
    )
    monkeypatch.setattr(
        consumption,
        "resolve_dataset_version",
        lambda *_: coverage_blocked_version,
    )

    with pytest.raises(DataFoundationValidationError, match="blocking coverage"):
        resolve_accepted_dataset_version(
            "synthetic_registry.sqlite",
            coverage_blocked_id,
            lifecycle_state="VERSIONED",
            quality_report=passing_quality,
            coverage_report=_coverage_report(coverage_blocked_id, blocking=True),
            source_manifest={"manifest_hash": coverage_blocked_version.manifest_hash},
            code_hash=coverage_blocked_version.code_hash,
            config_hash=coverage_blocked_version.config_hash,
        )


def test_raw_provider_fields_are_rejected_before_records_are_exposed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset_id = "dsv_databento_ohlcv_fixture_v1"
    accepted = _accepted_version(monkeypatch, dataset_id)
    raw_shaped_row = {
        **_bar_mapping(dataset_id),
        "provider_ts": "2024-01-02T14:30:00+00:00",
        "raw_payload": {"close": "100.25"},
    }

    with pytest.raises(DataFoundationValidationError, match="unsupported fields"):
        accepted.canonical_bars_from_mappings(
            [raw_shaped_row],
            partition_id="development_partition",
            purpose="feature_input",
        )

    rows = canonical_bars_from_mappings(
        accepted,
        [_bar_mapping(dataset_id)],
        partition_id="development_partition",
        purpose="feature_input",
    )
    assert not hasattr(rows[0], "provider_ts")
    assert not hasattr(rows[0], "raw_payload")


def test_record_data_version_must_match_accepted_dataset_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    accepted = _accepted_version(monkeypatch, "dsv_databento_ohlcv_fixture_v1")

    with pytest.raises(DataFoundationValidationError, match="data_version"):
        accepted.canonical_bars_from_mappings(
            [_bar_mapping("dsv_databento_ohlcv_other_v1")],
            partition_id="development_partition",
            purpose="feature_input",
        )


def test_locked_partition_use_without_contamination_metadata_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset_id = "dsv_databento_ohlcv_fixture_v1"
    accepted = _accepted_version(monkeypatch, dataset_id)
    plan = DatasetPartitionPlan.canonical()

    with pytest.raises(DataFoundationValidationError, match="Governance contamination"):
        accepted.canonical_bars_from_mappings(
            [_bar_mapping(dataset_id)],
            partition_id="locked_test_candidate",
            purpose="feature_input",
            partition_plan=plan,
        )

    rows = accepted.canonical_bars_from_mappings(
        [_bar_mapping(dataset_id)],
        partition_id="locked_test_candidate",
        purpose="feature_input",
        governance_metadata={
            "study_id": "study_fixture",
            "contamination_record_id": "locked_test_contamination_fixture",
            "reason": "synthetic test records locked-partition access",
        },
        partition_plan=plan,
    )

    assert len(rows) == 1


def test_databento_and_ibkr_dataset_versions_remain_distinct(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    databento_id = "dsv_databento_ohlcv_fixture_v1"
    ibkr_id = "dsv_ibkr_recent_validation_fixture_v1"
    databento_quality = _quality_report(databento_id)
    ibkr_quality = _quality_report(ibkr_id)
    versions = {
        databento_id: _dataset_version(
            databento_id,
            source="dsrc_databento_glbx_mdp3",
            quality_report=databento_quality,
        ),
        ibkr_id: _dataset_version(
            ibkr_id,
            source="dsrc_ibkr_historical",
            quality_report=ibkr_quality,
        ),
    }

    def fake_resolve(registry_path: object, dataset_version_id: object) -> DatasetVersion:
        return versions[str(dataset_version_id)]

    monkeypatch.setattr(consumption, "resolve_dataset_version", fake_resolve)

    databento = resolve_accepted_dataset_version(
        "synthetic_registry.sqlite",
        databento_id,
        lifecycle_state="VERSIONED",
        quality_report=databento_quality,
        coverage_report=_coverage_report(databento_id),
        source_manifest={"manifest_hash": versions[databento_id].manifest_hash},
        code_hash=versions[databento_id].code_hash,
        config_hash=versions[databento_id].config_hash,
    )
    ibkr = resolve_accepted_dataset_version(
        "synthetic_registry.sqlite",
        ibkr_id,
        lifecycle_state="VERSIONED",
        quality_report=ibkr_quality,
        coverage_report=_coverage_report(ibkr_id),
        source_manifest={"manifest_hash": versions[ibkr_id].manifest_hash},
        code_hash=versions[ibkr_id].code_hash,
        config_hash=versions[ibkr_id].config_hash,
    )

    assert databento.dataset_version_id == databento_id
    assert ibkr.dataset_version_id == ibkr_id
    assert databento.source != ibkr.source


def _accepted_version(
    monkeypatch: pytest.MonkeyPatch,
    dataset_id: str,
    *,
    source: str = "dsrc_databento_glbx_mdp3",
) -> AcceptedDatasetVersion:
    quality_report = _quality_report(dataset_id)
    coverage_report = _coverage_report(dataset_id)
    version = _dataset_version(dataset_id, source=source, quality_report=quality_report)
    monkeypatch.setattr(consumption, "resolve_dataset_version", lambda *_: version)
    return resolve_accepted_dataset_version(
        "synthetic_registry.sqlite",
        dataset_id,
        lifecycle_state="VERSIONED",
        quality_report=quality_report,
        coverage_report=coverage_report,
        source_manifest={"manifest_hash": version.manifest_hash},
        code_hash=version.code_hash,
        config_hash=version.config_hash,
    )


def _dataset_version(
    dataset_id: str,
    *,
    source: str = "dsrc_databento_glbx_mdp3",
    quality_report: DataQualityReport,
) -> DatasetVersion:
    return DatasetVersion(
        dataset_version_id=dataset_id,
        source=source,
        symbol_universe=("ES", "NQ", "RTY"),
        bar_size="1 min",
        what_to_show="TRADES",
        start_ts=datetime(2024, 1, 2, 14, 30, tzinfo=UTC),
        end_ts=datetime(2024, 1, 2, 14, 31, tzinfo=UTC),
        contract_universe=("ESM4", "NQM4", "RTYM4"),
        roll_policy_id="roll_policy_fixture",
        manifest_hash=HASH_0,
        code_hash=HASH_1,
        config_hash=HASH_2,
        quality_report_hash=compute_quality_report_hash(quality_report),
        created_at=datetime(2024, 1, 2, 15, 0, tzinfo=UTC),
    )


def _quality_report(dataset_id: str, *, blocking: bool = False) -> DataQualityReport:
    gap_summary = _quality_summary(blocking=blocking)
    return DataQualityReport(
        quality_report_id=f"qr_{dataset_id}",
        dataset_version_id=dataset_id,
        gap_summary=gap_summary,
        duplicate_summary=_quality_summary(),
        non_monotonic_summary=_quality_summary(),
        ohlc_errors=_quality_summary(),
        zero_negative_price_errors=_quality_summary(),
        zero_volume_anomalies=_quality_summary(),
        dst_anomalies=_quality_summary(),
        session_coverage=_quality_summary(),
        roll_discontinuities=_quality_summary(),
        provider_error_summary=_quality_summary(),
        bbo_missing_metric=_quality_summary(),
        abnormal_spread_summary=_quality_summary(),
        status=ReportStatus.BLOCKING if blocking else ReportStatus.PASSING,
    )


def _quality_summary(*, blocking: bool = False) -> dict[str, object]:
    return {
        "count": 1 if blocking else 0,
        "status": ReportStatus.BLOCKING.value if blocking else ReportStatus.PASSING.value,
        "blocking": blocking,
    }


def _coverage_report(dataset_id: str, *, blocking: bool = False) -> CoverageReport:
    missing_intervals = (
        {
            "start_ts": "2024-01-02T14:30:00+00:00",
            "end_ts": "2024-01-02T14:31:00+00:00",
            "status": ReportStatus.BLOCKING.value,
        },
    ) if blocking else ()
    return CoverageReport(
        coverage_report_id=f"cr_{dataset_id}",
        dataset_version_id=dataset_id,
        symbol_coverage=_coverage_summary(),
        contract_coverage=_coverage_summary(),
        session_coverage=_coverage_summary(),
        partition_coverage=_coverage_summary(
            blocking=blocking,
            include_partition_counts=True,
        ),
        missing_intervals=missing_intervals,
        incomplete_chunks=(),
    )


def _coverage_summary(
    *,
    blocking: bool = False,
    include_partition_counts: bool = False,
) -> dict[str, object]:
    summary: dict[str, object] = {
        "status": ReportStatus.BLOCKING.value if blocking else ReportStatus.PASSING.value,
        "blocking": blocking,
        "expected_count": 1,
        "observed_count": 0 if blocking else 1,
        "missing_count": 1 if blocking else 0,
    }
    if include_partition_counts:
        summary["missing_interval_count"] = 1 if blocking else 0
        summary["incomplete_chunk_count"] = 0
    return summary


def _bar_mapping(dataset_id: str) -> dict[str, object]:
    return {
        "instrument_id": "ES",
        "contract_id": "ESM4",
        "series_id": "ES_CONTINUOUS",
        "bar_start_ts": "2024-01-02T14:30:00+00:00",
        "bar_end_ts": "2024-01-02T14:31:00+00:00",
        "event_ts": "2024-01-02T14:31:00+00:00",
        "available_ts": "2024-01-02T14:31:01+00:00",
        "ingested_at": "2024-01-02T14:31:02+00:00",
        "open": "100.00",
        "high": "101.00",
        "low": "99.50",
        "close": "100.25",
        "volume": "10",
        "source": "dsrc_databento_glbx_mdp3",
        "source_request_id": "req_fixture_1",
        "data_version": dataset_id,
        "quality_flags": (),
        "session_label": "ETH",
    }


def _bbo_mapping(dataset_id: str) -> dict[str, object]:
    return {
        "instrument_id": "ES",
        "contract_id": "ESM4",
        "series_id": "ES_CONTINUOUS",
        "bar_start_ts": "2024-01-02T14:30:00+00:00",
        "bar_end_ts": "2024-01-02T14:31:00+00:00",
        "event_ts": "2024-01-02T14:31:00+00:00",
        "available_ts": "2024-01-02T14:31:01+00:00",
        "ingested_at": "2024-01-02T14:31:02+00:00",
        "bid": "99.50",
        "ask": "100.50",
        "bid_size": "4",
        "ask_size": "6",
        "mid": "100.00",
        "spread": "1.00",
        "source": "dsrc_databento_glbx_mdp3",
        "source_request_id": "req_fixture_1",
        "data_version": dataset_id,
        "quality_flags": (),
        "session_label": "ETH",
        "spread_ticks": "4",
        "microprice": "100.10",
        "bid_order_count": 2,
        "ask_order_count": 3,
    }


def _dense_bar_mapping(dataset_id: str) -> dict[str, object]:
    row = _bar_mapping(dataset_id)
    row.update(
        {
            "has_trade": True,
            "synthetic": False,
            "fill_method": None,
            "provider_bar_ref": "provider_bar_ref_fixture",
        }
    )
    return row
