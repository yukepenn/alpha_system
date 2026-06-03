from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

from alpha_system.management.spec import BreakevenStopSpec
from alpha_system.management.trailing import breakeven_stop_update
from tests.unit.test_management_rule_ordering import managed_state


def test_breakeven_stop_updates_only_after_trigger() -> None:
    state = managed_state(initial_stop=Decimal("98"))
    spec = BreakevenStopSpec(enabled=True, trigger_r=Decimal("1"), offset_r=Decimal("0.25"))

    assert breakeven_stop_update(state, spec, {"high": "101.9", "low": "99"}) == Decimal("98")
    assert breakeven_stop_update(state, spec, {"high": "102", "low": "99"}) == Decimal("100.50")


def test_breakeven_stop_never_makes_long_stop_less_protective() -> None:
    state = replace(managed_state(initial_stop=Decimal("98")), active_stop_price=Decimal("101"))
    spec = BreakevenStopSpec(enabled=True, trigger_r=Decimal("1"), offset_r=Decimal("0"))

    assert breakeven_stop_update(state, spec, {"high": "103", "low": "99"}) == Decimal("101")
