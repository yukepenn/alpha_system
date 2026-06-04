from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pytest

from alpha_system.data.foundation import (
    DataAccessMode,
    HistoricalChunkRecord,
    HistoricalPullLedger,
    HistoricalPullLedgerStatus,
    HistoricalRequestLifecycleState,
    HistoricalRequestManifest,
    HistoricalRequestSpec,
    IBKRClientIdPolicy,
    IBKRConnectionProfile,
    ReadOnlyBoundaryViolation,
    RequestPacingPolicy,
    authorize_historical_request_transition,
    build_read_only_ibkr_boundary,
    plan_historical_request_transition,
    require_pacing_policy_for_provider_pull,
    require_validated_manifest_for_provider_pull,
)
from alpha_system.data.foundation.bars import CanonicalBarRecord
from alpha_system.data.foundation.series import (
    ContinuousFuturesSeriesRecord,
    require_dated_contract_truth,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError

ROOT = Path(__file__).resolve().parents[3]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "data" / ("synthetic_ibkr_e2e_provider_fixture.json")
POLICY_PATH = ROOT / "configs" / "data" / "request_pacing_policy_to_be_verified.json"
CREATED_AT = datetime(2026, 6, 4, 0, 0, tzinfo=UTC)


class SyntheticFixtureTransport:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.synthetic_call_count = 0
        self.external_call_count = 0

    def pull_from_fixture(self) -> bytes:
        self.synthetic_call_count += 1
        return self.payload

    def reqHistoricalData(self, *args: object, **kwargs: object) -> bytes:
        self.external_call_count += 1
        raise AssertionError("external IBKR call attempted in DATA-P21")


def _fixture() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(FIXTURE_PATH.read_text(encoding="utf-8")))


def _pacing_policy() -> RequestPacingPolicy:
    values = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    return RequestPacingPolicy.from_mapping(cast(Mapping[str, object], values))


def _data_root() -> str:
    return (Path.home() / "alpha_data" / "alpha_system_synthetic_ibkr_e2e").as_posix()


def _request_spec(**overrides: object) -> HistoricalRequestSpec:
    values = dict(cast(Mapping[str, object], _fixture()["historical_request"]))
    values.update(overrides)
    return HistoricalRequestSpec.from_mapping(values)


def _manifest(
    request_spec: HistoricalRequestSpec | None = None,
) -> HistoricalRequestManifest:
    fixture = _fixture()
    manifest_values = cast(Mapping[str, object], fixture["manifest"])
    return HistoricalRequestManifest.create(
        manifest_id=cast(str, manifest_values["manifest_id"]),
        batch_id=cast(str, manifest_values["batch_id"]),
        request_specs=(request_spec or _request_spec(),),
        chunk_count=cast(int, manifest_values["chunk_count"]),
        expected_coverage=cast(Mapping[str, object], manifest_values["expected_coverage"]),
        pacing_policy_id=cast(str, manifest_values["pacing_policy_id"]),
        data_root=_data_root(),
        created_by=cast(str, manifest_values["created_by"]),
        created_at=CREATED_AT,
    )


def _historical_payload() -> bytes:
    return cast(str, _fixture()["historical_bars_csv"]).encode("utf-8")


def _raw_ref(payload: bytes) -> str:
    return "raw://sha256/" + hashlib.sha256(payload).hexdigest()


def _complete_chunk(payload: bytes, *, chunk_id: str) -> HistoricalChunkRecord:
    raw = cast(Mapping[str, object], _fixture()["raw_object"])
    return HistoricalChunkRecord.from_mapping(
        {
            "chunk_id": chunk_id,
            "request_spec_id": cast(str, raw["request_id"]),
            "symbol_root": "ES",
            "contract_ref": "fut_es_202606",
            "start_ts": "2026-06-01T14:30:00+00:00",
            "end_ts": "2026-06-01T14:33:00+00:00",
            "status": "COMPLETE",
            "attempt_count": 1,
            "provider_request_id": f"ibkr_req_{chunk_id}",
            "raw_object_ref": _raw_ref(payload),
            "row_count": cast(int, raw["row_count"]),
            "error_ref": None,
            "retrieved_at": cast(str, raw["retrieved_at"]),
        }
    )


