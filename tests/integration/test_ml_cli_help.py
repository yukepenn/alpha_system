from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"


def test_ml_cli_help() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alpha_system.cli", "ml", "run", "--help"],
        check=False,
        capture_output=True,
        cwd=REPO_ROOT,
        env=_env_with_src_path(),
        text=True,
    )

    assert result.returncode == 0
    assert "alpha ml run" in result.stdout
    assert "--feature-set" in result.stdout
    assert "--registry-path" in result.stdout


def _env_with_src_path() -> dict[str, str]:
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(SRC_ROOT) if not pythonpath else os.pathsep.join([str(SRC_ROOT), pythonpath])
    )
    return env
