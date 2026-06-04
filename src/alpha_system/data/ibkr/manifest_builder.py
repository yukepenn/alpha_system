"""Pure IBKR historical request manifest builders."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from types import MappingProxyType

from alpha_system.data.foundation.ibkr import IBKRConnectionProfile
from alpha_system.data.foundation.instruments import (
    InstrumentMasterRecord,
    load_futures_instrument_master_by_root,
)
from alpha_system.data.foundation.requests import (
    HistoricalRequestManifest,
    HistoricalRequestSpec,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError

DEFAULT_SYMBOLS: tuple[str, ...] = ("ES", "NQ", "RTY")
DEFAULT_PACING_POLICY_ID = "rpp_ibkr_historical_conservative_tobeverified_v1"
SOURCE_ID = "dsrc_ibkr_historical"
BAR_SIZE = "1 min"
WHAT_TO_SHOW = "TRADES"
QUARTER_MONTH_CODES: Mapping[int, str] = MappingProxyType({3: "H", 6: "M", 9: "U", 12: "Z"})
QUARTER_START_MONTHS: Mapping[int, int] = MappingProxyType({3: 1, 6: 4, 9: 7, 12: 10})


def _require_env_present(env: Mapping[str, str], name: str) -> str:
    value = env.get(name)
    if value is None or not value.strip():
        msg = f"{name} is required to build an IBKR backfill manifest"
        raise DataFoundationValidationError(msg)
    return value


def _normalize_symbols(symbols: Sequence[str]) -> tuple[str, ...]:
    normalized = tuple(symbol.strip().upper() for symbol in symbols if symbol.strip())
    if not normalized:
        msg = "symbols must contain at least one root"
        raise DataFoundationValidationError(msg)
    duplicates = tuple(sorted({symbol for symbol in normalized if normalized.count(symbol) > 1}))
    if duplicates:
        msg = "symbols must not contain duplicates: " + ", ".join(duplicates)
        raise DataFoundationValidationError(msg)
    masters = load_futures_instrument_master_by_root()
    missing = tuple(symbol for symbol in normalized if symbol not in masters)
    if missing:
        msg = "symbols missing from futures instrument master: " + ", ".join(missing)
        raise DataFoundationValidationError(msg)
    return normalized


def _require_positive_int(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        msg = f"{field_name} must be a positive integer"
        raise DataFoundationValidationError(msg)
    return value


def _utc_midnight(value: date) -> datetime:
    return datetime(value.year, value.month, value.day, tzinfo=UTC)


def _utc_minute(value: datetime) -> datetime:
    parsed = value
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        msg = "now must be timezone-aware"
        raise DataFoundationValidationError(msg)
    return parsed.astimezone(UTC).replace(second=0, microsecond=0)


def _master(symbol: str) -> InstrumentMasterRecord:
    return load_futures_instrument_master_by_root()[symbol]


def _recent_request_spec(
    *,
    symbol: str,
    master: InstrumentMasterRecord,
    profile: IBKRConnectionProfile,
    start_ts: datetime,
    end_ts: datetime,
    duration: str,
    trading_days: int,
) -> HistoricalRequestSpec:
    chunk_id = f"hchunk_ibkr_recent_{symbol.lower()}_{trading_days}d"
    return HistoricalRequestSpec(
        request_spec_id=f"hrs_ibkr_recent_{symbol.lower()}_{trading_days}d",
        source_id=SOURCE_ID,
        symbol_root=symbol,
        contract_ref=f"fcr_ibkr_{symbol.lower()}_contfut_recent_to_be_verified",
        sec_type="CONTFUT",
        exchange=master.exchange,
        currency=master.currency,
        bar_size=BAR_SIZE,
        what_to_show=WHAT_TO_SHOW,
        use_rth=False,
        duration=duration,
        end_datetime_policy="ibkr_contfut_uses_empty_end_datetime",
        start_ts=start_ts,
        end_ts=end_ts,
        chunk_policy={
            "chunk_id": chunk_id,
            "planned_chunks": 1,
            "trading_days": trading_days,
            "policy": "recent_contfut_slice",
        },
        client_id=profile.client_id,
    )


def build_recent_slice_manifest(
    *,
    env: Mapping[str, str],
    profile: IBKRConnectionProfile,
    now: datetime,
    symbols: Sequence[str] = DEFAULT_SYMBOLS,
    trading_days: int = 2,
    batch: str = "recent_slice",
    pacing_policy_id: str = DEFAULT_PACING_POLICY_ID,
) -> HistoricalRequestManifest:
    """Build one short CONTFUT recent-slice chunk per symbol."""

    roots = _normalize_symbols(symbols)
    day_count = _require_positive_int(trading_days, "trading_days")
    data_root = _require_env_present(env, "ALPHA_DATA_ROOT")
    created_at = _utc_minute(now)
    end_ts = created_at
    start_ts = end_ts - timedelta(days=day_count)
    duration = f"{day_count} D"
    request_specs = tuple(
        _recent_request_spec(
            symbol=symbol,
            master=_master(symbol),
            profile=profile,
            start_ts=start_ts,
            end_ts=end_ts,
            duration=duration,
            trading_days=day_count,
        )
        for symbol in roots
    )
    return HistoricalRequestManifest.create(
        manifest_id=f"hrm_ibkr_{batch}_{day_count}d_v1",
        batch_id=f"batch_ibkr_{batch}_{day_count}d_v1",
        request_specs=request_specs,
        chunk_count=len(request_specs),
        expected_coverage={
            "slice": "recent_contfut",
            "roots": roots,
            "trading_days": day_count,
            "bar_size": BAR_SIZE,
            "what_to_show": WHAT_TO_SHOW,
            "use_rth": False,
            "quality_claim": False,
            "real_coverage_claim": False,
            "production_readiness_claim": False,
        },
        pacing_policy_id=pacing_policy_id,
        data_root=data_root,
        created_by="ADF1 Task 1B Stage A manifest_builder",
        created_at=created_at,
    )


def _quarter_window(year: int, contract_month: int) -> tuple[datetime, datetime]:
    start_month = QUARTER_START_MONTHS[contract_month]
    start_ts = _utc_midnight(date(year, start_month, 1))
    if contract_month == 12:
        end_ts = _utc_midnight(date(year + 1, 1, 1))
    else:
        end_ts = _utc_midnight(date(year, start_month + 3, 1))
    return start_ts, end_ts


def _full_request_spec(
    *,
    symbol: str,
    master: InstrumentMasterRecord,
    profile: IBKRConnectionProfile,
    year: int,
    contract_month: int,
) -> HistoricalRequestSpec:
    yyyymm = f"{year}{contract_month:02d}"
    month_code = QUARTER_MONTH_CODES[contract_month]
    start_ts, end_ts = _quarter_window(year, contract_month)
    duration_days = int((end_ts - start_ts).total_seconds() // 86_400)
    chunk_id = f"hchunk_ibkr_full_{symbol.lower()}_{yyyymm}"
    return HistoricalRequestSpec(
        request_spec_id=f"hrs_ibkr_full_{symbol.lower()}_{yyyymm}",
        source_id=SOURCE_ID,
        symbol_root=symbol,
        contract_ref=f"fcr_ibkr_{symbol.lower()}_fut_{yyyymm}",
        sec_type="FUT",
        exchange=master.exchange,
        currency=master.currency,
        bar_size=BAR_SIZE,
        what_to_show=WHAT_TO_SHOW,
        use_rth=False,
        duration=f"{duration_days} D",
        end_datetime_policy="explicit_dated_fut_end_ts",
        start_ts=start_ts,
        end_ts=end_ts,
        chunk_policy={
            "chunk_id": chunk_id,
            "planned_chunks": 1,
            "contract_year": year,
            "contract_month": contract_month,
            "contract_month_code": month_code,
            "duration_days": duration_days,
            "policy": "quarterly_dated_fut_contract",
        },
        client_id=profile.client_id,
    )


def build_full_backfill_manifest(
    *,
    env: Mapping[str, str],
    profile: IBKRConnectionProfile,
    end_date: date,
    now: datetime,
    symbols: Sequence[str] = DEFAULT_SYMBOLS,
    start_date: date = date(2018, 1, 1),
    batch: str = "full_backfill",
    pacing_policy_id: str = DEFAULT_PACING_POLICY_ID,
) -> HistoricalRequestManifest:
    """Build dated quarterly FUT manifests for the requested year range."""

    if end_date < start_date:
        msg = "end_date must be greater than or equal to start_date"
        raise DataFoundationValidationError(msg)
    roots = _normalize_symbols(symbols)
    data_root = _require_env_present(env, "ALPHA_DATA_ROOT")
    created_at = _utc_minute(now)
    request_specs = tuple(
        _full_request_spec(
            symbol=symbol,
            master=_master(symbol),
            profile=profile,
            year=year,
            contract_month=contract_month,
        )
        for symbol in roots
        for year in range(start_date.year, end_date.year + 1)
        for contract_month in QUARTER_MONTH_CODES
    )
    return HistoricalRequestManifest.create(
        manifest_id=f"hrm_ibkr_{batch}_{start_date.year}_{end_date.year}_v1",
        batch_id=f"batch_ibkr_{batch}_{start_date.year}_{end_date.year}_v1",
        request_specs=request_specs,
        chunk_count=len(request_specs),
        expected_coverage={
            "slice": "full_dated_quarterly_fut",
            "roots": roots,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "contract_month_codes": tuple(QUARTER_MONTH_CODES.values()),
            "bar_size": BAR_SIZE,
            "what_to_show": WHAT_TO_SHOW,
            "use_rth": False,
            "quality_claim": False,
            "real_coverage_claim": False,
            "production_readiness_claim": False,
        },
        pacing_policy_id=pacing_policy_id,
        data_root=data_root,
        created_by="ADF1 Task 1B Stage A manifest_builder",
        created_at=created_at,
    )


def _json_ready(value: object) -> object:
    if isinstance(value, Mapping | MappingProxyType):
        return {str(key): _json_ready(nested) for key, nested in value.items()}
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Path):
        return value.as_posix()
    if value is None or isinstance(value, bool | int | float | str):
        return value
    msg = f"value {value!r} is not JSON-stable"
    raise DataFoundationValidationError(msg)


def write_manifest_json(manifest: HistoricalRequestManifest, path: str | Path) -> Path:
    """Write a manifest JSON file and return the resolved path."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(_json_ready(manifest.to_mapping()), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output


