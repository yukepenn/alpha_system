"""Train/validation, walk-forward, purge, and embargo utilities."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from typing import Any


class SplitError(ValueError):
    """Raised when an ML split declaration is invalid."""


@dataclass(frozen=True, slots=True)
class SplitWindow:
    """One train/validation split with explicit sample positions."""

    split_id: str
    train_indices: tuple[int, ...]
    validation_indices: tuple[int, ...]
    purge_gap: int = 0
    embargo_gap: int = 0

    def __post_init__(self) -> None:
        if not self.train_indices:
            raise SplitError("split requires at least one training index")
        if not self.validation_indices:
            raise SplitError("split requires at least one validation index")
        train = tuple(_non_negative_int(index, "train index") for index in self.train_indices)
        validation = tuple(
            _non_negative_int(index, "validation index") for index in self.validation_indices
        )
        if len(set(train).intersection(validation)) > 0:
            raise SplitError("train and validation indices must not overlap")
        object.__setattr__(self, "train_indices", train)
        object.__setattr__(self, "validation_indices", validation)
        object.__setattr__(self, "purge_gap", _non_negative_int(self.purge_gap, "purge_gap"))
        object.__setattr__(self, "embargo_gap", _non_negative_int(self.embargo_gap, "embargo_gap"))

    @property
    def train_end(self) -> int:
        return max(self.train_indices)

    @property
    def validation_start(self) -> int:
        return min(self.validation_indices)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["train_indices"] = list(self.train_indices)
        payload["validation_indices"] = list(self.validation_indices)
        return payload


def train_validation_split(
    sample_count: int,
    *,
    validation_fraction: float = 0.25,
    purge_gap: int = 0,
    embargo_gap: int = 0,
    split_id: str = "train_validation_0",
) -> SplitWindow:
    """Create one chronological train/validation split."""
    total = _positive_int(sample_count, "sample_count")
    if total < 2:
        raise SplitError("sample_count must be at least 2")
    validation_fraction = _fraction(validation_fraction, "validation_fraction")
    purge_gap = _non_negative_int(purge_gap, "purge_gap")
    embargo_gap = _non_negative_int(embargo_gap, "embargo_gap")
    validation_count = max(1, int(round(total * validation_fraction)))
    if validation_count >= total:
        validation_count = total - 1
    validation_start = total - validation_count
    train_indices = tuple(range(0, validation_start))
    validation_indices = tuple(range(validation_start, total))
    train_indices = apply_purge_embargo(
        train_indices,
        validation_indices,
        purge_gap=purge_gap,
        embargo_gap=embargo_gap,
    )
    return SplitWindow(
        split_id=split_id,
        train_indices=train_indices,
        validation_indices=validation_indices,
        purge_gap=purge_gap,
        embargo_gap=embargo_gap,
    )


def walk_forward_splits(
    sample_count: int,
    *,
    train_window: int,
    validation_window: int,
    step_size: int | None = None,
    purge_gap: int = 0,
    embargo_gap: int = 0,
) -> tuple[SplitWindow, ...]:
    """Create chronological walk-forward windows."""
    total = _positive_int(sample_count, "sample_count")
    train_window = _positive_int(train_window, "train_window")
    validation_window = _positive_int(validation_window, "validation_window")
    step = _positive_int(step_size or validation_window, "step_size")
    purge_gap = _non_negative_int(purge_gap, "purge_gap")
    embargo_gap = _non_negative_int(embargo_gap, "embargo_gap")
    windows: list[SplitWindow] = []
    start = 0
    split_number = 0
    while True:
        train_start = start
        train_end_exclusive = train_start + train_window
        validation_start = train_end_exclusive
        validation_end_exclusive = validation_start + validation_window
        if validation_end_exclusive > total:
            break
        raw_train = tuple(range(train_start, train_end_exclusive))
        validation = tuple(range(validation_start, validation_end_exclusive))
        train = apply_purge_embargo(
            raw_train,
            validation,
            purge_gap=purge_gap,
            embargo_gap=embargo_gap,
        )
        windows.append(
            SplitWindow(
                split_id=f"walk_forward_{split_number}",
                train_indices=train,
                validation_indices=validation,
                purge_gap=purge_gap,
                embargo_gap=embargo_gap,
            )
        )
        split_number += 1
        start += step
    if not windows:
        raise SplitError("walk-forward split produced no validation windows")
    return tuple(windows)


def apply_purge_embargo(
    train_indices: Sequence[int],
    validation_indices: Sequence[int],
    *,
    purge_gap: int = 0,
    embargo_gap: int = 0,
) -> tuple[int, ...]:
    """Remove training indices inside the validation purge/embargo exclusion zone."""
    train = tuple(_non_negative_int(index, "train index") for index in train_indices)
    validation = tuple(_non_negative_int(index, "validation index") for index in validation_indices)
    if not validation:
        raise SplitError("validation_indices must be non-empty")
    purge_gap = _non_negative_int(purge_gap, "purge_gap")
    embargo_gap = _non_negative_int(embargo_gap, "embargo_gap")
    validation_start = min(validation)
    validation_end = max(validation)
    lower_bound = validation_start - purge_gap
    upper_bound = validation_end + embargo_gap
    return tuple(index for index in train if not lower_bound <= index <= upper_bound)


def assert_chronological_split(window: SplitWindow) -> None:
    """Require all train samples to precede validation samples."""
    if max(window.train_indices) >= min(window.validation_indices):
        raise SplitError("training indices must precede validation indices")


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        raise SplitError(f"{field_name} must be a positive integer")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise SplitError(f"{field_name} must be a positive integer") from exc
    if number <= 0:
        raise SplitError(f"{field_name} must be positive")
    return number


def _non_negative_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        raise SplitError(f"{field_name} must be a non-negative integer")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise SplitError(f"{field_name} must be a non-negative integer") from exc
    if number < 0:
        raise SplitError(f"{field_name} must be non-negative")
    return number


def _fraction(value: Any, field_name: str) -> float:
    if isinstance(value, bool):
        raise SplitError(f"{field_name} must be a fraction between 0 and 1")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise SplitError(f"{field_name} must be a fraction between 0 and 1") from exc
    if not 0 < number < 1:
        raise SplitError(f"{field_name} must be between 0 and 1")
    return number
