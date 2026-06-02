"""Typed models for factor-card and study-report artifacts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class ReportModelError(ValueError):
    """Raised when report model input is incomplete or unsafe."""


class PromotionRecommendation(StrEnum):
    """Closed advisory recommendation vocabulary for report artifacts."""

    REJECT = "reject"
    NEEDS_MORE_DATA = "needs_more_data"
    CANDIDATE_FOR_STRATEGY_TEST = "candidate_for_strategy_test"
    CANDIDATE_FOR_REVIEW = "candidate_for_review"
    DO_NOT_PROMOTE = "do_not_promote"

    @classmethod
    def parse(cls, value: str | "PromotionRecommendation") -> "PromotionRecommendation":
        """Parse and validate a closed-set recommendation value."""
        if isinstance(value, PromotionRecommendation):
            return value
        try:
            return cls(str(value).strip())
        except ValueError as exc:
            allowed = ", ".join(sorted(item.value for item in cls))
            msg = f"promotion recommendation must be one of: {allowed}"
            raise ReportModelError(msg) from exc


ALLOWED_PROMOTION_RECOMMENDATIONS: tuple[str, ...] = tuple(
    item.value for item in PromotionRecommendation
)


@dataclass(frozen=True, slots=True)
class ReportMetadata:
    """Reproducibility and review metadata rendered on every report."""

    factor_id: str
    label_id: str
    data_version: str
    factor_version: str
    label_version: str
    run_manifest_path: str
    code_hash_ref: str = "not_available"
    config_hash_ref: str = "not_available"
    diagnostic_run_id: str = "not_available"
    diagnostic_engine_version: str = "not_available"
    no_lookahead_validation_status: str = "not_recorded"
    review_status: str = "not_reviewed"
    factor_label_alignment_status: str = "reported_not_verified"

    def __post_init__(self) -> None:
        required = {
            "factor_id": self.factor_id,
            "label_id": self.label_id,
            "data_version": self.data_version,
            "factor_version": self.factor_version,
            "label_version": self.label_version,
            "run_manifest_path": self.run_manifest_path,
            "no_lookahead_validation_status": self.no_lookahead_validation_status,
            "review_status": self.review_status,
        }
        missing = tuple(name for name, value in required.items() if not _text(value))
        if missing:
            msg = f"report metadata missing required fields: {', '.join(missing)}"
            raise ReportModelError(msg)

    def to_dict(self) -> dict[str, str]:
        """Return a stable dictionary representation."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ReportWarning:
    """A normalized report warning."""

    code: str
    message: str
    severity: str = "warning"

    def __post_init__(self) -> None:
        if not _text(self.code) or not _text(self.message):
            msg = "report warnings require non-empty code and message"
            raise ReportModelError(msg)

    def to_dict(self) -> dict[str, str]:
        """Return a stable dictionary representation."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class StabilitySections:
    """Required stability sections for report artifacts."""

    time_of_day: Mapping[str, Any] = field(default_factory=dict)
    session_segment: Mapping[str, Any] = field(default_factory=dict)
    monthly: Mapping[str, Any] = field(default_factory=dict)
    volatility_regime: Mapping[str, Any] = field(default_factory=dict)
    liquidity_regime: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return required stability sections with deterministic key order."""
        return {
            "time_of_day": _stable_mapping(self.time_of_day),
            "session_segment": _stable_mapping(self.session_segment),
            "monthly": _stable_mapping(self.monthly),
            "volatility_regime": _stable_mapping(self.volatility_regime),
            "liquidity_regime": _stable_mapping(self.liquidity_regime),
        }


