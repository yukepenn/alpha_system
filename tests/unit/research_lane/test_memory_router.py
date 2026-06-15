from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from alpha_system.governance.family_fdr_correction import correct_family
from alpha_system.governance.family_fdr_ledger import (
    FamilyFdrLedger,
    create_family_fdr_ledger_record,
)
from alpha_system.governance.idea_draft import build_idea_validation_bundle
from alpha_system.governance.ids import GovernanceIdKind, generate_governance_id
from alpha_system.governance.requeue import REQUEUE_REASON
from alpha_system.governance.validation import GovernanceValidationError
from alpha_system.research_lane import memory_router as memory_router_module
from alpha_system.research_lane.memory_router import route_verdict_to_memory

# The historical co-mined family the independent reviewer adjudicated REWORK
# (prior_session_high_sweep_and_reclaim, ES_2020_120m, net_excursion): 7 sibling
# pa_setup ideas against one slice, each with a surrogate run_count of 64.
_HISTORICAL_FAMILY_ID = "pa_setup_prior_session_high_sweep_and_reclaim"
_HISTORICAL_SLICE_ID = "ES_2020_120m"
_HISTORICAL_RUN_COUNT = 64
_HISTORICAL_BATCH_SIZE = 7

FIXTURE_IDEA = Path("research/idea_to_verdict_loop_v0/fixtures/day_of_week.idea.yaml")
TIMESTAMP = "2026-06-14T00:00:00Z"


def test_reject_routes_to_graveyard_keyed_by_alpha_spec_id() -> None:
    bundle = _bundle()

    result = route_verdict_to_memory(
        {
            "verdict": "REJECT",
            "reason_code": "DATA_QUALITY",
            "why": "Pre-test gate failed before interpretation.",
        },
        bundle.idea_draft,
        _readout(bundle),
        created_at=TIMESTAMP,
    )

    payload = result.to_dict()
    assert payload["action"] == "graveyard"
    assert payload["record_type"] == "RejectedIdeaRecord"
    assert payload["memory_record"]["alpha_spec_id_or_hypothesis_id"] == (
        bundle.idea_draft.alpha_spec_id
    )
    assert payload["memory_record"]["rejected_id"].startswith("rej_")
    assert payload["promotion_eligible"] is False
    assert payload["probe_spent"] is False
    assert payload["exploratory_refusal"]["status"] == "refused"


def test_reject_fails_closed_before_graveyard_write_without_alpha_spec_id(monkeypatch) -> None:
    bundle = _bundle()
    called = False

    def forbidden_write(**kwargs):
        nonlocal called
        called = True
        raise AssertionError("graveyard write must not be reached")

    monkeypatch.setattr(memory_router_module, "create_rejected_idea_record", forbidden_write)
    idea = bundle.idea_draft.to_dict()
    del idea["alpha_spec_id"]

    with pytest.raises(GovernanceValidationError) as exc_info:
        route_verdict_to_memory("REJECT", idea, _readout(bundle), created_at=TIMESTAMP)

    assert called is False
    assert exc_info.value.issues[0].field == "alpha_spec_id"


def test_data_gap_routes_to_valid_requeue_without_spending_probe() -> None:
    bundle = _bundle()

    result = route_verdict_to_memory(
        {
            "verdict": "DATA_GAP",
            "reason_code": "SUBSTRATE_GAP",
            "why": "Pre-test gate reports missing bounded slice metadata.",
        },
        bundle.idea_draft,
        _readout(bundle),
        created_at=TIMESTAMP,
    )

    payload = result.to_dict()
    assert payload["action"] == "requeue"
    assert payload["record_type"] == "RequeuedVerdictRecord"
    assert payload["memory_record"]["requeue_reason"] == REQUEUE_REASON
    assert payload["memory_record"]["eligible"] is False
    assert payload["memory_record"]["original_verdict_ref"] == "readout:unit_readout"
    assert payload["probe_spent"] is False
    assert payload["promotion_eligible"] is False


def test_inconclusive_routes_to_requeue_preserving_verdict_label() -> None:
    # INCONCLUSIVE (real probe ran, clean surrogate, but underpowered / no establishable
    # effect) routes to a reason-coded requeue like DATA_GAP, but the honest verdict label
    # is preserved on the result (not relabeled DATA_GAP).
    bundle = _bundle()

    result = route_verdict_to_memory(
        {
            "verdict": "INCONCLUSIVE",
            "reason_code": "UNDERPOWERED",
            "why": "Real probe ran with a clean surrogate gate but the effect is underpowered.",
        },
        bundle.idea_draft,
        _readout(bundle),
        created_at=TIMESTAMP,
    )

    payload = result.to_dict()
    assert payload["action"] == "requeue"
    assert payload["verdict"] == "INCONCLUSIVE"
    assert payload["record_type"] == "RequeuedVerdictRecord"
    assert payload["memory_record"]["eligible"] is False
    assert payload["probe_spent"] is False
    assert payload["promotion_eligible"] is False


