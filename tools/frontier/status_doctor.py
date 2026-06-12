#!/usr/bin/env python3
"""Frontier status doctor: one authoritative read of "what campaign/phase are we on".

Motivation
----------
Committed pointers (`ACTIVE_CAMPAIGN.md`, `README.md`, `PROJECT_STATUS.md`) carry
human-written phase state that drifts behind the live Workflow 2 run. The single
source of truth for an *in-flight* run is the run-local ``runs/<run_id>/state.json``
(+ ``heartbeat.json``), which Ralph updates every loop. This tool reads that live
state, reconciles it against the committed pointers, checks the runtime contract
(``campaign.yaml`` vs ``pyproject.toml``), and prints the authoritative answer.

It is intentionally stdlib-only (no PyYAML) so it can run inside the dependency-light
hook/preflight path. Parsing of ``campaign.yaml`` runtime is a narrow regex, not a
full YAML load.

Exit codes
----------
0  consistent (live state found; pointers agree or only lag, which is allowed)
1  hard contradiction: runtime mismatch, >1 campaign claimed active, or
   (under ``--strict``) committed pointer disagrees with live phase
2  could not determine live state (no run dir / unreadable state) - operator
   should fall back to ``runs/<run_id>/state.json`` directly

Usage
-----
    python tools/frontier/status_doctor.py            # report + soft drift warnings
    python tools/frontier/status_doctor.py --strict   # drift becomes a failure
    python tools/frontier/status_doctor.py --json      # machine-readable
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs"

# Pointers that are allowed to describe live status. Anything else that hardcodes
# a "Current phase" / "Next campaign" is flagged as a stale-status hazard.
ACTIVE_POINTER = ROOT / "ACTIVE_CAMPAIGN.md"
HISTORICAL_POINTERS = (
    ROOT / "README.md",
    ROOT / "PROJECT_STATUS.md",
    ROOT / "PROGRESS.md",
)

PHASE_RE = re.compile(r"`?([A-Z][A-Z0-9]+-P\d{2})`?")
ACTIVE_CAMPAIGN_RE = re.compile(r"Campaign:\s*`?campaigns/([A-Z0-9_]+)`?")
CURRENT_PHASE_RE = re.compile(r"Current phase:\s*`?([A-Z][A-Z0-9]+-P\d{2})`?")


@dataclass
class Finding:
    level: str  # "ok" | "warn" | "fail"
    message: str


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    live: dict = field(default_factory=dict)

    def ok(self, m: str) -> None:
        self.findings.append(Finding("ok", m))

    def warn(self, m: str) -> None:
        self.findings.append(Finding("warn", m))

    def fail(self, m: str) -> None:
        self.findings.append(Finding("fail", m))

    @property
    def has_fail(self) -> bool:
        return any(f.level == "fail" for f in self.findings)

    @property
    def has_warn(self) -> bool:
        return any(f.level == "warn" for f in self.findings)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def active_campaign_id() -> str | None:
    m = ACTIVE_CAMPAIGN_RE.search(_read(ACTIVE_POINTER))
    return m.group(1) if m else None


def claimed_current_phase() -> str | None:
    m = CURRENT_PHASE_RE.search(_read(ACTIVE_POINTER))
    return m.group(1) if m else None


def latest_run_dir(campaign_id: str | None) -> Path | None:
    if not RUNS.is_dir():
        return None
    candidates = [p for p in RUNS.iterdir() if p.is_dir() and (p / "state.json").exists()]
    if campaign_id:
        scoped = [p for p in candidates if p.name.endswith(campaign_id)]
        candidates = scoped or candidates
    if not candidates:
        return None
    # Run dir names are lexicographically sortable timestamps; newest wins.
    return sorted(candidates, key=lambda p: p.name)[-1]


def load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def campaign_runtime_python(campaign_id: str | None) -> str | None:
    if not campaign_id:
        return None
    text = _read(ROOT / "campaigns" / campaign_id / "campaign.yaml")
    if not text:
        return None
    # Match a `runtime:` block then its `python: '3.x'` child without a YAML parser.
    m = re.search(r"^runtime:\s*$.*?^\s*python:\s*['\"]?(\d+\.\d+)", text, re.M | re.S)
    if m:
        return m.group(1)
    m = re.search(r"runtime_python:\s*['\"]?(\d+\.\d+)", text)
    return m.group(1) if m else None


def pyproject_requires_python() -> str | None:
    text = _read(ROOT / "pyproject.toml")
    m = re.search(r"requires-python\s*=\s*['\"][^0-9]*(\d+\.\d+)", text)
    return m.group(1) if m else None


def check_runtime(report: Report, campaign_id: str | None) -> None:
    camp = campaign_runtime_python(campaign_id)
    proj = pyproject_requires_python()
    if camp and proj and camp != proj:
        report.fail(
            f"Runtime contract mismatch: campaign.yaml runtime.python={camp} "
            f"but pyproject requires-python>={proj}. Align them."
        )
    elif camp and proj:
        report.ok(f"Runtime contract consistent (python {camp} == pyproject >={proj}).")
    elif not camp:
        report.warn("campaign.yaml runtime.python not found; cannot verify runtime contract.")


def git_hooks_path() -> str | None:
    """Return the configured ``core.hooksPath`` for this checkout, or None."""
    try:
        result = subprocess.run(
            ["git", "config", "--get", "core.hooksPath"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return None
    value = result.stdout.strip()
    return value or None


def git_core_bare(root: Path | None = None) -> str | None:
    """Return configured ``core.bare`` for this checkout, or None when unset."""
    try:
        result = subprocess.run(
            ["git", "config", "--get", "--bool", "core.bare"],
            cwd=root or ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return None
    value = result.stdout.strip().lower()
    return value or None


def check_core_bare(report: Report, root: Path | None = None) -> None:
    value = git_core_bare(root)
    if value == "true":
        report.fail(
            f"core.bare is true for {root or ROOT}. Fix: git -C {root or ROOT} config core.bare false"
        )
    elif value in {None, "false"}:
        report.ok("core.bare is false (or unset, which is non-bare for this checkout).")
    else:
        report.warn(f"core.bare has unexpected value {value!r}; inspect `git config --get --bool core.bare`.")


def check_hooks_floor(report: Report) -> None:
    """WARN (not FAIL) when the deterministic hook floor is not armed locally.

    Local enforcement requires ``core.hooksPath = .githooks``; this stays a
    warning rather than a failure so CI containers (where hooks are irrelevant
    and the workflows enforce the same guards) do not go red.
    """
    actual = git_hooks_path()
    if actual == ".githooks":
        report.ok("Hook floor armed: core.hooksPath = .githooks.")
    else:
        report.warn(
            f"core.hooksPath is {actual!r} (expected '.githooks'); local guard hooks "
            "are NOT armed. Fix: git config core.hooksPath .githooks"
        )


def check_stale_pointers(report: Report, live_phase: str | None) -> None:
    """Flag historical docs that hardcode a *different* live phase, so an agent
    does not treat them as current."""
    for path in HISTORICAL_POINTERS:
        text = _read(path)
        if not text:
            continue
        if re.search(r"Current phase|Current campaign|Next campaign", text):
            phases = set(PHASE_RE.findall(text))
            if live_phase and phases and live_phase not in phases:
                report.warn(
                    f"{path.relative_to(ROOT)} contains live-status language "
                    f"({sorted(phases)[:3]}...) that does not include the live phase "
                    f"{live_phase}. Treat it as historical, not authoritative."
                )


def build_report(strict: bool) -> Report:
    report = Report()
    check_core_bare(report)
    check_hooks_floor(report)
    campaign_id = active_campaign_id()
    if not campaign_id:
        report.fail("ACTIVE_CAMPAIGN.md does not declare a campaign (Campaign: campaigns/<ID>).")
        return report
    report.ok(f"Active campaign (committed pointer): {campaign_id}")

    run_dir = latest_run_dir(campaign_id)
    if run_dir is None:
        report.warn(f"No run dir with state.json found for {campaign_id}; no live run to reconcile.")
        check_runtime(report, campaign_id)
        return report

    state = load_json(run_dir / "state.json") or {}
    heartbeat = load_json(run_dir / "heartbeat.json") or {}
    live_phase = heartbeat.get("current_phase_id") or state.get("current_phase_id")
    live_status = heartbeat.get("status") or state.get("status")
    phases = state.get("phases") or []
    done = [p for p in phases if isinstance(p, dict) and p.get("merged")]
    in_flight = [
        p.get("phase_id")
        for p in phases
        if isinstance(p, dict) and p.get("status") not in {"PENDING"} and not p.get("merged")
    ]
    stop = (run_dir / "STOP").exists()

    report.live = {
        "campaign_id": state.get("campaign_id", campaign_id),
        "run_id": run_dir.name,
        "live_phase": live_phase,
        "live_status": live_status,
        "merged_phases": len(done),
        "total_phases": len(phases),
        "in_flight": in_flight,
        "stop_requested": stop or bool(state.get("stop_requested")),
        "heartbeat_at": heartbeat.get("updated_at"),
    }
    report.ok(
        f"Live state ({run_dir.name}): phase={live_phase} status={live_status} "
        f"merged={len(done)}/{len(phases)}"
        + (" [STOP active]" if report.live["stop_requested"] else "")
    )

    claimed = claimed_current_phase()
    if claimed and live_phase and claimed != live_phase:
        msg = (
            f"Committed ACTIVE_CAMPAIGN.md claims Current phase {claimed} but the live run "
            f"is at {live_phase} (merged {len(done)}/{len(phases)}). The committed pointer lags."
        )
        (report.fail if strict else report.warn)(msg)

    check_stale_pointers(report, live_phase)
    check_runtime(report, campaign_id)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Authoritative campaign/phase status reconciliation.")
    parser.add_argument("--strict", action="store_true", help="Treat pointer drift as a failure.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    report = build_report(args.strict)

    if args.json:
        print(json.dumps(
            {
                "live": report.live,
                "findings": [{"level": f.level, "message": f.message} for f in report.findings],
                "ok": not report.has_fail,
            },
            indent=2,
        ))
    else:
        print("=" * 72)
        print("FRONTIER STATUS DOCTOR - live run state is the source of truth")
        print("=" * 72)
        if report.live:
            L = report.live
            print(f"  AUTHORITATIVE: {L['campaign_id']} :: {L['live_phase']} ({L['live_status']})")
            print(f"  run_id        : {L['run_id']}")
            print(f"  progress      : merged {L['merged_phases']}/{L['total_phases']}"
                  + (f", in-flight {L['in_flight']}" if L['in_flight'] else ""))
            if L["stop_requested"]:
                print("  STOP          : ACTIVE - run is halted, resume after clearing")
            print("-" * 72)
        icon = {"ok": "  ok  ", "warn": " WARN ", "fail": " FAIL "}
        for f in report.findings:
            print(f"[{icon[f.level]}] {f.message}")
        print("-" * 72)
        verdict = "FAIL" if report.has_fail else ("WARN" if report.has_warn else "OK")
        print(f"VERDICT: {verdict}")

    return 1 if report.has_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
