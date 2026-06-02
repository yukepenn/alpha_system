from __future__ import annotations

from alpha_system.reports.factor_card import build_factor_card
from tests.fixtures.reports.synthetic import (
    diagnostic_summary,
    report_metadata,
    without_diagnostic,
)


def test_factor_card_stability_sections_keep_diagnostic_values() -> None:
    card = build_factor_card(
        diagnostic_summary(),
        reproducibility_metadata=report_metadata(),
    )
    stability = card.stability.to_dict()

    assert stability["time_of_day"]["09:30"]["n"] == 21
    assert stability["session_segment"]["segment_2"]["pearson_ic"] == 0.1
    assert stability["monthly"]["2026-02"]["n"] == 22
    assert stability["volatility_regime"]["high"]["n"] == 22
    assert stability["liquidity_regime"]["deep"]["n"] == 24


def test_missing_stability_section_is_visible_warning() -> None:
    summary = without_diagnostic(diagnostic_summary(), "diagnostics", "stability", "liquidity_regime")
    card = build_factor_card(summary, reproducibility_metadata=report_metadata())

    assert card.stability.to_dict()["liquidity_regime"] == {"status": "not_available"}
    assert any(warning.code == "missing_liquidity_regime_stability" for warning in card.warnings)
