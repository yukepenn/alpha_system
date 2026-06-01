"""Detect forbidden operational patterns in executable/config files."""

from __future__ import annotations

import argparse
from pathlib import Path, PurePosixPath


FORBIDDEN_SNIPPETS = [
    "git add" + " .",
    "git add" + " -A",
    "git reset" + " --hard",
    "git push" + " --force",
    "git push" + " -f",
    "rm -rf",
    "rm -fr",
    "PLACE_LIVE_ORDER",
    "place_live_order",
    "paper_trade",
    "live_trade",
    "broker_call",
]
CHECK_SUFFIXES = {".py", ".sh", ".bash", ".zsh", ".toml", ".yml", ".yaml", ".js", ".ts"}
CHECK_NAMES = {"justfile", "Justfile"}
POLICY_ROOT_FILES = {"AGENTS.md", "CLAUDE.md", "frontier.yaml"}
POLICY_PREFIXES = (
    "docs/",
    ".claude/",
    ".codex/",
    "campaigns/",
    "specs/",
    "handoffs/",
    "reviews/",
    "decisions/",
    "evals/",
)
SELF_ALLOW_PREFIXES = ("tools/hooks/",)


def normalized_path(path: str) -> str:
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def is_policy_path(path: str) -> bool:
    normalized = normalized_path(path)
    return normalized in POLICY_ROOT_FILES or any(normalized.startswith(prefix) for prefix in POLICY_PREFIXES)


def is_self_guard_path(path: str) -> bool:
    normalized = normalized_path(path)
    return any(normalized.startswith(prefix) for prefix in SELF_ALLOW_PREFIXES)


def should_check(path: str) -> bool:
    if is_policy_path(path) or is_self_guard_path(path):
        return False
    normalized = normalized_path(path)
    parsed = PurePosixPath(normalized)
    return parsed.name in CHECK_NAMES or normalized.startswith(".githooks/") or parsed.suffix in CHECK_SUFFIXES


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Detect forbidden operational patterns.")
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args(argv)
    violations: list[str] = []
    for raw_path in args.paths:
        if not should_check(raw_path):
            continue
        path = Path(raw_path)
        if path.exists() and path.is_file():
            text = path.read_text(encoding="utf-8", errors="ignore")
            if any(snippet in text for snippet in FORBIDDEN_SNIPPETS):
                violations.append(raw_path)
    for violation in violations:
        print(f"Forbidden pattern found: {violation}")
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
