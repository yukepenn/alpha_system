from __future__ import annotations

from pathlib import Path

import pytest

from alpha_system.runtime.cost import CostModelVersion, CostStressSpec, load_cost_stress_config
from alpha_system.runtime.cost.spec import CostStressProfile, CostStressSpecError

CONFIG_PATH = Path("configs/runtime/cost/default_cost_stress.json")


def test_cost_stress_spec_requires_ordered_double_cost_profile() -> None:
    version = _version()
    spec = CostStressSpec(cost_model_version=version)

    assert spec.requires_double_cost is True
    assert spec.profile_names == ("base", "stress_1", "stress_2", "double_cost")
    assert spec.profile_by_name["double_cost"].cost_multiplier >= 2

    with pytest.raises(CostStressSpecError, match="double_cost"):
        CostStressSpec(
            cost_model_version=version,
            profiles=(
                CostStressProfile("base", "1.0", "1.0"),
                CostStressProfile("stress_1", "1.25", "1.25"),
                CostStressProfile("stress_2", "1.5", "1.5"),
            ),
        )


def test_cost_stress_config_loads_profiles_and_session_penalties_from_data() -> None:
    payload = load_cost_stress_config(CONFIG_PATH)
    spec = CostStressSpec.from_mapping(payload, cost_model_version=_version())

    assert spec.session_penalty_config_id == "runtime_cost_stress_default_v1"
    assert spec.penalty_for("RTH").cost_multiplier == 1
    assert spec.penalty_for("ETH").cost_multiplier > spec.penalty_for("RTH").cost_multiplier
    assert spec.penalty_for("ILLIQUID").slippage_multiplier > 1


def test_spec_fails_closed_when_requires_double_cost_is_disabled() -> None:
    with pytest.raises(CostStressSpecError, match="requires_double_cost"):
        CostStressSpec(cost_model_version=_version(), requires_double_cost=False)


def _version() -> CostModelVersion:
    return CostModelVersion.from_mappings(
        cost_model_descriptor={"model": "bps_cost", "bps": "1.0"},
        slippage_model_descriptor={"model": "bps", "bps": "0.5"},
        bbo_available=False,
    )
