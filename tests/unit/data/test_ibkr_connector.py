from __future__ import annotations

import ast
import csv
import hashlib
import io
import os
import subprocess
import sys
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from alpha_system.data.foundation import (
    DataAccessMode,
    IBKRClientIdPolicy,
    IBKRConnectionProfile,
    build_read_only_ibkr_boundary,
    run_connection_doctor,
)
from alpha_system.data.foundation.requests import HistoricalPullLedger, HistoricalRequestManifest
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.data.ibkr import connector as connector_module
from alpha_system.data.ibkr import smoke_connect
from alpha_system.data.ibkr.connector import (
    CSV_HEADER,
    FORBIDDEN_IB_METHODS,
    build_ibkr_historical_handler,
)
from alpha_system.data.ibkr.pull import (
    RawPayloadWriteResult,
    SmokePullDoctorReport,
    run_ibkr_smoke_pull,
)

NOW = datetime(2026, 6, 4, 12, 0, tzinfo=UTC)
BAR_TS = datetime(2026, 6, 1, 14, 30, tzinfo=UTC)
VALID_ENV = {
    "ALPHA_DATA_PULL_AUTHORIZED": "1",
    "ALPHA_ALLOW_EXTERNAL_IBKR": "1",
    "ALPHA_IBKR_READ_ONLY_MODE": "1",
    "ALPHA_ALLOW_RAW_LOCAL_WRITE": "1",
    "ALPHA_IBKR_HOST": "127.0.0.1",
    "ALPHA_IBKR_PORT": "4002",
    "ALPHA_IBKR_CLIENT_ID": "201",
}


@dataclass(frozen=True, slots=True)
class FakeBar:
    date: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    average: Decimal
    barCount: int


class FakeIB:
    def __init__(self, bars: list[FakeBar]) -> None:
        self.bars = bars
        self.calls: list[tuple[object, dict[str, object]]] = []

    def reqHistoricalData(self, contract: object, **kwargs: object) -> list[FakeBar]:
        self.calls.append((contract, kwargs))
        return self.bars

    def __getattr__(self, name: str) -> object:
        if name in FORBIDDEN_IB_METHODS:
            raise AssertionError(f"forbidden IBKR method reached: {name}")
        raise AttributeError(name)


class TmpSmokePullStore:
    def __init__(self, data_root: Path) -> None:
        self.data_root = data_root
        self.raw_paths: list[Path] = []
        self.ledgers: list[HistoricalPullLedger] = []

    def write_raw_payload(
        self,
        *,
        request_spec: object,
        chunk_id: str,
        payload: bytes,
        retrieved_at: datetime,
    ) -> RawPayloadWriteResult:
        del request_spec, retrieved_at
        digest = hashlib.sha256(payload).hexdigest()
        path = self.data_root / "raw" / f"{chunk_id}-{digest}.raw"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        self.raw_paths.append(path)
        return RawPayloadWriteResult(
            raw_object_ref="raw://sha256/" + digest,
            row_count=_count_csv_rows(payload),
            raw_object_id=f"raw_{chunk_id}",
        )

    def write_ledger(self, ledger: HistoricalPullLedger) -> None:
        self.ledgers.append(ledger)
        path = self.data_root / "metadata" / "ibkr_smoke_pull" / "ledgers"
        path.mkdir(parents=True, exist_ok=True)
        (path / f"{ledger.pull_id}.json").write_text("unit-ledger\n", encoding="utf-8")

    def write_provider_error(self, error: object) -> None:
        path = self.data_root / "metadata" / "ibkr_smoke_pull" / "provider_errors"
        path.mkdir(parents=True, exist_ok=True)
        (path / "unit-provider-error.json").write_text(repr(error), encoding="utf-8")


def _count_csv_rows(payload: bytes) -> int:
    lines = [line for line in payload.decode("utf-8").splitlines() if line.strip()]
    return max(0, len(lines) - 1)


def _profile() -> IBKRConnectionProfile:
    return IBKRConnectionProfile.from_env(VALID_ENV)


