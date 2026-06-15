from __future__ import annotations

import json
import math
from enum import StrEnum
from pathlib import Path

import pytest

from alpha_system.governance import pooled_hypothesis as pooled_hypothesis_module
from alpha_system.governance.ids import GovernanceIdKind, generate_governance_id
from alpha_system.governance.pooled_hypothesis import (
    POOLED_HYPOTHESIS_ID_COMPONENT_FIELDS,
    POOLED_HYPOTHESIS_REQUIRED_FIELDS,
    PooledHypothesisRecord,
    PooledHypothesisRegistry,
    aggregate_pooled_metric,
    ensure_registration_precedes_metrics,
    generate_pooled_hypothesis_id,
    track_b_minimum_satisfied,
    validate_pooled_hypothesis_record,
)
from alpha_system.governance.trial_ledger import create_trial_ledger_record
from alpha_system.governance.validation import GovernanceValidationError
from alpha_system.governance.variant_ledger import VariantLedger, validate_variant_ledger_record

RERUN_STUDY_IDS = (
    "sspec_f6cbd88caa0445f0f56d81fd",
    "sspec_1604b063f3a3401208ee0239",
    "sspec_dec89a327a9c50957adca780",
    "sspec_840e8342564226f2c3257903",
    "sspec_c237c6a8ce40c2585836fae0",
    "sspec_533f665ec4ac063dbb664a54",
)
ALPHA_SPEC_ID = generate_governance_id(
    GovernanceIdKind.ALPHA_SPEC,
    {"name": "synthetic-pooled-track-b-alpha"},
)
REGISTERED_AT = "2026-06-12T12:00:00Z"
CODE_HASH = "a" * 64
CONFIG_HASH = "b" * 64


def variant_ledger_record(
    *,
    study_spec_id: str,
    variant_id: str,
    registered_at: str = REGISTERED_AT,
) -> dict[str, object]:
    trial = create_trial_ledger_record(
        alpha_spec_id=ALPHA_SPEC_ID,
        study_spec_id=study_spec_id,
        run_id=f"pooled-registration-{variant_id}",
        variant_id=variant_id,
        status="PLANNED",
        parameters={"registration": "pre_metric_pooled_hypothesis"},
        metrics_summary={},
        failure_reason=None,
        oos_touched_flag=False,
        locked_test_contamination_flag=False,
        code_hash=CODE_HASH,
        config_hash=CONFIG_HASH,
    )
    return validate_variant_ledger_record(
        {
            "variant_id": variant_id,
            "alpha_spec_id": ALPHA_SPEC_ID,
            "study_spec_id": study_spec_id,
            "family_id": "pooled-track-b",
            "attempt_count": 1,
            "trial_ids": [trial.trial_id],
            "status": "PLANNED",
            "created_at": registered_at,
        }
    ).to_dict()


def pooled_payload(
    *,
    pool_kind: str = "cross_symbol",
    members: tuple[str, ...] = RERUN_STUDY_IDS[:3],
    horizons: tuple[str, ...] = ("5m",),
    symbols: tuple[str, ...] = ("ES", "NQ", "RTY"),
    variant_id: str = "pooled-cross-symbol-track-b",
    registered_at: str = REGISTERED_AT,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "mechanism_rationale": (
            "Synthetic Track-B pooled contract ties one predeclared mechanism to "
            "fixed members before any Track-A metrics are available."
        ),
        "pool_kind": pool_kind,
        "members": list(members),
        "aggregation_rule": "equal_weight_mean",
        "horizons": list(horizons),
        "sessions": ["rth"],
        "symbols": list(symbols),
        "registered_at": registered_at,
        "registered_before_metrics": True,
        "variant_ledger_record": variant_ledger_record(
            study_spec_id=members[0].split("#", maxsplit=1)[0],
            variant_id=variant_id,
            registered_at=registered_at,
        ),
    }
    payload["pooled_hypothesis_id"] = generate_pooled_hypothesis_id(payload)
    return payload


