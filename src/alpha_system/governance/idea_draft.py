"""Idea intake wrapper for the idea-to-verdict front door."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from alpha_system.governance.alpha_spec import (
    AlphaSpec,
    generate_alpha_spec_id,
    validate_alpha_spec,
)
from alpha_system.governance.hypothesis_card import (
    HypothesisCard,
    generate_hypothesis_id,
    validate_hypothesis_card,
)
from alpha_system.governance.ids import (
    GovernanceIdError,
    GovernanceIdKind,
    validate_governance_id,
)
from alpha_system.governance.mechanism_card import (
    EXPLORATORY_STAMP,
    MECHANISM_CARD_FIELD_TYPES,
    MECHANISM_CARD_REQUIRED_FIELDS,
    MechanismCard,
    create_mechanism_card,
)
from alpha_system.governance.serialization import JsonValue
from alpha_system.governance.setup_spec import (
    SETUP_SPEC_FIELD_TYPES,
    SETUP_SPEC_REQUIRED_FIELDS,
    SetupSpec,
    create_setup_spec,
)
from alpha_system.governance.validation import (
    GovernanceValidationError,
    ValidationIssue,
    require_mapping,
    validate_schema,
)

MAIN_EFFECT = "main_effect"
CONTEXT_NOT_EQUAL_TRIGGER = "context_not_equal_trigger"
ALLOWED_STUDY_KINDS = frozenset({MAIN_EFFECT, CONTEXT_NOT_EQUAL_TRIGGER})

IDEA_DRAFT_FIELDS = (
    "source",
    "study_kind",
    "hypothesis_id",
    "alpha_spec_id",
    "mechanism_id",
    "setup_spec_id",
)
IDEA_BUNDLE_INPUT_FIELDS = (
    "source",
    "study_kind",
    "hypothesis_card",
    "alpha_spec",
    "mechanism_card",
    "setup_spec",
)

_MECHANISM_INPUT_REQUIRED_FIELDS = tuple(
    field
    for field in MECHANISM_CARD_REQUIRED_FIELDS
    if field not in {"mechanism_id", "stamp"}
)
_MECHANISM_INPUT_ALLOWED_FIELDS = _MECHANISM_INPUT_REQUIRED_FIELDS + ("stamp",)
_MECHANISM_INPUT_FIELD_TYPES = {
    field: MECHANISM_CARD_FIELD_TYPES[field] for field in _MECHANISM_INPUT_ALLOWED_FIELDS
}

_SETUP_INPUT_REQUIRED_FIELDS = tuple(
    field
    for field in SETUP_SPEC_REQUIRED_FIELDS
    if field not in {"setup_spec_id", "mechanism_id", "stamp"}
)
_SETUP_INPUT_ALLOWED_FIELDS = _SETUP_INPUT_REQUIRED_FIELDS + ("stamp",)
_SETUP_INPUT_FIELD_TYPES = {
    field: SETUP_SPEC_FIELD_TYPES[field] for field in _SETUP_INPUT_ALLOWED_FIELDS
}


@dataclass(frozen=True, slots=True)
class IdeaDraft:
    """Validated intake-only sidecar tying emitted canonical object IDs together."""

    source: str
    study_kind: str
    hypothesis_id: str
    alpha_spec_id: str
    mechanism_id: str
    setup_spec_id: str | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> IdeaDraft:
        """Build an `IdeaDraft` from a mapping after fail-closed validation."""

        return validate_idea_draft(payload)

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a strict JSON-compatible representation."""

        return {
            "source": self.source,
            "study_kind": self.study_kind,
            "hypothesis_id": self.hypothesis_id,
            "alpha_spec_id": self.alpha_spec_id,
            "mechanism_id": self.mechanism_id,
            "setup_spec_id": self.setup_spec_id,
        }


