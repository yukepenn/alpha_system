"""Fail-closed label leakage guard for LabelSpec feature references."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from alpha_system.governance.label_spec import LabelSpec, validate_label_spec
from alpha_system.governance.serialization import JsonValue


FeatureReferences = Iterable[Any] | Mapping[str, Any] | str | None

_IDENTIFIER_RE = re.compile(r"[^a-z0-9]+")
_FEATURE_COLLECTION_KEYS = (
    "features",
    "feature_references",
    "requested_features",
    "requested_inputs",
)
_REFERENCE_KEYS = (
    "reference",
    "feature_reference",
    "feature_id",
    "name",
    "field",
    "fields",
    "input",
    "inputs",
    "requested_input",
    "requested_inputs",
    "factor_id",
)
_TRANSFORM_KEYS = ("transform", "transforms", "operation", "operator")
_AVAILABILITY_KEYS = (
    "information_time",
    "feature_information_time",
    "feature_availability_time",
    "availability_time",
    "available_at",
    "as_of",
)


class LabelLeakageFindingKind(StrEnum):
    """Label leakage finding kinds."""

    LABEL_AS_FEATURE = "LABEL_AS_FEATURE"
    LOOKAHEAD = "LOOKAHEAD"


class LabelLeakageSeverity(StrEnum):
    """Label leakage finding severity metadata."""

    BLOCKING = "BLOCKING"


@dataclass(frozen=True, slots=True)
class LabelLeakageFinding:
    """A blocking label leakage finding."""

    kind: LabelLeakageFindingKind
    severity: LabelLeakageSeverity
    offending_reference: dict[str, JsonValue]
    rationale: str

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a strict JSON-compatible representation."""

        return {
            "kind": self.kind.value,
            "severity": self.severity.value,
            "offending_reference": dict(self.offending_reference),
            "rationale": self.rationale,
        }


