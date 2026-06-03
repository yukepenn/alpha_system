"""ML score output schema and score-to-portfolio contract representation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any


SCORE_SCHEMA_VERSION = "ml_score_output_v1"


class MLOutputError(ValueError):
    """Raised when ML output contracts are invalid."""


@dataclass(frozen=True, slots=True)
class ScoreRecord:
    """One deterministic research score row."""

    run_id: str
    split_id: str
    instrument: str
    decision_ts: str
    score: float
    feature_set_id: str
    model_id: str
    data_version: str
    factor_versions: Mapping[str, str]
    label_version: str
    schema_version: str = SCORE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "run_id", _text(self.run_id, "run_id"))
        object.__setattr__(self, "split_id", _text(self.split_id, "split_id"))
        object.__setattr__(self, "instrument", _text(self.instrument, "instrument"))
        object.__setattr__(self, "decision_ts", _text(self.decision_ts, "decision_ts"))
        object.__setattr__(self, "score", float(self.score))
        object.__setattr__(self, "feature_set_id", _text(self.feature_set_id, "feature_set_id"))
        object.__setattr__(self, "model_id", _text(self.model_id, "model_id"))
        object.__setattr__(self, "data_version", _text(self.data_version, "data_version"))
        object.__setattr__(self, "label_version", _text(self.label_version, "label_version"))
        if not isinstance(self.factor_versions, Mapping) or not self.factor_versions:
            raise MLOutputError("factor_versions must be a non-empty mapping")
        object.__setattr__(
            self,
            "factor_versions",
            {str(key): str(value) for key, value in sorted(self.factor_versions.items())},
        )
        if self.schema_version != SCORE_SCHEMA_VERSION:
            raise MLOutputError(f"unsupported score schema version: {self.schema_version}")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["factor_versions"] = dict(self.factor_versions)
        return payload


@dataclass(frozen=True, slots=True)
class ScoreOutput:
    """Validated collection of score records."""

    records: tuple[ScoreRecord, ...]
    schema_version: str = SCORE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SCORE_SCHEMA_VERSION:
            raise MLOutputError(f"unsupported score schema version: {self.schema_version}")
        object.__setattr__(self, "records", tuple(self.records))
        for record in self.records:
            if record.schema_version != self.schema_version:
                raise MLOutputError("score record schema version mismatch")

    def summary(self) -> dict[str, Any]:
        scores = [record.score for record in self.records]
        return {
            "schema_version": self.schema_version,
            "score_count": len(scores),
            "score_min": min(scores) if scores else None,
            "score_max": max(scores) if scores else None,
            "score_mean": sum(scores) / len(scores) if scores else None,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "records": [record.to_dict() for record in self.records],
        }


@dataclass(frozen=True, slots=True)
class ScoreToPortfolioContract:
    """Contract metadata for a later score-to-portfolio conversion layer."""

    contract_id: str = "score_to_portfolio_contract_v1"
    score_field: str = "score"
    instrument_field: str = "instrument"
    timestamp_field: str = "decision_ts"
    target_role: str = "research_portfolio_target_contract"
    normalization: str = "deferred"
    sizing_implementation: str = "deferred"
    execution_implementation: str = "none"
    constraints: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "contract_id", _text(self.contract_id, "contract_id"))
        object.__setattr__(self, "score_field", _text(self.score_field, "score_field"))
        object.__setattr__(self, "instrument_field", _text(self.instrument_field, "instrument_field"))
        object.__setattr__(self, "timestamp_field", _text(self.timestamp_field, "timestamp_field"))
        object.__setattr__(self, "target_role", _text(self.target_role, "target_role"))
        if self.sizing_implementation != "deferred":
            raise MLOutputError("score-to-portfolio sizing implementation must be deferred")
        if self.execution_implementation != "none":
            raise MLOutputError("score-to-portfolio contract must not implement execution")
        if not isinstance(self.constraints, Mapping):
            raise MLOutputError("score-to-portfolio constraints must be a mapping")
        object.__setattr__(self, "constraints", dict(self.constraints))

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["constraints"] = dict(self.constraints)
        return payload


def validate_score_output_schema(records: Sequence[ScoreRecord]) -> ScoreOutput:
    """Validate score records and return a schema-tagged output object."""
    return ScoreOutput(records=tuple(records))


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MLOutputError(f"{field_name} must be a non-empty string")
    return value.strip()
