from __future__ import annotations

from decimal import Decimal

from alpha_system.management.integration import run_reference_backtest_with_management
from alpha_system.management.spec import ManagementSpec
from tests.fixtures.backtest_reference import SYNTH_INSTRUMENT_MULTIPLIERS, signal_record, synthetic_bar, zero_cost_config


def test_management_reference_integration_emits_visible_partial_and_eod_trades() -> None:
    bars = [
        synthetic_bar(0, open_price="100", high="101", low="99", close="100"),
        synthetic_bar(1, open_price="100", high="102.5", low="99", close="101"),
        synthetic_bar(2, open_price="102", high="103", low="101", close="102"),
    ]
    spec = ManagementSpec.from_mapping(
        {
            "fixed_stop": {"enabled": True, "stop_pct": "0.02"},
            "laddered_partial_take_profit": {
                "enabled": True,
                "steps": [{"label": "half_at_1r", "threshold_r": "1", "exit_fraction": "0.5"}],
            },
            "eod_exit": True,
        }
    )

    result = run_reference_backtest_with_management(
        bars=bars,
        signals=[signal_record(0, "entry", signal_id="entry")],
        config=zero_cost_config(default_quantity=Decimal("1")),
        management_spec=spec,
        run_id="managed-integration",
        instrument_multipliers=SYNTH_INSTRUMENT_MULTIPLIERS,
    )

    assert result.summary.total_trades == 2
    assert result.summary.open_positions == 0
    assert result.trades[0].exit_reason == "partial_take_profit:half_at_1r"
    assert result.trades[0].quantity == Decimal("0.5")
    assert result.trades[1].exit_reason == "eod_exit"
    assert result.trades[1].quantity == Decimal("0.5")
    assert result.output_paths is None
    assert result.manifest["artifact_paths"] == {}
