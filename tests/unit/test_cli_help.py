from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


SRC_ROOT = Path(__file__).resolve().parents[2] / "src"


def _env_with_src_path() -> dict[str, str]:
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(SRC_ROOT) if not pythonpath else os.pathsep.join([str(SRC_ROOT), pythonpath])
    )
    return env


@pytest.mark.parametrize("module_name", ["alpha_system", "alpha_system.cli"])
def test_module_help_returns_success(module_name: str, tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", module_name, "--help"],
        cwd=tmp_path,
        env=_env_with_src_path(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()
    assert "alpha" in result.stdout.lower()
    assert result.stderr == ""
