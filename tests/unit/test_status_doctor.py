"""Tests for the Frontier status doctor (live-state source-of-truth reconciliation)."""

from __future__ import annotations

from tools.frontier import status_doctor as sd


def test_pyproject_requires_python_is_312() -> None:
    assert sd.pyproject_requires_python() == "3.12"


def test_active_campaign_runtime_matches_pyproject() -> None:
    """The active campaign's runtime.python must equal pyproject requires-python.

    This is the exact contradiction the doctor was built to catch; it must stay fixed.
    """
    campaign = sd.active_campaign_id()
    assert campaign, "ACTIVE_CAMPAIGN.md must declare a campaign"
    camp_py = sd.campaign_runtime_python(campaign)
    assert camp_py == sd.pyproject_requires_python()


def test_check_runtime_flags_mismatch(monkeypatch) -> None:
    monkeypatch.setattr(sd, "campaign_runtime_python", lambda _cid: "3.11")
    monkeypatch.setattr(sd, "pyproject_requires_python", lambda: "3.12")
    report = sd.Report()
    sd.check_runtime(report, "ANY")
    assert report.has_fail
    assert any("mismatch" in f.message.lower() for f in report.findings)


def test_check_runtime_passes_when_aligned(monkeypatch) -> None:
    monkeypatch.setattr(sd, "campaign_runtime_python", lambda _cid: "3.12")
    monkeypatch.setattr(sd, "pyproject_requires_python", lambda: "3.12")
    report = sd.Report()
    sd.check_runtime(report, "ANY")
    assert not report.has_fail


def test_strict_makes_pointer_drift_fail(monkeypatch, tmp_path) -> None:
    """When the committed pointer claims a different phase than the live run,
    --strict must escalate the drift warning to a failure."""
    # Synthesize a live run dir with a phase ahead of the claimed pointer.
    run = tmp_path / "runs" / "2099Z_DEMO"
    run.mkdir(parents=True)
    (run / "state.json").write_text(
        '{"campaign_id":"DEMO","current_phase_id":"DEMO-P09","status":"RUNNING",'
        '"phases":[{"phase_id":"DEMO-P00","status":"PASS","merged":true},'
        '{"phase_id":"DEMO-P09","status":"RUNNING","merged":false}]}',
        encoding="utf-8",
    )
    (run / "heartbeat.json").write_text(
        '{"current_phase_id":"DEMO-P09","status":"RUNNING","updated_at":"2099"}',
        encoding="utf-8",
    )
    monkeypatch.setattr(sd, "RUNS", tmp_path / "runs")
    monkeypatch.setattr(sd, "active_campaign_id", lambda: "DEMO")
    monkeypatch.setattr(sd, "claimed_current_phase", lambda: "DEMO-P01")
    monkeypatch.setattr(sd, "campaign_runtime_python", lambda _cid: "3.12")
    monkeypatch.setattr(sd, "pyproject_requires_python", lambda: "3.12")
    monkeypatch.setattr(sd, "check_stale_pointers", lambda *a, **k: None)

    soft = sd.build_report(strict=False)
    assert soft.has_warn and not soft.has_fail

    strict = sd.build_report(strict=True)
    assert strict.has_fail
    assert strict.live["live_phase"] == "DEMO-P09"
    assert strict.live["merged_phases"] == 1


def test_main_exit_zero_when_no_hard_failure() -> None:
    # Against the real repo: runtime is aligned and drift is a soft warning by default.
    assert sd.main([]) == 0
