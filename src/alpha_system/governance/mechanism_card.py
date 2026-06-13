"""MechanismCard contract for strategy-shaped exploratory hypotheses."""

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

EXPLORATORY_STAMP = "EXPLORATORY"
ALLOWED_MECHANISM_STAMPS = frozenset({EXPLORATORY_STAMP})
MECHANISM_CARD_REQUIRED_FIELDS = (
    "mechanism_id",
    "source",
    "rationale",
    "expected_mechanism",
    "expected_direction",
    "horizon",
    "session",
    "required_features",
    "required_labels",
    "cost_sensitivity",
    "variant_budget",
    "duplicate_exposure",
    "stamp",
)
MECHANISM_CARD_ID_COMPONENT_FIELDS = tuple(
    field for field in MECHANISM_CARD_REQUIRED_FIELDS if field != "mechanism_id"
)
MECHANISM_CARD_FIELD_TYPES = {
    "mechanism_id": str,
    "source": str,
    "rationale": str,
    "expected_mechanism": str,
    "expected_direction": str,
    "horizon": str,
    "session": str,
    "required_features": list,
    "required_labels": list,
    "cost_sensitivity": dict,
    "variant_budget": int,
    "duplicate_exposure": dict,
    "stamp": str,
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
    "unbounded",
    "unlimited",
}
_VAGUE_PHRASES = (
    "add later",
    "figure out later",
    "look into",
    "maybe useful",
    "might work",
    "needs research",
    "not sure",
    "some signal",
    "to be added",
)


