from __future__ import annotations

import pytest

from alpha_system.reports.factor_card import build_factor_card, render_factor_card_markdown
from alpha_system.reports.report_models import (
    ALLOWED_PROMOTION_RECOMMENDATIONS,
    PromotionRecommendation,
    ReportModelError,
)
from tests.fixtures.reports.synthetic import diagnostic_summary, report_metadata


def test_recommendation_vocabulary_is_closed_set() -> None:
    assert ALLOWED_PROMOTION_RECOMMENDATIONS == (
        "reject",
        "needs_more_data",
        "candidate_for_strategy_test",
        "candidate_for_review",
        "do_not_promote",
    )


@pytest.mark.parametrize("recommendation", ALLOWED_PROMOTION_RECOMMENDATIONS)
def test_allowed_recommendations_render(recommendation: str) -> None:
    card = build_factor_card(
        diagnostic_summary(),
        reproducibility_metadata=report_metadata(),
        promotion_recommendation=recommendation,
    )

    assert card.promotion_recommendation.value == recommendation
    assert recommendation in render_factor_card_markdown(card)


def test_unknown_recommendation_is_rejected() -> None:
    with pytest.raises(ReportModelError):
        build_factor_card(
            diagnostic_summary(),
            reproducibility_metadata=report_metadata(),
            promotion_recommendation="ready",
        )


def test_default_recommendation_is_advisory_not_status_change() -> None:
    card = build_factor_card(
        diagnostic_summary(),
        reproducibility_metadata=report_metadata(),
    )
    rendered = render_factor_card_markdown(card).casefold()

    assert card.promotion_recommendation is PromotionRecommendation.CANDIDATE_FOR_REVIEW
    assert "registry status changes require a separate reviewed action" in rendered
    assert "approved" not in rendered
