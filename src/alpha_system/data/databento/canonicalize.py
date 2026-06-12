"""Databento DBN to local canonical OHLCV-1m and BBO-1m records.

The module is offline by default for tests: callers may inject a normalized
record source and no Databento, pandas, or Parquet dependency is imported at
module import time.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from numbers import Integral, Real
from pathlib import Path
from types import MappingProxyType
from typing import Any

from alpha_system.core.hashing import hash_config
from alpha_system.data.cli_validation import load_cli_config, validation_config_from_mapping
from alpha_system.data.databento.manifest_files import DatabentoFileManifest
from alpha_system.data.databento.request_spec import (
    DATABENTO_DATASET,
    DatabentoRequestSpec,
    load_json_mapping,
    request_spec_hash,
    write_json_mapping,
)
from alpha_system.data.foundation.bars import CanonicalBarRecord
from alpha_system.data.foundation.quotes import (
    BBO_QUARANTINE_QUALITY_FLAG,
    MISSING_BBO_QUALITY_FLAG,
    CanonicalBBORecord,
)
from alpha_system.data.foundation.serialization import json_ready as _json_ready
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.data.ibkr.materialize import (
    _load_calendar,
    _repo_root,
    _settings_for_symbols,
    _validate_data_root,
)
from alpha_system.data.quality import OUT_OF_SESSION_FLAG, normalize_quality_flags
from alpha_system.data.sessionize import sessionize_bars

SOURCE_ID = "dsrc_databento_historical"
CANONICAL_PROVIDER_SEGMENT = "glbx_mdp3"
OHLCV_SCHEMA = "ohlcv-1m"
BBO_SCHEMA = "bbo-1m"
TBBO_SCHEMA = "tbbo"
OHLCV_PARTITION_SCHEMA = "ohlcv_1m"
BBO_PARTITION_SCHEMA = "bbo_1m"
TBBO_PARTITION_SCHEMA = "tbbo"
CANONICALIZE_SUPPORTED_SCHEMAS = frozenset((OHLCV_SCHEMA, BBO_SCHEMA, TBBO_SCHEMA))
SUPPORTED_ROOTS: frozenset[str] = frozenset({"ES", "NQ", "RTY"})
_PRICE_SCALE = Decimal("1000000000")
# Real DBN loads use price_type="fixed", so price fields are raw fixed-point
# integers scaled by 1e9. Databento undefined prices use INT64_MAX; quarantine
# that sentinel instead of scaling it into a bogus canonical price.
_DATABENTO_UNDEF_PRICE = 2**63 - 1

RecordSource = Callable[
    ...,
    Mapping[str, Iterable[Mapping[str, object]]] | Iterable[Mapping[str, object]],
]


@dataclass(frozen=True, slots=True)
class CanonicalizeSummary:
    """Redacted summary of local canonicalization output."""

    canonical_root: str
    ohlcv_data_version: str
    bbo_data_version: str
    symbols: tuple[str, ...]
    ohlcv_row_count: int
    bbo_row_count: int
    missing_bbo_row_count: int
    duplicate_rows_dropped: int
    quarantined_row_count: int
    output_paths: Mapping[str, tuple[str, ...]]
    storage_format: str
    source_manifest_hash: str
    request_spec_hash: str
    tbbo_data_version: str | None = None
    tbbo_row_count: int = 0

    def to_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "canonical_root": self.canonical_root,
                "ohlcv_data_version": self.ohlcv_data_version,
                "bbo_data_version": self.bbo_data_version,
                "symbols": self.symbols,
                "ohlcv_row_count": self.ohlcv_row_count,
                "bbo_row_count": self.bbo_row_count,
                "missing_bbo_row_count": self.missing_bbo_row_count,
                "duplicate_rows_dropped": self.duplicate_rows_dropped,
                "quarantined_row_count": self.quarantined_row_count,
                "output_paths": self.output_paths,
                "storage_format": self.storage_format,
                "source_manifest_hash": self.source_manifest_hash,
                "request_spec_hash": self.request_spec_hash,
                "tbbo_data_version": self.tbbo_data_version,
                "tbbo_row_count": self.tbbo_row_count,
            }
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class CanonicalTBBORecord:
    """Validated local trade-with-BBO record for Databento TBBO rows."""

    instrument_id: str
    contract_id: str
    series_id: str
    bar_start_ts: datetime
    bar_end_ts: datetime
    event_ts: datetime
    available_ts: datetime
    ingested_at: datetime
    trade_price: Decimal
    trade_size: Decimal
    aggressor_side: str
    bid: Decimal
    ask: Decimal
    bid_size: Decimal
    ask_size: Decimal
    mid: Decimal
    spread: Decimal
    source: str
    source_request_id: str
    data_version: str
    quality_flags: tuple[str, ...]
    session_label: str
    bid_order_count: int | None = None
    ask_order_count: int | None = None
    sequence: int | None = None
    ts_in_delta: int | None = None

    def __post_init__(self) -> None:
        instrument_id = _require_text_value(self.instrument_id, "instrument_id")
        contract_id = _require_text_value(self.contract_id, "contract_id")
        series_id = _require_text_value(self.series_id, "series_id")
        bar_start_ts = _parse_timestamp(self.bar_start_ts, "bar_start_ts")
        bar_end_ts = _parse_timestamp(self.bar_end_ts, "bar_end_ts")
        event_ts = _parse_timestamp(self.event_ts, "event_ts")
        available_ts = _parse_timestamp(self.available_ts, "available_ts")
        ingested_at = _parse_timestamp(self.ingested_at, "ingested_at")
        trade_price = _positive_decimal(self.trade_price, "trade_price")
        trade_size = _positive_decimal(self.trade_size, "trade_size")
        aggressor_side = _normalize_aggressor_side(self.aggressor_side)
        bid = _non_negative_decimal(self.bid, "bid")
        ask = _non_negative_decimal(self.ask, "ask")
        bid_size = _non_negative_decimal(self.bid_size, "bid_size")
        ask_size = _non_negative_decimal(self.ask_size, "ask_size")
        mid = _non_negative_decimal(self.mid, "mid")
        spread = _non_negative_decimal(self.spread, "spread")
        source = _require_text_value(self.source, "source")
        source_request_id = _require_text_value(self.source_request_id, "source_request_id")
        data_version = _require_text_value(self.data_version, "data_version")
        quality_flags = _normalize_quality_flag_values(self.quality_flags)
        session_label = _require_text_value(self.session_label, "session_label").upper()
        bid_order_count = _optional_int(self.bid_order_count)
        ask_order_count = _optional_int(self.ask_order_count)
        sequence = _optional_int(self.sequence)
        ts_in_delta = _optional_int(self.ts_in_delta)

        if bar_end_ts <= bar_start_ts:
            msg = "bar_end_ts must be greater than bar_start_ts"
            raise DataFoundationValidationError(msg)
        if event_ts < bar_start_ts or event_ts > bar_end_ts:
            msg = "event_ts must fall within the TBBO minute interval"
            raise DataFoundationValidationError(msg)
        if available_ts < event_ts:
            msg = "available_ts must be greater than or equal to event_ts"
            raise DataFoundationValidationError(msg)
        if ingested_at == available_ts:
            msg = "ingested_at must be distinct from available_ts"
            raise DataFoundationValidationError(msg)
        if ask < bid:
            msg = "ask must be greater than or equal to bid"
            raise DataFoundationValidationError(msg)
        expected_mid = (bid + ask) / Decimal("2")
        expected_spread = ask - bid
        if mid != expected_mid:
            msg = "mid must equal (bid + ask) / 2"
            raise DataFoundationValidationError(msg)
        if spread != expected_spread:
            msg = "spread must equal ask - bid"
            raise DataFoundationValidationError(msg)

        object.__setattr__(self, "instrument_id", instrument_id)
        object.__setattr__(self, "contract_id", contract_id)
        object.__setattr__(self, "series_id", series_id)
        object.__setattr__(self, "bar_start_ts", bar_start_ts)
        object.__setattr__(self, "bar_end_ts", bar_end_ts)
        object.__setattr__(self, "event_ts", event_ts)
        object.__setattr__(self, "available_ts", available_ts)
        object.__setattr__(self, "ingested_at", ingested_at)
        object.__setattr__(self, "trade_price", trade_price)
        object.__setattr__(self, "trade_size", trade_size)
        object.__setattr__(self, "aggressor_side", aggressor_side)
        object.__setattr__(self, "bid", bid)
        object.__setattr__(self, "ask", ask)
        object.__setattr__(self, "bid_size", bid_size)
        object.__setattr__(self, "ask_size", ask_size)
        object.__setattr__(self, "mid", mid)
        object.__setattr__(self, "spread", spread)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "source_request_id", source_request_id)
        object.__setattr__(self, "data_version", data_version)
        object.__setattr__(self, "quality_flags", quality_flags)
        object.__setattr__(self, "session_label", session_label)
        object.__setattr__(self, "bid_order_count", bid_order_count)
        object.__setattr__(self, "ask_order_count", ask_order_count)
        object.__setattr__(self, "sequence", sequence)
        object.__setattr__(self, "ts_in_delta", ts_in_delta)

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable local canonical TBBO mapping."""

        return MappingProxyType(
            {
                "instrument_id": self.instrument_id,
                "contract_id": self.contract_id,
                "series_id": self.series_id,
                "bar_start_ts": self.bar_start_ts.isoformat(),
                "bar_end_ts": self.bar_end_ts.isoformat(),
                "event_ts": self.event_ts.isoformat(),
                "available_ts": self.available_ts.isoformat(),
                "ingested_at": self.ingested_at.isoformat(),
                "trade_price": str(self.trade_price),
                "trade_size": str(self.trade_size),
                "aggressor_side": self.aggressor_side,
                "bid": str(self.bid),
                "ask": str(self.ask),
                "bid_size": str(self.bid_size),
                "ask_size": str(self.ask_size),
                "mid": str(self.mid),
                "spread": str(self.spread),
                "source": self.source,
                "source_request_id": self.source_request_id,
                "data_version": self.data_version,
                "quality_flags": self.quality_flags,
                "session_label": self.session_label,
                "bid_order_count": self.bid_order_count,
                "ask_order_count": self.ask_order_count,
                "sequence": self.sequence,
                "ts_in_delta": self.ts_in_delta,
            }
        )