@dataclass(frozen=True, slots=True)
class IdeaValidationBundle:
    """Canonical object family emitted by `alpha idea validate`."""

    idea_draft: IdeaDraft
    hypothesis_card: HypothesisCard
    alpha_spec: AlphaSpec
    mechanism_card: MechanismCard
    setup_spec: SetupSpec | None = None

    def to_dict(self) -> dict[str, JsonValue]:
        """Return the emitted object family as JSON-compatible mappings."""

        return {
            "idea_draft": self.idea_draft.to_dict(),
            "hypothesis_card": self.hypothesis_card.to_dict(),
            "alpha_spec": self.alpha_spec.to_dict(),
            "mechanism_card": self.mechanism_card.to_dict(),
            "setup_spec": self.setup_spec.to_dict() if self.setup_spec is not None else None,
        }


def validate_study_kind(value: Any | None) -> str:
    """Validate and normalize the intake-only study kind discriminator."""

    if value is None:
        return MAIN_EFFECT
    if not isinstance(value, str):
        raise GovernanceValidationError(
            ValidationIssue(
                field="study_kind",
                code="invalid_field_type",
                message="IdeaDraft.study_kind must be a string",
                expected="string",
                actual=type(value).__name__,
            )
        )
    normalized = value.strip()
    if normalized not in ALLOWED_STUDY_KINDS:
        raise GovernanceValidationError(
            ValidationIssue(
                field="study_kind",
                code="invalid_study_kind",
                message=(
                    "IdeaDraft.study_kind must be main_effect or "
                    "context_not_equal_trigger"
                ),
                expected="main_effect|context_not_equal_trigger",
                actual=value,
            )
        )
    return normalized


def validate_idea_draft(payload: Mapping[str, Any]) -> IdeaDraft:
    """Validate an `IdeaDraft` sidecar without mutating governance schemas."""

    mapping = require_mapping(payload, object_name="IdeaDraft")
    issues: list[ValidationIssue] = []

    for field in mapping:
        if field not in IDEA_DRAFT_FIELDS:
            issues.append(
                ValidationIssue(
                    field=str(field),
                    code="unknown_field",
                    message=f"IdeaDraft.{field} is not declared in the schema",
                    expected="declared schema field",
                    actual="unknown field",
                )
            )

    source = mapping.get("source")
    if not isinstance(source, str) or not source.strip():
        issues.append(
            ValidationIssue(
                field="source",
                code="empty_required_field",
                message="IdeaDraft.source must be a non-empty provenance string",
                expected="non-empty string",
                actual=type(source).__name__ if source is not None else "missing",
            )
        )

    try:
        study_kind = validate_study_kind(mapping.get("study_kind"))
    except GovernanceValidationError as exc:
        issues.extend(exc.issues)
        study_kind = MAIN_EFFECT

    _append_governance_id_issue(
        issues,
        mapping,
        field="hypothesis_id",
        kind=GovernanceIdKind.HYPOTHESIS_CARD,
    )
    _append_governance_id_issue(
        issues,
        mapping,
        field="alpha_spec_id",
        kind=GovernanceIdKind.ALPHA_SPEC,
    )
    _append_governance_id_issue(
        issues,
        mapping,
        field="mechanism_id",
        kind=GovernanceIdKind.MECHANISM_CARD,
    )

    setup_spec_id = mapping.get("setup_spec_id")
    if study_kind == CONTEXT_NOT_EQUAL_TRIGGER:
        if setup_spec_id is None:
            issues.append(
                ValidationIssue(
                    field="setup_spec_id",
                    code="missing_required_field",
                    message=(
                        "IdeaDraft.setup_spec_id is required when study_kind is "
                        "context_not_equal_trigger"
                    ),
                    expected="SetupSpec id",
                    actual="missing",
                )
            )
        else:
            _append_governance_id_issue(
                issues,
                mapping,
                field="setup_spec_id",
                kind=GovernanceIdKind.SETUP_SPEC,
            )
    elif setup_spec_id is not None:
        issues.append(
            ValidationIssue(
                field="setup_spec_id",
                code="unexpected_setup_spec",
                message="IdeaDraft.setup_spec_id is only allowed for context_not_equal_trigger",
                expected="null for main_effect",
                actual=str(setup_spec_id),
            )
        )

    if issues:
        raise GovernanceValidationError(issues)

    return IdeaDraft(
        source=source.strip(),
        study_kind=study_kind,
        hypothesis_id=str(mapping["hypothesis_id"]),
        alpha_spec_id=str(mapping["alpha_spec_id"]),
        mechanism_id=str(mapping["mechanism_id"]),
        setup_spec_id=str(setup_spec_id) if setup_spec_id is not None else None,
    )


