"""StudySpec input-pack contract for governed feature/label study inputs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

from alpha_system.governance.alpha_spec import AlphaSpec, validate_alpha_spec
from alpha_system.governance.feature_request import (
    FeatureRequest,
    validate_feature_request,
)
from alpha_system.governance.ids import (
    GovernanceIdError,
    GovernanceIdKind,
    prefix_for_kind,
    validate_governance_id,
)
from alpha_system.governance.label_spec import LabelSpec, validate_label_spec
from alpha_system.governance.serialization import (
    GovernanceSerializationError,
    JsonValue,
    canonical_serialize,
    deserialize,
)
from alpha_system.governance.study_spec import StudySpec, validate_study_spec
from alpha_system.governance.validation import (
    GovernanceValidationError,
    ValidationIssue,
    require_mapping,
    validate_schema,
)

STUDY_INPUT_PACK_REQUIRED_FIELDS = (
    "feature_request_ids",
    "label_spec_ids",
    "alpha_spec_id",
    "dataset_scope",
)
STUDY_INPUT_PACK_FIELD_TYPES = {
    "feature_request_ids": list,
    "label_spec_ids": list,
    "alpha_spec_id": str,
    "dataset_scope": dict,
}

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
    "unbounded",
    "unlimited",
}


@dataclass(frozen=True, slots=True, init=False)
class StudyInputPack:
    """Immutable references a future `StudySpec` consumes as governed inputs."""

    feature_request_ids: tuple[str, ...]
    label_spec_ids: tuple[str, ...]
    alpha_spec_id: str
    _dataset_scope_json: str

    def __init__(
        self,
        *,
        feature_request_ids: Sequence[str],
        label_spec_ids: Sequence[str],
        alpha_spec_id: str,
        dataset_scope: Mapping[str, Any],
    ) -> None:
        """Build a validated, hashable input pack without creating a `StudySpec`."""

        payload = {
            "feature_request_ids": _sequence_as_list(feature_request_ids),
            "label_spec_ids": _sequence_as_list(label_spec_ids),
            "alpha_spec_id": alpha_spec_id,
            "dataset_scope": _mapping_as_dict(dataset_scope),
        }
        normalized = _validate_study_input_pack_payload(payload)
        object.__setattr__(
            self,
            "feature_request_ids",
            normalized["feature_request_ids"],
        )
        object.__setattr__(self, "label_spec_ids", normalized["label_spec_ids"])
        object.__setattr__(self, "alpha_spec_id", normalized["alpha_spec_id"])
        object.__setattr__(
            self,
            "_dataset_scope_json",
            normalized["dataset_scope_json"],
        )

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> StudyInputPack:
        """Build a `StudyInputPack` from a mapping after fail-closed validation."""

        return validate_study_input_pack(payload)

    @classmethod
    def from_canonical_json(cls, text: str) -> StudyInputPack:
        """Deserialize canonical JSON and validate the resulting input pack."""

        value = deserialize(text)
        mapping = require_mapping(value, object_name="StudyInputPack")
        return validate_study_input_pack(mapping)

    @property
    def dataset_scope(self) -> dict[str, JsonValue]:
        """Return a defensive copy of the StudySpec-compatible dataset scope."""

        value = deserialize(self._dataset_scope_json)
        mapping = require_mapping(value, object_name="StudyInputPack.dataset_scope")
        return cast(dict[str, JsonValue], dict(mapping))

    def to_dict(self) -> dict[str, JsonValue]:
        """Return the canonical public list/dict shape for this input bundle."""

        return {
            "feature_request_ids": list(self.feature_request_ids),
            "label_spec_ids": list(self.label_spec_ids),
            "alpha_spec_id": self.alpha_spec_id,
            "dataset_scope": self.dataset_scope,
        }

    def to_canonical_json(self) -> str:
        """Serialize the validated input pack through the canonical primitive."""

        return canonical_serialize(self.to_dict())


def create_study_input_pack(
    *,
    feature_request_ids: list[str],
    label_spec_ids: list[str],
    alpha_spec_id: str,
    dataset_scope: dict[str, JsonValue],
) -> StudyInputPack:
    """Create a validated input bundle without running or persisting a study."""

    return StudyInputPack(
        feature_request_ids=feature_request_ids,
        label_spec_ids=label_spec_ids,
        alpha_spec_id=alpha_spec_id,
        dataset_scope=dataset_scope,
    )


def validate_study_input_pack(payload: Mapping[str, Any]) -> StudyInputPack:
    """Validate a `StudyInputPack` mapping fail-closed and return a typed record."""

    normalized = _validate_study_input_pack_payload(payload)
    return StudyInputPack(
        feature_request_ids=list(normalized["feature_request_ids"]),
        label_spec_ids=list(normalized["label_spec_ids"]),
        alpha_spec_id=normalized["alpha_spec_id"],
        dataset_scope=cast(dict[str, JsonValue], deserialize(normalized["dataset_scope_json"])),
    )


def validate_study_input_pack_references(
    pack: StudyInputPack | Mapping[str, Any],
    *,
    feature_requests: Sequence[FeatureRequest | Mapping[str, Any]] = (),
    label_specs: Sequence[LabelSpec | Mapping[str, Any]] = (),
    alpha_spec: AlphaSpec | Mapping[str, Any] | None = None,
    study_spec: StudySpec | Mapping[str, Any] | None = None,
) -> StudyInputPack:
    """Validate resolved public governance contracts against an input pack.

    The pack itself is handle-only and performs no registry lookup. When callers
    have already resolved governance records, this helper consumes the public
    validators from the existing governance modules and cross-checks the
    resolved IDs without mutating or persisting any governance object.
    """

    validated_pack = pack if isinstance(pack, StudyInputPack) else validate_study_input_pack(pack)
    issues: list[ValidationIssue] = []

    if feature_requests:
        resolved_feature_requests = [_coerce_feature_request(record) for record in feature_requests]
        expected_ids = set(validated_pack.feature_request_ids)
        actual_ids = {record.feature_request_id for record in resolved_feature_requests}
        if actual_ids != expected_ids:
            issues.append(
                ValidationIssue(
                    field="feature_requests",
                    code="resolved_feature_requests_mismatch",
                    message=(
                        "resolved FeatureRequest ids must exactly match "
                        "StudyInputPack.feature_request_ids"
                    ),
                    expected=",".join(sorted(expected_ids)),
                    actual=",".join(sorted(actual_ids)),
                )
            )
        for record in resolved_feature_requests:
            if record.alpha_spec_id != validated_pack.alpha_spec_id:
                issues.append(
                    ValidationIssue(
                        field="feature_requests.alpha_spec_id",
                        code="feature_request_alpha_spec_mismatch",
                        message=(
                            "resolved FeatureRequest.alpha_spec_id must match "
                            "StudyInputPack.alpha_spec_id"
                        ),
                        expected=validated_pack.alpha_spec_id,
                        actual=record.alpha_spec_id,
                    )
                )

    if label_specs:
        resolved_label_specs = [_coerce_label_spec(record) for record in label_specs]
        expected_ids = set(validated_pack.label_spec_ids)
        actual_ids = {record.label_spec_id for record in resolved_label_specs}
        if actual_ids != expected_ids:
            issues.append(
                ValidationIssue(
                    field="label_specs",
                    code="resolved_label_specs_mismatch",
                    message=(
                        "resolved LabelSpec ids must exactly match StudyInputPack.label_spec_ids"
                    ),
                    expected=",".join(sorted(expected_ids)),
                    actual=",".join(sorted(actual_ids)),
                )
            )
        for record in resolved_label_specs:
            if (
                record.alpha_spec_id is not None
                and record.alpha_spec_id != validated_pack.alpha_spec_id
            ):
                issues.append(
                    ValidationIssue(
                        field="label_specs.alpha_spec_id",
                        code="label_spec_alpha_spec_mismatch",
                        message=(
                            "resolved LabelSpec.alpha_spec_id must match "
                            "StudyInputPack.alpha_spec_id when declared"
                        ),
                        expected=validated_pack.alpha_spec_id,
                        actual=record.alpha_spec_id,
                    )
                )

    if alpha_spec is not None:
        resolved_alpha_spec = _coerce_alpha_spec(alpha_spec)
        if resolved_alpha_spec.alpha_spec_id != validated_pack.alpha_spec_id:
            issues.append(
                ValidationIssue(
                    field="alpha_spec.alpha_spec_id",
                    code="resolved_alpha_spec_mismatch",
                    message=(
                        "resolved AlphaSpec.alpha_spec_id must match StudyInputPack.alpha_spec_id"
                    ),
                    expected=validated_pack.alpha_spec_id,
                    actual=resolved_alpha_spec.alpha_spec_id,
                )
            )

    if study_spec is not None:
        resolved_study_spec = _coerce_study_spec(study_spec)
        if resolved_study_spec.alpha_spec_id != validated_pack.alpha_spec_id:
            issues.append(
                ValidationIssue(
                    field="study_spec.alpha_spec_id",
                    code="study_spec_alpha_spec_mismatch",
                    message=(
                        "resolved StudySpec.alpha_spec_id must match StudyInputPack.alpha_spec_id"
                    ),
                    expected=validated_pack.alpha_spec_id,
                    actual=resolved_study_spec.alpha_spec_id,
                )
            )
        if resolved_study_spec.label_spec_id not in validated_pack.label_spec_ids:
            issues.append(
                ValidationIssue(
                    field="study_spec.label_spec_id",
                    code="study_spec_label_spec_missing_from_pack",
                    message=(
                        "resolved StudySpec.label_spec_id must be one of "
                        "StudyInputPack.label_spec_ids"
                    ),
                    expected=",".join(validated_pack.label_spec_ids),
                    actual=resolved_study_spec.label_spec_id,
                )
            )
        if resolved_study_spec.dataset_scope != validated_pack.dataset_scope:
            issues.append(
                ValidationIssue(
                    field="study_spec.dataset_scope",
                    code="study_spec_dataset_scope_mismatch",
                    message=(
                        "resolved StudySpec.dataset_scope must match StudyInputPack.dataset_scope"
                    ),
                    expected=canonical_serialize(validated_pack.dataset_scope),
                    actual=canonical_serialize(resolved_study_spec.dataset_scope),
                )
            )

    if issues:
        raise GovernanceValidationError(issues)
    return validated_pack


def _validate_study_input_pack_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    mapping = validate_schema(
        payload,
        required_fields=STUDY_INPUT_PACK_REQUIRED_FIELDS,
        field_types=STUDY_INPUT_PACK_FIELD_TYPES,
        allowed_fields=STUDY_INPUT_PACK_REQUIRED_FIELDS,
        object_name="StudyInputPack",
    )

    issues: list[ValidationIssue] = []
    issues.extend(
        _validate_handle_list(
            mapping["feature_request_ids"],
            field="feature_request_ids",
            expected_kind=GovernanceIdKind.FEATURE_REQUEST,
        )
    )
    issues.extend(
        _validate_handle_list(
            mapping["label_spec_ids"],
            field="label_spec_ids",
            expected_kind=GovernanceIdKind.LABEL_SPEC,
        )
    )
    issues.extend(
        _validate_handle(
            mapping["alpha_spec_id"],
            field="alpha_spec_id",
            expected_kind=GovernanceIdKind.ALPHA_SPEC,
        )
    )
    issues.extend(_validate_dataset_scope(mapping["dataset_scope"]))
    issues.extend(_validate_canonical_serializable(mapping))
    if issues:
        raise GovernanceValidationError(issues)

    dataset_scope_json = canonical_serialize(cast(JsonValue, mapping["dataset_scope"]))
    return {
        "feature_request_ids": tuple(mapping["feature_request_ids"]),
        "label_spec_ids": tuple(mapping["label_spec_ids"]),
        "alpha_spec_id": mapping["alpha_spec_id"],
        "dataset_scope_json": dataset_scope_json,
    }


def _validate_handle_list(
    values: list[Any],
    *,
    field: str,
    expected_kind: GovernanceIdKind,
) -> list[ValidationIssue]:
    if not values:
        return [
            ValidationIssue(
                field=field,
                code="empty_required_field",
                message=f"StudyInputPack.{field} must contain at least one handle",
                expected="non-empty list",
                actual="empty list",
            )
        ]

    issues: list[ValidationIssue] = []
    seen: set[str] = set()
    for index, value in enumerate(values):
        item_field = f"{field}[{index}]"
        issues.extend(
            _validate_handle(
                value,
                field=item_field,
                expected_kind=expected_kind,
            )
        )
        if isinstance(value, str):
            if value in seen:
                issues.append(
                    ValidationIssue(
                        field=item_field,
                        code="duplicate_governance_id",
                        message=f"StudyInputPack.{field} must not contain duplicate handles",
                        expected="unique governance id",
                        actual=value,
                    )
                )
            seen.add(value)
    return issues


def _validate_handle(
    value: Any,
    *,
    field: str,
    expected_kind: GovernanceIdKind,
) -> list[ValidationIssue]:
    try:
        validate_governance_id(
            value,
            expected_kind=expected_kind,
            expected_prefix=prefix_for_kind(expected_kind),
        )
    except GovernanceIdError as exc:
        return [
            ValidationIssue(
                field=field,
                code=exc.issue.code,
                message=exc.issue.message,
                expected=expected_kind.value,
                actual=str(exc.issue.value),
            )
        ]
    return []


def _validate_dataset_scope(value: Mapping[str, Any]) -> list[ValidationIssue]:
    if not value:
        return [
            ValidationIssue(
                field="dataset_scope",
                code="empty_required_field",
                message="StudyInputPack.dataset_scope must contain explicit metadata",
                expected="non-empty mapping",
                actual="empty mapping",
            )
        ]

    issues: list[ValidationIssue] = []
    for key, item in value.items():
        key_field = f"dataset_scope.{key}"
        if not isinstance(key, str) or _normalize_text(key) in _VAGUE_TEXT:
            issues.append(
                ValidationIssue(
                    field="dataset_scope",
                    code="invalid_metadata_key",
                    message="StudyInputPack.dataset_scope keys must be explicit strings",
                    expected="non-empty explicit string key",
                    actual=str(key),
                )
            )
        issues.extend(_validate_substantive_value(item, field=key_field))
    return issues


def _validate_substantive_value(value: Any, *, field: str) -> list[ValidationIssue]:
    if value is None:
        return [
            ValidationIssue(
                field=field,
                code="null_required_field",
                message=f"StudyInputPack.{field} must not be null",
                expected="explicit metadata value",
                actual="NoneType",
            )
        ]
    if isinstance(value, str):
        if _normalize_text(value) in _VAGUE_TEXT:
            return [
                ValidationIssue(
                    field=field,
                    code="vague_required_field",
                    message=f"StudyInputPack.{field} must be explicit, not vague",
                    expected="substantive explicit value",
                    actual=value,
                )
            ]
        return []
    if isinstance(value, list):
        if not value:
            return [
                ValidationIssue(
                    field=field,
                    code="empty_required_field",
                    message=f"StudyInputPack.{field} must not be an empty list",
                    expected="non-empty value",
                    actual="empty list",
                )
            ]
        issues: list[ValidationIssue] = []
        for index, item in enumerate(value):
            issues.extend(_validate_substantive_value(item, field=f"{field}[{index}]"))
        return issues
    if isinstance(value, Mapping):
        if not value:
            return [
                ValidationIssue(
                    field=field,
                    code="empty_required_field",
                    message=f"StudyInputPack.{field} must not be an empty mapping",
                    expected="non-empty value",
                    actual="empty mapping",
                )
            ]
        issues = []
        for key, item in value.items():
            nested_field = f"{field}.{key}"
            if not isinstance(key, str) or _normalize_text(key) in _VAGUE_TEXT:
                issues.append(
                    ValidationIssue(
                        field=field,
                        code="invalid_metadata_key",
                        message="StudyInputPack.dataset_scope nested keys must be explicit strings",
                        expected="non-empty explicit string key",
                        actual=str(key),
                    )
                )
            issues.extend(_validate_substantive_value(item, field=nested_field))
        return issues
    return []


def _validate_canonical_serializable(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    try:
        canonical_serialize({field: mapping[field] for field in STUDY_INPUT_PACK_REQUIRED_FIELDS})
    except GovernanceSerializationError as exc:
        return [
            ValidationIssue(
                field=exc.issue.path,
                code=exc.issue.code,
                message=exc.issue.message,
                expected="canonical JSON-compatible StudyInputPack",
                actual=exc.issue.path,
            )
        ]
    return []


def _coerce_feature_request(value: FeatureRequest | Mapping[str, Any]) -> FeatureRequest:
    if isinstance(value, FeatureRequest):
        return validate_feature_request(value.to_dict())
    return validate_feature_request(value)


def _coerce_label_spec(value: LabelSpec | Mapping[str, Any]) -> LabelSpec:
    if isinstance(value, LabelSpec):
        return validate_label_spec(value.to_dict())
    return validate_label_spec(value)


def _coerce_alpha_spec(value: AlphaSpec | Mapping[str, Any]) -> AlphaSpec:
    if isinstance(value, AlphaSpec):
        return validate_alpha_spec(value.to_dict())
    return validate_alpha_spec(value)


def _coerce_study_spec(value: StudySpec | Mapping[str, Any]) -> StudySpec:
    if isinstance(value, StudySpec):
        return validate_study_spec(value.to_dict())
    return validate_study_spec(value)


def _sequence_as_list(value: Sequence[str]) -> Any:
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    return value


def _mapping_as_dict(value: Mapping[str, Any]) -> Any:
    if isinstance(value, dict):
        return dict(value)
    return value


def _normalize_text(value: str) -> str:
    return " ".join(value.strip().casefold().split())


__all__ = [
    "STUDY_INPUT_PACK_FIELD_TYPES",
    "STUDY_INPUT_PACK_REQUIRED_FIELDS",
    "StudyInputPack",
    "create_study_input_pack",
    "validate_study_input_pack",
    "validate_study_input_pack_references",
]
