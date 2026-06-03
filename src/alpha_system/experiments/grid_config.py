"""GridSpec parsing and validation for bounded strategy grids."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field, replace
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from alpha_system.experiments.grid import GRID_DISCIPLINE, GRID_TYPES, count_grid_combinations


GRID_ENGINE_VERSION = "strategy_grid_mvp_v1"


class GridConfigError(ValueError):
    """Raised when a grid configuration is incomplete or unsafe."""


@dataclass(frozen=True, slots=True)
class RejectionRule:
    """Declarative rule for surfacing intentionally rejected configurations."""

    when: Mapping[str, Any]
    reason: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "RejectionRule":
        when = payload.get("when")
        if not isinstance(when, Mapping) or not when:
            msg = "rejection rule requires a non-empty 'when' mapping"
            raise GridConfigError(msg)
        reason = _text(payload.get("reason"), "rejection rule reason")
        return cls(when=dict(when), reason=reason)

    def matches(self, parameters: Mapping[str, Any]) -> bool:
        return all(parameters.get(str(path)) == expected for path, expected in self.when.items())

    def to_dict(self) -> dict[str, Any]:
        return {"when": dict(self.when), "reason": self.reason}


@dataclass(frozen=True, slots=True)
class GridSpec:
    """Finite local grid experiment declaration."""

    grid_id: str
    strategy_version: str
    data_version: str
    factor_versions: Mapping[str, str]
    label_versions: Mapping[str, str]
    parameter_space: Mapping[str, Mapping[str, tuple[Any, ...]]]
    max_combinations: int
    strategy_id: str = "grid_fixture_strategy"
    strategy_spec: str | None = None
    management_spec: str | None = None
    portfolio_spec: str | None = None
    execution_config: str | None = None
    run_id: str | None = None
    engine: str = "reference"
    fast_path_features: tuple[str, ...] = ()
    reference_fallback: bool = True
    allow_fixture_zero_cost: bool = False
    output_dir: str | None = None
    registry_path: str | None = None
    manifest_path: str | None = None
    top_config_count: int = 3
    rejection_rules: tuple[RejectionRule, ...] = ()
    discipline: tuple[str, ...] = GRID_DISCIPLINE
    engine_version: str = GRID_ENGINE_VERSION
    initial_cash: Decimal = Decimal("100000")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "GridSpec":
        """Build and validate a grid spec from JSON-like data."""
        required = ("grid_id", "strategy_version", "data_version", "factor_versions", "label_versions")
        missing = tuple(field for field in required if _missing(payload.get(field)))
        if missing:
            msg = f"grid spec missing required fields: {', '.join(missing)}"
            raise GridConfigError(msg)

        parameter_space = _parameter_space(payload.get("parameter_space"))
        max_combinations = _positive_int(payload.get("max_combinations"), "max_combinations")
        combination_count = count_grid_combinations(parameter_space)
        if combination_count <= 0:
            msg = "grid spec must declare at least one finite parameter"
            raise GridConfigError(msg)

        factor_versions = _version_map(payload["factor_versions"], "factor_versions")
        label_versions = _version_map(payload["label_versions"], "label_versions")
        top_config_count = _positive_int(payload.get("top_config_count", 3), "top_config_count")
        engine = _optional_text(payload.get("engine"), "engine") or "reference"
        if engine not in {"reference", "fast"}:
            msg = "engine must be either 'reference' or 'fast'"
            raise GridConfigError(msg)

        return cls(
            grid_id=_text(payload["grid_id"], "grid_id"),
            strategy_id=_optional_text(payload.get("strategy_id"), "strategy_id")
            or "grid_fixture_strategy",
            strategy_version=_text(payload["strategy_version"], "strategy_version"),
            data_version=_text(payload["data_version"], "data_version"),
            factor_versions=factor_versions,
            label_versions=label_versions,
            parameter_space=parameter_space,
            max_combinations=max_combinations,
            strategy_spec=_optional_text(payload.get("strategy_spec"), "strategy_spec"),
            management_spec=_optional_text(payload.get("management_spec"), "management_spec"),
            portfolio_spec=_optional_text(payload.get("portfolio_spec"), "portfolio_spec"),
            execution_config=_optional_text(payload.get("execution_config"), "execution_config"),
            run_id=_optional_text(payload.get("run_id"), "run_id"),
            engine=engine,
            fast_path_features=_text_tuple(payload.get("fast_path_features", ()), "fast_path_features"),
            reference_fallback=_bool(payload.get("reference_fallback", True), "reference_fallback"),
            allow_fixture_zero_cost=_bool(
                payload.get("allow_fixture_zero_cost", False),
                "allow_fixture_zero_cost",
            ),
            output_dir=_optional_text(payload.get("output_dir"), "output_dir"),
            registry_path=_optional_text(payload.get("registry_path"), "registry_path"),
            manifest_path=_optional_text(payload.get("manifest_path"), "manifest_path"),
            top_config_count=top_config_count,
            rejection_rules=tuple(
                RejectionRule.from_mapping(rule) for rule in payload.get("rejection_rules", ())
            ),
            discipline=_discipline(payload.get("discipline")),
            engine_version=_optional_text(payload.get("engine_version"), "engine_version")
            or GRID_ENGINE_VERSION,
            initial_cash=_positive_decimal(payload.get("initial_cash", "100000"), "initial_cash"),
        )

    def with_overrides(self, **overrides: Any) -> "GridSpec":
        """Return a spec with non-None CLI overrides applied."""
        updates = {key: value for key, value in overrides.items() if value is not None}
        if "engine" in updates and updates["engine"] not in {"reference", "fast"}:
            msg = "engine must be either 'reference' or 'fast'"
            raise GridConfigError(msg)
        if "factor_versions" in updates:
            updates["factor_versions"] = _version_map(updates["factor_versions"], "factor_versions")
        if "label_versions" in updates:
            updates["label_versions"] = _version_map(updates["label_versions"], "label_versions")
        if "reference_fallback" in updates:
            updates["reference_fallback"] = _bool(updates["reference_fallback"], "reference_fallback")
        return replace(self, **updates)

    @property
    def combination_count(self) -> int:
        return count_grid_combinations(self.parameter_space)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["factor_versions"] = dict(self.factor_versions)
        payload["label_versions"] = dict(self.label_versions)
        payload["parameter_space"] = {
            grid_type: {name: list(values) for name, values in dimensions.items()}
            for grid_type, dimensions in self.parameter_space.items()
        }
        payload["fast_path_features"] = list(self.fast_path_features)
        payload["rejection_rules"] = [rule.to_dict() for rule in self.rejection_rules]
        payload["discipline"] = list(self.discipline)
        payload["initial_cash"] = str(self.initial_cash)
        return payload


def load_grid_spec(path: str | Path) -> GridSpec:
    """Load a JSON grid spec from disk."""
    config_path = Path(path).expanduser().resolve(strict=False)
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        msg = "grid config root must be a JSON object"
        raise GridConfigError(msg)
    return GridSpec.from_mapping(payload)


def parse_version_overrides(values: Sequence[str] | None, *, field_name: str) -> dict[str, str] | None:
    """Parse repeated ``name=version`` CLI arguments."""
    if not values:
        return None
    versions: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            msg = f"{field_name} values must use name=version"
            raise GridConfigError(msg)
        name, version = value.split("=", 1)
        name = name.strip()
        version = version.strip()
        if not name or not version:
            msg = f"{field_name} values must include non-empty name and version"
            raise GridConfigError(msg)
        existing = versions.get(name)
        if existing is not None and existing != version:
            msg = f"conflicting version reference for {name}"
            raise GridConfigError(msg)
        versions[name] = version
    return versions


def _parameter_space(value: Any) -> dict[str, dict[str, tuple[Any, ...]]]:
    if not isinstance(value, Mapping) or not value:
        msg = "parameter_space must be a non-empty mapping"
        raise GridConfigError(msg)
    unknown = tuple(sorted(set(str(key) for key in value).difference(GRID_TYPES)))
    if unknown:
        msg = f"unsupported grid type(s): {', '.join(unknown)}"
        raise GridConfigError(msg)
    normalized: dict[str, dict[str, tuple[Any, ...]]] = {}
    for grid_type in GRID_TYPES:
        dimensions = value.get(grid_type, {})
        if dimensions in ({}, None):
            continue
        if not isinstance(dimensions, Mapping):
            msg = f"parameter_space.{grid_type} must be a mapping"
            raise GridConfigError(msg)
        normalized[grid_type] = {}
        for name, raw_values in dimensions.items():
            if isinstance(raw_values, str) or isinstance(raw_values, Mapping) or not isinstance(raw_values, Sequence):
                msg = f"parameter_space.{grid_type}.{name} must be an explicit finite list"
                raise GridConfigError(msg)
            values = tuple(raw_values)
            if not values:
                msg = f"parameter_space.{grid_type}.{name} must contain at least one value"
                raise GridConfigError(msg)
            normalized[grid_type][str(name)] = values
    if not any(normalized.values()):
        msg = "parameter_space must contain at least one finite parameter"
        raise GridConfigError(msg)
    return normalized


def _version_map(value: Any, field_name: str) -> dict[str, str]:
    if not isinstance(value, Mapping) or not value:
        msg = f"{field_name} must be a non-empty mapping"
        raise GridConfigError(msg)
    output: dict[str, str] = {}
    for name, version in value.items():
        output[_text(name, f"{field_name} key")] = _text(version, f"{field_name} value")
    return output


def _discipline(value: Any) -> tuple[str, ...]:
    if value is None:
        return GRID_DISCIPLINE
    discipline = _text_tuple(value, "discipline")
    if discipline != GRID_DISCIPLINE:
        msg = "discipline must match the required Grid Engine order"
        raise GridConfigError(msg)
    return discipline


def _text_tuple(value: Any, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (_text(value, field_name),)
    if not isinstance(value, Sequence):
        msg = f"{field_name} must be a string or sequence of strings"
        raise GridConfigError(msg)
    return tuple(_text(item, field_name) for item in value)


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        msg = f"{field_name} must be a non-empty string"
        raise GridConfigError(msg)
    return value.strip()


def _optional_text(value: Any, field_name: str) -> str | None:
    if value in (None, ""):
        return None
    return _text(value, field_name)


def _bool(value: Any, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip().lower() in {"true", "false"}:
        return value.strip().lower() == "true"
    msg = f"{field_name} must be boolean"
    raise GridConfigError(msg)


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        msg = f"{field_name} must be a positive integer"
        raise GridConfigError(msg)
    try:
        active = int(value)
    except (TypeError, ValueError) as exc:
        msg = f"{field_name} must be a positive integer"
        raise GridConfigError(msg) from exc
    if active <= 0:
        msg = f"{field_name} must be positive"
        raise GridConfigError(msg)
    return active


def _positive_decimal(value: Any, field_name: str) -> Decimal:
    if isinstance(value, bool):
        msg = f"{field_name} must be numeric"
        raise GridConfigError(msg)
    try:
        active = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        msg = f"{field_name} must be numeric"
        raise GridConfigError(msg) from exc
    if active <= 0:
        msg = f"{field_name} must be positive"
        raise GridConfigError(msg)
    return active


def _missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, Mapping | Sequence):
        return len(value) == 0
    return False
