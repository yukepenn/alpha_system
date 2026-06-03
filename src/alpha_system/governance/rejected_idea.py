"""RejectedIdeaRecord contract and append-only research graveyard ledger."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any, cast

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
    validate_required_fields,
    validate_schema,
)

REJECTED_IDEA_REQUIRED_FIELDS = (
    "rejected_id",
    "alpha_spec_id_or_hypothesis_id",
    "reason_category",
    "evidence_references",
    "duplicate_links",
    "leakage_cost_weakness_notes",
    "reviewer",
    "created_at",
)
REJECTED_IDEA_ID_COMPONENT_FIELDS = tuple(
    field for field in REJECTED_IDEA_REQUIRED_FIELDS if field != "rejected_id"
)
REJECTED_IDEA_FIELD_TYPES: dict[str, ExpectedType] = {
    "rejected_id": str,
    "alpha_spec_id_or_hypothesis_id": str,
    "reason_category": str,
    "evidence_references": list,
    "duplicate_links": list,
    "leakage_cost_weakness_notes": list,
    "reviewer": str,
    "created_at": str,
}
RECONSIDERATION_REQUIRED_FIELDS = (
    "rejected_id",
    "reconsidered_idea_id",
    "reconsideration_reference",
    "rationale",
    "reviewer",
    "created_at",
)
RECONSIDERATION_FIELD_TYPES: dict[str, ExpectedType] = {
    "rejected_id": str,
    "reconsidered_idea_id": str,
    "reconsideration_reference": str,
    "rationale": str,
    "reviewer": str,
    "created_at": str,
}
LEDGER_REQUIRED_FIELDS = ("records", "reconsiderations")
LEDGER_FIELD_TYPES: dict[str, ExpectedType] = {
    "records": list,
    "reconsiderations": list,
}
REJECTION_IS_PERMANENT_BAN = False

_UTC_SECONDS_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
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


class RejectedIdeaReasonCategory(StrEnum):
    """Closed reasons for first-class research graveyard records."""

    DUPLICATE = "duplicate"
    LEAKAGE = "leakage"
    WEAK_EVIDENCE = "weak_evidence"
    COST = "cost"
    FAILED_DIAGNOSTICS = "failed_diagnostics"
    OUT_OF_SCOPE = "out_of_scope"
    OTHER = "other"


REJECTED_IDEA_REASON_CATEGORY_DESCRIPTIONS = MappingProxyType(
    {
        RejectedIdeaReasonCategory.DUPLICATE.value: (
            "The idea duplicates, materially overlaps, or is equivalent to an existing "
            "hypothesis, AlphaSpec, or feature request."
        ),
        RejectedIdeaReasonCategory.LEAKAGE.value: (
            "The idea depends on lookahead, target leakage, locked-test contamination, "
            "or another inadmissible information path."
        ),
        RejectedIdeaReasonCategory.WEAK_EVIDENCE.value: (
            "The available evidence is incomplete, too weak, or fails to satisfy the "
            "campaign evidence standard."
        ),
        RejectedIdeaReasonCategory.COST.value: (
            "The expected implementation, compute, data, review, or maintenance cost is "
            "not justified under the current research budget."
        ),
        RejectedIdeaReasonCategory.FAILED_DIAGNOSTICS.value: (
            "A referenced diagnostic, trial, negative control, or validation check failed "
            "or was abandoned."
        ),
        RejectedIdeaReasonCategory.OUT_OF_SCOPE.value: (
            "The idea is outside the approved campaign, data, market, instrument, or "
            "operational scope."
        ),
        RejectedIdeaReasonCategory.OTHER.value: (
            "A reviewer-recorded reason that does not fit the other closed categories."
        ),
    }
)


@dataclass(frozen=True, slots=True)
class RejectedIdeaRecord:
    """Validated first-class record for a rejected, duplicate, leaky, or weak idea."""

    rejected_id: str
    alpha_spec_id_or_hypothesis_id: str
    reason_category: RejectedIdeaReasonCategory
    evidence_references: tuple[str, ...]
    duplicate_links: tuple[str, ...]
    leakage_cost_weakness_notes: tuple[str, ...]
    reviewer: str
    created_at: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> RejectedIdeaRecord:
        """Build a `RejectedIdeaRecord` from a mapping after validation."""

        return validate_rejected_idea_record(payload)

    @classmethod
    def from_canonical_json(cls, text: str) -> RejectedIdeaRecord:
        """Deserialize canonical JSON and validate the resulting record."""

        value = deserialize(text)
        mapping = require_mapping(value, object_name="RejectedIdeaRecord")
        return validate_rejected_idea_record(mapping)

    @property
    def implies_permanent_ban(self) -> bool:
        """Rejected ideas may be reconsidered through explicit linked records."""

        return REJECTION_IS_PERMANENT_BAN

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a strict JSON-compatible representation."""

        return {
            "rejected_id": self.rejected_id,
            "alpha_spec_id_or_hypothesis_id": self.alpha_spec_id_or_hypothesis_id,
            "reason_category": self.reason_category.value,
            "evidence_references": list(self.evidence_references),
            "duplicate_links": list(self.duplicate_links),
            "leakage_cost_weakness_notes": list(self.leakage_cost_weakness_notes),
            "reviewer": self.reviewer,
            "created_at": self.created_at,
        }

    def to_canonical_json(self) -> str:
        """Serialize the validated record through the canonical primitive."""

        return canonical_serialize(self.to_dict())