@dataclass(frozen=True, slots=True)
class MechanismCard:
    """Validated declaration of an exploratory strategy-shaped mechanism."""

    mechanism_id: str
    source: str
    rationale: str
    expected_mechanism: str
    expected_direction: str
    horizon: str
    session: str
    required_features: list[str]
    required_labels: list[str]
    cost_sensitivity: dict[str, JsonValue]
    variant_budget: int
    duplicate_exposure: dict[str, JsonValue]
    stamp: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> MechanismCard:
        """Build a `MechanismCard` from a mapping after fail-closed validation."""

        return validate_mechanism_card(payload)

    @classmethod
    def from_canonical_json(cls, text: str) -> MechanismCard:
        """Deserialize canonical JSON and validate the resulting `MechanismCard`."""

        value = deserialize(text)
        mapping = require_mapping(value, object_name="MechanismCard")
        return validate_mechanism_card(mapping)

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a strict JSON-compatible representation."""

        return {
            "mechanism_id": self.mechanism_id,
            "source": self.source,
            "rationale": self.rationale,
            "expected_mechanism": self.expected_mechanism,
            "expected_direction": self.expected_direction,
            "horizon": self.horizon,
            "session": self.session,
            "required_features": list(self.required_features),
            "required_labels": list(self.required_labels),
            "cost_sensitivity": dict(self.cost_sensitivity),
            "variant_budget": self.variant_budget,
            "duplicate_exposure": dict(self.duplicate_exposure),
            "stamp": self.stamp,
        }

    def to_canonical_json(self) -> str:
        """Serialize the validated record through the canonical primitive."""

        return canonical_serialize(self.to_dict())


def create_mechanism_card(
    *,
    source: str,
    rationale: str,
    expected_mechanism: str,
    expected_direction: str,
    horizon: str,
    session: str,
    required_features: list[str],
    required_labels: list[str],
    cost_sensitivity: dict[str, JsonValue],
    variant_budget: int,
    duplicate_exposure: dict[str, JsonValue],
    stamp: str = EXPLORATORY_STAMP,
) -> MechanismCard:
    """Create a validated `MechanismCard`, defaulting to the exploratory stamp."""

    payload: dict[str, JsonValue] = {
        "source": source,
        "rationale": rationale,
        "expected_mechanism": expected_mechanism,
        "expected_direction": expected_direction,
        "horizon": horizon,
        "session": session,
        "required_features": list(required_features),
        "required_labels": list(required_labels),
        "cost_sensitivity": dict(cost_sensitivity),
        "variant_budget": variant_budget,
        "duplicate_exposure": dict(duplicate_exposure),
        "stamp": stamp,
    }
    payload["mechanism_id"] = generate_mechanism_id(payload)
    return validate_mechanism_card(payload)


def generate_mechanism_id(payload: Mapping[str, Any]) -> str:
    """Generate the deterministic `MechanismCard` ID for a complete payload."""

    mapping = validate_required_fields(
        payload,
        MECHANISM_CARD_ID_COMPONENT_FIELDS,
        object_name="MechanismCard",
    )
    components = {field: mapping[field] for field in MECHANISM_CARD_ID_COMPONENT_FIELDS}
    return generate_governance_id(GovernanceIdKind.MECHANISM_CARD, components)


def validate_mechanism_card(payload: Mapping[str, Any]) -> MechanismCard:
    """Validate a `MechanismCard` mapping fail-closed and return a typed record."""

    mapping = validate_schema(
        payload,
        required_fields=MECHANISM_CARD_REQUIRED_FIELDS,
        field_types=MECHANISM_CARD_FIELD_TYPES,
        allowed_fields=MECHANISM_CARD_REQUIRED_FIELDS,
        object_name="MechanismCard",
    )

    issues: list[ValidationIssue] = []
    issues.extend(_validate_mechanism_id(mapping))
    issues.extend(
        _validate_non_empty_text(
            mapping,
            ("source", "expected_direction", "horizon", "session", "stamp"),
        )
    )
    for field in ("rationale", "expected_mechanism"):
        issues.extend(_validate_substantive_text(mapping[field], field=field))
    for field in ("required_features", "required_labels"):
        issues.extend(_validate_list_of_text(mapping, field))
    for field in ("cost_sensitivity", "duplicate_exposure"):
        issues.extend(_validate_mapping_is_substantive(mapping, field))
    issues.extend(_validate_variant_budget(mapping["variant_budget"]))
    issues.extend(_validate_stamp(mapping["stamp"]))
    issues.extend(_validate_canonical_serializable(mapping))
    if not issues:
        expected_id = generate_mechanism_id(mapping)
        if mapping["mechanism_id"] != expected_id:
            issues.append(
                ValidationIssue(
                    field="mechanism_id",
                    code="mechanism_id_mismatch",
                    message=(
                        "MechanismCard.mechanism_id must match deterministic "
                        "MechanismCard content"
                    ),
                    expected=expected_id,
                    actual=str(mapping["mechanism_id"]),
                )
            )

    if issues:
        raise GovernanceValidationError(issues)

    return MechanismCard(
        mechanism_id=mapping["mechanism_id"],
        source=mapping["source"],
        rationale=mapping["rationale"],
        expected_mechanism=mapping["expected_mechanism"],
        expected_direction=mapping["expected_direction"],
        horizon=mapping["horizon"],
        session=mapping["session"],
        required_features=list(mapping["required_features"]),
        required_labels=list(mapping["required_labels"]),
        cost_sensitivity=dict(mapping["cost_sensitivity"]),
        variant_budget=mapping["variant_budget"],
        duplicate_exposure=dict(mapping["duplicate_exposure"]),
        stamp=mapping["stamp"],
    )


def _validate_mechanism_id(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    try:
        validate_governance_id(
            mapping["mechanism_id"],
            expected_kind=GovernanceIdKind.MECHANISM_CARD,
        )
    except GovernanceIdError as exc:
        return [
            ValidationIssue(
                field="mechanism_id",
                code=exc.issue.code,
                message=exc.issue.message,
                expected=GovernanceIdKind.MECHANISM_CARD.value,
                actual=str(exc.issue.value),
            )
        ]
    return []


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
                    message=f"MechanismCard.{field} must be a non-empty, explicit value",
                    expected="non-empty explicit string",
                    actual=value,
                )
            )
    return issues


def _validate_substantive_text(value: str, *, field: str) -> list[ValidationIssue]:
    normalized = _normalize_text(value)
    words = _words(normalized)
    if normalized in _VAGUE_TEXT or any(phrase in normalized for phrase in _VAGUE_PHRASES):
        return [
            ValidationIssue(
                field=field,
                code="vague_required_field",
                message=f"MechanismCard.{field} must be explicit, not a placeholder",
                expected="substantive explicit text",
                actual=value,
            )
        ]
    if len(value.strip()) < 32 or len(words) < 6 or len(set(words)) < 4:
        return [
            ValidationIssue(
                field=field,
                code="vague_required_field",
                message=f"MechanismCard.{field} must be substantive, not terse",
                expected="substantive explicit text",
                actual=value,
            )
        ]
    return []


def _validate_list_of_text(mapping: Mapping[str, Any], field: str) -> list[ValidationIssue]:
    values = mapping[field]
    if not values:
        return [
            ValidationIssue(
                field=field,
                code="empty_required_field",
                message=f"MechanismCard.{field} must contain at least one entry",
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
                    message=f"MechanismCard.{item_field} must be a string",
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
                    message=f"MechanismCard.{item_field} must be explicit",
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
                message=f"MechanismCard.{field} must contain explicit metadata",
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
                    message=f"MechanismCard.{field} keys must be explicit strings",
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
                message=f"MechanismCard.{field} must not be null",
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
                    message=f"MechanismCard.{field} must be explicit, not vague",
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
                    message=f"MechanismCard.{field} must not be an empty list",
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
                    message=f"MechanismCard.{field} must not be an empty mapping",
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
                        message=f"MechanismCard.{field} nested keys must be explicit strings",
                        expected="non-empty explicit string key",
                        actual=str(key),
                    )
                )
            issues.extend(_validate_substantive_value(item, field=f"{field}.{key}"))
        return issues
    return []


def _validate_variant_budget(value: int) -> list[ValidationIssue]:
    if type(value) is not int:
        return [
            ValidationIssue(
                field="variant_budget",
                code="invalid_variant_budget_type",
                message="MechanismCard.variant_budget must be an exact integer cap",
                expected="positive int",
                actual=type(value).__name__,
            )
        ]
    if value <= 0:
        return [
            ValidationIssue(
                field="variant_budget",
                code="invalid_variant_budget",
                message="MechanismCard.variant_budget must be a positive bounded integer cap",
                expected="positive int",
                actual=str(value),
            )
        ]
    return []


def _validate_stamp(value: str) -> list[ValidationIssue]:
    if value not in ALLOWED_MECHANISM_STAMPS:
        return [
            ValidationIssue(
                field="stamp",
                code="invalid_stamp",
                message="MechanismCard.stamp must be EXPLORATORY",
                expected=EXPLORATORY_STAMP,
                actual=value,
            )
        ]
    return []


def _validate_canonical_serializable(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    try:
        canonical_serialize({field: mapping[field] for field in MECHANISM_CARD_REQUIRED_FIELDS})
    except GovernanceSerializationError as exc:
        return [
            ValidationIssue(
                field=exc.issue.path,
                code=exc.issue.code,
                message=exc.issue.message,
                expected="canonical JSON-compatible MechanismCard",
                actual=exc.issue.path,
            )
        ]
    return []


def _normalize_text(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _words(value: str) -> list[str]:
    return [
        word.strip(".,:;()[]{}'\"")
        for word in value.split()
        if word.strip(".,:;()[]{}'\"")
    ]


__all__ = [
    "ALLOWED_MECHANISM_STAMPS",
    "EXPLORATORY_STAMP",
    "MECHANISM_CARD_FIELD_TYPES",
    "MECHANISM_CARD_ID_COMPONENT_FIELDS",
    "MECHANISM_CARD_REQUIRED_FIELDS",
    "MechanismCard",
    "create_mechanism_card",
    "generate_mechanism_id",
    "validate_mechanism_card",
]
