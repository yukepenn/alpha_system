"""SQLite-backed persistence for validated governance records."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType
from typing import Any, cast

from alpha_system.core.registry import connect_registry, init_registry, resolve_registry_path
from alpha_system.governance.alpha_spec import AlphaSpec, validate_alpha_spec
from alpha_system.governance.canaries.negative_control_result import (
    NegativeControlResult,
    validate_negative_control_result,
)
from alpha_system.governance.evidence_bundle import EvidenceBundle, validate_evidence_bundle
from alpha_system.governance.feature_request import (
    FeatureRequest,
    validate_feature_request,
)
from alpha_system.governance.hypothesis_card import (
    HypothesisCard,
    validate_hypothesis_card,
)
from alpha_system.governance.ids import (
    GovernanceIdError,
    GovernanceIdKind,
    parse_governance_id,
    resolve_governance_id_kind,
    validate_governance_id,
)
from alpha_system.governance.label_spec import LabelSpec, validate_label_spec
from alpha_system.governance.promotion import (
    PROHIBITED_MVP_STATES,
    PromotionDecision,
    PromotionLifecycleState,
    validate_promotion_decision,
)
from alpha_system.governance.promotion_gate import (
    PromotionGateContext,
    validate_governance_transition,
)
from alpha_system.governance.rejected_idea import (
    RejectedIdeaRecord,
    validate_rejected_idea_record,
)
from alpha_system.governance.reviewer_verdict import (
    ReviewerVerdict,
    validate_reviewer_verdict,
)
from alpha_system.governance.serialization import (
    GovernanceSerializationError,
    canonical_serialize,
    content_hash,
    deserialize,
)
from alpha_system.governance.study_spec import StudySpec, validate_study_spec
from alpha_system.governance.trial_ledger import (
    TrialLedgerRecord,
    validate_trial_ledger_record,
)
from alpha_system.governance.validation import (
    GovernanceValidationError,
    ValidationIssue,
    require_mapping,
)

GOVERNANCE_OBJECT_TABLE = "governance_objects"
GOVERNANCE_LIFECYCLE_TABLE = "governance_lifecycle_states"

_SCHEMA_SQL = f"""
CREATE TABLE IF NOT EXISTS {GOVERNANCE_OBJECT_TABLE} (
    object_id TEXT PRIMARY KEY,
    object_kind TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS {GOVERNANCE_LIFECYCLE_TABLE} (
    object_id TEXT NOT NULL,
    object_kind TEXT NOT NULL,
    lifecycle_state TEXT NOT NULL,
    status_message TEXT NOT NULL DEFAULT '',
    recorded_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY (object_id, lifecycle_state),
    FOREIGN KEY (object_id) REFERENCES {GOVERNANCE_OBJECT_TABLE}(object_id)
);

CREATE INDEX IF NOT EXISTS idx_governance_objects_kind
    ON {GOVERNANCE_OBJECT_TABLE} (object_kind);

CREATE INDEX IF NOT EXISTS idx_governance_lifecycle_state
    ON {GOVERNANCE_LIFECYCLE_TABLE} (lifecycle_state, object_kind);
"""

type GovernanceObject = (
    HypothesisCard
    | AlphaSpec
    | FeatureRequest
    | LabelSpec
    | StudySpec
    | TrialLedgerRecord
    | EvidenceBundle
    | RejectedIdeaRecord
    | PromotionDecision
    | ReviewerVerdict
    | NegativeControlResult
)

_GOVERNANCE_OBJECT_TYPES = (
    HypothesisCard,
    AlphaSpec,
    FeatureRequest,
    LabelSpec,
    StudySpec,
    TrialLedgerRecord,
    EvidenceBundle,
    RejectedIdeaRecord,
    PromotionDecision,
    ReviewerVerdict,
    NegativeControlResult,
)


@dataclass(frozen=True, slots=True)
class GovernanceRegistryEntry:
    """Validated object loaded from the local governance registry."""

    object_id: str
    object_kind: str
    lifecycle_states: tuple[str, ...]
    payload: GovernanceObject
    payload_json: str
    content_hash: str

    @property
    def latest_lifecycle_state(self) -> str:
        """Return the most recent lifecycle state recorded for this object."""

        return self.lifecycle_states[-1]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible registry summary."""

        return {
            "object_id": self.object_id,
            "object_kind": self.object_kind,
            "lifecycle_states": list(self.lifecycle_states),
            "latest_lifecycle_state": self.latest_lifecycle_state,
            "payload": self.payload.to_dict(),
            "content_hash": self.content_hash,
        }


@dataclass(frozen=True, slots=True)
class _GovernanceObjectAdapter:
    kind: GovernanceIdKind
    id_attribute: str
    validate: Callable[[Mapping[str, Any]], GovernanceObject]
    allowed_lifecycle_states: frozenset[str]


_ADAPTERS: Mapping[str, _GovernanceObjectAdapter] = MappingProxyType(
    {
        GovernanceIdKind.HYPOTHESIS_CARD.value: _GovernanceObjectAdapter(
            kind=GovernanceIdKind.HYPOTHESIS_CARD,
            id_attribute="hypothesis_id",
            validate=validate_hypothesis_card,
            allowed_lifecycle_states=frozenset({"DRAFT", "REGISTERED", "REJECTED"}),
        ),
        GovernanceIdKind.ALPHA_SPEC.value: _GovernanceObjectAdapter(
            kind=GovernanceIdKind.ALPHA_SPEC,
            id_attribute="alpha_spec_id",
            validate=validate_alpha_spec,
            allowed_lifecycle_states=frozenset(
                {"REGISTERED", "IMPLEMENTATION_ALLOWED", "REJECTED"}
            ),
        ),
        GovernanceIdKind.FEATURE_REQUEST.value: _GovernanceObjectAdapter(
            kind=GovernanceIdKind.FEATURE_REQUEST,
            id_attribute="feature_request_id",
            validate=validate_feature_request,
            allowed_lifecycle_states=frozenset({"IMPLEMENTATION_ALLOWED", "REJECTED"}),
        ),
        GovernanceIdKind.LABEL_SPEC.value: _GovernanceObjectAdapter(
            kind=GovernanceIdKind.LABEL_SPEC,
            id_attribute="label_spec_id",
            validate=validate_label_spec,
            allowed_lifecycle_states=frozenset({"IMPLEMENTED", "DIAGNOSTICS_ALLOWED"}),
        ),
        GovernanceIdKind.STUDY_SPEC.value: _GovernanceObjectAdapter(
            kind=GovernanceIdKind.STUDY_SPEC,
            id_attribute="study_spec_id",
            validate=validate_study_spec,
            allowed_lifecycle_states=frozenset({"DIAGNOSTICS_ALLOWED", "REJECTED"}),
        ),
        GovernanceIdKind.TRIAL_LEDGER_RECORD.value: _GovernanceObjectAdapter(
            kind=GovernanceIdKind.TRIAL_LEDGER_RECORD,
            id_attribute="trial_id",
            validate=validate_trial_ledger_record,
            allowed_lifecycle_states=frozenset({"DIAGNOSTICS_RUN", "REJECTED"}),
        ),
        GovernanceIdKind.EVIDENCE_BUNDLE.value: _GovernanceObjectAdapter(
            kind=GovernanceIdKind.EVIDENCE_BUNDLE,
            id_attribute="evidence_bundle_id",
            validate=validate_evidence_bundle,
            allowed_lifecycle_states=frozenset({"EVIDENCE_READY", "REJECTED"}),
        ),
        GovernanceIdKind.REJECTED_IDEA_RECORD.value: _GovernanceObjectAdapter(
            kind=GovernanceIdKind.REJECTED_IDEA_RECORD,
            id_attribute="rejected_id",
            validate=validate_rejected_idea_record,
            allowed_lifecycle_states=frozenset({"REJECTED"}),
        ),
        GovernanceIdKind.PROMOTION_DECISION.value: _GovernanceObjectAdapter(
            kind=GovernanceIdKind.PROMOTION_DECISION,
            id_attribute="promotion_id",
            validate=validate_promotion_decision,
            allowed_lifecycle_states=frozenset({"REJECTED", "WATCH", "CANDIDATE", "VALIDATED"}),
        ),
        GovernanceIdKind.REVIEWER_VERDICT.value: _GovernanceObjectAdapter(
            kind=GovernanceIdKind.REVIEWER_VERDICT,
            id_attribute="reviewer_verdict_id",
            validate=validate_reviewer_verdict,
            allowed_lifecycle_states=frozenset({"REVIEWED"}),
        ),
        GovernanceIdKind.NEGATIVE_CONTROL_RESULT.value: _GovernanceObjectAdapter(
            kind=GovernanceIdKind.NEGATIVE_CONTROL_RESULT,
            id_attribute="canary_id",
            validate=validate_negative_control_result,
            allowed_lifecycle_states=frozenset({"DIAGNOSTICS_RUN", "EVIDENCE_READY"}),
        ),
    }
)


class GovernanceRegistry:
    """Local SQLite registry for immutable governance object persistence."""

    def __init__(self, registry_path: str | Path, *, initialize: bool = True) -> None:
        self.registry_path = resolve_registry_path(registry_path)
        if initialize:
            init_governance_registry(self.registry_path)

    def save(
        self,
        record: GovernanceObject | Mapping[str, Any],
        lifecycle_state: PromotionLifecycleState | str,
        *,
        object_kind: GovernanceIdKind | str | None = None,
        gate_context: PromotionGateContext | None = None,
        status_message: str = "",
    ) -> GovernanceRegistryEntry:
        """Validate and persist one governance object under a lifecycle state.

        `ReviewerVerdict` and `PromotionDecision` writes require a
        `PromotionGateContext`; the registry calls the existing promotion gate
        before writing them so persistence cannot become self-approval or
        force-promotion machinery.
        """

        kind = _resolve_record_kind(record, object_kind=object_kind)
        adapter = _adapter_for_kind(kind)
        validated = _validate_record(record, adapter)
        object_id = _object_id(validated, adapter)
        lifecycle_value = _validate_lifecycle_state(lifecycle_state)
        _validate_lifecycle_state_allowed(adapter, lifecycle_value)
        _validate_gate_write(adapter, validated, lifecycle_value, gate_context)
        payload = validated.to_dict()
        payload_json = canonical_serialize(payload)
        digest = content_hash(payload)

        with connect_registry(self.registry_path) as connection:
            ensure_governance_registry_schema(connection)
            _insert_immutable_object(
                connection,
                object_id=object_id,
                object_kind=adapter.kind.value,
                payload_json=payload_json,
                digest=digest,
            )
            _insert_lifecycle_state(
                connection,
                object_id=object_id,
                object_kind=adapter.kind.value,
                lifecycle_state=lifecycle_value,
                status_message=status_message,
            )
            connection.commit()

        return self.get(object_id, object_kind=adapter.kind)

    def put(
        self,
        record: GovernanceObject | Mapping[str, Any],
        lifecycle_state: PromotionLifecycleState | str,
        *,
        object_kind: GovernanceIdKind | str | None = None,
        gate_context: PromotionGateContext | None = None,
        status_message: str = "",
    ) -> GovernanceRegistryEntry:
        """Alias for `save`."""

        return self.save(
            record,
            lifecycle_state,
            object_kind=object_kind,
            gate_context=gate_context,
            status_message=status_message,
        )

    def get(
        self,
        object_id: str,
        *,
        object_kind: GovernanceIdKind | str | None = None,
    ) -> GovernanceRegistryEntry:
        """Retrieve and validate a registry entry by typed governance ID."""

        expected_kind = _coerce_kind(object_kind) if object_kind is not None else None
        if expected_kind is None:
            expected_kind = _kind_from_id(object_id)
        else:
            _validate_object_id_kind(object_id, expected_kind)

        try:
            with connect_registry(self.registry_path, read_only=True) as connection:
                row = connection.execute(
                    f"""
                    SELECT object_id, object_kind, payload_json, content_hash
                    FROM {GOVERNANCE_OBJECT_TABLE}
                    WHERE object_id = ?
                    """,
                    (object_id,),
                ).fetchone()
                if row is None:
                    _raise_issue(
                        "object_id",
                        "governance_record_not_found",
                        "governance registry record was not found",
                        expected="persisted governance object",
                        actual=object_id,
                    )
                states = _read_lifecycle_states(connection, object_id)
        except sqlite3.Error as exc:
            _raise_issue(
                "registry_path",
                "governance_registry_read_failed",
                "governance registry could not be read",
                expected="readable initialized governance registry",
                actual=str(exc),
            )

        assert row is not None
        return _entry_from_row(row, states, expected_kind=expected_kind)

    def get_object(
        self,
        object_id: str,
        *,
        object_kind: GovernanceIdKind | str | None = None,
    ) -> GovernanceObject:
        """Retrieve a validated governance object by typed ID."""

        return self.get(object_id, object_kind=object_kind).payload

    def list_by_lifecycle_state(
        self,
        lifecycle_state: PromotionLifecycleState | str,
        *,
        object_kind: GovernanceIdKind | str | None = None,
    ) -> tuple[GovernanceRegistryEntry, ...]:
        """Return validated entries associated with a lifecycle state."""

        lifecycle_value = _validate_lifecycle_state(lifecycle_state)
        expected_kind = _coerce_kind(object_kind) if object_kind is not None else None
        where = "WHERE s.lifecycle_state = ?"
        parameters: list[str] = [lifecycle_value]
        if expected_kind is not None:
            where += " AND o.object_kind = ?"
            parameters.append(expected_kind.value)

        try:
            with connect_registry(self.registry_path, read_only=True) as connection:
                rows = connection.execute(
                    f"""
                    SELECT
                        o.object_id,
                        o.object_kind,
                        o.payload_json,
                        o.content_hash
                    FROM {GOVERNANCE_OBJECT_TABLE} o
                    JOIN {GOVERNANCE_LIFECYCLE_TABLE} s
                      ON s.object_id = o.object_id
                    {where}
                    ORDER BY s.recorded_at, o.object_id
                    """,
                    parameters,
                ).fetchall()
                return tuple(
                    _entry_from_row(
                        row,
                        (lifecycle_value,),
                        expected_kind=expected_kind,
                    )
                    for row in rows
                )
        except sqlite3.Error as exc:
            _raise_issue(
                "registry_path",
                "governance_registry_read_failed",
                "governance registry could not be read",
                expected="readable initialized governance registry",
                actual=str(exc),
            )

    def list_by_state(
        self,
        lifecycle_state: PromotionLifecycleState | str,
        *,
        object_kind: GovernanceIdKind | str | None = None,
    ) -> tuple[GovernanceRegistryEntry, ...]:
        """Alias for `list_by_lifecycle_state`."""

        return self.list_by_lifecycle_state(lifecycle_state, object_kind=object_kind)


def init_governance_registry(registry_path: str | Path) -> Path:
    """Initialize the existing local registry and governance object schema."""

    resolved = resolve_registry_path(registry_path)
    status = init_registry(resolved)
    if not status.valid:
        _raise_issue(
            "registry_path",
            "invalid_base_registry",
            "base metadata registry is not valid",
            expected="valid local metadata registry",
            actual=status.status_message,
        )
    with connect_registry(resolved) as connection:
        ensure_governance_registry_schema(connection)
        connection.commit()
    return resolved


def ensure_governance_registry_schema(connection: sqlite3.Connection) -> None:
    """Create schema-only governance registry tables on an open connection."""

    connection.executescript(_SCHEMA_SQL)


def _insert_immutable_object(
    connection: sqlite3.Connection,
    *,
    object_id: str,
    object_kind: str,
    payload_json: str,
    digest: str,
) -> None:
    existing = connection.execute(
        f"""
        SELECT object_kind, payload_json, content_hash
        FROM {GOVERNANCE_OBJECT_TABLE}
        WHERE object_id = ?
        """,
        (object_id,),
    ).fetchone()
    if existing is not None:
        if (
            existing["object_kind"] == object_kind
            and existing["payload_json"] == payload_json
            and existing["content_hash"] == digest
        ):
            return
        _raise_issue(
            "object_id",
            "governance_record_rewrite_blocked",
            "governance registry records are immutable and cannot be overwritten",
            expected="same object kind and content hash",
            actual=object_id,
        )
    connection.execute(
        f"""
        INSERT INTO {GOVERNANCE_OBJECT_TABLE} (
            object_id, object_kind, payload_json, content_hash
        )
        VALUES (?, ?, ?, ?)
        """,
        (object_id, object_kind, payload_json, digest),
    )


def _insert_lifecycle_state(
    connection: sqlite3.Connection,
    *,
    object_id: str,
    object_kind: str,
    lifecycle_state: str,
    status_message: str,
) -> None:
    connection.execute(
        f"""
        INSERT OR IGNORE INTO {GOVERNANCE_LIFECYCLE_TABLE} (
            object_id, object_kind, lifecycle_state, status_message
        )
        VALUES (?, ?, ?, ?)
        """,
        (object_id, object_kind, lifecycle_state, str(status_message)),
    )


def _read_lifecycle_states(
    connection: sqlite3.Connection,
    object_id: str,
) -> tuple[str, ...]:
    rows = connection.execute(
        f"""
        SELECT lifecycle_state
        FROM {GOVERNANCE_LIFECYCLE_TABLE}
        WHERE object_id = ?
        ORDER BY recorded_at, lifecycle_state
        """,
        (object_id,),
    ).fetchall()
    if not rows:
        _raise_issue(
            "lifecycle_state",
            "missing_lifecycle_state",
            "governance registry record has no lifecycle state",
            expected="one or more recorded lifecycle states",
            actual=object_id,
        )
    return tuple(str(row["lifecycle_state"]) for row in rows)


def _entry_from_row(
    row: sqlite3.Row,
    lifecycle_states: Sequence[str],
    *,
    expected_kind: GovernanceIdKind | None,
) -> GovernanceRegistryEntry:
    object_id = str(row["object_id"])
    row_kind = _coerce_kind(str(row["object_kind"]))
    if expected_kind is not None and row_kind is not expected_kind:
        _raise_issue(
            "object_kind",
            "object_kind_mismatch",
            "governance registry row kind does not match requested kind",
            expected=expected_kind.value,
            actual=row_kind.value,
        )
    _validate_object_id_kind(object_id, row_kind)
    adapter = _adapter_for_kind(row_kind)
    validated_states = tuple(_validate_lifecycle_state(state) for state in lifecycle_states)
    for state in validated_states:
        _validate_lifecycle_state_allowed(adapter, state)

    payload_text = str(row["payload_json"])
    try:
        payload_value = deserialize(payload_text)
        payload_mapping = require_mapping(
            payload_value,
            object_name=f"{adapter.kind.value} registry payload",
        )
    except (GovernanceSerializationError, GovernanceValidationError) as exc:
        _raise_issue(
            "payload_json",
            "malformed_governance_registry_payload",
            "governance registry payload could not be deserialized as a valid mapping",
            expected="canonical JSON mapping",
            actual=str(exc),
        )

    payload = _validate_record(cast(Mapping[str, Any], payload_mapping), adapter)
    payload_id = _object_id(payload, adapter)
    if payload_id != object_id:
        _raise_issue(
            "object_id",
            "governance_registry_id_mismatch",
            "governance registry object ID does not match the validated payload",
            expected=payload_id,
            actual=object_id,
        )

    digest = content_hash(payload.to_dict())
    stored_digest = str(row["content_hash"])
    if stored_digest != digest:
        _raise_issue(
            "content_hash",
            "governance_registry_content_hash_mismatch",
            "governance registry content hash does not match the validated payload",
            expected=digest,
            actual=stored_digest,
        )

    return GovernanceRegistryEntry(
        object_id=object_id,
        object_kind=adapter.kind.value,
        lifecycle_states=validated_states,
        payload=payload,
        payload_json=payload_text,
        content_hash=digest,
    )


def _resolve_record_kind(
    record: GovernanceObject | Mapping[str, Any],
    *,
    object_kind: GovernanceIdKind | str | None,
) -> GovernanceIdKind:
    if object_kind is not None:
        return _coerce_kind(object_kind)
    for object_type in _GOVERNANCE_OBJECT_TYPES:
        if isinstance(record, object_type):
            return _kind_for_type(object_type)
    if isinstance(record, Mapping):
        return _infer_kind_from_mapping(record)
    _raise_issue(
        "record",
        "invalid_governance_record_type",
        "governance registry writes require a governance record or mapping",
        expected="governance object or mapping",
        actual=type(record).__name__,
    )


def _infer_kind_from_mapping(record: Mapping[str, Any]) -> GovernanceIdKind:
    matches: list[GovernanceIdKind] = []
    for adapter in _ADAPTERS.values():
        if adapter.id_attribute in record:
            matches.append(adapter.kind)
    if len(matches) == 1:
        return matches[0]
    _raise_issue(
        "object_kind",
        "object_kind_required",
        "object_kind is required when a mapping does not expose one unambiguous ID field",
        expected="canonical governance object kind",
        actual=", ".join(kind.value for kind in matches) if matches else "missing",
    )


def _kind_for_type(object_type: type[GovernanceObject]) -> GovernanceIdKind:
    type_map: Mapping[type[GovernanceObject], GovernanceIdKind] = MappingProxyType(
        {
            HypothesisCard: GovernanceIdKind.HYPOTHESIS_CARD,
            AlphaSpec: GovernanceIdKind.ALPHA_SPEC,
            FeatureRequest: GovernanceIdKind.FEATURE_REQUEST,
            LabelSpec: GovernanceIdKind.LABEL_SPEC,
            StudySpec: GovernanceIdKind.STUDY_SPEC,
            TrialLedgerRecord: GovernanceIdKind.TRIAL_LEDGER_RECORD,
            EvidenceBundle: GovernanceIdKind.EVIDENCE_BUNDLE,
            RejectedIdeaRecord: GovernanceIdKind.REJECTED_IDEA_RECORD,
            PromotionDecision: GovernanceIdKind.PROMOTION_DECISION,
            ReviewerVerdict: GovernanceIdKind.REVIEWER_VERDICT,
            NegativeControlResult: GovernanceIdKind.NEGATIVE_CONTROL_RESULT,
        }
    )
    return type_map[object_type]


def _validate_record(
    record: GovernanceObject | Mapping[str, Any],
    adapter: _GovernanceObjectAdapter,
) -> GovernanceObject:
    if isinstance(record, _GOVERNANCE_OBJECT_TYPES):
        payload = record.to_dict()
    elif isinstance(record, Mapping):
        payload = record
    else:
        _raise_issue(
            "record",
            "invalid_governance_record_type",
            "governance registry writes require a governance record or mapping",
            expected="governance object or mapping",
            actual=type(record).__name__,
        )
    return adapter.validate(payload)


def _object_id(record: GovernanceObject, adapter: _GovernanceObjectAdapter) -> str:
    value = getattr(record, adapter.id_attribute)
    if not isinstance(value, str):
        _raise_issue(
            adapter.id_attribute,
            "invalid_governance_object_id",
            "validated governance object did not expose a string ID",
            expected="string governance ID",
            actual=type(value).__name__,
        )
    _validate_object_id_kind(value, adapter.kind)
    return value


def _validate_gate_write(
    adapter: _GovernanceObjectAdapter,
    record: GovernanceObject,
    lifecycle_state: str,
    gate_context: PromotionGateContext | None,
) -> None:
    if adapter.kind is GovernanceIdKind.REVIEWER_VERDICT:
        context = _require_gate_context(adapter.kind, gate_context)
        verdict = cast(ReviewerVerdict, record)
        transition = validate_governance_transition(
            "EVIDENCE_READY",
            "REVIEWED",
            replace(context, reviewer_verdict=verdict),
        )
        if transition.reviewer_verdict_id != verdict.reviewer_verdict_id:
            _raise_issue(
                "reviewer_verdict_id",
                "reviewer_verdict_transition_mismatch",
                "reviewed transition did not reference the persisted ReviewerVerdict",
                expected=verdict.reviewer_verdict_id,
                actual=transition.reviewer_verdict_id,
            )
        return

    if adapter.kind is GovernanceIdKind.PROMOTION_DECISION:
        context = _require_gate_context(adapter.kind, gate_context)
        decision = cast(PromotionDecision, record)
        if lifecycle_state != decision.next_state.value:
            _raise_issue(
                "lifecycle_state",
                "promotion_decision_state_mismatch",
                "PromotionDecision lifecycle_state must match decision.next_state",
                expected=decision.next_state.value,
                actual=lifecycle_state,
            )
        validate_governance_transition(
            "REVIEWED",
            decision.next_state,
            replace(context, promotion_decision=decision),
        )


def _require_gate_context(
    kind: GovernanceIdKind,
    gate_context: PromotionGateContext | None,
) -> PromotionGateContext:
    if isinstance(gate_context, PromotionGateContext):
        return gate_context
    _raise_issue(
        "gate_context",
        "gate_context_required",
        f"{kind.value} registry writes require PromotionGateContext validation",
        expected="PromotionGateContext",
        actual=type(gate_context).__name__,
    )


def _validate_lifecycle_state(value: PromotionLifecycleState | str) -> str:
    if isinstance(value, PromotionLifecycleState):
        return value.value
    if not isinstance(value, str):
        _raise_issue(
            "lifecycle_state",
            "invalid_lifecycle_state_type",
            "lifecycle_state must be a governance lifecycle state string",
            expected="string lifecycle state",
            actual=type(value).__name__,
        )
    if value in PROHIBITED_MVP_STATES:
        _raise_issue(
            "lifecycle_state",
            "prohibited_mvp_state",
            "prohibited MVP state is not reachable in this governance registry",
            expected="reachable MVP lifecycle state",
            actual=value,
        )
    try:
        return PromotionLifecycleState(value).value
    except ValueError:
        _raise_issue(
            "lifecycle_state",
            "invalid_lifecycle_state",
            "lifecycle_state is not declared in the MVP governance state machine",
            expected=" | ".join(state.value for state in PromotionLifecycleState),
            actual=value,
        )


def _validate_lifecycle_state_allowed(
    adapter: _GovernanceObjectAdapter,
    lifecycle_state: str,
) -> None:
    if lifecycle_state in adapter.allowed_lifecycle_states:
        return
    _raise_issue(
        "lifecycle_state",
        "lifecycle_state_not_allowed_for_object",
        f"{adapter.kind.value} cannot be persisted under this lifecycle state",
        expected=" | ".join(sorted(adapter.allowed_lifecycle_states)),
        actual=lifecycle_state,
    )


def _adapter_for_kind(kind: GovernanceIdKind) -> _GovernanceObjectAdapter:
    adapter = _ADAPTERS.get(kind.value)
    if adapter is None:
        _raise_issue(
            "object_kind",
            "unsupported_governance_object_kind",
            "governance registry does not persist this object kind",
            expected="supported governance object kind",
            actual=kind.value,
        )
    return adapter


def _coerce_kind(value: GovernanceIdKind | str | None) -> GovernanceIdKind:
    if value is None:
        _raise_issue(
            "object_kind",
            "object_kind_required",
            "object_kind is required",
            expected="canonical governance object kind",
            actual="missing",
        )
    try:
        return resolve_governance_id_kind(value)
    except GovernanceIdError as exc:
        _raise_issue(
            "object_kind",
            exc.issue.code,
            exc.issue.message,
            expected="canonical governance object kind",
            actual=str(exc.issue.value),
        )


def _kind_from_id(object_id: str) -> GovernanceIdKind:
    try:
        return parse_governance_id(object_id).kind
    except GovernanceIdError as exc:
        _raise_issue(
            "object_id",
            exc.issue.code,
            exc.issue.message,
            expected="typed governance ID",
            actual=str(exc.issue.value),
        )


def _validate_object_id_kind(object_id: str, expected_kind: GovernanceIdKind) -> None:
    try:
        validate_governance_id(object_id, expected_kind=expected_kind)
    except GovernanceIdError as exc:
        _raise_issue(
            "object_id",
            exc.issue.code,
            exc.issue.message,
            expected=expected_kind.value,
            actual=str(exc.issue.value),
        )


def _raise_issue(
    field: str,
    code: str,
    message: str,
    *,
    expected: str = "",
    actual: str = "",
) -> None:
    raise GovernanceValidationError(
        ValidationIssue(
            field=field,
            code=code,
            message=message,
            expected=expected,
            actual=actual,
        )
    )


__all__ = [
    "GOVERNANCE_LIFECYCLE_TABLE",
    "GOVERNANCE_OBJECT_TABLE",
    "GovernanceRegistry",
    "GovernanceRegistryEntry",
    "ensure_governance_registry_schema",
    "init_governance_registry",
]
