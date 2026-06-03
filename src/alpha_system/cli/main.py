"""Minimal CLI shell for alpha_system."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from alpha_system.cli.backtest import register_subparser as register_backtest_subparser
from alpha_system.cli.data import register_subparser as register_data_subparser
from alpha_system.cli.factor import register_subparser as register_factor_subparser
from alpha_system.cli.grid import register_subparser as register_grid_subparser
from alpha_system.cli.management import register_subparser as register_management_subparser
from alpha_system.cli.ml import register_subparser as register_ml_subparser
from alpha_system.cli.registry import register_subparser as register_registry_subparser
from alpha_system.cli.study import register_subparser as register_study_subparser


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level parser."""
    from alpha_system.cli.report import register_subparser as register_report_subparser

    parser = argparse.ArgumentParser(
        prog="alpha",
        description=(
            "Local-first alpha_system command shell. Domain commands are "
            "reserved for later reviewed phases."
        ),
    )
    subparsers = parser.add_subparsers(dest="command")
    register_backtest_subparser(subparsers)
    register_data_subparser(subparsers)
    register_factor_subparser(subparsers)
    register_grid_subparser(subparsers)
    register_management_subparser(subparsers)
    register_ml_subparser(subparsers)
    register_report_subparser(subparsers)
    register_registry_subparser(subparsers)
    register_study_subparser(subparsers)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI shell."""
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        return 0
    return int(handler(args))
