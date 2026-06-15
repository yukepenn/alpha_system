from __future__ import annotations

import pytest

from alpha_system.agent_factory.memory.store import (
    ResearchMemoryStoreError,
    pending_signals,
    persist_reviewer_adjudication,
    persist_route,
    read_ledger,
    resolve_research_memory_dir,
    scan_research_memory,
)

CREATED_AT = "2026-06-15T00:00:00Z"


def _idea() -> dict:
    return {
        "alpha_spec_id": "aspec_unit",
        "mechanism_id": "mech_unit",
        "hypothesis_id": "hyp_unit",
        "source": "research/seeds/unit.idea.yaml",
    }


def _readout(factor_id: str = "base_ohlcv_distance_to_vwap") -> dict:
    return {
        "study_kind": "main_effect",
        "slice_spec": {
            "slice_id": "ES_2020_60m",
            "study_kind": "main_effect",
            "feature_inputs": [
                {
                    "role": "factor",
                    "factor_id": factor_id,
                    "pack_ref": "fver_unit",
                    "feature_request_id": "freq_unit",
                }
            ],
            "label_inputs": [
                {
                    "role": "label",
                    "label_id": "cost_adjusted_fwd_ret",
                    "pack_ref": "lver_unit",
                    "label_spec_id": "lspec_unit",
                }
            ],
        },
        "readout": {
            "factor_diagnostics_report": {
                "quality_summary": {
                    "pearson_ic": -0.0557,
                    "rank_ic": -0.0150,
                    "ic_power_n_eff": 327155,
                    "ic_power_mde_abs_ic": 0.0034,
                }
            }
        },
    }


def _signal_route(signal_ref: str = "readout:fpmain_unit") -> dict:
    return {
        "verdict": "INCONCLUSIVE",
        "action": "reviewer_pending_shelf",
        "record_type": "SignalPendingReviewerRecord",
        "alpha_spec_id": "aspec_unit",
        "promotion_eligible": False,
        "memory_record": {
            "requires_reviewer": True,
            "eligible": False,
            "pearson_ic": -0.0557,
            "original_verdict_ref": signal_ref,
        },
    }


def test_persist_signal_route_writes_queryable_provenance(tmp_path) -> None:
    path = persist_route(
        route_result=_signal_route(),
        idea=_idea(),
        readout=_readout(),
        verdict={"verdict": "INCONCLUSIVE", "reason_code": "SIGNAL_PENDING_REVIEWER"},
        created_at=CREATED_AT,
        memory_dir=tmp_path,
    )

    assert path.name == "signal_shelf.jsonl"
    rows = read_ledger("reviewer_pending_shelf", memory_dir=tmp_path)
    assert len(rows) == 1
    row = rows[0]
    assert row["verdict"] == "INCONCLUSIVE"
    assert row["reason_code"] == "SIGNAL_PENDING_REVIEWER"
    assert row["reviewer_required"] is True
    assert row["promotion_eligible"] is False
    assert row["factor_id"] == "base_ohlcv_distance_to_vwap"
    assert row["label_version_id"] == "lver_unit"
    assert row["slice_id"] == "ES_2020_60m"
    assert row["pearson_ic"] == pytest.approx(-0.0557)
    assert row["n_eff"] == 327155


def test_persist_is_append_only(tmp_path) -> None:
    for factor in ("factor_a", "factor_b"):
        persist_route(
            route_result=_signal_route(),
            idea=_idea(),
            readout=_readout(factor_id=factor),
            verdict={"verdict": "INCONCLUSIVE", "reason_code": "SIGNAL_PENDING_REVIEWER"},
            created_at=CREATED_AT,
            memory_dir=tmp_path,
        )
    rows = read_ledger("signal_shelf.jsonl", memory_dir=tmp_path)
    assert [row["factor_id"] for row in rows] == ["factor_a", "factor_b"]