@dataclass(frozen=True, slots=True)
class RejectedIdeaReconsideration:
    """Explicit linked reconsideration pointer that leaves the rejection intact."""

    rejected_id: str
    reconsidered_idea_id: str
    reconsideration_reference: str
    rationale: str
    reviewer: str
    created_at: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> RejectedIdeaReconsideration:
        """Build a reconsideration link from a mapping after validation."""

        return validate_rejected_idea_reconsideration(payload)

    @classmethod
    def from_canonical_json(cls, text: str) -> RejectedIdeaReconsideration:
        """Deserialize canonical JSON and validate the resulting link."""

        value = deserialize(text)
        mapping = require_mapping(value, object_name="RejectedIdeaReconsideration")
        return validate_rejected_idea_reconsideration(mapping)

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a strict JSON-compatible representation."""

        return {
            "rejected_id": self.rejected_id,
            "reconsidered_idea_id": self.reconsidered_idea_id,
            "reconsideration_reference": self.reconsideration_reference,
            "rationale": self.rationale,
            "reviewer": self.reviewer,
            "created_at": self.created_at,
        }

    def to_canonical_json(self) -> str:
        """Serialize the reconsideration link through the canonical primitive."""

        return canonical_serialize(self.to_dict())


class ResearchGraveyardLedger:
    """Append-only in-memory ledger for rejected ideas and reconsideration links."""

    def __init__(
        self,
        records: Iterable[RejectedIdeaRecord | Mapping[str, Any]] = (),
        reconsiderations: Iterable[RejectedIdeaReconsideration | Mapping[str, Any]] = (),
    ) -> None:
        self._record_order: list[str] = []
        self._records_by_id: dict[str, RejectedIdeaRecord] = {}
        self._records_by_referenced_idea: dict[str, list[str]] = {}
        self._reconsideration_order: list[tuple[str, str]] = []
        self._reconsiderations_by_key: dict[
            tuple[str, str],
            RejectedIdeaReconsideration,
        ] = {}
        self._reconsiderations_by_rejected_id: dict[
            str,
            list[RejectedIdeaReconsideration],
        ] = {}
        for record in records:
            self.append(record)
        for reconsideration in reconsiderations:
            self.append_reconsideration(reconsideration)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> ResearchGraveyardLedger:
        """Build a ledger from a serialized mapping."""

        mapping = validate_schema(
            payload,
            required_fields=LEDGER_REQUIRED_FIELDS,
            field_types=LEDGER_FIELD_TYPES,
            allowed_fields=LEDGER_REQUIRED_FIELDS,
            object_name="ResearchGraveyardLedger",
        )
        return cls(
            records=cast(list[Mapping[str, Any]], mapping["records"]),
            reconsiderations=cast(list[Mapping[str, Any]], mapping["reconsiderations"]),
        )

    @classmethod
    def from_canonical_json(cls, text: str) -> ResearchGraveyardLedger:
        """Deserialize canonical JSON and validate the resulting ledger."""

        value = deserialize(text)
        mapping = require_mapping(value, object_name="ResearchGraveyardLedger")
        return cls.from_mapping(mapping)

    def append(
        self,
        record: RejectedIdeaRecord | Mapping[str, Any],
    ) -> RejectedIdeaRecord:
        """Append a rejected idea record; duplicate IDs fail closed."""

        rejected_record = _coerce_rejected_record(record)
        if rejected_record.rejected_id in self._records_by_id:
            raise GovernanceValidationError(
                ValidationIssue(
                    field="rejected_id",
                    code="duplicate_rejected_id",
                    message="ResearchGraveyardLedger cannot overwrite a rejected idea record",
                    expected="new RejectedIdeaRecord ID",
                    actual=rejected_record.rejected_id,
                )
            )
        self._records_by_id[rejected_record.rejected_id] = rejected_record
        self._record_order.append(rejected_record.rejected_id)
        self._records_by_referenced_idea.setdefault(
            rejected_record.alpha_spec_id_or_hypothesis_id,
            [],
        ).append(rejected_record.rejected_id)
        return rejected_record

    def list_records(self) -> tuple[RejectedIdeaRecord, ...]:
        """Return all rejected records in append order."""

        return tuple(self._records_by_id[rejected_id] for rejected_id in self._record_order)

    def lookup_by_id(self, rejected_id: str) -> RejectedIdeaRecord | None:
        """Look up one rejected record by `rejected_id`."""

        _validate_rejected_id(rejected_id, field="rejected_id")
        return self._records_by_id.get(rejected_id)

    def lookup_by_referenced_idea(
        self,
        alpha_spec_id_or_hypothesis_id: str,
    ) -> tuple[RejectedIdeaRecord, ...]:
        """Look up rejected records for an AlphaSpec or HypothesisCard ID."""

        _validate_alpha_spec_or_hypothesis_id(
            alpha_spec_id_or_hypothesis_id,
            field="alpha_spec_id_or_hypothesis_id",
        )
        rejected_ids = self._records_by_referenced_idea.get(alpha_spec_id_or_hypothesis_id, [])
        return tuple(self._records_by_id[rejected_id] for rejected_id in rejected_ids)

    def append_reconsideration(
        self,
        reconsideration: RejectedIdeaReconsideration | Mapping[str, Any],
    ) -> RejectedIdeaReconsideration:
        """Append an explicit reconsideration link without mutating the rejection."""

        link = _coerce_reconsideration(reconsideration)
        if link.rejected_id not in self._records_by_id:
            raise GovernanceValidationError(
                ValidationIssue(
                    field="rejected_id",
                    code="unknown_rejected_id",
                    message="reconsideration links must point to an existing rejected record",
                    expected="known RejectedIdeaRecord ID",
                    actual=link.rejected_id,
                )
            )
        key = (link.rejected_id, link.reconsideration_reference)
        if key in self._reconsiderations_by_key:
            raise GovernanceValidationError(
                ValidationIssue(
                    field="reconsideration_reference",
                    code="duplicate_reconsideration_reference",
                    message="ResearchGraveyardLedger cannot overwrite a reconsideration link",
                    expected="new reconsideration reference for this rejected record",
                    actual=link.reconsideration_reference,
                )
            )
        self._reconsiderations_by_key[key] = link
        self._reconsideration_order.append(key)
        self._reconsiderations_by_rejected_id.setdefault(link.rejected_id, []).append(link)
        return link

    def list_reconsiderations(
        self,
        rejected_id: str | None = None,
    ) -> tuple[RejectedIdeaReconsideration, ...]:
        """Return explicit reconsideration links, optionally scoped by rejected ID."""

        if rejected_id is None:
            return tuple(self._reconsiderations_by_key[key] for key in self._reconsideration_order)
        _validate_rejected_id(rejected_id, field="rejected_id")
        return tuple(self._reconsiderations_by_rejected_id.get(rejected_id, ()))

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a serialized ledger snapshot without persisting it."""

        return {
            "records": [record.to_dict() for record in self.list_records()],
            "reconsiderations": [link.to_dict() for link in self.list_reconsiderations()],
        }

    def to_canonical_json(self) -> str:
        """Serialize the ledger snapshot through the canonical primitive."""

        return canonical_serialize(self.to_dict())

    def __iter__(self) -> Iterable[RejectedIdeaRecord]:
        """Iterate rejected records in append order."""

        return iter(self.list_records())

    def __len__(self) -> int:
        """Return the number of rejected records."""

        return len(self._record_order)


