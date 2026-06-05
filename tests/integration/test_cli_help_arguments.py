from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"


CLI_HELP_CASES = (
    (
        ("backtest", "run"),
        (
            "--strategy-id",
            "--strategy-version",
            "--management-spec",
            "--portfolio-spec",
            "--data-version",
            "--factor-version",
            "--execution-config",
            "--bars-path",
            "--signals-path",
            "--registry-path",
            "--output-dir",
            "--run-manifest",
        ),
    ),
    (
        ("grid", "run"),
        (
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
        ),
    ),
    (
        ("management", "grid"),
        (
            "--config",
            "--strategy-grid-ref",
            "--validate-only",
            "--registry-path",
            "--summary-out",
            "ASV1-P21",
        ),
    ),
    (
        ("ml", "run"),
        (
            "alpha ml run",
            "--feature-set",
            "--registry-path",
        ),
    ),
    (
        ("factor", "materialize"),
        (
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
        ),
    ),
    (
        ("factor", "validate"),
        (
            "--used-field",
        ),
    ),
    (
        ("study", "run"),
        (
            "--config",
            "--factor-version",
            "--label-version",
            "--data-version",
            "--factor-values-path",
            "--labels-path",
            "--horizon-seconds",
            "--output-dir",
            "--registry-path",
            "--manifest-out",
            "--json",
        ),
    ),
    (
        ("report", "build"),
        (
            "--run-id",
            "--registry-path",
            "--artifact-manifest",
            "--run-manifest",
            "--config",
            "--output-dir",
            "--source-root",
            "--include-html",
        ),
    ),
)


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


@pytest.mark.parametrize(
    ("cli_invocation", "expected_substrings"),
    CLI_HELP_CASES,
    ids=(" ".join(invocation) for invocation, _ in CLI_HELP_CASES),
)
def test_cli_help_exposes_stable_arguments(
    cli_invocation: tuple[str, ...],
    expected_substrings: tuple[str, ...],
) -> None:
    result = _run_help(*cli_invocation)

    assert result.returncode == 0
    assert result.stderr == ""
    for expected_substring in expected_substrings:
        assert expected_substring in result.stdout


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
