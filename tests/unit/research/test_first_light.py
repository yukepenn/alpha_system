from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from alpha_system.governance.mechanism_card import EXPLORATORY_STAMP, MechanismCard
from alpha_system.governance.promotion import (
    EXPLORATORY_PROMOTION_REFUSAL_CODE,
    reject_exploratory_promotion_artifact,
)
from alpha_system.governance.setup_spec import SetupSpec
from alpha_system.governance.validation import GovernanceValidationError
from alpha_system.research.conditional_probe import compile_setup_spec_to_conditional_probe
from alpha_system.research.first_light import (
    DE_STACK_FACTOR_REFERENCE,
    DE_STACK_ISOLATED_IC,
    DE_STACK_OBSERVATION_COUNT,
    FIRST_LIGHT_CONTEXT_FACTOR_ID,
    FIRST_LIGHT_CONTEXT_FACTOR_VERSION,
    FIRST_LIGHT_HOLD_MINUTES,
    FIRST_LIGHT_TRIGGER_FACTOR_ID,
    FIRST_LIGHT_TRIGGER_FACTOR_VERSION,
    FIRST_LIGHT_VARIANT_ID,
    build_de_stack_single_factor_evidence,
    build_first_light_data_gap_evidence,
    build_first_light_mechanism_card,
    build_first_light_setup_spec,
    evaluate_first_light_probe,
)


def test_first_light_declaration_has_separate_context_and_trigger() -> None:
    mechanism = build_first_light_mechanism_card()
    setup = build_first_light_setup_spec(mechanism)
    probe = compile_setup_spec_to_conditional_probe(setup)

    assert mechanism.stamp == EXPLORATORY_STAMP
    assert setup.stamp == EXPLORATORY_STAMP
    assert setup.mechanism_id == mechanism.mechanism_id
    assert probe.context.factor_id == FIRST_LIGHT_CONTEXT_FACTOR_ID
    assert probe.trigger.factor_id == FIRST_LIGHT_TRIGGER_FACTOR_ID
    assert probe.context.factor_id != probe.trigger.factor_id
    assert setup.target["path_outcome"] == "target_before_stop"
    assert int(setup.hold_time["max_minutes"]) <= FIRST_LIGHT_HOLD_MINUTES


def test_first_light_probe_runs_on_synthetic_path_label_fixture() -> None:
    setup = build_first_light_setup_spec()
    readout = evaluate_first_light_probe(
        context_factor_values=_factor_rows(
            FIRST_LIGHT_CONTEXT_FACTOR_ID,
            FIRST_LIGHT_CONTEXT_FACTOR_VERSION,
            (0.9, 0.8, 0.4, 0.95),
        ),
        trigger_factor_values=_factor_rows(
            FIRST_LIGHT_TRIGGER_FACTOR_ID,
            FIRST_LIGHT_TRIGGER_FACTOR_VERSION,
            (1.0, -0.1, 1.0, 0.6),
        ),
        path_labels=_path_label_rows(setup.path_label),
        surrogate_run_count=3,
        created_at="2026-06-13T22:30:00Z",
    )

    assert readout.stamp == EXPLORATORY_STAMP
    assert readout.promotion_eligible is False
    assert readout.variant_id == FIRST_LIGHT_VARIANT_ID
    assert readout.outcome_source == "materialized_path_labels"
    assert readout.context_factor_id == FIRST_LIGHT_CONTEXT_FACTOR_ID
    assert readout.trigger_factor_id == FIRST_LIGHT_TRIGGER_FACTOR_ID
    assert readout.observation_counts["aligned_observation_count"] == 4
    assert readout.observation_counts["conditioned_observation_count"] == 3
    assert readout.variant_ledger_binding["family_budget_check"]["status"] == "RESPECTED"
    assert readout.surrogate_fdr_gate["threshold_verdict"] == "zero-pass-met"
    assert readout.power["factor_id"] == FIRST_LIGHT_TRIGGER_FACTOR_ID
    assert readout.power["mde_abs_ic"] is not None


def test_first_light_data_gap_evidence_is_bounded_and_value_free(tmp_path) -> None:
    evidence = build_first_light_data_gap_evidence(alpha_data_root=tmp_path)

    assert evidence["status"] == "INCONCLUSIVE"
    assert evidence["issue_code"] == "DATA_GAP"
    assert evidence["stamp"] == EXPLORATORY_STAMP
    assert evidence["promotion_eligible"] is False
    assert evidence["surrogate_fdr_gate"]["gate_status"] == "BLOCKED"
    assert evidence["power"]["n_eff"] == 0
    assert evidence["row_access"]["fabricated_values"] is False
    assert _contains_forbidden_claim_token(evidence) is False


def test_first_light_committed_artifacts_validate_against_contracts() -> None:
    first_light_root = Path("research/strategy_shaped_lane_v0/first_light")
    mechanism = MechanismCard.from_mapping(
        json.loads((first_light_root / "mechanism_card.json").read_text(encoding="utf-8"))
    )
    setup = SetupSpec.from_mapping(
        json.loads((first_light_root / "setup_spec.json").read_text(encoding="utf-8"))
    )
    evidence = json.loads((first_light_root / "EVIDENCE.json").read_text(encoding="utf-8"))
    de_stack = json.loads(
        Path("research/strategy_shaped_lane_v0/de_stack/EVIDENCE.json").read_text(
            encoding="utf-8"
        )
    )

    assert setup.mechanism_id == mechanism.mechanism_id
    assert setup.entry_context["factor_id"] != setup.event_trigger["factor_id"]
    assert evidence["mechanism_card"]["mechanism_id"] == mechanism.mechanism_id
    assert evidence["setup_spec"]["setup_spec_id"] == setup.setup_spec_id
    assert evidence["status"] == "INCONCLUSIVE"
    assert evidence["issue_code"] == "DATA_GAP"
    assert evidence["stamp"] == EXPLORATORY_STAMP
    assert de_stack["factor_reference"] == DE_STACK_FACTOR_REFERENCE
    assert de_stack["single_factor_engine"]["engine_changed"] is False
    assert _contains_forbidden_claim_token(evidence) is False
    assert _contains_forbidden_claim_token(de_stack) is False


