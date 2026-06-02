from __future__ import annotations

from alpha_system.core.schema import contract_field_names
from alpha_system.management.contracts import ManagementSpec
from alpha_system.portfolio.contracts import PortfolioSpec


def test_management_spec_support_fields_present() -> None:
    assert set(contract_field_names(ManagementSpec)).issuperset(
        {
            "fixed_stop",
            "atr_stop",
            "volatility_stop",
            "target_r_multiple",
            "laddered_partial_take_profit",
            "breakeven_stop",
            "trailing_stop",
            "time_exit",
            "eod_exit",
            "max_trades_per_day",
            "cooldown",
            "scale_in",
            "scale_out",
            "max_holding_bars",
            "risk_per_trade",
            "max_position_percent",
        }
    )


def test_portfolio_spec_support_fields_present() -> None:
    assert set(contract_field_names(PortfolioSpec)).issuperset(
        {
            "portfolio_target",
            "position_sizing",
            "capital_allocation",
            "risk_limits",
            "multi_symbol_constraints",
            "max_gross_exposure",
            "max_net_exposure",
            "future_sector_asset_constraints",
            "future_correlation_aware_allocation",
            "signal_to_target_conversion",
        }
    )