def create_rejected_idea_record(
    *,
    alpha_spec_id_or_hypothesis_id: str,
    reason_category: RejectedIdeaReasonCategory | str,
    evidence_references: list[str],
    duplicate_links: list[str],
    leakage_cost_weakness_notes: list[str],
    reviewer: str,
    created_at: str,
) -> RejectedIdeaRecord:
    """Create a validated `RejectedIdeaRecord` without changing lifecycle state."""

    payload: dict[str, JsonValue] = {
        "alpha_spec_id_or_hypothesis_id": alpha_spec_id_or_hypothesis_id,
        "reason_category": _reason_category_value(reason_category),
        "evidence_references": list(evidence_references),
        "duplicate_links": list(duplicate_links),
        "leakage_cost_weakness_notes": list(leakage_cost_weakness_notes),
        "reviewer": reviewer,
        "created_at": created_at,
    }
    payload["rejected_id"] = generate_rejected_idea_id(payload)
    return validate_rejected_idea_record(payload)


def create_rejected_idea_reconsideration(
    *,
    rejected_id: str,
    reconsidered_idea_id: str,
    reconsideration_reference: str,
    rationale: str,
    reviewer: str,
    created_at: str,
) -> RejectedIdeaReconsideration:
    """Create a validated explicit reconsideration link."""

    return validate_rejected_idea_reconsideration(
        {
            "rejected_id": rejected_id,
            "reconsidered_idea_id": reconsidered_idea_id,
            "reconsideration_reference": reconsideration_reference,
            "rationale": rationale,
            "reviewer": reviewer,
            "created_at": created_at,
        }
    )


