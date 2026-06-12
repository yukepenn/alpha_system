"""Shared diagnostic-layer detection statistic evaluation."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from alpha_system.research.study_outputs import DiagnosticSummary

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


def evaluate_detection_statistic(
    summary: DiagnosticSummary | Mapping[str, Any],
    *,
    threshold_abs_pearson_ic: float,
) -> DetectionStatisticResult:
    """Evaluate the declared diagnostic-layer |Pearson IC| detection statistic."""

    threshold = _finite_number(
        threshold_abs_pearson_ic,
        field="detection_threshold_abs_pearson_ic",
    )
    measured = abs(_pearson_ic(summary))
    detected = measured >= threshold
    return DetectionStatisticResult(
        diagnostic_name=DETECTION_DIAGNOSTIC,
        measured_abs_pearson_ic=measured,
        detection_threshold_abs_pearson_ic=threshold,
        detected=detected,
        detection_outcome=DETECTED if detected else NOT_DETECTED,
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


__all__ = [
    "DETECTED",
    "DETECTION_DIAGNOSTIC",
    "NOT_DETECTED",
    "TRUE_ALPHA_DETECTION_THRESHOLD_ABS_PEARSON_IC",
    "DetectionStatisticError",
    "DetectionStatisticResult",
    "evaluate_detection_statistic",
]
