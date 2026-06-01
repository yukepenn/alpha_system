from __future__ import annotations

import json
from dataclasses import dataclass

from tools.frontier import github_utils
from tools.frontier.github_utils import (
    CI_FAILURE,
    CI_NOT_FOUND,
    CI_PENDING,
    CI_SUCCESS,
    checks_green,
    classify_ci_checks,
    create_pr,
    find_existing_pr,
    inspect_branch_protection,
    merge_pr,
    parse_github_remote,
    wait_for_ci,
)


@dataclass(frozen=True)
class Result:
    command: list[str]
    return_code: int = 0
    stdout: str = ""
    stderr: str = ""


class FakeRunner:
    def __init__(self, responses: list[Result]) -> None:
        self.responses = responses
        self.commands: list[list[str]] = []

    def run(self, command, **kwargs):
        del kwargs
        self.commands.append(list(command))
        if self.responses:
            return self.responses.pop(0)
        return Result(list(command), 0, "[]", "")


def test_parse_github_remote() -> None:
    assert parse_github_remote("git@github.com:owner/repo.git") == ("owner", "repo")
    assert parse_github_remote("https://github.com/owner/repo.git") == ("owner", "repo")


def test_dry_run_pr_does_not_call_network() -> None:
    runner = FakeRunner([])
    result = create_pr(title="Title", body="Body", base="main", head="branch", dry_run=True, runner=runner)

    assert result.dry_run
    assert result.command[:3] == ["gh", "pr", "create"]
    assert runner.commands == []


def test_existing_pr_detection() -> None:
    runner = FakeRunner(
        [
            Result(["gh"], stdout=json.dumps([{"number": 7, "headRefName": "branch", "url": "https://example.invalid"}])),
        ]
    )

    pr = find_existing_pr("branch", base="main", runner=runner)

    assert pr is not None
    assert pr["number"] == 7


def test_create_pr_missing_gh_is_blocked(monkeypatch) -> None:
    monkeypatch.setenv("FRONTIER_CREATE_PR", "1")
    runner = FakeRunner([Result(["gh", "auth", "status"], return_code=127, stderr="not found")])

    result = create_pr(title="Title", body="Body", base="main", head="branch", dry_run=False, runner=runner)

    assert result.blocked
    assert "gh auth login" in (result.instructions or "")


def test_dry_run_merge_does_not_call_network() -> None:
    result = merge_pr("1", dry_run=True)

    assert result.dry_run
    assert result.command[:3] == ["gh", "pr", "merge"]


def test_checks_green_parser() -> None:
    assert checks_green([{"conclusion": "success"}, {"conclusion": "skipped"}])
    assert not checks_green([{"conclusion": "failure"}])


def test_ci_classification_success_failure_pending_timeout() -> None:
    assert classify_ci_checks([{"name": "ci", "conclusion": "success"}]).state == CI_SUCCESS
    assert classify_ci_checks([{"name": "ci", "conclusion": "failure"}]).state == CI_FAILURE
    assert classify_ci_checks([{"name": "ci", "state": "PENDING"}]).state == CI_PENDING
    assert classify_ci_checks([], timed_out=True).state == "TIMED_OUT"


def test_ci_required_check_missing_is_not_found() -> None:
    result = classify_ci_checks([{"name": "lint", "conclusion": "success"}], required_checks=["test"])

    assert result.state == CI_NOT_FOUND
    assert result.missing_required == ["test"]


def test_wait_for_ci_success_with_mock_runner() -> None:
    runner = FakeRunner([Result(["gh"], stdout=json.dumps([{"name": "test", "conclusion": "success"}]))])

    result = wait_for_ci("3", timeout_seconds=1, poll_seconds=1, required_checks=["test"], runner=runner)

    assert result.state == CI_SUCCESS


def test_branch_protection_present(monkeypatch) -> None:
    monkeypatch.setattr(github_utils, "detect_repo_owner_name", lambda root=github_utils.ROOT: ("owner", "repo"))
    runner = FakeRunner(
        [
            Result(["gh", "auth", "status"], stdout="ok"),
            Result(
                ["gh", "api"],
                stdout=json.dumps({"required_status_checks": {"contexts": ["test"], "checks": []}}),
            ),
        ]
    )

    result = inspect_branch_protection(branch="main", required_checks=["test"], runner=runner)

    assert result.status == "PASS"
    assert result.protected is True


def test_branch_protection_missing_blocks_real_merge(monkeypatch) -> None:
    monkeypatch.setattr(github_utils, "detect_repo_owner_name", lambda root=github_utils.ROOT: ("owner", "repo"))
    runner = FakeRunner(
        [
            Result(["gh", "auth", "status"], stdout="ok"),
            Result(["gh", "api"], return_code=1, stderr="404 Not Found"),
        ]
    )

    result = inspect_branch_protection(branch="main", required_checks=["test"], runner=runner)

    assert result.status == "BLOCKED"


def test_branch_protection_dry_run_allowed() -> None:
    result = inspect_branch_protection(branch="main", required_checks=["test"], dry_run=True)

    assert result.status == "DRY_RUN"
