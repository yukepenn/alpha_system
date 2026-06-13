from __future__ import annotations

import json
import sys

from tools.frontier import command_runner, ralph_driver
from tools.frontier.command_runner import CommandRunner, ProviderWatchdogConfig, TIMEOUT_RETURN_CODE
from tools.frontier.provider_adapters import WAITING_CODEX_LIMIT


def _fast_watchdog(events_path, event_writer):
    return ProviderWatchdogConfig(
        events_path=events_path,
        event_writer=event_writer,
        sample_interval_seconds=0.02,
        hang_after_seconds=0.06,
        kill_grace_seconds=0.05,
    )


def test_watchdog_detects_frozen_ticks_and_routes_existing_provider_wait(tmp_path, monkeypatch) -> None:
    events_path = tmp_path / "events.jsonl"
    events_path.write_text("", encoding="utf-8")
    records: list[dict[str, object]] = []
    monkeypatch.setattr(command_runner, "_cpu_ticks_for_process_group", lambda pid: 100)

    result = CommandRunner(tmp_path).run(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        timeout_seconds=5,
        provider_watchdog=_fast_watchdog(
            events_path,
            lambda event, details: records.append({"event": event, **dict(details)}),
        ),
    )

    assert result.return_code == TIMEOUT_RETURN_CODE
    assert result.timed_out
    assert result.duration_ms < 120_000
    assert "Provider watchdog detected" in result.stderr
    assert records and records[0]["event"] == "PROVIDER_HANG_DETECTED"
    assert records[0]["cpu_delta"] == 0
    assert records[0]["pid"]
    assert records[0]["wall_seconds"] > 0
    assert records[0]["last_event_age_seconds"] > 0

    phase = {
        "phase_id": "SHIP_REFIT-P01",
        "status": "SPEC_READY",
        "lane": "yellow",
        "name": "Provider-Watchdog",
        "execution_mode": "provider_wired",
    }
    state = {
        "run_id": "watchdog-test",
        "campaign_id": "SHIP_REFIT_V1",
        "workflow": "workflow2",
        "driver": ralph_driver.PROVIDER_WIRED_DRIVER,
        "status": "RUNNING",
        "phases": [phase],
        "last_event_id": 0,
        "estimated_cost_usd": 0.0,
        "mock_providers": False,
        "provider_wired": True,
        "provider_mode": "external",
        "max_phases_requested": 1,
        "max_phases_source": "test",
        "max_repair_attempts": 1,
    }
    handled = ralph_driver.handle_provider_nonzero(
        tmp_path,
        state,
        phase,
        provider="codex",
        stage="execute",
        result=ralph_driver.CommandResult(
            tuple(result.command),
            result.return_code,
            result.stdout,
            result.stderr,
            result.duration_ms,
        ),
    )

    assert handled
    assert phase["status"] == WAITING_CODEX_LIMIT
    assert phase["resume_stage"] == "execute"


def test_watchdog_does_not_kill_benign_slow_provider_when_ticks_advance(tmp_path, monkeypatch) -> None:
    events_path = tmp_path / "events.jsonl"
    events_path.write_text("", encoding="utf-8")
    records: list[dict[str, object]] = []
    ticks = {"value": 0}

    def advancing_ticks(pid: int) -> int:
        ticks["value"] += 1
        return ticks["value"]

    monkeypatch.setattr(command_runner, "_cpu_ticks_for_process_group", advancing_ticks)

    result = CommandRunner(tmp_path).run(
        [sys.executable, "-c", "import time; time.sleep(0.25); print('finished')"],
        timeout_seconds=2,
        provider_watchdog=_fast_watchdog(
            events_path,
            lambda event, details: records.append({"event": event, **dict(details)}),
        ),
    )

    assert result.return_code == 0
    assert result.stdout.strip() == "finished"
    assert records == []


def test_watchdog_does_not_kill_benign_slow_provider_when_events_grow(tmp_path, monkeypatch) -> None:
    events_path = tmp_path / "events.jsonl"
    events_path.write_text("", encoding="utf-8")
    records: list[dict[str, object]] = []
    monkeypatch.setattr(command_runner, "_cpu_ticks_for_process_group", lambda pid: 100)

    result = CommandRunner(tmp_path).run(
        [
            sys.executable,
            "-c",
            (
                "import os, time\n"
                "path = os.environ['EVENTS_PATH']\n"
                "for i in range(30):\n"
                "    with open(path, 'a', encoding='utf-8') as handle:\n"
                "        handle.write(f'progress {i}\\n')\n"
                "    time.sleep(0.01)\n"
                "print('event-progress')\n"
            ),
        ],
        env={"EVENTS_PATH": str(events_path)},
        timeout_seconds=2,
        provider_watchdog=_fast_watchdog(
            events_path,
            lambda event, details: records.append({"event": event, **dict(details)}),
        ),
    )

    assert result.return_code == 0
    assert result.stdout.strip() == "event-progress"
    assert records == []
    assert events_path.stat().st_size > 0


def test_watchdog_event_writer_uses_run_event_contract(tmp_path) -> None:
    run_dir = tmp_path
    state = {"last_event_id": 0}
    phase = {"phase_id": "SHIP_REFIT-P01"}
    config = ralph_driver.provider_watchdog_config(
        run_dir,
        state,
        phase,
        provider="codex",
        stage="execute",
    )

    assert config.event_writer is not None
    config.event_writer(
        "PROVIDER_HANG_DETECTED",
        {
            "pid": 123,
            "wall_seconds": 61.0,
            "cpu_delta": 0,
            "last_event_age_seconds": 61.0,
        },
    )

    record = json.loads((run_dir / "events.jsonl").read_text(encoding="utf-8"))
    assert record["event_id"] == 1
    assert record["event"] == "PROVIDER_HANG_DETECTED"
    assert record["phase_id"] == "SHIP_REFIT-P01"
    assert record["provider"] == "codex"
    assert record["stage"] == "execute"
    assert record["pid"] == 123
    assert state["last_event_id"] == 1


def test_watchdog_first_light_preflight_uses_resolver_smoke_and_canaries(tmp_path, monkeypatch) -> None:
    commands: list[list[str]] = []

    def fake_run_local_command(command: list[str], *, root):
        commands.append(command)
        return ralph_driver.CommandResult(tuple(command), 0, "ok\n", "")

    monkeypatch.setattr(ralph_driver, "run_local_command", fake_run_local_command)

    ok, text = ralph_driver.run_first_light_preflight(root=tmp_path)

    assert ok
    assert commands == [
        ralph_driver.FIRST_LIGHT_RESOLVER_SMOKE_COMMAND,
        ralph_driver.FIRST_LIGHT_CANARY_COMMAND,
    ]
    assert "First-Light Preflight" in text
