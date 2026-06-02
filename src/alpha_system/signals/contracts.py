"""Signal contract primitives produced from reviewed factor information."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from alpha_system.core.contracts import QualityFlags, VersionMap
from alpha_system.core.enums import Direction


@dataclass(frozen=True, slots=True, kw_only=True)
class SignalRecord:
    signal_id: str
    strategy_id: str
    instrument_id: str
    event_ts: datetime
    available_ts: datetime
    session_id: str
    bar_index: int
    entry_signal: bool
    exit_signal: bool
    direction: Direction
    confidence_score: Decimal | float | None
    desired_exposure: Decimal | float | None
    factor_versions: VersionMap
    data_version: str
    quality_flags: QualityFlags
