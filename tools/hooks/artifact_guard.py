"""Block heavy, raw, generated, cache, and model artifacts."""

from __future__ import annotations

import argparse
import fnmatch
from pathlib import PurePosixPath


FORBIDDEN_SUFFIXES = {
    ".parquet",
    ".feather",
    ".sqlite",
    ".db",
    ".duckdb",
    ".log",
    ".pt",
    ".pth",
    ".onnx",
    ".pkl",
    ".joblib",
}
FORBIDDEN_PARTS = {"node_modules", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache", "cache"}
RAW_DATA_PREFIXES = {"data/raw", "raw", "artifacts/raw"}
PLACEHOLDER_EXCEPTIONS = ("**/.gitkeep", "**/README.md")
PLACEHOLDER_DIRS = (
    "data/raw/**",
    "data/cache/**",
    "data/canonical/**",
    "data/factors/**",
    "artifacts/raw/**",
)
CURATED_SUFFIXES = {".md", ".json", ".csv"}
CURATED_PREFIXES = {"docs", "reviews", "handoffs", "specs", "campaigns", "evals", "decisions"}


def normalized(path: str) -> str:
    value = path.replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    return value


def is_curated_summary(path: str) -> bool:
    parsed = PurePosixPath(normalized(path))
    return parsed.suffix.lower() in CURATED_SUFFIXES and parsed.parts and parsed.parts[0] in CURATED_PREFIXES


def matches_any(path: str, patterns: tuple[str, ...]) -> bool:
    clean = normalized(path)
    for pattern in patterns:
        if fnmatch.fnmatch(clean, pattern):
            return True
        if pattern.startswith("**/") and fnmatch.fnmatch(clean, pattern[3:]):
            return True
    return False


def is_placeholder_exception(path: str) -> bool:
    clean = normalized(path)
    # Keep these defaults in sync with frontier.yaml artifacts.placeholder_*.
    # The hook avoids loading YAML so pre-commit stays dependency-light.
    return matches_any(clean, PLACEHOLDER_EXCEPTIONS) and matches_any(clean, PLACEHOLDER_DIRS)


def forbidden(path: str) -> bool:
    clean = normalized(path)
    if is_placeholder_exception(clean):
        return False
    if is_curated_summary(clean):
        return False
    parsed = PurePosixPath(clean)
    if parsed.suffix.lower() in FORBIDDEN_SUFFIXES:
        return True
    if any(part in FORBIDDEN_PARTS for part in parsed.parts):
        return True
    return any(clean == prefix or clean.startswith(prefix + "/") for prefix in RAW_DATA_PREFIXES)


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
