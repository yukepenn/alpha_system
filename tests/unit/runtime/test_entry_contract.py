from __future__ import annotations

from dataclasses import replace

import pytest

from alpha_system.governance.study_input_pack import StudyInputPack
from alpha_system.runtime import entry_contract
from alpha_system.runtime.entry_contract import (
    RuntimeEntryRequest,
    RuntimeEntryStatus,
    evaluate_runtime_entry_request,
)

ALPHA_SPEC_REF = "aspec_af848bc999a4c4b11a421bd0"
STUDY_SPEC_REF = "sspec_438ceffd40855205de5497f0"
FEATURE_REQUEST_REF = "freq_eb180e1226ce34c048c7e6eb"
LABEL_SPEC_REF = "lspec_8663589ca7a9f1e5859289c7"
DATASET_VERSION_ID = "dsv_synthetic_feature_label_fixture_v1"
DATASET_SCOPE = {
    "instrument_universe": "SYNTH_US_EQUITY_LARGE_CAP fixture universe only",
    "source": "tiny synthetic governance fixture metadata, not real market data",
    "time_range": "2026-01-01 through 2026-01-31 synthetic timestamps",
}


def test_well_formed_reference_request_resolves_without_data_access() -> None:
    request = _valid_request()

    result = evaluate_runtime_entry_request(request)

    assert result.status is RuntimeEntryStatus.INPUTS_RESOLVED
    assert result.resolved
    assert result.study_input_pack == request.study_input_pack
    assert result.target_dataset_version_id == DATASET_VERSION_ID
    assert result.reasons[0].code == "runtime_entry_references_resolved"


@pytest.mark.parametrize(
    ("field", "expected_code"),
    [
        ("alpha_spec_ref", "missing_alpha_spec_ref"),
        ("study_spec_ref", "missing_study_spec_ref"),
    ],
)
def test_missing_alpha_or_study_spec_reference_blocks(
    field: str,
    expected_code: str,
) -> None:
    request = replace(_valid_request(), **{field: None})

    result = evaluate_runtime_entry_request(request)

    assert result.status is RuntimeEntryStatus.INPUTS_BLOCKED
    assert result.blocked
    assert expected_code in _reason_codes(result)


@pytest.mark.parametrize(
    ("replacement", "expected_code"),
    [
        ({"raw_provider_source": "databento"}, "raw_provider_source_requested"),
        ({"external_provider_call_requested": True}, "external_provider_call_requested"),
        ({"raw_file_path": "raw/provider/es_ohlcv.dbn.zst"}, "raw_provider_file_requested"),
        (
            {"dataset_scope": {**DATASET_SCOPE, "raw_path": "raw/provider/es.parquet"}},
            "raw_provider_file_requested",
        ),
    ],
)
def test_raw_provider_or_external_call_request_blocks(
    replacement: dict[str, object],
    expected_code: str,
) -> None:
    request = replace(_valid_request(), **replacement)

    result = evaluate_runtime_entry_request(request)

    assert result.status is RuntimeEntryStatus.INPUTS_BLOCKED
    assert expected_code in _reason_codes(result)


@pytest.mark.parametrize(
    ("field", "expected_code"),
    [
        ("target_dataset_version_id", "missing_target_dataset_version_id"),
        ("dataset_scope", "missing_dataset_scope"),
    ],
)
def test_missing_dataset_version_or_scope_blocks(field: str, expected_code: str) -> None:
    request = replace(_valid_request(), **{field: None})

    result = evaluate_runtime_entry_request(request)

    assert result.status is RuntimeEntryStatus.INPUTS_BLOCKED
    assert expected_code in _reason_codes(result)


def test_under_determined_locked_test_request_is_inconclusive() -> None:
    request = replace(
        _valid_request(),
        partition_scope={"partition_id": "locked_test_candidate"},
    )

    result = evaluate_runtime_entry_request(request)

    assert result.status is RuntimeEntryStatus.INPUTS_INCONCLUSIVE
    assert result.inconclusive
    assert "locked_test_governance_metadata_missing" in _reason_codes(result)


def test_study_input_pack_is_consumed_from_governance() -> None:
    request = _valid_request()

    result = evaluate_runtime_entry_request(request)

    assert entry_contract.StudyInputPack is StudyInputPack
    assert isinstance(result.study_input_pack, StudyInputPack)
    assert result.study_input_pack.alpha_spec_id == ALPHA_SPEC_REF


def _valid_request() -> RuntimeEntryRequest:
    return RuntimeEntryRequest(
        alpha_spec_ref=ALPHA_SPEC_REF,
        study_spec_ref=STUDY_SPEC_REF,
        study_input_pack=StudyInputPack(
            feature_request_ids=[FEATURE_REQUEST_REF],
            label_spec_ids=[LABEL_SPEC_REF],
            alpha_spec_id=ALPHA_SPEC_REF,
            dataset_scope=DATASET_SCOPE,
        ),
        target_dataset_version_id=DATASET_VERSION_ID,
        dataset_scope=DATASET_SCOPE,
        partition_scope={"partition_id": "development_partition"},
        expected_dataset_lifecycle_state="VERSIONED",
        dataset_version_source_family="databento",
    )


def _reason_codes(result: object) -> set[str]:
    return {reason.code for reason in result.reasons}
