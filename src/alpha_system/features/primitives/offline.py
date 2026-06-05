"""Offline-only centered and future-looking primitive windows.

These helpers deliberately live outside the package-root live primitive surface.
They require FLF-P06 ``WindowSpec`` objects marked ``offline_only`` with
centered/future causality and are not bindable through ``build_live_primitive``.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from alpha_system.features.contracts import WindowCausality, WindowKind, WindowSpec
from alpha_system.features.primitives.causal import (
    PrimitivePoint,
    PrimitiveResult,
    PrimitiveSpecError,
)


def offline_centered_mean(
    points: Iterable[PrimitivePoint],
    window: WindowSpec,
) -> tuple[PrimitiveResult, ...]:
    """Compute an offline centered mean that may use future availability."""

    _require_offline_window(window, expected_causality=WindowCausality.CENTERED)
    if window.length % 2 == 0:
        raise PrimitiveSpecError("centered offline windows require an odd length")
    ordered = _ordered_points(points)
    radius = window.length // 2
    results: list[PrimitiveResult] = []
    for index, point in enumerate(ordered):
        start = max(0, index - radius)
        stop = min(len(ordered), index + radius + 1)
        window_points = ordered[start:stop]
        results.append(_offline_mean_result(point, window_points, minimum_count=window.length))
    return tuple(results)


def offline_future_mean(
    points: Iterable[PrimitivePoint],
    window: WindowSpec,
) -> tuple[PrimitiveResult, ...]:
    """Compute an offline future mean over rows available after each timestamp."""

    _require_offline_window(window, expected_causality=WindowCausality.FUTURE)
    ordered = _ordered_points(points)
    results: list[PrimitiveResult] = []
    for index, point in enumerate(ordered):
        window_points = ordered[index + 1 : index + 1 + window.length]
        results.append(_offline_mean_result(point, window_points, minimum_count=window.length))
    return tuple(results)


def _offline_mean_result(
    point: PrimitivePoint,
    window_points: Sequence[PrimitivePoint],
    *,
    minimum_count: int,
) -> PrimitiveResult:
    flags: set[str] = set()
    if len(window_points) < minimum_count:
        flags.update({"insufficient_window", "primitive_gap"})
    for window_point in window_points:
        if window_point.is_gap:
            flags.update({"input_gap", "primitive_gap", *window_point.quality_flags})
    values = [
        window_point.value for window_point in window_points if window_point.value is not None
    ]
    if flags or len(values) != len(window_points):
        return PrimitiveResult(
            available_ts=point.available_ts,
            value=None,
            input_count=len(window_points),
            source_available_ts=tuple(window_point.available_ts for window_point in window_points),
            session_label=point.session_label,
            quality_flags=tuple(sorted(flags)),
        )
    return PrimitiveResult(
        available_ts=point.available_ts,
        value=sum(values) / len(values),
        input_count=len(window_points),
        source_available_ts=tuple(window_point.available_ts for window_point in window_points),
        session_label=point.session_label,
    )


def _require_offline_window(
    window: WindowSpec,
    *,
    expected_causality: WindowCausality,
) -> WindowSpec:
    if not isinstance(window, WindowSpec):
        raise PrimitiveSpecError("offline primitive windows require an FLF-P06 WindowSpec")
    if window.anchor != "available_ts":
        raise PrimitiveSpecError("offline primitives require WindowSpec.anchor='available_ts'")
    if not window.offline_only:
        raise PrimitiveSpecError("offline primitives require WindowSpec.offline_only=True")
    if window.causality is not expected_causality:
        raise PrimitiveSpecError(f"offline primitive requires causality={expected_causality.value}")
    if expected_causality is WindowCausality.CENTERED and window.kind is not WindowKind.CENTERED:
        raise PrimitiveSpecError("centered offline primitive requires kind=centered")
    if expected_causality is WindowCausality.FUTURE and window.kind is not WindowKind.FUTURE:
        raise PrimitiveSpecError("future offline primitive requires kind=future")
    return window


def _ordered_points(points: Iterable[PrimitivePoint]) -> tuple[PrimitivePoint, ...]:
    enumerated = tuple(enumerate(points))
    for _, point in enumerated:
        if not isinstance(point, PrimitivePoint):
            raise PrimitiveSpecError("offline primitive inputs must be PrimitivePoint objects")
    return tuple(
        point
        for _, point in sorted(enumerated, key=lambda item: (item[1].available_ts, item[0]))
    )


__all__ = [
    "offline_centered_mean",
    "offline_future_mean",
]
