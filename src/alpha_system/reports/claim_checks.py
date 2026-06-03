"""Deterministic prohibited-claim checks for review artifacts."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

from alpha_system.reports.prohibited_claims import ProhibitedClaimError


BLOCKED_PHRASES: tuple[str, ...] = (
    "profitable",
    "tradable",
    "production-ready",
    "guaranteed alpha",
    "market-beating",
    "live-ready",
    "deployable",
    "production candidate",
)

EVIDENCE_TERMS: tuple[str, ...] = (
    "evidence",
    "evidenced",
    "review",
    "reviewed",
    "validation",
    "validated",
)


@dataclass(frozen=True, slots=True)
class ClaimCheckViolation:
    """One blocked or context-sensitive language violation."""

    code: str
    phrase: str
    message: str

    def to_dict(self) -> dict[str, str]:
        """Return a stable dictionary representation."""
        return asdict(self)


def find_claim_violations(payload: Mapping[str, Any] | Sequence[Any] | str) -> tuple[
    ClaimCheckViolation,
    ...,
]:
    """Return deterministic prohibited-claim matches for a payload or text."""
    text = _payload_text(payload)
    normalized = _normalize_text(text)
    violations: list[ClaimCheckViolation] = []
    for phrase in BLOCKED_PHRASES:
        normalized_phrase = _normalize_text(phrase)
        if _contains_phrase(normalized, normalized_phrase):
            violations.append(
                ClaimCheckViolation(
                    code=f"blocked_claim:{normalized_phrase.replace(' ', '_')}",
                    phrase=phrase,
                    message=f"review artifact contains blocked claim phrase: {phrase}",
                )
            )

    if _contains_phrase(normalized, "robust") and not _has_evidence_context(normalized):
        violations.append(
            ClaimCheckViolation(
                code="blocked_claim:robust_without_evidence",
                phrase="robust",
                message="robustness language requires explicit evidence or review context",
            )
        )

    approved_mentions = tuple(_approved_mentions_without_review(text))
    for phrase in approved_mentions:
        violations.append(
            ClaimCheckViolation(
                code="blocked_claim:approved_without_review",
                phrase=phrase,
                message="approval language requires explicit review context",
            )
        )
    return tuple(violations)


def find_prohibited_claims(payload: Mapping[str, Any] | Sequence[Any] | str) -> tuple[
    ClaimCheckViolation,
    ...,
]:
    """Compatibility alias for report claim checks."""
    return find_claim_violations(payload)


def has_prohibited_claims(payload: Mapping[str, Any] | Sequence[Any] | str) -> bool:
    """Return whether the payload contains blocked claim language."""
    return bool(find_claim_violations(payload))


def validate_no_prohibited_claims(
    payload: Mapping[str, Any] | Sequence[Any] | str,
    *,
    context: str = "review artifact",
) -> None:
    """Raise when blocked report-language vocabulary appears."""
    violations = find_claim_violations(payload)
    if violations:
        blocked = ", ".join(violation.phrase for violation in violations)
        raise ProhibitedClaimError(f"{context} contains prohibited claim language: {blocked}")


def _payload_text(payload: Mapping[str, Any] | Sequence[Any] | str) -> str:
    if isinstance(payload, str):
        return payload
    return json.dumps(payload, sort_keys=True, default=str)


def _normalize_text(value: str) -> str:
    lowered = value.casefold()
    replaced = re.sub(r"[^a-z0-9]+", " ", lowered)
    return re.sub(r"\s+", " ", replaced).strip()


def _contains_phrase(normalized_text: str, normalized_phrase: str) -> bool:
    pattern = rf"(?<![a-z0-9]){re.escape(normalized_phrase)}(?![a-z0-9])"
    return re.search(pattern, normalized_text) is not None


def _has_evidence_context(normalized_text: str) -> bool:
    return any(_contains_phrase(normalized_text, term) for term in EVIDENCE_TERMS)


def _approved_mentions_without_review(text: str) -> tuple[str, ...]:
    lowered = text.casefold()
    matches: list[str] = []
    for match in re.finditer(r"(?<![a-z0-9])approved(?![a-z0-9])", lowered):
        window = lowered[max(0, match.start() - 96) : match.end() + 96]
        if "review" not in window:
            matches.append(text[match.start() : match.end()])
    return tuple(matches)
