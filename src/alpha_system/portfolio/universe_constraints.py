"""Universe-level portfolio exposure contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from decimal import Decimal, InvalidOperation
from typing import Any


CONTRACT_ONLY_MODE = "contract_only"


class UniverseConstraintError(ValueError):
    """Raised when universe-level portfolio constraints are invalid."""


@dataclass(frozen=True, slots=True, kw_only=True)
class UniverseExposureTarget:
    """Signed target exposure for one stable instrument identity."""

    instrument_id: str
    signed_notional: Decimal
    asset_class: str | None = None
    sector: str | None = None
    metadata: Mapping[str, Any] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "instrument_id", _text(self.instrument_id, "instrument_id"))
        object.__setattr__(self, "signed_notional", _decimal(self.signed_notional, "signed_notional"))
        if self.asset_class is not None:
            object.__setattr__(self, "asset_class", _text(self.asset_class, "asset_class"))
        if self.sector is not None:
            object.__setattr__(self, "sector", _text(self.sector, "sector"))
        object.__setattr__(self, "metadata", dict(self.metadata or {}))

    @property
    def gross_notional(self) -> Decimal:
        return abs(self.signed_notional)

    def with_signed_notional(self, signed_notional: Decimal) -> "UniverseExposureTarget":
        return replace(self, signed_notional=_decimal(signed_notional, "signed_notional"))

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


@dataclass(frozen=True, slots=True, kw_only=True)
class UniverseExposureConstraints:
    """Gross and net exposure limits across active universe symbols."""

    max_gross_exposure: Decimal | None = None
    max_net_exposure: Decimal | None = None
    required_identifier: str = "instrument_id"

    def __post_init__(self) -> None:
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
        object.__setattr__(self, "required_identifier", _text(self.required_identifier, "required_identifier"))
        if self.required_identifier != "instrument_id":
            raise UniverseConstraintError("universe exposure constraints require instrument_id identity")


@dataclass(frozen=True, slots=True, kw_only=True)
class UniverseExposureEvaluation:
    """Point-in-time exposure evaluation result."""

    equity: Decimal
    gross_notional: Decimal
    net_notional: Decimal
    max_gross_notional: Decimal | None
    max_net_notional: Decimal | None
    gross_limit_ok: bool
    net_limit_ok: bool
    by_asset_class: Mapping[str, Decimal]
    by_sector: Mapping[str, Decimal]
    breaches: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


@dataclass(frozen=True, slots=True, kw_only=True)
class UniverseExposureAdjustment:
    """Targets after deterministic gross/net scaling."""

    targets: tuple[UniverseExposureTarget, ...]
    evaluation: UniverseExposureEvaluation
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "targets": [target.to_dict() for target in self.targets],
            "evaluation": self.evaluation.to_dict(),
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class FutureSectorExposureConstraint:
    """Representation-only future sector exposure rule."""

    constraint_id: str
    sector: str
    max_exposure: Decimal | None = None
    mode: str = CONTRACT_ONLY_MODE
    enabled: bool = False
    metadata: Mapping[str, Any] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "constraint_id", _text(self.constraint_id, "constraint_id"))
        object.__setattr__(self, "sector", _text(self.sector, "sector"))
        object.__setattr__(self, "max_exposure", _optional_non_negative_decimal(self.max_exposure, "max_exposure"))
        object.__setattr__(self, "mode", _text(self.mode, "mode"))
        object.__setattr__(self, "enabled", _bool(self.enabled, "enabled"))
        _assert_contract_only(self.mode, self.enabled, "future sector exposure constraints")
        object.__setattr__(self, "metadata", dict(self.metadata or {}))

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


@dataclass(frozen=True, slots=True, kw_only=True)
class FutureAssetExposureConstraint:
    """Representation-only future asset-class exposure rule."""

    constraint_id: str
    asset_class: str
    max_exposure: Decimal | None = None
    mode: str = CONTRACT_ONLY_MODE
    enabled: bool = False
    metadata: Mapping[str, Any] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "constraint_id", _text(self.constraint_id, "constraint_id"))
        object.__setattr__(self, "asset_class", _text(self.asset_class, "asset_class"))
        object.__setattr__(self, "max_exposure", _optional_non_negative_decimal(self.max_exposure, "max_exposure"))
        object.__setattr__(self, "mode", _text(self.mode, "mode"))
        object.__setattr__(self, "enabled", _bool(self.enabled, "enabled"))
        _assert_contract_only(self.mode, self.enabled, "future asset exposure constraints")
        object.__setattr__(self, "metadata", dict(self.metadata or {}))

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


@dataclass(frozen=True, slots=True, kw_only=True)
class CorrelationAwareAllocationContract:
    """Representation-only contract for future correlation-aware allocation."""

    contract_id: str = "future_correlation_aware_allocation"
    mode: str = CONTRACT_ONLY_MODE
    enabled: bool = False
    required_inputs: tuple[str, ...] = ("future_correlation_matrix",)
    metadata: Mapping[str, Any] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "contract_id", _text(self.contract_id, "contract_id"))
        object.__setattr__(self, "mode", _text(self.mode, "mode"))
        object.__setattr__(self, "enabled", _bool(self.enabled, "enabled"))
        _assert_contract_only(self.mode, self.enabled, "future correlation-aware allocation")
        object.__setattr__(self, "required_inputs", _string_tuple(self.required_inputs, "required_inputs"))
        object.__setattr__(self, "metadata", dict(self.metadata or {}))

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


def evaluate_universe_exposure(
    targets: Sequence[UniverseExposureTarget | Mapping[str, Any]],
    *,
    equity: Decimal,
    constraints: UniverseExposureConstraints,
) -> UniverseExposureEvaluation:
    """Evaluate gross and net limits over stable instrument targets."""
    active_targets = _targets(targets)
    active_equity = _positive_decimal(equity, "equity")
    gross = sum((target.gross_notional for target in active_targets), Decimal("0"))
    net = sum((target.signed_notional for target in active_targets), Decimal("0"))
    max_gross = (
        None
        if constraints.max_gross_exposure is None
        else active_equity * constraints.max_gross_exposure
    )
    max_net = (
        None
        if constraints.max_net_exposure is None
        else active_equity * constraints.max_net_exposure
    )
    gross_ok = max_gross is None or gross <= max_gross
    net_ok = max_net is None or abs(net) <= max_net
    breaches: list[str] = []
    if not gross_ok:
        breaches.append("max_gross_exposure")
    if not net_ok:
        breaches.append("max_net_exposure")
    return UniverseExposureEvaluation(
        equity=active_equity,
        gross_notional=gross,
        net_notional=net,
        max_gross_notional=max_gross,
        max_net_notional=max_net,
        gross_limit_ok=gross_ok,
        net_limit_ok=net_ok,
        by_asset_class=_group_abs_exposure(active_targets, "asset_class"),
        by_sector=_group_abs_exposure(active_targets, "sector"),
        breaches=tuple(breaches),
    )


def apply_universe_exposure_constraints(
    targets: Sequence[UniverseExposureTarget | Mapping[str, Any]],
    *,
    equity: Decimal,
    constraints: UniverseExposureConstraints,
) -> UniverseExposureAdjustment:
    """Scale targets deterministically to satisfy gross then net limits."""
    active_targets = _targets(targets)
    active_equity = _positive_decimal(equity, "equity")
    reasons: list[str] = []

    if constraints.max_gross_exposure is not None:
        gross = sum((target.gross_notional for target in active_targets), Decimal("0"))
        max_gross = active_equity * constraints.max_gross_exposure
        if gross > max_gross and gross != 0:
            scale = max_gross / gross
            active_targets = tuple(
                target.with_signed_notional(target.signed_notional * scale)
                for target in active_targets
            )
            reasons.append("max_gross_exposure")

    if constraints.max_net_exposure is not None:
        net = sum((target.signed_notional for target in active_targets), Decimal("0"))
        max_net = active_equity * constraints.max_net_exposure
        if abs(net) > max_net and net != 0:
            scale = Decimal("0") if max_net == 0 else max_net / abs(net)
            active_targets = tuple(
                target.with_signed_notional(target.signed_notional * scale)
                for target in active_targets
            )
            active_targets = _trim_net_residual(active_targets, max_net)
            reasons.append("max_net_exposure")

    return UniverseExposureAdjustment(
        targets=active_targets,
        evaluation=evaluate_universe_exposure(
            active_targets,
            equity=active_equity,
            constraints=constraints,
        ),
        reasons=tuple(reasons),
    )


def _targets(values: Sequence[UniverseExposureTarget | Mapping[str, Any]]) -> tuple[UniverseExposureTarget, ...]:
    output: list[UniverseExposureTarget] = []
    seen: set[str] = set()
    for value in values:
        target = value if isinstance(value, UniverseExposureTarget) else UniverseExposureTarget(**value)
        if target.instrument_id in seen:
            raise UniverseConstraintError(f"duplicate instrument_id target: {target.instrument_id}")
        seen.add(target.instrument_id)
        output.append(target)
    return tuple(output)


def _group_abs_exposure(
    targets: Sequence[UniverseExposureTarget],
    attribute: str,
) -> dict[str, Decimal]:
    grouped: dict[str, Decimal] = {}
    for target in targets:
        key = getattr(target, attribute)
        if key is None:
            continue
        grouped[key] = grouped.get(key, Decimal("0")) + target.gross_notional
    return dict(sorted(grouped.items()))


def _trim_net_residual(
    targets: tuple[UniverseExposureTarget, ...],
    max_net: Decimal,
) -> tuple[UniverseExposureTarget, ...]:
    net = sum((target.signed_notional for target in targets), Decimal("0"))
    if abs(net) <= max_net:
        return targets
    direction = Decimal("1") if net > 0 else Decimal("-1")
    excess = abs(net) - max_net
    adjusted: list[UniverseExposureTarget] = []
    trimmed = False
    for target in targets:
        if not trimmed and target.signed_notional * direction > 0:
            adjusted.append(target.with_signed_notional(target.signed_notional - direction * excess))
            trimmed = True
            continue
        adjusted.append(target)
    return tuple(adjusted)


def _assert_contract_only(mode: str, enabled: bool, label: str) -> None:
    active_mode = _text(mode, "mode")
    active_enabled = _bool(enabled, "enabled")
    if active_mode != CONTRACT_ONLY_MODE:
        raise UniverseConstraintError(f"{label} are contract_only in this phase")
    if active_enabled:
        raise UniverseConstraintError(f"{label} are representation only in this phase")


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise UniverseConstraintError(f"{field_name} must be a non-empty string")
    return value.strip()


def _bool(value: Any, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip().lower() in {"true", "false"}:
        return value.strip().lower() == "true"
    raise UniverseConstraintError(f"{field_name} must be boolean")


def _decimal(value: Any, field_name: str) -> Decimal:
    if isinstance(value, bool):
        raise UniverseConstraintError(f"{field_name} must be numeric")
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise UniverseConstraintError(f"{field_name} must be numeric") from exc


def _positive_decimal(value: Any, field_name: str) -> Decimal:
    active = _decimal(value, field_name)
    if active <= 0:
        raise UniverseConstraintError(f"{field_name} must be positive")
    return active


def _optional_positive_decimal(value: Any, field_name: str) -> Decimal | None:
    if value in (None, ""):
        return None
    return _positive_decimal(value, field_name)


def _optional_non_negative_decimal(value: Any, field_name: str) -> Decimal | None:
    if value in (None, ""):
        return None
    active = _decimal(value, field_name)
    if active < 0:
        raise UniverseConstraintError(f"{field_name} must be non-negative")
    return active


def _string_tuple(value: Any, field_name: str) -> tuple[str, ...]:
    if isinstance(value, str):
        values = (value,)
    elif isinstance(value, Sequence) and not isinstance(value, bytes):
        values = tuple(str(item).strip() for item in value)
    else:
        raise UniverseConstraintError(f"{field_name} must be a string sequence")
    if any(not item for item in values):
        raise UniverseConstraintError(f"{field_name} contains an empty value")
    return values


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    return value
