"""Hard combination-count controls for bounded strategy grids."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


class GridLimitError(ValueError):
    """Raised when a grid is unbounded, empty, or exceeds its declared limit."""

    def __init__(
        self,
        message: str,
        *,
        count: int | None = None,
        max_combinations: int | None = None,
    ) -> None:
        self.count = count
        self.max_combinations = max_combinations
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class CombinationLimit:
    """Finite max-combination bound declared by a grid spec."""

    max_combinations: int

    def __post_init__(self) -> None:
        if isinstance(self.max_combinations, bool) or self.max_combinations <= 0:
            msg = "max_combinations must be a positive integer"
            raise GridLimitError(msg, max_combinations=self.max_combinations)

    def enforce(self, count: int, *, grid_id: str) -> None:
        """Raise if ``count`` exceeds the declared bound."""
        if count > self.max_combinations:
            msg = (
                f"grid {grid_id!r} expands to {count} combinations; "
                f"declared max_combinations is {self.max_combinations}"
            )
            raise GridLimitError(
                msg,
                count=count,
                max_combinations=self.max_combinations,
            )


def product_count(lengths: Iterable[int]) -> int:
    """Return a Cartesian-product count while rejecting empty dimensions."""
    count = 1
    saw_dimension = False
    for length in lengths:
        saw_dimension = True
        if isinstance(length, bool) or length <= 0:
            msg = "grid parameter dimensions must contain at least one value"
            raise GridLimitError(msg)
        count *= int(length)
    if not saw_dimension:
        msg = "grid parameter space must contain at least one dimension"
        raise GridLimitError(msg, count=0)
    return count
