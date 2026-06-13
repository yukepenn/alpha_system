"""SetupSpec contract for strategy-shaped exploratory setups."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from alpha_system.governance.ids import (
    GovernanceIdError,
    GovernanceIdKind,
    generate_governance_id,
    validate_governance_id,
)
from alpha_system.governance.mechanism_card import EXPLORATORY_STAMP
from alpha_system.governance.serialization import (
    GovernanceSerializationError,
    JsonValue,
    canonical_serialize,
    deserialize,
)
from alpha_system.governance.validation import (
    GovernanceValidationError,
    ValidationIssue,
    require_mapping,
    validate_required_fields,
    validate_schema,
)

ALLOWED_SETUP_STAMPS = frozenset({EXPLORATORY_STAMP})
SETUP_SPEC_REQUIRED_FIELDS = (
    "setup_spec_id",
    "entry_context",
    "event_trigger",
    "regime_filter",
    "confirmation",
    "invalidation",
    "stop",
    "target",
    "hold_time",
    "horizon",
    "path_label",
    "allowed_variants",
    "forbidden_post_hoc_changes",
    "mechanism_id",
    "stamp",
)
SETUP_SPEC_ID_COMPONENT_FIELDS = tuple(
    field for field in SETUP_SPEC_REQUIRED_FIELDS if field != "setup_spec_id"
)
SETUP_SPEC_FIELD_TYPES = {
    "setup_spec_id": str,
    "entry_context": dict,
    "event_trigger": dict,
    "regime_filter": dict,
    "confirmation": dict,
    "invalidation": dict,
    "stop": dict,
    "target": dict,
    "hold_time": dict,
    "horizon": str,
    "path_label": str,
    "allowed_variants": list,
    "forbidden_post_hoc_changes": list,
    "mechanism_id": str,
    "stamp": str,
}

_DERIVATION_KEYS = frozenset(
    {
        "alias",
        "alias_of",
        "derived_from",
        "same_as",
        "source_field",
    }
)
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
    "unbounded",
    "unlimited",
}


@dataclass(frozen=True, slots=True)
class SetupSpec:
    """Validated declaration of one exploratory setup shape."""

    setup_spec_id: str
    entry_context: dict[str, JsonValue]
    event_trigger: dict[str, JsonValue]
    regime_filter: dict[str, JsonValue]
    confirmation: dict[str, JsonValue]
    invalidation: dict[str, JsonValue]
    stop: dict[str, JsonValue]
    target: dict[str, JsonValue]
    hold_time: dict[str, JsonValue]
    horizon: str
    path_label: str
    allowed_variants: list[str]
    forbidden_post_hoc_changes: list[str]
    mechanism_id: str
    stamp: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> SetupSpec:
        """Build a `SetupSpec` from a mapping after fail-closed validation."""

        return validate_setup_spec(payload)

    @classmethod
    def from_canonical_json(cls, text: str) -> SetupSpec:
        """Deserialize canonical JSON and validate the resulting `SetupSpec`."""

        value = deserialize(text)
        mapping = require_mapping(value, object_name="SetupSpec")
        return validate_setup_spec(mapping)

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a strict JSON-compatible representation."""

        return {
            "setup_spec_id": self.setup_spec_id,
            "entry_context": dict(self.entry_context),
            "event_trigger": dict(self.event_trigger),
            "regime_filter": dict(self.regime_filter),
            "confirmation": dict(self.confirmation),
            "invalidation": dict(self.invalidation),
            "stop": dict(self.stop),
            "target": dict(self.target),
            "hold_time": dict(self.hold_time),
            "horizon": self.horizon,
            "path_label": self.path_label,
            "allowed_variants": list(self.allowed_variants),
            "forbidden_post_hoc_changes": list(self.forbidden_post_hoc_changes),
            "mechanism_id": self.mechanism_id,
            "stamp": self.stamp,
        }

    def to_canonical_json(self) -> str:
        """Serialize the validated record through the canonical primitive."""

        return canonical_serialize(self.to_dict())


