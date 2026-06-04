"""Free Databento historical cost quote and budget-gate manifest tooling."""

from __future__ import annotations

import argparse
import math
import os
import sys
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType

from alpha_system.data.databento.client import build_historical_client
from alpha_system.data.databento.request_spec import (
    DATABENTO_ALLOWED_SCHEMAS,
    DatabentoRequestSpec,
    _require_bool,
    _require_sha256_hex,
    _require_text,
    _stable_hash,
    load_json_mapping,
    request_spec_hash,
    write_json_mapping,
)
from alpha_system.data.foundation.sources import (
    DataFoundationValidationError,
    require_databento_external_access,
)

DEFAULT_MAX_COST_USD = 110.0
COST_MANIFEST_SCHEMA = "alpha_system.databento.cost_manifest.v1"


def _normalize_usd(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        msg = f"{field_name} must be a non-negative finite USD number"
        raise DataFoundationValidationError(msg)
    normalized = float(value)
    if not math.isfinite(normalized) or normalized < 0:
        msg = f"{field_name} must be a non-negative finite USD number"
        raise DataFoundationValidationError(msg)
    return round(normalized, 6)


def _normalize_max_cost(value: object) -> float:
    max_cost = _normalize_usd(value, "max_cost_usd")
    if max_cost <= 0:
        msg = "max_cost_usd must be positive"
        raise DataFoundationValidationError(msg)
    return max_cost


def _normalize_schema_costs(value: object) -> Mapping[str, float]:
    if not isinstance(value, Mapping):
        msg = "per_schema_usd must be a mapping"
        raise DataFoundationValidationError(msg)
    allowed = frozenset(DATABENTO_ALLOWED_SCHEMAS)
    costs: dict[str, float] = {}
    for schema, cost in value.items():
        schema_name = _require_text(schema, "per_schema_usd schema").lower()
        if schema_name not in allowed:
            allowed_text = ", ".join(DATABENTO_ALLOWED_SCHEMAS)
            msg = f"per_schema_usd keys must be a subset of {allowed_text}"
            raise DataFoundationValidationError(msg)
        costs[schema_name] = _normalize_usd(cost, f"per_schema_usd.{schema_name}")
    if not costs:
        msg = "per_schema_usd must not be empty"
        raise DataFoundationValidationError(msg)
    return MappingProxyType(dict(sorted(costs.items())))


def _normalize_text_tuple(value: object, field_name: str) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        msg = f"{field_name} must be a non-empty sequence of strings"
        raise DataFoundationValidationError(msg)
    normalized = tuple(_require_text(item, field_name) for item in value)
    if not normalized:
        msg = f"{field_name} must not be empty"
        raise DataFoundationValidationError(msg)
    return normalized


def _parse_created_at(value: object) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        raw = _require_text(value, "created_at")
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError as exc:
            msg = "created_at must be an ISO-8601 timezone-aware datetime"
            raise DataFoundationValidationError(msg) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        msg = "created_at must be timezone-aware"
        raise DataFoundationValidationError(msg)
    return parsed


def compute_cost_manifest_hash(
    *,
    request_spec_digest: str,
    per_schema_usd: Mapping[str, float],
    total_usd: float,
    max_cost_usd: float,
    under_budget: bool,
    symbols: Sequence[str],
    stype_in: str,
    start: str,
    end: str,
    dataset: str,
) -> str:
    return _stable_hash(
        {
            "schema": COST_MANIFEST_SCHEMA,
            "request_spec_hash": _require_sha256_hex(
                request_spec_digest,
                "request_spec_hash",
            ),
            "per_schema_usd": _normalize_schema_costs(per_schema_usd),
            "total_usd": _normalize_usd(total_usd, "total_usd"),
            "max_cost_usd": _normalize_max_cost(max_cost_usd),
            "under_budget": _require_bool(under_budget, "under_budget"),
            "symbols": _normalize_text_tuple(symbols, "symbols"),
            "stype_in": _require_text(stype_in, "stype_in"),
            "start": _require_text(start, "start"),
            "end": _require_text(end, "end"),
            "dataset": _require_text(dataset, "dataset"),
        }
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class CostManifest:
    """Databento quote manifest proving cost was checked before paid submit."""

    request_spec_hash: str
    per_schema_usd: Mapping[str, float]
    total_usd: float
    max_cost_usd: float
    under_budget: bool
    symbols: tuple[str, ...]
    stype_in: str
    start: str
    end: str
    dataset: str
    created_at: datetime
    manifest_hash: str | None = None

    def __post_init__(self) -> None:
        request_digest = _require_sha256_hex(self.request_spec_hash, "request_spec_hash")
        schema_costs = _normalize_schema_costs(self.per_schema_usd)
        total = _normalize_usd(self.total_usd, "total_usd")
        max_cost = _normalize_max_cost(self.max_cost_usd)
        under_budget = _require_bool(self.under_budget, "under_budget")
        symbols = _normalize_text_tuple(self.symbols, "symbols")
        stype_in = _require_text(self.stype_in, "stype_in")
        start = _require_text(self.start, "start")
        end = _require_text(self.end, "end")
        dataset = _require_text(self.dataset, "dataset")
        created_at = _parse_created_at(self.created_at)

        schema_total = round(sum(schema_costs.values()), 6)
        if not math.isclose(total, schema_total, rel_tol=0, abs_tol=0.000001):
            msg = "total_usd must equal the sum of per_schema_usd values"
            raise DataFoundationValidationError(msg)
        if under_budget != (total <= max_cost):
            msg = "under_budget must reflect total_usd <= max_cost_usd"
            raise DataFoundationValidationError(msg)

        computed_hash = compute_cost_manifest_hash(
            request_spec_digest=request_digest,
            per_schema_usd=schema_costs,
            total_usd=total,
            max_cost_usd=max_cost,
            under_budget=under_budget,
            symbols=symbols,
            stype_in=stype_in,
            start=start,
            end=end,
            dataset=dataset,
        )
        if self.manifest_hash is not None:
            supplied_hash = _require_sha256_hex(self.manifest_hash, "manifest_hash")
            if supplied_hash != computed_hash:
                msg = "manifest_hash does not match cost manifest content"
                raise DataFoundationValidationError(msg)

        object.__setattr__(self, "request_spec_hash", request_digest)
        object.__setattr__(self, "per_schema_usd", schema_costs)
        object.__setattr__(self, "total_usd", total)
        object.__setattr__(self, "max_cost_usd", max_cost)
        object.__setattr__(self, "under_budget", under_budget)
        object.__setattr__(self, "symbols", symbols)
        object.__setattr__(self, "stype_in", stype_in)
        object.__setattr__(self, "start", start)
        object.__setattr__(self, "end", end)
        object.__setattr__(self, "dataset", dataset)
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "manifest_hash", computed_hash)

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> CostManifest:
        if values.get("schema") != COST_MANIFEST_SCHEMA:
            msg = f"cost manifest schema must be {COST_MANIFEST_SCHEMA}"
            raise DataFoundationValidationError(msg)
        required = (
            "request_spec_hash",
            "per_schema_usd",
            "total_usd",
            "max_cost_usd",
            "under_budget",
            "symbols",
            "stype_in",
            "start",
            "end",
            "dataset",
            "created_at",
            "manifest_hash",
        )
        missing = tuple(field for field in required if field not in values)
        if missing:
            msg = "CostManifest missing required fields: " + ", ".join(missing)
            raise DataFoundationValidationError(msg)
        return cls(
            request_spec_hash=values["request_spec_hash"],
            per_schema_usd=values["per_schema_usd"],
            total_usd=values["total_usd"],
            max_cost_usd=values["max_cost_usd"],
            under_budget=values["under_budget"],
            symbols=values["symbols"],
            stype_in=values["stype_in"],
            start=values["start"],
            end=values["end"],
            dataset=values["dataset"],
            created_at=values["created_at"],
            manifest_hash=values["manifest_hash"],
        )

    def to_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "schema": COST_MANIFEST_SCHEMA,
                "request_spec_hash": self.request_spec_hash,
                "per_schema_usd": self.per_schema_usd,
                "total_usd": self.total_usd,
                "max_cost_usd": self.max_cost_usd,
                "under_budget": self.under_budget,
                "symbols": self.symbols,
                "stype_in": self.stype_in,
                "start": self.start,
                "end": self.end,
                "dataset": self.dataset,
                "created_at": self.created_at.isoformat(),
                "manifest_hash": self.manifest_hash,
            }
        )


