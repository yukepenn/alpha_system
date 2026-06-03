"""HypothesisCard contract and pre-registration linkage."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from alpha_system.governance.alpha_spec import AlphaSpec, validate_alpha_spec
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


HYPOTHESIS_CARD_REQUIRED_FIELDS = (
    "hypothesis_id",
    "title",
    "family",
    "rationale",
    "expected_mechanism",
    "falsification_criteria",
    "risks",
    "author",
    "created_at",
)
HYPOTHESIS_CARD_ID_COMPONENT_FIELDS = tuple(
    field for field in HYPOTHESIS_CARD_REQUIRED_FIELDS if field != "hypothesis_id"
)
HYPOTHESIS_CARD_FIELD_TYPES = {
    "hypothesis_id": str,
    "title": str,
    "family": str,
    "rationale": str,
    "expected_mechanism": str,
    "falsification_criteria": list,
    "risks": list,
    "author": str,
    "created_at": str,
}
DRAFT_STATE = "DRAFT"
REGISTERED_STATE = "REGISTERED"

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
_FALSIFICATION_WORDS = {
    "absent",
    "above",
    "below",
    "block",
    "blocked",
    "blocks",
    "cannot",
    "exceed",
    "exceeds",
    "fail",
    "failed",
    "fails",
    "invalid",
    "invalidate",
    "invalidated",
    "invalidates",
    "leakage",
    "missing",
    "negative",
    "reject",
    "rejected",
    "rejects",
    "threshold",
    "under",
    "without",
    "worse",
}


@dataclass(frozen=True, slots=True)
class HypothesisCard:
    """Validated governance record for a proposed research idea."""

    hypothesis_id: str
    title: str
    family: str
    rationale: str
    expected_mechanism: str
    falsification_criteria: list[str]
    risks: list[str]
    author: str
    created_at: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> HypothesisCard:
        """Build a `HypothesisCard` from a mapping after fail-closed validation."""

        return validate_hypothesis_card(payload)

    @classmethod
    def from_canonical_json(cls, text: str) -> HypothesisCard:
        """Deserialize canonical JSON and validate the resulting `HypothesisCard`."""

        value = deserialize(text)
        mapping = require_mapping(value, object_name="HypothesisCard")
        return validate_hypothesis_card(mapping)

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a strict JSON-compatible representation."""

        return {
            "hypothesis_id": self.hypothesis_id,
            "title": self.title,
            "family": self.family,
            "rationale": self.rationale,
            "expected_mechanism": self.expected_mechanism,
            "falsification_criteria": list(self.falsification_criteria),
            "risks": list(self.risks),
            "author": self.author,
            "created_at": self.created_at,
        }

    def to_canonical_json(self) -> str:
        """Serialize the validated record through the canonical primitive."""

        return canonical_serialize(self.to_dict())


@dataclass(frozen=True, slots=True)
class RegisteredResearchPair:
    """Validated `DRAFT -> REGISTERED` linkage for a card and specification."""

    hypothesis_card: HypothesisCard
    alpha_spec: AlphaSpec


def generate_hypothesis_id(payload: Mapping[str, Any]) -> str:
    """Generate the deterministic `HypothesisCard` ID for a complete payload."""

    mapping = validate_required_fields(
        payload,
        HYPOTHESIS_CARD_ID_COMPONENT_FIELDS,
        object_name="HypothesisCard",
    )
    components = {field: mapping[field] for field in HYPOTHESIS_CARD_ID_COMPONENT_FIELDS}
    return generate_governance_id(GovernanceIdKind.HYPOTHESIS_CARD, components)


