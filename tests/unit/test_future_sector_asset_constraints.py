from __future__ import annotations

import pytest

from alpha_system.portfolio.universe_constraints import (
    FutureAssetExposureConstraint,
    FutureSectorExposureConstraint,
    UniverseConstraintError,
)
from alpha_system.portfolio.spec import PortfolioSpec, PortfolioSpecError


def test_future_sector_asset_constraints_are_contract_only() -> None:
    spec = PortfolioSpec.from_mapping(
        {"future_sector_asset_constraints": {"mode": "contract_only", "enabled": False}}
    )

    assert spec.future_sector_asset_constraints.mode.value == "contract_only"
    assert spec.future_sector_asset_constraints.enabled is False

    with pytest.raises(PortfolioSpecError):
        PortfolioSpec.from_mapping({"future_sector_asset_constraints": {"mode": "contract_only", "enabled": True}})


def test_future_sector_and_asset_exposure_constraints_are_represented_only() -> None:
    sector = FutureSectorExposureConstraint(
        constraint_id="sector_contract",
        sector="synthetic_sector",
        max_exposure="0.25",
    )
    asset = FutureAssetExposureConstraint(
        constraint_id="asset_contract",
        asset_class="equity",
        max_exposure="1.0",
    )

    assert sector.to_dict()["mode"] == "contract_only"
    assert sector.to_dict()["enabled"] is False
    assert asset.to_dict()["asset_class"] == "equity"

    with pytest.raises(UniverseConstraintError, match="representation only"):
        FutureSectorExposureConstraint(
            constraint_id="enabled_sector",
            sector="synthetic_sector",
            enabled=True,
        )
