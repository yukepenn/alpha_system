from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from alpha_system.cli import idea as idea_cli
from alpha_system.cli.main import main
from alpha_system.research_lane.testability_gate import CHECK_PATH_LABEL_TWO_CLASS

DOGFOOD_DIR = Path("research/idea_to_verdict_loop_v0/dogfood")
ES2024_IDEA = DOGFOOD_DIR / "track_b_es2024_120m.idea.yaml"
ES2020_IDEA = DOGFOOD_DIR / "track_b_es2020_120m.idea.yaml"
BASE_TS = datetime(2020, 3, 2, 14, 30, tzinfo=UTC)


def test_ivl_dogfood_track_b_gate_and_run_loop(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    resolver_obj = _DogfoodResolver()
    fast_probe_calls: list[str] = []

    def fake_fast_probe(card, setup, slice_spec, *, resolver):
        fast_probe_calls.append(slice_spec.slice_id)
        assert slice_spec.slice_id == "ES_2020_120m"
        assert resolver is resolver_obj
        return {
            "schema": "alpha_system.research_lane.fast_probe.v1",
            "status": "RECORDED",
            "study_kind": "context_not_equal_trigger",
            "stamp": "EXPLORATORY",
            "promotion_eligible": False,
            "mechanism_card": card.to_dict(),
            "setup_spec": setup.to_dict(),
            "slice_spec": slice_spec.to_dict(),
            "row_access": {
                "status": "resolved_local_only",
                "reason": "integration fixture supplied value-free dogfood handles",
                "fabricated_values": False,
                "row_counts": {
                    "feature_rows": {"context": 4, "trigger": 4},
                    "label_rows": {"path": 12},
                },
            },
            "surrogate_fdr_gate": {
                "threshold_verdict": "zero-pass-met",
                "gate_status": "PASSED",
                "run_count": 64,
                "gate_pass_count": 0,
                "error_count": 0,
            },
            "variant_ledger_binding": {
                "family_budget_check": {
                    "status": "RESPECTED",
                    "family_budget": 1,
                    "observed_count": 1,
                }
            },
            "power": {
                "n_eff": 4,
                "minimum_detectable_abs_ic": 1.0,
            },
            "readout": {
                "counts": {
                    "aligned_observation_count": 4,
                    "conditioned_observation_count": 4,
                },
                "promotion_eligible": False,
            },
            "verdict": "REJECT",
            "reason_code": "DATA_QUALITY",
            "why": "Dogfood fixture records loop behavior without interpretation.",
            "next_action": "Keep the readout value-free and promotion-ineligible.",
            "readout_id": "readout_ivl_p06_es2020_fixture",
        }

    monkeypatch.setattr(idea_cli, "FeatureLabelPackResolver", lambda: resolver_obj)
    monkeypatch.setattr(idea_cli, "fast_probe", fake_fast_probe)

    es2024_gate_status = main(["idea", "gate", ES2024_IDEA.as_posix()])
    es2024_gate = json.loads(capsys.readouterr().out)
    es2024_run_status = main(
        [
            "idea",
            "run",
            ES2024_IDEA.as_posix(),
            "--report-output",
            (tmp_path / "ES_2024_120m_REPORT.md").as_posix(),
        ]
    )
    es2024_run = json.loads(capsys.readouterr().out)

    assert es2024_gate_status == 0
    assert es2024_run_status == 0
    assert es2024_gate["overall_status"] == "DATA_GAP"
    assert es2024_gate["probe_invoked"] is False
    assert es2024_gate["shot_spent"] is False
    assert _check_status(es2024_gate, CHECK_PATH_LABEL_TWO_CLASS) == "DATA_GAP"
    assert es2024_run["memory"]["action"] == "requeue"
    assert es2024_run["memory"]["probe_spent"] is False
    assert es2024_run["promotion_eligible"] is False
    assert fast_probe_calls == []

    es2020_gate_status = main(["idea", "gate", ES2020_IDEA.as_posix()])
    es2020_gate = json.loads(capsys.readouterr().out)
    es2020_run_status = main(
        [
            "idea",
            "run",
            ES2020_IDEA.as_posix(),
            "--report-output",
            (tmp_path / "ES_2020_120m_REPORT.md").as_posix(),
        ]
    )
    es2020_run = json.loads(capsys.readouterr().out)

    assert es2020_gate_status == 0
    assert es2020_run_status == 0
    assert es2020_gate["overall_status"] == "PASS"
    assert _check_status(es2020_gate, CHECK_PATH_LABEL_TWO_CLASS) == "PASS"
    assert es2020_gate["probe_invoked"] is False
    assert es2020_gate["shot_spent"] is False
    assert es2020_run["testability"]["overall_status"] == "PASS"
    assert es2020_run["fast_readout"]["status"] == "RECORDED"
    assert es2020_run["fast_readout"]["promotion_eligible"] is False
    assert es2020_run["fast_readout"]["row_access"]["fabricated_values"] is False
    assert es2020_run["memory"]["action"] == "graveyard"
    assert es2020_run["memory"]["promotion_eligible"] is False
    assert es2020_run["memory"]["probe_spent"] is False
    assert "- verdict: REJECT" in es2020_run["report"]
    assert fast_probe_calls == ["ES_2020_120m"]


def _check_status(payload: dict[str, object], check_id: str) -> str:
    checks = payload["checks"]
    assert isinstance(checks, list)
    for check in checks:
        assert isinstance(check, dict)
        if check.get("check_id") == check_id:
            return str(check["status"])
    raise AssertionError(f"missing check {check_id}")


@dataclass(frozen=True, slots=True)
class _FeatureHandle:
    feature_version_id: str
    feature_request_id: str
    dataset_version_id: str
    partition_id: str
    feature_set_id: str = "fset_ivl_p06_dogfood"
    feature_set_version: str = "1"
    materialization_plan_id: str = "feature_plan_ivl_p06"
    first_event_ts: str = BASE_TS.isoformat()
    last_event_ts: str = (BASE_TS + timedelta(minutes=4)).isoformat()
    first_available_ts: str = (BASE_TS + timedelta(seconds=1)).isoformat()
    last_available_ts: str = (BASE_TS + timedelta(minutes=4, seconds=1)).isoformat()
    lifecycle_state: str = "REGISTERED"


@dataclass(frozen=True, slots=True)
class _LabelHandle:
    label_version_id: str
    label_spec_id: str
    dataset_version_id: str
    partition_id: str
    label_id: str = "path_target_before_stop"
    materialization_plan_id: str = "label_plan_ivl_p06"
    first_event_ts: str = BASE_TS.isoformat()
    last_event_ts: str = (BASE_TS + timedelta(minutes=4)).isoformat()
    first_label_available_ts: str = (BASE_TS + timedelta(minutes=120)).isoformat()
    last_label_available_ts: str = (BASE_TS + timedelta(minutes=124)).isoformat()
    lifecycle_state: str = "REGISTERED"


class _DogfoodResolver:
    def resolve_feature_packs(
        self,
        refs,
        *,
        expected_dataset_version_id,
        expected_feature_request_ids,
        partition_id,
    ):
        request_ids = tuple(expected_feature_request_ids)
        return tuple(
            _FeatureHandle(
                feature_version_id=ref,
                feature_request_id=request_ids[index],
                dataset_version_id=expected_dataset_version_id,
                partition_id=partition_id,
            )
            for index, ref in enumerate(refs)
        )

    def resolve_label_packs(
        self,
        refs,
        *,
        expected_dataset_version_id,
        expected_label_spec_ids,
        partition_id,
    ):
        label_spec_id = tuple(expected_label_spec_ids)[0]
        return tuple(
            _LabelHandle(
                label_version_id=ref,
                label_spec_id=label_spec_id,
                dataset_version_id=expected_dataset_version_id,
                partition_id=partition_id,
            )
            for ref in refs
        )
