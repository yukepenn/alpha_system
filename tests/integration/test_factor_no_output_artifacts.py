from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
VALID_DRAFT = REPO_ROOT / "configs" / "factors" / "examples" / "valid_draft_factor.json"


def _env_with_src_path() -> dict[str, str]:
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(SRC_ROOT) if not pythonpath else os.pathsep.join([str(SRC_ROOT), pythonpath])
    )
    return env


def _repo_artifact_files() -> tuple[Path, ...]:
    allowed_names = {"README.md", ".gitkeep"}
    roots = ("data", "metadata", "artifacts")
    files: list[Path] = []
    for root_name in roots:
        root = REPO_ROOT / root_name
        files.extend(path for path in root.rglob("*") if path.is_file() and path.name not in allowed_names)
    return tuple(files)


def test_factor_cli_leaves_repo_artifact_roots_clean(tmp_path: Path) -> None:
    assert _repo_artifact_files() == ()

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alpha_system.cli",
            "factor",
            "validate",
            VALID_DRAFT.as_posix(),
            "--registry-path",
            (tmp_path / "registry.sqlite3").as_posix(),
            "--summary-out",
            (tmp_path / "summary.json").as_posix(),
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
    assert _repo_artifact_files() == ()


def test_factor_cli_rejects_repo_metadata_registry_path(tmp_path: Path) -> None:
    forbidden_registry = REPO_ROOT / "metadata" / "factor_registry.sqlite3"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alpha_system.cli",
            "factor",
            "validate",
            VALID_DRAFT.as_posix(),
            "--registry-path",
            forbidden_registry.as_posix(),
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
    assert "outside the repo" in result.stderr
    assert not forbidden_registry.exists()
