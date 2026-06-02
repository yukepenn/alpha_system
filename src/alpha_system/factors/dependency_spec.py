"""Declared factor dependency representation and validation."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

from alpha_system.core.enums import FactorInputDomain, LabelType


class FactorDependencyError(ValueError):
    """Raised when declared factor dependencies are invalid."""


LABEL_FIELD_TOKENS: tuple[str, ...] = tuple(label.value for label in LabelType)
LABEL_NAME_FRAGMENTS: tuple[str, ...] = (
    "label",
    "forward_return",
    "mfe",
    "mae",
    "target_before_stop",
    "stop_before_target",
    "future_realized",
    "future_spread",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class FactorInputField:
    """A declared input field available to a factor implementation."""

    name: str
    domain: FactorInputDomain
    source_field: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "FactorInputField":
        """Build an input-field declaration from a config mapping."""
        for field in ("name", "domain", "source_field"):
            if field not in payload:
                msg = f"input field is missing required key {field!r}"
                raise FactorDependencyError(msg)

        name = _required_string(payload["name"], "input_fields.name")
        source_field = _required_string(
            payload["source_field"],
            "input_fields.source_field",
        )
        domain = _parse_domain(payload["domain"])
        _reject_label_field(name, "input field name")
        _reject_label_field(source_field, "input source_field")
        return cls(name=name, domain=domain, source_field=source_field)

    def to_dict(self) -> dict[str, str]:
        payload = asdict(self)
        payload["domain"] = self.domain.value
        return payload


def normalize_input_fields(payload: Any) -> tuple[FactorInputField, ...]:
    """Normalize a config value into declared factor input fields."""
    if not isinstance(payload, Sequence) or isinstance(payload, str | bytes):
        msg = "input_fields must be a non-empty sequence of mappings"
        raise FactorDependencyError(msg)
    if not payload:
        msg = "input_fields must contain at least one declared input"
        raise FactorDependencyError(msg)

    fields: list[FactorInputField] = []
    for item in payload:
        if not isinstance(item, Mapping):
            msg = "each input_fields item must be a mapping"
            raise FactorDependencyError(msg)
        fields.append(FactorInputField.from_mapping(item))
    return tuple(fields)


def validate_declared_dependencies(
    input_fields: Sequence[FactorInputField],
    *,
    used_fields: Iterable[str] = (),
) -> None:
    """Validate declarations and reject undeclared implementation inputs."""
    if not input_fields:
        msg = "at least one input field must be declared"
        raise FactorDependencyError(msg)

    names: set[str] = set()
    source_fields: set[str] = set()
    for field in input_fields:
        if field.name in names:
            msg = f"duplicate input field name {field.name!r}"
            raise FactorDependencyError(msg)
        if field.source_field in source_fields:
            msg = f"duplicate input source_field {field.source_field!r}"
            raise FactorDependencyError(msg)
        names.add(field.name)
        source_fields.add(field.source_field)
        _reject_label_field(field.name, "input field name")
        _reject_label_field(field.source_field, "input source_field")

    allowed = names | source_fields
    undeclared = tuple(sorted(field for field in used_fields if field not in allowed))
    if undeclared:
        msg = f"undeclared implementation inputs are not allowed: {', '.join(undeclared)}"
        raise FactorDependencyError(msg)


def looks_like_label_field(value: str) -> bool:
    """Return whether a field name resembles a future label/target field."""
    normalized = value.strip().lower().replace("-", "_")
    if normalized in LABEL_FIELD_TOKENS:
        return True
    if normalized.startswith("label_") or normalized.endswith("_label"):
        return True
    return any(fragment in normalized for fragment in LABEL_NAME_FRAGMENTS)


def _parse_domain(value: Any) -> FactorInputDomain:
    if isinstance(value, FactorInputDomain):
        return value
    if not isinstance(value, str):
        msg = "input field domain must be a string"
        raise FactorDependencyError(msg)
    normalized = value.strip().lower()
    if normalized == "label":
        msg = "label fields must not be declared as factor inputs"
        raise FactorDependencyError(msg)
    try:
        return FactorInputDomain(normalized)
    except ValueError as exc:
        allowed = ", ".join(domain.value for domain in FactorInputDomain)
        msg = f"unsupported factor input domain {value!r}; allowed: {allowed}"
        raise FactorDependencyError(msg) from exc


def _reject_label_field(value: str, description: str) -> None:
    if looks_like_label_field(value):
        msg = f"{description} {value!r} looks like a label field"
        raise FactorDependencyError(msg)


def _required_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        msg = f"{field_name} must be a non-empty string"
        raise FactorDependencyError(msg)
    return value.strip()
