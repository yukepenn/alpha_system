"""Deterministic research cost models for conservative reference backtests."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol


ZERO = Decimal("0")


class CostModelError(ValueError):
    """Raised when a cost model or cost input is not conservative enough."""


class SupportsCost(Protocol):
    """Protocol for deterministic fill-level cost models."""

    def cost_for_fill(self, fill: "CostInput") -> "CostBreakdown":
        """Return an absolute non-negative cost breakdown for one fill."""


@dataclass(frozen=True, slots=True)
class CostInput:
    """Inputs available when calculating local research execution costs."""

    price: Decimal
    quantity: Decimal
    side: str
    bid: Decimal | None = None
    ask: Decimal | None = None
    spread: Decimal | None = None
    multiplier: Decimal = Decimal("1")
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "price", _non_negative_decimal(self.price, "price"))
        object.__setattr__(self, "quantity", _positive_decimal(self.quantity, "quantity"))
        object.__setattr__(self, "side", _side(self.side))
        object.__setattr__(self, "bid", _optional_non_negative_decimal(self.bid, "bid"))
        object.__setattr__(self, "ask", _optional_non_negative_decimal(self.ask, "ask"))
        object.__setattr__(self, "spread", _optional_non_negative_decimal(self.spread, "spread"))
        object.__setattr__(self, "multiplier", _positive_decimal(self.multiplier, "multiplier"))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def notional(self) -> Decimal:
        return self.price * self.quantity * self.multiplier

    @property
    def effective_spread(self) -> Decimal | None:
        if self.spread is not None:
            return self.spread
        if self.bid is None or self.ask is None:
            return None
        return max(self.ask - self.bid, ZERO)


@dataclass(frozen=True, slots=True)
class CostComponent:
    """One named absolute cost component."""

    name: str
    amount: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _text(self.name, "component name"))
        object.__setattr__(self, "amount", _non_negative_decimal(self.amount, self.name))

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "amount": _decimal_text(self.amount)}


@dataclass(frozen=True, slots=True)
class CostBreakdown:
    """Stable cost breakdown with an explicit total."""

    components: tuple[CostComponent, ...] = ()

    @property
    def total(self) -> Decimal:
        return sum((component.amount for component in self.components), ZERO)

    def with_component(self, name: str, amount: Decimal) -> "CostBreakdown":
        component = CostComponent(name=name, amount=amount)
        return replace(self, components=(*self.components, component))

    def merged(self, other: "CostBreakdown") -> "CostBreakdown":
        return replace(self, components=(*self.components, *other.components))

    def amount_for(self, name: str) -> Decimal:
        return sum((component.amount for component in self.components if component.name == name), ZERO)

    def to_dict(self) -> dict[str, Any]:
        return {
            "components": [component.to_dict() for component in self.components],
            "total": _decimal_text(self.total),
        }


@dataclass(frozen=True, slots=True)
class FixedCommissionCost:
    """Apply one fixed commission per fill."""

    amount: Decimal
    name: str = "fixed_commission"

    def __post_init__(self) -> None:
        object.__setattr__(self, "amount", _non_negative_decimal(self.amount, "amount"))
        object.__setattr__(self, "name", _text(self.name, "name"))

    def cost_for_fill(self, fill: CostInput) -> CostBreakdown:
        return CostBreakdown().with_component(self.name, self.amount)

    def to_dict(self) -> dict[str, str]:
        return {"model": "fixed_commission", "amount": _decimal_text(self.amount)}


@dataclass(frozen=True, slots=True)
class PerUnitCommissionCost:
    """Apply a per-share or per-contract commission."""

    amount_per_unit: Decimal
    name: str = "per_unit_commission"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "amount_per_unit",
            _non_negative_decimal(self.amount_per_unit, "amount_per_unit"),
        )
        object.__setattr__(self, "name", _text(self.name, "name"))

    def cost_for_fill(self, fill: CostInput) -> CostBreakdown:
        return CostBreakdown().with_component(self.name, self.amount_per_unit * fill.quantity)

    def to_dict(self) -> dict[str, str]:
        return {
            "model": "per_unit_commission",
            "amount_per_unit": _decimal_text(self.amount_per_unit),
        }


@dataclass(frozen=True, slots=True)
class BpsCost:
    """Apply an absolute cost in basis points of fill notional."""

    bps: Decimal
    minimum_cost: Decimal = ZERO
    name: str = "bps_cost"

    def __post_init__(self) -> None:
        object.__setattr__(self, "bps", _non_negative_decimal(self.bps, "bps"))
        object.__setattr__(
            self,
            "minimum_cost",
            _non_negative_decimal(self.minimum_cost, "minimum_cost"),
        )
        object.__setattr__(self, "name", _text(self.name, "name"))

    def cost_for_fill(self, fill: CostInput) -> CostBreakdown:
        amount = fill.notional * self.bps / Decimal("10000")
        return CostBreakdown().with_component(self.name, max(amount, self.minimum_cost))

    def to_dict(self) -> dict[str, str]:
        return {
            "model": "bps_cost",
            "bps": _decimal_text(self.bps),
            "minimum_cost": _decimal_text(self.minimum_cost),
        }


@dataclass(frozen=True, slots=True)
class SpreadCost:
    """Charge half-spread or full-spread as an explicit conservative cost."""

    assumption: str = "half_spread"
    name: str = "spread_cost"

    def __post_init__(self) -> None:
        assumption = _text(self.assumption, "assumption")
        if assumption not in {"half_spread", "full_spread"}:
            msg = "spread assumption must be half_spread or full_spread"
            raise CostModelError(msg)
        object.__setattr__(self, "assumption", assumption)
        object.__setattr__(self, "name", _text(self.name, "name"))

    def cost_for_fill(self, fill: CostInput) -> CostBreakdown:
        spread = fill.effective_spread
        if spread is None:
            return CostBreakdown().with_component(self.name, ZERO)
        multiplier = Decimal("0.5") if self.assumption == "half_spread" else Decimal("1")
        return CostBreakdown().with_component(
            self.name,
            spread * multiplier * fill.quantity * fill.multiplier,
        )

    def to_dict(self) -> dict[str, str]:
        return {"model": "spread_cost", "assumption": self.assumption}


@dataclass(frozen=True, slots=True)
class ExplicitZeroCostModel:
    """Explicit fixture-only zero-cost model for tiny correctness fixtures."""

    fixture_only: bool = True
    purpose: str = "synthetic fixture correctness only"

    def __post_init__(self) -> None:
        if self.fixture_only is not True:
            msg = "zero cost is only allowed for explicit fixture/test configurations"
            raise CostModelError(msg)
        purpose = _text(self.purpose, "purpose").lower()
        if "fixture" not in purpose and "test" not in purpose:
            msg = "zero cost purpose must explicitly identify fixture or test use"
            raise CostModelError(msg)
        object.__setattr__(self, "purpose", purpose)

    def cost_for_fill(self, fill: CostInput) -> CostBreakdown:
        return CostBreakdown().with_component("explicit_fixture_zero_cost", ZERO)

    def cost_for_notional(self, notional: Decimal) -> Decimal:
        _non_negative_decimal(abs(_decimal(notional, "notional")), "notional")
        return ZERO

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": "zero_cost",
            "fixture_only": self.fixture_only,
            "purpose": self.purpose,
        }


@dataclass(frozen=True, slots=True)
class CompositeCostModel:
    """Compose fill-level costs and expose reference-engine compatibility."""

    models: tuple[SupportsCost, ...]
    reference_quantity: Decimal = Decimal("1")
    reference_multiplier: Decimal = Decimal("1")
    fixture_zero_cost: bool = False

    def __post_init__(self) -> None:
        if not self.models:
            msg = "cost model must contain at least one explicit component"
            raise CostModelError(msg)
        object.__setattr__(
            self,
            "reference_quantity",
            _positive_decimal(self.reference_quantity, "reference_quantity"),
        )
        object.__setattr__(
            self,
            "reference_multiplier",
            _positive_decimal(self.reference_multiplier, "reference_multiplier"),
        )
        object.__setattr__(self, "models", tuple(self.models))
        if self.total_is_zero and not self.fixture_zero_cost:
            msg = "non-test execution configs must not silently be zero-cost"
            raise CostModelError(msg)

    @property
    def total_is_zero(self) -> bool:
        probe = CostInput(
            price=Decimal("100"),
            quantity=self.reference_quantity,
            side="buy",
            bid=Decimal("99.99"),
            ask=Decimal("100.01"),
            spread=Decimal("0.02"),
            multiplier=self.reference_multiplier,
        )
        return self.cost_for_fill(probe).total == ZERO

    def with_reference_quantity(self, quantity: Decimal) -> "CompositeCostModel":
        return replace(self, reference_quantity=_positive_decimal(quantity, "quantity"))

    def cost_for_fill(self, fill: CostInput) -> CostBreakdown:
        breakdown = CostBreakdown()
        for model in self.models:
            breakdown = breakdown.merged(model.cost_for_fill(fill))
        return breakdown

    def cost_for_notional(self, notional: Decimal) -> Decimal:
        """Compatibility hook consumed by the P15 reference fill path."""
        active_notional = abs(_decimal(notional, "notional"))
        price = active_notional / (self.reference_quantity * self.reference_multiplier)
        fill = CostInput(
            price=price,
            quantity=self.reference_quantity,
            side="buy",
            multiplier=self.reference_multiplier,
        )
        return self.cost_for_fill(fill).total

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": "composite",
            "reference_quantity": _decimal_text(self.reference_quantity),
            "reference_multiplier": _decimal_text(self.reference_multiplier),
            "fixture_zero_cost": self.fixture_zero_cost,
            "components": [_model_to_dict(model) for model in self.models],
        }


def conservative_default_cost_model(*, reference_quantity: Decimal = Decimal("1")) -> CompositeCostModel:
    """Return the non-zero conservative default for non-test research runs."""

    return CompositeCostModel(
        models=(BpsCost(Decimal("1.0")),),
        reference_quantity=reference_quantity,
    )


def explicit_fixture_zero_cost_model() -> CompositeCostModel:
    """Return the only supported zero-cost configuration shape."""

    return CompositeCostModel(
        models=(ExplicitZeroCostModel(),),
        fixture_zero_cost=True,
    )


def cost_model_from_mapping(payload: Mapping[str, Any] | None) -> CompositeCostModel:
    """Parse a small deterministic cost-model mapping."""

    if payload is None:
        return conservative_default_cost_model()
    model = str(payload.get("model", "composite")).strip()
    if model == "zero_cost":
        if payload.get("fixture_only") is not True:
            msg = "zero_cost requires fixture_only: true"
            raise CostModelError(msg)
        return explicit_fixture_zero_cost_model()
    if model != "composite":
        return CompositeCostModel(models=(_cost_component_from_mapping(payload),))
    components_payload = payload.get("components", ())
    if not isinstance(components_payload, Iterable) or isinstance(components_payload, str):
        msg = "composite cost model requires a components list"
        raise CostModelError(msg)
    components = tuple(_cost_component_from_mapping(component) for component in components_payload)
    return CompositeCostModel(
        models=components,
        reference_quantity=_decimal(payload.get("reference_quantity", "1"), "reference_quantity"),
        reference_multiplier=_decimal(payload.get("reference_multiplier", "1"), "reference_multiplier"),
        fixture_zero_cost=bool(payload.get("fixture_zero_cost", False)),
    )


def _cost_component_from_mapping(payload: Any) -> SupportsCost:
    if not isinstance(payload, Mapping):
        msg = "cost model component must be a mapping"
        raise CostModelError(msg)
    model = str(payload.get("model", "")).strip()
    if model == "fixed_commission":
        return FixedCommissionCost(amount=_decimal(payload.get("amount", "0"), "amount"))
    if model == "per_unit_commission":
        return PerUnitCommissionCost(
            amount_per_unit=_decimal(payload.get("amount_per_unit", "0"), "amount_per_unit")
        )
    if model in {"bps_cost", "fixed_bps"}:
        return BpsCost(
            bps=_decimal(payload.get("bps", payload.get("fixed_bps", "0")), "bps"),
            minimum_cost=_decimal(payload.get("minimum_cost", "0"), "minimum_cost"),
        )
    if model == "spread_cost":
        return SpreadCost(assumption=str(payload.get("assumption", "half_spread")))
    if model == "zero_cost":
        return ExplicitZeroCostModel(
            fixture_only=bool(payload.get("fixture_only", False)),
            purpose=str(payload.get("purpose", "synthetic fixture correctness only")),
        )
    msg = f"unsupported cost model component: {model}"
    raise CostModelError(msg)


def _model_to_dict(model: SupportsCost) -> dict[str, Any]:
    to_dict = getattr(model, "to_dict", None)
    if callable(to_dict):
        return dict(to_dict())
    return {"model": model.__class__.__name__}


def _side(value: str) -> str:
    active = _text(value, "side")
    if active not in {"buy", "sell"}:
        msg = "side must be buy or sell"
        raise CostModelError(msg)
    return active


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        msg = f"{field_name} must be a non-empty string"
        raise CostModelError(msg)
    return value.strip()


def _decimal(value: Any, field_name: str) -> Decimal:
    if isinstance(value, bool):
        msg = f"{field_name} must be numeric"
        raise CostModelError(msg)
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        msg = f"{field_name} must be numeric"
        raise CostModelError(msg) from exc


def _non_negative_decimal(value: Any, field_name: str) -> Decimal:
    active = _decimal(value, field_name)
    if active < ZERO:
        msg = f"{field_name} must be non-negative"
        raise CostModelError(msg)
    return active


def _optional_non_negative_decimal(value: Any, field_name: str) -> Decimal | None:
    if value is None:
        return None
    return _non_negative_decimal(value, field_name)


def _positive_decimal(value: Any, field_name: str) -> Decimal:
    active = _decimal(value, field_name)
    if active <= ZERO:
        msg = f"{field_name} must be positive"
        raise CostModelError(msg)
    return active


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f")
