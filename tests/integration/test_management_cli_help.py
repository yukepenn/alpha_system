from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"


def _env_with_src_path() -> dict[str, str]:
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(SRC_ROOT) if not pythonpath else os.pathsep.join([str(SRC_ROOT), pythonpath])
    return env


def _run_management(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "alpha_system.cli", "management", "grid", *args],
        cwd=REPO_ROOT,
        env=_env_with_src_path(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_management_grid_help_exposes_validation_only_arguments() -> None:
    result = _run_management("--help")

    assert result.returncode == 0
    assert result.stderr == ""
    for argument in ("--config", "--strategy-grid-ref", "--validate-only", "--registry-path", "--summary-out"):
        assert argument in result.stdout
    assert "ASV1-P21" in result.stdout


def test_management_grid_validates_bounded_config_and_temp_summary(tmp_path: Path) -> None:
    config = tmp_path / "management.json"
    summary = tmp_path / "summary.json"
    config.write_text(
        json.dumps(
            {
                "management": {
                    "management_id": "management:cli",
                    "fixed_stop": {"enabled": True, "stop_pct": "0.02"},
                    "target_r_multiple": {"enabled": True, "r_multiple": "2"},
                },
                "management_grid": {
                    "parameters": {
                        "fixed_stop.stop_pct": ["0.01", "0.02"],
                        "target_r_multiple.r_multiple": ["1", "2"],
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    result = _run_management("--config", config.as_posix(), "--summary-out", summary.as_posix())

    assert result.returncode == 0
    assert result.stderr == ""
    assert "Mode: validation only" in result.stdout
    payload = json.loads(summary.read_text(encoding="utf-8"))
    assert payload["grid_combinations"] == 4
    assert payload["execution_deferred_to"] == "ASV1-P21"


def test_management_grid_rejects_unbounded_config(tmp_path: Path) -> None:
    config = tmp_path / "management_unbounded.json"
    config.write_text(
        json.dumps(
            {
                "management": {"fixed_stop": {"enabled": True, "stop_pct": "0.02"}},
                "management_grid": {"parameters": {"fixed_stop.stop_pct": "*"}},
            }
        ),
        encoding="utf-8",
    )

    result = _run_management("--config", config.as_posix())

    assert result.returncode == 2
    assert "unbounded" in result.stderr
