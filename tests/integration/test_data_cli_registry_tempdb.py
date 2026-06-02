from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "data" / "synthetic_1min_bars.csv"
VALIDATION_CONFIG = REPO_ROOT / "configs" / "data" / "validation_example.yaml"


def _env_with_src_path() -> dict[str, str]:
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(SRC_ROOT) if not pythonpath else os.pathsep.join([str(SRC_ROOT), pythonpath])
    )
    return env


def test_data_validate_registry_write_targets_temp_database(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alpha_system.cli",
            "data",
            "validate",
            "--config",
            VALIDATION_CONFIG.as_posix(),
            "--input",
            FIXTURE_PATH.as_posix(),
            "--registry-path",
            registry_path.as_posix(),
            "--json",
        ],
        cwd=tmp_path,
        env=_env_with_src_path(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["registry_path"] == registry_path.as_posix()
    assert payload["data_version"].startswith("data:data_cli_validation:")

    with sqlite3.connect(registry_path) as connection:
        count = connection.execute("SELECT count(*) FROM dataset_versions").fetchone()[0]
    assert count == 1
