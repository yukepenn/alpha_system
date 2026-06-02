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


def _repo_artifact_files() -> tuple[Path, ...]:
    allowed_names = {"README.md", ".gitkeep"}
    files: list[Path] = []
    for root_name in ("data", "metadata", "artifacts"):
        root = REPO_ROOT / root_name
        files.extend(path for path in root.rglob("*") if path.is_file() and path.name not in allowed_names)
    return tuple(files)


def test_data_cli_runs_leave_repo_artifact_roots_clean(tmp_path: Path) -> None:
    assert _repo_artifact_files() == ()
    summary_path = tmp_path / "summaries" / "validation.json"
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
    assert summary_path.exists()
    assert _repo_artifact_files() == ()


def test_summary_output_rejects_committed_repo_path(tmp_path: Path) -> None:
    committed_output = REPO_ROOT / "docs" / "generated_validation_summary.json"
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
            "--summary-out",
            committed_output.as_posix(),
            "--json",
        ],
        cwd=tmp_path,
        env=_env_with_src_path(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 2
    assert "committed docs" in result.stderr
    assert not committed_output.exists()


def test_build_bars_refuses_non_fixture_input_by_default(tmp_path: Path) -> None:
    non_fixture = tmp_path / "input.csv"
    non_fixture.write_text(FIXTURE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    instrument_config = tmp_path / "instrument.yaml"
    instrument_config.write_text("instrument_id: SYNTH-1\n", encoding="utf-8")
    calendar_config = tmp_path / "calendar.json"
    calendar_config.write_text(
        json.dumps(
            {
                "calendar_id": "SYNTH_CLI",
                "timezone": "America/New_York",
                "regular_session": {"open": "09:30", "close": "09:33"},
                "sessions": [{"trading_date": "2026-01-02"}],
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alpha_system.cli",
            "data",
            "build-bars",
            "--input",
            non_fixture.as_posix(),
            "--instrument-config",
            instrument_config.as_posix(),
            "--calendar-config",
            calendar_config.as_posix(),
            "--output",
            (tmp_path / "data" / "canonical" / "bars.csv").as_posix(),
            "--data-version",
            "data:synthetic-cli:v1",
            "--json",
        ],
        cwd=tmp_path,
        env=_env_with_src_path(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 2
    assert "not under" in result.stderr
