"""Backtest CLI command group."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

from alpha_system.backtest.engine_config import (
    EngineConfigError,
    load_reference_engine_config,
)
from alpha_system.backtest.reference import ReferenceBacktestError, run_reference_backtest
from alpha_system.data.storage import read_csv_fixture_bars
from alpha_system.signals.io import SignalIOError, read_signal_records


def run_backtest(args: argparse.Namespace) -> int:
    """Run ``alpha backtest run``."""
    try:
        config = load_reference_engine_config(args.execution_config)
        bars = read_csv_fixture_bars(args.bars_path)
        signals = read_signal_records(args.signals_path)
        factor_versions = _parse_factor_versions(tuple(args.factor_version or ()))
        instrument_multipliers = _parse_key_value(
            tuple(args.instrument_multiplier or ()), "--instrument-multiplier"
        ) or None
        instrument_roots = _parse_key_value(
            tuple(args.instrument_root or ()), "--instrument-root"
        ) or None
        bars = _filter_bars(
            bars,
            start_ts=args.start_ts,
            end_ts=args.end_ts,
            sessions=tuple(args.session_id or ()),
        )
        signals = _filter_signals(
            signals,
            start_ts=args.start_ts,
            end_ts=args.end_ts,
            sessions=tuple(args.session_id or ()),
        )
        result = run_reference_backtest(
            bars=bars,
            signals=signals,
            config=config,
            strategy_id=args.strategy_id,
            strategy_version=args.strategy_version,
            data_version=args.data_version,
            factor_versions=factor_versions or None,
            instrument_multipliers=instrument_multipliers,
            instrument_roots=instrument_roots,
            output_dir=args.output_dir,
            registry_path=args.registry_path,
            run_manifest_path=args.run_manifest,
            run_parameters={
                "management_spec": args.management_spec,
                "portfolio_spec": args.portfolio_spec,
            },
            write_outputs=True,
        )
    except (
        EngineConfigError,
        ReferenceBacktestError,
        SignalIOError,
        OSError,
        ValueError,
    ) as exc:
        print(f"backtest command error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result.summary.to_dict(), sort_keys=True, indent=2))
        return 0

    print("Backtest command: run")
    print(f"Run: {result.summary.run_id}")
    print(f"Engine: {result.summary.engine_version}")
    print(f"Strategy: {result.summary.strategy_id} {result.summary.strategy_version}")
    print(f"Data version: {result.summary.data_version}")
    print(f"Trades: {result.summary.total_trades}")
    print(f"Open positions: {result.summary.open_positions}")
    print(f"Net PnL: {result.summary.net_pnl}")
    if result.output_paths is not None:
        print(f"Summary: {result.output_paths.summary_path}")
        print(f"Manifest: {result.output_paths.manifest_path}")
    if result.registry_path is not None:
        print(f"Registry: {result.registry_path}")
        print(f"Registry written: {'yes' if result.registry_written else 'no'}")
    return 0


def register_subparser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the ``alpha backtest`` command group."""
    backtest_parser = subparsers.add_parser(
        "backtest",
        help="Run canonical Tier 1 reference backtests on local inputs.",
    )
    backtest_subparsers = backtest_parser.add_subparsers(dest="backtest_command")

    run_parser = backtest_subparsers.add_parser(
        "run",
        help="Run the canonical reference 1-minute bar backtest.",
    )
    run_parser.add_argument(
        "--strategy-id",
        required=True,
        help="Strategy identifier for the declared signal stream.",
    )
    run_parser.add_argument(
        "--strategy-version",
        required=True,
        help="Strategy version for the declared signal stream.",
    )
    run_parser.add_argument(
        "--management-spec",
        default="baseline",
        help="Baseline management-spec placeholder recorded for run context.",
    )
    run_parser.add_argument(
        "--portfolio-spec",
        default="baseline",
        help="Baseline portfolio-spec placeholder recorded for run context.",
    )
    run_parser.add_argument(
        "--data-version",
        required=True,
        help="Data version expected on every selected bar and signal.",
    )
    run_parser.add_argument(
        "--factor-version",
        action="append",
        help="Declared factor version as factor_id=version; repeat for multiple factors.",
    )
    run_parser.add_argument(
        "--instrument-multiplier",
        action="append",
        help=(
            "Explicit dollar contract multiplier as instrument_id=value; repeat per "
            "instrument. Overrides instrument-master resolution (fail-loud otherwise)."
        ),
    )
    run_parser.add_argument(
        "--instrument-root",
        action="append",
        help=(
            "Map a bar instrument_id to an instrument-master root_symbol as "
            "instrument_id=ROOT (e.g. inst_databento_es=ES); repeat per instrument."
        ),
    )
    run_parser.add_argument(
        "--execution-config",
        required=True,
        help="Path to reference execution config JSON/YAML.",
    )
    run_parser.add_argument(
        "--bars-path",
        required=True,
        help="Local CSV canonical 1-minute bar input path.",
    )
    run_parser.add_argument(
        "--signals-path",
        required=True,
        help="Local JSONL SignalRecord input path.",
    )
    run_parser.add_argument(
        "--start-ts",
        help="Optional inclusive ISO-8601 bar event_ts start.",
    )
    run_parser.add_argument(
        "--end-ts",
        help="Optional inclusive ISO-8601 bar event_ts end.",
    )
    run_parser.add_argument(
        "--session-id",
        action="append",
        help="Optional session_id selector; repeat for multiple sessions.",
    )
    run_parser.add_argument(
        "--registry-path",
        help="Optional temp/local SQLite registry path outside the repository.",
    )
    run_parser.add_argument(
        "--output-dir",
        help="Optional temp/local output directory for trade/equity artifacts.",
    )
    run_parser.add_argument(
        "--run-manifest",
        help="Optional temp/local run manifest path.",
    )
    run_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON console summary.",
    )
    run_parser.set_defaults(handler=run_backtest)


