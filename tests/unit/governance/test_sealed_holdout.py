from __future__ import annotations

import json
from pathlib import Path

import pytest

from alpha_system.governance.label_leakage_guard import check_label_leakage
from alpha_system.governance.sealed_holdout import (
    HoldoutAccessLog,
    HoldoutAccessType,
    SealedHoldoutRegistry,
    SealedHoldoutStatus,
    SealedHoldoutWindow,
    access_intersects_holdout,
    create_sealed_holdout_window,
    emit_holdout_access_if_intersects,
    require_single_active_holdout_window,
    transition_sealed_holdout_status,
    validate_sealed_holdout_window,
)
from alpha_system.governance.serialization import deserialize
from alpha_system.governance.validation import GovernanceValidationError

LABEL_SPEC_FIXTURE = Path("tests/fixtures/governance/label_spec_valid.json")
STUDY_SPEC_ID = "sspec_438ceffd40855205de5497f0"
DECLARED_AT = "2026-06-11T22:36:43Z"
ACCESS_AT = "2026-06-11T23:00:00Z"


def _partition() -> dict[str, object]:
    return {
        "dataset_family": "futures_core_alpha_pilot_v1",
        "symbols": ["ES"],
        "split_role": "locked_test",
        "bar_interval": "governed futures research bars",
    }


def _window(*, status: SealedHoldoutStatus = SealedHoldoutStatus.SEALED) -> SealedHoldoutWindow:
    return create_sealed_holdout_window(
        partition_spec=_partition(),
        start_date="2025-01-01",
        end_date="2026-06-11",
        status=status,
        declared_at=DECLARED_AT,
        sealed_by="research-governance-owner",
        provenance={
            "compass_ref": "docs/OPERATING_COMPASS_V4.md Stage B sealed holdout doctrine",
            "value_free": True,
        },
    )


def _registry_file(tmp_path: Path, *windows: SealedHoldoutWindow) -> Path:
    path = tmp_path / "sealed-holdout.json"
    payload = {"windows": [window.to_dict() for window in windows]}
    path.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
    return path


def _access_log(tmp_path: Path) -> Path:
    path = tmp_path / "holdout-access.jsonl"
    path.write_text("", encoding="utf-8")
    return path


def test_sealed_holdout_window_round_trips_and_rejects_unknown_status() -> None:
    window = _window()

    assert window.window_id.startswith("holdwin_")
    assert SealedHoldoutWindow.from_canonical_json(window.to_canonical_json()) == window
    assert deserialize(window.to_canonical_json()) == window.to_dict()

    payload = window.to_dict()
    payload["status"] = "ACTIVE"
    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_sealed_holdout_window(payload)
    assert exc_info.value.issues[0].code == "invalid_sealed_holdout_status"


def test_rolling_holdout_window_allows_open_end_but_requires_marker() -> None:
    rolling = create_sealed_holdout_window(
        partition_spec=_partition(),
        start_date="2025-01-01",
        end_date=None,
        rolling=True,
        status=SealedHoldoutStatus.SEALED,
        declared_at=DECLARED_AT,
        sealed_by="research-governance-owner",
        provenance={
            "compass_ref": "docs/OPERATING_COMPASS_V4.md Stage B sealed holdout doctrine",
            "value_free": True,
        },
    )

    assert rolling.end_date is None
    assert rolling.rolling is True
    assert access_intersects_holdout(
        rolling,
        access_start_date="2027-01-01",
        access_end_date="2027-01-31",
        access_partition_spec={"dataset_family": "futures_core_alpha_pilot_v1"},
    )

    with pytest.raises(GovernanceValidationError) as exc_info:
        create_sealed_holdout_window(
            partition_spec=_partition(),
            start_date="2025-01-01",
            end_date=None,
            status=SealedHoldoutStatus.SEALED,
            declared_at=DECLARED_AT,
            sealed_by="research-governance-owner",
            provenance={
                "compass_ref": "docs/OPERATING_COMPASS_V4.md Stage B sealed holdout doctrine",
                "value_free": True,
            },
        )

    assert exc_info.value.issues[0].code == "missing_non_rolling_holdout_end_date"


def test_registry_enforces_exactly_one_active_window(tmp_path: Path) -> None:
    first = _window()
    second = create_sealed_holdout_window(
        partition_spec={**_partition(), "symbols": ["NQ"]},
        start_date="2025-01-01",
        end_date="2026-06-11",
        status=SealedHoldoutStatus.DECLARED,
        declared_at=DECLARED_AT,
        sealed_by="research-governance-owner",
        provenance={"compass_ref": "docs/OPERATING_COMPASS_V4.md Stage B"},
    )
    registry_path = _registry_file(tmp_path, first, second)

    with pytest.raises(GovernanceValidationError) as exc_info:
        SealedHoldoutRegistry(registry_path).active_window()

    assert exc_info.value.issues[0].code == "multiple_active_sealed_holdout_windows"


