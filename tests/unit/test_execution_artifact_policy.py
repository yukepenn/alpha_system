from __future__ import annotations

from pathlib import Path

from alpha_system.backtest.execution_config import default_execution_config
from alpha_system.backtest.reference import run_reference_backtest
from tests.fixtures.backtest_reference import SYNTH_INSTRUMENT_MULTIPLIERS, signal_record, synthetic_bars


def test_execution_config_does_not_write_repo_artifacts() -> None:
    config = default_execution_config()
    before = _repo_execution_artifacts()

    run_reference_backtest(
        bars=synthetic_bars(4),
        signals=[signal_record(0, "entry"), signal_record(1, "exit")],
        config=config,
        run_id="artifact-policy-no-output",
        instrument_multipliers=SYNTH_INSTRUMENT_MULTIPLIERS,
    )

    assert _repo_execution_artifacts() == before


def test_backtest_outputs_stay_in_explicit_tempdir(tmp_path: Path) -> None:
    output_dir = tmp_path / "execution_outputs"
    result = run_reference_backtest(
        bars=synthetic_bars(4),
        signals=[signal_record(0, "entry"), signal_record(1, "exit")],
        config=default_execution_config(),
        output_dir=output_dir,
        run_manifest_path=output_dir / "manifest.json",
        run_id="artifact-policy-tempdir",
        instrument_multipliers=SYNTH_INSTRUMENT_MULTIPLIERS,
    )

    assert result.output_paths is not None
    assert result.output_paths.trades_path.startswith(output_dir.as_posix())
    assert result.output_paths.equity_path.startswith(output_dir.as_posix())


def _repo_execution_artifacts() -> set[str]:
    root = Path("artifacts/execution_validations")
    if not root.exists():
        return set()
    return {
        path.as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.name not in {"README.md", ".gitkeep"}
    }
