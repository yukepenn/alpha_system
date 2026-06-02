"""Data-quality flagging for sessionized 1-minute bars."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from alpha_system.data.calendar import TradingCalendar
from alpha_system.data.sessions import expected_bar_starts, session_quality_available_ts


MISSING_BAR_FLAG = "missing_bar"
DUPLICATE_BAR_FLAG = "duplicate_bar"
OUT_OF_SESSION_FLAG = "out_of_session"


@dataclass(frozen=True, slots=True)
class QualityIssue:
    """One surfaced data-quality issue or warning."""

    category: str
    flag: str
    message: str
    count: int
    row_index: int | None = None
    instrument_id: str | None = None
    session_id: str | None = None
    bar_index: int | None = None
    bar_start_ts: datetime | None = None
    available_ts: datetime | None = None
    details: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class QualityReport:
    """Rows plus structured quality issues; rows are never dropped or merged."""

    rows: tuple[dict[str, Any], ...]
    issues: tuple[QualityIssue, ...]

    def count(self, flag: str) -> int:
        return sum(issue.count for issue in self.issues if issue.flag == flag)

    def messages(self) -> tuple[str, ...]:
        return tuple(issue.message for issue in self.issues)


def normalize_quality_flags(value: Any) -> tuple[str, ...]:
    """Normalize the canonical quality_flags field to tuple[str, ...]."""
    if value is None:
        return ()
    if isinstance(value, tuple):
        return tuple(str(item) for item in value)
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return ()
        return tuple(part.strip() for part in text.split("|") if part.strip())
    return (str(value),)


def add_quality_flags(row: Mapping[str, Any], *flags: str) -> dict[str, Any]:
    """Return a copied row with flags appended in stable order."""
    merged = list(normalize_quality_flags(row.get("quality_flags")))
    for flag in flags:
        if flag not in merged:
            merged.append(flag)
    copied = dict(row)
    copied["quality_flags"] = tuple(merged)
    return copied


def flag_out_of_session_bars(
    rows: Iterable[Mapping[str, Any]],
    calendar: TradingCalendar,
) -> QualityReport:
    """Flag bars whose interval is not contained by a trading session."""
    copied_rows: list[dict[str, Any]] = []
    issues: list[QualityIssue] = []
    for row_index, row in enumerate(rows):
        start = row.get("bar_start_ts")
        end = row.get("bar_end_ts")
        out_row = dict(row)
        if not isinstance(start, datetime) or not isinstance(end, datetime):
            out_row = add_quality_flags(out_row, OUT_OF_SESSION_FLAG)
            issues.append(
                QualityIssue(
                    category="out_of_session",
                    flag=OUT_OF_SESSION_FLAG,
                    message=f"row {row_index}: bar timestamps are not valid datetimes",
                    count=1,
                    row_index=row_index,
                    instrument_id=_str_or_none(row.get("instrument_id")),
                )
            )
            copied_rows.append(out_row)
            continue

        session = calendar.session_containing_bar(start, end)
        if session is None:
            out_row = add_quality_flags(out_row, OUT_OF_SESSION_FLAG)
            issues.append(
                QualityIssue(
                    category="out_of_session",
                    flag=OUT_OF_SESSION_FLAG,
                    message=(
                        f"row {row_index}: "
                        "bar is outside a configured trading session"
                    ),
                    count=1,
                    row_index=row_index,
                    instrument_id=_str_or_none(row.get("instrument_id")),
                    bar_start_ts=start,
                )
            )
        copied_rows.append(out_row)
    return QualityReport(tuple(copied_rows), tuple(issues))


def flag_duplicate_bars(rows: Iterable[Mapping[str, Any]]) -> QualityReport:
    """Flag duplicate instrument/session/bar-index and timestamp keys."""
    materialized = tuple(dict(row) for row in rows)
    flagged_indexes: set[int] = set()
    issues: list[QualityIssue] = []

    for key_name, key_fields in (
        (
            "instrument_session_bar_index",
            ("instrument_id", "session_id", "bar_index"),
        ),
        (
            "instrument_session_bar_start_ts",
            ("instrument_id", "session_id", "bar_start_ts"),
        ),
    ):
        groups: dict[tuple[Any, ...], list[int]] = defaultdict(list)
        for row_index, row in enumerate(materialized):
            key = tuple(row.get(field) for field in key_fields)
            if any(_missing_key_part(part) for part in key):
                continue
            groups[key].append(row_index)
        for key, indexes in groups.items():
            if len(indexes) < 2:
                continue
            flagged_indexes.update(indexes)
            first_row = materialized[indexes[0]]
            issues.append(
                QualityIssue(
                    category="duplicate",
                    flag=DUPLICATE_BAR_FLAG,
                    message=(
                        f"{len(indexes)} rows duplicate {key_name} key {key!r}"
                    ),
                    count=len(indexes),
                    instrument_id=_str_or_none(first_row.get("instrument_id")),
                    session_id=_str_or_none(first_row.get("session_id")),
                    bar_index=_int_or_none(first_row.get("bar_index")),
                    bar_start_ts=_datetime_or_none(first_row.get("bar_start_ts")),
                    details={"key_name": key_name},
                )
            )

    output = []
    for row_index, row in enumerate(materialized):
        if row_index in flagged_indexes:
            output.append(add_quality_flags(row, DUPLICATE_BAR_FLAG))
        else:
            output.append(dict(row))
    return QualityReport(tuple(output), tuple(issues))


def flag_missing_bars(
    rows: Iterable[Mapping[str, Any]],
    calendar: TradingCalendar,
    *,
    latency: timedelta = timedelta(0),
) -> QualityReport:
    """Surface gaps against each observed instrument/session expected grid."""
    materialized = tuple(dict(row) for row in rows)
    observed: dict[tuple[str, str], set[datetime]] = defaultdict(set)

    for row in materialized:
        flags = normalize_quality_flags(row.get("quality_flags"))
        if OUT_OF_SESSION_FLAG in flags:
            continue
        instrument_id = row.get("instrument_id")
        session_id = row.get("session_id")
        bar_start_ts = row.get("bar_start_ts")
        if (
            not isinstance(instrument_id, str)
            or not instrument_id
            or not isinstance(session_id, str)
            or not session_id
            or not isinstance(bar_start_ts, datetime)
        ):
            continue
        observed[(instrument_id, session_id)].add(bar_start_ts)

    issues: list[QualityIssue] = []
    for (instrument_id, session_id), starts in sorted(observed.items()):
        session = calendar.session_by_id(session_id)
        if session is None or session.is_holiday:
            continue
        expected = set(expected_bar_starts(session))
        missing = tuple(sorted(expected.difference(starts)))
        if not missing:
            continue
        available_ts = session_quality_available_ts(session, latency=latency)
        issues.append(
            QualityIssue(
                category="missing",
                flag=MISSING_BAR_FLAG,
                message=(
                    f"{len(missing)} expected bars are missing for "
                    f"{instrument_id} {session_id}"
                ),
                count=len(missing),
                instrument_id=instrument_id,
                session_id=session_id,
                bar_start_ts=missing[0],
                available_ts=available_ts,
                details={
                    "missing_bar_start_ts": tuple(
                        start.isoformat() for start in missing
                    )
                },
            )
        )

    return QualityReport(materialized, tuple(issues))


def evaluate_data_quality(
    rows: Iterable[Mapping[str, Any]],
    calendar: TradingCalendar,
    *,
    latency: timedelta = timedelta(0),
) -> QualityReport:
    """Run out-of-session, duplicate, and missing-bar quality checks."""
    out_of_session = flag_out_of_session_bars(rows, calendar)
    duplicates = flag_duplicate_bars(out_of_session.rows)
    missing = flag_missing_bars(duplicates.rows, calendar, latency=latency)
    return QualityReport(
        missing.rows,
        out_of_session.issues + duplicates.issues + missing.issues,
    )


def _missing_key_part(value: Any) -> bool:
    return value is None or value == "" or value == -1


def _str_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _int_or_none(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _datetime_or_none(value: Any) -> datetime | None:
    return value if isinstance(value, datetime) else None
