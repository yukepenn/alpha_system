"""Position-management specification primitives.

The management spec describes post-entry rules only. It does not own account
equity, portfolio allocation, broker order state, or strategy signal logic.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field, fields
from decimal import Decimal, InvalidOperation
from typing import Any


class ManagementSpecError(ValueError):
    """Raised when a management specification is invalid."""


@dataclass(frozen=True, slots=True)
class FixedStopSpec:
    enabled: bool = False
    stop_pct: Decimal | None = None
    stop_price: Decimal | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "enabled", _bool(self.enabled, "fixed_stop.enabled"))
        object.__setattr__(self, "stop_pct", _optional_positive_decimal(self.stop_pct, "fixed_stop.stop_pct"))
        object.__setattr__(self, "stop_price", _optional_positive_decimal(self.stop_price, "fixed_stop.stop_price"))
        if self.enabled and self.stop_pct is None and self.stop_price is None:
            raise ManagementSpecError("fixed_stop requires stop_pct or stop_price when enabled")
        if self.stop_pct is not None and self.stop_price is not None:
            raise ManagementSpecError("fixed_stop must define only one of stop_pct or stop_price")


@dataclass(frozen=True, slots=True)
class AtrStopSpec:
    enabled: bool = False
    atr_multiple: Decimal | None = None
    atr_value: Decimal | None = None
    bar_field: str = "atr"

    def __post_init__(self) -> None:
        object.__setattr__(self, "enabled", _bool(self.enabled, "atr_stop.enabled"))
        object.__setattr__(self, "atr_multiple", _optional_positive_decimal(self.atr_multiple, "atr_stop.atr_multiple"))
        object.__setattr__(self, "atr_value", _optional_positive_decimal(self.atr_value, "atr_stop.atr_value"))
        object.__setattr__(self, "bar_field", _text(self.bar_field, "atr_stop.bar_field"))
        if self.enabled and self.atr_multiple is None:
            raise ManagementSpecError("atr_stop requires atr_multiple when enabled")


@dataclass(frozen=True, slots=True)
class VolatilityStopSpec:
    enabled: bool = False
    volatility_multiple: Decimal | None = None
    volatility_value: Decimal | None = None
    bar_field: str = "volatility"

    def __post_init__(self) -> None:
        object.__setattr__(self, "enabled", _bool(self.enabled, "volatility_stop.enabled"))
        object.__setattr__(
            self,
            "volatility_multiple",
            _optional_positive_decimal(self.volatility_multiple, "volatility_stop.volatility_multiple"),
        )
        object.__setattr__(
            self,
            "volatility_value",
            _optional_positive_decimal(self.volatility_value, "volatility_stop.volatility_value"),
        )
        object.__setattr__(self, "bar_field", _text(self.bar_field, "volatility_stop.bar_field"))
        if self.enabled and self.volatility_multiple is None:
            raise ManagementSpecError("volatility_stop requires volatility_multiple when enabled")


@dataclass(frozen=True, slots=True)
class TargetRMultipleSpec:
    enabled: bool = False
    r_multiple: Decimal | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "enabled", _bool(self.enabled, "target_r_multiple.enabled"))
        object.__setattr__(
            self,
            "r_multiple",
            _optional_positive_decimal(self.r_multiple, "target_r_multiple.r_multiple"),
        )
        if self.enabled and self.r_multiple is None:
            raise ManagementSpecError("target_r_multiple requires r_multiple when enabled")


@dataclass(frozen=True, slots=True)
class PartialTakeProfitStep:
    threshold_r: Decimal
    exit_fraction: Decimal
    label: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "threshold_r", _positive_decimal(self.threshold_r, "partial.threshold_r"))
        object.__setattr__(
            self,
            "exit_fraction",
            _fraction_decimal(self.exit_fraction, "partial.exit_fraction"),
        )
        label = str(self.label or f"{self.threshold_r}R")
        object.__setattr__(self, "label", label)


@dataclass(frozen=True, slots=True)
class LadderedPartialsSpec:
    enabled: bool = False
    steps: tuple[PartialTakeProfitStep, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "enabled", _bool(self.enabled, "laddered_partial_take_profit.enabled"))
        steps = tuple(_partial_step(step) for step in self.steps)
        steps = tuple(sorted(steps, key=lambda step: (step.threshold_r, step.label)))
        object.__setattr__(self, "steps", steps)
        if self.enabled and not steps:
            raise ManagementSpecError("laddered_partial_take_profit requires at least one step when enabled")
        total = sum((step.exit_fraction for step in steps), Decimal("0"))
        if total > Decimal("1"):
            raise ManagementSpecError("laddered partial exit fractions must not exceed 1")
        labels = [step.label for step in steps]
        if len(set(labels)) != len(labels):
            raise ManagementSpecError("laddered partial labels must be unique")


@dataclass(frozen=True, slots=True)
class BreakevenStopSpec:
    enabled: bool = False
    trigger_r: Decimal | None = None
    offset_r: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        object.__setattr__(self, "enabled", _bool(self.enabled, "breakeven_stop.enabled"))
        object.__setattr__(self, "trigger_r", _optional_positive_decimal(self.trigger_r, "breakeven_stop.trigger_r"))
        object.__setattr__(self, "offset_r", _non_negative_decimal(self.offset_r, "breakeven_stop.offset_r"))
        if self.enabled and self.trigger_r is None:
            raise ManagementSpecError("breakeven_stop requires trigger_r when enabled")


@dataclass(frozen=True, slots=True)
class TrailingStopSpec:
    enabled: bool = False
    trail_r: Decimal | None = None
    trail_pct: Decimal | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "enabled", _bool(self.enabled, "trailing_stop.enabled"))
        object.__setattr__(self, "trail_r", _optional_positive_decimal(self.trail_r, "trailing_stop.trail_r"))
        object.__setattr__(self, "trail_pct", _optional_positive_decimal(self.trail_pct, "trailing_stop.trail_pct"))
        if self.enabled and self.trail_r is None and self.trail_pct is None:
            raise ManagementSpecError("trailing_stop requires trail_r or trail_pct when enabled")
        if self.trail_r is not None and self.trail_pct is not None:
            raise ManagementSpecError("trailing_stop must define only one of trail_r or trail_pct")


@dataclass(frozen=True, slots=True)
class TimeExitSpec:
    enabled: bool = False
    max_minutes: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "enabled", _bool(self.enabled, "time_exit.enabled"))
        object.__setattr__(self, "max_minutes", _optional_positive_int(self.max_minutes, "time_exit.max_minutes"))
        if self.enabled and self.max_minutes is None:
            raise ManagementSpecError("time_exit requires max_minutes when enabled")


@dataclass(frozen=True, slots=True)
class EodExitSpec:
    enabled: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "enabled", _bool(self.enabled, "eod_exit.enabled"))


@dataclass(frozen=True, slots=True)
class MaxTradesPerDaySpec:
    enabled: bool = False
    limit: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "enabled", _bool(self.enabled, "max_trades_per_day.enabled"))
        object.__setattr__(self, "limit", _optional_positive_int(self.limit, "max_trades_per_day.limit"))
        if self.enabled and self.limit is None:
            raise ManagementSpecError("max_trades_per_day requires limit when enabled")


@dataclass(frozen=True, slots=True)
class CooldownSpec:
    enabled: bool = False
    bars: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "enabled", _bool(self.enabled, "cooldown.enabled"))
        object.__setattr__(self, "bars", _optional_positive_int(self.bars, "cooldown.bars"))
        if self.enabled and self.bars is None:
            raise ManagementSpecError("cooldown requires bars when enabled")


@dataclass(frozen=True, slots=True)
class ScaleLegSpec:
    trigger_r: Decimal
    quantity_fraction: Decimal
    label: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "trigger_r", _positive_decimal(self.trigger_r, "scale_leg.trigger_r"))
        object.__setattr__(
            self,
            "quantity_fraction",
            _fraction_decimal(self.quantity_fraction, "scale_leg.quantity_fraction"),
        )
        object.__setattr__(self, "label", str(self.label or f"{self.trigger_r}R"))


@dataclass(frozen=True, slots=True)
class ScaleRuleSpec:
    enabled: bool = False
    mode: str = "contract_only"
    legs: tuple[ScaleLegSpec, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "enabled", _bool(self.enabled, "scale_rule.enabled"))
        object.__setattr__(self, "mode", _text(self.mode, "scale_rule.mode"))
        legs = tuple(_scale_leg(leg) for leg in self.legs)
        object.__setattr__(self, "legs", tuple(sorted(legs, key=lambda leg: (leg.trigger_r, leg.label))))


@dataclass(frozen=True, slots=True)
class MaxHoldingBarsSpec:
    enabled: bool = False
    max_bars: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "enabled", _bool(self.enabled, "max_holding_bars.enabled"))
        object.__setattr__(self, "max_bars", _optional_positive_int(self.max_bars, "max_holding_bars.max_bars"))
        if self.enabled and self.max_bars is None:
            raise ManagementSpecError("max_holding_bars requires max_bars when enabled")


@dataclass(frozen=True, slots=True)
class ManagementSpec:
    """Reviewed post-entry management contract."""

    fixed_stop: FixedStopSpec = field(default_factory=FixedStopSpec)
    atr_stop: AtrStopSpec = field(default_factory=AtrStopSpec)
    volatility_stop: VolatilityStopSpec = field(default_factory=VolatilityStopSpec)
    target_r_multiple: TargetRMultipleSpec = field(default_factory=TargetRMultipleSpec)
    laddered_partial_take_profit: LadderedPartialsSpec = field(default_factory=LadderedPartialsSpec)
    breakeven_stop: BreakevenStopSpec = field(default_factory=BreakevenStopSpec)
    trailing_stop: TrailingStopSpec = field(default_factory=TrailingStopSpec)
    time_exit: TimeExitSpec = field(default_factory=TimeExitSpec)
    eod_exit: EodExitSpec = field(default_factory=EodExitSpec)
    max_trades_per_day: MaxTradesPerDaySpec = field(default_factory=MaxTradesPerDaySpec)
    cooldown: CooldownSpec = field(default_factory=CooldownSpec)
    scale_in: ScaleRuleSpec = field(default_factory=ScaleRuleSpec)
    scale_out: ScaleRuleSpec = field(default_factory=ScaleRuleSpec)
    max_holding_bars: MaxHoldingBarsSpec = field(default_factory=MaxHoldingBarsSpec)
    risk_per_trade: Decimal | None = None
    max_position_percent: Decimal | None = None
    session_reset: bool = True
    management_id: str = "management:default"

    def __post_init__(self) -> None:
        object.__setattr__(self, "fixed_stop", _spec(self.fixed_stop, FixedStopSpec, "fixed_stop"))
        object.__setattr__(self, "atr_stop", _spec(self.atr_stop, AtrStopSpec, "atr_stop"))
        object.__setattr__(self, "volatility_stop", _spec(self.volatility_stop, VolatilityStopSpec, "volatility_stop"))
        object.__setattr__(
            self,
            "target_r_multiple",
            _spec(self.target_r_multiple, TargetRMultipleSpec, "target_r_multiple"),
        )
        object.__setattr__(
            self,
            "laddered_partial_take_profit",
            _spec(self.laddered_partial_take_profit, LadderedPartialsSpec, "laddered_partial_take_profit"),
        )
        object.__setattr__(self, "breakeven_stop", _spec(self.breakeven_stop, BreakevenStopSpec, "breakeven_stop"))
        object.__setattr__(self, "trailing_stop", _spec(self.trailing_stop, TrailingStopSpec, "trailing_stop"))
        object.__setattr__(self, "time_exit", _spec(self.time_exit, TimeExitSpec, "time_exit"))
        object.__setattr__(self, "eod_exit", _spec(self.eod_exit, EodExitSpec, "eod_exit"))
        object.__setattr__(
            self,
            "max_trades_per_day",
            _spec(self.max_trades_per_day, MaxTradesPerDaySpec, "max_trades_per_day"),
        )
        object.__setattr__(self, "cooldown", _spec(self.cooldown, CooldownSpec, "cooldown"))
        object.__setattr__(self, "scale_in", _spec(self.scale_in, ScaleRuleSpec, "scale_in"))
        object.__setattr__(self, "scale_out", _spec(self.scale_out, ScaleRuleSpec, "scale_out"))
        object.__setattr__(
            self,
            "max_holding_bars",
            _spec(self.max_holding_bars, MaxHoldingBarsSpec, "max_holding_bars"),
        )
        object.__setattr__(self, "risk_per_trade", _optional_fraction_decimal(self.risk_per_trade, "risk_per_trade"))
        object.__setattr__(
            self,
            "max_position_percent",
            _optional_fraction_decimal(self.max_position_percent, "max_position_percent"),
        )
        object.__setattr__(self, "session_reset", _bool(self.session_reset, "session_reset"))
        object.__setattr__(self, "management_id", _text(self.management_id, "management_id"))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any] | None) -> "ManagementSpec":
        if payload is None:
            return cls()
        active = dict(payload)
        return cls(
            fixed_stop=_fixed_stop(active.get("fixed_stop")),
            atr_stop=_atr_stop(active.get("atr_stop")),
            volatility_stop=_volatility_stop(active.get("volatility_stop")),
            target_r_multiple=_target_r(active.get("target_r_multiple")),
            laddered_partial_take_profit=_partials(active.get("laddered_partial_take_profit")),
            breakeven_stop=_breakeven(active.get("breakeven_stop")),
            trailing_stop=_trailing(active.get("trailing_stop")),
            time_exit=_time_exit(active.get("time_exit")),
            eod_exit=_eod_exit(active.get("eod_exit")),
            max_trades_per_day=_max_trades(active.get("max_trades_per_day")),
            cooldown=_cooldown(active.get("cooldown")),
            scale_in=_scale_rule(active.get("scale_in")),
            scale_out=_scale_rule(active.get("scale_out")),
            max_holding_bars=_max_holding(active.get("max_holding_bars")),
            risk_per_trade=active.get("risk_per_trade"),
            max_position_percent=active.get("max_position_percent"),
            session_reset=active.get("session_reset", True),
            management_id=str(active.get("management_id", "management:default")),
        )

    @classmethod
    def field_names(cls) -> tuple[str, ...]:
        return tuple(field.name for field in fields(cls))

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))

    @property
    def has_r_based_rule(self) -> bool:
        return (
            self.target_r_multiple.enabled
            or self.laddered_partial_take_profit.enabled
            or self.breakeven_stop.enabled
            or self.trailing_stop.enabled
            and self.trailing_stop.trail_r is not None
        )


def _fixed_stop(value: Any) -> FixedStopSpec:
    if value in (None, False):
        return FixedStopSpec()
    if isinstance(value, (int, float, str, Decimal)):
        return FixedStopSpec(enabled=True, stop_pct=value)
    payload = _mapping(value, "fixed_stop")
    return FixedStopSpec(
        enabled=payload.get("enabled", True),
        stop_pct=payload.get("stop_pct"),
        stop_price=payload.get("stop_price"),
    )


def _atr_stop(value: Any) -> AtrStopSpec:
    if value in (None, False):
        return AtrStopSpec()
    payload = _mapping(value, "atr_stop")
    return AtrStopSpec(
        enabled=payload.get("enabled", True),
        atr_multiple=payload.get("atr_multiple"),
        atr_value=payload.get("atr_value"),
        bar_field=str(payload.get("bar_field", "atr")),
    )


def _volatility_stop(value: Any) -> VolatilityStopSpec:
    if value in (None, False):
        return VolatilityStopSpec()
    payload = _mapping(value, "volatility_stop")
    return VolatilityStopSpec(
        enabled=payload.get("enabled", True),
        volatility_multiple=payload.get("volatility_multiple"),
        volatility_value=payload.get("volatility_value"),
        bar_field=str(payload.get("bar_field", "volatility")),
    )


def _target_r(value: Any) -> TargetRMultipleSpec:
    if value in (None, False):
        return TargetRMultipleSpec()
    if isinstance(value, (int, float, str, Decimal)):
        return TargetRMultipleSpec(enabled=True, r_multiple=value)
    payload = _mapping(value, "target_r_multiple")
    return TargetRMultipleSpec(enabled=payload.get("enabled", True), r_multiple=payload.get("r_multiple"))


def _partials(value: Any) -> LadderedPartialsSpec:
    if value in (None, False):
        return LadderedPartialsSpec()
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, Mapping)):
        return LadderedPartialsSpec(enabled=True, steps=tuple(_partial_step(item) for item in value))
    payload = _mapping(value, "laddered_partial_take_profit")
    return LadderedPartialsSpec(
        enabled=payload.get("enabled", True),
        steps=tuple(_partial_step(step) for step in payload.get("steps", ())),
    )


def _breakeven(value: Any) -> BreakevenStopSpec:
    if value in (None, False):
        return BreakevenStopSpec()
    payload = _mapping(value, "breakeven_stop")
    return BreakevenStopSpec(
        enabled=payload.get("enabled", True),
        trigger_r=payload.get("trigger_r"),
        offset_r=payload.get("offset_r", "0"),
    )


def _trailing(value: Any) -> TrailingStopSpec:
    if value in (None, False):
        return TrailingStopSpec()
    payload = _mapping(value, "trailing_stop")
    return TrailingStopSpec(
        enabled=payload.get("enabled", True),
        trail_r=payload.get("trail_r"),
        trail_pct=payload.get("trail_pct"),
    )


def _time_exit(value: Any) -> TimeExitSpec:
    if value in (None, False):
        return TimeExitSpec()
    if isinstance(value, (int, str)):
        return TimeExitSpec(enabled=True, max_minutes=value)
    payload = _mapping(value, "time_exit")
    return TimeExitSpec(enabled=payload.get("enabled", True), max_minutes=payload.get("max_minutes"))


def _eod_exit(value: Any) -> EodExitSpec:
    if value is None:
        return EodExitSpec()
    if isinstance(value, bool):
        return EodExitSpec(enabled=value)
    payload = _mapping(value, "eod_exit")
    return EodExitSpec(enabled=payload.get("enabled", True))


def _max_trades(value: Any) -> MaxTradesPerDaySpec:
    if value in (None, False):
        return MaxTradesPerDaySpec()
    if isinstance(value, (int, str)):
        return MaxTradesPerDaySpec(enabled=True, limit=value)
    payload = _mapping(value, "max_trades_per_day")
    return MaxTradesPerDaySpec(enabled=payload.get("enabled", True), limit=payload.get("limit"))


def _cooldown(value: Any) -> CooldownSpec:
    if value in (None, False):
        return CooldownSpec()
    if isinstance(value, (int, str)):
        return CooldownSpec(enabled=True, bars=value)
    payload = _mapping(value, "cooldown")
    return CooldownSpec(enabled=payload.get("enabled", True), bars=payload.get("bars"))


def _scale_rule(value: Any) -> ScaleRuleSpec:
    if value in (None, False):
        return ScaleRuleSpec()
    payload = _mapping(value, "scale_rule")
    return ScaleRuleSpec(
        enabled=payload.get("enabled", True),
        mode=str(payload.get("mode", "contract_only")),
        legs=tuple(_scale_leg(leg) for leg in payload.get("legs", ())),
    )


def _max_holding(value: Any) -> MaxHoldingBarsSpec:
    if value in (None, False):
        return MaxHoldingBarsSpec()
    if isinstance(value, (int, str)):
        return MaxHoldingBarsSpec(enabled=True, max_bars=value)
    payload = _mapping(value, "max_holding_bars")
    return MaxHoldingBarsSpec(enabled=payload.get("enabled", True), max_bars=payload.get("max_bars"))


def _partial_step(value: Any) -> PartialTakeProfitStep:
    if isinstance(value, PartialTakeProfitStep):
        return value
    payload = _mapping(value, "partial")
    return PartialTakeProfitStep(
        threshold_r=payload.get("threshold_r"),
        exit_fraction=payload.get("exit_fraction"),
        label=str(payload.get("label", "")),
    )


def _scale_leg(value: Any) -> ScaleLegSpec:
    if isinstance(value, ScaleLegSpec):
        return value
    payload = _mapping(value, "scale_leg")
    return ScaleLegSpec(
        trigger_r=payload.get("trigger_r"),
        quantity_fraction=payload.get("quantity_fraction"),
        label=str(payload.get("label", "")),
    )


def _spec(value: Any, cls: type[Any], field_name: str) -> Any:
    if isinstance(value, cls):
        return value
    if isinstance(value, Mapping):
        return cls(**value)
    raise ManagementSpecError(f"{field_name} must be {cls.__name__} or mapping")


def _mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ManagementSpecError(f"{field_name} must be a mapping")
    return value


def _bool(value: Any, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip().lower() in {"true", "false"}:
        return value.strip().lower() == "true"
    raise ManagementSpecError(f"{field_name} must be boolean")


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ManagementSpecError(f"{field_name} must be a non-empty string")
    return value.strip()


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        raise ManagementSpecError(f"{field_name} must be a positive integer")
    try:
        active = int(value)
    except (TypeError, ValueError) as exc:
        raise ManagementSpecError(f"{field_name} must be a positive integer") from exc
    if active <= 0:
        raise ManagementSpecError(f"{field_name} must be positive")
    return active


def _optional_positive_int(value: Any, field_name: str) -> int | None:
    if value in (None, ""):
        return None
    return _positive_int(value, field_name)


def _decimal(value: Any, field_name: str) -> Decimal:
    if isinstance(value, bool):
        raise ManagementSpecError(f"{field_name} must be numeric")
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ManagementSpecError(f"{field_name} must be numeric") from exc


def _positive_decimal(value: Any, field_name: str) -> Decimal:
    active = _decimal(value, field_name)
    if active <= 0:
        raise ManagementSpecError(f"{field_name} must be positive")
    return active


def _non_negative_decimal(value: Any, field_name: str) -> Decimal:
    active = _decimal(value, field_name)
    if active < 0:
        raise ManagementSpecError(f"{field_name} must be non-negative")
    return active


def _optional_positive_decimal(value: Any, field_name: str) -> Decimal | None:
    if value in (None, ""):
        return None
    return _positive_decimal(value, field_name)


def _fraction_decimal(value: Any, field_name: str) -> Decimal:
    active = _positive_decimal(value, field_name)
    if active > Decimal("1"):
        raise ManagementSpecError(f"{field_name} must be no greater than 1")
    return active


def _optional_fraction_decimal(value: Any, field_name: str) -> Decimal | None:
    if value in (None, ""):
        return None
    return _fraction_decimal(value, field_name)


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value.normalize(), "f")
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    return value
