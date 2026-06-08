"""Roll-splice leakage guard for forward label windows."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from enum import StrEnum
from types import MappingProxyType

from alpha_system.data.foundation.rolls import (
    CME_EQUITY_INDEX_QUARTERLY_ROLL_POLICY_ID,
    RollCalendarRecord,
)
from alpha_system.labels.validation import LabelValidationError

ROLL_POLICY_ID = CME_EQUITY_INDEX_QUARTERLY_ROLL_POLICY_ID
ROLL_GUARD_VERSION = "roll_guard_v1"
DEFAULT_ROLL_WINDOW_DAYS_BEFORE = 2
DEFAULT_ROLL_WINDOW_DAYS_AFTER = 1


class RollCrossPolicy(StrEnum):
    """Supported policy modes for label windows that span a roll boundary."""

    DROP = "drop"
    TRUNCATE = "truncate"
    FLAG = "flag"
    INVALID = "invalid"


class RollGuardAction(StrEnum):
    """Actions returned by the roll guard evaluator."""

    KEEP = "pass"
    DROP = "drop"
    TRUNCATE = "truncate"
    FLAG = "flag"
    INVALID = "invalid"


class RollWindowLabel(StrEnum):
    """Roll-window split labels for downstream diagnostics."""

    ROLL_WINDOW = "roll_window"
    NON_ROLL_WINDOW = "non_roll_window"
    UNKNOWN = "roll_window_unknown"


DEFAULT_CROSS_ROLL_POLICY = RollCrossPolicy.DROP
SAFE_MISSING_CALENDAR_POLICY = RollCrossPolicy.DROP


@dataclass(frozen=True, slots=True)
class RollWindowVerdict:
    """Deterministic roll-window split classification for one timestamp."""

    timestamp: datetime
    root_symbol: str | None
    label: RollWindowLabel
    in_roll_window: bool
    roll_date: date | None
    matched_roll_calendar_id: str | None
    reason: str
    safe_default_applied: bool
    roll_policy_id: str = ROLL_POLICY_ID
    roll_guard_version: str = ROLL_GUARD_VERSION

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable summary for materialization metadata."""

        return MappingProxyType(
            {
                "timestamp": self.timestamp.isoformat(),
                "root_symbol": self.root_symbol,
                "label": self.label.value,
                "in_roll_window": self.in_roll_window,
                "roll_date": self.roll_date.isoformat() if self.roll_date else None,
                "matched_roll_calendar_id": self.matched_roll_calendar_id,
                "reason": self.reason,
                "safe_default_applied": self.safe_default_applied,
                "roll_policy_id": self.roll_policy_id,
                "roll_guard_version": self.roll_guard_version,
            }
        )


