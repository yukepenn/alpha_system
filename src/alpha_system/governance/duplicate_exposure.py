"""Read-only duplicate/equivalent exposure guard for FeatureRequest records."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from alpha_system.core.registry import connect_registry
from alpha_system.governance.feature_request import (
    FeatureRequest,
    FeatureRequestApprovalStatus,
    generate_feature_request_id,
    validate_feature_request,
)
from alpha_system.governance.serialization import JsonValue


RegistryEntry = Mapping[str, Any]
RegistryReader = Callable[[], Iterable[RegistryEntry]] | Iterable[RegistryEntry] | str | Path

_IDENTIFIER_RE = re.compile(r"[^a-z0-9]+")
_OPERATION_SYNONYMS = {
    "change_pct": "return",
    "close_return": "return",
    "pct_change": "return",
    "percentage_change": "return",
    "return": "return",
    "returns": "return",
    "standard_score": "zscore",
    "standardize": "zscore",
    "standardized": "zscore",
    "z_score": "zscore",
    "zscore": "zscore",
}


class ExposureFindingKind(StrEnum):
    """Duplicate-exposure finding kinds."""

    DUPLICATE = "DUPLICATE"
    EQUIVALENT = "EQUIVALENT"


class ExposureFindingSeverity(StrEnum):
    """Duplicate-exposure finding severity metadata."""

    BLOCKING = "BLOCKING"
    WARNING = "WARNING"


class ExposureRegistryStatus(StrEnum):
    """Read-only registry read status."""

    CHECKED = "CHECKED"
    EMPTY = "EMPTY"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class ExposureFinding:
    """A likely duplicate or equivalent exposure found in the registry."""

    kind: ExposureFindingKind
    severity: ExposureFindingSeverity
    matched_registry_reference: dict[str, str]
    rationale: str

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a strict JSON-compatible representation."""

        return {
            "kind": self.kind.value,
            "severity": self.severity.value,
            "matched_registry_reference": dict(self.matched_registry_reference),
            "rationale": self.rationale,
        }


@dataclass(frozen=True, slots=True)
class ExposureCheckResult:
    """Structured result from a read-only duplicate-exposure check."""

    findings: tuple[ExposureFinding, ...]
    registry_status: ExposureRegistryStatus
    registry_entries_checked: int
    registry_error: str = ""

    @property
    def has_blocking_findings(self) -> bool:
        """Return whether any finding blocks acceptance without further action."""

        return any(
            finding.severity is ExposureFindingSeverity.BLOCKING
            for finding in self.findings
        )

    def to_notes(self) -> dict[str, JsonValue]:
        """Convert the check result to FeatureRequest guard notes."""

        return {
            "guard": "duplicate_exposure",
            "checked": True,
            "registry_status": self.registry_status.value,
            "registry_entries_checked": self.registry_entries_checked,
            "findings": [finding.to_dict() for finding in self.findings],
            "summary": _summary_for_result(self),
        }


@dataclass(frozen=True, slots=True)
class _ExposureSignature:
    factor_id: str
    factor_version: str
    name: str
    exposure_family: str
    operation: str
    window: str
    inputs: frozenset[str]
    tokens: frozenset[str]


def check_duplicate_exposure(
    feature_request: FeatureRequest | Mapping[str, Any],
    registry_reader: RegistryReader | object | None,
) -> ExposureCheckResult:
    """Check a `FeatureRequest` against an injected read-only registry view."""

    request = _coerce_feature_request(feature_request)
    entries, registry_status, registry_error = _read_registry_entries(registry_reader)
    if registry_status is ExposureRegistryStatus.UNAVAILABLE:
        return ExposureCheckResult(
            findings=(),
            registry_status=registry_status,
            registry_entries_checked=0,
            registry_error=registry_error,
        )
    if not entries:
        return ExposureCheckResult(
            findings=(),
            registry_status=ExposureRegistryStatus.EMPTY,
            registry_entries_checked=0,
        )

    request_signature = _request_signature(request)
    findings: list[ExposureFinding] = []
    seen_references: set[tuple[str, str, ExposureFindingKind]] = set()
    for entry in entries:
        entry_signature = _entry_signature(entry)
        duplicate_finding = _duplicate_finding(request_signature, entry_signature)
        if duplicate_finding is not None:
            key = _finding_key(duplicate_finding)
            if key not in seen_references:
                findings.append(duplicate_finding)
                seen_references.add(key)
            continue

        equivalent_finding = _equivalent_finding(request_signature, entry_signature)
        if equivalent_finding is not None:
            key = _finding_key(equivalent_finding)
            if key not in seen_references:
                findings.append(equivalent_finding)
                seen_references.add(key)

    return ExposureCheckResult(
        findings=tuple(findings),
        registry_status=ExposureRegistryStatus.CHECKED,
        registry_entries_checked=len(entries),
    )


