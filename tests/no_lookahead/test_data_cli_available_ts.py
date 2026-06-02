from __future__ import annotations

import csv
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


def test_data_validate_enforces_available_ts_latency_through_cli(tmp_path: Path) -> None:
    input_path = tmp_path / "lookahead.csv"
    with FIXTURE_PATH.open("r", encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))
    rows[0]["available_ts"] = "2026-01-02T14:31:04Z"

    with FIXTURE_PATH.open("r", encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        columns = reader.fieldnames
    assert columns is not None
    with input_path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

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
            input_path.as_posix(),
            "--json",
        ],
        cwd=tmp_path,
        env=_env_with_src_path(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 1
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["valid"] is False
    assert payload["validation_issue_counts"]["available_before_bar_latency"] == 1