def run_canonicalize(
    *,
    file_manifest_path: str | Path,
    request_spec: DatabentoRequestSpec | Mapping[str, object],
    output_root: str | Path,
    instrument_config_path: str | Path,
    calendar_config_path: str | Path,
    validation_config_path: str | Path,
    record_source: RecordSource | None = None,
    env: Mapping[str, str] | None = None,
    now: datetime | None = None,
) -> CanonicalizeSummary:
    """Canonicalize local Databento rows without provider calls."""

    spec = _coerce_request_spec(request_spec)
    manifest = DatabentoFileManifest.from_mapping(load_json_mapping(Path(file_manifest_path)))
    data_root = _require_data_root(env)
    output_base = _validate_output_root(Path(output_root), data_root=data_root)
    canonical_root = (
        output_base / "databento" / "canonical" / CANONICAL_PROVIDER_SEGMENT
    ).resolve(strict=False)

    instrument_config = load_cli_config(instrument_config_path)
    validation_mapping = load_cli_config(validation_config_path)
    validation_config = validation_config_from_mapping(validation_mapping)
    calendar = _load_calendar(Path(calendar_config_path), instrument_config)
    roots = tuple(_root_from_symbol(symbol) for symbol in spec.symbols)
    settings_by_symbol = _settings_for_symbols(
        symbols=roots,
        instrument_config=instrument_config,
    )
    ingested_at = _normalize_now(now)
    source_request_id = _source_request_id(manifest.manifest_hash)
    req_hash = request_spec_hash(spec)
    ohlcv_data_version = _data_version("ohlcv", manifest.manifest_hash, req_hash)
    bbo_data_version = _data_version("bbo", manifest.manifest_hash, req_hash)
    tbbo_data_version = _data_version("tbbo", manifest.manifest_hash, req_hash)
    rows_by_schema = _load_rows_by_schema(manifest, spec, record_source=record_source)
    requested_schemas = frozenset(spec.schemas)

    needs_ohlcv = OHLCV_SCHEMA in requested_schemas or BBO_SCHEMA in requested_schemas
    if needs_ohlcv:
        ohlcv_bars, ohlcv_duplicates, ohlcv_quarantine = _canonicalize_ohlcv(
            rows_by_schema.get(OHLCV_SCHEMA, ()),
            settings_by_symbol=settings_by_symbol,
            calendar=calendar,
            data_version=ohlcv_data_version,
            source_request_id=source_request_id,
            latency=validation_config.available_latency,
            ingested_at=ingested_at,
        )
        if not ohlcv_bars:
            msg = "Databento canonicalization produced no OHLCV bars"
            raise DataFoundationValidationError(msg)
    else:
        ohlcv_bars = ()
        ohlcv_duplicates = 0
        ohlcv_quarantine = 0

    if BBO_SCHEMA in requested_schemas:
        bbo_records, bbo_duplicates, bbo_quarantine, missing_bbo_count = _canonicalize_bbo(
            rows_by_schema.get(BBO_SCHEMA, ()),
            ohlcv_bars=ohlcv_bars,
            settings_by_symbol=settings_by_symbol,
            calendar=calendar,
            data_version=bbo_data_version,
            source_request_id=source_request_id,
            latency=validation_config.available_latency,
            ingested_at=ingested_at,
        )
        if not bbo_records:
            msg = "Databento canonicalization produced no BBO records"
            raise DataFoundationValidationError(msg)
    else:
        bbo_records = ()
        bbo_duplicates = 0
        bbo_quarantine = 0
        missing_bbo_count = 0

    if TBBO_SCHEMA in requested_schemas:
        tbbo_records, tbbo_duplicates, tbbo_quarantine = _canonicalize_tbbo(
            rows_by_schema.get(TBBO_SCHEMA, ()),
            settings_by_symbol=settings_by_symbol,
            calendar=calendar,
            data_version=tbbo_data_version,
            source_request_id=source_request_id,
            latency=validation_config.available_latency,
            ingested_at=ingested_at,
        )
        if not tbbo_records:
            msg = "Databento canonicalization produced no TBBO records"
            raise DataFoundationValidationError(msg)
    else:
        tbbo_records = ()
        tbbo_duplicates = 0
        tbbo_quarantine = 0

    output_paths: dict[str, tuple[str, ...]] = {}
    storage_formats: list[str] = []

    if OHLCV_SCHEMA in requested_schemas:
        ohlcv_paths, ohlcv_format = _write_schema_records(
            canonical_root=canonical_root,
            data_version=ohlcv_data_version,
            partition_schema=OHLCV_PARTITION_SCHEMA,
            records=ohlcv_bars,
        )
        storage_formats.append(ohlcv_format)
        output_paths[OHLCV_PARTITION_SCHEMA] = tuple(path.as_posix() for path in ohlcv_paths)
        _write_dataset_manifest(
            canonical_root=canonical_root,
            data_version=ohlcv_data_version,
            partition_schema=OHLCV_PARTITION_SCHEMA,
            paths=ohlcv_paths,
            row_count=len(ohlcv_bars),
            storage_format=ohlcv_format,
            source_manifest_hash=manifest.manifest_hash,
            request_hash=req_hash,
        )

    if BBO_SCHEMA in requested_schemas:
        bbo_paths, bbo_format = _write_schema_records(
            canonical_root=canonical_root,
            data_version=bbo_data_version,
            partition_schema=BBO_PARTITION_SCHEMA,
            records=bbo_records,
        )
        storage_formats.append(bbo_format)
        output_paths[BBO_PARTITION_SCHEMA] = tuple(path.as_posix() for path in bbo_paths)
        _write_dataset_manifest(
            canonical_root=canonical_root,
            data_version=bbo_data_version,
            partition_schema=BBO_PARTITION_SCHEMA,
            paths=bbo_paths,
            row_count=len(bbo_records),
            storage_format=bbo_format,
            source_manifest_hash=manifest.manifest_hash,
            request_hash=req_hash,
        )

    if TBBO_SCHEMA in requested_schemas:
        tbbo_paths, tbbo_format = _write_schema_records(
            canonical_root=canonical_root,
            data_version=tbbo_data_version,
            partition_schema=TBBO_PARTITION_SCHEMA,
            records=tbbo_records,
        )
        storage_formats.append(tbbo_format)
        output_paths[TBBO_PARTITION_SCHEMA] = tuple(path.as_posix() for path in tbbo_paths)
        _write_dataset_manifest(
            canonical_root=canonical_root,
            data_version=tbbo_data_version,
            partition_schema=TBBO_PARTITION_SCHEMA,
            paths=tbbo_paths,
            row_count=len(tbbo_records),
            storage_format=tbbo_format,
            source_manifest_hash=manifest.manifest_hash,
            request_hash=req_hash,
        )

    if not output_paths:
        supported_text = ", ".join(sorted(CANONICALIZE_SUPPORTED_SCHEMAS))
        msg = f"Databento canonicalization requires at least one schema in {supported_text}"
        raise DataFoundationValidationError(msg)

    return CanonicalizeSummary(
        canonical_root=canonical_root.as_posix(),
        ohlcv_data_version=ohlcv_data_version,
        bbo_data_version=bbo_data_version,
        symbols=roots,
        ohlcv_row_count=len(ohlcv_bars),
        bbo_row_count=len(bbo_records),
        missing_bbo_row_count=missing_bbo_count,
        duplicate_rows_dropped=ohlcv_duplicates + bbo_duplicates + tbbo_duplicates,
        quarantined_row_count=ohlcv_quarantine + bbo_quarantine + tbbo_quarantine,
        output_paths=MappingProxyType(output_paths),
        storage_format=_combined_storage_format(storage_formats),
        source_manifest_hash=manifest.manifest_hash,
        request_spec_hash=req_hash,
        tbbo_data_version=tbbo_data_version if TBBO_SCHEMA in requested_schemas else None,
        tbbo_row_count=len(tbbo_records),
    )


