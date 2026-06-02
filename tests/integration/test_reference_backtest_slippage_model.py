from __future__ import annotations

from decimal import Decimal

from alpha_system.backtest.execution_config import ExecutionConfig
from alpha_system.backtest.reference import run_reference_backtest
from alpha_system.backtest.slippage import BpsSlippageModel, CompositeSlippageModel
from alpha_system.core.hashing import hash_config
from tests.fixtures.backtest_reference import signal_record, synthetic_bars


def test_reference_backtest_surfaces_slippage_model_in_reproducibility_metadata() -> None:
    config = ExecutionConfig(
        slippage_model=CompositeSlippageModel(models=(BpsSlippageModel(Decimal("25")),))
    )

    result = run_reference_backtest(
        bars=synthetic_bars(4),
        signals=[signal_record(0, "entry"), signal_record(1, "exit")],
        config=config,
        run_id="slippage-metadata",
    )

    parameters = result.manifest["parameters"]
    assert parameters["slippage_model"]["components"][0]["bps"] == "25"
    assert parameters["research_only"] is True
    assert result.manifest["config_hash"] == hash_config(config.to_dict())
