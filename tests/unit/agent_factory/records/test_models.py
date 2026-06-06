from __future__ import annotations

from collections.abc import Callable
from dataclasses import FrozenInstanceError, fields, replace

import pytest

from alpha_system.agent_factory.records import (
    AgentAuditLog,
    AgentDecisionClassification,
    AgentDecisionRecord,
    AgentHandoff,
    AgentPermissionVersion,
    AgentPromptVersion,
    AgentRoleVersion,
    AgentRunRecord,
    AgentRunStatus,
    ToolInvocationRecord,
)
from alpha_system.agent_factory.separation.enforcement import SeparationRuleResult
from alpha_system.agent_factory.tools.results import AgentToolResult, AgentToolStatus


def test_record_contracts_import_and_round_trip() -> None:
    records = (
        valid_run_record(),
        valid_decision_record(),
        valid_tool_invocation_record(),
        valid_handoff(),
        valid_audit_log(),
        valid_prompt_version(),
        valid_role_version(),
        valid_permission_version(),
    )

    for record in records:
        payload = {field.name: getattr(record, field.name) for field in fields(record)}
        assert type(record)(**payload) == record


def test_records_are_immutable() -> None:
    record = valid_run_record()

    with pytest.raises(FrozenInstanceError):
        record.summary = "changed"  # type: ignore[misc]


def test_agent_handoff_links_decision_to_tool_invocation_to_spec_ids() -> None:
    handoff = valid_handoff()

    assert handoff.decision_ref == "agent_decision:diagnostics_request"
    assert handoff.tool_invocation_refs == ("tool_invocation:runtime_diagnostics",)
    assert handoff.spec_refs == (
        "alpha_spec:seed",
        "study_spec:seed",
        "dataset_version:es_2024_seed",
        "runtime_run:seed_contract",
        "feature_pack:seed_ohlcv",
        "label_pack:fixed_horizon_seed",
    )
    assert handoff.tool_invocations[0].result_status is AgentToolStatus.OK


def test_agent_handoff_rejects_missing_tool_linkage_to_spec_ids() -> None:
    invocation = valid_tool_invocation_record(
        result=valid_tool_result(dataset_version_id="dataset_version:different")
    )

    with pytest.raises(ValueError, match="dataset_version_id"):
        valid_handoff(tool_invocations=(invocation,))


def test_tool_invocation_uses_allowed_tool_registry_and_matching_result() -> None:
    record = valid_tool_invocation_record()

    assert record.tool_name == "runtime.run_diagnostics"
    assert "runtime_run:seed_contract" in record.result_refs

    with pytest.raises(PermissionError):
        valid_tool_invocation_record(caller_role_id="hypothesis_scout")

    with pytest.raises(ValueError, match="request_id"):
        valid_tool_invocation_record(result=valid_tool_result(request_id="request:other"))


def test_version_records_support_prompt_role_and_permission_versioning() -> None:
    prompt = valid_prompt_version()
    role = valid_role_version()
    permission = valid_permission_version()
    audit_log = valid_audit_log(
        version_refs=(
            prompt.prompt_version_id,
            role.role_version_id,
            permission.permission_version_id,
        )
    )

    assert prompt.role_id == "diagnostics_runner"
    assert role.role_contract_ref == "role_contract:diagnostics_runner"
    assert permission.permission_matrix_ref == "permission_matrix:diagnostics_runner"
    assert audit_log.version_refs == (
        "prompt_version:diagnostics_runner_v1",
        "role_version:diagnostics_runner_v1",
        "permission_version:diagnostics_runner_v1",
    )


def test_agent_audit_log_requires_ordered_activity_refs() -> None:
    audit_log = valid_audit_log()

    with pytest.raises(ValueError, match="missing"):
        replace(audit_log, ordered_activity_refs=("agent_run:diagnostics_seed",))

    appended = replace(
        audit_log,
        version_refs=("prompt_version:diagnostics_runner_v1",),
    ).append_ordered_ref("prompt_version:diagnostics_runner_v1")
    assert appended.ordered_activity_refs[-1] == "prompt_version:diagnostics_runner_v1"


