from __future__ import annotations

from decimal import Decimal

from alpha_system.backtest.slippage import BpsSlippageModel, SlippageInput


def test_bps_slippage_moves_buy_price_up_adversely() -> None:
    result = BpsSlippageModel(Decimal("10")).apply(
        SlippageInput(price=Decimal("100"), quantity=Decimal("1"), side="buy")
    )

    assert result.adjusted_price == Decimal("100.1")
    assert result.amount == Decimal("0.1")


def test_bps_slippage_moves_sell_price_down_adversely() -> None:
    result = BpsSlippageModel(Decimal("10")).apply(
        SlippageInput(price=Decimal("100"), quantity=Decimal("1"), side="sell")
    )

    assert result.adjusted_price == Decimal("99.9")
    assert result.amount == Decimal("0.1")
