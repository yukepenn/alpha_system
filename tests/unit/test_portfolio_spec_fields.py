from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from alpha_system.portfolio.spec import PortfolioSpec
from alpha_system.portfolio.validation import load_portfolio_config, validate_portfolio_config


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_portfolio_spec_required_fields_present_and_parseable() -> None:
    spec = PortfolioSpec.from_mapping(
        {
            "portfolio_id": "portfolio:test",
            "portfolio_target": {
                "schema_version": "portfolio_target_v1",
                "target_id_prefix": "target",
            },
            "position_sizing": {
                "method": "fixed_notional",
                "fixed_notional": "2500",
            },
            "capital_allocation": {
                "starting_equity": "100000",
                "cash_buffer": "0.05",
                "insufficient_capital_policy": "reject",
            },
            "risk_limits": {
                "max_position_percent": "0.2",
                "max_gross_exposure": "1.0",
                "max_net_exposure": "0.5",
            },
            "multi_symbol_constraints": {
                "required_identifier": "instrument_id",
                "max_active_instruments": 10,
            },
            "future_sector_asset_constraints": {"mode": "contract_only", "enabled": False},
            "future_correlation_aware_allocation": {"mode": "contract_only", "enabled": False},
            "signal_to_target_conversion": {"mode": "entry_exit_to_target"},
        }
    )

    assert set(PortfolioSpec.field_names()).issuperset(
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
    assert spec.portfolio_id == "portfolio:test"
    assert spec.position_sizing.fixed_notional == Decimal("2500")
    assert spec.max_gross_exposure == Decimal("1.0")
    assert spec.max_net_exposure == Decimal("0.5")
    assert spec.to_dict()["capital_allocation"]["insufficient_capital_policy"] == "reject"


def test_portfolio_example_config_validates() -> None:
    payload = load_portfolio_config(REPO_ROOT / "configs" / "portfolio" / "examples" / "fixed_notional_portfolio.json")
    result = validate_portfolio_config(payload)

    assert result.valid is True
    assert result.portfolio_id == "portfolio:fixed-notional-example"
