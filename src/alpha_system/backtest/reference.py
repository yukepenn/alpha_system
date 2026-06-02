"""Tier 1 reference 1-minute bar backtest truth engine."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from alpha_system.backtest.accounting import AccountState, Position
from alpha_system.backtest.engine_config import ReferenceEngineConfig
from alpha_system.backtest.equity import equity_point_for_bar
from alpha_system.backtest.fills import (
    FillReason,
    ReferenceFill,
    eod_exit_price,
    resolve_entry_fill,
    resolve_exit_signal_fill,
    resolve_policy_exit_fill,
    resolve_stop_target,
)
from alpha_system.backtest.orders import OrderIntent, ReferenceOrder, order_id_for
from alpha_system.backtest.results import (
    BacktestSummary,
    ReferenceBacktestResult,
    manifest_payload,
    write_backtest_outputs,
)
from alpha_system.backtest.trades import TradeRecord, trade_from_closed_position
from alpha_system.core.enums import Direction
from alpha_system.core.git_info import capture_git_info
from alpha_system.core.hashing import hash_config
from alpha_system.core.registry import connect_registry, init_registry
from alpha_system.core.run_ids import generate_run_id
from alpha_system.data.build_bars import normalize_bar_rows
from alpha_system.data.fixture_policy import assert_registry_path_allowed
from alpha_system.experiments.registry import RunRecord, insert_run_record
from alpha_system.signals.spec import SignalRecord, SignalType


class ReferenceBacktestError(ValueError):
    """Raised when a reference backtest cannot run safely."""


class BacktestTimingError(ReferenceBacktestError):
    """Raised when data or signal availability would create lookahead."""


def run_reference_backtest(
    *,
    bars: Iterable[Mapping[str, Any]],
    signals: Iterable[SignalRecord | Mapping[str, Any]],
    config: ReferenceEngineConfig | None = None,
    strategy_id: str | None = None,
    strategy_version: str | None = None,
    data_version: str | None = None,
    factor_versions: Mapping[str, str] | None = None,
    initial_cash: Decimal = Decimal("100000"),
    output_dir: str | Path | None = None,
    registry_path: str | Path | None = None,
    run_manifest_path: str | Path | None = None,
    run_id: str | None = None,
    repo_root: str | Path | None = None,
    run_parameters: Mapping[str, Any] | None = None,
    write_outputs: bool = False,
) -> ReferenceBacktestResult:
    """Run the canonical conservative reference backtest over 1-minute bars."""
    active_config = config or ReferenceEngineConfig()
    normalized_bars = _normalize_bars(bars)
    normalized_signals = _normalize_signals(signals)
    if not normalized_bars:
        msg = "reference backtest requires at least one bar"
        raise ReferenceBacktestError(msg)
    if not normalized_signals:
        msg = "reference backtest requires at least one signal"
        raise ReferenceBacktestError(msg)

    active_data_version = data_version or str(normalized_bars[0]["data_version"])
    _assert_bars_match_data_version(normalized_bars, active_data_version)
    _assert_bar_latency(normalized_bars, active_config)
    _assert_signals_safe(normalized_signals, normalized_bars, active_data_version)

    active_strategy_id = strategy_id or _single_signal_field(normalized_signals, "strategy_id")
    active_strategy_version = strategy_version or _single_signal_field(
        normalized_signals,
        "strategy_version",
    )
    active_factor_versions = dict(factor_versions or _factor_versions_from_signals(normalized_signals))
    config_payload = {
        **active_config.to_dict(),
        **dict(run_parameters or {}),
    }
    config_hash = hash_config(config_payload)
    active_run_id = run_id or generate_run_id(
        "backtest",
        seed=f"{active_strategy_id}:{active_strategy_version}",
        components={
            "strategy_id": active_strategy_id,
            "strategy_version": active_strategy_version,
            "data_version": active_data_version,
            "factor_versions": active_factor_versions,
            "config_hash": config_hash,
        },
    )

    signals_by_fill_bar = _signals_by_fill_bar(normalized_signals, normalized_bars, active_config)
    account = AccountState(initial_cash=initial_cash)
    trades: list[TradeRecord] = []
    fills: list[ReferenceFill] = []
    equity_curve = []
    warnings: list[str] = []
    marks: dict[str, Decimal] = {}
    sorted_bars = _sort_bars(normalized_bars)

    for bar in sorted_bars:
        instrument_id = str(bar["instrument_id"])
        bar_key = _bar_key(bar)
        positions_opened_this_bar: set[str] = set()
        account, policy_fills = _apply_stop_target_exits(
            account,
            bar,
            active_config,
            active_run_id,
            skip_instruments=positions_opened_this_bar,
        )
        fills.extend(policy_fills)
        for fill in policy_fills:
            closed_account, closed = _close_position_from_fill(account, fill)
            account = closed_account
            trades.append(
                trade_from_closed_position(
                    closed,
                    run_id=active_run_id,
                    sequence=len(trades) + 1,
                    quality_flags=_quality_flags_for_bar(bar),
                )
            )

        for signal in signals_by_fill_bar.get(bar_key, ()):
            account, produced_fill, produced_trade = _apply_signal_fill(
                account=account,
                signal=signal,
                bar=bar,
                config=active_config,
                run_id=active_run_id,
                strategy_id=active_strategy_id,
                strategy_version=active_strategy_version,
                data_version=active_data_version,
                factor_versions=active_factor_versions,
                trade_sequence=len(trades) + 1,
            )
            if produced_fill is not None:
                fills.append(produced_fill)
                if produced_fill.reason is FillReason.ENTRY_SIGNAL:
                    positions_opened_this_bar.add(produced_fill.instrument_id)
            if produced_trade is not None:
                trades.append(produced_trade)

        account, same_bar_policy_fills = _apply_stop_target_exits(
            account,
            bar,
            active_config,
            active_run_id,
            skip_instruments=(),
        )
        fills.extend(same_bar_policy_fills)
        for fill in same_bar_policy_fills:
            closed_account, closed = _close_position_from_fill(account, fill)
            account = closed_account
            trades.append(
                trade_from_closed_position(
                    closed,
                    run_id=active_run_id,
                    sequence=len(trades) + 1,
                    quality_flags=_quality_flags_for_bar(bar),
                )
            )

        if active_config.eod_flat and _is_last_session_bar(bar, sorted_bars):
            account, eod_fills = _apply_eod_flat_exits(
                account,
                bar,
                active_config,
                active_run_id,
            )
            fills.extend(eod_fills)
            for fill in eod_fills:
                closed_account, closed = _close_position_from_fill(account, fill)
                account = closed_account
                trades.append(
                    trade_from_closed_position(
                        closed,
                        run_id=active_run_id,
                        sequence=len(trades) + 1,
                        quality_flags=_quality_flags_for_bar(bar),
                    )
                )

        marks[instrument_id] = _decimal(bar["close"])
        equity_curve.append(
            equity_point_for_bar(
                run_id=active_run_id,
                bar=bar,
                account=account,
                marks=marks,
            )
        )

    if account.open_positions:
        warnings.append("open positions remain because eod_flat is disabled or no eligible exit occurred")

    summary = _summary(
        run_id=active_run_id,
        engine_version=active_config.engine_version,
        strategy_id=active_strategy_id,
        strategy_version=active_strategy_version,
        data_version=active_data_version,
        trades=tuple(trades),
        equity_curve=tuple(equity_curve),
        open_positions=len(account.open_positions),
        warnings=tuple(warnings),
    )
    empty_result = ReferenceBacktestResult(
        summary=summary,
        trades=tuple(trades),
        equity_curve=tuple(equity_curve),
        fills=tuple(fills),
        manifest={},
    )
    manifest = manifest_payload(
        empty_result,
        config_hash=config_hash,
        config_payload=config_payload,
        artifact_paths={},
    )
    result = replace(empty_result, manifest=manifest)
    output_paths = None
    if write_outputs or output_dir is not None or run_manifest_path is not None:
        output_paths = write_backtest_outputs(
            result,
            output_dir=output_dir,
            manifest_path=run_manifest_path,
            config_hash=config_hash,
            config_payload=config_payload,
        )
        manifest = manifest_payload(
            result,
            config_hash=config_hash,
            config_payload=config_payload,
            artifact_paths={
                "trades": output_paths.trades_path,
                "equity": output_paths.equity_path,
                "summary": output_paths.summary_path,
            },
        )
        result = replace(result, output_paths=output_paths, manifest=manifest)

    registry_written = False
    active_registry_path = None
    if registry_path is not None:
        active_registry_path = _record_backtest_run(
            registry_path,
            result,
            config_hash=config_hash,
            config_payload=config_payload,
            factor_versions=active_factor_versions,
            repo_root=repo_root,
        )
        registry_written = True

    return replace(
        result,
        registry_path=None if active_registry_path is None else active_registry_path.as_posix(),
        registry_written=registry_written,
    )


def _apply_signal_fill(
    *,
    account: AccountState,
    signal: SignalRecord,
    bar: Mapping[str, Any],
    config: ReferenceEngineConfig,
    run_id: str,
    strategy_id: str,
    strategy_version: str,
    data_version: str,
    factor_versions: Mapping[str, str],
    trade_sequence: int,
) -> tuple[AccountState, ReferenceFill | None, TradeRecord | None]:
    instrument_id = signal.instrument_id
    if signal.signal_type is SignalType.ENTRY:
        if instrument_id in account.open_positions:
            return account, None, None
        order = _order_from_signal(
            signal,
            run_id=run_id,
            bar=bar,
            intent=OrderIntent.ENTRY,
            quantity=config.default_quantity,
        )
        fill = resolve_entry_fill(order, bar, config)
        return (
            account.open_position(
                fill,
                strategy_id=strategy_id,
                strategy_version=strategy_version,
                data_version=data_version,
                factor_versions=factor_versions,
            ),
            fill,
            None,
        )

    if signal.signal_type is SignalType.EXIT:
        position = account.open_positions.get(instrument_id)
        if position is None:
            return account, None, None
        order = _order_from_signal(
            signal,
            run_id=run_id,
            bar=bar,
            intent=OrderIntent.EXIT,
            quantity=position.quantity,
            direction=position.direction,
        )
        fill = resolve_exit_signal_fill(order, bar, config)
        account, closed = account.close_position(fill)
        return (
            account,
            fill,
            trade_from_closed_position(
                closed,
                run_id=run_id,
                sequence=trade_sequence,
                quality_flags=_quality_flags_for_bar(bar),
            ),
        )
    return account, None, None


def _apply_stop_target_exits(
    account: AccountState,
    bar: Mapping[str, Any],
    config: ReferenceEngineConfig,
    run_id: str,
    *,
    skip_instruments: Iterable[str],
) -> tuple[AccountState, tuple[ReferenceFill, ...]]:
    fills: list[ReferenceFill] = []
    skip = set(skip_instruments)
    instrument_id = str(bar["instrument_id"])
    position = account.open_positions.get(instrument_id)
    if position is None or instrument_id in skip:
        return account, ()
    resolution = resolve_stop_target(
        direction=position.direction,
        entry_price=position.entry_price,
        bar=bar,
        stop_loss_pct=config.stop_loss_pct,
        target_profit_pct=config.target_profit_pct,
    )
    if resolution is None:
        return account, ()
    order = _policy_order(
        position,
        run_id=run_id,
        bar=bar,
        intent=resolution.intent,
    )
    fill = resolve_policy_exit_fill(
        order,
        bar,
        config,
        price=resolution.price,
        reason=resolution.reason,
    )
    fills.append(fill)
    return account, tuple(fills)


def _apply_eod_flat_exits(
    account: AccountState,
    bar: Mapping[str, Any],
    config: ReferenceEngineConfig,
    run_id: str,
) -> tuple[AccountState, tuple[ReferenceFill, ...]]:
    fills: list[ReferenceFill] = []
    position = account.open_positions.get(str(bar["instrument_id"]))
    if position is None:
        return account, ()
    order = _policy_order(position, run_id=run_id, bar=bar, intent=OrderIntent.EOD_FLAT)
    fills.append(
        resolve_policy_exit_fill(
            order,
            bar,
            config,
            price=eod_exit_price(position.direction, bar),
            reason=FillReason.EOD_FLAT,
        )
    )
    return account, tuple(fills)


def _close_position_from_fill(
    account: AccountState,
    fill: ReferenceFill,
):
    return account.close_position(fill)


def _normalize_bars(bars: Iterable[Mapping[str, Any]]) -> tuple[dict[str, Any], ...]:
    return normalize_bar_rows(bars)


def _normalize_signals(
    signals: Iterable[SignalRecord | Mapping[str, Any]],
) -> tuple[SignalRecord, ...]:
    return tuple(signal if isinstance(signal, SignalRecord) else SignalRecord.from_mapping(signal) for signal in signals)


def _assert_bars_match_data_version(bars: tuple[Mapping[str, Any], ...], data_version: str) -> None:
    mismatched = tuple(bar for bar in bars if str(bar["data_version"]) != data_version)
    if mismatched:
        msg = "all bars must match the requested data_version"
        raise ReferenceBacktestError(msg)


def _assert_bar_latency(
    bars: tuple[Mapping[str, Any], ...],
    config: ReferenceEngineConfig,
) -> None:
    latency = timedelta(seconds=config.data_latency_seconds)
    for bar in bars:
        required_available_ts = _datetime(bar["bar_end_ts"]) + latency
        if _datetime(bar["available_ts"]) < required_available_ts:
            msg = (
                "bar available_ts is earlier than bar_end_ts plus configured "
                f"latency for {bar['instrument_id']} {bar['session_id']} "
                f"bar_index={bar['bar_index']}"
            )
            raise BacktestTimingError(msg)


def _assert_signals_safe(
    signals: tuple[SignalRecord, ...],
    bars: tuple[Mapping[str, Any], ...],
    data_version: str,
) -> None:
    bars_by_key = {_bar_origin_key(bar): bar for bar in bars}
    for signal in signals:
        if signal.data_version and signal.data_version != data_version:
            msg = "signal data_version must match backtest data_version"
            raise ReferenceBacktestError(msg)
        origin = bars_by_key.get((signal.instrument_id, signal.session_id, signal.bar_index))
        if origin is None:
            msg = (
                "signal origin bar not found for "
                f"{signal.instrument_id} {signal.session_id} bar_index={signal.bar_index}"
            )
            raise BacktestTimingError(msg)
        if signal.available_ts < _datetime(origin["available_ts"]):
            msg = "signal available_ts must be at or after origin bar available_ts"
            raise BacktestTimingError(msg)


def _signals_by_fill_bar(
    signals: tuple[SignalRecord, ...],
    bars: tuple[Mapping[str, Any], ...],
    config: ReferenceEngineConfig,
) -> dict[tuple[str, str, int], tuple[SignalRecord, ...]]:
    bars_by_instrument_session: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for bar in _sort_bars(bars):
        bars_by_instrument_session[(str(bar["instrument_id"]), str(bar["session_id"]))].append(bar)

    scheduled: dict[tuple[str, str, int], list[SignalRecord]] = defaultdict(list)
    for signal in sorted(signals, key=lambda item: (item.available_ts, item.signal_id)):
        eligible = _eligible_fill_bar(
            signal,
            bars_by_instrument_session[(signal.instrument_id, signal.session_id)],
            config,
        )
        if eligible is not None:
            scheduled[_bar_key(eligible)].append(signal)
    return {key: tuple(value) for key, value in scheduled.items()}


def _eligible_fill_bar(
    signal: SignalRecord,
    bars: list[Mapping[str, Any]],
    config: ReferenceEngineConfig,
) -> Mapping[str, Any] | None:
    for bar in bars:
        if int(bar["bar_index"]) <= signal.bar_index:
            continue
        if _datetime(bar["bar_start_ts"]) < signal.available_ts:
            continue
        if _datetime(bar["available_ts"]) < _datetime(bar["bar_end_ts"]) + timedelta(seconds=config.data_latency_seconds):
            continue
        return bar
    return None


def _order_from_signal(
    signal: SignalRecord,
    *,
    run_id: str,
    bar: Mapping[str, Any],
    intent: OrderIntent,
    quantity: Decimal,
    direction: Direction | None = None,
) -> ReferenceOrder:
    active_direction = direction or signal.direction
    return ReferenceOrder(
        order_id=order_id_for(
            run_id=run_id,
            signal_id=signal.signal_id,
            instrument_id=signal.instrument_id,
            session_id=signal.session_id,
            bar_index=int(bar["bar_index"]),
            intent=intent,
        ),
        signal_id=signal.signal_id,
        instrument_id=signal.instrument_id,
        session_id=signal.session_id,
        origin_bar_index=signal.bar_index,
        earliest_bar_index=signal.bar_index + 1,
        available_ts=signal.available_ts,
        intent=intent,
        direction=active_direction,
        quantity=quantity,
    )


def _policy_order(
    position: Position,
    *,
    run_id: str,
    bar: Mapping[str, Any],
    intent: OrderIntent,
) -> ReferenceOrder:
    return ReferenceOrder(
        order_id=order_id_for(
            run_id=run_id,
            signal_id=None,
            instrument_id=position.instrument_id,
            session_id=position.session_id,
            bar_index=int(bar["bar_index"]),
            intent=intent,
        ),
        signal_id=None,
        instrument_id=position.instrument_id,
        session_id=position.session_id,
        origin_bar_index=int(bar["bar_index"]),
        earliest_bar_index=int(bar["bar_index"]),
        available_ts=_datetime(bar["bar_start_ts"]),
        intent=intent,
        direction=position.direction,
        quantity=position.quantity,
    )


def _summary(
    *,
    run_id: str,
    engine_version: str,
    strategy_id: str,
    strategy_version: str,
    data_version: str,
    trades: tuple[TradeRecord, ...],
    equity_curve: tuple[Any, ...],
    open_positions: int,
    warnings: tuple[str, ...],
) -> BacktestSummary:
    gross_pnl = sum((trade.gross_pnl for trade in trades), Decimal("0"))
    costs = sum((trade.costs for trade in trades), Decimal("0"))
    net_pnl = sum((trade.net_pnl for trade in trades), Decimal("0"))
    final_equity = equity_curve[-1].total_equity if equity_curve else Decimal("0")
    return BacktestSummary(
        run_id=run_id,
        engine_version=engine_version,
        strategy_id=strategy_id,
        strategy_version=strategy_version,
        data_version=data_version,
        total_trades=len(trades),
        open_positions=open_positions,
        gross_pnl=gross_pnl,
        costs=costs,
        net_pnl=net_pnl,
        final_equity=final_equity,
        warnings=warnings,
    )


def _record_backtest_run(
    registry_path: str | Path,
    result: ReferenceBacktestResult,
    *,
    config_hash: str,
    config_payload: Mapping[str, Any],
    factor_versions: Mapping[str, str],
    repo_root: str | Path | None,
) -> Path:
    registry = assert_registry_path_allowed(
        registry_path,
        repo_root=repo_root or Path.cwd(),
    )
    status = init_registry(registry)
    if not status.valid:
        msg = f"registry is not valid: {status.status_message}"
        raise ReferenceBacktestError(msg)
    git_info = capture_git_info(Path.cwd())
    code_hash = hash_config(
        {
            "engine": "alpha_system.backtest.reference",
            "engine_version": result.summary.engine_version,
        }
    )
    artifact_paths = {} if result.output_paths is None else result.output_paths.to_dict()
    record = RunRecord(
        run_id=result.summary.run_id,
        timestamp=datetime.now(timezone.utc),
        git_commit=git_info.commit,
        git_dirty=git_info.dirty,
        code_hash=code_hash,
        config_hash=config_hash,
        data_version=result.summary.data_version,
        factor_versions=dict(factor_versions),
        label_versions={},
        engine_version=result.summary.engine_version,
        parameters=config_payload,
        artifact_paths=artifact_paths,
        decision_status="reference_recorded",
        warnings=result.summary.warnings,
        status_message="Tier 1 reference backtest run recorded in local registry.",
    )
    with connect_registry(registry) as connection:
        insert_run_record(connection, "backtest_runs", record)
    return registry


def _sort_bars(bars: Iterable[Mapping[str, Any]]) -> tuple[Mapping[str, Any], ...]:
    return tuple(
        sorted(
            bars,
            key=lambda bar: (
                _datetime(bar["bar_start_ts"]),
                str(bar["instrument_id"]),
                str(bar["session_id"]),
                int(bar["bar_index"]),
            ),
        )
    )


def _is_last_session_bar(bar: Mapping[str, Any], bars: tuple[Mapping[str, Any], ...]) -> bool:
    for candidate in bars:
        if str(candidate["instrument_id"]) != str(bar["instrument_id"]):
            continue
        if str(candidate["session_id"]) != str(bar["session_id"]):
            continue
        if int(candidate["bar_index"]) > int(bar["bar_index"]):
            return False
    return True


def _single_signal_field(signals: tuple[SignalRecord, ...], field_name: str) -> str:
    values = {str(getattr(signal, field_name)) for signal in signals}
    if len(values) != 1:
        msg = f"signals must contain exactly one {field_name}"
        raise ReferenceBacktestError(msg)
    return next(iter(values))


def _factor_versions_from_signals(signals: tuple[SignalRecord, ...]) -> Mapping[str, str]:
    versions: dict[str, str] = {}
    for signal in signals:
        for factor_id, factor_version in signal.factor_versions.items():
            existing = versions.get(factor_id)
            if existing is not None and existing != factor_version:
                msg = f"conflicting factor version for {factor_id}"
                raise ReferenceBacktestError(msg)
            versions[factor_id] = factor_version
    return versions


def _bar_key(bar: Mapping[str, Any]) -> tuple[str, str, int]:
    return (str(bar["instrument_id"]), str(bar["session_id"]), int(bar["bar_index"]))


def _bar_origin_key(bar: Mapping[str, Any]) -> tuple[str, str, int]:
    return _bar_key(bar)


def _quality_flags_for_bar(bar: Mapping[str, Any]) -> tuple[str, ...]:
    value = bar.get("quality_flags", ())
    if isinstance(value, tuple):
        return tuple(str(item) for item in value)
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    if value is None:
        return ()
    return (str(value),)


def _datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        active = value
    else:
        active = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if active.tzinfo is None:
        active = active.replace(tzinfo=timezone.utc)
    return active.astimezone(timezone.utc)


def _decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))