@dataclass(frozen=True, slots=True)
class FactorCardReport:
    """Complete factor-card report model."""

    metadata: ReportMetadata
    stability: StabilitySections
    correlation_to_existing_factors: Mapping[str, Any]
    factor_cluster_id: str
    promotion_recommendation: PromotionRecommendation
    sample_size: int
    warnings: tuple[ReportWarning, ...]
    diagnostic_summary: Mapping[str, Any]
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.sample_size < 0:
            msg = "sample_size must be non-negative"
            raise ReportModelError(msg)
        if not _text(self.factor_cluster_id):
            msg = "factor_cluster_id must be represented"
            raise ReportModelError(msg)
        if not self.limitations:
            msg = "factor card requires at least one limitation"
            raise ReportModelError(msg)
        object.__setattr__(
            self,
            "promotion_recommendation",
            PromotionRecommendation.parse(self.promotion_recommendation),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a stable dictionary representation."""
        return {
            "metadata": self.metadata.to_dict(),
            "stability": self.stability.to_dict(),
            "correlation_to_existing_factors": _stable_mapping(
                self.correlation_to_existing_factors
            ),
            "factor_cluster_id": self.factor_cluster_id,
            "promotion_recommendation": self.promotion_recommendation.value,
            "sample_size": self.sample_size,
            "warnings": [warning.to_dict() for warning in self.warnings],
            "diagnostic_summary": _stable_mapping(self.diagnostic_summary),
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True, slots=True)
class StudyFactorSummary:
    """Compact per-factor summary for study reports."""

    factor_id: str
    factor_version: str
    label_version: str
    data_version: str
    sample_size: int
    promotion_recommendation: PromotionRecommendation
    warning_count: int
    no_lookahead_validation_status: str
    review_status: str

    def __post_init__(self) -> None:
        if self.sample_size < 0 or self.warning_count < 0:
            msg = "study factor summary counts must be non-negative"
            raise ReportModelError(msg)
        object.__setattr__(
            self,
            "promotion_recommendation",
            PromotionRecommendation.parse(self.promotion_recommendation),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a stable dictionary representation."""
        return {
            "factor_id": self.factor_id,
            "factor_version": self.factor_version,
            "label_version": self.label_version,
            "data_version": self.data_version,
            "sample_size": self.sample_size,
            "promotion_recommendation": self.promotion_recommendation.value,
            "warning_count": self.warning_count,
            "no_lookahead_validation_status": self.no_lookahead_validation_status,
            "review_status": self.review_status,
        }


@dataclass(frozen=True, slots=True)
class StudyReport:
    """Study report over one or more factor cards."""

    study_id: str
    factor_summaries: tuple[StudyFactorSummary, ...]
    factor_cards: tuple[FactorCardReport, ...]
    warnings: tuple[ReportWarning, ...]
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        if not _text(self.study_id):
            msg = "study_id must be non-empty"
            raise ReportModelError(msg)
        if not self.factor_summaries or not self.factor_cards:
            msg = "study report requires at least one factor"
            raise ReportModelError(msg)
        if len(self.factor_summaries) != len(self.factor_cards):
            msg = "study report factor summaries and cards must align"
            raise ReportModelError(msg)
        if not self.limitations:
            msg = "study report requires at least one limitation"
            raise ReportModelError(msg)

    def to_dict(self) -> dict[str, Any]:
        """Return a stable dictionary representation."""
        return {
            "study_id": self.study_id,
            "factor_summaries": [item.to_dict() for item in self.factor_summaries],
            "factor_cards": [card.to_dict() for card in self.factor_cards],
            "warnings": [warning.to_dict() for warning in self.warnings],
            "limitations": list(self.limitations),
        }


def advisory_recommendation_note() -> str:
    """Return the fixed report note that separates recommendations from decisions."""
    return (
        "Recommendation is advisory research guidance only; registry status changes "
        "require a separate reviewed action."
    )


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _stable_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    items = sorted(((str(key), active_value) for key, active_value in value.items()))
    return {key: _stable_value(active_value) for key, active_value in items}


def _stable_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _stable_mapping(value)
    if isinstance(value, (tuple, list)):
        return [_stable_value(item) for item in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value
