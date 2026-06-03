from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_l2_example_config_is_tiny_synthetic_and_not_market_data() -> None:
    path = REPO_ROOT / "configs/data/l2_examples/synthetic_l2_readiness_example.json"
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert path.stat().st_size < 10_000
    assert payload["synthetic"] is True
    assert payload["deterministic"] is True
    assert payload["correctness_only"] is True
    assert payload["real_market_data"] is False


def test_l2_source_does_not_introduce_forbidden_runtime_modules() -> None:
    l2_source_paths = tuple((REPO_ROOT / "src/alpha_system/l2").glob("*.py"))
    l2_source_names = {path.name for path in l2_source_paths}

    assert "replay.py" not in l2_source_names
    assert "queue_model.py" not in l2_source_names
    assert "passive_fills.py" not in l2_source_names
    assert not any("replay" in name for name in l2_source_names)
    assert not any(name.startswith("queue") for name in l2_source_names)
    assert not any("passive_fill" in name for name in l2_source_names)


def test_no_real_l2_data_files_exist_under_data_root() -> None:
    data_root = REPO_ROOT / "data"
    l2_data_files = [
        path
        for path in data_root.rglob("*l2*")
        if path.is_file() and path.name not in {".gitkeep", "README.md"}
    ]

    assert l2_data_files == []


def test_no_l2_db_or_columnar_artifacts_are_present() -> None:
    forbidden_suffixes = {
        ".parquet",
        ".arrow",
        ".feather",
        ".sqlite",
        ".sqlite3",
        ".db",
        ".wal",
        ".log",
    }
    paths = [
        path.relative_to(REPO_ROOT).as_posix()
        for path in REPO_ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and "__pycache__" not in path.parts
        and path.suffix in forbidden_suffixes
    ]

    assert paths == []
