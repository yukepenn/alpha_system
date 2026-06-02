from __future__ import annotations

from decimal import Decimal

from alpha_system.backtest.costs import BpsCost, CompositeCostModel
from alpha_system.backtest.fill_models import ConservativeFillModel, FillRequest
from alpha_system.backtest.liquidity import LiquidityPolicy
from alpha_system.backtest.slippage import explicit_fixture_no_slippage_model


def test_missing_bid_ask_fallback_is_explicit_and_flagged() -> None:
    model = ConservativeFillModel(
        cost_model=CompositeCostModel(models=(BpsCost(Decimal("1")),)),
        slippage_model=explicit_fixture_no_slippage_model(),
        liquidity_policy=LiquidityPolicy(max_participation=Decimal("1.0")),
    )
    fill = model.resolve(
        FillRequest(
            direction="short",
            intent="entry",
            quantity=Decimal("1"),
            bar={
                "open": Decimal("100"),
                "high": Decimal("101"),
                "low": Decimal("99"),
                "close": Decimal("100"),
                "volume": Decimal("1000"),
                "bid": None,
                "ask": None,
                "spread": None,
            },
        )
    )

    assert fill.fill_price == Decimal("100")
    assert fill.price_source == "open"
    assert fill.missing_bid_ask_fallback is True
    assert fill.warnings == ("bid missing; used open by explicit policy",)
