"""Idea-to-verdict front-door CLI commands."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from alpha_system.agent_factory.memory.store import (
    ensure_family_fdr_ledger_path,
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
from alpha_system.research_lane.environment_preflight import (
    EnvironmentPreflightResult,
    env_with_resolved_data_root,
    evaluate_environment_preflight,
)
from alpha_system.research_lane.fast_probe import FastProbeError, fast_probe
from alpha_system.research_lane.memory_router import route_verdict_to_memory
from alpha_system.research_lane.mining_driver import MiningDriverError, mine_ideas
from alpha_system.research_lane.pack_pin_audit import (
    audit_idea_pack_pins,
    payload_has_versioned_pack_refs,
)
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
        preflight = None
        if payload_has_versioned_pack_refs(payload):
            preflight = _environment_preflight_for_args(args)
            if not preflight.configured:
                _emit_environment_not_configured(preflight)
                return ENVIRONMENT_NOT_CONFIGURED_EXIT
        pack_pin_issues = _pack_pin_issues_for_validate(payload, preflight=preflight)
        if pack_pin_issues:
            raise GovernanceValidationError(pack_pin_issues)
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


# Exit code for an unmet ENVIRONMENT precondition. Deliberately distinct from the
# governance-validation exit (2) so a broken env is not confused with a malformed
# idea, and never with a DATA_GAP (which is a 0-exit research outcome).
ENVIRONMENT_NOT_CONFIGURED_EXIT = 3


def _emit_environment_not_configured(preflight: EnvironmentPreflightResult) -> None:
    """Print the LOUD, distinct unmet-precondition payload (NOT a DATA_GAP)."""

    print(
        json.dumps(
            {
                "error": "environment_not_configured",
                # overall_status mirrors the gate's key so downstream readers that
                # branch on overall_status see ENVIRONMENT_NOT_CONFIGURED, never DATA_GAP.
                "overall_status": preflight.status.value,
                "verdict": preflight.status.value,
                "issue_code": preflight.issue_code,
                "message": preflight.message,
                "data_root": preflight.data_root.as_posix(),
                "probe_invoked": False,
            },
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        ),
        file=sys.stderr,
    )


def _environment_preflight_for_args(args: argparse.Namespace) -> EnvironmentPreflightResult:
    """Resolve + check the data-ops environment precondition for an idea entrypoint."""

    explicit = getattr(args, "alpha_data_root", None)
    return evaluate_environment_preflight(alpha_data_root=explicit)


def _pack_pin_issues_for_validate(
    payload: Mapping[str, Any],
    *,
    preflight: EnvironmentPreflightResult | None,
):
    """Return deprecated/mismatched pack-pin issues for validate, if applicable."""

    if preflight is None:
        return ()
    return audit_idea_pack_pins(
        payload,
        resolver=FeatureLabelPackResolver(alpha_data_root=preflight.data_root),
    )


def _conditioned_power_slice_for(
    payload: Mapping[str, Any],
    bundle: Any,
    *,
    slice_id: str | None,
) -> SliceSpec | None:
    """Build the richer fast-probe slice for the gate's conditioned-power check.

    Only a context_not_equal_trigger idea (one that mints a SetupSpec) carries the
    context/trigger predicates the conditioned-power compute needs, so we only build
    the slice for that study kind. A malformed slice is left to the gate's own typed
    handling; here a SliceSpecError simply means no conditioned slice is supplied and
    the gate keeps its prior unconditioned plausibility behavior.
    """

    if bundle.setup_spec is None:
        return None
    try:
        return SliceSpec.from_idea_payload(payload, slice_id=slice_id)
    except SliceSpecError:
        return None


def run_idea_testability(args: argparse.Namespace) -> int:
    """Run ``alpha idea testability`` / ``alpha idea gate`` as a pre-test gate."""

    preflight = _environment_preflight_for_args(args)
    if not preflight.configured:
        _emit_environment_not_configured(preflight)
        return ENVIRONMENT_NOT_CONFIGURED_EXIT

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
            # The richer materialized-slice descriptor enables the honest CONDITIONED
            # (context AND trigger) power check for a context_not_equal_trigger setup.
            conditioned_power_slice=_conditioned_power_slice_for(
                payload, bundle, slice_id=args.slice
            ),
            # Pin the preflight-resolved root so the registry path resolves the
            # known-good store even if ALPHA_DATA_ROOT was unset in the process env.
            resolver=FeatureLabelPackResolver(alpha_data_root=preflight.data_root),
            env=env_with_resolved_data_root(preflight),
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

    preflight = _environment_preflight_for_args(args)
    if not preflight.configured:
        _emit_environment_not_configured(preflight)
        return ENVIRONMENT_NOT_CONFIGURED_EXIT
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
            # The richer materialized-slice descriptor enables the honest CONDITIONED
            # (context AND trigger) power check for a context_not_equal_trigger setup.
            conditioned_power_slice=_conditioned_power_slice_for(
                payload, bundle, slice_id=args.slice
            ),
            # Pin the preflight-resolved root so the registry path resolves the
            # known-good store even if ALPHA_DATA_ROOT was unset in the process env.
            resolver=FeatureLabelPackResolver(alpha_data_root=preflight.data_root),
            env=env_with_resolved_data_root(preflight),
        )
        # Defense-in-depth: even though the entrypoint preflight already gated an
        # unmet environment precondition, the gate may independently classify a
        # typed data-root precondition (reason code) as ENVIRONMENT_NOT_CONFIGURED.
        # Surface it as the distinct precondition error, never a DATA_GAP readout.
        if testability_result.overall_status == GateStatus.ENVIRONMENT_NOT_CONFIGURED:
            _emit_environment_not_configured(
                _environment_preflight_for_args(args)
            )
            return ENVIRONMENT_NOT_CONFIGURED_EXIT
        if testability_result.overall_status == GateStatus.PASS:
            fast_readout = fast_probe(
                bundle.mechanism_card,
                bundle.setup_spec,
                SliceSpec.from_idea_payload(payload, slice_id=args.slice),
                resolver=FeatureLabelPackResolver(alpha_data_root=preflight.data_root),
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
        # CROSS_IDEA_FDR_BUDGET_V1 Stage B: wire the append-only family-FDR accumulator
        # so a setup-lane SIGNAL_PENDING_REVIEWER signal is gated on the family-wise
        # multiplicity correction across its co-mined batch. Skipped for --no-persist
        # dry runs (the accumulator is a persistent side effect, like the route ledgers).
        family_fdr_ledger_path = (
            None if args.no_persist else ensure_family_fdr_ledger_path(args.memory_dir)
        )
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
            family_fdr_ledger_path=family_fdr_ledger_path,
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


def run_idea_mine(args: argparse.Namespace) -> int:
    """Run ``alpha idea mine``: the unattended multi-partition pooled mining loop.

    Takes a SET of idea files (explicit paths and/or a directory of ``*.idea.yaml``)
    plus an optional partition policy, runs each idea's multi-partition pooled run
    through the now-sound gates WITHOUT a human per idea, records each pooled verdict
    to the append-only research memory (which doubles as the idempotent resume
    record), and emits a run summary (counts per route + per status, partition
    coverage). It NEVER auto-promotes: the independent reviewer shelf + capital gate
    are unchanged.
    """

    preflight = _environment_preflight_for_args(args)
    if not preflight.configured:
        _emit_environment_not_configured(preflight)
        return ENVIRONMENT_NOT_CONFIGURED_EXIT
    try:
        idea_paths = _collect_idea_paths(args.idea_paths, directory=args.directory)
        if not idea_paths:
            print(
                json.dumps(
                    {"error": "idea_mine_failed", "message": "no idea files were found to mine"},
                    sort_keys=True,
                ),
                file=sys.stderr,
            )
            return 2
        family_fdr_ledger_path = (
            None if args.no_persist else ensure_family_fdr_ledger_path(args.memory_dir)
        )
        # Pin the preflight-resolved root into the mining env so per-partition
        # registries resolve the known-good store even with ALPHA_DATA_ROOT unset.
        mine_env = env_with_resolved_data_root(preflight)
        summary = mine_ideas(
            idea_paths,
            partition_policy=tuple(args.partition or ()) or None,
            years=tuple(args.years) if args.years else None,
            instruments=tuple(args.instruments) if args.instruments else None,
            env=mine_env,
            persist=not args.no_persist,
            memory_dir=args.memory_dir,
            family_fdr_ledger_path=family_fdr_ledger_path,
            pooled_registry_path=args.pooled_registry,
            skip_recorded=not args.no_skip_recorded,
        )
    except GovernanceValidationError as exc:
        print(
            json.dumps(
                {
                    "error": "idea_mine_failed",
                    "issues": [issue.to_dict() for issue in exc.issues],
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2
    except (OSError, ValueError, MiningDriverError) as exc:
        print(
            json.dumps({"error": "idea_mine_failed", "message": str(exc)}, sort_keys=True),
            file=sys.stderr,
        )
        return 2

    print(json.dumps(summary.to_dict(), ensure_ascii=True, indent=2, sort_keys=True))
    return 0


def _collect_idea_paths(
    explicit: list[str],
    *,
    directory: str | None,
) -> list[str]:
    """Resolve the ordered, de-duplicated idea-file set for a mining run."""

    paths: list[str] = []
    seen: set[str] = set()

    def _add(path: Path) -> None:
        key = path.as_posix()
        if key not in seen:
            seen.add(key)
            paths.append(key)

    if directory:
        base = Path(directory)
        if not base.is_dir():
            raise ValueError(f"--directory is not a directory: {directory}")
        for path in sorted(base.glob("*.idea.yaml")):
            _add(path)
        for path in sorted(base.glob("*.idea.json")):
            _add(path)
    for raw in explicit or []:
        _add(Path(raw))
    return paths


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
    validate_parser.add_argument(
        "--alpha-data-root",
        help=(
            "Explicit local data root override. Versioned feature/label pack pins "
            "are audited against this root (or the canonical default)."
        ),
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
    testability_parser.add_argument(
        "--alpha-data-root",
        help=(
            "Explicit local data root override. Default resolution: "
            "ALPHA_DATA_ROOT env, then ~/alpha_data/alpha_system."
        ),
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
    run_parser.add_argument(
        "--alpha-data-root",
        help=(
            "Explicit local data root override. Default resolution: "
            "ALPHA_DATA_ROOT env, then ~/alpha_data/alpha_system."
        ),
    )
    run_parser.set_defaults(handler=run_idea_run)

    mine_parser = idea_subparsers.add_parser(
        "mine",
        help=(
            "Unattended multi-partition pooled mining loop over a SET of ideas "
            "(BROAD_MINING_DRIVER_V0). Never auto-promotes."
        ),
    )
    mine_parser.add_argument(
        "idea_paths",
        nargs="*",
        default=[],
        help="Idea YAML/JSON paths to mine (combined with --directory).",
    )
    mine_parser.add_argument(
        "--directory",
        help="Directory of *.idea.yaml / *.idea.json files to mine (sorted).",
    )
    mine_parser.add_argument(
        "--partition",
        action="append",
        default=[],
        help=(
            "Explicit partition slice id (repeatable). Overrides each idea's "
            "declared slice set when provided."
        ),
    )
    mine_parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=None,
        help=(
            "Years to fan each idea over (e.g. --years 2019 2020 2021). Combined "
            "with the idea's own horizon and --instruments (default: the idea's "
            "declared instrument) to expand into target partitions resolved from "
            "the on-disk materialized registry. Ignored when --partition is given."
        ),
    )
    mine_parser.add_argument(
        "--instruments",
        nargs="+",
        default=None,
        help=(
            "Instruments to fan each idea over (e.g. --instruments ES NQ RTY). "
            "Combined with --years and the idea's horizon. Ignored when "
            "--partition is given."
        ),
    )
    mine_parser.add_argument(
        "--pooled-registry",
        help=(
            "Optional path to an existing writable PooledHypothesisRegistry JSONL "
            "to pre-register each pooled hypothesis into (local-only)."
        ),
    )
    mine_parser.add_argument(
        "--memory-dir",
        help=(
            "Local research-memory directory to append routes to "
            "(default: $ALPHA_DATA_ROOT/research_memory)."
        ),
    )
    mine_parser.add_argument(
        "--no-persist",
        action="store_true",
        help="Do not persist routes or the family-FDR accumulator (dry run).",
    )
    mine_parser.add_argument(
        "--no-skip-recorded",
        action="store_true",
        help=(
            "Re-mine ideas already recorded in the ledgers (default: skip them, "
            "so the loop is resumable/idempotent)."
        ),
    )
    mine_parser.add_argument(
        "--alpha-data-root",
        help=(
            "Explicit local data root override. Default resolution: "
            "ALPHA_DATA_ROOT env, then ~/alpha_data/alpha_system."
        ),
    )
    mine_parser.set_defaults(handler=run_idea_mine)

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
    "run_idea_mine",
    "run_idea_report",
    "run_idea_run",
    "run_idea_testability",
    "run_idea_validate",
]
