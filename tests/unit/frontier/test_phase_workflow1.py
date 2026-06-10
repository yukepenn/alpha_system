"""Tests for the minimal-real Workflow 1 runner in tools/frontier/phase.py."""

from __future__ import annotations

import json
from pathlib import Path

from tools.frontier import phase


def write_spec(
    root: Path,
    *,
    phase_id: str = "P0_DEMO",
    campaign_id: str = "DEMO_CAMPAIGN",
    status: str = "in_progress",
    body: str | None = None,
) -> Path:
    spec_dir = root / "specs" / campaign_id
    spec_dir.mkdir(parents=True, exist_ok=True)
    if body is None:
        body = "\n".join(
            [
                f"# {phase_id}: demo",
                "",
                "## Purpose",
                "",
                "A real purpose.",
                "",
                "## Validation",
                "",
                "- `python -c pass`",
                "",
            ]
        )
    spec_path = spec_dir / f"{phase_id}-demo.md"
    spec_path.write_text(
        "\n".join(
            [
                "---",
                f"campaign_id: {campaign_id}",
                f"phase_id: {phase_id}",
                "lane: yellow",
                f"status: {status}",
                "---",
                "",
                body,
            ]
        ),
        encoding="utf-8",
    )
    return spec_path


def test_missing_spec_fails_exit_2(tmp_path: Path) -> None:
    assert phase.workflow1("P0_NOPE", "validate", root=tmp_path) == 2


def test_template_placeholders_fail_exit_2(tmp_path: Path) -> None:
    body = "\n".join(
        [
            "## Purpose",
            "",
            "Define the purpose before execution.",
            "",
            "## Validation",
            "",
            "- `python -c pass`",
        ]
    )
    write_spec(tmp_path, body=body)
    assert phase.workflow1("P0_DEMO", "validate", root=tmp_path) == 2


def test_draft_status_fails_exit_2(tmp_path: Path) -> None:
    write_spec(tmp_path, status="draft")
    assert phase.workflow1("P0_DEMO", "validate", root=tmp_path) == 2


def test_validation_commands_run_and_are_recorded(tmp_path: Path) -> None:
    body = "\n".join(
        [
            "## Purpose",
            "",
            "A real purpose.",
            "",
            "## Validation",
            "",
            "- `python -c pass`",
            "- `python -c print(1)`",
            "",
            "## Notes",
            "",
            "- `python -c not_a_validation_command` lives outside the Validation section.",
        ]
    )
    write_spec(tmp_path, body=body)
    assert phase.workflow1("P0_DEMO", "validate", root=tmp_path) == 0
    payload = json.loads((tmp_path / "runs" / "wf1" / "P0_DEMO" / "validation.json").read_text())
    assert payload["phase_id"] == "P0_DEMO"
    assert payload["ok"] is True
    commands = [result["command"] for result in payload["results"]]
    assert commands == ["python -c pass", "python -c print(1)"]
    assert all(result["exit_code"] == 0 for result in payload["results"])
    assert all(result["duration_seconds"] >= 0 for result in payload["results"])
    assert (tmp_path / "runs" / "wf1" / "P0_DEMO" / "validation.md").exists()


def test_failing_validation_command_returns_nonzero_and_records_exit(tmp_path: Path) -> None:
    body = "\n".join(
        [
            "## Purpose",
            "",
            "A real purpose.",
            "",
            "## Validation",
            "",
            '- `python -c "raise SystemExit(3)"`',
        ]
    )
    write_spec(tmp_path, body=body)
    assert phase.workflow1("P0_DEMO", "validate", root=tmp_path) == 1
    payload = json.loads((tmp_path / "runs" / "wf1" / "P0_DEMO" / "validation.json").read_text())
    assert payload["ok"] is False
    assert payload["results"][0]["exit_code"] != 0


def test_empty_validation_section_fails(tmp_path: Path) -> None:
    body = "\n".join(["## Purpose", "", "A real purpose.", "", "## Validation", ""])
    write_spec(tmp_path, body=body)
    assert phase.workflow1("P0_DEMO", "validate", root=tmp_path) == 2


def test_review_gate_missing_verdict_fails(tmp_path: Path, capsys) -> None:
    write_spec(tmp_path)
    assert phase.workflow1("P0_DEMO", "review-gate", root=tmp_path) == 2
    assert "frontier-review" in capsys.readouterr().out


def test_review_gate_passes_on_pass_with_warnings(tmp_path: Path) -> None:
    write_spec(tmp_path)
    verdict_dir = tmp_path / "reviews" / "DEMO_CAMPAIGN"
    verdict_dir.mkdir(parents=True)
    (verdict_dir / "P0_DEMO-verdict.json").write_text(
        json.dumps({"verdict": "PASS_WITH_WARNINGS"}), encoding="utf-8"
    )
    assert phase.workflow1("P0_DEMO", "review-gate", root=tmp_path) == 0


def test_review_gate_rejects_non_passing_verdict(tmp_path: Path) -> None:
    write_spec(tmp_path)
    verdict_dir = tmp_path / "reviews" / "DEMO_CAMPAIGN"
    verdict_dir.mkdir(parents=True)
    (verdict_dir / "P0_DEMO-verdict.json").write_text(json.dumps({"verdict": "REWORK"}), encoding="utf-8")
    assert phase.workflow1("P0_DEMO", "review-gate", root=tmp_path) == 2


def test_review_subcommand_is_honest_nonzero(capsys) -> None:
    assert phase.review_contract("P0_DEMO") == 1
    out = capsys.readouterr().out
    assert "frontier-review skill" in out
    assert "PASS_WITH_WARNINGS" in out


def test_unstartable_command_records_exit_127(tmp_path: Path) -> None:
    body = "\n".join(
        [
            "## Purpose",
            "",
            "A real purpose.",
            "",
            "## Validation",
            "",
            "- `definitely-not-a-real-binary-xyz --flag`",
        ]
    )
    write_spec(tmp_path, body=body)
    assert phase.workflow1("P0_DEMO", "validate", root=tmp_path) == 1
    payload = json.loads((tmp_path / "runs" / "wf1" / "P0_DEMO" / "validation.json").read_text())
    assert payload["results"][0]["exit_code"] == 127