def generate_rejected_idea_id(payload: Mapping[str, Any]) -> str:
    """Generate the deterministic RejectedIdeaRecord ID from content fields."""

    mapping = validate_required_fields(
        payload,
        REJECTED_IDEA_ID_COMPONENT_FIELDS,
        object_name="RejectedIdeaRecord",
    )
    components = {
        field: _normalize_id_component(field, mapping[field])
        for field in REJECTED_IDEA_ID_COMPONENT_FIELDS
    }
    return generate_governance_id(GovernanceIdKind.REJECTED_IDEA_RECORD, components)


def validate_rejected_idea_record(payload: Mapping[str, Any]) -> RejectedIdeaRecord:
    """Validate a `RejectedIdeaRecord` mapping fail-closed and return a record."""

    mapping = validate_schema(
        payload,
        required_fields=REJECTED_IDEA_REQUIRED_FIELDS,
        field_types=REJECTED_IDEA_FIELD_TYPES,
        allowed_fields=REJECTED_IDEA_REQUIRED_FIELDS,
        object_name="RejectedIdeaRecord",
    )

    issues: list[ValidationIssue] = []
    issues.extend(_validate_rejected_id(mapping["rejected_id"], field="rejected_id"))
    issues.extend(
        _validate_alpha_spec_or_hypothesis_id(
            mapping["alpha_spec_id_or_hypothesis_id"],
            field="alpha_spec_id_or_hypothesis_id",
        )
    )
    reason_category = _parse_reason_category(mapping["reason_category"], issues)
    issues.extend(
        _validate_substantive_string_list(
            mapping["evidence_references"],
            field="evidence_references",
            item_name="evidence reference",
        )
    )
    issues.extend(
        _validate_substantive_string_list(
            mapping["duplicate_links"],
            field="duplicate_links",
            item_name="duplicate or equivalence reference",
        )
    )
    issues.extend(
        _validate_substantive_string_list(
            mapping["leakage_cost_weakness_notes"],
            field="leakage_cost_weakness_notes",
            item_name="review note",
        )
    )
    issues.extend(_validate_text_field(mapping["reviewer"], field="reviewer"))
    issues.extend(_validate_created_at(mapping["created_at"], field="created_at"))
    issues.extend(_validate_canonical_serializable(mapping))

    if not issues:
        expected_id = generate_rejected_idea_id(mapping)
        if mapping["rejected_id"] != expected_id:
            issues.append(
                ValidationIssue(
                    field="rejected_id",
                    code="rejected_id_mismatch",
                    message=(
                        "RejectedIdeaRecord.rejected_id must match deterministic "
                        "RejectedIdeaRecord content"
                    ),
                    expected=expected_id,
                    actual=str(mapping["rejected_id"]),
                )
            )

    if issues:
        raise GovernanceValidationError(issues)

    assert reason_category is not None
    return RejectedIdeaRecord(
        rejected_id=mapping["rejected_id"],
        alpha_spec_id_or_hypothesis_id=mapping["alpha_spec_id_or_hypothesis_id"],
        reason_category=reason_category,
        evidence_references=tuple(mapping["evidence_references"]),
        duplicate_links=tuple(mapping["duplicate_links"]),
        leakage_cost_weakness_notes=tuple(mapping["leakage_cost_weakness_notes"]),
        reviewer=mapping["reviewer"],
        created_at=mapping["created_at"],
    )


