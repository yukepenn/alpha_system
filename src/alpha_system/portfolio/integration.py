"""Signal-to-target portfolio integration helpers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from decimal import Decimal, InvalidOperation
from typing import Any

from alpha_system.core.enums import Direction
from alpha_system.portfolio.allocation import CapitalAllocationState
from alpha_system.portfolio.risk import apply_portfolio_limits
from alpha_system.portfolio.sizing import SizeDecision, SizeRequest, size_position, zero_size_decision
from alpha_system.portfolio.spec import PortfolioSpec
from alpha_system.portfolio.targets import PortfolioTarget, target_id_for, targets_to_records
from alpha_system.signals.spec import SignalRecord, SignalType


class PortfolioIntegrationError(ValueError):
    """Raised when signals cannot be converted to portfolio targets."""


def signals_to_portfolio_targets(
    *,
    signals: Iterable[SignalRecord | Mapping[str, Any]],
    prices: Mapping[str, Decimal | str | int | float],
    portfolio_spec: PortfolioSpec | Mapping[str, Any] | None = None,
    allocation_state: CapitalAllocationState | None = None,
    stop_distances: Mapping[str, Decimal | str | int | float] | None = None,
) -> tuple[PortfolioTarget, ...]:
    """Convert strategy-intent signals into deterministic portfolio targets."""
    active_spec = portfolio_spec if isinstance(portfolio_spec, PortfolioSpec) else PortfolioSpec.from_mapping(portfolio_spec)
    active_allocation = allocation_state or CapitalAllocationState.from_spec(active_spec.capital_allocation)
    normalized_signals = _normalize_signals(signals)
    decisions: list[SizeDecision] = []
    for signal in normalized_signals:
        if signal.signal_type is SignalType.ENTRY and signal.direction is not Direction.FLAT:
            price = _price_for(signal.instrument_id, prices)
            request = SizeRequest(
                instrument_id=signal.instrument_id,
                direction=signal.direction,
                price=price,
                equity=active_allocation.total_equity,
                source_signal_id=signal.signal_id,
                desired_exposure=_desired_exposure(signal, active_spec),
                confidence=_confidence(signal, active_spec),
                stop_distance=_optional_price_for(signal.instrument_id, stop_distances),
            )
            decisions.append(size_position(request, active_spec.position_sizing))
            continue
        decisions.append(
            zero_size_decision(
                instrument_id=signal.instrument_id,
                direction=Direction.FLAT,
                equity=active_allocation.total_equity,
                source_signal_id=signal.signal_id,
                reason="exit_or_hold_target_flat",
            )
        )
    constrained = apply_portfolio_limits(tuple(decisions), active_allocation, active_spec)
    targets = tuple(
        PortfolioTarget.from_decision(
            decision=decision,
            target_id=target_id_for(
                active_spec.portfolio_target.target_id_prefix,
                signal.signal_id,
                signal.instrument_id,
                signal.bar_index,
            ),
            event_ts=signal.event_ts,
            available_ts=signal.available_ts,
            session_id=signal.session_id,
            bar_index=signal.bar_index,
            strategy_id=signal.strategy_id,
            strategy_version=signal.strategy_version,
            data_version=signal.data_version,
            quality_flags=signal.quality_flags,
        )
        for signal, decision in zip(normalized_signals, constrained, strict=True)
    )
    return tuple(PortfolioTarget(**record) for record in targets_to_records(targets))


def reference_default_quantity_from_targets(
    targets: Iterable[PortfolioTarget],
    *,
    instrument_id: str | None = None,
) -> Decimal:
    """Return one deterministic target quantity for reference-engine config."""
    active = tuple(target for target in targets if not target.rejected and target.target_quantity > 0)
    if instrument_id is not None:
        active = tuple(target for target in active if target.instrument_id == instrument_id)
    if not active:
        return Decimal("0")
    ordered = sorted(active, key=lambda target: (target.instrument_id, target.source_signal_id, target.target_id))
    return ordered[0].target_quantity


def _normalize_signals(signals: Iterable[SignalRecord | Mapping[str, Any]]) -> tuple[SignalRecord, ...]:
    normalized = tuple(signal if isinstance(signal, SignalRecord) else SignalRecord.from_mapping(signal) for signal in signals)
    return tuple(
        sorted(
            normalized,
            key=lambda signal: (
                signal.available_ts,
                signal.instrument_id,
                signal.bar_index,
                signal.signal_id,
            ),
        )
    )


def _desired_exposure(signal: SignalRecord, spec: PortfolioSpec) -> Decimal | None:
    if not spec.signal_to_target_conversion.use_desired_exposure:
        return None
    if signal.desired_exposure in (None, ""):
        return None
    return _fraction(signal.desired_exposure, "desired_exposure")


def _confidence(signal: SignalRecord, spec: PortfolioSpec) -> Decimal | None:
    if not spec.signal_to_target_conversion.use_confidence:
        return None
    if signal.confidence in (None, ""):
        return None
    return _fraction(signal.confidence, "confidence")


def _price_for(instrument_id: str, prices: Mapping[str, Decimal | str | int | float]) -> Decimal:
    if instrument_id not in prices:
        raise PortfolioIntegrationError(f"missing price for instrument_id: {instrument_id}")
    return _positive_decimal(prices[instrument_id], "price")


def _optional_price_for(
    instrument_id: str,
    prices: Mapping[str, Decimal | str | int | float] | None,
) -> Decimal | None:
    if prices is None or instrument_id not in prices:
        return None
    return _positive_decimal(prices[instrument_id], "stop_distance")


def _decimal(value: Any, field_name: str) -> Decimal:
    if isinstance(value, bool):
        raise PortfolioIntegrationError(f"{field_name} must be numeric")
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise PortfolioIntegrationError(f"{field_name} must be numeric") from exc


def _positive_decimal(value: Any, field_name: str) -> Decimal:
    active = _decimal(value, field_name)
    if active <= 0:
        raise PortfolioIntegrationError(f"{field_name} must be positive")
    return active


def _fraction(value: Any, field_name: str) -> Decimal:
    active = _decimal(value, field_name)
    if active < 0 or active > Decimal("1"):
        raise PortfolioIntegrationError(f"{field_name} must be between 0 and 1")
    return active
