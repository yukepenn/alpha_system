from __future__ import annotations

import json
from pathlib import Path

import pytest

from alpha_system.cli.main import build_parser, main

FIXTURE_IDEA = Path("research/idea_to_verdict_loop_v0/fixtures/day_of_week.idea.yaml")


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
