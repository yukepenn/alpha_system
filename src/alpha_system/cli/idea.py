"""Idea-to-verdict front-door CLI commands."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from alpha_system.agent_factory.memory.store import (
    pending_signals,
    persist_reviewer_adjudication,
    persist_route,
    read_ledger,
)
from alpha_system.governance.idea_draft import build_idea_validation_bundle
from alpha_system.governance.mechanism_card import EXPLORATORY_STAMP
from alpha_system.governance.requeue import utc_now_seconds as _utc_now_seconds
from alpha_system.governance.reviewer_verdict import create_reviewer_verdict
from alpha_system.governance.validation import GovernanceValidationError, require_mapping
from alpha_system.research_lane.fast_probe import FastProbeError, fast_probe
from alpha_system.research_lane.memory_router import route_verdict_to_memory
from alpha_system.research_lane.reviewer import adjudicate_signal
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
        created_at = _created_at_from_bundle(bundle)
        memory = route_verdict_to_memory(
            verdict,
            bundle.idea_draft,
            fast_readout,
            reviewer_verdict_id=args.reviewer_verdict_id,
            evidence_bundle_id=args.evidence_bundle_id,
            trial_ledger_refs=tuple(args.trial_ledger_ref or ()),
            created_at=created_at,
            report_ref=report_path.as_posix() if report_path is not None else None,
            probe_spent=probe_spent,
        )
        memory_path = None
        if not args.no_persist:
            memory_path = persist_route(
                route_result=memory.to_dict(),
                idea=bundle.idea_draft.to_dict(),
                readout=fast_readout,
                verdict=verdict,
                created_at=created_at or _utc_now_seconds(),
                memory_dir=args.memory_dir,
            )
        output = {
            "idea_draft": bundle.idea_draft.to_dict(),
            "testability": testability_result.to_dict(),
            "fast_readout": fast_readout,
            "report": report,
            "report_path": report_path.as_posix() if report_path is not None else None,
            "memory": memory.to_dict(),
            "memory_persisted_path": None if memory_path is None else memory_path.as_posix(),
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


def run_idea_review_list(args: argparse.Namespace) -> int:
    """List signal-shelf rows awaiting independent reviewer adjudication."""

    pending = pending_signals(memory_dir=args.memory_dir)
    summary = [
        {
            "signal_ref": (row.get("memory_record") or {}).get("original_verdict_ref"),
            "factor_id": row.get("factor_id"),
            "label_version_id": row.get("label_version_id"),
            "slice_id": row.get("slice_id"),
            "pearson_ic": row.get("pearson_ic"),
            "rank_ic": row.get("rank_ic"),
            "n_eff": row.get("n_eff"),
            "detectable_abs_ic": row.get("detectable_abs_ic"),
        }
        for row in pending
    ]
    print(json.dumps({"pending_signals": summary}, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


def run_idea_review_adjudicate(args: argparse.Namespace) -> int:
    """Record an independent reviewer adjudication of one shelved signal."""

    try:
        shelf = read_ledger("reviewer_pending_shelf", memory_dir=args.memory_dir)
        signal_row = next(
            (
                row
                for row in shelf
                if (row.get("memory_record") or {}).get("original_verdict_ref")
                == args.signal_ref
            ),
            None,
        )
        if signal_row is None:
            print(
                json.dumps(
                    {"error": "signal_ref_not_found", "signal_ref": args.signal_ref},
                    sort_keys=True,
                ),
                file=sys.stderr,
            )
            return 2
        created_at = args.created_at or _utc_now_seconds()
        reviewer_verdict = create_reviewer_verdict(
            reviewer_id=args.reviewer_id,
            role=args.role,
            independence_statement=args.independence_statement,
            verdict=args.outcome,
            blocking_issues=list(args.blocking_issue or []),
            warnings=list(args.warning or []),
            checked_artifacts=[args.signal_ref],
            checked_commands=list(args.checked_command)
            or ["alpha idea review list: inspected shelved signal IC diagnostics"],
            timestamp=created_at,
            reason_code=args.reason_code,
        )
        adjudication = adjudicate_signal(
            signal_row,
            reviewer_verdict=reviewer_verdict,
            created_at=created_at,
        )
        path = None
        if not args.no_persist:
            path = persist_reviewer_adjudication(adjudication, memory_dir=args.memory_dir)
        adjudication_path = None if path is None else path.as_posix()
        print(
            json.dumps(
                {"adjudication": adjudication, "adjudication_path": adjudication_path},
                ensure_ascii=True,
                indent=2,
                sort_keys=True,
            )
        )
    except GovernanceValidationError as exc:
        print(
            json.dumps(
                {
                    "error": "idea_review_failed",
                    "issues": [issue.to_dict() for issue in exc.issues],
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2
    except (OSError, ValueError) as exc:
        print(
            json.dumps({"error": "idea_review_failed", "message": str(exc)}, sort_keys=True),
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
    run_parser.add_argument(
        "--memory-dir",
        help=(
            "Local research-memory directory to append the route to "
            "(default: $ALPHA_DATA_ROOT/research_memory)."
        ),
    )
    run_parser.add_argument(
        "--no-persist",
        action="store_true",
        help="Do not persist the route to the local research memory.",
    )
    run_parser.set_defaults(handler=run_idea_run)

    review_parser = idea_subparsers.add_parser(
        "review",
        help="Independent reviewer adjudication of shelved research signals.",
    )
    review_subparsers = review_parser.add_subparsers(dest="review_command", required=True)

    review_list = review_subparsers.add_parser(
        "list",
        help="List signal-shelf rows awaiting independent reviewer adjudication.",
    )
    review_list.add_argument(
        "--memory-dir",
        help="Local research-memory directory (default: $ALPHA_DATA_ROOT/research_memory).",
    )
    review_list.set_defaults(handler=run_idea_review_list)

    review_adj = review_subparsers.add_parser(
        "adjudicate",
        help="Record an independent reviewer verdict over one shelved signal.",
    )
    review_adj.add_argument("signal_ref", help="original_verdict_ref of the shelved signal.")
    review_adj.add_argument(
        "--outcome",
        required=True,
        choices=["PASS", "PASS_WITH_WARNINGS", "REWORK", "BLOCKED", "INCONCLUSIVE"],
        help="ReviewerVerdict outcome.",
    )
    review_adj.add_argument("--reviewer-id", required=True, help="Independent reviewer id.")
    review_adj.add_argument(
        "--role",
        default="statistical_reviewer",
        help="Reviewer role (default: statistical_reviewer).",
    )
    review_adj.add_argument(
        "--independence-statement",
        required=True,
        help="Explicit statement of reviewer independence from the signal's producer.",
    )
    review_adj.add_argument(
        "--blocking-issue",
        action="append",
        default=[],
        help="A blocking issue (repeatable).",
    )
    review_adj.add_argument(
        "--warning",
        action="append",
        default=[],
        help="A non-blocking warning (repeatable).",
    )
    review_adj.add_argument(
        "--checked-command",
        action="append",
        default=[],
        help="A command the reviewer ran (repeatable).",
    )
    review_adj.add_argument("--reason-code", help="Optional VerdictReasonCode.")
    review_adj.add_argument("--created-at", help="Optional UTC seconds timestamp.")
    review_adj.add_argument(
        "--memory-dir",
        help="Local research-memory directory (default: $ALPHA_DATA_ROOT/research_memory).",
    )
    review_adj.add_argument(
        "--no-persist",
        action="store_true",
        help="Do not persist the adjudication to the local research memory.",
    )
    review_adj.set_defaults(handler=run_idea_review_adjudicate)


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
            "mde_abs_ic": None,
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
