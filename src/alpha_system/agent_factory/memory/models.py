"""Rejected-idea and research memory contracts for Agent Factory."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from alpha_system.agent_factory.permissions.matrix import ROSTER_ROLE_IDS
from alpha_system.agent_factory.tools.results import (
    FORBIDDEN_HEAVY_SUFFIXES,
    FORBIDDEN_RESULT_MARKERS,
    RAW_OBJECT_MODULE_PREFIXES,
)
from alpha_system.governance.rejected_idea import (
    RejectedIdeaRecord,
    ResearchGraveyardLedger,
)

MAX_MEMORY_TEXT_LENGTH = 2048
MAX_MEMORY_TUPLE_LENGTH = 50

CONTRACT_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_.:-]*$")
IDEA_KEY_PATTERN = re.compile(r"^idea:[a-f0-9]{24}$")
IDEA_FINGERPRINT_PATTERN = re.compile(r"^idea_fingerprint:sha256:[a-f0-9]{64}$")

FORBIDDEN_MEMORY_MARKERS: tuple[str, ...] = FORBIDDEN_RESULT_MARKERS + (
    "embedded_values",
    "embedded values",
    "value_array",
    "value array",
    "feature_values",
    "label_values",
    "runtime_values",
    "market_values",
    "array values",
    "list[float]",
    "list[int]",
    "db blob",
    "binary blob",
)

TERMINAL_RESEARCH_MEMORY_STATUSES: frozenset[str] = frozenset(
    {"REJECTED", "FAILED", "DUPLICATE"}
)

IdeaCandidate = str | Mapping[str, object]


class RejectedIdeaMemoryStatus(StrEnum):
    """Statuses for a visible rejected or failed idea memory record."""

    REJECTED = "REJECTED"
    FAILED = "FAILED"
    DUPLICATE = "DUPLICATE"
    BLOCKED = "BLOCKED"


class ResearchMemoryStatus(StrEnum):
    """Bounded lifecycle statuses for value-free research memory."""

    DRAFTED = "DRAFTED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"
    DUPLICATE = "DUPLICATE"
    INCONCLUSIVE = "INCONCLUSIVE"
    WATCH = "WATCH"
    BLOCKED = "BLOCKED"
    REFERENCE_HANDOFF_RECORDED = "REFERENCE_HANDOFF_RECORDED"


@dataclass(frozen=True, slots=True)
class RejectedIdeaMemoryRecord:
    """Value-free memory row that keeps a rejected or failed idea visible."""

    memory_id: str
    idea_key: str
    idea_fingerprint: str
    status: RejectedIdeaMemoryStatus
    alpha_spec_id: str | None
    originating_role_id: str
    graveyard_rejected_ids: tuple[str, ...]
    rejection_reasons: tuple[str, ...]
    decision_refs: tuple[str, ...]
    handoff_refs: tuple[str, ...]
    tool_invocation_refs: tuple[str, ...]
    spec_refs: tuple[str, ...]
    next_required_gate: str
    summary: str
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_record_id("memory_id", self.memory_id, "rejected_idea_memory:")
        _validate_idea_key("idea_key", self.idea_key)
        _validate_idea_fingerprint("idea_fingerprint", self.idea_fingerprint)
        object.__setattr__(
            self,
            "status",
            _coerce_enum(RejectedIdeaMemoryStatus, self.status, "status"),
        )
        _validate_optional_identifier("alpha_spec_id", self.alpha_spec_id)
        _validate_role_id("originating_role_id", self.originating_role_id)
        _validate_prefixed_ref_tuple(
            "graveyard_rejected_ids",
            self.graveyard_rejected_ids,
            "rej_",
            allow_empty=False,
        )
        _validate_text_tuple("rejection_reasons", self.rejection_reasons, allow_empty=False)
        _validate_prefixed_ref_tuple(
            "decision_refs",
            self.decision_refs,
            "agent_decision:",
            allow_empty=False,
        )
        _validate_prefixed_ref_tuple(
            "handoff_refs",
            self.handoff_refs,
            "agent_handoff:",
            allow_empty=True,
        )
        _validate_prefixed_ref_tuple(
            "tool_invocation_refs",
            self.tool_invocation_refs,
            "tool_invocation:",
            allow_empty=True,
        )
        _validate_identifier_tuple("spec_refs", self.spec_refs, allow_empty=True)
        if not self.tool_invocation_refs and not self.spec_refs:
            raise ValueError(
                "RejectedIdeaMemoryRecord requires tool_invocation_refs or spec_refs"
            )
        _validate_identifier("next_required_gate", self.next_required_gate)
        _validate_text("summary", self.summary)
        _validate_identifier_tuple("limitations", self.limitations, allow_empty=False)


@dataclass(frozen=True, slots=True)
class ResearchMemoryRecord:
    """Value-free research memory entry linked to Agent Factory activity refs."""

    memory_id: str
    idea_key: str
    idea_fingerprint: str
    status: ResearchMemoryStatus
    originating_role_id: str
    prior_outcome_summary: str
    decision_refs: tuple[str, ...]
    handoff_refs: tuple[str, ...]
    tool_invocation_refs: tuple[str, ...]
    spec_refs: tuple[str, ...]
    related_rejected_memory_refs: tuple[str, ...]
    next_required_gate: str
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_record_id("memory_id", self.memory_id, "research_memory:")
        _validate_idea_key("idea_key", self.idea_key)
        _validate_idea_fingerprint("idea_fingerprint", self.idea_fingerprint)
        object.__setattr__(
            self,
            "status",
            _coerce_enum(ResearchMemoryStatus, self.status, "status"),
        )
        _validate_role_id("originating_role_id", self.originating_role_id)
        _validate_text("prior_outcome_summary", self.prior_outcome_summary)
        _validate_prefixed_ref_tuple(
            "decision_refs",
            self.decision_refs,
            "agent_decision:",
            allow_empty=True,
        )
        _validate_prefixed_ref_tuple(
            "handoff_refs",
            self.handoff_refs,
            "agent_handoff:",
            allow_empty=True,
        )
        _validate_prefixed_ref_tuple(
            "tool_invocation_refs",
            self.tool_invocation_refs,
            "tool_invocation:",
            allow_empty=True,
        )
        _validate_identifier_tuple("spec_refs", self.spec_refs, allow_empty=True)
        _validate_prefixed_ref_tuple(
            "related_rejected_memory_refs",
            self.related_rejected_memory_refs,
            "rejected_idea_memory:",
            allow_empty=True,
        )
        if not (
            self.decision_refs
            or self.handoff_refs
            or self.tool_invocation_refs
            or self.spec_refs
            or self.related_rejected_memory_refs
        ):
            raise ValueError("ResearchMemoryRecord requires at least one activity or memory ref")
        if (
            self.status.value in TERMINAL_RESEARCH_MEMORY_STATUSES
            and not self.related_rejected_memory_refs
        ):
            raise ValueError(
                "terminal rejected or failed research memory requires a rejected memory ref"
            )
        _validate_identifier("next_required_gate", self.next_required_gate)
        _validate_identifier_tuple("limitations", self.limitations, allow_empty=False)


@dataclass(frozen=True, slots=True)
class DuplicateIdeaReport:
    """Pure duplicate-check result carrying ids, refs, and reasons only."""

    idea_key: str
    idea_fingerprint: str
    already_rejected: bool
    matched_memory_refs: tuple[str, ...]
    matched_graveyard_refs: tuple[str, ...]
    rejection_reasons: tuple[str, ...]
    next_required_gate: str

    def __post_init__(self) -> None:
        _validate_idea_key("idea_key", self.idea_key)
        _validate_idea_fingerprint("idea_fingerprint", self.idea_fingerprint)
        if not isinstance(self.already_rejected, bool):
            raise TypeError("already_rejected must be a bool")
        _validate_prefixed_ref_tuple(
            "matched_memory_refs",
            self.matched_memory_refs,
            "rejected_idea_memory:",
            allow_empty=True,
        )
        _validate_prefixed_ref_tuple(
            "matched_graveyard_refs",
            self.matched_graveyard_refs,
            "rej_",
            allow_empty=True,
        )
        _validate_text_tuple("rejection_reasons", self.rejection_reasons, allow_empty=True)
        _validate_identifier("next_required_gate", self.next_required_gate)


def idea_fingerprint(candidate: IdeaCandidate) -> str:
    """Return a deterministic value-free fingerprint for an idea summary."""

    digest = _idea_digest(candidate)
    return f"idea_fingerprint:sha256:{digest}"


def idea_key(candidate: IdeaCandidate) -> str:
    """Return the short deterministic idea key used for duplicate checks."""

    return f"idea:{_idea_digest(candidate)[:24]}"


def detect_duplicate_idea(
    candidate: IdeaCandidate,
    memory_records: Iterable[RejectedIdeaMemoryRecord],
    graveyard: ResearchGraveyardLedger | None = None,
) -> DuplicateIdeaReport:
    """Report whether a candidate already appears in memory or the graveyard."""

    key = idea_key(candidate)
    fingerprint = idea_fingerprint(candidate)
    records = _rejected_memory_records_tuple(memory_records)
    memory_matches = tuple(record for record in records if record.idea_key == key)
    graveyard_matches = _graveyard_matches(candidate, memory_matches, graveyard)
    reasons = _unique_text(
        tuple(reason for record in memory_matches for reason in record.rejection_reasons)
        + tuple(reason for record in graveyard_matches for reason in _graveyard_reasons(record))
    )
    already_rejected = bool(memory_matches or graveyard_matches)
    next_gate = (
        memory_matches[0].next_required_gate
        if memory_matches
        else "hypothesis_scout_prior_rejection_review"
        if graveyard_matches
        else "alphaspec_critic_review"
    )
    return DuplicateIdeaReport(
        idea_key=key,
        idea_fingerprint=fingerprint,
        already_rejected=already_rejected,
        matched_memory_refs=tuple(record.memory_id for record in memory_matches),
        matched_graveyard_refs=tuple(record.rejected_id for record in graveyard_matches),
        rejection_reasons=reasons,
        next_required_gate=next_gate,
    )


def prior_rejection_reasons(
    known_idea_key: str,
    memory_records: Iterable[RejectedIdeaMemoryRecord],
    graveyard: ResearchGraveyardLedger | None = None,
) -> tuple[str, ...]:
    """Return recorded rejection reasons for a known idea key."""

    _validate_idea_key("known_idea_key", known_idea_key)
    records = tuple(record for record in _rejected_memory_records_tuple(memory_records))
    matches = tuple(record for record in records if record.idea_key == known_idea_key)
    graveyard_records = _graveyard_matches_by_memory(matches, graveyard)
    return _unique_text(
        tuple(reason for record in matches for reason in record.rejection_reasons)
        + tuple(reason for record in graveyard_records for reason in _graveyard_reasons(record))
    )


def ensure_rejected_ideas_visible(
    memory_records: Iterable[RejectedIdeaMemoryRecord],
    graveyard: ResearchGraveyardLedger,
) -> tuple[RejectedIdeaMemoryRecord, ...]:
    """Fail closed when a graveyard record has no visible memory row."""

    _validate_type("graveyard", graveyard, ResearchGraveyardLedger)
    records = _rejected_memory_records_tuple(memory_records)
    visible_rejected_ids = {
        rejected_id for record in records for rejected_id in record.graveyard_rejected_ids
    }
    graveyard_rejected_ids = {record.rejected_id for record in graveyard.list_records()}
    unknown = sorted(visible_rejected_ids.difference(graveyard_rejected_ids))
    if unknown:
        raise ValueError(
            "rejected idea memory references unknown graveyard records: " + ", ".join(unknown)
        )
    missing = sorted(graveyard_rejected_ids.difference(visible_rejected_ids))
    if missing:
        raise ValueError(
            "rejected idea memory is missing graveyard records: " + ", ".join(missing)
        )
    return records


def _idea_digest(candidate: IdeaCandidate) -> str:
    canonical = _canonical_candidate(candidate)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _canonical_candidate(candidate: IdeaCandidate) -> str:
    if isinstance(candidate, str):
        normalized = _normalize_text(candidate)
        _validate_text("candidate", normalized)
        return json.dumps(("text", normalized), separators=(",", ":"))
    if isinstance(candidate, Mapping):
        if not candidate:
            raise ValueError("candidate mapping must be non-empty")
        normalized_items: list[tuple[str, object]] = []
        for key, value in sorted(candidate.items(), key=lambda item: str(item[0])):
            _validate_text("candidate field", key)
            normalized_items.append((_normalize_text(key), _canonical_candidate_value(value)))
        return json.dumps(normalized_items, separators=(",", ":"), ensure_ascii=True)
    raise TypeError("candidate must be a string or mapping of value-free idea fields")


def _canonical_candidate_value(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, str):
        normalized = _normalize_text(value)
        _validate_text("candidate value", normalized)
        return normalized
    if isinstance(value, tuple | list):
        if not value:
            raise ValueError("candidate sequence values must be non-empty")
        return tuple(sorted(_canonical_candidate_value(item) for item in value))
    raise TypeError("candidate values must be strings, string sequences, or None")


def _candidate_referenced_idea_ids(candidate: IdeaCandidate) -> tuple[str, ...]:
    if not isinstance(candidate, Mapping):
        return ()
    refs: list[str] = []
    for value in candidate.values():
        if isinstance(value, str) and _is_governance_idea_ref(value):
            refs.append(value)
        elif isinstance(value, tuple | list):
            refs.extend(
                item
                for item in value
                if isinstance(item, str) and _is_governance_idea_ref(item)
            )
    return tuple(dict.fromkeys(refs))


def _is_governance_idea_ref(value: str) -> bool:
    return value.startswith(("aspec_", "hyp_"))


def _graveyard_matches(
    candidate: IdeaCandidate,
    memory_matches: tuple[RejectedIdeaMemoryRecord, ...],
    graveyard: ResearchGraveyardLedger | None,
) -> tuple[RejectedIdeaRecord, ...]:
    if graveyard is None:
        return ()
    matches: dict[str, RejectedIdeaRecord] = {}
    for record in _graveyard_matches_by_memory(memory_matches, graveyard):
        matches[record.rejected_id] = record
    candidate_refs = _candidate_referenced_idea_ids(candidate)
    for ref in candidate_refs:
        for record in graveyard.lookup_by_referenced_idea(ref):
            matches[record.rejected_id] = record
    for record in graveyard.list_records():
        if any(ref in record.duplicate_links for ref in candidate_refs):
            matches[record.rejected_id] = record
    return tuple(matches.values())


def _graveyard_matches_by_memory(
    memory_matches: tuple[RejectedIdeaMemoryRecord, ...],
    graveyard: ResearchGraveyardLedger | None,
) -> tuple[RejectedIdeaRecord, ...]:
    if graveyard is None:
        return ()
    matches: dict[str, RejectedIdeaRecord] = {}
    for memory_record in memory_matches:
        for rejected_id in memory_record.graveyard_rejected_ids:
            record = graveyard.lookup_by_id(rejected_id)
            if record is not None:
                matches[record.rejected_id] = record
    return tuple(matches.values())


def _graveyard_reasons(record: RejectedIdeaRecord) -> tuple[str, ...]:
    return tuple(
        f"{record.reason_category.value}: {note}"
        for note in record.leakage_cost_weakness_notes
    )


def _unique_text(values: Iterable[str]) -> tuple[str, ...]:
    unique: list[str] = []
    seen: set[str] = set()
    for value in values:
        _validate_text("rejection_reasons", value)
        if value not in seen:
            unique.append(value)
            seen.add(value)
    return tuple(unique)


def _rejected_memory_records_tuple(
    memory_records: Iterable[RejectedIdeaMemoryRecord],
) -> tuple[RejectedIdeaMemoryRecord, ...]:
    records = tuple(memory_records)
    for record in records:
        _validate_type("memory_records", record, RejectedIdeaMemoryRecord)
    return records


def _coerce_enum[EnumT: StrEnum](
    enum_type: type[EnumT],
    value: object,
    field_name: str,
) -> EnumT:
    _reject_raw_object(field_name, value)
    if isinstance(value, enum_type):
        return value
    if isinstance(value, str):
        _validate_text(field_name, value)
        try:
            return enum_type(value)
        except ValueError as error:
            raise ValueError(f"{field_name} is not a valid {enum_type.__name__}") from error
    raise TypeError(f"{field_name} must be a {enum_type.__name__}")


def _validate_idea_key(field_name: str, value: object) -> None:
    _validate_text(field_name, value)
    if IDEA_KEY_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be an idea:<24 hex> key")


def _validate_idea_fingerprint(field_name: str, value: object) -> None:
    _validate_text(field_name, value)
    if IDEA_FINGERPRINT_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be an idea_fingerprint:sha256:<64 hex> ref")


def _validate_record_id(field_name: str, value: object, prefix: str) -> None:
    _validate_identifier(field_name, value)
    if not value.startswith(prefix):
        raise ValueError(f"{field_name} must start with {prefix}")


def _validate_role_id(field_name: str, value: object) -> None:
    _validate_identifier(field_name, value)
    if value not in ROSTER_ROLE_IDS:
        raise ValueError(f"{field_name} contains an unknown Agent Factory role id")


def _validate_optional_identifier(field_name: str, value: object) -> None:
    if value is None:
        return
    _validate_identifier(field_name, value)


def _validate_prefixed_ref_tuple(
    field_name: str,
    value: object,
    prefix: str,
    *,
    allow_empty: bool,
) -> None:
    _validate_identifier_tuple(field_name, value, allow_empty=allow_empty)
    for item in value:
        if not item.startswith(prefix):
            raise ValueError(f"{field_name} values must start with {prefix}")


def _validate_identifier_tuple(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> None:
    _reject_raw_object(field_name, value)
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple[str, ...]")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must be non-empty")
    if len(value) > MAX_MEMORY_TUPLE_LENGTH:
        raise ValueError(f"{field_name} exceeds memory tuple cap")
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must not contain duplicates")
    for item in value:
        _validate_identifier(field_name, item)


def _validate_text_tuple(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> None:
    _reject_raw_object(field_name, value)
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple[str, ...]")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must be non-empty")
    if len(value) > MAX_MEMORY_TUPLE_LENGTH:
        raise ValueError(f"{field_name} exceeds memory tuple cap")
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must not contain duplicates")
    for item in value:
        _validate_text(field_name, item)


def _validate_identifier(field_name: str, value: object) -> None:
    _validate_text(field_name, value)
    if CONTRACT_ID_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a stable declarative identifier")


def _validate_text(field_name: str, value: object) -> None:
    _reject_raw_object(field_name, value)
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a str")
    if value != value.strip() or not value:
        raise ValueError(f"{field_name} must be non-empty without surrounding whitespace")
    if len(value) > MAX_MEMORY_TEXT_LENGTH:
        raise ValueError(f"{field_name} exceeds memory text length")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{field_name} must be a single-line memory string")
    lowered = value.lower()
    if any(marker in lowered for marker in FORBIDDEN_MEMORY_MARKERS):
        raise ValueError(f"{field_name} contains a forbidden raw/heavy payload marker")
    if any(suffix in lowered for suffix in FORBIDDEN_HEAVY_SUFFIXES):
        raise ValueError(f"{field_name} contains a forbidden heavy artifact reference")


def _validate_type(field_name: str, value: object, expected_type: type[object]) -> None:
    _reject_raw_object(field_name, value)
    if not isinstance(value, expected_type):
        raise TypeError(f"{field_name} must be a {expected_type.__name__}")


def _reject_raw_object(field_name: str, value: Any) -> None:
    if isinstance(value, (bytes, bytearray, memoryview)):
        raise TypeError(f"{field_name} must not contain bytes")
    if isinstance(value, (dict, set)):
        raise TypeError(f"{field_name} must not contain mutable collections")
    module_root = type(value).__module__.split(".", 1)[0]
    if module_root in RAW_OBJECT_MODULE_PREFIXES:
        raise TypeError(f"{field_name} must not contain dataframe or array objects")


def _normalize_text(value: str) -> str:
    return " ".join(value.strip().lower().split())


__all__ = [
    "DuplicateIdeaReport",
    "RejectedIdeaMemoryRecord",
    "RejectedIdeaMemoryStatus",
    "ResearchMemoryRecord",
    "ResearchMemoryStatus",
    "detect_duplicate_idea",
    "ensure_rejected_ideas_visible",
    "idea_fingerprint",
    "idea_key",
    "prior_rejection_reasons",
]
