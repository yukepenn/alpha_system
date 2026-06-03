from __future__ import annotations

import time
from pathlib import Path

from alpha_system.backtest.fast_path import FAST_PATH_MODE_ACCELERATED, run_fast_path_backtest
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


def test_fast_path_smoke_is_bounded_and_emits_no_benchmark_artifacts() -> None:
    before = _forbidden_repo_files()
    case = parity_case("simple_long")

    started = time.perf_counter()
    result = None
    for _ in range(25):
        result = run_fast_path_backtest(
            bars=case.bars,
            signals=case.signals,
            config=case.config,
            requested_features=case.features,
            run_id=case.run_id,
            allow_reference_fallback=False,
        )
    elapsed = time.perf_counter() - started

    assert result is not None
    assert result.mode == FAST_PATH_MODE_ACCELERATED
    assert result.summary.total_trades == 1
    assert result.result.output_paths is None
    assert elapsed < 10
    assert _forbidden_repo_files() == before


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
