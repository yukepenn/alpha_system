from __future__ import annotations

from alpha_system.reports.factor_card import build_factor_card, render_factor_card_markdown
from tests.fixtures.reports.synthetic import diagnostic_summary, report_metadata


def test_factor_card_contains_all_required_sections() -> None:
    card = build_factor_card(
        diagnostic_summary(),
        reproducibility_metadata=report_metadata(),
    )
    payload = card.to_dict()

    assert set(payload["stability"]) == {
        "time_of_day",
        "session_segment",
        "monthly",
        "volatility_regime",
        "liquidity_regime",
    }
    assert payload["correlation_to_existing_factors"]["fixture_momentum"]["n"] == 42
    assert payload["factor_cluster_id"] == "cluster_01"
    assert payload["sample_size"] == 42
    assert "diagnostic_summary" in payload
    assert payload["limitations"]


def test_factor_card_markdown_renders_required_section_headers() -> None:
    card = build_factor_card(
        diagnostic_summary(),
        reproducibility_metadata=report_metadata(),
    )
    rendered = render_factor_card_markdown(card)

    for header in (
        "## Metadata",
        "## Diagnostic Summary",
        "## Stability",
        "### Time Of Day",
        "### Session Segment",
        "### Monthly",
        "### Volatility Regime",
        "### Liquidity Regime",
        "## Correlation To Existing Factors",
        "## Cluster And Recommendation",
        "## Warnings",
        "## Limitations",
    ):
        assert header in rendered
