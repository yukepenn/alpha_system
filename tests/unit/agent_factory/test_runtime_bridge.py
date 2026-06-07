from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest

from alpha_system.agent_factory import runtime_bridge
from alpha_system.agent_factory.runtime_bridge import (
    ADMISSIBLE_DATASET_VERSION_STATES,
    DATASET_RESOLUTION_GATE,
    adapt_runtime_run_summary,
    adapt_runtime_tool_result,
)
from alpha_system.agent_factory.tools.results import AgentToolResult, AgentToolStatus
from alpha_system.runtime.contracts.run_record import RuntimeArtifactRef
from alpha_system.runtime.decisions.records import RejectionReasonRecord
from alpha_system.runtime.decisions.states import RuntimeDecisionState
from alpha_system.runtime.tool_results import (
    RuntimeCostSummary,
    RuntimeDiagnosticsSummary,
    RuntimeRunSummary,
    RuntimeToolResult,
    RuntimeVersionIds,
)

ROLE_ID = "diagnostics_runner"
REQUEST_ID = "request:runtime_bridge_unit"
ALPHA_SPEC_ID = "alpha_spec:bounded_seed"
STUDY_SPEC_ID = "study_spec:bounded_seed"
DATASET_VERSION_ID = "dsv_synthetic_feature_label_fixture_v1"
FEATURE_PACK_ID = "feature_pack:seed_ohlcv"
LABEL_PACK_ID = "label_pack:fixed_horizon_seed"
RUNTIME_RUN_ID = "runtime_run:bridge_unit"
REGISTRY_PATH = "registry_fixture"
_DEFAULT_COST = object()


@dataclass(frozen=True, slots=True)
class _ResolvedDatasetVersion:
    dataset_version_id: str = DATASET_VERSION_ID
    lifecycle_state: str = "VERSIONED"


def test_runtime_tool_result_maps_to_agent_tool_result_with_fidelity() -> None:
    calls: list[tuple[object, object]] = []

    agent_result = adapt_runtime_tool_result(
        _runtime_result(),
        role=ROLE_ID,
        request_id=REQUEST_ID,
        alpha_spec_id=ALPHA_SPEC_ID,
        study_spec_id=STUDY_SPEC_ID,
        registry_path=REGISTRY_PATH,
        dataset_version_resolver=_recording_resolver(calls),
    )

    assert isinstance(agent_result, AgentToolResult)
    assert agent_result.status is AgentToolStatus.OK
    assert agent_result.role == ROLE_ID
    assert agent_result.request_id == REQUEST_ID
    assert agent_result.alpha_spec_id == ALPHA_SPEC_ID
    assert agent_result.study_spec_id == STUDY_SPEC_ID
    assert agent_result.runtime_run_id == RUNTIME_RUN_ID
    assert agent_result.dataset_version_id == DATASET_VERSION_ID
    assert agent_result.feature_pack_refs == (FEATURE_PACK_ID,)
    assert agent_result.label_pack_refs == (LABEL_PACK_ID,)
    assert agent_result.next_required_gate == "statistical_review"
    assert agent_result.rejection_reasons == ()
    assert agent_result.limitations == ("synthetic fixture summary only",)
    assert "coverage_summary" in (agent_result.diagnostics_summary or "")
    assert "cost_summary=" in (agent_result.cost_summary or "")
    assert calls == [(REGISTRY_PATH, DATASET_VERSION_ID)]


def test_runtime_run_summary_maps_equivalently() -> None:
    summary = RuntimeRunSummary.from_tool_result(_runtime_result())

    agent_result = adapt_runtime_run_summary(
        summary,
        role=ROLE_ID,
        request_id=REQUEST_ID,
        alpha_spec_id=ALPHA_SPEC_ID,
        study_spec_id=STUDY_SPEC_ID,
        registry_path=REGISTRY_PATH,
        dataset_lifecycle_state="READY_FOR_RESEARCH",
        dataset_version_resolver=lambda _path, _id: _ResolvedDatasetVersion(
            lifecycle_state="READY_FOR_RESEARCH"
        ),
    )

    assert agent_result.status is AgentToolStatus.OK
    assert agent_result.runtime_run_id == RUNTIME_RUN_ID
    assert agent_result.dataset_version_id == DATASET_VERSION_ID
    assert agent_result.feature_pack_refs == (FEATURE_PACK_ID,)
    assert agent_result.label_pack_refs == (LABEL_PACK_ID,)
    assert agent_result.next_required_gate == "statistical_review"