def emit_backfill_manifests(
    *,
    output_dir: str | Path,
    env: Mapping[str, str],
    profile: IBKRConnectionProfile,
    now: datetime,
    full_end_date: date,
    symbols: Sequence[str] = DEFAULT_SYMBOLS,
    recent_trading_days: int = 2,
    full_start_date: date = date(2018, 1, 1),
    pacing_policy_id: str = DEFAULT_PACING_POLICY_ID,
) -> Mapping[str, Path]:
    """Emit recent and full manifests under an operator-selected directory."""

    output = Path(output_dir)
    recent = build_recent_slice_manifest(
        env=env,
        profile=profile,
        now=now,
        symbols=symbols,
        trading_days=recent_trading_days,
        pacing_policy_id=pacing_policy_id,
    )
    full = build_full_backfill_manifest(
        env=env,
        profile=profile,
        now=now,
        symbols=symbols,
        start_date=full_start_date,
        end_date=full_end_date,
        pacing_policy_id=pacing_policy_id,
    )
    return MappingProxyType(
        {
            "recent": write_manifest_json(recent, output / "recent_slice_manifest.json"),
            "full": write_manifest_json(full, output / "full_backfill_manifest.json"),
        }
    )


def _parse_symbols(value: str) -> tuple[str, ...]:
    return tuple(part.strip().upper() for part in value.split(",") if part.strip())


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        msg = f"date must be ISO-8601 YYYY-MM-DD: {value!r}"
        raise argparse.ArgumentTypeError(msg) from exc