def _not_started_chunk() -> HistoricalChunkRecord:
    raw = cast(Mapping[str, object], _fixture()["raw_object"])
    return HistoricalChunkRecord.from_mapping(
        {
            "chunk_id": "hchunk_synthetic_ibkr_e2e_b",
            "request_spec_id": cast(str, raw["request_id"]),
            "symbol_root": "ES",
            "contract_ref": "fut_es_202606",
            "start_ts": "2026-06-01T14:33:00+00:00",
            "end_ts": "2026-06-01T14:36:00+00:00",
            "status": "NOT_STARTED",
            "attempt_count": 0,
            "provider_request_id": None,
            "raw_object_ref": None,
            "row_count": None,
            "error_ref": None,
            "retrieved_at": None,
        }
    )


def _synthetic_pull(
    *,
    manifest: HistoricalRequestManifest | None,
    pacing_policy: RequestPacingPolicy | None,
    transport: SyntheticFixtureTransport,
) -> bytes:
    require_validated_manifest_for_provider_pull(manifest)
    require_pacing_policy_for_provider_pull(pacing_policy)
    return transport.pull_from_fixture()


def test_synthetic_access_mode_blocks_registered_external_handler() -> None:
    fixture = _fixture()
    profile_values = cast(Mapping[str, object], fixture["connection_profile"])
    transport = SyntheticFixtureTransport(_historical_payload())
    boundary = build_read_only_ibkr_boundary(
        profile=IBKRConnectionProfile(
            host=cast(str, profile_values["host"]),
            port=cast(int, profile_values["port"]),
            client_id=cast(int, profile_values["client_id"]),
            read_only_mode=cast(bool, profile_values["read_only_mode"]),
            environment=cast(str, profile_values["environment"]),
            connection_timeout=cast(float, profile_values["connection_timeout"]),
            validated_at=datetime.fromisoformat(cast(str, profile_values["validated_at"])),
        ),
        access_mode=DataAccessMode.synthetic(),
        read_only_methods={"reqHistoricalData": transport.reqHistoricalData},
    )

    assert boundary.access_mode.mode == "synthetic"
    assert boundary.access_mode.ci_allowed is True
    assert boundary.access_mode.allows_external_api is False

    with pytest.raises(ReadOnlyBoundaryViolation, match="forbids API calls"):
        boundary.request_historical_data("synthetic contract", env={}, ci=True)

    assert transport.external_call_count == 0
    assert transport.synthetic_call_count == 0


