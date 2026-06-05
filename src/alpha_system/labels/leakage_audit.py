"""Label leakage and availability audits for registered labels.

The audit layer is descriptive and fail-closed. It consumes the governance
``label_leakage_guard`` and label registry records; it does not materialize
labels, read provider data, persist values, or expose labels as features.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from alpha_system.governance.label_leakage_guard import (
    FeatureReferences,
    LabelLeakageFindingKind,
    LabelLeakageResult,
    check_label_leakage,
)
from alpha_system.governance.serialization import JsonValue
from alpha_system.labels.registry import LabelRegistry, LabelRegistryRecord
from alpha_system.labels.version import LabelValueRecord


class LabelLeakageAuditError(ValueError):
    """Raised when a label leakage audit cannot be constructed."""


class LabelLeakageAuditSeverity(StrEnum):
    """Finding severity used by label leakage audit reports."""

    BLOCKING = "BLOCKING"
    NON_BLOCKING = "NON_BLOCKING"


class LabelLeakageAuditStatus(StrEnum):
    """Compact audit status."""

    CLEAN = "CLEAN"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class LabelLeakageAuditFinding:
    """One leakage or availability audit finding."""

    check: str
    severity: LabelLeakageAuditSeverity
    label_version_id: str
    label_id: str
    label_spec_id: str
    message: str
    offending_reference: Mapping[str, Any] | None = None

    @property
    def is_blocking(self) -> bool:
        """Return whether this finding must block the label."""

        return self.severity is LabelLeakageAuditSeverity.BLOCKING

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a strict JSON-compatible representation."""

        payload: dict[str, JsonValue] = {
            "check": self.check,
            "severity": self.severity.value,
            "label_version_id": self.label_version_id,
            "label_id": self.label_id,
            "label_spec_id": self.label_spec_id,
            "message": self.message,
        }
        if self.offending_reference is not None:
            payload["offending_reference"] = _json_mapping(self.offending_reference)
        return payload


