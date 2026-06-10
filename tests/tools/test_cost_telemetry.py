"""Cost/latency telemetry: duration and tokens must land in costs.jsonl."""

from __future__ import annotations

import json

from tools.frontier import ralph_driver


def test_command_result_carries_duration_with_default() -> None:
    result = ralph_driver.CommandResult(("x",), 0, "", "")
    assert result.duration_ms == 0
    timed = ralph_driver.CommandResult(("x",), 0, "", "", 1234)
    assert timed.duration_ms == 1234


def test_parse_provider_tokens_reads_codex_footer_last_match() -> None:
    result = ralph_driver.CommandResult(
        ("codex",), 0, "earlier tokens used: 10\n...\nTokens used: 12,345\n", ""
    )
    assert ralph_driver.parse_provider_tokens(result) == 12345


def test_parse_provider_tokens_none_for_plain_text() -> None:
    result = ralph_driver.CommandResult(("claude",), 0, "plain review markdown", "")
    assert ralph_driver.parse_provider_tokens(result) is None


def test_append_cost_record_writes_duration_and_tokens(tmp_path) -> None:
    state = {"run_id": "r", "campaign_id": "c"}
    ralph_driver.append_cost_record(
        tmp_path,
        state,
        provider="codex",
        model=None,
        phase_id="T-P00",
        note="phase_execution",
        duration_ms=2500,
        tokens=777,
    )
    record = json.loads((tmp_path / "costs.jsonl").read_text(encoding="utf-8").strip())
    assert record["duration_ms"] == 2500
    assert record["tokens"] == 777
    assert record["note"] == "phase_execution"
    assert record["cost_usd"] == 0.0  # honest: no fabricated USD


def test_cost_breakdown_aggregates_by_provider_and_stage(tmp_path) -> None:
    state = {"run_id": "r", "campaign_id": "c"}
    for duration, tokens in ((1000, 100), (2000, 200)):
        ralph_driver.append_cost_record(
            tmp_path, state, provider="codex", model=None, phase_id="T-P00",
            note="phase_execution", duration_ms=duration, tokens=tokens,
        )
    ralph_driver.append_cost_record(
        tmp_path, state, provider="claude", model=None, phase_id="T-P00", note="phase_review",
        duration_ms=500,
    )
    lines = "\n".join(ralph_driver.cost_breakdown_lines(tmp_path))
    assert "## Provider Time And Tokens" in lines
    assert "| codex | phase_execution | 2 | 3s | 300 |" in lines
    assert "| claude | phase_review | 1 | 0s | n/a |" in lines


def test_cost_breakdown_empty_without_ledger(tmp_path) -> None:
    assert ralph_driver.cost_breakdown_lines(tmp_path) == []
