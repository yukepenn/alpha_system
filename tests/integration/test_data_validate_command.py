from __future__ import annotations

import json
import os
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


def test_data_validate_command_accepts_tiny_fixture(tmp_path: Path) -> None:
    summary_path = tmp_path / "validation_summary.json"
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
            "--schema-id",
            "canonical_1min_bars_v1",
            "--summary-out",
            summary_path.as_posix(),
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
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert payload["valid"] is True
    assert payload["row_count"] == 3
    assert payload["validation_issue_counts"] == {}
    assert payload["quality_flag_counts"] == {
        "correctness_only": 3,
        "synthetic": 3,
    }
    assert summary["validation_summary_path"] == summary_path.as_posix()
