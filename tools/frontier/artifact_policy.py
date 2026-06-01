"""Frontier artifact policy checks."""

from __future__ import annotations

import argparse
import fnmatch
import re
from pathlib import Path, PurePosixPath


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
DEFAULT_PLACEHOLDER_EXCEPTIONS = ["**/.gitkeep", "**/README.md"]
DEFAULT_PLACEHOLDER_DIRS = [
    "data/raw/**",
    "data/cache/**",
    "data/canonical/**",
    "data/factors/**",
    "data/labels/**",
    "metadata/**",
    "artifacts/**",
]
FORBIDDEN_PREFIXES = (
    ".frontier/upgrade_reports",
    "logs",
    "runs",
)
SECRET_TOKENS = {"secret", "secrets"}
SECRET_TOOLING_TOKENS = {"canary", "forbidden", "guard", "policy", "scan", "scanner", "scanning"}
TOKEN_TOKENS = {"token", "tokens"}
CREDENTIAL_TOKENS = {"credential", "credentials"}
TOKEN_RE = re.compile(r"[a-z0-9]+")


def path_parts(path: Path) -> list[str]:
    return [part for part in str(path).replace("\\", "/").split("/") if part and part != "."]


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


def check_path(path: Path) -> bool:
    parts = path_parts(path)
    normalized = "/".join(parts)
    if any(normalized == prefix or normalized.startswith(prefix + "/") for prefix in FORBIDDEN_PREFIXES):
        return False
    return not any(is_forbidden_part(part) for part in parts)


def matches_any(path: str, patterns: list[str]) -> bool:
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    for pattern in patterns:
        if fnmatch.fnmatch(normalized, pattern):
            return True
        if pattern.startswith("**/") and fnmatch.fnmatch(normalized, pattern[3:]):
            return True
    return False


def is_placeholder_exception(
    path: str,
    *,
    placeholder_exceptions: list[str] | None = None,
    placeholder_dirs: list[str] | None = None,
) -> bool:
    exceptions = DEFAULT_PLACEHOLDER_EXCEPTIONS if placeholder_exceptions is None else placeholder_exceptions
    dirs = DEFAULT_PLACEHOLDER_DIRS if placeholder_dirs is None else placeholder_dirs
    return matches_any(path, exceptions) and matches_any(path, dirs)


def curate_commit_paths(
    paths: list[str],
    *,
    allow_patterns: list[str],
    forbid_patterns: list[str],
    placeholder_exceptions: list[str] | None = None,
    placeholder_dirs: list[str] | None = None,
) -> tuple[list[str], list[str]]:
    """Split changed files into explicitly stageable and blocked paths."""

    allowed: list[str] = []
    blocked: list[str] = []
    for raw_path in sorted(dict.fromkeys(paths)):
        normalized = raw_path.replace("\\", "/")
        while normalized.startswith("./"):
            normalized = normalized[2:]
        if not normalized:
            continue
        path_ok = check_path(Path(normalized))
        allowed_by_config = matches_any(normalized, allow_patterns)
        forbidden_by_config = matches_any(normalized, forbid_patterns)
        placeholder_ok = is_placeholder_exception(
            normalized,
            placeholder_exceptions=placeholder_exceptions,
            placeholder_dirs=placeholder_dirs,
        )
        if path_ok and allowed_by_config and (not forbidden_by_config or placeholder_ok):
            allowed.append(normalized)
        else:
            blocked.append(normalized)
    return allowed, blocked


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check paths against Frontier artifact policy.")
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args(argv)
    violations = [path for path in map(Path, args.paths) if not check_path(path)]
    for violation in violations:
        print(f"Forbidden artifact path: {violation}")
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
