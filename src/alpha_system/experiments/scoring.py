"""Deterministic MVP scoring for ML/factor-combination experiments."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

from alpha_system.experiments.feature_sets import FeatureSetSpec, LabelSpec
from alpha_system.experiments.ml_outputs import ScoreOutput, ScoreRecord
from alpha_system.experiments.model_specs import ModelSpec, ModelSpecError


class ScoringError(ValueError):
    """Raised when deterministic ML scoring cannot proceed."""


@dataclass(frozen=True, slots=True)
class LinearBaselineFit:
    """Deterministic linear/ridge-style fitted score skeleton."""

    model_id: str
    model_type: str
    feature_ids: tuple[str, ...]
    weights: Mapping[str, float]
    intercept: float
    training_row_count: int

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["weights"] = dict(self.weights)
        return payload


def fit_linear_baseline(
    model_spec: ModelSpec,
    rows: Sequence[Mapping[str, Any]],
    labels: Sequence[Any],
    feature_ids: Sequence[str],
) -> LinearBaselineFit:
    """Fit a deterministic covariance-weighted linear baseline."""
    try:
        model_spec.require_executable()
    except ModelSpecError as exc:
        raise ScoringError(str(exc)) from exc
    if model_spec.model_type not in {"linear_baseline", "ridge_baseline", "ic_weighted_score"}:
        raise ScoringError(f"model type has no MVP scoring path: {model_spec.model_type}")
    if not rows:
        raise ScoringError("at least one training row is required")
    if len(rows) != len(labels):
        raise ScoringError("training rows and labels must have equal length")
    feature_ids = tuple(_text(feature_id, "feature_id") for feature_id in feature_ids)
    if not feature_ids:
        raise ScoringError("at least one feature id is required")

    y = [_float(label, "label") for label in labels]
    y_mean = sum(y) / len(y)
    centered_y = [value - y_mean for value in y]
    ridge_l2 = model_spec.ridge_l2
    means: dict[str, float] = {}
    weights: dict[str, float] = {}
    for feature_id in feature_ids:
        x = [_float(row.get(feature_id), feature_id) for row in rows]
        x_mean = sum(x) / len(x)
        means[feature_id] = x_mean
        centered_x = [value - x_mean for value in x]
        numerator = sum(a * b for a, b in zip(centered_x, centered_y, strict=True))
        denominator = sum(value * value for value in centered_x) + ridge_l2
        weights[feature_id] = 0.0 if denominator == 0 else numerator / denominator

    if model_spec.model_type == "ic_weighted_score":
        gross = sum(abs(weight) for weight in weights.values())
        if gross > 0:
            weights = {feature_id: weight / gross for feature_id, weight in weights.items()}

    intercept = 0.0
    if model_spec.fit_intercept:
        intercept = y_mean - sum(weights[feature_id] * means[feature_id] for feature_id in feature_ids)

    return LinearBaselineFit(
        model_id=model_spec.model_id,
        model_type=model_spec.model_type,
        feature_ids=feature_ids,
        weights=dict(sorted(weights.items())),
        intercept=intercept,
        training_row_count=len(rows),
    )


def score_rows(
    fit: LinearBaselineFit,
    rows: Sequence[Mapping[str, Any]],
    *,
    run_id: str,
    split_id: str,
    feature_set: FeatureSetSpec,
    label_spec: LabelSpec,
) -> ScoreOutput:
    """Score validation rows with a deterministic fitted baseline."""
    records: list[ScoreRecord] = []
    for row_number, row in enumerate(rows):
        score = fit.intercept
        for feature_id in fit.feature_ids:
            score += fit.weights[feature_id] * _float(row.get(feature_id), feature_id)
        records.append(
            ScoreRecord(
                run_id=run_id,
                split_id=split_id,
                instrument=str(row.get("instrument", f"row_{row_number}")),
                decision_ts=str(row.get(label_spec.decision_ts_field)),
                score=score,
                feature_set_id=feature_set.feature_set_id,
                model_id=fit.model_id,
                data_version=feature_set.data_version,
                factor_versions=feature_set.factor_versions,
                label_version=label_spec.label_version,
            )
        )
    return ScoreOutput(records=tuple(records))


def combine_score_outputs(outputs: Sequence[ScoreOutput]) -> ScoreOutput:
    """Combine fold-level score outputs without changing schema."""
    records: list[ScoreRecord] = []
    for output in outputs:
        records.extend(output.records)
    return ScoreOutput(records=tuple(records))


def _float(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or value is None:
        raise ScoringError(f"{field_name} must be numeric")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ScoringError(f"{field_name} must be numeric") from exc


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ScoringError(f"{field_name} must be a non-empty string")
    return value.strip()