def test_signal_pending_reviewer_routes_to_non_promoting_shelf() -> None:
    # A well-powered main_effect IC signal: the machine records it to a
    # reviewer-pending shelf (non-promoting) instead of burying it in a generic
    # requeue. Primary verdict stays INCONCLUSIVE; it never auto-promotes.
    bundle = _bundle()

    result = route_verdict_to_memory(
        {
            "verdict": "INCONCLUSIVE",
            "reason_code": "SIGNAL_PENDING_REVIEWER",
            "why": "Well-powered main-effect probe resolved an IC above the floor.",
        },
        bundle.idea_draft,
        _main_effect_signal_readout(bundle),
        created_at=TIMESTAMP,
    )

    payload = result.to_dict()
    assert payload["action"] == "reviewer_pending_shelf"
    assert payload["record_type"] == "SignalPendingReviewerRecord"
    assert payload["verdict"] == "INCONCLUSIVE"
    assert payload["promotion_eligible"] is False
    assert payload["probe_spent"] is False
    record = payload["memory_record"]
    assert record["requires_reviewer"] is True
    assert record["eligible"] is False
    assert record["pearson_ic"] == pytest.approx(-0.0557)
    assert record["rank_ic"] == pytest.approx(-0.0150)
    assert record["n_eff"] == 327155
    assert record["factor_id"] == "base_ohlcv_distance_to_vwap"
    assert record["slice_id"] == "ES_2020_60m"


def test_setup_lane_signal_pending_reviewer_routes_to_shelf_without_ic_summary() -> None:
    # The setup/path-outcome lane (context_not_equal_trigger) has NO main_effect IC
    # quality summary. A surrogate-gated signed net_excursion mean_lift must still
    # reach the reviewer shelf (no missing_main_effect_quality_summary error).
    # No family-FDR ledger supplied -> the Stage-B gate is opt-in and a no-op, so
    # this preserves the pre-Stage-B always-shelf behavior.
    bundle = _bundle()

    result = route_verdict_to_memory(
        {
            "verdict": "INCONCLUSIVE",
            "reason_code": "SIGNAL_PENDING_REVIEWER",
            "why": "Surrogate-gated net_excursion resolved a signed directional asymmetry.",
        },
        bundle.idea_draft,
        _setup_lane_signal_readout(bundle),
        created_at=TIMESTAMP,
    )

    payload = result.to_dict()
    assert payload["action"] == "reviewer_pending_shelf"
    assert payload["record_type"] == "SignalPendingReviewerRecord"
    assert payload["verdict"] == "INCONCLUSIVE"
    assert payload["promotion_eligible"] is False
    record = payload["memory_record"]
    assert record["study_kind"] == "context_not_equal_trigger"
    assert record["requires_reviewer"] is True
    assert record["eligible"] is False
    # The signed net excursion + surrogate evidence is preserved; no IC fields.
    assert record["pearson_ic"] is None
    assert record["rank_ic"] is None
    assert record["detectable_abs_ic"] is None
    assert record["net_mean_lift"] == pytest.approx(-0.0031)
    # observed_effect is optional: absent in the ZERO_PASS_MET path -> None.
    assert record["observed_effect"] is None
    assert record["outcome_label_type"] == "net_excursion"
    assert record["surrogate_gate_pass_count"] == 0
    assert record["surrogate_run_count"] == 200
    # n_eff sourced from the top-level power statement (mirrors verdict_report).
    assert record["n_eff"] == 412
    assert record["slice_id"] == "ES_2020_120m"


