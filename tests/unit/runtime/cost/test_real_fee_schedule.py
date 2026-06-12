from __future__ import annotations

from decimal import Decimal

import pytest

from alpha_system.backtest.costs import CostInput, FuturesFeeScheduleCost
from alpha_system.backtest.futures_fees import (
    ACTIVE_FEE_SCHEDULE_VERSION_ID,
    PLACEHOLDER_FEE_SCHEDULE_VERSION_ID,
    REAL_FEE_SCHEDULE_VERSION_ID,
    active_fee_schedule,
    fee_schedule_by_version,
)
from alpha_system.runtime.cost import CostModelVersion, CostStressSpec


EXPECTED_ALL_IN_PER_SIDE = {
    "ES": Decimal("1.99"),
    "NQ": Decimal("1.99"),
    "RTY": Decimal("1.99"),
    "MES": Decimal("0.36"),
    "MNQ": Decimal("0.36"),
    "M2K": Decimal("0.36"),
}


def test_real_fee_schedule_pins_symbol_all_in_totals_and_keeps_history() -> None:
    schedule = active_fee_schedule()

    assert schedule.version_id == REAL_FEE_SCHEDULE_VERSION_ID
    assert ACTIVE_FEE_SCHEDULE_VERSION_ID == REAL_FEE_SCHEDULE_VERSION_ID
    assert fee_schedule_by_version(PLACEHOLDER_FEE_SCHEDULE_VERSION_ID).placeholder is True
    assert {
        symbol: schedule.entry_for_symbol(symbol).all_in_per_side
        for symbol in EXPECTED_ALL_IN_PER_SIDE
    } == EXPECTED_ALL_IN_PER_SIDE


def test_micro_fees_are_below_matching_mini_fees() -> None:
    schedule = active_fee_schedule()

    assert schedule.entry_for_symbol("MES").all_in_per_side < schedule.entry_for_symbol(
        "ES"
    ).all_in_per_side
    assert schedule.entry_for_symbol("MNQ").all_in_per_side < schedule.entry_for_symbol(
        "NQ"
    ).all_in_per_side
    assert schedule.entry_for_symbol("M2K").all_in_per_side < schedule.entry_for_symbol(
        "RTY"
    ).all_in_per_side


@pytest.mark.parametrize("symbol", ("ES", "NQ", "RTY", "MES", "MNQ", "M2K"))
def test_fee_schedule_cost_breakdown_uses_components_per_contract(symbol: str) -> None:
    model = FuturesFeeScheduleCost(default_symbol="ES")

    breakdown = model.cost_for_fill(
        CostInput(
            price=Decimal("100"),
            quantity=Decimal("2"),
            side="buy",
            metadata={"symbol": symbol},
        )
    )

    assert breakdown.total == EXPECTED_ALL_IN_PER_SIDE[symbol] * 2
    assert breakdown.amount_for(f"{symbol}_cme_exchange_fee") > 0
    assert breakdown.amount_for(f"{symbol}_nfa_regulatory_fee") > 0
    assert breakdown.amount_for(f"{symbol}_retail_discount_broker_commission") > 0


def test_default_base_profile_consumes_real_fee_version_and_zero_cost_stays_zero() -> None:
    real_version = CostModelVersion.from_mappings(bbo_available=True)
    descriptor = real_version.cost_model_descriptor
    fee_component = [
        component
        for component in descriptor["components"]
        if component["model"] == "futures_fee_schedule"
    ][0]
    spec = CostStressSpec(cost_model_version=real_version)

    assert fee_component["schedule_version_id"] == REAL_FEE_SCHEDULE_VERSION_ID
    assert spec.profile_by_name["base"].cost_multiplier == Decimal("1.0")
    assert spec.profile_by_name["double_cost"].cost_multiplier == Decimal("2.0")

    zero_version = CostModelVersion.from_mappings(
        cost_model_descriptor={"model": "zero_cost", "fixture_only": True},
        slippage_model_descriptor={"model": "none", "fixture_only": True},
        bbo_available=False,
    )
    zero_model = zero_version.cost_model_descriptor

    assert zero_version.zero_cost_diagnostic_only is True
    assert zero_model["model"] == "composite"
    assert zero_model["fixture_zero_cost"] is True
    assert zero_model["components"][0]["model"] == "zero_cost"
