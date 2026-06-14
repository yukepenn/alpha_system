"""Idea-to-verdict front-door CLI commands."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from alpha_system.governance.idea_draft import build_idea_validation_bundle
from alpha_system.governance.validation import GovernanceValidationError, require_mapping
from alpha_system.research_lane.testability_gate import (
    TestabilityGateError,
    evaluate_testability_gate,
    slice_spec_from_idea_payload,
)
from alpha_system.research_lane.verdict_report import render_verdict_report
from alpha_system.runtime.input_resolver import FeatureLabelPackResolver


def run_idea_validate(args: argparse.Namespace) -> int:
    """Run ``alpha idea validate`` and emit canonical intake objects."""

    try:
        idea_path = Path(args.idea_yaml)
        payload = load_idea_document(idea_path)
        bundle = build_idea_validation_bundle(payload, source=idea_path.as_posix())
    except GovernanceValidationError as exc:
        print(
            json.dumps(
                {
                    "error": "idea_validation_failed",
                    "issues": [issue.to_dict() for issue in exc.issues],
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2
    except (OSError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "error": "idea_validation_failed",
                    "message": str(exc),
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2

    print(json.dumps(bundle.to_dict(), ensure_ascii=True, indent=2, sort_keys=True))
    return 0


def run_idea_testability(args: argparse.Namespace) -> int:
    """Run ``alpha idea testability`` / ``alpha idea gate`` as a pre-test gate."""

    try:
        idea_path = Path(args.idea_yaml)
        payload = load_idea_document(idea_path)
        bundle = build_idea_validation_bundle(payload, source=idea_path.as_posix())
        slice_spec = slice_spec_from_idea_payload(payload, slice_id=args.slice)
        result = evaluate_testability_gate(
            bundle.idea_draft,
            alpha_spec=bundle.alpha_spec,
            mechanism_card=bundle.mechanism_card,
            setup_spec=bundle.setup_spec,
            slice_spec=slice_spec,
            resolver=FeatureLabelPackResolver(),
        )
    except GovernanceValidationError as exc:
        print(
            json.dumps(
                {
                    "error": "idea_testability_failed",
                    "issues": [issue.to_dict() for issue in exc.issues],
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2
    except (OSError, ValueError, TestabilityGateError) as exc:
        print(
            json.dumps(
                {
                    "error": "idea_testability_failed",
                    "message": str(exc),
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2

    print(json.dumps(result.to_dict(), ensure_ascii=True, indent=2, sort_keys=True))
    return 0


def run_idea_report(args: argparse.Namespace) -> int:
    """Render ``alpha idea report`` from precomputed gate/readout summaries."""

    try:
        idea_path = Path(args.idea_yaml)
        payload = load_idea_document(idea_path)
        bundle = build_idea_validation_bundle(payload, source=idea_path.as_posix())
        testability_result = load_idea_document(Path(args.testability_json))
        fast_readout = load_idea_document(Path(args.fast_readout_json))
        report = render_verdict_report(
            bundle.idea_draft,
            testability_result,
            fast_readout,
        )
        if args.output:
            Path(args.output).write_text(report, encoding="utf-8")
        else:
            print(report, end="")
    except GovernanceValidationError as exc:
        print(
            json.dumps(
                {
                    "error": "idea_report_failed",
                    "issues": [issue.to_dict() for issue in exc.issues],
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2
    except (OSError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "error": "idea_report_failed",
                    "message": str(exc),
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2
    return 0


def load_idea_document(path: Path) -> Mapping[str, Any]:
    """Load an idea document from JSON or YAML without adding a hard dependency."""

    text = path.read_text(encoding="utf-8")
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        value = _load_yaml_if_available(text, path=path)
    return require_mapping(value, object_name=f"idea document {path}")


def register_subparser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the ``alpha idea`` command group."""

    idea_parser = subparsers.add_parser(
        "idea",
        help="Validate idea intake documents into canonical governance objects.",
    )
    idea_subparsers = idea_parser.add_subparsers(dest="idea_command")

    validate_parser = idea_subparsers.add_parser(
        "validate",
        help="Validate one idea document and emit canonical intake objects.",
    )
    validate_parser.add_argument(
        "idea_yaml",
        help="Path to an idea YAML or JSON-subset YAML document.",
    )
    validate_parser.set_defaults(handler=run_idea_validate)

    testability_parser = idea_subparsers.add_parser(
        "testability",
        aliases=["gate"],
        help="Run the pre-test idea testability gate.",
    )
    testability_parser.add_argument(
        "idea_yaml",
        help="Path to an idea YAML or JSON-subset YAML document.",
    )
    testability_parser.add_argument(
        "--slice",
        help="Optional embedded slice id to select for the pre-test gate.",
    )
    testability_parser.set_defaults(handler=run_idea_testability)

    report_parser = idea_subparsers.add_parser(
        "report",
        help="Render a governed REPORT.md from precomputed idea readouts.",
    )
    report_parser.add_argument(
        "idea_yaml",
        help="Path to the idea YAML or JSON-subset YAML document.",
    )
    report_parser.add_argument(
        "--testability-json",
        "--testability",
        required=True,
        help="Path to the precomputed testability gate JSON or YAML summary.",
    )
    report_parser.add_argument(
        "--fast-readout-json",
        "--fast-readout",
        required=True,
        help="Path to the precomputed fast-probe readout JSON or YAML summary.",
    )
    report_parser.add_argument(
        "-o",
        "--output",
        help="Optional path to write REPORT.md instead of stdout.",
    )
    report_parser.set_defaults(handler=run_idea_report)


def _load_yaml_if_available(text: str, *, path: Path) -> Any:
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ValueError(
            f"{path} is not JSON-subset YAML and PyYAML is not available"
        ) from exc
    return yaml.safe_load(text)


__all__ = [
    "load_idea_document",
    "register_subparser",
    "run_idea_report",
    "run_idea_testability",
    "run_idea_validate",
]
