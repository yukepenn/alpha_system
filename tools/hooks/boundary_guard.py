"""Repository boundary guard scaffold."""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def inside_root(path: str) -> bool:
    try:
        resolved = (ROOT / path).resolve()
    except OSError:
        return False
    return resolved == ROOT or ROOT in resolved.parents


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check paths stay inside the repository.")
    parser.add_argument("--claude-pre-tool-use", action="store_true")
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args(argv)
    violations = [path for path in args.paths if not inside_root(path)]
    for violation in violations:
        print(f"Path escapes repository boundary: {violation}")
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
