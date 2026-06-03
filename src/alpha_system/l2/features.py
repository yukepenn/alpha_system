"""Fixture-only L2-derived feature transforms.

The functions in this module operate only on tiny synthetic L2 fixtures. They
emit in-memory rows compatible with the existing factor value schema and do not
register, promote, persist, replay, reconstruct, simulate fills, or model queues.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from alpha_system.factors.base import FactorValue, assert_factor_value_schema
from alpha_system.l2.feature_specs import l2_feature_declaration
from alpha_system.l2.feature_validation import (
    L2FeatureValidationError,
    require_no_l2_feature_materialization_request,
    require_synthetic_l2_feature_inputs,
)
from alpha_system.l2.quality import (
    L2_FEATURE_FIXTURE_ONLY,
    L2_FEATURE_INCOMPLETE_TOP_OF_BOOK,
    L2_FEATURE_MISSING_LEVEL,
    L2_FEATURE_MISSING_ORDER_COUNT,
    L2_FEATURE_MISSING_SIDE,
    L2_FEATURE_ZERO_DENOMINATOR,
    merge_l2_feature_quality_flags,
    normalize_l2_quality_flags,
)
from alpha_system.l2.timestamps import l2_research_order_key
from alpha_system.l2.validation import (
    L2ValidationError,
    validate_l2_delta,
    validate_l2_snapshot,
)


L2_FEATURE_COMPUTE_VERSION = "l2_feature_fixture_skeleton_v1"
L2_FEATURE_SCHEMA_COMPATIBLE = True


@dataclass(frozen=True, slots=True)
class L2FeatureScope:
    """Static scope metadata for ASV1-P26 feature transforms."""

    fixture_only: bool = True
    design_only: bool = True
    materialize_by_default: bool = False
    replay_engine: bool = False
    queue_model: bool = False
    passive_fill_model: bool = False
    broker_or_live_scope: bool = False


def l2_feature_scope() -> L2FeatureScope:
    """Return immutable ASV1-P26 scope metadata."""
    return L2FeatureScope()


def materialize_l2_feature_values_by_default(*, persist: bool = False) -> None:
    """Reject materialization requests for this design-scope skeleton."""
    require_no_l2_feature_materialization_request(persist=persist)


def compute_top_of_book_spread(
    snapshot_rows: Iterable[Mapping[str, Any]],
) -> FactorValue:
    """Compute synthetic top-of-book spread as ask price minus bid price."""
    rows = _prepare_snapshot_rows(snapshot_rows)
    bid = _row_for(rows, side="bid", level=1)
    ask = _row_for(rows, side="ask", level=1)
    used = tuple(row for row in (bid, ask) if row is not None)
    extra_flags = [L2_FEATURE_FIXTURE_ONLY]
    value: float | None = None

    if bid is None or ask is None:
        extra_flags.extend((L2_FEATURE_MISSING_SIDE, L2_FEATURE_INCOMPLETE_TOP_OF_BOOK))
    else:
        value = float(_decimal(ask["price"], "price") - _decimal(bid["price"], "price"))

    return _feature_value(
        feature_id="l2_top_of_book_spread",
        rows=used or rows,
        value=value,
        extra_flags=extra_flags,
    )


def compute_l2_imbalance(
    snapshot_rows: Iterable[Mapping[str, Any]],
    *,
    depth_levels: int,
    feature_id: str | None = None,
) -> FactorValue:
    """Compute displayed-size imbalance for synthetic depth levels."""
    if depth_levels <= 0:
        msg = "depth_levels must be positive"
        raise L2FeatureValidationError(msg)

    rows = tuple(
        row
        for row in _prepare_snapshot_rows(snapshot_rows)
        if _int(row["book_level"], "book_level") <= depth_levels
    )
    bid_rows = tuple(row for row in rows if _side(row) == "bid")
    ask_rows = tuple(row for row in rows if _side(row) == "ask")
    missing_flags = _missing_depth_flags(rows, depth_levels=depth_levels)
    extra_flags = [L2_FEATURE_FIXTURE_ONLY, *missing_flags]

    bid_size = _sum_sizes(bid_rows)
    ask_size = _sum_sizes(ask_rows)
    total = bid_size + ask_size
    value: float | None

    if not bid_rows or not ask_rows:
        extra_flags.append(L2_FEATURE_MISSING_SIDE)
        value = None
    elif total == 0:
        extra_flags.append(L2_FEATURE_ZERO_DENOMINATOR)
        value = None
    else:
        value = float((bid_size - ask_size) / total)

    active_feature_id = feature_id or (
        "l2_top1_imbalance" if depth_levels == 1 else "l2_top5_imbalance"
    )
    return _feature_value(
        feature_id=active_feature_id,
        rows=rows,
        value=value,
        extra_flags=extra_flags,
    )


def compute_top1_imbalance(snapshot_rows: Iterable[Mapping[str, Any]]) -> FactorValue:
    """Compute synthetic top-one bid/ask size imbalance."""
    return compute_l2_imbalance(snapshot_rows, depth_levels=1, feature_id="l2_top1_imbalance")


def compute_top5_imbalance(snapshot_rows: Iterable[Mapping[str, Any]]) -> FactorValue:
    """Compute synthetic top-five bid/ask displayed-depth imbalance."""
    return compute_l2_imbalance(snapshot_rows, depth_levels=5, feature_id="l2_top5_imbalance")


def compute_depth_by_side(
    snapshot_rows: Iterable[Mapping[str, Any]],
    *,
    side: str,
    depth_levels: int = 5,
) -> FactorValue:
    """Compute synthetic displayed depth for one side through ``depth_levels``."""
    normalized_side = _normalize_side(side)
    rows = tuple(
        row
        for row in _prepare_snapshot_rows(snapshot_rows)
        if _int(row["book_level"], "book_level") <= depth_levels
    )
    side_rows = tuple(row for row in rows if _side(row) == normalized_side)
    extra_flags = [L2_FEATURE_FIXTURE_ONLY, *_missing_depth_flags(rows, depth_levels=depth_levels)]
    value: float | None

    if not side_rows:
        extra_flags.append(L2_FEATURE_MISSING_SIDE)
        value = None
    else:
        value = float(_sum_sizes(side_rows))

    return _feature_value(
        feature_id="l2_depth_by_side",
        rows=side_rows or rows,
        value=value,
        extra_flags=extra_flags,
    )


def compute_order_count_by_level(
    snapshot_rows: Iterable[Mapping[str, Any]],
    *,
    side: str,
    level: int = 1,
) -> FactorValue:
    """Compute synthetic displayed order count for one side and level."""
    normalized_side = _normalize_side(side)
    rows = _prepare_snapshot_rows(snapshot_rows)
    row = _row_for(rows, side=normalized_side, level=level)
    extra_flags = [L2_FEATURE_FIXTURE_ONLY]
    value: float | None

    if row is None:
        extra_flags.extend((L2_FEATURE_MISSING_SIDE, L2_FEATURE_MISSING_LEVEL))
        used = rows
        value = None
    else:
        used = (row,)
        order_count = row.get("order_count")
        if order_count is None:
            extra_flags.append(L2_FEATURE_MISSING_ORDER_COUNT)
            value = None
        else:
            value = float(_int(order_count, "order_count"))

    return _feature_value(
        feature_id="l2_order_count_by_level",
        rows=used,
        value=value,
        extra_flags=extra_flags,
    )


def compute_microprice(snapshot_rows: Iterable[Mapping[str, Any]]) -> FactorValue:
    """Compute synthetic top-of-book microprice."""
    rows = _prepare_snapshot_rows(snapshot_rows)
    bid = _row_for(rows, side="bid", level=1)
    ask = _row_for(rows, side="ask", level=1)
    used = tuple(row for row in (bid, ask) if row is not None)
    extra_flags = [L2_FEATURE_FIXTURE_ONLY]
    value: float | None = None

    if bid is None or ask is None:
        extra_flags.extend((L2_FEATURE_MISSING_SIDE, L2_FEATURE_INCOMPLETE_TOP_OF_BOOK))
    else:
        bid_size = _decimal(bid["size"], "size")
        ask_size = _decimal(ask["size"], "size")
        total = bid_size + ask_size
        if total == 0:
            extra_flags.append(L2_FEATURE_ZERO_DENOMINATOR)
        else:
            bid_price = _decimal(bid["price"], "price")
            ask_price = _decimal(ask["price"], "price")
            value = float(((ask_price * bid_size) + (bid_price * ask_size)) / total)

    return _feature_value(
        feature_id="l2_microprice",
        rows=used or rows,
        value=value,
        extra_flags=extra_flags,
    )


def compute_quote_update_intensity(
    delta_rows: Iterable[Mapping[str, Any]],
    *,
    window: timedelta = timedelta(seconds=1),
) -> tuple[FactorValue, ...]:
    """Compute synthetic available_ts-ordered quote update intensity values."""
    if window.total_seconds() <= 0:
        msg = "window must be positive"
        raise L2FeatureValidationError(msg)
    rows = _prepare_delta_rows(delta_rows)
    ordered = tuple(sorted(rows, key=l2_research_order_key))
    values: list[FactorValue] = []

    for index, row in enumerate(ordered):
        current_available = _datetime(row["available_ts"], "available_ts")
        window_start = current_available - window
        visible_count = sum(
            1
            for prior in ordered[: index + 1]
            if _datetime(prior["available_ts"], "available_ts") >= window_start
        )
        values.append(
            _feature_value(
                feature_id="l2_quote_update_intensity",
                rows=(row,),
                value=visible_count / window.total_seconds(),
                extra_flags=(L2_FEATURE_FIXTURE_ONLY,),
                bar_index=index,
            )
        )
    return tuple(values)


def compute_liquidity_regime_tag(
    snapshot_rows: Iterable[Mapping[str, Any]],
    *,
    max_tight_spread: Decimal = Decimal("0.10"),
    min_displayed_depth: Decimal = Decimal("50"),
) -> FactorValue:
    """Return a conservative synthetic liquidity-regime tag."""
    rows = _prepare_snapshot_rows(snapshot_rows)
    spread = compute_top_of_book_spread(rows)
    bid_depth = compute_depth_by_side(rows, side="bid", depth_levels=5)
    ask_depth = compute_depth_by_side(rows, side="ask", depth_levels=5)
    flags = normalize_l2_quality_flags(
        (
            L2_FEATURE_FIXTURE_ONLY,
            *spread.quality_flags,
            *bid_depth.quality_flags,
            *ask_depth.quality_flags,
        )
    )

    if spread.value is None or bid_depth.value is None or ask_depth.value is None:
        tag = "incomplete"
    elif (
        Decimal(str(spread.value)) <= max_tight_spread
        and Decimal(str(bid_depth.value)) >= min_displayed_depth
        and Decimal(str(ask_depth.value)) >= min_displayed_depth
    ):
        tag = "tight_deep"
    else:
        tag = "wide_or_shallow"

    return _feature_value(
        feature_id="l2_liquidity_regime_tag",
        rows=rows,
        value=tag,
        extra_flags=flags,
    )


def _prepare_snapshot_rows(
    snapshot_rows: Iterable[Mapping[str, Any]],
) -> tuple[Mapping[str, Any], ...]:
    rows = require_synthetic_l2_feature_inputs(snapshot_rows)
    issues = []
    for index, row in enumerate(rows):
        issues.extend(validate_l2_snapshot(row, row_index=index).issues)
    if issues:
        raise L2ValidationError(tuple(issues))
    _assert_common_context(rows)
    return rows


def _prepare_delta_rows(
    delta_rows: Iterable[Mapping[str, Any]],
) -> tuple[Mapping[str, Any], ...]:
    rows = require_synthetic_l2_feature_inputs(delta_rows)
    issues = []
    for index, row in enumerate(rows):
        issues.extend(validate_l2_delta(row, row_index=index).issues)
    if issues:
        raise L2ValidationError(tuple(issues))
    _assert_common_context(rows)
    return rows


def _assert_common_context(rows: Sequence[Mapping[str, Any]]) -> None:
    first = rows[0]
    for field in ("instrument_id", "session_id", "data_version"):
        expected = first.get(field)
        for row in rows[1:]:
            if row.get(field) != expected:
                msg = f"L2 feature fixture rows must share {field}"
                raise L2FeatureValidationError(msg)


def _feature_value(
    *,
    feature_id: str,
    rows: Sequence[Mapping[str, Any]],
    value: float | str | None,
    extra_flags: Iterable[Any],
    bar_index: int = 0,
) -> FactorValue:
    if not rows:
        msg = "cannot build L2 feature value without input rows"
        raise L2FeatureValidationError(msg)

    declaration = l2_feature_declaration(feature_id)
    event_ts = max(_datetime(row["event_ts"], "event_ts") for row in rows)
    available_ts = max(_datetime(row["available_ts"], "available_ts") for row in rows)
    if available_ts < event_ts:
        msg = "derived L2 feature available_ts must not precede event_ts"
        raise L2FeatureValidationError(msg)
    quality_flags = merge_l2_feature_quality_flags(rows, extra_flags=extra_flags)
    result = FactorValue(
        factor_id=declaration.factor_spec.factor_id,
        factor_version=declaration.factor_spec.version,
        instrument_id=str(rows[0]["instrument_id"]),
        event_ts=event_ts,
        available_ts=available_ts,
        session_id=str(rows[0]["session_id"]),
        bar_index=bar_index,
        value=value,
        normalized_value=None,
        quality_flags=quality_flags,
        data_version=str(rows[0]["data_version"]),
        compute_version=L2_FEATURE_COMPUTE_VERSION,
    )
    assert_factor_value_schema(result)
    return result


def _row_for(
    rows: Iterable[Mapping[str, Any]],
    *,
    side: str,
    level: int,
) -> Mapping[str, Any] | None:
    normalized_side = _normalize_side(side)
    for row in rows:
        if _side(row) == normalized_side and _int(row["book_level"], "book_level") == level:
            return row
    return None


def _missing_depth_flags(
    rows: Sequence[Mapping[str, Any]],
    *,
    depth_levels: int,
) -> tuple[str, ...]:
    flags: list[str] = []
    for level in range(1, depth_levels + 1):
        for side in ("bid", "ask"):
            if _row_for(rows, side=side, level=level) is None:
                flags.append(L2_FEATURE_MISSING_LEVEL)
    return normalize_l2_quality_flags(flags)


def _sum_sizes(rows: Iterable[Mapping[str, Any]]) -> Decimal:
    total = Decimal("0")
    for row in rows:
        total += _decimal(row["size"], "size")
    return total


def _side(row: Mapping[str, Any]) -> str:
    return _normalize_side(row["side"])


def _normalize_side(value: Any) -> str:
    text = str(getattr(value, "value", value)).strip().lower()
    if text not in {"bid", "ask"}:
        msg = "side must be bid or ask"
        raise L2FeatureValidationError(msg)
    return text


def _decimal(value: Any, field_name: str) -> Decimal:
    if isinstance(value, Decimal):
        return value
    msg = f"{field_name} must be Decimal"
    raise L2FeatureValidationError(msg)


def _int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        msg = f"{field_name} must be int"
        raise L2FeatureValidationError(msg)
    return value


def _datetime(value: Any, field_name: str) -> datetime:
    if isinstance(value, datetime):
        active = value
    else:
        msg = f"{field_name} must be datetime"
        raise L2FeatureValidationError(msg)
    if active.tzinfo is None:
        active = active.replace(tzinfo=timezone.utc)
    return active.astimezone(timezone.utc)
