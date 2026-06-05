"""Databento definition/statistics/status metadata normalization.

The module is offline-testable: callers may inject metadata rows, and real DBN
loading is reached only when no ``record_source`` is supplied.
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
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from types import MappingProxyType

from alpha_system.core.hashing import hash_config
from alpha_system.core.registry import is_local_only_registry_path
from alpha_system.data.databento.manifest_files import DatabentoFileManifest
from alpha_system.data.databento.request_spec import DATABENTO_DATASET, load_json_mapping
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.data.ibkr._json_utils import json_ready as _json_ready
from alpha_system.data.ibkr.materialize import _repo_root, _validate_data_root

METADATA_SCHEMAS: tuple[str, ...] = ("definition", "statistics", "status")
METADATA_PROVIDER_SEGMENT = "glbx_mdp3"
METADATA_REF_SCHEMA = "alpha_system.databento.metadata_ref.v1"
METADATA_MANIFEST_SCHEMA = "alpha_system.databento.metadata_manifest.v1"
SUPPORTED_ROOTS: frozenset[str] = frozenset({"ES", "NQ", "RTY"})
MICRO_ROOTS: frozenset[str] = frozenset({"MES", "MNQ", "M2K"})
_PRICE_SCALE = Decimal("1000000000")
_DATABENTO_UNDEF_PRICE = 2**63 - 1

RecordSource = Callable[
    ...,
    Mapping[str, Iterable[object]] | Iterable[object],
]


@dataclass(frozen=True, slots=True)
class MetadataIngestSummary:
    """Redacted summary of Databento metadata refs written under ALPHA_DATA_ROOT."""

    metadata_version_id: str
    metadata_root: str
    manifest_path: str
    counts_by_schema: Mapping[str, int]
    ref_paths: Mapping[str, tuple[str, ...]]
    warnings: tuple[str, ...]
    source_manifest_hash: str
    ingested_at: str

    def to_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "metadata_version_id": self.metadata_version_id,
                "metadata_root": self.metadata_root,
                "manifest_path": self.manifest_path,
                "counts_by_schema": self.counts_by_schema,
                "ref_paths": self.ref_paths,
                "warnings": self.warnings,
                "source_manifest_hash": self.source_manifest_hash,
                "ingested_at": self.ingested_at,
            }
        )


def run_metadata_ingest(
    *,
    file_manifest_path: str | Path,
    output_root: str | Path,
    record_source: RecordSource | None = None,
    env: Mapping[str, str] | None = None,
    now: datetime | None = None,
) -> MetadataIngestSummary:
    """Normalize Databento metadata rows into local-only JSON reference files."""

    manifest = DatabentoFileManifest.from_mapping(load_json_mapping(Path(file_manifest_path)))
    data_root = _require_data_root(env)
    output_base = _validate_output_root(Path(output_root), data_root=data_root)
    ingested_at = _normalize_now(now)
    metadata_version_id = _metadata_version_id(manifest.manifest_hash)
    metadata_root = (
        output_base / "databento" / "metadata" / METADATA_PROVIDER_SEGMENT
    ).resolve(strict=False)

    rows_by_schema = _load_rows_by_schema(manifest, record_source=record_source)
    warnings: list[str] = []
    normalized_by_schema: dict[str, tuple[Mapping[str, object], ...]] = {}
    for schema in METADATA_SCHEMAS:
        rows = rows_by_schema.get(schema, ())
        if not rows:
            warnings.append(
                f"WARNING: Databento metadata schema {schema!r} is unavailable or empty"
            )
            normalized_by_schema[schema] = ()
            continue
        normalized, schema_warnings = _normalize_schema_rows(schema, rows)
        warnings.extend(schema_warnings)
        if not normalized:
            warnings.append(
                f"WARNING: Databento metadata schema {schema!r} produced no ES/NQ/RTY refs"
            )
        normalized_by_schema[schema] = normalized

    ref_paths = _write_metadata_refs(
        metadata_root=metadata_root,
        metadata_version_id=metadata_version_id,
        rows_by_schema=normalized_by_schema,
        source_manifest_hash=manifest.manifest_hash,
        ingested_at=ingested_at,
    )
    manifest_path = _write_metadata_manifest(
        metadata_root=metadata_root,
        metadata_version_id=metadata_version_id,
        rows_by_schema=normalized_by_schema,
        ref_paths=ref_paths,
        source_manifest_hash=manifest.manifest_hash,
        ingested_at=ingested_at,
        warnings=tuple(warnings),
    )

    return MetadataIngestSummary(
        metadata_version_id=metadata_version_id,
        metadata_root=metadata_root.as_posix(),
        manifest_path=manifest_path.as_posix(),
        counts_by_schema=MappingProxyType(
            {schema: len(normalized_by_schema[schema]) for schema in METADATA_SCHEMAS}
        ),
        ref_paths=MappingProxyType(ref_paths),
        warnings=tuple(warnings),
        source_manifest_hash=manifest.manifest_hash or "",
        ingested_at=ingested_at.isoformat(),
    )


def _require_data_root(env: Mapping[str, str] | None) -> Path:
    source = os.environ if env is None else env
    value = source.get("ALPHA_DATA_ROOT")
    if value is None or not value.strip():
        msg = "ALPHA_DATA_ROOT is required for Databento metadata ingest"
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
    local_probe = resolved / "databento_metadata_refs.sqlite3"
    if not is_local_only_registry_path(local_probe):
        msg = f"output_root is not local-only: {resolved.as_posix()}"
        raise DataFoundationValidationError(msg)
    return resolved


def _normalize_now(now: datetime | None) -> datetime:
    active = now or datetime.now(UTC)
    if active.tzinfo is None or active.utcoffset() is None:
        msg = "now must be timezone-aware"
        raise DataFoundationValidationError(msg)
    return active.astimezone(UTC).replace(microsecond=0)


def _metadata_version_id(manifest_hash: str | None) -> str:
    if not manifest_hash:
        msg = "Databento file manifest must expose manifest_hash"
        raise DataFoundationValidationError(msg)
    digest = hash_config(
        {
            "schema": "alpha_system.databento.metadata_version.v1",
            "source_manifest_hash": manifest_hash,
            "metadata_schemas": METADATA_SCHEMAS,
        }
    )
    return f"dsv_databento_metadata_{digest[:16]}"


def _load_rows_by_schema(
    manifest: DatabentoFileManifest,
    *,
    record_source: RecordSource | None,
) -> Mapping[str, tuple[Mapping[str, object], ...]]:
    source_rows = _load_real_dbn_rows(manifest) if record_source is None else record_source(
        file_manifest=manifest
    )
    by_schema: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    if isinstance(source_rows, Mapping):
        iterable = (
            (str(schema).lower(), row)
            for schema, rows in source_rows.items()
            for row in _require_row_iterable(rows, str(schema))
        )
    else:
        iterable = ((_schema_from_row(row), row) for row in source_rows)

    for schema, row in iterable:
        if schema not in METADATA_SCHEMAS:
            continue
        by_schema[schema].append(MappingProxyType(_record_to_mapping(row)))
    return MappingProxyType({schema: tuple(rows) for schema, rows in by_schema.items()})


def _require_row_iterable(value: object, schema: str) -> Iterable[object]:
    if isinstance(value, Mapping) or not isinstance(value, Iterable):
        msg = f"record_source schema {schema!r} must yield row objects"
        raise DataFoundationValidationError(msg)
    return value


def _schema_from_row(row: object) -> str:
    values = _record_to_mapping(row)
    for key in ("schema", "_schema"):
        value = values.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
    msg = "record_source iterable metadata rows must include schema or _schema"
    raise DataFoundationValidationError(msg)


def _record_to_mapping(row: object) -> dict[str, object]:
    if isinstance(row, Mapping):
        return dict(row)
    values: dict[str, object] = {}
    raw_dict = getattr(row, "__dict__", None)
    if isinstance(raw_dict, Mapping):
        values.update(raw_dict)
    for name in getattr(row, "__slots__", ()):
        if isinstance(name, str) and hasattr(row, name):
            values[name] = getattr(row, name)
    if values:
        return values
    msg = "Databento metadata rows must be mappings or introspectable record objects"
    raise DataFoundationValidationError(msg)


def _load_real_dbn_rows(
    manifest: DatabentoFileManifest,
) -> Mapping[str, tuple[Mapping[str, object], ...]]:
    dbn_store = _load_dbn_store()
    by_schema: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    raw_root = Path(manifest.raw_root).expanduser().resolve(strict=False)
    _validate_data_root(raw_root, _repo_root())
    for file_record in manifest.files:
        if file_record.schema not in METADATA_SCHEMAS:
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
            values = _record_to_mapping(row)
            values.setdefault("job_id", file_record.job_id)
            values.setdefault("schema", file_record.schema)
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
    msg = "DBNStore is required for real Databento metadata ingest"
    raise DataFoundationValidationError(msg)


def _normalize_schema_rows(
    schema: str,
    rows: Sequence[Mapping[str, object]],
) -> tuple[tuple[Mapping[str, object], ...], tuple[str, ...]]:
    if schema == "definition":
        return _normalize_definition_rows(rows)
    if schema == "statistics":
        return _normalize_statistics_rows(rows)
    if schema == "status":
        return _normalize_status_rows(rows)
    msg = f"unsupported Databento metadata schema: {schema}"
    raise DataFoundationValidationError(msg)


def _normalize_definition_rows(
    rows: Sequence[Mapping[str, object]],
) -> tuple[tuple[Mapping[str, object], ...], tuple[str, ...]]:
    records: list[Mapping[str, object]] = []
    warnings: list[str] = []
    skipped_root = 0
    missing_dates = 0
    for row in rows:
        root = _row_root(row)
        if root is None:
            skipped_root += 1
            continue
        expiration = _date_or_timestamp_text(
            _first(row, ("expiration", "expiration_ts", "maturity_month_year"))
        )
        activation = _date_or_timestamp_text(_first(row, ("activation", "activation_ts")))
        listing = _date_or_timestamp_text(_first(row, ("listing", "listing_ts", "ts_event")))
        if expiration is None and activation is None and listing is None:
            missing_dates += 1
        tick_size = _price_text(_first(row, ("min_price_increment", "tick_size")))
        multiplier = _decimal_text(
            _first(row, ("contract_multiplier", "unit_of_measure_qty", "contract_size"))
        )
        records.append(
            MappingProxyType(
                {
                    "metadata_schema": "definition",
                    "root": root,
                    "instrument_id": _text_or_none(_first(row, ("instrument_id",))),
                    "raw_symbol": _text_or_none(
                        _first(row, ("raw_symbol", "symbol", "display_symbol"))
                    ),
                    "expiration": expiration,
                    "activation": activation,
                    "listing": listing,
                    "tick_size": tick_size,
                    "min_price_increment": tick_size,
                    "contract_multiplier": multiplier,
                    "point_value": _decimal_text(
                        _first(row, ("point_value", "min_price_increment_amount"))
                    ),
                    "contract_multiplier_unit": _text_or_none(
                        _first(row, ("unit_of_measure", "contract_multiplier_unit"))
                    ),
                    "security_type": _text_or_none(
                        _first(row, ("security_type", "instrument_class", "sec_type"))
                    ),
                    "currency": _text_or_none(_first(row, ("currency", "settl_currency"))),
                    "exchange": _text_or_none(_first(row, ("exchange", "exchange_id"))),
                    "source_job_id": _text_or_none(_first(row, ("job_id",))),
                }
            )
        )
    if skipped_root:
        warnings.append(f"WARNING: definition skipped {skipped_root} non-ES/NQ/RTY rows")
    if missing_dates:
        warnings.append(
            f"WARNING: definition has {missing_dates} ES/NQ/RTY rows without date metadata"
        )
    return _sort_records(records), tuple(warnings)


def _normalize_statistics_rows(
    rows: Sequence[Mapping[str, object]],
) -> tuple[tuple[Mapping[str, object], ...], tuple[str, ...]]:
    records: list[Mapping[str, object]] = []
    warnings: list[str] = []
    skipped_root = 0
    missing_dates = 0
    for row in rows:
        root = _row_root(row)
        if root is None:
            skipped_root += 1
            continue
        stat_day = _date_text(_first(row, ("ts_ref", "ref_ts", "trading_date", "ts_event")))
        if stat_day is None:
            missing_dates += 1
        raw_stat_type = _text_or_none(_first(row, ("stat_type", "statistic_type", "type")))
        records.append(
            MappingProxyType(
                {
                    "metadata_schema": "statistics",
                    "root": root,
                    "instrument_id": _text_or_none(_first(row, ("instrument_id",))),
                    "raw_symbol": _text_or_none(
                        _first(row, ("raw_symbol", "symbol", "display_symbol"))
                    ),
                    "stat_kind": _stat_kind(raw_stat_type),
                    "stat_type": raw_stat_type,
                    "date": stat_day,
                    "event_ts": _timestamp_text(_first(row, ("ts_event", "event_ts"))),
                    "price": _price_text(_first(row, ("price", "settlement_price"))),
                    "quantity": _decimal_text(
                        _first(row, ("quantity", "qty", "volume", "open_interest"))
                    ),
                    "source_job_id": _text_or_none(_first(row, ("job_id",))),
                }
            )
        )
    if skipped_root:
        warnings.append(f"WARNING: statistics skipped {skipped_root} non-ES/NQ/RTY rows")
    if missing_dates:
        warnings.append(f"WARNING: statistics has {missing_dates} rows without daily date refs")
    return _sort_records(records), tuple(warnings)


def _normalize_status_rows(
    rows: Sequence[Mapping[str, object]],
) -> tuple[tuple[Mapping[str, object], ...], tuple[str, ...]]:
    records: list[Mapping[str, object]] = []
    warnings: list[str] = []
    skipped_root = 0
    missing_events = 0
    for row in rows:
        root = _row_root(row)
        if root is None:
            skipped_root += 1
            continue
        event_ts = _timestamp_text(_first(row, ("ts_event", "event_ts")))
        if event_ts is None:
            missing_events += 1
        action = _text_or_none(_first(row, ("action", "status_action")))
        reason = _text_or_none(_first(row, ("reason", "status_reason")))
        trading_event = _text_or_none(_first(row, ("trading_event", "event")))
        is_trading = _bool_or_none(_first(row, ("is_trading", "trading")))
        is_quoting = _bool_or_none(_first(row, ("is_quoting", "quoting")))
        records.append(
            MappingProxyType(
                {
                    "metadata_schema": "status",
                    "root": root,
                    "instrument_id": _text_or_none(_first(row, ("instrument_id",))),
                    "raw_symbol": _text_or_none(
                        _first(row, ("raw_symbol", "symbol", "display_symbol"))
                    ),
                    "event_ts": event_ts,
                    "session_date": _date_text(_first(row, ("ts_event", "event_ts"))),
                    "action": action,
                    "reason": reason,
                    "trading_event": trading_event,
                    "is_trading": is_trading,
                    "is_quoting": is_quoting,
                    "status_kind": _status_kind(
                        action=action,
                        reason=reason,
                        trading_event=trading_event,
                        is_trading=is_trading,
                    ),
                    "source_job_id": _text_or_none(_first(row, ("job_id",))),
                }
            )
        )
    if skipped_root:
        warnings.append(f"WARNING: status skipped {skipped_root} non-ES/NQ/RTY rows")
    if missing_events:
        warnings.append(f"WARNING: status has {missing_events} rows without event timestamps")
    return _sort_records(records), tuple(warnings)


def _sort_records(records: Sequence[Mapping[str, object]]) -> tuple[Mapping[str, object], ...]:
    return tuple(
        sorted(
            records,
            key=lambda row: (
                str(row.get("root", "")),
                str(row.get("date", row.get("event_ts", row.get("expiration", "")))),
                str(row.get("instrument_id", "")),
                str(row.get("raw_symbol", "")),
            ),
        )
    )


def _row_root(row: Mapping[str, object]) -> str | None:
    for field_name in (
        "symbol",
        "raw_symbol",
        "display_symbol",
        "instrument_id",
        "security_id",
        "contract_id",
        "series_id",
    ):
        value = row.get(field_name)
        if value is None:
            continue
        root = _supported_root_from_text(str(value))
        if root is not None:
            return root
    return None


def _supported_root_from_text(value: str) -> str | None:
    normalized = value.strip().upper()
    if not normalized:
        return None
    first = normalized.replace(".", " ").replace("_", " ").replace("-", " ").split()[0]
    if first in MICRO_ROOTS:
        return None
    if first in SUPPORTED_ROOTS:
        return first
    compact = "".join(char for char in normalized if char.isalnum())
    if any(compact.startswith(root) for root in MICRO_ROOTS):
        return None
    for root in ("RTY", "NQ", "ES"):
        if compact.startswith(root):
            return root
    lowered = normalized.lower()
    for root in ("rty", "nq", "es"):
        if f"_{root}" in lowered or f"-{root}" in lowered:
            return root.upper()
    return None


def _first(row: Mapping[str, object], names: Sequence[str]) -> object | None:
    for name in names:
        value = row.get(name)
        if value is not None:
            return value
    return None


def _text_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _decimal_text(value: object) -> str | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if not parsed.is_finite():
        return None
    return str(parsed)


def _price_text(value: object) -> str | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        if value == _DATABENTO_UNDEF_PRICE:
            return None
        return str(Decimal(value) / _PRICE_SCALE)
    if isinstance(value, str) and value.strip() == str(_DATABENTO_UNDEF_PRICE):
        return None
    return _decimal_text(value)


def _date_or_timestamp_text(value: object) -> str | None:
    parsed = _parse_datetime_like(value)
    if parsed is None:
        return _text_or_none(value)
    if isinstance(parsed, date) and not isinstance(parsed, datetime):
        return parsed.isoformat()
    return parsed.isoformat()


def _timestamp_text(value: object) -> str | None:
    parsed = _parse_datetime_like(value)
    if parsed is None:
        return None
    if isinstance(parsed, datetime):
        return parsed.isoformat()
    return datetime.combine(parsed, datetime.min.time(), UTC).isoformat()


def _date_text(value: object) -> str | None:
    parsed = _parse_datetime_like(value)
    if parsed is None:
        return None
    if isinstance(parsed, datetime):
        return parsed.date().isoformat()
    return parsed.isoformat()


def _parse_datetime_like(value: object) -> datetime | date | None:
    if value is None:
        return None
    to_pydatetime = getattr(value, "to_pydatetime", None)
    if callable(to_pydatetime):
        value = to_pydatetime()
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    if isinstance(value, date):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        text = str(value)
        if len(text) == 8:
            try:
                return date.fromisoformat(f"{text[:4]}-{text[4:6]}-{text[6:]}")
            except ValueError:
                return None
        if abs(value) > 10_000_000_000:
            seconds, nanoseconds = divmod(value, 1_000_000_000)
            return datetime.fromtimestamp(seconds, UTC) + timedelta(
                microseconds=nanoseconds // 1000
            )
        if abs(value) > 1_000_000_000:
            return datetime.fromtimestamp(value, UTC)
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        if len(raw) == 8 and raw.isdigit():
            try:
                return date.fromisoformat(f"{raw[:4]}-{raw[4:6]}-{raw[6:]}")
            except ValueError:
                return None
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            try:
                return date.fromisoformat(raw)
            except ValueError:
                return None
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    return None


def _stat_kind(stat_type: str | None) -> str:
    if stat_type is None:
        return "unknown"
    normalized = stat_type.strip().lower().replace("-", "_").replace(" ", "_")
    compact = normalized.replace("_", "")
    if "settle" in compact:
        return "settlement"
    if "openinterest" in compact:
        return "open_interest"
    if "volume" in compact:
        return "official_volume"
    return normalized or "unknown"


def _bool_or_none(value: object) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in {0, 1}:
        return bool(value)
    if isinstance(value, str):
        raw = value.strip().lower()
        if raw in {"true", "1", "yes", "y"}:
            return True
        if raw in {"false", "0", "no", "n"}:
            return False
    return None


def _status_kind(
    *,
    action: str | None,
    reason: str | None,
    trading_event: str | None,
    is_trading: bool | None,
) -> str:
    joined = " ".join(value or "" for value in (action, reason, trading_event)).lower()
    if is_trading is False or "halt" in joined:
        return "halt"
    if "pause" in joined:
        return "pause"
    if "open" in joined or "close" in joined or "pre" in joined:
        return "session_state"
    return "status_transition"


def _write_metadata_refs(
    *,
    metadata_root: Path,
    metadata_version_id: str,
    rows_by_schema: Mapping[str, Sequence[Mapping[str, object]]],
    source_manifest_hash: str | None,
    ingested_at: datetime,
) -> dict[str, tuple[str, ...]]:
    ref_paths: dict[str, tuple[str, ...]] = {}
    for schema in METADATA_SCHEMAS:
        paths: list[str] = []
        by_root: dict[str, list[Mapping[str, object]]] = defaultdict(list)
        for row in rows_by_schema.get(schema, ()):
            by_root[str(row["root"])].append(row)
        for root, rows in sorted(by_root.items()):
            path = (
                metadata_root
                / metadata_version_id
                / f"schema={schema}"
                / f"root={root}"
                / "part-00000.json"
            )
            _write_json(
                path,
                {
                    "schema": METADATA_REF_SCHEMA,
                    "dataset": DATABENTO_DATASET,
                    "metadata_version_id": metadata_version_id,
                    "metadata_schema": schema,
                    "root": root,
                    "row_count": len(rows),
                    "source_manifest_hash": source_manifest_hash,
                    "ingested_at": ingested_at.isoformat(),
                    "records": tuple(rows),
                },
            )
            paths.append(path.as_posix())
        ref_paths[schema] = tuple(paths)
    return ref_paths


def _write_metadata_manifest(
    *,
    metadata_root: Path,
    metadata_version_id: str,
    rows_by_schema: Mapping[str, Sequence[Mapping[str, object]]],
    ref_paths: Mapping[str, Sequence[str]],
    source_manifest_hash: str | None,
    ingested_at: datetime,
    warnings: tuple[str, ...],
) -> Path:
    path = metadata_root / metadata_version_id / "manifest.json"
    _write_json(
        path,
        {
            "schema": METADATA_MANIFEST_SCHEMA,
            "dataset": DATABENTO_DATASET,
            "metadata_version_id": metadata_version_id,
            "metadata_schemas": METADATA_SCHEMAS,
            "counts_by_schema": {
                schema: len(rows_by_schema.get(schema, ())) for schema in METADATA_SCHEMAS
            },
            "ref_paths": ref_paths,
            "source_manifest_hash": source_manifest_hash,
            "ingested_at": ingested_at.isoformat(),
            "warnings": warnings,
        },
    )
    return path


def _write_json(path: Path, payload: Mapping[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(_json_ready(payload), handle, indent=2, sort_keys=True)
        handle.write("\n")
    return path


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize local Databento definition/statistics/status metadata",
    )
    parser.add_argument("--file-manifest", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    return parser.parse_args(argv)


def _print_summary(summary: MetadataIngestSummary) -> None:
    print(json.dumps(_json_ready(summary.to_mapping()), indent=2, sort_keys=True))


def main(argv: Sequence[str] | None = None) -> int:
    """CLI for ``python -m alpha_system.data.databento.metadata_ingest``."""

    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        summary = run_metadata_ingest(
            file_manifest_path=args.file_manifest,
            output_root=args.output_root,
        )
    except DataFoundationValidationError as exc:
        print(f"metadata_ingest blocked: {exc}", file=sys.stderr)
        return 2
    _print_summary(summary)
    return 0


__all__ = ["MetadataIngestSummary", "run_metadata_ingest"]


if __name__ == "__main__":
    raise SystemExit(main())
