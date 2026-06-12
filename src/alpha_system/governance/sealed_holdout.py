"""Sealed holdout declarations, append-only access logs, and fail-closed gates."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import StrEnum
from pathlib import Path
from types import NoneType
from typing import Any

from alpha_system.governance.ids import (
    GovernanceIdError,
    GovernanceIdKind,
    generate_governance_id,
    validate_governance_id,
)
from alpha_system.governance.serialization import (
    GovernanceSerializationError,
    JsonValue,
    canonical_serialize,
    deserialize,
)
from alpha_system.governance.validation import (
    ExpectedType,
    GovernanceValidationError,
    ValidationIssue,
    require_mapping,
    validate_schema,
)

SEALED_HOLDOUT_WINDOW_REQUIRED_FIELDS = (
    "window_id",
    "partition_spec",
    "start_date",
    "status",
    "declared_at",
    "sealed_by",
)
SEALED_HOLDOUT_WINDOW_OPTIONAL_FIELDS = (
    "end_date",
    "rolling",
    "provenance",
    "superseded_declaration",
    "redeclaration_reason",
)
SEALED_HOLDOUT_WINDOW_ALLOWED_FIELDS = (
    SEALED_HOLDOUT_WINDOW_REQUIRED_FIELDS + SEALED_HOLDOUT_WINDOW_OPTIONAL_FIELDS
)
SEALED_HOLDOUT_WINDOW_ID_COMPONENT_FIELDS = (
    "partition_spec",
    "start_date",
    "end_date",
    "rolling",
    "declared_at",
    "sealed_by",
)
SEALED_HOLDOUT_WINDOW_FIELD_TYPES: dict[str, ExpectedType] = {
    "window_id": str,
    "partition_spec": dict,
    "start_date": str,
    "end_date": (str, NoneType),
    "rolling": bool,
    "status": str,
    "declared_at": str,
    "sealed_by": str,
    "provenance": dict,
    "superseded_declaration": dict,
    "redeclaration_reason": str,
}

HOLDOUT_ACCESS_LOG_RECORD_REQUIRED_FIELDS = (
    "access_id",
    "study_spec_id",
    "actor",
    "timestamp",
    "access_type",
    "rationale",
)
HOLDOUT_ACCESS_LOG_RECORD_ID_COMPONENT_FIELDS = tuple(
    field for field in HOLDOUT_ACCESS_LOG_RECORD_REQUIRED_FIELDS if field != "access_id"
)
HOLDOUT_ACCESS_LOG_RECORD_FIELD_TYPES: dict[str, ExpectedType] = {
    "access_id": str,
    "study_spec_id": str,
    "actor": str,
    "timestamp": str,
    "access_type": str,
    "rationale": str,
}

_VAGUE_TEXT = {
    "",
    "-",
    "n/a",
    "na",
    "none",
    "null",
    "tbd",
    "todo",
    "unknown",
    "placeholder",
    "to be defined",
    "to be determined",
}


class SealedHoldoutStatus(StrEnum):
    """Closed status values for a declared holdout window."""

    DECLARED = "DECLARED"
    SEALED = "SEALED"
    BREACHED = "BREACHED"


class HoldoutAccessType(StrEnum):
    """Closed data-access classes for holdout access logging."""

    TRAINING = "TRAINING"
    VALIDATION = "VALIDATION"
    LOCKED_TEST = "LOCKED_TEST"


@dataclass(frozen=True, slots=True)
class SealedHoldoutWindow:
    """Validated, value-free sealed holdout declaration."""

    window_id: str
    partition_spec: dict[str, JsonValue]
    start_date: str
    end_date: str | None
    status: SealedHoldoutStatus
    declared_at: str
    sealed_by: str
    rolling: bool = False
    provenance: dict[str, JsonValue] | None = None
    superseded_declaration: dict[str, JsonValue] | None = None
    redeclaration_reason: str | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> SealedHoldoutWindow:
        """Build a sealed holdout window from a mapping after validation."""

        return validate_sealed_holdout_window(payload)

    @classmethod
    def from_canonical_json(cls, text: str) -> SealedHoldoutWindow:
        """Deserialize canonical JSON and validate the resulting window."""

        value = deserialize(text)
        mapping = require_mapping(value, object_name="SealedHoldoutWindow")
        return validate_sealed_holdout_window(mapping)

    @property
    def is_active(self) -> bool:
        """Return true when the window is still non-breached."""

        return self.status is not SealedHoldoutStatus.BREACHED

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a strict JSON-compatible representation."""

        payload: dict[str, JsonValue] = {
            "window_id": self.window_id,
            "partition_spec": dict(self.partition_spec),
            "start_date": self.start_date,
            "end_date": self.end_date,
            "status": self.status.value,
            "declared_at": self.declared_at,
            "sealed_by": self.sealed_by,
        }
        if self.rolling:
            payload["rolling"] = self.rolling
        if self.provenance is not None:
            payload["provenance"] = dict(self.provenance)
        if self.superseded_declaration is not None:
            payload["superseded_declaration"] = dict(self.superseded_declaration)
        if self.redeclaration_reason is not None:
            payload["redeclaration_reason"] = self.redeclaration_reason
        return payload

    def to_canonical_json(self) -> str:
        """Serialize through the governance canonical JSON primitive."""

        return canonical_serialize(self.to_dict())