def validate_hypothesis_card(payload: Mapping[str, Any]) -> HypothesisCard:
    """Validate a `HypothesisCard` mapping fail-closed and return a typed record."""

    mapping = validate_schema(
        payload,
        required_fields=HYPOTHESIS_CARD_REQUIRED_FIELDS,
        field_types=HYPOTHESIS_CARD_FIELD_TYPES,
        allowed_fields=HYPOTHESIS_CARD_REQUIRED_FIELDS,
        object_name="HypothesisCard",
    )

    issues: list[ValidationIssue] = []
    issues.extend(_validate_hypothesis_id(mapping))
    issues.extend(_validate_non_empty_text(mapping, ("title", "family", "author", "created_at")))
    for field in ("rationale", "expected_mechanism"):
        issues.extend(_validate_substantive_text(mapping[field], field=field, minimum_chars=32))
    issues.extend(_validate_falsification_criteria(mapping))
    issues.extend(_validate_list_of_text(mapping, "risks", minimum_chars=20))
    issues.extend(_validate_created_at(mapping["created_at"]))
    issues.extend(_validate_canonical_serializable(mapping))
    if not issues:
        expected_id = generate_hypothesis_id(mapping)
        if mapping["hypothesis_id"] != expected_id:
            issues.append(
                ValidationIssue(
                    field="hypothesis_id",
                    code="hypothesis_id_mismatch",
                    message=(
                        "HypothesisCard.hypothesis_id must match deterministic "
                        "HypothesisCard content"
                    ),
                    expected=expected_id,
                    actual=str(mapping["hypothesis_id"]),
                )
            )

    if issues:
        raise GovernanceValidationError(issues)

    return HypothesisCard(
        hypothesis_id=mapping["hypothesis_id"],
        title=mapping["title"],
        family=mapping["family"],
        rationale=mapping["rationale"],
        expected_mechanism=mapping["expected_mechanism"],
        falsification_criteria=list(mapping["falsification_criteria"]),
        risks=list(mapping["risks"]),
        author=mapping["author"],
        created_at=mapping["created_at"],
    )


def validate_pre_registration(
    hypothesis_card: HypothesisCard | Mapping[str, Any] | None,
    alpha_spec: AlphaSpec | Mapping[str, Any] | None,
    *,
    from_state: str = DRAFT_STATE,
    to_state: str = REGISTERED_STATE,
) -> RegisteredResearchPair:
    """Validate the pure `DRAFT -> REGISTERED` card/specification precondition."""

    issues: list[ValidationIssue] = []
    if from_state != DRAFT_STATE or to_state != REGISTERED_STATE:
        issues.append(
            ValidationIssue(
                field="transition",
                code="unsupported_pre_registration_transition",
                message="pre-registration only evaluates DRAFT -> REGISTERED",
                expected=f"{DRAFT_STATE}->{REGISTERED_STATE}",
                actual=f"{from_state}->{to_state}",
            )
        )
    if hypothesis_card is None:
        issues.append(
            ValidationIssue(
                field="hypothesis_card",
                code="missing_hypothesis_card",
                message="valid HypothesisCard is required for registration",
                expected="validated HypothesisCard",
                actual="missing",
            )
        )
    if alpha_spec is None:
        issues.append(
            ValidationIssue(
                field="alpha_spec",
                code="missing_alpha_spec",
                message="valid AlphaSpec is required for registration",
                expected="validated AlphaSpec",
                actual="missing",
            )
        )

    if issues:
        raise GovernanceValidationError(issues)

    validated_card = (
        validate_hypothesis_card(hypothesis_card.to_dict())
        if isinstance(hypothesis_card, HypothesisCard)
        else validate_hypothesis_card(hypothesis_card)
    )
    validated_spec = (
        validate_alpha_spec(alpha_spec.to_dict())
        if isinstance(alpha_spec, AlphaSpec)
        else validate_alpha_spec(alpha_spec)
    )

    if validated_spec.hypothesis_id != validated_card.hypothesis_id:
        raise GovernanceValidationError(
            ValidationIssue(
                field="alpha_spec.hypothesis_id",
                code="hypothesis_id_mismatch",
                message="AlphaSpec.hypothesis_id must reference the validated HypothesisCard",
                expected=validated_card.hypothesis_id,
                actual=validated_spec.hypothesis_id,
            )
        )

    return RegisteredResearchPair(
        hypothesis_card=validated_card,
        alpha_spec=validated_spec,
    )


def assert_pre_registered(
    hypothesis_card: HypothesisCard | Mapping[str, Any] | None,
    alpha_spec: AlphaSpec | Mapping[str, Any] | None,
) -> RegisteredResearchPair:
    """Alias for the pure pre-registration precondition."""

    return validate_pre_registration(hypothesis_card, alpha_spec)


