"""Block heavy, raw, generated, cache, and model artifacts."""

from __future__ import annotations

import argparse
import fnmatch
import re
from pathlib import PurePosixPath


FORBIDDEN_SUFFIXES = {
    ".key",
    ".pem",
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
FORBIDDEN_PARTS = {"node_modules", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache", "cache", "logs"}
FORBIDDEN_PREFIXES = (".frontier/upgrade_reports", "logs", "runs")
LOCAL_ONLY_PREFIXES = {"data/raw", "raw", "data/cache", "data/canonical", "data/factors", "data/labels", "metadata", "artifacts"}
PLACEHOLDER_EXCEPTIONS = ("**/.gitkeep", "**/README.md")
PLACEHOLDER_DIRS = (
    "data/raw/**",
    "data/cache/**",
    "data/canonical/**",
    "data/factors/**",
    "data/labels/**",
    "metadata/**",
    "artifacts/**",
)
CURATED_SUFFIXES = {".md", ".json", ".csv"}
CURATED_PREFIXES = {"docs", "reviews", "handoffs", "specs", "campaigns", "evals", "decisions"}
SECRET_TOKENS = {"secret", "secrets"}
SECRET_TOOLING_TOKENS = {"canary", "forbidden", "guard", "policy", "scan", "scanner", "scanning"}
TOKEN_TOKENS = {"token", "tokens"}
CREDENTIAL_TOKENS = {"credential", "credentials"}
TOKEN_RE = re.compile(r"[a-z0-9]+")


def normalized(path: str) -> str:
    value = path.replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    return value


def is_curated_summary(path: str) -> bool:
    parsed = PurePosixPath(normalized(path))
    return parsed.suffix.lower() in CURATED_SUFFIXES and parsed.parts and parsed.parts[0] in CURATED_PREFIXES


def effective_name(name: str) -> str:
    lowered = name.lower()
    return lowered[:-3] if lowered.endswith(".j2") else lowered


def name_tokens(name: str) -> list[str]:
    return TOKEN_RE.findall(effective_name(name))


def has_private_key_tokens(tokens: list[str]) -> bool:
    return any(left == "private" and right == "key" for left, right in zip(tokens, tokens[1:]))


def has_secret_artifact_tokens(tokens: list[str]) -> bool:
    if not SECRET_TOKENS.intersection(tokens):
        return False
    return not SECRET_TOOLING_TOKENS.intersection(tokens)


def is_forbidden_part(part: str) -> bool:
    name = effective_name(part)
    if name == ".env" or name.startswith(".env."):
        return True
    if PurePosixPath(name).suffix.lower() in FORBIDDEN_SUFFIXES:
        return True

    tokens = name_tokens(part)
    return (
        bool(CREDENTIAL_TOKENS.intersection(tokens))
        or bool(TOKEN_TOKENS.intersection(tokens))
        or has_private_key_tokens(tokens)
        or has_secret_artifact_tokens(tokens)
    )


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
    if any(clean == prefix or clean.startswith(prefix + "/") for prefix in FORBIDDEN_PREFIXES):
        return True
    if is_placeholder_exception(clean):
        return False
    parsed = PurePosixPath(clean)
    if parsed.suffix.lower() in FORBIDDEN_SUFFIXES:
        return True
    if any(part in FORBIDDEN_PARTS or is_forbidden_part(part) for part in parsed.parts):
        return True
    if is_curated_summary(clean):
        return False
    return any(clean == prefix or clean.startswith(prefix + "/") for prefix in LOCAL_ONLY_PREFIXES)


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
