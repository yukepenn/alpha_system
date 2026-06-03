"""Validation guards for fixture-only L2-derived feature skeletons."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

from alpha_system.core.enums import FactorInputDomain, FactorStatus
from alpha_system.factors.base import FactorValue
from alpha_system.factors.dependency_spec import looks_like_label_field


SYNTHETIC_L2_DATA_VERSION_PREFIX = "l2:synthetic:"
L2_FEATURE_DESIGN_SCOPE = "fixture_only_design"
L2_FEATURE_MATERIALIZATION_DEFAULT = False


class L2FeatureValidationError(ValueError):
    """Raised when L2 feature skeleton inputs violate phase constraints."""


class L2FeatureMaterializationError(ValueError):
    """Raised when callers request L2 feature materialization in this skeleton."""


def require_synthetic_l2_feature_inputs(
    records: Iterable[Mapping[str, Any]],
) -> tuple[Mapping[str, Any], ...]:
    """Return L2 rows after enforcing synthetic fixture-only input scope."""
    materialized = tuple(records)
    if not materialized:
        msg = "L2-derived feature skeleton requires at least one synthetic fixture row"
        raise L2FeatureValidationError(msg)

    reject_label_like_l2_feature_inputs(materialized)
    for index, record in enumerate(materialized):
        data_version = str(record.get("data_version", ""))
        if not data_version.startswith(SYNTHETIC_L2_DATA_VERSION_PREFIX):
            msg = (
                "L2-derived feature skeleton accepts only synthetic fixture data "
                f"versions prefixed by {SYNTHETIC_L2_DATA_VERSION_PREFIX!r}; "
                f"row {index} has {data_version!r}"
            )
            raise L2FeatureValidationError(msg)
    return materialized


def reject_label_like_l2_feature_inputs(
    records: Iterable[Mapping[str, Any]],
) -> None:
    """Fail closed when labels or label availability appear in feature inputs."""
    for row_index, record in enumerate(records):
        for field in record:
            if looks_like_label_field(str(field)):
                msg = (
                    "labels and label_available_ts values are not valid inputs "
                    f"to L2-derived features; row {row_index} contains {field!r}"
                )
                raise L2FeatureValidationError(msg)


def assert_l2_feature_available(value: FactorValue, *, as_of: datetime) -> None:
    """Raise when a derived feature is read before its available_ts."""
    if as_of < value.available_ts:
        msg = (
            "L2-derived feature value is not available before available_ts "
            f"{value.available_ts.isoformat()}"
        )
        raise L2FeatureValidationError(msg)


def validate_l2_feature_declarations(declarations: Iterable[Any]) -> None:
    """Validate design-scope declarations without registering or materializing."""
    materialized = tuple(declarations)
    if not materialized:
        msg = "at least one L2 feature declaration is required"
        raise L2FeatureValidationError(msg)

    for declaration in materialized:
        factor_spec = getattr(declaration, "factor_spec", None)
        if factor_spec is None:
            msg = "L2 feature declaration must expose a factor_spec"
            raise L2FeatureValidationError(msg)

        if getattr(declaration, "design_scope", None) != L2_FEATURE_DESIGN_SCOPE:
            msg = "L2 feature declarations must remain fixture_only_design scope"
            raise L2FeatureValidationError(msg)
        if getattr(declaration, "fixture_only", None) is not True:
            msg = "L2 feature declarations must be fixture-only"
            raise L2FeatureValidationError(msg)
        if getattr(declaration, "materialize_by_default", None) is not False:
            msg = "L2 feature declarations must not materialize by default"
            raise L2FeatureValidationError(msg)

        if factor_spec.status is not FactorStatus.DRAFT:
            msg = "L2 feature FactorSpec entries must remain draft in this phase"
            raise L2FeatureValidationError(msg)
        if factor_spec.validation_artifact_path is not None:
            msg = "draft L2 feature FactorSpec entries must not carry validation artifacts"
            raise L2FeatureValidationError(msg)
        for field in factor_spec.input_fields:
            if field.domain is not FactorInputDomain.L2:
                msg = "L2 feature FactorSpec inputs must use the l2 domain"
                raise L2FeatureValidationError(msg)
            if looks_like_label_field(field.name) or looks_like_label_field(
                field.source_field
            ):
                msg = "L2 feature FactorSpec inputs must not reference labels"
                raise L2FeatureValidationError(msg)


def l2_feature_materialization_enabled_by_default() -> bool:
    """Return the phase-level materialization default for L2-derived features."""
    return L2_FEATURE_MATERIALIZATION_DEFAULT


def require_no_l2_feature_materialization_request(
    *,
    output_path: str | Path | None = None,
    persist: bool = False,
) -> None:
    """Reject any request to persist L2-derived feature values in ASV1-P26."""
    if persist or output_path is not None:
        msg = (
            "ASV1-P26 L2-derived feature skeleton is design/fixture-only and "
            "does not materialize feature values or write factor stores"
        )
        raise L2FeatureMaterializationError(msg)
