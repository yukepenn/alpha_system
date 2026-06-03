"""Portfolio target, sizing, allocation, and risk specification primitives."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field, fields
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any


class PortfolioSpecError(ValueError):
    """Raised when a portfolio specification is invalid."""


class SizingMethod(str, Enum):
    FIXED_NOTIONAL = "fixed_notional"
    RISK_PER_TRADE = "risk_per_trade"


class InsufficientCapitalPolicy(str, Enum):
    REJECT = "reject"
    CAP = "cap"


class FutureConstraintMode(str, Enum):
    CONTRACT_ONLY = "contract_only"


@dataclass(frozen=True, slots=True)
class PortfolioTargetSpec:
    schema_version: str = "portfolio_target_v1"
    target_id_prefix: str = "portfolio-target"
    deterministic_sort: tuple[str, ...] = ("instrument_id", "source_signal_id", "target_id")

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_version", _text(self.schema_version, "portfolio_target.schema_version"))
        object.__setattr__(self, "target_id_prefix", _text(self.target_id_prefix, "portfolio_target.target_id_prefix"))
        object.__setattr__(
            self,
            "deterministic_sort",
            _string_tuple(self.deterministic_sort, "portfolio_target.deterministic_sort"),
        )


@dataclass(frozen=True, slots=True)
class PositionSizingSpec:
    method: SizingMethod = SizingMethod.FIXED_NOTIONAL
    fixed_notional: Decimal | None = Decimal("1000")
    risk_per_trade: Decimal | None = None
    stop_distance: Decimal | None = None
    min_notional: Decimal = Decimal("0")
    allow_fractional: bool = True

    def __post_init__(self) -> None:
        method = _sizing_method(self.method)
        object.__setattr__(self, "method", method)
        object.__setattr__(self, "fixed_notional", _optional_positive_decimal(self.fixed_notional, "fixed_notional"))
        object.__setattr__(self, "risk_per_trade", _optional_fraction_decimal(self.risk_per_trade, "risk_per_trade"))
        object.__setattr__(self, "stop_distance", _optional_positive_decimal(self.stop_distance, "stop_distance"))
        object.__setattr__(self, "min_notional", _non_negative_decimal(self.min_notional, "min_notional"))
        object.__setattr__(self, "allow_fractional", _bool(self.allow_fractional, "allow_fractional"))
        if method is SizingMethod.FIXED_NOTIONAL and self.fixed_notional is None:
            raise PortfolioSpecError("fixed_notional sizing requires fixed_notional")
        if method is SizingMethod.RISK_PER_TRADE:
            if self.risk_per_trade is None:
                raise PortfolioSpecError("risk_per_trade sizing requires risk_per_trade")
            if self.stop_distance is None:
                raise PortfolioSpecError("risk_per_trade sizing requires stop_distance")


@dataclass(frozen=True, slots=True)
class CapitalAllocationSpec:
    starting_equity: Decimal = Decimal("100000")
    cash_buffer: Decimal = Decimal("0")
    insufficient_capital_policy: InsufficientCapitalPolicy = InsufficientCapitalPolicy.REJECT

    def __post_init__(self) -> None:
        object.__setattr__(self, "starting_equity", _positive_decimal(self.starting_equity, "starting_equity"))
        object.__setattr__(self, "cash_buffer", _fraction_decimal(self.cash_buffer, "cash_buffer", allow_zero=True))
        object.__setattr__(
            self,
            "insufficient_capital_policy",
            _capital_policy(self.insufficient_capital_policy),
        )


@dataclass(frozen=True, slots=True)
class RiskLimitsSpec:
    max_position_percent: Decimal | None = None
    max_gross_exposure: Decimal | None = None
    max_net_exposure: Decimal | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "max_position_percent",
            _optional_fraction_decimal(self.max_position_percent, "max_position_percent"),
        )
        object.__setattr__(
            self,
            "max_gross_exposure",
            _optional_positive_decimal(self.max_gross_exposure, "max_gross_exposure"),
        )
        object.__setattr__(
            self,
            "max_net_exposure",
            _optional_non_negative_decimal(self.max_net_exposure, "max_net_exposure"),
        )


@dataclass(frozen=True, slots=True)
class MultiSymbolConstraintsSpec:
    required_identifier: str = "instrument_id"
    max_active_instruments: int | None = None
    max_target_percent_per_instrument: Decimal | None = None
    allow_repeated_instrument_targets: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "required_identifier", _text(self.required_identifier, "required_identifier"))
        if self.required_identifier != "instrument_id":
            raise PortfolioSpecError("multi-symbol constraints require instrument_id identity")
        object.__setattr__(
            self,
            "max_active_instruments",
            _optional_positive_int(self.max_active_instruments, "max_active_instruments"),
        )
        object.__setattr__(
            self,
            "max_target_percent_per_instrument",
            _optional_fraction_decimal(
                self.max_target_percent_per_instrument,
                "max_target_percent_per_instrument",
            ),
        )
        object.__setattr__(
            self,
            "allow_repeated_instrument_targets",
            _bool(self.allow_repeated_instrument_targets, "allow_repeated_instrument_targets"),
        )


@dataclass(frozen=True, slots=True)
class FutureSectorAssetConstraintsSpec:
    mode: FutureConstraintMode = FutureConstraintMode.CONTRACT_ONLY
    enabled: bool = False
    rules: tuple[Mapping[str, Any], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "mode", _future_mode(self.mode))
        object.__setattr__(self, "enabled", _bool(self.enabled, "future_sector_asset_constraints.enabled"))
        object.__setattr__(
            self,
            "rules",
            tuple(_mapping(rule, "future_sector_asset_constraints.rule") for rule in self.rules),
        )
        if self.enabled:
            raise PortfolioSpecError("sector and asset constraints are contract-only in this phase")


@dataclass(frozen=True, slots=True)
class FutureCorrelationAwareAllocationSpec:
    mode: FutureConstraintMode = FutureConstraintMode.CONTRACT_ONLY
    enabled: bool = False
    inputs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "mode", _future_mode(self.mode))
        object.__setattr__(self, "enabled", _bool(self.enabled, "future_correlation_aware_allocation.enabled"))
        object.__setattr__(
            self,
            "inputs",
            _string_tuple(self.inputs, "future_correlation_aware_allocation.inputs"),
        )
        if self.enabled:
            raise PortfolioSpecError("correlation-aware allocation is contract-only in this phase")


@dataclass(frozen=True, slots=True)
class SignalToTargetConversionSpec:
    mode: str = "entry_exit_to_target"
    use_desired_exposure: bool = True
    use_confidence: bool = False
    exit_signal_target_percent: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        object.__setattr__(self, "mode", _text(self.mode, "signal_to_target_conversion.mode"))
        if self.mode != "entry_exit_to_target":
            raise PortfolioSpecError("unsupported signal-to-target conversion mode")
        object.__setattr__(self, "use_desired_exposure", _bool(self.use_desired_exposure, "use_desired_exposure"))
        object.__setattr__(self, "use_confidence", _bool(self.use_confidence, "use_confidence"))
        object.__setattr__(
            self,
            "exit_signal_target_percent",
            _fraction_decimal(self.exit_signal_target_percent, "exit_signal_target_percent", allow_zero=True),
        )


@dataclass(frozen=True, slots=True)
class PortfolioSpec:
    """Reviewed portfolio contract for deterministic target sizing."""

    portfolio_target: PortfolioTargetSpec = field(default_factory=PortfolioTargetSpec)
    position_sizing: PositionSizingSpec = field(default_factory=PositionSizingSpec)
    capital_allocation: CapitalAllocationSpec = field(default_factory=CapitalAllocationSpec)
    risk_limits: RiskLimitsSpec = field(default_factory=RiskLimitsSpec)
    multi_symbol_constraints: MultiSymbolConstraintsSpec = field(default_factory=MultiSymbolConstraintsSpec)
    max_gross_exposure: Decimal | None = None
    max_net_exposure: Decimal | None = None
    future_sector_asset_constraints: FutureSectorAssetConstraintsSpec = field(
        default_factory=FutureSectorAssetConstraintsSpec,
    )
    future_correlation_aware_allocation: FutureCorrelationAwareAllocationSpec = field(
        default_factory=FutureCorrelationAwareAllocationSpec,
    )
    signal_to_target_conversion: SignalToTargetConversionSpec = field(default_factory=SignalToTargetConversionSpec)
    portfolio_id: str = "portfolio:default"

    def __post_init__(self) -> None:
        object.__setattr__(self, "portfolio_target", _spec(self.portfolio_target, PortfolioTargetSpec, "portfolio_target"))
        object.__setattr__(self, "position_sizing", _spec(self.position_sizing, PositionSizingSpec, "position_sizing"))
        object.__setattr__(
            self,
            "capital_allocation",
            _spec(self.capital_allocation, CapitalAllocationSpec, "capital_allocation"),
        )
        object.__setattr__(self, "risk_limits", _spec(self.risk_limits, RiskLimitsSpec, "risk_limits"))
        object.__setattr__(
            self,
            "multi_symbol_constraints",
            _spec(self.multi_symbol_constraints, MultiSymbolConstraintsSpec, "multi_symbol_constraints"),
        )
        explicit_gross = _optional_positive_decimal(self.max_gross_exposure, "max_gross_exposure")
        explicit_net = _optional_non_negative_decimal(self.max_net_exposure, "max_net_exposure")
        risk_limits = self.risk_limits
        object.__setattr__(
            self,
            "max_gross_exposure",
            explicit_gross if explicit_gross is not None else risk_limits.max_gross_exposure,
        )
        object.__setattr__(
            self,
            "max_net_exposure",
            explicit_net if explicit_net is not None else risk_limits.max_net_exposure,
        )
        object.__setattr__(
            self,
            "future_sector_asset_constraints",
            _spec(
                self.future_sector_asset_constraints,
                FutureSectorAssetConstraintsSpec,
                "future_sector_asset_constraints",
            ),
        )
        object.__setattr__(
            self,
            "future_correlation_aware_allocation",
            _spec(
                self.future_correlation_aware_allocation,
                FutureCorrelationAwareAllocationSpec,
                "future_correlation_aware_allocation",
            ),
        )
        object.__setattr__(
            self,
            "signal_to_target_conversion",
            _spec(
                self.signal_to_target_conversion,
                SignalToTargetConversionSpec,
                "signal_to_target_conversion",
            ),
        )
        object.__setattr__(self, "portfolio_id", _text(self.portfolio_id, "portfolio_id"))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any] | None) -> "PortfolioSpec":
        if payload is None:
            return cls()
        active = dict(payload.get("portfolio", payload)) if isinstance(payload.get("portfolio", payload), Mapping) else {}
        if not active:
            raise PortfolioSpecError("portfolio specification must be a mapping")
        risk_payload = _mapping(active.get("risk_limits", {}), "risk_limits")
        return cls(
            portfolio_target=_portfolio_target(active.get("portfolio_target")),
            position_sizing=_position_sizing(active.get("position_sizing")),
            capital_allocation=_capital_allocation(active.get("capital_allocation")),
            risk_limits=_risk_limits(risk_payload),
            multi_symbol_constraints=_multi_symbol_constraints(active.get("multi_symbol_constraints")),
            max_gross_exposure=active.get("max_gross_exposure", risk_payload.get("max_gross_exposure")),
            max_net_exposure=active.get("max_net_exposure", risk_payload.get("max_net_exposure")),
            future_sector_asset_constraints=_future_sector(active.get("future_sector_asset_constraints")),
            future_correlation_aware_allocation=_future_correlation(
                active.get("future_correlation_aware_allocation"),
            ),
            signal_to_target_conversion=_signal_conversion(active.get("signal_to_target_conversion")),
            portfolio_id=str(active.get("portfolio_id", "portfolio:default")),
        )

    @classmethod
    def field_names(cls) -> tuple[str, ...]:
        return tuple(field.name for field in fields(cls))

    def to_dict(self) -> dict[str, Any]:
        payload = _json_ready(asdict(self))
        payload["max_gross_exposure"] = _json_ready(self.max_gross_exposure)
        payload["max_net_exposure"] = _json_ready(self.max_net_exposure)
        return payload


def _portfolio_target(value: Any) -> PortfolioTargetSpec:
    if value in (None, False):
        return PortfolioTargetSpec()
    payload = _mapping(value, "portfolio_target")
    return PortfolioTargetSpec(
        schema_version=payload.get("schema_version", "portfolio_target_v1"),
        target_id_prefix=payload.get("target_id_prefix", "portfolio-target"),
        deterministic_sort=tuple(payload.get("deterministic_sort", ("instrument_id", "source_signal_id", "target_id"))),
    )


def _position_sizing(value: Any) -> PositionSizingSpec:
    if value in (None, False):
        return PositionSizingSpec()
    payload = _mapping(value, "position_sizing")
    return PositionSizingSpec(
        method=payload.get("method", SizingMethod.FIXED_NOTIONAL.value),
        fixed_notional=payload.get("fixed_notional", "1000"),
        risk_per_trade=payload.get("risk_per_trade"),
        stop_distance=payload.get("stop_distance"),
        min_notional=payload.get("min_notional", "0"),
        allow_fractional=payload.get("allow_fractional", True),
    )


def _capital_allocation(value: Any) -> CapitalAllocationSpec:
    if value in (None, False):
        return CapitalAllocationSpec()
    payload = _mapping(value, "capital_allocation")
    return CapitalAllocationSpec(
        starting_equity=payload.get("starting_equity", "100000"),
        cash_buffer=payload.get("cash_buffer", "0"),
        insufficient_capital_policy=payload.get("insufficient_capital_policy", InsufficientCapitalPolicy.REJECT.value),
    )


def _risk_limits(value: Any) -> RiskLimitsSpec:
    if value in (None, False):
        return RiskLimitsSpec()
    payload = _mapping(value, "risk_limits")
    return RiskLimitsSpec(
        max_position_percent=payload.get("max_position_percent"),
        max_gross_exposure=payload.get("max_gross_exposure"),
        max_net_exposure=payload.get("max_net_exposure"),
    )


def _multi_symbol_constraints(value: Any) -> MultiSymbolConstraintsSpec:
    if value in (None, False):
        return MultiSymbolConstraintsSpec()
    payload = _mapping(value, "multi_symbol_constraints")
    return MultiSymbolConstraintsSpec(
        required_identifier=payload.get("required_identifier", "instrument_id"),
        max_active_instruments=payload.get("max_active_instruments"),
        max_target_percent_per_instrument=payload.get("max_target_percent_per_instrument"),
        allow_repeated_instrument_targets=payload.get("allow_repeated_instrument_targets", False),
    )


def _future_sector(value: Any) -> FutureSectorAssetConstraintsSpec:
    if value in (None, False):
        return FutureSectorAssetConstraintsSpec()
    payload = _mapping(value, "future_sector_asset_constraints")
    return FutureSectorAssetConstraintsSpec(
        mode=payload.get("mode", FutureConstraintMode.CONTRACT_ONLY.value),
        enabled=payload.get("enabled", False),
        rules=tuple(payload.get("rules", ())),
    )


def _future_correlation(value: Any) -> FutureCorrelationAwareAllocationSpec:
    if value in (None, False):
        return FutureCorrelationAwareAllocationSpec()
    payload = _mapping(value, "future_correlation_aware_allocation")
    return FutureCorrelationAwareAllocationSpec(
        mode=payload.get("mode", FutureConstraintMode.CONTRACT_ONLY.value),
        enabled=payload.get("enabled", False),
        inputs=tuple(payload.get("inputs", ())),
    )


def _signal_conversion(value: Any) -> SignalToTargetConversionSpec:
    if value in (None, False):
        return SignalToTargetConversionSpec()
    payload = _mapping(value, "signal_to_target_conversion")
    return SignalToTargetConversionSpec(
        mode=payload.get("mode", "entry_exit_to_target"),
        use_desired_exposure=payload.get("use_desired_exposure", True),
        use_confidence=payload.get("use_confidence", False),
        exit_signal_target_percent=payload.get("exit_signal_target_percent", "0"),
    )


def _spec(value: Any, cls: type[Any], field_name: str) -> Any:
    if isinstance(value, cls):
        return value
    if isinstance(value, Mapping):
        return cls(**value)
    raise PortfolioSpecError(f"{field_name} must be {cls.__name__} or mapping")


def _mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise PortfolioSpecError(f"{field_name} must be a mapping")
    return value


def _bool(value: Any, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip().lower() in {"true", "false"}:
        return value.strip().lower() == "true"
    raise PortfolioSpecError(f"{field_name} must be boolean")


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PortfolioSpecError(f"{field_name} must be a non-empty string")
    return value.strip()


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        raise PortfolioSpecError(f"{field_name} must be a positive integer")
    try:
        active = int(value)
    except (TypeError, ValueError) as exc:
        raise PortfolioSpecError(f"{field_name} must be a positive integer") from exc
    if active <= 0:
        raise PortfolioSpecError(f"{field_name} must be positive")
    return active


def _optional_positive_int(value: Any, field_name: str) -> int | None:
    if value in (None, ""):
        return None
    return _positive_int(value, field_name)


def _decimal(value: Any, field_name: str) -> Decimal:
    if isinstance(value, bool):
        raise PortfolioSpecError(f"{field_name} must be numeric")
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise PortfolioSpecError(f"{field_name} must be numeric") from exc


def _positive_decimal(value: Any, field_name: str) -> Decimal:
    active = _decimal(value, field_name)
    if active <= 0:
        raise PortfolioSpecError(f"{field_name} must be positive")
    return active


def _non_negative_decimal(value: Any, field_name: str) -> Decimal:
    active = _decimal(value, field_name)
    if active < 0:
        raise PortfolioSpecError(f"{field_name} must be non-negative")
    return active


def _optional_positive_decimal(value: Any, field_name: str) -> Decimal | None:
    if value in (None, ""):
        return None
    return _positive_decimal(value, field_name)


def _optional_non_negative_decimal(value: Any, field_name: str) -> Decimal | None:
    if value in (None, ""):
        return None
    return _non_negative_decimal(value, field_name)


def _fraction_decimal(value: Any, field_name: str, *, allow_zero: bool = False) -> Decimal:
    active = _non_negative_decimal(value, field_name) if allow_zero else _positive_decimal(value, field_name)
    if active > Decimal("1"):
        raise PortfolioSpecError(f"{field_name} must be no greater than 1")
    if not allow_zero and active == 0:
        raise PortfolioSpecError(f"{field_name} must be positive")
    return active


def _optional_fraction_decimal(value: Any, field_name: str) -> Decimal | None:
    if value in (None, ""):
        return None
    return _fraction_decimal(value, field_name)


def _string_tuple(value: Any, field_name: str) -> tuple[str, ...]:
    if isinstance(value, str):
        values = (value,)
    elif isinstance(value, Sequence) and not isinstance(value, bytes):
        values = tuple(str(item) for item in value)
    else:
        raise PortfolioSpecError(f"{field_name} must be a string sequence")
    if any(not item.strip() for item in values):
        raise PortfolioSpecError(f"{field_name} contains an empty value")
    return tuple(item.strip() for item in values)


def _sizing_method(value: Any) -> SizingMethod:
    if isinstance(value, SizingMethod):
        return value
    try:
        return SizingMethod(str(value))
    except ValueError as exc:
        raise PortfolioSpecError(f"unsupported sizing method: {value}") from exc


def _capital_policy(value: Any) -> InsufficientCapitalPolicy:
    if isinstance(value, InsufficientCapitalPolicy):
        return value
    try:
        return InsufficientCapitalPolicy(str(value))
    except ValueError as exc:
        raise PortfolioSpecError(f"unsupported insufficient capital policy: {value}") from exc


def _future_mode(value: Any) -> FutureConstraintMode:
    if isinstance(value, FutureConstraintMode):
        return value
    try:
        return FutureConstraintMode(str(value))
    except ValueError as exc:
        raise PortfolioSpecError(f"future constraint mode must be contract_only: {value}") from exc


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    return value