def _validate_hypothesis_id(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    try:
        validate_governance_id(
            mapping["hypothesis_id"],
            expected_kind=GovernanceIdKind.HYPOTHESIS_CARD,
        )
    except GovernanceIdError as exc:
        return [
            ValidationIssue(
                field="hypothesis_id",
                code=exc.issue.code,
                message=exc.issue.message,
                expected=GovernanceIdKind.HYPOTHESIS_CARD.value,
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
        normalized = _normalize_text(value)
        if normalized in _VAGUE_TEXT:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="empty_required_field",
                    message=f"HypothesisCard.{field} must be a non-empty, explicit value",
                    expected="non-empty explicit string",
                    actual=value,
                )
            )
    return issues


def _validate_substantive_text(
    value: str,
    *,
    field: str,
    minimum_chars: int,
) -> list[ValidationIssue]:
    normalized = _normalize_text(value)
    words = _words(normalized)
    if normalized in _VAGUE_TEXT or any(phrase in normalized for phrase in _VAGUE_PHRASES):
        return [
            ValidationIssue(
                field=field,
                code="vague_required_field",
                message=f"HypothesisCard.{field} must be explicit, not a placeholder",
                expected="substantive explicit text",
                actual=value,
            )
        ]
    if len(value.strip()) < minimum_chars or len(words) < 6 or len(set(words)) < 4:
        return [
            ValidationIssue(
                field=field,
                code="vague_required_field",
                message=f"HypothesisCard.{field} must be substantive, not terse",
                expected="substantive explicit text",
                actual=value,
            )
        ]
    return []


def _validate_list_of_text(
    mapping: Mapping[str, Any],
    field: str,
    *,
    minimum_chars: int,
) -> list[ValidationIssue]:
    values = mapping[field]
    if not values:
        return [
            ValidationIssue(
                field=field,
                code="empty_required_field",
                message=f"HypothesisCard.{field} must contain at least one entry",
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
                    message=f"HypothesisCard.{item_field} must be a string",
                    expected="str",
                    actual=type(item).__name__,
                )
            )
            continue
        issues.extend(
            _validate_substantive_text(
                item,
                field=item_field,
                minimum_chars=minimum_chars,
            )
        )
    return issues


def _validate_falsification_criteria(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    values = mapping["falsification_criteria"]
    issues = _validate_list_of_text(mapping, "falsification_criteria", minimum_chars=32)
    if issues:
        return issues

    for index, item in enumerate(values):
        item_field = f"falsification_criteria[{index}]"
        normalized = _normalize_text(item)
        word_set = set(_words(normalized))
        has_condition_word = bool(word_set & _FALSIFICATION_WORDS) or "falsif" in normalized
        if not has_condition_word:
            issues.append(
                ValidationIssue(
                    field=item_field,
                    code="missing_falsification_condition",
                    message=(
                        "HypothesisCard.falsification_criteria entries must describe "
                        "a condition that can reject or block the idea later"
                    ),
                    expected="explicit falsification condition",
                    actual=item,
                )
            )
    return issues


def _validate_created_at(value: str) -> list[ValidationIssue]:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return [
            ValidationIssue(
                field="created_at",
                code="malformed_timestamp",
                message="HypothesisCard.created_at must be an ISO-8601 timestamp",
                expected="ISO-8601 timestamp with timezone",
                actual=value,
            )
        ]
    if parsed.tzinfo is None:
        return [
            ValidationIssue(
                field="created_at",
                code="missing_timestamp_timezone",
                message="HypothesisCard.created_at must include a timezone",
                expected="timezone-aware ISO-8601 timestamp",
                actual=value,
            )
        ]
    return []


def _validate_canonical_serializable(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    try:
        canonical_serialize({field: mapping[field] for field in HYPOTHESIS_CARD_REQUIRED_FIELDS})
    except GovernanceSerializationError as exc:
        return [
            ValidationIssue(
                field=exc.issue.path,
                code=exc.issue.code,
                message=exc.issue.message,
                expected="canonical JSON-compatible HypothesisCard",
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
    "DRAFT_STATE",
    "HYPOTHESIS_CARD_REQUIRED_FIELDS",
    "REGISTERED_STATE",
    "HypothesisCard",
    "RegisteredResearchPair",
    "assert_pre_registered",
    "generate_hypothesis_id",
    "validate_hypothesis_card",
    "validate_pre_registration",
]