def _spec():
    return connector_module.HistoricalRequestSpec(
        request_spec_id="hrs_ibkr_connector_unit_es_v1",
        source_id="dsrc_ibkr_historical",
        symbol_root="ES",
        contract_ref="fcr_ibkr_connector_unit_es_contfut",
        sec_type="CONTFUT",
        exchange="CME",
        currency="USD",
        bar_size="1 min",
        what_to_show="TRADES",
        use_rth=False,
        duration="1800 S",
        end_datetime_policy="explicit_unit_end",
        start_ts=NOW - timedelta(minutes=30),
        end_ts=NOW,
        chunk_policy={"planned_chunks": 1, "max_duration": "1800 S"},
        client_id=201,
    )


def _dated_fut_spec():
    return replace(
        _spec(),
        request_spec_id="hrs_ibkr_connector_unit_es_202609_v1",
        contract_ref="fut_es_202609",
        sec_type="FUT",
    )


def _manifest() -> HistoricalRequestManifest:
    request_spec = _spec()
    return HistoricalRequestManifest.create(
        manifest_id="hrm_ibkr_connector_unit_v1",
        batch_id="batch_ibkr_connector_unit_v1",
        request_specs=(request_spec,),
        chunk_count=1,
        expected_coverage={
            "smoke_pull": True,
            "bounded_chunk_count": 1,
            "coverage_status": "connector_unit_not_quality_checked",
            "quality_claim": False,
        },
        pacing_policy_id="rpp_ibkr_historical_conservative_tobeverified_v1",
        data_root=Path.home() / "alpha_data" / "alpha_system_connector_unit_manifest",
        created_by="ADF1 Task 1A connector unit test",
        created_at=NOW,
    )


def _fake_bar() -> FakeBar:
    return FakeBar(
        date=BAR_TS,
        open=Decimal("5000.25"),
        high=Decimal("5001.00"),
        low=Decimal("4999.75"),
        close=Decimal("5000.50"),
        volume=100,
        average=Decimal("5000.40"),
        barCount=3,
    )


def _passing_probe(profile: IBKRConnectionProfile) -> SmokePullDoctorReport:
    return SmokePullDoctorReport(
        profile=run_connection_doctor(profile),
        reachable=True,
        probe_performed=True,
    )


def test_historical_handler_maps_request_to_req_historical_data_csv() -> None:
    fake_ib = FakeIB([_fake_bar()])
    spec = _spec()
    handler = build_ibkr_historical_handler(ib=fake_ib, profile=_profile())

    payload = handler(spec)
    rows = list(csv.reader(io.StringIO(payload.decode("utf-8"))))

    assert rows[0] == list(CSV_HEADER)
    assert rows[1] == [
        "ES",
        "fcr_ibkr_connector_unit_es_contfut",
        "2026-06-01 14:30:00 UTC",
        "5000.25",
        "5001.00",
        "4999.75",
        "5000.50",
        "100",
        "5000.40",
        "3",
    ]
    assert len(fake_ib.calls) == 1
    contract, kwargs = fake_ib.calls[0]
    assert getattr(contract, "secType") == "CONTFUT"
    assert getattr(contract, "symbol") == "ES"
    assert not hasattr(contract, "includeExpired")
    assert kwargs["whatToShow"] == spec.what_to_show
    assert kwargs["endDateTime"] == ""
    assert kwargs["barSizeSetting"] == spec.bar_size
    assert kwargs["durationStr"] == spec.duration
    assert kwargs["useRTH"] == spec.use_rth
    assert kwargs["formatDate"] == 2


