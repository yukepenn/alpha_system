"""Portfolio contract primitives."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from alpha_system.core.contracts import ConfigParameters


@dataclass(frozen=True, slots=True, kw_only=True)
class PortfolioSpec:
    portfolio_target: ConfigParameters
    position_sizing: ConfigParameters
    capital_allocation: ConfigParameters
    risk_limits: ConfigParameters
    multi_symbol_constraints: ConfigParameters
    max_gross_exposure: Decimal | None
    max_net_exposure: Decimal | None
    future_sector_asset_constraints: ConfigParameters
    future_correlation_aware_allocation: ConfigParameters
    signal_to_target_conversion: ConfigParameters
