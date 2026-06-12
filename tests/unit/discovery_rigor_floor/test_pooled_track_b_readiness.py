from __future__ import annotations

import json
from pathlib import Path

import pytest

from alpha_system.governance.ids import GovernanceIdKind, generate_governance_id
from alpha_system.governance.pooled_hypothesis import (
    generate_pooled_hypothesis_id,
    track_b_minimum_satisfied,
    validate_pooled_hypothesis_record,
)
from alpha_system.governance.trial_ledger import create_trial_ledger_record
from alpha_system.governance.validation import GovernanceValidationError
from alpha_system.governance.variant_ledger import validate_variant_ledger_record

TRACK_B_TEMPLATE_ROOT = Path("research/discovery_rigor_floor_v1/track_b")
RERUN_STUDY_IDS = (
    "sspec_652fcc23a6f725b405612b8e",
    "sspec_676a012a4a4cdf3d169cd981",
    "sspec_1d87dfbe3d24810720f75014",
    "sspec_c2114a3c6c90595350151af0",
    "sspec_950ad6bb7063928d9ff8ea4f",
    "sspec_6088f0ed5b02b161bfb54943",
)
ALPHA_SPEC_ID = generate_governance_id(
    GovernanceIdKind.ALPHA_SPEC,
    {"name": "synthetic-pooled-track-b-readiness-alpha"},
)
REGISTERED_AT = "2026-06-12T12:00:00Z"
CODE_HASH = "a" * 64
CONFIG_HASH = "b" * 64


def pooled_payload(
    *,
    pool_kind: str = "cross_symbol",
    members: tuple[str, ...] = RERUN_STUDY_IDS[:3],
    horizons: tuple[str, ...] = ("5m",),
    symbols: tuple[str, ...] = ("ES", "NQ", "RTY"),
    variant_id: str = "pooled-cross-symbol-track-b-readiness",
) -> dict[str, object]:
    anchor_study_spec_id = members[0].split("#", maxsplit=1)[0]
    trial = create_trial_ledger_record(
        alpha_spec_id=ALPHA_SPEC_ID,
        study_spec_id=anchor_study_spec_id,
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
    variant_record = validate_variant_ledger_record(
        {
            "variant_id": variant_id,
            "alpha_spec_id": ALPHA_SPEC_ID,
            "study_spec_id": anchor_study_spec_id,
            "family_id": "pooled-track-b-readiness",
            "attempt_count": 1,
            "trial_ids": [trial.trial_id],
            "status": "PLANNED",
            "created_at": REGISTERED_AT,
        }
    ).to_dict()
    payload: dict[str, object] = {
        "mechanism_rationale": (
            "Synthetic readiness pooled contract ties one predeclared mechanism "
            "to fixed members before any Track-A metrics are available."
        ),
        "pool_kind": pool_kind,
        "members": list(members),
        "aggregation_rule": "equal_weight_mean",
        "horizons": list(horizons),
        "sessions": ["rth"],
        "symbols": list(symbols),
        "registered_at": REGISTERED_AT,
        "registered_before_metrics": True,
        "variant_ledger_record": variant_record,
    }
    payload["pooled_hypothesis_id"] = generate_pooled_hypothesis_id(payload)
    return payload


def test_track_b_minimum_helper_is_callable_from_readiness_checklist() -> None:
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


def test_track_b_templates_are_draft_not_registered_and_reference_relocked_ids() -> None:
    template_paths = sorted(TRACK_B_TEMPLATE_ROOT.glob("*POOLED_HYPOTHESIS_TEMPLATE.json"))

    assert {path.name for path in template_paths} == {
        "CROSS_HORIZON_POOLED_HYPOTHESIS_TEMPLATE.json",
        "CROSS_SYMBOL_POOLED_HYPOTHESIS_TEMPLATE.json",
    }
    for path in template_paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["template_status"] == "DRAFT_NOT_REGISTERED"
        assert payload["not_registered"] is True
        assert set(payload["candidate_study_spec_ids"]) == set(RERUN_STUDY_IDS)
        serialized = json.dumps(payload, sort_keys=True)
        for study_spec_id in RERUN_STUDY_IDS:
            assert study_spec_id in serialized


def test_track_b_draft_templates_are_unregistrable_as_is() -> None:
    template_paths = sorted(TRACK_B_TEMPLATE_ROOT.glob("*POOLED_HYPOTHESIS_TEMPLATE.json"))

    assert template_paths
    for path in template_paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        with pytest.raises(GovernanceValidationError) as wrapper_exc:
            validate_pooled_hypothesis_record(payload)
        wrapper_codes = {issue.code for issue in wrapper_exc.value.issues}
        assert "missing_required_field" in wrapper_codes
        assert "unknown_field" in wrapper_codes

        with pytest.raises(GovernanceValidationError) as inner_exc:
            validate_pooled_hypothesis_record(payload["registration_payload_template"])
        inner_codes = {issue.code for issue in inner_exc.value.issues}
        assert "invalid_field_type" in inner_codes
