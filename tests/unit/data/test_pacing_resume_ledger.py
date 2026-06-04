from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pytest

from alpha_system.data.foundation.requests import (
    HistoricalChunkRecord,
    HistoricalChunkStatus,
    HistoricalPullLedger,
    HistoricalPullLedgerStatus,
    ProviderErrorRecord,
    ProviderErrorResolution,
    RequestPacingPolicy,
    forbid_naive_request_loop,
    provider_pull_pacing_guard,
    require_pacing_policy_for_provider_pull,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError

ROOT = Path(__file__).resolve().parents[3]
POLICY_PATH = ROOT / "configs" / "data" / "request_pacing_policy_to_be_verified.json"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "data" / "synthetic_pacing_resume_chunks.json"

START_TS = datetime(2025, 1, 2, 14, 30, tzinfo=UTC)
MID_TS = datetime(2025, 1, 3, 0, 0, tzinfo=UTC)
END_TS = datetime(2025, 1, 3, 22, 0, tzinfo=UTC)
RETRIEVED_AT = datetime(2026, 6, 3, 21, 52, 49, tzinfo=UTC)
RAW_A = "raw://sha256/" + "a" * 64
RAW_B = "raw://sha256/" + "b" * 64


def _deepcopy_mapping(values: Mapping[str, object]) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(json.dumps(values)))


def _policy_values(**overrides: object) -> dict[str, Any]:
    values = _deepcopy_mapping(
        cast(Mapping[str, object], json.loads(POLICY_PATH.read_text(encoding="utf-8")))
    )
    values.update(overrides)
    return values


def _chunk_values(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "chunk_id": "hchunk_synth_es_20250102_a",
        "request_spec_id": "hrs_synthetic_es_h5_20250102_20250103",
        "symbol_root": "ES",
        "contract_ref": "fcr_synthetic_es_h5",
        "start_ts": START_TS.isoformat(),
        "end_ts": MID_TS.isoformat(),
        "status": "COMPLETE",
        "attempt_count": 1,
        "provider_request_id": "ibkr_req_synth_001",
        "raw_object_ref": RAW_A,
        "row_count": 10,
        "error_ref": None,
        "retrieved_at": RETRIEVED_AT.isoformat(),
    }
    values.update(overrides)
    return values


def test_pacing_policy_requires_guard_and_to_be_verified_source() -> None:
    policy = RequestPacingPolicy.from_mapping(_policy_values())

    assert policy.source["verification_status"] == "to_be_verified"
    assert policy.accounting_weight("TRADES") == 1
    assert policy.accounting_weight("BID_ASK") == 2
    assert policy.backoff_delay_seconds(3) == 8.0
    assert require_pacing_policy_for_provider_pull(policy) is policy
    assert provider_pull_pacing_guard(policy) is True
    assert forbid_naive_request_loop(policy) is True

    with pytest.raises(DataFoundationValidationError, match="missing RequestPacingPolicy"):
        require_pacing_policy_for_provider_pull(None)
    assert provider_pull_pacing_guard(None) is False

    with pytest.raises(DataFoundationValidationError, match="positive finite"):
        RequestPacingPolicy.from_mapping(_policy_values(min_seconds_between_identical_requests=0))
    with pytest.raises(DataFoundationValidationError, match="bid_ask_counts_double"):
        RequestPacingPolicy.from_mapping(_policy_values(bid_ask_counts_double=False))

    bad_source = _policy_values()
    bad_source["source"]["verification_status"] = "verified"
    with pytest.raises(DataFoundationValidationError, match="to_be_verified"):
        RequestPacingPolicy.from_mapping(bad_source)


def test_chunk_record_statuses_attempts_provider_ids_and_raw_refs() -> None:
    not_started = HistoricalChunkRecord.from_mapping(
        _chunk_values(
            status="not-started",
            attempt_count=0,
            provider_request_id=None,
            raw_object_ref=None,
            row_count=None,
            error_ref=None,
            retrieved_at=None,
        )
    )
    complete = HistoricalChunkRecord.from_mapping(_chunk_values())

    assert not_started.status is HistoricalChunkStatus.NOT_STARTED
    assert complete.status is HistoricalChunkStatus.COMPLETE
    assert "quality_status" not in complete.to_mapping()

    with pytest.raises(DataFoundationValidationError, match="status must be one of"):
        HistoricalChunkRecord.from_mapping(_chunk_values(status="ASSUMED_COMPLETE"))
    with pytest.raises(DataFoundationValidationError, match="raw_object_ref"):
        HistoricalChunkRecord.from_mapping(_chunk_values(raw_object_ref=None))
    with pytest.raises(DataFoundationValidationError, match="content-addressed"):
        HistoricalChunkRecord.from_mapping(_chunk_values(raw_object_ref="data/raw/file.json"))
    with pytest.raises(DataFoundationValidationError, match="immutable"):
        complete.with_recorded_raw_object_ref(RAW_B, row_count=10, retrieved_at=RETRIEVED_AT)

    same_raw = complete.with_recorded_raw_object_ref(
        RAW_A,
        row_count=10,
        retrieved_at=RETRIEVED_AT,
    )
    assert same_raw.raw_object_ref == RAW_A


