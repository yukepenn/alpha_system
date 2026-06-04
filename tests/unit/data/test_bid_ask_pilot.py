from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import pytest

from alpha_system.data.foundation.bid_ask_pilot import (
    BID_ASK_PILOT_PLAN,
    BID_ASK_PILOT_PLAN_ID,
    BID_ASK_PILOT_WHAT_TO_SHOW,
    REQUIRED_BID_ASK_PILOT_PLAN_FIELDS,
    BidAskPilotPlan,
    compute_spread_proxy_metrics,
)
from alpha_system.data.foundation.datasets import CoverageReport, DataQualityReport
from alpha_system.data.foundation.requests import (
    HistoricalChunkRecord,
    HistoricalPullLedger,
    HistoricalRequestManifest,
    HistoricalRequestSpec,
    RequestPacingPolicy,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError

ROOT = Path(__file__).resolve().parents[3]
PILOT_CONFIG_PATH = ROOT / "configs" / "data" / "bid_ask_pilot_plan.json"
PACING_CONFIG_PATH = ROOT / "configs" / "data" / "request_pacing_policy_to_be_verified.json"
SPREAD_FIXTURE_PATH = (
    ROOT / "tests" / "fixtures" / "data" / "synthetic_bid_ask_spread_proxy_inputs.json"
)
QUALITY_FIXTURE_PATH = (
    ROOT / "tests" / "fixtures" / "data" / "synthetic_quality_coverage_inputs.json"
)

START_TS = datetime(2025, 1, 2, 14, 30, tzinfo=UTC)
MID_TS = datetime(2025, 1, 3, 0, 0, tzinfo=UTC)
END_TS = datetime(2025, 1, 3, 22, 0, tzinfo=UTC)
CREATED_AT = datetime(2026, 6, 4, 1, 0, tzinfo=UTC)


def _json_file(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _pilot_values(**overrides: object) -> dict[str, Any]:
    values = _json_file(PILOT_CONFIG_PATH)
    values.update(overrides)
    return values


def _pacing_policy() -> RequestPacingPolicy:
    return RequestPacingPolicy.from_mapping(_json_file(PACING_CONFIG_PATH))


def _request_spec(**overrides: object) -> HistoricalRequestSpec:
    values: dict[str, object] = {
        "request_spec_id": "hrs_synthetic_bid_ask_es_h5_20250102",
        "source_id": "dsrc_ibkr_historical",
        "symbol_root": "ES",
        "contract_ref": "fcr_synthetic_es_h5",
        "sec_type": "FUT",
        "exchange": "CME",
        "currency": "USD",
        "bar_size": "1 min",
        "what_to_show": "BID_ASK",
        "use_rth": False,
        "duration": "2 D",
        "end_datetime_policy": "explicit_end_ts_required",
        "start_ts": START_TS.isoformat(),
        "end_ts": END_TS.isoformat(),
        "chunk_policy": {
            "planned_chunks": 2,
            "max_duration": "1 D",
            "policy": "synthetic_bid_ask_planning_only",
        },
        "client_id": 201,
    }
    values.update(overrides)
    return HistoricalRequestSpec.from_mapping(values)


def _manifest(*, request_spec: HistoricalRequestSpec | None = None) -> HistoricalRequestManifest:
    spec = _request_spec() if request_spec is None else request_spec
    return HistoricalRequestManifest.create(
        manifest_id="hrm_synthetic_bid_ask_es_h5_manifest_v1",
        batch_id="batch_synthetic_bid_ask_pilot_planning_only",
        request_specs=(spec,),
        chunk_count=2,
        expected_coverage={
            "synthetic": True,
            "coverage_status": "planned_only_not_requested",
            "what_to_show": "BID_ASK",
            "symbols": ("ES",),
            "real_coverage_claim": False,
            "authorization_claim": False,
        },
        pacing_policy_id="rpp_ibkr_historical_conservative_tobeverified_v1",
        data_root="~/alpha_data/alpha_system",
        created_by="DATA-P20 synthetic BID_ASK pilot test",
        created_at=CREATED_AT,
    )


def _ledger(manifest: HistoricalRequestManifest) -> HistoricalPullLedger:
    chunks = (
        HistoricalChunkRecord.from_mapping(
            {
                "chunk_id": "hchunk_synth_bidask_es_20250102_a",
                "request_spec_id": manifest.request_specs[0].request_spec_id,
                "symbol_root": "ES",
                "contract_ref": "fcr_synthetic_es_h5",
                "start_ts": START_TS.isoformat(),
                "end_ts": MID_TS.isoformat(),
                "status": "NOT_STARTED",
                "attempt_count": 0,
                "provider_request_id": None,
                "raw_object_ref": None,
                "row_count": None,
                "error_ref": None,
                "retrieved_at": None,
            }
        ),
        HistoricalChunkRecord.from_mapping(
            {
                "chunk_id": "hchunk_synth_bidask_es_20250103_b",
                "request_spec_id": manifest.request_specs[0].request_spec_id,
                "symbol_root": "ES",
                "contract_ref": "fcr_synthetic_es_h5",
                "start_ts": MID_TS.isoformat(),
                "end_ts": END_TS.isoformat(),
                "status": "NOT_STARTED",
                "attempt_count": 0,
                "provider_request_id": None,
                "raw_object_ref": None,
                "row_count": None,
                "error_ref": None,
                "retrieved_at": None,
            }
        ),
    )
    return HistoricalPullLedger.create(
        pull_id="hpl_synthetic_bid_ask_pilot_001",
        manifest_id=manifest.manifest_id,
        chunk_records=chunks,
        expected_chunk_ids=(chunk.chunk_id for chunk in chunks),
        started_at=CREATED_AT,
    )


def _quality_fixture() -> dict[str, Any]:
    return _json_file(QUALITY_FIXTURE_PATH)


def _quality_report() -> DataQualityReport:
    return DataQualityReport.from_canonical_bars(
        quality_report_id="dqr_synthetic_bidask_linkage",
        dataset_version_id="dsv_synthetic_bidask_v1",
        bars=cast(list[Mapping[str, object]], _quality_fixture()["bars"]),
    )


def _coverage_report() -> CoverageReport:
    fixture = _quality_fixture()
    return CoverageReport.from_canonical_bars(
        coverage_report_id="covr_synthetic_bidask_linkage",
        dataset_version_id="dsv_synthetic_bidask_v1",
        bars=cast(list[Mapping[str, object]], fixture["bars"]),
        expected_intervals=cast(list[Mapping[str, object]], fixture["expected_intervals"]),
    )


def test_bid_ask_pilot_plan_is_optional_bounded_and_configured() -> None:
    plan = BidAskPilotPlan.from_mapping(_pilot_values())

    assert tuple(plan.to_mapping()) == REQUIRED_BID_ASK_PILOT_PLAN_FIELDS
    assert plan.plan_id == BID_ASK_PILOT_PLAN_ID
    assert plan.optional is True
    assert plan.pilot_only is True
    assert plan.research_diagnostics_only is True
    assert plan.secondary_to_primary_trades_panel is True
    assert plan.what_to_show == BID_ASK_PILOT_WHAT_TO_SHOW
    assert plan.symbols == ("ES",)
    assert plan.max_symbols == 1
    assert plan.max_contracts == 1
    assert plan.max_date_window_days == 3
    assert plan.max_chunk_count == 4
    assert plan.max_local_storage_bytes == 5 * 1024 * 1024
    assert plan.merge_into_primary_trades_panel is False
    assert plan.implies_pull_authorization is False
    assert plan.external_provider_call is False
    assert plan.real_data_pull is False
    assert BID_ASK_PILOT_PLAN.to_mapping() == plan.to_mapping()


def test_bid_ask_pilot_plan_fails_closed_when_bounds_or_posture_are_weakened() -> None:
    with pytest.raises(DataFoundationValidationError, match="must be optional"):
        BidAskPilotPlan.from_mapping(_pilot_values(optional=False))

    with pytest.raises(DataFoundationValidationError, match="what_to_show must be BID_ASK"):
        BidAskPilotPlan.from_mapping(_pilot_values(what_to_show="TRADES"))

    with pytest.raises(DataFoundationValidationError, match="symbols exceed max_symbols"):
        BidAskPilotPlan.from_mapping(_pilot_values(symbols=["ES", "NQ"], max_symbols=1))

    with pytest.raises(DataFoundationValidationError, match="date window exceeds"):
        BidAskPilotPlan.from_mapping(_pilot_values(end_date="2025-01-20"))

    with pytest.raises(DataFoundationValidationError, match="must not merge"):
        BidAskPilotPlan.from_mapping(_pilot_values(merge_into_primary_trades_panel=True))

    with pytest.raises(DataFoundationValidationError, match="must not authorize"):
        BidAskPilotPlan.from_mapping(_pilot_values(implies_pull_authorization=True))


def test_bid_ask_pilot_reuses_p08_pacing_with_double_accounting() -> None:
    plan = BidAskPilotPlan.from_mapping(_pilot_values())
    policy = plan.validate_pacing_policy(_pacing_policy())

    assert policy.bid_ask_counts_double is True
    assert policy.accounting_weight("TRADES") == 1
    assert policy.accounting_weight("BID_ASK") == 2

    with pytest.raises(DataFoundationValidationError, match="missing RequestPacingPolicy"):
        plan.validate_pacing_policy(None)


def test_bid_ask_manifest_pacing_and_resume_contracts_are_required() -> None:
    plan = BidAskPilotPlan.from_mapping(_pilot_values())
    manifest = _manifest()
    ledger = _ledger(manifest)

    preflight = plan.validate_provider_pull_contracts(
        manifest=manifest,
        pacing_policy=_pacing_policy(),
        pull_ledger=ledger,
    )

    assert preflight["provider_pull_authorized"] is False
    assert preflight["external_provider_call"] is False
    assert preflight["manifest_id"] == manifest.manifest_id

    trades_manifest = _manifest(request_spec=_request_spec(what_to_show="TRADES"))
    with pytest.raises(DataFoundationValidationError, match="must use what_to_show BID_ASK"):
        plan.validate_manifest_scope(trades_manifest)

    over_cap_manifest = HistoricalRequestManifest.create(
        manifest_id="hrm_synthetic_bid_ask_es_h5_manifest_over_cap",
        batch_id="batch_synthetic_bid_ask_pilot_planning_only",
        request_specs=(manifest.request_specs[0],),
        chunk_count=5,
        expected_coverage=manifest.expected_coverage,
        pacing_policy_id=manifest.pacing_policy_id,
        data_root=manifest.data_root,
        created_by=manifest.created_by,
        created_at=CREATED_AT,
    )
    with pytest.raises(DataFoundationValidationError, match="chunk_count exceeds"):
        plan.validate_manifest_scope(over_cap_manifest)

    with pytest.raises(DataFoundationValidationError, match="missing HistoricalPullLedger"):
        plan.validate_provider_pull_contracts(
            manifest=manifest,
            pacing_policy=_pacing_policy(),
            pull_ledger=None,
        )


def test_bid_ask_pilot_reuses_p16_quality_and_coverage_linkage() -> None:
    plan = BidAskPilotPlan.from_mapping(_pilot_values())
    quality = _quality_report()
    coverage = _coverage_report()

    linked_quality, linked_coverage = plan.require_quality_coverage_contract(
        quality_report=quality,
        coverage_report=coverage,
    )

    assert linked_quality is quality
    assert linked_coverage is coverage

    with pytest.raises(DataFoundationValidationError, match="missing DataQualityReport"):
        plan.require_quality_coverage_contract(
            quality_report=None,
            coverage_report=coverage,
        )


def test_spread_proxy_scaffold_computes_and_rejects_invalid_inputs() -> None:
    payload = _json_file(SPREAD_FIXTURE_PATH)
    observations = cast(list[Mapping[str, object]], payload["observations"])
    invalid = cast(list[Mapping[str, object]], payload["invalid_observations"])

    metrics = compute_spread_proxy_metrics(observations)

    assert len(metrics) == 2
    assert metrics[0].spread == Decimal("0.25")
    assert metrics[0].mid == Decimal("5000.125")
    assert metrics[0].to_mapping()["spread_bps"] == "0.499988"
    assert metrics[0].pilot_only is True
    assert metrics[0].research_diagnostics_only is True
    assert metrics[0].tradable_cost_claim is False
    assert metrics[0].liquidity_truth_claim is False
    assert metrics[0].feeds_canonical_trades_panel is False

    with pytest.raises(DataFoundationValidationError, match="ask must be greater"):
        compute_spread_proxy_metrics(invalid)

    bad_bid = dict(observations[0])
    bad_bid["bid"] = "0"
    with pytest.raises(DataFoundationValidationError, match="bid must be positive"):
        compute_spread_proxy_metrics((bad_bid,))