def _parse_factor_versions(values: tuple[str, ...]) -> dict[str, str]:
    versions: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            msg = "--factor-version values must be factor_id=version"
            raise ValueError(msg)
        factor_id, factor_version = value.split("=", 1)
        factor_id = factor_id.strip()
        factor_version = factor_version.strip()
        if not factor_id or not factor_version:
            msg = "--factor-version values must include non-empty factor_id and version"
            raise ValueError(msg)
        existing = versions.get(factor_id)
        if existing is not None and existing != factor_version:
            msg = f"conflicting factor version for {factor_id}"
            raise ValueError(msg)
        versions[factor_id] = factor_version
    return versions


def _parse_key_value(values: tuple[str, ...], flag: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            msg = f"{flag} values must be key=value"
            raise ValueError(msg)
        key, raw = value.split("=", 1)
        key = key.strip()
        raw = raw.strip()
        if not key or not raw:
            msg = f"{flag} values must include non-empty key and value"
            raise ValueError(msg)
        existing = parsed.get(key)
        if existing is not None and existing != raw:
            msg = f"conflicting {flag} value for {key}"
            raise ValueError(msg)
        parsed[key] = raw
    return parsed


def _filter_bars(
    bars: tuple[dict[str, object], ...],
    *,
    start_ts: str | None,
    end_ts: str | None,
    sessions: tuple[str, ...],
) -> tuple[dict[str, object], ...]:
    start = _optional_datetime(start_ts)
    end = _optional_datetime(end_ts)
    session_filter = set(sessions)
    return tuple(
        bar
        for bar in bars
        if _selected(bar["event_ts"], str(bar["session_id"]), start, end, session_filter)
    )


def _filter_signals(
    signals: tuple[object, ...],
    *,
    start_ts: str | None,
    end_ts: str | None,
    sessions: tuple[str, ...],
) -> tuple[object, ...]:
    start = _optional_datetime(start_ts)
    end = _optional_datetime(end_ts)
    session_filter = set(sessions)
    return tuple(
        signal
        for signal in signals
        if _selected(signal.event_ts, signal.session_id, start, end, session_filter)
    )


def _selected(
    event_ts: object,
    session_id: str,
    start_ts,
    end_ts,
    sessions: set[str],
) -> bool:
    active = _optional_datetime(event_ts)
    if active is None:
        return False
    if start_ts is not None and active < start_ts:
        return False
    if end_ts is not None and active > end_ts:
        return False
    return not sessions or session_id in sessions


def _optional_datetime(value):
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        active = value
    else:
        active = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if active.tzinfo is None:
        active = active.replace(tzinfo=timezone.utc)
    return active.astimezone(timezone.utc)
