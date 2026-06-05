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
from alpha_system.data.foundation.quotes import MISSING_BBO_QUALITY_FLAG, CanonicalBBORecord
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.data.ibkr._json_utils import json_ready as _json_ready
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
OHLCV_PARTITION_SCHEMA = "ohlcv_1m"
BBO_PARTITION_SCHEMA = "bbo_1m"
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
    rows_by_schema = _load_rows_by_schema(manifest, spec, record_source=record_source)

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

    ohlcv_paths, ohlcv_format = _write_schema_records(
        canonical_root=canonical_root,
        data_version=ohlcv_data_version,
        partition_schema=OHLCV_PARTITION_SCHEMA,
        records=ohlcv_bars,
    )
    bbo_paths, bbo_format = _write_schema_records(
        canonical_root=canonical_root,
        data_version=bbo_data_version,
        partition_schema=BBO_PARTITION_SCHEMA,
        records=bbo_records,
    )
    storage_format = ohlcv_format if ohlcv_format == bbo_format else "mixed"
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

    return CanonicalizeSummary(
        canonical_root=canonical_root.as_posix(),
        ohlcv_data_version=ohlcv_data_version,
        bbo_data_version=bbo_data_version,
        symbols=roots,
        ohlcv_row_count=len(ohlcv_bars),
        bbo_row_count=len(bbo_records),
        missing_bbo_row_count=missing_bbo_count,
        duplicate_rows_dropped=ohlcv_duplicates + bbo_duplicates,
        quarantined_row_count=ohlcv_quarantine + bbo_quarantine,
        output_paths=MappingProxyType(
            {
                OHLCV_PARTITION_SCHEMA: tuple(path.as_posix() for path in ohlcv_paths),
                BBO_PARTITION_SCHEMA: tuple(path.as_posix() for path in bbo_paths),
            }
        ),
        storage_format=storage_format,
        source_manifest_hash=manifest.manifest_hash,
        request_spec_hash=req_hash,
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
        if normalized_schema not in {OHLCV_SCHEMA, BBO_SCHEMA}:
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
        if file_record.schema not in {OHLCV_SCHEMA, BBO_SCHEMA}:
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
) -> CanonicalBBORecord:
    del root
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
            "quality_flags": (MISSING_BBO_QUALITY_FLAG,),
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


def _record_root(record: CanonicalBarRecord | CanonicalBBORecord) -> str:
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
    records: Sequence[CanonicalBarRecord | CanonicalBBORecord],
) -> tuple[tuple[Path, ...], str]:
    paths = []
    formats = set()
    by_root: dict[str, list[CanonicalBarRecord | CanonicalBBORecord]] = defaultdict(list)
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
    records: Sequence[CanonicalBarRecord | CanonicalBBORecord],
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
        description="Canonicalize local Databento DBN files into OHLCV-1m and BBO-1m refs",
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


__all__ = ["CanonicalizeSummary", "main", "run_canonicalize"]


if __name__ == "__main__":
    raise SystemExit(main())
