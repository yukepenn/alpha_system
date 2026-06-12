from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from alpha_system.backtest.costs import SpreadCost, explicit_fixture_zero_cost_model
from alpha_system.backtest.slippage import (
    SpreadSensitiveSlippageModel,
    explicit_fixture_no_slippage_model,
)
from alpha_system.runtime.cost import CostModelVersion
from alpha_system.runtime.cost.model_version import CostModelVersionError


def test_cost_model_version_serializes_consumed_primitives_and_is_hashable() -> None:
    version = CostModelVersion.from_models(
        cost_model=SpreadCost("half_spread"),
        slippage_model=SpreadSensitiveSlippageModel(spread_fraction=Decimal("0.25")),
        bbo_available=True,
    )
    same_version = CostModelVersion.from_models(
        cost_model=SpreadCost("half_spread"),
        slippage_model=SpreadSensitiveSlippageModel(spread_fraction=Decimal("0.25")),
        bbo_available=True,
    )

    assert version.cost_model_version_id == same_version.cost_model_version_id
    assert version.content_hash == same_version.content_hash
    assert hash(version)
    assert version.slippage_is_proxy is True
    assert version.bbo_available is True
    assert version.promotion_basis_allowed is False
    assert version.cost_model_descriptor == {
        "model": "spread_cost",
        "assumption": "half_spread",
    }
    assert version.slippage_model_descriptor["model"] == "spread_sensitive"

    with pytest.raises(FrozenInstanceError):
        version.bbo_available = False  # type: ignore[misc]


def test_cost_model_version_rejects_unlabeled_slippage_proxy() -> None:
    with pytest.raises(CostModelVersionError, match="proxy"):
        CostModelVersion.from_mappings(
            cost_model_descriptor={"model": "bps_cost", "bps": "1.0"},
            slippage_model_descriptor={"model": "bps", "bps": "0.5"},
            slippage_is_proxy=False,
            bbo_available=False,
        )


def test_cost_model_version_defaults_to_spread_when_bbo_is_available() -> None:
    bbo_version = CostModelVersion.from_mappings(bbo_available=True)
    fallback_version = CostModelVersion.from_mappings(bbo_available=False)

    assert bbo_version.cost_model_descriptor["components"][0]["model"] == "futures_fee_schedule"
    assert bbo_version.cost_model_descriptor["components"][1]["model"] == "spread_cost"
    assert bbo_version.slippage_model_descriptor["components"][0]["model"] == "spread_sensitive"
    assert fallback_version.cost_model_descriptor["components"][0]["model"] == "futures_fee_schedule"
    assert fallback_version.slippage_model_descriptor["components"][0]["model"] == "bps"


def test_zero_cost_version_is_diagnostic_only_and_not_promotion_basis() -> None:
    version = CostModelVersion.from_models(
        cost_model=explicit_fixture_zero_cost_model(),
        slippage_model=explicit_fixture_no_slippage_model(),
        bbo_available=False,
    )

    payload = version.to_dict()
    assert version.zero_cost_diagnostic_only is True
    assert payload["zero_cost_diagnostic_only"] is True
    assert payload["promotion_basis_allowed"] is False
    assert payload["cost_model_descriptor"]["fixture_zero_cost"] is True
