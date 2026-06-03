from __future__ import annotations

import subprocess
from pathlib import Path

from alpha_system.backtest.parity import certify_parity
from alpha_system.backtest.parity_cases import parity_case


REPO_ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN_SUFFIXES = {
    ".arrow",
    ".db",
    ".db-journal",
    ".feather",
    ".log",
    ".npy",
    ".npz",
    ".parquet",
    ".sqlite",
    ".sqlite3",
    ".wal",
}


def test_fast_path_parity_runs_do_not_write_repo_artifacts() -> None:
    before = _forbidden_repo_files()
    certification = certify_parity((parity_case("simple_long"), parity_case("same_bar_ambiguity")))

    assert certification.certified
    assert _forbidden_repo_files() == before


def test_no_fast_path_forbidden_artifacts_are_tracked() -> None:
    completed = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode == 0
    tracked = [
        line
        for line in completed.stdout.splitlines()
        if not line.startswith("tests/fixtures/")
        and Path(line).suffix.lower() in FORBIDDEN_SUFFIXES
    ]
    assert tracked == []
    assert "runs/" not in completed.stdout


def _forbidden_repo_files() -> tuple[str, ...]:
    files: list[str] = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.is_relative_to(REPO_ROOT / "tests" / "fixtures"):
            continue
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            files.append(path.relative_to(REPO_ROOT).as_posix())
    return tuple(sorted(files))
