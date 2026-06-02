from __future__ import annotations

from decimal import Decimal

from alpha_system.backtest.costs import BpsCost, CompositeCostModel
from alpha_system.backtest.fill_models import ConservativeFillModel, FillRequest
from alpha_system.backtest.liquidity import LiquidityPolicy
from alpha_system.backtest.slippage import explicit_fixture_no_slippage_model


def _bar() -> dict[str, object]:
    return {
        "open": Decimal("100"),
        "high": Decimal("101"),
        "low": Decimal("99"),
        "close": Decimal("100"),
        "volume": Decimal("1000"),
        "bid": Decimal("99.95"),
        "ask": Decimal("100.05"),
        "spread": Decimal("0.10"),
    }


def _model() -> ConservativeFillModel:
    return ConservativeFillModel(
        cost_model=CompositeCostModel(models=(BpsCost(Decimal("1")),)),
        slippage_model=explicit_fixture_no_slippage_model(),
        liquidity_policy=LiquidityPolicy(max_participation=Decimal("1.0")),
    )


def test_long_entry_uses_ask_when_bid_ask_present() -> None:
    fill = _model().resolve(
        FillRequest(direction="long", intent="entry", quantity=Decimal("1"), bar=_bar())
    )

    assert fill.fill_price == Decimal("100.05")
    assert fill.price_source == "ask"
    assert fill.used_bid_ask is True


def test_long_exit_uses_bid_when_bid_ask_present() -> None:
    fill = _model().resolve(
        FillRequest(direction="long", intent="exit", quantity=Decimal("1"), bar=_bar())
    )

    assert fill.fill_price == Decimal("99.95")
    assert fill.price_source == "bid"
    assert fill.used_bid_ask is True