def test_pooled_hypothesis_record_round_trips_and_id_changes() -> None:
    payload = pooled_payload()
    record = validate_pooled_hypothesis_record(payload)

    assert isinstance(record, PooledHypothesisRecord)
    assert record.pool_kind.value == "cross_symbol"
    assert record.aggregation_rule.value == "equal_weight_mean"
    assert PooledHypothesisRecord.from_canonical_json(record.to_canonical_json()) == record

    changed = dict(payload)
    changed["members"] = [*RERUN_STUDY_IDS[:3], RERUN_STUDY_IDS[3]]
    assert generate_pooled_hypothesis_id(changed) != payload["pooled_hypothesis_id"]
    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_pooled_hypothesis_record(changed)
    assert exc_info.value.issues[0].code == "pooled_hypothesis_id_mismatch"


def test_pooled_hypothesis_id_changes_for_each_contract_component(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert set(POOLED_HYPOTHESIS_ID_COMPONENT_FIELDS) == (
        set(POOLED_HYPOTHESIS_REQUIRED_FIELDS) - {"pooled_hypothesis_id"}
    )
    payload = pooled_payload()
    original_id = str(payload["pooled_hypothesis_id"])

    class ExtendedAggregationRule(StrEnum):
        EQUAL_WEIGHT_MEAN = "equal_weight_mean"
        INVERSE_VARIANCE_MEAN = "inverse_variance_mean"

    monkeypatch.setattr(
        pooled_hypothesis_module,
        "PooledAggregationRule",
        ExtendedAggregationRule,
    )
    changes: dict[str, object] = {
        "mechanism_rationale": (
            "Synthetic Track-B pooled contract uses a revised mechanism rationale "
            "that must create a distinct pooled hypothesis identifier."
        ),
        "members": [*RERUN_STUDY_IDS[:3], RERUN_STUDY_IDS[3]],
        "horizons": ["15m"],
        "sessions": ["eth"],
        "symbols": ["CL", "GC", "ZN"],
        "aggregation_rule": "inverse_variance_mean",
    }

    for field, replacement in changes.items():
        changed = dict(payload)
        changed[field] = replacement
        changed_id = generate_pooled_hypothesis_id(changed)

        assert changed_id.startswith("poolhyp_")
        assert changed_id != original_id, field


def test_registry_refuses_modified_payload_under_existing_id(tmp_path: Path) -> None:
    registry_path = tmp_path / "pooled-hypotheses.jsonl"
    registry_path.write_text("", encoding="utf-8")
    variant_ledger_path = tmp_path / "variant-ledger.jsonl"
    variant_ledger_path.write_text("", encoding="utf-8")
    registry = PooledHypothesisRegistry(registry_path)
    payload = pooled_payload()

    result = registry.register(payload, variant_ledger_path=variant_ledger_path)

    assert result.appended is True
    assert result.variant_ledger_appended_count == 1
    assert len(registry.load_records()) == 1
    assert len(VariantLedger(variant_ledger_path).load_records()) == 1

    tampered = dict(payload)
    tampered["mechanism_rationale"] = (
        "Synthetic Track-B pooled contract was edited after registration, which "
        "must be rejected under the original content-addressed identifier."
    )
    with pytest.raises(GovernanceValidationError) as exc_info:
        registry.register(tampered, variant_ledger_path=variant_ledger_path)

    assert exc_info.value.issues[0].code == "pooled_hypothesis_payload_conflict"
    assert "mechanism_rationale" in exc_info.value.issues[0].actual

    idempotent = registry.register(payload, variant_ledger_path=variant_ledger_path)
    assert idempotent.appended is False
    assert idempotent.variant_ledger_appended_count == 0
    assert len(registry.load_records()) == 1
    assert len(VariantLedger(variant_ledger_path).load_records()) == 1


def test_registry_refuses_backdated_new_registration_after_metrics_marker_exists(
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "pooled-hypotheses.jsonl"
    registry_path.write_text("", encoding="utf-8")
    variant_ledger_path = tmp_path / "variant-ledger.jsonl"
    variant_ledger_path.write_text("", encoding="utf-8")
    marker_path = tmp_path / "metrics-started.txt"
    marker_path.write_text("2026-06-12T12:00:00Z", encoding="utf-8")
    registry = PooledHypothesisRegistry(registry_path)
    payload = pooled_payload(
        registered_at="2026-06-12T11:00:00Z",
        variant_id="pooled-cross-symbol-track-b-backdated",
    )

    with pytest.raises(GovernanceValidationError) as exc_info:
        registry.register(
            payload,
            variant_ledger_path=variant_ledger_path,
            metrics_started_marker_path=marker_path,
        )

    assert exc_info.value.issues[0].code == "pooled_registration_window_closed"
    assert registry_path.read_text(encoding="utf-8") == ""
    assert variant_ledger_path.read_text(encoding="utf-8") == ""


def test_metrics_started_marker_enforces_pre_metric_ordering(tmp_path: Path) -> None:
    record = validate_pooled_hypothesis_record(pooled_payload())

    ensure_registration_precedes_metrics(record, tmp_path / "absent-marker.json")

    after_marker = tmp_path / "after-marker.json"
    after_marker.write_text(
        json.dumps({"metrics_started_at": "2026-06-12T12:00:01Z"}),
        encoding="utf-8",
    )
    ensure_registration_precedes_metrics(record, after_marker)

    before_marker = tmp_path / "before-marker.txt"
    before_marker.write_text("2026-06-12T11:59:59Z", encoding="utf-8")
    with pytest.raises(GovernanceValidationError) as exc_info:
        ensure_registration_precedes_metrics(record, before_marker)
    assert exc_info.value.issues[0].code == "pooled_registration_after_metrics_started"


def _effect_components() -> tuple[dict[str, object], ...]:
    return (
        {
            "component_ref": RERUN_STUDY_IDS[0],
            "metric_name": "synthetic_effect_size",
            "point_estimate": 0.3,
            "standard_error": 0.09,
            "n_eff": 100,
            "metadata": {"source": "component-a"},
        },
        {
            "component_ref": RERUN_STUDY_IDS[1],
            "metric_name": "synthetic_effect_size",
            "point_estimate": 0.6,
            "standard_error": 0.12,
            "n_eff": 90,
            "metadata": {"source": "component-b"},
        },
        {
            "component_ref": RERUN_STUDY_IDS[2],
            "metric_name": "synthetic_effect_size",
            "point_estimate": 0.0,
            "standard_error": 0.15,
            "n_eff": 80,
            "metadata": {"source": "component-c"},
        },
    )


def test_equal_weight_aggregation_reports_pool_and_components() -> None:
    # Genuinely-independent pool (rho=0) reproduces the historical independent
    # numbers exactly: back-compat for a pool whose components truly are
    # uncorrelated.
    payload = pooled_payload(members=RERUN_STUDY_IDS[:3])
    result = aggregate_pooled_metric(
        payload,
        _effect_components(),
        pooled_correlation=0.0,
    )

    assert result.metric_name == "synthetic_effect_size"
    assert result.point_estimate == pytest.approx(0.3)
    assert result.standard_error == pytest.approx(math.sqrt(0.09**2 + 0.12**2 + 0.15**2) / 3)
    assert result.n_eff == 270
    assert result.assumed_correlation == pytest.approx(0.0)
    payload_dict = result.to_dict()
    assert payload_dict["pooled_result"]["point_estimate"] == pytest.approx(0.3)
    assert payload_dict["assumed_correlation"] == pytest.approx(0.0)
    assert payload_dict["pool_kind"] == "cross_symbol"
    assert len(payload_dict["components"]) == 3


def test_cross_horizon_default_uses_worst_case_correlation() -> None:
    # CROSS_HORIZON pools overlap on the same bars; the default is the worst-case
    # rho=1.0, so the pooled SE equals mean(se_i) and is STRICTLY LARGER than the
    # naive sqrt(sum se^2)/K, and n_eff is floored at the weakest component.
    horizon_members = tuple(
        f"{RERUN_STUDY_IDS[0]}#horizon={horizon}" for horizon in ("60m", "120m", "240m")
    )
    payload = pooled_payload(
        pool_kind="cross_horizon",
        members=horizon_members,
        horizons=("60m", "120m", "240m"),
        symbols=("ES",),
        variant_id="pooled-cross-horizon-overlap",
    )
    components = tuple(
        {**component, "component_ref": ref}
        for component, ref in zip(_effect_components(), horizon_members, strict=True)
    )
    result = aggregate_pooled_metric(payload, components)

    naive_se = math.sqrt(0.09**2 + 0.12**2 + 0.15**2) / 3
    mean_se = (0.09 + 0.12 + 0.15) / 3
    assert result.assumed_correlation == pytest.approx(1.0)
    assert result.standard_error == pytest.approx(mean_se)
    assert result.standard_error > naive_se  # rail is no longer understated
    # rho=1 -> n_eff floored at min(n_eff_i)=80, never the naive sum of 270.
    assert result.n_eff == 80


def test_cross_symbol_default_between_independent_and_worst_case() -> None:
    # CROSS_SYMBOL default rho=0.6 sits strictly between the independent SE
    # (rho=0) and the fully-redundant worst case (rho=1).
    payload = pooled_payload(members=RERUN_STUDY_IDS[:3])
    components = _effect_components()
    independent = aggregate_pooled_metric(payload, components, pooled_correlation=0.0)
    worst_case = aggregate_pooled_metric(payload, components, pooled_correlation=1.0)
    result = aggregate_pooled_metric(payload, components)  # default 0.6

    assert result.assumed_correlation == pytest.approx(0.6)
    assert independent.standard_error < result.standard_error < worst_case.standard_error
    # n_eff is discounted, not summed, and never exceeds the independent sum.
    assert independent.n_eff == 270
    assert independent.n_eff >= result.n_eff >= worst_case.n_eff


def test_worst_case_correlation_collapses_se_to_mean() -> None:
    payload = pooled_payload(members=RERUN_STUDY_IDS[:3])
    result = aggregate_pooled_metric(
        payload, _effect_components(), pooled_correlation=1.0
    )
    assert result.standard_error == pytest.approx((0.09 + 0.12 + 0.15) / 3)
    assert result.n_eff == 80  # floored at min(n_eff_i)


def test_pooled_correlation_must_be_in_unit_interval() -> None:
    payload = pooled_payload(members=RERUN_STUDY_IDS[:3])
    with pytest.raises(GovernanceValidationError) as exc_info:
        aggregate_pooled_metric(payload, _effect_components(), pooled_correlation=1.5)
    assert exc_info.value.issues[0].code == "invalid_pooled_correlation"


def test_aggregation_rejects_dropped_or_extra_components() -> None:
    payload = pooled_payload(members=RERUN_STUDY_IDS[:3])

    with pytest.raises(GovernanceValidationError) as exc_info:
        aggregate_pooled_metric(
            payload,
            (
                {
                    "component_ref": RERUN_STUDY_IDS[0],
                    "metric_name": "synthetic_effect_size",
                    "point_estimate": 0.3,
                    "standard_error": None,
                    "n_eff": None,
                    "metadata": {},
                },
            ),
        )

    assert exc_info.value.issues[0].code == "pooled_component_membership_mismatch"


def test_track_b_minimum_requires_cross_symbol_and_cross_horizon() -> None:
    cross_symbol = validate_pooled_hypothesis_record(pooled_payload())
    horizon_members = tuple(
        f"{RERUN_STUDY_IDS[0]}#horizon={horizon}" for horizon in ("5m", "15m", "30m")
    )
    cross_horizon = validate_pooled_hypothesis_record(
        pooled_payload(
            pool_kind="cross_horizon",
            members=horizon_members,
            horizons=("5m", "15m", "30m"),
            symbols=("ES",),
            variant_id="pooled-cross-horizon-track-b",
        )
    )

    assert track_b_minimum_satisfied(
        (cross_symbol, cross_horizon),
        (*RERUN_STUDY_IDS[:3], *horizon_members),
    )
    assert not track_b_minimum_satisfied((cross_symbol,), RERUN_STUDY_IDS[:3])
    assert not track_b_minimum_satisfied(
        (cross_symbol, cross_horizon),
        ("sspec_000000000000000000000000",),
    )
