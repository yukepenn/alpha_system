from __future__ import annotations

from decimal import Decimal

from alpha_system.management.spec import BreakevenStopSpec, TrailingStopSpec
from alpha_system.management.trailing import trailing_stop_update, update_protective_stop_for_next_bar
from tests.unit.test_management_rule_ordering import managed_state


def test_trailing_stop_updates_from_high_watermark() -> None:
    state = managed_state(initial_stop=Decimal("98"))
    spec = TrailingStopSpec(enabled=True, trail_r=Decimal("1"))

    assert trailing_stop_update(state, spec, {"high": "105", "low": "99"}) == Decimal("103")


def test_trailing_update_is_applied_for_next_bar_state() -> None:
    state = managed_state(initial_stop=Decimal("98"))

    updated = update_protective_stop_for_next_bar(
        state,
        breakeven=BreakevenStopSpec(),
        trailing=TrailingStopSpec(enabled=True, trail_r=Decimal("1")),
        bar={"high": "105", "low": "99"},
    )

    assert updated.active_stop_price == Decimal("103")
