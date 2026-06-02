"""Factor quality-flag representation and deterministic propagation."""

from __future__ import annotations

from collections.abc import Iterable
from enum import Enum
from typing import Any


class FactorQualityFlag(str, Enum):
    """Quality flags emitted by the factor compute SDK MVP."""

    INSUFFICIENT_WARMUP = "insufficient_warmup"
    MISSING_INPUT = "missing_input"
    INPUT_QUALITY = "input_quality"
    NORMALIZATION_UNAVAILABLE = "normalization_unavailable"
    NON_NUMERIC_VALUE = "non_numeric_value"


def normalize_quality_flags(flags: Iterable[Any] = ()) -> tuple[str, ...]:
    """Return quality flags as stable, unique strings in first-seen order."""
    normalized: list[str] = []
    seen: set[str] = set()
    for flag in flags:
        if flag is None:
            continue
        if isinstance(flag, FactorQualityFlag):
            text = flag.value
        else:
            text = str(flag).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        normalized.append(text)
    return tuple(normalized)


def merge_quality_flags(*groups: Iterable[Any]) -> tuple[str, ...]:
    """Merge several quality-flag collections deterministically."""
    merged: list[Any] = []
    for group in groups:
        merged.extend(group)
    return normalize_quality_flags(merged)


def propagate_input_quality_flags(
    input_flags: Iterable[Any],
    *,
    extra_flags: Iterable[Any] = (),
) -> tuple[str, ...]:
    """Propagate source quality flags and tag that inputs carried quality state."""
    normalized_input = normalize_quality_flags(input_flags)
    if not normalized_input:
        return normalize_quality_flags(extra_flags)
    return merge_quality_flags(
        (FactorQualityFlag.INPUT_QUALITY,),
        normalized_input,
        extra_flags,
    )
