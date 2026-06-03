from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"


def test_grid_run_help_exposes_stable_arguments() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alpha_system.cli", "grid", "run", "--help"],
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
        "--config",
        "--strategy-spec",
        "--management-spec",
        "--portfolio-spec",
        "--data-version",
        "--factor-version",
        "--label-version",
        "--execution-config",
        "--engine",
        "--registry-path",
        "--output-dir",
        "--manifest-out",
        "--json",
    ):
        assert argument in result.stdout


def _env_with_src_path() -> dict[str, str]:
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(SRC_ROOT) if not pythonpath else os.pathsep.join([str(SRC_ROOT), pythonpath])
    )
    return env
