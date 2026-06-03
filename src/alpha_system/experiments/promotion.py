"""Promotion-decision model with mandatory review traceability."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from alpha_system.core.hashing import canonical_json, hash_config


APPROVAL_STATUSES: frozenset[str] = frozenset(
    {"approved", "promoted", "pass", "pass_with_warnings"}
)
RECOMMENDATION_STATUSES: frozenset[str] = frozenset(
    {"recommended", "recommend", "recommend_review", "candidate_recommended"}
)
REVIEWED_STATUSES: frozenset[str] = frozenset(
    {"reviewed", "pass", "pass_with_warnings", "rejected", "blocked"}
)


class PromotionDecisionError(ValueError):
    """Raised when a promotion decision lacks a review trail."""


@dataclass(frozen=True, slots=True, kw_only=True)
class PromotionDecision:
    """Review-backed promotion decision metadata."""

    candidate_id: str
    source_run_id: str
    review_status: str
    decision_status: str
    rationale: str
    timestamp: datetime | str
    reviewer_identity: str = ""
    review_artifact_ref: str = ""
    artifact_references: Mapping[str, str] | None = None
    decision_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "candidate_id", _require_text(self.candidate_id, "candidate_id"))
        object.__setattr__(
            self,
            "source_run_id",
            _require_text(self.source_run_id, "source_run_id"),
        )
        object.__setattr__(
            self,
            "review_status",
            _require_text(self.review_status, "review_status").lower(),
        )
        object.__setattr__(
            self,
            "decision_status",
            _require_text(self.decision_status, "decision_status").lower(),
        )
        object.__setattr__(self, "rationale", _require_text(self.rationale, "rationale"))
        object.__setattr__(self, "timestamp", _timestamp_text(self.timestamp))
        object.__setattr__(
            self,
            "artifact_references",
            dict(sorted((self.artifact_references or {}).items())),
        )
        self.validate_review_trail()
        if self.decision_id is None:
            object.__setattr__(self, "decision_id", _decision_id(self))
        else:
            object.__setattr__(self, "decision_id", _require_text(self.decision_id, "decision_id"))

    def validate_review_trail(self) -> None:
        if self.review_status in RECOMMENDATION_STATUSES:
            raise PromotionDecisionError("recommendation review status is not approval")
        if self.decision_status in APPROVAL_STATUSES and self.review_status not in REVIEWED_STATUSES:
            raise PromotionDecisionError("approved promotion decisions require reviewed status")
        if not self.reviewer_identity.strip() and not self.review_artifact_ref.strip():
            raise PromotionDecisionError("reviewer_identity or review_artifact_ref is required")
        if self.reviewer_identity.strip() == self.candidate_id:
            raise PromotionDecisionError("candidate cannot self-approve promotion")

    @property
    def is_approval(self) -> bool:
        return self.decision_status in APPROVAL_STATUSES

    @property
    def is_recommendation(self) -> bool:
        return self.decision_status in RECOMMENDATION_STATUSES

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["artifact_references"] = dict(self.artifact_references or {})
        return payload


def _require_text(value: str, field_name: str) -> str:
    text = str(value).strip()
    if not text:
        raise PromotionDecisionError(f"{field_name} must be non-empty")
    return text


def _timestamp_text(value: datetime | str) -> str:
    if isinstance(value, str):
        return _require_text(value, "timestamp")
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _decision_id(decision: PromotionDecision) -> str:
    return hash_config(
        {
            "candidate_id": decision.candidate_id,
            "source_run_id": decision.source_run_id,
            "review_status": decision.review_status,
            "decision_status": decision.decision_status,
            "timestamp": decision.timestamp,
        }
    )[:24]


def insert_promotion_decision(
    connection: sqlite3.Connection,
    decision: PromotionDecision,
) -> str:
    """Insert a promotion decision using the existing registry table."""
    metadata = {
        "review_status": decision.review_status,
        "reviewer_identity": decision.reviewer_identity,
        "review_artifact_ref": decision.review_artifact_ref,
        "recommendation_is_approval": False,
        "review_backed": True,
    }
    connection.execute(
        """
        INSERT INTO promotion_decisions (
            decision_id,
            subject_type,
            subject_id,
            subject_version,
            run_id,
            decision_status,
            decided_at,
            reviewer,
            rationale,
            artifact_paths_json,
            metadata_json,
            status_message
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            decision.decision_id,
            "candidate",
            decision.candidate_id,
            "",
            decision.source_run_id,
            decision.decision_status,
            decision.timestamp,
            decision.reviewer_identity,
            decision.rationale,
            canonical_json(decision.artifact_references or {}),
            canonical_json(metadata),
            "review-backed promotion decision",
        ),
    )
    return str(decision.decision_id)


def decision_status_is_approval(status: str) -> bool:
    return str(status).strip().lower() in APPROVAL_STATUSES


def decision_status_is_recommendation(status: str) -> bool:
    return str(status).strip().lower() in RECOMMENDATION_STATUSES


def promotion_row_has_review_trail(row: sqlite3.Row) -> bool:
    """Return whether a registry promotion row has explicit review metadata."""
    metadata = _loads_dict(row["metadata_json"])
    artifact_paths = _loads_dict(row["artifact_paths_json"])
    reviewer = str(row["reviewer"] or metadata.get("reviewer_identity", "")).strip()
    review_status = str(metadata.get("review_status", "")).strip().lower()
    review_artifact = str(metadata.get("review_artifact_ref", "")).strip()
    rationale = str(row["rationale"] or "").strip()
    review_backed = metadata.get("review_backed") is True
    has_review_status = review_status in REVIEWED_STATUSES or review_backed
    has_review_identity = bool(reviewer or review_artifact or artifact_paths.get("review"))
    return has_review_status and has_review_identity and bool(rationale)


def _loads_dict(value: str) -> dict[str, Any]:
    try:
        payload = json.loads(value or "{}")
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}
