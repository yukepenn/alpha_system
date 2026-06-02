"""Factor compute dependency resolution against canonical bar inputs."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from alpha_system.core.enums import FactorInputDomain
from alpha_system.data.bar_schema import REQUIRED_BAR_FIELDS
from alpha_system.factors.dependency_spec import (
    FactorDependencyError,
    FactorInputField,
    looks_like_label_field,
    validate_declared_dependencies,
)
from alpha_system.factors.spec import FactorSpec
from alpha_system.labels.alignment import LabelAlignmentError, reject_labels_as_factor_inputs


class FactorDependencyResolutionError(ValueError):
    """Raised when compute dependencies are missing or undeclared."""


CANONICAL_BAR_FIELD_SET: frozenset[str] = frozenset(REQUIRED_BAR_FIELDS)


def validate_compute_dependencies(
    spec: FactorSpec,
    *,
    available_columns: Iterable[str] = (),
    used_fields: Iterable[str] = (),
) -> None:
    """Validate that a factor consumes only declared canonical bar columns."""
    try:
        validate_declared_dependencies(spec.input_fields, used_fields=used_fields)
    except FactorDependencyError as exc:
        raise FactorDependencyResolutionError(str(exc)) from exc

    try:
        reject_labels_as_factor_inputs(field.to_dict() for field in spec.input_fields)
    except LabelAlignmentError as exc:
        raise FactorDependencyResolutionError(str(exc)) from exc

    for field in spec.input_fields:
        _validate_bar_input_field(field)

    if available_columns:
        _reject_label_columns(available_columns)
        _reject_ad_hoc_columns(available_columns)
        missing = tuple(
            field.source_field
            for field in spec.input_fields
            if field.source_field not in set(available_columns)
        )
        if missing:
            msg = f"missing declared input columns: {', '.join(missing)}"
            raise FactorDependencyResolutionError(msg)


def select_declared_bar_inputs(
    spec: FactorSpec,
    bar: Mapping[str, Any],
    *,
    used_fields: Iterable[str] = (),
) -> dict[str, Any]:
    """Return only declared inputs from one canonical bar record."""
    validate_compute_dependencies(
        spec,
        available_columns=bar.keys(),
        used_fields=used_fields,
    )
    return {field.name: bar[field.source_field] for field in spec.input_fields}


def declared_source_fields(spec: FactorSpec) -> tuple[str, ...]:
    """Return source columns declared by a factor spec."""
    return tuple(field.source_field for field in spec.input_fields)


def declared_input_names(spec: FactorSpec) -> tuple[str, ...]:
    """Return implementation input names declared by a factor spec."""
    return tuple(field.name for field in spec.input_fields)


def _validate_bar_input_field(field: FactorInputField) -> None:
    if field.domain is not FactorInputDomain.BAR:
        msg = "Factor Compute SDK MVP supports only canonical bar input fields"
        raise FactorDependencyResolutionError(msg)
    if field.source_field not in CANONICAL_BAR_FIELD_SET:
        msg = (
            f"declared input source_field {field.source_field!r} is not in the "
            "canonical 1-minute bar contract"
        )
        raise FactorDependencyResolutionError(msg)
    if looks_like_label_field(field.name) or looks_like_label_field(field.source_field):
        msg = f"label-like field {field.name!r} cannot be a factor input"
        raise FactorDependencyResolutionError(msg)


def _reject_label_columns(columns: Iterable[str]) -> None:
    label_columns = tuple(sorted(column for column in columns if looks_like_label_field(column)))
    if label_columns:
        msg = f"label columns cannot be factor inputs: {', '.join(label_columns)}"
        raise FactorDependencyResolutionError(msg)


def _reject_ad_hoc_columns(columns: Iterable[str]) -> None:
    extra = tuple(sorted(set(columns) - CANONICAL_BAR_FIELD_SET))
    if extra:
        msg = f"undeclared/ad-hoc input columns are not allowed: {', '.join(extra)}"
        raise FactorDependencyResolutionError(msg)