def test_setup_lane_signal_falls_back_to_gate_conditioned_n_eff_and_observed_effect() -> None:
    # The enriched surrogate gate (carrying conditioned_n_eff + observed_effect) is
    # the source when no top-level power statement is present.
    bundle = _bundle()
    readout = _setup_lane_signal_readout(bundle)
    del readout["power"]
    gate = dict(readout["surrogate_fdr_gate"])  # type: ignore[arg-type]
    gate["conditioned_n_eff"] = 333
    gate["observed_effect"] = -0.0031
    readout["surrogate_fdr_gate"] = gate

    result = route_verdict_to_memory(
        {"verdict": "INCONCLUSIVE", "reason_code": "SIGNAL_PENDING_REVIEWER"},
        bundle.idea_draft,
        readout,
        created_at=TIMESTAMP,
    )

    record = result.to_dict()["memory_record"]
    assert record["n_eff"] == 333
    assert record["observed_effect"] == pytest.approx(-0.0031)


def test_setup_lane_lone_adequate_signal_clears_family_fdr_and_shelves(tmp_path) -> None:
    # CROSS_IDEA_FDR_BUDGET_V1 Stage B: a lone co-mined idea with adequate surrogate
    # resolution (run=200, m=1, BH alpha=0.10) and a significant corrected p still
    # reaches the reviewer shelf when the family-FDR gate is wired. The corrected
    # verdict is attached so the independent reviewer sees the multiplicity context.
    bundle = _bundle()
    ledger_path = _empty_ledger(tmp_path)

    result = route_verdict_to_memory(
        {"verdict": "INCONCLUSIVE", "reason_code": "SIGNAL_PENDING_REVIEWER"},
        bundle.idea_draft,
        _setup_lane_signal_readout(bundle),
        created_at=TIMESTAMP,
        family_fdr_ledger_path=ledger_path,
    )

    payload = result.to_dict()
    assert payload["action"] == "reviewer_pending_shelf"
    assert payload["record_type"] == "SignalPendingReviewerRecord"
    family = payload["memory_record"]["family_fdr_verdict"]
    assert family["eligible"] is True
    assert family["reason"] == "eligible"
    assert family["method"] == "benjamini_hochberg"
    assert family["alpha_fw"] == pytest.approx(0.10)
    assert family["family_size"] == 1
    assert family["provisional"] is True
    # The ledger accumulated this idea's per-test record (append-only).
    records = FamilyFdrLedger(ledger_path).load_records()
    assert len(records) == 1
    assert records[0].run_count == 200


def test_historical_prior_high_sweep_seven_idea_batch_routes_to_requeue(tmp_path) -> None:
    # Regression: the historical prior_session_high_sweep_and_reclaim signal
    # (p=(0+1)/(64+1)=1/65, run_count=64) inside its REAL co-mined batch of 7 sibling
    # pa_setup ideas. With m=7 at the BH policy default alpha=0.10 the required
    # run_count is ceil(7/0.10)-1 = 69 > 64, so the surrogate count CANNOT resolve the
    # corrected threshold -> not eligible -> REQUEUE (not the reviewer shelf, not
    # graveyard). The machine now enforces deterministically what the independent
    # reviewer concluded by hand (REWORK).
    bundle = _bundle()
    ledger_path = _empty_ledger(tmp_path)
    # Seed the 6 co-mined siblings into the ledger (same alpha_spec + family + slice;
    # distinct mechanism idea_keys), each with the historical run_count=64.
    _seed_siblings(
        ledger_path,
        alpha_spec_id=bundle.idea_draft.alpha_spec_id,
        count=_HISTORICAL_BATCH_SIZE - 1,
    )

    readout = _historical_setup_readout(bundle)
    result = route_verdict_to_memory(
        {
            "verdict": "INCONCLUSIVE",
            "reason_code": "SIGNAL_PENDING_REVIEWER",
            "why": "Surrogate-gated net_excursion in a co-mined batch of 7 pa_setup ideas.",
        },
        bundle.idea_draft,
        readout,
        created_at=TIMESTAMP,
        family_fdr_ledger_path=ledger_path,
    )

    payload = result.to_dict()
    assert payload["action"] == "requeue"
    assert payload["record_type"] == "RequeuedVerdictRecord"
    # The honest verdict label is preserved (not relabeled DATA_GAP).
    assert payload["verdict"] == "INCONCLUSIVE"
    record = payload["memory_record"]
    assert record["eligible"] is False
    # Value-free reason: the surrogate run_count cannot resolve the corrected threshold.
    assert record["family_fdr_requeue_reason"] == "surrogate_resolution_inadequate"
    family = record["family_fdr_verdict"]
    assert family["eligible"] is False
    assert family["resolution_adequate"] is False
    assert family["rejected_null"] is True
    assert family["family_size"] == _HISTORICAL_BATCH_SIZE
    assert payload["promotion_eligible"] is False


