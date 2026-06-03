"""Point-in-time cross-sectional ranking utilities."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from alpha_system.data.universe import (
    INACTIVE_UNIVERSE_MEMBER_FLAG,
    MISALIGNED_TIMESTAMP_FLAG,
    MISSING_DATA_FLAG,
    UNAVAILABLE_DATA_FLAG,
    UniverseSpec,
)


NOT_IN_UNIVERSE_FLAG = "not_in_universe"


class CrossSectionalRankError(ValueError):
    """Raised when cross-sectional inputs are structurally unsafe."""


@dataclass(frozen=True, slots=True, kw_only=True)
class CrossSectionalRank:
    """Ranked value for one active instrument at one decision timestamp."""

    instrument_id: str
    decision_ts: datetime
    available_ts: datetime
    value: Decimal
    rank: int
    percentile: Decimal
    universe_id: str
    data_version: str

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


@dataclass(frozen=True, slots=True, kw_only=True)
class CrossSectionalRankResult:
    """Ranks and per-instrument availability flags for one timestamp."""

    decision_ts: datetime
    universe_id: str
    ranks: tuple[CrossSectionalRank, ...]
    missing_data_flags: Mapping[str, tuple[str, ...]]

    @property
    def ranked_instrument_ids(self) -> tuple[str, ...]:
        return tuple(rank.instrument_id for rank in self.ranks)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_ts": self.decision_ts.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "universe_id": self.universe_id,
            "ranks": [rank.to_dict() for rank in self.ranks],
            "missing_data_flags": {
                instrument_id: list(flags)
                for instrument_id, flags in sorted(self.missing_data_flags.items())
            },
        }


def point_in_time_cross_sectional_rank(
    rows: Sequence[Mapping[str, Any]],
    universe: UniverseSpec,
    *,
    decision_ts: datetime | str,
    value_field: str = "value",
    event_ts_field: str = "event_ts",
    available_ts_field: str = "available_ts",
    higher_is_better: bool = True,
) -> CrossSectionalRankResult:
    """Rank active universe rows available at ``decision_ts`` only."""
    active_decision_ts = _datetime_value(decision_ts, "decision_ts")
    active_members = universe.active_members_at(active_decision_ts)
    active_ids = {member.instrument_id for member in active_members}
    known_ids = set(universe.member_by_instrument_id())
    flags: dict[str, list[str]] = {instrument_id: [] for instrument_id in sorted(active_ids)}
    selected: dict[str, tuple[Decimal, datetime]] = {}

    for row_number, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise CrossSectionalRankError("cross-sectional rows must be mappings")
        instrument_id = _text(row.get("instrument_id"), f"row {row_number} instrument_id")
        if instrument_id not in known_ids:
            flags.setdefault(instrument_id, []).append(NOT_IN_UNIVERSE_FLAG)
            continue
        if instrument_id not in active_ids:
            flags.setdefault(instrument_id, []).append(INACTIVE_UNIVERSE_MEMBER_FLAG)
            continue

        event_ts = _datetime_value(row.get(event_ts_field), f"row {row_number} {event_ts_field}")
        if event_ts != active_decision_ts:
            flags[instrument_id].append(MISALIGNED_TIMESTAMP_FLAG)
            continue

        available_ts = _datetime_value(
            row.get(available_ts_field),
            f"row {row_number} {available_ts_field}",
        )
        if available_ts > active_decision_ts:
            flags[instrument_id].append(UNAVAILABLE_DATA_FLAG)
            continue

        if instrument_id in selected:
            raise CrossSectionalRankError(f"duplicate aligned row for instrument_id {instrument_id}")
        selected[instrument_id] = (_decimal(row.get(value_field), f"row {row_number} {value_field}"), available_ts)

    for instrument_id in sorted(active_ids):
        if instrument_id not in selected and not flags[instrument_id]:
            flags[instrument_id].append(MISSING_DATA_FLAG)

    ranked_rows = sorted(
        selected.items(),
        key=lambda item: (
            -item[1][0] if higher_is_better else item[1][0],
            item[0],
        ),
    )
    ranks: list[CrossSectionalRank] = []
    count = len(ranked_rows)
    for index, (instrument_id, (value, available_ts)) in enumerate(ranked_rows, start=1):
        percentile = Decimal("1") if count == 1 else Decimal(count - index) / Decimal(count - 1)
        ranks.append(
            CrossSectionalRank(
                instrument_id=instrument_id,
                decision_ts=active_decision_ts,
                available_ts=available_ts,
                value=value,
                rank=index,
                percentile=percentile,
                universe_id=universe.universe_id,
                data_version=universe.get_member(instrument_id).data_version,
            )
        )

    return CrossSectionalRankResult(
        decision_ts=active_decision_ts,
        universe_id=universe.universe_id,
        ranks=tuple(ranks),
        missing_data_flags={
            instrument_id: tuple(dict.fromkeys(items))
            for instrument_id, items in sorted(flags.items())
            if items
        },
    )


def cross_sectional_rank(
    rows: Sequence[Mapping[str, Any]],
    universe: UniverseSpec,
    *,
    decision_ts: datetime | str,
    value_field: str = "value",
    event_ts_field: str = "event_ts",
    available_ts_field: str = "available_ts",
    higher_is_better: bool = True,
) -> CrossSectionalRankResult:
    """Alias for the point-in-time rank utility."""
    return point_in_time_cross_sectional_rank(
        rows,
        universe,
        decision_ts=decision_ts,
        value_field=value_field,
        event_ts_field=event_ts_field,
        available_ts_field=available_ts_field,
        higher_is_better=higher_is_better,
    )


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CrossSectionalRankError(f"{field_name} must be a non-empty string")
    return value.strip()


def _decimal(value: Any, field_name: str) -> Decimal:
    if isinstance(value, bool):
        raise CrossSectionalRankError(f"{field_name} must be numeric")
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise CrossSectionalRankError(f"{field_name} must be numeric") from exc


def _datetime_value(value: datetime | str | Any, field_name: str) -> datetime:
    if isinstance(value, datetime):
        active = value
    elif isinstance(value, str):
        text = value.replace("Z", "+00:00")
        try:
            active = datetime.fromisoformat(text)
        except ValueError as exc:
            raise CrossSectionalRankError(f"{field_name} must be an ISO datetime") from exc
    else:
        raise CrossSectionalRankError(f"{field_name} must be a datetime or ISO datetime string")
    if active.tzinfo is None or active.utcoffset() is None:
        raise CrossSectionalRankError(f"{field_name} must be timezone-aware")
    return active


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    return value
