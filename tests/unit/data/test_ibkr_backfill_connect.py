from __future__ import annotations

import json
from contextlib import AbstractContextManager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import TracebackType

import pytest

from alpha_system.data.foundation import (
    DataAccessMode,
    IBKRConnectionProfile,
    build_read_only_ibkr_boundary,
    run_connection_doctor,
)
from alpha_system.data.foundation.requests import HistoricalRequestManifest, HistoricalRequestSpec
from alpha_system.data.ibkr import backfill_connect
from alpha_system.data.ibkr.manifest_builder import write_manifest_json
from alpha_system.data.ibkr.pull import SmokePullDoctorReport, load_default_pacing_policy

NOW = datetime(2026, 6, 4, 12, 0, tzinfo=UTC)
DATA_ROOT = (Path.home() / "alpha_data" / "alpha_system_backfill_connect_unit").as_posix()
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


def _json_ready(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): _json_ready(nested) for key, nested in value.items()}
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    if hasattr(value, "items"):
        return {str(key): _json_ready(nested) for key, nested in value.items()}
    if isinstance(value, datetime):
        return value.isoformat()
    return value


class FakeBoundaryContext(AbstractContextManager[object]):
    def __init__(self, boundary: object) -> None:
        self.boundary = boundary
        self.entered = False

    def __enter__(self) -> object:
        self.entered = True
        return self.boundary

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exc_type, exc_value, traceback


class FakeSummary:
    def to_mapping(self) -> dict[str, object]:
        return {
            "status": "COMPLETE",
            "external_call_attempted": True,
            "interruption_simulated": False,
            "chunks_complete": 1,
        }


def _profile() -> IBKRConnectionProfile:
    return IBKRConnectionProfile.from_env(VALID_ENV)


def _manifest() -> HistoricalRequestManifest:
    request_spec = HistoricalRequestSpec(
        request_spec_id="hrs_backfill_connect_unit_es",
        source_id="dsrc_ibkr_historical",
        symbol_root="ES",
        contract_ref="fcr_ibkr_backfill_connect_es_contfut",
        sec_type="CONTFUT",
        exchange="CME",
        currency="USD",
        bar_size="1 min",
        what_to_show="TRADES",
        use_rth=False,
        duration="1800 S",
        end_datetime_policy="unit",
        start_ts=NOW - timedelta(minutes=30),
        end_ts=NOW,
        chunk_policy={"chunk_id": "hchunk_backfill_connect_unit_es", "planned_chunks": 1},
        client_id=201,
    )
    return HistoricalRequestManifest.create(
        manifest_id="hrm_backfill_connect_unit",
        batch_id="batch_backfill_connect_unit",
        request_specs=(request_spec,),
        chunk_count=1,
        expected_coverage={
            "coverage_status": "unit_not_quality_checked",
            "quality_claim": False,
            "real_coverage_claim": False,
        },
        pacing_policy_id="rpp_ibkr_historical_conservative_tobeverified_v1",
        data_root=DATA_ROOT,
        created_by="ADF1 Task 1B Stage A unit test",
        created_at=NOW,
    )


def _write_inputs(tmp_path: Path) -> tuple[Path, Path, HistoricalRequestManifest]:
    manifest = _manifest()
    manifest_path = write_manifest_json(manifest, tmp_path / "manifest.json")
    pacing_path = tmp_path / "pacing.json"
    pacing_path.write_text(
        json.dumps(_json_ready(load_default_pacing_policy().to_mapping()), indent=2),
        encoding="utf-8",
    )
    return manifest_path, pacing_path, manifest


def _passing_probe(profile: IBKRConnectionProfile) -> SmokePullDoctorReport:
    return SmokePullDoctorReport(
        profile=run_connection_doctor(profile),
        reachable=True,
        probe_performed=True,
    )