def test_provider_error_records_classify_retryable_and_non_retryable() -> None:
    policy = RequestPacingPolicy.from_mapping(_policy_values())
    retryable = ProviderErrorRecord(
        error_id="perr_synth_retryable_001",
        provider="ibkr",
        request_id="ibkr_req_synth_002",
        chunk_id="hchunk_synth_es_20250103_b",
        error_code=162,
        error_message="synthetic pacing response for retry classification",
        retryable=True,
        attempt=2,
        timestamp=RETRIEVED_AT,
        resolution=ProviderErrorResolution.RETRY_BACKOFF_SCHEDULED,
    )
    non_retryable = ProviderErrorRecord(
        error_id="perr_synth_nonretryable_001",
        provider="ibkr",
        request_id="ibkr_req_synth_003",
        chunk_id="hchunk_synth_es_20250103_b",
        error_code="synthetic_contract_not_available",
        error_message="synthetic non-retryable response for quarantine classification",
        retryable=False,
        attempt=1,
        timestamp=RETRIEVED_AT,
        resolution=ProviderErrorResolution.QUARANTINED_NON_RETRYABLE,
    )

    assert retryable.backoff_delay_seconds(policy) == 4.0
    with pytest.raises(DataFoundationValidationError, match="quarantine instead of backing off"):
        non_retryable.backoff_delay_seconds(policy)
    with pytest.raises(DataFoundationValidationError, match="must quarantine"):
        ProviderErrorRecord(
            error_id="perr_synth_bad_nonretryable_001",
            provider="ibkr",
            request_id="ibkr_req_synth_004",
            chunk_id="hchunk_synth_es_20250103_b",
            error_code=200,
            error_message="synthetic non-retryable response",
            retryable=False,
            attempt=1,
            timestamp=RETRIEVED_AT,
            resolution=ProviderErrorResolution.RETRY_BACKOFF_SCHEDULED,
        )


def test_pull_ledger_reconciles_expected_chunks_and_resumes_without_repulling_complete() -> None:
    payload = cast(
        Mapping[str, object],
        json.loads(FIXTURE_PATH.read_text(encoding="utf-8")),
    )
    chunks = tuple(
        HistoricalChunkRecord.from_mapping(cast(Mapping[str, object], item))
        for item in cast(list[object], payload["chunk_records"])
    )
    expected_chunk_ids = cast(list[str], payload["expected_chunk_ids"])

    ledger = HistoricalPullLedger.create(
        pull_id="hpl_synthetic_resume_001",
        manifest_id=cast(str, payload["manifest_id"]),
        chunk_records=chunks,
        expected_chunk_ids=expected_chunk_ids,
        started_at=RETRIEVED_AT,
    )

    assert ledger.status is HistoricalPullLedgerStatus.IN_PROGRESS
    assert ledger.completed_chunk_ids() == ("hchunk_synth_es_20250102_a",)
    assert ledger.pending_chunk_ids_for_resume(ledger.resume_token) == (
        "hchunk_synth_es_20250103_b",
    )

    persisted = HistoricalPullLedger.from_mapping(ledger.to_mapping())
    assert persisted.resume_token == ledger.resume_token

    tampered = dict(ledger.to_mapping())
    tampered["resume_token"] = "sha256:" + "0" * 64
    with pytest.raises(DataFoundationValidationError, match="resume_token"):
        HistoricalPullLedger.from_mapping(tampered)

    with pytest.raises(DataFoundationValidationError, match="missing expected chunks"):
        HistoricalPullLedger.create(
            pull_id="hpl_synthetic_resume_002",
            manifest_id=cast(str, payload["manifest_id"]),
            chunk_records=chunks,
            expected_chunk_ids=expected_chunk_ids + ["hchunk_synth_missing"],
            started_at=RETRIEVED_AT,
        )


