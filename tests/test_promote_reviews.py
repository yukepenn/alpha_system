"""Tests for the coordinator review-promotion helper."""

from __future__ import annotations

import json
from pathlib import Path

from tools.frontier.promote_reviews import main, promote_reviews


def _make_run(run_dir: Path, phases: dict[str, str]) -> None:
    for phase_id, verdict in phases.items():
        pdir = run_dir / "phases" / phase_id
        pdir.mkdir(parents=True)
        (pdir / "review.md").write_text(f"# review {phase_id}\n", encoding="utf-8")
        (pdir / "verdict.json").write_text(json.dumps({"verdict": verdict}), encoding="utf-8")


def test_promote_reviews_copies_complete_records(tmp_path: Path) -> None:
    run_dir = tmp_path / "runs" / "RUN1"
    _make_run(run_dir, {"RT-P00": "PASS_WITH_WARNINGS", "RT-P01": "PASS"})
    dest = tmp_path / "reviews"

    promoted = promote_reviews(run_dir, "CAMPAIGN_X", dest)

    assert promoted == ["RT-P00", "RT-P01"]
    for phase_id in promoted:
        assert (dest / "CAMPAIGN_X" / phase_id / "review.md").is_file()
        assert (dest / "CAMPAIGN_X" / phase_id / "verdict.json").is_file()
    copied = json.loads((dest / "CAMPAIGN_X" / "RT-P01" / "verdict.json").read_text())
    assert copied["verdict"] == "PASS"


def test_promote_reviews_skips_incomplete_records(tmp_path: Path) -> None:
    run_dir = tmp_path / "runs" / "RUN1"
    _make_run(run_dir, {"RT-P00": "PASS"})
    # A phase that was never reviewed: review.md present but verdict.json missing.
    partial = run_dir / "phases" / "RT-P01"
    partial.mkdir(parents=True)
    (partial / "review.md").write_text("partial\n", encoding="utf-8")
    dest = tmp_path / "reviews"

    promoted = promote_reviews(run_dir, "CAMPAIGN_X", dest)

    assert promoted == ["RT-P00"]
    assert not (dest / "CAMPAIGN_X" / "RT-P01").exists()


def test_promote_reviews_main_reports_and_returns_nonzero_when_empty(tmp_path: Path, capsys) -> None:
    empty_run = tmp_path / "runs" / "EMPTY"
    (empty_run / "phases").mkdir(parents=True)

    rc = main(["--run-dir", str(empty_run), "--campaign-id", "CAMPAIGN_X", "--dest-root", str(tmp_path / "reviews")])

    assert rc == 1
    assert "No run-local review records" in capsys.readouterr().out