def _coerce_request_spec(
    request_spec: DatabentoRequestSpec | Mapping[str, object],
) -> DatabentoRequestSpec:
    return (
        request_spec
        if isinstance(request_spec, DatabentoRequestSpec)
        else DatabentoRequestSpec.from_mapping(request_spec)
    )


def _require_data_root(env: Mapping[str, str] | None) -> Path:
    source = os.environ if env is None else env
    value = source.get("ALPHA_DATA_ROOT")
    if value is None or not value.strip():
        msg = "ALPHA_DATA_ROOT is required for Databento canonicalization"
        raise DataFoundationValidationError(msg)
    return _validate_data_root(Path(value), _repo_root())


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _validate_output_root(output_root: Path, *, data_root: Path) -> Path:
    resolved = _validate_data_root(output_root, _repo_root())
    if resolved != data_root and not _is_relative_to(resolved, data_root):
        msg = "output_root must resolve under ALPHA_DATA_ROOT"
        raise DataFoundationValidationError(msg)
    return resolved


def _normalize_now(now: datetime | None) -> datetime:
    active = now or datetime.now(UTC)
    if active.tzinfo is None or active.utcoffset() is None:
        msg = "now must be timezone-aware"
        raise DataFoundationValidationError(msg)
    return active.astimezone(UTC).replace(microsecond=0)