def test_reject_and_signal_route_to_distinct_ledgers(tmp_path) -> None:
    reject = {
        "verdict": "REJECT",
        "action": "graveyard",
        "record_type": "RejectedIdeaRecord",
        "alpha_spec_id": "aspec_unit",
        "promotion_eligible": False,
        "memory_record": {"rejected_id": "rej_unit"},
    }
    persist_route(
        route_result=reject,
        idea=_idea(),
        readout=_readout(factor_id="range_contraction"),
        verdict={"verdict": "REJECT", "reason_code": "WELL_POWERED_NULL"},
        created_at=CREATED_AT,
        memory_dir=tmp_path,
    )
    persist_route(
        route_result=_signal_route(),
        idea=_idea(),
        readout=_readout(),
        verdict={"verdict": "INCONCLUSIVE", "reason_code": "SIGNAL_PENDING_REVIEWER"},
        created_at=CREATED_AT,
        memory_dir=tmp_path,
    )

    assert len(read_ledger("graveyard", memory_dir=tmp_path)) == 1
    assert len(read_ledger("signal_shelf.jsonl", memory_dir=tmp_path)) == 1
    rejects = scan_research_memory(memory_dir=tmp_path, verdict="REJECT")
    assert len(rejects) == 1
    assert rejects[0]["factor_id"] == "range_contraction"


def test_scan_filters_by_factor_and_slice(tmp_path) -> None:
    for factor in ("base_ohlcv_distance_to_vwap", "base_ohlcv_opening_range"):
        persist_route(
            route_result=_signal_route(),
            idea=_idea(),
            readout=_readout(factor_id=factor),
            verdict={"verdict": "INCONCLUSIVE", "reason_code": "SIGNAL_PENDING_REVIEWER"},
            created_at=CREATED_AT,
            memory_dir=tmp_path,
        )
    hits = scan_research_memory(memory_dir=tmp_path, factor_id="base_ohlcv_opening_range")
    assert len(hits) == 1
    assert hits[0]["factor_id"] == "base_ohlcv_opening_range"
    assert scan_research_memory(memory_dir=tmp_path, slice_id="ES_2020_60m").__len__() == 2


def test_persist_refuses_promotion_eligible_route(tmp_path) -> None:
    bad = {**_signal_route(), "promotion_eligible": True}
    with pytest.raises(ResearchMemoryStoreError):
        persist_route(
            route_result=bad,
            idea=_idea(),
            readout=_readout(),
            verdict="INCONCLUSIVE",
            created_at=CREATED_AT,
            memory_dir=tmp_path,
        )


def test_persist_rejects_unknown_action(tmp_path) -> None:
    bad = {**_signal_route(), "action": "promote_to_factor_library"}
    with pytest.raises(ResearchMemoryStoreError):
        persist_route(
            route_result=bad,
            idea=_idea(),
            readout=_readout(),
            verdict="INCONCLUSIVE",
            created_at=CREATED_AT,
            memory_dir=tmp_path,
        )


def test_pending_signals_excludes_adjudicated(tmp_path) -> None:
    for ref, factor in (("readout:a", "factor_a"), ("readout:b", "factor_b")):
        persist_route(
            route_result=_signal_route(signal_ref=ref),
            idea=_idea(),
            readout=_readout(factor_id=factor),
            verdict={"verdict": "INCONCLUSIVE", "reason_code": "SIGNAL_PENDING_REVIEWER"},
            created_at=CREATED_AT,
            memory_dir=tmp_path,
        )
    assert len(pending_signals(memory_dir=tmp_path)) == 2

    persist_reviewer_adjudication(
        {
            "schema": "alpha_system.research_lane.reviewer_adjudication.v1",
            "signal_ref": "readout:a",
            "routing_intent": "CONFIRMED_FOR_TRUSTED_STUDY",
            "promotion_eligible": False,
        },
        memory_dir=tmp_path,
    )
    pending = pending_signals(memory_dir=tmp_path)
    assert len(pending) == 1
    assert pending[0]["memory_record"]["original_verdict_ref"] == "readout:b"


def test_persist_adjudication_refuses_promotion_eligible(tmp_path) -> None:
    with pytest.raises(ResearchMemoryStoreError):
        persist_reviewer_adjudication(
            {"signal_ref": "readout:a", "promotion_eligible": True},
            memory_dir=tmp_path,
        )


def test_resolve_dir_prefers_override_then_env(tmp_path) -> None:
    assert resolve_research_memory_dir(tmp_path) == tmp_path
    env = {"ALPHA_DATA_ROOT": "/data/alpha"}
    resolved = resolve_research_memory_dir(None, env=env)
    assert resolved.as_posix() == "/data/alpha/research_memory"