def test_historical_handler_keeps_end_datetime_for_dated_future_contract() -> None:
    fake_ib = FakeIB([_fake_bar()])
    spec = _dated_fut_spec()
    handler = build_ibkr_historical_handler(ib=fake_ib, profile=_profile())

    payload = handler(spec)
    rows = list(csv.reader(io.StringIO(payload.decode("utf-8"))))

    assert rows[0] == list(CSV_HEADER)
    assert len(fake_ib.calls) == 1
    contract, kwargs = fake_ib.calls[0]
    assert getattr(contract, "secType") == "FUT"
    assert getattr(contract, "symbol") == "ES"
    assert getattr(contract, "lastTradeDateOrContractMonth") == "202609"
    assert getattr(contract, "localSymbol") == ""
    assert getattr(contract, "includeExpired") is True
    assert kwargs["endDateTime"] == spec.end_ts


def test_connector_handler_wires_through_smoke_pull_and_writes_only_tmp_data_root(
    tmp_path: Path,
) -> None:
    env = {**VALID_ENV, "ALPHA_DATA_ROOT": tmp_path.as_posix()}
    fake_ib = FakeIB([_fake_bar()])
    handler = build_ibkr_historical_handler(ib=fake_ib, profile=_profile())
    boundary = build_read_only_ibkr_boundary(
        profile=_profile(),
        access_mode=DataAccessMode.authorized_pull(),
        read_only_methods={"reqHistoricalData": handler},
    )
    store = TmpSmokePullStore(tmp_path)

    summary = run_ibkr_smoke_pull(
        manifest=_manifest(),
        boundary=boundary,
        execute=True,
        env=env,
        ci=False,
        max_chunks=1,
        batch="mini_main",
        artifact_store=store,
        reachability_probe=_passing_probe,
        use_default_pacing_policy=True,
        now=lambda: NOW,
    )

    assert summary.status == "COMPLETE"
    assert summary.chunks_complete == 1
    assert summary.raw_objects_written == 1
    assert len(store.raw_paths) == 1
    assert store.raw_paths[0].is_file()
    store.raw_paths[0].relative_to(tmp_path)
    assert not (Path.cwd() / "data" / store.raw_paths[0].name).exists()


