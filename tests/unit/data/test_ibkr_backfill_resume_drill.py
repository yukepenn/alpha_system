from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from alpha_system.data.foundation import (
    DataAccessMode,
    HistoricalPullLedgerStatus,
    IBKRConnectionProfile,
    build_read_only_ibkr_boundary,
    run_connection_doctor,
)
from alpha_system.data.foundation.requests import HistoricalRequestManifest
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.data.ibkr import backfill as backfill_module
from alpha_system.data.ibkr.backfill import (
    InMemoryBackfillArtifactStore,
    load_synthetic_backfill_resume_fixture,
    run_local_backfill_resume_drill,
)
from alpha_system.data.ibkr.pull import SmokePullDoctorReport, load_default_pacing_policy

NOW = datetime(2026, 6, 4, 12, 0, tzinfo=UTC)
VALID_ENV = {
    "ALPHA_DATA_PULL_AUTHORIZED": "true",
    "ALPHA_ALLOW_EXTERNAL_IBKR": "true",
    "ALPHA_IBKR_READ_ONLY_MODE": "true",
    "ALPHA_ALLOW_RAW_LOCAL_WRITE": "true",
    "ALPHA_IBKR_HOST": "127.0.0.1",
    "ALPHA_IBKR_PORT": "4002",
    "ALPHA_IBKR_CLIENT_ID": "201",
    "ALPHA_DATA_ROOT": (Path.home() / "alpha_data" / "alpha_system_backfill_unit").as_posix(),
}


class CountingHistoricalTransport:
    def __init__(self) -> None:
        self.call_count = 0

    def reqHistoricalData(self, *args: object, **kwargs: object) -> bytes:
        del args, kwargs
        self.call_count += 1
        return b"time,open,high,low,close,volume\nsynthetic-authorized,1,2,1,2,3\n"


def _profile(env: dict[str, str] | None = None) -> IBKRConnectionProfile:
    return IBKRConnectionProfile.from_env(VALID_ENV if env is None else env)


def _boundary(transport: CountingHistoricalTransport):
    return build_read_only_ibkr_boundary(
        profile=_profile(),
        access_mode=DataAccessMode.authorized_pull(),
        read_only_methods={"reqHistoricalData": transport.reqHistoricalData},
    )


def _passing_probe(profile: IBKRConnectionProfile) -> SmokePullDoctorReport:
    return SmokePullDoctorReport(
        profile=run_connection_doctor(profile),
        reachable=True,
        probe_performed=True,
    )


def test_synthetic_resume_drill_interrupts_and_resumes_from_ledger_token() -> None:
    fixture = load_synthetic_backfill_resume_fixture()
    store = InMemoryBackfillArtifactStore()

    summary = run_local_backfill_resume_drill(
        manifest=fixture.manifest,
        pacing_policy=load_default_pacing_policy(),
        access_mode=DataAccessMode.synthetic(),
        artifact_store=store,
        synthetic_payloads_by_chunk_id=fixture.payloads_by_chunk_id,
        execute=True,
        now=lambda: NOW,
    )
    summary_text = repr(summary.to_mapping())

    assert summary.status == "SYNTHETIC_COMPLETE"
    assert summary.external_call_attempted is False
    assert summary.chunks_planned == 2
    assert summary.chunks_completed_before_resume == 1
    assert summary.chunks_requested_initial == 1
    assert summary.chunks_requested_on_resume == 1
    assert summary.completed_chunk_ids_before_resume == ("hchunk_synthetic_backfill_es_a",)
    assert summary.resumed_chunk_ids == ("hchunk_synthetic_backfill_es_b",)
    assert summary.skipped_completed_chunk_ids == ("hchunk_synthetic_backfill_es_a",)
    assert summary.initial_resume_token is not None
    assert summary.final_resume_token is not None
    assert summary.initial_resume_token != summary.final_resume_token
    assert "synthetic-a-001" not in summary_text
    assert "synthetic-b-001" not in summary_text

    assert len(store.ledgers) == 2
    interrupted, resumed = store.ledgers
    assert interrupted.status is HistoricalPullLedgerStatus.INCOMPLETE
    assert resumed.status is HistoricalPullLedgerStatus.COMPLETE
    assert interrupted.pending_chunk_ids_for_resume(interrupted.resume_token) == (
        "hchunk_synthetic_backfill_es_b",
    )
    assert interrupted.completed_chunk_ids() == ("hchunk_synthetic_backfill_es_a",)
    assert resumed.coverage_summary["missing_chunk_ids"] == ()
    assert resumed.coverage_summary["complete_count"] == 2
    assert resumed.coverage_summary["incomplete_count"] == 0
    assert len(store.raw_by_slot) == 2
    assert len(store.provider_errors) == 1
    assert store.provider_errors[0].resolution.value == "INCOMPLETE_RESPONSE_RECORDED"