@dataclass(frozen=True, slots=True)
class SealedHoldoutStatusAuditRecord:
    """Audit record returned by monotonic holdout status transitions."""

    window_id: str
    previous_status: SealedHoldoutStatus
    next_status: SealedHoldoutStatus
    actor: str
    timestamp: str
    rationale: str

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a strict JSON-compatible audit record."""

        return {
            "window_id": self.window_id,
            "previous_status": self.previous_status.value,
            "next_status": self.next_status.value,
            "actor": self.actor,
            "timestamp": self.timestamp,
            "rationale": self.rationale,
        }


@dataclass(frozen=True, slots=True)
class HoldoutAccessLogRecord:
    """Validated append-only access-log entry for holdout-touching access."""

    access_id: str
    study_spec_id: str
    actor: str
    timestamp: str
    access_type: HoldoutAccessType
    rationale: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> HoldoutAccessLogRecord:
        """Build an access-log record from a mapping after validation."""

        return validate_holdout_access_log_record(payload)

    @classmethod
    def from_canonical_json(cls, text: str) -> HoldoutAccessLogRecord:
        """Deserialize canonical JSON and validate the resulting record."""

        value = deserialize(text)
        mapping = require_mapping(value, object_name="HoldoutAccessLog")
        return validate_holdout_access_log_record(mapping)

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a strict JSON-compatible representation."""

        return {
            "access_id": self.access_id,
            "study_spec_id": self.study_spec_id,
            "actor": self.actor,
            "timestamp": self.timestamp,
            "access_type": self.access_type.value,
            "rationale": self.rationale,
        }

    def to_canonical_json(self) -> str:
        """Serialize through the governance canonical JSON primitive."""

        return canonical_serialize(self.to_dict())


@dataclass(frozen=True, slots=True)
class HoldoutAccessDecision:
    """Result of evaluating one data-access request against the active holdout."""

    active_window_id: str
    intersects_holdout: bool
    contamination_detected: bool
    access_record: HoldoutAccessLogRecord | None

    def to_dict(self) -> dict[str, JsonValue]:
        """Return explicit value-free decision metadata."""

        return {
            "active_window_id": self.active_window_id,
            "intersects_holdout": self.intersects_holdout,
            "contamination_detected": self.contamination_detected,
            "access_record": (
                self.access_record.to_dict() if self.access_record is not None else None
            ),
        }


class SealedHoldoutRegistry:
    """Read-only declaration registry with exactly-one-active enforcement."""

    def __init__(self, path: str | Path | None) -> None:
        self.path = resolve_sealed_holdout_registry_path(path)

    def load_windows(self) -> tuple[SealedHoldoutWindow, ...]:
        """Read and validate every sealed holdout declaration from the registry."""

        if not self.path.exists():
            raise GovernanceValidationError(
                ValidationIssue(
                    field="sealed_holdout_registry_path",
                    code="missing_sealed_holdout_registry",
                    message="sealed holdout registry path is required",
                    expected="existing JSON declaration file or directory",
                    actual=str(self.path),
                )
            )
        paths = (
            tuple(sorted(self.path.glob("*.json")))
            if self.path.is_dir()
            else (self.path,)
        )
        if not paths:
            raise GovernanceValidationError(
                ValidationIssue(
                    field="sealed_holdout_registry_path",
                    code="empty_sealed_holdout_registry",
                    message="sealed holdout registry contains no JSON declarations",
                    expected="one active SealedHoldoutWindow declaration",
                    actual=str(self.path),
                )
            )

        windows: list[SealedHoldoutWindow] = []
        for source in paths:
            windows.extend(load_sealed_holdout_windows(source))
        return tuple(windows)

    def active_window(self) -> SealedHoldoutWindow:
        """Return the single non-breached window or fail closed."""

        return require_single_active_holdout_window(self.load_windows())

    def gate_window(self) -> SealedHoldoutWindow:
        """Return the active window, or the sole breached window for gate blocking."""

        windows = self.load_windows()
        active = [window for window in windows if window.is_active]
        if len(active) == 1:
            return active[0]
        if len(active) > 1:
            raise _multiple_active_windows_issue(active)
        if len(windows) == 1 and windows[0].status is SealedHoldoutStatus.BREACHED:
            return windows[0]
        raise GovernanceValidationError(
            ValidationIssue(
                field="sealed_holdout_registry",
                code="missing_active_sealed_holdout_window",
                message="exactly one active sealed holdout window is required",
                expected="one DECLARED or SEALED window",
                actual=f"{len(active)} active windows",
            )
        )

    def summary(self) -> dict[str, JsonValue]:
        """Return a value-free summary of declarations."""

        windows = self.load_windows()
        active = [window for window in windows if window.is_active]
        return {
            "registry_path": str(self.path),
            "window_count": len(windows),
            "active_window_count": len(active),
            "windows": [
                {
                    "window_id": window.window_id,
                    "status": window.status.value,
                    "start_date": window.start_date,
                    "end_date": window.end_date,
                }
                for window in windows
            ],
        }


