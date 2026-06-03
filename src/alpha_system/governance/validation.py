"""Fail-closed validation primitives for governance records."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from types import NoneType
from typing import Any


ExpectedType = type[Any] | tuple[type[Any], ...]


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """Structured governance validation issue."""

    field: str
    code: str
    message: str
    expected: str = ""
    actual: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "field": self.field,
            "code": self.code,
            "message": self.message,
            "expected": self.expected,
            "actual": self.actual,
        }


class GovernanceValidationError(ValueError):
    """Raised when governance validation fails closed."""

    def __init__(self, issues: ValidationIssue | Iterable[ValidationIssue]):
        if isinstance(issues, ValidationIssue):
            normalized = (issues,)
        else:
            normalized = tuple(issues)
        if not normalized:
            msg = "governance validation error requires at least one issue"
            raise ValueError(msg)
        self.issues = normalized
        super().__init__("; ".join(issue.message for issue in normalized))

    def to_dict(self) -> dict[str, list[dict[str, str]]]:
        return {"issues": [issue.to_dict() for issue in self.issues]}


def require_mapping(value: Any, *, object_name: str = "governance object") -> Mapping[str, Any]:
    """Require a mapping root and return it unchanged."""

    if not isinstance(value, Mapping):
        raise GovernanceValidationError(
            ValidationIssue(
                field="$",
                code="invalid_root_type",
                message=f"{object_name} must be a mapping",
                expected="mapping",
                actual=type(value).__name__,
            )
        )
    return value


def validate_required_fields(
    payload: Mapping[str, Any],
    required_fields: Iterable[str],
    *,
    object_name: str = "governance object",
) -> Mapping[str, Any]:
    """Require explicitly declared fields and return the payload unchanged."""

    mapping = require_mapping(payload, object_name=object_name)
    issues: list[ValidationIssue] = []
    for field in required_fields:
        _require_field_name(field)
        if field not in mapping:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="missing_required_field",
                    message=f"{object_name}.{field} is required",
                    expected="present non-null value",
                    actual="missing",
                )
            )
        elif mapping[field] is None:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="null_required_field",
                    message=f"{object_name}.{field} must not be null",
                    expected="present non-null value",
                    actual="NoneType",
                )
            )
    _raise_if_issues(issues)
    return mapping


def validate_field_types(
    payload: Mapping[str, Any],
    field_types: Mapping[str, ExpectedType],
    *,
    object_name: str = "governance object",
) -> Mapping[str, Any]:
    """Validate declared field types exactly enough to avoid silent coercion."""

    mapping = require_mapping(payload, object_name=object_name)
    issues: list[ValidationIssue] = []
    for field, expected_type in field_types.items():
        _require_field_name(field)
        _require_expected_type(expected_type, field)
        if field not in mapping:
            continue
        value = mapping[field]
        if not _matches_expected_type(value, expected_type):
            issues.append(
                ValidationIssue(
                    field=field,
                    code="invalid_field_type",
                    message=(
                        f"{object_name}.{field} must be {_expected_type_name(expected_type)}, "
                        f"got {type(value).__name__}"
                    ),
                    expected=_expected_type_name(expected_type),
                    actual=type(value).__name__,
                )
            )
    _raise_if_issues(issues)
    return mapping


def reject_unknown_fields(
    payload: Mapping[str, Any],
    allowed_fields: Iterable[str],
    *,
    object_name: str = "governance object",
) -> Mapping[str, Any]:
    """Reject undeclared fields and return the payload unchanged."""

    mapping = require_mapping(payload, object_name=object_name)
    allowed = set()
    for field in allowed_fields:
        _require_field_name(field)
        allowed.add(field)
    issues = [
        ValidationIssue(
            field=str(field),
            code="unknown_field",
            message=f"{object_name}.{field} is not declared in the schema",
            expected="declared schema field",
            actual="unknown field",
        )
        for field in mapping
        if field not in allowed
    ]
    _raise_if_issues(issues)
    return mapping


def validate_schema(
    payload: Mapping[str, Any],
    *,
    required_fields: Iterable[str],
    field_types: Mapping[str, ExpectedType] | None = None,
    allowed_fields: Iterable[str] | None = None,
    object_name: str = "governance object",
) -> Mapping[str, Any]:
    """Validate a minimal mapping schema and return valid input unchanged."""

    mapping = require_mapping(payload, object_name=object_name)
    issues: list[ValidationIssue] = []

    required = tuple(required_fields)
    for field in required:
        _require_field_name(field)
        if field not in mapping:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="missing_required_field",
                    message=f"{object_name}.{field} is required",
                    expected="present non-null value",
                    actual="missing",
                )
            )
        elif mapping[field] is None:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="null_required_field",
                    message=f"{object_name}.{field} must not be null",
                    expected="present non-null value",
                    actual="NoneType",
                )
            )

    if field_types is not None:
        for field, expected_type in field_types.items():
            _require_field_name(field)
            _require_expected_type(expected_type, field)
            if field in mapping and not _matches_expected_type(mapping[field], expected_type):
                issues.append(
                    ValidationIssue(
                        field=field,
                        code="invalid_field_type",
                        message=(
                            f"{object_name}.{field} must be "
                            f"{_expected_type_name(expected_type)}, "
                            f"got {type(mapping[field]).__name__}"
                        ),
                        expected=_expected_type_name(expected_type),
                        actual=type(mapping[field]).__name__,
                    )
                )

    if allowed_fields is not None:
        allowed = set()
        for field in allowed_fields:
            _require_field_name(field)
            allowed.add(field)
        for field in mapping:
            if field not in allowed:
                issues.append(
                    ValidationIssue(
                        field=str(field),
                        code="unknown_field",
                        message=f"{object_name}.{field} is not declared in the schema",
                        expected="declared schema field",
                        actual="unknown field",
                    )
                )

    _raise_if_issues(issues)
    return mapping


def _raise_if_issues(issues: list[ValidationIssue]) -> None:
    if issues:
        raise GovernanceValidationError(issues)


def _require_field_name(field: Any) -> None:
    if not isinstance(field, str) or not field:
        raise GovernanceValidationError(
            ValidationIssue(
                field="$schema",
                code="invalid_field_name",
                message="governance schema field names must be non-empty strings",
                expected="non-empty string",
                actual=type(field).__name__,
            )
        )


def _require_expected_type(expected_type: Any, field: str) -> None:
    if isinstance(expected_type, tuple):
        valid = expected_type and all(isinstance(item, type) for item in expected_type)
    else:
        valid = isinstance(expected_type, type)
    if not valid:
        raise GovernanceValidationError(
            ValidationIssue(
                field=field,
                code="invalid_expected_type",
                message=f"governance schema type for {field} must be a type or tuple of types",
                expected="type declaration",
                actual=type(expected_type).__name__,
            )
        )


def _matches_expected_type(value: Any, expected_type: ExpectedType) -> bool:
    expected = expected_type if isinstance(expected_type, tuple) else (expected_type,)
    for candidate in expected:
        if candidate is int and type(value) is int:
            return True
        if candidate is float and type(value) is float:
            return True
        if candidate is bool and type(value) is bool:
            return True
        if candidate is str and type(value) is str:
            return True
        if candidate is NoneType and value is None:
            return True
        if candidate not in (int, float, bool, str, NoneType) and isinstance(value, candidate):
            return True
    return False


def _expected_type_name(expected_type: ExpectedType) -> str:
    expected = expected_type if isinstance(expected_type, tuple) else (expected_type,)
    return " | ".join(item.__name__ for item in expected)


__all__ = [
    "ExpectedType",
    "GovernanceValidationError",
    "ValidationIssue",
    "reject_unknown_fields",
    "require_mapping",
    "validate_field_types",
    "validate_required_fields",
    "validate_schema",
]
