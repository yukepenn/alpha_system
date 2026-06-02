"""Conservative slippage models for local reference research simulation."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol


ZERO = Decimal("0")


class SlippageModelError(ValueError):
    """Raised when a slippage model or input is invalid."""


class SupportsSlippage(Protocol):
    """Protocol for deterministic adverse slippage models."""

    def apply(self, fill: "SlippageInput") -> "SlippageResult":
        """Return the adverse price adjustment for one fill."""


@dataclass(frozen=True, slots=True)
class SlippageInput:
    """Inputs available before a conservative fill is finalized."""

    price: Decimal
    quantity: Decimal
    side: str
    bid: Decimal | None = None
    ask: Decimal | None = None
    spread: Decimal | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "price", _non_negative_decimal(self.price, "price"))
        object.__setattr__(self, "quantity", _positive_decimal(self.quantity, "quantity"))
        object.__setattr__(self, "side", _side(self.side))
        object.__setattr__(self, "bid", _optional_non_negative_decimal(self.bid, "bid"))
        object.__setattr__(self, "ask", _optional_non_negative_decimal(self.ask, "ask"))
        object.__setattr__(self, "spread", _optional_non_negative_decimal(self.spread, "spread"))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def sign(self) -> Decimal:
        return Decimal("1") if self.side == "buy" else Decimal("-1")

    @property
    def effective_spread(self) -> Decimal | None:
        if self.spread is not None:
            return self.spread
        if self.bid is None or self.ask is None:
            return None
        return max(self.ask - self.bid, ZERO)


@dataclass(frozen=True, slots=True)
class SlippageResult:
    """Adjusted price and absolute adverse adjustment."""

    base_price: Decimal
    adjusted_price: Decimal
    amount: Decimal
    components: tuple[tuple[str, Decimal], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "base_price", _non_negative_decimal(self.base_price, "base_price"))
        object.__setattr__(
            self,
            "adjusted_price",
            _non_negative_decimal(self.adjusted_price, "adjusted_price"),
        )
        object.__setattr__(self, "amount", _non_negative_decimal(self.amount, "amount"))
        object.__setattr__(
            self,
            "components",
            tuple((_text(name, "component"), _non_negative_decimal(amount, name)) for name, amount in self.components),
        )

    @property
    def total_cost_amount(self) -> Decimal:
        return self.amount

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_price": _decimal_text(self.base_price),
            "adjusted_price": _decimal_text(self.adjusted_price),
            "amount": _decimal_text(self.amount),
            "components": [
                {"name": name, "amount": _decimal_text(amount)} for name, amount in self.components
            ],
        }


@dataclass(frozen=True, slots=True)
class NoSlippageModel:
    """Explicit fixture-only no-slippage model."""

    fixture_only: bool = True

    def __post_init__(self) -> None:
        if self.fixture_only is not True:
            msg = "zero slippage is only allowed as an explicit fixture/test model"
            raise SlippageModelError(msg)

    def apply(self, fill: SlippageInput) -> SlippageResult:
        return SlippageResult(
            base_price=fill.price,
            adjusted_price=fill.price,
            amount=ZERO,
            components=(("explicit_fixture_zero_slippage", ZERO),),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"model": "none", "fixture_only": self.fixture_only}


@dataclass(frozen=True, slots=True)
class BpsSlippageModel:
    """Move the fill price adversely by a configured number of bps."""

    bps: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "bps", _non_negative_decimal(self.bps, "bps"))

    def apply(self, fill: SlippageInput) -> SlippageResult:
        amount = fill.price * self.bps / Decimal("10000")
        adjusted = fill.price + fill.sign * amount
        return SlippageResult(
            base_price=fill.price,
            adjusted_price=adjusted,
            amount=amount,
            components=(("slippage_bps", amount),),
        )

    def to_dict(self) -> dict[str, str]:
        return {"model": "bps", "bps": _decimal_text(self.bps)}


@dataclass(frozen=True, slots=True)
class SpreadSensitiveSlippageModel:
    """Scale adverse slippage by the observed bid/ask spread."""

    spread_fraction: Decimal = Decimal("0.25")
    fallback_bps: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "spread_fraction",
            _non_negative_decimal(self.spread_fraction, "spread_fraction"),
        )
        object.__setattr__(self, "fallback_bps", _non_negative_decimal(self.fallback_bps, "fallback_bps"))

    def apply(self, fill: SlippageInput) -> SlippageResult:
        spread = fill.effective_spread
        amount = (
            fill.price * self.fallback_bps / Decimal("10000")
            if spread is None
            else spread * self.spread_fraction
        )
        adjusted = fill.price + fill.sign * amount
        return SlippageResult(
            base_price=fill.price,
            adjusted_price=adjusted,
            amount=amount,
            components=(("spread_sensitive_slippage", amount),),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "model": "spread_sensitive",
            "spread_fraction": _decimal_text(self.spread_fraction),
            "fallback_bps": _decimal_text(self.fallback_bps),
        }


@dataclass(frozen=True, slots=True)
class AdverseSelectionProxyModel:
    """Call a configurable adverse-selection proxy and apply returned bps."""

    proxy: Callable[[SlippageInput], Decimal]
    name: str = "adverse_selection_proxy"

    def apply(self, fill: SlippageInput) -> SlippageResult:
        bps = _non_negative_decimal(self.proxy(fill), "adverse_selection_bps")
        amount = fill.price * bps / Decimal("10000")
        adjusted = fill.price + fill.sign * amount
        return SlippageResult(
            base_price=fill.price,
            adjusted_price=adjusted,
            amount=amount,
            components=((self.name, amount),),
        )

    def to_dict(self) -> dict[str, str]:
        return {"model": "adverse_selection_proxy", "name": self.name}


@dataclass(frozen=True, slots=True)
class CompositeSlippageModel:
    """Apply slippage components sequentially and conservatively."""

    models: tuple[SupportsSlippage, ...]
    fixture_zero_slippage: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "models", tuple(self.models))
        if not self.models:
            msg = "slippage model must contain at least one explicit component"
            raise SlippageModelError(msg)
        if self.total_is_zero and not self.fixture_zero_slippage:
            msg = "non-test execution configs must not silently have zero slippage"
            raise SlippageModelError(msg)

    @property
    def total_is_zero(self) -> bool:
        probe = SlippageInput(
            price=Decimal("100"),
            quantity=Decimal("1"),
            side="buy",
            bid=Decimal("99.99"),
            ask=Decimal("100.01"),
            spread=Decimal("0.02"),
        )
        return self.apply(probe).amount == ZERO

    def apply(self, fill: SlippageInput) -> SlippageResult:
        price = fill.price
        components: list[tuple[str, Decimal]] = []
        amount = ZERO
        for model in self.models:
            result = model.apply(
                SlippageInput(
                    price=price,
                    quantity=fill.quantity,
                    side=fill.side,
                    bid=fill.bid,
                    ask=fill.ask,
                    spread=fill.spread,
                    metadata=fill.metadata,
                )
            )
            price = result.adjusted_price
            amount += result.amount
            components.extend(result.components)
        return SlippageResult(
            base_price=fill.price,
            adjusted_price=price,
            amount=amount,
            components=tuple(components),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": "composite",
            "fixture_zero_slippage": self.fixture_zero_slippage,
            "components": [_model_to_dict(model) for model in self.models],
        }


def conservative_default_slippage_model() -> CompositeSlippageModel:
    """Return the non-zero conservative slippage default for research runs."""

    return CompositeSlippageModel(models=(BpsSlippageModel(Decimal("0.5")),))


def explicit_fixture_no_slippage_model() -> CompositeSlippageModel:
    """Return the only supported no-slippage model for fixture tests."""

    return CompositeSlippageModel(
        models=(NoSlippageModel(),),
        fixture_zero_slippage=True,
    )


def slippage_model_from_mapping(payload: Mapping[str, Any] | None) -> CompositeSlippageModel:
    """Parse a small deterministic slippage model mapping."""

    if payload is None:
        return conservative_default_slippage_model()
    model = str(payload.get("model", "composite")).strip()
    if model in {"none", "zero"}:
        if payload.get("fixture_only") is not True:
            msg = "zero slippage requires fixture_only: true"
            raise SlippageModelError(msg)
        return explicit_fixture_no_slippage_model()
    if model != "composite":
        return CompositeSlippageModel(models=(_slippage_component_from_mapping(payload),))
    raw_components = payload.get("components", ())
    if not isinstance(raw_components, list | tuple):
        msg = "composite slippage model requires a components list"
        raise SlippageModelError(msg)
    return CompositeSlippageModel(
        models=tuple(_slippage_component_from_mapping(component) for component in raw_components),
        fixture_zero_slippage=bool(payload.get("fixture_zero_slippage", False)),
    )


def _slippage_component_from_mapping(payload: Any) -> SupportsSlippage:
    if not isinstance(payload, Mapping):
        msg = "slippage component must be a mapping"
        raise SlippageModelError(msg)
    model = str(payload.get("model", "")).strip()
    if model == "bps":
        return BpsSlippageModel(_decimal(payload.get("bps", "0"), "bps"))
    if model == "spread_sensitive":
        return SpreadSensitiveSlippageModel(
            spread_fraction=_decimal(payload.get("spread_fraction", "0.25"), "spread_fraction"),
            fallback_bps=_decimal(payload.get("fallback_bps", "0"), "fallback_bps"),
        )
    if model in {"none", "zero"}:
        return NoSlippageModel(fixture_only=bool(payload.get("fixture_only", False)))
    msg = f"unsupported slippage component: {model}"
    raise SlippageModelError(msg)


def _model_to_dict(model: SupportsSlippage) -> dict[str, Any]:
    to_dict = getattr(model, "to_dict", None)
    if callable(to_dict):
        return dict(to_dict())
    return {"model": model.__class__.__name__}


def _side(value: str) -> str:
    active = _text(value, "side")
    if active not in {"buy", "sell"}:
        msg = "side must be buy or sell"
        raise SlippageModelError(msg)
    return active


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        msg = f"{field_name} must be a non-empty string"
        raise SlippageModelError(msg)
    return value.strip()


def _decimal(value: Any, field_name: str) -> Decimal:
    if isinstance(value, bool):
        msg = f"{field_name} must be numeric"
        raise SlippageModelError(msg)
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        msg = f"{field_name} must be numeric"
        raise SlippageModelError(msg) from exc


def _non_negative_decimal(value: Any, field_name: str) -> Decimal:
    active = _decimal(value, field_name)
    if active < ZERO:
        msg = f"{field_name} must be non-negative"
        raise SlippageModelError(msg)
    return active


def _optional_non_negative_decimal(value: Any, field_name: str) -> Decimal | None:
    if value is None:
        return None
    return _non_negative_decimal(value, field_name)


def _positive_decimal(value: Any, field_name: str) -> Decimal:
    active = _decimal(value, field_name)
    if active <= ZERO:
        msg = f"{field_name} must be positive"
        raise SlippageModelError(msg)
    return active


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f")
