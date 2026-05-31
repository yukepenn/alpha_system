"""Artifact guard for generated projects."""

from __future__ import annotations

import argparse
from pathlib import Path


FORBIDDEN_SUFFIXES = {".parquet", ".feather", ".sqlite", ".db", ".duckdb", ".log", ".pt", ".pth", ".onnx", ".pkl", ".joblib"}
FORBIDDEN_PARTS = {"data/raw", "cache", "node_modules", ".venv", "__pycache__", ".pytest_cache"}


def forbidden(path: str) -> bool:
    normalized = path.replace("\\", "/")
    suffix = Path(path).suffix.lower()
    return suffix in FORBIDDEN_SUFFIXES or any(part in normalized for part in FORBIDDEN_PARTS)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Block forbidden generated or heavy artifacts.")
    parser.add_argument("--claude-post-tool-use", action="store_true")
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args(argv)
    violations = [path for path in args.paths if forbidden(path)]
    for violation in violations:
        print(f"Forbidden artifact path: {violation}")
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
