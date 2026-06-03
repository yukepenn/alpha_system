from __future__ import annotations

import pytest

from alpha_system.portfolio.spec import PortfolioSpec, PortfolioSpecError


def test_future_sector_asset_constraints_are_contract_only() -> None:
    spec = PortfolioSpec.from_mapping(
        {"future_sector_asset_constraints": {"mode": "contract_only", "enabled": False}}
    )

    assert spec.future_sector_asset_constraints.mode.value == "contract_only"
    assert spec.future_sector_asset_constraints.enabled is False

    with pytest.raises(PortfolioSpecError):
        PortfolioSpec.from_mapping({"future_sector_asset_constraints": {"mode": "contract_only", "enabled": True}})