def test_breached_status_is_terminal_and_monotonic() -> None:
    declared = _window(status=SealedHoldoutStatus.DECLARED)
    sealed, audit = transition_sealed_holdout_status(
        declared,
        next_status=SealedHoldoutStatus.SEALED,
        actor="research-governance-owner",
        timestamp=ACCESS_AT,
        rationale="Seal synthetic holdout declaration after governance review.",
    )
    assert sealed.status is SealedHoldoutStatus.SEALED
    assert audit.previous_status is SealedHoldoutStatus.DECLARED
    assert audit.next_status is SealedHoldoutStatus.SEALED

    breached = _window(status=SealedHoldoutStatus.BREACHED)
    with pytest.raises(GovernanceValidationError) as exc_info:
        transition_sealed_holdout_status(
            breached,
            next_status=SealedHoldoutStatus.SEALED,
            actor="retroactive-editor",
            timestamp=ACCESS_AT,
            rationale="Attempted un-breach should fail closed.",
        )

    assert exc_info.value.issues[0].code == "sealed_holdout_breach_is_terminal"


def test_holdout_access_log_appends_only_when_access_intersects(tmp_path: Path) -> None:
    registry_path = _registry_file(tmp_path, _window())
    log_path = _access_log(tmp_path)

    decision = emit_holdout_access_if_intersects(
        sealed_holdout_registry_path=registry_path,
        holdout_access_log_path=log_path,
        study_spec_id=STUDY_SPEC_ID,
        actor="codex:synthetic-study-executor",
        access_type=HoldoutAccessType.VALIDATION,
        rationale="Synthetic validation access intersects the declared holdout.",
        timestamp=ACCESS_AT,
        access_start_date="2025-06-01",
        access_end_date="2025-06-30",
        access_partition_spec={"dataset_family": "futures_core_alpha_pilot_v1", "symbols": ["ES"]},
    )

    records = HoldoutAccessLog(log_path).load_records()
    assert decision.intersects_holdout is True
    assert decision.contamination_detected is False
    assert len(records) == 1
    assert records[0].access_type is HoldoutAccessType.VALIDATION
    assert not hasattr(HoldoutAccessLog, "update_record")
    assert not hasattr(HoldoutAccessLog, "delete_record")


def test_holdout_access_log_unwritable_fails_closed(tmp_path: Path) -> None:
    registry_path = _registry_file(tmp_path, _window())
    log_path = _access_log(tmp_path)
    log_path.chmod(0o444)

    try:
        with pytest.raises(GovernanceValidationError) as exc_info:
            emit_holdout_access_if_intersects(
                sealed_holdout_registry_path=registry_path,
                holdout_access_log_path=log_path,
                study_spec_id=STUDY_SPEC_ID,
                actor="codex:synthetic-study-executor",
                access_type=HoldoutAccessType.TRAINING,
                rationale="Synthetic training access intersects the declared holdout.",
                timestamp=ACCESS_AT,
            )
        assert exc_info.value.issues[0].code == "unwritable_holdout_access_log"
    finally:
        log_path.chmod(0o644)


def test_unauthorized_locked_test_access_is_logged_then_blocks(tmp_path: Path) -> None:
    registry_path = _registry_file(tmp_path, _window())
    log_path = _access_log(tmp_path)

    with pytest.raises(GovernanceValidationError) as exc_info:
        emit_holdout_access_if_intersects(
            sealed_holdout_registry_path=registry_path,
            holdout_access_log_path=log_path,
            study_spec_id=STUDY_SPEC_ID,
            actor="codex:synthetic-study-executor",
            access_type=HoldoutAccessType.LOCKED_TEST,
            rationale="Synthetic locked-test access outside authorized evaluation.",
            timestamp=ACCESS_AT,
        )

    assert exc_info.value.issues[0].code == "unauthorized_locked_test_holdout_access"
    records = HoldoutAccessLog(log_path).load_records()
    assert len(records) == 1
    assert records[0].access_type is HoldoutAccessType.LOCKED_TEST


def test_label_leakage_guard_emits_holdout_access_log(tmp_path: Path) -> None:
    registry_path = _registry_file(tmp_path, _window())
    log_path = _access_log(tmp_path)
    label_spec = json.loads(LABEL_SPEC_FIXTURE.read_text(encoding="utf-8"))

    result = check_label_leakage(
        label_spec,
        [
            {
                "feature_id": "synthetic_safe_feature",
                "available_at": "2025-01-02T00:00:00Z",
            }
        ],
        sealed_holdout_registry_path=registry_path,
        holdout_access_log_path=log_path,
        study_spec_id=STUDY_SPEC_ID,
        actor="governance.label_leakage_guard",
        rationale="Label leakage guard evaluated fixture access against sealed holdout.",
        timestamp=ACCESS_AT,
        access_start_date="2025-01-01",
        access_end_date="2025-01-31",
        access_partition_spec={"dataset_family": "futures_core_alpha_pilot_v1"},
    )

    assert result.is_clean is True
    records = HoldoutAccessLog(log_path).load_records()
    assert len(records) == 1
    assert records[0].actor == "governance.label_leakage_guard"


def test_single_active_helper_rejects_all_breached_windows() -> None:
    with pytest.raises(GovernanceValidationError) as exc_info:
        require_single_active_holdout_window((_window(status=SealedHoldoutStatus.BREACHED),))

    assert exc_info.value.issues[0].code == "missing_active_sealed_holdout_window"
