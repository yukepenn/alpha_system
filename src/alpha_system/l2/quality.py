"""Quality-flag helpers for fixture-only L2-derived features."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


L2_FEATURE_QUALITY_PREFIX = "l2_feature_"

L2_FEATURE_MISSING_SIDE = f"{L2_FEATURE_QUALITY_PREFIX}missing_side"
L2_FEATURE_MISSING_LEVEL = f"{L2_FEATURE_QUALITY_PREFIX}missing_book_level"
L2_FEATURE_MISSING_ORDER_COUNT = f"{L2_FEATURE_QUALITY_PREFIX}missing_order_count"
L2_FEATURE_ZERO_DENOMINATOR = f"{L2_FEATURE_QUALITY_PREFIX}zero_denominator"
L2_FEATURE_INCOMPLETE_TOP_OF_BOOK = (
    f"{L2_FEATURE_QUALITY_PREFIX}incomplete_top_of_book"
)
L2_FEATURE_FIXTURE_ONLY = f"{L2_FEATURE_QUALITY_PREFIX}fixture_only"

L2_FEATURE_QUALITY_FLAGS: tuple[str, ...] = (
    L2_FEATURE_FIXTURE_ONLY,
    L2_FEATURE_INCOMPLETE_TOP_OF_BOOK,
    L2_FEATURE_MISSING_LEVEL,
    L2_FEATURE_MISSING_ORDER_COUNT,
    L2_FEATURE_MISSING_SIDE,
    L2_FEATURE_ZERO_DENOMINATOR,
)


def normalize_l2_quality_flags(flags: Iterable[Any]) -> tuple[str, ...]:
    """Return deterministic string quality flags."""
    normalized: set[str] = set()
    for flag in flags:
        if flag is None:
            continue
        text = str(flag).strip()
        if text:
            normalized.add(text)
    return tuple(sorted(normalized))


def l2_input_quality_flags(records: Iterable[Mapping[str, Any]]) -> tuple[str, ...]:
    """Collect quality flags from L2 input rows."""
    flags: list[Any] = []
    for record in records:
        value = record.get("quality_flags", ())
        if isinstance(value, str):
            flags.extend(part for part in value.split("|") if part)
        elif isinstance(value, Iterable):
            flags.extend(value)
        elif value is not None:
            flags.append(value)
    return normalize_l2_quality_flags(flags)


def merge_l2_feature_quality_flags(
    records: Iterable[Mapping[str, Any]],
    *,
    extra_flags: Iterable[Any] = (),
) -> tuple[str, ...]:
    """Merge input quality flags with deterministic feature-level flags."""
    return normalize_l2_quality_flags(
        (*l2_input_quality_flags(records), *tuple(extra_flags))
    )
