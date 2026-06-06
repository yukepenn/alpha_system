"""Runtime CLI command group for local-only research runtime orchestration."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class RuntimeCliError(ValueError):
    """Raised when runtime CLI input cannot be dispatched safely."""


type _RuntimeHandler = Callable[[argparse.Namespace], int]


def register_subparser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the ``alpha runtime`` command group."""

    runtime_parser = subparsers.add_parser(
        "runtime",
        help="Drive local-only research runtime contracts and summaries.",
        description="Drive local-only research runtime contracts and summaries.",
    )
    runtime_subparsers = runtime_parser.add_subparsers(dest="runtime_command")

    _register_input_command(
        runtime_subparsers,
        "plan",
        help_text="Validate a bounded RuntimePlan from a local JSON envelope.",
        handler=run_plan,
    )
    _register_input_command(
        runtime_subparsers,
        "validate-inputs",
        help_text="Validate runtime entry inputs and, when requested, resolve local handles.",
        handler=run_validate_inputs,
    )

    diagnostics_parser = _register_input_command(
        runtime_subparsers,
        "run-diagnostics",
        help_text="Run local factor, split, or cross-market runtime diagnostics.",
        handler=run_diagnostics,
    )
    diagnostics_parser.add_argument(
        "--family",
        choices=("factor", "splits", "session-split", "regime-split", "cross-market"),
        default="factor",
        help="Diagnostics family to dispatch. Defaults to factor.",
    )

    _register_input_command(
        runtime_subparsers,
        "run-label-diagnostics",
        help_text="Run local label diagnostics from a resolved RuntimeInputPack envelope.",
        handler=run_label_diagnostics,
    )
    _register_input_command(
        runtime_subparsers,
        "run-signal-probe",
        help_text="Run a bounded local signal probe from a declared probe envelope.",
        handler=run_signal_probe_command,
    )
    _register_input_command(
        runtime_subparsers,
        "run-cost-stress",
        help_text="Run local descriptive cost stress from declared fills and cost config.",
        handler=run_cost_stress,
    )
    _register_input_command(
        runtime_subparsers,
        "build-evidence-draft",
        help_text="Build a local EvidenceDraft from existing runtime contract inputs.",
        handler=run_build_evidence_draft,
    )
    _register_input_command(
        runtime_subparsers,
        "build-reference-handoff",
        help_text="Build a reference-only handoff package from runtime contract inputs.",
        handler=run_build_reference_handoff,
    )
    _register_input_command(
        runtime_subparsers,
        "summarize",
        help_text="Summarize a local runtime JSON payload without executing runtime work.",
        handler=run_summarize,
    )
    _register_input_command(
        runtime_subparsers,
        "inspect",
        help_text="Inspect a local runtime contract payload and emit compact metadata.",
        handler=run_inspect,
    )
    _register_input_command(
        runtime_subparsers,
        "replay-summary",
        help_text="Replay a local StudyRun manifest/record summary without rerunning work.",
        handler=run_replay_summary,
    )


def run_plan(args: argparse.Namespace) -> int:
    """Run ``alpha runtime plan``."""

    return _run_command(args, "plan", _build_plan_payload)


def run_validate_inputs(args: argparse.Namespace) -> int:
    """Run ``alpha runtime validate-inputs``."""

    return _run_command(args, "validate-inputs", _build_validate_inputs_payload)


def run_diagnostics(args: argparse.Namespace) -> int:
    """Run ``alpha runtime run-diagnostics``."""

    return _run_command(args, "run-diagnostics", _build_diagnostics_payload)


def run_label_diagnostics(args: argparse.Namespace) -> int:
    """Run ``alpha runtime run-label-diagnostics``."""

    return _run_command(args, "run-label-diagnostics", _build_label_diagnostics_payload)


def run_signal_probe_command(args: argparse.Namespace) -> int:
    """Run ``alpha runtime run-signal-probe``."""

    return _run_command(args, "run-signal-probe", _build_signal_probe_payload)