@dataclass(frozen=True, slots=True)
class RollGuardVerdict:
    """Deterministic guard result for one forward label window."""

    entry_ts: datetime
    label_horizon_ts: datetime
    effective_label_horizon_ts: datetime | None
    root_symbol: str | None
    requested_policy: RollCrossPolicy
    applied_policy: RollCrossPolicy
    action: RollGuardAction
    crosses_roll: bool
    in_roll_window: bool
    valid: bool
    roll_date: date | None
    matched_roll_calendar_id: str | None
    reason: str
    safe_default_applied: bool
    roll_policy_id: str = ROLL_POLICY_ID
    roll_guard_version: str = ROLL_GUARD_VERSION

    @property
    def should_drop(self) -> bool:
        """Return true when materialization should remove this window."""

        return self.action is RollGuardAction.DROP

    @property
    def should_flag(self) -> bool:
        """Return true when materialization should retain and flag this window."""

        return self.action is RollGuardAction.FLAG

    @property
    def truncated(self) -> bool:
        """Return true when the horizon was shortened before the roll boundary."""

        return self.action is RollGuardAction.TRUNCATE

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable summary for label metadata."""

        return MappingProxyType(
            {
                "entry_ts": self.entry_ts.isoformat(),
                "label_horizon_ts": self.label_horizon_ts.isoformat(),
                "effective_label_horizon_ts": (
                    self.effective_label_horizon_ts.isoformat()
                    if self.effective_label_horizon_ts
                    else None
                ),
                "root_symbol": self.root_symbol,
                "requested_policy": self.requested_policy.value,
                "applied_policy": self.applied_policy.value,
                "action": self.action.value,
                "crosses_roll": self.crosses_roll,
                "in_roll_window": self.in_roll_window,
                "valid": self.valid,
                "roll_date": self.roll_date.isoformat() if self.roll_date else None,
                "matched_roll_calendar_id": self.matched_roll_calendar_id,
                "reason": self.reason,
                "safe_default_applied": self.safe_default_applied,
                "roll_policy_id": self.roll_policy_id,
                "roll_guard_version": self.roll_guard_version,
            }
        )


def evaluate_roll_guard(
    *,
    entry_ts: datetime | str,
    label_horizon_ts: datetime | str,
    calendar: Iterable[RollCalendarRecord | Mapping[str, object]] | None,
    policy: RollCrossPolicy | str = DEFAULT_CROSS_ROLL_POLICY,
    root_symbol: str | None = None,
    roll_window_days_before: int = DEFAULT_ROLL_WINDOW_DAYS_BEFORE,
    roll_window_days_after: int = DEFAULT_ROLL_WINDOW_DAYS_AFTER,
) -> RollGuardVerdict:
    """Evaluate one forward label window against an approximate roll calendar."""

    entry = _normalize_datetime(entry_ts, "entry_ts")
    horizon = _normalize_datetime(label_horizon_ts, "label_horizon_ts")
    if horizon < entry:
        msg = "label_horizon_ts must be at or after entry_ts"
        raise LabelValidationError(msg)

    requested_policy = _normalize_policy(policy)
    root = _normalize_root_symbol(root_symbol)
    records = _coerce_calendar(calendar)
    window = classify_roll_window(
        entry,
        records,
        root_symbol=root,
        roll_window_days_before=roll_window_days_before,
        roll_window_days_after=roll_window_days_after,
    )
    filtered_records = _records_for_root(records, root)

    missing_or_ambiguous = _calendar_blocking_reason(filtered_records, root)
    if missing_or_ambiguous is not None:
        return _safe_default_verdict(
            entry_ts=entry,
            label_horizon_ts=horizon,
            root_symbol=root,
            requested_policy=requested_policy,
            in_roll_window=window.in_roll_window,
            reason=missing_or_ambiguous,
        )

    spanned_rolls = _spanned_rolls(filtered_records, entry, horizon)
    if len(spanned_rolls) > 1:
        return _safe_default_verdict(
            entry_ts=entry,
            label_horizon_ts=horizon,
            root_symbol=root,
            requested_policy=requested_policy,
            in_roll_window=window.in_roll_window,
            reason="ambiguous_multiple_rolls_in_window",
        )
    if not spanned_rolls:
        return RollGuardVerdict(
            entry_ts=entry,
            label_horizon_ts=horizon,
            effective_label_horizon_ts=horizon,
            root_symbol=root,
            requested_policy=requested_policy,
            applied_policy=requested_policy,
            action=RollGuardAction.KEEP,
            crosses_roll=False,
            in_roll_window=window.in_roll_window,
            valid=True,
            roll_date=None,
            matched_roll_calendar_id=None,
            reason="no_roll_boundary_in_window",
            safe_default_applied=False,
        )

    roll_record = spanned_rolls[0]
    return _cross_roll_verdict(
        entry_ts=entry,
        label_horizon_ts=horizon,
        root_symbol=root,
        requested_policy=requested_policy,
        in_roll_window=window.in_roll_window,
        roll_record=roll_record,
    )


def classify_roll_window(
    timestamp: datetime | str,
    calendar: Iterable[RollCalendarRecord | Mapping[str, object]] | None,
    *,
    root_symbol: str | None = None,
    roll_window_days_before: int = DEFAULT_ROLL_WINDOW_DAYS_BEFORE,
    roll_window_days_after: int = DEFAULT_ROLL_WINDOW_DAYS_AFTER,
) -> RollWindowVerdict:
    """Classify a timestamp into the deterministic roll-window split."""

    ts = _normalize_datetime(timestamp, "timestamp")
    _validate_roll_window_width(roll_window_days_before, roll_window_days_after)
    root = _normalize_root_symbol(root_symbol)
    records = _records_for_root(_coerce_calendar(calendar), root)
    missing_or_ambiguous = _calendar_blocking_reason(records, root)
    if missing_or_ambiguous is not None:
        return RollWindowVerdict(
            timestamp=ts,
            root_symbol=root,
            label=RollWindowLabel.UNKNOWN,
            in_roll_window=False,
            roll_date=None,
            matched_roll_calendar_id=None,
            reason=missing_or_ambiguous,
            safe_default_applied=True,
        )

    matches = tuple(
        record
        for record in records
        if _timestamp_in_roll_window(
            ts,
            record,
            roll_window_days_before=roll_window_days_before,
            roll_window_days_after=roll_window_days_after,
        )
    )
    if matches:
        selected = sorted(matches, key=lambda record: (record.root_symbol, record.roll_date))[0]
        return RollWindowVerdict(
            timestamp=ts,
            root_symbol=root,
            label=RollWindowLabel.ROLL_WINDOW,
            in_roll_window=True,
            roll_date=selected.roll_date,
            matched_roll_calendar_id=selected.roll_calendar_id,
            reason="timestamp_inside_roll_window",
            safe_default_applied=False,
        )
    return RollWindowVerdict(
        timestamp=ts,
        root_symbol=root,
        label=RollWindowLabel.NON_ROLL_WINDOW,
        in_roll_window=False,
        roll_date=None,
        matched_roll_calendar_id=None,
        reason="timestamp_outside_roll_window",
        safe_default_applied=False,
    )


def is_roll_window(
    timestamp: datetime | str,
    calendar: Iterable[RollCalendarRecord | Mapping[str, object]] | None,
    *,
    root_symbol: str | None = None,
    roll_window_days_before: int = DEFAULT_ROLL_WINDOW_DAYS_BEFORE,
    roll_window_days_after: int = DEFAULT_ROLL_WINDOW_DAYS_AFTER,
) -> bool:
    """Return true when a timestamp is inside the configured roll window."""

    return classify_roll_window(
        timestamp,
        calendar,
        root_symbol=root_symbol,
        roll_window_days_before=roll_window_days_before,
        roll_window_days_after=roll_window_days_after,
    ).in_roll_window


def roll_window_label(
    timestamp: datetime | str,
    calendar: Iterable[RollCalendarRecord | Mapping[str, object]] | None,
    *,
    root_symbol: str | None = None,
    roll_window_days_before: int = DEFAULT_ROLL_WINDOW_DAYS_BEFORE,
    roll_window_days_after: int = DEFAULT_ROLL_WINDOW_DAYS_AFTER,
) -> str:
    """Return ``roll_window``, ``non_roll_window``, or ``roll_window_unknown``."""

    return classify_roll_window(
        timestamp,
        calendar,
        root_symbol=root_symbol,
        roll_window_days_before=roll_window_days_before,
        roll_window_days_after=roll_window_days_after,
    ).label.value


def _safe_default_verdict(
    *,
    entry_ts: datetime,
    label_horizon_ts: datetime,
    root_symbol: str | None,
    requested_policy: RollCrossPolicy,
    in_roll_window: bool,
    reason: str,
) -> RollGuardVerdict:
    return RollGuardVerdict(
        entry_ts=entry_ts,
        label_horizon_ts=label_horizon_ts,
        effective_label_horizon_ts=None,
        root_symbol=root_symbol,
        requested_policy=requested_policy,
        applied_policy=SAFE_MISSING_CALENDAR_POLICY,
        action=RollGuardAction.DROP,
        crosses_roll=True,
        in_roll_window=in_roll_window,
        valid=False,
        roll_date=None,
        matched_roll_calendar_id=None,
        reason=reason,
        safe_default_applied=True,
    )


def _cross_roll_verdict(
    *,
    entry_ts: datetime,
    label_horizon_ts: datetime,
    root_symbol: str | None,
    requested_policy: RollCrossPolicy,
    in_roll_window: bool,
    roll_record: RollCalendarRecord,
) -> RollGuardVerdict:
    roll_boundary_ts = datetime.combine(
        roll_record.roll_date,
        time.min,
        tzinfo=entry_ts.tzinfo,
    )
    if requested_policy is RollCrossPolicy.DROP:
        action = RollGuardAction.DROP
        effective_horizon = None
        valid = False
        reason = "cross_roll_window_dropped"
    elif requested_policy is RollCrossPolicy.TRUNCATE:
        if roll_boundary_ts <= entry_ts:
            action = RollGuardAction.INVALID
            effective_horizon = None
            valid = False
            reason = "cross_roll_window_cannot_truncate_before_entry"
        else:
            action = RollGuardAction.TRUNCATE
            effective_horizon = roll_boundary_ts
            valid = True
            reason = "cross_roll_window_truncated"
    elif requested_policy is RollCrossPolicy.FLAG:
        action = RollGuardAction.FLAG
        effective_horizon = label_horizon_ts
        valid = True
        reason = "cross_roll_window_flagged"
    else:
        action = RollGuardAction.INVALID
        effective_horizon = None
        valid = False
        reason = "cross_roll_window_invalidated"

    return RollGuardVerdict(
        entry_ts=entry_ts,
        label_horizon_ts=label_horizon_ts,
        effective_label_horizon_ts=effective_horizon,
        root_symbol=root_symbol,
        requested_policy=requested_policy,
        applied_policy=requested_policy,
        action=action,
        crosses_roll=True,
        in_roll_window=in_roll_window,
        valid=valid,
        roll_date=roll_record.roll_date,
        matched_roll_calendar_id=roll_record.roll_calendar_id,
        reason=reason,
        safe_default_applied=False,
    )


def _spanned_rolls(
    records: tuple[RollCalendarRecord, ...],
    entry_ts: datetime,
    label_horizon_ts: datetime,
) -> tuple[RollCalendarRecord, ...]:
    entry_date = entry_ts.date()
    horizon_date = label_horizon_ts.date()
    return tuple(
        record
        for record in records
        if entry_date <= record.roll_date <= horizon_date
    )


def _timestamp_in_roll_window(
    timestamp: datetime,
    record: RollCalendarRecord,
    *,
    roll_window_days_before: int,
    roll_window_days_after: int,
) -> bool:
    timestamp_date = timestamp.date()
    window_start = record.roll_date - timedelta(days=roll_window_days_before)
    window_end = record.roll_date + timedelta(days=roll_window_days_after)
    return window_start <= timestamp_date <= window_end


def _calendar_blocking_reason(
    records: tuple[RollCalendarRecord, ...],
    root_symbol: str | None,
) -> str | None:
    if not records:
        if root_symbol is None:
            return "missing_calendar"
        return f"missing_calendar_for_{root_symbol.lower()}"

    seen: set[tuple[str, date]] = set()
    duplicates: set[tuple[str, date]] = set()
    for record in records:
        key = (record.root_symbol, record.roll_date)
        if key in seen:
            duplicates.add(key)
        seen.add(key)
    if duplicates:
        return "ambiguous_duplicate_roll_dates"
    return None


def _records_for_root(
    records: tuple[RollCalendarRecord, ...],
    root_symbol: str | None,
) -> tuple[RollCalendarRecord, ...]:
    filtered = (
        records
        if root_symbol is None
        else tuple(record for record in records if record.root_symbol == root_symbol)
    )
    return tuple(sorted(filtered, key=lambda record: (record.root_symbol, record.roll_date)))


def _coerce_calendar(
    calendar: Iterable[RollCalendarRecord | Mapping[str, object]] | None,
) -> tuple[RollCalendarRecord, ...]:
    if calendar is None:
        return ()
    return tuple(
        record
        if isinstance(record, RollCalendarRecord)
        else RollCalendarRecord.from_mapping(record)
        for record in calendar
    )


def _normalize_policy(policy: RollCrossPolicy | str) -> RollCrossPolicy:
    if isinstance(policy, RollCrossPolicy):
        return policy
    if isinstance(policy, str):
        raw = policy.strip().lower()
        try:
            return RollCrossPolicy(raw)
        except ValueError as exc:
            allowed = ", ".join(policy.value for policy in RollCrossPolicy)
            msg = f"policy must be one of {allowed}"
            raise LabelValidationError(msg) from exc
    msg = "policy must be a roll cross policy string"
    raise LabelValidationError(msg)


def _normalize_root_symbol(root_symbol: str | None) -> str | None:
    if root_symbol is None:
        return None
    root = root_symbol.strip().upper()
    if not root or not root.isalnum():
        msg = "root_symbol must be an alphanumeric futures root"
        raise LabelValidationError(msg)
    return root


def _normalize_datetime(value: datetime | str, field_name: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            msg = f"{field_name} must be an ISO-8601 datetime"
            raise LabelValidationError(msg) from exc
    else:
        msg = f"{field_name} must be a datetime or ISO-8601 string"
        raise LabelValidationError(msg)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        msg = f"{field_name} must be timezone-aware"
        raise LabelValidationError(msg)
    return parsed


def _validate_roll_window_width(days_before: int, days_after: int) -> None:
    for value, field_name in (
        (days_before, "roll_window_days_before"),
        (days_after, "roll_window_days_after"),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            msg = f"{field_name} must be a non-negative integer"
            raise LabelValidationError(msg)


__all__ = [
    "DEFAULT_CROSS_ROLL_POLICY",
    "DEFAULT_ROLL_WINDOW_DAYS_AFTER",
    "DEFAULT_ROLL_WINDOW_DAYS_BEFORE",
    "ROLL_GUARD_VERSION",
    "ROLL_POLICY_ID",
    "SAFE_MISSING_CALENDAR_POLICY",
    "RollCrossPolicy",
    "RollGuardAction",
    "RollGuardVerdict",
    "RollWindowLabel",
    "RollWindowVerdict",
    "classify_roll_window",
    "evaluate_roll_guard",
    "is_roll_window",
    "roll_window_label",
]
