"""Raw IBKR bar lake to accepted DatasetVersion materializer."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sqlite3
import sys
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from types import MappingProxyType
from zoneinfo import ZoneInfo

from alpha_system.core.enums import SessionType
from alpha_system.core.hashing import hash_config
from alpha_system.core.registry import connect_registry, is_local_only_registry_path
from alpha_system.data.calendar import load_calendar_config
from alpha_system.data.cli_validation import (
    load_cli_config,
    validation_config_from_mapping,
)
from alpha_system.data.contracts import TradingSession
from alpha_system.data.fixture_policy import FixturePolicyError, assert_build_input_allowed
from alpha_system.data.foundation.bars import CanonicalBarRecord, ParsedBarRecord
from alpha_system.data.foundation.datasets import (
    CoverageReport,
    DataQualityReport,
    DatasetPartitionPlan,
    DatasetVersion,
    ReportStatus,
    compute_quality_report_hash,
    require_governance_metadata_for_locked_partition_use,
)
from alpha_system.data.foundation.sessions import (
    SESSION_TYPE_EARLY_CLOSE,
    SESSION_TYPE_ETH,
    SESSION_TYPE_HOLIDAY,
    SessionTemplate,
    load_session_templates_by_id,
    load_trading_calendar_records,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.data.foundation.version_registry import persist_dataset_version
from alpha_system.data.ibkr._json_utils import json_ready as _json_ready
from alpha_system.data.quality import evaluate_data_quality, normalize_quality_flags
from alpha_system.data.sessionize import sessionize_bars
from alpha_system.data.sessions import build_session_id, session_contains_bar
from alpha_system.data.validation import validate_bars

SOURCE_ID = "dsrc_ibkr_historical"
DEFAULT_INSTRUMENT_CONFIG = (
    Path(__file__).resolve(strict=False).parents[4]
    / "configs"
    / "data"
    / "ibkr_es_nq_rty_instruments.json"
)
DEFAULT_CALENDAR_CONFIG = (
    Path(__file__).resolve(strict=False).parents[4]
    / "configs"
    / "data"
    / "session_templates_and_calendar.json"
)
DEFAULT_VALIDATION_CONFIG = (
    Path(__file__).resolve(strict=False).parents[4]
    / "configs"
    / "data"
    / "ibkr_materialize_validation.json"
)
RAW_HEADER = (
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


@dataclass(frozen=True, slots=True)
class RawPathRecord:
    path: Path
    source: str
    request_id: str
    chunk_id: str
    raw_object_id: str
    content_hash: str
    row_count: int


@dataclass(frozen=True, slots=True)
class InstrumentSettings:
    symbol: str
    instrument_id: str
    series_id: str
    roll_policy_id: str
    session_label: str


@dataclass(frozen=True, slots=True)
class MaterializeSummary:
    dataset_version_id: str
    symbols: tuple[str, ...]
    contract_universe: tuple[str, ...]
    start_ts: str
    end_ts: str
    raw_object_count: int
    parsed_row_count: int
    canonical_row_count: int
    duplicate_rows_dropped: int
    quality_status: str
    coverage_status: str
    partition: str
    registry_path: str | None
    registered: bool
    blocking_summary: Mapping[str, object]
    contamination_metadata: Mapping[str, object]

    def to_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "dataset_version_id": self.dataset_version_id,
                "symbols": self.symbols,
                "contract_universe": self.contract_universe,
                "start_ts": self.start_ts,
                "end_ts": self.end_ts,
                "raw_object_count": self.raw_object_count,
                "parsed_row_count": self.parsed_row_count,
                "canonical_row_count": self.canonical_row_count,
                "duplicate_rows_dropped": self.duplicate_rows_dropped,
                "quality_status": self.quality_status,
                "coverage_status": self.coverage_status,
                "partition": self.partition,
                "registry_path": self.registry_path,
                "registered": self.registered,
                "blocking_summary": self.blocking_summary,
                "contamination_metadata": self.contamination_metadata,
            }
        )


@dataclass(frozen=True, slots=True)
class _MaterializeCalendarOverride:
    is_holiday: bool
    is_half_day: bool
    close_ts: datetime | None


@dataclass(frozen=True, slots=True)
class _MaterializeTemplateCalendar:
    """Strict ETH template shim with bounded holiday/half-day awareness."""

    # This shim models the full roughly 23-hour CME index ETH overnight session.
    # The internal SessionType.OVERNIGHT id differs from the foundation ETH
    # session label; that vocabulary split stays internal here.
    calendar_id: str
    template: SessionTemplate
    calendar_overrides: Mapping[date, _MaterializeCalendarOverride]

    @property
    def timezone(self) -> str:
        return self.template.timezone

    @property
    def zone(self) -> ZoneInfo:
        return self.template.zone

    def session_containing_bar(
        self,
        bar_start_ts: datetime,
        bar_end_ts: datetime,
    ) -> TradingSession | None:
        local_start = bar_start_ts.astimezone(self.zone)
        candidates = (local_start.date(), local_start.date() + timedelta(days=1))
        for candidate in candidates:
            session = self.trading_session_for_date(candidate)
            if session is None:
                continue
            if session_contains_bar(session, bar_start_ts, bar_end_ts):
                return session
        return None

    def session_by_id(self, session_id: str) -> TradingSession | None:
        prefix = f"{self.calendar_id}:"
        if not session_id.startswith(prefix):
            return None
        parts = session_id.split(":")
        if len(parts) != 3:
            return None
        try:
            trading_date = date.fromisoformat(parts[1])
            session_type = SessionType(parts[2])
        except ValueError:
            return None
        if session_type is not SessionType.OVERNIGHT:
            return None
        return self._eth_session_for_date(trading_date)

    def trading_session_for_date(self, trading_date: date) -> TradingSession | None:
        session = self._eth_session_for_date(trading_date)
        if session.is_holiday:
            return None
        return session

    def _eth_session_for_date(self, trading_date: date) -> TradingSession:
        open_date = trading_date
        if self.template.eth_end <= self.template.eth_start:
            open_date = trading_date - timedelta(days=1)
        open_ts = datetime.combine(open_date, self.template.eth_start, self.zone)
        close_ts = datetime.combine(trading_date, self.template.eth_end, self.zone)
        if close_ts <= open_ts:
            close_ts += timedelta(days=1)
        is_holiday = trading_date.weekday() >= 5
        is_half_day = False
        quality_flags: tuple[str, ...] = ("weekend_closed",) if is_holiday else ()
        override = self.calendar_overrides.get(trading_date)
        if override is not None:
            is_holiday = override.is_holiday
            is_half_day = override.is_half_day
            quality_flags = ()
            if override.is_holiday:
                open_ts = datetime.combine(trading_date, self.template.eth_end, self.zone)
                close_ts = open_ts
                quality_flags = ("holiday",)
            elif override.close_ts is not None:
                close_ts = override.close_ts.astimezone(self.zone)
                if close_ts <= open_ts:
                    msg = (
                        "calendar early-close override must close after the ETH open "
                        f"for {trading_date.isoformat()}"
                    )
                    raise DataFoundationValidationError(msg)
                quality_flags = ("half_day",)
        return TradingSession(
            calendar_id=self.calendar_id,
            trading_date=trading_date,
            session_id=build_session_id(
                self.calendar_id,
                trading_date,
                SessionType.OVERNIGHT,
            ),
            open_ts=open_ts,
            close_ts=close_ts,
            is_holiday=is_holiday,
            is_half_day=is_half_day,
            session_type=SessionType.OVERNIGHT,
            timezone=self.template.timezone,
            quality_flags=quality_flags,
        )


def _repo_root() -> Path:
    return Path(__file__).resolve(strict=False).parents[4]


def _parse_symbols(value: str) -> tuple[str, ...]:
    symbols = tuple(part.strip().upper() for part in value.split(",") if part.strip())
    if not symbols:
        msg = "--symbols must contain at least one comma-separated root"
        raise argparse.ArgumentTypeError(msg)
    duplicates = tuple(sorted({symbol for symbol in symbols if symbols.count(symbol) > 1}))
    if duplicates:
        msg = "--symbols contains duplicates: " + ", ".join(duplicates)
        raise argparse.ArgumentTypeError(msg)
    return symbols


def _parse_aware_datetime_arg(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        msg = f"timestamp must be ISO-8601 timezone-aware: {value!r}"
        raise argparse.ArgumentTypeError(msg) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        msg = f"timestamp must be timezone-aware: {value!r}"
        raise argparse.ArgumentTypeError(msg)
    return parsed.astimezone(UTC)


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize local IBKR raw bars into a gated DatasetVersion",
    )
    parser.add_argument("--symbols", type=_parse_symbols, required=True)
    parser.add_argument("--registry-path", type=Path, required=True)
    parser.add_argument("--data-version", required=True)
    parser.add_argument("--partition", required=True)
    parser.add_argument("--start-ts", type=_parse_aware_datetime_arg, required=True)
    parser.add_argument("--end-ts", type=_parse_aware_datetime_arg, required=True)
    parser.add_argument("--instrument-config", type=Path, default=DEFAULT_INSTRUMENT_CONFIG)
    parser.add_argument("--calendar-config", type=Path, default=DEFAULT_CALENDAR_CONFIG)
    parser.add_argument("--validation-config", type=Path, default=DEFAULT_VALIDATION_CONFIG)
    return parser.parse_args(argv)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _validate_data_root(root: Path, repo_root: Path) -> Path:
    """Reject ALPHA_DATA_ROOT locations inside the repository."""

    resolved = root.expanduser().resolve(strict=False)
    resolved_repo = repo_root.expanduser().resolve(strict=False)
    if resolved == resolved_repo or _is_relative_to(resolved, resolved_repo):
        msg = "ALPHA_DATA_ROOT must not resolve inside the alpha_system repository"
        raise DataFoundationValidationError(msg)
    return resolved


def _require_data_root(env: Mapping[str, str]) -> Path:
    value = env.get("ALPHA_DATA_ROOT")
    if value is None or not value.strip():
        msg = "ALPHA_DATA_ROOT is required for raw-lake materialization"
        raise DataFoundationValidationError(msg)
    return _validate_data_root(Path(value), _repo_root())


def _validate_registry_path(path: Path) -> Path:
    resolved = path.expanduser().resolve(strict=False)
    if not is_local_only_registry_path(resolved):
        msg = f"registry path is not local-only: {resolved.as_posix()}"
        raise DataFoundationValidationError(msg)
    return resolved


def _row_count(path: Path) -> int:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return max(0, sum(1 for line in handle if line.strip()) - 1)


def _raw_path_record(path: Path, *, data_root: Path) -> RawPathRecord:
    raw_root = data_root / "raw"
    try:
        relative = path.resolve(strict=False).relative_to(raw_root.resolve(strict=False))
    except ValueError as exc:
        msg = f"raw path is outside ALPHA_DATA_ROOT/raw: {path.as_posix()}"
        raise DataFoundationValidationError(msg) from exc
    parts = relative.parts
    if len(parts) != 5 or not parts[0].startswith("source="):
        msg = f"raw path does not follow source/request/chunk layout: {path.as_posix()}"
        raise DataFoundationValidationError(msg)
    source = parts[0].removeprefix("source=")
    request_id = parts[1].removeprefix("request=")
    chunk_id = parts[2].removeprefix("chunk=")
    hash_dir = parts[3].removeprefix("sha256=")
    digest = path.stem.lower()
    if not parts[1].startswith("request=") or not parts[2].startswith("chunk="):
        msg = f"raw path does not include request/chunk bindings: {path.as_posix()}"
        raise DataFoundationValidationError(msg)
    if not parts[3].startswith("sha256=") or hash_dir != digest[:2]:
        msg = f"raw path sha256 prefix does not match file digest: {path.as_posix()}"
        raise DataFoundationValidationError(msg)
    payload = path.read_bytes()
    actual_digest = hashlib.sha256(payload).hexdigest()
    if actual_digest != digest:
        msg = f"raw payload hash mismatch: {path.as_posix()}"
        raise DataFoundationValidationError(msg)
    return RawPathRecord(
        path=path,
        source=source,
        request_id=request_id,
        chunk_id=chunk_id,
        raw_object_id=f"raw_materialize_{source}_{request_id}_{chunk_id}_{digest[:12]}",
        content_hash="sha256:" + digest,
        row_count=_row_count(path),
    )


def _discover_raw_records(
    *,
    data_root: Path,
    allow_non_fixture_input: bool,
) -> tuple[RawPathRecord, ...]:
    raw_root = data_root / "raw"
    if not raw_root.is_dir():
        msg = f"raw directory does not exist: {raw_root.as_posix()}"
        raise DataFoundationValidationError(msg)
    records = []
    for path in sorted(raw_root.glob("source=*/request=*/chunk=*/sha256=*/*.raw")):
        try:
            allowed = assert_build_input_allowed(
                path,
                repo_root=_repo_root(),
                allow_non_fixture_input=allow_non_fixture_input,
            )
        except FixturePolicyError as exc:
            raise DataFoundationValidationError(str(exc)) from exc
        records.append(_raw_path_record(allowed, data_root=data_root))
    if not records:
        msg = f"no raw .raw files found under {raw_root.as_posix()}"
        raise DataFoundationValidationError(msg)
    return tuple(records)


# Connector provider timestamp formatting and materialize provider_ts parsing serve
# different boundaries; both helpers intentionally remain separate.
def _parse_provider_ts(value: object) -> datetime:
    raw = str(value).strip()
    if not raw:
        msg = "provider_ts must not be empty"
        raise DataFoundationValidationError(msg)
    candidates = (raw, raw.replace(" UTC", "+00:00"), raw.replace("Z", "+00:00"))
    for candidate in candidates:
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError:
            continue
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    for pattern in (
        "%Y%m%d %H:%M:%S",
        "%Y%m%d %H:%M:%S UTC",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S UTC",
    ):
        try:
            parsed = datetime.strptime(raw, pattern).replace(tzinfo=UTC)
        except ValueError:
            continue
        return parsed.astimezone(UTC)
    msg = f"provider_ts is not a supported timestamp: {raw!r}"
    raise DataFoundationValidationError(msg)


def _parse_raw_csv(record: RawPathRecord) -> tuple[ParsedBarRecord, ...]:
    with record.path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = tuple(reader.fieldnames or ())
        missing = tuple(column for column in RAW_HEADER if column not in fieldnames)
        if missing:
            msg = f"raw CSV missing required columns: {', '.join(missing)}"
            raise DataFoundationValidationError(msg)
        parsed = tuple(
            ParsedBarRecord.from_mapping(
                {
                    "source": record.source,
                    "symbol": row["symbol"],
                    "contract_ref": row["contract_ref"],
                    "provider_ts": row["provider_ts"],
                    "open": row["open"],
                    "high": row["high"],
                    "low": row["low"],
                    "close": row["close"],
                    "volume": row["volume"],
                    "wap_if_available": row.get("wap"),
                    "bar_count_if_available": row.get("barCount"),
                    "request_id": record.request_id,
                    "raw_object_id": record.raw_object_id,
                }
            )
            for row in reader
        )
    if len(parsed) != record.row_count:
        msg = f"raw row count mismatch for {record.path.as_posix()}"
        raise DataFoundationValidationError(msg)
    return parsed


def _template_eth_open_ts(template: SessionTemplate, trading_date: date) -> datetime:
    open_date = trading_date
    if template.eth_end <= template.eth_start:
        open_date = trading_date - timedelta(days=1)
    return datetime.combine(open_date, template.eth_start, template.zone)


def _calendar_overrides_from_records(
    path: Path,
    *,
    template: SessionTemplate,
) -> Mapping[date, _MaterializeCalendarOverride]:
    overrides: dict[date, _MaterializeCalendarOverride] = {}
    for record in load_trading_calendar_records(path):
        if record.session_type == SESSION_TYPE_HOLIDAY:
            override = _MaterializeCalendarOverride(
                is_holiday=True,
                is_half_day=False,
                close_ts=None,
            )
        elif record.session_type == SESSION_TYPE_EARLY_CLOSE:
            if record.open_ts is None or record.close_ts is None:
                msg = (
                    "early-close calendar_records require explicit open_ts and close_ts "
                    f"for {record.date.isoformat()}"
                )
                raise DataFoundationValidationError(msg)
            expected_open = _template_eth_open_ts(template, record.date)
            if record.open_ts.astimezone(template.zone) != expected_open:
                msg = (
                    "early-close calendar_records must use the template ETH open "
                    f"for {record.date.isoformat()}"
                )
                raise DataFoundationValidationError(msg)
            close_ts = record.close_ts.astimezone(template.zone)
            if close_ts <= expected_open:
                msg = (
                    "early-close calendar_records must close after the ETH open "
                    f"for {record.date.isoformat()}"
                )
                raise DataFoundationValidationError(msg)
            override = _MaterializeCalendarOverride(
                is_holiday=False,
                is_half_day=True,
                close_ts=close_ts,
            )
        else:
            continue

        existing = overrides.get(record.date)
        if existing is not None and existing != override:
            msg = (
                "calendar_records contain conflicting materialize overrides for "
                f"{record.date.isoformat()}"
            )
            raise DataFoundationValidationError(msg)
        overrides[record.date] = override
    return MappingProxyType(overrides)


def _load_calendar(path: Path, instrument_config: Mapping[str, object]) -> object:
    # The shipped session_templates_and_calendar.json uses the session_templates
    # schema, so load_calendar_config raises and the ETH template shim below is
    # the de-facto path for that config. A future calendar-config schema change
    # could silently shift behavior into load_calendar_config instead.
    try:
        return load_calendar_config(path)
    except (TypeError, ValueError, json.JSONDecodeError):
        pass
    templates = load_session_templates_by_id(path)
    template_id = str(
        instrument_config.get("session_template_id", "session_cme_index_futures_eth")
    )
    template = templates.get(template_id)
    if template is None:
        msg = f"session_template_id does not resolve in calendar config: {template_id}"
        raise DataFoundationValidationError(msg)
    return _MaterializeTemplateCalendar(
        calendar_id=template.template_id,
        template=template,
        calendar_overrides=_calendar_overrides_from_records(path, template=template),
    )


def _instrument_entries(config: Mapping[str, object]) -> Mapping[str, Mapping[str, object]]:
    raw_entries = config.get("instruments", ())
    if isinstance(raw_entries, str) or not isinstance(raw_entries, Iterable):
        msg = "instrument config instruments must be a list"
        raise DataFoundationValidationError(msg)
    entries = {}
    for raw_entry in raw_entries:
        if not isinstance(raw_entry, Mapping):
            msg = "instrument config entries must be JSON objects"
            raise DataFoundationValidationError(msg)
        symbol = str(raw_entry.get("symbol", "")).strip().upper()
        if not symbol:
            msg = "instrument config entry missing symbol"
            raise DataFoundationValidationError(msg)
        entries[symbol] = raw_entry
    return MappingProxyType(entries)


def _settings_for_symbols(
    *,
    symbols: Sequence[str],
    instrument_config: Mapping[str, object],
) -> Mapping[str, InstrumentSettings]:
    entries = _instrument_entries(instrument_config)
    defaults = {
        "roll_policy_id": str(
            instrument_config.get("roll_policy_id", "roll_cme_index_futures_quarterly")
        ),
        "session_label": str(instrument_config.get("session_label", SESSION_TYPE_ETH)),
    }
    settings: dict[str, InstrumentSettings] = {}
    for symbol in symbols:
        entry = entries.get(symbol, {})
        settings[symbol] = InstrumentSettings(
            symbol=symbol,
            instrument_id=str(entry.get("instrument_id", f"inst_ibkr_{symbol.lower()}")),
            series_id=str(
                entry.get("series_id", f"series_ibkr_{symbol.lower()}_front_unadjusted")
            ),
            roll_policy_id=str(entry.get("roll_policy_id", defaults["roll_policy_id"])),
            session_label=str(entry.get("session_label", defaults["session_label"])).upper(),
        )
    return MappingProxyType(settings)


def _parsed_for_window(
    records: Iterable[ParsedBarRecord],
    *,
    symbols: Sequence[str],
    start_ts: datetime,
    end_ts: datetime,
) -> tuple[ParsedBarRecord, ...]:
    wanted = set(symbols)
    filtered = []
    for record in records:
        bar_start = _parse_provider_ts(record.provider_ts)
        if record.symbol.upper() not in wanted:
            continue
        if start_ts <= bar_start and bar_start + timedelta(minutes=1) <= end_ts:
            filtered.append(record)
    if not filtered:
        msg = "no parsed raw bars matched requested symbols/window"
        raise DataFoundationValidationError(msg)
    return tuple(filtered)


def _dedupe_parsed(
    records: Iterable[ParsedBarRecord],
) -> tuple[tuple[ParsedBarRecord, datetime], int]:
    ordered = sorted(
        ((record, _parse_provider_ts(record.provider_ts)) for record in records),
        key=lambda item: (
            item[0].symbol.upper(),
            item[1],
            item[0].request_id,
            item[0].raw_object_id,
        ),
    )
    deduped: dict[tuple[str, datetime], tuple[ParsedBarRecord, datetime]] = {}
    for record, provider_ts in ordered:
        deduped.setdefault((record.symbol.upper(), provider_ts), (record, provider_ts))
    return tuple(deduped.values()), len(ordered) - len(deduped)


def _canonical_input_rows(
    records: Iterable[tuple[ParsedBarRecord, datetime]],
    *,
    settings_by_symbol: Mapping[str, InstrumentSettings],
    data_version: str,
    latency: timedelta,
) -> tuple[dict[str, object], ...]:
    rows = []
    for record, bar_start in records:
        symbol = record.symbol.upper()
        settings = settings_by_symbol[symbol]
        bar_end = bar_start + timedelta(minutes=1)
        rows.append(
            {
                "instrument_id": settings.instrument_id,
                "session_id": "",
                "bar_index": -1,
                "bar_start_ts": bar_start,
                "bar_end_ts": bar_end,
                "event_ts": bar_end,
                "available_ts": bar_end + latency,
                "open": record.open,
                "high": record.high,
                "low": record.low,
                "close": record.close,
                "volume": record.volume,
                "vwap": record.wap_if_available or record.close,
                "trade_count": record.bar_count_if_available or 0,
                "bid": None,
                "ask": None,
                "spread": None,
                "source_version": record.raw_object_id,
                "data_version": data_version,
                "quality_flags": (),
                "symbol": symbol,
                "contract_id": record.contract_ref,
                "series_id": settings.series_id,
                "source": record.source,
                "source_request_id": record.request_id,
                "foundation_session_label": settings.session_label,
                "roll_policy_id": settings.roll_policy_id,
            }
        )
    return tuple(rows)


def _quality_issue_counts(issues: Iterable[object]) -> Mapping[str, int]:
    counts: Counter[str] = Counter()
    for issue in issues:
        flag = getattr(issue, "flag", None) or getattr(issue, "code", None)
        counts[str(flag)] += 1
    return MappingProxyType(dict(counts))


def _foundation_canonical_rows(
    rows: Iterable[Mapping[str, object]],
    *,
    ingested_at: datetime,
) -> tuple[CanonicalBarRecord, ...]:
    canonical = []
    for row in rows:
        canonical.append(
            CanonicalBarRecord.from_mapping(
                {
                    "instrument_id": row["instrument_id"],
                    "contract_id": row["contract_id"],
                    "series_id": row["series_id"],
                    "bar_start_ts": row["bar_start_ts"],
                    "bar_end_ts": row["bar_end_ts"],
                    "event_ts": row["event_ts"],
                    "available_ts": row["available_ts"],
                    "ingested_at": ingested_at,
                    "open": row["open"],
                    "high": row["high"],
                    "low": row["low"],
                    "close": row["close"],
                    "volume": row["volume"],
                    "source": row["source"],
                    "source_request_id": row["source_request_id"],
                    "data_version": row["data_version"],
                    "quality_flags": normalize_quality_flags(row.get("quality_flags")),
                    "session_label": row["foundation_session_label"],
                }
            )
        )
    return tuple(canonical)


def _calendar_session_for_date(
    calendar: object,
    trading_date: date,
) -> TradingSession | None:
    trading_session_for_date = getattr(calendar, "trading_session_for_date", None)
    if callable(trading_session_for_date):
        session = trading_session_for_date(trading_date)
    else:
        session_for_date = getattr(calendar, "session_for_date", None)
        if not callable(session_for_date):
            msg = "calendar does not expose session lookup for materialize coverage"
            raise DataFoundationValidationError(msg)
        session = session_for_date(trading_date)
    if session is None or session.is_holiday:
        return None
    return session


def _trading_sessions_for_window(
    calendar: object,
    *,
    start_ts: datetime,
    end_ts: datetime,
) -> tuple[TradingSession, ...]:
    zone = getattr(calendar, "zone", None)
    if zone is None:
        msg = "calendar does not expose a timezone for materialize coverage"
        raise DataFoundationValidationError(msg)
    start_date = start_ts.astimezone(zone).date()
    end_date = end_ts.astimezone(zone).date()
    sessions = []
    current = start_date
    while current <= end_date:
        session = _calendar_session_for_date(calendar, current)
        if session is not None and session.close_ts > start_ts and session.open_ts < end_ts:
            sessions.append(session)
        current += timedelta(days=1)
    if not sessions:
        msg = "no tradable calendar sessions overlap the materialize coverage window"
        raise DataFoundationValidationError(msg)
    return tuple(sessions)


def _expected_intervals(
    bars: Sequence[CanonicalBarRecord],
    *,
    symbols: Sequence[str],
    partition_id: str,
    settings_by_symbol: Mapping[str, InstrumentSettings],
    calendar: object,
    start_ts: datetime,
    end_ts: datetime,
) -> tuple[Mapping[str, object], ...]:
    # Coverage expects every minute in each calendar-emitted session for each
    # observed symbol/contract/session group. Weekend and configured holiday
    # dates are not emitted, while any emitted session with missing bars blocks.
    symbol_by_instrument = {
        settings.instrument_id: symbol for symbol, settings in settings_by_symbol.items()
    }
    groups = {
        (
            symbol_by_instrument[bar.instrument_id],
            bar.instrument_id,
            bar.contract_id,
            bar.session_label,
        )
        for bar in bars
    }
    observed_symbols = {group[0] for group in groups}
    missing_symbols = tuple(symbol for symbol in symbols if symbol not in observed_symbols)
    if missing_symbols:
        msg = "no canonical bars for requested symbols: " + ", ".join(missing_symbols)
        raise DataFoundationValidationError(msg)
    sessions = _trading_sessions_for_window(calendar, start_ts=start_ts, end_ts=end_ts)
    return tuple(
        MappingProxyType(
            {
                "symbol": symbol,
                "instrument_id": instrument_id,
                "contract_id": contract_id,
                "session_label": session_label,
                "start_ts": session.open_ts.isoformat(),
                "end_ts": session.close_ts.isoformat(),
                "partition_id": partition_id,
            }
        )
        for symbol, instrument_id, contract_id, session_label in sorted(groups)
        for session in sessions
    )


def _partition_plan(partition_id: str) -> DatasetPartitionPlan:
    if partition_id == "latest_shadow_candidate":
        return DatasetPartitionPlan.canonical(
            latest_shadow_candidate={
                "partition_id": "latest_shadow_candidate",
                "start_date": "rolling_recent",
                "end_date": "as_of_run",
                "role": "latest_shadow_candidate",
                "rolling": True,
                "optional": True,
            }
        )
    return DatasetPartitionPlan.canonical()


def _blocking_summary(
    *,
    validation_valid: bool,
    validation_issues: Mapping[str, int],
    session_quality_issues: Mapping[str, int],
    data_quality_report: DataQualityReport | None,
    coverage_report: CoverageReport | None,
) -> Mapping[str, object]:
    return MappingProxyType(
        {
            "validation_valid": validation_valid,
            "validation_issues": validation_issues,
            "session_quality_issues": session_quality_issues,
            "data_quality_status": (
                None if data_quality_report is None else data_quality_report.status.value
            ),
            "coverage_status": (
                None if coverage_report is None else coverage_report.coverage_status.value
            ),
            "quality_blocks": (
                None if data_quality_report is None else data_quality_report.blocks_versioning
            ),
            "coverage_blocks": (
                None if coverage_report is None else coverage_report.blocks_versioning
            ),
        }
    )


def _source_manifest_hash(
    *,
    raw_records: Sequence[RawPathRecord],
    symbols: Sequence[str],
    start_ts: datetime,
    end_ts: datetime,
) -> str:
    return hash_config(
        {
            "schema": "alpha_system.materialize.source_manifest.v1",
            "raw_objects": tuple(
                {
                    "source": record.source,
                    "request_id": record.request_id,
                    "chunk_id": record.chunk_id,
                    "content_hash": record.content_hash,
                    "row_count": record.row_count,
                }
                for record in raw_records
            ),
            "symbols": tuple(symbols),
            "start_ts": start_ts.isoformat(),
            "end_ts": end_ts.isoformat(),
        }
    )


def _persist_partition_metadata(
    *,
    registry_path: Path,
    dataset_version_id: str,
    created_at: datetime,
    config_hash: str,
    metadata: Mapping[str, object],
) -> None:
    payload = json.dumps(_json_ready(metadata), sort_keys=True)
    with connect_registry(registry_path) as connection:
        try:
            connection.execute(
                """
                INSERT INTO artifact_manifest (
                    artifact_id,
                    run_id,
                    run_table,
                    artifact_key,
                    artifact_path,
                    content_hash,
                    artifact_role,
                    created_at,
                    metadata_json,
                    status_message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"art_materialize_partition_{dataset_version_id}",
                    dataset_version_id,
                    "dataset_versions",
                    "partition_contamination_metadata",
                    registry_path.as_posix(),
                    config_hash,
                    "dataset_partition_metadata",
                    created_at.isoformat(),
                    payload,
                    "ADF1 Stage A materialize partition metadata",
                ),
            )
        except sqlite3.IntegrityError as exc:
            msg = f"partition metadata already exists for {dataset_version_id}"
            raise DataFoundationValidationError(msg) from exc


