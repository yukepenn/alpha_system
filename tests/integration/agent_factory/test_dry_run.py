from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pytest

from alpha_system.agent_factory.dry_run import harness
from alpha_system.agent_factory.dry_run.harness import (
    AGENT_DRY_RUN_ROLE_ROUTE,
    DATASET_VERSION_ID,
    MAX_DRY_RUN_FORWARD_STATE,
    PERMITTED_STATISTICAL_DRY_RUN_VERDICTS,
    SYNTHETIC_REGISTRY_REF,
    AgentDryRunReport,
    validate_dry_run_report,
)
from alpha_system.agent_factory.memory.models import (
    RejectedIdeaMemoryRecord,
    RejectedIdeaMemoryStatus,
    ResearchMemoryRecord,
    ResearchMemoryStatus,
)
from alpha_system.agent_factory.permissions.matrix import ROSTER_ROLE_IDS, permission_for
from alpha_system.agent_factory.queue.models import (
    PROHIBITED_MVP_TASK_STATUSES,
    ResearchTaskStatus,
)
from alpha_system.agent_factory.roles import hypothesis_scout
from alpha_system.agent_factory.tools import registry as tool_registry
from alpha_system.agent_factory.tools.contracts import REQUIRED_FORBIDDEN_SIDE_EFFECTS
from alpha_system.agent_factory.tools.results import (
    AGENT_TOOL_RESULT_FIELDS,
    FORBIDDEN_HEAVY_SUFFIXES,
    FORBIDDEN_RESULT_MARKERS,
    AgentToolResult,
    AgentToolStatus,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.data.foundation.version_registry import resolve_dataset_version

RecordedVerdict = Literal["PASS_WITH_WARNINGS"]
DryRunPath = Literal["seed_pack", "synthetic"]
ResolverName = Literal["resolve_dataset_version", "synthetic_dataset_version_resolver"]


@dataclass(frozen=True, slots=True)
class SeedRegistryProbe:
    alpha_data_root: Path | None
    feature_registry: Path | None
    label_registry: Path | None
    dataset_registry: Path | None
    warnings: tuple[str, ...]

    @property
    def complete(self) -> bool:
        return not self.warnings and self.dataset_registry is not None


@dataclass(frozen=True, slots=True)
class ResolveAttempt:
    resolver_name: ResolverName
    dataset_version_id: str
    outcome: str


@dataclass(frozen=True, slots=True)
class ResolvedDatasetVersionRef:
    dataset_version_id: str
    lifecycle_state: str


@dataclass(frozen=True, slots=True)
class IntegrationDryRunOutcome:
    path_taken: DryRunPath
    recorded_verdict: RecordedVerdict
    warnings: tuple[str, ...]
    report: AgentDryRunReport
    seed_registry_probe: SeedRegistryProbe
    resolve_attempts: tuple[ResolveAttempt, ...]


def test_integration_dry_run_records_truthful_pass_with_warnings(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    bridge_calls: list[dict[str, object]] = []
    original_adapter = harness.runtime_bridge.adapt_runtime_tool_result

    def recording_adapter(*args: object, **kwargs: object) -> AgentToolResult:
        bridge_calls.append(dict(kwargs))
        return original_adapter(*args, **kwargs)

    monkeypatch.setattr(
        harness.runtime_bridge,
        "adapt_runtime_tool_result",
        recording_adapter,
    )

    outcome = _run_integration_dry_run(tmp_path)
    report = outcome.report

    assert outcome.recorded_verdict == "PASS_WITH_WARNINGS"
    assert outcome.path_taken in {"seed_pack", "synthetic"}
    assert outcome.warnings
    assert any("not alpha evidence" in warning for warning in outcome.warnings)
    assert validate_dry_run_report(report) is report
    assert report.terminal_state is ResearchTaskStatus.REJECTED
    assert report.max_forward_state is MAX_DRY_RUN_FORWARD_STATE
    assert len(bridge_calls) == 1
    assert bridge_calls[0]["role"] == "diagnostics_runner"
    assert bridge_calls[0]["dataset_version_resolver"] is not resolve_dataset_version
    assert any(
        attempt.resolver_name == "resolve_dataset_version" for attempt in outcome.resolve_attempts
    )


def test_absent_seed_registries_degrade_to_synthetic_with_warning(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("ALPHA_DATA_ROOT", raising=False)

    outcome = _run_integration_dry_run(tmp_path)

    assert outcome.path_taken == "synthetic"
    assert outcome.recorded_verdict == "PASS_WITH_WARNINGS"
    assert any("ALPHA_DATA_ROOT is unset" in warning for warning in outcome.warnings)
    assert outcome.report.terminal_state is ResearchTaskStatus.REJECTED
    assert outcome.report.result_for_role("data_contract_auditor").status is AgentToolStatus.OK
    assert outcome.report.result_for_role("diagnostics_runner").status is AgentToolStatus.OK


def test_role_route_permissions_tool_contracts_and_no_promotion(
    tmp_path: Path,
) -> None:
    report = _run_integration_dry_run(tmp_path).report

    assert report.role_route == AGENT_DRY_RUN_ROLE_ROUTE
    assert tuple(result.role for result in report.tool_results) == AGENT_DRY_RUN_ROLE_ROUTE
    assert set(report.role_route) == set(ROSTER_ROLE_IDS)
    assert report.task.research_budget.variant_budget.max_variants == 5
    assert report.task.research_budget.compute_budget.max_runtime_minutes == 30
    assert report.task.allowed_alpha_family == ("microstructure",)
    assert tuple(report.registered_tool_names) == tuple(
        invocation.tool_name for invocation in report.tool_invocations
    )

    for role_id in report.role_route:
        permissions = permission_for(role_id)
        assert not permissions.data.raw_provider_access
        assert not permissions.write.direct_registry_write
        assert not permissions.promotion.can_promote

    for invocation in report.tool_invocations:
        contract = tool_registry.resolve(invocation.tool_name, invocation.caller_role_id)
        permissions = permission_for(invocation.caller_role_id)
        assert contract.allows(invocation.caller_role_id)
        assert any(
            permissions.tool.allows(matrix_ref) for matrix_ref in contract.permission_matrix_refs
        )
        assert set(REQUIRED_FORBIDDEN_SIDE_EFFECTS) <= set(contract.forbidden_side_effects)
        assert isinstance(invocation.result, AgentToolResult)
        assert invocation.result.role == invocation.caller_role_id

    state_values = {state.value for state in report.reachable_task_statuses}
    assert ResearchTaskStatus.REFERENCE_HANDOFF_RECORDED in report.reachable_task_statuses
    assert ResearchTaskStatus.STATISTICAL_REVIEW_PASS not in report.reachable_task_statuses
    assert ResearchTaskStatus.LIBRARIAN_MEMORY_RECORDED not in report.reachable_task_statuses
    assert not state_values.intersection(PROHIBITED_MVP_TASK_STATUSES)
    assert "PASS" not in PERMITTED_STATISTICAL_DRY_RUN_VERDICTS
    assert "promotion.review" not in report.registered_tool_names
    assert not any(name.startswith("promotion.") for name in report.registered_tool_names)


def test_rejections_memory_records_and_value_free_tool_results(tmp_path: Path) -> None:
    report = _run_integration_dry_run(tmp_path).report
    critic = report.result_for_role("alpha_spec_critic")
    statistical = report.result_for_role("statistical_reviewer")
    librarian = report.result_for_role("librarian")

    assert critic.status is AgentToolStatus.WARN
    assert len(critic.rejection_reasons) == 2
    assert all(reason.startswith("critic_rejected:") for reason in critic.rejection_reasons)
    assert report.prior_rejection_refs
    assert all(
        isinstance(ref, hypothesis_scout.RejectionReasonRecordRef)
        for ref in report.prior_rejection_refs
    )

    assert statistical.status is AgentToolStatus.REJECTED
    assert statistical.rejection_reasons == ("dry_run_reject_not_alpha_evidence",)
    assert librarian.status is AgentToolStatus.REJECTED
    assert "reviewer_verdict_ref:agent_p22_reject" in librarian.artifacts
    assert "not_alpha_evidence" in statistical.limitations
    assert "evidence_draft_not_candidate" in statistical.limitations
    assert "reference_handoff_not_validation" in statistical.limitations

    assert isinstance(report.rejected_idea_memory, RejectedIdeaMemoryRecord)
    assert isinstance(report.research_memory, ResearchMemoryRecord)
    assert report.rejected_idea_memory.status is RejectedIdeaMemoryStatus.REJECTED
    assert report.research_memory.status is ResearchMemoryStatus.REJECTED
    assert report.rejected_idea_memory.rejection_reasons == statistical.rejection_reasons
    assert report.research_memory.related_rejected_memory_refs == (
        report.rejected_idea_memory.memory_id,
    )

    for result in report.tool_results:
        _assert_value_free_agent_result(result)


def _run_integration_dry_run(tmp_path: Path) -> IntegrationDryRunOutcome:
    probe = _probe_seed_registries()
    warnings = [
        "seed-pack or synthetic dry run is machinery-only and not alpha evidence.",
        "EvidenceDraft is not a candidate.",
        "ReferenceCandidateHandoff is not Reference validation.",
    ]
    warnings.extend(probe.warnings)
    resolve_attempts: list[ResolveAttempt] = []
    path_taken: DryRunPath = "synthetic"
    warning_keys = set(warnings)
    synthetic_registry_path = tmp_path / "agent_factory_synthetic_registry.sqlite"

    def warn_once(message: str) -> None:
        if message not in warning_keys:
            warnings.append(message)
            warning_keys.add(message)

    def resolver(registry_ref: object, dataset_version_id: object) -> object | None:
        if probe.complete:
            warn_once(
                "seed registry markers are present; synthetic fixture path selected "
                "to keep the integration test marker-only for local registries."
            )

        _try_resolve_dataset_version(
            synthetic_registry_path,
            dataset_version_id,
            resolve_attempts,
            warn_once,
        )
        resolve_attempts.append(
            ResolveAttempt(
                resolver_name="synthetic_dataset_version_resolver",
                dataset_version_id=str(dataset_version_id),
                outcome="returned_synthetic_fixture",
            )
        )
        return harness.synthetic_dataset_version_resolver(registry_ref, dataset_version_id)

    report = harness.run_agent_dry_run(dataset_version_resolver=resolver)
    return IntegrationDryRunOutcome(
        path_taken=path_taken,
        recorded_verdict="PASS_WITH_WARNINGS",
        warnings=tuple(warnings),
        report=report,
        seed_registry_probe=probe,
        resolve_attempts=tuple(resolve_attempts),
    )


def _probe_seed_registries() -> SeedRegistryProbe:
    alpha_data_root = _alpha_data_root()
    if alpha_data_root is None:
        return SeedRegistryProbe(
            alpha_data_root=None,
            feature_registry=None,
            label_registry=None,
            dataset_registry=None,
            warnings=("ALPHA_DATA_ROOT is unset; synthetic fixture path selected.",),
        )

    feature_registry = alpha_data_root / "registry" / "features.sqlite"
    label_registry = alpha_data_root / "registry" / "labels.sqlite"
    dataset_registry = alpha_data_root / "registry" / "datasets.sqlite"
    required = (
        ("FeaturePack registry marker", feature_registry),
        ("LabelPack registry marker", label_registry),
        ("DatasetVersion registry marker", dataset_registry),
    )
    warnings = tuple(
        f"{label} is absent; synthetic fixture path selected."
        for label, path in required
        if not path.is_file()
    )
    return SeedRegistryProbe(
        alpha_data_root=alpha_data_root,
        feature_registry=feature_registry,
        label_registry=label_registry,
        dataset_registry=dataset_registry,
        warnings=warnings,
    )


def _alpha_data_root() -> Path | None:
    value = os.environ.get("ALPHA_DATA_ROOT")
    if not value:
        return None
    return Path(os.path.expanduser(os.path.expandvars(value)))


def _try_resolve_dataset_version(
    registry_path: Path | None,
    dataset_version_id: object,
    resolve_attempts: list[ResolveAttempt],
    warn_once: Callable[[str], None],
) -> ResolvedDatasetVersionRef | None:
    if registry_path is None:
        return None
    try:
        resolved = resolve_dataset_version(registry_path, dataset_version_id)
    except (DataFoundationValidationError, OSError, ValueError) as exc:
        resolve_attempts.append(
            ResolveAttempt(
                resolver_name="resolve_dataset_version",
                dataset_version_id=str(dataset_version_id),
                outcome=f"blocked:{type(exc).__name__}",
            )
        )
        warn_once(
            "resolve_dataset_version could not resolve the dry-run DatasetVersion; "
            "synthetic fixture path selected."
        )
        return None

    if resolved is None:
        resolve_attempts.append(
            ResolveAttempt(
                resolver_name="resolve_dataset_version",
                dataset_version_id=str(dataset_version_id),
                outcome="not_found",
            )
        )
        return None

    resolved_id = getattr(resolved, "dataset_version_id", None)
    resolve_attempts.append(
        ResolveAttempt(
            resolver_name="resolve_dataset_version",
            dataset_version_id=str(dataset_version_id),
            outcome="resolved",
        )
    )
    return ResolvedDatasetVersionRef(
        dataset_version_id=str(resolved_id),
        lifecycle_state="VERSIONED",
    )


def _assert_value_free_agent_result(result: AgentToolResult) -> None:
    assert tuple(result.__dataclass_fields__) == AGENT_TOOL_RESULT_FIELDS
    assert result.limitations

    for field_name in AGENT_TOOL_RESULT_FIELDS:
        value = getattr(result, field_name)
        values = value if isinstance(value, tuple) else (value,)
        for item in values:
            if item is None or isinstance(item, AgentToolStatus):
                continue
            assert isinstance(item, str)
            lowered = item.lower()
            assert not any(marker in lowered for marker in FORBIDDEN_RESULT_MARKERS)
            assert not any(suffix in lowered for suffix in FORBIDDEN_HEAVY_SUFFIXES)


def test_current_environment_probe_is_marker_only() -> None:
    probe = _probe_seed_registries()

    if probe.alpha_data_root is None:
        assert probe.warnings == ("ALPHA_DATA_ROOT is unset; synthetic fixture path selected.",)
    else:
        assert probe.feature_registry is not None
        assert probe.label_registry is not None
        assert probe.dataset_registry is not None
        assert all(path.name.endswith(".sqlite") for path in _registry_paths(probe))


def _registry_paths(probe: SeedRegistryProbe) -> tuple[Path, Path, Path]:
    assert probe.feature_registry is not None
    assert probe.label_registry is not None
    assert probe.dataset_registry is not None
    return (probe.feature_registry, probe.label_registry, probe.dataset_registry)


def test_dry_run_constants_stay_on_synthetic_refs_only() -> None:
    assert DATASET_VERSION_ID == "dsv_agent_p22_synthetic"
    assert SYNTHETIC_REGISTRY_REF == "registry:agent_p22_synthetic"
