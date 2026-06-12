from __future__ import annotations

import json
from pathlib import Path

from alpha_system.cli.main import main
from alpha_system.governance.ids import GovernanceIdKind, generate_governance_id
from alpha_system.governance.pooled_hypothesis import generate_pooled_hypothesis_id
from alpha_system.governance.trial_ledger import create_trial_ledger_record
from alpha_system.governance.variant_ledger import validate_variant_ledger_record

RERUN_STUDY_IDS = (
    "sspec_652fcc23a6f725b405612b8e",
    "sspec_676a012a4a4cdf3d169cd981",
    "sspec_1d87dfbe3d24810720f75014",
)
ALPHA_SPEC_ID = generate_governance_id(
    GovernanceIdKind.ALPHA_SPEC,
    {"name": "synthetic-pooled-track-b-cli-alpha"},
)
REGISTERED_AT = "2026-06-12T12:00:00Z"
CODE_HASH = "a" * 64
CONFIG_HASH = "b" * 64


def pooled_payload() -> dict[str, object]:
    variant_id = "pooled-cross-symbol-track-b-cli"
    trial = create_trial_ledger_record(
        alpha_spec_id=ALPHA_SPEC_ID,
        study_spec_id=RERUN_STUDY_IDS[0],
        run_id="pooled-registration-cli",
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
            "study_spec_id": RERUN_STUDY_IDS[0],
            "family_id": "pooled-track-b-cli",
            "attempt_count": 1,
            "trial_ids": [trial.trial_id],
            "status": "PLANNED",
            "created_at": REGISTERED_AT,
        }
    ).to_dict()
    payload: dict[str, object] = {
        "mechanism_rationale": (
            "Synthetic CLI pooled contract ties one predeclared mechanism to "
            "fixed members before any Track-A metrics are available."
        ),
        "pool_kind": "cross_symbol",
        "members": list(RERUN_STUDY_IDS),
        "aggregation_rule": "equal_weight_mean",
        "horizons": ["5m"],
        "sessions": ["rth"],
        "symbols": ["ES", "NQ", "RTY"],
        "registered_at": REGISTERED_AT,
        "registered_before_metrics": True,
        "variant_ledger_record": variant_record,
    }
    payload["pooled_hypothesis_id"] = generate_pooled_hypothesis_id(payload)
    return payload


def test_register_pooled_hypothesis_and_list_json_are_read_only(
    tmp_path: Path,
    capsys,
) -> None:
    registry_path = tmp_path / "pooled-hypotheses.jsonl"
    registry_path.write_text("", encoding="utf-8")
    variant_ledger_path = tmp_path / "variant-ledger.jsonl"
    variant_ledger_path.write_text("", encoding="utf-8")
    pooled_path = tmp_path / "pooled.json"
    pooled_path.write_text(json.dumps(pooled_payload(), sort_keys=True), encoding="utf-8")

    register_code = main(
        [
            "governance",
            "register-pooled-hypothesis",
            str(pooled_path),
            "--registry-path",
            str(registry_path),
            "--variant-ledger-path",
            str(variant_ledger_path),
        ]
    )
    registered = json.loads(capsys.readouterr().out)

    assert register_code == 0
    assert registered["status"] == "ok"
    assert registered["command"] == "register-pooled-hypothesis"
    assert registered["appended"] is True
    assert registered["variant_ledger_appended_count"] == 1

    before_registry = registry_path.read_text(encoding="utf-8")
    before_variant_ledger = variant_ledger_path.read_text(encoding="utf-8")
    list_code = main(
        [
            "governance",
            "pooled-hypotheses",
            "list",
            "--registry-path",
            str(registry_path),
            "--json",
        ]
    )
    listed = json.loads(capsys.readouterr().out)

    assert list_code == 0
    assert listed["status"] == "ok"
    assert listed["count"] == 1
    assert listed["pooled_hypotheses"][0]["pool_kind"] == "cross_symbol"
    assert registry_path.read_text(encoding="utf-8") == before_registry
    assert variant_ledger_path.read_text(encoding="utf-8") == before_variant_ledger


def test_register_pooled_hypothesis_cli_surfaces_marker_ordering(
    tmp_path: Path,
    capsys,
) -> None:
    registry_path = tmp_path / "pooled-hypotheses.jsonl"
    registry_path.write_text("", encoding="utf-8")
    variant_ledger_path = tmp_path / "variant-ledger.jsonl"
    variant_ledger_path.write_text("", encoding="utf-8")
    marker_path = tmp_path / "metrics-started.txt"
    marker_path.write_text("2026-06-12T11:59:59Z", encoding="utf-8")
    pooled_path = tmp_path / "pooled.json"
    pooled_path.write_text(json.dumps(pooled_payload(), sort_keys=True), encoding="utf-8")

    code = main(
        [
            "governance",
            "register-pooled-hypothesis",
            str(pooled_path),
            "--registry-path",
            str(registry_path),
            "--variant-ledger-path",
            str(variant_ledger_path),
            "--metrics-started-marker",
            str(marker_path),
        ]
    )
    payload = json.loads(capsys.readouterr().err)

    assert code == 2
    assert payload["status"] == "rejected"
    assert payload["issues"][0]["code"] == "pooled_registration_window_closed"
