"""Acceleration-only fast path for scoped reference backtest parity."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

from alpha_system.backtest.accounting import AccountState
from alpha_system.backtest.fast_arrays import (
    FastArrayBackend,
    build_bar_arrays,
    resolve_stop_target_event,
)
from alpha_system.backtest.fills import (
    FillReason,
    ReferenceFill,
    eod_exit_price,
    resolve_entry_fill,
    resolve_exit_signal_fill,
    resolve_policy_exit_fill,
)
from alpha_system.backtest.instrument_economics import resolve_instrument_multipliers
from alpha_system.backtest.orders import OrderIntent
from alpha_system.backtest.reference import (
    BacktestTimingError,
    ReferenceBacktestError,
    _assert_bar_latency,
    _assert_bars_match_data_version,
    _assert_signals_safe,
    _bar_key,
    _factor_versions_from_signals,
    _is_last_session_bar,
    _multiplier_for,
    _normalize_bars,
    _normalize_signals,
    _order_from_signal,
    _policy_order,
    _quality_flags_for_bar,
    _signals_by_fill_bar,
    _single_signal_field,
    _sort_bars,
    _summary,
    run_reference_backtest,
)
from alpha_system.backtest.results import ReferenceBacktestResult, manifest_payload
from alpha_system.backtest.trades import TradeRecord, trade_from_closed_position
from alpha_system.core.hashing import hash_config
from alpha_system.core.run_ids import generate_run_id
from alpha_system.management.integration import run_reference_backtest_with_management
from alpha_system.management.spec import ManagementSpec
from alpha_system.signals.spec import SignalRecord, SignalType


FAST_PATH_VERSION = "fast_path_v1"
FAST_PATH_MODE_ACCELERATED = "accelerated"
FAST_PATH_MODE_REFERENCE_FALLBACK = "reference_fallback"

ACCELERATED_FEATURES = frozenset(
    {
        "no_trade",
        "simple_long",
        "simple_short",
        "costs",
        "fixed_stop",
        "target",
        "same_bar_ambiguity",
        "eod_exit",
        "trade_summary",
        "equity_curve",
    }
)
REFERENCE_FALLBACK_FEATURES = frozenset(
    {
        "slippage",
        "partial_exit",
        "cooldown",
        "max_holding_bars",
        "management_fixed_stop",
        "management_target",
        "management_eod_exit",
        "time_exit",
        "trailing_stop",
        "breakeven_stop",
        "atr_stop",
        "volatility_stop",
        "scale_in",
        "scale_out",
        "max_trades_per_day",
        "risk_per_trade",
        "max_position_percent",
        "liquidity_policy",
        "portfolio_target",
        "multi_instrument",
    }
)
KNOWN_FAST_PATH_FEATURES = ACCELERATED_FEATURES | REFERENCE_FALLBACK_FEATURES


class FastPathError(ValueError):
    """Raised when fast-path execution cannot run safely."""


class UnsupportedFastPathFeatureError(FastPathError):
    """Raised when a feature is not accelerated and fallback is disabled."""

    def __init__(self, features: Iterable[str]) -> None:
        self.features = tuple(sorted(set(features)))
        super().__init__(f"unsupported fast-path features: {', '.join(self.features)}")


@dataclass(frozen=True, slots=True)
class FastPathRun:
    """Result wrapper for an acceleration-only fast path run."""

    result: ReferenceBacktestResult
    mode: str
    fast_path_version: str
    accelerated_features: tuple[str, ...]
    unsupported_features: tuple[str, ...]
    array_backend: FastArrayBackend | None

    @property
    def summary(self):
        return self.result.summary

    @property
    def trades(self):
        return self.result.trades

    @property
    def equity_curve(self):
        return self.result.equity_curve

    @property
    def fills(self):
        return self.result.fills


def run_fast_path_backtest(
    *,
    bars: Iterable[Mapping[str, Any]],
    signals: Iterable[SignalRecord | Mapping[str, Any]],
    config: Any | None = None,
    management_spec: ManagementSpec | Mapping[str, Any] | None = None,
    requested_features: Iterable[str] = (),
    strategy_id: str | None = None,
    strategy_version: str | None = None,
    data_version: str | None = None,
    factor_versions: Mapping[str, str] | None = None,
    initial_cash: Decimal = Decimal("100000"),
    instrument_multipliers: Mapping[str, Any] | None = None,
    instrument_roots: Mapping[str, str] | None = None,
    run_id: str | None = None,
    allow_reference_fallback: bool = True,
) -> FastPathRun:
    """Run the scoped fast path or route unsupported features to reference.

    The returned ``ReferenceBacktestResult`` uses the reference result schema.
    This function never writes trade, equity, benchmark, array, registry, or
    database artifacts.
    """

    active_config = config
    if active_config is None:
        from alpha_system.backtest.engine_config import ReferenceEngineConfig

        active_config = ReferenceEngineConfig()
    normalized_bars = _normalize_bars(bars)
    normalized_signals = _normalize_signals(signals)
    active_management = _management_spec(management_spec)
    requested = frozenset(str(feature) for feature in requested_features)
    unknown = requested.difference(KNOWN_FAST_PATH_FEATURES)
    if unknown:
        raise UnsupportedFastPathFeatureError(unknown)
    unsupported = _unsupported_features(
        bars=normalized_bars,
        signals=normalized_signals,
        config=active_config,
        management_spec=active_management,
        requested_features=requested,
    )
    if unsupported:
        if not allow_reference_fallback:
            raise UnsupportedFastPathFeatureError(unsupported)
        result = _run_reference_fallback(
            bars=normalized_bars,
            signals=normalized_signals,
            config=active_config,
            management_spec=active_management,
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            data_version=data_version,
            factor_versions=factor_versions,
            initial_cash=initial_cash,
            instrument_multipliers=instrument_multipliers,
            instrument_roots=instrument_roots,
            run_id=run_id,
        )
        return FastPathRun(
            result=result,
            mode=FAST_PATH_MODE_REFERENCE_FALLBACK,
            fast_path_version=FAST_PATH_VERSION,
            accelerated_features=(),
            unsupported_features=tuple(sorted(unsupported)),
            array_backend=None,
        )

    return _run_accelerated(
        bars=normalized_bars,
        signals=normalized_signals,
        config=active_config,
        requested_features=requested,
        strategy_id=strategy_id,
        strategy_version=strategy_version,
        data_version=data_version,
        factor_versions=factor_versions,
        initial_cash=initial_cash,
        instrument_multipliers=instrument_multipliers,
        instrument_roots=instrument_roots,
        run_id=run_id,
    )


def _run_accelerated(
    *,
    bars: tuple[Mapping[str, Any], ...],
    signals: tuple[SignalRecord, ...],
    config: Any,
    requested_features: frozenset[str],
    strategy_id: str | None,
    strategy_version: str | None,
    data_version: str | None,
    factor_versions: Mapping[str, str] | None,
    initial_cash: Decimal,
    instrument_multipliers: Mapping[str, Any] | None = None,
    instrument_roots: Mapping[str, str] | None = None,
    run_id: str | None,
) -> FastPathRun:
    if not bars:
        raise ReferenceBacktestError("reference backtest requires at least one bar")
    if not signals:
        raise ReferenceBacktestError("reference backtest requires at least one signal")

    active_data_version = data_version or str(bars[0]["data_version"])
    _assert_bars_match_data_version(bars, active_data_version)
    _assert_bar_latency(bars, config)
    _assert_signals_safe(signals, bars, active_data_version)
    active_strategy_id = strategy_id or _single_signal_field(signals, "strategy_id")
    active_strategy_version = strategy_version or _single_signal_field(signals, "strategy_version")
    active_factor_versions = dict(factor_versions or _factor_versions_from_signals(signals))
    config_payload = config.to_dict()
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

    signals_by_fill_bar = _signals_by_fill_bar(signals, bars, config)
    sorted_bars = _sort_bars(bars)
    arrays = build_bar_arrays(sorted_bars)
    instrument_ids = tuple({str(bar["instrument_id"]) for bar in bars})
    multiplier_map = resolve_instrument_multipliers(
        instrument_ids,
        multipliers=instrument_multipliers,
        roots=instrument_roots,
    )
    fee_symbols = {
        instrument_id: str((instrument_roots or {}).get(instrument_id, instrument_id))
        for instrument_id in instrument_ids
    }
    account = AccountState(initial_cash=initial_cash, instrument_multipliers=multiplier_map)
    trades: list[TradeRecord] = []
    fills: list[ReferenceFill] = []
    equity_curve = []
    warnings: list[str] = []
    marks: dict[str, Decimal] = {}

    for bar in arrays.bars:
        instrument_id = str(bar["instrument_id"])
        account = _close_policy_fills(
            account=account,
            fills=fills,
            trades=trades,
            policy_fills=_fast_stop_target_fills(
                account=account,
                bar=bar,
                config=config,
                run_id=active_run_id,
                skip_instruments=(),
                multipliers=multiplier_map,
                symbols=fee_symbols,
            ),
            run_id=active_run_id,
            bar=bar,
        )

        for signal in signals_by_fill_bar.get(_bar_key(bar), ()):
            account, produced_fill, produced_trade = _fast_signal_fill(
                account=account,
                signal=signal,
                bar=bar,
                config=config,
                run_id=active_run_id,
                strategy_id=active_strategy_id,
                strategy_version=active_strategy_version,
                data_version=active_data_version,
                factor_versions=active_factor_versions,
                trade_sequence=len(trades) + 1,
                multipliers=multiplier_map,
                symbols=fee_symbols,
            )
            if produced_fill is not None:
                fills.append(produced_fill)
            if produced_trade is not None:
                trades.append(produced_trade)

        account = _close_policy_fills(
            account=account,
            fills=fills,
            trades=trades,
            policy_fills=_fast_stop_target_fills(
                account=account,
                bar=bar,
                config=config,
                run_id=active_run_id,
                skip_instruments=(),
                multipliers=multiplier_map,
                symbols=fee_symbols,
            ),
            run_id=active_run_id,
            bar=bar,
        )

        if bool(getattr(config, "eod_flat", False)) and _is_last_session_bar(bar, sorted_bars):
            account = _close_policy_fills(
                account=account,
                fills=fills,
                trades=trades,
                policy_fills=_fast_eod_fills(
                    account=account,
                    bar=bar,
                    config=config,
                    run_id=active_run_id,
                    multipliers=multiplier_map,
                    symbols=fee_symbols,
                ),
                run_id=active_run_id,
                bar=bar,
            )

        marks[instrument_id] = _decimal(bar["close"])
        from alpha_system.backtest.equity import equity_point_for_bar

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
        engine_version=str(getattr(config, "engine_version")),
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
    return FastPathRun(
        result=result,
        mode=FAST_PATH_MODE_ACCELERATED,
        fast_path_version=FAST_PATH_VERSION,
        accelerated_features=tuple(sorted(requested_features.intersection(ACCELERATED_FEATURES))),
        unsupported_features=(),
        array_backend=arrays.backend,
    )


def _fast_signal_fill(
    *,
    account: AccountState,
    signal: SignalRecord,
    bar: Mapping[str, Any],
    config: Any,
    run_id: str,
    strategy_id: str,
    strategy_version: str,
    data_version: str,
    factor_versions: Mapping[str, str],
    trade_sequence: int,
    multipliers: Mapping[str, Decimal],
    symbols: Mapping[str, str],
) -> tuple[AccountState, ReferenceFill | None, TradeRecord | None]:
    instrument_id = signal.instrument_id
    if signal.signal_type is SignalType.HOLD:
        return account, None, None
    multiplier = _multiplier_for(multipliers, instrument_id)
    symbol = symbols.get(instrument_id)
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
        fill = resolve_entry_fill(order, bar, config, multiplier=multiplier, symbol=symbol)
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
        fill = resolve_exit_signal_fill(order, bar, config, multiplier=multiplier, symbol=symbol)
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


def _fast_stop_target_fills(
    *,
    account: AccountState,
    bar: Mapping[str, Any],
    config: Any,
    run_id: str,
    skip_instruments: Iterable[str],
    multipliers: Mapping[str, Decimal],
    symbols: Mapping[str, str],
) -> tuple[ReferenceFill, ...]:
    skip = set(skip_instruments)
    instrument_id = str(bar["instrument_id"])
    position = account.open_positions.get(instrument_id)
    if position is None or instrument_id in skip:
        return ()
    event = resolve_stop_target_event(
        direction=position.direction.value,
        entry_price=position.entry_price,
        high=_decimal(bar["high"]),
        low=_decimal(bar["low"]),
        stop_loss_pct=getattr(config, "stop_loss_pct", None),
        target_profit_pct=getattr(config, "target_profit_pct", None),
    )
    if event is None:
        return ()
    intent = OrderIntent.STOP_LOSS if event.reason == "stop_loss" else OrderIntent.TAKE_PROFIT
    reason = FillReason.STOP_LOSS if event.reason == "stop_loss" else FillReason.TAKE_PROFIT
    order = _policy_order(position, run_id=run_id, bar=bar, intent=intent)
    fill = resolve_policy_exit_fill(
        order,
        bar,
        config,
        price=event.price,
        reason=reason,
        multiplier=_multiplier_for(multipliers, instrument_id),
        symbol=symbols.get(instrument_id),
    )
    return (fill,)


def _fast_eod_fills(
    *,
    account: AccountState,
    bar: Mapping[str, Any],
    config: Any,
    run_id: str,
    multipliers: Mapping[str, Decimal],
    symbols: Mapping[str, str],
) -> tuple[ReferenceFill, ...]:
    instrument_id = str(bar["instrument_id"])
    position = account.open_positions.get(instrument_id)
    if position is None:
        return ()
    order = _policy_order(position, run_id=run_id, bar=bar, intent=OrderIntent.EOD_FLAT)
    fill = resolve_policy_exit_fill(
        order,
        bar,
        config,
        price=eod_exit_price(position.direction, bar),
        reason=FillReason.EOD_FLAT,
        multiplier=_multiplier_for(multipliers, instrument_id),
        symbol=symbols.get(instrument_id),
    )
    return (fill,)


def _close_policy_fills(
    *,
    account: AccountState,
    fills: list[ReferenceFill],
    trades: list[TradeRecord],
    policy_fills: tuple[ReferenceFill, ...],
    run_id: str,
    bar: Mapping[str, Any],
) -> AccountState:
    for fill in policy_fills:
        fills.append(fill)
        account, closed = account.close_position(fill)
        trades.append(
            trade_from_closed_position(
                closed,
                run_id=run_id,
                sequence=len(trades) + 1,
                quality_flags=_quality_flags_for_bar(bar),
            )
        )
    return account


def _run_reference_fallback(
    *,
    bars: tuple[Mapping[str, Any], ...],
    signals: tuple[SignalRecord, ...],
    config: Any,
    management_spec: ManagementSpec | None,
    strategy_id: str | None,
    strategy_version: str | None,
    data_version: str | None,
    factor_versions: Mapping[str, str] | None,
    initial_cash: Decimal,
    instrument_multipliers: Mapping[str, Any] | None = None,
    instrument_roots: Mapping[str, str] | None = None,
    run_id: str | None,
) -> ReferenceBacktestResult:
    if management_spec is not None:
        return run_reference_backtest_with_management(
            bars=bars,
            signals=signals,
            management_spec=management_spec,
            config=config,
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            data_version=data_version,
            factor_versions=factor_versions,
            initial_cash=initial_cash,
            instrument_multipliers=instrument_multipliers,
            instrument_roots=instrument_roots,
            run_id=run_id or "fast-path-reference-fallback",
        )
    return run_reference_backtest(
        bars=bars,
        signals=signals,
        config=config,
        strategy_id=strategy_id,
        strategy_version=strategy_version,
        data_version=data_version,
        factor_versions=factor_versions,
        initial_cash=initial_cash,
        instrument_multipliers=instrument_multipliers,
        instrument_roots=instrument_roots,
        run_id=run_id,
        output_dir=None,
        registry_path=None,
        run_manifest_path=None,
        repo_root=Path.cwd(),
        write_outputs=False,
    )


def _unsupported_features(
    *,
    bars: tuple[Mapping[str, Any], ...],
    signals: tuple[SignalRecord, ...],
    config: Any,
    management_spec: ManagementSpec | None,
    requested_features: frozenset[str],
) -> frozenset[str]:
    unsupported = set(requested_features.intersection(REFERENCE_FALLBACK_FEATURES))
    if _uses_nonzero_slippage(config):
        unsupported.add("slippage")
    if _uses_liquidity_policy(config):
        unsupported.add("liquidity_policy")
    if _uses_multiple_instruments(bars):
        unsupported.add("multi_instrument")
    for signal in signals:
        if signal.desired_exposure is not None:
            unsupported.add("portfolio_target")
        if signal.direction.value not in {"long", "short"}:
            unsupported.add(f"direction:{signal.direction.value}")
    unsupported.update(_management_features(management_spec))
    return frozenset(unsupported)


def _management_spec(value: ManagementSpec | Mapping[str, Any] | None) -> ManagementSpec | None:
    if value is None:
        return None
    if isinstance(value, ManagementSpec):
        return value
    return ManagementSpec.from_mapping(value)


def _management_features(spec: ManagementSpec | None) -> tuple[str, ...]:
    if spec is None:
        return ()
    features: list[str] = []
    if spec.fixed_stop.enabled:
        features.append("management_fixed_stop")
    if spec.target_r_multiple.enabled:
        features.append("management_target")
    if spec.laddered_partial_take_profit.enabled:
        features.append("partial_exit")
    if spec.eod_exit.enabled:
        features.append("management_eod_exit")
    if spec.cooldown.enabled:
        features.append("cooldown")
    if spec.max_holding_bars.enabled:
        features.append("max_holding_bars")
    if spec.time_exit.enabled:
        features.append("time_exit")
    if spec.trailing_stop.enabled:
        features.append("trailing_stop")
    if spec.breakeven_stop.enabled:
        features.append("breakeven_stop")
    if spec.atr_stop.enabled:
        features.append("atr_stop")
    if spec.volatility_stop.enabled:
        features.append("volatility_stop")
    if spec.scale_in.enabled:
        features.append("scale_in")
    if spec.scale_out.enabled:
        features.append("scale_out")
    if spec.max_trades_per_day.enabled:
        features.append("max_trades_per_day")
    if spec.risk_per_trade is not None:
        features.append("risk_per_trade")
    if spec.max_position_percent is not None:
        features.append("max_position_percent")
    return tuple(sorted(set(features)))


def _uses_nonzero_slippage(config: Any) -> bool:
    slippage_model = getattr(config, "slippage_model", None)
    if slippage_model is None:
        return False
    return not bool(getattr(slippage_model, "total_is_zero", False))


def _uses_liquidity_policy(config: Any) -> bool:
    policy = getattr(config, "liquidity_policy", None)
    if policy is None:
        return False
    payload = policy.to_dict() if hasattr(policy, "to_dict") else {}
    return any(value not in (None, False, "0", "0.0") for value in payload.values())


def _uses_multiple_instruments(bars: tuple[Mapping[str, Any], ...]) -> bool:
    instruments = {str(bar["instrument_id"]) for bar in bars}
    sessions = {str(bar["session_id"]) for bar in bars}
    return len(instruments) > 1 or len(sessions) > 1


def _decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


__all__ = [
    "ACCELERATED_FEATURES",
    "FAST_PATH_MODE_ACCELERATED",
    "FAST_PATH_MODE_REFERENCE_FALLBACK",
    "FAST_PATH_VERSION",
    "FastPathError",
    "FastPathRun",
    "KNOWN_FAST_PATH_FEATURES",
    "REFERENCE_FALLBACK_FEATURES",
    "UnsupportedFastPathFeatureError",
    "run_fast_path_backtest",
]
