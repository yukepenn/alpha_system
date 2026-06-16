"""Deterministic summary metrics derived from the reference equity curve/trades.

These are baked into ``BacktestSummary`` so the post-cost-LEVEL gate can read
Sharpe, max-drawdown, and turnover directly instead of re-deriving them. All math
is standard and stated explicitly:

* **returns** are per-bar simple returns of the dollar equity curve,
  ``r_t = (E_t - E_{t-1}) / E_{t-1}`` over consecutive equity points (skipping any
  point whose prior equity is zero, which cannot define a simple return).
* **Sharpe** is ``mean(r) / std(r) * sqrt(bars_per_year)`` with a zero risk-free
  rate and the *population* standard deviation (``ddof=0``). ``bars_per_year`` is
  derived from the median wall-clock bar cadence
  (``seconds_per_year / cadence_seconds``, ``seconds_per_year = 365.25 days``); it
  is ``None`` (and Sharpe ``None``) when fewer than two equity points or a
  zero-variance return series make Sharpe undefined.
* **max_drawdown** is the largest peak-to-trough decline of the equity curve as a
  non-negative fraction of the running peak (``max_t (peak_t - E_t) / peak_t``).
* **turnover** is total absolute traded dollar notional divided by initial
  capital. Each closed trade contributes its entry leg plus exit leg notional
  ``price * quantity * multiplier``; initial capital is ``final_equity - net_pnl``.

Decimal in, Decimal out: ``float`` is used only for the ``sqrt``/``ln`` transcendental
in the Sharpe annualization, then re-quantized to ``Decimal``.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import Any

_SECONDS_PER_YEAR = Decimal("31557600")  # 365.25 * 24 * 3600
_QUANT = Decimal("0.00000001")


def _decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def equity_simple_returns(equities: Sequence[Decimal]) -> list[Decimal]:
    """Per-bar simple returns of a dollar equity curve."""
    returns: list[Decimal] = []
    for previous, current in zip(equities, equities[1:], strict=False):
        if previous == 0:
            continue
        returns.append((current - previous) / previous)
    return returns


def median_cadence_seconds(timestamps: Sequence[Any]) -> Decimal | None:
    """Median wall-clock spacing, in seconds, between consecutive bar timestamps."""
    gaps: list[Decimal] = []
    for previous, current in zip(timestamps, timestamps[1:], strict=False):
        delta = (current - previous).total_seconds()
        if delta > 0:
            gaps.append(_decimal(delta))
    if not gaps:
        return None
    gaps.sort()
    mid = len(gaps) // 2
    if len(gaps) % 2 == 1:
        return gaps[mid]
    return (gaps[mid - 1] + gaps[mid]) / Decimal("2")


def annualized_sharpe(
    returns: Sequence[Decimal],
    *,
    bars_per_year: Decimal | None,
) -> Decimal | None:
    """Annualized Sharpe with zero risk-free rate and population std (ddof=0)."""
    n = len(returns)
    if n < 2 or bars_per_year is None or bars_per_year <= 0:
        return None
    count = Decimal(n)
    mean = sum(returns, Decimal("0")) / count
    variance = sum(((r - mean) ** 2 for r in returns), Decimal("0")) / count
    if variance <= 0:
        return None
    std = variance.sqrt()
    per_bar_sharpe = mean / std
    annualization = bars_per_year.sqrt()
    return (per_bar_sharpe * annualization).quantize(_QUANT)


def max_drawdown(equities: Sequence[Decimal]) -> Decimal | None:
    """Largest peak-to-trough decline as a non-negative fraction of the peak."""
    if not equities:
        return None
    peak = equities[0]
    worst = Decimal("0")
    for equity in equities:
        if equity > peak:
            peak = equity
        if peak > 0:
            drawdown = (peak - equity) / peak
            if drawdown > worst:
                worst = drawdown
    return worst.quantize(_QUANT)


def turnover_ratio(
    traded_notional: Decimal,
    *,
    initial_capital: Decimal,
) -> Decimal | None:
    """Total absolute traded dollar notional divided by initial capital."""
    if initial_capital <= 0:
        return None
    return (traded_notional / initial_capital).quantize(_QUANT)


__all__ = [
    "annualized_sharpe",
    "equity_simple_returns",
    "max_drawdown",
    "median_cadence_seconds",
    "turnover_ratio",
]
