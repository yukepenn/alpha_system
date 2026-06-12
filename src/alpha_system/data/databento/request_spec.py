"""Databento historical request specs for the ES/NQ/RTY deep-history pull.

This module is intentionally offline: it validates and writes request intent,
but it performs no provider calls and imports no Databento SDK objects.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import MappingProxyType

from alpha_system.data.foundation.serialization import json_ready as _json_ready
from alpha_system.data.foundation.sources import DataFoundationValidationError

DATABENTO_DATASET = "GLBX.MDP3"
DATABENTO_ENCODING = "dbn"
DATABENTO_COMPRESSION = "zstd"
DATABENTO_STYPE_CONTINUOUS = "continuous"
DATABENTO_STYPE_PARENT = "parent"
DATABENTO_ALLOWED_STYPES: tuple[str, ...] = (
    DATABENTO_STYPE_CONTINUOUS,
    DATABENTO_STYPE_PARENT,
)
DATABENTO_ALLOWED_SCHEMAS: tuple[str, ...] = (
    "ohlcv-1m",
    "bbo-1m",
    "tbbo",
    "definition",
    "statistics",
    "status",
)
DATABENTO_CONTINUOUS_SYMBOLS: tuple[str, ...] = ("ES.v.0", "NQ.v.0", "RTY.v.0")
DATABENTO_PARENT_SYMBOLS: tuple[str, ...] = ("ES.FUT", "NQ.FUT", "RTY.FUT")
DATABENTO_MICRO_ROOTS: frozenset[str] = frozenset({"MES", "MNQ", "M2K"})

REQUEST_SPEC_HASH_SCHEMA = "alpha_system.databento.request_spec.v1"
_SHA256_HEX_LEN = 64


def _stable_hash(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        _json_ready(payload),
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _require_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        msg = f"{field_name} must be a mapping"
        raise DataFoundationValidationError(msg)
    return value


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        msg = f"{field_name} must be a non-empty string"
        raise DataFoundationValidationError(msg)
    normalized = value.strip()
    if not normalized:
        msg = f"{field_name} must be a non-empty string"
        raise DataFoundationValidationError(msg)
    return normalized


def _require_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        msg = f"{field_name} must be a boolean"
        raise DataFoundationValidationError(msg)
    return value


def _require_sha256_hex(value: object, field_name: str) -> str:
    digest = _require_text(value, field_name).lower()
    if len(digest) != _SHA256_HEX_LEN or not all(char in "0123456789abcdef" for char in digest):
        msg = f"{field_name} must be a lowercase sha256 hex digest"
        raise DataFoundationValidationError(msg)
    return digest


def _parse_aware_datetime(value: object, field_name: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        raw = _require_text(value, field_name)
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError as exc:
            msg = f"{field_name} must be an ISO-8601 timezone-aware datetime"
            raise DataFoundationValidationError(msg) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        msg = f"{field_name} must be timezone-aware"
        raise DataFoundationValidationError(msg)
    return parsed


def _datetime_iso(value: datetime) -> str:
    return value.isoformat()


def _normalize_dataset(value: object) -> str:
    dataset = _require_text(value, "dataset").upper()
    if dataset != DATABENTO_DATASET:
        msg = f"dataset must be {DATABENTO_DATASET}"
        raise DataFoundationValidationError(msg)
    return DATABENTO_DATASET


def _normalize_stype(value: object) -> str:
    stype = _require_text(value, "stype_in").lower()
    if stype not in DATABENTO_ALLOWED_STYPES:
        allowed = ", ".join(DATABENTO_ALLOWED_STYPES)
        msg = f"stype_in must be one of {allowed}"
        raise DataFoundationValidationError(msg)
    return stype


def _symbol_root(symbol: str) -> str:
    return symbol.replace(".", " ").split()[0].upper()


def _normalize_symbols(value: object, *, stype_in: str) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, Iterable):
        msg = "symbols must be a non-empty iterable of Databento symbols"
        raise DataFoundationValidationError(msg)

    allowed = (
        DATABENTO_CONTINUOUS_SYMBOLS
        if stype_in == DATABENTO_STYPE_CONTINUOUS
        else DATABENTO_PARENT_SYMBOLS
    )
    canonical_by_lower = {symbol.lower(): symbol for symbol in allowed}

    symbols: list[str] = []
    seen: set[str] = set()
    for item in value:
        raw = _require_text(item, "symbols")
        root = _symbol_root(raw)
        if root in DATABENTO_MICRO_ROOTS:
            msg = "Databento ES/NQ/RTY pull rejects micro futures symbols"
            raise DataFoundationValidationError(msg)
        try:
            symbol = canonical_by_lower[raw.lower()]
        except KeyError as exc:
            allowed_text = ", ".join(allowed)
            msg = f"symbols for stype_in={stype_in!r} must be a subset of {allowed_text}"
            raise DataFoundationValidationError(msg) from exc
        if symbol in seen:
            msg = f"symbols contains duplicate Databento symbol {symbol!r}"
            raise DataFoundationValidationError(msg)
        seen.add(symbol)
        symbols.append(symbol)

    if not symbols:
        msg = "symbols must not be empty"
        raise DataFoundationValidationError(msg)
    return tuple(symbols)


def _normalize_schemas(value: object) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, Iterable):
        msg = "schemas must be a non-empty iterable of Databento schema names"
        raise DataFoundationValidationError(msg)

    allowed = frozenset(DATABENTO_ALLOWED_SCHEMAS)
    schemas: list[str] = []
    seen: set[str] = set()
    for item in value:
        schema = _require_text(item, "schemas").lower()
        if schema not in allowed:
            allowed_text = ", ".join(DATABENTO_ALLOWED_SCHEMAS)
            msg = f"schemas must be a subset of {allowed_text}"
            raise DataFoundationValidationError(msg)
        if schema in seen:
            msg = f"schemas contains duplicate schema {schema!r}"
            raise DataFoundationValidationError(msg)
        seen.add(schema)
        schemas.append(schema)

    if not schemas:
        msg = "schemas must not be empty"
        raise DataFoundationValidationError(msg)
    return tuple(schemas)


def _normalize_encoding(value: object) -> str:
    encoding = _require_text(value, "encoding").lower()
    if encoding != DATABENTO_ENCODING:
        msg = f"encoding must be {DATABENTO_ENCODING}"
        raise DataFoundationValidationError(msg)
    return DATABENTO_ENCODING


def _normalize_compression(value: object) -> str:
    compression = _require_text(value, "compression").lower()
    if compression != DATABENTO_COMPRESSION:
        msg = f"compression must be {DATABENTO_COMPRESSION}"
        raise DataFoundationValidationError(msg)
    return DATABENTO_COMPRESSION


def load_json_mapping(path: Path) -> Mapping[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        msg = f"{path.as_posix()} must contain JSON object content"
        raise DataFoundationValidationError(msg) from exc
    return _require_mapping(payload, path.as_posix())


def write_json_mapping(path: Path, payload: Mapping[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(_json_ready(payload), handle, indent=2, sort_keys=True)
        handle.write("\n")
    return path


@dataclass(frozen=True, slots=True, kw_only=True)
class DatabentoRequestSpec:
    """Validated offline request spec for a Databento historical batch."""

    symbols: tuple[str, ...]
    stype_in: str
    schemas: tuple[str, ...]
    start: datetime
    end: datetime
    dataset: str = DATABENTO_DATASET
    encoding: str = DATABENTO_ENCODING
    compression: str = DATABENTO_COMPRESSION

    def __post_init__(self) -> None:
        stype_in = _normalize_stype(self.stype_in)
        symbols = _normalize_symbols(self.symbols, stype_in=stype_in)
        schemas = _normalize_schemas(self.schemas)
        start = _parse_aware_datetime(self.start, "start")
        end = _parse_aware_datetime(self.end, "end")
        if end <= start:
            msg = "end must be after start"
            raise DataFoundationValidationError(msg)

        object.__setattr__(self, "dataset", _normalize_dataset(self.dataset))
        object.__setattr__(self, "symbols", symbols)
        object.__setattr__(self, "stype_in", stype_in)
        object.__setattr__(self, "schemas", schemas)
        object.__setattr__(self, "start", start)
        object.__setattr__(self, "end", end)
        object.__setattr__(self, "encoding", _normalize_encoding(self.encoding))
        object.__setattr__(self, "compression", _normalize_compression(self.compression))

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> DatabentoRequestSpec:
        missing = tuple(
            field for field in ("symbols", "stype_in", "schemas", "start") if field not in values
        )
        if missing:
            msg = "DatabentoRequestSpec missing required fields: " + ", ".join(missing)
            raise DataFoundationValidationError(msg)
        if "end" not in values:
            msg = "DatabentoRequestSpec missing required field: end"
            raise DataFoundationValidationError(msg)

        spec = cls(
            dataset=values.get("dataset", DATABENTO_DATASET),
            symbols=values["symbols"],
            stype_in=values["stype_in"],
            schemas=values["schemas"],
            start=_parse_aware_datetime(values["start"], "start"),
            end=_parse_aware_datetime(values["end"], "end"),
            encoding=values.get("encoding", DATABENTO_ENCODING),
            compression=values.get("compression", DATABENTO_COMPRESSION),
        )
        if "as_of" in values:
            as_of = _parse_aware_datetime(values["as_of"], "as_of")
            if as_of != spec.end:
                msg = "as_of must match the explicit end timestamp"
                raise DataFoundationValidationError(msg)
        return spec

    def to_mapping(self) -> Mapping[str, object]:
        """Return the JSON-stable request spec with explicit ``as_of`` end metadata."""

        return MappingProxyType(
            {
                "dataset": self.dataset,
                "symbols": self.symbols,
                "stype_in": self.stype_in,
                "schemas": self.schemas,
                "start": _datetime_iso(self.start),
                "end": _datetime_iso(self.end),
                "as_of": _datetime_iso(self.end),
                "encoding": self.encoding,
                "compression": self.compression,
            }
        )


def request_spec_hash(request_spec: DatabentoRequestSpec | Mapping[str, object]) -> str:
    spec = (
        request_spec
        if isinstance(request_spec, DatabentoRequestSpec)
        else DatabentoRequestSpec.from_mapping(request_spec)
    )
    return _stable_hash(
        {
            "schema": REQUEST_SPEC_HASH_SCHEMA,
            "request_spec": spec.to_mapping(),
        }
    )


def build_default_continuous_request_spec(
    start: str | datetime,
    end: str | datetime,
) -> DatabentoRequestSpec:
    """Build the default ES/NQ/RTY continuous spec over all allowed schemas."""

    return DatabentoRequestSpec(
        symbols=DATABENTO_CONTINUOUS_SYMBOLS,
        stype_in=DATABENTO_STYPE_CONTINUOUS,
        schemas=DATABENTO_ALLOWED_SCHEMAS,
        start=_parse_aware_datetime(start, "start"),
        end=_parse_aware_datetime(end, "end"),
    )


def write_request_spec_json(request_spec: DatabentoRequestSpec, output_path: Path) -> Path:
    return write_json_mapping(output_path, request_spec.to_mapping())


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Emit an offline Databento ES/NQ/RTY request spec JSON file",
    )
    parser.add_argument("--start", required=True, help="Timezone-aware ISO start timestamp")
    parser.add_argument("--end", required=True, help="Timezone-aware ISO explicit end timestamp")
    parser.add_argument("--output", "-o", type=Path, required=True)
    parser.add_argument("--dataset", default=DATABENTO_DATASET)
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=DATABENTO_CONTINUOUS_SYMBOLS,
        help="Databento symbols; defaults to ES.v.0 NQ.v.0 RTY.v.0",
    )
    parser.add_argument(
        "--stype-in",
        choices=DATABENTO_ALLOWED_STYPES,
        default=DATABENTO_STYPE_CONTINUOUS,
    )
    parser.add_argument(
        "--schemas",
        nargs="+",
        default=DATABENTO_ALLOWED_SCHEMAS,
        help="Allowed schemas: ohlcv-1m bbo-1m tbbo definition statistics status",
    )
    parser.add_argument("--encoding", default=DATABENTO_ENCODING)
    parser.add_argument("--compression", default=DATABENTO_COMPRESSION)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI for ``python -m alpha_system.data.databento.request_spec``."""

    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        spec = DatabentoRequestSpec(
            dataset=args.dataset,
            symbols=tuple(args.symbols),
            stype_in=args.stype_in,
            schemas=tuple(args.schemas),
            start=_parse_aware_datetime(args.start, "start"),
            end=_parse_aware_datetime(args.end, "end"),
            encoding=args.encoding,
            compression=args.compression,
        )
        path = write_request_spec_json(spec, args.output)
    except DataFoundationValidationError as exc:
        print(f"request_spec blocked: {exc}", file=sys.stderr)
        return 2
    print(path.as_posix())
    return 0


__all__ = [
    "DATABENTO_ALLOWED_SCHEMAS",
    "DATABENTO_ALLOWED_STYPES",
    "DATABENTO_COMPRESSION",
    "DATABENTO_CONTINUOUS_SYMBOLS",
    "DATABENTO_DATASET",
    "DATABENTO_ENCODING",
    "DATABENTO_PARENT_SYMBOLS",
    "DatabentoRequestSpec",
    "build_default_continuous_request_spec",
    "load_json_mapping",
    "request_spec_hash",
    "write_json_mapping",
    "write_request_spec_json",
]


if __name__ == "__main__":
    raise SystemExit(main())
