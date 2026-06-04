"""Optional read-only IBKR historical-data connector.

This module exposes historical data only. It adds no order, account, broker,
position, paper, live, or trading surface. ``ib_insync`` is an optional
dependency and is imported lazily only when a real IBKR client or contract class
is needed. For a real operator pull, install the optional dependency in a local
venv with ``python -m venv .venv && .venv/bin/pip install -e ".[ibkr]"``. If a
venv is not available, use ``python -m pip install --target ~/.alpha_ibkr_libs
ib_insync`` and run with ``PYTHONPATH=src:~/.alpha_ibkr_libs``.
"""

from __future__ import annotations

import contextlib
import csv
import io
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from types import ModuleType
from typing import Any

from alpha_system.data.foundation.ibkr import (
    IBKRConnectionProfile,
    IBKRReadOnlyApiBoundary,
    build_read_only_ibkr_boundary,
)
from alpha_system.data.foundation.requests import HistoricalRequestSpec
from alpha_system.data.foundation.sources import DataAccessMode, DataFoundationValidationError

FORBIDDEN_IB_METHODS: tuple[str, ...] = (
    "placeOrder",
    "cancelOrder",
    "reqAccountSummary",
    "reqAccountUpdates",
    "accountSummary",
    "accountValues",
    "portfolio",
    "positions",
    "reqPositions",
    "openOrders",
    "reqOpenOrders",
    "reqExecutions",
    "reqAllOpenOrders",
    "reqAutoOpenOrders",
    "exerciseOptions",
    "reqGlobalCancel",
)

CSV_HEADER: tuple[str, ...] = (
    "symbol",
    "contract_ref",
    "provider_ts",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "wap",
    "barCount",
)

_HISTORICAL_METHOD_NAME = "reqHistoricalData"
_IBKR_EXTRA_INSTALL_HINT = (
    'python -m venv .venv && .venv/bin/pip install -e ".[ibkr]"'
)
_IBKR_TARGET_INSTALL_HINT = (
    "python -m pip install --target ~/.alpha_ibkr_libs ib_insync "
    "and run with PYTHONPATH=src:~/.alpha_ibkr_libs"
)
_CONTRACT_MONTH_RE = re.compile(r"(?<!\d)(\d{6}|\d{8})(?!\d)")


@dataclass(frozen=True, slots=True)
class _InjectedContFuture:
    symbol: str
    exchange: str
    currency: str
    secType: str = "CONTFUT"


@dataclass(frozen=True, slots=True)
class _InjectedFuture:
    symbol: str
    exchange: str
    currency: str
    lastTradeDateOrContractMonth: str = ""
    localSymbol: str = ""
    includeExpired: bool = True
    secType: str = "FUT"


def _load_ib_insync() -> ModuleType:
    """Import ``ib_insync`` only when a real connector path needs it."""

    try:
        import ib_insync
    except ImportError as exc:
        msg = (
            "ib_insync is required for real IBKR historical pulls; install it with "
            f"{_IBKR_EXTRA_INSTALL_HINT}; fallback: {_IBKR_TARGET_INSTALL_HINT}"
        )
        raise ImportError(msg) from exc
    return ib_insync


def _assert_connector_scope() -> None:
    if _HISTORICAL_METHOD_NAME in FORBIDDEN_IB_METHODS:
        msg = "connector scope is contradictory: historical method is forbidden"
        raise RuntimeError(msg)


def _uses_ib_insync_client(ib: object) -> bool:
    return type(ib).__module__.split(".", maxsplit=1)[0] == "ib_insync"


def _contract_classes_for_client(ib: object) -> tuple[type[Any], type[Any]]:
    if _uses_ib_insync_client(ib):
        ib_insync = _load_ib_insync()
        return ib_insync.ContFuture, ib_insync.Future
    return _InjectedContFuture, _InjectedFuture


def _contract_month_from_ref(contract_ref: str) -> str:
    match = _CONTRACT_MONTH_RE.search(contract_ref)
    return "" if match is None else match.group(1)


def _contract_for_spec(request_spec: HistoricalRequestSpec, *, ib: object) -> object:
    cont_future_class, future_class = _contract_classes_for_client(ib)
    if request_spec.sec_type == "CONTFUT":
        return cont_future_class(
            symbol=request_spec.symbol_root,
            exchange=request_spec.exchange,
            currency=request_spec.currency,
        )
    if request_spec.sec_type == "FUT":
        return future_class(
            symbol=request_spec.symbol_root,
            exchange=request_spec.exchange,
            currency=request_spec.currency,
            lastTradeDateOrContractMonth=_contract_month_from_ref(request_spec.contract_ref),
            localSymbol=request_spec.contract_ref,
            includeExpired=True,
        )
    msg = f"unsupported IBKR historical sec_type {request_spec.sec_type!r}"
    raise DataFoundationValidationError(msg)


def _format_provider_ts(value: object) -> str:
    if isinstance(value, datetime):
        timestamp = value
    elif isinstance(value, date):
        timestamp = datetime.combine(value, time.min, tzinfo=UTC)
    elif isinstance(value, str):
        timestamp = _parse_provider_ts_text(value)
    else:
        msg = f"historical bar date has unsupported type {type(value).__name__}"
        raise DataFoundationValidationError(msg)

    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    return timestamp.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")


