from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from alpha_system.data.foundation import (
    DataAccessMode,
    HistoricalPullLedgerStatus,
    IBKRConnectionProfile,
    build_read_only_ibkr_boundary,
    run_connection_doctor,
)
from alpha_system.data.foundation.requests import (
    HistoricalChunkStatus,
    HistoricalRequestManifest,
    HistoricalRequestSpec,
    RequestPacingPolicy,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.data.ibkr.backfill import (
    InMemoryBackfillArtifactStore,
    load_synthetic_backfill_resume_fixture,
    run_local_backfill_resume_drill,
)
from alpha_system.data.ibkr.pull import SmokePullDoctorReport, load_default_pacing_policy

NOW = datetime(2026, 6, 4, 12, 0, tzinfo=UTC)
DATA_ROOT = (Path.home() / "alpha_data" / "alpha_system_backfill_pacing_unit").as_posix()
PACING_POLICY_ID = "rpp_ibkr_historical_conservative_tobeverified_v1"
VALID_ENV = {
    "ALPHA_DATA_PULL_AUTHORIZED": "1",
    "ALPHA_ALLOW_EXTERNAL_IBKR": "1",
    "ALPHA_IBKR_READ_ONLY_MODE": "1",
    "ALPHA_ALLOW_RAW_LOCAL_WRITE": "1",
    "ALPHA_IBKR_HOST": "127.0.0.1",
    "ALPHA_IBKR_PORT": "4002",
    "ALPHA_IBKR_CLIENT_ID": "201",
    "ALPHA_DATA_ROOT": DATA_ROOT,
}


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def clock(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(round(seconds, 6))
        self.now += seconds


class RecordingHistoricalHandler:
    def __init__(
        self,
        *,
        failures_before_success: dict[str, int] | None = None,
        always_fail_ids: set[str] | None = None,
        guard_failure_ids: set[str] | None = None,
    ) -> None:
        self.failures_before_success = failures_before_success or {}
        self.always_fail_ids = always_fail_ids or set()
        self.guard_failure_ids = guard_failure_ids or set()
        self.calls: list[HistoricalRequestSpec] = []
        self.attempts_by_request_spec_id: dict[str, int] = {}

    def __call__(self, request_spec: HistoricalRequestSpec) -> bytes:
        self.calls.append(request_spec)
        attempts = self.attempts_by_request_spec_id.get(request_spec.request_spec_id, 0) + 1
        self.attempts_by_request_spec_id[request_spec.request_spec_id] = attempts
        if request_spec.request_spec_id in self.guard_failure_ids:
            raise DataFoundationValidationError("unit guard/config failure")
        if request_spec.request_spec_id in self.always_fail_ids:
            raise RuntimeError("unit provider failure")
        allowed_failures = self.failures_before_success.get(request_spec.request_spec_id, 0)
        if attempts <= allowed_failures:
            raise RuntimeError("unit provider retry failure")
        return (
            "time,open,high,low,close,volume\n"
            f"{request_spec.request_spec_id},1,2,1,2,3\n"
        ).encode()


def _profile() -> IBKRConnectionProfile:
    return IBKRConnectionProfile.from_env(VALID_ENV)


def _passing_probe(profile: IBKRConnectionProfile) -> SmokePullDoctorReport:
    return SmokePullDoctorReport(
        profile=run_connection_doctor(profile),
        reachable=True,
        probe_performed=True,
    )


def _boundary(handler: RecordingHistoricalHandler):
    return build_read_only_ibkr_boundary(
        profile=_profile(),
        access_mode=DataAccessMode.authorized_pull(),
        read_only_methods={"reqHistoricalData": handler},
    )


def _pacing_policy(
    *,
    min_seconds: float = 0.1,
    max_requests: int = 100,
    window_seconds: float = 60.0,
    base_seconds: float = 2.0,
    multiplier: float = 2.0,
    max_attempts: int = 4,
) -> RequestPacingPolicy:
    return RequestPacingPolicy(
        pacing_policy_id=PACING_POLICY_ID,
        min_seconds_between_identical_requests=min_seconds,
        max_requests_per_window=max_requests,
        window_seconds=window_seconds,
        bid_ask_counts_double=True,
        backoff_policy={
            "base_seconds": base_seconds,
            "multiplier": multiplier,
            "max_seconds": 120.0,
            "max_attempts": max_attempts,
        },
        source={
            "provider": "IBKR",
            "verification_status": "to_be_verified",
            "verification_method": "unit deterministic fake clock",
            "last_verified_at": None,
        },
    )


def _request_spec(
    *,
    request_spec_id: str,
    chunk_id: str,
    start_ts: datetime,
    end_ts: datetime,
    sec_type: str = "CONTFUT",
    contract_ref: str | None = None,
    duration: str = "1800 S",
) -> HistoricalRequestSpec:
    return HistoricalRequestSpec(
        request_spec_id=request_spec_id,
        source_id="dsrc_ibkr_historical",
        symbol_root="ES",
        contract_ref=contract_ref or f"fcr_{request_spec_id}",
        sec_type=sec_type,
        exchange="CME",
        currency="USD",
        bar_size="1 min",
        what_to_show="TRADES",
        use_rth=False,
        duration=duration,
        end_datetime_policy="unit",
        start_ts=start_ts,
        end_ts=end_ts,
        chunk_policy={"chunk_id": chunk_id, "planned_chunks": 1, "policy": "unit"},
        client_id=201,
    )


def _manifest(
    *,
    manifest_id: str,
    request_specs: tuple[HistoricalRequestSpec, ...],
) -> HistoricalRequestManifest:
    return HistoricalRequestManifest.create(
        manifest_id=manifest_id,
        batch_id=f"batch_{manifest_id}",
        request_specs=request_specs,
        chunk_count=len(request_specs),
        expected_coverage={
            "unit": True,
            "coverage_status": "unit_not_quality_checked",
            "quality_claim": False,
            "real_coverage_claim": False,
        },
        pacing_policy_id=PACING_POLICY_ID,
        data_root=DATA_ROOT,
        created_by="ADF1 backfill pacing unit test",
        created_at=NOW,
    )


def _run_authorized(
    *,
    manifest: HistoricalRequestManifest,
    handler: RecordingHistoricalHandler,
    pacing_policy: RequestPacingPolicy,
    fake_clock: FakeClock,
    interrupt_after_chunks: int = sys.maxsize,
    max_chunks: int | None = None,
    enforce_expanded_max_chunks: bool = True,
) -> tuple[object, InMemoryBackfillArtifactStore]:
    store = InMemoryBackfillArtifactStore()
    summary = run_local_backfill_resume_drill(
        manifest=manifest,
        pacing_policy=pacing_policy,
        boundary=_boundary(handler),
        access_mode=DataAccessMode.authorized_pull(),
        env=VALID_ENV,
        ci=False,
        max_chunks=max_chunks,
        enforce_expanded_max_chunks=enforce_expanded_max_chunks,
        interrupt_after_chunks=interrupt_after_chunks,
        artifact_store=store,
        reachability_probe=_passing_probe,
        now=lambda: NOW,
        clock=fake_clock.clock,
        sleep=fake_clock.sleep,
        execute=True,
    )
    return summary, store


def test_authorized_pacing_honors_min_interval_and_sliding_window() -> None:
    fake_clock = FakeClock()
    start = datetime(2026, 6, 1, 14, 30, tzinfo=UTC)
    specs = tuple(
        _request_spec(
            request_spec_id=f"hrs_unit_pacing_es_{suffix}",
            chunk_id=f"hchunk_unit_pacing_es_{suffix}",
            start_ts=start + timedelta(minutes=index * 30),
            end_ts=start + timedelta(minutes=(index + 1) * 30),
        )
        for index, suffix in enumerate(("a", "b", "c"))
    )
    handler = RecordingHistoricalHandler(
        failures_before_success={"hrs_unit_pacing_es_a": 1}
    )

    summary, _ = _run_authorized(
        manifest=_manifest(
            manifest_id="hrm_unit_pacing_min_and_window",
            request_specs=specs,
        ),
        handler=handler,
        pacing_policy=_pacing_policy(
            min_seconds=5.0,
            max_requests=2,
            window_seconds=20.0,
            base_seconds=1.0,
            max_attempts=2,
        ),
        fake_clock=fake_clock,
        max_chunks=3,
    )

    assert summary.status == "COMPLETE"
    assert [call.request_spec_id for call in handler.calls] == [
        "hrs_unit_pacing_es_a",
        "hrs_unit_pacing_es_a",
        "hrs_unit_pacing_es_b",
        "hrs_unit_pacing_es_c",
    ]
    assert fake_clock.sleeps == [1.0, 4.0, 15.0, 5.0]


def test_synthetic_mode_does_not_pace_or_sleep() -> None:
    fixture = load_synthetic_backfill_resume_fixture()
    fake_clock = FakeClock()

    summary = run_local_backfill_resume_drill(
        manifest=fixture.manifest,
        pacing_policy=load_default_pacing_policy(),
        access_mode=DataAccessMode.synthetic(),
        artifact_store=InMemoryBackfillArtifactStore(),
        synthetic_payloads_by_chunk_id=fixture.payloads_by_chunk_id,
        now=lambda: NOW,
        clock=fake_clock.clock,
        sleep=fake_clock.sleep,
        execute=True,
    )

    assert summary.status == "SYNTHETIC_COMPLETE"
    assert summary.external_call_attempted is False
    assert fake_clock.sleeps == []


def test_retry_backoff_success_completes_chunk() -> None:
    fake_clock = FakeClock()
    spec = _request_spec(
        request_spec_id="hrs_unit_retry_success_es",
        chunk_id="hchunk_unit_retry_success_es",
        start_ts=datetime(2026, 6, 1, 14, 30, tzinfo=UTC),
        end_ts=datetime(2026, 6, 1, 15, 0, tzinfo=UTC),
    )
    handler = RecordingHistoricalHandler(
        failures_before_success={"hrs_unit_retry_success_es": 2}
    )

    summary, store = _run_authorized(
        manifest=_manifest(
            manifest_id="hrm_unit_retry_success",
            request_specs=(spec,),
        ),
        handler=handler,
        pacing_policy=_pacing_policy(
            min_seconds=0.1,
            base_seconds=2.0,
            multiplier=2.0,
            max_attempts=4,
        ),
        fake_clock=fake_clock,
        max_chunks=1,
    )

    final_record = store.ledgers[-1].chunk_records[0]
    assert summary.status == "COMPLETE"
    assert summary.provider_errors_logged == 0
    assert fake_clock.sleeps == [2.0, 4.0]
    assert final_record.status is HistoricalChunkStatus.COMPLETE
    assert final_record.attempt_count == 3
    assert handler.attempts_by_request_spec_id["hrs_unit_retry_success_es"] == 3


def test_retry_exhaustion_quarantines_chunk_and_continues() -> None:
    fake_clock = FakeClock()
    start = datetime(2026, 6, 1, 14, 30, tzinfo=UTC)
    failing = _request_spec(
        request_spec_id="hrs_unit_retry_exhausted_es_a",
        chunk_id="hchunk_unit_retry_exhausted_es_a",
        start_ts=start,
        end_ts=start + timedelta(minutes=30),
    )
    succeeding = _request_spec(
        request_spec_id="hrs_unit_retry_exhausted_es_b",
        chunk_id="hchunk_unit_retry_exhausted_es_b",
        start_ts=start + timedelta(minutes=30),
        end_ts=start + timedelta(minutes=60),
    )
    handler = RecordingHistoricalHandler(
        always_fail_ids={"hrs_unit_retry_exhausted_es_a"}
    )

    summary, store = _run_authorized(
        manifest=_manifest(
            manifest_id="hrm_unit_retry_exhaustion_continues",
            request_specs=(failing, succeeding),
        ),
        handler=handler,
        pacing_policy=_pacing_policy(
            min_seconds=0.1,
            base_seconds=1.0,
            multiplier=2.0,
            max_attempts=3,
        ),
        fake_clock=fake_clock,
        max_chunks=2,
    )

    final_ledger = store.ledgers[-1]
    quarantined_ids = tuple(
        record.chunk_id
        for record in final_ledger.chunk_records
        if record.status is HistoricalChunkStatus.QUARANTINED
    )
    complete_ids = tuple(
        record.chunk_id
        for record in final_ledger.chunk_records
        if record.status is HistoricalChunkStatus.COMPLETE
    )

    assert summary.status == "INCOMPLETE"
    assert summary.resumed_ledger_status == HistoricalPullLedgerStatus.QUARANTINED.value
    assert summary.chunks_quarantined == 1
    assert summary.chunks_complete == 1
    assert summary.provider_errors_logged == 1
    assert final_ledger.coverage_summary["missing_chunk_ids"] == ()
    assert quarantined_ids == ("hchunk_unit_retry_exhausted_es_a",)
    assert complete_ids == ("hchunk_unit_retry_exhausted_es_b",)
    assert fake_clock.sleeps == [1.0, 2.0]
    assert [call.request_spec_id for call in handler.calls] == [
        "hrs_unit_retry_exhausted_es_a",
        "hrs_unit_retry_exhausted_es_a",
        "hrs_unit_retry_exhausted_es_a",
        "hrs_unit_retry_exhausted_es_b",
    ]


def test_guard_config_error_fails_fast_without_retry_or_quarantine() -> None:
    fake_clock = FakeClock()
    spec = _request_spec(
        request_spec_id="hrs_unit_retry_guard_config_es",
        chunk_id="hchunk_unit_retry_guard_config_es",
        start_ts=datetime(2026, 6, 1, 14, 30, tzinfo=UTC),
        end_ts=datetime(2026, 6, 1, 15, 0, tzinfo=UTC),
    )
    handler = RecordingHistoricalHandler(
        guard_failure_ids={"hrs_unit_retry_guard_config_es"}
    )
    store = InMemoryBackfillArtifactStore()

    with pytest.raises(DataFoundationValidationError, match="unit guard/config failure"):
        run_local_backfill_resume_drill(
            manifest=_manifest(
                manifest_id="hrm_unit_retry_guard_config_fail_fast",
                request_specs=(spec,),
            ),
            pacing_policy=_pacing_policy(
                min_seconds=0.1,
                base_seconds=1.0,
                multiplier=2.0,
                max_attempts=3,
            ),
            boundary=_boundary(handler),
            access_mode=DataAccessMode.authorized_pull(),
            env=VALID_ENV,
            ci=False,
            max_chunks=1,
            interrupt_after_chunks=sys.maxsize,
            artifact_store=store,
            reachability_probe=_passing_probe,
            now=lambda: NOW,
            clock=fake_clock.clock,
            sleep=fake_clock.sleep,
            execute=True,
        )

    assert handler.attempts_by_request_spec_id["hrs_unit_retry_guard_config_es"] == 1
    assert fake_clock.sleeps == []
    assert store.provider_errors == []
    assert store.ledgers == []


def test_dated_fut_one_min_plan_expands_to_daily_subchunks() -> None:
    fake_clock = FakeClock()
    spec = _request_spec(
        request_spec_id="hrs_unit_subchunk_es_202609",
        chunk_id="hchunk_unit_subchunk_es_202609",
        contract_ref="fcr_ibkr_es_fut_202609",
        sec_type="FUT",
        duration="3 D",
        start_ts=datetime(2026, 6, 1, tzinfo=UTC),
        end_ts=datetime(2026, 6, 4, tzinfo=UTC),
    )
    handler = RecordingHistoricalHandler()

    summary, store = _run_authorized(
        manifest=_manifest(
            manifest_id="hrm_unit_subchunk_dated_fut",
            request_specs=(spec,),
        ),
        handler=handler,
        pacing_policy=_pacing_policy(),
        fake_clock=fake_clock,
        max_chunks=3,
    )

    assert summary.status == "COMPLETE"
    assert summary.chunks_planned == 3
    assert [call.request_spec_id for call in handler.calls] == [
        "hrs_unit_subchunk_es_202609_20260601",
        "hrs_unit_subchunk_es_202609_20260602",
        "hrs_unit_subchunk_es_202609_20260603",
    ]
    assert [call.chunk_policy["chunk_id"] for call in handler.calls] == [
        "hchunk_unit_subchunk_es_202609_20260601",
        "hchunk_unit_subchunk_es_202609_20260602",
        "hchunk_unit_subchunk_es_202609_20260603",
    ]
    assert [call.duration for call in handler.calls] == [
        "86400 S",
        "86400 S",
        "86400 S",
    ]
    assert [call.end_ts for call in handler.calls] == [
        datetime(2026, 6, 2, tzinfo=UTC),
        datetime(2026, 6, 3, tzinfo=UTC),
        datetime(2026, 6, 4, tzinfo=UTC),
    ]
    assert {call.end_datetime_policy for call in handler.calls} == {
        "explicit_dated_fut_sub_window_end_ts"
    }
    assert store.ledgers[-1].coverage_summary["expected_chunk_count"] == 3


def test_one_min_max_request_span_over_one_day_is_rejected() -> None:
    fake_clock = FakeClock()
    spec = _request_spec(
        request_spec_id="hrs_unit_span_reject_es_202609",
        chunk_id="hchunk_unit_span_reject_es_202609",
        contract_ref="fcr_ibkr_es_fut_202609",
        sec_type="FUT",
        duration="2 D",
        start_ts=datetime(2026, 6, 1, tzinfo=UTC),
        end_ts=datetime(2026, 6, 3, tzinfo=UTC),
    )
    handler = RecordingHistoricalHandler()
    store = InMemoryBackfillArtifactStore()

    with pytest.raises(DataFoundationValidationError, match="1 min.*<= 1 day"):
        run_local_backfill_resume_drill(
            manifest=_manifest(
                manifest_id="hrm_unit_span_reject_one_min_over_day",
                request_specs=(spec,),
            ),
            pacing_policy=_pacing_policy(),
            boundary=_boundary(handler),
            access_mode=DataAccessMode.authorized_pull(),
            env=VALID_ENV,
            ci=False,
            max_chunks=2,
            max_request_span_by_bar_size={"1 min": timedelta(days=2)},
            interrupt_after_chunks=sys.maxsize,
            artifact_store=store,
            reachability_probe=_passing_probe,
            now=lambda: NOW,
            clock=fake_clock.clock,
            sleep=fake_clock.sleep,
            execute=True,
        )

    assert handler.calls == []
    assert fake_clock.sleeps == []
    assert store.provider_errors == []
    assert store.ledgers == []


def test_contfut_one_min_plan_is_not_subchunked() -> None:
    fake_clock = FakeClock()
    spec = _request_spec(
        request_spec_id="hrs_unit_contfut_no_subchunk_es",
        chunk_id="hchunk_unit_contfut_no_subchunk_es",
        duration="3 D",
        start_ts=datetime(2026, 6, 1, tzinfo=UTC),
        end_ts=datetime(2026, 6, 4, tzinfo=UTC),
    )
    handler = RecordingHistoricalHandler()

    summary, _ = _run_authorized(
        manifest=_manifest(
            manifest_id="hrm_unit_contfut_no_subchunk",
            request_specs=(spec,),
        ),
        handler=handler,
        pacing_policy=_pacing_policy(),
        fake_clock=fake_clock,
        max_chunks=1,
    )

    assert summary.status == "COMPLETE"
    assert summary.chunks_planned == 1
    assert len(handler.calls) == 1
    assert handler.calls[0].request_spec_id == "hrs_unit_contfut_no_subchunk_es"
    assert handler.calls[0].duration == "3 D"


def test_resume_across_subchunks_completes_without_duplicates_or_overwrite() -> None:
    fake_clock = FakeClock()
    spec = _request_spec(
        request_spec_id="hrs_unit_resume_subchunk_es_202609",
        chunk_id="hchunk_unit_resume_subchunk_es_202609",
        contract_ref="fcr_ibkr_es_fut_202609",
        sec_type="FUT",
        duration="3 D",
        start_ts=datetime(2026, 6, 1, tzinfo=UTC),
        end_ts=datetime(2026, 6, 4, tzinfo=UTC),
    )
    handler = RecordingHistoricalHandler()

    summary, store = _run_authorized(
        manifest=_manifest(
            manifest_id="hrm_unit_resume_across_subchunks",
            request_specs=(spec,),
        ),
        handler=handler,
        pacing_policy=_pacing_policy(),
        fake_clock=fake_clock,
        interrupt_after_chunks=1,
        max_chunks=3,
    )

    called_ids = [call.request_spec_id for call in handler.calls]
    raw_slots = tuple(store.raw_by_slot)
    final_ledger = store.ledgers[-1]

    assert summary.status == "COMPLETE"
    assert summary.interruption_simulated is True
    assert summary.chunks_completed_before_resume == 1
    assert summary.chunks_requested_initial == 1
    assert summary.chunks_requested_on_resume == 2
    assert summary.raw_objects_written == 3
    assert called_ids == [
        "hrs_unit_resume_subchunk_es_202609_20260601",
        "hrs_unit_resume_subchunk_es_202609_20260602",
        "hrs_unit_resume_subchunk_es_202609_20260603",
    ]
    assert len(called_ids) == len(set(called_ids))
    assert len(raw_slots) == 3
    assert len(raw_slots) == len(set(raw_slots))
    assert final_ledger.coverage_summary["missing_chunk_ids"] == ()
    assert final_ledger.coverage_summary["complete_count"] == 3
    assert fake_clock.sleeps == []
