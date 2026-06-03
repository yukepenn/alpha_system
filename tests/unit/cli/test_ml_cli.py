from __future__ import annotations

from alpha_system.cli.main import main


def test_ml_cli_missing_config_returns_usage_error() -> None:
    assert main(["ml", "run"]) == 2