def validate_rejected_idea_reconsideration(
    payload: Mapping[str, Any],
) -> RejectedIdeaReconsideration:
    """Validate an explicit reconsideration link fail-closed."""

    mapping = validate_schema(
        payload,
        required_fields=RECONSIDERATION_REQUIRED_FIELDS,
        field_types=RECONSIDERATION_FIELD_TYPES,
        allowed_fields=RECONSIDERATION_REQUIRED_FIELDS,
        object_name="RejectedIdeaReconsideration",
    )

    issues: list[ValidationIssue] = []
    issues.extend(_validate_rejected_id(mapping["rejected_id"], field="rejected_id"))
    issues.extend(
        _validate_alpha_spec_or_hypothesis_id(
            mapping["reconsidered_idea_id"],
            field="reconsidered_idea_id",
        )
    )
    for field in ("reconsideration_reference", "rationale", "reviewer"):
        issues.extend(_validate_text_field(mapping[field], field=field))
    issues.extend(_validate_created_at(mapping["created_at"], field="created_at"))
    issues.extend(_validate_reconsideration_canonical_serializable(mapping))

    if issues:
        raise GovernanceValidationError(issues)

    return RejectedIdeaReconsideration(
        rejected_id=mapping["rejected_id"],
        reconsidered_idea_id=mapping["reconsidered_idea_id"],
        reconsideration_reference=mapping["reconsideration_reference"],
        rationale=mapping["rationale"],
        reviewer=mapping["reviewer"],
        created_at=mapping["created_at"],
    )


def _coerce_rejected_record(
    record: RejectedIdeaRecord | Mapping[str, Any],
) -> RejectedIdeaRecord:
    if isinstance(record, RejectedIdeaRecord):
        return validate_rejected_idea_record(record.to_dict())
    if isinstance(record, Mapping):
        return validate_rejected_idea_record(record)
    raise GovernanceValidationError(
        ValidationIssue(
            field="record",
            code="invalid_record_type",
            message="ResearchGraveyardLedger accepts only RejectedIdeaRecord mappings",
            expected="RejectedIdeaRecord or mapping",
            actual=type(record).__name__,
        )
    )