@pytest.mark.parametrize(
    ("factory", "field_name", "bad_value"),
    [
        (
            lambda: valid_run_record(),
            "summary",
            "raw_payload=data/raw/es_ticks.parquet",
        ),
        (
            lambda: valid_decision_record(),
            "rationale_summary",
            "embedded value_array=[1,2,3]",
        ),
        (
            lambda: valid_tool_invocation_record(),
            "input_refs",
            ("raw_payload:provider_blob",),
        ),
        (
            lambda: valid_tool_invocation_record(),
            "input_refs",
            ("artifact:diagnostics.arrow",),
        ),
        (
            lambda: valid_handoff(),
            "feature_pack_refs",
            ("feature_pack:seed_ohlcv", "feature_pack:seed_ohlcv"),
        ),
        (
            lambda: valid_prompt_version(),
            "change_summary",
            "provider_payload stored as binary blob",
        ),
        (
            lambda: valid_role_version(),
            "role_contract_ref",
            "role_contract:dataframe_payload",
        ),
        (
            lambda: valid_permission_version(),
            "permission_matrix_ref",
            "permission_matrix:local.sqlite",
        ),
    ],
)
def test_records_reject_raw_heavy_payloads_and_embedded_value_arrays(
    factory: Callable[[], object],
    field_name: str,
    bad_value: object,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        replace(factory(), **{field_name: bad_value})


def test_records_reject_mutable_or_binary_payloads() -> None:
    with pytest.raises(TypeError):
        replace(valid_audit_log(), ordered_activity_refs=["agent_run:diagnostics_seed"])

    with pytest.raises(TypeError):
        replace(valid_run_record(), limitations=(b"raw-bytes",))


def valid_run_record() -> AgentRunRecord:
    return AgentRunRecord(
        run_id="agent_run:diagnostics_seed",
        role_id="diagnostics_runner",
        request_id="request:diagnostics_seed",
        status=AgentRunStatus.COMPLETED,
        queue_ref="queue:synthetic_batch",
        task_ref="research_task:seed_scope",
        task_status="DIAGNOSTICS_COMPLETE",
        started_at_ref="time_ref:started",
        ended_at_ref="time_ref:ended",
        summary="Diagnostics runner recorded refs and summaries only.",
        limitations=("contract_only",),
    )


def valid_decision_record() -> AgentDecisionRecord:
    return AgentDecisionRecord(
        decision_id="agent_decision:diagnostics_request",
        run_id="agent_run:diagnostics_seed",
        role_id="diagnostics_runner",
        request_id="request:diagnostics_seed",
        decision_kind="request_runtime_diagnostics",
        classification=AgentDecisionClassification.ALLOWED,
        rationale_summary="Inputs were bounded by task refs and accepted dataset refs.",
        next_required_gate="statistical_reviewer_independent_review",
        separation_results=(
            SeparationRuleResult.passed(
                "implementer_reviewer_separation",
                ("diagnostics_runner", "statistical_reviewer"),
                "diagnostics_runner and statistical_reviewer are independent roles",
            ),
        ),
    )


def valid_tool_invocation_record(
    *,
    caller_role_id: str = "diagnostics_runner",
    result: AgentToolResult | None = None,
) -> ToolInvocationRecord:
    return ToolInvocationRecord(
        invocation_id="tool_invocation:runtime_diagnostics",
        tool_name="runtime.run_diagnostics",
        caller_role_id=caller_role_id,
        request_id="request:diagnostics_seed",
        started_at_ref="time_ref:tool_started",
        ended_at_ref="time_ref:tool_ended",
        input_refs=(
            "study_spec:seed",
            "dataset_version:es_2024_seed",
        ),
        result=result if result is not None else valid_tool_result(role=caller_role_id),
        limitations=("structured_result_only",),
    )


def valid_tool_result(
    *,
    role: str = "diagnostics_runner",
    request_id: str = "request:diagnostics_seed",
    dataset_version_id: str = "dataset_version:es_2024_seed",
) -> AgentToolResult:
    return AgentToolResult(
        status=AgentToolStatus.OK,
        role=role,
        request_id=request_id,
        alpha_spec_id="alpha_spec:seed",
        study_spec_id="study_spec:seed",
        dataset_version_id=dataset_version_id,
        feature_pack_refs=("feature_pack:seed_ohlcv",),
        label_pack_refs=("label_pack:fixed_horizon_seed",),
        runtime_run_id="runtime_run:seed_contract",
        diagnostics_summary="status counts and blocker refs only",
        cost_summary="cost assumption refs only",
        rejection_reasons=(),
        blocking_findings=(),
        next_required_gate="statistical_reviewer_independent_review",
        artifacts=("artifact_ref:diagnostics_summary",),
        limitations=("structured_result_only",),
    )


def valid_handoff(
    *,
    tool_invocations: tuple[ToolInvocationRecord, ...] | None = None,
) -> AgentHandoff:
    return AgentHandoff(
        handoff_id="agent_handoff:diagnostics_to_review",
        from_role_id="diagnostics_runner",
        to_role_id="statistical_reviewer",
        request_id="request:diagnostics_seed",
        decision=valid_decision_record(),
        tool_invocations=tool_invocations
        if tool_invocations is not None
        else (valid_tool_invocation_record(),),
        alpha_spec_id="alpha_spec:seed",
        study_spec_id="study_spec:seed",
        dataset_version_id="dataset_version:es_2024_seed",
        feature_pack_refs=("feature_pack:seed_ohlcv",),
        label_pack_refs=("label_pack:fixed_horizon_seed",),
        runtime_run_id="runtime_run:seed_contract",
        blocking_findings=(),
        next_required_gate="statistical_reviewer_independent_review",
        summary="Decision, tool invocation, and spec refs are linked for review.",
        limitations=("not_alpha_evidence", "contract_only"),
    )


def valid_audit_log(
    *,
    version_refs: tuple[str, ...] = (),
) -> AgentAuditLog:
    return AgentAuditLog(
        audit_log_id="agent_audit:diagnostics_seed",
        request_id="request:diagnostics_seed",
        run_refs=("agent_run:diagnostics_seed",),
        decision_refs=("agent_decision:diagnostics_request",),
        handoff_refs=("agent_handoff:diagnostics_to_review",),
        tool_invocation_refs=("tool_invocation:runtime_diagnostics",),
        version_refs=version_refs,
        ordered_activity_refs=(
            "agent_run:diagnostics_seed",
            "agent_decision:diagnostics_request",
            "tool_invocation:runtime_diagnostics",
            "agent_handoff:diagnostics_to_review",
        ),
        summary="Append-style refs make the lifecycle auditable.",
        limitations=("refs_only",),
    )


def valid_prompt_version() -> AgentPromptVersion:
    return AgentPromptVersion(
        prompt_version_id="prompt_version:diagnostics_runner_v1",
        role_id="diagnostics_runner",
        prompt_ref="prompt:diagnostics_runner",
        template_ref="template:diagnostics_runner",
        version_label="v1",
        change_summary="Initial prompt contract ref.",
        approved_by_ref="review:operator_prompt_review",
        effective_from_ref="time_ref:phase_p17",
        supersedes_prompt_version_id=None,
        limitations=("contracts_only",),
    )


def valid_role_version() -> AgentRoleVersion:
    return AgentRoleVersion(
        role_version_id="role_version:diagnostics_runner_v1",
        role_id="diagnostics_runner",
        role_contract_ref="role_contract:diagnostics_runner",
        version_label="v1",
        change_summary="Initial role contract ref.",
        approved_by_ref="review:operator_role_review",
        effective_from_ref="time_ref:phase_p17",
        supersedes_role_version_id=None,
        limitations=("contracts_only",),
    )


def valid_permission_version() -> AgentPermissionVersion:
    return AgentPermissionVersion(
        permission_version_id="permission_version:diagnostics_runner_v1",
        role_id="diagnostics_runner",
        permission_matrix_ref="permission_matrix:diagnostics_runner",
        version_label="v1",
        change_summary="Initial permission matrix ref.",
        approved_by_ref="review:operator_permission_review",
        effective_from_ref="time_ref:phase_p17",
        supersedes_permission_version_id=None,
        limitations=("contracts_only",),
    )
