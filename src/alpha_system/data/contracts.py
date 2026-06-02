"""Data-layer contract primitives for instruments, sessions, and bars."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from alpha_system.core.contracts import ContractMetadata, QualityFlags
from alpha_system.core.enums import (
    AssetClass,
    CorporateActionPolicy,
    ReadinessState,
    SessionType,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class InstrumentMaster:
    instrument_id: str
    symbol: str
    asset_class: AssetClass
    exchange: str
    currency: str
    timezone: str
    tick_size: Decimal
    lot_size: Decimal
    multiplier: Decimal
    start_date: date
    end_date: date | None
    corporate_action_policy: CorporateActionPolicy
    metadata: ContractMetadata


@dataclass(frozen=True, slots=True, kw_only=True)
class TradingSession:
    calendar_id: str
    trading_date: date
    session_id: str
    open_ts: datetime
    close_ts: datetime
    is_holiday: bool
    is_half_day: bool
    session_type: SessionType
    timezone: str
    quality_flags: QualityFlags


@dataclass(frozen=True, slots=True, kw_only=True)
class OneMinuteBar:
    instrument_id: str
    session_id: str
    bar_index: int
    bar_start_ts: datetime
    bar_end_ts: datetime
    event_ts: datetime
    available_ts: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    vwap: Decimal
    trade_count: int
    bid: Decimal | None
    ask: Decimal | None
    spread: Decimal | None
    source_version: str
    data_version: str
    quality_flags: QualityFlags


@dataclass(frozen=True, slots=True, kw_only=True)
class QuoteTradeReadiness:
    readiness_id: str
    instrument_id: str
    quote_data: ReadinessState
    trade_prints: ReadinessState
    bid_ask_spread: ReadinessState
    executable_labels: ReadinessState
    cost_modeling: ReadinessState
    event_ts: datetime
    available_ts: datetime
    data_version: str
    quality_flags: QualityFlags