def _coerce_reconsideration(
    reconsideration: RejectedIdeaReconsideration | Mapping[str, Any],
) -> RejectedIdeaReconsideration:
    if isinstance(reconsideration, RejectedIdeaReconsideration):
        return validate_rejected_idea_reconsideration(reconsideration.to_dict())
    if isinstance(reconsideration, Mapping):
        return validate_rejected_idea_reconsideration(reconsideration)
    raise GovernanceValidationError(
        ValidationIssue(
            field="reconsideration",
            code="invalid_reconsideration_type",
            message=("ResearchGraveyardLedger accepts only RejectedIdeaReconsideration mappings"),
            expected="RejectedIdeaReconsideration or mapping",
            actual=type(reconsideration).__name__,
        )
    )


def _validate_rejected_id(value: Any, *, field: str) -> list[ValidationIssue]:
    try:
        validate_governance_id(value, expected_kind=GovernanceIdKind.REJECTED_IDEA_RECORD)
    except GovernanceIdError as exc:
        return [
            ValidationIssue(
                field=field,
                code=exc.issue.code,
                message=exc.issue.message,
                expected=GovernanceIdKind.REJECTED_IDEA_RECORD.value,
                actual=str(exc.issue.value),
            )
        ]
    return []


def _validate_alpha_spec_or_hypothesis_id(
    value: Any,
    *,
    field: str,
) -> list[ValidationIssue]:
    for kind in (GovernanceIdKind.ALPHA_SPEC, GovernanceIdKind.HYPOTHESIS_CARD):
        try:
            validate_governance_id(value, expected_kind=kind)
            return []
        except GovernanceIdError:
            continue
    return [
        ValidationIssue(
            field=field,
            code="invalid_referenced_idea_id",
            message=(
                "RejectedIdeaRecord references must be AlphaSpec or HypothesisCard governance IDs"
            ),
            expected=(
                f"{GovernanceIdKind.ALPHA_SPEC.value} or {GovernanceIdKind.HYPOTHESIS_CARD.value}"
            ),
            actual=str(value),
        )
    ]


def _parse_reason_category(
    value: Any,
    issues: list[ValidationIssue],
) -> RejectedIdeaReasonCategory | None:
    try:
        return RejectedIdeaReasonCategory(value)
    except ValueError:
        issues.append(
            ValidationIssue(
                field="reason_category",
                code="invalid_reason_category",
                message="RejectedIdeaRecord.reason_category must be a declared category",
                expected=" | ".join(category.value for category in RejectedIdeaReasonCategory),
                actual=str(value),
            )
        )
        return None


def _reason_category_value(reason_category: RejectedIdeaReasonCategory | str) -> str:
    try:
        return RejectedIdeaReasonCategory(reason_category).value
    except ValueError as exc:
        raise GovernanceValidationError(
            ValidationIssue(
                field="reason_category",
                code="invalid_reason_category",
                message="RejectedIdeaRecord.reason_category must be a declared category",
                expected=" | ".join(value.value for value in RejectedIdeaReasonCategory),
                actual=str(reason_category),
            )
        ) from exc


def _validate_substantive_string_list(
    values: list[Any],
    *,
    field: str,
    item_name: str,
) -> list[ValidationIssue]:
    if not values:
        return [
            ValidationIssue(
                field=field,
                code="empty_required_field",
                message=f"RejectedIdeaRecord.{field} must contain at least one {item_name}",
                expected=f"non-empty list of explicit {item_name}s",
                actual="empty list",
            )
        ]

    issues: list[ValidationIssue] = []
    seen: set[str] = set()
    for index, item in enumerate(values):
        item_field = f"{field}[{index}]"
        if type(item) is not str:
            issues.append(
                ValidationIssue(
                    field=item_field,
                    code="invalid_item_type",
                    message=f"RejectedIdeaRecord.{item_field} must be a string",
                    expected=f"explicit {item_name}",
                    actual=type(item).__name__,
                )
            )
            continue
        if _normalize_text(item) in _VAGUE_TEXT:
            issues.append(
                ValidationIssue(
                    field=item_field,
                    code="empty_required_field",
                    message=f"RejectedIdeaRecord.{item_field} must be explicit",
                    expected=f"non-empty explicit {item_name}",
                    actual=item,
                )
            )
            continue
        if item in seen:
            issues.append(
                ValidationIssue(
                    field=item_field,
                    code="duplicate_reference",
                    message=f"RejectedIdeaRecord.{field} must not contain duplicate entries",
                    expected="unique explicit references",
                    actual=item,
                )
            )
        seen.add(item)
    return issues


