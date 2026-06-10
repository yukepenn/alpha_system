"""Lessons flywheel: friction signals must be distilled from run artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from tools.frontier import lessons_candidates


def _make_run(tmp_path: Path) -> tuple[Path, dict]:
    run_dir = tmp_path / "runs" / "2026-01-01T000000Z_TEST"
    state = {
        "run_id": "2026-01-01T000000Z_TEST",
        "campaign_id": "TEST_CAMPAIGN",
        "phases": [
            {"phase_id": "T-P00", "status": "PASS"},
            {"phase_id": "T-P01", "status": "BLOCKED", "status_reason": "STOP file exists."},
        ],
    }
    phase_dir = run_dir / "phases" / "T-P01"
    (phase_dir / "repair_attempts").mkdir(parents=True)
    (phase_dir / "repair_attempts" / "attempt_1").mkdir()
    (phase_dir / "verdict.json").write_text(
        json.dumps(
            {"verdict": "REWORK", "findings": ["test weakened in foo"], "warnings": ["stale doc"]}
        ),
        encoding="utf-8",
    )
    (phase_dir / "done_check.json").write_text(
        json.dumps({"verdict": "PASS_WITH_WARNINGS", "warnings": ["handoff thin"]}),
        encoding="utf-8",
    )
    return run_dir, state


def test_render_collects_friction_signals(tmp_path) -> None:
    run_dir, state = _make_run(tmp_path)
    text = lessons_candidates.render(state, run_dir)
    assert "## T-P01" in text
    assert "Final status `BLOCKED` — STOP file exists." in text
    assert "1 repair-attempt artifact(s)" in text
    assert "Review verdict `REWORK`" in text
    assert "Review finding: test weakened in foo" in text
    assert "Done-check warning: handoff thin" in text
    assert "## T-P00" not in text  # clean phases carry no section


def test_render_clean_run_is_explicit(tmp_path) -> None:
    state = {"run_id": "r", "campaign_id": "c", "phases": [{"phase_id": "T-P00", "status": "PASS"}]}
    text = lessons_candidates.render(state, tmp_path)
    assert "No friction signals recorded" in text


def test_write_for_run_writes_local_only_artifact(tmp_path) -> None:
    run_dir, state = _make_run(tmp_path)
    output = lessons_candidates.write_for_run(run_dir, state)
    assert output is not None
    assert output.name == lessons_candidates.OUTPUT_NAME
    assert output.parent == run_dir
    assert "promote only entries" in output.read_text(encoding="utf-8")


def test_enabled_defaults_true_when_config_unreadable(tmp_path) -> None:
    assert lessons_candidates.enabled(tmp_path) is True
