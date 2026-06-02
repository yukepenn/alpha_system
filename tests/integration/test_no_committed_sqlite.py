from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_no_sqlite_or_db_files_are_tracked() -> None:
    result = subprocess.run(
        [
            "git",
            "ls-files",
            "*.sqlite",
            "*.sqlite3",
            "*.db",
            "*.db-journal",
            "*.wal",
        ],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
