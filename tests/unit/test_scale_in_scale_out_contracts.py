from __future__ import annotations

from decimal import Decimal

from alpha_system.management.spec import ManagementSpec


def test_scale_in_scale_out_contract_representation() -> None:
    spec = ManagementSpec.from_mapping(
        {
            "scale_in": {
                "enabled": True,
                "mode": "contract_only",
                "legs": [{"label": "add", "trigger_r": "1.5", "quantity_fraction": "0.25"}],
            },
            "scale_out": {
                "enabled": True,
                "mode": "contract_only",
                "legs": [{"label": "trim", "trigger_r": "1", "quantity_fraction": "0.5"}],
            },
        }
    )

    assert spec.scale_in.enabled
    assert spec.scale_in.legs[0].trigger_r == Decimal("1.5")
    assert spec.scale_out.legs[0].quantity_fraction == Decimal("0.5")
