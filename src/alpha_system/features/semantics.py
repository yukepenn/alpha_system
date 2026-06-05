"""Dense-grid, no-trade, and BBO missingness semantics.

The predicates in this module operate only on FLF-P03 input-view rows and
FLF-P01 reconstructed canonical dense-grid records. They do not load data,
materialize values, fill quotes, or compute features or labels.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from alpha_system.data.foundation.grid import (
    NO_TRADE_QUALITY_FLAG,
    PREVIOUS_CLOSE_FILL_METHOD,
    DenseGridBarRecord,
)
from alpha_system.data.foundation.quotes import (
    BBO_QUARANTINE_QUALITY_FLAG,
    MISSING_BBO_QUALITY_FLAG,
    CanonicalBBORecord,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.features.input_views import BBOInputRow, OHLCVInputRow

BBO_MISSINGNESS_QUALITY_FLAGS: frozenset[str] = frozenset(
    {
        MISSING_BBO_QUALITY_FLAG,
        BBO_QUARANTINE_QUALITY_FLAG,
    }
)

type TradeBarRow = OHLCVInputRow | DenseGridBarRecord
type BBOQuoteRow = BBOInputRow | CanonicalBBORecord


@dataclass(frozen=True, slots=True)
class DenseGridBarSemantics:
    """Dense-grid flags that separate provider trade truth from no-trade rows."""

    has_trade: bool
    synthetic: bool
    fill_method: str | None
    provider_bar_ref: str | None
    no_trade: bool


@dataclass(frozen=True, slots=True)
class BBOQuoteSemantics:
    """BBO quality and invariant flags without quote filling or interpolation."""

    missing_bbo: bool
    bbo_quarantined: bool
    missing_or_abnormal: bool
    invariants_hold: bool


def dense_grid_bar_semantics(row: object) -> DenseGridBarSemantics:
    """Return the explicit dense-grid trade/no-trade fields for one row."""

    dense_row = _require_dense_grid_bar(row)
    return DenseGridBarSemantics(
        has_trade=dense_row.has_trade,
        synthetic=dense_row.synthetic,
        fill_method=dense_row.fill_method,
        provider_bar_ref=dense_row.provider_bar_ref,
        no_trade=_has_quality_flag(dense_row, NO_TRADE_QUALITY_FLAG),
    )


def is_synthetic_no_trade_bar(row: object) -> bool:
    """Return true only for the canonical dense-grid no-trade signature."""

    trade_row = _require_trade_bar_row(row)
    if isinstance(trade_row, OHLCVInputRow):
        return False

    return (
        trade_row.has_trade is False
        and trade_row.synthetic is True
        and trade_row.fill_method == PREVIOUS_CLOSE_FILL_METHOD
        and trade_row.volume == Decimal("0")
        and _has_quality_flag(trade_row, NO_TRADE_QUALITY_FLAG)
        and trade_row.provider_bar_ref is None
    )


def is_real_trade_bar(row: object) -> bool:
    """Return true for sparse provider trade bars or dense rows with real trades."""

    trade_row = _require_trade_bar_row(row)
    if isinstance(trade_row, OHLCVInputRow):
        return not _has_quality_flag(trade_row, NO_TRADE_QUALITY_FLAG)

    return (
        trade_row.has_trade is True
        and trade_row.synthetic is False
        and trade_row.fill_method is None
        and trade_row.provider_bar_ref is not None
        and not _has_quality_flag(trade_row, NO_TRADE_QUALITY_FLAG)
    )


def select_real_trade_bars[TradeRowT: (OHLCVInputRow, DenseGridBarRecord)](
    rows: Iterable[TradeRowT],
) -> tuple[TradeRowT, ...]:
    """Return rows downstream trade-bar logic may treat as real trade bars."""

    return tuple(row for row in rows if is_real_trade_bar(row))


def select_synthetic_no_trade_bars[TradeRowT: (OHLCVInputRow, DenseGridBarRecord)](
    rows: Iterable[TradeRowT],
) -> tuple[TradeRowT, ...]:
    """Return rows carrying the canonical synthetic no-trade signature."""

    return tuple(row for row in rows if is_synthetic_no_trade_bar(row))


def bbo_quote_semantics(row: object) -> BBOQuoteSemantics:
    """Return BBO missingness/quarantine flags and invariant status for one row."""

    quote_row = _require_bbo_quote_row(row)
    missing_bbo = _has_quality_flag(quote_row, MISSING_BBO_QUALITY_FLAG)
    bbo_quarantined = _has_quality_flag(quote_row, BBO_QUARANTINE_QUALITY_FLAG)
    return BBOQuoteSemantics(
        missing_bbo=missing_bbo,
        bbo_quarantined=bbo_quarantined,
        missing_or_abnormal=missing_bbo or bbo_quarantined,
        invariants_hold=bbo_invariants_hold(quote_row),
    )


def has_missing_bbo(row: object) -> bool:
    """Return true when the canonical ``missing_bbo`` flag is present."""

    return _has_quality_flag(_require_bbo_quote_row(row), MISSING_BBO_QUALITY_FLAG)


def is_bbo_quarantined(row: object) -> bool:
    """Return true when the canonical ``bbo_quarantined`` flag is present."""

    return _has_quality_flag(_require_bbo_quote_row(row), BBO_QUARANTINE_QUALITY_FLAG)


def has_missing_or_abnormal_bbo(row: object) -> bool:
    """Return true for missing/bad quotes or quarantined abnormal BBO rows."""

    quote_row = _require_bbo_quote_row(row)
    return has_missing_bbo(quote_row) or is_bbo_quarantined(quote_row)


def bbo_invariants_hold(row: object) -> bool:
    """Check canonical BBO arithmetic and availability invariants on the row as given."""

    quote_row = _require_bbo_quote_row(row)
    required_decimal_fields = (
        quote_row.bid,
        quote_row.ask,
        quote_row.bid_size,
        quote_row.ask_size,
        quote_row.mid,
        quote_row.spread,
    )
    if not all(isinstance(value, Decimal) for value in required_decimal_fields):
        return False
    if not isinstance(quote_row.available_ts, datetime) or not isinstance(
        quote_row.bar_end_ts,
        datetime,
    ):
        return False
    if quote_row.ask < quote_row.bid:
        return False
    if quote_row.mid != (quote_row.bid + quote_row.ask) / Decimal("2"):
        return False
    if quote_row.spread != quote_row.ask - quote_row.bid:
        return False
    if quote_row.available_ts < quote_row.bar_end_ts:
        return False
    if quote_row.microprice is None:
        return True
    if not isinstance(quote_row.microprice, Decimal):
        return False
    if quote_row.bid_size <= 0 or quote_row.ask_size <= 0:
        return False
    return quote_row.bid <= quote_row.microprice <= quote_row.ask


def is_valid_bbo_quote(row: object) -> bool:
    """Return true only for unflagged BBO rows whose stored invariants hold."""

    quote_row = _require_bbo_quote_row(row)
    return not has_missing_or_abnormal_bbo(quote_row) and bbo_invariants_hold(quote_row)


def select_missing_or_abnormal_bbo_rows[BBOQuoteRowT: (BBOInputRow, CanonicalBBORecord)](
    rows: Iterable[BBOQuoteRowT],
) -> tuple[BBOQuoteRowT, ...]:
    """Return BBO rows explicitly flagged as missing or quarantined."""

    return tuple(row for row in rows if has_missing_or_abnormal_bbo(row))


def select_valid_bbo_quotes[BBOQuoteRowT: (BBOInputRow, CanonicalBBORecord)](
    rows: Iterable[BBOQuoteRowT],
) -> tuple[BBOQuoteRowT, ...]:
    """Return unflagged BBO rows without producing filled or interpolated quotes."""

    return tuple(row for row in rows if is_valid_bbo_quote(row))


def _has_quality_flag(row: TradeBarRow | BBOQuoteRow, token: str) -> bool:
    return token in _quality_flag_tokens(row)


def _quality_flag_tokens(row: TradeBarRow | BBOQuoteRow) -> frozenset[str]:
    quality_flags = row.quality_flags
    if isinstance(quality_flags, str) or not isinstance(quality_flags, Iterable):
        msg = "quality_flags must be an explicit collection of strings"
        raise DataFoundationValidationError(msg)
    tokens: set[str] = set()
    for flag in quality_flags:
        if not isinstance(flag, str) or not flag.strip():
            msg = "quality_flags must contain non-empty strings"
            raise DataFoundationValidationError(msg)
        tokens.add(flag.strip().lower())
    return frozenset(tokens)


def _require_trade_bar_row(row: object) -> TradeBarRow:
    if isinstance(row, OHLCVInputRow | DenseGridBarRecord):
        return row
    msg = "trade-bar semantics require an OHLCVInputRow or DenseGridBarRecord"
    raise DataFoundationValidationError(msg)


def _require_dense_grid_bar(row: object) -> DenseGridBarRecord:
    if isinstance(row, DenseGridBarRecord):
        return row
    msg = "dense-grid semantics require a DenseGridBarRecord"
    raise DataFoundationValidationError(msg)


def _require_bbo_quote_row(row: object) -> BBOQuoteRow:
    if isinstance(row, BBOInputRow | CanonicalBBORecord):
        return row
    msg = "BBO semantics require a BBOInputRow or CanonicalBBORecord"
    raise DataFoundationValidationError(msg)


__all__ = [
    "BBO_MISSINGNESS_QUALITY_FLAGS",
    "BBOQuoteSemantics",
    "BBOQuoteRow",
    "DenseGridBarSemantics",
    "TradeBarRow",
    "bbo_invariants_hold",
    "bbo_quote_semantics",
    "dense_grid_bar_semantics",
    "has_missing_bbo",
    "has_missing_or_abnormal_bbo",
    "is_bbo_quarantined",
    "is_real_trade_bar",
    "is_synthetic_no_trade_bar",
    "is_valid_bbo_quote",
    "select_missing_or_abnormal_bbo_rows",
    "select_real_trade_bars",
    "select_synthetic_no_trade_bars",
    "select_valid_bbo_quotes",
]