class HoldoutAccessLog:
    """Append-only JSONL persistence for validated holdout access records."""

    def __init__(self, path: str | Path | None) -> None:
        self.path = resolve_holdout_access_log_path(path)

    def load_records(self) -> tuple[HoldoutAccessLogRecord, ...]:
        """Read all JSONL access records fail-closed from the log path."""

        _require_existing_file(
            self.path,
            field="holdout_access_log_path",
            code="missing_holdout_access_log",
            message="HoldoutAccessLog file is required for sealed-window access",
        )
        records: list[HoldoutAccessLogRecord] = []
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise GovernanceValidationError(
                ValidationIssue(
                    field="holdout_access_log_path",
                    code="holdout_access_log_read_failed",
                    message="HoldoutAccessLog path could not be read",
                    expected="readable text JSONL access log",
                    actual=f"{self.path}: {exc}",
                )
            ) from exc
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                value = deserialize(line)
                mapping = require_mapping(value, object_name="HoldoutAccessLog")
                records.append(validate_holdout_access_log_record(mapping))
            except (GovernanceSerializationError, GovernanceValidationError) as exc:
                raise GovernanceValidationError(
                    ValidationIssue(
                        field=f"holdout_access_log_path:{line_number}",
                        code="invalid_holdout_access_log_row",
                        message="HoldoutAccessLog row is not a valid canonical record",
                        expected="canonical HoldoutAccessLog JSON line",
                        actual=str(exc),
                    )
                ) from exc
        return tuple(records)

    def require_writable(self) -> None:
        """Fail closed unless the log exists and can be appended to."""

        _require_existing_file(
            self.path,
            field="holdout_access_log_path",
            code="missing_holdout_access_log",
            message="HoldoutAccessLog file is required for sealed-window access",
        )
        _require_writable_file(self.path)

    def append_record(self, record: HoldoutAccessLogRecord) -> HoldoutAccessLogRecord:
        """Append one validated access record."""

        valid_record = validate_holdout_access_log_record(record.to_dict())
        self.require_writable()
        try:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(valid_record.to_canonical_json())
                handle.write("\n")
        except OSError as exc:
            raise GovernanceValidationError(
                ValidationIssue(
                    field="holdout_access_log_path",
                    code="holdout_access_log_append_failed",
                    message="HoldoutAccessLog path could not be appended",
                    expected="appendable text JSONL access log",
                    actual=f"{self.path}: {exc}",
                )
            ) from exc
        return valid_record


def create_sealed_holdout_window(
    *,
    partition_spec: dict[str, JsonValue],
    start_date: str,
    end_date: str | None,
    status: SealedHoldoutStatus | str,
    declared_at: str,
    sealed_by: str,
    rolling: bool = False,
    provenance: dict[str, JsonValue] | None = None,
    superseded_declaration: dict[str, JsonValue] | None = None,
    redeclaration_reason: str | None = None,
) -> SealedHoldoutWindow:
    """Create a validated sealed holdout declaration with a stable ID."""

    payload: dict[str, JsonValue] = {
        "partition_spec": dict(partition_spec),
        "start_date": start_date,
        "end_date": end_date,
        "status": SealedHoldoutStatus(status).value,
        "declared_at": declared_at,
        "sealed_by": sealed_by,
    }
    if rolling:
        payload["rolling"] = rolling
    if provenance is not None:
        payload["provenance"] = dict(provenance)
    if superseded_declaration is not None:
        payload["superseded_declaration"] = dict(superseded_declaration)
    if redeclaration_reason is not None:
        payload["redeclaration_reason"] = redeclaration_reason
    payload["window_id"] = generate_sealed_holdout_window_id(payload)
    return validate_sealed_holdout_window(payload)


def generate_sealed_holdout_window_id(payload: Mapping[str, Any]) -> str:
    """Generate a stable SealedHoldoutWindow ID from the window contract."""

    mapping = require_mapping(payload, object_name="SealedHoldoutWindow")
    components = {
        field: mapping[field]
        for field in SEALED_HOLDOUT_WINDOW_ID_COMPONENT_FIELDS
        if field in mapping
    }
    return generate_governance_id(GovernanceIdKind.SEALED_HOLDOUT_WINDOW, components)


def validate_sealed_holdout_window(payload: Mapping[str, Any]) -> SealedHoldoutWindow:
    """Validate a SealedHoldoutWindow mapping fail-closed and return a record."""

    mapping = validate_schema(
        payload,
        required_fields=SEALED_HOLDOUT_WINDOW_REQUIRED_FIELDS,
        field_types=SEALED_HOLDOUT_WINDOW_FIELD_TYPES,
        allowed_fields=SEALED_HOLDOUT_WINDOW_ALLOWED_FIELDS,
        object_name="SealedHoldoutWindow",
    )

    issues: list[ValidationIssue] = []
    try:
        validate_governance_id(
            mapping["window_id"],
            expected_kind=GovernanceIdKind.SEALED_HOLDOUT_WINDOW,
        )
    except GovernanceIdError as exc:
        issues.append(_id_issue("window_id", exc, GovernanceIdKind.SEALED_HOLDOUT_WINDOW))
    status = _parse_holdout_status(mapping["status"], issues)
    start = _parse_date(mapping["start_date"], field="start_date", issues=issues)
    rolling = mapping.get("rolling", False)
    end = None
    if mapping.get("end_date") is None:
        if rolling is not True:
            issues.append(
                ValidationIssue(
                    field="end_date",
                    code="missing_non_rolling_holdout_end_date",
                    message=(
                        "SealedHoldoutWindow.end_date is required unless rolling "
                        "open-ended coverage is explicitly declared"
                    ),
                    expected="YYYY-MM-DD or rolling=true",
                    actual="missing/null end_date with rolling=false",
                )
            )
    else:
        end = _parse_date(mapping["end_date"], field="end_date", issues=issues)
    if start is not None and end is not None and start > end:
        issues.append(
            ValidationIssue(
                field="date_range",
                code="invalid_holdout_date_range",
                message="SealedHoldoutWindow.start_date must be on or before end_date",
                expected="start_date <= end_date",
                actual=f"{mapping['start_date']} > {mapping['end_date']}",
            )
        )
    issues.extend(_validate_partition_spec(mapping["partition_spec"]))
    issues.extend(_validate_utc_timestamp(mapping["declared_at"], field="declared_at"))
    issues.extend(_validate_text_value(mapping["sealed_by"], field="sealed_by"))
    if "provenance" in mapping:
        issues.extend(_validate_metadata_mapping(mapping["provenance"], field="provenance"))
    if "superseded_declaration" in mapping:
        issues.extend(
            _validate_metadata_mapping(
                mapping["superseded_declaration"],
                field="superseded_declaration",
            )
        )
    if "redeclaration_reason" in mapping:
        issues.extend(
            _validate_text_value(mapping["redeclaration_reason"], field="redeclaration_reason")
        )
    issues.extend(
        _validate_canonical_serializable(
            mapping,
            fields=SEALED_HOLDOUT_WINDOW_ALLOWED_FIELDS,
        )
    )
    if not issues:
        expected_id = generate_sealed_holdout_window_id(mapping)
        if mapping["window_id"] != expected_id:
            issues.append(
                ValidationIssue(
                    field="window_id",
                    code="sealed_holdout_window_id_mismatch",
                    message=(
                        "SealedHoldoutWindow.window_id must match deterministic "
                        "SealedHoldoutWindow content"
                    ),
                    expected=expected_id,
                    actual=str(mapping["window_id"]),
                )
            )

    if issues:
        raise GovernanceValidationError(issues)
    assert status is not None
    return SealedHoldoutWindow(
        window_id=mapping["window_id"],
        partition_spec=dict(mapping["partition_spec"]),
        start_date=mapping["start_date"],
        end_date=mapping.get("end_date"),
        status=status,
        declared_at=mapping["declared_at"],
        sealed_by=mapping["sealed_by"],
        rolling=rolling,
        provenance=dict(mapping["provenance"]) if "provenance" in mapping else None,
        superseded_declaration=(
            dict(mapping["superseded_declaration"])
            if "superseded_declaration" in mapping
            else None
        ),
        redeclaration_reason=mapping.get("redeclaration_reason"),
    )


