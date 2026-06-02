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


def _env_with_src_path() -> dict[str, str]:
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(SRC_ROOT) if not pythonpath else os.pathsep.join([str(SRC_ROOT), pythonpath])
    )
    return env


def _write_three_bar_calendar(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "calendar_id": "SYNTH_CLI",
                "timezone": "America/New_York",
                "regular_session": {
                    "open": "09:30",
                    "close": "09:33",
                    "session_type": "regular",
                },
                "sessions": [
                    {"trading_date": "2026-01-02", "session_type": "regular"}
                ],
                "metadata": {"fixture_scope": "synthetic cli test"},
            }
        ),
        encoding="utf-8",
    )


def test_build_bars_command_writes_only_temp_fixture_outputs(tmp_path: Path) -> None:
    instrument_config = tmp_path / "instrument.yaml"
    instrument_config.write_text(
        "instrument_id: SYNTH-1\nfixture_policy: synthetic_correctness_only\n",
        encoding="utf-8",
    )
    calendar_config = tmp_path / "calendar.json"
    _write_three_bar_calendar(calendar_config)
    validation_config = tmp_path / "validation.yaml"
    validation_config.write_text("available_latency_seconds: 5\n", encoding="utf-8")
    output_path = tmp_path / "data" / "canonical" / "bars.csv"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alpha_system.cli",
            "data",
            "build-bars",
            "--input",
            FIXTURE_PATH.as_posix(),
            "--instrument-config",
            instrument_config.as_posix(),
            "--calendar-config",
            calendar_config.as_posix(),
            "--output",
            output_path.as_posix(),
            "--data-version",
            "data:synthetic-cli:v1",
            "--validation-config",
            validation_config.as_posix(),
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
    assert payload["output_path"] == output_path.as_posix()
    assert Path(payload["manifest_path"]).exists()
    assert Path(payload["validation_summary_path"]).exists()

    with output_path.open("r", encoding="utf-8", newline="") as handle:
        rows = tuple(csv.DictReader(handle))
    assert len(rows) == 3
    assert rows[0]["session_id"] == "SYNTH_CLI:2026-01-02:regular"
    assert rows[0]["bar_index"] == "0"
    assert rows[0]["data_version"] == "data:synthetic-cli:v1"
