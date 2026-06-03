from __future__ import annotations

from decimal import Decimal

from alpha_system.management.integration import run_reference_backtest_with_management
from alpha_system.management.spec import ManagementSpec
from tests.fixtures.backtest_reference import signal_record, synthetic_bar, zero_cost_config


def test_same_bar_management_stop_wins_over_target() -> None:
    bars = [
        synthetic_bar(0, open_price="100", high="101", low="99", close="100"),
        synthetic_bar(1, open_price="100", high="103", low="97", close="101"),
        synthetic_bar(2, open_price="101", high="102", low="100", close="101"),
    ]
    spec = ManagementSpec.from_mapping(
        {
            "fixed_stop": {"enabled": True, "stop_pct": "0.01"},
            "target_r_multiple": {"enabled": True, "r_multiple": "1"},
        }
    )

    result = run_reference_backtest_with_management(
        bars=bars,
        signals=[signal_record(0, "entry", signal_id="entry")],
        config=zero_cost_config(default_quantity=Decimal("1")),
        management_spec=spec,
        run_id="managed-same-bar",
    )

    trade = result.trades[0]
    assert trade.exit_reason == "stop_loss"
    assert trade.exit_bar_index == 1
    assert "same_bar_adverse_first" in trade.quality_flags
    assert trade.net_pnl < 0
