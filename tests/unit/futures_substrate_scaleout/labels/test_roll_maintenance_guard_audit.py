from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from alpha_system.data.foundation.rolls import (
    build_analytic_cme_equity_index_quarterly_roll_calendar,
)
from alpha_system.labels.families.fixed_horizon.family import _crosses_maintenance_break
from alpha_system.labels.roll_guard import RollCrossPolicy, RollGuardAction, evaluate_roll_guard


@dataclass(frozen=True, slots=True)
class SyntheticWindow:
    entry_ts: datetime
    horizon_ts: datetime
    root_symbol: str
    observed_action: RollGuardAction
    roll_policy: RollCrossPolicy = RollCrossPolicy.DROP


@dataclass(frozen=True, slots=True)
class AuditClassification:
    boundary_type: str
    expected_action: RollGuardAction


class GuardAuditViolation(AssertionError):
    """Raised when a boundary-crossing window was silently measured."""


def test_roll_crossing_windows_are_classified_for_all_roll_policies() -> None:
    calendar = _calendar()
    expected_by_policy = {
        RollCrossPolicy.DROP: RollGuardAction.DROP,
        RollCrossPolicy.TRUNCATE: RollGuardAction.TRUNCATE,
        RollCrossPolicy.FLAG: RollGuardAction.FLAG,
        RollCrossPolicy.INVALID: RollGuardAction.INVALID,
    }

    for policy, expected_action in expected_by_policy.items():
        classification = _audit_window(
            SyntheticWindow(
                entry_ts=_dt("2024-06-12T23:45:00+00:00"),
                horizon_ts=_dt("2024-06-13T00:15:00+00:00"),
                root_symbol="ES",
                observed_action=expected_action,
                roll_policy=policy,
            ),
            calendar=calendar,
        )

        assert classification.boundary_type == "roll"
        assert classification.expected_action is expected_action


def test_maintenance_crossing_window_is_detected_and_classified_as_drop() -> None:
    classification = _audit_window(
        SyntheticWindow(
            entry_ts=_dt("2024-01-02T21:45:00+00:00"),
            horizon_ts=_dt("2024-01-02T22:15:00+00:00"),
            root_symbol="ES",
            observed_action=RollGuardAction.DROP,
        ),
        calendar=_calendar(),
    )

    assert classification == AuditClassification(
        boundary_type="maintenance",
        expected_action=RollGuardAction.DROP,
    )


def test_silently_measured_crossing_window_is_a_violation() -> None:
    with pytest.raises(GuardAuditViolation, match="silently measured"):
        _audit_window(
            SyntheticWindow(
                entry_ts=_dt("2024-06-12T23:45:00+00:00"),
                horizon_ts=_dt("2024-06-13T00:15:00+00:00"),
                root_symbol="ES",
                observed_action=RollGuardAction.KEEP,
            ),
            calendar=_calendar(),
        )


def test_guarded_non_crossing_window_passes() -> None:
    classification = _audit_window(
        SyntheticWindow(
            entry_ts=_dt("2024-01-02T14:30:00+00:00"),
            horizon_ts=_dt("2024-01-02T15:00:00+00:00"),
            root_symbol="ES",
            observed_action=RollGuardAction.KEEP,
        ),
        calendar=_calendar(),
    )

    assert classification == AuditClassification(
        boundary_type="none",
        expected_action=RollGuardAction.KEEP,
    )


def _audit_window(
    window: SyntheticWindow,
    *,
    calendar: object,
) -> AuditClassification:
    expected = _classify_expected_action(window, calendar=calendar)
    if expected.expected_action is not RollGuardAction.KEEP and (
        window.observed_action is RollGuardAction.KEEP
    ):
        raise GuardAuditViolation(
            f"silently measured {expected.boundary_type} crossing window"
        )
    if window.observed_action is not expected.expected_action:
        raise GuardAuditViolation(
            "observed guard action does not match expected policy: "
            f"{window.observed_action.value} != {expected.expected_action.value}"
        )
    return expected


def _classify_expected_action(
    window: SyntheticWindow,
    *,
    calendar: object,
) -> AuditClassification:
    if _crosses_maintenance_break(window.entry_ts, window.horizon_ts):
        return AuditClassification("maintenance", RollGuardAction.DROP)
    roll_verdict = evaluate_roll_guard(
        entry_ts=window.entry_ts,
        label_horizon_ts=window.horizon_ts,
        calendar=calendar,
        policy=window.roll_policy,
        root_symbol=window.root_symbol,
    )
    if roll_verdict.crosses_roll:
        return AuditClassification("roll", roll_verdict.action)
    return AuditClassification("none", RollGuardAction.KEEP)


def _calendar() -> object:
    return build_analytic_cme_equity_index_quarterly_roll_calendar(
        root_symbols=("ES",),
        start_year=2024,
        end_year=2024,
    )


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