@dataclass(frozen=True, slots=True)
class LabelLeakageAuditReport:
    """Leakage and availability audit report for one registered label."""

    label_version_id: str
    label_id: str
    label_spec_id: str
    dataset_version_id: str
    partition_id: str
    lifecycle_state: str
    availability_time: datetime
    governance_result: LabelLeakageResult
    findings: tuple[LabelLeakageAuditFinding, ...]
    value_records_checked: int

    @property
    def blocking_findings(self) -> tuple[LabelLeakageAuditFinding, ...]:
        """Return blocking findings."""

        return tuple(finding for finding in self.findings if finding.is_blocking)

    @property
    def non_blocking_findings(self) -> tuple[LabelLeakageAuditFinding, ...]:
        """Return non-blocking findings."""

        return tuple(finding for finding in self.findings if not finding.is_blocking)

    @property
    def status(self) -> LabelLeakageAuditStatus:
        """Return the fail-closed audit status."""

        if self.blocking_findings:
            return LabelLeakageAuditStatus.BLOCKED
        return LabelLeakageAuditStatus.CLEAN

    @property
    def blocked(self) -> bool:
        """Return whether the registered label is blocked."""

        return self.status is LabelLeakageAuditStatus.BLOCKED

    @property
    def clean(self) -> bool:
        """Return whether the registered label passed the audit."""

        return self.status is LabelLeakageAuditStatus.CLEAN

    @property
    def has_blocking_findings(self) -> bool:
        """Return whether any finding blocks acceptance."""

        return self.blocked

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a strict JSON-compatible report payload."""

        return {
            "label_version_id": self.label_version_id,
            "label_id": self.label_id,
            "label_spec_id": self.label_spec_id,
            "dataset_version_id": self.dataset_version_id,
            "partition_id": self.partition_id,
            "lifecycle_state": self.lifecycle_state,
            "availability_time": self.availability_time.isoformat(),
            "status": self.status.value,
            "blocked": self.blocked,
            "clean": self.clean,
            "features_checked": self.governance_result.features_checked,
            "value_records_checked": self.value_records_checked,
            "blocking_finding_count": len(self.blocking_findings),
            "non_blocking_finding_count": len(self.non_blocking_findings),
            "governance_result": self.governance_result.to_dict(),
            "findings": [finding.to_dict() for finding in self.findings],
        }


@dataclass(frozen=True, slots=True)
class _RegisteredLabelAuditInput:
    label_version_id: str
    label_id: str
    label_spec_id: str
    dataset_version_id: str
    partition_id: str
    lifecycle_state: str
    availability_time: datetime
    first_label_available_ts: datetime
    last_label_available_ts: datetime
    value_record_count: int
    governance_label_spec: Mapping[str, Any]


def audit_registered_label(
    registered_label: LabelRegistryRecord,
    *,
    live_feature_references: FeatureReferences,
    label_value_records: Iterable[LabelValueRecord | Mapping[str, Any]] | None,
) -> LabelLeakageAuditReport:
    """Audit one registered label for leakage and ``label_available_ts`` safety.

    ``live_feature_references`` is passed to the existing governance
    ``check_label_leakage`` guard. ``label_value_records`` must contain the
    materialized values for this registered label; omission is blocking because
    the audit cannot prove per-row availability ordering.
    """

    label = _registered_label_input(registered_label)
    governance_result = _governance_leakage_result(label, live_feature_references)
    findings: list[LabelLeakageAuditFinding] = []
    findings.extend(_findings_from_governance_result(label, governance_result))
    findings.extend(_label_identity_feature_findings(label, live_feature_references))
    value_record_count = _append_availability_findings(
        label,
        label_value_records,
        findings,
    )

    return LabelLeakageAuditReport(
        label_version_id=label.label_version_id,
        label_id=label.label_id,
        label_spec_id=label.label_spec_id,
        dataset_version_id=label.dataset_version_id,
        partition_id=label.partition_id,
        lifecycle_state=label.lifecycle_state,
        availability_time=label.availability_time,
        governance_result=governance_result,
        findings=tuple(findings),
        value_records_checked=value_record_count,
    )


def audit_registered_labels(
    registered_labels: Iterable[LabelRegistryRecord],
    *,
    live_feature_references_by_label: Mapping[str, FeatureReferences],
    label_value_records_by_label: Mapping[str, Iterable[LabelValueRecord | Mapping[str, Any]]],
) -> tuple[LabelLeakageAuditReport, ...]:
    """Audit every supplied registered label and fail closed on missing inputs."""

    if isinstance(registered_labels, str):
        raise LabelLeakageAuditError("registered_labels must be an iterable of records")
    reports: list[LabelLeakageAuditReport] = []
    for record in registered_labels:
        label = _registered_label_input(record)
        reports.append(
            audit_registered_label(
                record,
                live_feature_references=_lookup_label_mapping(
                    live_feature_references_by_label,
                    label,
                ),
                label_value_records=_lookup_label_mapping(
                    label_value_records_by_label,
                    label,
                ),
            )
        )
    return tuple(reports)


def audit_label_registry(
    registry: LabelRegistry,
    *,
    live_feature_references_by_label: Mapping[str, FeatureReferences],
    label_value_records_by_label: Mapping[str, Iterable[LabelValueRecord | Mapping[str, Any]]],
) -> tuple[LabelLeakageAuditReport, ...]:
    """Audit every registered label in a local-only ``LabelRegistry``."""

    if not isinstance(registry, LabelRegistry):
        raise LabelLeakageAuditError("audit_label_registry requires a LabelRegistry")
    return audit_registered_labels(
        registry.read_label_records(),
        live_feature_references_by_label=live_feature_references_by_label,
        label_value_records_by_label=label_value_records_by_label,
    )


def _registered_label_input(record: LabelRegistryRecord) -> _RegisteredLabelAuditInput:
    if not isinstance(record, LabelRegistryRecord):
        raise LabelLeakageAuditError("registered_label must be a LabelRegistryRecord")
    contract = record.label_contract
    governance_spec = contract.governance_label_spec_snapshot.to_dict()
    availability_time = _require_datetime(
        contract.availability_policy.availability_time,
        "LabelSpec.availability_time",
    )
    return _RegisteredLabelAuditInput(
        label_version_id=record.label_version_id,
        label_id=record.label_id,
        label_spec_id=record.label_spec_id,
        dataset_version_id=record.dataset_version_id,
        partition_id=record.partition_id,
        lifecycle_state=record.lifecycle_state.value,
        availability_time=availability_time,
        first_label_available_ts=record.first_label_available_ts,
        last_label_available_ts=record.last_label_available_ts,
        value_record_count=record.value_record_count,
        governance_label_spec=governance_spec,
    )


def _governance_leakage_result(
    label: _RegisteredLabelAuditInput,
    live_feature_references: FeatureReferences,
) -> LabelLeakageResult:
    try:
        return check_label_leakage(label.governance_label_spec, live_feature_references)
    except ValueError as exc:
        raise LabelLeakageAuditError(
            "governance label leakage guard failed to validate the registered LabelSpec"
        ) from exc


def _findings_from_governance_result(
    label: _RegisteredLabelAuditInput,
    governance_result: LabelLeakageResult,
) -> tuple[LabelLeakageAuditFinding, ...]:
    findings: list[LabelLeakageAuditFinding] = []
    for finding in governance_result.findings:
        if finding.kind is LabelLeakageFindingKind.LABEL_AS_FEATURE:
            check = "label_as_feature"
        else:
            check = "availability_time"
        findings.append(
            _finding(
                label,
                check=check,
                message=finding.rationale,
                offending_reference=finding.offending_reference,
            )
        )
    return tuple(findings)


def _label_identity_feature_findings(
    label: _RegisteredLabelAuditInput,
    live_feature_references: FeatureReferences,
) -> tuple[LabelLeakageAuditFinding, ...]:
    label_identities = {
        _normalize_reference(label.label_id),
        _normalize_reference(label.label_version_id),
        _normalize_reference(label.label_spec_id),
    }
    findings: list[LabelLeakageAuditFinding] = []
    for index, references in enumerate(_reference_sets(live_feature_references)):
        overlap = sorted(label_identities.intersection(references))
        if not overlap:
            continue
        findings.append(
            _finding(
                label,
                check="label_identity_as_feature",
                message=(
                    "live feature references expose the registered label identity; "
                    "label-as-feature reuse is blocked"
                ),
                offending_reference={
                    "source_index": index,
                    "matched_reference": overlap[0],
                },
            )
        )
    return tuple(findings)


def _append_availability_findings(
    label: _RegisteredLabelAuditInput,
    label_value_records: Iterable[LabelValueRecord | Mapping[str, Any]] | None,
    findings: list[LabelLeakageAuditFinding],
) -> int:
    if label.value_record_count <= 0:
        findings.append(
            _finding(
                label,
                check="registry_value_record_count",
                message="registered label has no value records; audit fails closed",
            )
        )
    if label.first_label_available_ts < label.availability_time:
        findings.append(
            _finding(
                label,
                check="registry_label_available_ts",
                message="registry first_label_available_ts precedes LabelSpec.availability_time",
                offending_reference={
                    "first_label_available_ts": label.first_label_available_ts.isoformat(),
                    "availability_time": label.availability_time.isoformat(),
                },
            )
        )
    if label.last_label_available_ts < label.availability_time:
        findings.append(
            _finding(
                label,
                check="registry_label_available_ts",
                message="registry last_label_available_ts precedes LabelSpec.availability_time",
                offending_reference={
                    "last_label_available_ts": label.last_label_available_ts.isoformat(),
                    "availability_time": label.availability_time.isoformat(),
                },
            )
        )

    records = _label_value_records(label_value_records)
    if records is None:
        findings.append(
            _finding(
                label,
                check="label_value_records_required",
                message=(
                    "label value records are required to prove label_available_ts "
                    "ordering; audit fails closed"
                ),
            )
        )
        return 0
    if not records:
        findings.append(
            _finding(
                label,
                check="label_value_records_required",
                message="no label value records supplied; audit fails closed",
            )
        )
        return 0

    for index, record in enumerate(records):
        _append_value_record_findings(label, record, index, findings)
    return len(records)


def _append_value_record_findings(
    label: _RegisteredLabelAuditInput,
    record: LabelValueRecord | Mapping[str, Any],
    index: int,
    findings: list[LabelLeakageAuditFinding],
) -> None:
    label_version_id = _field(record, "label_version_id")
    if label_version_id != label.label_version_id:
        findings.append(
            _finding(
                label,
                check="label_value_binding",
                message="label value record does not bind the audited LabelVersion",
                offending_reference={
                    "source_index": index,
                    "label_version_id": _json_scalar(label_version_id),
                },
            )
        )

    label_spec_id = _field(record, "label_spec_id")
    if label_spec_id is not None and label_spec_id != label.label_spec_id:
        findings.append(
            _finding(
                label,
                check="label_value_binding",
                message="label value record label_spec_id does not match the registered label",
                offending_reference={
                    "source_index": index,
                    "label_spec_id": _json_scalar(label_spec_id),
                },
            )
        )

    event_ts = _datetime_field(label, record, "event_ts", index, findings)
    horizon_end_ts = _datetime_field(label, record, "horizon_end_ts", index, findings)
    label_available_ts = _datetime_field(
        label,
        record,
        "label_available_ts",
        index,
        findings,
    )
    if event_ts is None or horizon_end_ts is None or label_available_ts is None:
        return

    if horizon_end_ts < event_ts:
        findings.append(
            _finding(
                label,
                check="label_horizon_ordering",
                message="label horizon_end_ts precedes event_ts",
                offending_reference=_timestamp_payload(
                    index,
                    event_ts=event_ts,
                    horizon_end_ts=horizon_end_ts,
                ),
            )
        )
    if label_available_ts < event_ts:
        findings.append(
            _finding(
                label,
                check="label_available_ts_ordering",
                message="label_available_ts precedes event_ts",
                offending_reference=_timestamp_payload(
                    index,
                    event_ts=event_ts,
                    label_available_ts=label_available_ts,
                ),
            )
        )
    if label_available_ts < horizon_end_ts:
        findings.append(
            _finding(
                label,
                check="label_available_ts_ordering",
                message=(
                    "label_available_ts precedes horizon_end_ts; join could make "
                    "the label usable before the forward outcome is known"
                ),
                offending_reference=_timestamp_payload(
                    index,
                    horizon_end_ts=horizon_end_ts,
                    label_available_ts=label_available_ts,
                ),
            )
        )
    if label_available_ts < label.availability_time:
        findings.append(
            _finding(
                label,
                check="label_available_ts_ordering",
                message="label_available_ts precedes LabelSpec.availability_time",
                offending_reference=_timestamp_payload(
                    index,
                    availability_time=label.availability_time,
                    label_available_ts=label_available_ts,
                ),
            )
        )


def _label_value_records(
    records: Iterable[LabelValueRecord | Mapping[str, Any]] | None,
) -> tuple[LabelValueRecord | Mapping[str, Any], ...] | None:
    if records is None or isinstance(records, str):
        return None
    try:
        return tuple(records)
    except TypeError:
        return None


def _lookup_label_mapping(
    values: Mapping[str, Any],
    label: _RegisteredLabelAuditInput,
) -> Any:
    for key in (label.label_version_id, label.label_id, label.label_spec_id):
        if key in values:
            return values[key]
    return None


def _field(record: LabelValueRecord | Mapping[str, Any], field_name: str) -> object:
    if isinstance(record, Mapping):
        payload: Mapping[str, Any] = record
        nested_value = payload.get("value")
        if field_name not in payload and isinstance(nested_value, Mapping):
            payload = nested_value
        return payload.get(field_name)
    return getattr(record, field_name, None)


def _datetime_field(
    label: _RegisteredLabelAuditInput,
    record: LabelValueRecord | Mapping[str, Any],
    field_name: str,
    index: int,
    findings: list[LabelLeakageAuditFinding],
) -> datetime | None:
    value = _field(record, field_name)
    try:
        return _require_datetime(value, field_name)
    except LabelLeakageAuditError:
        findings.append(
            _finding(
                label,
                check="label_available_ts_present" if field_name == "label_available_ts" else (
                    "label_value_timestamp_present"
                ),
                message=f"{field_name} is missing or not timezone-aware; audit fails closed",
                offending_reference={
                    "source_index": index,
                    "field": field_name,
                },
            )
        )
        return None


def _require_datetime(value: object, field_name: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise LabelLeakageAuditError(f"{field_name} must be an ISO datetime") from exc
    else:
        raise LabelLeakageAuditError(f"{field_name} must be a timezone-aware datetime")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise LabelLeakageAuditError(f"{field_name} must be timezone-aware")
    return parsed


def _reference_sets(feature_references: FeatureReferences) -> tuple[frozenset[str], ...]:
    items = _feature_items(feature_references)
    return tuple(
        frozenset(
            _normalize_reference(value)
            for value in _string_values(item)
            if _normalize_reference(value)
        )
        for item in items
    )


def _feature_items(feature_references: FeatureReferences) -> tuple[object, ...]:
    if feature_references is None:
        return ()
    if isinstance(feature_references, str):
        return (feature_references,)
    if isinstance(feature_references, Mapping):
        for key in (
            "features",
            "feature_references",
            "requested_features",
            "requested_inputs",
        ):
            value = feature_references.get(key)
            if value is None:
                continue
            if isinstance(value, str):
                return (value,)
            if isinstance(value, Iterable):
                return tuple(value)
            return ()
        return (feature_references,)
    if isinstance(feature_references, Iterable):
        return tuple(feature_references)
    return ()


def _string_values(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Mapping):
        values: list[str] = []
        for item in value.values():
            values.extend(_string_values(item))
        return tuple(values)
    if isinstance(value, Sequence) and not isinstance(value, bytes | bytearray):
        values: list[str] = []
        for item in value:
            values.extend(_string_values(item))
        return tuple(values)
    return ()


def _normalize_reference(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _finding(
    label: _RegisteredLabelAuditInput,
    *,
    check: str,
    message: str,
    offending_reference: Mapping[str, Any] | None = None,
    severity: LabelLeakageAuditSeverity = LabelLeakageAuditSeverity.BLOCKING,
) -> LabelLeakageAuditFinding:
    return LabelLeakageAuditFinding(
        check=check,
        severity=severity,
        label_version_id=label.label_version_id,
        label_id=label.label_id,
        label_spec_id=label.label_spec_id,
        message=message,
        offending_reference=offending_reference,
    )


def _timestamp_payload(source_index: int, **timestamps: datetime) -> dict[str, JsonValue]:
    payload: dict[str, JsonValue] = {"source_index": source_index}
    for key, value in timestamps.items():
        payload[key] = value.isoformat()
    return payload


def _json_mapping(value: Mapping[str, Any]) -> dict[str, JsonValue]:
    return {str(key): _json_scalar(item) for key, item in value.items()}


def _json_scalar(value: object) -> JsonValue:
    if isinstance(value, datetime):
        return value.isoformat()
    if value is None or isinstance(value, bool | int | float | str):
        return value
    return str(value)


__all__ = [
    "LabelLeakageAuditError",
    "LabelLeakageAuditFinding",
    "LabelLeakageAuditReport",
    "LabelLeakageAuditSeverity",
    "LabelLeakageAuditStatus",
    "audit_label_registry",
    "audit_registered_label",
    "audit_registered_labels",
]
