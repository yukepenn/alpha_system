"""Agent-facing, value-free runtime tool result contracts."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

from alpha_system.governance.serialization import (
    GovernanceSerializationError,
    JsonValue,
    canonical_serialize,
    deserialize,
)
from alpha_system.runtime.contracts.artifacts import RuntimeArtifactEntry, RuntimeArtifactManifest
from alpha_system.runtime.contracts.manifest import StudyRunManifest
from alpha_system.runtime.contracts.run_record import (
    RuntimeArtifactRef,
    StudyRunRecord,
    StudyRunResultState,
)
from alpha_system.runtime.contracts.run_spec import RuntimeLifecycleState
from alpha_system.runtime.cost.report import CostSensitivityReport
from alpha_system.runtime.decisions.records import RejectionReasonRecord
from alpha_system.runtime.decisions.states import (
    FORWARD_DECISION_STATES,
    TERMINAL_DECISION_STATES,
    RuntimeDecisionState,
    coerce_runtime_decision_state,
)
from alpha_system.runtime.diagnostics.contracts import DiagnosticsReportRef
from alpha_system.runtime.diagnostics.report import DiagnosticsReport
from alpha_system.runtime.entry_contract import RuntimeEntryStatus

type JsonScalar = None | bool | int | float | str

RUNTIME_TOOL_RESULT_SCHEMA = "alpha_system.runtime.tool_result.v1"
RUNTIME_RUN_SUMMARY_SCHEMA = "alpha_system.runtime.run_summary.v1"

FORBIDDEN_DATA_FIELD_TOKENS: tuple[str, ...] = (
    "array",
    "bars",
    "canonical_bar",
    "canonical_bbo",
    "canonical_bars",
    "dataframe",
    "feature_value",
    "feature_values",
    "label_value",
    "label_values",
    "market_value",
    "provider_payload",
    "provider_response",
    "provider_rows",
    "raw_payload",
    "raw_values",
    "rows",
    "series",
    "value_array",
    "value_table",
    "values",
)
HEAVY_ARTIFACT_TOKENS: tuple[str, ...] = (
    ".arrow",
    ".db",
    ".dbn",
    ".feather",
    ".joblib",
    ".log",
    ".npy",
    ".npz",
    ".onnx",
    ".parquet",
    ".pkl",
    ".sqlite",
    ".wal",
    ".zst",
)
FORBIDDEN_DATA_PATH_PREFIXES: tuple[str, ...] = (
    "artifacts/",
    "data/cache/",
    "data/canonical/",
    "data/factors/",
    "data/labels/",
    "data/raw/",
    "metadata/",
)
PROMOTIONAL_CLAIM_PHRASES: tuple[str, ...] = (
    "alpha validated",
    "candidate approved",
    "factor promoted",
    "fast path is reference truth",
    "live ready",
    "paper ready",
    "portfolio ready",
    "production ready",
    "production-ready",
    "profitable",
    "promoted factor",
    "reference validation complete",
    "strategy ready",
    "tradable",
    "validated alpha",
)


class RuntimeToolResultContractError(ValueError):
    """Raised when a tool-result contract would expose unsupported runtime state."""


@dataclass(frozen=True, slots=True, init=False)
class RuntimeVersionIds:
    """Version id references needed by agent-facing runtime summaries."""

    dataset_version_id: str
    feature_pack_ids: tuple[str, ...]
    label_pack_ids: tuple[str, ...]
    code_version: str
    config_version: str

    def __init__(
        self,
        *,
        dataset_version_id: str,
        feature_pack_ids: Sequence[str],
        label_pack_ids: Sequence[str],
        code_version: str,
        config_version: str,
    ) -> None:
        object.__setattr__(
            self,
            "dataset_version_id",
            _checked_text(dataset_version_id, field="dataset_version_id"),
        )
        object.__setattr__(
            self,
            "feature_pack_ids",
            _checked_text_sequence(
                feature_pack_ids,
                field="feature_pack_ids",
                require_non_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "label_pack_ids",
            _checked_text_sequence(
                label_pack_ids,
                field="label_pack_ids",
                require_non_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "code_version",
            _checked_text(code_version, field="code_version"),
        )
        object.__setattr__(
            self,
            "config_version",
            _checked_text(config_version, field="config_version"),
        )

    @classmethod
    def from_manifest(cls, manifest: StudyRunManifest) -> RuntimeVersionIds:
        """Extract version ids from an existing study-run manifest."""

        if not isinstance(manifest, StudyRunManifest):
            raise RuntimeToolResultContractError("manifest must be a StudyRunManifest")
        return cls(
            dataset_version_id=manifest.dataset_version_id,
            feature_pack_ids=tuple(ref.pack_id for ref in manifest.feature_pack_versions),
            label_pack_ids=tuple(ref.pack_id for ref in manifest.label_pack_versions),
            code_version=manifest.code_version,
            config_version=manifest.config_version,
        )

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> RuntimeVersionIds:
        """Build version ids from a stable reference mapping."""

        _reject_extra_keys(
            value,
            allowed={
                "dataset_version_id",
                "feature_pack_ids",
                "label_pack_ids",
                "code_version",
                "config_version",
            },
            field="version_ids",
        )
        return cls(
            dataset_version_id=value.get("dataset_version_id"),
            feature_pack_ids=_mapping_sequence(value, "feature_pack_ids"),
            label_pack_ids=_mapping_sequence(value, "label_pack_ids"),
            code_version=value.get("code_version"),
            config_version=value.get("config_version"),
        )

    def to_dict(self) -> dict[str, object]:
        """Return version identifiers without hashes, rows, or value payloads."""

        return {
            "dataset_version_id": self.dataset_version_id,
            "feature_pack_ids": list(self.feature_pack_ids),
            "label_pack_ids": list(self.label_pack_ids),
            "code_version": self.code_version,
            "config_version": self.config_version,
        }


@dataclass(frozen=True, slots=True, init=False)
class RuntimeDiagnosticsSummary:
    """Compact diagnostics summary assembled from existing diagnostics reports."""

    report_refs: tuple[DiagnosticsReportRef, ...]
    coverage_summary_json: str
    quality_summary_json: str
    limitations: tuple[str, ...]

    def __init__(
        self,
        *,
        report_refs: Sequence[DiagnosticsReport | DiagnosticsReportRef | Mapping[str, Any]] = (),
        coverage_summary: Mapping[str, JsonScalar] | None = None,
        quality_summary: Mapping[str, JsonScalar] | None = None,
        limitations: Sequence[str] = (),
    ) -> None:
        object.__setattr__(
            self,
            "report_refs",
            tuple(_coerce_diagnostics_report_ref(ref) for ref in report_refs),
        )
        object.__setattr__(
            self,
            "coverage_summary_json",
            _canonical_scalar_mapping(
                coverage_summary or {},
                field="diagnostics_summary.coverage_summary",
            ),
        )
        object.__setattr__(
            self,
            "quality_summary_json",
            _canonical_scalar_mapping(
                quality_summary or {},
                field="diagnostics_summary.quality_summary",
            ),
        )
        object.__setattr__(
            self,
            "limitations",
            _checked_text_sequence(
                limitations,
                field="diagnostics_summary.limitations",
                require_non_empty=False,
            ),
        )

    @classmethod
    def from_reports(cls, reports: Sequence[DiagnosticsReport]) -> RuntimeDiagnosticsSummary:
        """Read compact scalar summaries from existing diagnostics reports."""

        if isinstance(reports, str) or not isinstance(reports, Sequence):
            raise RuntimeToolResultContractError("diagnostics reports must be a finite sequence")
        normalized = tuple(_coerce_diagnostics_report(report) for report in reports)

        coverage_summary: dict[str, JsonScalar] = {"report_count": len(normalized)}
        quality_summary: dict[str, JsonScalar] = {"report_count": len(normalized)}
        limitations: list[str] = []
        for report in normalized:
            prefix = _summary_prefix(report.report_kind)
            coverage_summary[f"{prefix}_status"] = report.status.value
            coverage_summary[f"{prefix}_diagnostics_family"] = report.diagnostics_family.value
            coverage_summary[f"{prefix}_quality_gate_count"] = len(report.quality_gates)
            coverage_summary[f"{prefix}_rejection_reason_count"] = len(report.rejection_reasons)
            for key, value in report.coverage_summary.items():
                coverage_summary[f"{prefix}_coverage_{key}"] = value
            for key, value in report.quality_summary.items():
                quality_summary[f"{prefix}_quality_{key}"] = value
            limitations.extend(report.limitations)

        return cls(
            report_refs=tuple(report.to_ref() for report in normalized),
            coverage_summary=coverage_summary,
            quality_summary=quality_summary,
            limitations=tuple(limitations),
        )

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> RuntimeDiagnosticsSummary:
        """Build a diagnostics summary from a stable mapping."""

        _reject_extra_keys(
            value,
            allowed={"report_refs", "coverage_summary", "quality_summary", "limitations"},
            field="diagnostics_summary",
        )
        return cls(
            report_refs=_mapping_sequence(value, "report_refs", default=()),
            coverage_summary=_mapping_mapping(value, "coverage_summary", default={}),
            quality_summary=_mapping_mapping(value, "quality_summary", default={}),
            limitations=_mapping_sequence(value, "limitations", default=()),
        )

    @property
    def coverage_summary(self) -> dict[str, JsonScalar]:
        """Return scalar coverage summary values as a defensive copy."""

        return _scalar_mapping_from_json(
            self.coverage_summary_json,
            field="diagnostics_summary.coverage_summary",
        )

    @property
    def quality_summary(self) -> dict[str, JsonScalar]:
        """Return scalar quality summary values as a defensive copy."""

        return _scalar_mapping_from_json(
            self.quality_summary_json,
            field="diagnostics_summary.quality_summary",
        )

    def to_dict(self) -> dict[str, object]:
        """Return diagnostics references and scalar summaries only."""

        return {
            "report_refs": [ref.to_dict() for ref in self.report_refs],
            "coverage_summary": self.coverage_summary,
            "quality_summary": self.quality_summary,
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True, slots=True, init=False)
class RuntimeCostSummary:
    """Compact cost-stress summary with slippage explicitly labeled as a proxy."""

    diagnostics_report_ref: DiagnosticsReportRef
    cost_model_version_id: str
    profile_count: int
    double_cost_profile_name: str
    double_cost_combined_cost_slippage_proxy: str
    slippage_labeled_proxy: bool
    zero_cost_diagnostic_only: bool
    bbo_spread_crossing_used: bool
    bbo_unavailable_fallback_used: bool

    def __init__(
        self,
        *,
        diagnostics_report_ref: DiagnosticsReport | DiagnosticsReportRef | Mapping[str, Any],
        cost_model_version_id: str,
        profile_count: int,
        double_cost_profile_name: str,
        double_cost_combined_cost_slippage_proxy: str,
        slippage_labeled_proxy: bool = True,
        zero_cost_diagnostic_only: bool = False,
        bbo_spread_crossing_used: bool = False,
        bbo_unavailable_fallback_used: bool = False,
    ) -> None:
        if slippage_labeled_proxy is not True:
            raise RuntimeToolResultContractError("slippage must be labeled as a proxy")
        object.__setattr__(
            self,
            "diagnostics_report_ref",
            _coerce_diagnostics_report_ref(diagnostics_report_ref),
        )
        object.__setattr__(
            self,
            "cost_model_version_id",
            _checked_text(cost_model_version_id, field="cost_summary.cost_model_version_id"),
        )
        object.__setattr__(
            self,
            "profile_count",
            _non_negative_int(profile_count, field="cost_summary.profile_count"),
        )
        object.__setattr__(
            self,
            "double_cost_profile_name",
            _checked_text(
                double_cost_profile_name,
                field="cost_summary.double_cost_profile_name",
            ),
        )
        object.__setattr__(
            self,
            "double_cost_combined_cost_slippage_proxy",
            _checked_text(
                double_cost_combined_cost_slippage_proxy,
                field="cost_summary.double_cost_combined_cost_slippage_proxy",
            ),
        )
        object.__setattr__(self, "slippage_labeled_proxy", True)
        object.__setattr__(
            self,
            "zero_cost_diagnostic_only",
            _coerce_bool(
                zero_cost_diagnostic_only,
                field="cost_summary.zero_cost_diagnostic_only",
            ),
        )
        object.__setattr__(
            self,
            "bbo_spread_crossing_used",
            _coerce_bool(
                bbo_spread_crossing_used,
                field="cost_summary.bbo_spread_crossing_used",
            ),
        )
        object.__setattr__(
            self,
            "bbo_unavailable_fallback_used",
            _coerce_bool(
                bbo_unavailable_fallback_used,
                field="cost_summary.bbo_unavailable_fallback_used",
            ),
        )

    @classmethod
    def from_cost_report(cls, report: CostSensitivityReport) -> RuntimeCostSummary:
        """Read compact scalar fields from an existing cost sensitivity report."""

        if not isinstance(report, CostSensitivityReport):
            raise RuntimeToolResultContractError("cost report must be a CostSensitivityReport")
        double_cost = report.double_cost_summary
        return cls(
            diagnostics_report_ref=report.to_ref(),
            cost_model_version_id=report.cost_model_version.cost_model_version_id,
            profile_count=len(report.profile_summaries),
            double_cost_profile_name=double_cost.profile_name,
            double_cost_combined_cost_slippage_proxy=double_cost.to_dict()[
                "combined_cost_slippage_proxy"
            ],
            slippage_labeled_proxy=report.slippage_labeled_proxy,
            zero_cost_diagnostic_only=report.cost_model_version.zero_cost_diagnostic_only,
            bbo_spread_crossing_used=report.bbo_spread_crossing_used,
            bbo_unavailable_fallback_used=report.bbo_unavailable_fallback_used,
        )

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> RuntimeCostSummary:
        """Build a cost summary from a stable mapping."""

        _reject_extra_keys(
            value,
            allowed={
                "diagnostics_report_ref",
                "cost_model_version_id",
                "profile_count",
                "double_cost_profile_name",
                "double_cost_combined_cost_slippage_proxy",
                "slippage_labeled_proxy",
                "zero_cost_diagnostic_only",
                "bbo_spread_crossing_used",
                "bbo_unavailable_fallback_used",
            },
            field="cost_summary",
        )
        return cls(
            diagnostics_report_ref=value.get("diagnostics_report_ref"),
            cost_model_version_id=value.get("cost_model_version_id"),
            profile_count=value.get("profile_count"),
            double_cost_profile_name=value.get("double_cost_profile_name"),
            double_cost_combined_cost_slippage_proxy=value.get(
                "double_cost_combined_cost_slippage_proxy"
            ),
            slippage_labeled_proxy=value.get("slippage_labeled_proxy", True),
            zero_cost_diagnostic_only=value.get("zero_cost_diagnostic_only", False),
            bbo_spread_crossing_used=value.get("bbo_spread_crossing_used", False),
            bbo_unavailable_fallback_used=value.get("bbo_unavailable_fallback_used", False),
        )

    def to_dict(self) -> dict[str, object]:
        """Return scalar cost stress fields only."""

        return {
            "diagnostics_report_ref": self.diagnostics_report_ref.to_dict(),
            "cost_model_version_id": self.cost_model_version_id,
            "profile_count": self.profile_count,
            "double_cost_profile_name": self.double_cost_profile_name,
            "double_cost_combined_cost_slippage_proxy": (
                self.double_cost_combined_cost_slippage_proxy
            ),
            "slippage_labeled_proxy": True,
            "zero_cost_diagnostic_only": self.zero_cost_diagnostic_only,
            "bbo_spread_crossing_used": self.bbo_spread_crossing_used,
            "bbo_unavailable_fallback_used": self.bbo_unavailable_fallback_used,
        }


@dataclass(frozen=True, slots=True, init=False)
class RuntimeToolResult:
    """Agent-facing result for one approved runtime tool surface."""

    status: RuntimeDecisionState
    run_id: str
    version_ids: RuntimeVersionIds
    diagnostics_summary: RuntimeDiagnosticsSummary
    cost_summary: RuntimeCostSummary | None
    rejection_reasons: tuple[RejectionReasonRecord, ...]
    artifacts: tuple[RuntimeArtifactRef, ...]
    next_required_gate: str

    def __init__(
        self,
        *,
        status: RuntimeDecisionState
        | RuntimeLifecycleState
        | StudyRunResultState
        | RuntimeEntryStatus
        | str,
        run_id: str,
        version_ids: RuntimeVersionIds | StudyRunManifest | Mapping[str, Any],
        diagnostics_summary: (
            RuntimeDiagnosticsSummary
            | DiagnosticsReport
            | Sequence[DiagnosticsReport]
            | Mapping[str, Any]
            | None
        ) = None,
        cost_summary: RuntimeCostSummary | CostSensitivityReport | Mapping[str, Any] | None = None,
        rejection_reasons: Sequence[RejectionReasonRecord | Mapping[str, Any]] = (),
        artifacts: Sequence[
            RuntimeArtifactRef | RuntimeArtifactEntry | RuntimeArtifactManifest | Mapping[str, Any]
        ] = (),
        next_required_gate: str,
    ) -> None:
        fields = _coerce_result_fields(
            status=status,
            run_id=run_id,
            version_ids=version_ids,
            diagnostics_summary=diagnostics_summary,
            cost_summary=cost_summary,
            rejection_reasons=rejection_reasons,
            artifacts=artifacts,
            next_required_gate=next_required_gate,
        )
        for name, value in fields.items():
            object.__setattr__(self, name, value)

    @classmethod
    def from_study_run_record(
        cls,
        *,
        study_run_record: StudyRunRecord,
        manifest: StudyRunManifest,
        diagnostics_summary: (
            RuntimeDiagnosticsSummary
            | DiagnosticsReport
            | Sequence[DiagnosticsReport]
            | Mapping[str, Any]
            | None
        ) = None,
        cost_summary: RuntimeCostSummary | CostSensitivityReport | Mapping[str, Any] | None = None,
        rejection_reasons: Sequence[RejectionReasonRecord | Mapping[str, Any]] = (),
        next_required_gate: str,
    ) -> RuntimeToolResult:
        """Build a tool result by consuming existing run-record and manifest contracts."""

        if not isinstance(study_run_record, StudyRunRecord):
            raise RuntimeToolResultContractError("study_run_record must be a StudyRunRecord")
        return cls(
            status=study_run_record.result_state,
            run_id=study_run_record.run_id,
            version_ids=manifest,
            diagnostics_summary=diagnostics_summary,
            cost_summary=cost_summary,
            rejection_reasons=rejection_reasons,
            artifacts=study_run_record.artifact_refs,
            next_required_gate=next_required_gate,
        )

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> RuntimeToolResult:
        """Build a tool result from a stable value-free payload."""

        return cls(**_validated_payload_mapping(value, field="runtime_tool_result"))

    def to_dict(self) -> dict[str, object]:
        """Return a stable agent-facing payload with no raw or heavy data."""

        return _payload_dict(self)


@dataclass(frozen=True, slots=True, init=False)
class RuntimeRunSummary:
    """Agent-facing summary for the current state of one bounded runtime run."""

    status: RuntimeDecisionState
    run_id: str
    version_ids: RuntimeVersionIds
    diagnostics_summary: RuntimeDiagnosticsSummary
    cost_summary: RuntimeCostSummary | None
    rejection_reasons: tuple[RejectionReasonRecord, ...]
    artifacts: tuple[RuntimeArtifactRef, ...]
    next_required_gate: str

    def __init__(
        self,
        *,
        status: RuntimeDecisionState
        | RuntimeLifecycleState
        | StudyRunResultState
        | RuntimeEntryStatus
        | str,
        run_id: str,
        version_ids: RuntimeVersionIds | StudyRunManifest | Mapping[str, Any],
        diagnostics_summary: (
            RuntimeDiagnosticsSummary
            | DiagnosticsReport
            | Sequence[DiagnosticsReport]
            | Mapping[str, Any]
            | None
        ) = None,
        cost_summary: RuntimeCostSummary | CostSensitivityReport | Mapping[str, Any] | None = None,
        rejection_reasons: Sequence[RejectionReasonRecord | Mapping[str, Any]] = (),
        artifacts: Sequence[
            RuntimeArtifactRef | RuntimeArtifactEntry | RuntimeArtifactManifest | Mapping[str, Any]
        ] = (),
        next_required_gate: str,
    ) -> None:
        fields = _coerce_result_fields(
            status=status,
            run_id=run_id,
            version_ids=version_ids,
            diagnostics_summary=diagnostics_summary,
            cost_summary=cost_summary,
            rejection_reasons=rejection_reasons,
            artifacts=artifacts,
            next_required_gate=next_required_gate,
        )
        for name, value in fields.items():
            object.__setattr__(self, name, value)

    @classmethod
    def from_tool_result(cls, result: RuntimeToolResult) -> RuntimeRunSummary:
        """Build a run summary from a single tool-result contract."""

        if not isinstance(result, RuntimeToolResult):
            raise RuntimeToolResultContractError("result must be a RuntimeToolResult")
        return cls(
            status=result.status,
            run_id=result.run_id,
            version_ids=result.version_ids,
            diagnostics_summary=result.diagnostics_summary,
            cost_summary=result.cost_summary,
            rejection_reasons=result.rejection_reasons,
            artifacts=result.artifacts,
            next_required_gate=result.next_required_gate,
        )

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> RuntimeRunSummary:
        """Build a run summary from a stable value-free payload."""

        return cls(**_validated_payload_mapping(value, field="runtime_run_summary"))

    def to_dict(self) -> dict[str, object]:
        """Return a stable agent-facing payload with no raw or heavy data."""

        return _payload_dict(self)


def _coerce_result_fields(
    *,
    status: RuntimeDecisionState
    | RuntimeLifecycleState
    | StudyRunResultState
    | RuntimeEntryStatus
    | str,
    run_id: str,
    version_ids: RuntimeVersionIds | StudyRunManifest | Mapping[str, Any],
    diagnostics_summary: (
        RuntimeDiagnosticsSummary
        | DiagnosticsReport
        | Sequence[DiagnosticsReport]
        | Mapping[str, Any]
        | None
    ),
    cost_summary: RuntimeCostSummary | CostSensitivityReport | Mapping[str, Any] | None,
    rejection_reasons: Sequence[RejectionReasonRecord | Mapping[str, Any]],
    artifacts: Sequence[
        RuntimeArtifactRef | RuntimeArtifactEntry | RuntimeArtifactManifest | Mapping[str, Any]
    ],
    next_required_gate: str,
) -> dict[str, object]:
    normalized_status = coerce_runtime_decision_state(status)
    normalized_reasons = _coerce_rejection_reasons(rejection_reasons)
    if normalized_status in TERMINAL_DECISION_STATES and not normalized_reasons:
        raise RuntimeToolResultContractError(
            "terminal REJECTED/INCONCLUSIVE/BLOCKED tool results require visible reasons"
        )
    if normalized_status in FORWARD_DECISION_STATES and normalized_reasons:
        raise RuntimeToolResultContractError(
            "forward tool results must not carry rejection reasons"
        )
    if any(reason.decision_state is not normalized_status for reason in normalized_reasons):
        raise RuntimeToolResultContractError("rejection reasons must match the tool status")

    return {
        "status": normalized_status,
        "run_id": _checked_text(run_id, field="run_id"),
        "version_ids": _coerce_version_ids(version_ids),
        "diagnostics_summary": _coerce_diagnostics_summary(diagnostics_summary),
        "cost_summary": _coerce_cost_summary(cost_summary),
        "rejection_reasons": normalized_reasons,
        "artifacts": _coerce_artifact_refs(artifacts),
        "next_required_gate": _checked_text(next_required_gate, field="next_required_gate"),
    }


def _payload_dict(value: RuntimeToolResult | RuntimeRunSummary) -> dict[str, object]:
    return {
        "status": value.status.value,
        "run_id": value.run_id,
        "version_ids": value.version_ids.to_dict(),
        "diagnostics_summary": value.diagnostics_summary.to_dict(),
        "cost_summary": None if value.cost_summary is None else value.cost_summary.to_dict(),
        "rejection_reasons": [reason.to_dict() for reason in value.rejection_reasons],
        "artifacts": [artifact.to_dict() for artifact in value.artifacts],
        "next_required_gate": value.next_required_gate,
    }


def _validated_payload_mapping(value: Mapping[str, Any], *, field: str) -> dict[str, Any]:
    _reject_extra_keys(
        value,
        allowed={
            "status",
            "run_id",
            "version_ids",
            "diagnostics_summary",
            "cost_summary",
            "rejection_reasons",
            "artifacts",
            "next_required_gate",
        },
        field=field,
    )
    return {
        "status": value.get("status"),
        "run_id": value.get("run_id"),
        "version_ids": value.get("version_ids"),
        "diagnostics_summary": value.get("diagnostics_summary"),
        "cost_summary": value.get("cost_summary"),
        "rejection_reasons": _mapping_sequence(value, "rejection_reasons", default=()),
        "artifacts": _mapping_sequence(value, "artifacts", default=()),
        "next_required_gate": value.get("next_required_gate"),
    }


def _coerce_version_ids(
    value: RuntimeVersionIds | StudyRunManifest | Mapping[str, Any],
) -> RuntimeVersionIds:
    if isinstance(value, RuntimeVersionIds):
        return value
    if isinstance(value, StudyRunManifest):
        return RuntimeVersionIds.from_manifest(value)
    if isinstance(value, Mapping):
        return RuntimeVersionIds.from_dict(value)
    raise RuntimeToolResultContractError(
        "version_ids must be RuntimeVersionIds, StudyRunManifest, or mapping, "
        f"got {type(value).__name__}"
    )


def _coerce_diagnostics_summary(
    value: RuntimeDiagnosticsSummary
    | DiagnosticsReport
    | Sequence[DiagnosticsReport]
    | Mapping[str, Any]
    | None,
) -> RuntimeDiagnosticsSummary:
    if value is None:
        return RuntimeDiagnosticsSummary()
    if isinstance(value, RuntimeDiagnosticsSummary):
        return value
    if isinstance(value, DiagnosticsReport):
        return RuntimeDiagnosticsSummary.from_reports((value,))
    if isinstance(value, Mapping):
        return RuntimeDiagnosticsSummary.from_dict(value)
    if isinstance(value, Sequence) and not isinstance(value, str):
        return RuntimeDiagnosticsSummary.from_reports(value)
    raise RuntimeToolResultContractError(
        "diagnostics_summary must be RuntimeDiagnosticsSummary, DiagnosticsReport, "
        "sequence of DiagnosticsReport, mapping, or None"
    )


def _coerce_cost_summary(
    value: RuntimeCostSummary | CostSensitivityReport | Mapping[str, Any] | None,
) -> RuntimeCostSummary | None:
    if value is None:
        return None
    if isinstance(value, RuntimeCostSummary):
        return value
    if isinstance(value, CostSensitivityReport):
        return RuntimeCostSummary.from_cost_report(value)
    if isinstance(value, Mapping):
        return RuntimeCostSummary.from_dict(value)
    raise RuntimeToolResultContractError(
        "cost_summary must be RuntimeCostSummary, CostSensitivityReport, mapping, "
        f"or None, got {type(value).__name__}"
    )


def _coerce_rejection_reasons(
    reasons: Sequence[RejectionReasonRecord | Mapping[str, Any]],
) -> tuple[RejectionReasonRecord, ...]:
    if isinstance(reasons, str) or not isinstance(reasons, Sequence):
        raise RuntimeToolResultContractError("rejection_reasons must be a finite sequence")
    return tuple(_coerce_rejection_reason(reason) for reason in reasons)


def _coerce_rejection_reason(
    value: RejectionReasonRecord | Mapping[str, Any],
) -> RejectionReasonRecord:
    if isinstance(value, RejectionReasonRecord):
        return value
    if isinstance(value, Mapping):
        return RejectionReasonRecord.from_dict(value)
    raise RuntimeToolResultContractError(
        f"rejection reason must be a RejectionReasonRecord or mapping, got {type(value).__name__}"
    )


def _coerce_artifact_refs(
    artifacts: Sequence[
        RuntimeArtifactRef | RuntimeArtifactEntry | RuntimeArtifactManifest | Mapping[str, Any]
    ],
) -> tuple[RuntimeArtifactRef, ...]:
    if isinstance(artifacts, str) or not isinstance(artifacts, Sequence):
        raise RuntimeToolResultContractError("artifacts must be a finite sequence")
    return tuple(ref for artifact in artifacts for ref in _coerce_one_artifact_ref(artifact))


def _coerce_one_artifact_ref(
    value: RuntimeArtifactRef | RuntimeArtifactEntry | RuntimeArtifactManifest | Mapping[str, Any],
) -> tuple[RuntimeArtifactRef, ...]:
    if isinstance(value, RuntimeArtifactRef):
        _checked_artifact_location(value.location)
        return (value,)
    if isinstance(value, RuntimeArtifactEntry):
        _checked_artifact_location(value.location)
        return (
            RuntimeArtifactRef(
                artifact_id=value.artifact_id,
                location=value.location,
                content_hash=value.content_hash,
            ),
        )
    if isinstance(value, RuntimeArtifactManifest):
        return tuple(ref for entry in value.entries for ref in _coerce_one_artifact_ref(entry))
    if isinstance(value, Mapping):
        _reject_extra_keys(
            value,
            allowed={"artifact_id", "location", "content_hash"},
            field="artifacts",
        )
        location = _checked_artifact_location(value.get("location"))
        return (
            RuntimeArtifactRef(
                artifact_id=value.get("artifact_id"),
                location=location,
                content_hash=value.get("content_hash"),
            ),
        )
    raise RuntimeToolResultContractError(
        "artifact must be RuntimeArtifactRef, RuntimeArtifactEntry, "
        f"RuntimeArtifactManifest, or mapping, got {type(value).__name__}"
    )


def _coerce_diagnostics_report_ref(
    value: DiagnosticsReport | DiagnosticsReportRef | Mapping[str, Any],
) -> DiagnosticsReportRef:
    if isinstance(value, DiagnosticsReport):
        return value.to_ref()
    if isinstance(value, DiagnosticsReportRef):
        return value
    if isinstance(value, Mapping):
        _reject_extra_keys(
            value,
            allowed={"report_id", "report_hash", "report_kind"},
            field="diagnostics_report_ref",
        )
        return DiagnosticsReportRef(
            report_id=value.get("report_id"),
            report_hash=value.get("report_hash"),
            report_kind=value.get("report_kind"),
        )
    raise RuntimeToolResultContractError(
        "diagnostics report reference must be DiagnosticsReport, DiagnosticsReportRef, "
        f"or mapping, got {type(value).__name__}"
    )


def _coerce_diagnostics_report(value: object) -> DiagnosticsReport:
    if not isinstance(value, DiagnosticsReport):
        raise RuntimeToolResultContractError(
            f"diagnostics reports must be DiagnosticsReport objects, got {type(value).__name__}"
        )
    return value


def _canonical_scalar_mapping(value: Mapping[str, JsonScalar], *, field: str) -> str:
    if not isinstance(value, Mapping):
        raise RuntimeToolResultContractError(f"{field} must be a mapping")
    normalized: dict[str, JsonScalar] = {}
    for key, item in value.items():
        normalized_key = _checked_key(key, field=field)
        normalized[normalized_key] = _coerce_scalar(item, field=f"{field}.{normalized_key}")
    return _canonical_json(normalized, field=field)


def _scalar_mapping_from_json(text: str, *, field: str) -> dict[str, JsonScalar]:
    try:
        value = deserialize(text)
    except GovernanceSerializationError as exc:
        raise RuntimeToolResultContractError(f"{field} must be serialized JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeToolResultContractError(f"{field} must serialize to a mapping")
    return {str(key): _coerce_scalar(item, field=f"{field}.{key}") for key, item in value.items()}


def _canonical_json(value: Mapping[str, JsonScalar], *, field: str) -> str:
    try:
        return canonical_serialize(cast(JsonValue, dict(value)))
    except GovernanceSerializationError as exc:
        raise RuntimeToolResultContractError(f"{field} must be JSON-compatible: {exc}") from exc


def _coerce_scalar(value: object, *, field: str) -> JsonScalar:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise RuntimeToolResultContractError(f"{field} must be finite")
        return value
    if isinstance(value, str):
        return _checked_text(value, field=field)
    raise RuntimeToolResultContractError(
        f"{field} must be a scalar summary value, got {type(value).__name__}"
    )


def _checked_key(value: object, *, field: str) -> str:
    text = _required_text(value, field=field)
    normalized = text.lower().replace("-", "_")
    if any(token in normalized for token in FORBIDDEN_DATA_FIELD_TOKENS):
        raise RuntimeToolResultContractError(f"{field} must not include raw or value-bearing keys")
    if any(token in normalized for token in HEAVY_ARTIFACT_TOKENS):
        raise RuntimeToolResultContractError(f"{field} must not include heavy artifact keys")
    return text


def _checked_text(value: object, *, field: str) -> str:
    text = _required_text(value, field=field)
    lowered = text.lower()
    if any(token in lowered for token in HEAVY_ARTIFACT_TOKENS):
        raise RuntimeToolResultContractError(f"{field} must not reference heavy artifacts")
    if any(lowered.startswith(prefix) for prefix in FORBIDDEN_DATA_PATH_PREFIXES):
        raise RuntimeToolResultContractError(f"{field} must not reference local data artifacts")
    if any(phrase in lowered for phrase in PROMOTIONAL_CLAIM_PHRASES):
        raise RuntimeToolResultContractError(f"{field} must not make promotional claims")
    return text


def _checked_artifact_location(value: object) -> str:
    location = _required_text(value, field="artifact.location")
    if location.startswith(("/", "~")) or "\\" in location:
        raise RuntimeToolResultContractError("artifact locations must be relative references")
    parts = location.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise RuntimeToolResultContractError(
            "artifact locations must not contain empty or parent segments"
        )
    return _checked_text(location, field="artifact.location")


def _checked_text_sequence(
    values: Sequence[str],
    *,
    field: str,
    require_non_empty: bool,
) -> tuple[str, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise RuntimeToolResultContractError(f"{field} must be a sequence of text")
    normalized = tuple(
        _checked_text(value, field=f"{field}[{index}]") for index, value in enumerate(values)
    )
    if require_non_empty and not normalized:
        raise RuntimeToolResultContractError(f"{field} must not be empty")
    return normalized


def _required_text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeToolResultContractError(f"{field} is required")
    return value.strip()


def _non_negative_int(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RuntimeToolResultContractError(f"{field} must be a non-negative integer")
    return value


def _coerce_bool(value: object, *, field: str) -> bool:
    if not isinstance(value, bool):
        raise RuntimeToolResultContractError(f"{field} must be a boolean")
    return value


def _mapping_sequence(
    value: Mapping[str, Any],
    key: str,
    default: Sequence[Any] | None = None,
) -> Sequence[Any]:
    item = value.get(key, default)
    if isinstance(item, str) or not isinstance(item, Sequence):
        raise RuntimeToolResultContractError(f"{key} must be a sequence")
    return item


def _mapping_mapping(
    value: Mapping[str, Any],
    key: str,
    default: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    item = value.get(key, default)
    if not isinstance(item, Mapping):
        raise RuntimeToolResultContractError(f"{key} must be a mapping")
    return item


def _reject_extra_keys(value: Mapping[str, Any], *, allowed: set[str], field: str) -> None:
    if not isinstance(value, Mapping):
        raise RuntimeToolResultContractError(f"{field} must be a mapping")
    extra = set(value) - allowed
    if extra:
        raise RuntimeToolResultContractError(
            f"{field} contains unsupported or value-bearing fields: {', '.join(sorted(extra))}"
        )


def _summary_prefix(value: str) -> str:
    text = _checked_text(value, field="diagnostics_summary.report_kind")
    normalized = "".join(char.lower() if char.isalnum() else "_" for char in text)
    return "_".join(part for part in normalized.split("_") if part)


__all__ = [
    "RUNTIME_RUN_SUMMARY_SCHEMA",
    "RUNTIME_TOOL_RESULT_SCHEMA",
    "RuntimeCostSummary",
    "RuntimeDiagnosticsSummary",
    "RuntimeRunSummary",
    "RuntimeToolResult",
    "RuntimeToolResultContractError",
    "RuntimeVersionIds",
]
