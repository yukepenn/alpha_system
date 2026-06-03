from __future__ import annotations

from decimal import Decimal

import pytest

from alpha_system.core.enums import Direction
from alpha_system.portfolio.risk import enforce_multi_symbol_constraints
from alpha_system.portfolio.sizing import SizeDecision
from alpha_system.portfolio.spec import PortfolioSpec, PortfolioSpecError


def test_multi_symbol_constraints_represent_instrument_limits() -> None:
    decisions = (
        SizeDecision("SYNTH_A", Direction.LONG, Decimal("1000"), Decimal("10"), Decimal("0.01"), "sig-1"),
        SizeDecision("SYNTH_B", Direction.LONG, Decimal("1000"), Decimal("10"), Decimal("0.01"), "sig-2"),
        SizeDecision("SYNTH_C", Direction.LONG, Decimal("1000"), Decimal("10"), Decimal("0.01"), "sig-3"),
    )
    spec = PortfolioSpec.from_mapping(
        {
            "multi_symbol_constraints": {
                "required_identifier": "instrument_id",
                "max_active_instruments": 2,
            }
        }
    )

    constrained = enforce_multi_symbol_constraints(decisions, spec)

    assert [decision.rejected for decision in constrained] == [False, False, True]
    assert constrained[2].target_notional == Decimal("0")
    assert "max_active_instruments" in constrained[2].reasons


def test_multi_symbol_constraints_require_instrument_id_identity() -> None:
    with pytest.raises(PortfolioSpecError):
        PortfolioSpec.from_mapping({"multi_symbol_constraints": {"required_identifier": "symbol"}})