def build_idea_validation_bundle(
    payload: Mapping[str, Any],
    *,
    source: str | None = None,
) -> IdeaValidationBundle:
    """Build the canonical intake object family from one idea document."""

    mapping = require_mapping(payload, object_name="idea document")
    _reject_unknown_bundle_fields(mapping)

    study_kind = validate_study_kind(mapping.get("study_kind"))
    idea_source = _resolve_source(mapping, source=source)
    hypothesis_card = _build_hypothesis_card(_required_mapping(mapping, "hypothesis_card"))
    alpha_spec = _build_alpha_spec(
        _required_mapping(mapping, "alpha_spec"),
        hypothesis_id=hypothesis_card.hypothesis_id,
    )
    mechanism_card = _build_mechanism_card(_required_mapping(mapping, "mechanism_card"))
    setup_spec = _build_setup_spec(
        mapping,
        study_kind=study_kind,
        mechanism_id=mechanism_card.mechanism_id,
    )
    idea_draft = validate_idea_draft(
        {
            "source": idea_source,
            "study_kind": study_kind,
            "hypothesis_id": hypothesis_card.hypothesis_id,
            "alpha_spec_id": alpha_spec.alpha_spec_id,
            "mechanism_id": mechanism_card.mechanism_id,
            "setup_spec_id": setup_spec.setup_spec_id if setup_spec is not None else None,
        }
    )
    return IdeaValidationBundle(
        idea_draft=idea_draft,
        hypothesis_card=hypothesis_card,
        alpha_spec=alpha_spec,
        mechanism_card=mechanism_card,
        setup_spec=setup_spec,
    )


def _append_governance_id_issue(
    issues: list[ValidationIssue],
    mapping: Mapping[str, Any],
    *,
    field: str,
    kind: GovernanceIdKind,
) -> None:
    value = mapping.get(field)
    if value is None:
        issues.append(
            ValidationIssue(
                field=field,
                code="missing_required_field",
                message=f"IdeaDraft.{field} is required",
                expected=kind.value,
                actual="missing",
            )
        )
        return
    try:
        validate_governance_id(value, expected_kind=kind)
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


def _reject_unknown_bundle_fields(mapping: Mapping[str, Any]) -> None:
    issues = [
        ValidationIssue(
            field=str(field),
            code="unknown_field",
            message=f"idea document field {field!r} is not declared",
            expected="declared idea bundle field",
            actual="unknown field",
        )
        for field in mapping
        if field not in IDEA_BUNDLE_INPUT_FIELDS
    ]
    if issues:
        raise GovernanceValidationError(issues)


def _resolve_source(mapping: Mapping[str, Any], *, source: str | None) -> str:
    resolved = source if source is not None else mapping.get("source")
    if not isinstance(resolved, str) or not resolved.strip():
        raise GovernanceValidationError(
            ValidationIssue(
                field="source",
                code="missing_required_field",
                message="idea document source provenance is required",
                expected="non-empty provenance string",
                actual=type(resolved).__name__ if resolved is not None else "missing",
            )
        )
    return resolved.strip()


def _required_mapping(mapping: Mapping[str, Any], field: str) -> Mapping[str, Any]:
    if field not in mapping or mapping[field] is None:
        raise GovernanceValidationError(
            ValidationIssue(
                field=field,
                code="missing_required_field",
                message=f"idea document {field!r} mapping is required",
                expected="mapping",
                actual="missing",
            )
        )
    return require_mapping(mapping[field], object_name=f"idea document {field}")


def _build_hypothesis_card(payload: Mapping[str, Any]) -> HypothesisCard:
    card_payload = dict(payload)
    if "hypothesis_id" not in card_payload:
        card_payload["hypothesis_id"] = generate_hypothesis_id(card_payload)
    return validate_hypothesis_card(card_payload)


