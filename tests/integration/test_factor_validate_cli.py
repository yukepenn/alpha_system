from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
VALID_DRAFT = REPO_ROOT / "configs" / "factors" / "examples" / "valid_draft_factor.json"
INVALID_LABEL = (
    REPO_ROOT / "configs" / "factors" / "examples" / "invalid_label_input_factor.json"
)


def _env_with_src_path() -> dict[str, str]:
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(SRC_ROOT) if not pythonpath else os.pathsep.join([str(SRC_ROOT), pythonpath])
    )
    return env


def test_factor_validate_help_exposes_stable_arguments() -> None:
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
    for argument in (
        "spec_path",
        "--registry-path",
        "--code-path",
        "--validation-artifact-path",
        "--summary-out",
        "--used-field",
        "--json",
    ):
        assert argument in result.stdout


def test_factor_validate_writes_temp_registry_and_summary(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    summary_path = tmp_path / "factor_summary.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alpha_system.cli",
            "factor",
            "validate",
            VALID_DRAFT.as_posix(),
            "--registry-path",
            registry_path.as_posix(),
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
    assert payload["valid"] is True
    assert payload["registry_written"] is True
    assert payload["validation_summary_path"] == summary_path.as_posix()
    assert summary_path.exists()

    with sqlite3.connect(registry_path) as connection:
        count = connection.execute("SELECT count(*) FROM factor_versions").fetchone()[0]
    assert count == 1


def test_factor_validate_invalid_spec_returns_validation_failure(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alpha_system.cli",
            "factor",
            "validate",
            INVALID_LABEL.as_posix(),
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
    assert payload["issue_counts"] == {"spec_invalid": 1}
