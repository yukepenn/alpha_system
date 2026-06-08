"""CLI for local-only scaleout materialization orchestration."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from alpha_system.features.scaleout import (
    DEFAULT_SCALEOUT_CONFIG,
)
from alpha_system.features.scaleout.driver import (
    ScaleoutError,
    ScaleoutTarget,
    load_scaleout_config,
    render_scaleout_summary_markdown,
    run_scaleout,
)

# The provider canonical layout lives in the orchestration/CLI layer (and the
# data layer), never in provider-agnostic feature code. The scaleout driver
# under features/ requires the caller to pass a resolved canonical_root.
_CANONICAL_ROOT_SUBPATH = ("databento", "canonical", "glbx_mdp3")


def _resolve_canonical_root(
    canonical_root: str | None, alpha_data_root: str | None
) -> str | None:
    """Resolve the canonical Parquet root passed to the driver.

    Uses ``--canonical-root`` when given; otherwise derives it under the resolved
    ALPHA_DATA_ROOT. Returns ``None`` when no data root is available so the driver
    fails closed with a clear message (only reached under ``--execute``).
    """

    if canonical_root is not None:
        return canonical_root
    root_value = alpha_data_root or os.environ.get("ALPHA_DATA_ROOT")
    if not root_value:
        return None
    return str(Path(root_value).expanduser().joinpath(*_CANONICAL_ROOT_SUBPATH))


def run_feature_pack(args: argparse.Namespace) -> int:
    """Run ``alpha scaleout feature-pack``."""

    try:
        if args.execute and args.dry_run:
            raise ScaleoutError("--dry-run and --execute cannot be combined")
        config = load_scaleout_config(args.config)
        summary = run_scaleout(
            config,
            alpha_data_root=args.alpha_data_root,
            dataset_registry_path=args.dataset_registry,
            canonical_root=_resolve_canonical_root(
                args.canonical_root, args.alpha_data_root
            ),
            rollout=args.rollout,
            execute=args.execute,
            bounded_year=args.bounded_year,
            target=_target_from_args(args),
        )
        if args.summary_out:
            path = Path(args.summary_out)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(render_scaleout_summary_markdown(summary), encoding="utf-8")
        if args.json:
            print(json.dumps(summary.to_dict(), sort_keys=True, indent=2))
        else:
            _emit_text(summary.to_dict())
        return 0 if summary.failed_count == 0 else 2
    except (OSError, ScaleoutError, ValueError) as exc:
        print(f"scaleout command error: {exc}", file=sys.stderr)
        return 2


def register_subparser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the ``alpha scaleout`` command group."""

    scaleout_parser = subparsers.add_parser(
        "scaleout",
        help="Plan or execute governed local-only materialization scaleout.",
    )
    scaleout_subparsers = scaleout_parser.add_subparsers(dest="scaleout_command")

    feature_parser = scaleout_subparsers.add_parser(
        "feature-pack",
        help="Plan or execute governed FeaturePack scaleout.",
    )
    feature_parser.add_argument(
        "--config",
        default=DEFAULT_SCALEOUT_CONFIG,
        help="Feature scaleout config path.",
    )
    feature_parser.add_argument(
        "--execute",
        action="store_true",
        help="Write Parquet values, ledger entries, and registry metadata.",
    )
    feature_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan selected units and emit a value-free row/unit/time estimate.",
    )
    feature_parser.add_argument(
        "--family",
        help="Target one family; nonmatching configs select no units.",
    )
    feature_parser.add_argument(
        "--feature-id",
        action="append",
        help="Target a governed feature id/name; repeat or comma-separate.",
    )
    feature_parser.add_argument(
        "--feature-group",
        action="append",
        help="Target a configured feature group; repeat or comma-separate.",
    )
    feature_parser.add_argument(
        "--label-id",
        action="append",
        help="Target a governed label id/name when a label scaleout surface exists.",
    )
    feature_parser.add_argument(
        "--label-group",
        action="append",
        help="Target a configured label group when a label scaleout surface exists.",
    )
    feature_parser.add_argument(
        "--symbols",
        action="append",
        help="Target symbols; repeat or comma-separate (for example ES,NQ).",
    )
    feature_parser.add_argument(
        "--years",
        action="append",
        help="Target accepted years; repeat or comma-separate.",
    )
    feature_parser.add_argument(
        "--dataset-version-ids",
        action="append",
        help="Target accepted DatasetVersion ids; repeat or comma-separate.",
    )
    feature_parser.add_argument(
        "--rollout",
        choices=("bounded-real", "full-window", "bounded-then-full"),
        default="bounded-then-full",
        help="Rollout mode; default validates bounded-real before full expansion.",
    )
    feature_parser.add_argument(
        "--bounded-year",
        type=int,
        default=None,
        help="Accepted full year used for bounded-real rollout.",
    )
    feature_parser.add_argument(
        "--alpha-data-root",
        help="Local data root for values, registry, ledger, and checkpoints.",
    )
    feature_parser.add_argument(
        "--dataset-registry",
        help="Local DatasetVersion registry path; required with --execute.",
    )
    feature_parser.add_argument(
        "--canonical-root",
        help="Canonical Parquet root; defaults below ALPHA_DATA_ROOT.",
    )
    feature_parser.add_argument(
        "--summary-out",
        help="Optional value-free Markdown summary output path.",
    )
    feature_parser.add_argument("--json", action="store_true", help="Emit JSON.")
    feature_parser.set_defaults(handler=run_feature_pack)


