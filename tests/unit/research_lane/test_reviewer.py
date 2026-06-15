from __future__ import annotations

import pytest

from alpha_system.governance.reviewer_verdict import create_reviewer_verdict
from alpha_system.research_lane.reviewer import (
    INTENT_CONFIRMED_FOR_TRUSTED_STUDY,
    INTENT_NEEDS_MORE_EVIDENCE,
    INTENT_REJECTED_BY_REVIEW,
    ReviewerAdjudicationError,
    adjudicate_signal,
)

TIMESTAMP = "2026-06-15T00:00:00Z"


def _signal_row(reason_code: str = "SIGNAL_PENDING_REVIEWER") -> dict:
    return {
        "reason_code": reason_code,
        "alpha_spec_id": "aspec_unit",
        "factor_id": "base_ohlcv_distance_to_vwap",
        "label_version_id": "lver_unit",
        "slice_id": "ES_2020_60m",
        "study_kind": "main_effect",
        "pearson_ic": -0.0557,
        "rank_ic": -0.0150,
        "n_eff": 327155,
        "detectable_abs_ic": 0.0034,
        "memory_record": {"original_verdict_ref": "readout:fpmain_unit"},
    }


def _verdict(outcome: str):
    return create_reviewer_verdict(
        reviewer_id="adversarial_reviewer_01",
        role="statistical_reviewer",
        independence_statement="Independent of the signal's producer; no authoring access.",
        verdict=outcome,
        blocking_issues=["Label is a proxy; not validated OOS."] if outcome == "BLOCKED" else [],
        warnings=["Exploratory IC only."] if outcome == "PASS_WITH_WARNINGS" else [],
        checked_artifacts=["readout:fpmain_unit"],
        checked_commands=["alpha idea review list"],
        timestamp=TIMESTAMP,
        reason_code="UNDERPOWERED" if outcome == "INCONCLUSIVE" else None,
    )


@pytest.mark.parametrize(
    ("outcome", "intent", "gate"),
    [
        ("PASS", INTENT_CONFIRMED_FOR_TRUSTED_STUDY, "trusted_study_spec"),
        ("PASS_WITH_WARNINGS", INTENT_CONFIRMED_FOR_TRUSTED_STUDY, "trusted_study_spec"),
        ("REWORK", INTENT_NEEDS_MORE_EVIDENCE, "evidence_accrual_or_retest"),
        ("INCONCLUSIVE", INTENT_NEEDS_MORE_EVIDENCE, "evidence_accrual_or_retest"),
        ("BLOCKED", INTENT_REJECTED_BY_REVIEW, "none"),
    ],
)
def test_adjudicate_maps_outcome_to_intent(outcome: str, intent: str, gate: str) -> None:
    adjudication = adjudicate_signal(
        _signal_row(), reviewer_verdict=_verdict(outcome), created_at=TIMESTAMP
    )

    assert adjudication["reviewer_outcome"] == outcome
    assert adjudication["routing_intent"] == intent
    assert adjudication["next_required_gate"] == gate
    assert adjudication["signal_ref"] == "readout:fpmain_unit"
    assert adjudication["factor_id"] == "base_ohlcv_distance_to_vwap"
    assert adjudication["pearson_ic"] == pytest.approx(-0.0557)


def test_adjudication_is_never_promotion_or_market_truth() -> None:
    adjudication = adjudicate_signal(
        _signal_row(), reviewer_verdict=_verdict("PASS"), created_at=TIMESTAMP
    )

    assert adjudication["promotion_eligible"] is False
    assert adjudication["implies_market_truth"] is False
    assert adjudication["implies_tradability"] is False
    # the strongest positive intent is the trusted-study bridge, never WATCH/CANDIDATE
    assert adjudication["routing_intent"] == INTENT_CONFIRMED_FOR_TRUSTED_STUDY
    assert "WATCH" not in adjudication["routing_intent"]
    assert "CANDIDATE" not in adjudication["routing_intent"]


def _setup_lane_signal_row() -> dict:
    return {
        "reason_code": "SIGNAL_PENDING_REVIEWER",
        "alpha_spec_id": "aspec_setup",
        "factor_id": "prior_session_high",
        "label_version_id": "lver_setup",
        "slice_id": "ES_2020_120m",
        "study_kind": "context_not_equal_trigger",
        # No IC numbers in the setup lane.
        "pearson_ic": None,
        "rank_ic": None,
        "n_eff": 412,
        "detectable_abs_ic": None,
        # The signed net excursion + surrogate evidence.
        "net_mean_lift": -0.0031,
        "observed_effect": -0.0031,
        "surrogate_gate_pass_count": 0,
        "surrogate_run_count": 200,
        "outcome_label_type": "net_excursion",
        "memory_record": {"original_verdict_ref": "readout:fpsetup_unit"},
    }


def test_adjudicate_surfaces_setup_lane_net_evidence() -> None:
    adjudication = adjudicate_signal(
        _setup_lane_signal_row(), reviewer_verdict=_verdict("PASS"), created_at=TIMESTAMP
    )

    # The reviewer of a setup-lane signal sees the signed net excursion + surrogate
    # evidence, not empty IC fields.
    assert adjudication["study_kind"] == "context_not_equal_trigger"
    assert adjudication["net_mean_lift"] == pytest.approx(-0.0031)
    assert adjudication["observed_effect"] == pytest.approx(-0.0031)
    assert adjudication["surrogate_gate_pass_count"] == 0
    assert adjudication["surrogate_run_count"] == 200
    assert adjudication["outcome_label_type"] == "net_excursion"
    assert adjudication["pearson_ic"] is None
    assert adjudication["promotion_eligible"] is False
    assert adjudication["routing_intent"] == INTENT_CONFIRMED_FOR_TRUSTED_STUDY


def test_adjudicate_refuses_non_signal_rows() -> None:
    with pytest.raises(ReviewerAdjudicationError):
        adjudicate_signal(
            _signal_row(reason_code="UNDERPOWERED"),
            reviewer_verdict=_verdict("PASS"),
            created_at=TIMESTAMP,
        )
