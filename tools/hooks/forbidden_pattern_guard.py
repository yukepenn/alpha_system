"""Detect forbidden operational patterns in executable/config files.

Also enforces the single-PnL-truth invariant (AGENTS.md Hard Constraints):
value/accounting math lives only in the sanctioned reference engine, so a
function *definition* whose name claims pnl/equity-curve semantics anywhere
else under ``src/**`` (including the value-only ``features/fast`` /
``labels/fast`` producers) is a second value truth and is blocked. The check
is definition-scoped on purpose: PnL/equity values are legitimately *consumed*
across many modules (see ADR-0008), so a consumption grep would false-positive
en masse.
"""

from __future__ import annotations

import argparse
import re
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

# Single-PnL-truth invariant: only the reference engine may *define*
# pnl/equity-curve computations. Names like `equity_index` or
# `accounting_weight` deliberately do not match (verified legitimate
# definitions in data/foundation and governance).
SECOND_TRUTH_DEF_RE = re.compile(
    r"^\s*(?:async\s+)?def\s+\w*(?:pnl|equity_curve)\w*\s*\(", re.IGNORECASE | re.MULTILINE
)
SECOND_TRUTH_SCOPE_PREFIX = "src/"
SANCTIONED_VALUE_TRUTH_PREFIXES = ("src/alpha_system/backtest/",)


def is_second_truth_scope(path: str) -> bool:
    normalized = normalized_path(path)
    if not normalized.startswith(SECOND_TRUTH_SCOPE_PREFIX) or not normalized.endswith(".py"):
        return False
    return not any(normalized.startswith(prefix) for prefix in SANCTIONED_VALUE_TRUTH_PREFIXES)


def second_truth_violation(path: str, text: str) -> bool:
    return is_second_truth_scope(path) and bool(SECOND_TRUTH_DEF_RE.search(text))


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
                violations.append(f"Forbidden pattern found: {raw_path}")
            if second_truth_violation(raw_path, text):
                violations.append(
                    f"Second PnL/value truth: {raw_path} defines a pnl/equity_curve function "
                    "outside the sanctioned reference engine (src/alpha_system/backtest/**). "
                    "Value/accounting math has a single truth (AGENTS.md Hard Constraints)."
                )
    for violation in violations:
        print(violation)
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
