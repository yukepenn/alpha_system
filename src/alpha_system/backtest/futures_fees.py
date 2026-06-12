"""Versioned public futures fee schedules for local research cost models."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Final


PLACEHOLDER_FEE_SCHEDULE_VERSION_ID: Final = "fee_schedule_futcore_pilot_placeholder_v1"
REAL_FEE_SCHEDULE_VERSION_ID: Final = (
    "fee_schedule_cme_equity_index_retail_discount_v2_2026_06_11"
)
ACTIVE_FEE_SCHEDULE_VERSION_ID: Final = REAL_FEE_SCHEDULE_VERSION_ID

# Source citation for ES: CME Group public Equity Index futures fee schedule,
# CME Globex non-member E-mini S&P 500 futures exchange fee, offline as-of
# 2026-06-11; verify before any paper/live/broker use.
ES_CME_EXCHANGE_FEE_PER_SIDE: Final = Decimal("1.38")
# Source citation for ES: CME Group public clearing/transaction fee table for
# Equity Index futures, clearing fee line item observed as zero in the public
# retail-facing schedules used here, offline as-of 2026-06-11.
ES_CME_CLEARING_FEE_PER_SIDE: Final = Decimal("0.00")
# Source citation for ES: NFA public assessment fee schedule, futures contracts
# assessment fee of $0.02 per side, offline as-of 2026-06-11.
ES_NFA_REGULATORY_FEE_PER_SIDE: Final = Decimal("0.02")
# Source citation for ES: representative public retail discount futures broker
# commission tier for E-mini equity index futures, offline as-of 2026-06-11;
# not account-specific and not a broker recommendation.
ES_RETAIL_DISCOUNT_BROKER_COMMISSION_PER_SIDE: Final = Decimal("0.59")

# Source citation for NQ: CME Group public Equity Index futures fee schedule,
# CME Globex non-member E-mini Nasdaq-100 futures exchange fee, offline as-of
# 2026-06-11; verify before any paper/live/broker use.
NQ_CME_EXCHANGE_FEE_PER_SIDE: Final = Decimal("1.38")
# Source citation for NQ: CME Group public clearing/transaction fee table for
# Equity Index futures, clearing fee line item observed as zero in the public
# retail-facing schedules used here, offline as-of 2026-06-11.
NQ_CME_CLEARING_FEE_PER_SIDE: Final = Decimal("0.00")
# Source citation for NQ: NFA public assessment fee schedule, futures contracts
# assessment fee of $0.02 per side, offline as-of 2026-06-11.
NQ_NFA_REGULATORY_FEE_PER_SIDE: Final = Decimal("0.02")
# Source citation for NQ: representative public retail discount futures broker
# commission tier for E-mini equity index futures, offline as-of 2026-06-11;
# not account-specific and not a broker recommendation.
NQ_RETAIL_DISCOUNT_BROKER_COMMISSION_PER_SIDE: Final = Decimal("0.59")

# Source citation for RTY: CME Group public Equity Index futures fee schedule,
# CME Globex non-member E-mini Russell 2000 futures exchange fee, offline as-of
# 2026-06-11; verify before any paper/live/broker use.
RTY_CME_EXCHANGE_FEE_PER_SIDE: Final = Decimal("1.38")
# Source citation for RTY: CME Group public clearing/transaction fee table for
# Equity Index futures, clearing fee line item observed as zero in the public
# retail-facing schedules used here, offline as-of 2026-06-11.
RTY_CME_CLEARING_FEE_PER_SIDE: Final = Decimal("0.00")
# Source citation for RTY: NFA public assessment fee schedule, futures contracts
# assessment fee of $0.02 per side, offline as-of 2026-06-11.
RTY_NFA_REGULATORY_FEE_PER_SIDE: Final = Decimal("0.02")
# Source citation for RTY: representative public retail discount futures broker
# commission tier for E-mini equity index futures, offline as-of 2026-06-11;
# not account-specific and not a broker recommendation.
RTY_RETAIL_DISCOUNT_BROKER_COMMISSION_PER_SIDE: Final = Decimal("0.59")

# Source citation for MES: CME Group public Micro E-mini Equity Index futures
# fee schedule, CME Globex non-member exchange fee, offline as-of 2026-06-11;
# verify before any paper/live/broker use.
MES_CME_EXCHANGE_FEE_PER_SIDE: Final = Decimal("0.25")
# Source citation for MES: CME Group public clearing/transaction fee table for
# Micro E-mini Equity Index futures, clearing fee line item observed as zero in
# the public retail-facing schedules used here, offline as-of 2026-06-11.
MES_CME_CLEARING_FEE_PER_SIDE: Final = Decimal("0.00")
# Source citation for MES: NFA public assessment fee schedule, futures contracts
# assessment fee of $0.02 per side, offline as-of 2026-06-11.
MES_NFA_REGULATORY_FEE_PER_SIDE: Final = Decimal("0.02")
# Source citation for MES: representative public retail discount futures broker
# commission tier for Micro E-mini equity index futures, offline as-of
# 2026-06-11; not account-specific and not a broker recommendation.
MES_RETAIL_DISCOUNT_BROKER_COMMISSION_PER_SIDE: Final = Decimal("0.09")

# Source citation for MNQ: CME Group public Micro E-mini Equity Index futures
# fee schedule, CME Globex non-member exchange fee, offline as-of 2026-06-11;
# verify before any paper/live/broker use.
MNQ_CME_EXCHANGE_FEE_PER_SIDE: Final = Decimal("0.25")
# Source citation for MNQ: CME Group public clearing/transaction fee table for
# Micro E-mini Equity Index futures, clearing fee line item observed as zero in
# the public retail-facing schedules used here, offline as-of 2026-06-11.
MNQ_CME_CLEARING_FEE_PER_SIDE: Final = Decimal("0.00")
# Source citation for MNQ: NFA public assessment fee schedule, futures contracts
# assessment fee of $0.02 per side, offline as-of 2026-06-11.
MNQ_NFA_REGULATORY_FEE_PER_SIDE: Final = Decimal("0.02")
# Source citation for MNQ: representative public retail discount futures broker
# commission tier for Micro E-mini equity index futures, offline as-of
# 2026-06-11; not account-specific and not a broker recommendation.
MNQ_RETAIL_DISCOUNT_BROKER_COMMISSION_PER_SIDE: Final = Decimal("0.09")

# Source citation for M2K: CME Group public Micro E-mini Equity Index futures
# fee schedule, CME Globex non-member exchange fee, offline as-of 2026-06-11;
# verify before any paper/live/broker use.
M2K_CME_EXCHANGE_FEE_PER_SIDE: Final = Decimal("0.25")
# Source citation for M2K: CME Group public clearing/transaction fee table for
# Micro E-mini Equity Index futures, clearing fee line item observed as zero in
# the public retail-facing schedules used here, offline as-of 2026-06-11.
M2K_CME_CLEARING_FEE_PER_SIDE: Final = Decimal("0.00")
# Source citation for M2K: NFA public assessment fee schedule, futures contracts
# assessment fee of $0.02 per side, offline as-of 2026-06-11.
M2K_NFA_REGULATORY_FEE_PER_SIDE: Final = Decimal("0.02")
# Source citation for M2K: representative public retail discount futures broker
# commission tier for Micro E-mini equity index futures, offline as-of
# 2026-06-11; not account-specific and not a broker recommendation.
M2K_RETAIL_DISCOUNT_BROKER_COMMISSION_PER_SIDE: Final = Decimal("0.09")


class FuturesFeeScheduleError(ValueError):
    """Raised when a futures fee schedule is missing or malformed."""


@dataclass(frozen=True, slots=True)
class FuturesFeeScheduleEntry:
    """One symbol's hard fees, in USD per contract per side."""

    symbol: str
    cme_exchange_fee: Decimal
    cme_clearing_fee: Decimal
    nfa_regulatory_fee: Decimal
    retail_discount_broker_commission: Decimal

    @property
    def all_in_per_side(self) -> Decimal:
        """Return exchange + clearing + NFA + broker commission."""

        return (
            self.cme_exchange_fee
            + self.cme_clearing_fee
            + self.nfa_regulatory_fee
            + self.retail_discount_broker_commission
        )

    def component_amounts(self) -> tuple[tuple[str, Decimal], ...]:
        """Return stable named fee components for cost breakdowns."""

        symbol = self.symbol
        return (
            (f"{symbol}_cme_exchange_fee", self.cme_exchange_fee),
            (f"{symbol}_cme_clearing_fee", self.cme_clearing_fee),
            (f"{symbol}_nfa_regulatory_fee", self.nfa_regulatory_fee),
            (
                f"{symbol}_retail_discount_broker_commission",
                self.retail_discount_broker_commission,
            ),
        )

    def to_dict(self) -> dict[str, str]:
        """Return a stable JSON-compatible entry payload."""

        return {
            "symbol": self.symbol,
            "cme_exchange_fee": _decimal_text(self.cme_exchange_fee),
            "cme_clearing_fee": _decimal_text(self.cme_clearing_fee),
            "nfa_regulatory_fee": _decimal_text(self.nfa_regulatory_fee),
            "retail_discount_broker_commission": _decimal_text(
                self.retail_discount_broker_commission
            ),
            "all_in_per_side": _decimal_text(self.all_in_per_side),
        }


