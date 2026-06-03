from __future__ import annotations

from decimal import Decimal

from alpha_system.core.enums import Direction
from alpha_system.portfolio.risk import enforce_gross_exposure
from alpha_system.portfolio.sizing import SizeDecision
from alpha_system.portfolio.spec import PortfolioSpec


def test_max_gross_exposure_scales_targets_deterministically() -> None:
    decisions = (
        SizeDecision("SYNTH_A", Direction.LONG, Decimal("60000"), Decimal("600"), Decimal("0.6"), "sig-1"),
        SizeDecision("SYNTH_B", Direction.SHORT, Decimal("60000"), Decimal("300"), Decimal("-0.6"), "sig-2"),
    )
    spec = PortfolioSpec.from_mapping(
        {
            "position_sizing": {"method": "fixed_notional", "fixed_notional": "60000"},
            "risk_limits": {"max_gross_exposure": "1.0"},
        }
    )

    constrained = enforce_gross_exposure(decisions, Decimal("100000"), spec)

    assert sum(decision.target_notional for decision in constrained) == Decimal("100000.0")
    assert constrained[0].target_notional == Decimal("50000.0")
    assert constrained[1].target_notional == Decimal("50000.0")
    assert all("max_gross_exposure" in decision.reasons for decision in constrained)
