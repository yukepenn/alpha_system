"""Deterministic typed IDs for governance records."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Any

from alpha_system.governance.serialization import (
    GovernanceSerializationError,
    canonical_serialize,
)

TOKEN_LENGTH = 24
GOVERNANCE_ID_PATTERN = re.compile(
    rf"^(?P<prefix>[a-z][a-z0-9]*)_(?P<token>[a-f0-9]{{{TOKEN_LENGTH}}})$"
)


class GovernanceIdKind(StrEnum):
    """Governance ID kinds fixed by the naming contract."""

    HYPOTHESIS_CARD = "HypothesisCard"
    ALPHA_SPEC = "AlphaSpec"
    FEATURE_REQUEST = "FeatureRequest"
    LABEL_SPEC = "LabelSpec"
    STUDY_SPEC = "StudySpec"
    TRIAL_LEDGER_RECORD = "TrialLedgerRecord"
    EVIDENCE_BUNDLE = "EvidenceBundle"
    REJECTED_IDEA_RECORD = "RejectedIdeaRecord"
    PROMOTION_DECISION = "PromotionDecision"
    REVIEWER_VERDICT = "ReviewerVerdict"
    NEGATIVE_CONTROL_RESULT = "NegativeControlResult"
    ALPHA_BOOK_RECORD = "AlphaBookRecord"
    BUDGET_AMENDMENT_RECORD = "BudgetAmendmentRecord"
    SEALED_HOLDOUT_WINDOW = "SealedHoldoutWindow"
    HOLDOUT_ACCESS_LOG = "HoldoutAccessLog"
    SURROGATE_STUDY_RUN = "SurrogateStudyRun"
    POOLED_HYPOTHESIS_RECORD = "PooledHypothesisRecord"


GOVERNANCE_ID_PREFIXES = MappingProxyType(
    {
        GovernanceIdKind.HYPOTHESIS_CARD.value: "hyp",
        GovernanceIdKind.ALPHA_SPEC.value: "aspec",
        GovernanceIdKind.FEATURE_REQUEST.value: "freq",
        GovernanceIdKind.LABEL_SPEC.value: "lspec",
        GovernanceIdKind.STUDY_SPEC.value: "sspec",
        GovernanceIdKind.TRIAL_LEDGER_RECORD.value: "trial",
        GovernanceIdKind.EVIDENCE_BUNDLE.value: "evb",
        GovernanceIdKind.REJECTED_IDEA_RECORD.value: "rej",
        GovernanceIdKind.PROMOTION_DECISION.value: "prom",
        GovernanceIdKind.REVIEWER_VERDICT.value: "rver",
        GovernanceIdKind.NEGATIVE_CONTROL_RESULT.value: "nctrl",
        GovernanceIdKind.ALPHA_BOOK_RECORD.value: "abook",
        GovernanceIdKind.BUDGET_AMENDMENT_RECORD.value: "bamend",
        GovernanceIdKind.SEALED_HOLDOUT_WINDOW.value: "holdwin",
        GovernanceIdKind.HOLDOUT_ACCESS_LOG.value: "haccess",
        GovernanceIdKind.SURROGATE_STUDY_RUN.value: "surrun",
        GovernanceIdKind.POOLED_HYPOTHESIS_RECORD.value: "poolhyp",
    }
)
GOVERNANCE_ID_OBJECTS_BY_PREFIX = MappingProxyType(
    {prefix: object_name for object_name, prefix in GOVERNANCE_ID_PREFIXES.items()}
)


@dataclass(frozen=True, slots=True)
class GovernanceIdIssue:
    """Structured reason a governance ID failed validation."""

    code: str
    message: str
    value: object | None = None

    def to_dict(self) -> dict[str, object | None]:
        return {
            "code": self.code,
            "message": self.message,
            "value": self.value,
        }


class GovernanceIdError(ValueError):
    """Raised when governance ID generation or parsing fails closed."""

    def __init__(self, issue: GovernanceIdIssue):
        self.issue = issue
        super().__init__(issue.message)

    def to_dict(self) -> dict[str, object | None]:
        return self.issue.to_dict()


@dataclass(frozen=True, slots=True)
class GovernanceId:
    """Parsed governance ID components."""

    value: str
    kind: GovernanceIdKind
    object_name: str
    prefix: str
    token: str


def generate_governance_id(kind: GovernanceIdKind | str, components: Mapping[str, Any]) -> str:
    """Generate a deterministic governance ID from explicit typed components."""

    resolved_kind = resolve_governance_id_kind(kind)
    if not isinstance(components, Mapping):
        raise GovernanceIdError(
            GovernanceIdIssue(
                code="invalid_components",
                message="governance ID components must be a mapping",
                value=type(components).__name__,
            )
        )
    prefix = prefix_for_kind(resolved_kind)
    payload = {
        "components": components,
        "kind": resolved_kind.value,
        "prefix": prefix,
    }
    try:
        token = hashlib.sha256(canonical_serialize(payload).encode("utf-8")).hexdigest()[
            :TOKEN_LENGTH
        ]
    except GovernanceSerializationError as exc:
        raise GovernanceIdError(
            GovernanceIdIssue(
                code="invalid_components",
                message=f"governance ID components are not canonically serializable: {exc}",
                value=resolved_kind.value,
            )
        ) from exc
    return f"{prefix}_{token}"


def parse_governance_id(
    value: str,
    *,
    expected_kind: GovernanceIdKind | str | None = None,
    expected_prefix: str | None = None,
) -> GovernanceId:
    """Parse a governance ID and reject malformed, unknown, or wrong-prefix values."""

    if not isinstance(value, str):
        raise GovernanceIdError(
            GovernanceIdIssue(
                code="invalid_id_type",
                message="governance ID must be a string",
                value=type(value).__name__,
            )
        )
    match = GOVERNANCE_ID_PATTERN.fullmatch(value)
    if match is None:
        raise GovernanceIdError(
            GovernanceIdIssue(
                code="malformed_id",
                message=f"governance ID must match '<prefix>_<{TOKEN_LENGTH}-hex-token>'",
                value=value,
            )
        )
    prefix = match.group("prefix")
    token = match.group("token")
    object_name = GOVERNANCE_ID_OBJECTS_BY_PREFIX.get(prefix)
    if object_name is None:
        raise GovernanceIdError(
            GovernanceIdIssue(
                code="unknown_prefix",
                message=f"unknown governance ID prefix: {prefix}",
                value=value,
            )
        )

    if expected_prefix is not None:
        _validate_expected_prefix(expected_prefix)
        if prefix != expected_prefix:
            raise GovernanceIdError(
                GovernanceIdIssue(
                    code="unexpected_prefix",
                    message=f"expected governance ID prefix {expected_prefix!r}, got {prefix!r}",
                    value=value,
                )
            )

    kind = resolve_governance_id_kind(object_name)
    if expected_kind is not None:
        resolved_expected_kind = resolve_governance_id_kind(expected_kind)
        expected_kind_prefix = prefix_for_kind(resolved_expected_kind)
        if expected_prefix is not None and expected_prefix != expected_kind_prefix:
            raise GovernanceIdError(
                GovernanceIdIssue(
                    code="inconsistent_expected_prefix",
                    message=(
                        f"expected prefix {expected_prefix!r} does not match "
                        f"{resolved_expected_kind.value} prefix {expected_kind_prefix!r}"
                    ),
                    value=value,
                )
            )
        if kind != resolved_expected_kind:
            raise GovernanceIdError(
                GovernanceIdIssue(
                    code="unexpected_kind",
                    message=(
                        f"expected governance ID kind {resolved_expected_kind.value}, "
                        f"got {kind.value}"
                    ),
                    value=value,
                )
            )

    return GovernanceId(
        value=value,
        kind=kind,
        object_name=object_name,
        prefix=prefix,
        token=token,
    )


def validate_governance_id(
    value: str,
    *,
    expected_kind: GovernanceIdKind | str | None = None,
    expected_prefix: str | None = None,
) -> str:
    """Validate a governance ID and return the original ID unchanged."""

    parse_governance_id(value, expected_kind=expected_kind, expected_prefix=expected_prefix)
    return value


def resolve_governance_id_kind(kind: GovernanceIdKind | str) -> GovernanceIdKind:
    """Resolve an exact canonical governance object name into an ID kind."""

    if isinstance(kind, GovernanceIdKind):
        return kind
    if isinstance(kind, str):
        try:
            return GovernanceIdKind(kind)
        except ValueError as exc:
            raise GovernanceIdError(
                GovernanceIdIssue(
                    code="unknown_kind",
                    message=f"unknown governance ID kind: {kind}",
                    value=kind,
                )
            ) from exc
    raise GovernanceIdError(
        GovernanceIdIssue(
            code="invalid_kind_type",
            message="governance ID kind must be a GovernanceIdKind or canonical object name",
            value=type(kind).__name__,
        )
    )


def prefix_for_kind(kind: GovernanceIdKind | str) -> str:
    """Return the canonical prefix for a governance ID kind."""

    resolved_kind = resolve_governance_id_kind(kind)
    return GOVERNANCE_ID_PREFIXES[resolved_kind.value]


def prefix_for_object(object_name: str) -> str:
    """Return the canonical prefix for an exact governance object name."""

    return prefix_for_kind(object_name)


def object_for_prefix(prefix: str) -> str:
    """Return the canonical governance object name for a known ID prefix."""

    _validate_expected_prefix(prefix)
    return GOVERNANCE_ID_OBJECTS_BY_PREFIX[prefix]


def _validate_expected_prefix(prefix: str) -> None:
    if not isinstance(prefix, str):
        raise GovernanceIdError(
            GovernanceIdIssue(
                code="invalid_prefix_type",
                message="expected governance ID prefix must be a string",
                value=type(prefix).__name__,
            )
        )
    if prefix not in GOVERNANCE_ID_OBJECTS_BY_PREFIX:
        raise GovernanceIdError(
            GovernanceIdIssue(
                code="unknown_prefix",
                message=f"unknown governance ID prefix: {prefix}",
                value=prefix,
            )
        )


__all__ = [
    "GOVERNANCE_ID_OBJECTS_BY_PREFIX",
    "GOVERNANCE_ID_PATTERN",
    "GOVERNANCE_ID_PREFIXES",
    "TOKEN_LENGTH",
    "GovernanceId",
    "GovernanceIdError",
    "GovernanceIdIssue",
    "GovernanceIdKind",
    "generate_governance_id",
    "object_for_prefix",
    "parse_governance_id",
    "prefix_for_kind",
    "prefix_for_object",
    "resolve_governance_id_kind",
    "validate_governance_id",
]