def test_de_stack_single_factor_read_uses_existing_threshold_template() -> None:
    evidence = build_de_stack_single_factor_evidence()

    assert evidence["status"] == "RECORDED"
    assert evidence["promotion_eligible"] is False
    assert evidence["factor_reference"] == DE_STACK_FACTOR_REFERENCE
    assert evidence["single_factor_engine"]["template"] == "single_factor_threshold"
    assert evidence["single_factor_engine"]["sample_signal_type"] == "entry"
    assert evidence["single_factor_engine"]["engine_changed"] is False
    assert evidence["isolated_read"]["ic"] == pytest.approx(DE_STACK_ISOLATED_IC)
    assert evidence["isolated_read"]["observation_count"] == DE_STACK_OBSERVATION_COUNT
    assert evidence["surrogate_fdr_gate"]["threshold_verdict"] == "zero-pass-met"
    assert evidence["power"]["n_eff"] == DE_STACK_OBSERVATION_COUNT
    assert evidence["power"]["mde_abs_ic"] is not None


def test_first_light_exploratory_readout_is_refused_by_promotion_guard() -> None:
    setup = build_first_light_setup_spec()
    readout = evaluate_first_light_probe(
        context_factor_values=_factor_rows(
            FIRST_LIGHT_CONTEXT_FACTOR_ID,
            FIRST_LIGHT_CONTEXT_FACTOR_VERSION,
            (0.9, 0.8, 0.7),
        ),
        trigger_factor_values=_factor_rows(
            FIRST_LIGHT_TRIGGER_FACTOR_ID,
            FIRST_LIGHT_TRIGGER_FACTOR_VERSION,
            (1.0, 1.0, 1.0),
        ),
        path_labels=_path_label_rows(setup.path_label, count=3),
        surrogate_run_count=3,
        created_at="2026-06-13T22:30:00Z",
    )

    with pytest.raises(GovernanceValidationError) as exc_info:
        reject_exploratory_promotion_artifact(readout.to_dict(), field="first_light")

    assert exc_info.value.issues[0].code == EXPLORATORY_PROMOTION_REFUSAL_CODE


def _contains_forbidden_claim_token(value: object) -> bool:
    forbidden = (
        "pnl",
        "profit",
        "tradab",
        "sharpe",
        "return on",
        "expected value",
        "alpha found",
        "alpha exists",
    )
    if isinstance(value, Mapping):
        return any(_contains_forbidden_claim_token(item) for item in value.values())
    if isinstance(value, list | tuple):
        return any(_contains_forbidden_claim_token(item) for item in value)
    if isinstance(value, str):
        lowered = value.lower()
        return any(token in lowered for token in forbidden)
    return False


def _factor_rows(
    factor_id: str,
    factor_version: str,
    values: tuple[float, ...],
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for index, value in enumerate(values):
        event_ts = _event_ts(index)
        rows.append(
            {
                "factor_id": factor_id,
                "factor_version": factor_version,
                "instrument_id": "ES",
                "event_ts": _text(event_ts),
                "available_ts": _text(event_ts + timedelta(seconds=5)),
                "session_id": "CME:2026-01-02:RTH",
                "bar_index": index + 1,
                "value": value,
                "normalized_value": value,
                "quality_flags": ["synthetic"],
                "data_version": "data:v1",
                "compute_version": "test",
            }
        )
    return tuple(rows)


def _path_label_rows(path_label: str, *, count: int = 4) -> tuple[dict[str, object], ...]:
    target_values = (True, False, True, False)
    mfe_values = (0.05, 0.02, 0.01, 0.03)
    mae_values = (-0.01, -0.03, -0.02, -0.04)
    rows: list[dict[str, object]] = []
    for index in range(count):
        event_ts = _event_ts(index)
        rows.extend(
            [
                _label_row(path_label, event_ts, "target_before_stop", target_values[index]),
                _label_row(path_label, event_ts, "mfe_by_horizon", mfe_values[index]),
                _label_row(path_label, event_ts, "mae_by_horizon", mae_values[index]),
            ]
        )
    return tuple(rows)


def _label_row(
    path_label: str,
    event_ts: datetime,
    label_type: str,
    value: bool | float,
) -> dict[str, object]:
    horizon_end = event_ts + timedelta(minutes=120)
    return {
        "label_id": path_label,
        "instrument_id": "ES",
        "event_ts": _text(event_ts),
        "horizon": 7200,
        "label_type": label_type,
        "value": value,
        "path_metadata": {
            "session_id": "CME:2026-01-02:RTH",
            "label_version": "labels:v1",
            "horizon_end_ts": _text(horizon_end),
            "required_future_bars": 120,
            "observed_future_bars": 120,
            "entry_bar_index": 1,
            "target_hit_bar_index": 30,
            "path_label_binding": path_label,
        },
        "data_version": "data:v1",
        "label_available_ts": _text(horizon_end + timedelta(seconds=1)),
    }


def _event_ts(index: int) -> datetime:
    return datetime(2026, 1, 2, 14, 31 + index, tzinfo=UTC)


def _text(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")