def test_setup_lane_family_fdr_not_cleared_routes_to_requeue(tmp_path) -> None:
    # A signal whose corrected null is NOT rejected (a weak per-test p inside a large
    # batch, but with adequate resolution) routes to requeue with the distinct
    # family_fdr_not_cleared reason -- not graveyard, because more surrogates / a
    # filling batch may yet clear it.
    bundle = _bundle()
    ledger_path = _empty_ledger(tmp_path)
    # 4 siblings with a strong p (cleared) + this idea with a weak p but adequate
    # resolution so the ONLY failing dimension is the corrected significance.
    big_run = 5000
    _seed_siblings(
        ledger_path,
        alpha_spec_id=bundle.idea_draft.alpha_spec_id,
        count=4,
        gate_pass_count=0,
        run_count=big_run,
    )

    readout = _historical_setup_readout(bundle)
    # Weak per-test p: many surrogate passes (still adequate resolution at run=5000).
    readout["surrogate_fdr_gate"] = {
        "gate_status": "PASSED",
        "threshold_verdict": "zero-pass-met",
        "run_count": big_run,
        "gate_pass_count": 4000,
        "error_count": 0,
        "promotion_evidence": False,
    }

    result = route_verdict_to_memory(
        {"verdict": "INCONCLUSIVE", "reason_code": "SIGNAL_PENDING_REVIEWER"},
        bundle.idea_draft,
        readout,
        created_at=TIMESTAMP,
        family_fdr_ledger_path=ledger_path,
    )

    payload = result.to_dict()
    assert payload["action"] == "requeue"
    record = payload["memory_record"]
    assert record["family_fdr_requeue_reason"] == "family_fdr_not_cleared"
    assert record["family_fdr_verdict"]["resolution_adequate"] is True
    assert record["family_fdr_verdict"]["rejected_null"] is False


def test_main_effect_signal_routing_unchanged_by_family_fdr_ledger(tmp_path) -> None:
    # The family-FDR gate is setup-lane only. A main_effect signal must still shelve
    # even when a ledger path is supplied (no surrogate-p definition for IC yet), and
    # must NOT carry a family_fdr_verdict attachment.
    bundle = _bundle()
    ledger_path = _empty_ledger(tmp_path)

    result = route_verdict_to_memory(
        {"verdict": "INCONCLUSIVE", "reason_code": "SIGNAL_PENDING_REVIEWER"},
        bundle.idea_draft,
        _main_effect_signal_readout(bundle),
        created_at=TIMESTAMP,
        family_fdr_ledger_path=ledger_path,
    )

    payload = result.to_dict()
    assert payload["action"] == "reviewer_pending_shelf"
    assert "family_fdr_verdict" not in payload["memory_record"]
    # The setup-lane accumulator stays empty (main_effect never records into it).
    assert FamilyFdrLedger(ledger_path).load_records() == ()


def test_signal_pending_reviewer_never_writes_promotion_decision() -> None:
    bundle = _bundle()

    result = route_verdict_to_memory(
        {"verdict": "INCONCLUSIVE", "reason_code": "SIGNAL_PENDING_REVIEWER"},
        bundle.idea_draft,
        _main_effect_signal_readout(bundle),
        created_at=TIMESTAMP,
        # Even if reviewer-gated promotion inputs were (wrongly) supplied, a
        # SIGNAL_PENDING_REVIEWER must NOT become a PromotionDecision.
        reviewer_verdict_id=_id(GovernanceIdKind.REVIEWER_VERDICT, "rver"),
        evidence_bundle_id=_id(GovernanceIdKind.EVIDENCE_BUNDLE, "evb"),
        trial_ledger_refs=(_id(GovernanceIdKind.TRIAL_LEDGER_RECORD, "trial"),),
    )

    payload = result.to_dict()
    assert payload["record_type"] == "SignalPendingReviewerRecord"
    assert payload["record_type"] != "PromotionDecision"
    assert payload["action"] == "reviewer_pending_shelf"


def test_well_powered_null_reject_routes_to_graveyard() -> None:
    bundle = _bundle()

    result = route_verdict_to_memory(
        {"verdict": "REJECT", "reason_code": "WELL_POWERED_NULL"},
        bundle.idea_draft,
        _readout(bundle),
        created_at=TIMESTAMP,
    )

    payload = result.to_dict()
    assert payload["action"] == "graveyard"
    assert payload["record_type"] == "RejectedIdeaRecord"
    assert payload["promotion_eligible"] is False