def find_duplicate_exposures(
    feature_request: FeatureRequest | Mapping[str, Any],
    registry_reader: RegistryReader | object | None,
) -> tuple[ExposureFinding, ...]:
    """Pure finding-list entry point for duplicate/equivalent exposure checks."""

    return check_duplicate_exposure(feature_request, registry_reader).findings


def apply_duplicate_exposure_notes(
    feature_request: FeatureRequest | Mapping[str, Any],
    result: ExposureCheckResult,
) -> FeatureRequest:
    """Return a validated FeatureRequest with guard notes populated from a result."""

    request = _coerce_feature_request(feature_request)
    payload = request.to_dict()
    payload["duplicate_or_equivalent_exposure_notes"] = result.to_notes()
    if result.has_blocking_findings:
        payload["approval_status"] = FeatureRequestApprovalStatus.BLOCKED_DUPLICATE.value
    payload["feature_request_id"] = generate_feature_request_id(payload)
    return validate_feature_request(payload)


def check_and_update_feature_request(
    feature_request: FeatureRequest | Mapping[str, Any],
    registry_reader: RegistryReader | object | None,
) -> FeatureRequest:
    """Run the read-only guard and return a request carrying the guard notes."""

    result = check_duplicate_exposure(feature_request, registry_reader)
    return apply_duplicate_exposure_notes(feature_request, result)


def _coerce_feature_request(value: FeatureRequest | Mapping[str, Any]) -> FeatureRequest:
    if isinstance(value, FeatureRequest):
        return validate_feature_request(value.to_dict())
    return validate_feature_request(value)


def _read_registry_entries(
    registry_reader: RegistryReader | object | None,
) -> tuple[list[RegistryEntry], ExposureRegistryStatus, str]:
    if registry_reader is None:
        return [], ExposureRegistryStatus.UNAVAILABLE, "registry reader is missing"

    try:
        if isinstance(registry_reader, str | Path):
            entries = _read_registry_path(Path(registry_reader))
        elif hasattr(registry_reader, "read_factor_versions"):
            entries = registry_reader.read_factor_versions()
        elif callable(registry_reader):
            entries = registry_reader()
        else:
            entries = registry_reader
        return _coerce_registry_entries(entries), ExposureRegistryStatus.CHECKED, ""
    except Exception as exc:  # Guard must degrade safely when injected readers fail.
        return [], ExposureRegistryStatus.UNAVAILABLE, str(exc)


def _read_registry_path(registry_path: Path) -> list[RegistryEntry]:
    with connect_registry(registry_path, read_only=True) as connection:
        rows = connection.execute(
            """
            SELECT
                r.factor_id,
                r.name,
                r.description,
                r.metadata_json,
                v.factor_version,
                v.parameters_json
            FROM factor_versions v
            JOIN factor_registry r ON r.factor_id = v.factor_id
            ORDER BY r.factor_id, v.factor_version
            """
        ).fetchall()
    entries: list[RegistryEntry] = []
    for row in rows:
        payload = dict(row)
        payload["metadata"] = _loads(payload.pop("metadata_json"))
        payload["parameters"] = _loads(payload.pop("parameters_json"))
        entries.append(payload)
    return entries


def _coerce_registry_entries(entries: object) -> list[RegistryEntry]:
    if entries is None:
        return []
    if isinstance(entries, Mapping):
        if isinstance(entries.get("factors"), Iterable):
            entries = entries["factors"]
        elif isinstance(entries.get("entries"), Iterable):
            entries = entries["entries"]
        else:
            entries = entries.values()
    if not isinstance(entries, Iterable) or isinstance(entries, str | bytes):
        msg = "registry reader must return an iterable of mappings"
        raise TypeError(msg)
    result: list[RegistryEntry] = []
    for entry in entries:
        if isinstance(entry, Mapping):
            result.append(entry)
    return result


