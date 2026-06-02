from __future__ import annotations

from decimal import Decimal

from alpha_system.backtest.slippage import AdverseSelectionProxyModel, SlippageInput


def test_adverse_selection_proxy_hook_is_invoked_and_configurable() -> None:
    calls: list[str] = []

    def proxy(fill: SlippageInput) -> Decimal:
        calls.append(fill.side)
        return Decimal("2")

    result = AdverseSelectionProxyModel(proxy=proxy).apply(
        SlippageInput(price=Decimal("100"), quantity=Decimal("1"), side="buy")
    )

    assert calls == ["buy"]
    assert result.adjusted_price == Decimal("100.02")
    assert result.components[0][0] == "adverse_selection_proxy"
