from __future__ import annotations

import pytest

from alpha_system.reports.factor_card import build_factor_card
from alpha_system.reports.prohibited_claims import (
    PROHIBITED_CLAIMS,
    ProhibitedClaimError,
    find_prohibited_claims,
    validate_no_prohibited_claims,
)
from alpha_system.reports.report_models import ALLOWED_PROMOTION_RECOMMENDATIONS
from tests.fixtures.reports.synthetic import diagnostic_summary, report_metadata


@pytest.mark.parametrize("claim", PROHIBITED_CLAIMS)
def test_each_prohibited_claim_is_detected(claim: str) -> None:
    matches = find_prohibited_claims(f"Report text says {claim}.")

    assert [match.claim for match in matches] == [claim]


@pytest.mark.parametrize(
    ("text", "claim"),
    (
        ("This says PRODUCTION READY.", "production-ready"),
        ("This says market beating.", "market-beating"),
        ("This says live ready.", "live-ready"),
        ("This says approved_without_review.", "approved without review"),
    ),
)
def test_prohibited_claim_detection_normalizes_case_and_punctuation(
    text: str,
    claim: str,
) -> None:
    assert any(match.claim == claim for match in find_prohibited_claims(text))


def test_prohibited_claim_validation_is_blocking() -> None:
    with pytest.raises(ProhibitedClaimError):
        validate_no_prohibited_claims({"limitation": "deployable"})


def test_factor_card_blocks_prohibited_metadata_language() -> None:
    metadata = report_metadata()
    metadata["review_status"] = "live-ready"

    with pytest.raises(ProhibitedClaimError):
        build_factor_card(diagnostic_summary(), reproducibility_metadata=metadata)


def test_allowed_recommendation_values_are_not_prohibited_claims() -> None:
    for recommendation in ALLOWED_PROMOTION_RECOMMENDATIONS:
        assert find_prohibited_claims(recommendation) == ()
