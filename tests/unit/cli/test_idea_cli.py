from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from alpha_system.cli import idea as idea_cli
from alpha_system.cli.main import build_parser, main
from alpha_system.governance.ids import GovernanceIdKind, generate_governance_id

FIXTURE_IDEA = Path("research/idea_to_verdict_loop_v0/fixtures/day_of_week.idea.yaml")
DATASET_VERSION_ID = "dsv_cli_resolving_slice"
PARTITION_ID = "ES_2020_120m"
FEATURE_VERSION_ID = "fver_" + "1" * 64
LABEL_VERSION_ID = "lver_" + "2" * 64
FEATURE_REQUEST_ID = "freq_" + "3" * 24
BASE_TS = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)


def test_idea_command_is_registered() -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["idea", "validate", "--help"])

    assert exc_info.value.code == 0


def test_idea_gate_alias_is_registered() -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["idea", "gate", "--help"])

    assert exc_info.value.code == 0


def test_idea_run_command_is_registered() -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["idea", "run", "--help"])

    assert exc_info.value.code == 0


def test_idea_validate_cli_emits_canonical_bundle(capsys) -> None:
    status = main(["idea", "validate", FIXTURE_IDEA.as_posix()])
    captured = capsys.readouterr()

    assert status == 0
    assert captured.err == ""
    payload = json.loads(captured.out)
    assert payload["idea_draft"]["study_kind"] == "main_effect"
    assert payload["alpha_spec"]["alpha_spec_id"].startswith("aspec_")
    assert payload["hypothesis_card"]["hypothesis_id"].startswith("hyp_")
    assert payload["mechanism_card"]["mechanism_id"].startswith("mech_")
    assert payload["mechanism_card"]["stamp"] == "EXPLORATORY"
    assert payload["setup_spec"] is None
    assert "study_kind" not in payload["alpha_spec"]
    assert "study_kind" not in payload["mechanism_card"]


@pytest.mark.parametrize("command", ["testability", "gate"])
def test_idea_testability_cli_returns_pre_test_data_gap_without_slice(
    capsys,
    command: str,
) -> None:
    status = main(["idea", command, FIXTURE_IDEA.as_posix()])
    captured = capsys.readouterr()

    assert status == 0
    assert captured.err == ""
    payload = json.loads(captured.out)
    assert payload["overall_status"] == "DATA_GAP"
    assert payload["verdict"] == "DATA_GAP"
    assert payload["pre_test"] is True
    assert payload["shot_spent"] is False
    assert payload["probe_invoked"] is False
    assert {check["status"] for check in payload["checks"]} == {"DATA_GAP"}


@pytest.mark.parametrize(
    "gap_field",
    ["source", "cost_sensitivity", "variant_budget", "duplicate_exposure"],
)
def test_idea_validate_cli_fails_closed_on_missing_mechanism_gap_fields(
    tmp_path: Path,
    capsys,
    gap_field: str,
) -> None:
    payload = json.loads(FIXTURE_IDEA.read_text(encoding="utf-8"))
    del payload["mechanism_card"][gap_field]
    idea_path = tmp_path / f"missing-{gap_field}.idea.yaml"
    idea_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")

    status = main(["idea", "validate", idea_path.as_posix()])
    captured = capsys.readouterr()

    assert status == 2
    assert captured.out == ""
    error = json.loads(captured.err)
    assert error["error"] == "idea_validation_failed"
    assert error["issues"][0]["code"] == "missing_required_field"
    assert error["issues"][0]["field"] == gap_field


def test_idea_run_fixture_short_circuits_data_gap_to_requeue(
    tmp_path: Path,
    capsys,
) -> None:
    report_path = tmp_path / "REPORT.md"

    status = main(
        [
            "idea",
            "run",
            FIXTURE_IDEA.as_posix(),
            "--report-output",
            report_path.as_posix(),
            "--no-persist",
        ]
    )
    captured = capsys.readouterr()

    assert status == 0
    assert captured.err == ""
    payload = json.loads(captured.out)
    assert payload["promotion_eligible"] is False
    assert payload["testability"]["overall_status"] == "DATA_GAP"
    assert payload["testability"]["shot_spent"] is False
    assert payload["testability"]["probe_invoked"] is False
    assert payload["fast_readout"]["issue_code"] == "DATA_GAP"
    assert payload["fast_readout"]["promotion_eligible"] is False
    assert payload["fast_readout"]["row_access"]["fabricated_values"] is False
    assert payload["memory"]["action"] == "requeue"
    assert payload["memory"]["record_type"] == "RequeuedVerdictRecord"
    assert payload["memory"]["memory_record"]["requeue_reason"] == (
        "UNDERPOWERED_EVIDENCE_ACCRUAL"
    )
    assert payload["memory"]["probe_spent"] is False
    assert payload["memory"]["promotion_eligible"] is False
    assert payload["memory"]["exploratory_refusal"]["status"] == "refused"
    assert payload["report_path"] == report_path.as_posix()
    report = report_path.read_text(encoding="utf-8")
    assert report == payload["report"]
    assert "## Final Verdict" in report
    assert "- verdict: DATA_GAP" in report


