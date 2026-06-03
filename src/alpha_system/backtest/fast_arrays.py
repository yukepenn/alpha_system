"""Array structures and conservative kernels for the fast backtest path.

The fast path is acceleration support only. These helpers intentionally keep
reference-engine containers and conservative semantics as the source of truth.
NumPy and Numba are optional because this repository's current dependency
contract does not require them.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from alpha_system.backtest.conservative_semantics import resolve_same_bar_stop_target

try:  # pragma: no cover - exercised only when optional dependency exists.
    import numpy as _np
except ModuleNotFoundError:  # pragma: no cover - current repo env has no numpy.
    _np = None

try:  # pragma: no cover - exercised only when optional dependency exists.
    from numba import njit as _numba_njit
except ModuleNotFoundError:  # pragma: no cover - current repo env has no numba.
    _numba_njit = None


STOP_TARGET_NONE = 0
STOP_TARGET_STOP = 1
STOP_TARGET_TARGET = 2


@dataclass(frozen=True, slots=True)
class FastArrayBackend:
    """Describe the available local array backend."""

    name: str
    numpy_available: bool
    numba_available: bool


@dataclass(frozen=True, slots=True)
class FastBarArrays:
    """Columnar 1-minute bar fields used by the accelerated loop."""

    bars: tuple[Mapping[str, Any], ...]
    bar_index: Sequence[int]
    open: Sequence[float]
    high: Sequence[float]
    low: Sequence[float]
    close: Sequence[float]
    bid: Sequence[float]
    ask: Sequence[float]
    backend: FastArrayBackend

    def __len__(self) -> int:
        return len(self.bars)

    def bar_at(self, offset: int) -> Mapping[str, Any]:
        return self.bars[offset]


@dataclass(frozen=True, slots=True)
class StopTargetEvent:
    """Fast-array stop/target outcome for one bar."""

    reason: str
    price: Decimal
    ambiguous: bool


def array_backend() -> FastArrayBackend:
    """Return the selected array backend without importing optional packages late."""

    if _np is not None and _numba_njit is not None:
        return FastArrayBackend(name="numpy_numba", numpy_available=True, numba_available=True)
    if _np is not None:
        return FastArrayBackend(name="numpy", numpy_available=True, numba_available=False)
    return FastArrayBackend(name="python", numpy_available=False, numba_available=False)


def build_bar_arrays(bars: Iterable[Mapping[str, Any]]) -> FastBarArrays:
    """Build deterministic columnar bar arrays from normalized bar mappings."""

    rows = tuple(bars)
    return FastBarArrays(
        bars=rows,
        bar_index=_array([int(row["bar_index"]) for row in rows], dtype="int64"),
        open=_array([float(Decimal(str(row["open"]))) for row in rows], dtype="float64"),
        high=_array([float(Decimal(str(row["high"]))) for row in rows], dtype="float64"),
        low=_array([float(Decimal(str(row["low"]))) for row in rows], dtype="float64"),
        close=_array([float(Decimal(str(row["close"]))) for row in rows], dtype="float64"),
        bid=_array([float(Decimal(str(row.get("bid", row["open"])))) for row in rows], dtype="float64"),
        ask=_array([float(Decimal(str(row.get("ask", row["open"])))) for row in rows], dtype="float64"),
        backend=array_backend(),
    )


def resolve_stop_target_event(
    *,
    direction: str,
    entry_price: Decimal,
    high: Decimal,
    low: Decimal,
    stop_loss_pct: Decimal | None,
    target_profit_pct: Decimal | None,
) -> StopTargetEvent | None:
    """Resolve a stop/target event with the public conservative semantics helper."""

    outcome = resolve_same_bar_stop_target(
        direction=direction,
        entry_price=entry_price,
        high=high,
        low=low,
        stop_loss_pct=stop_loss_pct,
        target_profit_pct=target_profit_pct,
    )
    if outcome is None:
        return None
    return StopTargetEvent(
        reason=outcome.reason,
        price=outcome.price,
        ambiguous=outcome.ambiguous,
    )


def stop_target_code(
    *,
    direction_code: int,
    entry_price: float,
    high: float,
    low: float,
    stop_loss_pct: float,
    target_profit_pct: float,
) -> tuple[int, float, int]:
    """Return a numeric stop/target event for optional compiled callers.

    Direction code is ``1`` for long and ``-1`` for short. A non-positive stop
    or target percentage means the corresponding rule is disabled.
    """

    return _compiled_stop_target_code(
        direction_code,
        entry_price,
        high,
        low,
        stop_loss_pct,
        target_profit_pct,
    )


def _array(values: list[Any], *, dtype: str) -> Sequence[Any]:
    if _np is None:
        return tuple(values)
    return _np.asarray(values, dtype=dtype)


def _stop_target_code_py(
    direction_code: int,
    entry_price: float,
    high: float,
    low: float,
    stop_loss_pct: float,
    target_profit_pct: float,
) -> tuple[int, float, int]:
    stop_enabled = stop_loss_pct > 0.0
    target_enabled = target_profit_pct > 0.0
    if not stop_enabled and not target_enabled:
        return STOP_TARGET_NONE, 0.0, 0

    stop_price = 0.0
    target_price = 0.0
    stop_hit = False
    target_hit = False
    if direction_code == 1:
        if stop_enabled:
            stop_price = entry_price * (1.0 - stop_loss_pct)
            stop_hit = low <= stop_price
        if target_enabled:
            target_price = entry_price * (1.0 + target_profit_pct)
            target_hit = high >= target_price
    elif direction_code == -1:
        if stop_enabled:
            stop_price = entry_price * (1.0 + stop_loss_pct)
            stop_hit = high >= stop_price
        if target_enabled:
            target_price = entry_price * (1.0 - target_profit_pct)
            target_hit = low <= target_price
    else:
        return STOP_TARGET_NONE, 0.0, 0

    if stop_hit:
        return STOP_TARGET_STOP, stop_price, 1 if target_hit else 0
    if target_hit:
        return STOP_TARGET_TARGET, target_price, 0
    return STOP_TARGET_NONE, 0.0, 0


_compiled_stop_target_code = (
    _numba_njit(_stop_target_code_py) if _numba_njit is not None else _stop_target_code_py
)
