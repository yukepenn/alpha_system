"""Shared diagnostic-layer detection statistic evaluation."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from alpha_system.research.study_outputs import DiagnosticSummary
from alpha_system.runtime.diagnostics.power import (
    DEFAULT_IC_MDE_Z_MULTIPLE,
    build_detection_power_report,
)

DETECTION_DIAGNOSTIC = "directional.pearson_ic"
DETECTED = "DETECTED"
NOT_DETECTED = "NOT_DETECTED"
TRUE_ALPHA_DETECTION_THRESHOLD_ABS_PEARSON_IC = 0.95


class DetectionStatisticError(ValueError):
    """Raised when the diagnostic-layer detection statistic is unavailable."""


@dataclass(frozen=True, slots=True)
class DetectionStatisticResult:
    """Value-free threshold result for the shared detection statistic."""

    diagnostic_name: str
    measured_abs_pearson_ic: float
    detection_threshold_abs_pearson_ic: float
    detected: bool
    detection_outcome: str
    detection_power: Mapping[str, Any]

    @property
    def power_statement(self) -> Mapping[str, Any]:
        """Return the stacked power statement for compatibility with report callers."""

        statement = self.detection_power.get("stacked")
        return statement if isinstance(statement, Mapping) else {}

    def to_dict(self) -> dict[str, Any]:
        """Return a stable detection-statistic payload."""

        return {
            "diagnostic_name": self.diagnostic_name,
            "measured_abs_pearson_ic": self.measured_abs_pearson_ic,
            "detection_threshold_abs_pearson_ic": self.detection_threshold_abs_pearson_ic,
            "detected": self.detected,
            "detection_outcome": self.detection_outcome,
            "detection_power": dict(self.detection_power),
        }


def evaluate_detection_statistic(
    summary: DiagnosticSummary | Mapping[str, Any],
    *,
    threshold_abs_pearson_ic: float,
    n_eff: int | None = None,
    per_factor_n_eff: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None = None,
    z_multiple: float = DEFAULT_IC_MDE_Z_MULTIPLE,
) -> DetectionStatisticResult:
    """Evaluate the declared diagnostic-layer |Pearson IC| detection statistic."""

    threshold = _finite_number(
        threshold_abs_pearson_ic,
        field="detection_threshold_abs_pearson_ic",
    )
    measured = abs(_pearson_ic(summary))
    active_n_eff = _n_eff(summary, override=n_eff)
    per_factor_inputs = _per_factor_inputs(summary, active_n_eff, per_factor_n_eff)
    detected = measured >= threshold
    return DetectionStatisticResult(
        diagnostic_name=DETECTION_DIAGNOSTIC,
        measured_abs_pearson_ic=measured,
        detection_threshold_abs_pearson_ic=threshold,
        detected=detected,
        detection_outcome=DETECTED if detected else NOT_DETECTED,
        detection_power=build_detection_power_report(
            stacked_n_eff=active_n_eff,
            per_factor_inputs=per_factor_inputs,
            z_multiple=z_multiple,
        ),
    )


def _pearson_ic(summary: DiagnosticSummary | Mapping[str, Any]) -> float:
    diagnostics = _diagnostics(summary)
    directional = diagnostics.get("directional")
    if not isinstance(directional, Mapping):
        msg = "directional diagnostics are required for detection statistic"
        raise DetectionStatisticError(msg)
    value = directional.get("pearson_ic")
    if isinstance(value, Mapping):
        value = value.get("ic")
    return _finite_number(value, field=DETECTION_DIAGNOSTIC)


def _pearson_ic_payload(summary: DiagnosticSummary | Mapping[str, Any]) -> Mapping[str, Any] | None:
    diagnostics = _diagnostics(summary)
    directional = diagnostics.get("directional")
    if not isinstance(directional, Mapping):
        return None
    value = directional.get("pearson_ic")
    return value if isinstance(value, Mapping) else None


def _n_eff(summary: DiagnosticSummary | Mapping[str, Any], *, override: int | None) -> int:
    if override is not None:
        return _non_negative_int(override, field="n_eff")
    payload = _pearson_ic_payload(summary)
    if payload is not None and "n" in payload:
        return _non_negative_int(payload.get("n"), field=f"{DETECTION_DIAGNOSTIC}.n")
    sample_size = getattr(summary, "sample_size", None)
    if sample_size is None and isinstance(summary, Mapping):
        sample_size = summary.get("sample_size")
    if sample_size is not None:
        return _non_negative_int(sample_size, field="sample_size")
    return 0


def _per_factor_inputs(
    summary: DiagnosticSummary | Mapping[str, Any],
    active_n_eff: int,
    explicit_inputs: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None,
) -> tuple[Mapping[str, Any], ...]:
    if explicit_inputs is not None:
        return _coerce_per_factor_inputs(explicit_inputs)

    factor_id = getattr(summary, "factor_id", None)
    factor_version = getattr(summary, "factor_version", None)
    if isinstance(summary, Mapping):
        factor_id = summary.get("factor_id", factor_id)
        factor_version = summary.get("factor_version", factor_version)
    if factor_id is None:
        return ()
    item: dict[str, Any] = {"factor_id": str(factor_id), "n_eff": active_n_eff}
    if factor_version is not None:
        item["factor_version"] = str(factor_version)
    return (item,)


def _coerce_per_factor_inputs(
    value: Iterable[Mapping[str, Any]] | Mapping[str, Any],
) -> tuple[Mapping[str, Any], ...]:
    if isinstance(value, Mapping):
        if "factor_id" in value or "n_eff" in value:
            return (value,)
        return tuple({"factor_id": str(key), "n_eff": item} for key, item in value.items())
    return tuple(value)


def _diagnostics(summary: DiagnosticSummary | Mapping[str, Any]) -> Mapping[str, Any]:
    if isinstance(summary, DiagnosticSummary):
        return summary.diagnostics
    diagnostics = summary.get("diagnostics")
    if not isinstance(diagnostics, Mapping):
        msg = "diagnostic summary requires a diagnostics mapping"
        raise DetectionStatisticError(msg)
    return diagnostics


def _finite_number(value: Any, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        msg = f"{field} must be a finite number"
        raise DetectionStatisticError(msg)
    active = float(value)
    if not math.isfinite(active):
        msg = f"{field} must be a finite number"
        raise DetectionStatisticError(msg)
    return active


def _non_negative_int(value: Any, *, field: str) -> int:
    if isinstance(value, bool):
        msg = f"{field} must be a non-negative integer"
        raise DetectionStatisticError(msg)
    try:
        active = int(value)
    except (TypeError, ValueError) as exc:
        msg = f"{field} must be a non-negative integer"
        raise DetectionStatisticError(msg) from exc
    if active < 0:
        msg = f"{field} must be a non-negative integer"
        raise DetectionStatisticError(msg)
    return active


__all__ = [
    "DETECTED",
    "DETECTION_DIAGNOSTIC",
    "NOT_DETECTED",
    "TRUE_ALPHA_DETECTION_THRESHOLD_ABS_PEARSON_IC",
    "DetectionStatisticError",
    "DetectionStatisticResult",
    "evaluate_detection_statistic",
]