def _validate_text_field(value: str, *, field: str) -> list[ValidationIssue]:
    if _normalize_text(value) not in _VAGUE_TEXT:
        return []
    return [
        ValidationIssue(
            field=field,
            code="empty_required_field",
            message=f"RejectedIdeaRecord.{field} must be explicit",
            expected="non-empty explicit string",
            actual=str(value),
        )
    ]


def _validate_created_at(value: str, *, field: str) -> list[ValidationIssue]:
    if _normalize_text(value) in _VAGUE_TEXT:
        return [
            ValidationIssue(
                field=field,
                code="empty_required_field",
                message=f"RejectedIdeaRecord.{field} must be explicit",
                expected="UTC timestamp in YYYY-MM-DDTHH:MM:SSZ format",
                actual=str(value),
            )
        ]
    if _UTC_SECONDS_PATTERN.fullmatch(value) is None:
        return [
            ValidationIssue(
                field=field,
                code="invalid_created_at",
                message=("RejectedIdeaRecord.created_at must use UTC YYYY-MM-DDTHH:MM:SSZ format"),
                expected="YYYY-MM-DDTHH:MM:SSZ",
                actual=value,
            )
        ]
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return [
            ValidationIssue(
                field=field,
                code="invalid_created_at",
                message="RejectedIdeaRecord.created_at must be a real UTC timestamp",
                expected="valid UTC timestamp",
                actual=value,
            )
        ]
    return []


def _validate_canonical_serializable(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    try:
        canonical_serialize(
            {
                field: _normalize_id_component(field, mapping[field])
                for field in REJECTED_IDEA_REQUIRED_FIELDS
                if field in mapping
            }
        )
    except GovernanceSerializationError as exc:
        return [
            ValidationIssue(
                field=exc.issue.path,
                code=exc.issue.code,
                message=exc.issue.message,
                expected="canonical JSON-compatible RejectedIdeaRecord",
                actual=exc.issue.path,
            )
        ]
    return []


def _validate_reconsideration_canonical_serializable(
    mapping: Mapping[str, Any],
) -> list[ValidationIssue]:
    try:
        canonical_serialize(
            {
                field: cast(JsonValue, mapping[field])
                for field in RECONSIDERATION_REQUIRED_FIELDS
                if field in mapping
            }
        )
    except GovernanceSerializationError as exc:
        return [
            ValidationIssue(
                field=exc.issue.path,
                code=exc.issue.code,
                message=exc.issue.message,
                expected="canonical JSON-compatible RejectedIdeaReconsideration",
                actual=exc.issue.path,
            )
        ]
    return []


def _normalize_id_component(field: str, value: Any) -> JsonValue:
    if field == "reason_category":
        return _reason_category_value(value)
    if isinstance(value, RejectedIdeaReasonCategory):
        return value.value
    return cast(JsonValue, value)


def _normalize_text(value: object) -> str:
    if isinstance(value, str):
        return " ".join(value.strip().lower().split())
    return str(value).strip().lower()


__all__ = [
    "LEDGER_FIELD_TYPES",
    "LEDGER_REQUIRED_FIELDS",
    "RECONSIDERATION_FIELD_TYPES",
    "RECONSIDERATION_REQUIRED_FIELDS",
    "REJECTED_IDEA_FIELD_TYPES",
    "REJECTED_IDEA_ID_COMPONENT_FIELDS",
    "REJECTED_IDEA_REASON_CATEGORY_DESCRIPTIONS",
    "REJECTED_IDEA_REQUIRED_FIELDS",
    "REJECTION_IS_PERMANENT_BAN",
    "RejectedIdeaReasonCategory",
    "RejectedIdeaReconsideration",
    "RejectedIdeaRecord",
    "ResearchGraveyardLedger",
    "create_rejected_idea_record",
    "create_rejected_idea_reconsideration",
    "generate_rejected_idea_id",
    "validate_rejected_idea_record",
    "validate_rejected_idea_reconsideration",
]
