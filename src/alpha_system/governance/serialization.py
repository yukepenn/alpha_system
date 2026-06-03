"""Canonical serialization and hashing primitives for governance records."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]


@dataclass(frozen=True, slots=True)
class SerializationIssue:
    """Structured reason a governance value cannot be serialized safely."""

    code: str
    message: str
    path: str = "$"

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "message": self.message,
            "path": self.path,
        }


class GovernanceSerializationError(ValueError):
    """Raised when canonical governance serialization fails closed."""

    def __init__(self, issue: SerializationIssue):
        self.issue = issue
        super().__init__(f"{issue.path}: {issue.message}")

    def to_dict(self) -> dict[str, str]:
        return self.issue.to_dict()


def canonical_serialize(value: JsonValue) -> str:
    """Return deterministic canonical JSON for a JSON-compatible governance value."""

    normalized = _require_json_value(value)
    return json.dumps(
        normalized,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def serialize(value: JsonValue) -> str:
    """Alias for canonical governance serialization."""

    return canonical_serialize(value)


def deserialize(text: str) -> JsonValue:
    """Deserialize canonical JSON and reject ambiguous or malformed payloads."""

    if not isinstance(text, str):
        raise GovernanceSerializationError(
            SerializationIssue(
                code="invalid_serialized_type",
                message="serialized governance content must be a string",
            )
        )
    try:
        value = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except GovernanceSerializationError:
        raise
    except json.JSONDecodeError as exc:
        raise GovernanceSerializationError(
            SerializationIssue(
                code="invalid_json",
                message=f"invalid JSON: {exc.msg}",
                path=f"${exc.pos}",
            )
        ) from exc
    return _require_json_value(value)


def content_hash(value: JsonValue) -> str:
    """Hash the canonical serialized form of a governance value with SHA-256."""

    return hashlib.sha256(canonical_serialize(value).encode("utf-8")).hexdigest()


def hash_content(value: JsonValue) -> str:
    """Alias for deterministic governance content hashing."""

    return content_hash(value)


def _require_json_value(value: Any, *, path: str = "$") -> JsonValue:
    if value is None or isinstance(value, bool | str):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise GovernanceSerializationError(
                SerializationIssue(
                    code="non_finite_number",
                    message="JSON numbers must be finite",
                    path=path,
                )
            )
        return value
    if isinstance(value, list):
        return [
            _require_json_value(item, path=f"{path}[{index}]")
            for index, item in enumerate(value)
        ]
    if isinstance(value, Mapping):
        normalized: dict[str, JsonValue] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise GovernanceSerializationError(
                    SerializationIssue(
                        code="non_string_key",
                        message="governance serialization requires string mapping keys",
                        path=path,
                    )
                )
            normalized[key] = _require_json_value(item, path=f"{path}.{key}")
        return normalized
    raise GovernanceSerializationError(
        SerializationIssue(
            code="unsupported_value_type",
            message=f"unsupported governance serialization type: {type(value).__name__}",
            path=path,
        )
    )


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise GovernanceSerializationError(
                SerializationIssue(
                    code="duplicate_key",
                    message=f"duplicate JSON key: {key}",
                )
            )
        result[key] = value
    return result


__all__ = [
    "GovernanceSerializationError",
    "JsonValue",
    "SerializationIssue",
    "canonical_serialize",
    "content_hash",
    "deserialize",
    "hash_content",
    "serialize",
]
