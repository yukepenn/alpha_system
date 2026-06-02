from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"


def _env_with_src_path() -> dict[str, str]:
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(SRC_ROOT) if not pythonpath else os.pathsep.join([str(SRC_ROOT), pythonpath])
    )
    return env


def _run_help(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "alpha_system.cli", *args, "--help"],
        cwd=REPO_ROOT,
        env=_env_with_src_path(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_data_command_group_help_exposes_subcommands() -> None:
    result = _run_help("data")

    assert result.returncode == 0
    assert result.stderr == ""
    assert "validate" in result.stdout
    assert "build-bars" in result.stdout


def test_data_validate_help_exposes_stable_arguments() -> None:
    result = _run_help("data", "validate")

    assert result.returncode == 0
    assert result.stderr == ""
    for argument in (
        "--config",
        "--input",
        "--schema-id",
        "--calendar-id",
        "--registry-path",
        "--summary-out",
        "--json",
    ):
        assert argument in result.stdout


def test_data_build_bars_help_exposes_stable_arguments() -> None:
    result = _run_help("data", "build-bars")

    assert result.returncode == 0
    assert result.stderr == ""
    for argument in (
        "--input",
        "--instrument-config",
        "--calendar-config",
        "--output",
        "--data-version",
        "--registry-path",
        "--validation-config",
        "--json",
    ):
        assert argument in result.stdout
