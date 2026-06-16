"""Configuration for the Tier 1 reference 1-minute backtest engine."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


REFERENCE_ENGINE_VERSION = "reference_1min_v1"
NEXT_BAR_CONSERVATIVE = "next_bar_conservative"
SAME_BAR_ADVERSE_FIRST = "adverse_first"


class EngineConfigError(ValueError):
    """Raised when reference engine configuration is invalid."""


@dataclass(frozen=True, slots=True)
class CostModelConfig:
    """Deterministic cost hook used by the reference engine."""

    model: str = "fixed_bps"
    fixed_bps: Decimal = Decimal("1.0")
    minimum_cost: Decimal = Decimal("0")
    description: str = "conservative non-zero placeholder cost hook"

    def __post_init__(self) -> None:
        object.__setattr__(self, "model", _text(self.model, "cost_model.model"))
        if self.model != "fixed_bps":
            msg = "cost_model.model must be fixed_bps for ASV1-P15"
            raise EngineConfigError(msg)
        object.__setattr__(self, "fixed_bps", _non_negative_decimal(self.fixed_bps, "fixed_bps"))
        object.__setattr__(
            self,
            "minimum_cost",
            _non_negative_decimal(self.minimum_cost, "minimum_cost"),
        )
        object.__setattr__(
            self,
            "description",
            _text(self.description, "cost_model.description"),
        )

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any] | None) -> "CostModelConfig":
        if payload is None:
            return cls()
        return cls(
            model=payload.get("model", "fixed_bps"),
            fixed_bps=_decimal(payload.get("fixed_bps", "1.0"), "fixed_bps"),
            minimum_cost=_decimal(payload.get("minimum_cost", "0"), "minimum_cost"),
            description=str(
                payload.get(
                    "description",
                    "conservative non-zero placeholder cost hook",
                )
            ),
        )

    def cost_for_notional(self, notional: Decimal) -> Decimal:
        """Return deterministic absolute cost for one fill notional."""
        active_notional = abs(_decimal(notional, "notional"))
        bps_cost = active_notional * self.fixed_bps / Decimal("10000")
        return max(bps_cost, self.minimum_cost)

    def to_dict(self) -> dict[str, str]:
        return {
            "model": self.model,
            "fixed_bps": _decimal_text(self.fixed_bps),
            "minimum_cost": _decimal_text(self.minimum_cost),
            "description": self.description,
        }


def _resolve_cost_model(value: Any) -> Any:
    """Resolve the reference-engine cost model, keeping ``fixed_bps`` back-compat.

    A ``fixed_bps`` mapping (or ``None``) yields the legacy ``CostModelConfig``
    hook. Any other ``model`` (``composite`` / ``spread_cost`` /
    ``futures_fee_schedule`` / ...) is delegated to the single sanctioned
    ``costs.cost_model_from_mapping`` factory so the reference engine can charge
    per-contract futures fees and an explicit spread term without a second cost
    truth. Already-constructed cost-model objects (anything exposing
    ``cost_for_notional``) are passed through unchanged.
    """
    if value is None:
        return CostModelConfig()
    if isinstance(value, CostModelConfig):
        return value
    if callable(getattr(value, "cost_for_notional", None)):
        # Already a concrete cost model (e.g. CompositeCostModel from costs.py).
        return value
    if not isinstance(value, Mapping):
        msg = "cost_model must be a mapping or a cost-model object"
        raise EngineConfigError(msg)
    model = str(value.get("model", "fixed_bps")).strip()
    if model == "fixed_bps":
        return CostModelConfig.from_mapping(value)
    # Delegate richer cost models to the single sanctioned factory.
    from alpha_system.backtest.costs import CostModelError, cost_model_from_mapping

    try:
        return cost_model_from_mapping(value)
    except CostModelError as exc:
        raise EngineConfigError(str(exc)) from exc


@dataclass(frozen=True, slots=True)
class ReferenceEngineConfig:
    """Conservative Tier 1 reference execution configuration."""

    data_latency_seconds: int = 0
    execution_timing: str = NEXT_BAR_CONSERVATIVE
    same_bar_policy: str = SAME_BAR_ADVERSE_FIRST
    eod_flat: bool = False
    default_quantity: Decimal = Decimal("1")
    stop_loss_pct: Decimal | None = None
    target_profit_pct: Decimal | None = None
    cost_model: Any = field(default_factory=CostModelConfig)
    engine_version: str = REFERENCE_ENGINE_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "data_latency_seconds",
            _non_negative_int(self.data_latency_seconds, "data_latency_seconds"),
        )
        object.__setattr__(self, "execution_timing", _text(self.execution_timing, "execution_timing"))
        if self.execution_timing != NEXT_BAR_CONSERVATIVE:
            msg = "reference engine only supports next_bar_conservative execution"
            raise EngineConfigError(msg)
        object.__setattr__(self, "same_bar_policy", _text(self.same_bar_policy, "same_bar_policy"))
        if self.same_bar_policy != SAME_BAR_ADVERSE_FIRST:
            msg = "same_bar_policy must be adverse_first for the reference engine"
            raise EngineConfigError(msg)
        object.__setattr__(self, "eod_flat", _bool(self.eod_flat, "eod_flat"))
        object.__setattr__(
            self,
            "default_quantity",
            _positive_decimal(self.default_quantity, "default_quantity"),
        )
        object.__setattr__(
            self,
            "stop_loss_pct",
            _optional_positive_decimal(self.stop_loss_pct, "stop_loss_pct"),
        )
        object.__setattr__(
            self,
            "target_profit_pct",
            _optional_positive_decimal(self.target_profit_pct, "target_profit_pct"),
        )
        object.__setattr__(self, "cost_model", _resolve_cost_model(self.cost_model))
        object.__setattr__(self, "engine_version", _text(self.engine_version, "engine_version"))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any] | None) -> "ReferenceEngineConfig":
        if payload is None:
            return cls()
        return cls(
            data_latency_seconds=payload.get("data_latency_seconds", 0),
            execution_timing=payload.get("execution_timing", NEXT_BAR_CONSERVATIVE),
            same_bar_policy=payload.get("same_bar_policy", SAME_BAR_ADVERSE_FIRST),
            eod_flat=payload.get("eod_flat", False),
            default_quantity=_decimal(payload.get("default_quantity", "1"), "default_quantity"),
            stop_loss_pct=_optional_decimal(payload.get("stop_loss_pct"), "stop_loss_pct"),
            target_profit_pct=_optional_decimal(payload.get("target_profit_pct"), "target_profit_pct"),
            cost_model=_resolve_cost_model(payload.get("cost_model")),
            engine_version=str(payload.get("engine_version", REFERENCE_ENGINE_VERSION)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "data_latency_seconds": self.data_latency_seconds,
            "execution_timing": self.execution_timing,
            "same_bar_policy": self.same_bar_policy,
            "eod_flat": self.eod_flat,
            "default_quantity": _decimal_text(self.default_quantity),
            "stop_loss_pct": _optional_decimal_text(self.stop_loss_pct),
            "target_profit_pct": _optional_decimal_text(self.target_profit_pct),
            "cost_model": self.cost_model.to_dict(),
            "engine_version": self.engine_version,
        }


def load_reference_engine_config(path: str | Path) -> ReferenceEngineConfig:
    """Load a JSON or small YAML execution config."""
    config_path = Path(path).expanduser().resolve(strict=False)
    text = config_path.read_text(encoding="utf-8")
    if config_path.suffix.lower() == ".json":
        payload = json.loads(text)
    else:
        payload = _parse_simple_yaml(text)
    if not isinstance(payload, Mapping):
        msg = "reference engine config root must be a mapping"
        raise EngineConfigError(msg)
    return ReferenceEngineConfig.from_mapping(payload)


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    """Parse the small mapping-only YAML subset used by repo configs."""
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if ":" not in stripped:
            msg = f"unsupported YAML line: {raw_line!r}"
            raise EngineConfigError(msg)
        key, value = stripped.split(":", 1)
        key = key.strip()
        if not key:
            msg = f"empty YAML key in line: {raw_line!r}"
            raise EngineConfigError(msg)
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        value = value.strip()
        if value == "":
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = _yaml_scalar(value)
    return root


def _yaml_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none"}:
        return None
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        msg = f"{field_name} must be a non-empty string"
        raise EngineConfigError(msg)
    return value.strip()


def _bool(value: Any, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip().lower() in {"true", "false"}:
        return value.strip().lower() == "true"
    msg = f"{field_name} must be boolean"
    raise EngineConfigError(msg)


def _non_negative_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        msg = f"{field_name} must be a non-negative integer"
        raise EngineConfigError(msg)
    try:
        active = int(value)
    except (TypeError, ValueError) as exc:
        msg = f"{field_name} must be a non-negative integer"
        raise EngineConfigError(msg) from exc
    if active < 0:
        msg = f"{field_name} must be non-negative"
        raise EngineConfigError(msg)
    return active


def _decimal(value: Any, field_name: str = "value") -> Decimal:
    if isinstance(value, bool):
        msg = f"{field_name} must be numeric"
        raise EngineConfigError(msg)
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        msg = f"{field_name} must be numeric"
        raise EngineConfigError(msg) from exc


def _optional_decimal(value: Any, field_name: str) -> Decimal | None:
    if value in (None, ""):
        return None
    return _decimal(value, field_name)


def _non_negative_decimal(value: Any, field_name: str) -> Decimal:
    active = _decimal(value, field_name)
    if active < 0:
        msg = f"{field_name} must be non-negative"
        raise EngineConfigError(msg)
    return active


def _positive_decimal(value: Any, field_name: str) -> Decimal:
    active = _decimal(value, field_name)
    if active <= 0:
        msg = f"{field_name} must be positive"
        raise EngineConfigError(msg)
    return active


def _optional_positive_decimal(value: Any, field_name: str) -> Decimal | None:
    if value is None:
        return None
    return _positive_decimal(value, field_name)


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f")


def _optional_decimal_text(value: Decimal | None) -> str | None:
    return None if value is None else _decimal_text(value)
