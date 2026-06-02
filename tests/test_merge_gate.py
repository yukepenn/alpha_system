from __future__ import annotations

from dataclasses import dataclass

from tools.frontier.github_utils import BranchProtectionResult
from tools.frontier.merge_gate import evaluate_merge_gate, perform_merge


CONFIG = {
    "workflow2": {"auto_pr": True, "auto_merge": True},
    "github": {"merge_method": "squash", "require_branch_protection": True},
    "lanes": {
        "green": {"auto_pr": True, "auto_merge": True, "max_changed_files": 10, "merge_policy": {"allow_pass_with_warnings": True, "block_on_critical": True}},
        "yellow": {"auto_pr": True, "auto_merge": True, "max_changed_files": 10, "merge_policy": {"allow_pass_with_warnings": True, "block_on_critical": True}},
        "red": {"auto_pr": True, "auto_merge": False, "can_auto_merge_when_authorized": True, "merge_policy": {"allow_pass_with_warnings": False, "require_operation_scope_match": True}},
    },
}


BP = BranchProtectionResult(
    status="PASS",
    protected=True,
    branch="main",
    required_checks=["test"],
    configured_required_checks=["test"],
    missing_required_checks=[],
)


@dataclass(frozen=True)
class Result:
    command: list[str]
    return_code: int = 0
    stdout: str = ""
    stderr: str = ""


class FakeRunner:
    def __init__(self) -> None:
        self.commands: list[list[str]] = []

    def run(self, command, **kwargs):
        del kwargs
        self.commands.append(list(command))
        return Result(list(command), 0, "ok", "")


def test_green_pass_ci_success_allows_real_merge() -> None:
    result = evaluate_merge_gate(
        campaign_id="C1",
        phase_id="P1",
        lane="green",
        verdict="PASS",
        ci_status="SUCCESS",
        config=CONFIG,
        branch_protection=BP,
        dry_run=False,
    )

    assert result.status == "PASS"
    assert result.merge_allowed is True


def test_yellow_pass_with_warnings_allowed() -> None:
    result = evaluate_merge_gate(
        campaign_id="C1",
        phase_id="P1",
        lane="yellow",
        verdict="PASS_WITH_WARNINGS",
        ci_status="SUCCESS",
        config=CONFIG,
        branch_protection=BP,
        dry_run=False,
    )

    assert result.merge_allowed is True


def test_merge_gate_blocks_failed_ci() -> None:
    result = evaluate_merge_gate(
        campaign_id="C1",
        phase_id="P1",
        lane="green",
        verdict="PASS",
        ci_status="FAILURE",
        config=CONFIG,
        branch_protection=BP,
    )

    assert result.status == "BLOCKED"


def test_merge_gate_blocks_blocked_verdict() -> None:
    result = evaluate_merge_gate(
        campaign_id="C1",
        phase_id="P1",
        lane="green",
        verdict="BLOCKED",
        ci_status="SUCCESS",
        config=CONFIG,
        branch_protection=BP,
    )

    assert result.status == "BLOCKED"


def test_merge_gate_blocks_red_without_authorization() -> None:
    result = evaluate_merge_gate(
        campaign_id="C1",
        phase_id="P1",
        lane="red",
        verdict="PASS",
        ci_status="SUCCESS",
        config=CONFIG,
        env={},
        branch_protection=BP,
        dry_run=False,
    )

    assert result.status == "BLOCKED"


def test_frontier_disable_automerge_blocks() -> None:
    result = evaluate_merge_gate(
        campaign_id="C1",
        phase_id="P1",
        lane="green",
        verdict="PASS",
        ci_status="SUCCESS",
        config=CONFIG,
        env={"FRONTIER_DISABLE_AUTOMERGE": "1"},
        branch_protection=BP,
        dry_run=False,
    )

    assert result.merge_allowed is False
    assert result.status == "BLOCKED"


def test_dry_run_logs_command_but_does_not_execute_merge() -> None:
    gate = evaluate_merge_gate(
        campaign_id="C1",
        phase_id="P1",
        lane="green",
        verdict="PASS",
        ci_status="SUCCESS",
        config=CONFIG,
        branch_protection=BP,
        dry_run=True,
    )
    runner = FakeRunner()
    result = perform_merge(pr_number=5, gate=gate, runner=runner)

    assert result.dry_run is True
    assert runner.commands == []


def test_real_merge_path_calls_gh(monkeypatch) -> None:
    monkeypatch.delenv("FRONTIER_DISABLE_AUTOMERGE", raising=False)
    monkeypatch.delenv("FRONTIER_MERGE_DRY_RUN", raising=False)
    gate = evaluate_merge_gate(
        campaign_id="C1",
        phase_id="P1",
        lane="green",
        verdict="PASS",
        ci_status="SUCCESS",
        config=CONFIG,
        branch_protection=BP,
        dry_run=False,
    )
    runner = FakeRunner()
    result = perform_merge(pr_number=5, gate=gate, runner=runner)

    assert result.ok
    assert runner.commands[0] == ["gh", "auth", "status"]
    assert runner.commands[1][:3] == ["gh", "pr", "view"]
    assert runner.commands[2][:4] == ["gh", "pr", "merge", "5"]