def create_holdout_access_log_record(
    *,
    study_spec_id: str,
    actor: str,
    timestamp: str,
    access_type: HoldoutAccessType | str,
    rationale: str,
) -> HoldoutAccessLogRecord:
    """Create a validated holdout access-log record with a deterministic ID."""

    payload: dict[str, JsonValue] = {
        "study_spec_id": study_spec_id,
        "actor": actor,
        "timestamp": timestamp,
        "access_type": HoldoutAccessType(access_type).value,
        "rationale": rationale,
    }
    payload["access_id"] = generate_holdout_access_id(payload)
    return validate_holdout_access_log_record(payload)


def generate_holdout_access_id(payload: Mapping[str, Any]) -> str:
    """Generate the deterministic HoldoutAccessLog access ID."""

    mapping = require_mapping(payload, object_name="HoldoutAccessLog")
    components = {
        field: _access_id_component(field, mapping[field])
        for field in HOLDOUT_ACCESS_LOG_RECORD_ID_COMPONENT_FIELDS
        if field in mapping
    }
    return generate_governance_id(GovernanceIdKind.HOLDOUT_ACCESS_LOG, components)


def validate_holdout_access_log_record(payload: Mapping[str, Any]) -> HoldoutAccessLogRecord:
    """Validate a HoldoutAccessLog mapping fail-closed and return a record."""

    mapping = validate_schema(
        payload,
        required_fields=HOLDOUT_ACCESS_LOG_RECORD_REQUIRED_FIELDS,
        field_types=HOLDOUT_ACCESS_LOG_RECORD_FIELD_TYPES,
        allowed_fields=HOLDOUT_ACCESS_LOG_RECORD_REQUIRED_FIELDS,
        object_name="HoldoutAccessLog",
    )

    issues: list[ValidationIssue] = []
    try:
        validate_governance_id(
            mapping["access_id"],
            expected_kind=GovernanceIdKind.HOLDOUT_ACCESS_LOG,
        )
    except GovernanceIdError as exc:
        issues.append(_id_issue("access_id", exc, GovernanceIdKind.HOLDOUT_ACCESS_LOG))
    try:
        validate_governance_id(mapping["study_spec_id"], expected_kind=GovernanceIdKind.STUDY_SPEC)
    except GovernanceIdError as exc:
        issues.append(_id_issue("study_spec_id", exc, GovernanceIdKind.STUDY_SPEC))
    access_type = _parse_access_type(mapping["access_type"], issues)
    issues.extend(_validate_text_value(mapping["actor"], field="actor"))
    issues.extend(_validate_utc_timestamp(mapping["timestamp"], field="timestamp"))
    issues.extend(_validate_text_value(mapping["rationale"], field="rationale"))
    issues.extend(
        _validate_canonical_serializable(
            mapping,
            fields=HOLDOUT_ACCESS_LOG_RECORD_REQUIRED_FIELDS,
        )
    )
    if not issues:
        expected_id = generate_holdout_access_id(mapping)
        if mapping["access_id"] != expected_id:
            issues.append(
                ValidationIssue(
                    field="access_id",
                    code="holdout_access_id_mismatch",
                    message="HoldoutAccessLog.access_id must match deterministic content",
                    expected=expected_id,
                    actual=str(mapping["access_id"]),
                )
            )

    if issues:
        raise GovernanceValidationError(issues)
    assert access_type is not None
    return HoldoutAccessLogRecord(
        access_id=mapping["access_id"],
        study_spec_id=mapping["study_spec_id"],
        actor=mapping["actor"],
        timestamp=mapping["timestamp"],
        access_type=access_type,
        rationale=mapping["rationale"],
    )