def test_pull_ledger_detects_duplicate_requests_and_status_mismatches() -> None:
    complete = HistoricalChunkRecord.from_mapping(_chunk_values())
    duplicate_chunk_id = HistoricalChunkRecord.from_mapping(
        _chunk_values(
            request_spec_id="hrs_synthetic_es_h5_other",
            provider_request_id="ibkr_req_synth_002",
            raw_object_ref=RAW_B,
        )
    )
    duplicate_request = HistoricalChunkRecord.from_mapping(
        _chunk_values(
            chunk_id="hchunk_synth_es_duplicate_request",
            provider_request_id="ibkr_req_synth_003",
            raw_object_ref=RAW_B,
        )
    )

    with pytest.raises(DataFoundationValidationError, match="duplicate chunk_id"):
        HistoricalPullLedger.create(
            pull_id="hpl_synthetic_duplicate_001",
            manifest_id="hrm_synthetic_es_h5_manifest_v1",
            chunk_records=(complete, duplicate_chunk_id),
            expected_chunk_ids=(complete.chunk_id, duplicate_chunk_id.chunk_id),
            started_at=RETRIEVED_AT,
            finished_at=RETRIEVED_AT,
        )
    with pytest.raises(DataFoundationValidationError, match="duplicate chunk request"):
        HistoricalPullLedger.create(
            pull_id="hpl_synthetic_duplicate_002",
            manifest_id="hrm_synthetic_es_h5_manifest_v1",
            chunk_records=(complete, duplicate_request),
            expected_chunk_ids=(complete.chunk_id, duplicate_request.chunk_id),
            started_at=RETRIEVED_AT,
            finished_at=RETRIEVED_AT,
        )

    not_started = HistoricalChunkRecord.from_mapping(
        _chunk_values(
            chunk_id="hchunk_synth_es_20250103_b",
            request_spec_id="hrs_synthetic_es_h5_20250103_20250104",
            start_ts=MID_TS.isoformat(),
            end_ts=END_TS.isoformat(),
            status="NOT_STARTED",
            attempt_count=0,
            provider_request_id=None,
            raw_object_ref=None,
            row_count=None,
            error_ref=None,
            retrieved_at=None,
        )
    )
    with pytest.raises(DataFoundationValidationError, match="status does not reconcile"):
        HistoricalPullLedger(
            pull_id="hpl_synthetic_bad_status",
            manifest_id="hrm_synthetic_es_h5_manifest_v1",
            chunk_records=(complete, not_started),
            started_at=RETRIEVED_AT,
            finished_at=RETRIEVED_AT,
            status=HistoricalPullLedgerStatus.COMPLETE,
            resume_token=None,
            coverage_summary={
                "expected_chunk_ids": (complete.chunk_id, not_started.chunk_id),
                "quality_status": "not_quality_checked",
            },
            error_summary={"error_refs": ()},
        )


def test_incomplete_chunks_are_accounted_for_in_coverage_and_error_summary() -> None:
    complete = HistoricalChunkRecord.from_mapping(_chunk_values())
    incomplete = HistoricalChunkRecord.from_mapping(
        _chunk_values(
            chunk_id="hchunk_synth_es_20250103_b",
            request_spec_id="hrs_synthetic_es_h5_20250103_20250104",
            start_ts=MID_TS.isoformat(),
            end_ts=END_TS.isoformat(),
            status="INCOMPLETE",
            provider_request_id="ibkr_req_synth_005",
            raw_object_ref=None,
            row_count=4,
            error_ref="perr_synth_incomplete_001",
            retrieved_at=RETRIEVED_AT.isoformat(),
        )
    )

    ledger = HistoricalPullLedger.create(
        pull_id="hpl_synthetic_incomplete_001",
        manifest_id="hrm_synthetic_es_h5_manifest_v1",
        chunk_records=(complete, incomplete),
        expected_chunk_ids=(complete.chunk_id, incomplete.chunk_id),
        started_at=RETRIEVED_AT,
        finished_at=RETRIEVED_AT,
    )

    assert ledger.status is HistoricalPullLedgerStatus.INCOMPLETE
    assert ledger.coverage_summary["incomplete_count"] == 1
    assert ledger.error_summary["error_refs"] == ("perr_synth_incomplete_001",)