def _target_from_args(args: argparse.Namespace) -> ScaleoutTarget:
    return ScaleoutTarget(
        family=args.family,
        feature_ids=_split_text_targets(args.feature_id),
        feature_groups=_split_text_targets(args.feature_group),
        label_ids=_split_text_targets(args.label_id),
        label_groups=_split_text_targets(args.label_group),
        symbols=_split_text_targets(args.symbols, uppercase=True),
        years=_split_year_targets(args.years),
        dataset_version_ids=_split_text_targets(args.dataset_version_ids),
    )


def _split_text_targets(values: list[str] | None, *, uppercase: bool = False) -> tuple[str, ...]:
    if not values:
        return ()
    targets: list[str] = []
    for value in values:
        for part in value.split(","):
            text = part.strip()
            if not text:
                continue
            targets.append(text.upper() if uppercase else text)
    return tuple(dict.fromkeys(targets))


def _split_year_targets(values: list[str] | None) -> tuple[int, ...]:
    years: list[int] = []
    for text in _split_text_targets(values):
        try:
            years.append(int(text))
        except ValueError as exc:
            raise ScaleoutError(f"--years target must be an integer: {text}") from exc
    return tuple(dict.fromkeys(years))


def _emit_text(payload: dict[str, object]) -> None:
    print("Scaleout feature-pack")
    print(f"Campaign: {payload['campaign_id']}")
    print(f"Phase: {payload['phase_id']}")
    print(f"Family: {payload['family']}")
    target = payload.get("target")
    if isinstance(target, dict) and target.get("active"):
        print(f"Target: {json.dumps(target, sort_keys=True)}")
    print(f"Rollout: {payload['rollout']}")
    print(f"Dry run: {'yes' if payload['dry_run'] else 'no'}")
    print(f"Accepted units: {payload['accepted_unit_count']}")
    print(f"Bounded units: {payload['bounded_unit_count']}")
    print(f"Planned: {payload['planned_count']}")
    print(f"Completed: {payload['completed_count']}")
    print(f"Skipped: {payload['skipped_count']}")
    print(f"Failed: {payload['failed_count']}")
    estimate = payload.get("dry_run_estimate")
    if isinstance(estimate, dict):
        print(f"Estimated rows/unit: {estimate['estimated_rows_per_unit']}")
        print(f"Estimated total rows: {estimate['estimated_total_rows']}")
        print(f"Estimated seconds/unit: {estimate['estimated_seconds_per_unit']}")
        print(f"Estimated total seconds: {estimate['estimated_total_seconds']}")


__all__ = ["register_subparser", "run_feature_pack"]