def run_materialize(
    *,
    symbols: Sequence[str],
    registry_path: Path,
    data_version: str,
    partition: str,
    start_ts: datetime,
    end_ts: datetime,
    instrument_config_path: Path,
    calendar_config_path: Path,
    validation_config_path: Path,
    env: Mapping[str, str] | None = None,
    now: datetime | None = None,
) -> MaterializeSummary:
    """Materialize raw bars with the no-lookahead five-timestamp policy.

    Canonical output keeps bar_start_ts, bar_end_ts, event_ts, available_ts,
    and ingested_at distinct. available_ts is bar_end_ts plus configured
    latency; ingested_at remains the local materialization timestamp.
    """

    if end_ts <= start_ts:
        msg = "end_ts must be greater than start_ts"
        raise DataFoundationValidationError(msg)
    registry = _validate_registry_path(registry_path)
    source = os.environ if env is None else env
    data_root = _require_data_root(source)
    instrument_config = load_cli_config(instrument_config_path)
    validation_config_mapping = load_cli_config(validation_config_path)
    validation_config = validation_config_from_mapping(validation_config_mapping)
    allow_non_fixture = bool(
        instrument_config.get("allow_non_fixture_input", False)
        or validation_config_mapping.get("allow_non_fixture_input", False)
    )
    raw_records = _discover_raw_records(
        data_root=data_root,
        allow_non_fixture_input=allow_non_fixture,
    )
    parsed_all = tuple(record for raw in raw_records for record in _parse_raw_csv(raw))
    parsed_window = _parsed_for_window(
        parsed_all,
        symbols=symbols,
        start_ts=start_ts,
        end_ts=end_ts,
    )
    deduped, dropped_count = _dedupe_parsed(parsed_window)
    settings_by_symbol = _settings_for_symbols(
        symbols=symbols,
        instrument_config=instrument_config,
    )
    canonical_inputs = _canonical_input_rows(
        deduped,
        settings_by_symbol=settings_by_symbol,
        data_version=data_version,
        latency=validation_config.available_latency,
    )
    calendar = _load_calendar(calendar_config_path, instrument_config)
    sessionized = sessionize_bars(
        canonical_inputs,
        calendar,
        available_latency=validation_config.available_latency,
        validate_existing_keys=False,
    )
    session_quality = evaluate_data_quality(
        sessionized,
        calendar,
        latency=validation_config.available_latency,
    )
    validation = validate_bars(session_quality.rows, config=validation_config)
    validation_issues = _quality_issue_counts(validation.issues)
    session_quality_issues = _quality_issue_counts(session_quality.issues)
    ingested_at = (now or datetime.now(UTC)).astimezone(UTC).replace(microsecond=0)
    canonical_bars: tuple[CanonicalBarRecord, ...] = ()
    quality_report: DataQualityReport | None = None
    coverage_report: CoverageReport | None = None

    if validation.valid:
        canonical_bars = _foundation_canonical_rows(session_quality.rows, ingested_at=ingested_at)
        expected_intervals = _expected_intervals(
            canonical_bars,
            symbols=symbols,
            partition_id=partition,
            settings_by_symbol=settings_by_symbol,
            calendar=calendar,
            start_ts=start_ts,
            end_ts=end_ts,
        )
        quality_report = DataQualityReport.from_canonical_bars(
            quality_report_id=f"dqr_{data_version}",
            dataset_version_id=data_version,
            bars=canonical_bars,
            expected_sessions=tuple(
                sorted({settings.session_label for settings in settings_by_symbol.values()})
            ),
            expected_gap_intervals=expected_intervals,
        )
        coverage_report = CoverageReport.from_canonical_bars(
            coverage_report_id=f"covr_{data_version}",
            dataset_version_id=data_version,
            bars=canonical_bars,
            expected_intervals=expected_intervals,
        )

    plan = _partition_plan(partition)
    plan.permits_coverage_qa(partition)
    require_governance_metadata_for_locked_partition_use(
        partition_id=partition,
        purpose="data_qa_coverage_inspection",
        plan=plan,
    )
    contamination_metadata = MappingProxyType(
        {
            "purpose": "data_qa_coverage_inspection",
            "partition_id": partition,
            "partition_plan_id": plan.plan_id,
            "contamination_metadata_rules": plan.contamination_metadata_rules,
        }
    )
    blocking = _blocking_summary(
        validation_valid=validation.valid,
        validation_issues=validation_issues,
        session_quality_issues=session_quality_issues,
        data_quality_report=quality_report,
        coverage_report=coverage_report,
    )
    quality_status = quality_report.status if quality_report is not None else ReportStatus.BLOCKING
    coverage_status = (
        coverage_report.coverage_status if coverage_report is not None else ReportStatus.BLOCKING
    )
    if (
        not validation.valid
        or session_quality.issues
        or quality_report is None
        or coverage_report is None
        or quality_report.blocks_versioning
        or coverage_report.blocks_versioning
    ):
        return MaterializeSummary(
            dataset_version_id=data_version,
            symbols=tuple(symbols),
            contract_universe=tuple(sorted({bar.contract_id for bar in canonical_bars})),
            start_ts=start_ts.isoformat(),
            end_ts=end_ts.isoformat(),
            raw_object_count=len(raw_records),
            parsed_row_count=len(parsed_window),
            canonical_row_count=len(canonical_bars),
            duplicate_rows_dropped=dropped_count,
            quality_status=quality_status.value,
            coverage_status=coverage_status.value,
            partition=partition,
            registry_path=None,
            registered=False,
            blocking_summary=blocking,
            contamination_metadata=contamination_metadata,
        )

    manifest_hash = _source_manifest_hash(
        raw_records=raw_records,
        symbols=symbols,
        start_ts=start_ts,
        end_ts=end_ts,
    )
    code_hash = hash_config(
        {
            "module": "alpha_system.data.ibkr.materialize",
            "canonical_schema": "foundation.CanonicalBarRecord",
        }
    )
    config_hash = hash_config(
        {
            "instrument_config": instrument_config,
            "validation_config": validation_config_mapping,
            "calendar_config_path": calendar_config_path.as_posix(),
            "partition_metadata": contamination_metadata,
        }
    )
    version = DatasetVersion.from_mapping(
        {
            "dataset_version_id": data_version,
            "source": SOURCE_ID,
            "symbol_universe": tuple(symbols),
            "bar_size": "1 min",
            "what_to_show": "TRADES",
            "start_ts": start_ts.isoformat(),
            "end_ts": end_ts.isoformat(),
            "contract_universe": tuple(sorted({bar.contract_id for bar in canonical_bars})),
            "roll_policy_id": next(iter(settings_by_symbol.values())).roll_policy_id,
            "manifest_hash": manifest_hash,
            "code_hash": code_hash,
            "config_hash": config_hash,
            "quality_report_hash": compute_quality_report_hash(quality_report),
            "created_at": ingested_at.isoformat(),
        }
    )
    source_manifest = {"manifest_hash": manifest_hash}
    persist_dataset_version(
        registry,
        version,
        quality_report=quality_report,
        coverage_report=coverage_report,
        source_manifest=source_manifest,
        code_hash=code_hash,
        config_hash=config_hash,
    )
    _persist_partition_metadata(
        registry_path=registry,
        dataset_version_id=data_version,
        created_at=ingested_at,
        config_hash=config_hash,
        metadata=contamination_metadata,
    )
    return MaterializeSummary(
        dataset_version_id=data_version,
        symbols=tuple(symbols),
        contract_universe=version.contract_universe,
        start_ts=start_ts.isoformat(),
        end_ts=end_ts.isoformat(),
        raw_object_count=len(raw_records),
        parsed_row_count=len(parsed_window),
        canonical_row_count=len(canonical_bars),
        duplicate_rows_dropped=dropped_count,
        quality_status=quality_report.status.value,
        coverage_status=coverage_report.coverage_status.value,
        partition=partition,
        registry_path=registry.as_posix(),
        registered=True,
        blocking_summary=blocking,
        contamination_metadata=contamination_metadata,
    )


def _print_summary(summary: MaterializeSummary) -> None:
    print(json.dumps(_json_ready(summary.to_mapping()), indent=2, sort_keys=True))


def main(argv: Sequence[str] | None = None) -> int:
    """CLI for ``python -m alpha_system.data.ibkr.materialize``."""

    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        summary = run_materialize(
            symbols=args.symbols,
            registry_path=args.registry_path,
            data_version=args.data_version,
            partition=args.partition,
            start_ts=args.start_ts,
            end_ts=args.end_ts,
            instrument_config_path=args.instrument_config,
            calendar_config_path=args.calendar_config,
            validation_config_path=args.validation_config,
        )
    except DataFoundationValidationError as exc:
        print(f"materialize blocked: {exc}", file=sys.stderr)
        return 2
    _print_summary(summary)
    return 0 if summary.registered else 1


if __name__ == "__main__":
    raise SystemExit(main())
