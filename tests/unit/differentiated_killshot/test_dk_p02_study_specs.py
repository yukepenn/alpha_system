from __future__ import annotations

from pathlib import Path

from alpha_system.governance.serialization import deserialize
from alpha_system.governance.study_spec import validate_study_spec


SPEC_ROOT = Path("research/differentiated_substrate_v1/study_specs")

EXPECTED = {
    "day_of_week": {
        "mechanism_id": "day_of_week_effect",
        "horizons": ["30m"],
        "factor_ids": ["session_calendar_roll_day_of_week"],
        "variant_budget": 1,
        "family_budget": 4,
        "lock_status": "LOCKED",
    },
    "opex": {
        "mechanism_id": "opex_pinning",
        "horizons": ["30m"],
        "factor_ids": [
            "session_calendar_roll_is_opex_day_flag",
            "session_calendar_roll_is_quad_witch_day_flag",
        ],
        "variant_budget": 1,
        "family_budget": 6,
        "lock_status": "LOCKED",
    },
    "month_end": {
        "mechanism_id": "month_end_flow",
        "horizons": ["30m"],
        "factor_ids": [
            "session_calendar_roll_is_month_end_session_flag",
            "session_calendar_roll_is_quarter_end_session_flag",
        ],
        "variant_budget": 1,
        "family_budget": 6,
        "lock_status": "LOCKED",
    },
    "roll_week": {
        "mechanism_id": "roll_week_flow",
        "horizons": ["30m"],
        "factor_ids": ["session_calendar_roll_in_roll_window_flag"],
        "variant_budget": 1,
        "family_budget": 4,
        "lock_status": "LOCKED",
    },
    "open_close": {
        "mechanism_id": "open_close_auction_flow",
        "horizons": ["5m", "30m"],
        "factor_ids": [
            "session_calendar_roll_minutes_from_rth_open",
            "session_calendar_roll_minutes_to_rth_close",
        ],
        "variant_budget": 2,
        "family_budget": 4,
        "lock_status": "LOCKED",
    },
}


def test_dk_p02_track_a_study_specs_validate_and_declare_closed_surface() -> None:
    for name, expected in EXPECTED.items():
        payload = deserialize((SPEC_ROOT / f"{name}.json").read_text(encoding="utf-8"))
        spec = validate_study_spec(payload)
        scope = spec.dataset_scope

        assert scope["campaign_id"] == "DIFFERENTIATED_KILLSHOT_V1"
        assert scope["phase_id"] == "DK-P02"
        assert scope["mechanism_id"] == expected["mechanism_id"]
        assert scope["declared_conditioning_feature_family"] == "session_calendar_roll"
        assert scope["declared_conditioning_feature_ids"] == expected["factor_ids"]
        assert scope["primary_horizons"] == expected["horizons"]
        assert spec.variant_budget == expected["variant_budget"]
        assert spec.family_budget == expected["family_budget"]
        assert scope["pooling"]["instruments"] == ["ES", "NQ", "RTY"]
        assert scope["pooling"]["pooled_as_one_test_per_mechanism"] is True
        assert scope["lock_status"] == expected["lock_status"]
        assert scope["fdr_gate"]["real_metric_inspection_allowed_in_this_phase"] is False
        assert scope["artifact_notes"]["contains_real_metric_values"] is False

        label_roots = {
            str(lock["partition"]).split("_", 1)[0]
            for lock in scope["label_pack_locks"]
        }
        assert label_roots == {"ES", "NQ", "RTY"}
        if expected["lock_status"] == "LOCKED":
            assert "feature_pack_locks" in scope
            assert "missing_feature_pack_locks" not in scope
        else:
            assert "missing_feature_pack_locks" in scope
            assert "feature_pack_locks" not in scope