@pytest.mark.parametrize(
    ("runtime_status", "agent_status"),
    [
        (RuntimeDecisionState.BLOCKED, AgentToolStatus.BLOCKED),
        (RuntimeDecisionState.REJECTED, AgentToolStatus.REJECTED),
        (RuntimeDecisionState.INCONCLUSIVE, AgentToolStatus.INCONCLUSIVE),
    ],
)
def test_non_success_runtime_outcomes_preserve_reasons_and_blocking_findings(
    runtime_status: RuntimeDecisionState,
    agent_status: AgentToolStatus,
) -> None:
    agent_result = adapt_runtime_tool_result(
        _runtime_result(
            status=runtime_status,
            rejection_reasons=(_rejection_reason(runtime_status),),
        ),
        role=ROLE_ID,
        request_id=REQUEST_ID,
        alpha_spec_id=ALPHA_SPEC_ID,
        study_spec_id=STUDY_SPEC_ID,
        registry_path=REGISTRY_PATH,
        dataset_version_resolver=_resolver(),
    )

    assert agent_result.status is agent_status
    assert "bridge fixture reason" in agent_result.rejection_reasons[0]
    assert "bridge fixture reason" in agent_result.blocking_findings[0]
    assert agent_result.next_required_gate == "statistical_review"


def test_optional_fields_degrade_without_crashing() -> None:
    agent_result = adapt_runtime_tool_result(
        _runtime_result(
            diagnostics_summary=RuntimeDiagnosticsSummary(),
            cost_summary=None,
            artifacts=(),
        ),
        role=ROLE_ID,
        request_id=REQUEST_ID,
        alpha_spec_id=ALPHA_SPEC_ID,
        study_spec_id=STUDY_SPEC_ID,
        registry_path=REGISTRY_PATH,
        dataset_version_resolver=_resolver(),
    )

    assert agent_result.status is AgentToolStatus.OK
    assert agent_result.cost_summary is None
    assert agent_result.artifacts == ()
    assert agent_result.limitations == ()
    assert agent_result.diagnostics_summary == (
        'diagnostics_summary={"coverage_summary":{},"quality_summary":{},"report_refs":[]}'
    )


def test_agent_result_rejects_raw_or_heavy_runtime_payload_markers() -> None:
    raw_reason_result = _runtime_result(
        status=RuntimeDecisionState.BLOCKED,
        rejection_reasons=(
            _rejection_reason(
                RuntimeDecisionState.BLOCKED,
                message="raw bars included in a forbidden fixture",
            ),
        ),
    )

    with pytest.raises(ValueError, match="forbidden raw/heavy payload marker"):
        adapt_runtime_tool_result(
            raw_reason_result,
            role=ROLE_ID,
            request_id=REQUEST_ID,
            alpha_spec_id=ALPHA_SPEC_ID,
            study_spec_id=STUDY_SPEC_ID,
            registry_path=REGISTRY_PATH,
            dataset_version_resolver=_resolver(),
        )


def test_bridge_imports_runtime_contracts_and_runtime_source_is_not_bridge_path() -> None:
    assert runtime_bridge.RuntimeToolResult is RuntimeToolResult
    assert runtime_bridge.RuntimeRunSummary is RuntimeRunSummary

    bridge_path = Path(runtime_bridge.__file__).as_posix()
    runtime_contract_path = Path(RuntimeToolResult.__module__.replace(".", "/")).as_posix()
    assert "src/alpha_system/runtime/" not in bridge_path
    assert runtime_contract_path == "alpha_system/runtime/tool_results"

    bridge_source = Path(runtime_bridge.__file__).read_text(encoding="utf-8")
    assert "from alpha_system.runtime.tool_results import RuntimeRunSummary" in bridge_source
    assert "RuntimeToolResult" in bridge_source
    assert "class RuntimeToolResult" not in bridge_source
    assert "class RuntimeRunSummary" not in bridge_source


def test_resolution_boundary_uses_resolve_dataset_version_and_admissible_states() -> None:
    calls: list[tuple[object, object]] = []

    result = adapt_runtime_tool_result(
        _runtime_result(),
        role=ROLE_ID,
        request_id=REQUEST_ID,
        alpha_spec_id=ALPHA_SPEC_ID,
        study_spec_id=STUDY_SPEC_ID,
        registry_path=REGISTRY_PATH,
        dataset_lifecycle_state="READY_FOR_RESEARCH",
        dataset_version_resolver=_recording_resolver(calls),
    )

    assert result.status is AgentToolStatus.OK
    assert calls == [(REGISTRY_PATH, DATASET_VERSION_ID)]
    assert ADMISSIBLE_DATASET_VERSION_STATES == frozenset({"VERSIONED", "READY_FOR_RESEARCH"})

    blocked = adapt_runtime_tool_result(
        _runtime_result(),
        role=ROLE_ID,
        request_id=REQUEST_ID,
        alpha_spec_id=ALPHA_SPEC_ID,
        study_spec_id=STUDY_SPEC_ID,
        registry_path=REGISTRY_PATH,
        dataset_lifecycle_state="DRAFT",
        dataset_version_resolver=_resolver(),
    )

    assert blocked.status is AgentToolStatus.BLOCKED
    assert blocked.next_required_gate == DATASET_RESOLUTION_GATE
    assert "inadmissible_dataset_lifecycle_state" in blocked.rejection_reasons[0]
    assert "inadmissible_dataset_lifecycle_state" in blocked.blocking_findings[0]


