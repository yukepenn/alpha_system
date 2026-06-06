"""Local-only runtime smoke over one accepted FLF DatasetVersion.

The smoke exercises the runtime orchestration surface without fetching data,
reading provider files, persisting values, or making any alpha claim. When the
operator has not supplied local Feature/Label Foundation registries, it returns
``PASS_WITH_WARNINGS`` instead of fabricating a run.
"""

from __future__ import annotations

import json
import os
import sqlite3
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Any, cast

from alpha_system.data.foundation.datasets import DATASET_VERSION_ADMISSIBLE_STATES, DatasetVersion
from alpha_system.data.foundation.version_registry import resolve_dataset_version
from alpha_system.governance.alpha_spec import AlphaSpec, generate_alpha_spec_id, validate_alpha_spec
from alpha_system.governance.ids import GovernanceIdKind, generate_governance_id
from alpha_system.governance.serialization import JsonValue
from alpha_system.governance.serialization import content_hash as governance_content_hash
from alpha_system.governance.study_input_pack import StudyInputPack
from alpha_system.governance.study_input_pack import (
    validate_study_input_pack_references,
)
from alpha_system.governance.study_spec import StudySpec, create_study_spec
from alpha_system.runtime.audit.no_lookahead import NoLookaheadRuntimeAudit
from alpha_system.runtime.contracts.manifest import (
    FeaturePackVersionRef,
    LabelPackVersionRef,
    StudyRunManifest,
)
from alpha_system.runtime.contracts.run_record import StudyRunRecord, StudyRunResultState
from alpha_system.runtime.cost.model_version import CostModelVersion
from alpha_system.runtime.cost.runtime import CostStressFill, build_cost_sensitivity_report
from alpha_system.runtime.cost.spec import CostStressSpec
from alpha_system.runtime.decisions import (
    RejectionReasonRecord,
    RuntimeDecision,
    RuntimeDecisionStage,
    RuntimeDecisionState,
    normalize_rejection_reason,
)
from alpha_system.runtime.diagnostics.contracts import DiagnosticsFamily, DiagnosticsRunSpec
from alpha_system.runtime.diagnostics.factor.runtime import build_factor_diagnostics_run
from alpha_system.runtime.diagnostics.label.runtime import (
    LabelDiagnosticsConfig,
    build_label_diagnostics_report,
)
from alpha_system.runtime.entry_contract import (
    RuntimeEntryRequest,
    evaluate_runtime_entry_request,
)
from alpha_system.runtime.evidence.draft import EvidenceDraft, build_evidence_draft
from alpha_system.runtime.input_resolver import (
    FeatureLabelPackResolver,
    RuntimeInputPack,
    resolve_runtime_input_pack,
)
from alpha_system.runtime.tool_results import RuntimeRunSummary, RuntimeToolResult

SMOKE_RESULT_SCHEMA = "alpha_system.runtime.real_dataset_version_smoke.v1"
PHASE_ID = "RT-P21"
DEFAULT_RUN_ID = "rt_p21_real_dataset_version_smoke"
DEFAULT_PARTITION_ID = "development_partition"
DEFAULT_SESSION_SCOPE = {"session": "rth_and_eth"}
OPERATOR_COMMAND_TEMPLATE = (
    "ALPHA_DATA_ROOT=/abs/local/alpha_data "
    "ALPHA_DATASET_VERSION_ID=dsv_... "
    "ALPHA_FEATURE_PACK_REFS=fver_... "
    "ALPHA_LABEL_PACK_REFS=lver_... "
    "python -m alpha_system.runtime.smoke"
)
DatasetVersionResolver = Callable[[str | Path, object], object | None]


class RuntimeSmokeStatus(StrEnum):
    """CI-safe smoke result status."""

    PASS = "PASS"
    PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"


@dataclass(frozen=True, slots=True)
class SmokeConfig:
    """Operator-configurable local smoke inputs."""

    alpha_data_root: Path | None = None
    dataset_version_id: str | None = None
    feature_pack_refs: tuple[str, ...] = ()
    label_pack_refs: tuple[str, ...] = ()
    feature_request_ids: tuple[str, ...] = ()
    label_spec_ids: tuple[str, ...] = ()
    partition_scope: Mapping[str, Any] | None = None
    session_scope: Mapping[str, Any] = field(default_factory=lambda: dict(DEFAULT_SESSION_SCOPE))
    dataset_lifecycle_state: str | None = None
    run_id: str = DEFAULT_RUN_ID
    operator_command: str = OPERATOR_COMMAND_TEMPLATE

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> SmokeConfig:
        """Build config from local operator environment variables."""

        source = os.environ if env is None else env
        root = source.get("ALPHA_DATA_ROOT")
        partition_id = source.get("ALPHA_RUNTIME_SMOKE_PARTITION_ID")
        return cls(
            alpha_data_root=Path(root).expanduser() if root else None,
            dataset_version_id=_optional_text(source.get("ALPHA_DATASET_VERSION_ID")),
            feature_pack_refs=_csv(source.get("ALPHA_FEATURE_PACK_REFS"))
            or _csv(source.get("ALPHA_FEATURE_PACK_REF")),
            label_pack_refs=_csv(source.get("ALPHA_LABEL_PACK_REFS"))
            or _csv(source.get("ALPHA_LABEL_PACK_REF")),
            feature_request_ids=_csv(source.get("ALPHA_FEATURE_REQUEST_IDS")),
            label_spec_ids=_csv(source.get("ALPHA_LABEL_SPEC_IDS")),
            partition_scope={"partition_id": partition_id.strip()} if partition_id else None,
            session_scope=_json_mapping_env(
                source.get("ALPHA_RUNTIME_SMOKE_SESSION_SCOPE"),
                default=DEFAULT_SESSION_SCOPE,
            ),
            dataset_lifecycle_state=_optional_text(source.get("ALPHA_DATASET_LIFECYCLE_STATE")),
            run_id=_optional_text(source.get("ALPHA_RUNTIME_SMOKE_RUN_ID")) or DEFAULT_RUN_ID,
            operator_command=source.get("ALPHA_RUNTIME_SMOKE_OPERATOR_COMMAND")
            or OPERATOR_COMMAND_TEMPLATE,
        )