def test_backfill_connect_wires_straight_pull_with_fake_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest_path, pacing_path, manifest = _write_inputs(tmp_path)
    for name, value in VALID_ENV.items():
        monkeypatch.setenv(name, value)
    monkeypatch.delenv("CI", raising=False)

    profile = _profile()
    boundary = build_read_only_ibkr_boundary(
        profile=profile,
        access_mode=DataAccessMode.authorized_pull(),
        read_only_methods={"reqHistoricalData": lambda request_spec: b"unit\n"},
    )
    boundary_context = FakeBoundaryContext(boundary)
    runner_calls: list[dict[str, object]] = []

    def fake_open(
        opened_profile: IBKRConnectionProfile,
        access_mode: DataAccessMode,
        *,
        env: object,
    ) -> FakeBoundaryContext:
        assert opened_profile.host == profile.host
        assert opened_profile.port == profile.port
        assert opened_profile.client_id == profile.client_id
        assert access_mode.mode == "authorized_pull"
        assert env is not None
        return boundary_context

    def fake_runner(**kwargs: object) -> FakeSummary:
        runner_calls.append(dict(kwargs))
        assert kwargs["manifest"] == manifest
        assert kwargs["pacing_policy"] == load_default_pacing_policy()
        assert kwargs["execute"] is True
        assert kwargs["ci"] is None
        assert kwargs["max_chunks"] == manifest.chunk_count
        assert kwargs["interrupt_after_chunks"] >= manifest.chunk_count
        return FakeSummary()

    monkeypatch.setattr(backfill_connect, "open_ibkr_historical_boundary", fake_open)
    monkeypatch.setattr(backfill_connect, "run_local_backfill_resume_drill", fake_runner)

    result = backfill_connect.main(
        [
            "--manifest",
            manifest_path.as_posix(),
            "--pacing-policy",
            pacing_path.as_posix(),
        ],
        reachability_probe=_passing_probe,
    )
    captured = capsys.readouterr()

    assert result == 0
    assert boundary_context.entered is True
    assert len(runner_calls) == 1
    payload = json.loads(captured.out)
    assert payload["status"] == "COMPLETE"
    assert payload["interruption_simulated"] is False


def test_backfill_connect_validates_auth_gates_before_probe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest_path, pacing_path, _ = _write_inputs(tmp_path)
    for name, value in VALID_ENV.items():
        monkeypatch.setenv(name, value)
    monkeypatch.delenv("ALPHA_DATA_PULL_AUTHORIZED", raising=False)
    monkeypatch.delenv("CI", raising=False)
    probe_calls = 0

    def probe(profile: IBKRConnectionProfile) -> SmokePullDoctorReport:
        nonlocal probe_calls
        del profile
        probe_calls += 1
        raise AssertionError("probe must not run before authorization")

    result = backfill_connect.main(
        [
            "--manifest",
            manifest_path.as_posix(),
            "--pacing-policy",
            pacing_path.as_posix(),
        ],
        reachability_probe=probe,
    )
    captured = capsys.readouterr()

    assert result == 2
    assert probe_calls == 0
    assert "ALPHA_DATA_PULL_AUTHORIZED" in captured.err


def test_backfill_connect_short_circuits_unreachable_probe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest_path, pacing_path, _ = _write_inputs(tmp_path)
    for name, value in VALID_ENV.items():
        monkeypatch.setenv(name, value)
    monkeypatch.delenv("CI", raising=False)

    def unreachable_probe(profile: IBKRConnectionProfile) -> SmokePullDoctorReport:
        return SmokePullDoctorReport(
            profile=run_connection_doctor(profile),
            reachable=False,
            probe_performed=True,
            failure_reason="unit-unreachable",
        )

    def fail_open(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise AssertionError("boundary must not open when doctor blocks")

    monkeypatch.setattr(backfill_connect, "open_ibkr_historical_boundary", fail_open)

    result = backfill_connect.main(
        [
            "--manifest",
            manifest_path.as_posix(),
            "--pacing-policy",
            pacing_path.as_posix(),
        ],
        reachability_probe=unreachable_probe,
    )
    captured = capsys.readouterr()

    assert result == 2
    assert "connection doctor" in captured.err
    assert "127.0.0.1:4002" in captured.err
    assert "unit-unreachable" in captured.err
    assert "NOT changed automatically" in captured.err


def test_backfill_connect_refuses_external_access_in_ci(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest_path, pacing_path, _ = _write_inputs(tmp_path)
    for name, value in VALID_ENV.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv("CI", "true")
    probe_calls = 0

    def probe(profile: IBKRConnectionProfile) -> SmokePullDoctorReport:
        nonlocal probe_calls
        del profile
        probe_calls += 1
        raise AssertionError("probe must not run in CI")

    result = backfill_connect.main(
        [
            "--manifest",
            manifest_path.as_posix(),
            "--pacing-policy",
            pacing_path.as_posix(),
        ],
        reachability_probe=probe,
    )
    captured = capsys.readouterr()

    assert result == 2
    assert probe_calls == 0
    assert "CI" in captured.err