def _source_request_id(manifest_hash: str | None) -> str:
    if not manifest_hash:
        msg = "Databento file manifest must expose manifest_hash"
        raise DataFoundationValidationError(msg)
    return "dbnmanifest_" + manifest_hash[:16]


def _data_version(kind: str, manifest_hash: str | None, request_hash: str) -> str:
    if not manifest_hash:
        msg = "Databento file manifest must expose manifest_hash"
        raise DataFoundationValidationError(msg)
    digest = hash_config(
        {
            "schema": "alpha_system.databento.canonical_dataset_version.v1",
            "kind": kind,
            "manifest_hash": manifest_hash,
            "request_spec_hash": request_hash,
        }
    )
    return f"dsv_databento_{kind}_{digest[:16]}"


def _load_rows_by_schema(
    manifest: DatabentoFileManifest,
    spec: DatabentoRequestSpec,
    *,
    record_source: RecordSource | None,
) -> Mapping[str, tuple[Mapping[str, object], ...]]:
    source_rows = (
        _load_real_dbn_rows(manifest)
        if record_source is None
        else record_source(file_manifest=manifest, request_spec=spec)
    )
    by_schema: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    if isinstance(source_rows, Mapping):
        iterable = (
            (str(schema), row)
            for schema, rows in source_rows.items()
            for row in _require_row_iterable(rows, str(schema))
        )
    else:
        iterable = ((_schema_from_row(row), row) for row in source_rows)

    allowed = set(spec.schemas)
    for schema, row in iterable:
        normalized_schema = schema.lower()
        if normalized_schema not in allowed:
            continue
        if normalized_schema not in CANONICALIZE_SUPPORTED_SCHEMAS:
            continue
        if not isinstance(row, Mapping):
            msg = "Databento record_source rows must be mappings"
            raise DataFoundationValidationError(msg)
        by_schema[normalized_schema].append(MappingProxyType(dict(row)))
    return MappingProxyType({schema: tuple(rows) for schema, rows in by_schema.items()})


def _require_row_iterable(value: object, schema: str) -> Iterable[Mapping[str, object]]:
    if isinstance(value, Mapping) or not isinstance(value, Iterable):
        msg = f"record_source schema {schema!r} must yield row mappings"
        raise DataFoundationValidationError(msg)
    return value


