from __future__ import annotations

from alpha_system.reports.factor_card import build_factor_card
from alpha_system.reports.report_models import PromotionRecommendation
from tests.fixtures.reports.synthetic import (
    diagnostic_summary,
    report_metadata,
    without_diagnostic,
)


def test_insufficient_sample_size_emits_warning_and_conservative_recommendation() -> None:
    card = build_factor_card(
        diagnostic_summary(sample_size=4),
        reproducibility_metadata=report_metadata(),
        min_sample_size=30,
    )

    assert card.promotion_recommendation is PromotionRecommendation.NEEDS_MORE_DATA
    assert any(warning.code == "insufficient_sample_size" for warning in card.warnings)


def test_missing_correlation_to_existing_factors_emits_warning() -> None:
    summary = without_diagnostic(
        diagnostic_summary(),
        "diagnostics",
        "correlation_to_existing_factors",
    )
    card = build_factor_card(summary, reproducibility_metadata=report_metadata())

    assert any(
        warning.code == "missing_correlation_to_existing_factors" for warning in card.warnings
    )