def load_cost_manifest(path: Path) -> CostManifest:
    return CostManifest.from_mapping(load_json_mapping(path))


def write_cost_manifest(manifest: CostManifest, output_path: Path) -> Path:
    return write_json_mapping(output_path, manifest.to_mapping())


@contextmanager
def _historical_client_context(
    *,
    client: object | None,
    env: Mapping[str, str] | None,
    require_raw_write: bool,
) -> Iterator[object]:
    if client is not None:
        with nullcontext(client) as injected:
            yield injected
        return

    require_databento_external_access(env, require_raw_write=require_raw_write)
    with build_historical_client(env) as live_client:
        yield live_client


def _coerce_request_spec(
    request_spec: DatabentoRequestSpec | Mapping[str, object],
) -> DatabentoRequestSpec:
    if isinstance(request_spec, DatabentoRequestSpec):
        return request_spec
    return DatabentoRequestSpec.from_mapping(request_spec)


def run_cost_check(
    *,
    request_spec: DatabentoRequestSpec | Mapping[str, object],
    client: object | None = None,
    max_cost_usd: float = DEFAULT_MAX_COST_USD,
    env: Mapping[str, str] | None = None,
    output_path: Path | None = None,
    now: datetime | None = None,
) -> CostManifest:
    """Quote Databento cost for each schema and optionally write a manifest."""

    spec = _coerce_request_spec(request_spec)
    max_cost = _normalize_max_cost(max_cost_usd)
    created_at = now or datetime.now(UTC)
    request_digest = request_spec_hash(spec)

    per_schema: dict[str, float] = {}
    with _historical_client_context(client=client, env=env, require_raw_write=False) as db_client:
        metadata = getattr(db_client, "metadata", None)
        get_cost = getattr(metadata, "get_cost", None)
        if not callable(get_cost):
            msg = "Databento client must expose metadata.get_cost"
            raise DataFoundationValidationError(msg)
        for schema in spec.schemas:
            quoted = get_cost(
                dataset=spec.dataset,
                start=spec.start.isoformat(),
                end=spec.end.isoformat(),
                mode="historical",
                symbols=list(spec.symbols),
                schema=schema,
                stype_in=spec.stype_in,
            )
            per_schema[schema] = _normalize_usd(quoted, f"get_cost.{schema}")

    total = round(sum(per_schema.values()), 6)
    manifest = CostManifest(
        request_spec_hash=request_digest,
        per_schema_usd=per_schema,
        total_usd=total,
        max_cost_usd=max_cost,
        under_budget=total <= max_cost,
        symbols=spec.symbols,
        stype_in=spec.stype_in,
        start=spec.start.isoformat(),
        end=spec.end.isoformat(),
        dataset=spec.dataset,
        created_at=created_at,
    )
    if output_path is not None:
        write_cost_manifest(manifest, output_path)
    return manifest


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Quote Databento historical cost and enforce the budget gate",
    )
    parser.add_argument("--request-spec", type=Path, required=True)
    parser.add_argument("--output", "-o", type=Path, required=True)
    parser.add_argument("--max-cost-usd", type=float, default=DEFAULT_MAX_COST_USD)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI for ``python -m alpha_system.data.databento.cost_check``."""

    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        spec = DatabentoRequestSpec.from_mapping(load_json_mapping(args.request_spec))
        manifest = run_cost_check(
            request_spec=spec,
            max_cost_usd=args.max_cost_usd,
            env=os.environ,
            output_path=args.output,
        )
    except DataFoundationValidationError as exc:
        print(f"cost_check blocked: {exc}", file=sys.stderr)
        return 2
    return 0 if manifest.under_budget else 2


__all__ = [
    "COST_MANIFEST_SCHEMA",
    "DEFAULT_MAX_COST_USD",
    "CostManifest",
    "compute_cost_manifest_hash",
    "load_cost_manifest",
    "run_cost_check",
    "write_cost_manifest",
]


if __name__ == "__main__":
    raise SystemExit(main())
