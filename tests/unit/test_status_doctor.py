"""Tests for the Frontier status doctor (live-state source-of-truth reconciliation)."""

from __future__ import annotations

import json
import subprocess

from tools.frontier import status_doctor as sd


def _make_run(runs_dir, name, *, status="STOPPED", lock=False, phases=None, events=None):
    """Synthesize a runs/<name>/ dir with state.json (+ optional RUN.lock / events.jsonl)."""
    run = runs_dir / name
    run.mkdir(parents=True)
    state = {"campaign_id": name.split("_", 1)[-1], "status": status, "phases": phases or []}
    (run / "state.json").write_text(json.dumps(state), encoding="utf-8")
    if lock:
        (run / "RUN.lock").write_text("pid 1\n", encoding="utf-8")
    if events is not None:
        (run / "events.jsonl").write_text(
            "\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8"
        )
    return run


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


def test_hooks_floor_warns_when_hooks_path_not_set(monkeypatch) -> None:
    monkeypatch.setattr(sd, "git_hooks_path", lambda: None)
    report = sd.Report()
    sd.check_hooks_floor(report)
    assert report.has_warn and not report.has_fail
    assert any("core.hooksPath" in f.message for f in report.findings)


def test_hooks_floor_ok_when_githooks_configured(monkeypatch) -> None:
    monkeypatch.setattr(sd, "git_hooks_path", lambda: ".githooks")
    report = sd.Report()
    sd.check_hooks_floor(report)
    assert not report.has_warn and not report.has_fail


def test_core_bare_true_is_hard_failure_in_temp_repo(tmp_path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "core.bare", "true"], cwd=tmp_path, check=True)
    report = sd.Report()
    sd.check_core_bare(report, root=tmp_path)
    assert report.has_fail
    assert any("git -C" in f.message and "config core.bare false" in f.message for f in report.findings)


# --- stale RUNNING / lock guard --------------------------------------------------


def test_stale_running_run_flagged_and_live_excluded(monkeypatch, tmp_path) -> None:
    runs = tmp_path / "runs"
    live = _make_run(runs, "2099Z_LIVE", status="RUNNING")
    _make_run(runs, "2001Z_OLD", status="RUNNING", lock=True)
    monkeypatch.setattr(sd, "RUNS", runs)
    report = sd.Report()
    sd.check_stale_running_runs(report, live)  # authoritative run excluded
    assert report.has_warn
    msgs = " ".join(f.message for f in report.findings)
    assert "2001Z_OLD" in msgs
    assert "2099Z_LIVE" not in msgs  # the live run is never flagged


def test_run_lock_alone_flags_stale(monkeypatch, tmp_path) -> None:
    runs = tmp_path / "runs"
    _make_run(runs, "2001Z_LOCKED", status="STOPPED", lock=True)
    monkeypatch.setattr(sd, "RUNS", runs)
    report = sd.Report()
    sd.check_stale_running_runs(report, None)
    assert report.has_warn
    assert any("RUN.lock present" in f.message for f in report.findings)


def test_no_stale_runs_is_ok(monkeypatch, tmp_path) -> None:
    runs = tmp_path / "runs"
    _make_run(runs, "2001Z_DONE", status="COMPLETED")
    _make_run(runs, "2002Z_STOPPED", status="STOPPED")
    monkeypatch.setattr(sd, "RUNS", runs)
    report = sd.Report()
    sd.check_stale_running_runs(report, None)
    assert not report.has_warn and not report.has_fail


# --- state-surgery merge guard ---------------------------------------------------


def test_surgery_merge_flagged_by_phase_id(tmp_path) -> None:
    run = _make_run(
        tmp_path / "runs",
        "2099Z_DEMO",
        phases=[
            {"phase_id": "DEMO-P00", "merged": True},
            {"phase_id": "DEMO-P01", "merged": True},  # hand-merged, no driver event
        ],
        events=[
            {"event": "MERGED", "phase_id": "DEMO-P00", "pr_number": 1},
            {"event": "PR_MERGED", "phase_id": "DEMO-P00", "pr_number": 1},
        ],
    )
    state = sd.load_json(run / "state.json")
    report = sd.Report()
    sd.check_surgery_merges(report, run, state)
    assert report.has_warn
    msgs = " ".join(f.message for f in report.findings)
    assert "DEMO-P01" in msgs and "surgery" in msgs.lower()
    assert "DEMO-P00" not in msgs  # the driver-merged phase is not flagged


def test_clean_driver_merges_not_flagged(tmp_path) -> None:
    run = _make_run(
        tmp_path / "runs",
        "2099Z_CLEAN",
        phases=[{"phase_id": "C-P00", "merged": True}],
        events=[{"event": "PR_MERGED", "phase_id": "C-P00", "pr_number": 1}],
    )
    state = sd.load_json(run / "state.json")
    report = sd.Report()
    sd.check_surgery_merges(report, run, state)
    assert not report.has_warn and not report.has_fail


def test_surgery_check_quiet_without_events_log(tmp_path) -> None:
    run = _make_run(
        tmp_path / "runs",
        "2099Z_NOEV",
        phases=[{"phase_id": "N-P00", "merged": True}],
        events=None,  # no events.jsonl -> cannot assess -> stay silent
    )
    state = sd.load_json(run / "state.json")
    report = sd.Report()
    sd.check_surgery_merges(report, run, state)
    assert not report.findings