@dataclass(frozen=True, slots=True)
class FuturesFeeScheduleVersion:
    """Immutable fee schedule version for futures hard-cost components."""

    version_id: str
    semantic_version: str
    as_of_date: str
    source_summary: str
    currency: str
    entries: tuple[FuturesFeeScheduleEntry, ...]
    default_symbol: str = "ES"
    placeholder: bool = False

    def __post_init__(self) -> None:
        symbols = tuple(entry.symbol for entry in self.entries)
        if len(set(symbols)) != len(symbols):
            raise FuturesFeeScheduleError("fee schedule contains duplicate symbols")
        if not self.placeholder and self.default_symbol not in symbols:
            raise FuturesFeeScheduleError("default symbol must exist in fee schedule")

    @property
    def symbols(self) -> tuple[str, ...]:
        """Return symbols covered by this schedule."""

        return tuple(entry.symbol for entry in self.entries)

    def entry_for_symbol(self, symbol: str | None) -> FuturesFeeScheduleEntry:
        """Return the normalized schedule entry for a symbol."""

        active_symbol = self.default_symbol if symbol is None else _normalize_symbol(symbol)
        for entry in self.entries:
            if entry.symbol == active_symbol:
                return entry
        raise FuturesFeeScheduleError(
            f"fee schedule {self.version_id} does not cover symbol {active_symbol}"
        )

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-compatible schedule payload."""

        return {
            "version_id": self.version_id,
            "semantic_version": self.semantic_version,
            "as_of_date": self.as_of_date,
            "source_summary": self.source_summary,
            "currency": self.currency,
            "default_symbol": self.default_symbol,
            "placeholder": self.placeholder,
            "entries": [entry.to_dict() for entry in self.entries],
        }


PLACEHOLDER_FEE_SCHEDULE: Final = FuturesFeeScheduleVersion(
    version_id=PLACEHOLDER_FEE_SCHEDULE_VERSION_ID,
    semantic_version="1.0.0",
    as_of_date="2026-06-07",
    source_summary=(
        "FUTCORE-P04 symbolic Layer-1 placeholder retained for history only; "
        "no fee amounts are usable from this version."
    ),
    currency="USD",
    entries=(),
    default_symbol="ES",
    placeholder=True,
)

REAL_FEE_SCHEDULE: Final = FuturesFeeScheduleVersion(
    version_id=REAL_FEE_SCHEDULE_VERSION_ID,
    semantic_version="2.0.0",
    as_of_date="2026-06-11",
    source_summary=(
        "Offline public-source schedule: CME Group Equity Index futures fee "
        "tables, NFA futures assessment fee schedule, and a representative "
        "public retail discount broker commission tier; research constants "
        "only, not account-specific."
    ),
    currency="USD",
    entries=(
        FuturesFeeScheduleEntry(
            symbol="ES",
            cme_exchange_fee=ES_CME_EXCHANGE_FEE_PER_SIDE,
            cme_clearing_fee=ES_CME_CLEARING_FEE_PER_SIDE,
            nfa_regulatory_fee=ES_NFA_REGULATORY_FEE_PER_SIDE,
            retail_discount_broker_commission=(
                ES_RETAIL_DISCOUNT_BROKER_COMMISSION_PER_SIDE
            ),
        ),
        FuturesFeeScheduleEntry(
            symbol="NQ",
            cme_exchange_fee=NQ_CME_EXCHANGE_FEE_PER_SIDE,
            cme_clearing_fee=NQ_CME_CLEARING_FEE_PER_SIDE,
            nfa_regulatory_fee=NQ_NFA_REGULATORY_FEE_PER_SIDE,
            retail_discount_broker_commission=(
                NQ_RETAIL_DISCOUNT_BROKER_COMMISSION_PER_SIDE
            ),
        ),
        FuturesFeeScheduleEntry(
            symbol="RTY",
            cme_exchange_fee=RTY_CME_EXCHANGE_FEE_PER_SIDE,
            cme_clearing_fee=RTY_CME_CLEARING_FEE_PER_SIDE,
            nfa_regulatory_fee=RTY_NFA_REGULATORY_FEE_PER_SIDE,
            retail_discount_broker_commission=(
                RTY_RETAIL_DISCOUNT_BROKER_COMMISSION_PER_SIDE
            ),
        ),
        FuturesFeeScheduleEntry(
            symbol="MES",
            cme_exchange_fee=MES_CME_EXCHANGE_FEE_PER_SIDE,
            cme_clearing_fee=MES_CME_CLEARING_FEE_PER_SIDE,
            nfa_regulatory_fee=MES_NFA_REGULATORY_FEE_PER_SIDE,
            retail_discount_broker_commission=(
                MES_RETAIL_DISCOUNT_BROKER_COMMISSION_PER_SIDE
            ),
        ),
        FuturesFeeScheduleEntry(
            symbol="MNQ",
            cme_exchange_fee=MNQ_CME_EXCHANGE_FEE_PER_SIDE,
            cme_clearing_fee=MNQ_CME_CLEARING_FEE_PER_SIDE,
            nfa_regulatory_fee=MNQ_NFA_REGULATORY_FEE_PER_SIDE,
            retail_discount_broker_commission=(
                MNQ_RETAIL_DISCOUNT_BROKER_COMMISSION_PER_SIDE
            ),
        ),
        FuturesFeeScheduleEntry(
            symbol="M2K",
            cme_exchange_fee=M2K_CME_EXCHANGE_FEE_PER_SIDE,
            cme_clearing_fee=M2K_CME_CLEARING_FEE_PER_SIDE,
            nfa_regulatory_fee=M2K_NFA_REGULATORY_FEE_PER_SIDE,
            retail_discount_broker_commission=(
                M2K_RETAIL_DISCOUNT_BROKER_COMMISSION_PER_SIDE
            ),
        ),
    ),
)

_FEE_SCHEDULES: Final = {
    PLACEHOLDER_FEE_SCHEDULE.version_id: PLACEHOLDER_FEE_SCHEDULE,
    REAL_FEE_SCHEDULE.version_id: REAL_FEE_SCHEDULE,
}


def fee_schedule_by_version(version_id: str) -> FuturesFeeScheduleVersion:
    """Resolve a fee schedule version by id."""

    try:
        return _FEE_SCHEDULES[_normalize_version_id(version_id)]
    except KeyError as exc:
        raise FuturesFeeScheduleError(f"unknown fee schedule version: {version_id}") from exc


def active_fee_schedule() -> FuturesFeeScheduleVersion:
    """Return the active real fee schedule."""

    return fee_schedule_by_version(ACTIVE_FEE_SCHEDULE_VERSION_ID)


def active_fee_schedule_cost_component_descriptor(
    *,
    default_symbol: str = "ES",
) -> dict[str, object]:
    """Return the active hard-fee cost component descriptor."""

    schedule = active_fee_schedule()
    schedule.entry_for_symbol(default_symbol)
    return {
        "model": "futures_fee_schedule",
        "schedule_version_id": schedule.version_id,
        "default_symbol": _normalize_symbol(default_symbol),
    }


def _normalize_symbol(value: str) -> str:
    symbol = str(value).strip().upper()
    if not symbol:
        raise FuturesFeeScheduleError("symbol is required")
    return symbol


def _normalize_version_id(value: str) -> str:
    version_id = str(value).strip()
    if not version_id:
        raise FuturesFeeScheduleError("fee schedule version id is required")
    return version_id


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f")


__all__ = [
    "ACTIVE_FEE_SCHEDULE_VERSION_ID",
    "M2K_CME_CLEARING_FEE_PER_SIDE",
    "M2K_CME_EXCHANGE_FEE_PER_SIDE",
    "M2K_NFA_REGULATORY_FEE_PER_SIDE",
    "M2K_RETAIL_DISCOUNT_BROKER_COMMISSION_PER_SIDE",
    "MES_CME_CLEARING_FEE_PER_SIDE",
    "MES_CME_EXCHANGE_FEE_PER_SIDE",
    "MES_NFA_REGULATORY_FEE_PER_SIDE",
    "MES_RETAIL_DISCOUNT_BROKER_COMMISSION_PER_SIDE",
    "MNQ_CME_CLEARING_FEE_PER_SIDE",
    "MNQ_CME_EXCHANGE_FEE_PER_SIDE",
    "MNQ_NFA_REGULATORY_FEE_PER_SIDE",
    "MNQ_RETAIL_DISCOUNT_BROKER_COMMISSION_PER_SIDE",
    "NQ_CME_CLEARING_FEE_PER_SIDE",
    "NQ_CME_EXCHANGE_FEE_PER_SIDE",
    "NQ_NFA_REGULATORY_FEE_PER_SIDE",
    "NQ_RETAIL_DISCOUNT_BROKER_COMMISSION_PER_SIDE",
    "PLACEHOLDER_FEE_SCHEDULE_VERSION_ID",
    "REAL_FEE_SCHEDULE_VERSION_ID",
    "RTY_CME_CLEARING_FEE_PER_SIDE",
    "RTY_CME_EXCHANGE_FEE_PER_SIDE",
    "RTY_NFA_REGULATORY_FEE_PER_SIDE",
    "RTY_RETAIL_DISCOUNT_BROKER_COMMISSION_PER_SIDE",
    "ES_CME_CLEARING_FEE_PER_SIDE",
    "ES_CME_EXCHANGE_FEE_PER_SIDE",
    "ES_NFA_REGULATORY_FEE_PER_SIDE",
    "ES_RETAIL_DISCOUNT_BROKER_COMMISSION_PER_SIDE",
    "FuturesFeeScheduleEntry",
    "FuturesFeeScheduleError",
    "FuturesFeeScheduleVersion",
    "active_fee_schedule",
    "active_fee_schedule_cost_component_descriptor",
    "fee_schedule_by_version",
]
