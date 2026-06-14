"""Idea-to-verdict front-door CLI commands."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from alpha_system.governance.idea_draft import build_idea_validation_bundle
from alpha_system.governance.mechanism_card import EXPLORATORY_STAMP
from alpha_system.governance.validation import GovernanceValidationError, require_mapping
from alpha_system.research_lane.fast_probe import FastProbeError, fast_probe
from alpha_system.research_lane.memory_router import route_verdict_to_memory
from alpha_system.research_lane.slice_spec import SliceSpec, SliceSpecError
from alpha_system.research_lane.testability_gate import (
    GateStatus,
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


def run_idea_run(args: argparse.Namespace) -> int:
    """Run the end-to-end idea validate -> gate -> probe -> report -> memory loop."""

    try:
        idea_path = Path(args.idea_yaml)
        payload = load_idea_document(idea_path)
        bundle = build_idea_validation_bundle(payload, source=idea_path.as_posix())
        testability_result = evaluate_testability_gate(
            bundle.idea_draft,
            alpha_spec=bundle.alpha_spec,
            mechanism_card=bundle.mechanism_card,
            setup_spec=bundle.setup_spec,
            slice_spec=slice_spec_from_idea_payload(payload, slice_id=args.slice),
            resolver=FeatureLabelPackResolver(),
        )
        if testability_result.overall_status == GateStatus.PASS:
            fast_readout = fast_probe(
                bundle.mechanism_card,
                bundle.setup_spec,
                SliceSpec.from_idea_payload(payload, slice_id=args.slice),
                resolver=FeatureLabelPackResolver(),
            )
            probe_spent = str(fast_readout.get("status") or "").upper() == "RECORDED"
        else:
            fast_readout = _pre_probe_exploratory_readout(
                bundle,
                testability_result.to_dict(),
            )
            probe_spent = False

        report = render_verdict_report(
            bundle.idea_draft,
            testability_result,
            fast_readout,
        )
        report_path = None
        if args.report_output:
            report_path = Path(args.report_output)
            report_path.write_text(report, encoding="utf-8")
        verdict = _final_verdict_from_report(report)
        memory = route_verdict_to_memory(
            verdict,
            bundle.idea_draft,
            fast_readout,
            reviewer_verdict_id=args.reviewer_verdict_id,
            evidence_bundle_id=args.evidence_bundle_id,
            trial_ledger_refs=tuple(args.trial_ledger_ref or ()),
            created_at=_created_at_from_bundle(bundle),
            report_ref=report_path.as_posix() if report_path is not None else None,
            probe_spent=probe_spent,
        )
        output = {
            "idea_draft": bundle.idea_draft.to_dict(),
            "testability": testability_result.to_dict(),
            "fast_readout": fast_readout,
            "report": report,
            "report_path": report_path.as_posix() if report_path is not None else None,
            "memory": memory.to_dict(),
            "promotion_eligible": False,
        }
        print(json.dumps(output, ensure_ascii=True, indent=2, sort_keys=True))
    except GovernanceValidationError as exc:
        print(
            json.dumps(
                {
                    "error": "idea_run_failed",
                    "issues": [issue.to_dict() for issue in exc.issues],
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2
    except (OSError, ValueError, TestabilityGateError, FastProbeError, SliceSpecError) as exc:
        print(
            json.dumps(
                {
                    "error": "idea_run_failed",
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

    run_parser = idea_subparsers.add_parser(
        "run",
        help="Run validate, testability, fast-probe, report, and memory routing.",
    )
    run_parser.add_argument(
        "idea_yaml",
        help="Path to the idea YAML or JSON-subset YAML document.",
    )
    run_parser.add_argument(
        "--slice",
        help="Optional embedded slice id to select for the gate and fast probe.",
    )
    run_parser.add_argument(
        "--report-output",
        help="Optional path to write the generated REPORT.md.",
    )
    run_parser.add_argument(
        "--reviewer-verdict-id",
        help="ReviewerVerdict id required for WATCH/CANDIDATE memory routing.",
    )
    run_parser.add_argument(
        "--evidence-bundle-id",
        help="EvidenceBundle id required for WATCH/CANDIDATE memory routing.",
    )
    run_parser.add_argument(
        "--trial-ledger-ref",
        action="append",
        default=[],
        help="TrialLedgerRecord id required for WATCH/CANDIDATE memory routing.",
    )
    run_parser.set_defaults(handler=run_idea_run)


def _load_yaml_if_available(text: str, *, path: Path) -> Any:
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ValueError(
            f"{path} is not JSON-subset YAML and PyYAML is not available"
        ) from exc
    return yaml.safe_load(text)


def _pre_probe_exploratory_readout(bundle: Any, gate: Mapping[str, Any]) -> dict[str, Any]:
    status = str(gate.get("overall_status") or gate.get("verdict") or "DATA_GAP").upper()
    blocked = status == "FAIL"
    return {
        "schema": "alpha_system.research_lane.fast_probe.v1",
        "status": "INCONCLUSIVE",
        "issue_code": "PRE_TEST_FAIL" if blocked else "DATA_GAP",
        "study_kind": bundle.idea_draft.study_kind,
        "stamp": EXPLORATORY_STAMP,
        "promotion_eligible": False,
        "mechanism_card": bundle.mechanism_card.to_dict(),
        "setup_spec": bundle.setup_spec.to_dict() if bundle.setup_spec is not None else None,
        "slice_spec": {
            "slice_id": gate.get("slice_id"),
            "study_kind": bundle.idea_draft.study_kind,
        },
        "row_access": {
            "status": "blocked" if blocked else "unresolved",
            "reason": "pre-test gate failed" if blocked else "pre-test gate returned DATA_GAP",
            "fabricated_values": False,
        },
        "surrogate_fdr_gate": {
            "threshold_verdict": "CALIBRATION_BLOCKED",
            "gate_status": "BLOCKED",
        },
        "power": {
            "n_eff": 0,
            "minimum_detectable_abs_ic": None,
        },
        "readout": {},
        "readout_id": f"preprobe_{bundle.idea_draft.alpha_spec_id}_{status.lower()}",
    }


def _final_verdict_from_report(report: str) -> dict[str, str]:
    in_final_section = False
    payload: dict[str, str] = {}
    for raw_line in report.splitlines():
        line = raw_line.strip()
        if line == "## Final Verdict":
            in_final_section = True
            continue
        if in_final_section and line.startswith("## "):
            break
        if in_final_section and line.startswith("- ") and ": " in line:
            key, value = line[2:].split(": ", 1)
            payload[key.strip()] = value.strip()
    if "verdict" not in payload:
        raise ValueError("REPORT.md final verdict section did not include a verdict")
    return payload


def _created_at_from_bundle(bundle: Any) -> str | None:
    alpha_spec = bundle.alpha_spec.to_dict()
    created_at = alpha_spec.get("created_at")
    return str(created_at) if created_at else None


__all__ = [
    "load_idea_document",
    "register_subparser",
    "run_idea_report",
    "run_idea_run",
    "run_idea_testability",
    "run_idea_validate",
]