@dataclass(frozen=True, slots=True)
class LabelLeakageResult:
    """Structured result from a label leakage check."""

    findings: tuple[LabelLeakageFinding, ...]
    features_checked: int

    @property
    def is_clean(self) -> bool:
        """Return true only when the guard found no blocking leakage."""

        return not self.findings

    @property
    def clean(self) -> bool:
        """Alias for callers that need an explicit clean boolean."""

        return self.is_clean

    @property
    def is_blocked(self) -> bool:
        """Return whether the result blocks the feature set."""

        return not self.is_clean

    @property
    def blocked(self) -> bool:
        """Alias for callers that need an explicit blocked boolean."""

        return self.is_blocked

    @property
    def has_blocking_findings(self) -> bool:
        """Return whether any finding blocks acceptance without repair."""

        return self.is_blocked

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a strict JSON-compatible representation."""

        return {
            "clean": self.is_clean,
            "blocked": self.is_blocked,
            "features_checked": self.features_checked,
            "findings": [finding.to_dict() for finding in self.findings],
        }


@dataclass(frozen=True, slots=True)
class _FeatureReference:
    index: int
    reference: str
    candidate_references: frozenset[str]
    information_time: str | None
    metadata_issue: str


def check_label_leakage(
    label_spec: LabelSpec | Mapping[str, Any],
    feature_references: FeatureReferences,
) -> LabelLeakageResult:
    """Check requested features against a `LabelSpec` for future-information leakage."""

    spec = _coerce_label_spec(label_spec)
    label_availability = _parse_iso_datetime(spec.availability_time)
    forbidden = _forbidden_reference_sets(spec)
    features, findings = _coerce_feature_references(feature_references)

    for feature in features:
        findings.extend(_label_as_feature_findings(feature, forbidden))
        findings.extend(_lookahead_findings(feature, label_availability))

    return LabelLeakageResult(
        findings=tuple(findings),
        features_checked=len(features),
    )


def _coerce_label_spec(value: LabelSpec | Mapping[str, Any]) -> LabelSpec:
    if isinstance(value, LabelSpec):
        return validate_label_spec(value.to_dict())
    return validate_label_spec(value)


def _coerce_feature_references(
    feature_references: FeatureReferences,
) -> tuple[list[_FeatureReference], list[LabelLeakageFinding]]:
    if feature_references is None:
        return [], [
            _metadata_finding(
                index=0,
                reference="",
                rationale=(
                    "feature availability metadata is missing; label leakage guard "
                    "fails closed"
                ),
            )
        ]

    items = _feature_items(feature_references)
    if items is None:
        return [], [
            _metadata_finding(
                index=0,
                reference=str(type(feature_references).__name__),
                rationale=(
                    "feature references must be an iterable or mapping; label leakage "
                    "guard fails closed"
                ),
            )
        ]

    features: list[_FeatureReference] = []
    findings: list[LabelLeakageFinding] = []
    for index, item in enumerate(items):
        feature = _feature_reference_from_item(item, index)
        features.append(feature)
        if not feature.candidate_references:
            findings.append(
                _metadata_finding(
                    index=index,
                    reference=feature.reference,
                    rationale=(
                        "feature reference is missing or ambiguous; label leakage guard "
                        "fails closed"
                    ),
                )
            )
    return features, findings


def _feature_items(feature_references: FeatureReferences) -> list[Any] | None:
    if isinstance(feature_references, str):
        return [feature_references]
    if isinstance(feature_references, Mapping):
        for key in _FEATURE_COLLECTION_KEYS:
            if key in feature_references:
                value = feature_references[key]
                if isinstance(value, str):
                    return [value]
                if isinstance(value, Iterable):
                    return list(value)
                return None
        return [feature_references]
    if isinstance(feature_references, Iterable):
        return list(feature_references)
    return None


def _feature_reference_from_item(item: Any, index: int) -> _FeatureReference:
    candidate_references = _candidate_reference_strings(item)
    information_time, metadata_issue = _information_time(item)
    reference = sorted(candidate_references)[0] if candidate_references else str(type(item).__name__)
    return _FeatureReference(
        index=index,
        reference=reference,
        candidate_references=frozenset(candidate_references),
        information_time=information_time,
        metadata_issue=metadata_issue,
    )


def _candidate_reference_strings(item: Any) -> set[str]:
    if isinstance(item, str):
        return {item}
    if not isinstance(item, Mapping):
        return set()

    references: set[str] = set()
    transforms: set[str] = set()
    for key in _REFERENCE_KEYS:
        if key in item:
            references.update(_string_values(item[key]))
    for key in _TRANSFORM_KEYS:
        if key in item:
            transforms.update(_string_values(item[key]))
    for reference in tuple(references):
        for transform in transforms:
            references.add(f"{transform}({reference})")
    return {value for value in references if _normalize_text(value)}


def _information_time(item: Any) -> tuple[str | None, str]:
    if not isinstance(item, Mapping):
        return None, "missing availability metadata"

    values: set[str] = set()
    for key in _AVAILABILITY_KEYS:
        if key in item:
            values.update(_string_values(item[key]))
    normalized_values = {_normalize_text(value) for value in values if _normalize_text(value)}
    if not normalized_values:
        return None, "missing availability metadata"
    if len(normalized_values) > 1:
        return None, "ambiguous availability metadata"
    return next(iter(values)), ""


def _label_as_feature_findings(
    feature: _FeatureReference,
    forbidden: tuple[set[str], set[str]],
) -> list[LabelLeakageFinding]:
    forbidden_identifiers, forbidden_text = forbidden
    findings: list[LabelLeakageFinding] = []
    for candidate in feature.candidate_references:
        if (
            _normalize_identifier(candidate) in forbidden_identifiers
            or _normalize_text(candidate) in forbidden_text
        ):
            findings.append(
                LabelLeakageFinding(
                    kind=LabelLeakageFindingKind.LABEL_AS_FEATURE,
                    severity=LabelLeakageSeverity.BLOCKING,
                    offending_reference=_safe_feature_payload(
                        feature,
                        matched_reference=candidate,
                    ),
                    rationale=(
                        "requested feature matches a forbidden label reference, alias, "
                        "or transform declared by LabelSpec"
                    ),
                )
            )
            break
    return findings


def _lookahead_findings(
    feature: _FeatureReference,
    label_availability: datetime | None,
) -> list[LabelLeakageFinding]:
    if label_availability is None:
        return [
            _metadata_finding(
                index=feature.index,
                reference=feature.reference,
                rationale=(
                    "label availability time is not comparable; label leakage guard "
                    "fails closed"
                ),
            )
        ]
    if feature.metadata_issue:
        return [
            _metadata_finding(
                index=feature.index,
                reference=feature.reference,
                rationale=f"{feature.metadata_issue}; label leakage guard fails closed",
            )
        ]

    assert feature.information_time is not None
    feature_time = _parse_iso_datetime(feature.information_time)
    if feature_time is None:
        return [
            _metadata_finding(
                index=feature.index,
                reference=feature.reference,
                rationale=(
                    "feature information time is not timezone-aware ISO-8601; "
                    "label leakage guard fails closed"
                ),
            )
        ]
    if feature_time >= label_availability:
        return [
            LabelLeakageFinding(
                kind=LabelLeakageFindingKind.LOOKAHEAD,
                severity=LabelLeakageSeverity.BLOCKING,
                offending_reference=_safe_feature_payload(feature),
                rationale=(
                    "feature information time is at or after label availability time"
                ),
            )
        ]
    return []


def _metadata_finding(index: int, reference: str, rationale: str) -> LabelLeakageFinding:
    return LabelLeakageFinding(
        kind=LabelLeakageFindingKind.LOOKAHEAD,
        severity=LabelLeakageSeverity.BLOCKING,
        offending_reference={
            "source_index": index,
            "reference": reference,
        },
        rationale=rationale,
    )


def _safe_feature_payload(
    feature: _FeatureReference,
    *,
    matched_reference: str | None = None,
) -> dict[str, JsonValue]:
    payload: dict[str, JsonValue] = {
        "source_index": feature.index,
        "reference": feature.reference,
    }
    if matched_reference is not None:
        payload["matched_reference"] = matched_reference
    if feature.information_time is not None:
        payload["information_time"] = feature.information_time
    return payload


def _forbidden_reference_sets(label_spec: LabelSpec) -> tuple[set[str], set[str]]:
    declared = _declared_strings(label_spec.forbidden_feature_overlap)
    return (
        {_normalize_identifier(value) for value in declared},
        {_normalize_text(value) for value in declared},
    )


def _declared_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(_declared_strings(item))
        return result
    if isinstance(value, dict):
        result: list[str] = []
        for item in value.values():
            result.extend(_declared_strings(item))
        return result
    return []


def _string_values(value: Any) -> set[str]:
    if isinstance(value, str):
        return {value}
    if isinstance(value, list | tuple | set):
        result: set[str] = set()
        for item in value:
            result.update(_string_values(item))
        return result
    return set()


def _parse_iso_datetime(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed


def _normalize_identifier(value: str) -> str:
    return _IDENTIFIER_RE.sub("_", _normalize_text(value)).strip("_")


def _normalize_text(value: str) -> str:
    return " ".join(value.strip().lower().split())


__all__ = [
    "FeatureReferences",
    "LabelLeakageFinding",
    "LabelLeakageFindingKind",
    "LabelLeakageResult",
    "LabelLeakageSeverity",
    "check_label_leakage",
]
