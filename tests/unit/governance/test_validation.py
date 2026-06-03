from __future__ import annotations

import pytest

from alpha_system.governance.validation import (
    GovernanceValidationError,
    reject_unknown_fields,
    require_mapping,
    validate_field_types,
    validate_required_fields,
    validate_schema,
)


def test_validate_schema_returns_valid_payload_unchanged() -> None:
    payload = {
        "object_id": "hyp_0123456789abcdef01234567",
        "title": "synthetic governance fixture",
        "version": 1,
    }

    result = validate_schema(
        payload,
        required_fields=("object_id", "title", "version"),
        field_types={"object_id": str, "title": str, "version": int},
        allowed_fields=("object_id", "title", "version"),
        object_name="FixtureRecord",
    )

    assert result is payload


def test_validate_required_fields_fails_closed_for_missing_field() -> None:
    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_required_fields(
            {"object_id": "hyp_0123456789abcdef01234567"},
            ("object_id", "title"),
            object_name="FixtureRecord",
        )

    assert exc_info.value.issues[0].code == "missing_required_field"
    assert exc_info.value.issues[0].field == "title"


def test_validate_required_fields_fails_closed_for_null_required_field() -> None:
    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_required_fields(
            {"object_id": "hyp_0123456789abcdef01234567", "title": None},
            ("object_id", "title"),
            object_name="FixtureRecord",
        )

    assert exc_info.value.issues[0].code == "null_required_field"


def test_validate_field_types_rejects_malformed_values_without_coercion() -> None:
    payload = {"version": "1", "enabled": 1}

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_field_types(
            payload,
            {"version": int, "enabled": bool},
            object_name="FixtureRecord",
        )

    assert [issue.code for issue in exc_info.value.issues] == [
        "invalid_field_type",
        "invalid_field_type",
    ]
    assert payload["version"] == "1"
    assert payload["enabled"] == 1


def test_validate_field_types_treats_bool_as_distinct_from_int() -> None:
    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_field_types({"version": True}, {"version": int}, object_name="FixtureRecord")

    assert exc_info.value.issues[0].actual == "bool"


def test_reject_unknown_fields_fails_closed_without_dropping_fields() -> None:
    payload = {"object_id": "hyp_0123456789abcdef01234567", "extra": "not declared"}

    with pytest.raises(GovernanceValidationError) as exc_info:
        reject_unknown_fields(payload, ("object_id",), object_name="FixtureRecord")

    assert exc_info.value.issues[0].code == "unknown_field"
    assert "extra" in payload


def test_validate_schema_aggregates_missing_invalid_and_unknown_issues() -> None:
    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_schema(
            {"object_id": None, "version": "1", "extra": "not declared"},
            required_fields=("object_id", "title", "version"),
            field_types={"object_id": str, "version": int},
            allowed_fields=("object_id", "title", "version"),
            object_name="FixtureRecord",
        )

    assert [issue.code for issue in exc_info.value.issues] == [
        "null_required_field",
        "missing_required_field",
        "invalid_field_type",
        "invalid_field_type",
        "unknown_field",
    ]


def test_require_mapping_rejects_non_mapping_root() -> None:
    with pytest.raises(GovernanceValidationError) as exc_info:
        require_mapping([("object_id", "hyp_0123456789abcdef01234567")], object_name="FixtureRecord")

    assert exc_info.value.issues[0].code == "invalid_root_type"
