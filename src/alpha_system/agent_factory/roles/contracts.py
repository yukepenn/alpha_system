"""Value-free Agent Factory role contract model."""

from __future__ import annotations

import re
from dataclasses import dataclass

MAX_DECLARATIVE_TEXT_LENGTH = 512
FORBIDDEN_PAYLOAD_MARKERS: tuple[str, ...] = (
    "raw_payload",
    "provider_payload",
    "db_rows",
    "data/raw/",
    "data/canonical/",
    "data/factors/",
    "data/labels/",
    "data/cache/",
    "metadata/",
    "artifacts/",
)
FORBIDDEN_HEAVY_SUFFIXES: tuple[str, ...] = (
    ".parquet",
    ".arrow",
    ".feather",
    ".dbn",
    ".zst",
    ".sqlite",
    ".db",
    ".wal",
)
_ROLE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(frozen=True, slots=True)
class AgentRole:
    """Immutable declaration of one Agent Factory role boundary.

    The contract stores only short declarative references. It does not carry
    raw data, provider payloads, records, runtime values, or heavy artifacts.
    """

    role_id: str
    name: str
    purpose: str
    readable_inputs: tuple[str, ...]
    callable_tools: tuple[str, ...]
    producible_outputs: tuple[str, ...]
    allowed_decisions: tuple[str, ...]
    forbidden_decisions: tuple[str, ...]
    handoff_format: tuple[str, ...]
    reviewer_independence: tuple[str, ...]
    failure_modes: tuple[str, ...]

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> AgentRole:
        """Fail closed unless every field is populated and value-free."""

        _validate_role_id(self.role_id)
        _validate_text("name", self.name)
        _validate_text("purpose", self.purpose)
        _validate_string_tuple("readable_inputs", self.readable_inputs)
        _validate_string_tuple("callable_tools", self.callable_tools)
        _validate_string_tuple("producible_outputs", self.producible_outputs)
        _validate_string_tuple("allowed_decisions", self.allowed_decisions)
        _validate_string_tuple("forbidden_decisions", self.forbidden_decisions)
        _validate_string_tuple("handoff_format", self.handoff_format)
        _validate_string_tuple("reviewer_independence", self.reviewer_independence)
        _validate_string_tuple("failure_modes", self.failure_modes)
        return self


def _validate_role_id(value: object) -> None:
    _validate_text("role_id", value)
    if not _ROLE_ID_PATTERN.fullmatch(value):
        raise ValueError("role_id must be stable snake_case")


def _validate_string_tuple(field_name: str, value: object) -> None:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple[str, ...]")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    for item in value:
        _validate_text(field_name, item)


def _validate_text(field_name: str, value: object) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a str")
    if value != value.strip() or not value:
        raise ValueError(f"{field_name} must be non-empty without surrounding whitespace")
    if len(value) > MAX_DECLARATIVE_TEXT_LENGTH:
        raise ValueError(f"{field_name} exceeds declarative text length")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{field_name} must be a single-line declarative string")
    lowered = value.lower()
    if any(marker in lowered for marker in FORBIDDEN_PAYLOAD_MARKERS):
        raise ValueError(f"{field_name} contains a forbidden payload marker")
    if any(suffix in lowered for suffix in FORBIDDEN_HEAVY_SUFFIXES):
        raise ValueError(f"{field_name} contains a forbidden heavy artifact reference")