def _parse_provider_ts_text(value: str) -> datetime:
    raw = value.strip()
    if not raw:
        msg = "historical bar date must not be empty"
        raise DataFoundationValidationError(msg)

    iso_candidate = raw.replace("Z", "+00:00")
    if iso_candidate.endswith(" UTC"):
        iso_candidate = iso_candidate.removesuffix(" UTC") + "+00:00"
    try:
        return datetime.fromisoformat(iso_candidate)
    except ValueError:
        pass

    for pattern in (
        "%Y%m%d %H:%M:%S",
        "%Y%m%d %H:%M:%S UTC",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S UTC",
    ):
        try:
            parsed = datetime.strptime(raw, pattern)
        except ValueError:
            continue
        return parsed.replace(tzinfo=UTC)

    msg = f"historical bar date {raw!r} is not a supported timestamp format"
    raise DataFoundationValidationError(msg)


def _required_bar_value(bar: object, name: str) -> object:
    if not hasattr(bar, name):
        msg = f"historical bar is missing required field {name!r}"
        raise DataFoundationValidationError(msg)
    value = getattr(bar, name)
    if value is None:
        msg = f"historical bar field {name!r} must not be None"
        raise DataFoundationValidationError(msg)
    return value


def _optional_bar_value(bar: object, names: Sequence[str]) -> object:
    for name in names:
        if hasattr(bar, name):
            return getattr(bar, name)
    return None


def _csv_cell(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def _bars_to_csv_bytes(
    bars: object,
    *,
    request_spec: HistoricalRequestSpec,
) -> bytes:
    if isinstance(bars, (str, bytes)):
        msg = "IBKR historical response must be an iterable of bar objects"
        raise DataFoundationValidationError(msg)

    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=CSV_HEADER, lineterminator="\n")
    writer.writeheader()
    for bar in bars:
        writer.writerow(
            {
                "symbol": request_spec.symbol_root,
                "contract_ref": request_spec.contract_ref,
                "provider_ts": _format_provider_ts(_required_bar_value(bar, "date")),
                "open": _csv_cell(_required_bar_value(bar, "open")),
                "high": _csv_cell(_required_bar_value(bar, "high")),
                "low": _csv_cell(_required_bar_value(bar, "low")),
                "close": _csv_cell(_required_bar_value(bar, "close")),
                "volume": _csv_cell(_required_bar_value(bar, "volume")),
                "wap": _csv_cell(_optional_bar_value(bar, ("average", "wap"))),
                "barCount": _csv_cell(_optional_bar_value(bar, ("barCount", "bar_count"))),
            }
        )
    return output.getvalue().encode("utf-8")


def build_ibkr_historical_handler(
    *,
    ib: object,
    profile: IBKRConnectionProfile,
) -> Callable[[HistoricalRequestSpec], bytes]:
    """Build a read-only historical handler for ``IBKRReadOnlyApiBoundary``."""

    if not isinstance(profile, IBKRConnectionProfile):
        msg = "build_ibkr_historical_handler requires an IBKRConnectionProfile"
        raise DataFoundationValidationError(msg)
    _assert_connector_scope()

    def handler(request_spec: HistoricalRequestSpec) -> bytes:
        if not isinstance(request_spec, HistoricalRequestSpec):
            msg = "IBKR historical handler requires a HistoricalRequestSpec"
            raise DataFoundationValidationError(msg)
        if request_spec.client_id != profile.client_id:
            msg = "request_spec client_id must match the IBKR connection profile"
            raise DataFoundationValidationError(msg)

        contract = _contract_for_spec(request_spec, ib=ib)
        end_datetime = "" if request_spec.sec_type == "CONTFUT" else request_spec.end_ts
        bars = ib.reqHistoricalData(
            contract,
            endDateTime=end_datetime,
            durationStr=request_spec.duration,
            barSizeSetting=request_spec.bar_size,
            whatToShow=request_spec.what_to_show,
            useRTH=request_spec.use_rth,
            formatDate=2,
        )
        return _bars_to_csv_bytes(bars, request_spec=request_spec)

    return handler


@contextlib.contextmanager
def open_ibkr_historical_boundary(
    profile: IBKRConnectionProfile,
    access_mode: DataAccessMode,
    *,
    env: Mapping[str, str] | None = None,
    ib: object | None = None,
) -> IBKRReadOnlyApiBoundary:
    """Open a read-only historical boundary around an optional IBKR client."""

    if not isinstance(profile, IBKRConnectionProfile):
        msg = "open_ibkr_historical_boundary requires an IBKRConnectionProfile"
        raise DataFoundationValidationError(msg)
    if not isinstance(access_mode, DataAccessMode):
        msg = "open_ibkr_historical_boundary requires a DataAccessMode"
        raise DataFoundationValidationError(msg)
    if env is not None:
        access_mode.validate_runtime_env(env, ci=None)

    created_client = ib is None
    client = ib
    if client is None:
        ib_insync = _load_ib_insync()
        client = ib_insync.IB()
        client.connect(
            profile.host,
            profile.port,
            clientId=profile.client_id,
            readonly=True,
            timeout=profile.connection_timeout,
        )

    try:
        handler = build_ibkr_historical_handler(ib=client, profile=profile)
        yield build_read_only_ibkr_boundary(
            profile=profile,
            access_mode=access_mode,
            read_only_methods={_HISTORICAL_METHOD_NAME: handler},
        )
    finally:
        if created_client:
            client.disconnect()


__all__ = [
    "CSV_HEADER",
    "FORBIDDEN_IB_METHODS",
    "build_ibkr_historical_handler",
    "open_ibkr_historical_boundary",
]