@dataclass(frozen=True, slots=True)
class RuntimeSmokeResult:
    """Value-free result returned by the local real-DatasetVersion smoke."""

    status: RuntimeSmokeStatus
    run_id: str
    operator_command: str
    real_dataset_version_smoke_ran: bool
    warning_reason: str | None
    dataset_version_id: str | None
    feature_pack_refs: tuple[str, ...]
    label_pack_refs: tuple[str, ...]
    entry_status: str | None = None
    input_resolution_status: str | None = None
    diagnostics_statuses: Mapping[str, str] | None = None
    cost_profiles: tuple[str, ...] = ()
    evidence_draft: EvidenceDraft | None = None
    tool_result: RuntimeToolResult | None = None
    run_summary: RuntimeRunSummary | None = None
    rejection_reasons: tuple[RejectionReasonRecord, ...] = ()
    emitted_paths: tuple[str, ...] = ()
    external_provider_call: bool = False
    raw_file_read: bool = False
    limitations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Return a stable value-free smoke payload."""

        return {
            "schema": SMOKE_RESULT_SCHEMA,
            "phase_id": PHASE_ID,
            "status": self.status.value,
            "run_id": self.run_id,
            "operator_command": self.operator_command,
            "real_dataset_version_smoke_ran": self.real_dataset_version_smoke_ran,
            "warning_reason": self.warning_reason,
            "dataset_version_id": self.dataset_version_id,
            "feature_pack_refs": list(self.feature_pack_refs),
            "label_pack_refs": list(self.label_pack_refs),
            "entry_status": self.entry_status,
            "input_resolution_status": self.input_resolution_status,
            "diagnostics_statuses": dict(self.diagnostics_statuses or {}),
            "cost_profiles": list(self.cost_profiles),
            "evidence_draft_ref": None
            if self.evidence_draft is None
            else {
                "draft_id": self.evidence_draft.draft_id,
                "draft_hash": self.evidence_draft.draft_hash,
                "decision_state": self.evidence_draft.decision_state.value,
                "descriptive_only": True,
                "not_a_candidate": True,
                "not_reference_truth": True,
            },
            "tool_result": None if self.tool_result is None else self.tool_result.to_dict(),
            "run_summary": None if self.run_summary is None else self.run_summary.to_dict(),
            "rejection_reasons": [reason.to_dict() for reason in self.rejection_reasons],
            "emitted_paths": list(self.emitted_paths),
            "external_provider_call": False,
            "raw_file_read": False,
            "raw_or_heavy_data_embedded": False,
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True, slots=True)
class _SelectedSmokeInputs:
    dataset_version: DatasetVersion
    dataset_lifecycle_state: str
    feature_pack_refs: tuple[str, ...]
    label_pack_refs: tuple[str, ...]
    feature_request_ids: tuple[str, ...]
    label_spec_ids: tuple[str, ...]
    partition_scope: Mapping[str, Any]
    session_scope: Mapping[str, Any]


def run_real_dataset_version_smoke(
    config: SmokeConfig | None = None,
    *,
    dataset_version_resolver: DatasetVersionResolver = resolve_dataset_version,
    feature_label_resolver: FeatureLabelPackResolver | None = None,
) -> RuntimeSmokeResult:
    """Run the local-only real-DatasetVersion runtime smoke.

    A missing local data root, registry, DatasetVersion, or Feature/Label handle
    returns ``PASS_WITH_WARNINGS`` so CI remains safe in clean checkouts.
    """

    active = config or SmokeConfig.from_env()
    preflight_reason = _preflight_config(active)
    if preflight_reason is not None:
        return _warning_result(active, preflight_reason)

    assert active.alpha_data_root is not None
    registry_path = active.alpha_data_root / "registry" / "datasets.sqlite"
    selection = _select_smoke_inputs(
        active,
        registry_path=registry_path,
        dataset_version_resolver=dataset_version_resolver,
    )
    if isinstance(selection, str):
        return _warning_result(active, selection)

    governance = _build_governance_specs(selection)
    entry_result = evaluate_runtime_entry_request(
        RuntimeEntryRequest(
            alpha_spec_ref=governance.alpha_spec.alpha_spec_id,
            study_spec_ref=governance.study_spec.study_spec_id,
            study_input_pack=governance.study_input_pack,
            target_dataset_version_id=selection.dataset_version.dataset_version_id,
            dataset_scope=governance.dataset_scope,
            partition_scope=selection.partition_scope,
            expected_dataset_lifecycle_state=selection.dataset_lifecycle_state,
            dataset_version_source_family=selection.dataset_version.source,
            external_provider_call_requested=False,
            request_metadata={
                "phase_id": PHASE_ID,
                "local_only": True,
                "external_provider_call": False,
                "raw_file_read": False,
            },
        )
    )
    if not entry_result.resolved:
        return _warning_result(
            active,
            _reason_text("runtime entry blocked or inconclusive", entry_result.reasons),
            dataset_version_id=selection.dataset_version.dataset_version_id,
            feature_pack_refs=selection.feature_pack_refs,
            label_pack_refs=selection.label_pack_refs,
            entry_status=entry_result.status.value,
        )

    resolver = feature_label_resolver or FeatureLabelPackResolver(
        alpha_data_root=active.alpha_data_root
    )
    resolution = resolve_runtime_input_pack(
        entry_result,
        registry_path=registry_path,
        dataset_lifecycle_state=selection.dataset_lifecycle_state,
        feature_pack_refs=selection.feature_pack_refs,
        label_pack_refs=selection.label_pack_refs,
        partition_scope=selection.partition_scope,
        session_scope=selection.session_scope,
        governance_metadata={"rt_p21_smoke": "development_partition_only_no_locked_selection"},
        partition_purpose="rt_p21_runtime_smoke",
        feature_label_resolver=resolver,
        dataset_version_resolver=dataset_version_resolver,
    )
    if not resolution.resolved or resolution.input_pack is None:
        return _warning_result(
            active,
            _reason_text("runtime input resolution did not resolve", resolution.reasons),
            dataset_version_id=selection.dataset_version.dataset_version_id,
            feature_pack_refs=selection.feature_pack_refs,
            label_pack_refs=selection.label_pack_refs,
            entry_status=entry_result.status.value,
            input_resolution_status=resolution.status.value,
        )

    return _run_resolved_smoke(
        active,
        selection=selection,
        governance=governance,
        input_pack=resolution.input_pack,
        entry_status=entry_result.status.value,
        input_resolution_status=resolution.status.value,
    )


@dataclass(frozen=True, slots=True)
class _GovernanceSpecs:
    alpha_spec: AlphaSpec
    study_spec: StudySpec
    study_input_pack: StudyInputPack
    dataset_scope: Mapping[str, JsonValue]


def _run_resolved_smoke(
    config: SmokeConfig,
    *,
    selection: _SelectedSmokeInputs,
    governance: _GovernanceSpecs,
    input_pack: RuntimeInputPack,
    entry_status: str,
    input_resolution_status: str,
) -> RuntimeSmokeResult:
    spec_ref = _study_run_spec_ref(governance.study_spec, input_pack)
    plan_ref = _runtime_plan_ref(governance.study_spec, input_pack)
    diagnostics_specs = {
        "factor": DiagnosticsRunSpec(
            diagnostics_family=DiagnosticsFamily.FACTOR,
            study_run_spec=spec_ref,
            runtime_plan=plan_ref,
            spec_metadata={"phase_id": PHASE_ID, "tier": "tier_0_factor_smoke"},
        ),
        "label": DiagnosticsRunSpec(
            diagnostics_family=DiagnosticsFamily.LABEL,
            study_run_spec=spec_ref,
            runtime_plan=plan_ref,
            spec_metadata={"phase_id": PHASE_ID, "tier": "tier_0_label_smoke"},
        ),
        "cost": DiagnosticsRunSpec(
            diagnostics_family=DiagnosticsFamily.COST,
            study_run_spec=spec_ref,
            runtime_plan=plan_ref,
            spec_metadata={"phase_id": PHASE_ID, "tier": "tier_0_cost_stress_smoke"},
        ),
    }

    factor_result = build_factor_diagnostics_run(
        diagnostics_run_spec=diagnostics_specs["factor"],
        observations=_smoke_factor_observations(input_pack),
        lineage_refs=_lineage_refs(input_pack),
        thresholds={"min_observations": 3},
    )
    label_report = build_label_diagnostics_report(
        diagnostics_run_spec=diagnostics_specs["label"],
        runtime_input_pack=input_pack,
        label_observations=_smoke_label_observations(input_pack),
        label_profiles=(
            {
                "profile": "rt_p21_smoke_cost_adjusted_label_profile",
                "cost_model_ref": "rt_p21_slippage_proxy_cost_model",
                "cost_adjusted": True,
            },
        ),
        live_feature_references=tuple(pack.feature_version_id for pack in input_pack.feature_packs),
        config=LabelDiagnosticsConfig(
            require_label_audit=False,
            require_feature_label_coverage=False,
            require_cost_adjustment_metadata=True,
        ),
    )
    cost_model_version = CostModelVersion.from_mappings(bbo_available=True)
    cost_spec = CostStressSpec(cost_model_version=cost_model_version)
    cost_report = build_cost_sensitivity_report(
        diagnostics_run_spec=diagnostics_specs["cost"],
        fills=_smoke_fills(),
        lineage_refs=_lineage_refs(input_pack),
        cost_stress_spec=cost_spec,
    )
    audit_result = NoLookaheadRuntimeAudit().evaluate(
        runtime_input_pack=input_pack,
        decision_ts=_decision_ts(input_pack),
        feature_inputs=_audit_feature_inputs(input_pack),
        label_inputs=_audit_label_inputs(input_pack),
        partition_scope=input_pack.partition_scope,
        partition_purpose="rt_p21_runtime_smoke",
        governance_metadata=input_pack.governance_metadata,
    )

    manifest = _study_run_manifest(
        run_id=config.run_id,
        input_pack=input_pack,
        cost_model_version=cost_model_version,
    )
    if audit_result.rejected:
        terminal_reasons = tuple(
            normalize_rejection_reason(
                reason,
                stage=RuntimeDecisionStage.NO_LOOKAHEAD_AUDIT,
            )
            for reason in audit_result.reasons
        )
        study_run_record = StudyRunRecord(
            run_id=config.run_id,
            study_run_spec_ref=spec_ref,
            result_state=StudyRunResultState.BLOCKED,
            rejection_reasons=audit_result.runtime_entry_reasons,
            manifest_ref=manifest,
        )
        decision = RuntimeDecision.from_reasons(terminal_reasons)
        status = RuntimeSmokeStatus.PASS_WITH_WARNINGS
        warning_reason = "no-lookahead audit rejected the resolved local smoke inputs"
    else:
        terminal_reasons = ()
        study_run_record = StudyRunRecord(
            run_id=config.run_id,
            study_run_spec_ref=spec_ref,
            result_state=StudyRunResultState.EVIDENCE_DRAFT_READY,
            manifest_ref=manifest,
        )
        decision = RuntimeDecision(state=RuntimeDecisionState.EVIDENCE_DRAFT_READY)
        status = RuntimeSmokeStatus.PASS
        warning_reason = None

    evidence_draft = build_evidence_draft(
        alpha_spec_id=governance.alpha_spec.alpha_spec_id,
        study_spec_id=governance.study_spec.study_spec_id,
        trial_refs=(
            generate_governance_id(
                GovernanceIdKind.TRIAL_LEDGER_RECORD,
                {
                    "phase_id": PHASE_ID,
                    "run_id": config.run_id,
                    "dataset_version_id": input_pack.dataset_version_id,
                },
            ),
        ),
        study_run_manifest=manifest,
        study_run_record=study_run_record,
        negative_control_results=(
            {
                "control_id": "rt_p21_no_external_provider_call",
                "status": "RECORDED",
                "finding": "no provider surface is imported or called by the smoke",
            },
        ),
        factor_diagnostics_report=factor_result.report,
        label_diagnostics_report=label_report,
        cost_sensitivity_report=cost_report,
        no_lookahead_audit_result=audit_result,
        decision=decision,
        limitations=(
            "Local runtime smoke only; not alpha validation.",
            "Smoke observations are deterministic wiring checks, not research evidence.",
            "Slippage is labeled as a proxy.",
        ),
    )
    tool_result = RuntimeToolResult.from_study_run_record(
        study_run_record=study_run_record,
        manifest=manifest,
        diagnostics_summary=(
            factor_result.report.report,
            label_report.diagnostics_report,
            cost_report.diagnostics_report,
        ),
        cost_summary=cost_report,
        rejection_reasons=terminal_reasons,
        next_required_gate="fresh_yellow_lane_review_before_merge",
    )
    run_summary = RuntimeRunSummary.from_tool_result(tool_result)

    return RuntimeSmokeResult(
        status=status,
        run_id=config.run_id,
        operator_command=config.operator_command,
        real_dataset_version_smoke_ran=True,
        warning_reason=warning_reason,
        dataset_version_id=input_pack.dataset_version_id,
        feature_pack_refs=selection.feature_pack_refs,
        label_pack_refs=selection.label_pack_refs,
        entry_status=entry_status,
        input_resolution_status=input_resolution_status,
        diagnostics_statuses={
            "factor": factor_result.report.status.value,
            "label": label_report.status.value,
            "cost": cost_report.status.value,
            "no_lookahead_audit": audit_result.outcome.value,
        },
        cost_profiles=cost_spec.profile_names,
        evidence_draft=evidence_draft,
        tool_result=tool_result,
        run_summary=run_summary,
        rejection_reasons=terminal_reasons,
        limitations=(
            "Smoke PASS is not alpha validation.",
            "EvidenceDraft is not a candidate.",
            "Fast path is not Reference truth.",
            "No external provider call or raw provider file read is performed.",
        ),
    )


def _select_smoke_inputs(
    config: SmokeConfig,
    *,
    registry_path: Path,
    dataset_version_resolver: DatasetVersionResolver,
) -> _SelectedSmokeInputs | str:
    assert config.alpha_data_root is not None
    dataset_ids = (config.dataset_version_id,) if config.dataset_version_id else _dataset_ids(registry_path)
    if not dataset_ids:
        return "no DatasetVersion id supplied and no local DatasetVersion registry rows found"

    missing_reasons: list[str] = []
    for dataset_id in dataset_ids:
        dataset_version = dataset_version_resolver(registry_path, dataset_id)
        if dataset_version is None:
            missing_reasons.append(f"{dataset_id}: resolve_dataset_version returned no record")
            continue
        if not isinstance(dataset_version, DatasetVersion):
            return f"{dataset_id}: resolve_dataset_version did not return a DatasetVersion"

        lifecycle_state = _lifecycle_state(config, dataset_version)
        if lifecycle_state not in DATASET_VERSION_ADMISSIBLE_STATES:
            missing_reasons.append(
                f"{dataset_id}: lifecycle state {lifecycle_state!r} is not admissible"
            )
            continue

        selection = _select_feature_label_refs(
            config,
            dataset_version_id=dataset_version.dataset_version_id,
        )
        if isinstance(selection, str):
            missing_reasons.append(f"{dataset_id}: {selection}")
            continue
        feature_refs, label_refs, feature_request_ids, label_spec_ids, partition_scope = selection
        return _SelectedSmokeInputs(
            dataset_version=dataset_version,
            dataset_lifecycle_state=lifecycle_state,
            feature_pack_refs=feature_refs,
            label_pack_refs=label_refs,
            feature_request_ids=feature_request_ids,
            label_spec_ids=label_spec_ids,
            partition_scope=partition_scope,
            session_scope=config.session_scope,
        )

    return "; ".join(missing_reasons) or "no admissible DatasetVersion resolved"


def _select_feature_label_refs(
    config: SmokeConfig,
    *,
    dataset_version_id: str,
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    Mapping[str, Any],
] | str:
    assert config.alpha_data_root is not None
    if (
        config.feature_pack_refs
        and config.label_pack_refs
        and config.feature_request_ids
        and config.label_spec_ids
        and config.partition_scope is not None
    ):
        return (
            config.feature_pack_refs,
            config.label_pack_refs,
            config.feature_request_ids,
            config.label_spec_ids,
            config.partition_scope,
        )

    feature_rows = _feature_registry_rows(
        config.alpha_data_root / "registry" / "features.sqlite",
        dataset_version_id=dataset_version_id,
        feature_refs=config.feature_pack_refs,
    )
    label_rows = _label_registry_rows(
        config.alpha_data_root / "registry" / "labels.sqlite",
        dataset_version_id=dataset_version_id,
        label_refs=config.label_pack_refs,
    )
    if isinstance(feature_rows, str):
        return feature_rows
    if isinstance(label_rows, str):
        return label_rows

    feature_refs = config.feature_pack_refs or tuple(row["feature_version_id"] for row in feature_rows[:1])
    label_refs = config.label_pack_refs or tuple(row["label_version_id"] for row in label_rows[:1])
    feature_request_ids = config.feature_request_ids or tuple(
        row["feature_request_id"] for row in feature_rows[: len(feature_refs)]
    )
    label_spec_ids = config.label_spec_ids or tuple(
        row["label_spec_id"] for row in label_rows[: len(label_refs)]
    )
    partition_id = _partition_id(config, feature_rows, label_rows)

    if not feature_refs:
        return "no registered feature pack found for DatasetVersion"
    if not label_refs:
        return "no registered label pack found for DatasetVersion"
    if not feature_request_ids:
        return "no FeatureRequest id found for selected feature pack"
    if not label_spec_ids:
        return "no LabelSpec id found for selected label pack"
    if partition_id is None:
        return "no partition id found for selected Feature/Label packs"
    return (
        tuple(feature_refs),
        tuple(label_refs),
        tuple(feature_request_ids),
        tuple(label_spec_ids),
        config.partition_scope or {"partition_id": partition_id},
    )


def _preflight_config(config: SmokeConfig) -> str | None:
    if config.alpha_data_root is None:
        return "ALPHA_DATA_ROOT is not set"
    root = config.alpha_data_root.expanduser().resolve(strict=False)
    repo_root = Path.cwd().resolve(strict=False)
    if root == repo_root or repo_root in root.parents:
        return "ALPHA_DATA_ROOT must be outside the repository"
    registry_dir = root / "registry"
    if not registry_dir.exists():
        return "$ALPHA_DATA_ROOT/registry is absent"
    required = ("datasets.sqlite", "features.sqlite", "labels.sqlite")
    missing = [name for name in required if not (registry_dir / name).is_file()]
    if missing:
        return "missing local registry file(s): " + ", ".join(missing)
    return None


def _build_governance_specs(selection: _SelectedSmokeInputs) -> _GovernanceSpecs:
    dataset_version = selection.dataset_version
    dataset_scope: dict[str, JsonValue] = {
        "dataset_version_id": dataset_version.dataset_version_id,
        "source": dataset_version.source,
        "symbol_universe": list(dataset_version.symbol_universe),
        "contract_universe": list(dataset_version.contract_universe),
        "accepted_dataset_version_only": True,
        "raw_provider_access": False,
        "external_provider_call": False,
    }
    hypothesis_id = generate_governance_id(
        GovernanceIdKind.HYPOTHESIS_CARD,
        {
            "phase_id": PHASE_ID,
            "dataset_version_id": dataset_version.dataset_version_id,
            "label_spec_ids": list(selection.label_spec_ids),
        },
    )
    alpha_payload: dict[str, JsonValue] = {
        "hypothesis_id": hypothesis_id,
        "target_instruments": list(dataset_version.symbol_universe) or ["local_dataset_symbol"],
        "data_assumptions": {
            "accepted_dataset_version_only": True,
            "dataset_version_id": dataset_version.dataset_version_id,
            "feature_label_packs_registered": True,
        },
        "factor_inputs": list(selection.feature_request_ids),
        "label_references": list(selection.label_spec_ids),
        "exclusion_rules": [
            "no external provider call",
            "no raw provider file access",
            "no label as live feature input",
        ],
        "timestamp_assumptions": {
            "feature_available_ts_required": True,
            "label_available_ts_required": True,
        },
        "cost_assumptions": {
            "double_cost_profile_required": True,
            "slippage_labeled_proxy": True,
        },
        "expected_failure_modes": [
            "local registry absent",
            "feature or label pack absent",
            "inconclusive diagnostics remain visible",
        ],
        "promotion_criteria": [
            "no promotion decision is made by this smoke",
            "fresh review remains required before merge",
        ],
        "created_by": "rt_p21_runtime_smoke",
        "created_at": "2026-06-06T00:00:00+00:00",
    }
    alpha_payload["alpha_spec_id"] = generate_alpha_spec_id(alpha_payload)
    alpha_spec = validate_alpha_spec(alpha_payload)
    study_spec = create_study_spec(
        alpha_spec_id=alpha_spec.alpha_spec_id,
        label_spec_id=selection.label_spec_ids[0],
        dataset_scope=dataset_scope,
        split_protocol={
            "partition_id": str(selection.partition_scope["partition_id"]),
            "single_partition_smoke": True,
        },
        metrics=[
            "tier_0_factor_diagnostics",
            "tier_0_label_diagnostics",
            "double_cost_stress",
        ],
        cost_assumptions={
            "double_cost_required": True,
            "slippage_labeled_proxy": True,
        },
        variant_budget=1,
        locked_test_policy={
            "policy": "locked_test_not_used_by_rt_p21_smoke",
            "selection_on_locked_test": "forbidden",
            "locked_test_not_used_by_smoke": "true",
        },
        negative_controls=[
            "no_external_provider_call",
            "no_raw_provider_file_read",
        ],
        stopping_rules=[
            "stop_on_unresolved_dataset_version",
            "stop_on_missing_feature_or_label_pack",
            "record_inconclusive_without_claims",
        ],
    )
    study_input_pack = StudyInputPack(
        feature_request_ids=selection.feature_request_ids,
        label_spec_ids=selection.label_spec_ids,
        alpha_spec_id=alpha_spec.alpha_spec_id,
        dataset_scope=dataset_scope,
    )
    validate_study_input_pack_references(
        study_input_pack,
        alpha_spec=alpha_spec,
        study_spec=study_spec,
    )
    return _GovernanceSpecs(
        alpha_spec=alpha_spec,
        study_spec=study_spec,
        study_input_pack=study_input_pack,
        dataset_scope=dataset_scope,
    )


def _study_run_manifest(
    *,
    run_id: str,
    input_pack: RuntimeInputPack,
    cost_model_version: CostModelVersion,
) -> StudyRunManifest:
    return StudyRunManifest(
        run_id=run_id,
        dataset_version_id=input_pack.dataset_version_id,
        dataset_version_hash=_hash_from_mapping(dict(input_pack.dataset_reproducibility_hashes)),
        dataset_lineage_ref=f"dataset_version:{input_pack.dataset_version_id}",
        dataset_admissibility_state=input_pack.dataset_lifecycle_state,
        feature_pack_versions=tuple(_feature_ref(pack) for pack in input_pack.feature_packs),
        label_pack_versions=tuple(_label_ref(pack) for pack in input_pack.label_packs),
        code_version="rt_p21_runtime_smoke",
        code_content_hash=governance_content_hash(
            {"phase_id": PHASE_ID, "module": "alpha_system.runtime.smoke"}
        ),
        config_version="rt_p21_smoke_config_v1",
        config_hash=governance_content_hash(
            {
                "dataset_version_id": input_pack.dataset_version_id,
                "feature_pack_count": len(input_pack.feature_packs),
                "label_pack_count": len(input_pack.label_packs),
            }
        ),
        cost_model_version=cost_model_version.cost_model_version_id,
        cost_model_hash=cost_model_version.content_hash,
    )


def _feature_ref(pack: Any) -> FeaturePackVersionRef:
    payload = pack.to_dict()
    return FeaturePackVersionRef(
        pack_id=pack.feature_version_id,
        content_hash=governance_content_hash(cast(JsonValue, payload)),
        lineage_ref=f"feature_lineage:{pack.materialization_plan_id}:{pack.feature_request_id}",
        available_ts_ref=f"available_ts:{pack.first_available_ts}:{pack.last_available_ts}",
    )


def _label_ref(pack: Any) -> LabelPackVersionRef:
    payload = pack.to_dict()
    return LabelPackVersionRef(
        pack_id=pack.label_version_id,
        content_hash=governance_content_hash(cast(JsonValue, payload)),
        lineage_ref=f"label_lineage:{pack.materialization_plan_id}:{pack.label_spec_id}",
        label_available_ts_ref=(
            f"label_available_ts:{pack.first_label_available_ts}:{pack.last_label_available_ts}"
        ),
    )


def _smoke_factor_observations(input_pack: RuntimeInputPack) -> tuple[dict[str, object], ...]:
    feature = input_pack.feature_packs[0]
    label = input_pack.label_packs[0]
    event_ts = _max_ts(feature.first_event_ts, label.first_event_ts)
    available_ts = _max_ts(feature.first_available_ts, event_ts.isoformat())
    label_available_ts = _max_ts(label.first_label_available_ts, event_ts.isoformat())
    values = ((-1.0, -0.01, 300), (0.0, 0.0, 300), (1.0, 0.01, 600), (2.0, 0.02, 600))
    return tuple(
        {
            "factor_value": factor_value,
            "label_value": label_value,
            "horizon_seconds": horizon,
            "available_ts": available_ts.isoformat(),
            "label_available_ts": label_available_ts.isoformat(),
        }
        for factor_value, label_value, horizon in values
    )


def _smoke_label_observations(input_pack: RuntimeInputPack) -> tuple[dict[str, object], ...]:
    label = input_pack.label_packs[0]
    event_ts = _parse_ts(label.first_event_ts)
    label_available_ts = _max_ts(
        label.first_label_available_ts,
        (event_ts + timedelta(minutes=10)).isoformat(),
    )
    observations: list[dict[str, object]] = []
    for index, (label_value, horizon_seconds) in enumerate(
        ((-0.01, 300), (0.01, 300), (-0.02, 600), (0.02, 600))
    ):
        current_event = event_ts + timedelta(minutes=index)
        horizon_end = current_event + timedelta(seconds=horizon_seconds)
        known_ts = max(label_available_ts, horizon_end)
        observations.append(
            {
                "event_ts": current_event.isoformat(),
                "horizon_end_ts": horizon_end.isoformat(),
                "label_available_ts": known_ts.isoformat(),
                "value_known_ts": known_ts.isoformat(),
                "label_value": label_value,
                "horizon_seconds": horizon_seconds,
                "cost_model_ref": "rt_p21_slippage_proxy_cost_model",
                "cost_adjusted": True,
                "target_before_stop": label_value > 0,
                "path_ambiguity": False,
            }
        )
    return tuple(observations)


def _smoke_fills() -> tuple[CostStressFill, ...]:
    return (
        CostStressFill(price="5000.00", quantity="1", side="buy", bid="4999.75", ask="5000.25"),
        CostStressFill(price="5001.00", quantity="1", side="sell", bid="5000.75", ask="5001.25"),
    )


def _audit_feature_inputs(input_pack: RuntimeInputPack) -> tuple[Mapping[str, object], ...]:
    return tuple(
        {
            "event_ts": pack.first_event_ts,
            "available_ts": pack.first_available_ts,
            "feature_version_id": pack.feature_version_id,
        }
        for pack in input_pack.feature_packs
    )


def _audit_label_inputs(input_pack: RuntimeInputPack) -> tuple[Mapping[str, object], ...]:
    return tuple(
        {
            "event_ts": pack.first_event_ts,
            "label_available_ts": pack.first_label_available_ts,
            "label_version_id": pack.label_version_id,
        }
        for pack in input_pack.label_packs
    )


def _decision_ts(input_pack: RuntimeInputPack) -> str:
    latest_feature = max(_parse_ts(pack.last_available_ts) for pack in input_pack.feature_packs)
    return (latest_feature + timedelta(seconds=1)).isoformat()


def _lineage_refs(input_pack: RuntimeInputPack) -> dict[str, str]:
    return {
        "dataset_version_id": input_pack.dataset_version_id,
        "feature_pack_refs": ",".join(pack.feature_version_id for pack in input_pack.feature_packs),
        "label_pack_refs": ",".join(pack.label_version_id for pack in input_pack.label_packs),
    }


def _study_run_spec_ref(study_spec: StudySpec, input_pack: RuntimeInputPack) -> dict[str, str]:
    digest = governance_content_hash(
        {
            "phase_id": PHASE_ID,
            "study_spec_id": study_spec.study_spec_id,
            "dataset_version_id": input_pack.dataset_version_id,
        }
    )
    return {"study_run_spec_id": f"srun_{digest[:24]}", "content_hash": digest}


def _runtime_plan_ref(study_spec: StudySpec, input_pack: RuntimeInputPack) -> dict[str, str]:
    digest = governance_content_hash(
        {
            "phase_id": PHASE_ID,
            "study_spec_id": study_spec.study_spec_id,
            "partition_scope": input_pack.partition_scope,
            "session_scope": input_pack.session_scope,
            "cost_profiles": ["base", "stress_1", "stress_2", "double_cost"],
        }
    )
    return {"plan_id": f"rplan_{digest[:24]}", "content_hash": digest}


def _dataset_ids(registry_path: Path) -> tuple[str, ...]:
    try:
        with _sqlite_read_only(registry_path) as connection:
            rows = connection.execute(
                """
                SELECT data_version
                FROM dataset_versions
                ORDER BY created_at DESC, data_version
                """
            ).fetchall()
    except (OSError, sqlite3.Error):
        return ()
    return tuple(str(row["data_version"]) for row in rows)


def _feature_registry_rows(
    registry_path: Path,
    *,
    dataset_version_id: str,
    feature_refs: Sequence[str],
) -> tuple[dict[str, str], ...] | str:
    if not registry_path.is_file():
        return "local FeatureStore registry is absent"
    query = """
        SELECT feature_version_id, feature_request_id, partition_id
        FROM feature_registry_records
        WHERE dataset_version_id = ?
          AND lifecycle_state != 'DEPRECATED'
    """
    params: list[str] = [dataset_version_id]
    if feature_refs:
        placeholders = ",".join("?" for _ in feature_refs)
        query += f" AND feature_version_id IN ({placeholders})"
        params.extend(feature_refs)
    query += " ORDER BY feature_version_id"
    try:
        with _sqlite_read_only(registry_path) as connection:
            rows = connection.execute(query, params).fetchall()
    except (OSError, sqlite3.Error) as exc:
        return f"local FeatureStore registry could not be read: {exc}"
    return tuple({key: str(row[key]) for key in row.keys()} for row in rows)


def _label_registry_rows(
    registry_path: Path,
    *,
    dataset_version_id: str,
    label_refs: Sequence[str],
) -> tuple[dict[str, str], ...] | str:
    if not registry_path.is_file():
        return "local LabelStore registry is absent"
    query = """
        SELECT label_version_id, label_spec_id, partition_id
        FROM label_registry_records
        WHERE dataset_version_id = ?
          AND lifecycle_state != 'DEPRECATED'
    """
    params: list[str] = [dataset_version_id]
    if label_refs:
        placeholders = ",".join("?" for _ in label_refs)
        query += f" AND label_version_id IN ({placeholders})"
        params.extend(label_refs)
    query += " ORDER BY label_version_id"
    try:
        with _sqlite_read_only(registry_path) as connection:
            rows = connection.execute(query, params).fetchall()
    except (OSError, sqlite3.Error) as exc:
        return f"local LabelStore registry could not be read: {exc}"
    return tuple({key: str(row[key]) for key in row.keys()} for row in rows)


def _sqlite_read_only(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _partition_id(
    config: SmokeConfig,
    feature_rows: Sequence[Mapping[str, str]],
    label_rows: Sequence[Mapping[str, str]],
) -> str | None:
    if config.partition_scope is not None:
        value = config.partition_scope.get("partition_id") or config.partition_scope.get("id")
        return str(value) if value else None
    if feature_rows:
        return feature_rows[0].get("partition_id")
    if label_rows:
        return label_rows[0].get("partition_id")
    return None


def _lifecycle_state(config: SmokeConfig, dataset_version: DatasetVersion) -> str:
    value = config.dataset_lifecycle_state or getattr(dataset_version, "lifecycle_state", None)
    return str(value or "VERSIONED").strip().upper()


def _warning_result(
    config: SmokeConfig,
    warning_reason: str,
    *,
    dataset_version_id: str | None = None,
    feature_pack_refs: Sequence[str] = (),
    label_pack_refs: Sequence[str] = (),
    entry_status: str | None = None,
    input_resolution_status: str | None = None,
) -> RuntimeSmokeResult:
    return RuntimeSmokeResult(
        status=RuntimeSmokeStatus.PASS_WITH_WARNINGS,
        run_id=config.run_id,
        operator_command=config.operator_command,
        real_dataset_version_smoke_ran=False,
        warning_reason=warning_reason,
        dataset_version_id=dataset_version_id or config.dataset_version_id,
        feature_pack_refs=tuple(feature_pack_refs or config.feature_pack_refs),
        label_pack_refs=tuple(label_pack_refs or config.label_pack_refs),
        entry_status=entry_status,
        input_resolution_status=input_resolution_status,
        limitations=(
            "CI-safe absence path; no local real DatasetVersion smoke was fabricated.",
            "Provide ALPHA_DATA_ROOT and accepted Feature/Label handles to run the smoke.",
            "No external provider call or raw provider file read was performed.",
        ),
    )


def _reason_text(prefix: str, reasons: Sequence[Any]) -> str:
    if not reasons:
        return prefix
    return prefix + ": " + "; ".join(
        f"{getattr(reason, 'code', 'reason')}={getattr(reason, 'message', reason)}"
        for reason in reasons
    )


def _hash_from_mapping(value: Mapping[str, object]) -> str:
    if not value:
        return governance_content_hash({"dataset_reproducibility_hashes": "absent"})
    return governance_content_hash(cast(JsonValue, dict(value)))


def _parse_ts(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def _max_ts(*values: str) -> datetime:
    return max(_parse_ts(value) for value in values)


def _csv(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _json_mapping_env(value: str | None, *, default: Mapping[str, Any]) -> Mapping[str, Any]:
    if not value:
        return dict(default)
    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return dict(default)
    if not isinstance(payload, Mapping):
        return dict(default)
    return dict(payload)


def main() -> int:
    """CLI entry point for ``python -m alpha_system.runtime.smoke``."""

    result = run_real_dataset_version_smoke()
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "OPERATOR_COMMAND_TEMPLATE",
    "RuntimeSmokeResult",
    "RuntimeSmokeStatus",
    "SmokeConfig",
    "main",
    "run_real_dataset_version_smoke",
]
