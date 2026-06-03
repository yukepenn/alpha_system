from __future__ import annotations

from decimal import Decimal

from alpha_system.management.spec import ManagementSpec


def test_management_spec_required_fields_present_and_parseable() -> None:
    spec = ManagementSpec.from_mapping(
        {
            "management_id": "management:test",
            "fixed_stop": {"enabled": True, "stop_pct": "0.02"},
            "atr_stop": {"enabled": True, "atr_multiple": "2", "atr_value": "1.5"},
            "volatility_stop": {
                "enabled": True,
                "volatility_multiple": "3",
                "volatility_value": "0.5",
            },
            "target_r_multiple": {"enabled": True, "r_multiple": "2"},
            "laddered_partial_take_profit": {
                "enabled": True,
                "steps": [{"label": "half", "threshold_r": "1", "exit_fraction": "0.5"}],
            },
            "breakeven_stop": {"enabled": True, "trigger_r": "1", "offset_r": "0.1"},
            "trailing_stop": {"enabled": True, "trail_r": "1.5"},
            "time_exit": {"enabled": True, "max_minutes": 30},
            "eod_exit": True,
            "max_trades_per_day": 3,
            "cooldown": {"enabled": True, "bars": 2},
            "scale_in": {
                "enabled": True,
                "mode": "contract_only",
                "legs": [{"label": "add", "trigger_r": "1", "quantity_fraction": "0.25"}],
            },
            "scale_out": {
                "enabled": True,
                "mode": "contract_only",
                "legs": [{"label": "trim", "trigger_r": "1", "quantity_fraction": "0.25"}],
            },
            "max_holding_bars": 12,
            "risk_per_trade": "0.01",
            "max_position_percent": "0.2",
        }
    )

    assert set(ManagementSpec.field_names()).issuperset(
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
    assert spec.management_id == "management:test"
    assert spec.risk_per_trade == Decimal("0.01")
    assert spec.to_dict()["scale_out"]["legs"][0]["label"] == "trim"
