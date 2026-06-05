"""Provider-agnostic canonical input views for feature and label code.

The public builders accept only an FLF-P01 ``AcceptedDatasetVersion`` handle and
canonical in-memory mappings. They reconstruct canonical records through
``alpha_system.features.consumption`` and expose frozen rows ordered by
``available_ts``.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from alpha_system.data.foundation.bars import CanonicalBarRecord
from alpha_system.data.foundation.datasets import DatasetPartitionPlan
from alpha_system.data.foundation.quotes import (
    BBO_QUARANTINE_QUALITY_FLAG,
    MISSING_BBO_QUALITY_FLAG,
    CanonicalBBORecord,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.features import consumption
from alpha_system.features.consumption import AcceptedDatasetVersion

BBO_QUALITY_FLAG_TOKENS: frozenset[str] = frozenset(
    {
        MISSING_BBO_QUALITY_FLAG,
        BBO_QUARANTINE_QUALITY_FLAG,
    }
)

@dataclass(frozen=True, slots=True)
class OHLCVInputRow:
    """Read-only canonical OHLCV row with explicit timestamp fields."""

    instrument_id: str
    contract_id: str
    series_id: str
    bar_start_ts: datetime
    bar_end_ts: datetime
    event_ts: datetime
    available_ts: datetime
    ingested_at: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    data_version: str
    quality_flags: tuple[str, ...]
    session_label: str


@dataclass(frozen=True, slots=True)
class BBOInputRow:
    """Read-only canonical BBO row with explicit timestamp and quote fields."""

    instrument_id: str
    contract_id: str
    series_id: str
    bar_start_ts: datetime
    bar_end_ts: datetime
    event_ts: datetime
    available_ts: datetime
    ingested_at: datetime
    bid: Decimal
    ask: Decimal
    bid_size: Decimal
    ask_size: Decimal
    mid: Decimal
    spread: Decimal
    data_version: str
    quality_flags: tuple[str, ...]
    session_label: str
    spread_ticks: Decimal | None = None
    microprice: Decimal | None = None
    bid_order_count: int | None = None
    ask_order_count: int | None = None


@dataclass(frozen=True, slots=True)
class OHLCVInputView:
    """Read-only OHLCV view ordered only by canonical ``available_ts``."""

    rows: tuple[OHLCVInputRow, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "rows", _order_by_available_ts(self.rows))

    @property
    def available_timestamps(self) -> tuple[datetime, ...]:
        """Return row availability timestamps in view order."""

        return tuple(row.available_ts for row in self.rows)

    def as_of(self, available_ts: datetime) -> tuple[OHLCVInputRow, ...]:
        """Return rows usable at or before ``available_ts``."""

        cutoff = _require_aware_datetime(available_ts, "available_ts")
        return tuple(row for row in self.rows if row.available_ts <= cutoff)


@dataclass(frozen=True, slots=True)
class BBOInputView:
    """Read-only BBO view ordered only by canonical ``available_ts``."""

    rows: tuple[BBOInputRow, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "rows", _order_by_available_ts(self.rows))

    @property
    def available_timestamps(self) -> tuple[datetime, ...]:
        """Return row availability timestamps in view order."""

        return tuple(row.available_ts for row in self.rows)

    def as_of(self, available_ts: datetime) -> tuple[BBOInputRow, ...]:
        """Return rows usable at or before ``available_ts``."""

        cutoff = _require_aware_datetime(available_ts, "available_ts")
        return tuple(row for row in self.rows if row.available_ts <= cutoff)


@dataclass(frozen=True, slots=True)
class CanonicalInputViews:
    """Aligned canonical OHLCV and BBO views over one accepted DatasetVersion."""

    ohlcv: OHLCVInputView
    bbo: BBOInputView

    def __post_init__(self) -> None:
        if not isinstance(self.ohlcv, OHLCVInputView):
            msg = "ohlcv must be an OHLCVInputView"
            raise DataFoundationValidationError(msg)
        if not isinstance(self.bbo, BBOInputView):
            msg = "bbo must be a BBOInputView"
            raise DataFoundationValidationError(msg)

    @property
    def available_timestamps(self) -> tuple[datetime, ...]:
        """Return the combined availability timeline for both views."""

        return tuple(sorted(set(self.ohlcv.available_timestamps + self.bbo.available_timestamps)))

    def as_of(self, available_ts: datetime) -> CanonicalInputViews:
        """Return OHLCV and BBO rows usable at or before ``available_ts``."""

        cutoff = _require_aware_datetime(available_ts, "available_ts")
        return CanonicalInputViews(
            ohlcv=OHLCVInputView(self.ohlcv.as_of(cutoff)),
            bbo=BBOInputView(self.bbo.as_of(cutoff)),
        )


def build_canonical_input_views(
    accepted_version: AcceptedDatasetVersion,
    *,
    bar_rows: Iterable[Mapping[str, object]],
    bbo_rows: Iterable[Mapping[str, object]],
    partition_id: object,
    purpose: object,
    governance_metadata: Mapping[str, object] | None = None,
    partition_plan: DatasetPartitionPlan | None = None,
) -> CanonicalInputViews:
    """Build aligned OHLCV and BBO views through the FLF-P01 consumption surface."""

    return CanonicalInputViews(
        ohlcv=build_ohlcv_input_view(
            accepted_version,
            bar_rows,
            partition_id=partition_id,
            purpose=purpose,
            governance_metadata=governance_metadata,
            partition_plan=partition_plan,
        ),
        bbo=build_bbo_input_view(
            accepted_version,
            bbo_rows,
            partition_id=partition_id,
            purpose=purpose,
            governance_metadata=governance_metadata,
            partition_plan=partition_plan,
        ),
    )


def build_ohlcv_input_view(
    accepted_version: AcceptedDatasetVersion,
    rows: Iterable[Mapping[str, object]],
    *,
    partition_id: object,
    purpose: object,
    governance_metadata: Mapping[str, object] | None = None,
    partition_plan: DatasetPartitionPlan | None = None,
) -> OHLCVInputView:
    """Build an OHLCV view from canonical mappings for one accepted DatasetVersion."""

    records = consumption.canonical_bars_from_mappings(
        accepted_version,
        rows,
        partition_id=partition_id,
        purpose=purpose,
        governance_metadata=governance_metadata,
        partition_plan=partition_plan,
    )
    return OHLCVInputView(tuple(_ohlcv_row_from_record(record) for record in records))


def build_bbo_input_view(
    accepted_version: AcceptedDatasetVersion,
    rows: Iterable[Mapping[str, object]],
    *,
    partition_id: object,
    purpose: object,
    governance_metadata: Mapping[str, object] | None = None,
    partition_plan: DatasetPartitionPlan | None = None,
) -> BBOInputView:
    """Build a BBO view from canonical mappings for one accepted DatasetVersion."""

    records = consumption.canonical_bbos_from_mappings(
        accepted_version,
        rows,
        partition_id=partition_id,
        purpose=purpose,
        governance_metadata=governance_metadata,
        partition_plan=partition_plan,
    )
    return BBOInputView(tuple(_bbo_row_from_record(record) for record in records))


def _ohlcv_row_from_record(record: CanonicalBarRecord) -> OHLCVInputRow:
    return OHLCVInputRow(
        instrument_id=record.instrument_id,
        contract_id=record.contract_id,
        series_id=record.series_id,
        bar_start_ts=record.bar_start_ts,
        bar_end_ts=record.bar_end_ts,
        event_ts=record.event_ts,
        available_ts=record.available_ts,
        ingested_at=record.ingested_at,
        open=record.open,
        high=record.high,
        low=record.low,
        close=record.close,
        volume=record.volume,
        data_version=record.data_version,
        quality_flags=record.quality_flags,
        session_label=record.session_label,
    )


def _bbo_row_from_record(record: CanonicalBBORecord) -> BBOInputRow:
    return BBOInputRow(
        instrument_id=record.instrument_id,
        contract_id=record.contract_id,
        series_id=record.series_id,
        bar_start_ts=record.bar_start_ts,
        bar_end_ts=record.bar_end_ts,
        event_ts=record.event_ts,
        available_ts=record.available_ts,
        ingested_at=record.ingested_at,
        bid=record.bid,
        ask=record.ask,
        bid_size=record.bid_size,
        ask_size=record.ask_size,
        mid=record.mid,
        spread=record.spread,
        data_version=record.data_version,
        quality_flags=record.quality_flags,
        session_label=record.session_label,
        spread_ticks=record.spread_ticks,
        microprice=record.microprice,
        bid_order_count=record.bid_order_count,
        ask_order_count=record.ask_order_count,
    )


def _order_by_available_ts[InputRowT: (OHLCVInputRow, BBOInputRow)](
    rows: Iterable[InputRowT],
) -> tuple[InputRowT, ...]:
    enumerated = tuple(enumerate(rows))
    for _, row in enumerated:
        _require_aware_datetime(row.available_ts, "available_ts")
    return tuple(
        row
        for _, row in sorted(
            enumerated,
            key=lambda item: (item[1].available_ts, item[0]),
        )
    )


def _require_aware_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        msg = f"{field_name} must be a timezone-aware datetime"
        raise DataFoundationValidationError(msg)
    if value.tzinfo is None or value.utcoffset() is None:
        msg = f"{field_name} must be timezone-aware"
        raise DataFoundationValidationError(msg)
    return value


__all__ = [
    "BBOInputRow",
    "BBOInputView",
    "BBO_QUALITY_FLAG_TOKENS",
    "CanonicalInputViews",
    "OHLCVInputRow",
    "OHLCVInputView",
    "build_bbo_input_view",
    "build_canonical_input_views",
    "build_ohlcv_input_view",
]
