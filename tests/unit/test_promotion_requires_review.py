from __future__ import annotations

import pytest

from alpha_system.experiments.promotion import PromotionDecision, PromotionDecisionError


def test_approved_promotion_requires_review_metadata() -> None:
    with pytest.raises(PromotionDecisionError, match="reviewer_identity"):
        PromotionDecision(
            candidate_id="candidate-1",
            source_run_id="grid-run-1",
            review_status="pass",
            decision_status="approved",
            rationale="reviewed evidence",
            timestamp="2026-06-02T01:20:07Z",
        )


def test_recommendation_is_not_approval() -> None:
    decision = PromotionDecision(
        candidate_id="candidate-1",
        source_run_id="grid-run-1",
        review_status="reviewed",
        decision_status="recommended",
        reviewer_identity="reviewer-1",
        rationale="recommend review only",
        timestamp="2026-06-02T01:20:07Z",
    )

    assert decision.is_recommendation is True
    assert decision.is_approval is False


def test_recommendation_review_status_cannot_approve() -> None:
    with pytest.raises(PromotionDecisionError, match="recommendation"):
        PromotionDecision(
            candidate_id="candidate-1",
            source_run_id="grid-run-1",
            review_status="recommended",
            decision_status="approved",
            reviewer_identity="reviewer-1",
            rationale="not enough review status",
            timestamp="2026-06-02T01:20:07Z",
        )
