from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from alpha_system.runtime.audit import NoLookaheadRuntimeAudit

FIXTURE_PATH = (
    Path(__file__).parents[2] / "fixtures" / "runtime" / "fail_closed" / "invalid_shortcuts.json"
)
DECISION_TS = "2026-01-02T14:36:00+00:00"


def test_rt_p20_fixture_rejects_feature_input_without_available_ts() -> None:
    fixture = _fixture()

    result = _audit(
        fixture,
        feature_inputs=(fixture["feature_inputs"]["missing_available_ts"],),
    )

    assert result.rejected
    assert "feature_available_ts_missing" in _reason_codes(result)


def test_rt_p20_fixture_rejects_label_input_without_label_available_ts() -> None:
    fixture = _fixture()

    result = _audit(
        fixture,
        label_inputs=(fixture["label_inputs"]["missing_label_available_ts"],),
    )

    assert result.rejected
    assert "label_available_ts_missing" in _reason_codes(result)


def test_rt_p20_fixture_rejects_same_bar_fill_metadata() -> None:
    fixture = _fixture()

    result = _audit(
        fixture,
        signal_probe_report=fixture["probe"]["same_bar_report"],
        probe_fill_records=(fixture["probe"]["same_bar_fill_record"],),
    )

    assert result.rejected
    assert "same_bar_optimistic_fill" in _reason_codes(result)


def test_rt_p20_fixture_rejects_locked_test_without_contamination_metadata() -> None:
    fixture = _fixture()

    result = _audit(
        fixture,
        runtime_input_pack=_runtime_input_pack(
            fixture,
            partition_scope=fixture["partition_scope"]["locked_test_without_metadata"],
        ),
        partition_purpose="descriptive_locked_partition_audit",
    )

    assert result.rejected
    assert "locked_partition_governance_metadata_missing" in _reason_codes(result)


def _fixture() -> dict[str, Any]:
    with FIXTURE_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    assert payload["synthetic_attestation"]["provider_response"] is False
    return payload


def _audit(fixture: Mapping[str, Any], **kwargs: Any) -> Any:
    options: dict[str, Any] = {
        "runtime_input_pack": _runtime_input_pack(fixture),
        "decision_ts": DECISION_TS,
        "signal_probe_report": {
            "position_summary": {"same_bar_fill_count": 0},
            "trade_summary": {"fill_delay_bars": 1},
            "report_metadata": {"same_bar_optimistic_fill_forbidden": True},
        },
    }
    options.update(kwargs)
    return NoLookaheadRuntimeAudit().evaluate(**options)


def _runtime_input_pack(
    fixture: Mapping[str, Any],
    *,
    partition_scope: Mapping[str, Any] | None = None,
    governance_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    ids = fixture["ids"]
    return {
        "alpha_spec_ref": ids["alpha_spec_ref"],
        "study_spec_ref": ids["study_spec_ref"],
        "study_input_pack": {
            "alpha_spec_id": ids["alpha_spec_ref"],
            "feature_request_ids": [ids["feature_request_ref"]],
            "label_spec_ids": [ids["label_spec_ref"]],
            "dataset_scope": fixture["dataset_scope"],
        },
        "dataset_version_id": ids["dataset_version_id"],
        "dataset_lifecycle_state": "VERSIONED",
        "feature_packs": [
            {
                "feature_version_id": ids["feature_version_id"],
                "feature_request_id": ids["feature_request_ref"],
                "event_ts": {
                    "first": "2026-01-02T14:30:00+00:00",
                    "last": "2026-01-02T14:35:00+00:00",
                },
                "available_ts": {
                    "first": "2026-01-02T14:30:05+00:00",
                    "last": "2026-01-02T14:35:05+00:00",
                },
            }
        ],
        "label_packs": [
            {
                "label_version_id": ids["label_version_id"],
                "label_spec_id": ids["label_spec_ref"],
                "event_ts": {
                    "first": "2026-01-02T14:30:00+00:00",
                    "last": "2026-01-02T14:35:00+00:00",
                },
                "label_available_ts": {
                    "first": "2026-01-02T14:35:00+00:00",
                    "last": "2026-01-02T14:40:00+00:00",
                },
            }
        ],
        "partition_scope": partition_scope or fixture["partition_scope"]["development"],
        "governance_metadata": dict(governance_metadata or {}),
    }


def _reason_codes(result: Any) -> set[str]:
    return {reason.code for reason in result.reasons}