def load_sealed_holdout_windows(path: str | Path) -> tuple[SealedHoldoutWindow, ...]:
    """Load one declaration file containing a window, a list, or a windows mapping."""

    source = Path(path)
    try:
        value = deserialize(source.read_text(encoding="utf-8"))
    except (OSError, GovernanceSerializationError) as exc:
        raise GovernanceValidationError(
            ValidationIssue(
                field="sealed_holdout_registry_path",
                code="sealed_holdout_declaration_read_failed",
                message="sealed holdout declaration could not be read as JSON",
                expected="readable JSON declaration file",
                actual=f"{source}: {exc}",
            )
        ) from exc

    if isinstance(value, list):
        items = value
    elif isinstance(value, Mapping) and "windows" in value:
        windows = value["windows"]
        if not isinstance(windows, list):
            raise GovernanceValidationError(
                ValidationIssue(
                    field="windows",
                    code="invalid_sealed_holdout_windows_type",
                    message="sealed holdout windows must be a list",
                    expected="list of SealedHoldoutWindow mappings",
                    actual=type(windows).__name__,
                )
            )
        items = windows
    else:
        items = [value]

    records: list[SealedHoldoutWindow] = []
    for index, item in enumerate(items):
        try:
            mapping = require_mapping(item, object_name="SealedHoldoutWindow")
            records.append(validate_sealed_holdout_window(mapping))
        except GovernanceValidationError as exc:
            raise GovernanceValidationError(
                ValidationIssue(
                    field=f"sealed_holdout_window[{index}]",
                    code="invalid_sealed_holdout_window",
                    message="sealed holdout declaration is invalid",
                    expected="valid SealedHoldoutWindow mapping",
                    actual=str(exc),
                )
            ) from exc
    return tuple(records)


def require_single_active_holdout_window(
    windows: Iterable[SealedHoldoutWindow | Mapping[str, Any]],
) -> SealedHoldoutWindow:
    """Fail closed unless exactly one declared window is non-breached."""

    validated = _coerce_windows(windows)
    active = [window for window in validated if window.is_active]
    if len(active) == 1:
        return active[0]
    if len(active) > 1:
        raise _multiple_active_windows_issue(active)
    raise GovernanceValidationError(
        ValidationIssue(
            field="sealed_holdout_registry",
            code="missing_active_sealed_holdout_window",
            message="exactly one active sealed holdout window is required",
            expected="one DECLARED or SEALED window",
            actual="0 active windows",
        )
    )


def transition_sealed_holdout_status(
    window: SealedHoldoutWindow | Mapping[str, Any],
    *,
    next_status: SealedHoldoutStatus | str,
    actor: str,
    timestamp: str,
    rationale: str,
) -> tuple[SealedHoldoutWindow, SealedHoldoutStatusAuditRecord]:
    """Return a monotonic status transition plus an explicit audit record."""

    active_window = (
        validate_sealed_holdout_window(window.to_dict())
        if isinstance(window, SealedHoldoutWindow)
        else validate_sealed_holdout_window(window)
    )
    issues: list[ValidationIssue] = []
    status = _parse_holdout_status(next_status, issues)
    issues.extend(_validate_text_value(actor, field="actor"))
    issues.extend(_validate_utc_timestamp(timestamp, field="timestamp"))
    issues.extend(_validate_text_value(rationale, field="rationale"))
    if status is not None:
        current_rank = _status_rank(active_window.status)
        next_rank = _status_rank(status)
        if (
            active_window.status is SealedHoldoutStatus.BREACHED
            and status is not active_window.status
        ):
            issues.append(
                ValidationIssue(
                    field="status",
                    code="sealed_holdout_breach_is_terminal",
                    message="a BREACHED sealed holdout window cannot return to active status",
                    expected=SealedHoldoutStatus.BREACHED.value,
                    actual=status.value,
                )
            )
        elif next_rank < current_rank:
            issues.append(
                ValidationIssue(
                    field="status",
                    code="non_monotonic_holdout_status_transition",
                    message="sealed holdout status transitions must be monotonic",
                    expected=f">= {active_window.status.value}",
                    actual=status.value,
                )
            )
    if issues:
        raise GovernanceValidationError(issues)
    assert status is not None
    payload = active_window.to_dict()
    payload["status"] = status.value
    updated = validate_sealed_holdout_window(payload)
    audit = SealedHoldoutStatusAuditRecord(
        window_id=active_window.window_id,
        previous_status=active_window.status,
        next_status=status,
        actor=actor,
        timestamp=timestamp,
        rationale=rationale,
    )
    return updated, audit


def emit_holdout_access_if_intersects(
    *,
    sealed_holdout_registry_path: str | Path | None,
    holdout_access_log_path: str | Path | None,
    study_spec_id: str,
    actor: str,
    access_type: HoldoutAccessType | str,
    rationale: str,
    timestamp: str | None = None,
    access_start_date: str | None = None,
    access_end_date: str | None = None,
    access_partition_spec: Mapping[str, Any] | None = None,
    authorized_evaluation_context: bool = False,
    fail_on_unauthorized_locked_test: bool = True,
) -> HoldoutAccessDecision:
    """Append an access-log record when declared access intersects the holdout."""

    active_window = SealedHoldoutRegistry(sealed_holdout_registry_path).active_window()
    access_kind = _coerce_access_type(access_type)
    intersects = access_intersects_holdout(
        active_window,
        access_start_date=access_start_date,
        access_end_date=access_end_date,
        access_partition_spec=access_partition_spec,
    )
    if not intersects:
        return HoldoutAccessDecision(
            active_window_id=active_window.window_id,
            intersects_holdout=False,
            contamination_detected=False,
            access_record=None,
        )

    record = create_holdout_access_log_record(
        study_spec_id=study_spec_id,
        actor=actor,
        timestamp=timestamp or utc_now_iso(),
        access_type=access_kind,
        rationale=rationale,
    )
    appended = HoldoutAccessLog(holdout_access_log_path).append_record(record)
    contamination = (
        access_kind is HoldoutAccessType.LOCKED_TEST and not authorized_evaluation_context
    )
    decision = HoldoutAccessDecision(
        active_window_id=active_window.window_id,
        intersects_holdout=True,
        contamination_detected=contamination,
        access_record=appended,
    )
    if contamination and fail_on_unauthorized_locked_test:
        raise GovernanceValidationError(
            ValidationIssue(
                field="holdout_access_log",
                code="unauthorized_locked_test_holdout_access",
                message=(
                    "LOCKED_TEST access intersected the sealed holdout outside an "
                    "authorized evaluation context"
                ),
                expected="authorized_evaluation_context=True",
                actual=appended.access_id,
            )
        )
    return decision