def test_manifest_pacing_chunks_and_resume_compose_on_synthetic_fixture() -> None:
    payload = _historical_payload()
    request_spec = _request_spec()
    manifest = _manifest(request_spec)
    policy = _pacing_policy()
    complete = _complete_chunk(payload, chunk_id="hchunk_synthetic_ibkr_e2e_a")
    pending = _not_started_chunk()

    assert (
        plan_historical_request_transition(request_spec)
        is HistoricalRequestLifecycleState.REQUEST_PLANNED
    )
    assert (
        authorize_historical_request_transition(manifest)
        is HistoricalRequestLifecycleState.REQUEST_AUTHORIZED
    )
    assert require_validated_manifest_for_provider_pull(manifest) is manifest
    assert policy.accounting_weight(request_spec.what_to_show) == 1
    assert policy.accounting_weight("BID_ASK") == 2

    ledger = HistoricalPullLedger.create(
        pull_id="hpl_synthetic_ibkr_e2e_v1",
        manifest_id=manifest.manifest_id,
        chunk_records=(complete, pending),
        expected_chunk_ids=("hchunk_synthetic_ibkr_e2e_a", "hchunk_synthetic_ibkr_e2e_b"),
        started_at=CREATED_AT,
    )

    assert ledger.status is HistoricalPullLedgerStatus.IN_PROGRESS
    assert ledger.completed_chunk_ids() == ("hchunk_synthetic_ibkr_e2e_a",)
    assert ledger.pending_chunk_ids_for_resume(ledger.resume_token) == (
        "hchunk_synthetic_ibkr_e2e_b",
    )
    assert HistoricalPullLedger.from_mapping(ledger.to_mapping()).resume_token == (
        ledger.resume_token
    )

    duplicate = _complete_chunk(payload, chunk_id="hchunk_synthetic_ibkr_duplicate")
    with pytest.raises(DataFoundationValidationError, match="duplicate chunk request"):
        HistoricalPullLedger.create(
            pull_id="hpl_synthetic_ibkr_duplicate",
            manifest_id=manifest.manifest_id,
            chunk_records=(complete, duplicate),
            expected_chunk_ids=(complete.chunk_id, duplicate.chunk_id),
            started_at=CREATED_AT,
            finished_at=CREATED_AT,
        )

    with pytest.raises(DataFoundationValidationError, match="missing expected chunks"):
        HistoricalPullLedger.create(
            pull_id="hpl_synthetic_ibkr_missing_chunk",
            manifest_id=manifest.manifest_id,
            chunk_records=(complete, pending),
            expected_chunk_ids=(
                complete.chunk_id,
                pending.chunk_id,
                "hchunk_synthetic_missing",
            ),
            started_at=CREATED_AT,
        )


def test_composed_fail_closed_guards_block_before_synthetic_payload_use() -> None:
    policy = IBKRClientIdPolicy.default()
    transport = SyntheticFixtureTransport(_historical_payload())

    for forbidden_client_id in (101, 102):
        with pytest.raises(DataFoundationValidationError, match="hard-blocked"):
            policy.validate_client_id(forbidden_client_id)

    with pytest.raises(DataFoundationValidationError, match="missing HistoricalRequestManifest"):
        _synthetic_pull(
            manifest=None,
            pacing_policy=_pacing_policy(),
            transport=transport,
        )
    assert transport.synthetic_call_count == 0

    with pytest.raises(DataFoundationValidationError, match="missing RequestPacingPolicy"):
        _synthetic_pull(
            manifest=_manifest(),
            pacing_policy=None,
            transport=transport,
        )
    assert transport.synthetic_call_count == 0

    canonical = {
        "instrument_id": "inst_synth_es",
        "contract_id": "fut_es_202606",
        "series_id": "series_es_front_unadjusted",
        "bar_start_ts": "2026-06-01T14:30:00+00:00",
        "bar_end_ts": "2026-06-01T14:31:00+00:00",
        "event_ts": "2026-06-01T14:30:30+00:00",
        "ingested_at": "2026-06-01T14:31:45+00:00",
        "open": "5000.25",
        "high": "5001.00",
        "low": "4999.75",
        "close": "5000.50",
        "volume": "100",
        "source": "dsrc_ibkr_historical",
        "source_request_id": "hrs_synthetic_ibkr_e2e_es_m6",
        "data_version": "dsv_synthetic_ibkr_e2e_v1",
        "quality_flags": (),
        "session_label": "ETH",
    }
    with pytest.raises(DataFoundationValidationError, match="missing required fields"):
        CanonicalBarRecord.from_mapping(canonical)

    continuous = ContinuousFuturesSeriesRecord(
        series_id="series_synthetic_es_continuous",
        root_symbol="ES",
        provider="IBKR",
        provenance_label="provider_continuous",
        orderable=False,
        dated_truth=False,
        roll_adjustment_note=(
            "provider continuous diagnostic series; not orderable and not dated truth"
        ),
        source_retrieved_at=CREATED_AT,
    )
    with pytest.raises(DataFoundationValidationError, match="cannot be used"):
        require_dated_contract_truth(continuous)
