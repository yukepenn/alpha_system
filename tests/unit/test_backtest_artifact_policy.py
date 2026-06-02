from __future__ import annotations

from pathlib import Path

import pytest

from alpha_system.backtest.engine_config import load_reference_engine_config
from alpha_system.backtest.results import (
    BacktestOutputError,
    resolve_backtest_output_dir,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_backtest_default_output_root_is_local_only_outside_repo() -> None:
    output_dir = resolve_backtest_output_dir(None)

    assert output_dir.as_posix().startswith("/tmp/alpha_system/backtests")
    assert not output_dir.is_relative_to(REPO_ROOT)


def test_backtest_output_policy_rejects_repo_and_forbidden_suffixes(tmp_path: Path) -> None:
    with pytest.raises(BacktestOutputError, match="outside the repo"):
        resolve_backtest_output_dir(REPO_ROOT / "artifacts" / "backtests")

    with pytest.raises(BacktestOutputError, match="must not be a DB"):
        resolve_backtest_output_dir(tmp_path / "backtest.sqlite")


def test_reference_non_test_config_has_non_zero_cost_hook() -> None:
    config = load_reference_engine_config("configs/execution/reference_1min.yaml")

    assert config.execution_timing == "next_bar_conservative"
    assert config.same_bar_policy == "adverse_first"
    assert config.cost_model.fixed_bps > 0
