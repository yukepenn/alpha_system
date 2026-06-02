"""Factor contract primitives."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from alpha_system.core.contracts import ConfigParameters, QualityFlags
from alpha_system.core.enums import (
    FactorEvaluationType,
    FactorFrequency,
    FactorInputDomain,
    FactorStatus,
    FactorType,
)

DRAFT_FACTOR_LONG_TERM_MATERIALIZATION_DEFAULT = False


@dataclass(frozen=True, slots=True, kw_only=True)
class FactorInputField:
    name: str
    domain: FactorInputDomain
    source_field: str


@dataclass(frozen=True, slots=True, kw_only=True)
class FactorSpec:
    factor_id: str
    name: str
    version: str
    owner: str
    description: str
    input_fields: tuple[FactorInputField, ...]
    parameters: ConfigParameters
    frequency: FactorFrequency
    warmup_bars: int
    session_reset: bool
    availability_lag: timedelta
    factor_type: FactorType
    evaluation_type: FactorEvaluationType
    code_hash: str
    config_hash: str
    status: FactorStatus
    created_at: datetime
    validation_artifact_path: str | None


@dataclass(frozen=True, slots=True, kw_only=True)
class FactorValue:
    factor_id: str
    factor_version: str
    instrument_id: str
    event_ts: datetime
    available_ts: datetime
    session_id: str
    bar_index: int
    value: Decimal | float | int | str | None
    normalized_value: Decimal | float | int | None
    quality_flags: QualityFlags
    data_version: str
    compute_version: str