def run_cost_stress(args: argparse.Namespace) -> int:
    """Run ``alpha runtime run-cost-stress``."""

    return _run_command(args, "run-cost-stress", _build_cost_stress_payload)


def run_build_evidence_draft(args: argparse.Namespace) -> int:
    """Run ``alpha runtime build-evidence-draft``."""

    return _run_command(args, "build-evidence-draft", _build_evidence_draft_payload)


def run_build_reference_handoff(args: argparse.Namespace) -> int:
    """Run ``alpha runtime build-reference-handoff``."""

    return _run_command(args, "build-reference-handoff", _build_reference_handoff_payload)


def run_summarize(args: argparse.Namespace) -> int:
    """Run ``alpha runtime summarize``."""

    return _run_command(args, "summarize", _build_summary_payload)


def run_inspect(args: argparse.Namespace) -> int:
    """Run ``alpha runtime inspect``."""

    return _run_command(args, "inspect", _build_inspect_payload)


def run_replay_summary(args: argparse.Namespace) -> int:
    """Run ``alpha runtime replay-summary``."""

    return _run_command(args, "replay-summary", _build_replay_summary_payload)


def _register_input_command(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    name: str,
    *,
    help_text: str,
    handler: _RuntimeHandler,
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(name, help=help_text)
    parser.add_argument(
        "--input",
        help="Path to a local JSON command envelope or runtime payload.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON console summary.",
    )
    parser.set_defaults(handler=handler)
    return parser


def _run_command(
    args: argparse.Namespace,
    command: str,
    builder: Callable[[argparse.Namespace], Mapping[str, Any]],
) -> int:
    try:
        payload = builder(args)
    except (
        RuntimeCliError,
        TypeError,
        ValueError,
        OSError,
        json.JSONDecodeError,
    ) as exc:
        print(f"runtime command error: {command}: {exc}", file=sys.stderr)
        return 2
    _emit(command, payload, emit_json=bool(args.json))
    return 0


def _build_plan_payload(args: argparse.Namespace) -> Mapping[str, Any]:
    payload = _load_mapping(args)

    from alpha_system.runtime.contracts.plan import validate_runtime_plan

    kwargs = dict(payload)
    if isinstance(kwargs.get("runtime_request"), Mapping):
        kwargs["runtime_request"] = _runtime_request_from_mapping(
            _required_mapping(kwargs["runtime_request"], "runtime_request")
        )
    result = validate_runtime_plan(**kwargs)
    return _command_payload("plan", result)


def _build_validate_inputs_payload(args: argparse.Namespace) -> Mapping[str, Any]:
    payload = _load_mapping(args)

    from alpha_system.runtime.entry_contract import (
        RuntimeEntryRequest,
        evaluate_runtime_entry_request,
    )
    from alpha_system.runtime.input_resolver import resolve_runtime_input_pack

    entry_mapping = _required_mapping(payload.get("entry_request"), "entry_request")
    entry_result = evaluate_runtime_entry_request(RuntimeEntryRequest(**entry_mapping))
    result: object = entry_result

    resolution = payload.get("resolution")
    if resolution is not None:
        resolution_kwargs = dict(_required_mapping(resolution, "resolution"))
        if "registry_path" not in resolution_kwargs:
            raise RuntimeCliError("resolution.registry_path is required")
        result = resolve_runtime_input_pack(entry_result, **resolution_kwargs)
    return _command_payload("validate-inputs", result)


def _build_diagnostics_payload(args: argparse.Namespace) -> Mapping[str, Any]:
    payload = _load_mapping(args)
    family = args.family.replace("-", "_")
    spec = _diagnostics_run_spec_ref(payload.get("diagnostics_run_spec"))
    observations = _mapping_sequence(payload.get("observations", ()), "observations")

    if family == "factor":
        from alpha_system.runtime.diagnostics.factor import build_factor_diagnostics_run

        result = build_factor_diagnostics_run(
            diagnostics_run_spec=spec,
            observations=observations,
            lineage_refs=_string_mapping(payload.get("lineage_refs", {}), "lineage_refs"),
            study_run_record_ref=payload.get("study_run_record_ref"),
            thresholds=payload.get("thresholds"),
        )
        return _command_payload("run-diagnostics", result)

    runtime_input_pack = _runtime_input_pack_from_mapping(
        _required_mapping(payload.get("runtime_input_pack"), "runtime_input_pack")
    )
    if family == "cross_market":
        from alpha_system.runtime.diagnostics.cross_market import (
            build_cross_market_diagnostics_run,
        )

        result = build_cross_market_diagnostics_run(
            diagnostics_run_spec=spec,
            runtime_input_pack=runtime_input_pack,
            observations=observations,
            config=payload.get("config"),
        )
        return _command_payload("run-diagnostics", result)

    if family in {"splits", "session_split", "regime_split"}:
        from alpha_system.runtime.diagnostics.splits import (
            build_regime_split_report,
            build_session_split_report,
            build_split_diagnostics_reports,
        )

        min_sample_count = int(payload.get("min_sample_count", 1))
        if family == "session_split":
            result = build_session_split_report(
                diagnostics_run_spec_ref=spec,
                runtime_input_pack=runtime_input_pack,
                observations=observations,
                min_sample_count=min_sample_count,
            )
        elif family == "regime_split":
            result = build_regime_split_report(
                diagnostics_run_spec_ref=spec,
                runtime_input_pack=runtime_input_pack,
                observations=observations,
                min_sample_count=min_sample_count,
            )
        else:
            result = build_split_diagnostics_reports(
                diagnostics_run_spec_ref=spec,
                runtime_input_pack=runtime_input_pack,
                observations=observations,
                min_sample_count=min_sample_count,
            )
        return _command_payload("run-diagnostics", result)

    raise RuntimeCliError(f"unsupported diagnostics family: {args.family}")


def _build_label_diagnostics_payload(args: argparse.Namespace) -> Mapping[str, Any]:
    payload = _load_mapping(args)

    from alpha_system.runtime.diagnostics.label.runtime import build_label_diagnostics_report

    result = build_label_diagnostics_report(
        diagnostics_run_spec=_diagnostics_run_spec_ref(payload.get("diagnostics_run_spec")),
        runtime_input_pack=_runtime_input_pack_from_mapping(
            _required_mapping(payload.get("runtime_input_pack"), "runtime_input_pack")
        ),
        feature_quality_reports=_mapping_sequence(
            payload.get("feature_quality_reports", ()),
            "feature_quality_reports",
        ),
        feature_coverage_reports=_mapping_sequence(
            payload.get("feature_coverage_reports", ()),
            "feature_coverage_reports",
        ),
        label_audit_reports=_mapping_sequence(
            payload.get("label_audit_reports", ()),
            "label_audit_reports",
        ),
        label_observations=_mapping_sequence(
            payload.get("label_observations", ()), "label_observations"
        ),
        label_profiles=payload.get("label_profiles", ()),
        live_feature_references=payload.get("live_feature_references", ()),
        config=payload.get("config"),
    )
    return _command_payload("run-label-diagnostics", result)


def _build_signal_probe_payload(args: argparse.Namespace) -> Mapping[str, Any]:
    payload = _load_mapping(args)

    from alpha_system.runtime.probe import run_signal_probe

    result = run_signal_probe(
        signal_probe_spec=_signal_probe_spec_from_mapping(
            _required_mapping(payload.get("signal_probe_spec"), "signal_probe_spec")
        ),
        observations=_mapping_sequence(payload.get("observations", ()), "observations"),
        cost_diagnostics_run_spec=_diagnostics_run_spec_ref(
            payload.get("cost_diagnostics_run_spec")
        ),
        lineage_refs=_string_mapping(payload.get("lineage_refs", {}), "lineage_refs"),
        cost_thresholds=payload.get("cost_thresholds"),
    )
    return _command_payload("run-signal-probe", result)


def _build_cost_stress_payload(args: argparse.Namespace) -> Mapping[str, Any]:
    payload = _load_mapping(args)

    from alpha_system.runtime.cost import build_cost_sensitivity_report

    result = build_cost_sensitivity_report(
        diagnostics_run_spec=_diagnostics_run_spec_ref(payload.get("diagnostics_run_spec")),
        fills=_mapping_sequence(payload.get("fills", ()), "fills"),
        lineage_refs=_string_mapping(payload.get("lineage_refs", {}), "lineage_refs"),
        cost_stress_spec=_cost_stress_spec_from_payload(payload),
        thresholds=payload.get("thresholds"),
    )
    return _command_payload("run-cost-stress", result)


def _build_evidence_draft_payload(args: argparse.Namespace) -> Mapping[str, Any]:
    draft = _evidence_draft_from_payload(_load_mapping(args))
    return _command_payload("build-evidence-draft", draft)


def _build_reference_handoff_payload(args: argparse.Namespace) -> Mapping[str, Any]:
    payload = _load_mapping(args)

    from alpha_system.runtime.handoff import build_reference_candidate_handoff

    evidence_input = payload.get("evidence_draft_input")
    if evidence_input is None:
        raise RuntimeCliError(
            "evidence_draft_input is required; EvidenceDraft objects are rebuilt through "
            "the existing evidence builder"
        )
    result = build_reference_candidate_handoff(
        alpha_spec_id=_required_text(payload.get("alpha_spec_id"), "alpha_spec_id"),
        study_spec_id=_required_text(payload.get("study_spec_id"), "study_spec_id"),
        evidence_draft=_evidence_draft_from_payload(
            _required_mapping(evidence_input, "evidence_draft_input")
        ),
        study_run_manifest=_study_run_manifest_from_mapping(
            _required_mapping(payload.get("study_run_manifest"), "study_run_manifest")
        ),
        runtime_artifact_manifest=_runtime_artifact_manifest_from_mapping(
            _required_mapping(
                payload.get("runtime_artifact_manifest"),
                "runtime_artifact_manifest",
            )
        ),
        cost_sensitivity_report=None,
        no_lookahead_audit_result=payload.get("no_lookahead_audit_result"),
        decision=payload.get("decision"),
        rejection_reasons=payload.get("rejection_reasons", ()),
        limitations=_text_sequence(payload.get("limitations", ()), "limitations"),
    )
    return _command_payload("build-reference-handoff", result)


def _build_summary_payload(args: argparse.Namespace) -> Mapping[str, Any]:
    payload = _load_mapping(args)
    return {
        "command": "summarize",
        "summary": _summarize_mapping(payload),
        "input": _compact_payload(payload),
    }


def _build_inspect_payload(args: argparse.Namespace) -> Mapping[str, Any]:
    payload = _load_mapping(args)
    inspected: object = payload
    schema = payload.get("schema")
    if schema == "alpha_system.runtime.study_run_manifest.v1":
        inspected = _study_run_manifest_from_mapping(payload)
    elif schema == "alpha_system.runtime.artifact_manifest.v1":
        inspected = _runtime_artifact_manifest_from_mapping(payload)
    elif schema == "alpha_system.runtime.study_run_record.v1":
        inspected = _study_run_record_from_mapping(payload)

    return {
        "command": "inspect",
        "summary": _summarize_mapping(_jsonable(inspected)),
        "payload": _jsonable(inspected),
    }


def _build_replay_summary_payload(args: argparse.Namespace) -> Mapping[str, Any]:
    payload = _load_mapping(args)
    manifest_payload = payload.get("study_run_manifest", payload)
    manifest = _study_run_manifest_from_mapping(
        _required_mapping(manifest_payload, "study_run_manifest")
    )
    record_payload = payload.get("study_run_record")
    record = (
        None
        if record_payload is None
        else _study_run_record_from_mapping(_required_mapping(record_payload, "study_run_record"))
    )
    summary: dict[str, Any] = {
        "run_id": manifest.run_id,
        "manifest_id": manifest.manifest_id,
        "dataset_version_id": manifest.dataset_version_id,
        "feature_pack_count": len(manifest.feature_pack_versions),
        "label_pack_count": len(manifest.label_pack_versions),
        "cost_model_version": manifest.cost_model_version,
        "rerun_performed": False,
    }
    if record is not None:
        summary["record_id"] = record.record_id
        summary["result_state"] = record.result_state.value
        summary["rejection_reason_count"] = len(record.rejection_reasons)
    return {"command": "replay-summary", "summary": summary}


def _evidence_draft_from_payload(payload: Mapping[str, Any]) -> object:
    from alpha_system.runtime.evidence import build_evidence_draft
    from alpha_system.runtime.evidence.draft import REVIEWER_VERDICT_PENDING_REF

    return build_evidence_draft(
        alpha_spec_id=_required_text(payload.get("alpha_spec_id"), "alpha_spec_id"),
        study_spec_id=_required_text(payload.get("study_spec_id"), "study_spec_id"),
        trial_refs=_text_sequence(payload.get("trial_refs", ()), "trial_refs"),
        study_run_manifest=_study_run_manifest_from_mapping(
            _required_mapping(payload.get("study_run_manifest"), "study_run_manifest")
        ),
        study_run_record=_study_run_record_from_mapping(
            _required_mapping(payload.get("study_run_record"), "study_run_record")
        ),
        negative_control_results=_mapping_sequence(
            payload.get("negative_control_results", ()),
            "negative_control_results",
        ),
        no_lookahead_audit_result=payload.get("no_lookahead_audit_result"),
        decision=payload.get("decision"),
        rejection_reasons=payload.get("rejection_reasons", ()),
        limitations=_text_sequence(payload.get("limitations", ()), "limitations"),
        artifact_manifest=_mapping_sequence(
            payload.get("artifact_manifest", ()), "artifact_manifest"
        ),
        reviewer_verdict_reference=str(
            payload.get("reviewer_verdict_reference", REVIEWER_VERDICT_PENDING_REF)
        ),
    )


def _runtime_request_from_mapping(payload: Mapping[str, Any]) -> object:
    from alpha_system.runtime.contracts.run_spec import RuntimeRequest

    kwargs = dict(payload)
    if isinstance(kwargs.get("runtime_input_pack"), Mapping):
        kwargs["runtime_input_pack"] = _runtime_input_pack_from_mapping(
            _required_mapping(kwargs["runtime_input_pack"], "runtime_input_pack")
        )
    return RuntimeRequest(**kwargs)


def _runtime_input_pack_from_mapping(payload: Mapping[str, Any]) -> object:
    from alpha_system.runtime.input_resolver import (
        CanonicalInputViewHandle,
        FeaturePackHandle,
        LabelPackHandle,
        RuntimeInputPack,
    )

    dataset_version = _optional_mapping(payload.get("dataset_version"), "dataset_version")
    return RuntimeInputPack(
        alpha_spec_ref=_required_text(payload.get("alpha_spec_ref"), "alpha_spec_ref"),
        study_spec_ref=_required_text(payload.get("study_spec_ref"), "study_spec_ref"),
        study_input_pack=_required_mapping(payload.get("study_input_pack"), "study_input_pack"),
        dataset_version_id=_required_text(
            payload.get("dataset_version_id")
            if dataset_version is None
            else dataset_version.get("dataset_version_id"),
            "dataset_version_id",
        ),
        dataset_lifecycle_state=_required_text(
            payload.get("dataset_lifecycle_state")
            if dataset_version is None
            else dataset_version.get("lifecycle_state"),
            "dataset_lifecycle_state",
        ),
        dataset_source=_required_text(
            payload.get("dataset_source")
            if dataset_version is None
            else dataset_version.get("source"),
            "dataset_source",
        ),
        dataset_reproducibility_hashes=_required_mapping(
            payload.get("dataset_reproducibility_hashes")
            if dataset_version is None
            else dataset_version.get("reproducibility_hashes"),
            "dataset_reproducibility_hashes",
        ),
        canonical_input_views=tuple(
            CanonicalInputViewHandle(**item)
            for item in _mapping_sequence(
                payload.get("canonical_input_views", ()), "canonical_input_views"
            )
        ),
        feature_packs=tuple(
            _feature_pack_handle(item, FeaturePackHandle)
            for item in _mapping_sequence(payload.get("feature_packs", ()), "feature_packs")
        ),
        label_packs=tuple(
            _label_pack_handle(item, LabelPackHandle)
            for item in _mapping_sequence(payload.get("label_packs", ()), "label_packs")
        ),
        dataset_scope=_required_mapping(payload.get("dataset_scope"), "dataset_scope"),
        partition_scope=_required_mapping(payload.get("partition_scope"), "partition_scope"),
        session_scope=_required_mapping(payload.get("session_scope"), "session_scope"),
        governance_metadata=_optional_mapping(
            payload.get("governance_metadata", {}),
            "governance_metadata",
        ),
    )


def _feature_pack_handle(payload: Mapping[str, Any], cls: Any) -> object:
    event_ts = _optional_mapping(payload.get("event_ts"), "event_ts") or {}
    available_ts = _optional_mapping(payload.get("available_ts"), "available_ts") or {}
    return cls(
        feature_version_id=payload.get("feature_version_id"),
        feature_request_id=payload.get("feature_request_id"),
        feature_set_id=payload.get("feature_set_id"),
        feature_set_version=payload.get("feature_set_version"),
        dataset_version_id=payload.get("dataset_version_id"),
        partition_id=payload.get("partition_id"),
        materialization_plan_id=payload.get("materialization_plan_id"),
        first_event_ts=payload.get("first_event_ts", event_ts.get("first")),
        last_event_ts=payload.get("last_event_ts", event_ts.get("last")),
        first_available_ts=payload.get("first_available_ts", available_ts.get("first")),
        last_available_ts=payload.get("last_available_ts", available_ts.get("last")),
        lifecycle_state=payload.get("lifecycle_state"),
    )


def _label_pack_handle(payload: Mapping[str, Any], cls: Any) -> object:
    event_ts = _optional_mapping(payload.get("event_ts"), "event_ts") or {}
    label_available_ts = (
        _optional_mapping(payload.get("label_available_ts"), "label_available_ts") or {}
    )
    return cls(
        label_version_id=payload.get("label_version_id"),
        label_spec_id=payload.get("label_spec_id"),
        label_id=payload.get("label_id"),
        dataset_version_id=payload.get("dataset_version_id"),
        partition_id=payload.get("partition_id"),
        materialization_plan_id=payload.get("materialization_plan_id"),
        first_event_ts=payload.get("first_event_ts", event_ts.get("first")),
        last_event_ts=payload.get("last_event_ts", event_ts.get("last")),
        first_label_available_ts=payload.get(
            "first_label_available_ts",
            label_available_ts.get("first"),
        ),
        last_label_available_ts=payload.get(
            "last_label_available_ts",
            label_available_ts.get("last"),
        ),
        lifecycle_state=payload.get("lifecycle_state"),
    )


def _diagnostics_run_spec_ref(value: object) -> object:
    from alpha_system.runtime.diagnostics.contracts import DiagnosticsRunSpecRef

    payload = _required_mapping(value, "diagnostics_run_spec")
    return DiagnosticsRunSpecRef(
        diagnostics_run_spec_id=payload.get("diagnostics_run_spec_id"),
        content_hash=payload.get("content_hash"),
    )


def _signal_probe_spec_from_mapping(payload: Mapping[str, Any]) -> object:
    from alpha_system.runtime.probe import SignalProbeSpec

    cost_payload = payload.get("cost_stress_spec", payload)
    return SignalProbeSpec(
        alpha_spec_ref=payload.get("alpha_spec_ref"),
        study_spec_ref=payload.get("study_spec_ref"),
        runtime_input_pack=_runtime_input_pack_from_mapping(
            _required_mapping(payload.get("runtime_input_pack"), "runtime_input_pack")
        ),
        feature_ref=_required_mapping(payload.get("feature_ref"), "feature_ref"),
        label_ref=_required_mapping(payload.get("label_ref"), "label_ref"),
        direction_policy=str(payload.get("direction_policy", "long_short_flat")),
        thresholds=payload.get("thresholds", ()),
        primary_threshold=payload.get("primary_threshold"),
        fill_policy=payload.get("fill_policy"),
        cost_stress_spec=_cost_stress_spec_from_payload(
            _required_mapping(cost_payload, "cost_stress_spec")
        ),
        spec_metadata=_optional_mapping(payload.get("spec_metadata", {}), "spec_metadata"),
    )


def _cost_stress_spec_from_payload(payload: Mapping[str, Any]) -> object:
    from alpha_system.runtime.cost import CostModelVersion, CostStressSpec

    model_payload = _required_mapping(payload.get("cost_model_version"), "cost_model_version")
    cost_model_version = CostModelVersion.from_mappings(
        cost_model_descriptor=_optional_mapping(
            model_payload.get("cost_model_descriptor"),
            "cost_model_descriptor",
        ),
        slippage_model_descriptor=_optional_mapping(
            model_payload.get("slippage_model_descriptor"),
            "slippage_model_descriptor",
        ),
        slippage_is_proxy=bool(model_payload.get("slippage_is_proxy", True)),
        bbo_available=bool(model_payload.get("bbo_available")),
    )
    config = _required_mapping(payload.get("cost_stress_config", {}), "cost_stress_config")
    return CostStressSpec.from_mapping(config, cost_model_version=cost_model_version)


def _study_run_manifest_from_mapping(payload: Mapping[str, Any]) -> object:
    from alpha_system.runtime.contracts import StudyRunManifest

    kwargs = {
        key: value
        for key, value in payload.items()
        if key not in {"schema", "manifest_id", "manifest_hash", "value_free"}
    }
    return StudyRunManifest(**kwargs)


def _runtime_artifact_manifest_from_mapping(payload: Mapping[str, Any]) -> object:
    from alpha_system.runtime.contracts import RuntimeArtifactManifest

    kwargs = {
        key: value
        for key, value in payload.items()
        if key not in {"schema", "manifest_id", "manifest_hash", "value_free"}
    }
    return RuntimeArtifactManifest(**kwargs)


def _study_run_record_from_mapping(payload: Mapping[str, Any]) -> object:
    from alpha_system.runtime.contracts import StudyRunRecord

    kwargs = {
        key: value
        for key, value in payload.items()
        if key not in {"schema", "record_id", "record_hash", "value_free"}
    }
    if "rejection_reason_records" in kwargs and "rejection_reasons" not in kwargs:
        kwargs["rejection_reasons"] = kwargs.pop("rejection_reason_records")
    return StudyRunRecord(**kwargs)


def _load_mapping(args: argparse.Namespace) -> Mapping[str, Any]:
    input_path = getattr(args, "input", None)
    if not input_path:
        raise RuntimeCliError("provide --input with a local JSON command envelope")
    value = json.loads(Path(input_path).read_text(encoding="utf-8"))
    return _required_mapping(value, "input")


def _emit(command: str, payload: Mapping[str, Any], *, emit_json: bool) -> None:
    if emit_json:
        print(json.dumps(_jsonable(payload), sort_keys=True, indent=2))
        return

    summary = _summarize_mapping(payload)
    print(f"Runtime command: {command}")
    if "status" in summary:
        print(f"Status: {summary['status']}")
    if "state" in summary:
        print(f"State: {summary['state']}")
    for key in ("id", "schema", "reason_count", "artifact_count"):
        if key in summary:
            label = key.replace("_", " ").capitalize()
            print(f"{label}: {summary[key]}")
    print("Local only: yes")
    print("Provider or broker action: no")


def _command_payload(command: str, result: object) -> Mapping[str, Any]:
    payload = _jsonable(result)
    return {
        "command": command,
        "result": payload,
        "summary": _summarize_mapping(payload),
        "local_only": True,
        "provider_or_broker_action": False,
    }


def _summarize_mapping(value: object) -> dict[str, Any]:
    payload = _jsonable(value)
    if not isinstance(payload, Mapping):
        return {"value_type": type(payload).__name__}

    summary: dict[str, Any] = {}
    if isinstance(payload.get("schema"), str):
        summary["schema"] = payload["schema"]

    state = _first_present(
        payload.get("status"),
        payload.get("state"),
        payload.get("result_state"),
        payload.get("decision_state"),
    )
    if state is not None:
        raw_state = str(state)
        summary["status" if "status" in payload else "state"] = raw_state
        decision_state = _decision_state_text(raw_state)
        if decision_state != raw_state:
            summary["decision_state"] = decision_state

    for key, item in payload.items():
        if key.endswith("_id") and isinstance(item, str):
            summary["id"] = item
            break

    reasons = _first_present(
        payload.get("reasons"),
        payload.get("rejection_reasons"),
        payload.get("rejection_reason_records"),
    )
    if isinstance(reasons, Sequence) and not isinstance(reasons, str):
        summary["reason_count"] = len(reasons)

    entries = payload.get("entries")
    if isinstance(entries, Sequence) and not isinstance(entries, str):
        summary["artifact_count"] = len(entries)

    if not summary:
        summary["keys"] = sorted(str(key) for key in payload.keys())[:12]
    return summary


def _decision_state_text(value: object) -> str:
    from alpha_system.runtime.decisions import coerce_runtime_decision_state

    try:
        return coerce_runtime_decision_state(str(value)).value
    except ValueError:
        return str(value)


def _compact_payload(value: Mapping[str, Any]) -> Mapping[str, Any]:
    keys = (
        "schema",
        "status",
        "state",
        "result_state",
        "decision",
        "reasons",
        "rejection_reasons",
        "rejection_reason_records",
    )
    return {key: value[key] for key in keys if key in value}


def _jsonable(value: object) -> Any:
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return _jsonable(to_dict())
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _jsonable(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return value.as_posix()
    if value is None or isinstance(value, bool | int | float | str):
        return value
    return str(value)


def _required_mapping(value: object, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise RuntimeCliError(f"{field} must be a JSON object")
    return value


def _optional_mapping(value: object, field: str) -> Mapping[str, Any] | None:
    if value is None:
        return None
    return _required_mapping(value, field)


def _mapping_sequence(value: object, field: str) -> tuple[Mapping[str, Any], ...]:
    if value is None:
        return ()
    if isinstance(value, Mapping) or isinstance(value, str):
        raise RuntimeCliError(f"{field} must be a JSON array of objects")
    if not isinstance(value, Sequence):
        raise RuntimeCliError(f"{field} must be a JSON array of objects")
    return tuple(_required_mapping(item, f"{field}[]") for item in value)


def _text_sequence(value: object, field: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if not isinstance(value, Sequence):
        raise RuntimeCliError(f"{field} must be a JSON array of strings")
    return tuple(_required_text(item, field) for item in value)


def _string_mapping(value: object, field: str) -> Mapping[str, str]:
    mapping = _required_mapping(value, field)
    return {str(key): _required_text(item, f"{field}.{key}") for key, item in mapping.items()}


def _required_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise RuntimeCliError(f"{field} must be a non-empty string")
    return value


def _first_present(*values: object) -> object | None:
    for value in values:
        if value is not None:
            return value
    return None


__all__ = [
    "RuntimeCliError",
    "register_subparser",
    "run_build_evidence_draft",
    "run_build_reference_handoff",
    "run_cost_stress",
    "run_diagnostics",
    "run_inspect",
    "run_label_diagnostics",
    "run_plan",
    "run_replay_summary",
    "run_signal_probe_command",
    "run_summarize",
    "run_validate_inputs",
]