def _request_signature(request: FeatureRequest) -> _ExposureSignature:
    formula = request.formula_sketch
    inputs = frozenset(_normalize_identifier(value) for value in request.requested_inputs)
    formula_inputs = _input_names(formula)
    exposure_family = _first_text(
        formula,
        ("exposure_family", "exposure", "family", "factor_id", "name"),
    )
    operation = _normalize_operation(
        _first_text(formula, ("operation", "operator", "transform", "method", "formula"))
    )
    window = _window_value(formula)
    tokens = _tokens(
        {
            "requested_inputs": request.requested_inputs,
            "formula_sketch": formula,
            "availability_assumptions": request.availability_assumptions,
            "data_requirements": request.data_requirements,
        }
    )
    return _ExposureSignature(
        factor_id="",
        factor_version="",
        name="",
        exposure_family=_normalize_identifier(exposure_family),
        operation=operation,
        window=window,
        inputs=frozenset(value for value in inputs | formula_inputs if value),
        tokens=tokens,
    )


def _entry_signature(entry: RegistryEntry) -> _ExposureSignature:
    metadata = _mapping_value(entry.get("metadata"))
    parameters = _mapping_value(entry.get("parameters"))
    merged = {
        "entry": dict(entry),
        "metadata": metadata,
        "parameters": parameters,
    }
    factor_id = _normalize_identifier(_first_text(entry, ("factor_id", "id")))
    factor_version = _first_text(entry, ("factor_version", "version"))
    name = _normalize_identifier(_first_text(entry, ("name", "display_name")))
    exposure_family = _normalize_identifier(
        _first_text(
            entry,
            ("exposure_family", "family"),
            fallback=_first_text(metadata, ("exposure_family", "family")),
        )
        or _first_text(parameters, ("exposure_family", "family"))
    )
    operation = _normalize_operation(
        _first_text(
            entry,
            ("operation", "operator", "transform", "method"),
            fallback=_first_text(metadata, ("operation", "operator", "transform", "method")),
        )
        or _first_text(parameters, ("operation", "operator", "transform", "method"))
    )
    window = _window_value(parameters) or _window_value(metadata) or _window_value(entry)
    inputs = _input_names(entry) | _input_names(metadata) | _input_names(parameters)
    tokens = _tokens(merged)
    if factor_id:
        tokens = tokens | frozenset({factor_id})
    if name:
        tokens = tokens | frozenset({name})
    if exposure_family:
        tokens = tokens | frozenset({exposure_family})
    return _ExposureSignature(
        factor_id=factor_id,
        factor_version=factor_version,
        name=name,
        exposure_family=exposure_family,
        operation=operation,
        window=window,
        inputs=frozenset(value for value in inputs if value),
        tokens=tokens,
    )


def _duplicate_finding(
    request: _ExposureSignature,
    entry: _ExposureSignature,
) -> ExposureFinding | None:
    exact_exposure = (
        request.exposure_family
        and request.exposure_family
        in {entry.exposure_family, entry.factor_id, entry.name}
    )
    entry_identifiers = {
        value for value in (entry.factor_id, entry.name, entry.exposure_family) if value
    }
    requested_existing_factor = bool(request.inputs & entry_identifiers)
    if not exact_exposure and not requested_existing_factor:
        return None
    return ExposureFinding(
        kind=ExposureFindingKind.DUPLICATE,
        severity=ExposureFindingSeverity.BLOCKING,
        matched_registry_reference=_registry_reference(entry),
        rationale=(
            "requested exposure matches an existing registry factor identity or "
            "exposure family"
        ),
    )


def _equivalent_finding(
    request: _ExposureSignature,
    entry: _ExposureSignature,
) -> ExposureFinding | None:
    if not request.operation or not entry.operation or request.operation != entry.operation:
        return None
    if request.window and entry.window and request.window != entry.window:
        return None
    has_input_overlap = bool(request.inputs and entry.inputs and request.inputs & entry.inputs)
    has_token_overlap = bool(request.tokens and entry.tokens and request.tokens & entry.tokens)
    if not has_input_overlap and not has_token_overlap:
        return None
    return ExposureFinding(
        kind=ExposureFindingKind.EQUIVALENT,
        severity=ExposureFindingSeverity.WARNING,
        matched_registry_reference=_registry_reference(entry),
        rationale=(
            "requested formula has equivalent operation, lookback, or input metadata "
            "to an existing registry exposure"
        ),
    )


