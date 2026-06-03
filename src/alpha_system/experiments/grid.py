"""Finite strategy-grid expansion and object model."""

from __future__ import annotations

import itertools
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from alpha_system.experiments.limits import CombinationLimit, GridLimitError, product_count


GRID_TYPES: tuple[str, ...] = (
    "factor",
    "strategy",
    "execution",
    "risk",
    "management",
)

GRID_DISCIPLINE: tuple[str, ...] = (
    "factor_diagnostics",
    "simple_signal_grid",
    "simple_management_baseline",
    "survivor_strategy_management_hook",
    "finalist_execution_validation",
)

DISCIPLINE_PARAMETER_ORDER: tuple[str, ...] = (
    "factor",
    "strategy",
    "risk",
    "management",
    "execution",
)


class GridExpansionError(GridLimitError):
    """Raised when expansion cannot produce a bounded finite grid."""

    def __init__(
        self,
        message: str,
        *,
        rejected_configs: Sequence["RejectedGridConfig"] = (),
        count: int | None = None,
        max_combinations: int | None = None,
    ) -> None:
        self.rejected_configs = tuple(rejected_configs)
        super().__init__(message, count=count, max_combinations=max_combinations)


@dataclass(frozen=True, slots=True)
class GridParameter:
    """One finite grid dimension."""

    grid_type: str
    name: str
    values: tuple[Any, ...]

    @property
    def path(self) -> str:
        return f"{self.grid_type}.{self.name}"


@dataclass(frozen=True, slots=True)
class GridConfiguration:
    """One expanded grid configuration."""

    config_id: str
    ordinal: int
    parameters: Mapping[str, Any]

    def grouped_parameters(self) -> dict[str, dict[str, Any]]:
        grouped: dict[str, dict[str, Any]] = {}
        for path, value in sorted(self.parameters.items()):
            grid_type, name = path.split(".", 1)
            grouped.setdefault(grid_type, {})[name] = value
        return grouped


@dataclass(frozen=True, slots=True)
class RejectedGridConfig:
    """A rejected grid configuration with visible reason text."""

    config_id: str
    reason: str
    parameters: Mapping[str, Any]
    status: str = "rejected"

    def to_row(self, *, grid_run_id: str) -> dict[str, Any]:
        return {
            "grid_run_id": grid_run_id,
            "config_id": self.config_id,
            "status": self.status,
            "reason": self.reason,
            "parameters": dict(sorted(self.parameters.items())),
        }


@dataclass(frozen=True, slots=True)
class GridExpansion:
    """Expanded configurations plus deterministic expansion metadata."""

    grid_id: str
    parameters: tuple[GridParameter, ...]
    configurations: tuple[GridConfiguration, ...]
    combination_count: int
    max_combinations: int

    @property
    def parameter_paths(self) -> tuple[str, ...]:
        return tuple(parameter.path for parameter in self.parameters)


def ordered_parameters(parameter_space: Mapping[str, Mapping[str, Sequence[Any]]]) -> tuple[GridParameter, ...]:
    """Return grid dimensions in discipline order, then by parameter name."""
    parameters: list[GridParameter] = []
    unknown_types = tuple(sorted(set(parameter_space).difference(GRID_TYPES)))
    if unknown_types:
        msg = f"unsupported grid type(s): {', '.join(unknown_types)}"
        raise GridExpansionError(msg)

    for grid_type in DISCIPLINE_PARAMETER_ORDER:
        dimensions = parameter_space.get(grid_type, {})
        if not isinstance(dimensions, Mapping):
            msg = f"grid parameter group {grid_type!r} must be a mapping"
            raise GridExpansionError(msg)
        for name in sorted(dimensions):
            values = _finite_values(dimensions[name], f"{grid_type}.{name}")
            parameters.append(GridParameter(grid_type=grid_type, name=str(name), values=values))
    return tuple(parameters)


def count_grid_combinations(parameter_space: Mapping[str, Mapping[str, Sequence[Any]]]) -> int:
    """Count finite grid combinations without materializing them."""
    return product_count(len(parameter.values) for parameter in ordered_parameters(parameter_space))


def expand_grid(
    *,
    grid_id: str,
    parameter_space: Mapping[str, Mapping[str, Sequence[Any]]],
    max_combinations: int,
) -> GridExpansion:
    """Expand a finite grid and raise before materialization when it exceeds bounds."""
    parameters = ordered_parameters(parameter_space)
    count = product_count(len(parameter.values) for parameter in parameters)
    limit = CombinationLimit(max_combinations)
    try:
        limit.enforce(count, grid_id=grid_id)
    except GridLimitError as exc:
        rejection = RejectedGridConfig(
            config_id="grid",
            reason=str(exc),
            parameters={"combination_count": count, "max_combinations": max_combinations},
        )
        raise GridExpansionError(
            str(exc),
            rejected_configs=(rejection,),
            count=count,
            max_combinations=max_combinations,
        ) from exc

    configurations = []
    value_product = itertools.product(*(parameter.values for parameter in parameters))
    paths = tuple(parameter.path for parameter in parameters)
    for index, values in enumerate(value_product, start=1):
        configurations.append(
            GridConfiguration(
                config_id=f"cfg_{index:06d}",
                ordinal=index,
                parameters=dict(zip(paths, values, strict=True)),
            )
        )
    return GridExpansion(
        grid_id=grid_id,
        parameters=parameters,
        configurations=tuple(configurations),
        combination_count=count,
        max_combinations=max_combinations,
    )


def _finite_values(value: Any, path: str) -> tuple[Any, ...]:
    if isinstance(value, str) or isinstance(value, Mapping) or not isinstance(value, Sequence):
        msg = f"grid parameter {path!r} must be an explicit finite list"
        raise GridExpansionError(msg)
    values = tuple(value)
    if not values:
        msg = f"grid parameter {path!r} must contain at least one value"
        raise GridExpansionError(msg)
    return values
