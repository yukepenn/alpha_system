"""Minimal CLI shell for alpha_system."""

from __future__ import annotations

import argparse
from collections.abc import Sequence


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level parser without adding domain subcommands."""
    return argparse.ArgumentParser(
        prog="alpha",
        description=(
            "Local-first alpha_system command shell. Domain commands are "
            "reserved for later reviewed phases."
        ),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI shell."""
    parser = build_parser()
    parser.parse_args(argv)
    return 0
