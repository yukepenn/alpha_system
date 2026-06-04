from __future__ import annotations

import hashlib
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
from alpha_system.data.foundation.requests import (
    HistoricalPullLedger,
    ProviderErrorRecord,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.data.ibkr import pull as pull_module
from alpha_system.data.ibkr.pull import (
    RawPayloadWriteResult,
    SmokePullDoctorReport,
    build_default_smoke_manifest,
    load_default_pacing_policy,
    run_ibkr_smoke_pull,
)

NOW = datetime(2026, 6, 4, 12, 0, tzinfo=UTC)
VALID_ENV = {
    "ALPHA_DATA_PULL_AUTHORIZED": "true",
    "ALPHA_ALLOW_EXTERNAL_IBKR": "true",
    "ALPHA_IBKR_READ_ONLY_MODE": "true",
    "ALPHA_ALLOW_RAW_LOCAL_WRITE": "true",
    "ALPHA_IBKR_HOST": "127.0.0.1",
    "ALPHA_IBKR_PORT": "4002",
    "ALPHA_IBKR_CLIENT_ID": "201",
    "ALPHA_DATA_ROOT": (Path.home() / "alpha_data" / "alpha_system_smoke_pull_unit").as_posix(),
}
PAYLOAD = b"time,open,high,low,close,volume\n2026-06-04 12:00,1,2,1,2,3\n"


class CountingHistoricalTransport:
    def __init__(self, payload: bytes = PAYLOAD, *, fail: bool = False) -> None:
        self.payload = payload
        self.fail = fail
        self.call_count = 0

    def reqHistoricalData(self, *args: object, **kwargs: object) -> bytes:
        self.call_count += 1
        if self.fail:
            raise RuntimeError("raw provider details must not appear in summaries")
        return self.payload


class InMemorySmokePullStore:
    def __init__(self) -> None:
        self.raw_payloads: list[bytes] = []
        self.ledgers: list[HistoricalPullLedger] = []
        self.provider_errors: list[ProviderErrorRecord] = []

    def write_raw_payload(self, **kwargs: object) -> RawPayloadWriteResult:
        payload = kwargs["payload"]
        assert isinstance(payload, bytes)
        self.raw_payloads.append(payload)
        digest = hashlib.sha256(payload).hexdigest()
        return RawPayloadWriteResult(
            raw_object_ref="raw://sha256/" + digest,
            row_count=1,
            raw_object_id="raw_ibkr_smoke_unit",
        )

    def write_ledger(self, ledger: HistoricalPullLedger) -> None:
        self.ledgers.append(ledger)

    def write_provider_error(self, error: ProviderErrorRecord) -> None:
        self.provider_errors.append(error)


def _profile(env: dict[str, str] | None = None) -> IBKRConnectionProfile:
    return IBKRConnectionProfile.from_env(VALID_ENV if env is None else env)


def _manifest(env: dict[str, str] | None = None):
    source = VALID_ENV if env is None else env
    return build_default_smoke_manifest(env=source, profile=_profile(source), now=NOW)


def _policy():
    return load_default_pacing_policy()


def _passing_probe(profile: IBKRConnectionProfile) -> SmokePullDoctorReport:
    return SmokePullDoctorReport(
        profile=run_connection_doctor(profile),
        reachable=True,
        probe_performed=True,
    )


def _failing_probe(profile: IBKRConnectionProfile) -> SmokePullDoctorReport:
    return SmokePullDoctorReport(
        profile=run_connection_doctor(profile),
        reachable=False,
        probe_performed=True,
        failure_reason="synthetic unreachable host",
    )


def _boundary(transport: CountingHistoricalTransport):
    return build_read_only_ibkr_boundary(
        profile=_profile(),
        access_mode=DataAccessMode.authorized_pull(),
        read_only_methods={"reqHistoricalData": transport.reqHistoricalData},
    )


def test_authorized_smoke_pull_uses_read_only_handler_and_emits_redacted_summary() -> None:
    transport = CountingHistoricalTransport()
    store = InMemorySmokePullStore()

    summary = run_ibkr_smoke_pull(
        manifest=_manifest(),
        pacing_policy=_policy(),
        boundary=_boundary(transport),
        env=VALID_ENV,
        ci=False,
        execute=True,
        artifact_store=store,
        reachability_probe=_passing_probe,
        now=lambda: NOW,
    )

    summary_text = repr(summary.to_mapping())

    assert transport.call_count == 1
    assert store.raw_payloads == [PAYLOAD]
    assert len(store.ledgers) == 1
    assert store.ledgers[0].status is HistoricalPullLedgerStatus.COMPLETE
    assert store.ledgers[0].resume_token is not None
    assert summary.status == "COMPLETE"
    assert summary.external_call_attempted is True
    assert summary.raw_objects_written == 1
    assert "time,open,high" not in summary_text
    assert "2026-06-04 12:00" not in summary_text


def test_authorization_env_is_fail_closed_before_external_handler() -> None:
    transport = CountingHistoricalTransport()
    store = InMemorySmokePullStore()
    env = dict(VALID_ENV)
    env.pop("ALPHA_DATA_PULL_AUTHORIZED")

    with pytest.raises(DataFoundationValidationError, match="ALPHA_DATA_PULL_AUTHORIZED"):
        run_ibkr_smoke_pull(
            manifest=_manifest(),
            pacing_policy=_policy(),
            boundary=_boundary(transport),
            env=env,
            ci=False,
            execute=True,
            artifact_store=store,
            reachability_probe=_passing_probe,
            now=lambda: NOW,
        )

    assert transport.call_count == 0
    assert store.raw_payloads == []
    assert store.ledgers == []
    assert store.provider_errors == []


def test_connection_doctor_must_pass_before_external_handler() -> None:
    transport = CountingHistoricalTransport()
    store = InMemorySmokePullStore()

    with pytest.raises(DataFoundationValidationError, match="connection doctor failed"):
        run_ibkr_smoke_pull(
            manifest=_manifest(),
            pacing_policy=_policy(),
            boundary=_boundary(transport),
            env=VALID_ENV,
            ci=False,
            execute=True,
            artifact_store=store,
            reachability_probe=_failing_probe,
            now=lambda: NOW,
        )

    assert transport.call_count == 0
    assert store.raw_payloads == []
    assert store.ledgers == []


@pytest.mark.parametrize("client_id", ["101", "102"])
def test_reserved_client_ids_are_rejected_before_external_handler(client_id: str) -> None:
    transport = CountingHistoricalTransport()
    env = {**VALID_ENV, "ALPHA_IBKR_CLIENT_ID": client_id}

    with pytest.raises(DataFoundationValidationError, match="hard-blocked"):
        run_ibkr_smoke_pull(
            manifest=_manifest(),
            pacing_policy=_policy(),
            boundary=_boundary(transport),
            env=env,
            ci=False,
            execute=True,
            artifact_store=InMemorySmokePullStore(),
            reachability_probe=_passing_probe,
            now=lambda: NOW,
        )

    assert transport.call_count == 0


def test_missing_manifest_or_pacing_policy_blocks_before_external_handler() -> None:
    transport = CountingHistoricalTransport()
    store = InMemorySmokePullStore()

    with pytest.raises(DataFoundationValidationError, match="HistoricalRequestManifest"):
        run_ibkr_smoke_pull(
            manifest=None,
            pacing_policy=_policy(),
            boundary=_boundary(transport),
            env=VALID_ENV,
            ci=False,
            execute=True,
            artifact_store=store,
            reachability_probe=_passing_probe,
            now=lambda: NOW,
        )
    with pytest.raises(DataFoundationValidationError, match="RequestPacingPolicy"):
        run_ibkr_smoke_pull(
            manifest=_manifest(),
            pacing_policy=None,
            boundary=_boundary(transport),
            env=VALID_ENV,
            ci=False,
            execute=True,
            artifact_store=store,
            reachability_probe=_passing_probe,
            now=lambda: NOW,
        )

    assert transport.call_count == 0
    assert store.raw_payloads == []


def test_authorized_pull_mode_is_not_ci_allowed() -> None:
    transport = CountingHistoricalTransport()

    assert DataAccessMode.authorized_pull().ci_allowed is False

    with pytest.raises(DataFoundationValidationError, match="CI"):
        run_ibkr_smoke_pull(
            manifest=_manifest(),
            pacing_policy=_policy(),
            boundary=_boundary(transport),
            env=VALID_ENV,
            ci=True,
            execute=True,
            artifact_store=InMemorySmokePullStore(),
            reachability_probe=_passing_probe,
            now=lambda: NOW,
        )

    assert transport.call_count == 0


def test_missing_registered_historical_handler_blocks_before_provider_call() -> None:
    with pytest.raises(DataFoundationValidationError, match="missing registered"):
        run_ibkr_smoke_pull(
            manifest=_manifest(),
            pacing_policy=_policy(),
            env=VALID_ENV,
            ci=False,
            execute=True,
            artifact_store=InMemorySmokePullStore(),
            reachability_probe=_passing_probe,
            now=lambda: NOW,
        )


def test_provider_errors_are_recorded_without_raw_error_text_in_summary_path() -> None:
    transport = CountingHistoricalTransport(fail=True)
    store = InMemorySmokePullStore()

    with pytest.raises(DataFoundationValidationError, match="provider error recorded"):
        run_ibkr_smoke_pull(
            manifest=_manifest(),
            pacing_policy=_policy(),
            boundary=_boundary(transport),
            env=VALID_ENV,
            ci=False,
            execute=True,
            artifact_store=store,
            reachability_probe=_passing_probe,
            now=lambda: NOW,
        )

    assert transport.call_count == 1
    assert store.raw_payloads == []
    assert len(store.provider_errors) == 1
    assert store.provider_errors[0].error_message == "redacted provider error class: RuntimeError"
    assert "raw provider details" not in repr(store.provider_errors[0].to_mapping())
    assert len(store.ledgers) == 1
    assert store.ledgers[0].status is HistoricalPullLedgerStatus.QUARANTINED


def test_smoke_pull_path_exposes_no_order_or_account_methods() -> None:
    transport = CountingHistoricalTransport()
    boundary = _boundary(transport)
    store = InMemorySmokePullStore()
    forbidden_methods = (
        "place" + "Order",
        "req" + "Positions",
        "req" + "AccountUpdates",
        "req" + "AccountSummary",
        "req" + "OpenOrders",
        "req" + "Executions",
    )

    for method_name in forbidden_methods:
        assert method_name not in dir(boundary)
        assert hasattr(boundary, method_name) is False
        assert hasattr(store, method_name) is False
        assert hasattr(pull_module, method_name) is False
