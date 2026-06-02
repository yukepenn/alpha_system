from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HEAVY_SUFFIXES = (
    ".parquet",
    ".arrow",
    ".feather",
    ".sqlite",
    ".sqlite3",
    ".db",
    ".db-journal",
    ".wal",
    ".log",
)
TABULAR_SUFFIXES = (".csv", ".jsonl")


def _tracked_files() -> tuple[str, ...]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0
    assert result.stderr == ""
    return tuple(line for line in result.stdout.splitlines() if line)


def test_no_generated_data_or_heavy_artifacts_are_tracked() -> None:
    tracked = _tracked_files()

    forbidden: list[str] = []
    for path in tracked:
        path_obj = Path(path)
        if path.startswith("runs/"):
            forbidden.append(path)
        if path.startswith("data/") and path_obj.name not in {"README.md", ".gitkeep"}:
            forbidden.append(path)
        if path.endswith(HEAVY_SUFFIXES):
            forbidden.append(path)
        if path.endswith(TABULAR_SUFFIXES) and not path.startswith("tests/fixtures/"):
            forbidden.append(path)

    assert forbidden == []