def test_backfill_drill_rejects_hidden_manifest_chunks_to_prevent_silent_gaps() -> None:
    fixture = load_synthetic_backfill_resume_fixture()
    hidden_gap_manifest = HistoricalRequestManifest.create(
        manifest_id="hrm_synthetic_backfill_resume_hidden_gap",
        batch_id=fixture.manifest.batch_id,
        request_specs=fixture.manifest.request_specs,
        chunk_count=3,
        expected_coverage=fixture.manifest.expected_coverage,
        pacing_policy_id=fixture.manifest.pacing_policy_id,
        data_root=fixture.manifest.data_root,
        created_by=fixture.manifest.created_by,
        created_at=fixture.manifest.created_at,
    )

    with pytest.raises(DataFoundationValidationError, match="one request_spec per planned chunk"):
        run_local_backfill_resume_drill(
            manifest=hidden_gap_manifest,
            pacing_policy=load_default_pacing_policy(),
            access_mode=DataAccessMode.synthetic(),
            artifact_store=InMemoryBackfillArtifactStore(),
            synthetic_payloads_by_chunk_id=fixture.payloads_by_chunk_id,
            max_chunks=3,
            execute=True,
            now=lambda: NOW,
        )


def test_in_memory_store_rejects_raw_overwrite_for_same_logical_chunk() -> None:
    fixture = load_synthetic_backfill_resume_fixture()
    request_spec = fixture.manifest.request_specs[0]
    chunk_id = "hchunk_synthetic_backfill_es_a"
    store = InMemoryBackfillArtifactStore()

    store.write_raw_payload(
        request_spec=request_spec,
        chunk_id=chunk_id,
        payload=b"time,open,high,low,close,volume\nsame-slot,1,2,1,2,3\n",
        retrieved_at=NOW,
    )

    with pytest.raises(DataFoundationValidationError, match="different content hash"):
        store.write_raw_payload(
            request_spec=request_spec,
            chunk_id=chunk_id,
            payload=b"time,open,high,low,close,volume\nsame-slot,9,9,9,9,9\n",
            retrieved_at=NOW,
        )


def test_authorized_pull_env_blocks_before_external_handler() -> None:
    fixture = load_synthetic_backfill_resume_fixture()
    transport = CountingHistoricalTransport()
    store = InMemoryBackfillArtifactStore()
    env = dict(VALID_ENV)
    env.pop("ALPHA_DATA_PULL_AUTHORIZED")

    with pytest.raises(DataFoundationValidationError, match="ALPHA_DATA_PULL_AUTHORIZED"):
        run_local_backfill_resume_drill(
            manifest=fixture.manifest,
            pacing_policy=load_default_pacing_policy(),
            boundary=_boundary(transport),
            access_mode=DataAccessMode.authorized_pull(),
            env=env,
            ci=False,
            artifact_store=store,
            reachability_probe=_passing_probe,
            execute=True,
            now=lambda: NOW,
        )

    assert transport.call_count == 0
    assert store.raw_by_slot == {}
    assert store.ledgers == []
    assert store.provider_errors == []


def test_authorized_pull_mode_is_never_ci_allowed() -> None:
    fixture = load_synthetic_backfill_resume_fixture()
    transport = CountingHistoricalTransport()
    store = InMemoryBackfillArtifactStore()

    with pytest.raises(DataFoundationValidationError, match="CI"):
        run_local_backfill_resume_drill(
            manifest=fixture.manifest,
            pacing_policy=load_default_pacing_policy(),
            boundary=_boundary(transport),
            access_mode=DataAccessMode.authorized_pull(),
            env=VALID_ENV,
            ci=True,
            artifact_store=store,
            reachability_probe=_passing_probe,
            execute=True,
            now=lambda: NOW,
        )

    assert transport.call_count == 0
    assert store.raw_by_slot == {}
    assert store.ledgers == []


def test_backfill_resume_path_exposes_no_order_or_account_methods() -> None:
    store = InMemoryBackfillArtifactStore()
    forbidden_methods = (
        "place" + "Order",
        "req" + "Positions",
        "req" + "AccountUpdates",
        "req" + "AccountSummary",
        "req" + "OpenOrders",
        "req" + "Executions",
    )

    for method_name in forbidden_methods:
        assert hasattr(store, method_name) is False
        assert hasattr(backfill_module, method_name) is False