@pytest.mark.parametrize("verdict", ["WATCH", "CANDIDATE"])
def test_watch_candidate_require_reviewer_verdict_id(verdict: str) -> None:
    bundle = _bundle()

    with pytest.raises(GovernanceValidationError) as exc_info:
        route_verdict_to_memory(
            {"verdict": verdict, "reason_code": "REGIME_UNSTABLE"},
            bundle.idea_draft,
            _readout(bundle),
            created_at=TIMESTAMP,
            evidence_bundle_id=_id(GovernanceIdKind.EVIDENCE_BUNDLE, "evb"),
            trial_ledger_refs=(_id(GovernanceIdKind.TRIAL_LEDGER_RECORD, "trial"),),
        )

    assert any(issue.field == "reviewer_verdict_id" for issue in exc_info.value.issues)


@pytest.mark.parametrize("verdict", ["WATCH", "CANDIDATE"])
def test_watch_candidate_create_only_reviewer_gated_promotion(verdict: str) -> None:
    bundle = _bundle()

    result = route_verdict_to_memory(
        {"verdict": verdict, "reason_code": "REGIME_UNSTABLE"},
        bundle.idea_draft,
        _readout(bundle),
        reviewer_verdict_id=_id(GovernanceIdKind.REVIEWER_VERDICT, "rver"),
        evidence_bundle_id=_id(GovernanceIdKind.EVIDENCE_BUNDLE, "evb"),
        trial_ledger_refs=(_id(GovernanceIdKind.TRIAL_LEDGER_RECORD, "trial"),),
        created_at=TIMESTAMP,
        probe_spent=True,
    )

    payload = result.to_dict()
    assert payload["action"] == "reviewer_gated_promotion"
    assert payload["record_type"] == "PromotionDecision"
    assert payload["memory_record"]["reviewer_verdict_id"].startswith("rver_")
    assert payload["memory_record"]["decision"] == verdict
    assert payload["memory_record"]["next_state"] == verdict
    assert payload["promotion_eligible"] is False


def test_exploratory_guard_must_refuse_the_readout() -> None:
    bundle = _bundle()
    readout = {
        "schema": "alpha_system.research_lane.fast_probe.v1",
        "status": "INCONCLUSIVE",
        "promotion_eligible": False,
        "row_access": {"status": "unresolved", "fabricated_values": False},
    }

    with pytest.raises(GovernanceValidationError) as exc_info:
        route_verdict_to_memory("DATA_GAP", bundle.idea_draft, readout, created_at=TIMESTAMP)

    assert exc_info.value.issues[0].code == "exploratory_refusal_missing"


def test_memory_router_source_never_writes_survivor_libraries() -> None:
    source = inspect.getsource(memory_router_module)

    assert "FactorLibrary" not in source
    assert "factor_library" not in source
    assert "AlphaBook" not in source
    assert "alpha_book" not in source


def _bundle():
    return build_idea_validation_bundle(
        json.loads(FIXTURE_IDEA.read_text(encoding="utf-8")),
        source=FIXTURE_IDEA.as_posix(),
    )


def _readout(bundle) -> dict[str, object]:
    return {
        "schema": "alpha_system.research_lane.fast_probe.v1",
        "readout_id": "unit_readout",
        "status": "INCONCLUSIVE",
        "issue_code": "DATA_GAP",
        "stamp": "EXPLORATORY",
        "promotion_eligible": False,
        "mechanism_card": bundle.mechanism_card.to_dict(),
        "slice_spec": {"slice_id": "unit-slice", "study_kind": "main_effect"},
        "row_access": {
            "status": "unresolved",
            "reason": "unit fixture has no materialized slice",
            "fabricated_values": False,
        },
    }


def _main_effect_signal_readout(bundle) -> dict[str, object]:
    return {
        "schema": "alpha_system.research_lane.fast_probe.v1",
        "readout_id": "fpmain_unit",
        "status": "RECORDED",
        "study_kind": "main_effect",
        "stamp": "EXPLORATORY",
        "promotion_eligible": False,
        "mechanism_card": bundle.mechanism_card.to_dict(),
        "slice_spec": {
            "slice_id": "ES_2020_60m",
            "study_kind": "main_effect",
            "feature_inputs": [
                {"role": "factor", "factor_id": "base_ohlcv_distance_to_vwap"}
            ],
        },
        "row_access": {
            "status": "resolved_local_only",
            "fabricated_values": False,
        },
        "readout": {
            "factor_diagnostics_report": {
                "quality_summary": {
                    "pearson_ic": -0.0557,
                    "rank_ic": -0.0150,
                    "ic_power_mde_abs_ic": 0.0034,
                    "ic_power_n_eff": 327155,
                    "bucket_rank_correlation": -0.805,
                }
            }
        },
    }


