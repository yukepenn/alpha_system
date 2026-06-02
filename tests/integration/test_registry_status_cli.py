from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from alpha_system.core.registry import init_registry


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"


def _env_with_src_path() -> dict[str, str]:
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(SRC_ROOT) if not pythonpath else os.pathsep.join([str(SRC_ROOT), pythonpath])
    )
    return env


def _run_cli(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "alpha_system.cli", *args],
        cwd=cwd,
        env=_env_with_src_path(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_registry_status_help_resolves_without_creating_database(tmp_path: Path) -> None:
    result = _run_cli(["registry", "status", "--help"], cwd=tmp_path)

    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()
    assert "registry status" in result.stdout
    assert not (tmp_path / "metadata" / "registry.sqlite3").exists()


def test_registry_status_reports_temp_database_as_valid(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    init_registry(registry_path)

    result = _run_cli(
        ["registry", "status", "--registry-path", str(registry_path), "--json"],
        cwd=tmp_path,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["registry_path"] == registry_path.as_posix()
    assert payload["exists"] is True
    assert payload["valid"] is True
    assert payload["local_only"] is True
    assert payload["schema_version"] == 1
    assert payload["migrations_current"] is True
    assert payload["missing_tables"] == []
    assert result.stderr == ""


def test_registry_status_reads_registry_path_from_config(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    config_path = tmp_path / "registry.yaml"
    init_registry(registry_path)
    config_path.write_text(f"registry_path: {registry_path.as_posix()}\n", encoding="utf-8")

    result = _run_cli(["registry", "status", "--config", str(config_path)], cwd=tmp_path)

    assert result.returncode == 0
    assert f"Registry: {registry_path.as_posix()}" in result.stdout
    assert "Status: OK" in result.stdout
    assert result.stderr == ""


def test_registry_status_reports_missing_database_without_creating_it(
    tmp_path: Path,
) -> None:
    missing_path = tmp_path / "missing.sqlite3"

    result = _run_cli(
        ["registry", "status", "--registry-path", str(missing_path), "--json"],
        cwd=tmp_path,
    )

    assert result.returncode != 0
    payload = json.loads(result.stdout)
    assert payload["exists"] is False
    assert payload["valid"] is False
    assert payload["missing_tables"]
    assert "does not exist" in payload["status_message"]
    assert "registry status invalid" in result.stderr
    assert not missing_path.exists()