def _schema_from_row(row: Mapping[str, object]) -> str:
    for key in ("schema", "_schema"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
    msg = "record_source iterable rows must include schema or _schema"
    raise DataFoundationValidationError(msg)


def _load_real_dbn_rows(
    manifest: DatabentoFileManifest,
) -> Mapping[str, tuple[Mapping[str, object], ...]]:
    dbn_store = _load_dbn_store()
    by_schema: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    raw_root = Path(manifest.raw_root).expanduser().resolve(strict=False)
    _validate_data_root(raw_root, _repo_root())
    for file_record in manifest.files:
        if file_record.schema not in CANONICALIZE_SUPPORTED_SCHEMAS:
            continue
        path = (raw_root / file_record.relative_path).resolve(strict=False)
        if not _is_relative_to(path, raw_root):
            msg = "Databento manifest file path escaped raw_root"
            raise DataFoundationValidationError(msg)
        store = dbn_store.from_file(path)
        frame = store.to_df(price_type="fixed", pretty_ts=True, map_symbols=True)
        reset_index = getattr(frame, "reset_index", None)
        if callable(reset_index):
            frame = reset_index()
        to_dict = getattr(frame, "to_dict", None)
        if not callable(to_dict):
            msg = "DBNStore.to_df result must expose pandas-like to_dict"
            raise DataFoundationValidationError(msg)
        for row in to_dict("records"):
            if not isinstance(row, Mapping):
                msg = "DBNStore.to_df records must be mappings"
                raise DataFoundationValidationError(msg)
            values = dict(row)
            values.setdefault("job_id", file_record.job_id)
            by_schema[file_record.schema].append(MappingProxyType(values))
    return MappingProxyType({schema: tuple(rows) for schema, rows in by_schema.items()})


def _load_dbn_store() -> object:
    for module_name in ("databento_dbn", "databento"):
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            if exc.name != module_name:
                raise
            continue
        store = getattr(module, "DBNStore", None)
        if store is not None:
            return store
    msg = "DBNStore is required for real Databento DBN canonicalization"
    raise DataFoundationValidationError(msg)


def _canonicalize_ohlcv(
    rows: Iterable[Mapping[str, object]],
    *,
    settings_by_symbol: Mapping[str, object],
    calendar: object,
    data_version: str,
    source_request_id: str,
    latency: timedelta,
    ingested_at: datetime,
) -> tuple[tuple[CanonicalBarRecord, ...], int, int]:
    deduped: dict[tuple[str, datetime], Mapping[str, object]] = {}
    duplicate_count = 0
    quarantine_count = 0
    for row in rows:
        try:
            root = _root_from_symbol(_require_row_text(row, "symbol"))
            bar_start = _row_timestamp(row, "bar_start_ts", "ts_event", "pretty_ts_event")
        except DataFoundationValidationError:
            quarantine_count += 1
            continue
        key = (root, bar_start)
        if key in deduped:
            duplicate_count += 1
            continue
        deduped[key] = row

    canonical_inputs = []
    for (root, bar_start), row in sorted(deduped.items(), key=lambda item: item[0]):
        settings = settings_by_symbol[root]
        bar_end = bar_start + timedelta(minutes=1)
        canonical_inputs.append(
            {
                "instrument_id": settings.instrument_id,
                "session_id": "",
                "bar_index": -1,
                "bar_start_ts": bar_start,
                "bar_end_ts": bar_end,
                "event_ts": bar_end,
                "available_ts": bar_end + latency,
                "open": _price_decimal(row.get("open"), "open"),
                "high": _price_decimal(row.get("high"), "high"),
                "low": _price_decimal(row.get("low"), "low"),
                "close": _price_decimal(row.get("close"), "close"),
                "volume": _decimal_value(row.get("volume"), "volume"),
                "source": SOURCE_ID,
                "source_request_id": source_request_id,
                "data_version": data_version,
                "quality_flags": (),
                "symbol": root,
                "contract_id": getattr(
                    settings,
                    "contract_id",
                    f"contract_databento_{root.lower()}_v_0_front",
                ),
                "series_id": settings.series_id,
                "foundation_session_label": settings.session_label,
            }
        )

    sessionized = sessionize_bars(
        canonical_inputs,
        calendar,
        available_latency=latency,
        validate_existing_keys=False,
    )
    canonical: list[CanonicalBarRecord] = []
    for row in sessionized:
        if OUT_OF_SESSION_FLAG in normalize_quality_flags(row.get("quality_flags")):
            quarantine_count += 1
            continue
        try:
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
        except DataFoundationValidationError:
            quarantine_count += 1
    return tuple(canonical), duplicate_count, quarantine_count


def _canonicalize_bbo(
    rows: Iterable[Mapping[str, object]],
    *,
    ohlcv_bars: Sequence[CanonicalBarRecord],
    settings_by_symbol: Mapping[str, object],
    calendar: object,
    data_version: str,
    source_request_id: str,
    latency: timedelta,
    ingested_at: datetime,
) -> tuple[tuple[CanonicalBBORecord, ...], int, int, int]:
    ohlcv_by_key = {
        (_root_from_instrument_id(bar.instrument_id, settings_by_symbol), bar.bar_start_ts): bar
        for bar in ohlcv_bars
    }
    deduped: dict[tuple[str, datetime], Mapping[str, object]] = {}
    duplicate_count = 0
    quarantine_count = 0
    for row in rows:
        try:
            root = _root_from_symbol(_require_row_text(row, "symbol"))
            bar_start = _bbo_bar_start(row, root=root, ohlcv_by_key=ohlcv_by_key)
        except DataFoundationValidationError:
            quarantine_count += 1
            continue
        key = (root, bar_start)
        if key in deduped:
            duplicate_count += 1
            continue
        deduped[key] = row

    canonical_by_key: dict[tuple[str, datetime], CanonicalBBORecord] = {}
    quarantined_by_key: set[tuple[str, datetime]] = set()
    for (root, bar_start), row in sorted(deduped.items(), key=lambda item: item[0]):
        ohlcv_bar = ohlcv_by_key.get((root, bar_start))
        if ohlcv_bar is None:
            quarantine_count += 1
            continue
        try:
            record = _bbo_record_from_row(
                row,
                root=root,
                ohlcv_bar=ohlcv_bar,
                settings_by_symbol=settings_by_symbol,
                data_version=data_version,
                source_request_id=source_request_id,
                latency=latency,
                ingested_at=ingested_at,
            )
        except DataFoundationValidationError:
            quarantine_count += 1
            quarantined_by_key.add((root, bar_start))
            continue
        canonical_by_key[(root, bar_start)] = record

    missing_count = 0
    output = []
    for root, bar_start in sorted(ohlcv_by_key):
        record = canonical_by_key.get((root, bar_start))
        if record is None:
            missing_count += 1
            record = _missing_bbo_record(
                root=root,
                ohlcv_bar=ohlcv_by_key[(root, bar_start)],
                data_version=data_version,
                source_request_id=source_request_id,
                latency=latency,
                ingested_at=ingested_at,
                quarantined_raw_bbo=(root, bar_start) in quarantined_by_key,
            )
        output.append(record)

    sessionized = sessionize_bars(
        (
            {
                "instrument_id": record.instrument_id,
                "session_id": "",
                "bar_index": -1,
                "bar_start_ts": record.bar_start_ts,
                "bar_end_ts": record.bar_end_ts,
                "quality_flags": record.quality_flags,
            }
            for record in output
        ),
        calendar,
        available_latency=latency,
        validate_existing_keys=False,
    )
    out_of_session_keys = {
        (row["instrument_id"], row["bar_start_ts"])
        for row in sessionized
        if OUT_OF_SESSION_FLAG in normalize_quality_flags(row.get("quality_flags"))
    }
    if out_of_session_keys:
        quarantine_count += len(out_of_session_keys)
        output = [
            record
            for record in output
            if (record.instrument_id, record.bar_start_ts) not in out_of_session_keys
        ]
    return tuple(output), duplicate_count, quarantine_count, missing_count


def _canonicalize_tbbo(
    rows: Iterable[Mapping[str, object]],
    *,
    settings_by_symbol: Mapping[str, object],
    calendar: object,
    data_version: str,
    source_request_id: str,
    latency: timedelta,
    ingested_at: datetime,
) -> tuple[tuple[CanonicalTBBORecord, ...], int, int]:
    deduped: dict[
        tuple[str, datetime, object, str, str, str, str, str],
        tuple[str, datetime, Mapping[str, object]],
    ] = {}
    duplicate_count = 0
    quarantine_count = 0
    for row in rows:
        try:
            root = _root_from_symbol(_require_row_text(row, "symbol"))
            event_ts = _row_timestamp(row, "ts_event", "pretty_ts_event", "event_ts")
        except DataFoundationValidationError:
            quarantine_count += 1
            continue
        key = _tbbo_dedupe_key(row, root=root, event_ts=event_ts)
        if key in deduped:
            duplicate_count += 1
            continue
        deduped[key] = (root, event_ts, row)

    session_inputs = []
    for key, (root, event_ts, _row) in sorted(deduped.items(), key=lambda item: item[0]):
        settings = settings_by_symbol[root]
        bar_start = _minute_start(event_ts)
        session_inputs.append(
            {
                "_tbbo_key": key,
                "instrument_id": settings.instrument_id,
                "session_id": "",
                "bar_index": -1,
                "bar_start_ts": bar_start,
                "bar_end_ts": bar_start + timedelta(minutes=1),
                "quality_flags": (),
            }
        )
    sessionized = {
        row["_tbbo_key"]: row
        for row in sessionize_bars(
            session_inputs,
            calendar,
            available_latency=latency,
            validate_existing_keys=False,
        )
    }

    output = []
    for key, (root, event_ts, row) in sorted(deduped.items(), key=lambda item: item[0]):
        session_row = sessionized[key]
        if OUT_OF_SESSION_FLAG in normalize_quality_flags(session_row.get("quality_flags")):
            quarantine_count += 1
            continue
        try:
            output.append(
                _tbbo_record_from_row(
                    row,
                    root=root,
                    event_ts=event_ts,
                    session_row=session_row,
                    settings_by_symbol=settings_by_symbol,
                    data_version=data_version,
                    source_request_id=source_request_id,
                    latency=latency,
                    ingested_at=ingested_at,
                )
            )
        except DataFoundationValidationError:
            quarantine_count += 1
    return tuple(output), duplicate_count, quarantine_count


def _tbbo_record_from_row(
    row: Mapping[str, object],
    *,
    root: str,
    event_ts: datetime,
    session_row: Mapping[str, object],
    settings_by_symbol: Mapping[str, object],
    data_version: str,
    source_request_id: str,
    latency: timedelta,
    ingested_at: datetime,
) -> CanonicalTBBORecord:
    settings = settings_by_symbol[root]
    bid = _price_decimal(row.get("bid_px_00", row.get("bid")), "bid_px_00")
    ask = _price_decimal(row.get("ask_px_00", row.get("ask")), "ask_px_00")
    if ask < bid:
        msg = "Databento TBBO crossed quote quarantined"
        raise DataFoundationValidationError(msg)
    bid_size = _decimal_value(row.get("bid_sz_00", row.get("bid_size")), "bid_sz_00")
    ask_size = _decimal_value(row.get("ask_sz_00", row.get("ask_size")), "ask_sz_00")
    trade_price = _price_decimal(row.get("price", row.get("trade_price")), "price")
    trade_size = _decimal_value(row.get("size", row.get("trade_size")), "size")
    bar_start = session_row["bar_start_ts"]
    bar_end = session_row["bar_end_ts"]
    return CanonicalTBBORecord(
        instrument_id=settings.instrument_id,
        contract_id=getattr(
            settings,
            "contract_id",
            f"contract_databento_{root.lower()}_v_0_front",
        ),
        series_id=settings.series_id,
        bar_start_ts=bar_start,
        bar_end_ts=bar_end,
        event_ts=event_ts,
        available_ts=event_ts + latency,
        ingested_at=ingested_at,
        trade_price=trade_price,
        trade_size=trade_size,
        aggressor_side=row.get("side", row.get("aggressor_side")),
        bid=bid,
        ask=ask,
        bid_size=bid_size,
        ask_size=ask_size,
        mid=(bid + ask) / Decimal("2"),
        spread=ask - bid,
        source=SOURCE_ID,
        source_request_id=source_request_id,
        data_version=data_version,
        quality_flags=normalize_quality_flags(session_row.get("quality_flags")),
        session_label=settings.session_label,
        bid_order_count=_optional_int(row.get("bid_ct_00", row.get("bid_order_count"))),
        ask_order_count=_optional_int(row.get("ask_ct_00", row.get("ask_order_count"))),
        sequence=_optional_int(row.get("sequence")),
        ts_in_delta=_optional_int(row.get("ts_in_delta")),
    )


def _tbbo_dedupe_key(
    row: Mapping[str, object],
    *,
    root: str,
    event_ts: datetime,
) -> tuple[str, datetime, object, str, str, str, str, str]:
    return (
        root,
        event_ts,
        row.get("sequence"),
        str(row.get("price", row.get("trade_price"))),
        str(row.get("size", row.get("trade_size"))),
        str(row.get("side", row.get("aggressor_side"))),
        str(row.get("bid_px_00", row.get("bid"))),
        str(row.get("ask_px_00", row.get("ask"))),
    )


def _minute_start(value: datetime) -> datetime:
    return value.replace(second=0, microsecond=0)


def _bbo_record_from_row(
    row: Mapping[str, object],
    *,
    root: str,
    ohlcv_bar: CanonicalBarRecord,
    settings_by_symbol: Mapping[str, object],
    data_version: str,
    source_request_id: str,
    latency: timedelta,
    ingested_at: datetime,
) -> CanonicalBBORecord:
    del settings_by_symbol
    bid = _price_decimal(row.get("bid_px_00", row.get("bid")), "bid_px_00")
    ask = _price_decimal(row.get("ask_px_00", row.get("ask")), "ask_px_00")
    if ask < bid:
        msg = "Databento BBO crossed quote quarantined"
        raise DataFoundationValidationError(msg)
    bid_size = _decimal_value(row.get("bid_sz_00", row.get("bid_size")), "bid_sz_00")
    ask_size = _decimal_value(row.get("ask_sz_00", row.get("ask_size")), "ask_sz_00")
    event_ts = _row_timestamp(row, "ts_event", "pretty_ts_event", "event_ts")
    bar_start = _bbo_bar_start(
        row,
        root=root,
        ohlcv_by_key={(root, ohlcv_bar.bar_start_ts): ohlcv_bar},
    )
    if bar_start != ohlcv_bar.bar_start_ts:
        msg = "Databento BBO row does not align to OHLCV minute"
        raise DataFoundationValidationError(msg)
    if event_ts < ohlcv_bar.bar_start_ts or event_ts > ohlcv_bar.bar_end_ts:
        msg = "Databento BBO ts_event outside OHLCV minute quarantined"
        raise DataFoundationValidationError(msg)
    bid_order_count = _optional_int(row.get("bid_ct_00", row.get("bid_order_count")))
    ask_order_count = _optional_int(row.get("ask_ct_00", row.get("ask_order_count")))
    spread = ask - bid
    return CanonicalBBORecord.from_mapping(
        {
            "instrument_id": ohlcv_bar.instrument_id,
            "contract_id": ohlcv_bar.contract_id,
            "series_id": ohlcv_bar.series_id,
            "bar_start_ts": ohlcv_bar.bar_start_ts,
            "bar_end_ts": ohlcv_bar.bar_end_ts,
            "event_ts": event_ts,
            "available_ts": ohlcv_bar.bar_end_ts + latency,
            "ingested_at": ingested_at,
            "bid": bid,
            "ask": ask,
            "bid_size": bid_size,
            "ask_size": ask_size,
            "mid": (bid + ask) / Decimal("2"),
            "spread": spread,
            "source": SOURCE_ID,
            "source_request_id": source_request_id,
            "data_version": data_version,
            "quality_flags": (),
            "session_label": ohlcv_bar.session_label,
            "spread_ticks": None,
            "microprice": None,
            "bid_order_count": bid_order_count,
            "ask_order_count": ask_order_count,
        }
    )


def _missing_bbo_record(
    *,
    root: str,
    ohlcv_bar: CanonicalBarRecord,
    data_version: str,
    source_request_id: str,
    latency: timedelta,
    ingested_at: datetime,
    quarantined_raw_bbo: bool = False,
) -> CanonicalBBORecord:
    del root
    quality_flags = (
        (MISSING_BBO_QUALITY_FLAG, BBO_QUARANTINE_QUALITY_FLAG)
        if quarantined_raw_bbo
        else (MISSING_BBO_QUALITY_FLAG,)
    )
    return CanonicalBBORecord.from_mapping(
        {
            "instrument_id": ohlcv_bar.instrument_id,
            "contract_id": ohlcv_bar.contract_id,
            "series_id": ohlcv_bar.series_id,
            "bar_start_ts": ohlcv_bar.bar_start_ts,
            "bar_end_ts": ohlcv_bar.bar_end_ts,
            "event_ts": ohlcv_bar.bar_end_ts,
            "available_ts": ohlcv_bar.bar_end_ts + latency,
            "ingested_at": ingested_at,
            "bid": Decimal("0"),
            "ask": Decimal("0"),
            "bid_size": Decimal("0"),
            "ask_size": Decimal("0"),
            "mid": Decimal("0"),
            "spread": Decimal("0"),
            "source": SOURCE_ID,
            "source_request_id": source_request_id,
            "data_version": data_version,
            "quality_flags": quality_flags,
            "session_label": ohlcv_bar.session_label,
            "spread_ticks": None,
            "microprice": None,
            "bid_order_count": 0,
            "ask_order_count": 0,
        }
    )


def _bbo_bar_start(
    row: Mapping[str, object],
    *,
    root: str,
    ohlcv_by_key: Mapping[tuple[str, datetime], CanonicalBarRecord],
) -> datetime:
    if row.get("bar_start_ts") is not None:
        return _row_timestamp(row, "bar_start_ts")
    event_ts = _row_timestamp(row, "ts_event", "pretty_ts_event", "event_ts")
    floored = event_ts.replace(second=0, microsecond=0)
    candidates = (floored, floored - timedelta(minutes=1))
    for candidate in candidates:
        if (root, candidate) in ohlcv_by_key:
            return candidate
    return floored


def _root_from_symbol(symbol: str) -> str:
    root = symbol.replace(".", " ").split()[0].upper()
    if root not in SUPPORTED_ROOTS:
        msg = "Databento canonicalization is scoped to ES/NQ/RTY"
        raise DataFoundationValidationError(msg)
    return root


def _root_from_instrument_id(
    instrument_id: str,
    settings_by_symbol: Mapping[str, object],
) -> str:
    for symbol, settings in settings_by_symbol.items():
        if settings.instrument_id == instrument_id:
            return symbol
    msg = f"instrument_id does not resolve to Databento root: {instrument_id}"
    raise DataFoundationValidationError(msg)


def _require_row_text(row: Mapping[str, object], field_name: str) -> str:
    value = row.get(field_name)
    if not isinstance(value, str) or not value.strip():
        msg = f"Databento row missing {field_name}"
        raise DataFoundationValidationError(msg)
    return value.strip()


def _require_text_value(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        msg = f"{field_name} must be a non-empty string"
        raise DataFoundationValidationError(msg)
    normalized = value.strip()
    if "\n" in normalized or "\r" in normalized:
        msg = f"{field_name} must be a single-line string"
        raise DataFoundationValidationError(msg)
    return normalized


def _row_timestamp(row: Mapping[str, object], *field_names: str) -> datetime:
    for field_name in field_names:
        value = row.get(field_name)
        if value is not None:
            return _parse_timestamp(value, field_name)
    msg = "Databento row missing timestamp field: " + ", ".join(field_names)
    raise DataFoundationValidationError(msg)


def _parse_timestamp(value: object, field_name: str) -> datetime:
    to_pydatetime = getattr(value, "to_pydatetime", None)
    if callable(to_pydatetime):
        value = to_pydatetime()
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, int) and not isinstance(value, bool):
        seconds, nanoseconds = divmod(value, 1_000_000_000)
        parsed = datetime.fromtimestamp(seconds, UTC) + timedelta(
            microseconds=nanoseconds // 1000
        )
    elif isinstance(value, str):
        raw = value.strip()
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError as exc:
            msg = f"{field_name} must be an ISO-8601 timestamp or UTC ns integer"
            raise DataFoundationValidationError(msg) from exc
    else:
        msg = f"{field_name} must be a timestamp"
        raise DataFoundationValidationError(msg)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        msg = f"{field_name} must be timezone-aware"
        raise DataFoundationValidationError(msg)
    return parsed.astimezone(UTC)


def _price_decimal(value: object, field_name: str) -> Decimal:
    if isinstance(value, Integral) and not isinstance(value, bool):
        raw_value = int(value)
        if raw_value == _DATABENTO_UNDEF_PRICE:
            msg = f"{field_name} is undefined"
            raise DataFoundationValidationError(msg)
        return Decimal(raw_value) / _PRICE_SCALE
    if isinstance(value, str) and value.strip() == str(_DATABENTO_UNDEF_PRICE):
        msg = f"{field_name} is undefined"
        raise DataFoundationValidationError(msg)
    if isinstance(value, Real):
        msg = f"{field_name} must be a raw fixed-point integer or exact decimal text"
        raise DataFoundationValidationError(msg)
    return _decimal_value(value, field_name)


def _decimal_value(value: object, field_name: str) -> Decimal:
    if value is None or isinstance(value, bool):
        msg = f"{field_name} must be a finite decimal"
        raise DataFoundationValidationError(msg)
    if isinstance(value, Decimal):
        parsed = value
    else:
        try:
            parsed = Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            msg = f"{field_name} must be a finite decimal"
            raise DataFoundationValidationError(msg) from exc
    if not parsed.is_finite():
        msg = f"{field_name} must be finite"
        raise DataFoundationValidationError(msg)
    return parsed


def _positive_decimal(value: object, field_name: str) -> Decimal:
    parsed = _decimal_value(value, field_name)
    if parsed <= 0:
        msg = f"{field_name} must be positive"
        raise DataFoundationValidationError(msg)
    return parsed


def _non_negative_decimal(value: object, field_name: str) -> Decimal:
    parsed = _decimal_value(value, field_name)
    if parsed < 0:
        msg = f"{field_name} must be non-negative"
        raise DataFoundationValidationError(msg)
    return parsed


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    if isinstance(value, bool):
        msg = "optional BBO count must be an integer"
        raise DataFoundationValidationError(msg)
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        msg = "optional BBO count must be an integer"
        raise DataFoundationValidationError(msg) from exc
    if parsed < 0:
        msg = "optional BBO count must be non-negative"
        raise DataFoundationValidationError(msg)
    return parsed


def _normalize_quality_flag_values(value: object) -> tuple[str, ...]:
    flags = normalize_quality_flags(value)
    duplicates = sorted({flag for flag in flags if flags.count(flag) > 1})
    if duplicates:
        msg = "quality_flags must not contain duplicate values: "
        raise DataFoundationValidationError(msg + ", ".join(duplicates))
    return flags


def _normalize_aggressor_side(value: object) -> str:
    side = _require_text_value(value, "aggressor_side").strip().lower()
    aliases = {
        "a": "ask",
        "ask": "ask",
        "b": "bid",
        "bid": "bid",
        "n": "none",
        "none": "none",
        "unknown": "none",
    }
    try:
        return aliases[side]
    except KeyError as exc:
        msg = "aggressor_side must be one of A, B, N, ask, bid, or none"
        raise DataFoundationValidationError(msg) from exc


def _combined_storage_format(storage_formats: Sequence[str]) -> str:
    unique = set(storage_formats)
    if not unique:
        return "none"
    return unique.pop() if len(unique) == 1 else "mixed"


def _record_root(record: CanonicalBarRecord | CanonicalBBORecord | CanonicalTBBORecord) -> str:
    if "_es" in record.instrument_id:
        return "ES"
    if "_nq" in record.instrument_id:
        return "NQ"
    if "_rty" in record.instrument_id:
        return "RTY"
    return record.instrument_id.rsplit("_", maxsplit=1)[-1].upper()


def _write_schema_records(
    *,
    canonical_root: Path,
    data_version: str,
    partition_schema: str,
    records: Sequence[CanonicalBarRecord | CanonicalBBORecord | CanonicalTBBORecord],
) -> tuple[tuple[Path, ...], str]:
    paths = []
    formats = set()
    by_root: dict[
        str,
        list[CanonicalBarRecord | CanonicalBBORecord | CanonicalTBBORecord],
    ] = defaultdict(list)
    for record in records:
        by_root[_record_root(record)].append(record)

    for root, root_records in sorted(by_root.items()):
        output_dir = (
            canonical_root
            / data_version
            / f"schema={partition_schema}"
            / f"root={root}"
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        path, storage_format = _write_records_file(output_dir / "part-00000.parquet", root_records)
        paths.append(path)
        formats.add(storage_format)
    return tuple(paths), formats.pop() if len(formats) == 1 else "mixed"


def _write_records_file(
    path: Path,
    records: Sequence[CanonicalBarRecord | CanonicalBBORecord | CanonicalTBBORecord],
) -> tuple[Path, str]:
    rows = [dict(_json_ready(record.to_mapping())) for record in records]
    pyarrow = _optional_module("pyarrow")
    if pyarrow is not None:
        parquet = importlib.import_module("pyarrow.parquet")
        table = pyarrow.Table.from_pylist(rows)
        parquet.write_table(table, path)
        return path, "parquet"

    polars = _optional_module("polars")
    if polars is not None:
        polars.DataFrame(rows).write_parquet(path.as_posix())
        return path, "parquet"

    fallback = path.with_suffix(path.suffix + ".jsonl")
    with fallback.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")))
            handle.write("\n")
    return fallback, "jsonl_fallback_no_parquet_dependency"


def _optional_module(module_name: str) -> Any | None:
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name == module_name:
            return None
        raise


def _write_dataset_manifest(
    *,
    canonical_root: Path,
    data_version: str,
    partition_schema: str,
    paths: Sequence[Path],
    row_count: int,
    storage_format: str,
    source_manifest_hash: str | None,
    request_hash: str,
) -> None:
    if source_manifest_hash is None:
        msg = "source manifest hash is required"
        raise DataFoundationValidationError(msg)
    manifest_path = canonical_root / data_version / "manifest.json"
    write_json_mapping(
        manifest_path,
        {
            "schema": "alpha_system.databento.canonical_manifest.v1",
            "dataset": DATABENTO_DATASET,
            "data_version": data_version,
            "partition_schema": partition_schema,
            "row_count": row_count,
            "storage_format": storage_format,
            "paths": tuple(path.as_posix() for path in paths),
            "source_manifest_hash": source_manifest_hash,
            "request_spec_hash": request_hash,
        },
    )


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Canonicalize local Databento DBN files into OHLCV-1m, BBO-1m, "
            "and TBBO refs"
        ),
    )
    parser.add_argument("--file-manifest", type=Path, required=True)
    parser.add_argument("--request-spec", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--instrument-config", type=Path, required=True)
    parser.add_argument("--calendar-config", type=Path, required=True)
    parser.add_argument("--validation-config", type=Path, required=True)
    return parser.parse_args(argv)


def _print_summary(summary: CanonicalizeSummary) -> None:
    print(json.dumps(_json_ready(summary.to_mapping()), indent=2, sort_keys=True))


def main(argv: Sequence[str] | None = None) -> int:
    """CLI for ``python -m alpha_system.data.databento.canonicalize``."""

    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        summary = run_canonicalize(
            file_manifest_path=args.file_manifest,
            request_spec=DatabentoRequestSpec.from_mapping(load_json_mapping(args.request_spec)),
            output_root=args.output_root,
            instrument_config_path=args.instrument_config,
            calendar_config_path=args.calendar_config,
            validation_config_path=args.validation_config,
        )
    except DataFoundationValidationError as exc:
        print(f"canonicalize blocked: {exc}", file=sys.stderr)
        return 2
    _print_summary(summary)
    return 0


__all__ = ["CanonicalTBBORecord", "CanonicalizeSummary", "main", "run_canonicalize"]


if __name__ == "__main__":
    raise SystemExit(main())
