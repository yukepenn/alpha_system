from __future__ import annotations

import pytest

from alpha_system.data.foundation.dry_run import (
    PROHIBITED_MVP_STATES,
    assert_lifecycle_blocks_fail_closed,
    run_synthetic_data_foundation_dry_run,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError

EXPECTED_BLOCK_IDS = {
    "missing_manifest_blocks_provider_pull",
    "reserved_client_ids_block_connection",
    "client_ids_outside_201_209_fail_closed",
    "missing_pacing_guard_blocks_pull",
    "missing_local_data_root_policy_blocks_raw_writes",
    "missing_available_ts_blocks_canonicalization",
    "available_ts_before_bar_end_blocks_canonicalization",
    "quality_gap_blocks_versioning",
    "incomplete_chunk_blocks_versioning",
    "prohibited_mvp_states_unreachable",
    "order_account_methods_unreachable_from_data_boundary",
}


def test_data_p24_lifecycle_blocks_fail_closed() -> None:
    assertions = assert_lifecycle_blocks_fail_closed()
    by_id = {assertion.block_id: assertion for assertion in assertions}

    assert set(by_id) == EXPECTED_BLOCK_IDS
    assert all(assertion.blocked for assertion in assertions)
    assert "HistoricalRequestManifest" in by_id["missing_manifest_blocks_provider_pull"].reason
    assert "101" in by_id["reserved_client_ids_block_connection"].reason
    assert "201-209" in by_id["client_ids_outside_201_209_fail_closed"].reason
    assert "RequestPacingPolicy" in by_id["missing_pacing_guard_blocks_pull"].reason
    assert "LocalDataRootPolicy" in by_id["missing_local_data_root_policy_blocks_raw_writes"].reason
    assert "available_ts" in by_id["missing_available_ts_blocks_canonicalization"].reason
    assert "blocking DataQualityReport" in by_id["quality_gap_blocks_versioning"].reason
    assert "blocking coverage report" in by_id["incomplete_chunk_blocks_versioning"].reason
    for state in PROHIBITED_MVP_STATES:
        assert state in by_id["prohibited_mvp_states_unreachable"].reason
    assert (
        "refuses API method" in by_id["order_account_methods_unreachable_from_data_boundary"].reason
    )


@pytest.mark.parametrize("mode", ["smoke", "authorized_pull"])
def test_data_p24_dry_run_rejects_external_access_modes(mode: str) -> None:
    with pytest.raises(DataFoundationValidationError, match="dry_run or synthetic"):
        run_synthetic_data_foundation_dry_run(access_mode=mode)


def test_data_p24_dry_run_dry_run_mode_still_forbids_external_api() -> None:
    summary = run_synthetic_data_foundation_dry_run(access_mode="dry_run")

    assert summary.access_mode == "dry_run"
    assert summary.allows_external_api is False
    assert summary.external_call_attempted is False
