from __future__ import annotations

from decimal import Decimal

from alpha_system.backtest.slippage import SpreadSensitiveSlippageModel, SlippageInput


def test_spread_sensitive_slippage_scales_with_spread() -> None:
    result = SpreadSensitiveSlippageModel(spread_fraction=Decimal("0.50")).apply(
        SlippageInput(
            price=Decimal("100"),
            quantity=Decimal("1"),
            side="buy",
            bid=Decimal("99.90"),
            ask=Decimal("100.10"),
            spread=Decimal("0.20"),
        )
    )

    assert result.adjusted_price == Decimal("100.100")
    assert result.amount == Decimal("0.100")


def test_spread_sensitive_slippage_uses_fallback_bps_when_spread_missing() -> None:
    result = SpreadSensitiveSlippageModel(
        spread_fraction=Decimal("0.50"),
        fallback_bps=Decimal("5"),
    ).apply(SlippageInput(price=Decimal("100"), quantity=Decimal("1"), side="sell"))

    assert result.adjusted_price == Decimal("99.95")
    assert result.amount == Decimal("0.05")
