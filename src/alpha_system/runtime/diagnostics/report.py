"""Descriptive, value-free diagnostics report contracts."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, cast

from alpha_system.governance.serialization import (
    GovernanceSerializationError,
    JsonValue,
    canonical_serialize,
    deserialize,
)
from alpha_system.governance.serialization import (
    content_hash as governance_content_hash,
)
from alpha_system.runtime.contracts.run_record import RunRejectionReason, StudyRunResultState
from alpha_system.runtime.diagnostics.contracts import (
    DIAGNOSTICS_FAILURE_STATES,
    DiagnosticsContractError,
    DiagnosticsFamily,
    DiagnosticsReportRef,
    DiagnosticsRunSpec,
    DiagnosticsRunSpecRef,
)

DIAGNOSTICS_REPORT_SCHEMA = "alpha_system.runtime.diagnostics.report.v1"
DIAGNOSTICS_REPORT_ID_PREFIX = "dreport"
DIAGNOSTICS_QUALITY_GATE_SCHEMA = "alpha_system.runtime.diagnostics.quality_gate.v1"

JsonScalar = None | bool | int | float | str

REPORT_ALLOWED_STATES: frozenset[StudyRunResultState] = frozenset(
    {
        StudyRunResultState.DIAGNOSTICS_COMPLETE,
        StudyRunResultState.DIAGNOSTICS_FAILED,
        StudyRunResultState.REJECTED,
        StudyRunResultState.INCONCLUSIVE,
        StudyRunResultState.BLOCKED,
    }
)

FORBIDDEN_DATA_FIELD_TOKENS: tuple[str, ...] = (
    "array",
    "bars",
    "canonical_bars",
    "dataframe",
    "feature_values",
    "label_values",
    "market_values",
    "provider_rows",
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
    ".npy",
    ".npz",
    ".parquet",
    ".sqlite",
    ".wal",
    ".zst",
)
PROMOTIONAL_CLAIM_PHRASES: tuple[str, ...] = (
    "alpha validated",
    "candidate approved",
    "factor promoted",
    "live ready",
    "paper ready",
    "portfolio ready",
    "production ready",
    "production-ready",
    "profitable",
    "promoted factor",
    "strategy ready",
    "tradable",
    "validated alpha",
)


class DiagnosticsReportContractError(ValueError):
    """Raised when a diagnostics report violates descriptive-only constraints."""


class DiagnosticsQualityGateStatus(StrEnum):
    """Descriptive quality-gate outcome; PASS is not alpha validation."""

    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True, init=False)
class DiagnosticsQualityGate:
    """One descriptive diagnostics quality gate with scalar-only evidence refs."""

    gate_id: str
    name: str
    status: DiagnosticsQualityGateStatus
    summary: str
    metric_refs_json: str
    limitations: tuple[str, ...]

    def __init__(
        self,
        *,
        gate_id: str,
        name: str,
        status: DiagnosticsQualityGateStatus | str,
        summary: str,
        metric_refs: Mapping[str, JsonScalar] | None = None,
        limitations: Sequence[str] = (),
    ) -> None:
        normalized_gate_id = _required_text(gate_id, field="gate_id")
        normalized_name = _checked_text(name, field="name")
        normalized_status = _coerce_gate_status(status)
        normalized_summary = _checked_text(summary, field="summary")
        normalized_metric_refs = _canonical_scalar_mapping(
            metric_refs or {},
            field="metric_refs",
            require_non_empty=False,
        )
        normalized_limitations = _coerce_text_sequence(
            limitations,
            field="limitations",
            require_non_empty=False,
        )

        object.__setattr__(self, "gate_id", normalized_gate_id)
        object.__setattr__(self, "name", normalized_name)
        object.__setattr__(self, "status", normalized_status)
        object.__setattr__(self, "summary", normalized_summary)
        object.__setattr__(self, "metric_refs_json", normalized_metric_refs)
        object.__setattr__(self, "limitations", normalized_limitations)

    @property
    def metric_refs(self) -> dict[str, JsonScalar]:
        """Return scalar metric references as a defensive copy."""

        return _scalar_mapping_from_json(self.metric_refs_json, field="metric_refs")

    def to_dict(self) -> dict[str, object]:
        """Return a stable, value-free quality-gate payload."""

        return {
            "schema": DIAGNOSTICS_QUALITY_GATE_SCHEMA,
            "gate_id": self.gate_id,
            "name": self.name,
            "status": self.status.value,
            "summary": self.summary,
            "metric_refs": self.metric_refs,
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True, slots=True, init=False)
class DiagnosticsReport:
    """Common descriptive report shape for diagnostics family specializations."""

    report_id: str
    report_kind: str
    diagnostics_family: DiagnosticsFamily
    diagnostics_run_spec_ref: DiagnosticsRunSpecRef
    status: StudyRunResultState
    lineage_refs_json: str
    coverage_summary_json: str
    quality_summary_json: str
    limitations: tuple[str, ...]
    quality_gates: tuple[DiagnosticsQualityGate, ...]
    rejection_reasons: tuple[RunRejectionReason, ...]
    report_metadata_json: str
    report_hash: str

    def __init__(
        self,
        *,
        report_kind: str,
        diagnostics_family: DiagnosticsFamily | str,
        diagnostics_run_spec_ref: DiagnosticsRunSpec | DiagnosticsRunSpecRef | Mapping[str, Any],
        status: StudyRunResultState | str,
        lineage_refs: Mapping[str, str],
        coverage_summary: Mapping[str, JsonScalar],
        quality_summary: Mapping[str, JsonScalar],
        limitations: Sequence[str],
        quality_gates: Sequence[DiagnosticsQualityGate | Mapping[str, Any]] = (),
        rejection_reasons: Sequence[RunRejectionReason | Mapping[str, Any]] = (),
        report_metadata: Mapping[str, JsonScalar] | None = None,
    ) -> None:
        normalized_report_kind = _checked_text(report_kind, field="report_kind")
        family = _coerce_family(diagnostics_family)
        spec_ref = _coerce_diagnostics_run_spec_ref(diagnostics_run_spec_ref)
        normalized_status = _coerce_report_status(status)
        lineage_json = _canonical_lineage_refs(lineage_refs)
        coverage_json = _canonical_scalar_mapping(
            coverage_summary,
            field="coverage_summary",
            require_non_empty=True,
        )
        quality_json = _canonical_scalar_mapping(
            quality_summary,
            field="quality_summary",
            require_non_empty=True,
        )
        normalized_limitations = _coerce_text_sequence(
            limitations,
            field="limitations",
            require_non_empty=True,
        )
        normalized_gates = tuple(_coerce_quality_gate(gate) for gate in quality_gates)
        normalized_reasons = tuple(_coerce_rejection_reason(reason) for reason in rejection_reasons)
        metadata_json = _canonical_scalar_mapping(
            report_metadata or {},
            field="report_metadata",
            require_non_empty=False,
        )

        if normalized_status in DIAGNOSTICS_FAILURE_STATES and not normalized_reasons:
            raise DiagnosticsReportContractError(
                "failed, rejected, inconclusive, and blocked diagnostics reports "
                "require at least one visible rejection reason"
            )

        payload = {
            "schema": DIAGNOSTICS_REPORT_SCHEMA,
            "report_kind": normalized_report_kind,
            "diagnostics_family": family.value,
            "diagnostics_run_spec_ref": spec_ref.to_dict(),
            "status": normalized_status.value,
            "lineage_refs": _scalar_mapping_from_json(lineage_json, field="lineage_refs"),
            "coverage_summary": _scalar_mapping_from_json(
                coverage_json,
                field="coverage_summary",
            ),
            "quality_summary": _scalar_mapping_from_json(quality_json, field="quality_summary"),
            "limitations": list(normalized_limitations),
            "quality_gates": [gate.to_dict() for gate in normalized_gates],
            "rejection_reason_records": [reason.to_dict() for reason in normalized_reasons],
            "report_metadata": _scalar_mapping_from_json(metadata_json, field="report_metadata"),
            "descriptive_only": True,
            "non_promotional": True,
            "raw_or_heavy_data_embedded": False,
            "diagnostic_pass_is_alpha_validation": False,
        }
        digest = governance_content_hash(cast(JsonValue, payload))

        object.__setattr__(self, "report_id", f"{DIAGNOSTICS_REPORT_ID_PREFIX}_{digest[:24]}")
        object.__setattr__(self, "report_kind", normalized_report_kind)
        object.__setattr__(self, "diagnostics_family", family)
        object.__setattr__(self, "diagnostics_run_spec_ref", spec_ref)
        object.__setattr__(self, "status", normalized_status)
        object.__setattr__(self, "lineage_refs_json", lineage_json)
        object.__setattr__(self, "coverage_summary_json", coverage_json)
        object.__setattr__(self, "quality_summary_json", quality_json)
        object.__setattr__(self, "limitations", normalized_limitations)
        object.__setattr__(self, "quality_gates", normalized_gates)
        object.__setattr__(self, "rejection_reasons", normalized_reasons)
        object.__setattr__(self, "report_metadata_json", metadata_json)
        object.__setattr__(self, "report_hash", digest)

    @property
    def lineage_refs(self) -> dict[str, str]:
        """Return version and run lineage references as a defensive copy."""

        return {
            key: str(value)
            for key, value in _scalar_mapping_from_json(
                self.lineage_refs_json,
                field="lineage_refs",
            ).items()
        }

    @property
    def coverage_summary(self) -> dict[str, JsonScalar]:
        """Return scalar coverage summary fields."""

        return _scalar_mapping_from_json(self.coverage_summary_json, field="coverage_summary")

    @property
    def quality_summary(self) -> dict[str, JsonScalar]:
        """Return scalar quality summary fields."""

        return _scalar_mapping_from_json(self.quality_summary_json, field="quality_summary")

    @property
    def report_metadata(self) -> dict[str, JsonScalar]:
        """Return scalar report metadata fields."""

        return _scalar_mapping_from_json(self.report_metadata_json, field="report_metadata")

    def to_ref(self) -> DiagnosticsReportRef:
        """Return a compact report reference for diagnostics run records."""

        return DiagnosticsReportRef(
            report_id=self.report_id,
            report_hash=self.report_hash,
            report_kind=self.report_kind,
        )

    def to_dict(self) -> dict[str, object]:
        """Return the common diagnostics report payload with no raw or heavy data."""

        return {
            "schema": DIAGNOSTICS_REPORT_SCHEMA,
            "report_id": self.report_id,
            "report_kind": self.report_kind,
            "diagnostics_family": self.diagnostics_family.value,
            "diagnostics_run_spec_ref": self.diagnostics_run_spec_ref.to_dict(),
            "status": self.status.value,
            "lineage_refs": self.lineage_refs,
            "coverage_summary": self.coverage_summary,
            "quality_summary": self.quality_summary,
            "limitations": list(self.limitations),
            "quality_gates": [gate.to_dict() for gate in self.quality_gates],
            "rejection_reason_records": [reason.to_dict() for reason in self.rejection_reasons],
            "report_metadata": self.report_metadata,
            "report_hash": self.report_hash,
            "descriptive_only": True,
            "non_promotional": True,
            "raw_or_heavy_data_embedded": False,
            "diagnostic_pass_is_alpha_validation": False,
            "value_free": True,
        }


def _coerce_family(value: DiagnosticsFamily | str) -> DiagnosticsFamily:
    try:
        return value if isinstance(value, DiagnosticsFamily) else DiagnosticsFamily(value)
    except ValueError as exc:
        raise DiagnosticsReportContractError(f"unsupported diagnostics family: {value}") from exc


def _coerce_report_status(value: StudyRunResultState | str) -> StudyRunResultState:
    if isinstance(value, StudyRunResultState):
        state = value
    elif isinstance(value, str):
        try:
            state = StudyRunResultState(value)
        except ValueError as exc:
            raise DiagnosticsReportContractError(f"unsupported report status: {value}") from exc
    else:
        raise DiagnosticsReportContractError(
            f"status must be StudyRunResultState or str, got {type(value).__name__}"
        )

    if state not in REPORT_ALLOWED_STATES:
        allowed = ", ".join(sorted(item.value for item in REPORT_ALLOWED_STATES))
        raise DiagnosticsReportContractError(f"report status must be one of: {allowed}")
    return state


def _coerce_gate_status(value: DiagnosticsQualityGateStatus | str) -> DiagnosticsQualityGateStatus:
    try:
        return (
            value
            if isinstance(value, DiagnosticsQualityGateStatus)
            else DiagnosticsQualityGateStatus(value)
        )
    except ValueError as exc:
        raise DiagnosticsReportContractError(f"unsupported quality gate status: {value}") from exc


def _coerce_diagnostics_run_spec_ref(
    value: DiagnosticsRunSpec | DiagnosticsRunSpecRef | Mapping[str, Any],
) -> DiagnosticsRunSpecRef:
    if isinstance(value, DiagnosticsRunSpec):
        return value.to_ref()
    if isinstance(value, DiagnosticsRunSpecRef):
        return value
    if not isinstance(value, Mapping):
        raise DiagnosticsReportContractError(
            "diagnostics_run_spec_ref must be DiagnosticsRunSpec or reference mapping, "
            f"got {type(value).__name__}"
        )
    extra = set(value) - {"diagnostics_run_spec_id", "content_hash"}
    if extra:
        raise DiagnosticsReportContractError(
            f"diagnostics_run_spec_ref contains non-reference fields: {', '.join(sorted(extra))}"
        )
    try:
        return DiagnosticsRunSpecRef(
            diagnostics_run_spec_id=value.get("diagnostics_run_spec_id"),
            content_hash=value.get("content_hash"),
        )
    except DiagnosticsContractError as exc:
        raise DiagnosticsReportContractError(str(exc)) from exc


def _coerce_quality_gate(
    value: DiagnosticsQualityGate | Mapping[str, Any],
) -> DiagnosticsQualityGate:
    if isinstance(value, DiagnosticsQualityGate):
        return value
    if not isinstance(value, Mapping):
        raise DiagnosticsReportContractError(
            f"quality gate must be DiagnosticsQualityGate or mapping, got {type(value).__name__}"
        )
    allowed = {"gate_id", "name", "status", "summary", "metric_refs", "limitations"}
    extra = set(value) - allowed
    if extra:
        raise DiagnosticsReportContractError(
            f"quality gate contains non-summary fields: {', '.join(sorted(extra))}"
        )
    return DiagnosticsQualityGate(
        gate_id=value.get("gate_id"),
        name=value.get("name"),
        status=value.get("status"),
        summary=value.get("summary"),
        metric_refs=value.get("metric_refs") or {},
        limitations=value.get("limitations") or (),
    )


def _coerce_rejection_reason(value: RunRejectionReason | Mapping[str, Any]) -> RunRejectionReason:
    if isinstance(value, RunRejectionReason):
        return value
    if not isinstance(value, Mapping):
        raise DiagnosticsReportContractError(
            f"rejection reason must be RunRejectionReason or mapping, got {type(value).__name__}"
        )
    extra = set(value) - {"code", "message"}
    if extra:
        raise DiagnosticsReportContractError(
            f"rejection reason contains non-reference fields: {', '.join(sorted(extra))}"
        )
    return RunRejectionReason(code=value.get("code"), message=value.get("message"))


def _canonical_lineage_refs(value: Mapping[str, str]) -> str:
    if not isinstance(value, Mapping) or not value:
        raise DiagnosticsReportContractError("lineage_refs must be a non-empty mapping")
    normalized: dict[str, JsonScalar] = {}
    for key, item in value.items():
        normalized_key = _checked_key(key, field="lineage_refs")
        normalized_value = _checked_text(item, field=f"lineage_refs.{normalized_key}")
        normalized[normalized_key] = normalized_value
    return _canonical_json(normalized, field="lineage_refs")


def _canonical_scalar_mapping(
    value: Mapping[str, JsonScalar],
    *,
    field: str,
    require_non_empty: bool,
) -> str:
    if not isinstance(value, Mapping):
        raise DiagnosticsReportContractError(f"{field} must be a mapping")
    if require_non_empty and not value:
        raise DiagnosticsReportContractError(f"{field} must not be empty")

    normalized: dict[str, JsonScalar] = {}
    for key, item in value.items():
        normalized_key = _checked_key(key, field=field)
        normalized[normalized_key] = _coerce_scalar(item, field=f"{field}.{normalized_key}")
    return _canonical_json(normalized, field=field)


def _scalar_mapping_from_json(text: str, *, field: str) -> dict[str, JsonScalar]:
    try:
        value = deserialize(text)
    except GovernanceSerializationError as exc:
        raise DiagnosticsReportContractError(f"{field} must be serialized JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise DiagnosticsReportContractError(f"{field} must serialize to a mapping")

    normalized: dict[str, JsonScalar] = {}
    for key, item in value.items():
        normalized[key] = _coerce_scalar(item, field=f"{field}.{key}")
    return normalized


def _canonical_json(value: Mapping[str, JsonScalar], *, field: str) -> str:
    try:
        return canonical_serialize(cast(JsonValue, dict(value)))
    except GovernanceSerializationError as exc:
        raise DiagnosticsReportContractError(f"{field} must be JSON-compatible: {exc}") from exc


def _coerce_text_sequence(
    values: Sequence[str],
    *,
    field: str,
    require_non_empty: bool,
) -> tuple[str, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise DiagnosticsReportContractError(f"{field} must be a sequence of text")
    normalized = tuple(
        _checked_text(value, field=f"{field}[{index}]") for index, value in enumerate(values)
    )
    if require_non_empty and not normalized:
        raise DiagnosticsReportContractError(f"{field} must not be empty")
    return normalized


def _coerce_scalar(value: object, *, field: str) -> JsonScalar:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise DiagnosticsReportContractError(f"{field} must be finite")
        return value
    if isinstance(value, str):
        return _checked_text(value, field=field)
    raise DiagnosticsReportContractError(
        f"{field} must be a scalar summary value, got {type(value).__name__}"
    )


def _checked_key(value: object, *, field: str) -> str:
    text = _required_text(value, field=field)
    normalized = text.lower().replace("-", "_")
    if any(token in normalized for token in FORBIDDEN_DATA_FIELD_TOKENS):
        raise DiagnosticsReportContractError(f"{field} must not include raw or value-bearing keys")
    if any(token in normalized for token in HEAVY_ARTIFACT_TOKENS):
        raise DiagnosticsReportContractError(f"{field} must not include heavy artifact keys")
    return text


def _checked_text(value: object, *, field: str) -> str:
    text = _required_text(value, field=field)
    lowered = text.lower()
    if any(token in lowered for token in HEAVY_ARTIFACT_TOKENS):
        raise DiagnosticsReportContractError(f"{field} must not reference heavy artifacts")
    if any(phrase in lowered for phrase in PROMOTIONAL_CLAIM_PHRASES):
        raise DiagnosticsReportContractError(f"{field} must not make promotional claims")
    return text


def _required_text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DiagnosticsReportContractError(f"{field} is required")
    return value.strip()


__all__ = [
    "DIAGNOSTICS_QUALITY_GATE_SCHEMA",
    "DIAGNOSTICS_REPORT_SCHEMA",
    "DiagnosticsQualityGate",
    "DiagnosticsQualityGateStatus",
    "DiagnosticsReport",
    "DiagnosticsReportContractError",
    "REPORT_ALLOWED_STATES",
]
