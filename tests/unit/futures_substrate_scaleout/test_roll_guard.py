from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from alpha_system.data.foundation.rolls import (
    CME_EQUITY_INDEX_QUARTERLY_VALIDATION_STATUS,
    build_analytic_cme_equity_index_quarterly_roll_calendar,
    build_cme_equity_index_quarterly_roll_policy,
    cme_equity_index_quarterly_roll_date,
    require_roll_calendar_matches_policy,
    third_friday,
)
from alpha_system.labels.roll_guard import (
    DEFAULT_CROSS_ROLL_POLICY,
    ROLL_GUARD_VERSION,
    ROLL_POLICY_ID,
    RollCrossPolicy,
    RollGuardAction,
    classify_roll_window,
    evaluate_roll_guard,
    is_roll_window,
    roll_window_label,
)

FIXTURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "futures_substrate_scaleout"
    / "roll_guard"
    / "known_roll_week.json"
)


def _fixture() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _known_roll_date() -> date:
    return date.fromisoformat(str(_fixture()["expected_roll_date"]))


def _known_calendar():
    return build_analytic_cme_equity_index_quarterly_roll_calendar(
        root_symbols=("ES",),
        start_year=2024,
        end_year=2024,
    )


def _cross_roll_entry() -> datetime:
    return datetime(2024, 3, 6, 15, 0, tzinfo=UTC)


def _cross_roll_horizon() -> datetime:
    return datetime(2024, 3, 8, 15, 0, tzinfo=UTC)


def test_analytic_known_roll_week_calendar_is_approximate_and_policy_consistent() -> None:
    fixture = _fixture()
    calendar = _known_calendar()
    policy = build_cme_equity_index_quarterly_roll_policy()
    roll_record = next(record for record in calendar if record.roll_date == _known_roll_date())

    assert third_friday(2024, 3) == date.fromisoformat(str(fixture["expiration_date"]))
    assert cme_equity_index_quarterly_roll_date(year=2024, month=3) == _known_roll_date()
    assert policy.roll_policy_id == ROLL_POLICY_ID == fixture["roll_policy_id"]
    assert ROLL_GUARD_VERSION == fixture["roll_guard_version"]
    assert DEFAULT_CROSS_ROLL_POLICY.value == fixture["default_cross_roll_policy"]
    assert roll_record.validation_status == CME_EQUITY_INDEX_QUARTERLY_VALIDATION_STATUS
    assert roll_record.validation_status == fixture["validation_status"]
    assert roll_record.evidence["approximate"] is True
    assert roll_record.evidence["provider_exact_splice"] is False
    assert require_roll_calendar_matches_policy(roll_record, policy) is roll_record


@pytest.mark.parametrize(
    ("policy", "expected_action", "expected_valid"),
    (
        (RollCrossPolicy.DROP, RollGuardAction.DROP, False),
        (RollCrossPolicy.TRUNCATE, RollGuardAction.TRUNCATE, True),
        (RollCrossPolicy.FLAG, RollGuardAction.FLAG, True),
        (RollCrossPolicy.INVALID, RollGuardAction.INVALID, False),
    ),
)
def test_cross_roll_window_policy_modes(
    policy: RollCrossPolicy,
    expected_action: RollGuardAction,
    expected_valid: bool,
) -> None:
    verdict = evaluate_roll_guard(
        entry_ts=_cross_roll_entry(),
        label_horizon_ts=_cross_roll_horizon(),
        calendar=_known_calendar(),
        policy=policy,
        root_symbol="ES",
    )

    assert verdict.crosses_roll is True
    assert verdict.roll_date == _known_roll_date()
    assert verdict.requested_policy is policy
    assert verdict.applied_policy is policy
    assert verdict.action is expected_action
    assert verdict.valid is expected_valid
    assert verdict.safe_default_applied is False

    if expected_action is RollGuardAction.DROP:
        assert verdict.should_drop is True
        assert verdict.effective_label_horizon_ts is None
    elif expected_action is RollGuardAction.TRUNCATE:
        assert verdict.truncated is True
        assert verdict.effective_label_horizon_ts == datetime(2024, 3, 7, tzinfo=UTC)
    elif expected_action is RollGuardAction.FLAG:
        assert verdict.should_flag is True
        assert verdict.effective_label_horizon_ts == _cross_roll_horizon()
    else:
        assert verdict.effective_label_horizon_ts is None


def test_non_cross_roll_window_is_untouched() -> None:
    entry = datetime(2024, 3, 12, 15, 0, tzinfo=UTC)
    horizon = datetime(2024, 3, 12, 16, 0, tzinfo=UTC)

    verdict = evaluate_roll_guard(
        entry_ts=entry,
        label_horizon_ts=horizon,
        calendar=_known_calendar(),
        policy=RollCrossPolicy.INVALID,
        root_symbol="ES",
    )

    assert verdict.action is RollGuardAction.KEEP
    assert verdict.crosses_roll is False
    assert verdict.valid is True
    assert verdict.effective_label_horizon_ts == horizon
    assert verdict.safe_default_applied is False


def test_roll_window_membership_and_labeller() -> None:
    calendar = _known_calendar()
    inside = datetime(2024, 3, 6, 12, 0, tzinfo=UTC)
    outside = datetime(2024, 3, 10, 12, 0, tzinfo=UTC)

    inside_verdict = classify_roll_window(inside, calendar, root_symbol="ES")
    outside_verdict = classify_roll_window(outside, calendar, root_symbol="ES")

    assert inside_verdict.in_roll_window is True
    assert inside_verdict.roll_date == _known_roll_date()
    assert is_roll_window(inside, calendar, root_symbol="ES") is True
    assert roll_window_label(inside, calendar, root_symbol="ES") == "roll_window"
    assert outside_verdict.in_roll_window is False
    assert roll_window_label(outside, calendar, root_symbol="ES") == "non_roll_window"


def test_roll_guard_is_deterministic() -> None:
    kwargs = {
        "entry_ts": _cross_roll_entry(),
        "label_horizon_ts": _cross_roll_horizon(),
        "calendar": _known_calendar(),
        "policy": RollCrossPolicy.FLAG,
        "root_symbol": "ES",
    }

    assert evaluate_roll_guard(**kwargs) == evaluate_roll_guard(**kwargs)


def test_missing_calendar_defaults_to_safe_drop_policy() -> None:
    verdict = evaluate_roll_guard(
        entry_ts=_cross_roll_entry(),
        label_horizon_ts=_cross_roll_horizon(),
        calendar=(),
        policy=RollCrossPolicy.FLAG,
        root_symbol="ES",
    )

    assert verdict.safe_default_applied is True
    assert verdict.requested_policy is RollCrossPolicy.FLAG
    assert verdict.applied_policy is RollCrossPolicy.DROP
    assert verdict.action is RollGuardAction.DROP
    assert verdict.valid is False
    assert verdict.crosses_roll is True
    assert verdict.reason == "missing_calendar_for_es"
    assert roll_window_label(_cross_roll_entry(), (), root_symbol="ES") == "roll_window_unknown"
