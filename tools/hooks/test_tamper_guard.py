"""Test tamper guard scaffold."""

from __future__ import annotations

import argparse
from pathlib import Path


FORBIDDEN_SNIPPETS = ["pytest.skip(", "@pytest.mark.skip", ".only("]
SELF_PATH = "tools/hooks/test_tamper_guard.py"


def should_check(path: Path) -> bool:
    normalized = path.as_posix()
    return normalized != SELF_PATH and ("test" in path.parts or path.name.startswith("test_"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Detect obvious test weakening.")
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args(argv)
    violations: list[str] = []
    for raw_path in args.paths:
        path = Path(raw_path)
        if not should_check(path):
            continue
        if path.exists() and path.is_file():
            text = path.read_text(encoding="utf-8", errors="ignore")
            if any(snippet in text for snippet in FORBIDDEN_SNIPPETS):
                violations.append(raw_path)
    for violation in violations:
        print(f"Possible test tamper pattern: {violation}")
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
