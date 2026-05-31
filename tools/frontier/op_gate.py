"""Frontier red-lane operation authorization gate."""

from __future__ import annotations

import argparse
import os


REQUIRED_ENV = ["PROJECT_OP_AUTHORIZED", "PROJECT_OP_SCOPE", "PROJECT_OP_EXPIRES"]


def check() -> int:
    missing = [name for name in REQUIRED_ENV if not os.environ.get(name)]
    if missing:
        print("Operation gate is not armed. Missing: " + ", ".join(missing))
        return 1
    print("Operation gate environment is present. Validate scope before executing red-lane work.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check red-lane operation authorization environment.")
    parser.add_argument("--check", action="store_true")
    parser.parse_args(argv)
    return check()


if __name__ == "__main__":
    raise SystemExit(main())