def test_idea_run_persists_route_to_isolated_memory_dir(tmp_path: Path, capsys) -> None:
    memory_dir = tmp_path / "research_memory"

    status = main(
        [
            "idea",
            "run",
            FIXTURE_IDEA.as_posix(),
            "--memory-dir",
            memory_dir.as_posix(),
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert status == 0
    # day_of_week fixture short-circuits to a DATA_GAP requeue route.
    assert payload["memory"]["action"] == "requeue"
    persisted = payload["memory_persisted_path"]
    assert persisted == (memory_dir / "requeue.jsonl").as_posix()
    rows = [json.loads(line) for line in (memory_dir / "requeue.jsonl").read_text().splitlines()]
    assert len(rows) == 1
    assert rows[0]["promotion_eligible"] is False


def test_idea_run_no_persist_writes_nothing(tmp_path: Path, capsys) -> None:
    memory_dir = tmp_path / "research_memory"

    status = main(
        [
            "idea",
            "run",
            FIXTURE_IDEA.as_posix(),
            "--memory-dir",
            memory_dir.as_posix(),
            "--no-persist",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert status == 0
    assert payload["memory_persisted_path"] is None
    assert not memory_dir.exists()


def _shelve_signal(memory_dir: Path, *, signal_ref: str, factor_id: str) -> None:
    from alpha_system.agent_factory.memory.store import persist_route

    persist_route(
        route_result={
            "verdict": "INCONCLUSIVE",
            "action": "reviewer_pending_shelf",
            "record_type": "SignalPendingReviewerRecord",
            "alpha_spec_id": "aspec_cli",
            "promotion_eligible": False,
            "memory_record": {
                "requires_reviewer": True,
                "eligible": False,
                "original_verdict_ref": signal_ref,
            },
        },
        idea={"alpha_spec_id": "aspec_cli", "mechanism_id": "mech_cli"},
        readout={
            "study_kind": "main_effect",
            "slice_spec": {
                "slice_id": "ES_2020_60m",
                "feature_inputs": [{"role": "factor", "factor_id": factor_id, "pack_ref": "fver"}],
                "label_inputs": [{"role": "label", "label_id": "cost_adjusted_fwd_ret"}],
            },
            "readout": {
                "factor_diagnostics_report": {
                    "quality_summary": {"pearson_ic": -0.05, "rank_ic": -0.02}
                }
            },
        },
        verdict={"verdict": "INCONCLUSIVE", "reason_code": "SIGNAL_PENDING_REVIEWER"},
        created_at="2026-06-15T00:00:00Z",
        memory_dir=memory_dir,
    )


def test_idea_review_list_and_adjudicate(tmp_path: Path, capsys) -> None:
    memory_dir = tmp_path / "research_memory"
    _shelve_signal(memory_dir, signal_ref="readout:sig_a", factor_id="base_ohlcv_distance_to_vwap")

    assert main(["idea", "review", "list", "--memory-dir", memory_dir.as_posix()]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert len(listed["pending_signals"]) == 1
    assert listed["pending_signals"][0]["signal_ref"] == "readout:sig_a"

    status = main(
        [
            "idea",
            "review",
            "adjudicate",
            "readout:sig_a",
            "--outcome",
            "PASS_WITH_WARNINGS",
            "--reviewer-id",
            "adversarial_reviewer_01",
            "--independence-statement",
            "Independent of the signal producer; no authoring access.",
            "--warning",
            "Exploratory IC only; requires trusted StudySpec.",
            "--memory-dir",
            memory_dir.as_posix(),
        ]
    )
    adjudicated = json.loads(capsys.readouterr().out)
    assert status == 0
    assert adjudicated["adjudication"]["routing_intent"] == "CONFIRMED_FOR_TRUSTED_STUDY"
    assert adjudicated["adjudication"]["promotion_eligible"] is False

    assert main(["idea", "review", "list", "--memory-dir", memory_dir.as_posix()]) == 0
    assert json.loads(capsys.readouterr().out)["pending_signals"] == []


def test_idea_gate_and_run_consume_embedded_resolving_slice(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    payload = _context_idea_payload_with_slice()
    idea_path = tmp_path / "resolving-slice.idea.yaml"
    report_path = tmp_path / "REPORT.md"
    idea_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    resolver_obj = _Resolver(label_spec_id=_path_label_id())
    fast_probe_calls: list[str] = []

    def fake_resolver():
        return resolver_obj

    def fake_fast_probe(card, setup, slice_spec, *, resolver):
        fast_probe_calls.append(slice_spec.slice_id)
        assert slice_spec.slice_id == "resolving-slice"
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
                "reason": "unit-test resolver supplied value-free handles",
                "fabricated_values": False,
                "row_counts": {
                    "feature_rows": {"context": 4, "trigger": 4},
                    "label_rows": {"path": 12},
                },
            },
            "surrogate_fdr_gate": {
                "threshold_verdict": "zero-pass-met",
                "gate_status": "PASSED",
                "run_count": 8,
                "gate_pass_count": 0,
                "error_count": 0,
            },
            "power": {
                "n_eff": 4,
                "minimum_detectable_abs_ic": 1.0,
            },
            "readout": {
                "counts": {"conditioned_observation_count": 4},
                "promotion_eligible": False,
            },
            "verdict": "REJECT",
            "reason_code": "DATA_QUALITY",
            "why": "Deterministic regression readout carries no interpretation.",
            "next_action": "Keep the fixture value-free.",
            "readout_id": "readout_cli_resolving_slice",
        }

    monkeypatch.setattr(idea_cli, "FeatureLabelPackResolver", fake_resolver)
    monkeypatch.setattr(idea_cli, "fast_probe", fake_fast_probe)

    validate_status = main(["idea", "validate", idea_path.as_posix()])
    validate_out = json.loads(capsys.readouterr().out)
    gate_status = main(["idea", "gate", idea_path.as_posix()])
    gate_out = json.loads(capsys.readouterr().out)
    run_status = main(
        [
            "idea",
            "run",
            idea_path.as_posix(),
            "--report-output",
            report_path.as_posix(),
            "--no-persist",
        ]
    )
    run_out = json.loads(capsys.readouterr().out)

    assert validate_status == 0
    assert gate_status == 0
    assert run_status == 0
    assert validate_out["alpha_spec"]["alpha_spec_id"] == run_out["idea_draft"]["alpha_spec_id"]
    assert validate_out["mechanism_card"]["mechanism_id"] == (
        run_out["idea_draft"]["mechanism_id"]
    )
    assert validate_out["setup_spec"]["setup_spec_id"] == run_out["idea_draft"]["setup_spec_id"]
    assert gate_out["overall_status"] == "PASS"
    assert gate_out["slice_id"] == "resolving-slice"
    assert gate_out["probe_invoked"] is False
    assert gate_out["shot_spent"] is False
    assert run_out["testability"]["overall_status"] == "PASS"
    assert run_out["testability"]["slice_id"] == "resolving-slice"
    assert run_out["promotion_eligible"] is False
    assert run_out["fast_readout"]["promotion_eligible"] is False
    assert run_out["fast_readout"]["row_access"]["fabricated_values"] is False
    assert run_out["memory"]["action"] == "graveyard"
    assert run_out["memory"]["promotion_eligible"] is False
    assert run_out["memory"]["probe_spent"] is False
    assert report_path.read_text(encoding="utf-8") == run_out["report"]
    assert "- verdict: REJECT" in run_out["report"]
    assert fast_probe_calls == ["resolving-slice"]
    assert resolver_obj.feature_calls == [FEATURE_VERSION_ID, FEATURE_VERSION_ID]
    assert resolver_obj.label_calls == [LABEL_VERSION_ID, LABEL_VERSION_ID]


def _context_idea_payload_with_slice() -> dict[str, Any]:
    path_label_id = _path_label_id()
    return {
        "source": "unit:embedded_resolving_slice",
        "study_kind": "context_not_equal_trigger",
        "hypothesis_card": {
            "title": "Embedded resolving slice CLI fixture",
            "family": "idea_to_verdict_fixture",
            "rationale": (
                "A value-free fixture can prove the front door preserves slice "
                "metadata for downstream gates."
            ),
            "expected_mechanism": (
                "A declared context and separate trigger may be evaluated only "
                "after the embedded slice passes pre-test checks."
            ),
            "falsification_criteria": [
                "Fail the fixture if the embedded slice cannot satisfy pre-test checks.",
                "Block the fixture if the context and trigger are not declared separately.",
            ],
            "risks": [
                "The fixture has no empirical interpretation.",
                "Future rows must remain unavailable until a governed slice is selected.",
            ],
            "author": "codex-fixture",
            "created_at": "2026-06-14T00:00:00Z",
        },
        "alpha_spec": {
            "target_instruments": ["ES"],
            "data_assumptions": {
                "coverage": "Unit-test slice metadata is supplied in the idea file.",
                "source": "No market data is loaded by this CLI regression.",
            },
            "factor_inputs": ["context_factor", "trigger_factor"],
            "label_references": [path_label_id],
            "exclusion_rules": [
                "Exclude rows where context or trigger availability is unknown.",
                "Do not interpret any readout from this unit-test fixture.",
            ],
            "timestamp_assumptions": {
                "availability": "Fixture context and trigger handles are point-in-time.",
                "timezone": "Fixture timestamps use UTC.",
            },
            "cost_assumptions": {
                "model": "No execution cost estimate is produced by this fixture.",
                "scope": "Value-free regression only.",
            },
            "expected_failure_modes": [
                "The bounded slice may be unavailable in a real executor.",
                "Duplicate exposure could block later interpretation.",
            ],
            "promotion_criteria": [
                "No promotion is allowed from this exploratory fixture.",
                "Reviewer-gated evidence would be required for future routing.",
            ],
            "created_by": "codex-fixture",
            "created_at": "2026-06-14T00:00:00Z",
        },
        "mechanism_card": {
            "source": "unit:embedded_resolving_slice",
            "rationale": "A declared context and separate trigger remain value-free inputs.",
            "expected_mechanism": (
                "The context gates rows while the trigger marks a separate event."
            ),
            "expected_direction": "undirected",
            "horizon": "120m",
            "session": "RTH",
            "required_features": ["context_factor", "trigger_factor"],
            "required_labels": ["target_before_stop"],
            "cost_sensitivity": {"scope": "value-free regression"},
            "variant_budget": 1,
            "duplicate_exposure": {
                "status": "bounded",
                "family_id": "embedded_resolving_slice_fixture",
                "variant_id": "baseline",
            },
        },
        "setup_spec": {
            "entry_context": {
                "factor_id": "context_factor",
                "factor_version": "ctx:v1",
                "value_field": "normalized_value",
                "operator": ">=",
                "threshold": 0.5,
            },
            "event_trigger": {
                "factor_id": "trigger_factor",
                "factor_version": "trg:v1",
                "value_field": "normalized_value",
                "operator": ">",
                "threshold": 0.0,
            },
            "regime_filter": {"session": "RTH", "policy": "unit fixture"},
            "confirmation": {"policy": "no additional confirmation beyond declared trigger"},
            "invalidation": {"policy": "fixed path"},
            "stop": {"binding": "fixed stop"},
            "target": {"binding": "fixed target"},
            "hold_time": {"max_minutes": 120, "horizon": "120m"},
            "horizon": "120m",
            "path_label": path_label_id,
            "allowed_variants": ["baseline"],
            "forbidden_post_hoc_changes": ["No changes after readout."],
        },
        "slices": {
            "resolving-slice": {
                "slice_id": "resolving-slice",
                "study_kind": "context_not_equal_trigger",
                "dataset_version_id": DATASET_VERSION_ID,
                "partition_id": PARTITION_ID,
                "instrument_id": "ES",
                "session_id": "ES:RTH",
                "data_version": DATASET_VERSION_ID,
                "feature_pack_refs": [FEATURE_VERSION_ID],
                "label_pack_refs": [LABEL_VERSION_ID],
                "feature_request_ids": [FEATURE_REQUEST_ID],
                "label_spec_ids": [path_label_id],
                "path_label_class_counts": {"false": 2, "true": 2},
                "n_eff": 4,
                "minimum_detectable_effect": 1.0,
                "available_ts_satisfiable": True,
                "surrogate_fdr_requirement": "zero-pass-met",
                "features": [
                    {
                        "role": "context",
                        "factor_id": "context_factor",
                        "factor_version": "ctx:v1",
                        "relative_path": "features/context.parquet",
                        "pack_ref": FEATURE_VERSION_ID,
                        "feature_request_id": FEATURE_REQUEST_ID,
                    },
                    {
                        "role": "trigger",
                        "factor_id": "trigger_factor",
                        "factor_version": "trg:v1",
                        "relative_path": "features/trigger.parquet",
                        "pack_ref": FEATURE_VERSION_ID,
                        "feature_request_id": FEATURE_REQUEST_ID,
                    },
                ],
                "labels": [
                    {
                        "role": "path",
                        "label_id": path_label_id,
                        "relative_path": "labels/path.parquet",
                        "pack_ref": LABEL_VERSION_ID,
                        "label_spec_id": path_label_id,
                    }
                ],
                "label_version_map": {
                    LABEL_VERSION_ID: ["target_before_stop", "bool"],
                },
                "horizon_seconds": 7200,
                "required_future_bars": 120,
                "materialized_label_version": LABEL_VERSION_ID,
                "surrogate_run_count": 8,
                "surrogate_base_seed": 0,
                "family_id": "embedded_resolving_slice_fixture",
                "family_budget": 1,
                "variant_id": "baseline",
                "created_at": "2026-06-14T00:00:00Z",
            }
        },
    }


def _path_label_id() -> str:
    return generate_governance_id(
        GovernanceIdKind.LABEL_SPEC,
        {"family": "fixture_path", "name": "target_before_stop", "version": 1},
    )


@dataclass(frozen=True, slots=True)
class _FeatureHandle:
    feature_version_id: str = FEATURE_VERSION_ID
    feature_request_id: str = FEATURE_REQUEST_ID
    feature_set_id: str = "fset_cli"
    feature_set_version: str = "1"
    dataset_version_id: str = DATASET_VERSION_ID
    partition_id: str = PARTITION_ID
    materialization_plan_id: str = "feature_plan_cli"
    first_event_ts: str = BASE_TS.isoformat()
    last_event_ts: str = (BASE_TS + timedelta(minutes=4)).isoformat()
    first_available_ts: str = (BASE_TS + timedelta(seconds=1)).isoformat()
    last_available_ts: str = (BASE_TS + timedelta(minutes=4, seconds=1)).isoformat()
    lifecycle_state: str = "REGISTERED"


@dataclass(frozen=True, slots=True)
class _LabelHandle:
    label_spec_id: str
    label_version_id: str = LABEL_VERSION_ID
    label_id: str = "path_target_before_stop"
    dataset_version_id: str = DATASET_VERSION_ID
    partition_id: str = PARTITION_ID
    materialization_plan_id: str = "label_plan_cli"
    first_event_ts: str = BASE_TS.isoformat()
    last_event_ts: str = (BASE_TS + timedelta(minutes=4)).isoformat()
    first_label_available_ts: str = (BASE_TS + timedelta(minutes=120)).isoformat()
    last_label_available_ts: str = (BASE_TS + timedelta(minutes=124)).isoformat()
    lifecycle_state: str = "REGISTERED"


class _Resolver:
    def __init__(self, *, label_spec_id: str) -> None:
        self.label_spec_id = label_spec_id
        self.feature_calls: list[str] = []
        self.label_calls: list[str] = []

    def resolve_feature_packs(
        self,
        refs,
        *,
        expected_dataset_version_id,
        expected_feature_request_ids,
        partition_id,
        allow_horizon_agnostic_partition=False,
    ):
        assert expected_dataset_version_id == DATASET_VERSION_ID
        assert tuple(expected_feature_request_ids) == (FEATURE_REQUEST_ID,)
        assert partition_id == PARTITION_ID
        self.feature_calls.extend(refs)
        return tuple(_FeatureHandle(feature_version_id=ref) for ref in refs)

    def resolve_label_packs(
        self,
        refs,
        *,
        expected_dataset_version_id,
        expected_label_spec_ids,
        partition_id,
    ):
        assert expected_dataset_version_id == DATASET_VERSION_ID
        assert self.label_spec_id in expected_label_spec_ids
        assert partition_id == PARTITION_ID
        self.label_calls.extend(refs)
        return tuple(
            _LabelHandle(label_version_id=ref, label_spec_id=self.label_spec_id)
            for ref in refs
        )