def _build_alpha_spec(payload: Mapping[str, Any], *, hypothesis_id: str) -> AlphaSpec:
    spec_payload = dict(payload)
    existing_hypothesis_id = spec_payload.get("hypothesis_id")
    if existing_hypothesis_id is not None and existing_hypothesis_id != hypothesis_id:
        raise GovernanceValidationError(
            ValidationIssue(
                field="alpha_spec.hypothesis_id",
                code="hypothesis_id_mismatch",
                message="AlphaSpec.hypothesis_id must reference the minted HypothesisCard",
                expected=hypothesis_id,
                actual=str(existing_hypothesis_id),
            )
        )
    spec_payload["hypothesis_id"] = hypothesis_id
    if "alpha_spec_id" not in spec_payload:
        spec_payload["alpha_spec_id"] = generate_alpha_spec_id(spec_payload)
    return validate_alpha_spec(spec_payload)


def _build_mechanism_card(payload: Mapping[str, Any]) -> MechanismCard:
    mechanism_payload = validate_schema(
        payload,
        required_fields=_MECHANISM_INPUT_REQUIRED_FIELDS,
        field_types=_MECHANISM_INPUT_FIELD_TYPES,
        allowed_fields=_MECHANISM_INPUT_ALLOWED_FIELDS,
        object_name="idea document mechanism_card",
    )
    return create_mechanism_card(
        source=mechanism_payload["source"],
        rationale=mechanism_payload["rationale"],
        expected_mechanism=mechanism_payload["expected_mechanism"],
        expected_direction=mechanism_payload["expected_direction"],
        horizon=mechanism_payload["horizon"],
        session=mechanism_payload["session"],
        required_features=list(mechanism_payload["required_features"]),
        required_labels=list(mechanism_payload["required_labels"]),
        cost_sensitivity=dict(mechanism_payload["cost_sensitivity"]),
        variant_budget=mechanism_payload["variant_budget"],
        duplicate_exposure=dict(mechanism_payload["duplicate_exposure"]),
        stamp=mechanism_payload.get("stamp", EXPLORATORY_STAMP),
    )


def _build_setup_spec(
    mapping: Mapping[str, Any],
    *,
    study_kind: str,
    mechanism_id: str,
) -> SetupSpec | None:
    if study_kind == MAIN_EFFECT:
        if "setup_spec" in mapping and mapping["setup_spec"] is not None:
            raise GovernanceValidationError(
                ValidationIssue(
                    field="setup_spec",
                    code="unexpected_setup_spec",
                    message="setup_spec is only valid for context_not_equal_trigger ideas",
                    expected="absent for main_effect",
                    actual="present",
                )
            )
        return None

    setup_payload = validate_schema(
        _required_mapping(mapping, "setup_spec"),
        required_fields=_SETUP_INPUT_REQUIRED_FIELDS,
        field_types=_SETUP_INPUT_FIELD_TYPES,
        allowed_fields=_SETUP_INPUT_ALLOWED_FIELDS,
        object_name="idea document setup_spec",
    )
    return create_setup_spec(
        entry_context=dict(setup_payload["entry_context"]),
        event_trigger=dict(setup_payload["event_trigger"]),
        regime_filter=dict(setup_payload["regime_filter"]),
        confirmation=dict(setup_payload["confirmation"]),
        invalidation=dict(setup_payload["invalidation"]),
        stop=dict(setup_payload["stop"]),
        target=dict(setup_payload["target"]),
        hold_time=dict(setup_payload["hold_time"]),
        horizon=setup_payload["horizon"],
        path_label=setup_payload["path_label"],
        allowed_variants=list(setup_payload["allowed_variants"]),
        forbidden_post_hoc_changes=list(setup_payload["forbidden_post_hoc_changes"]),
        mechanism_id=mechanism_id,
        stamp=setup_payload.get("stamp", EXPLORATORY_STAMP),
    )


__all__ = [
    "ALLOWED_STUDY_KINDS",
    "CONTEXT_NOT_EQUAL_TRIGGER",
    "IDEA_DRAFT_FIELDS",
    "IdeaDraft",
    "IdeaValidationBundle",
    "MAIN_EFFECT",
    "build_idea_validation_bundle",
    "validate_idea_draft",
    "validate_study_kind",
]