def _registry_reference(signature: _ExposureSignature) -> dict[str, str]:
    return {
        "factor_id": signature.factor_id,
        "factor_version": signature.factor_version,
        "name": signature.name,
        "exposure_family": signature.exposure_family,
    }


def _finding_key(
    finding: ExposureFinding,
) -> tuple[str, str, ExposureFindingKind]:
    reference = finding.matched_registry_reference
    return (
        reference.get("factor_id", ""),
        reference.get("exposure_family", ""),
        finding.kind,
    )


def _summary_for_result(result: ExposureCheckResult) -> str:
    if result.registry_status is ExposureRegistryStatus.UNAVAILABLE:
        return (
            "duplicate-exposure guard registry unavailable; request is not clean until "
            "a read-only registry check succeeds"
        )
    if not result.findings:
        if result.registry_status is ExposureRegistryStatus.EMPTY:
            return "duplicate-exposure guard checked an empty registry and found no matches"
        return "duplicate-exposure guard checked the registry and found no matches"
    blocking_count = sum(
        finding.severity is ExposureFindingSeverity.BLOCKING
        for finding in result.findings
    )
    warning_count = len(result.findings) - blocking_count
    return (
        "duplicate-exposure guard found "
        f"{blocking_count} blocking and {warning_count} warning finding(s)"
    )


def _input_names(value: object) -> frozenset[str]:
    found: set[str] = set()
    if isinstance(value, Mapping):
        for key in ("input", "inputs", "input_fields", "field", "fields", "source_fields"):
            if key in value:
                found.update(_input_names(value[key]))
        for key in ("name", "field_name"):
            text = value.get(key)
            if isinstance(text, str):
                found.add(_normalize_identifier(text))
    elif isinstance(value, list | tuple):
        for item in value:
            found.update(_input_names(item))
    elif isinstance(value, str):
        found.add(_normalize_identifier(value))
    return frozenset(item for item in found if item)


def _tokens(value: object) -> frozenset[str]:
    found: set[str] = set()
    if isinstance(value, Mapping):
        for key, item in value.items():
            found.add(_normalize_identifier(str(key)))
            found.update(_tokens(item))
    elif isinstance(value, list | tuple):
        for item in value:
            found.update(_tokens(item))
    elif isinstance(value, str):
        for token in value.split():
            normalized = _normalize_identifier(token)
            if normalized:
                found.add(normalized)
        normalized_value = _normalize_identifier(value)
        if normalized_value:
            found.add(normalized_value)
    elif isinstance(value, int | float | bool):
        found.add(str(value).lower())
    return frozenset(found)


def _first_text(
    mapping: Mapping[str, Any],
    fields: tuple[str, ...],
    *,
    fallback: str = "",
) -> str:
    for field in fields:
        value = mapping.get(field)
        if isinstance(value, str) and value.strip():
            return value
    return fallback


def _window_value(mapping: Mapping[str, Any]) -> str:
    for key in ("window", "lookback", "period", "horizon"):
        value = mapping.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            return str(value)
        if isinstance(value, str) and value.strip():
            return _normalize_identifier(value)
    return ""


def _normalize_operation(value: str) -> str:
    normalized = _normalize_identifier(value)
    return _OPERATION_SYNONYMS.get(normalized, normalized)


def _normalize_identifier(value: str) -> str:
    return _IDENTIFIER_RE.sub("_", value.strip().lower()).strip("_")


def _mapping_value(value: object) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _loads(value: str) -> dict[str, Any]:
    payload = json.loads(value or "{}")
    if isinstance(payload, dict):
        return payload
    return {}


__all__ = [
    "ExposureCheckResult",
    "ExposureFinding",
    "ExposureFindingKind",
    "ExposureFindingSeverity",
    "ExposureRegistryStatus",
    "RegistryReader",
    "apply_duplicate_exposure_notes",
    "check_and_update_feature_request",
    "check_duplicate_exposure",
    "find_duplicate_exposures",
]
