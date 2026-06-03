from __future__ import annotations

import math

import pytest

from alpha_system.governance.serialization import (
    GovernanceSerializationError,
    canonical_serialize,
    content_hash,
    deserialize,
    serialize,
)


def test_canonical_serialize_orders_keys_and_uses_stable_formatting() -> None:
    value = {"b": [2, "fixture"], "a": {"y": True, "x": 1}}

    assert canonical_serialize(value) == '{"a":{"x":1,"y":true},"b":[2,"fixture"]}'
    assert serialize(value) == canonical_serialize(value)


def test_deserialize_round_trips_logical_content() -> None:
    value = {"name": "synthetic-governance-fixture", "nested": {"enabled": True}, "version": 1}

    assert deserialize(canonical_serialize(value)) == value


def test_content_hash_is_order_invariant_and_change_sensitive() -> None:
    left = {"version": 1, "fields": {"b": "beta", "a": "alpha"}}
    reordered = {"fields": {"a": "alpha", "b": "beta"}, "version": 1}
    changed = {"fields": {"a": "alpha", "b": "changed"}, "version": 1}

    assert content_hash(left) == content_hash(reordered)
    assert content_hash(left) != content_hash(changed)


def test_serialize_rejects_non_string_mapping_keys() -> None:
    with pytest.raises(GovernanceSerializationError) as exc_info:
        canonical_serialize({1: "not allowed"})  # type: ignore[dict-item]

    assert exc_info.value.issue.code == "non_string_key"


def test_serialize_rejects_values_that_cannot_round_trip_as_json() -> None:
    with pytest.raises(GovernanceSerializationError) as exc_info:
        canonical_serialize({"tags": {"unordered"}})  # type: ignore[dict-item]

    assert exc_info.value.issue.code == "unsupported_value_type"


def test_serialize_rejects_non_finite_numbers() -> None:
    with pytest.raises(GovernanceSerializationError) as exc_info:
        canonical_serialize({"score": math.nan})

    assert exc_info.value.issue.code == "non_finite_number"


def test_deserialize_rejects_duplicate_keys() -> None:
    with pytest.raises(GovernanceSerializationError) as exc_info:
        deserialize('{"a":1,"a":2}')

    assert exc_info.value.issue.code == "duplicate_key"


def test_deserialize_rejects_non_string_input() -> None:
    with pytest.raises(GovernanceSerializationError) as exc_info:
        deserialize(b'{"a":1}')  # type: ignore[arg-type]

    assert exc_info.value.issue.code == "invalid_serialized_type"