def test_missing_dataset_resolution_blocks_without_runtime_failure() -> None:
    blocked = adapt_runtime_tool_result(
        _runtime_result(),
        role=ROLE_ID,
        request_id=REQUEST_ID,
        alpha_spec_id=ALPHA_SPEC_ID,
        study_spec_id=STUDY_SPEC_ID,
        registry_path=REGISTRY_PATH,
        dataset_version_resolver=lambda _path, _id: None,
    )

    assert blocked.status is AgentToolStatus.BLOCKED
    assert blocked.next_required_gate == DATASET_RESOLUTION_GATE
    assert "dataset_version_not_found" in blocked.rejection_reasons[0]
    assert blocked.runtime_run_id == RUNTIME_RUN_ID


def _runtime_result(
    *,
    status: RuntimeDecisionState = RuntimeDecisionState.DIAGNOSTICS_COMPLETE,
    diagnostics_summary: RuntimeDiagnosticsSummary | None = None,
    cost_summary: RuntimeCostSummary | None | object = _DEFAULT_COST,
    rejection_reasons: tuple[RejectionReasonRecord, ...] = (),
    artifacts: tuple[RuntimeArtifactRef, ...] | None = None,
) -> RuntimeToolResult:
    return RuntimeToolResult(
        status=status,
        run_id=RUNTIME_RUN_ID,
        version_ids=RuntimeVersionIds(
            dataset_version_id=DATASET_VERSION_ID,
            feature_pack_ids=(FEATURE_PACK_ID,),
            label_pack_ids=(LABEL_PACK_ID,),
            code_version="code_version:unit",
            config_version="config_version:unit",
        ),
        diagnostics_summary=diagnostics_summary or _diagnostics_summary(),
        cost_summary=_cost_summary() if cost_summary is _DEFAULT_COST else cost_summary,
        rejection_reasons=rejection_reasons,
        artifacts=(_artifact_ref(),) if artifacts is None else artifacts,
        next_required_gate="statistical_review",
    )


def _diagnostics_summary() -> RuntimeDiagnosticsSummary:
    return RuntimeDiagnosticsSummary(
        report_refs=(
            {
                "report_id": "report:coverage",
                "report_hash": "hash:coverage",
                "report_kind": "coverage",
            },
        ),
        coverage_summary={"report_count": 1, "blocking_count": 0},
        quality_summary={"report_count": 1, "warning_count": 0},
        limitations=("synthetic fixture summary only",),
    )


def _cost_summary() -> RuntimeCostSummary:
    return RuntimeCostSummary(
        diagnostics_report_ref={
            "report_id": "report:cost",
            "report_hash": "hash:cost",
            "report_kind": "cost",
        },
        cost_model_version_id="cost_model:unit",
        profile_count=2,
        double_cost_profile_name="double_cost",
        double_cost_combined_cost_slippage_proxy="proxy_units_only",
    )


def _rejection_reason(
    state: RuntimeDecisionState,
    *,
    message: str = "bridge fixture reason",
) -> RejectionReasonRecord:
    return RejectionReasonRecord(
        code="blocked_by_policy" if state is RuntimeDecisionState.BLOCKED else "weak_diagnostics",
        message=message,
        decision_state=state,
        stage="diagnostics",
        source_code="bridge_fixture",
        source_id="bridge_fixture_source",
    )


def _artifact_ref() -> RuntimeArtifactRef:
    return RuntimeArtifactRef(
        artifact_id="artifact:diagnostics_summary",
        location="runtime/reports/diagnostics_summary",
        content_hash="hash:diagnostics_summary",
    )


def _resolver() -> Callable[[object, object], _ResolvedDatasetVersion]:
    return lambda _path, _id: _ResolvedDatasetVersion()


def _recording_resolver(
    calls: list[tuple[object, object]],
) -> Callable[[object, object], _ResolvedDatasetVersion]:
    def resolver(registry_path: object, dataset_version_id: object) -> _ResolvedDatasetVersion:
        calls.append((registry_path, dataset_version_id))
        return _ResolvedDatasetVersion(dataset_version_id=str(dataset_version_id))

    return resolver
