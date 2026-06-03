"""Report CLI command group for local evidence artifacts."""

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
from alpha_system.reports.review_bundle import build_review_bundle, write_review_bundle
from alpha_system.reports.study_report import (
    build_study_report,
    render_study_report_csv,
    render_study_report_markdown,
    write_study_report,
)


def build_report_cli(args: argparse.Namespace) -> int:
    """Run ``alpha report build`` for local report output."""
    try:
        if args.kind == "review-bundle":
            if not args.run_id:
                raise ReportModelError("review-bundle generation requires --run-id")
            if not args.artifact_manifest:
                raise ReportModelError("review-bundle generation requires --artifact-manifest")
            report_config = _read_report_config(args.config)
            bundle = build_review_bundle(
                run_id=args.run_id,
                artifact_manifest=args.artifact_manifest,
                run_manifest=args.run_manifest,
                report_config=report_config,
                registry_path=args.registry_path,
                source_root=args.source_root,
            )
            result = write_review_bundle(
                bundle,
                args.output_dir,
                include_html=args.include_html,
            )
            print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
            return 0

        summaries = [_read_json(path) for path in args.diagnostic_summary or ()]
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
        help="Build local report and review-bundle evidence artifacts.",
    )
    report_subparsers = report_parser.add_subparsers(dest="report_command")

    build_parser = report_subparsers.add_parser(
        "build",
        help="Build a local review bundle, factor card, or study report.",
    )
    _add_build_arguments(build_parser)
    build_parser.set_defaults(handler=build_report_cli)


def _add_build_arguments(build_parser: argparse.ArgumentParser) -> None:
    build_parser.add_argument(
        "--kind",
        choices=("review-bundle", "factor-card", "study-report"),
        default="review-bundle",
        help="Report type to build.",
    )
    build_parser.add_argument(
        "--run-id",
        help="Run id for a review bundle.",
    )
    build_parser.add_argument(
        "--registry-path",
        help="Optional read-only SQLite registry path for review-bundle records.",
    )
    build_parser.add_argument(
        "--artifact-manifest",
        help="JSON artifact manifest path for a review bundle.",
    )
    build_parser.add_argument(
        "--run-manifest",
        help="Optional JSON run manifest path for a review bundle.",
    )
    build_parser.add_argument(
        "--config",
        default="configs/reports/review_bundle.yaml",
        help="Report config path for review-bundle source-map defaults.",
    )
    build_parser.add_argument(
        "--output-dir",
        help="Optional local-only review-bundle output directory.",
    )
    build_parser.add_argument(
        "--source-root",
        help="Optional source root used for source-map discovery.",
    )
    build_parser.add_argument(
        "--include-html",
        action="store_true",
        help="Also write a tiny static HTML bundle index.",
    )
    build_parser.add_argument(
        "--diagnostic-summary",
        action="append",
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


def build_parser() -> argparse.ArgumentParser:
    """Build a standalone parser for ``python -m alpha_system.cli.report``."""
    parser = argparse.ArgumentParser(prog="alpha report")
    subparsers = parser.add_subparsers(dest="report_command")
    build_parser = subparsers.add_parser(
        "build",
        help="Build a local review bundle, factor card, or study report.",
    )
    _add_build_arguments(build_parser)
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


def _read_report_config(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    config_path = Path(path)
    if not config_path.exists():
        return {}
    if config_path.suffix.lower() == ".json":
        payload = _read_json(config_path)
        return dict(payload) if isinstance(payload, dict) else {}
    return _parse_simple_yaml(config_path.read_text(encoding="utf-8"))


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    active_list: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        stripped = line.strip()
        if stripped.startswith("- ") and active_list is not None:
            payload.setdefault(active_list, []).append(_parse_yaml_scalar(stripped[2:].strip()))
            continue
        active_list = None
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not value:
            payload[key] = []
            active_list = key
        else:
            payload[key] = _parse_yaml_scalar(value)
    return payload


def _parse_yaml_scalar(value: str) -> Any:
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_yaml_scalar(item.strip()) for item in inner.split(",")]
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


if __name__ == "__main__":
    raise SystemExit(main())
