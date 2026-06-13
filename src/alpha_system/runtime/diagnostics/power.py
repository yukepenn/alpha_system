"""Pure-Python IC detection-power reporting helpers."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from typing import Any, cast

from alpha_system.governance.serialization import JsonValue

IC_POWER_STATEMENT_SCHEMA = "alpha_system.runtime.diagnostics.ic_power_statement.v1"
IC_POWER_REPORT_SCHEMA = "alpha_system.runtime.diagnostics.ic_power_report.v1"
DEFAULT_IC_MDE_Z_MULTIPLE = 1.96
IC_POWER_ESTIMATOR_FORMULA = "SE(IC) ~= 1 / sqrt(N_eff - 1); MDE(|IC|) = z_multiple * SE(IC)"


class ICPowerStatementError(ValueError):
    """Raised when IC power reporting inputs are invalid."""


def estimate_ic_standard_error(n_eff: int | float) -> float | None:
    """Return first-order SE(IC), or ``None`` when N_eff cannot support it."""

    active_n_eff = _non_negative_int(n_eff, "n_eff")
    if active_n_eff <= 1:
        return None
    return 1.0 / math.sqrt(active_n_eff - 1)


def minimum_detectable_abs_ic(
    n_eff: int | float,
    *,
    z_multiple: float = DEFAULT_IC_MDE_Z_MULTIPLE,
) -> float | None:
    """Return the first-order minimum detectable absolute IC."""

    se_ic = estimate_ic_standard_error(n_eff)
    if se_ic is None:
        return None
    return _positive_finite(z_multiple, "z_multiple") * se_ic


def build_ic_power_statement(
    *,
    n_eff: int | float,
    z_multiple: float = DEFAULT_IC_MDE_Z_MULTIPLE,
    scope: str = "stacked",
    factor_id: str | None = None,
    factor_version: str | None = None,
) -> dict[str, JsonValue]:
    """Build a deterministic, value-free IC detection-power statement."""

    active_n_eff = _non_negative_int(n_eff, "n_eff")
    active_z = _positive_finite(z_multiple, "z_multiple")
    active_scope = _text(scope, "scope")
    active_factor_id = None if factor_id is None else _text(factor_id, "factor_id")
    active_factor_version = (
        None if factor_version is None else _text(factor_version, "factor_version")
    )
    se_ic = estimate_ic_standard_error(active_n_eff)
    mde_abs_ic = None if se_ic is None else active_z * se_ic

    payload: dict[str, JsonValue] = {
        "schema": IC_POWER_STATEMENT_SCHEMA,
        "scope": active_scope,
        "n_eff": active_n_eff,
        "se_ic": se_ic,
        "mde_abs_ic": mde_abs_ic,
        "z_multiple": active_z,
        "estimator_formula": IC_POWER_ESTIMATOR_FORMULA,
        "statement": _statement(n_eff=active_n_eff, mde_abs_ic=mde_abs_ic, z_multiple=active_z),
        "statistical_validity_claim": False,
    }
    if active_factor_id is not None:
        payload["factor_id"] = active_factor_id
    if active_factor_version is not None:
        payload["factor_version"] = active_factor_version
    return payload


def build_detection_power_report(
    *,
    stacked_n_eff: int | float,
    per_factor_inputs: Iterable[Mapping[str, Any]] = (),
    z_multiple: float = DEFAULT_IC_MDE_Z_MULTIPLE,
) -> dict[str, JsonValue]:
    """Build stacked and per-factor IC power statements."""

    active_z = _positive_finite(z_multiple, "z_multiple")
    per_factor = [
        build_ic_power_statement(
            n_eff=item.get("n_eff"),
            z_multiple=active_z,
            scope="per_factor",
            factor_id=cast(str | None, item.get("factor_id")),
            factor_version=cast(str | None, item.get("factor_version")),
        )
        for item in per_factor_inputs
    ]
    return {
        "schema": IC_POWER_REPORT_SCHEMA,
        "stacked": build_ic_power_statement(
            n_eff=stacked_n_eff,
            z_multiple=active_z,
            scope="stacked",
        ),
        "per_factor": per_factor,
        "statistical_validity_claim": False,
    }


def _statement(*, n_eff: int, mde_abs_ic: float | None, z_multiple: float) -> str:
    if mde_abs_ic is None:
        return (
            "Could have detected IC down to unresolved at "
            f"N_eff = {n_eff}; SE(IC) requires N_eff > 1."
        )
    return (
        f"Could have detected IC down to {mde_abs_ic:.6f} at "
        f"N_eff = {n_eff} using z = {z_multiple:.6f}."
    )


def _non_negative_int(value: object, field: str) -> int:
    if isinstance(value, bool):
        raise ICPowerStatementError(f"{field} must be a non-negative integer")
    try:
        number = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ICPowerStatementError(f"{field} must be a non-negative integer") from exc
    if number < 0:
        raise ICPowerStatementError(f"{field} must be a non-negative integer")
    return number


def _positive_finite(value: object, field: str) -> float:
    if isinstance(value, bool):
        raise ICPowerStatementError(f"{field} must be a positive finite number")
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ICPowerStatementError(f"{field} must be a positive finite number") from exc
    if not math.isfinite(number) or number <= 0:
        raise ICPowerStatementError(f"{field} must be a positive finite number")
    return number


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ICPowerStatementError(f"{field} must be non-empty text")
    return value.strip()


__all__ = [
    "DEFAULT_IC_MDE_Z_MULTIPLE",
    "IC_POWER_ESTIMATOR_FORMULA",
    "IC_POWER_REPORT_SCHEMA",
    "IC_POWER_STATEMENT_SCHEMA",
    "ICPowerStatementError",
    "build_detection_power_report",
    "build_ic_power_statement",
    "estimate_ic_standard_error",
    "minimum_detectable_abs_ic",
]
