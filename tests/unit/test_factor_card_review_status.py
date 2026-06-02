from __future__ import annotations

import pytest

from alpha_system.reports.factor_card import build_factor_card, render_factor_card_markdown
from alpha_system.reports.prohibited_claims import ProhibitedClaimError
from alpha_system.reports.report_models import PromotionRecommendation
from tests.fixtures.reports.synthetic import diagnostic_summary, report_metadata


def test_no_lookahead_and_review_status_are_preserved() -> None:
    metadata = report_metadata()
    metadata["no_lookahead_validation_status"] = "passed"
    metadata["review_status"] = "semantic_review_pending"
    card = build_factor_card(diagnostic_summary(), reproducibility_metadata=metadata)
    rendered = render_factor_card_markdown(card)

    assert card.metadata.no_lookahead_validation_status == "passed"
    assert card.metadata.review_status == "semantic_review_pending"
    assert "semantic_review_pending" in rendered
    assert "passed" in rendered


def test_failed_no_lookahead_status_blocks_promotion_recommendation_by_default() -> None:
    metadata = report_metadata()
    metadata["no_lookahead_validation_status"] = "failed"
    card = build_factor_card(diagnostic_summary(), reproducibility_metadata=metadata)

    assert card.promotion_recommendation is PromotionRecommendation.DO_NOT_PROMOTE


def test_review_status_with_blocked_language_is_rejected() -> None:
    metadata = report_metadata()
    metadata["review_status"] = "approved_without_review"

    with pytest.raises(ProhibitedClaimError):
        build_factor_card(diagnostic_summary(), reproducibility_metadata=metadata)