def test_smoke_connect_short_circuits_unreachable_doctor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env = {**VALID_ENV, "ALPHA_DATA_ROOT": tmp_path.as_posix()}
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    monkeypatch.delenv("CI", raising=False)

    sys.modules.pop("ib_insync", None)

    def unreachable_probe(profile: IBKRConnectionProfile) -> SmokePullDoctorReport:
        return SmokePullDoctorReport(
            profile=run_connection_doctor(profile),
            reachable=False,
            probe_performed=True,
            failure_reason="unit-unreachable",
        )

    def fail_open_boundary(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise AssertionError("open_ibkr_historical_boundary must not be reached")

    monkeypatch.setattr(smoke_connect, "open_ibkr_historical_boundary", fail_open_boundary)

    result = smoke_connect.main([], reachability_probe=unreachable_probe)
    captured = capsys.readouterr()

    assert result == 2
    assert "ib_insync" not in sys.modules
    assert "connection doctor" in captured.err
    assert "127.0.0.1:4002" in captured.err
    assert "unit-unreachable" in captured.err
    assert "NOT changed automatically" in captured.err


def test_smoke_connect_refuses_external_access_in_ci(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env = {**VALID_ENV, "ALPHA_DATA_ROOT": tmp_path.as_posix()}
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv("CI", "true")

    probe_calls = 0
    boundary_calls = 0

    def reachable_probe(profile: IBKRConnectionProfile) -> SmokePullDoctorReport:
        nonlocal probe_calls
        probe_calls += 1
        return SmokePullDoctorReport(
            profile=run_connection_doctor(profile),
            reachable=True,
            probe_performed=True,
        )

    def fail_open_boundary(*args: object, **kwargs: object) -> object:
        nonlocal boundary_calls
        del args, kwargs
        boundary_calls += 1
        raise AssertionError("open_ibkr_historical_boundary must not be reached")

    monkeypatch.setattr(smoke_connect, "open_ibkr_historical_boundary", fail_open_boundary)

    result = smoke_connect.main([], reachability_probe=reachable_probe)
    captured = capsys.readouterr()

    assert result == 2
    assert probe_calls == 0
    assert boundary_calls == 0
    assert "CI" in captured.err


def test_smoke_connect_validates_authorization_before_reachability_probe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    for name in (
        "ALPHA_DATA_PULL_AUTHORIZED",
        "ALPHA_ALLOW_EXTERNAL_IBKR",
        "ALPHA_IBKR_READ_ONLY_MODE",
        "ALPHA_ALLOW_RAW_LOCAL_WRITE",
        "CI",
    ):
        monkeypatch.delenv(name, raising=False)
    for name, value in {
        "ALPHA_IBKR_HOST": "127.0.0.1",
        "ALPHA_IBKR_PORT": "4002",
        "ALPHA_IBKR_CLIENT_ID": "201",
        "ALPHA_DATA_ROOT": tmp_path.as_posix(),
    }.items():
        monkeypatch.setenv(name, value)

    probe_calls = 0

    def reachable_probe(profile: IBKRConnectionProfile) -> SmokePullDoctorReport:
        nonlocal probe_calls
        probe_calls += 1
        return SmokePullDoctorReport(
            profile=run_connection_doctor(profile),
            reachable=True,
            probe_performed=True,
        )

    def fail_open_boundary(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise AssertionError("open_ibkr_historical_boundary must not be reached")

    monkeypatch.setattr(smoke_connect, "open_ibkr_historical_boundary", fail_open_boundary)

    result = smoke_connect.main([], reachability_probe=reachable_probe)
    captured = capsys.readouterr()

    assert result == 2
    assert probe_calls == 0
    assert "blocked" in captured.err
    assert "ALPHA_DATA_PULL_AUTHORIZED" in captured.err


def test_open_ibkr_historical_boundary_validates_env_for_injected_client() -> None:
    sys.modules.pop("ib_insync", None)
    fake_ib = FakeIB([_fake_bar()])
    env = dict(VALID_ENV)
    env.pop("ALPHA_DATA_PULL_AUTHORIZED")

    with pytest.raises(DataFoundationValidationError, match="ALPHA_DATA_PULL_AUTHORIZED"):
        with connector_module.open_ibkr_historical_boundary(
            _profile(),
            DataAccessMode.authorized_pull(),
            env=env,
            ib=fake_ib,
        ):
            raise AssertionError("boundary must not open without authorization gates")

    assert fake_ib.calls == []
    assert "ib_insync" not in sys.modules


def test_connector_source_guard_blocks_forbidden_attribute_calls() -> None:
    source = Path(connector_module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    load_function = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_load_ib_insync"
    )
    load_function_lines = set(range(load_function.lineno, load_function.end_lineno + 1))

    for method_name in FORBIDDEN_IB_METHODS:
        assert f".{method_name}" not in source
    assert "from ib_insync import" not in source
    assert not any(line.startswith("import ib_insync") for line in source.splitlines())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "ib_insync":
            pytest.fail("connector must not use from ib_insync import")
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] == "ib_insync":
                    assert node.lineno in load_function_lines


@pytest.mark.parametrize("client_id", [101, 102])
def test_connector_entry_path_reuses_client_id_guard(client_id: int) -> None:
    with pytest.raises(DataFoundationValidationError, match="hard-blocked"):
        IBKRClientIdPolicy.default().validate_client_id(client_id)


def test_connector_import_is_lazy_for_ib_insync() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    src_path = repo_root / "src"
    pythonpath = src_path.as_posix()
    if os.environ.get("PYTHONPATH"):
        pythonpath = f"{pythonpath}{os.pathsep}{os.environ['PYTHONPATH']}"
    code = (
        "import sys; "
        "import alpha_system.data.ibkr.connector as c; "
        "assert c.__name__ == 'alpha_system.data.ibkr.connector'; "
        "assert 'ib_insync' not in sys.modules, 'ib_insync imported eagerly'; "
        "print('ok')"
    )

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
        cwd=repo_root,
        env={**os.environ, "PYTHONPATH": pythonpath},
    )

    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout
