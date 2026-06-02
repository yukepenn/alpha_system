from __future__ import annotations

import json
from dataclasses import dataclass

from tools.frontier import github_utils
from tools.frontier.github_utils import (
    ALREADY_MERGED,
    AUTO_MERGE_ARMED,
    CI_FAILURE,
    CI_NOT_FOUND,
    CI_PENDING,
    CI_SUCCESS,
    MERGE_DRAFT_BLOCKED,
    MERGED,
    checks_green,
    classify_ci_checks,
    create_pr,
    find_existing_pr,
    get_pr_changed_files,
    inspect_branch_protection,
    list_pr_diff_files,
    list_pr_checks,
    merge_pr,
    parse_github_remote,
    view_pr,
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


def test_dry_run_pr_does_not_call_network(tmp_path) -> None:
    runner = FakeRunner([])
    body_file = tmp_path / "pr_body.md"
    result = create_pr(
        title="Title",
        body="Body",
        base="main",
        head="branch",
        body_file=body_file,
        root=tmp_path,
        dry_run=True,
        runner=runner,
    )

    assert result.dry_run
    assert result.command[:3] == ["gh", "pr", "create"]
    assert "--body-file" in result.command
    assert "--body" not in result.command
    assert body_file.read_text(encoding="utf-8") == "Body"
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


def test_list_pr_checks_uses_stable_supported_fields() -> None:
    runner = FakeRunner([Result(["gh"], stdout="[]")])

    checks = list_pr_checks("3", runner=runner)

    assert checks == []
    assert runner.commands
    command = runner.commands[0]
    fields = command[command.index("--json") + 1]
    assert fields == "name,state,link,bucket,workflow,event,startedAt,completedAt,description"
    assert "conclusion" not in fields


def test_view_pr_requests_head_ref_oid_for_resume() -> None:
    runner = FakeRunner([Result(["gh"], stdout=json.dumps({"number": 3, "state": "OPEN", "headRefOid": "a" * 40}))])

    result = view_pr("3", runner=runner)

    assert result.ok
    assert result.metadata["pr"]["headRefOid"] == "a" * 40
    fields = runner.commands[0][runner.commands[0].index("--json") + 1]
    assert "headRefOid" in fields
    assert "mergedAt" in fields
    assert "mergeStateStatus" in fields
    assert "statusCheckRollup" in fields


def test_pr_diff_files_uses_name_only() -> None:
    runner = FakeRunner([Result(["gh"], stdout="docs/a.md\n")])

    result = list_pr_diff_files("3", runner=runner)

    assert result.ok
    assert result.metadata["artifact_source"] == "pr_diff"
    assert result.metadata["files"] == ["docs/a.md"]
    assert runner.commands[0][:4] == ["gh", "pr", "diff", "3"]
    assert "--name-only" in runner.commands[0]


def test_get_pr_changed_files_returns_name_only_diff() -> None:
    runner = FakeRunner([Result(["gh"], stdout="docs/a.md\nsrc/b.py\n")])

    files = get_pr_changed_files("3", runner=runner, repo="owner/repo")

    assert files == ["docs/a.md", "src/b.py"]
    assert runner.commands[0] == ["gh", "pr", "diff", "3", "--name-only", "--repo", "owner/repo"]


def test_create_pr_missing_gh_is_blocked(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("FRONTIER_CREATE_PR", "1")
    runner = FakeRunner([Result(["gh", "auth", "status"], return_code=127, stderr="not found")])

    result = create_pr(
        title="Title",
        body="Body",
        base="main",
        head="branch",
        body_file=tmp_path / "pr_body.md",
        root=tmp_path,
        dry_run=False,
        runner=runner,
    )

    assert result.blocked
    assert "gh auth login" in (result.instructions or "")


def test_create_pr_uses_body_file_and_reuses_existing_pr(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("FRONTIER_CREATE_PR", "1")
    runner = FakeRunner(
        [
            Result(["gh", "auth", "status"], stdout="ok"),
            Result(["gh", "pr", "list"], stdout=json.dumps([{"number": 7, "headRefName": "branch"}])),
        ]
    )

    result = create_pr(
        title="Title",
        body="Large body",
        base="main",
        head="branch",
        body_file=tmp_path / "pr_body.md",
        branch_pushed=True,
        remote_sha="a" * 40,
        local_sha="a" * 40,
        root=tmp_path,
        dry_run=False,
        runner=runner,
    )

    assert result.ok
    assert result.metadata["existing"] is True
    assert result.metadata["branch_pushed"] is True
    assert "--body-file" in result.command
    assert "Large body" not in result.command
    assert runner.commands[-1][:4] == ["gh", "pr", "list", "--head"]


def test_create_pr_retries_owner_head_after_head_lookup_failure(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("FRONTIER_CREATE_PR", "1")
    monkeypatch.setattr(github_utils, "detect_repo_owner_name", lambda root=github_utils.ROOT: ("owner", "repo"))
    runner = FakeRunner(
        [
            Result(["gh", "auth", "status"], stdout="ok"),
            Result(["gh", "pr", "list"], stdout="[]"),
            Result(
                ["gh", "pr", "create"],
                return_code=1,
                stderr="GraphQL: Head sha can't be blank, Head ref must be a branch.",
            ),
            Result(["gh", "pr", "list"], stdout="[]"),
            Result(["gh", "pr", "create"], stdout="https://github.com/owner/repo/pull/9\n"),
            Result(["gh", "pr", "list"], stdout=json.dumps([{"number": 9, "headRefName": "branch"}])),
        ]
    )

    result = create_pr(
        title="Title",
        body="Body",
        base="main",
        head="branch",
        body_file=tmp_path / "pr_body.md",
        root=tmp_path,
        dry_run=False,
        runner=runner,
    )

    assert result.ok
    assert result.metadata["head_owner"] == "owner"
    assert result.metadata["number"] == 9
    assert "--head" in result.command
    assert "owner:branch" in result.command


def test_dry_run_merge_does_not_call_network() -> None:
    result = merge_pr("1", dry_run=True)

    assert result.dry_run
    assert result.command[:3] == ["gh", "pr", "merge"]
    assert result.metadata["classification"] == "dry_run"


def test_merge_pr_already_merged_pre_read_does_not_execute(monkeypatch) -> None:
    monkeypatch.delenv("FRONTIER_DISABLE_AUTOMERGE", raising=False)
    monkeypatch.delenv("FRONTIER_MERGE_DRY_RUN", raising=False)
    runner = FakeRunner(
        [
            Result(["gh", "auth", "status"], stdout="ok"),
            Result(["gh", "pr", "view"], stdout=json.dumps({"number": 3, "state": "MERGED", "mergedAt": "2026-01-01T00:00:00Z"})),
        ]
    )

    result = merge_pr("3", dry_run=False, runner=runner)

    assert result.ok
    assert result.metadata["status"] == ALREADY_MERGED
    assert result.metadata["already_merged"] is True
    assert [command[:3] for command in runner.commands] == [["gh", "auth", "status"], ["gh", "pr", "view"]]


def test_merge_pr_draft_blocks_before_merge(monkeypatch) -> None:
    monkeypatch.delenv("FRONTIER_DISABLE_AUTOMERGE", raising=False)
    monkeypatch.delenv("FRONTIER_MERGE_DRY_RUN", raising=False)
    runner = FakeRunner(
        [
            Result(["gh", "auth", "status"], stdout="ok"),
            Result(["gh", "pr", "view"], stdout=json.dumps({"number": 3, "state": "OPEN", "isDraft": True})),
        ]
    )

    result = merge_pr("3", dry_run=False, runner=runner)

    assert result.blocked
    assert result.metadata["status"] == MERGE_DRAFT_BLOCKED
    assert result.metadata["classification"] == "draft"


def test_merge_pr_arms_auto_merge_for_branch_policy_timing(monkeypatch) -> None:
    monkeypatch.delenv("FRONTIER_DISABLE_AUTOMERGE", raising=False)
    monkeypatch.delenv("FRONTIER_MERGE_DRY_RUN", raising=False)
    monkeypatch.setenv("FRONTIER_ALLOW_AUTOMERGE", "1")
    open_pr = {"number": 3, "state": "OPEN", "isDraft": False, "mergeStateStatus": "CLEAN"}
    runner = FakeRunner(
        [
            Result(["gh", "auth", "status"], stdout="ok"),
            Result(["gh", "pr", "view"], stdout=json.dumps(open_pr)),
            Result(
                ["gh", "pr", "merge"],
                return_code=1,
                stderr="base branch policy prohibits the merge. To have the pull request merged after all the requirements have been met, add the `--auto` flag.",
            ),
            Result(["gh", "pr", "view"], stdout=json.dumps(open_pr)),
            Result(["gh", "pr", "merge", "--auto"], stdout="Auto-merge enabled\n"),
            Result(["gh", "pr", "view"], stdout=json.dumps(open_pr)),
        ]
    )

    result = merge_pr("3", dry_run=False, runner=runner)

    assert result.ok
    assert result.metadata["status"] == AUTO_MERGE_ARMED
    assert result.metadata["classification"] == "branch_policy_auto_armed"
    assert result.metadata["auto_merge_armed"] is True
    assert runner.commands[2] == ["gh", "pr", "merge", "3", "--squash", "--delete-branch"]
    assert runner.commands[4] == ["gh", "pr", "merge", "3", "--auto", "--squash", "--delete-branch"]


def test_merge_pr_direct_failure_but_pr_is_merged_succeeds(monkeypatch) -> None:
    monkeypatch.delenv("FRONTIER_DISABLE_AUTOMERGE", raising=False)
    monkeypatch.delenv("FRONTIER_MERGE_DRY_RUN", raising=False)
    runner = FakeRunner(
        [
            Result(["gh", "auth", "status"], stdout="ok"),
            Result(["gh", "pr", "view"], stdout=json.dumps({"number": 3, "state": "OPEN", "isDraft": False})),
            Result(["gh", "pr", "merge"], return_code=1, stderr="failed to delete branch"),
            Result(["gh", "pr", "view"], stdout=json.dumps({"number": 3, "state": "MERGED"})),
        ]
    )

    result = merge_pr("3", dry_run=False, runner=runner)

    assert result.ok
    assert result.metadata["status"] == MERGED
    assert result.metadata["merged"] is True
    assert "branch deletion" in result.metadata["warning"]


def test_checks_green_parser() -> None:
    assert checks_green([{"conclusion": "success"}, {"conclusion": "skipped"}])
    assert not checks_green([{"conclusion": "failure"}])


def test_ci_classification_success_failure_pending_timeout() -> None:
    assert classify_ci_checks([{"name": "ci", "conclusion": "success"}]).state == CI_SUCCESS
    assert classify_ci_checks([{"name": "ci", "conclusion": "failure"}]).state == CI_FAILURE
    assert classify_ci_checks([{"name": "ci", "state": "PENDING"}]).state == CI_PENDING
    assert classify_ci_checks([], timed_out=True).state == "TIMED_OUT"


def test_ci_classification_uses_state_and_bucket_without_conclusion() -> None:
    assert classify_ci_checks([{"name": "validate", "state": "SUCCESS", "bucket": "pass"}]).state == CI_SUCCESS
    assert classify_ci_checks([{"name": "validate", "state": "FAILURE", "bucket": "fail"}]).state == CI_FAILURE
    assert classify_ci_checks([{"name": "validate", "state": "QUEUED", "bucket": "pending"}]).state == CI_PENDING


def test_ci_required_check_missing_is_not_found() -> None:
    result = classify_ci_checks([{"name": "lint", "conclusion": "success"}], required_checks=["test"])

    assert result.state == CI_NOT_FOUND
    assert result.missing_required == ["test"]


def test_wait_for_ci_success_with_mock_runner() -> None:
    runner = FakeRunner([Result(["gh"], stdout=json.dumps([{"name": "test", "state": "SUCCESS", "bucket": "pass"}]))])

    result = wait_for_ci("3", timeout_seconds=1, poll_seconds=1, required_checks=["test"], runner=runner)

    assert result.state == CI_SUCCESS


def test_wait_for_ci_polls_not_found_until_required_check_appears() -> None:
    runner = FakeRunner(
        [
            Result(["gh"], stdout="[]"),
            Result(["gh"], stdout=json.dumps([{"name": "test", "state": "SUCCESS", "bucket": "pass"}])),
        ]
    )

    result = wait_for_ci("3", timeout_seconds=1, poll_seconds=0, required_checks=["test"], runner=runner)

    assert result.state == CI_SUCCESS
    assert len(runner.commands) == 2


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