def create_setup_spec(
    *,
    entry_context: dict[str, JsonValue],
    event_trigger: dict[str, JsonValue],
    regime_filter: dict[str, JsonValue],
    confirmation: dict[str, JsonValue],
    invalidation: dict[str, JsonValue],
    stop: dict[str, JsonValue],
    target: dict[str, JsonValue],
    hold_time: dict[str, JsonValue],
    horizon: str,
    path_label: str,
    allowed_variants: list[str],
    forbidden_post_hoc_changes: list[str],
    mechanism_id: str,
    stamp: str = EXPLORATORY_STAMP,
) -> SetupSpec:
    """Create a validated `SetupSpec`, defaulting to the exploratory stamp."""

    payload: dict[str, JsonValue] = {
        "entry_context": dict(entry_context),
        "event_trigger": dict(event_trigger),
        "regime_filter": dict(regime_filter),
        "confirmation": dict(confirmation),
        "invalidation": dict(invalidation),
        "stop": dict(stop),
        "target": dict(target),
        "hold_time": dict(hold_time),
        "horizon": horizon,
        "path_label": path_label,
        "allowed_variants": list(allowed_variants),
        "forbidden_post_hoc_changes": list(forbidden_post_hoc_changes),
        "mechanism_id": mechanism_id,
        "stamp": stamp,
    }
    payload["setup_spec_id"] = generate_setup_spec_id(payload)
    return validate_setup_spec(payload)


def generate_setup_spec_id(payload: Mapping[str, Any]) -> str:
    """Generate the deterministic `SetupSpec` ID for a complete payload."""

    mapping = validate_required_fields(
        payload,
        SETUP_SPEC_ID_COMPONENT_FIELDS,
        object_name="SetupSpec",
    )
    components = {field: mapping[field] for field in SETUP_SPEC_ID_COMPONENT_FIELDS}
    return generate_governance_id(GovernanceIdKind.SETUP_SPEC, components)


def validate_setup_spec(payload: Mapping[str, Any]) -> SetupSpec:
    """Validate a `SetupSpec` mapping fail-closed and return a typed record."""

    mapping = validate_schema(
        payload,
        required_fields=SETUP_SPEC_REQUIRED_FIELDS,
        field_types=SETUP_SPEC_FIELD_TYPES,
        allowed_fields=SETUP_SPEC_REQUIRED_FIELDS,
        object_name="SetupSpec",
    )

    issues: list[ValidationIssue] = []
    issues.extend(_validate_ids(mapping))
    for field in (
        "entry_context",
        "event_trigger",
        "regime_filter",
        "confirmation",
        "invalidation",
        "stop",
        "target",
        "hold_time",
    ):
        issues.extend(_validate_mapping_is_substantive(mapping, field))
    issues.extend(_validate_event_trigger_is_separate(mapping))
    issues.extend(_validate_non_empty_text(mapping, ("horizon", "stamp")))
    for field in ("allowed_variants", "forbidden_post_hoc_changes"):
        issues.extend(_validate_list_of_text(mapping, field))
    issues.extend(_validate_stamp(mapping["stamp"]))
    issues.extend(_validate_canonical_serializable(mapping))
    if not issues:
        expected_id = generate_setup_spec_id(mapping)
        if mapping["setup_spec_id"] != expected_id:
            issues.append(
                ValidationIssue(
                    field="setup_spec_id",
                    code="setup_spec_id_mismatch",
                    message=(
                        "SetupSpec.setup_spec_id must match deterministic "
                        "SetupSpec content"
                    ),
                    expected=expected_id,
                    actual=str(mapping["setup_spec_id"]),
                )
            )

    if issues:
        raise GovernanceValidationError(issues)

    return SetupSpec(
        setup_spec_id=mapping["setup_spec_id"],
        entry_context=dict(mapping["entry_context"]),
        event_trigger=dict(mapping["event_trigger"]),
        regime_filter=dict(mapping["regime_filter"]),
        confirmation=dict(mapping["confirmation"]),
        invalidation=dict(mapping["invalidation"]),
        stop=dict(mapping["stop"]),
        target=dict(mapping["target"]),
        hold_time=dict(mapping["hold_time"]),
        horizon=mapping["horizon"],
        path_label=mapping["path_label"],
        allowed_variants=list(mapping["allowed_variants"]),
        forbidden_post_hoc_changes=list(mapping["forbidden_post_hoc_changes"]),
        mechanism_id=mapping["mechanism_id"],
        stamp=mapping["stamp"],
    )


