"""FIX 3 canaries: BacktestSummary bakes Sharpe, max-drawdown, and turnover, and
they match hand computations on a known equity curve / trade set.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from alpha_system.backtest.metrics import (
    annualized_sharpe,
    equity_simple_returns,
    max_drawdown,
    median_cadence_seconds,
    turnover_ratio,
)


def test_equity_simple_returns_hand_computation() -> None:
    equities = [Decimal("100"), Decimal("110"), Decimal("99")]
    returns = equity_simple_returns(equities)
    assert returns[0] == Decimal("0.1")  # (110-100)/100
    assert returns[1] == (Decimal("99") - Decimal("110")) / Decimal("110")


def test_max_drawdown_hand_computation() -> None:
    # peak 120, trough 90 -> drawdown 30/120 = 0.25
    equities = [Decimal("100"), Decimal("120"), Decimal("90"), Decimal("110")]
    assert max_drawdown(equities) == Decimal("0.25")


def test_max_drawdown_monotonic_increase_is_zero() -> None:
    assert max_drawdown([Decimal("100"), Decimal("101"), Decimal("105")]) == Decimal("0")


def test_turnover_ratio_hand_computation() -> None:
    # traded notional 250000 over initial capital 100000 -> 2.5
    assert turnover_ratio(Decimal("250000"), initial_capital=Decimal("100000")) == Decimal("2.5")
    assert turnover_ratio(Decimal("0"), initial_capital=Decimal("0")) is None


def test_median_cadence_one_minute_bars() -> None:
    base = datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc)
    stamps = [base + timedelta(minutes=i) for i in range(5)]
    assert median_cadence_seconds(stamps) == Decimal("60")


def test_annualized_sharpe_matches_hand_computation() -> None:
    # returns with nonzero variance; bars_per_year = 4 -> sqrt(4) = 2 annualization.
    returns = [Decimal("0.01"), Decimal("-0.01"), Decimal("0.02"), Decimal("0.00")]
    n = Decimal(len(returns))
    mean = sum(returns, Decimal("0")) / n
    var = sum(((r - mean) ** 2 for r in returns), Decimal("0")) / n
    expected = (mean / var.sqrt() * Decimal("4").sqrt()).quantize(Decimal("0.00000001"))
    assert annualized_sharpe(returns, bars_per_year=Decimal("4")) == expected


def test_sharpe_none_when_undefined() -> None:
    assert annualized_sharpe([Decimal("0.01")], bars_per_year=Decimal("4")) is None  # <2 points
    assert annualized_sharpe(
        [Decimal("0.01"), Decimal("0.01")], bars_per_year=Decimal("4")
    ) is None  # zero variance
    assert annualized_sharpe(
        [Decimal("0.01"), Decimal("-0.01")], bars_per_year=None
    ) is None  # no cadence


def test_summary_exposes_metrics_in_dict() -> None:
    from alpha_system.backtest.reference import run_reference_backtest
    from tests.fixtures.backtest_reference import (
        SYNTH_INSTRUMENT_MULTIPLIERS,
        signal_record,
        synthetic_bars,
    )

    result = run_reference_backtest(
        bars=synthetic_bars(4),
        signals=[signal_record(0, "entry"), signal_record(1, "exit")],
        instrument_multipliers=SYNTH_INSTRUMENT_MULTIPLIERS,
        run_id="metrics-summary",
    )
    payload = result.summary.to_dict()
    for key in ("sharpe", "max_drawdown", "turnover", "bars_per_year"):
        assert key in payload
    # max_drawdown is always defined (>=0) once there is an equity curve.
    assert result.summary.max_drawdown is not None
    assert result.summary.max_drawdown >= 0
    # one round-trip trade -> turnover is defined and positive.
    assert result.summary.turnover is not None
    assert result.summary.turnover > 0