def access_intersects_holdout(
    window: SealedHoldoutWindow | Mapping[str, Any],
    *,
    access_start_date: str | None = None,
    access_end_date: str | None = None,
    access_partition_spec: Mapping[str, Any] | None = None,
) -> bool:
    """Conservatively determine whether access metadata overlaps the holdout."""

    active_window = (
        validate_sealed_holdout_window(window.to_dict())
        if isinstance(window, SealedHoldoutWindow)
        else validate_sealed_holdout_window(window)
    )
    start = access_start_date or active_window.start_date
    issues: list[ValidationIssue] = []
    access_start = _parse_date(start, field="access_start_date", issues=issues)
    access_end = (
        _parse_date(access_end_date, field="access_end_date", issues=issues)
        if access_end_date is not None
        else _effective_holdout_end(active_window)
    )
    if access_start is not None and access_end is not None and access_start > access_end:
        issues.append(
            ValidationIssue(
                field="access_date_range",
                code="invalid_access_date_range",
                message="access_start_date must be on or before access_end_date",
                expected="access_start_date <= access_end_date",
                actual=f"{start} > {access_end_date or 'open-ended'}",
            )
        )
    if access_partition_spec is not None:
        issues.extend(
            _validate_partition_spec(
                access_partition_spec,
                field="access_partition_spec",
            )
        )
    if issues:
        raise GovernanceValidationError(issues)
    assert access_start is not None
    assert access_end is not None
    holdout_start = date.fromisoformat(active_window.start_date)
    holdout_end = _effective_holdout_end(active_window)
    date_overlap = access_start <= holdout_end and holdout_start <= access_end
    if not date_overlap:
        return False
    return _partitions_intersect(active_window.partition_spec, access_partition_spec)


def resolve_sealed_holdout_registry_path(path: str | Path | None) -> Path:
    """Resolve an explicitly supplied holdout declaration path fail-closed."""

    if path is None or _normalize_text(path) in _VAGUE_TEXT:
        raise GovernanceValidationError(
            ValidationIssue(
                field="sealed_holdout_registry_path",
                code="missing_sealed_holdout_registry_path",
                message="sealed holdout registry path is required",
                expected="explicit path to a sealed holdout JSON file or directory",
                actual="missing",
            )
        )
    return Path(path).expanduser()


def resolve_holdout_access_log_path(path: str | Path | None) -> Path:
    """Resolve an explicitly supplied holdout access-log path fail-closed."""

    if path is None or _normalize_text(path) in _VAGUE_TEXT:
        raise GovernanceValidationError(
            ValidationIssue(
                field="holdout_access_log_path",
                code="missing_holdout_access_log_path",
                message="holdout access log path is required for sealed-window access",
                expected="explicit path to an existing writable HoldoutAccessLog JSONL file",
                actual="missing",
            )
        )
    return Path(path).expanduser()


def utc_now_iso() -> str:
    """Return a second-resolution UTC ISO-8601 timestamp ending in Z."""

    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _coerce_windows(
    windows: Iterable[SealedHoldoutWindow | Mapping[str, Any]],
) -> tuple[SealedHoldoutWindow, ...]:
    if isinstance(windows, Mapping) or isinstance(windows, str) or windows is None:
        raise GovernanceValidationError(
            ValidationIssue(
                field="sealed_holdout_windows",
                code="invalid_sealed_holdout_windows_type",
                message="sealed holdout declarations must be an iterable",
                expected="iterable of SealedHoldoutWindow or mapping",
                actual=type(windows).__name__,
            )
        )
    result: list[SealedHoldoutWindow] = []
    for index, window in enumerate(windows):
        if isinstance(window, SealedHoldoutWindow):
            result.append(validate_sealed_holdout_window(window.to_dict()))
        elif isinstance(window, Mapping):
            result.append(validate_sealed_holdout_window(window))
        else:
            raise GovernanceValidationError(
                ValidationIssue(
                    field=f"sealed_holdout_windows[{index}]",
                    code="invalid_sealed_holdout_window_type",
                    message="sealed holdout declarations must be records or mappings",
                    expected="SealedHoldoutWindow or mapping",
                    actual=type(window).__name__,
                )
            )
    return tuple(result)


def _multiple_active_windows_issue(
    active_windows: Iterable[SealedHoldoutWindow],
) -> GovernanceValidationError:
    active_ids = [window.window_id for window in active_windows]
    return GovernanceValidationError(
        ValidationIssue(
            field="sealed_holdout_registry",
            code="multiple_active_sealed_holdout_windows",
            message="exactly one active sealed holdout window is allowed platform-wide",
            expected="one DECLARED or SEALED window",
            actual=", ".join(active_ids),
        )
    )


