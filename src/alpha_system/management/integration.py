"""Management adapter for the reference 1-minute backtest engine."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import replace
from decimal import Decimal
from typing import Any

from alpha_system.backtest.accounting import AccountState, Position
from alpha_system.backtest.engine_config import ReferenceEngineConfig
from alpha_system.backtest.equity import equity_point_for_bar
from alpha_system.backtest.fills import (
    FillReason,
    ReferenceFill,
    resolve_entry_fill,
    resolve_exit_signal_fill,
    resolve_policy_exit_fill,
)
from alpha_system.backtest.instrument_economics import resolve_instrument_multipliers
from alpha_system.backtest.orders import OrderIntent, ReferenceOrder, order_id_for
from alpha_system.backtest.reference import (
    ReferenceBacktestError,
    _assert_bar_latency,
    _assert_bars_match_data_version,
    _assert_signals_safe,
    _bar_key,
    _datetime,
    _factor_versions_from_signals,
    _is_last_session_bar,
    _last_bar_index_by_session,
    _multiplier_for,
    _normalize_bars,
    _normalize_signals,
    _order_from_signal,
    _quality_flags_for_bar,
    _signals_by_fill_bar,
    _single_signal_field,
    _sort_bars,
    _summary,
)
from alpha_system.backtest.results import ReferenceBacktestResult, manifest_payload
from alpha_system.backtest.trades import TradeRecord, trade_from_closed_position
from alpha_system.core.hashing import hash_config
from alpha_system.management.partials import PartialExitDecision, account_partial_exit
from alpha_system.management.rules import ManagementExitDecision, evaluate_management_bar
from alpha_system.management.spec import ManagementSpec
from alpha_system.management.state import ManagedPositionState, ManagementRuntimeState
from alpha_system.management.stops import initial_stop_price
from alpha_system.management.trailing import update_protective_stop_for_next_bar
from alpha_system.signals.spec import SignalRecord, SignalType


def run_reference_backtest_with_management(
    *,
    bars: Iterable[Mapping[str, Any]],
    signals: Iterable[SignalRecord | Mapping[str, Any]],
    management_spec: ManagementSpec | Mapping[str, Any] | None = None,
    config: ReferenceEngineConfig | None = None,
    strategy_id: str | None = None,
    strategy_version: str | None = None,
    data_version: str | None = None,
    factor_versions: Mapping[str, str] | None = None,
    initial_cash: Decimal = Decimal("100000"),
    instrument_multipliers: Mapping[str, Any] | None = None,
    instrument_roots: Mapping[str, str] | None = None,
    run_id: str = "managed-reference",
) -> ReferenceBacktestResult:
    """Run the reference engine path with deterministic management rules.

    This adapter reuses reference fills, trade journal containers, cost model,
    signal scheduling, and equity accounting. It does not write management study
    outputs and does not introduce broker or order-router behavior.
    """
    active_config = config or ReferenceEngineConfig()
    active_management = (
        management_spec
        if isinstance(management_spec, ManagementSpec)
        else ManagementSpec.from_mapping(management_spec)
    )
    normalized_bars = _normalize_bars(bars)
    normalized_signals = _normalize_signals(signals)
    if not normalized_bars:
        raise ReferenceBacktestError("managed reference backtest requires at least one bar")
    if not normalized_signals:
        raise ReferenceBacktestError("managed reference backtest requires at least one signal")
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
        "management_spec": active_management.to_dict(),
    }
    config_hash = hash_config(config_payload)
    signals_by_fill_bar = _signals_by_fill_bar(normalized_signals, normalized_bars, active_config)
    instrument_ids = tuple({str(bar["instrument_id"]) for bar in normalized_bars})
    multiplier_map = resolve_instrument_multipliers(
        instrument_ids,
        multipliers=instrument_multipliers,
        roots=instrument_roots,
    )
    fee_symbols = {
        symbol_instrument_id: str((instrument_roots or {}).get(symbol_instrument_id, symbol_instrument_id))
        for symbol_instrument_id in instrument_ids
    }
    account = AccountState(initial_cash=initial_cash, instrument_multipliers=multiplier_map)
    runtime = ManagementRuntimeState()
    managed_positions: dict[str, ManagedPositionState] = {}
    trades: list[TradeRecord] = []
    fills: list[ReferenceFill] = []
    equity_curve = []
    warnings: list[str] = []
    marks: dict[str, Decimal] = {}
    sorted_bars = _sort_bars(normalized_bars)
    last_bar_index_by_session = _last_bar_index_by_session(sorted_bars)

    for bar in sorted_bars:
        instrument_id = str(bar["instrument_id"])
        session_id = str(bar["session_id"])
        bar_index = int(bar["bar_index"])
        runtime = runtime.for_session(session_id, session_reset=active_management.session_reset)

        account, runtime = _apply_management_for_bar(
            account=account,
            runtime=runtime,
            managed_positions=managed_positions,
            bar=bar,
            config=active_config,
            management_spec=active_management,
            run_id=run_id,
            trades=trades,
            fills=fills,
            last_bar_index_by_session=last_bar_index_by_session,
            symbol=fee_symbols.get(instrument_id),
        )

        for signal in signals_by_fill_bar.get(_bar_key(bar), ()):
            if signal.signal_type is SignalType.ENTRY:
                if instrument_id in account.open_positions:
                    continue
                max_trades = (
                    active_management.max_trades_per_day.limit
                    if active_management.max_trades_per_day.enabled
                    else None
                )
                if not runtime.can_enter(
                    session_id=session_id,
                    bar_index=bar_index,
                    max_trades_per_day=max_trades,
                ):
                    continue
                order = _order_from_signal(
                    signal,
                    run_id=run_id,
                    bar=bar,
                    intent=OrderIntent.ENTRY,
                    quantity=active_config.default_quantity,
                )
                fill = resolve_entry_fill(
                    order,
                    bar,
                    active_config,
                    multiplier=_multiplier_for(multiplier_map, instrument_id),
                    symbol=fee_symbols.get(instrument_id),
                )
                account = account.open_position(
                    fill,
                    strategy_id=active_strategy_id,
                    strategy_version=active_strategy_version,
                    data_version=active_data_version,
                    factor_versions=active_factor_versions,
                )
                fills.append(fill)
                runtime = runtime.record_entry(session_id=session_id)
                position = account.open_positions[instrument_id]
                managed_positions[instrument_id] = ManagedPositionState.from_position(
                    position,
                    initial_stop_price=initial_stop_price(
                        position.direction,
                        position.entry_price,
                        active_management,
                        bar,
                    ),
                )
                account, runtime = _apply_management_for_bar(
                    account=account,
                    runtime=runtime,
                    managed_positions=managed_positions,
                    bar=bar,
                    config=active_config,
                    management_spec=active_management,
                    run_id=run_id,
                    trades=trades,
                    fills=fills,
                    last_bar_index_by_session=last_bar_index_by_session,
                )
                continue
            if signal.signal_type is SignalType.EXIT:
                position = account.open_positions.get(instrument_id)
                if position is None:
                    continue
                order = _order_from_signal(
                    signal,
                    run_id=run_id,
                    bar=bar,
                    intent=OrderIntent.EXIT,
                    quantity=position.quantity,
                    direction=position.direction,
                )
                fill = resolve_exit_signal_fill(
                    order,
                    bar,
                    active_config,
                    multiplier=_multiplier_for(multiplier_map, instrument_id),
                    symbol=fee_symbols.get(instrument_id),
                )
                account, closed = account.close_position(fill)
                fills.append(fill)
                trades.append(
                    trade_from_closed_position(
                        closed,
                        run_id=run_id,
                        sequence=len(trades) + 1,
                        quality_flags=_quality_flags_for_bar(bar),
                    )
                )
                managed_positions.pop(instrument_id, None)
                cooldown = active_management.cooldown.bars if active_management.cooldown.enabled else None
                runtime = runtime.record_exit(
                    session_id=session_id,
                    exit_bar_index=bar_index,
                    cooldown_bars=cooldown,
                )

        marks[instrument_id] = _decimal(bar["close"])
        equity_curve.append(
            equity_point_for_bar(
                run_id=run_id,
                bar=bar,
                account=account,
                marks=marks,
            )
        )

    if account.open_positions:
        warnings.append("open positions remain because management did not close every position")

    summary = _summary(
        run_id=run_id,
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
    return replace(empty_result, manifest=manifest)


def _apply_management_for_bar(
    *,
    account: AccountState,
    runtime: ManagementRuntimeState,
    managed_positions: dict[str, ManagedPositionState],
    bar: Mapping[str, Any],
    config: ReferenceEngineConfig,
    management_spec: ManagementSpec,
    run_id: str,
    trades: list[TradeRecord],
    fills: list[ReferenceFill],
    last_bar_index_by_session: Mapping[tuple[str, str], int],
    symbol: str | None = None,
) -> tuple[AccountState, ManagementRuntimeState]:
    instrument_id = str(bar["instrument_id"])
    state = managed_positions.get(instrument_id)
    if state is None:
        return account, runtime
    decision = evaluate_management_bar(
        state,
        bar,
        management_spec,
        is_last_session_bar=_is_last_session_bar(bar, last_bar_index_by_session),
    )
    if decision.full_exit is not None:
        account, runtime = _apply_full_exit(
            account=account,
            runtime=runtime,
            managed_positions=managed_positions,
            state=state,
            decision=decision.full_exit,
            bar=bar,
            config=config,
            management_spec=management_spec,
            run_id=run_id,
            trades=trades,
            fills=fills,
            symbol=symbol,
        )
        return account, runtime
    for partial in decision.partial_exits:
        state = managed_positions[instrument_id]
        account, state = _apply_partial_exit(
            account=account,
            state=state,
            partial=partial,
            bar=bar,
            config=config,
            run_id=run_id,
            trades=trades,
            fills=fills,
            symbol=symbol,
        )
        if state.remaining_quantity <= 0:
            managed_positions.pop(instrument_id, None)
            return account, runtime
        managed_positions[instrument_id] = state
    if instrument_id in managed_positions:
        managed_positions[instrument_id] = update_protective_stop_for_next_bar(
            managed_positions[instrument_id],
            breakeven=management_spec.breakeven_stop,
            trailing=management_spec.trailing_stop,
            bar=bar,
        )
    return account, runtime


def _apply_full_exit(
    *,
    account: AccountState,
    runtime: ManagementRuntimeState,
    managed_positions: dict[str, ManagedPositionState],
    state: ManagedPositionState,
    decision: ManagementExitDecision,
    bar: Mapping[str, Any],
    config: ReferenceEngineConfig,
    management_spec: ManagementSpec,
    run_id: str,
    trades: list[TradeRecord],
    fills: list[ReferenceFill],
    symbol: str | None = None,
) -> tuple[AccountState, ManagementRuntimeState]:
    position = account.open_positions.get(state.instrument_id)
    if position is None:
        managed_positions.pop(state.instrument_id, None)
        return account, runtime
    reason = _fill_reason(decision.reason)
    order = _management_order(
        position,
        run_id=run_id,
        bar=bar,
        reason=decision.reason,
        quantity=position.quantity,
    )
    fill = resolve_policy_exit_fill(
        order,
        bar,
        config,
        price=decision.price,
        reason=reason,
        multiplier=position.multiplier,
        symbol=symbol,
    )
    account, closed = account.close_position(fill)
    fills.append(fill)
    trade = trade_from_closed_position(
        closed,
        run_id=run_id,
        sequence=len(trades) + 1,
        quality_flags=_quality_flags_for_bar(bar),
    )
    if decision.reason not in {"stop_loss", "take_profit", "eod_flat"}:
        trade = replace(trade, exit_reason=decision.reason)
    if decision.reason == "eod_exit":
        trade = replace(trade, exit_reason="eod_exit")
    if decision.ambiguous_same_bar:
        trade = replace(
            trade,
            quality_flags=tuple((*trade.quality_flags, "same_bar_adverse_first")),
        )
    trades.append(trade)
    managed_positions.pop(state.instrument_id, None)
    cooldown = management_spec.cooldown.bars if management_spec.cooldown.enabled else None
    runtime = runtime.record_exit(
        session_id=state.session_id,
        exit_bar_index=int(bar["bar_index"]),
        cooldown_bars=cooldown,
    )
    return account, runtime


def _apply_partial_exit(
    *,
    account: AccountState,
    state: ManagedPositionState,
    partial: PartialExitDecision,
    bar: Mapping[str, Any],
    config: ReferenceEngineConfig,
    run_id: str,
    trades: list[TradeRecord],
    fills: list[ReferenceFill],
    symbol: str | None = None,
) -> tuple[AccountState, ManagedPositionState]:
    position = account.open_positions[state.instrument_id]
    order = _management_order(
        position,
        run_id=run_id,
        bar=bar,
        reason=f"partial_take_profit_{partial.step.label}",
        quantity=partial.quantity,
    )
    fill = resolve_policy_exit_fill(
        order,
        bar,
        config,
        price=partial.price,
        reason=FillReason.TAKE_PROFIT,
        multiplier=position.multiplier,
        symbol=symbol,
    )
    accounting = account_partial_exit(
        direction=state.direction,
        entry_price=state.entry_price,
        exit_price=partial.price,
        exit_quantity=partial.quantity,
        current_quantity=position.quantity,
        current_entry_cost=position.entry_cost,
        exit_cost=fill.cost,
        multiplier=position.multiplier,
    )
    positions = dict(account.open_positions)
    if accounting.remaining_quantity > 0:
        positions[state.instrument_id] = replace(
            position,
            quantity=accounting.remaining_quantity,
            entry_cost=accounting.remaining_entry_cost,
        )
    else:
        positions.pop(state.instrument_id, None)
    account = replace(
        account,
        realized_pnl=account.realized_pnl + accounting.net_pnl,
        positions=positions,
    )
    fills.append(fill)
    trades.append(
        TradeRecord(
            trade_id=f"{run_id}:trade:{len(trades) + 1:06d}",
            run_id=run_id,
            instrument_id=state.instrument_id,
            session_id=state.session_id,
            strategy_id=state.strategy_id,
            strategy_version=state.strategy_version,
            direction=state.direction.value,
            quantity=partial.quantity,
            entry_signal_id=state.entry_signal_id,
            exit_signal_id=None,
            entry_order_id=state.entry_order_id,
            exit_order_id=fill.order_id,
            entry_ts=state.entry_ts,
            exit_ts=fill.fill_ts,
            entry_bar_index=state.entry_bar_index,
            exit_bar_index=fill.bar_index,
            entry_price=state.entry_price,
            exit_price=partial.price,
            gross_pnl=accounting.gross_pnl,
            costs=accounting.allocated_entry_cost + fill.cost,
            net_pnl=accounting.net_pnl,
            exit_reason=f"partial_take_profit:{partial.step.label}",
            data_version=state.data_version,
            factor_versions=dict(state.factor_versions),
            quality_flags=tuple((*_quality_flags_for_bar(bar), "partial_exit")),
        )
    )
    updated_state = state.with_quantity(
        remaining_quantity=accounting.remaining_quantity,
        entry_cost_remaining=accounting.remaining_entry_cost,
    ).with_partial_label(partial.step.label)
    return account, updated_state


def _management_order(
    position: Position,
    *,
    run_id: str,
    bar: Mapping[str, Any],
    reason: str,
    quantity: Decimal,
) -> ReferenceOrder:
    base_order_id = order_id_for(
        run_id=run_id,
        signal_id=None,
        instrument_id=position.instrument_id,
        session_id=position.session_id,
        bar_index=int(bar["bar_index"]),
        intent=_order_intent(reason),
    )
    return ReferenceOrder(
        order_id=f"{base_order_id}:{reason}",
        signal_id=None,
        instrument_id=position.instrument_id,
        session_id=position.session_id,
        origin_bar_index=int(bar["bar_index"]),
        earliest_bar_index=int(bar["bar_index"]),
        available_ts=_datetime(bar["bar_start_ts"]),
        intent=_order_intent(reason),
        direction=position.direction,
        quantity=quantity,
    )


def _order_intent(reason: str) -> OrderIntent:
    if reason == "stop_loss":
        return OrderIntent.STOP_LOSS
    if reason in {"take_profit"} or reason.startswith("partial_take_profit"):
        return OrderIntent.TAKE_PROFIT
    if reason in {"eod_exit", "eod_flat"}:
        return OrderIntent.EOD_FLAT
    return OrderIntent.EXIT


def _fill_reason(reason: str) -> FillReason:
    if reason == "stop_loss":
        return FillReason.STOP_LOSS
    if reason == "take_profit":
        return FillReason.TAKE_PROFIT
    if reason in {"eod_exit", "eod_flat"}:
        return FillReason.EOD_FLAT
    return FillReason.EXIT_SIGNAL


def _decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))