def _parse_datetime(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        msg = f"datetime must be ISO-8601 timezone-aware: {value!r}"
        raise argparse.ArgumentTypeError(msg) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        msg = f"datetime must be timezone-aware: {value!r}"
        raise argparse.ArgumentTypeError(msg)
    return parsed


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build IBKR historical request manifests")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS))
    parser.add_argument("--recent-trading-days", type=int, default=2)
    parser.add_argument("--full-start-date", type=_parse_date, default=date(2018, 1, 1))
    parser.add_argument("--full-end-date", type=_parse_date, required=True)
    parser.add_argument("--now", type=_parse_datetime)
    parser.add_argument("--pacing-policy-id", default=DEFAULT_PACING_POLICY_ID)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI for ``python -m alpha_system.data.ibkr.manifest_builder``."""

    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        profile = IBKRConnectionProfile.from_env(os.environ)
        now = args.now or datetime.now(UTC)
        paths = emit_backfill_manifests(
            output_dir=args.output_dir,
            env=os.environ,
            profile=profile,
            now=now,
            symbols=_parse_symbols(args.symbols),
            recent_trading_days=args.recent_trading_days,
            full_start_date=args.full_start_date,
            full_end_date=args.full_end_date,
            pacing_policy_id=args.pacing_policy_id,
        )
    except DataFoundationValidationError as exc:
        print(f"IBKR manifest builder blocked: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({key: path.as_posix() for key, path in paths.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