def _setup_lane_signal_readout(bundle) -> dict[str, object]:
    return {
        "schema": "alpha_system.research_lane.fast_probe.v1",
        "readout_id": "fpsetup_unit",
        "status": "RECORDED",
        "study_kind": "context_not_equal_trigger",
        "stamp": "EXPLORATORY",
        "promotion_eligible": False,
        "mechanism_card": bundle.mechanism_card.to_dict(),
        "slice_spec": {
            "slice_id": "ES_2020_120m",
            "study_kind": "context_not_equal_trigger",
        },
        "row_access": {
            "status": "resolved_local_only",
            "fabricated_values": False,
        },
        # ZERO_PASS_MET path: the surrogate exposes the conditioned overlap-aware
        # power as a top-level power.n_eff statement (the gate carries no
        # conditioned_n_eff/observed_effect in this path -- mirrors the real readout).
        "power": {"n_eff": 412, "mde_abs_ic": 0.084},
        "surrogate_fdr_gate": {
            "gate_status": "PASSED",
            "threshold_verdict": "zero-pass-met",
            "run_count": 200,
            "gate_pass_count": 0,
            "error_count": 0,
            "promotion_evidence": False,
        },
        "readout": {
            "diagnostics": {
                "continuous_outcome_mean_lift": {
                    "outcome_label_type": "net_excursion",
                    "conditioned_mean": -0.0021,
                    "base_mean": 0.0010,
                    "mean_lift": -0.0031,
                    "conditioned_n": 1200,
                    "base_n": 4800,
                }
            }
        },
    }


def _empty_ledger(tmp_path) -> Path:
    """An existing, writable, empty family-FDR ledger file (fail-closed contract)."""

    path = tmp_path / "family_fdr_ledger.jsonl"
    path.touch()
    return path


def _seed_siblings(
    ledger_path: Path,
    *,
    alpha_spec_id: str,
    count: int,
    gate_pass_count: int = 0,
    run_count: int = _HISTORICAL_RUN_COUNT,
) -> None:
    """Append ``count`` co-mined sibling records sharing the historical batch key.

    Siblings share the batch identity (alpha_spec_id, slice, family) and differ only
    by their intra-batch ``idea_key`` (a distinct mechanism per variant).
    """

    ledger = FamilyFdrLedger(ledger_path)
    records = []
    for index in range(count):
        idea_key = f"mech_sibling_{index:02d}"
        (verdict,) = correct_family(
            ({"idea_key": idea_key, "gate_pass_count": gate_pass_count, "run_count": run_count},),
            alpha_fw=0.10,
        )
        records.append(
            create_family_fdr_ledger_record(
                family_id=_HISTORICAL_FAMILY_ID,
                slice_id=_HISTORICAL_SLICE_ID,
                alpha_spec_id=alpha_spec_id,
                idea_key=idea_key,
                p_value=verdict.p_value,
                run_count=run_count,
                verdict=verdict,
                created_at=TIMESTAMP,
            )
        )
    ledger.append_records(records)


def _historical_setup_readout(bundle) -> dict[str, object]:
    """The setup-lane readout for the historical prior_high_sweep signal.

    Shares the historical batch identity: mechanism_card.duplicate_exposure.family_id
    pins the co-mined family and the slice is ES_2020_120m. The surrogate gate carries
    run_count=64 (gate_pass_count=0) -> p=1/65.
    """

    readout = _setup_lane_signal_readout(bundle)
    mechanism = dict(readout["mechanism_card"])  # type: ignore[arg-type]
    duplicate = dict(mechanism.get("duplicate_exposure") or {})
    duplicate["family_id"] = _HISTORICAL_FAMILY_ID
    mechanism["duplicate_exposure"] = duplicate
    readout["mechanism_card"] = mechanism
    readout["surrogate_fdr_gate"] = {
        "gate_status": "PASSED",
        "threshold_verdict": "zero-pass-met",
        "run_count": _HISTORICAL_RUN_COUNT,
        "gate_pass_count": 0,
        "error_count": 0,
        "promotion_evidence": False,
    }
    return readout


def _id(kind: GovernanceIdKind, salt: str) -> str:
    return generate_governance_id(kind, {"test": "memory_router", "salt": salt})
