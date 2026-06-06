from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

import alpha_system.cli.runtime as runtime_cli
from alpha_system.cli.main import build_parser, main

RUNTIME_SUBCOMMANDS = (
    "plan",
    "validate-inputs",
    "run-diagnostics",
    "run-label-diagnostics",
    "run-signal-probe",
    "run-cost-stress",
    "build-evidence-draft",
    "build-reference-handoff",
    "summarize",
    "inspect",
    "replay-summary",
)


def test_runtime_module_importable() -> None:
    assert runtime_cli.register_subparser is not None


def test_runtime_group_help_lists_planned_subcommands(capsys: pytest.CaptureFixture[str]) -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["runtime", "--help"])

    captured = capsys.readouterr()
    assert exc.value.code == 0
    assert "Drive local-only research runtime contracts" in captured.out
    for command in RUNTIME_SUBCOMMANDS:
        assert command in captured.out


@pytest.mark.parametrize("command", RUNTIME_SUBCOMMANDS)
def test_runtime_subcommand_help_is_available(
    command: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["runtime", command, "--help"])

    captured = capsys.readouterr()
    assert exc.value.code == 0
    assert "--input" in captured.out
    assert "--json" in captured.out


def test_runtime_registration_is_additive() -> None:
    parser = build_parser()

    assert {
        "backtest",
        "data",
        "factor",
        "feature",
        "governance",
        "grid",
        "label",
        "management",
        "ml",
        "registry",
        "report",
        "runtime",
        "study",
    }.issubset(_top_level_commands(parser))


def test_help_does_not_dispatch_handlers(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    def fail_if_called(_args: argparse.Namespace) -> int:
        nonlocal called
        called = True
        raise AssertionError("help should not call runtime handlers")

    monkeypatch.setattr(runtime_cli, "run_plan", fail_if_called)
    parser = build_parser()

    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["runtime", "plan", "--help"])

    assert exc.value.code == 0
    assert called is False


@pytest.mark.parametrize("command", RUNTIME_SUBCOMMANDS)
def test_runtime_subcommands_fail_cleanly_when_input_is_missing(
    command: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    status = main(["runtime", command])

    captured = capsys.readouterr()
    assert status == 2
    assert "runtime command error" in captured.err
    assert "provide --input" in captured.err


def test_validate_inputs_dispatches_entry_contract_and_emits_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_path = tmp_path / "runtime-entry.json"
    input_path.write_text(json.dumps(_entry_payload(), sort_keys=True), encoding="utf-8")

    status = main(["runtime", "validate-inputs", "--input", input_path.as_posix(), "--json"])

    captured = capsys.readouterr()
    assert status == 0
    assert captured.err == ""
    payload = json.loads(captured.out)
    assert payload["command"] == "validate-inputs"
    assert payload["result"]["status"] == "INPUTS_RESOLVED"
    assert payload["provider_or_broker_action"] is False
    assert payload["local_only"] is True


def test_summarize_is_value_free_and_local_json_only(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_path = tmp_path / "summary.json"
    input_path.write_text(
        json.dumps(
            {
                "schema": "alpha_system.runtime.study_run_record.v1",
                "result_state": "BLOCKED",
                "rejection_reason_records": [
                    {"code": "fixture_missing", "message": "fixture only"}
                ],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    status = main(["runtime", "summarize", "--input", input_path.as_posix(), "--json"])

    captured = capsys.readouterr()
    assert status == 0
    payload = json.loads(captured.out)
    assert payload["command"] == "summarize"
    assert payload["summary"]["state"] == "BLOCKED"
    assert payload["summary"]["reason_count"] == 1


def _top_level_commands(parser: argparse.ArgumentParser) -> set[str]:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return set(action.choices)
    raise AssertionError("top-level subparsers not found")


def _entry_payload() -> dict[str, object]:
    alpha_spec_ref = "aspec_af848bc999a4c4b11a421bd0"
    study_spec_ref = "sspec_438ceffd40855205de5497f0"
    feature_request_ref = "freq_eb180e1226ce34c048c7e6eb"
    label_spec_ref = "lspec_8663589ca7a9f1e5859289c7"
    dataset_scope = {
        "instrument_universe": "SYNTH fixture universe only",
        "source": "synthetic fixture metadata, not provider data",
        "time_range": "2026-01-01 through 2026-01-31 synthetic timestamps",
    }
    return {
        "entry_request": {
            "alpha_spec_ref": alpha_spec_ref,
            "study_spec_ref": study_spec_ref,
            "study_input_pack": {
                "feature_request_ids": [feature_request_ref],
                "label_spec_ids": [label_spec_ref],
                "alpha_spec_id": alpha_spec_ref,
                "dataset_scope": dataset_scope,
            },
            "target_dataset_version_id": "dsv_synthetic_feature_label_fixture_v1",
            "dataset_scope": dataset_scope,
            "expected_dataset_lifecycle_state": "VERSIONED",
            "dataset_version_source_family": "databento",
        }
    }
