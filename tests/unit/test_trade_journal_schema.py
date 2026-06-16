from __future__ import annotations

from alpha_system.backtest.trades import TRADE_JOURNAL_FIELDS, assert_trade_journal_schema
from alpha_system.backtest.reference import run_reference_backtest
from tests.fixtures.backtest_reference import SYNTH_INSTRUMENT_MULTIPLIERS, signal_record, synthetic_bars, zero_cost_config


def test_trade_journal_records_required_schema_fields() -> None:
    result = run_reference_backtest(
        bars=synthetic_bars(4),
        signals=[signal_record(0, "entry"), signal_record(1, "exit")],
        config=zero_cost_config(),
        run_id="trade-schema",
        instrument_multipliers=SYNTH_INSTRUMENT_MULTIPLIERS,
    )

    payload = result.trades[0].to_dict()

    assert tuple(payload) == TRADE_JOURNAL_FIELDS
    assert_trade_journal_schema(payload)
    for field in ("gross_pnl", "costs", "net_pnl", "entry_price", "exit_price"):
        assert field in payload
