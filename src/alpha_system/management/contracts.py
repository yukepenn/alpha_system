"""Position-management contract primitives."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from alpha_system.core.contracts import ConfigParameters


@dataclass(frozen=True, slots=True, kw_only=True)
class ManagementSpec:
    fixed_stop: Decimal | None
    atr_stop: ConfigParameters
    volatility_stop: ConfigParameters
    target_r_multiple: Decimal | None
    laddered_partial_take_profit: tuple[ConfigParameters, ...]
    breakeven_stop: ConfigParameters
    trailing_stop: ConfigParameters
    time_exit: timedelta | None
    eod_exit: bool
    max_trades_per_day: int | None
    cooldown: timedelta | None
    scale_in: ConfigParameters
    scale_out: ConfigParameters
    max_holding_bars: int | None
    risk_per_trade: Decimal | None
    max_position_percent: Decimal | None
