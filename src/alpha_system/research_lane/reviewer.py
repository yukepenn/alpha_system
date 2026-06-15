"""Independent reviewer adjudication for shelved research signals.

The machine may CLASSIFY evidence autonomously but may NEVER PROMOTE it. A
``SIGNAL_PENDING_REVIEWER`` row on the signal shelf is an exploratory IC signal,
not promotion evidence. This module adds the independent-review layer on top of
the shelf: an independent reviewer (a separate, adversarial party -- never the
runner that produced the signal) records a ``ReviewerVerdict`` over a signal,
and that judgment maps to a value-free, non-promoting routing intent.

Crucially this does NOT mint WATCH / CANDIDATE / PromotionDecision /
FactorLibrary. Those promotion-lifecycle states require a real EvidenceBundle
produced by a TRUSTED slow-path StudySpec (fast_probe IC is not promotion
evidence). The strongest positive a reviewer can give an exploratory signal is
``CONFIRMED_FOR_TRUSTED_STUDY`` -- the bridge into that slow path, not a
shortcut around it.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from alpha_system.governance.reviewer_verdict import (
    ReviewerVerdict,
    ReviewerVerdictOutcome,
)

REVIEWER_ADJUDICATION_SCHEMA = "alpha_system.research_lane.reviewer_adjudication.v1"

# value-free routing intents (NOT promotion-lifecycle states)
INTENT_CONFIRMED_FOR_TRUSTED_STUDY = "CONFIRMED_FOR_TRUSTED_STUDY"
INTENT_NEEDS_MORE_EVIDENCE = "NEEDS_MORE_EVIDENCE"
INTENT_REJECTED_BY_REVIEW = "REJECTED_BY_REVIEW"

_OUTCOME_INTENT: dict[ReviewerVerdictOutcome, str] = {
    ReviewerVerdictOutcome.PASS: INTENT_CONFIRMED_FOR_TRUSTED_STUDY,
    ReviewerVerdictOutcome.PASS_WITH_WARNINGS: INTENT_CONFIRMED_FOR_TRUSTED_STUDY,
    ReviewerVerdictOutcome.REWORK: INTENT_NEEDS_MORE_EVIDENCE,
    ReviewerVerdictOutcome.INCONCLUSIVE: INTENT_NEEDS_MORE_EVIDENCE,
    ReviewerVerdictOutcome.BLOCKED: INTENT_REJECTED_BY_REVIEW,
}

# Intent that confirms the signal warrants a trusted StudySpec next.
_NEXT_GATE = {
    INTENT_CONFIRMED_FOR_TRUSTED_STUDY: "trusted_study_spec",
    INTENT_NEEDS_MORE_EVIDENCE: "evidence_accrual_or_retest",
    INTENT_REJECTED_BY_REVIEW: "none",
}


class ReviewerAdjudicationError(ValueError):
    """Raised when a signal cannot be adjudicated."""


def routing_intent_for(verdict: ReviewerVerdict) -> str:
    """Map a reviewer verdict outcome to a value-free routing intent."""

    intent = _OUTCOME_INTENT.get(verdict.verdict)
    if intent is None:  # pragma: no cover - closed enum, defensive
        raise ReviewerAdjudicationError(f"unhandled reviewer outcome: {verdict.verdict}")
    return intent


def adjudicate_signal(
    signal_row: Mapping[str, Any],
    *,
    reviewer_verdict: ReviewerVerdict,
    created_at: str,
) -> dict[str, Any]:
    """Adjudicate one shelved signal with an independent reviewer verdict.

    Returns a value-free, non-promoting adjudication envelope. It never marks
    WATCH/CANDIDATE/promotion; the strongest positive intent is
    CONFIRMED_FOR_TRUSTED_STUDY (the entry to the trusted slow path).
    """

    if str(signal_row.get("reason_code") or "") != "SIGNAL_PENDING_REVIEWER":
        raise ReviewerAdjudicationError(
            "reviewer adjudication only applies to SIGNAL_PENDING_REVIEWER shelf rows"
        )
    independence = reviewer_verdict.independence_statement.strip()
    if not independence:
        raise ReviewerAdjudicationError(
            "reviewer verdict must carry an explicit independence_statement"
        )
    intent = routing_intent_for(reviewer_verdict)
    return {
        "schema": REVIEWER_ADJUDICATION_SCHEMA,
        "created_at": created_at,
        "signal_ref": signal_row.get("original_verdict_ref")
        or (signal_row.get("memory_record") or {}).get("original_verdict_ref"),
        "alpha_spec_id": signal_row.get("alpha_spec_id"),
        "factor_id": signal_row.get("factor_id"),
        "label_version_id": signal_row.get("label_version_id"),
        "slice_id": signal_row.get("slice_id"),
        "study_kind": signal_row.get("study_kind"),
        # preserve the source diagnostic numbers so the trusted path / fleet can
        # query the adjudication without re-reading the shelf. The evidence is
        # lane-aware: main_effect rows carry IC numbers; setup-lane
        # (context_not_equal_trigger) rows carry the signed net excursion +
        # surrogate evidence (and None IC fields). The reviewer sees whichever the
        # lane actually produced rather than empty IC fields.
        "pearson_ic": signal_row.get("pearson_ic"),
        "rank_ic": signal_row.get("rank_ic"),
        "n_eff": signal_row.get("n_eff"),
        "detectable_abs_ic": signal_row.get("detectable_abs_ic"),
        # setup-lane (context_not_equal_trigger) evidence; None for main_effect rows.
        "net_mean_lift": signal_row.get("net_mean_lift"),
        "observed_effect": signal_row.get("observed_effect"),
        "surrogate_gate_pass_count": signal_row.get("surrogate_gate_pass_count"),
        "surrogate_run_count": signal_row.get("surrogate_run_count"),
        "outcome_label_type": signal_row.get("outcome_label_type"),
        "reviewer_outcome": reviewer_verdict.verdict.value,
        "routing_intent": intent,
        "next_required_gate": _NEXT_GATE[intent],
        "reviewer_verdict_id": reviewer_verdict.reviewer_verdict_id,
        "reviewer_verdict": reviewer_verdict.to_dict(),
        # the rail: a reviewer adjudication is never itself a promotion.
        "promotion_eligible": False,
        "implies_market_truth": reviewer_verdict.implies_market_truth,
        "implies_tradability": reviewer_verdict.implies_tradability,
    }


__all__ = [
    "INTENT_CONFIRMED_FOR_TRUSTED_STUDY",
    "INTENT_NEEDS_MORE_EVIDENCE",
    "INTENT_REJECTED_BY_REVIEW",
    "REVIEWER_ADJUDICATION_SCHEMA",
    "ReviewerAdjudicationError",
    "adjudicate_signal",
    "routing_intent_for",
]