def _parse_holdout_status(
    value: object,
    issues: list[ValidationIssue],
) -> SealedHoldoutStatus | None:
    try:
        return SealedHoldoutStatus(value)
    except ValueError:
        issues.append(
            ValidationIssue(
                field="status",
                code="invalid_sealed_holdout_status",
                message="SealedHoldoutWindow.status must be declared",
                expected=" | ".join(status.value for status in SealedHoldoutStatus),
                actual=str(value),
            )
        )
        return None


def _parse_access_type(value: object, issues: list[ValidationIssue]) -> HoldoutAccessType | None:
    try:
        return HoldoutAccessType(value)
    except ValueError:
        issues.append(
            ValidationIssue(
                field="access_type",
                code="invalid_holdout_access_type",
                message="HoldoutAccessLog.access_type must be declared",
                expected=" | ".join(access_type.value for access_type in HoldoutAccessType),
                actual=str(value),
            )
        )
        return None


def _coerce_access_type(value: HoldoutAccessType | str) -> HoldoutAccessType:
    try:
        return HoldoutAccessType(value)
    except ValueError as exc:
        raise GovernanceValidationError(
            ValidationIssue(
                field="access_type",
                code="invalid_holdout_access_type",
                message="HoldoutAccessLog.access_type must be declared",
                expected=" | ".join(access_type.value for access_type in HoldoutAccessType),
                actual=str(value),
            )
        ) from exc


def _status_rank(status: SealedHoldoutStatus) -> int:
    return {
        SealedHoldoutStatus.DECLARED: 0,
        SealedHoldoutStatus.SEALED: 1,
        SealedHoldoutStatus.BREACHED: 2,
    }[status]


def _parse_date(value: object, *, field: str, issues: list[ValidationIssue]) -> date | None:
    if not isinstance(value, str):
        issues.append(
            ValidationIssue(
                field=field,
                code="invalid_date_type",
                message=f"{field} must be an ISO calendar date string",
                expected="YYYY-MM-DD",
                actual=type(value).__name__,
            )
        )
        return None
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        issues.append(
            ValidationIssue(
                field=field,
                code="invalid_date",
                message=f"{field} must be a parseable ISO calendar date",
                expected="YYYY-MM-DD",
                actual=value,
            )
        )
        return None
    if "T" in value:
        issues.append(
            ValidationIssue(
                field=field,
                code="invalid_date",
                message=f"{field} must be a date, not a timestamp",
                expected="YYYY-MM-DD",
                actual=value,
            )
        )
        return None
    return parsed


def _effective_holdout_end(window: SealedHoldoutWindow) -> date:
    if window.rolling or window.end_date is None:
        return date.max
    return date.fromisoformat(window.end_date)


def _validate_utc_timestamp(value: object, *, field: str) -> list[ValidationIssue]:
    if not isinstance(value, str) or not value.endswith("Z"):
        return [
            ValidationIssue(
                field=field,
                code="invalid_utc_timestamp",
                message=f"{field} must be an ISO-8601 UTC timestamp ending in Z",
                expected="YYYY-MM-DDTHH:MM:SSZ",
                actual=str(value),
            )
        ]
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return [
            ValidationIssue(
                field=field,
                code="invalid_utc_timestamp",
                message=f"{field} must be a parseable ISO-8601 UTC timestamp",
                expected="YYYY-MM-DDTHH:MM:SSZ",
                actual=value,
            )
        ]
    if parsed.tzinfo is None or parsed.utcoffset() != datetime.now(UTC).utcoffset():
        return [
            ValidationIssue(
                field=field,
                code="invalid_utc_timestamp",
                message=f"{field} must use UTC timezone",
                expected="UTC timestamp ending in Z",
                actual=value,
            )
        ]
    return []


def _validate_partition_spec(
    value: Mapping[str, Any],
    *,
    field: str = "partition_spec",
) -> list[ValidationIssue]:
    if not value:
        return [
            ValidationIssue(
                field=field,
                code="empty_required_field",
                message=f"{field} must contain explicit partition metadata",
                expected="non-empty mapping",
                actual="empty mapping",
            )
        ]
    return _validate_metadata_mapping(value, field=field)


def _validate_metadata_mapping(
    value: Mapping[str, Any],
    *,
    field: str,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not value:
        issues.append(
            ValidationIssue(
                field=field,
                code="empty_required_field",
                message=f"{field} must not be empty",
                expected="non-empty mapping",
                actual="empty mapping",
            )
        )
        return issues
    for key, item in value.items():
        key_field = f"{field}.{key}"
        if not isinstance(key, str) or _normalize_text(key) in _VAGUE_TEXT:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="invalid_metadata_key",
                    message=f"{field} keys must be explicit strings",
                    expected="non-empty explicit string key",
                    actual=str(key),
                )
            )
            continue
        issues.extend(_validate_substantive_value(item, field=key_field))
    return issues


def _validate_substantive_value(value: Any, *, field: str) -> list[ValidationIssue]:
    if value is None:
        return [
            ValidationIssue(
                field=field,
                code="null_required_field",
                message=f"{field} must not be null",
                expected="explicit metadata value",
                actual="NoneType",
            )
        ]
    if isinstance(value, str):
        if _normalize_text(value) in _VAGUE_TEXT:
            return [
                ValidationIssue(
                    field=field,
                    code="vague_required_field",
                    message=f"{field} must be explicit, not vague",
                    expected="substantive explicit value",
                    actual=value,
                )
            ]
        return []
    if isinstance(value, list):
        if not value:
            return [
                ValidationIssue(
                    field=field,
                    code="empty_required_field",
                    message=f"{field} must not be an empty list",
                    expected="non-empty value",
                    actual="empty list",
                )
            ]
        issues: list[ValidationIssue] = []
        for index, item in enumerate(value):
            issues.extend(_validate_substantive_value(item, field=f"{field}[{index}]"))
        return issues
    if isinstance(value, dict):
        return _validate_metadata_mapping(value, field=field)
    return []