def _validate_ids(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    id_checks = (
        ("setup_spec_id", GovernanceIdKind.SETUP_SPEC),
        ("path_label", GovernanceIdKind.LABEL_SPEC),
        ("mechanism_id", GovernanceIdKind.MECHANISM_CARD),
    )
    for field, kind in id_checks:
        try:
            validate_governance_id(mapping[field], expected_kind=kind)
        except GovernanceIdError as exc:
            issues.append(
                ValidationIssue(
                    field=field,
                    code=exc.issue.code,
                    message=exc.issue.message,
                    expected=kind.value,
                    actual=str(exc.issue.value),
                )
            )
    return issues


def _validate_event_trigger_is_separate(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    entry_context = mapping["entry_context"]
    event_trigger = mapping["event_trigger"]
    if event_trigger is entry_context:
        return [
            ValidationIssue(
                field="event_trigger",
                code="event_trigger_aliases_entry_context",
                message="SetupSpec.event_trigger must not alias entry_context",
                expected="independent event trigger mapping",
                actual="same object as entry_context",
            )
        ]
    try:
        if canonical_serialize(event_trigger) == canonical_serialize(entry_context):
            return [
                ValidationIssue(
                    field="event_trigger",
                    code="event_trigger_matches_entry_context",
                    message="SetupSpec.event_trigger must be distinct from entry_context",
                    expected="trigger logic different from entry context",
                    actual="same canonical content as entry_context",
                )
            ]
    except GovernanceSerializationError:
        return []
    if _contains_entry_context_derivation(event_trigger):
        return [
            ValidationIssue(
                field="event_trigger",
                code="event_trigger_derived_from_entry_context",
                message="SetupSpec.event_trigger must not derive from entry_context",
                expected="independent trigger declaration",
                actual="declared as derived from entry_context",
            )
        ]
    return []


def _contains_entry_context_derivation(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized_key = _normalize_key(str(key))
            if normalized_key in _DERIVATION_KEYS and _is_entry_context_marker(item):
                return True
            if _contains_entry_context_derivation(item):
                return True
    if isinstance(value, list):
        return any(_contains_entry_context_derivation(item) for item in value)
    return False


def _is_entry_context_marker(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    normalized = _normalize_text(value).replace(" ", "_")
    return normalized in {
        "entry_context",
        "same_as_entry_context",
        "derived_from_entry_context",
        "alias_of_entry_context",
    }


def _validate_non_empty_text(
    mapping: Mapping[str, Any],
    fields: tuple[str, ...],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for field in fields:
        value = mapping[field]
        if _normalize_text(value) in _VAGUE_TEXT:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="empty_required_field",
                    message=f"SetupSpec.{field} must be a non-empty, explicit value",
                    expected="non-empty explicit string",
                    actual=value,
                )
            )
    return issues


def _validate_list_of_text(mapping: Mapping[str, Any], field: str) -> list[ValidationIssue]:
    values = mapping[field]
    if not values:
        return [
            ValidationIssue(
                field=field,
                code="empty_required_field",
                message=f"SetupSpec.{field} must contain at least one entry",
                expected="non-empty list",
                actual="empty list",
            )
        ]

    issues: list[ValidationIssue] = []
    for index, item in enumerate(values):
        item_field = f"{field}[{index}]"
        if type(item) is not str:
            issues.append(
                ValidationIssue(
                    field=item_field,
                    code="invalid_item_type",
                    message=f"SetupSpec.{item_field} must be a string",
                    expected="str",
                    actual=type(item).__name__,
                )
            )
            continue
        if _normalize_text(item) in _VAGUE_TEXT:
            issues.append(
                ValidationIssue(
                    field=item_field,
                    code="empty_required_field",
                    message=f"SetupSpec.{item_field} must be explicit",
                    expected="non-empty explicit string",
                    actual=item,
                )
            )
    return issues


def _validate_mapping_is_substantive(
    mapping: Mapping[str, Any],
    field: str,
) -> list[ValidationIssue]:
    value = mapping[field]
    if not value:
        return [
            ValidationIssue(
                field=field,
                code="empty_required_field",
                message=f"SetupSpec.{field} must contain explicit metadata",
                expected="non-empty mapping",
                actual="empty mapping",
            )
        ]

    issues: list[ValidationIssue] = []
    for key, item in value.items():
        if not isinstance(key, str) or _normalize_text(key) in _VAGUE_TEXT:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="invalid_metadata_key",
                    message=f"SetupSpec.{field} keys must be explicit strings",
                    expected="non-empty explicit string key",
                    actual=str(key),
                )
            )
        issues.extend(_validate_substantive_value(item, field=f"{field}.{key}"))
    return issues


def _validate_substantive_value(value: Any, *, field: str) -> list[ValidationIssue]:
    if value is None:
        return [
            ValidationIssue(
                field=field,
                code="null_required_field",
                message=f"SetupSpec.{field} must not be null",
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
                    message=f"SetupSpec.{field} must be explicit, not vague",
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
                    message=f"SetupSpec.{field} must not be an empty list",
                    expected="non-empty value",
                    actual="empty list",
                )
            ]
        issues: list[ValidationIssue] = []
        for index, item in enumerate(value):
            issues.extend(_validate_substantive_value(item, field=f"{field}[{index}]"))
        return issues
    if isinstance(value, dict):
        if not value:
            return [
                ValidationIssue(
                    field=field,
                    code="empty_required_field",
                    message=f"SetupSpec.{field} must not be an empty mapping",
                    expected="non-empty value",
                    actual="empty mapping",
                )
            ]
        issues = []
        for key, item in value.items():
            if not isinstance(key, str) or _normalize_text(key) in _VAGUE_TEXT:
                issues.append(
                    ValidationIssue(
                        field=field,
                        code="invalid_metadata_key",
                        message=f"SetupSpec.{field} nested keys must be explicit strings",
                        expected="non-empty explicit string key",
                        actual=str(key),
                    )
                )
            issues.extend(_validate_substantive_value(item, field=f"{field}.{key}"))
        return issues
    return []


def _validate_stamp(value: str) -> list[ValidationIssue]:
    if value not in ALLOWED_SETUP_STAMPS:
        return [
            ValidationIssue(
                field="stamp",
                code="invalid_stamp",
                message="SetupSpec.stamp must be EXPLORATORY",
                expected=EXPLORATORY_STAMP,
                actual=value,
            )
        ]
    return []


def _validate_canonical_serializable(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    try:
        canonical_serialize({field: mapping[field] for field in SETUP_SPEC_REQUIRED_FIELDS})
    except GovernanceSerializationError as exc:
        return [
            ValidationIssue(
                field=exc.issue.path,
                code=exc.issue.code,
                message=exc.issue.message,
                expected="canonical JSON-compatible SetupSpec",
                actual=exc.issue.path,
            )
        ]
    return []


def _normalize_key(value: str) -> str:
    return _normalize_text(value).replace("-", "_").replace(" ", "_")


def _normalize_text(value: str) -> str:
    return " ".join(value.strip().lower().split())


__all__ = [
    "ALLOWED_SETUP_STAMPS",
    "EXPLORATORY_STAMP",
    "SETUP_SPEC_FIELD_TYPES",
    "SETUP_SPEC_ID_COMPONENT_FIELDS",
    "SETUP_SPEC_REQUIRED_FIELDS",
    "SetupSpec",
    "create_setup_spec",
    "generate_setup_spec_id",
    "validate_setup_spec",
]
