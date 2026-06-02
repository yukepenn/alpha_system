"""Blocking language validation for report artifacts."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


class ProhibitedClaimError(ValueError):
    """Raised when report text contains blocked claim language."""


PROHIBITED_CLAIMS: tuple[str, ...] = (
    "profitable",
    "tradable",
    "production-ready",
    "guaranteed alpha",
    "market-beating",
    "robust without evidence",
    "approved without review",
    "live-ready",
    "deployable",
    "production candidate",
)


@dataclass(frozen=True, slots=True)
class ProhibitedClaimMatch:
    """A blocked report-language match."""

    claim: str
    normalized_claim: str

    def to_dict(self) -> dict[str, str]:
        """Return a stable dictionary representation."""
        return {"claim": self.claim, "normalized_claim": self.normalized_claim}


def find_prohibited_claims(payload: Mapping[str, Any] | Sequence[Any] | str) -> tuple[
    ProhibitedClaimMatch,
    ...,
]:
    """Return prohibited claim matches found in a report payload or text."""
    normalized_text = _normalize_text(_payload_text(payload))
    matches: list[ProhibitedClaimMatch] = []
    for claim, normalized_claim in _NORMALIZED_CLAIMS:
        if _contains_claim(normalized_text, normalized_claim):
            matches.append(
                ProhibitedClaimMatch(claim=claim, normalized_claim=normalized_claim)
            )
    return tuple(matches)


def has_prohibited_claims(payload: Mapping[str, Any] | Sequence[Any] | str) -> bool:
    """Return whether a report payload or text contains blocked claim language."""
    return bool(find_prohibited_claims(payload))


def validate_no_prohibited_claims(
    payload: Mapping[str, Any] | Sequence[Any] | str,
    *,
    context: str = "report",
) -> None:
    """Raise when blocked report-language vocabulary appears."""
    matches = find_prohibited_claims(payload)
    if matches:
        blocked = ", ".join(match.claim for match in matches)
        msg = f"{context} contains prohibited claim language: {blocked}"
        raise ProhibitedClaimError(msg)


def _normalize_text(value: str) -> str:
    lowered = value.casefold()
    replaced = re.sub(r"[^a-z0-9]+", " ", lowered)
    return re.sub(r"\s+", " ", replaced).strip()


_NORMALIZED_CLAIMS: tuple[tuple[str, str], ...] = tuple(
    (claim, _normalize_text(claim)) for claim in PROHIBITED_CLAIMS
)


def _payload_text(payload: Mapping[str, Any] | Sequence[Any] | str) -> str:
    if isinstance(payload, str):
        return payload
    return json.dumps(payload, sort_keys=True, default=str)


def _contains_claim(normalized_text: str, normalized_claim: str) -> bool:
    pattern = rf"(?<![a-z0-9]){re.escape(normalized_claim)}(?![a-z0-9])"
    return re.search(pattern, normalized_text) is not None
