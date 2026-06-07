"""Adapt value-free Research Runtime outputs into Agent Factory tool results."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from alpha_system.agent_factory.tools.results import (
    MAX_RESULT_TEXT_LENGTH,
    MAX_SUMMARY_TEXT_LENGTH,
    AgentToolResult,
    AgentToolStatus,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.data.foundation.version_registry import resolve_dataset_version
from alpha_system.runtime.decisions.states import RuntimeDecisionState
from alpha_system.runtime.tool_results import RuntimeRunSummary, RuntimeToolResult

ADMISSIBLE_DATASET_VERSION_STATES: frozenset[str] = frozenset({"VERSIONED", "READY_FOR_RESEARCH"})
DATASET_RESOLUTION_GATE = "resolve_dataset_version"

RuntimeResult = RuntimeToolResult | RuntimeRunSummary
DatasetVersionResolver = Callable[[str | Path, object], object | None]


class RuntimeBridgeError(ValueError):
    """Raised when a runtime bridge input cannot be adapted safely."""


def adapt_runtime_tool_result(
    result: RuntimeToolResult,
    *,
    role: str,
    request_id: str,
    alpha_spec_id: str,
    study_spec_id: str,
    registry_path: str | Path,
    dataset_lifecycle_state: str | None = None,
    dataset_version_resolver: DatasetVersionResolver = resolve_dataset_version,
) -> AgentToolResult:
    """Adapt one ``RuntimeToolResult`` into a value-free ``AgentToolResult``."""

    if not isinstance(result, RuntimeToolResult):
        raise TypeError("result must be a RuntimeToolResult")
    return adapt_runtime_result(
        result,
        role=role,
        request_id=request_id,
        alpha_spec_id=alpha_spec_id,
        study_spec_id=study_spec_id,
        registry_path=registry_path,
        dataset_lifecycle_state=dataset_lifecycle_state,
        dataset_version_resolver=dataset_version_resolver,
    )


def adapt_runtime_run_summary(
    summary: RuntimeRunSummary,
    *,
    role: str,
    request_id: str,
    alpha_spec_id: str,
    study_spec_id: str,
    registry_path: str | Path,
    dataset_lifecycle_state: str | None = None,
    dataset_version_resolver: DatasetVersionResolver = resolve_dataset_version,
) -> AgentToolResult:
    """Adapt one ``RuntimeRunSummary`` into a value-free ``AgentToolResult``."""

    if not isinstance(summary, RuntimeRunSummary):
        raise TypeError("summary must be a RuntimeRunSummary")
    return adapt_runtime_result(
        summary,
        role=role,
        request_id=request_id,
        alpha_spec_id=alpha_spec_id,
        study_spec_id=study_spec_id,
        registry_path=registry_path,
        dataset_lifecycle_state=dataset_lifecycle_state,
        dataset_version_resolver=dataset_version_resolver,
    )


def adapt_runtime_result(
    result: RuntimeResult,
    *,
    role: str,
    request_id: str,
    alpha_spec_id: str,
    study_spec_id: str,
    registry_path: str | Path,
    dataset_lifecycle_state: str | None = None,
    dataset_version_resolver: DatasetVersionResolver = resolve_dataset_version,
) -> AgentToolResult:
    """Adapt a runtime result or summary after accepted DatasetVersion resolution."""

    if not isinstance(result, (RuntimeToolResult, RuntimeRunSummary)):
        raise TypeError("result must be a RuntimeToolResult or RuntimeRunSummary")
    _require_bound_spec_ids(alpha_spec_id=alpha_spec_id, study_spec_id=study_spec_id)

    dataset_version_id = result.version_ids.dataset_version_id
    dataset_blocker = _dataset_admissibility_blocker(
        registry_path=registry_path,
        dataset_version_id=dataset_version_id,
        dataset_lifecycle_state=dataset_lifecycle_state,
        dataset_version_resolver=dataset_version_resolver,
    )
    if dataset_blocker is not None:
        return _build_agent_result(
            result,
            status=AgentToolStatus.BLOCKED,
            role=role,
            request_id=request_id,
            alpha_spec_id=alpha_spec_id,
            study_spec_id=study_spec_id,
            diagnostics_summary=dataset_blocker,
            extra_rejection_reasons=(dataset_blocker,),
            extra_blocking_findings=(dataset_blocker,),
            next_required_gate=DATASET_RESOLUTION_GATE,
        )

    return _build_agent_result(
        result,
        status=_agent_status_from_runtime(result.status),
        role=role,
        request_id=request_id,
        alpha_spec_id=alpha_spec_id,
        study_spec_id=study_spec_id,
        diagnostics_summary=None,
        extra_rejection_reasons=(),
        extra_blocking_findings=(),
        next_required_gate=result.next_required_gate,
    )


def _require_bound_spec_ids(*, alpha_spec_id: str, study_spec_id: str) -> None:
    if not isinstance(alpha_spec_id, str) or not alpha_spec_id.strip():
        raise RuntimeBridgeError("alpha_spec_id is required before adapting runtime diagnostics")
    if not isinstance(study_spec_id, str) or not study_spec_id.strip():
        raise RuntimeBridgeError("study_spec_id is required before adapting runtime diagnostics")


def _dataset_admissibility_blocker(
    *,
    registry_path: str | Path,
    dataset_version_id: str,
    dataset_lifecycle_state: str | None,
    dataset_version_resolver: DatasetVersionResolver,
) -> str | None:
    try:
        resolved = dataset_version_resolver(registry_path, dataset_version_id)
    except (DataFoundationValidationError, OSError, ValueError) as exc:
        return _bounded_text(
            (
                "dataset_version_resolution_failed: "
                "resolve_dataset_version could not resolve the DatasetVersion; "
                f"reason={exc}"
            ),
            max_length=MAX_RESULT_TEXT_LENGTH,
        )

    if resolved is None:
        return (
            "dataset_version_not_found: resolve_dataset_version returned no DatasetVersion record"
        )

    resolved_id = getattr(resolved, "dataset_version_id", dataset_version_id)
    if resolved_id != dataset_version_id:
        return _bounded_text(
            (
                "dataset_version_mismatch: resolve_dataset_version returned "
                f"{resolved_id!s} for requested {dataset_version_id}"
            ),
            max_length=MAX_RESULT_TEXT_LENGTH,
        )

    lifecycle_state = dataset_lifecycle_state
    if lifecycle_state is None:
        lifecycle_state = getattr(resolved, "lifecycle_state", None)
    if not isinstance(lifecycle_state, str) or not lifecycle_state.strip():
        return (
            "missing_dataset_lifecycle_state: DatasetVersion lifecycle state is "
            "required and must be VERSIONED or READY_FOR_RESEARCH"
        )

    normalized_state = lifecycle_state.strip().upper()
    if normalized_state not in ADMISSIBLE_DATASET_VERSION_STATES:
        allowed = ",".join(sorted(ADMISSIBLE_DATASET_VERSION_STATES))
        return (
            "inadmissible_dataset_lifecycle_state: DatasetVersion lifecycle state "
            f"{normalized_state} is not one of {allowed}"
        )
    return None


def _build_agent_result(
    result: RuntimeResult,
    *,
    status: AgentToolStatus,
    role: str,
    request_id: str,
    alpha_spec_id: str,
    study_spec_id: str,
    diagnostics_summary: str | None,
    extra_rejection_reasons: tuple[str, ...],
    extra_blocking_findings: tuple[str, ...],
    next_required_gate: str,
) -> AgentToolResult:
    reason_strings = _rejection_reason_strings(result)
    blocking_findings = (
        tuple(
            _bounded_text(f"blocking:{reason}", max_length=MAX_RESULT_TEXT_LENGTH)
            for reason in reason_strings
        )
        if status
        in {
            AgentToolStatus.BLOCKED,
            AgentToolStatus.REJECTED,
            AgentToolStatus.INCONCLUSIVE,
        }
        else ()
    )
    diagnostics_text = diagnostics_summary or _diagnostics_summary_text(result)

    return AgentToolResult(
        status=status,
        role=role,
        request_id=request_id,
        alpha_spec_id=alpha_spec_id,
        study_spec_id=study_spec_id,
        dataset_version_id=result.version_ids.dataset_version_id,
        feature_pack_refs=tuple(result.version_ids.feature_pack_ids),
        label_pack_refs=tuple(result.version_ids.label_pack_ids),
        runtime_run_id=result.run_id,
        diagnostics_summary=diagnostics_text,
        cost_summary=_cost_summary_text(result),
        rejection_reasons=_dedupe((*reason_strings, *extra_rejection_reasons)),
        blocking_findings=_dedupe((*blocking_findings, *extra_blocking_findings)),
        next_required_gate=next_required_gate,
        artifacts=_artifact_ref_strings(result),
        limitations=_dedupe(tuple(result.diagnostics_summary.limitations)),
    )


def _agent_status_from_runtime(status: RuntimeDecisionState) -> AgentToolStatus:
    if status is RuntimeDecisionState.BLOCKED:
        return AgentToolStatus.BLOCKED
    if status is RuntimeDecisionState.REJECTED:
        return AgentToolStatus.REJECTED
    if status is RuntimeDecisionState.INCONCLUSIVE:
        return AgentToolStatus.INCONCLUSIVE
    return AgentToolStatus.OK


def _diagnostics_summary_text(result: RuntimeResult) -> str:
    summary = result.diagnostics_summary
    report_refs = tuple(_report_ref_string(ref) for ref in summary.report_refs)
    payload = {
        "report_refs": report_refs,
        "coverage_summary": _json_from_text(summary.coverage_summary_json),
        "quality_summary": _json_from_text(summary.quality_summary_json),
    }
    return _bounded_summary("diagnostics_summary=" + _canonical_json(payload))


def _cost_summary_text(result: RuntimeResult) -> str | None:
    if result.cost_summary is None:
        return None
    return _bounded_summary("cost_summary=" + _canonical_json(result.cost_summary.to_dict()))


def _rejection_reason_strings(result: RuntimeResult) -> tuple[str, ...]:
    return tuple(
        _bounded_text(
            (
                f"reason[{index}]:code={reason.code.value};"
                f"state={reason.decision_state.value};"
                f"stage={reason.stage};"
                f"source={reason.source_code};"
                f"message={reason.message}"
            ),
            max_length=MAX_RESULT_TEXT_LENGTH,
        )
        for index, reason in enumerate(result.rejection_reasons)
    )


def _artifact_ref_strings(result: RuntimeResult) -> tuple[str, ...]:
    return tuple(
        _bounded_text(
            (
                f"artifact_ref[{index}]:id={artifact.artifact_id};"
                f"location={artifact.location};"
                f"hash={artifact.content_hash}"
            ),
            max_length=MAX_RESULT_TEXT_LENGTH,
        )
        for index, artifact in enumerate(result.artifacts)
    )


def _report_ref_string(ref: Any) -> str:
    return _bounded_text(
        f"report_ref:id={ref.report_id};kind={ref.report_kind};hash={ref.report_hash}",
        max_length=MAX_RESULT_TEXT_LENGTH,
    )


def _json_from_text(value: str) -> object:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return {"summary_json_sha256": hashlib.sha256(value.encode("utf-8")).hexdigest()}


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _bounded_summary(value: str) -> str:
    return _bounded_text(value, max_length=MAX_SUMMARY_TEXT_LENGTH)


def _bounded_text(value: str, *, max_length: int) -> str:
    if len(value) <= max_length:
        return value
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    prefix = value[: max_length - 80].rstrip(";:, ")
    return f"{prefix};summary_sha256={digest}"


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


__all__ = [
    "ADMISSIBLE_DATASET_VERSION_STATES",
    "DATASET_RESOLUTION_GATE",
    "DatasetVersionResolver",
    "RuntimeBridgeError",
    "RuntimeResult",
    "adapt_runtime_result",
    "adapt_runtime_run_summary",
    "adapt_runtime_tool_result",
]
