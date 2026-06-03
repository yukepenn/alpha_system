from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from alpha_system.portfolio.validation import (
    PortfolioValidationError,
    validate_portfolio_config,
    write_validation_summary,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_portfolio_validation_summary_rejects_repo_paths() -> None:
    result = validate_portfolio_config({"position_sizing": {"method": "fixed_notional", "fixed_notional": "1000"}})

    with pytest.raises(PortfolioValidationError):
        write_validation_summary(REPO_ROOT / "artifacts" / "portfolio" / "summary.json", result)


def test_no_portfolio_outputs_or_forbidden_artifacts_are_tracked() -> None:
    completed = subprocess.run(
        ["git", "ls-files", "artifacts/portfolio", "data", "metadata"],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode == 0
    unexpected = [
        line
        for line in completed.stdout.splitlines()
        if not line.endswith(("README.md", ".gitkeep"))
    ]
    assert unexpected == []
