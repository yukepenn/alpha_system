from __future__ import annotations

from decimal import Decimal

import pytest

from alpha_system.backtest.liquidity import (
    LiquidityInput,
    LiquidityPolicy,
    LiquidityRejectedError,
)


def test_liquidity_policy_rejects_when_requested_quantity_exceeds_cap() -> None:
    policy = LiquidityPolicy(max_participation=Decimal("0.10"), reject_when_exceeds=True)

    with pytest.raises(LiquidityRejectedError):
        policy.evaluate(
            LiquidityInput(
                requested_quantity=Decimal("200"),
                bar_volume=Decimal("1000"),
                price=Decimal("10"),
            )
        )


def test_liquidity_policy_can_apply_penalty_when_capped() -> None:
    policy = LiquidityPolicy(
        max_participation=Decimal("0.10"),
        reject_when_exceeds=False,
        penalty_bps_when_capped=Decimal("10"),
    )

    decision = policy.evaluate(
        LiquidityInput(
            requested_quantity=Decimal("200"),
            bar_volume=Decimal("1000"),
            price=Decimal("10"),
        )
    )

    assert decision.accepted is True
    assert decision.fill_quantity == Decimal("100.00")
    assert decision.penalty_cost == Decimal("1.000")
