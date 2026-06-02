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


def test_factor_materialize_help_exposes_stable_arguments() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alpha_system.cli", "factor", "materialize", "--help"],
        cwd=REPO_ROOT,
        env=_env_with_src_path(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    for argument in (
        "spec_path",
        "--canonical-data-path",
        "--dataset-version",
        "--data-version",
        "--instrument",
        "--session-id",
        "--output-policy",
        "--registry-path",
        "--output-dir",
        "--manifest-out",
        "--compute-version",
        "--json",
    ):
        assert argument in result.stdout


def test_factor_validate_help_still_works() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alpha_system.cli", "factor", "validate", "--help"],
        cwd=REPO_ROOT,
        env=_env_with_src_path(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert "--used-field" in result.stdout
