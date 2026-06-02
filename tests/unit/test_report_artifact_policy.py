from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from alpha_system.reports.factor_card import (
    default_report_output_path,
    resolve_report_output_path,
)
from alpha_system.reports.report_models import ReportModelError


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_default_report_output_path_is_local_artifacts_reports_root() -> None:
    path = default_report_output_path("factor_card.md")

    assert path.as_posix() == "artifacts/reports/factor_card.md"
    assert not path.is_absolute()


def test_repo_report_output_outside_artifacts_reports_is_rejected() -> None:
    with pytest.raises(ReportModelError):
        resolve_report_output_path("docs/generated_factor_card.md")


def test_temp_report_output_path_is_allowed(tmp_path) -> None:
    assert resolve_report_output_path(tmp_path / "factor_card.md") == tmp_path / "factor_card.md"


def test_no_run_or_artifact_paths_are_staged() -> None:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    staged = result.stdout.splitlines()
    assert not any(path.startswith("runs/") for path in staged)
    assert not any(path.startswith("artifacts/") for path in staged)


def test_runs_directory_has_no_tracked_files() -> None:
    result = subprocess.run(
        ["git", "ls-files", "runs"],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    assert result.stdout == ""
