from __future__ import annotations

from pathlib import Path

from alpha_system.data.foundation.dry_run import run_synthetic_data_foundation_dry_run


def test_data_p24_synthetic_end_to_end_dry_run_round_trips_registry(
    tmp_path: Path,
) -> None:
    summary = run_synthetic_data_foundation_dry_run(
        registry_path=tmp_path / "data_p24_synthetic_registry.sqlite"
    )

    assert summary.status == "SYNTHETIC_COMPLETE"
    assert summary.access_mode == "synthetic"
    assert summary.allows_external_api is False
    assert summary.external_call_attempted is False
    assert summary.client_id == 201
    assert summary.manifest_id == "hrm_synthetic_ibkr_e2e_v1"
    assert summary.pacing_policy_id == "rpp_ibkr_historical_conservative_tobeverified_v1"
    assert summary.chunk_count == 1
    assert summary.completed_chunk_count == 1
    assert summary.pending_resume_chunk_count == 0
    assert summary.raw_object_count == 1
    assert summary.parsed_bar_count == 3
    assert summary.canonical_bar_count == 3
    assert summary.quality_status == "PASSING"
    assert summary.coverage_status == "PASSING"
    assert summary.registry_round_trip is True
    assert "development_partition" in summary.partition_ids
    assert summary.read_only_boundary_confirmed is True
    assert summary.prohibited_states_unreachable is True
    assert set(summary.reproducibility_hashes) == {
        "manifest_hash",
        "code_hash",
        "config_hash",
        "quality_report_hash",
    }
    assert all(assertion.blocked for assertion in summary.lifecycle_blocks)


def test_data_p24_dry_run_summary_is_aggregate_only() -> None:
    summary = run_synthetic_data_foundation_dry_run()
    payload = summary.to_mapping()

    assert "historical_bars_csv" not in payload
    assert "raw_payload" not in payload
    assert "canonical_bars" not in payload
    assert payload["raw_object_count"] == 1
    assert payload["canonical_bar_count"] == 3
