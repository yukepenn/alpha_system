from __future__ import annotations

from pathlib import Path

from alpha_system.reports.prohibited_claims import PROHIBITED_CLAIMS, find_prohibited_claims
from alpha_system.reports.report_models import ALLOWED_PROMOTION_RECOMMENDATIONS


def test_report_language_policy_documents_blocked_vocabulary() -> None:
    text = Path("docs/REPORT_LANGUAGE_POLICY.md").read_text(encoding="utf-8")

    for claim in PROHIBITED_CLAIMS:
        assert f"`{claim}`" in text


def test_report_language_policy_documents_allowed_recommendations() -> None:
    text = Path("docs/REPORT_LANGUAGE_POLICY.md").read_text(encoding="utf-8")

    for recommendation in ALLOWED_PROMOTION_RECOMMENDATIONS:
        assert f"`{recommendation}`" in text
    assert "Recommendations are advisory research guidance only." in text


def test_factor_card_docs_avoid_blocked_generated_report_language() -> None:
    text = Path("docs/FACTOR_CARDS.md").read_text(encoding="utf-8")

    assert find_prohibited_claims(text) == ()
    assert "A recommendation is not approval" in text
