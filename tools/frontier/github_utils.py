"""GitHub helper scaffold.

This module intentionally avoids live GitHub API calls until project-specific
credentials, permissions, and merge policy are implemented.
"""

from __future__ import annotations

import argparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GitHub integration scaffold.")
    parser.add_argument("--preview-pr", action="store_true")
    parser.parse_args(argv)
    print("GitHub integration scaffold: no API call was made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
