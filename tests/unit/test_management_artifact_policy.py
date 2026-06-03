from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from alpha_system.management.validation import (
    ManagementValidationError,
    validate_management_config,
    write_validation_summary,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_management_validation_summary_rejects_repo_paths() -> None:
    result = validate_management_config({"fixed_stop": {"enabled": True, "stop_pct": "0.02"}})

    with pytest.raises(ManagementValidationError):
        write_validation_summary(REPO_ROOT / "artifacts" / "management_studies" / "summary.json", result)


def test_no_management_outputs_are_tracked() -> None:
    completed = subprocess.run(
        ["git", "ls-files", "artifacts/management_studies", "artifacts/execution_validations"],
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