def _validate_text_value(value: object, *, field: str) -> list[ValidationIssue]:
    if not isinstance(value, str) or _normalize_text(value) in _VAGUE_TEXT:
        return [
            ValidationIssue(
                field=field,
                code="empty_required_field",
                message=f"{field} must be an explicit non-empty string",
                expected="non-empty explicit string",
                actual=str(value),
            )
        ]
    return []


def _validate_canonical_serializable(
    mapping: Mapping[str, Any],
    *,
    fields: Iterable[str],
) -> list[ValidationIssue]:
    try:
        canonical_serialize(
            {field: _json_value(mapping[field]) for field in fields if field in mapping}
        )
    except (GovernanceSerializationError, ValueError) as exc:
        if isinstance(exc, GovernanceSerializationError):
            return [
                ValidationIssue(
                    field=exc.issue.path,
                    code=exc.issue.code,
                    message=exc.issue.message,
                    expected="canonical JSON-compatible governance record",
                    actual=exc.issue.path,
                )
            ]
        return [
            ValidationIssue(
                field="record",
                code="non_canonical_governance_record",
                message=str(exc),
                expected="canonical JSON-compatible governance record",
                actual=type(exc).__name__,
            )
        ]
    return []


def _json_value(value: Any) -> JsonValue:
    if isinstance(value, StrEnum):
        return value.value
    return value


def _access_id_component(field: str, value: Any) -> JsonValue:
    if field == "access_type":
        return HoldoutAccessType(value).value
    return value


def _id_issue(
    field: str,
    exc: GovernanceIdError,
    expected_kind: GovernanceIdKind,
) -> ValidationIssue:
    return ValidationIssue(
        field=field,
        code=exc.issue.code,
        message=exc.issue.message,
        expected=expected_kind.value,
        actual=str(exc.issue.value),
    )


def _partitions_intersect(
    holdout_partition: Mapping[str, Any],
    access_partition: Mapping[str, Any] | None,
) -> bool:
    if access_partition is None:
        return True
    shared_keys = set(holdout_partition) & set(access_partition)
    if not shared_keys:
        return True
    for key in shared_keys:
        holdout_values = _partition_values(holdout_partition[key])
        access_values = _partition_values(access_partition[key])
        if holdout_values and access_values and holdout_values.isdisjoint(access_values):
            return False
    return True


def _partition_values(value: Any) -> set[str]:
    if isinstance(value, list | tuple | set):
        result: set[str] = set()
        for item in value:
            result.update(_partition_values(item))
        return result
    if isinstance(value, dict):
        result: set[str] = set()
        for item in value.values():
            result.update(_partition_values(item))
        return result
    if value is None:
        return set()
    return {_normalize_text(str(value))}


def _require_existing_file(path: Path, *, field: str, code: str, message: str) -> None:
    if not path.exists() or not path.is_file():
        raise GovernanceValidationError(
            ValidationIssue(
                field=field,
                code=code,
                message=message,
                expected="existing text file",
                actual=str(path),
            )
        )


def _require_writable_file(path: Path) -> None:
    try:
        mode = path.stat().st_mode
    except OSError as exc:
        raise GovernanceValidationError(
            ValidationIssue(
                field="holdout_access_log_path",
                code="unwritable_holdout_access_log",
                message="HoldoutAccessLog file permissions could not be inspected",
                expected="writable text JSONL access log",
                actual=f"{path}: {exc}",
            )
        ) from exc
    if mode & 0o222 == 0:
        raise GovernanceValidationError(
            ValidationIssue(
                field="holdout_access_log_path",
                code="unwritable_holdout_access_log",
                message="HoldoutAccessLog file must be writable before access is allowed",
                expected="writable text JSONL access log",
                actual=str(path),
            )
        )
    try:
        with path.open("a", encoding="utf-8"):
            pass
    except OSError as exc:
        raise GovernanceValidationError(
            ValidationIssue(
                field="holdout_access_log_path",
                code="unwritable_holdout_access_log",
                message="HoldoutAccessLog file could not be opened for append",
                expected="writable text JSONL access log",
                actual=f"{path}: {exc}",
            )
        ) from exc


def _normalize_text(value: object) -> str:
    if isinstance(value, str):
        return " ".join(value.strip().lower().split())
    return str(value).strip().lower()


__all__ = [
    "HOLDOUT_ACCESS_LOG_RECORD_REQUIRED_FIELDS",
    "SEALED_HOLDOUT_WINDOW_REQUIRED_FIELDS",
    "HoldoutAccessDecision",
    "HoldoutAccessLog",
    "HoldoutAccessLogRecord",
    "HoldoutAccessType",
    "SealedHoldoutRegistry",
    "SealedHoldoutStatus",
    "SealedHoldoutStatusAuditRecord",
    "SealedHoldoutWindow",
    "access_intersects_holdout",
    "create_holdout_access_log_record",
    "create_sealed_holdout_window",
    "emit_holdout_access_if_intersects",
    "generate_holdout_access_id",
    "generate_sealed_holdout_window_id",
    "load_sealed_holdout_windows",
    "require_single_active_holdout_window",
    "resolve_holdout_access_log_path",
    "resolve_sealed_holdout_registry_path",
    "transition_sealed_holdout_status",
    "utc_now_iso",
    "validate_holdout_access_log_record",
    "validate_sealed_holdout_window",
]
