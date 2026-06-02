from __future__ import annotations

from pathlib import Path

import pytest

from alpha_system.backtest.execution_config import (
    ExecutionConfig,
    ExecutionConfigError,
    default_execution_config,
    fixture_zero_cost_execution_config,
    load_execution_config,
)


def test_default_execution_config_is_nonzero_and_conservative() -> None:
    config = default_execution_config()

    assert config.zero_cost_fixture is False
    assert config.cost_model.total_is_zero is False
    assert config.slippage_model.total_is_zero is False
    assert config.execution_timing == "next_bar_conservative"
    assert config.same_bar_policy == "adverse_first"


def test_zero_cost_requires_explicit_fixture_config() -> None:
    config = fixture_zero_cost_execution_config()

    assert config.zero_cost_fixture is True
    assert config.cost_model.total_is_zero is True
    assert config.slippage_model.total_is_zero is True


def test_zero_cost_mapping_without_fixture_flag_is_rejected() -> None:
    with pytest.raises(ExecutionConfigError):
        ExecutionConfig.from_mapping(
            {
                "cost_model": {"model": "zero_cost", "fixture_only": True},
                "slippage_model": {"model": "none", "fixture_only": True},
                "zero_cost_fixture": False,
            }
        )


def test_curated_cost_model_configs_are_explicit_about_zero_cost_policy() -> None:
    config_root = Path("configs/execution/cost_models")

    default_config = load_execution_config(config_root / "default_conservative.json")
    spread_config = load_execution_config(config_root / "spread_sensitive_conservative.json")
    fixture_config = load_execution_config(config_root / "fixture_zero_cost.json")

    assert default_config.zero_cost_fixture is False
    assert default_config.cost_model.total_is_zero is False
    assert spread_config.zero_cost_fixture is False
    assert spread_config.cost_model.total_is_zero is False
    assert fixture_config.zero_cost_fixture is True
    assert fixture_config.cost_model.total_is_zero is True
