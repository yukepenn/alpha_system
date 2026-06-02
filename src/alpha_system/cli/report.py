"""Report CLI command group for factor cards and study reports."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from alpha_system.reports.factor_card import (
    build_factor_card,
    render_factor_card_csv,
    render_factor_card_markdown,
    write_factor_card,
)
from alpha_system.reports.prohibited_claims import ProhibitedClaimError
from alpha_system.reports.report_models import ReportModelError
from alpha_system.reports.study_report import (
    build_study_report,
    render_study_report_csv,
    render_study_report_markdown,
    write_study_report,
)


def build_report_cli(args: argparse.Namespace) -> int:
    """Run ``alpha report build`` for factor-card or study-report output."""
    try:
        summaries = [_read_json(path) for path in args.diagnostic_summary]
        metadata = _read_json(args.metadata_json) if args.metadata_json else {}
        if not isinstance(metadata, dict):
            msg = "metadata JSON root must be an object"
            raise ReportModelError(msg)

        if args.kind == "factor-card":
            if len(summaries) != 1:
                msg = "factor-card generation requires exactly one --diagnostic-summary"
                raise ReportModelError(msg)
            card = build_factor_card(
                summaries[0],
                reproducibility_metadata=metadata,
                promotion_recommendation=args.recommendation,
                factor_cluster_id=args.factor_cluster_id,
                min_sample_size=args.min_sample_size,
            )
            if args.output:
                write_factor_card(card, args.output, output_format=args.format)
            else:
                print(
                    render_factor_card_markdown(card)
                    if args.format == "markdown"
                    else render_factor_card_csv(card),
                    end="",
                )
            return 0

        report = build_study_report(
            summaries,
            study_id=args.study_id,
            reproducibility_metadata=metadata,
            min_sample_size=args.min_sample_size,
        )
        if args.output:
            write_study_report(report, args.output, output_format=args.format)
        else:
            print(
                render_study_report_markdown(report)
                if args.format == "markdown"
                else render_study_report_csv(report),
                end="",
            )
        return 0
    except (
        OSError,
        json.JSONDecodeError,
        ProhibitedClaimError,
        ReportModelError,
        ValueError,
    ) as exc:
        print(f"report command error: {exc}", file=sys.stderr)
        return 2


def register_subparser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the ``alpha report`` command group."""
    report_parser = subparsers.add_parser(
        "report",
        help="Build local factor-card or study-report evidence artifacts.",
    )
    report_subparsers = report_parser.add_subparsers(dest="report_command")

    build_parser = report_subparsers.add_parser(
        "build",
        help="Render a factor card or study report from diagnostic summaries.",
    )
    build_parser.add_argument(
        "--kind",
        choices=("factor-card", "study-report"),
        default="factor-card",
        help="Report type to render.",
    )
    build_parser.add_argument(
        "--diagnostic-summary",
        action="append",
        required=True,
        help="Path to a diagnostic_summary.json file; repeat for study reports.",
    )
    build_parser.add_argument(
        "--metadata-json",
        help="Optional JSON object with manifest path, hashes, no-lookahead status, and review status.",
    )
    build_parser.add_argument(
        "--output",
        help="Optional local-only output path. If omitted, report text is printed to stdout.",
    )
    build_parser.add_argument(
        "--format",
        choices=("markdown", "csv"),
        default="markdown",
        help="Output format.",
    )
    build_parser.add_argument(
        "--recommendation",
        help="Optional closed-set advisory recommendation for a single factor card.",
    )
    build_parser.add_argument(
        "--factor-cluster-id",
        help="Optional factor cluster identifier for a single factor card.",
    )
    build_parser.add_argument(
        "--study-id",
        help="Optional study id override for study reports.",
    )
    build_parser.add_argument(
        "--min-sample-size",
        type=int,
        default=30,
        help="Conservative sample-size threshold used for warnings.",
    )
    build_parser.set_defaults(handler=build_report_cli)


def build_parser() -> argparse.ArgumentParser:
    """Build a standalone parser for ``python -m alpha_system.cli.report``."""
    parser = argparse.ArgumentParser(prog="alpha report")
    subparsers = parser.add_subparsers(dest="report_command")
    build_parser = subparsers.add_parser(
        "build",
        help="Render a factor card or study report from diagnostic summaries.",
    )
    build_parser.add_argument(
        "--kind",
        choices=("factor-card", "study-report"),
        default="factor-card",
        help="Report type to render.",
    )
    build_parser.add_argument(
        "--diagnostic-summary",
        action="append",
        required=True,
        help="Path to a diagnostic_summary.json file; repeat for study reports.",
    )
    build_parser.add_argument(
        "--metadata-json",
        help="Optional JSON object with manifest path, hashes, no-lookahead status, and review status.",
    )
    build_parser.add_argument(
        "--output",
        help="Optional local-only output path. If omitted, report text is printed to stdout.",
    )
    build_parser.add_argument(
        "--format",
        choices=("markdown", "csv"),
        default="markdown",
        help="Output format.",
    )
    build_parser.add_argument(
        "--recommendation",
        help="Optional closed-set advisory recommendation for a single factor card.",
    )
    build_parser.add_argument(
        "--factor-cluster-id",
        help="Optional factor cluster identifier for a single factor card.",
    )
    build_parser.add_argument(
        "--study-id",
        help="Optional study id override for study reports.",
    )
    build_parser.add_argument(
        "--min-sample-size",
        type=int,
        default=30,
        help="Conservative sample-size threshold used for warnings.",
    )
    build_parser.set_defaults(handler=build_report_cli)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the standalone report CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        return 0
    return int(handler(args))


def _read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
