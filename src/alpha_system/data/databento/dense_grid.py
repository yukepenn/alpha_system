"""Build a dense Databento OHLCV-1m research grid from sparse provider truth."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType
from typing import Any

from alpha_system.core.hashing import hash_config, hash_file
from alpha_system.data.cli_validation import load_cli_config, validation_config_from_mapping
from alpha_system.data.databento.canonicalize import (
    CANONICAL_PROVIDER_SEGMENT,
    OHLCV_PARTITION_SCHEMA,
    _write_dataset_manifest,
    _write_schema_records,
)
from alpha_system.data.databento.coverage import (
    DEFAULT_MAX_CONTIGUOUS_NO_TRADE_MINUTES,
    LONG_NO_TRADE_RUN,
    PROVIDER_DATA_GAP,
    SUSPECTED_NON_TRADING_SESSION,
    expected_intervals_for_symbols,
)
from alpha_system.data.databento.request_spec import (
    DatabentoRequestSpec,
    load_json_mapping,
    request_spec_hash,
)
from alpha_system.data.foundation.bars import CanonicalBarRecord
from alpha_system.data.foundation.grid import (
    NO_TRADE_QUALITY_FLAG,
    PREVIOUS_CLOSE_FILL_METHOD,
    DenseGridBarRecord,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.data.ibkr._json_utils import json_ready as _json_ready
from alpha_system.data.ibkr.materialize import (
    _load_calendar,
    _repo_root,
    _settings_for_symbols,
    _validate_data_root,
)

DENSE_OHLCV_PARTITION_SCHEMA = "ohlcv_1m_dense"
DENSE_GRID_PARTITION_ID = "dense_grid"


@dataclass(frozen=True, slots=True)
class DenseGridSummary:
    """Redacted summary of dense-grid construction."""

    canonical_root: str
    sparse_ohlcv_data_version: str
    dense_data_version: str
    symbols: tuple[str, ...]
    row_count: int
    counts_by_symbol: Mapping[str, Mapping[str, object]]
    provider_gap_sessions: tuple[Mapping[str, object], ...]
    suspected_non_trading_sessions: tuple[Mapping[str, object], ...]
    output_paths: Mapping[str, tuple[str, ...]]
    storage_format: str
    source_manifest_hash: str
    request_spec_hash: str

    def to_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "canonical_root": self.canonical_root,
                "sparse_ohlcv_data_version": self.sparse_ohlcv_data_version,
                "dense_data_version": self.dense_data_version,
                "symbols": self.symbols,
                "row_count": self.row_count,
                "counts_by_symbol": self.counts_by_symbol,
                "provider_gap_sessions": self.provider_gap_sessions,
                "suspected_non_trading_sessions": self.suspected_non_trading_sessions,
                "output_paths": self.output_paths,
                "storage_format": self.storage_format,
                "source_manifest_hash": self.source_manifest_hash,
                "request_spec_hash": self.request_spec_hash,
            }
        )


def run_dense_grid(
    *,
    sparse_canonical_root: str | Path,
    ohlcv_data_version: str,
    request_spec: DatabentoRequestSpec | Mapping[str, object],
    output_root: str | Path,
    dense_data_version: str,
    instrument_config_path: str | Path,
    calendar_config_path: str | Path,
    validation_config_path: str | Path,
    env: Mapping[str, str] | None = None,
    now: datetime | None = None,
) -> DenseGridSummary:
    """Create the derived dense research grid without provider/API access."""

    spec = _coerce_request_spec(request_spec)
    data_root = _require_data_root(env)
    sparse_root = _validate_canonical_root(Path(sparse_canonical_root), data_root=data_root)
    output_base = _validate_output_root(Path(output_root), data_root=data_root)
    canonical_root = (
        output_base / "databento" / "canonical" / CANONICAL_PROVIDER_SEGMENT
    ).resolve(strict=False)

    instrument_config = load_cli_config(instrument_config_path)
    validation_mapping = load_cli_config(validation_config_path)
    validation_config = validation_config_from_mapping(validation_mapping)
    max_no_trade = _max_contiguous_no_trade_minutes(validation_mapping)
    calendar = _load_calendar(Path(calendar_config_path), instrument_config)
    roots = tuple(_root_from_symbol(symbol) for symbol in spec.symbols)
    settings_by_symbol = _settings_for_symbols(
        symbols=roots,
        instrument_config=instrument_config,
    )
    ingested_at = _normalize_now(now)
    sparse_bars = _read_ohlcv_records(sparse_root, ohlcv_data_version)
    expected_intervals = expected_intervals_for_symbols(
        symbols=roots,
        partition_id=DENSE_GRID_PARTITION_ID,
        settings_by_symbol=settings_by_symbol,
        calendar=calendar,
        start_ts=spec.start,
        end_ts=spec.end,
    )
    (
        dense_rows,
        counts_by_symbol,
        provider_gap_sessions,
        suspected_non_trading_sessions,
    ) = _build_dense_rows(
        sparse_bars=sparse_bars,
        expected_intervals=expected_intervals,
        ohlcv_data_version=ohlcv_data_version,
        dense_data_version=dense_data_version,
        latency=validation_config.available_latency,
        ingested_at=ingested_at,
        max_contiguous_no_trade_minutes=max_no_trade,
    )
    if not dense_rows:
        if not suspected_non_trading_sessions or provider_gap_sessions:
            msg = "dense grid produced no rows"
            raise DataFoundationValidationError(msg)

    paths, storage_format = (
        _write_schema_records(
            canonical_root=canonical_root,
            data_version=dense_data_version,
            partition_schema=DENSE_OHLCV_PARTITION_SCHEMA,
            records=dense_rows,
        )
        if dense_rows
        else ((), "empty_quarantined")
    )
    sparse_manifest_hash = _canonical_manifest_hash(
        canonical_root=sparse_root,
        data_version=ohlcv_data_version,
        partition_schema=OHLCV_PARTITION_SCHEMA,
        request_spec=spec,
    )
    req_hash = request_spec_hash(spec)
    _write_dataset_manifest(
        canonical_root=canonical_root,
        data_version=dense_data_version,
        partition_schema=DENSE_OHLCV_PARTITION_SCHEMA,
        paths=paths,
        row_count=len(dense_rows),
        storage_format=storage_format,
        source_manifest_hash=sparse_manifest_hash,
        request_hash=req_hash,
    )
    return DenseGridSummary(
        canonical_root=canonical_root.as_posix(),
        sparse_ohlcv_data_version=ohlcv_data_version,
        dense_data_version=dense_data_version,
        symbols=roots,
        row_count=len(dense_rows),
        counts_by_symbol=counts_by_symbol,
        provider_gap_sessions=provider_gap_sessions,
        suspected_non_trading_sessions=suspected_non_trading_sessions,
        output_paths=MappingProxyType(
            {
                DENSE_OHLCV_PARTITION_SCHEMA: tuple(path.as_posix() for path in paths),
            }
        ),
        storage_format=storage_format,
        source_manifest_hash=sparse_manifest_hash,
        request_spec_hash=req_hash,
    )


def _build_dense_rows(
    *,
    sparse_bars: Sequence[CanonicalBarRecord],
    expected_intervals: Sequence[Mapping[str, object]],
    ohlcv_data_version: str,
    dense_data_version: str,
    latency: timedelta,
    ingested_at: datetime,
    max_contiguous_no_trade_minutes: int,
) -> tuple[
    tuple[DenseGridBarRecord, ...],
    Mapping[str, Mapping[str, object]],
    tuple[Mapping[str, object], ...],
    tuple[Mapping[str, object], ...],
]:
    by_key: dict[tuple[str, str, str], dict[datetime, CanonicalBarRecord]] = defaultdict(dict)
    for bar in sparse_bars:
        by_key[(bar.instrument_id, bar.contract_id, bar.session_label)][
            bar.bar_start_ts.astimezone(UTC)
        ] = bar

    rows: list[DenseGridBarRecord] = []
    counts: dict[str, dict[str, int]] = defaultdict(_dense_counts)
    provider_gap_sessions: list[Mapping[str, object]] = []
    suspected_non_trading_sessions: list[Mapping[str, object]] = []
    intervals = tuple(_normalize_interval(interval) for interval in expected_intervals)
    session_presence = _session_presence_by_key(intervals, sparse_bars_by_key=by_key)
    all_symbols_absent_by_date = _all_symbols_absent_by_date(session_presence)
    recorded_suspected_sessions: set[tuple[str, str, str, str, str]] = set()

    for interval in intervals:
        symbol = str(interval["symbol"])
        metrics = counts[symbol]
        expected_starts = _minute_starts(interval["start_ts"], interval["end_ts"])
        key = (
            str(interval["instrument_id"]),
            str(interval["contract_id"]),
            str(interval["session_label"]),
        )
        real_by_start = by_key.get(key, {})
        observed = {start for start in expected_starts if start in real_by_start}
        session_key = _session_key(interval)
        session = session_presence[session_key]
        if not bool(session["has_trade"]):
            metrics["suspected_non_trading_session_minutes"] += len(expected_starts)
            metrics["suspected_non_trading_session_count"] += 1
            if session_key not in recorded_suspected_sessions:
                suspected_non_trading_sessions.append(
                    _suspected_non_trading_session(
                        interval=interval,
                        session=session,
                        all_symbols_absent=all_symbols_absent_by_date[
                            str(interval["trading_date"])
                        ],
                    )
                )
                recorded_suspected_sessions.add(session_key)
            continue

        metrics["expected_minutes"] += len(expected_starts)
        if not observed:
            metrics["no_trade_unfilled_minutes"] += len(expected_starts)
            metrics["missing_previous_price_minutes"] += len(expected_starts)
            continue
        first_observed = min(observed)
        for run in _long_no_trade_runs(
            expected_starts=expected_starts,
            observed=observed,
            max_contiguous_no_trade_minutes=max_contiguous_no_trade_minutes,
            interval=interval,
        ):
            metrics["long_no_trade_run_count"] += 1
            metrics["long_no_trade_run_minutes"] += int(run["minute_count"])
        prior_close: Decimal | None = None
        prior_real: CanonicalBarRecord | None = None
        for start in expected_starts:
            real = real_by_start.get(start)
            if real is not None:
                row = _real_dense_row(
                    real,
                    ohlcv_data_version=ohlcv_data_version,
                    dense_data_version=dense_data_version,
                    latency=latency,
                    ingested_at=ingested_at,
                )
                rows.append(row)
                metrics["trade_minutes"] += 1
                prior_close = real.close
                prior_real = real
                continue
            if start < first_observed:
                metrics["no_trade_unfilled_minutes"] += 1
                metrics["missing_previous_price_minutes"] += 1
                continue
            if prior_close is None or prior_real is None:
                metrics["no_trade_unfilled_minutes"] += 1
                metrics["missing_previous_price_minutes"] += 1
                continue
            rows.append(
                _synthetic_dense_row(
                    template=prior_real,
                    bar_start_ts=start,
                    previous_close=prior_close,
                    dense_data_version=dense_data_version,
                    latency=latency,
                    ingested_at=ingested_at,
                )
            )
            metrics["no_trade_filled_minutes"] += 1

    frozen_counts: dict[str, Mapping[str, object]] = {}
    for symbol, metrics in sorted(counts.items()):
        expected = metrics["expected_minutes"]
        frozen_counts[symbol] = MappingProxyType(
            {
                **metrics,
                "no_trade_ratio": (
                    float(metrics["no_trade_filled_minutes"] / expected) if expected else 0.0
                ),
            }
        )
    return (
        tuple(sorted(rows, key=lambda row: (row.instrument_id, row.bar_start_ts))),
        MappingProxyType(frozen_counts),
        _dedupe_provider_gap_sessions(provider_gap_sessions),
        _dedupe_suspected_non_trading_sessions(suspected_non_trading_sessions),
    )


def _real_dense_row(
    bar: CanonicalBarRecord,
    *,
    ohlcv_data_version: str,
    dense_data_version: str,
    latency: timedelta,
    ingested_at: datetime,
) -> DenseGridBarRecord:
    return DenseGridBarRecord.from_mapping(
        {
            "instrument_id": bar.instrument_id,
            "contract_id": bar.contract_id,
            "series_id": bar.series_id,
            "bar_start_ts": bar.bar_start_ts,
            "bar_end_ts": bar.bar_end_ts,
            "event_ts": bar.event_ts,
            "available_ts": bar.bar_end_ts + latency,
            "ingested_at": ingested_at,
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
            "volume": bar.volume,
            "source": bar.source,
            "source_request_id": bar.source_request_id,
            "data_version": dense_data_version,
            "quality_flags": bar.quality_flags,
            "session_label": bar.session_label,
            "has_trade": True,
            "synthetic": False,
            "fill_method": None,
            "provider_bar_ref": ohlcv_data_version,
        }
    )


def _synthetic_dense_row(
    *,
    template: CanonicalBarRecord,
    bar_start_ts: datetime,
    previous_close: Decimal,
    dense_data_version: str,
    latency: timedelta,
    ingested_at: datetime,
) -> DenseGridBarRecord:
    bar_end_ts = bar_start_ts + timedelta(minutes=1)
    return DenseGridBarRecord.from_mapping(
        {
            "instrument_id": template.instrument_id,
            "contract_id": template.contract_id,
            "series_id": template.series_id,
            "bar_start_ts": bar_start_ts,
            "bar_end_ts": bar_end_ts,
            "event_ts": bar_end_ts,
            "available_ts": bar_end_ts + latency,
            "ingested_at": ingested_at,
            "open": previous_close,
            "high": previous_close,
            "low": previous_close,
            "close": previous_close,
            "volume": Decimal("0"),
            "source": template.source,
            "source_request_id": template.source_request_id,
            "data_version": dense_data_version,
            "quality_flags": (NO_TRADE_QUALITY_FLAG,),
            "session_label": template.session_label,
            "has_trade": False,
            "synthetic": True,
            "fill_method": PREVIOUS_CLOSE_FILL_METHOD,
            "provider_bar_ref": None,
        }
    )


def _long_no_trade_runs(
    *,
    expected_starts: tuple[datetime, ...],
    observed: set[datetime],
    max_contiguous_no_trade_minutes: int,
    interval: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    if not observed:
        return ()
    first_observed = min(observed)
    runs: list[Mapping[str, object]] = []
    active: list[datetime] = []
    for start in expected_starts:
        if start in observed:
            if (
                active
                and active[0] > first_observed
                and _run_bounded_by_trades(
                    observed,
                    run_start=active[0],
                    run_end=start,
                )
                and len(active) > max_contiguous_no_trade_minutes
            ):
                runs.append(
                    _long_no_trade_run(
                        interval,
                        minute_count=len(active),
                        start_ts=active[0],
                        end_ts=active[-1] + timedelta(minutes=1),
                        threshold_minutes=max_contiguous_no_trade_minutes,
                    )
                )
            active = []
            continue
        active.append(start)
    if (
        active
        and active[0] > first_observed
        and _run_bounded_by_trades(
            observed,
            run_start=active[0],
            run_end=active[-1] + timedelta(minutes=1),
        )
        and len(active) > max_contiguous_no_trade_minutes
    ):
        runs.append(
            _long_no_trade_run(
                interval,
                minute_count=len(active),
                start_ts=active[0],
                end_ts=active[-1] + timedelta(minutes=1),
                threshold_minutes=max_contiguous_no_trade_minutes,
            )
        )
    return tuple(runs)


def _long_no_trade_run(
    interval: Mapping[str, object],
    *,
    minute_count: int,
    start_ts: datetime,
    end_ts: datetime,
    threshold_minutes: int,
) -> Mapping[str, object]:
    return MappingProxyType(
        {
            "symbol": interval["symbol"],
            "session_date": interval["trading_date"],
            "trading_date": interval["trading_date"],
            "session_label": interval["session_label"],
            "start_ts": start_ts.isoformat(),
            "end_ts": end_ts.isoformat(),
            "minute_count": minute_count,
            "threshold_minutes": threshold_minutes,
            "classification": LONG_NO_TRADE_RUN,
            "reason": "max_contiguous_no_trade_exceeded",
            "status": "WARNING",
            "blocking": False,
        }
    )


def _provider_gap_session(
    interval: Mapping[str, object],
    *,
    reason: str,
    minute_count: int,
    start_ts: datetime | None = None,
    end_ts: datetime | None = None,
) -> Mapping[str, object]:
    start = start_ts or interval["start_ts"]
    end = end_ts or interval["end_ts"]
    return MappingProxyType(
        {
            "symbol": interval["symbol"],
            "session_date": interval["trading_date"],
            "trading_date": interval["trading_date"],
            "session_label": interval["session_label"],
            "start_ts": start.isoformat(),
            "end_ts": end.isoformat(),
            "minute_count": minute_count,
            "classification": PROVIDER_DATA_GAP,
            "reason": reason,
        }
    )


def _suspected_non_trading_session(
    *,
    interval: Mapping[str, object],
    session: Mapping[str, object],
    all_symbols_absent: bool,
) -> Mapping[str, object]:
    start = _parse_datetime(session["start_ts"], "session.start_ts")
    end = _parse_datetime(session["end_ts"], "session.end_ts")
    return MappingProxyType(
        {
            "symbol": interval["symbol"],
            "session_date": str(session["trading_date"]),
            "trading_date": str(session["trading_date"]),
            "session_label": interval["session_label"],
            "start_ts": start.isoformat(),
            "end_ts": end.isoformat(),
            "minute_count": int(session["minute_count"]),
            "classification": SUSPECTED_NON_TRADING_SESSION,
            "reason": "whole_expected_session_absent",
            "all_symbols_absent": all_symbols_absent,
            "status": "WARNING",
        }
    )


def _dedupe_provider_gap_sessions(
    sessions: Iterable[Mapping[str, object]],
) -> tuple[Mapping[str, object], ...]:
    deduped: dict[tuple[object, ...], Mapping[str, object]] = {}
    for session in sessions:
        key = (
            session["symbol"],
            session["session_label"],
            session["start_ts"],
            session["end_ts"],
            session["reason"],
        )
        deduped[key] = session
    return tuple(deduped[key] for key in sorted(deduped))


def _dedupe_suspected_non_trading_sessions(
    sessions: Iterable[Mapping[str, object]],
) -> tuple[Mapping[str, object], ...]:
    deduped: dict[tuple[object, ...], Mapping[str, object]] = {}
    for session in sessions:
        key = (
            session["symbol"],
            session["session_date"],
            session["session_label"],
            session["start_ts"],
            session["end_ts"],
        )
        deduped[key] = session
    return tuple(deduped[key] for key in sorted(deduped))


def _session_presence_by_key(
    intervals: Sequence[Mapping[str, object]],
    *,
    sparse_bars_by_key: Mapping[tuple[str, str, str], Mapping[datetime, CanonicalBarRecord]],
) -> Mapping[tuple[str, str, str, str, str], Mapping[str, object]]:
    sessions: dict[tuple[str, str, str, str, str], dict[str, object]] = {}
    for interval in intervals:
        key = (
            str(interval["instrument_id"]),
            str(interval["contract_id"]),
            str(interval["session_label"]),
        )
        expected_starts = _minute_starts(interval["start_ts"], interval["end_ts"])
        real_by_start = sparse_bars_by_key.get(key, {})
        observed = {start for start in expected_starts if start in real_by_start}
        session_key = _session_key(interval)
        current = sessions.setdefault(
            session_key,
            {
                "symbol": interval["symbol"],
                "instrument_id": interval["instrument_id"],
                "contract_id": interval["contract_id"],
                "session_label": interval["session_label"],
                "trading_date": interval["trading_date"],
                "start_ts": interval["start_ts"],
                "end_ts": interval["end_ts"],
                "minute_count": 0,
                "has_trade": False,
            },
        )
        current["start_ts"] = min(
            _parse_datetime(current["start_ts"], "session.start_ts"),
            interval["start_ts"],
        )
        current["end_ts"] = max(
            _parse_datetime(current["end_ts"], "session.end_ts"),
            interval["end_ts"],
        )
        current["minute_count"] = int(current["minute_count"]) + len(expected_starts)
        current["has_trade"] = bool(current["has_trade"]) or bool(observed)
    return MappingProxyType(
        {key: MappingProxyType(value) for key, value in sessions.items()}
    )


def _session_key(interval: Mapping[str, object]) -> tuple[str, str, str, str, str]:
    return (
        str(interval["symbol"]),
        str(interval["instrument_id"]),
        str(interval["contract_id"]),
        str(interval["session_label"]),
        str(interval["trading_date"]),
    )


def _all_symbols_absent_by_date(
    session_presence: Mapping[tuple[str, str, str, str, str], Mapping[str, object]],
) -> Mapping[str, bool]:
    by_date: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for session in session_presence.values():
        by_date[str(session["trading_date"])].append(session)
    return MappingProxyType(
        {
            trading_date: all(not bool(session["has_trade"]) for session in sessions)
            for trading_date, sessions in by_date.items()
        }
    )


def _run_bounded_by_trades(
    trades: set[datetime],
    *,
    run_start: datetime,
    run_end: datetime,
) -> bool:
    has_trade_before = any(start < run_start for start in trades)
    has_trade_after = any(start >= run_end for start in trades)
    return has_trade_before and has_trade_after


def _dense_counts() -> dict[str, int]:
    return {
        "expected_minutes": 0,
        "trade_minutes": 0,
        "no_trade_filled_minutes": 0,
        "no_trade_unfilled_minutes": 0,
        "missing_previous_price_minutes": 0,
        "suspected_non_trading_session_minutes": 0,
        "suspected_non_trading_session_count": 0,
        "provider_gap_minutes": 0,
        "long_no_trade_run_count": 0,
        "long_no_trade_run_minutes": 0,
    }


def _read_ohlcv_records(canonical_root: Path, data_version: str) -> tuple[CanonicalBarRecord, ...]:
    return tuple(
        CanonicalBarRecord.from_mapping(row)
        for row in _read_schema_rows(canonical_root, data_version, OHLCV_PARTITION_SCHEMA)
    )


def _read_schema_rows(
    canonical_root: Path,
    data_version: str,
    partition_schema: str,
) -> tuple[Mapping[str, object], ...]:
    schema_root = canonical_root / data_version / f"schema={partition_schema}"
    if not schema_root.is_dir():
        msg = f"canonical schema directory does not exist: {schema_root.as_posix()}"
        raise DataFoundationValidationError(msg)
    rows: list[Mapping[str, object]] = []
    for path in _canonical_data_files(canonical_root, data_version, partition_schema):
        if path.suffix == ".jsonl":
            rows.extend(_read_jsonl(path))
        elif path.suffix == ".parquet":
            rows.extend(_read_parquet(path))
    if not rows:
        msg = f"no canonical records found for {data_version} {partition_schema}"
        raise DataFoundationValidationError(msg)
    return tuple(rows)


def _canonical_data_files(
    canonical_root: Path,
    data_version: str,
    partition_schema: str,
) -> tuple[Path, ...]:
    schema_root = canonical_root / data_version / f"schema={partition_schema}"
    paths = []
    for path in sorted(schema_root.glob("root=*/part-*")):
        if path.name.endswith(".json") or path.name.endswith(".manifest"):
            continue
        if path.suffix in {".jsonl", ".parquet"}:
            paths.append(path)
    return tuple(paths)


def _read_jsonl(path: Path) -> tuple[Mapping[str, object], ...]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                payload = json.loads(line)
                if not isinstance(payload, Mapping):
                    msg = f"canonical JSONL row is not a mapping: {path.as_posix()}"
                    raise DataFoundationValidationError(msg)
                rows.append(MappingProxyType(dict(payload)))
    return tuple(rows)


def _read_parquet(path: Path) -> tuple[Mapping[str, object], ...]:
    pyarrow = _optional_module("pyarrow")
    if pyarrow is not None:
        parquet = importlib.import_module("pyarrow.parquet")
        return tuple(parquet.ParquetFile(path).read().to_pylist())
    polars = _optional_module("polars")
    if polars is not None:
        return tuple(polars.read_parquet(path.as_posix()).to_dicts())
    msg = f"cannot read Parquet without pyarrow or polars: {path.as_posix()}"
    raise DataFoundationValidationError(msg)


def _optional_module(module_name: str) -> Any | None:
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name == module_name:
            return None
        raise


def _canonical_manifest_hash(
    *,
    canonical_root: Path,
    data_version: str,
    partition_schema: str,
    request_spec: DatabentoRequestSpec,
) -> str:
    files = _canonical_data_files(canonical_root, data_version, partition_schema)
    if not files:
        msg = f"no canonical files found for manifest hash: {data_version}"
        raise DataFoundationValidationError(msg)
    return hash_config(
        {
            "schema": "alpha_system.databento.dense_grid.source_manifest.v1",
            "data_version": data_version,
            "partition_schema": partition_schema,
            "request_spec_hash": request_spec_hash(request_spec),
            "files": tuple(
                {
                    "relative_path": path.relative_to(canonical_root).as_posix(),
                    "sha256": hash_file(path),
                    "size_bytes": path.stat().st_size,
                }
                for path in files
            ),
        }
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
        msg = "ALPHA_DATA_ROOT is required for Databento dense-grid construction"
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


def _validate_canonical_root(canonical_root: Path, *, data_root: Path) -> Path:
    resolved = _validate_data_root(canonical_root, _repo_root())
    if resolved != data_root and not _is_relative_to(resolved, data_root):
        msg = "sparse_canonical_root must resolve under ALPHA_DATA_ROOT"
        raise DataFoundationValidationError(msg)
    if resolved.name != CANONICAL_PROVIDER_SEGMENT:
        candidate = (
            resolved / "databento" / "canonical" / CANONICAL_PROVIDER_SEGMENT
        ).resolve(strict=False)
        if candidate.exists():
            return candidate
    return resolved


def _normalize_now(now: datetime | None) -> datetime:
    active = now or datetime.now(UTC)
    if active.tzinfo is None or active.utcoffset() is None:
        msg = "now must be timezone-aware"
        raise DataFoundationValidationError(msg)
    return active.astimezone(UTC).replace(microsecond=0)


def _root_from_symbol(symbol: str) -> str:
    root = symbol.replace(".", " ").split()[0].upper()
    if root not in {"ES", "NQ", "RTY"}:
        msg = "Databento dense grid is scoped to ES/NQ/RTY"
        raise DataFoundationValidationError(msg)
    return root


def _normalize_interval(value: Mapping[str, object]) -> Mapping[str, object]:
    start = _parse_datetime(value["start_ts"], "start_ts")
    end = _parse_datetime(value["end_ts"], "end_ts")
    if end <= start:
        msg = "expected interval end_ts must be greater than start_ts"
        raise DataFoundationValidationError(msg)
    trading_date = _normalize_trading_date(value, start)
    return MappingProxyType(
        {
            "symbol": str(value["symbol"]).upper(),
            "instrument_id": str(value["instrument_id"]),
            "contract_id": str(value["contract_id"]),
            "session_label": str(value["session_label"]).upper(),
            "start_ts": start,
            "end_ts": end,
            "trading_date": trading_date,
        }
    )


def _normalize_trading_date(value: Mapping[str, object], start: datetime) -> str:
    raw = value.get("trading_date", value.get("session_date"))
    if raw is None:
        return start.date().isoformat()
    if isinstance(raw, datetime):
        return raw.date().isoformat()
    if isinstance(raw, date):
        return raw.isoformat()
    try:
        return date.fromisoformat(str(raw)).isoformat()
    except ValueError as exc:
        msg = "expected interval trading_date must be YYYY-MM-DD"
        raise DataFoundationValidationError(msg) from exc


def _parse_datetime(value: object, field_name: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError as exc:
            msg = f"{field_name} must be a timezone-aware datetime"
            raise DataFoundationValidationError(msg) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        msg = f"{field_name} must be timezone-aware"
        raise DataFoundationValidationError(msg)
    return parsed.astimezone(UTC)


def _minute_starts(start: datetime, end: datetime) -> tuple[datetime, ...]:
    current = start.astimezone(UTC)
    stop = end.astimezone(UTC)
    starts = []
    while current < stop:
        starts.append(current)
        current += timedelta(minutes=1)
    return tuple(starts)


def _max_contiguous_no_trade_minutes(config: Mapping[str, object]) -> int:
    raw = config.get(
        "max_contiguous_no_trade_minutes",
        DEFAULT_MAX_CONTIGUOUS_NO_TRADE_MINUTES,
    )
    if isinstance(raw, bool):
        msg = "max_contiguous_no_trade_minutes must be a positive integer"
        raise DataFoundationValidationError(msg)
    try:
        parsed = int(raw)
    except (TypeError, ValueError) as exc:
        msg = "max_contiguous_no_trade_minutes must be a positive integer"
        raise DataFoundationValidationError(msg) from exc
    if parsed <= 0:
        msg = "max_contiguous_no_trade_minutes must be a positive integer"
        raise DataFoundationValidationError(msg)
    return parsed


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build dense Databento OHLCV-1m research-grid rows",
    )
    parser.add_argument("--sparse-canonical-root", type=Path, required=True)
    parser.add_argument("--ohlcv-data-version", required=True)
    parser.add_argument("--request-spec", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--dense-data-version", required=True)
    parser.add_argument("--instrument-config", type=Path, required=True)
    parser.add_argument("--calendar-config", type=Path, required=True)
    parser.add_argument("--validation-config", type=Path, required=True)
    return parser.parse_args(argv)


def _print_summary(summary: DenseGridSummary) -> None:
    print(json.dumps(_json_ready(summary.to_mapping()), indent=2, sort_keys=True))


def main(argv: Sequence[str] | None = None) -> int:
    """CLI for ``python -m alpha_system.data.databento.dense_grid``."""

    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        summary = run_dense_grid(
            sparse_canonical_root=args.sparse_canonical_root,
            ohlcv_data_version=args.ohlcv_data_version,
            request_spec=DatabentoRequestSpec.from_mapping(load_json_mapping(args.request_spec)),
            output_root=args.output_root,
            dense_data_version=args.dense_data_version,
            instrument_config_path=args.instrument_config,
            calendar_config_path=args.calendar_config,
            validation_config_path=args.validation_config,
        )
    except DataFoundationValidationError as exc:
        print(f"dense_grid blocked: {exc}", file=sys.stderr)
        return 2
    _print_summary(summary)
    return 0


__all__ = [
    "DENSE_GRID_PARTITION_ID",
    "DENSE_OHLCV_PARTITION_SCHEMA",
    "DenseGridSummary",
    "main",
    "run_dense_grid",
]


if __name__ == "__main__":
    raise SystemExit(main())
