"""GitHub CLI helpers for Frontier Workflow 2.

All network-facing behavior goes through the local ``gh`` CLI. Tests can pass a
mock ``CommandRunner`` and never touch the network.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.frontier.command_runner import CommandRunner
from tools.frontier.git_utils import current_branch, git, remote_url


GITHUB_RE = re.compile(r"(?:github\.com[:/])([^/\s]+)/([^/\s]+?)(?:\.git)?/?$")
CI_SUCCESS = "SUCCESS"
CI_FAILURE = "FAILURE"
CI_PENDING = "PENDING"
CI_TIMED_OUT = "TIMED_OUT"
CI_NOT_FOUND = "NOT_FOUND"
CI_STATES = {CI_SUCCESS, CI_FAILURE, CI_PENDING, CI_TIMED_OUT, CI_NOT_FOUND}
PASSING_CONCLUSIONS = {"success", "neutral", "skipped"}
FAILING_CONCLUSIONS = {
    "failure",
    "cancelled",
    "timed_out",
    "action_required",
    "startup_failure",
    "stale",
}
PENDING_STATES = {"pending", "queued", "in_progress", "waiting", "requested", "expected"}
MERGED = "MERGED"
ALREADY_MERGED = "ALREADY_MERGED"
AUTO_MERGE_ARMED = "AUTO_MERGE_ARMED"
MERGE_EXECUTION_BLOCKED = "MERGE_EXECUTION_BLOCKED"
MERGE_RETRYABLE = "MERGE_RETRYABLE"
MERGE_CONFLICT = "MERGE_CONFLICT"
MERGE_PERMISSION_BLOCKED = "MERGE_PERMISSION_BLOCKED"
MERGE_DRAFT_BLOCKED = "MERGE_DRAFT_BLOCKED"


@dataclass(frozen=True)
class GitHubResult:
    action: str
    dry_run: bool
    command: list[str]
    return_code: int = 0
    stdout: str = ""
    stderr: str = ""
    blocked: bool = False
    instructions: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.return_code == 0 and not self.blocked

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CIStatusResult:
    state: str
    checks: list[dict[str, Any]]
    required_checks: list[str]
    missing_required: list[str]
    blocking_checks: list[str]
    timed_out: bool = False
    message: str = ""

    @property
    def success(self) -> bool:
        return self.state == CI_SUCCESS

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BranchProtectionResult:
    status: str
    protected: bool
    branch: str
    required_checks: list[str]
    configured_required_checks: list[str]
    missing_required_checks: list[str]
    permission_error: bool = False
    dry_run: bool = False
    message: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status == "PASS"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_github_remote(url: str | None) -> tuple[str, str] | None:
    if not url:
        return None
    match = GITHUB_RE.search(url.strip())
    if not match:
        return None
    return match.group(1), match.group(2)


def detect_repo_owner_name(root: Path = ROOT) -> tuple[str, str] | None:
    return parse_github_remote(remote_url(root))


def detect_repo_remote(root: Path = ROOT) -> str | None:
    parsed = detect_repo_owner_name(root)
    if parsed is None:
        return None
    return "/".join(parsed)


def detect_current_branch(root: Path = ROOT) -> str:
    return current_branch(root)


def _runner(root: Path, runner: CommandRunner | None) -> CommandRunner:
    return runner or CommandRunner(root)


def _run_gh(
    command: list[str],
    *,
    root: Path = ROOT,
    runner: CommandRunner | None = None,
    timeout_seconds: int = 120,
) -> Any:
    return _runner(root, runner).run(command, timeout_seconds=timeout_seconds)


def _with_repo(command: list[str], repo: str) -> list[str]:
    return [*command, "--repo", repo]


def gh_auth_status(*, root: Path = ROOT, runner: CommandRunner | None = None) -> GitHubResult:
    command = ["gh", "auth", "status"]
    result = _run_gh(command, root=root, runner=runner, timeout_seconds=60)
    if result.return_code == 127:
        return GitHubResult(
            "gh_auth_status",
            False,
            command,
            result.return_code,
            result.stdout,
            result.stderr,
            blocked=True,
            instructions="Install GitHub CLI: https://cli.github.com/ and run `gh auth login`.",
        )
    if result.return_code != 0:
        return GitHubResult(
            "gh_auth_status",
            False,
            command,
            result.return_code,
            result.stdout,
            result.stderr,
            blocked=True,
            instructions="Authenticate GitHub CLI with `gh auth login` before real PR, CI, or merge operations.",
        )
    return GitHubResult("gh_auth_status", False, command, result.return_code, result.stdout, result.stderr)


def detect_default_branch(*, root: Path = ROOT, runner: CommandRunner | None = None) -> str:
    command = ["gh", "repo", "view", "--json", "defaultBranchRef", "-q", ".defaultBranchRef.name"]
    result = _run_gh(command, root=root, runner=runner, timeout_seconds=60)
    if result.return_code == 0 and result.stdout.strip():
        return result.stdout.strip()

    fallback = git(root, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD")
    if fallback.returncode == 0 and "/" in fallback.stdout.strip():
        return fallback.stdout.strip().split("/", 1)[1]
    configured = git(root, "config", "--get", "init.defaultBranch")
    if configured.returncode == 0 and configured.stdout.strip():
        return configured.stdout.strip()
    return "main"


def find_existing_pr(
    head: str,
    *,
    base: str | None = None,
    root: Path = ROOT,
    runner: CommandRunner | None = None,
) -> dict[str, Any] | None:
    command = [
        "gh",
        "pr",
        "list",
        "--head",
        head,
        "--state",
        "open",
        "--json",
        "number,title,url,headRefName,baseRefName,state",
        "--limit",
        "20",
    ]
    if base:
        command.extend(["--base", base])
    result = _run_gh(command, root=root, runner=runner, timeout_seconds=120)
    if result.return_code != 0:
        return None
    try:
        data = json.loads(result.stdout or "[]")
    except json.JSONDecodeError:
        return None
    if not isinstance(data, list) or not data:
        return None
    first = data[0]
    return first if isinstance(first, dict) else None


def view_pr(
    pr: str | int,
    *,
    root: Path = ROOT,
    runner: CommandRunner | None = None,
    repo: str | None = None,
) -> GitHubResult:
    fields = (
        "number,state,mergedAt,mergeStateStatus,isDraft,headRefOid,headRefName,"
        "baseRefName,statusCheckRollup,url"
    )
    base_command = ["gh", "pr", "view", str(pr), "--json", fields]
    command = _with_repo(base_command, repo) if repo else base_command
    result = _run_gh(command, root=root, runner=runner, timeout_seconds=120)
    metadata: dict[str, Any] = {}
    if result.return_code != 0 and repo is None:
        detected_repo = detect_repo_remote(root)
        if detected_repo:
            retry_command = _with_repo(base_command, detected_repo)
            retry = _run_gh(retry_command, root=root, runner=runner, timeout_seconds=120)
            metadata["repo"] = detected_repo
            result = retry
            command = retry_command
    if result.return_code == 0:
        try:
            data = json.loads(result.stdout or "{}")
        except json.JSONDecodeError:
            data = {}
        if isinstance(data, dict):
            metadata["pr"] = data
    return GitHubResult(
        "view_pr",
        False,
        command,
        result.return_code,
        result.stdout,
        result.stderr,
        blocked=result.return_code != 0,
        instructions=None if result.return_code == 0 else "Inspect `gh pr view` output and resume after the PR is readable.",
        metadata=metadata,
    )


def list_pr_diff_files(
    pr: str | int,
    *,
    root: Path = ROOT,
    runner: CommandRunner | None = None,
    repo: str | None = None,
) -> GitHubResult:
    base_command = ["gh", "pr", "diff", str(pr), "--name-only"]
    command = _with_repo(base_command, repo) if repo else base_command
    result = _run_gh(command, root=root, runner=runner, timeout_seconds=120)
    metadata: dict[str, Any] = {"artifact_source": "pr_diff"}
    if result.return_code != 0 and repo is None:
        detected_repo = detect_repo_remote(root)
        if detected_repo:
            retry_command = _with_repo(base_command, detected_repo)
            retry = _run_gh(retry_command, root=root, runner=runner, timeout_seconds=120)
            metadata["repo"] = detected_repo
            result = retry
            command = retry_command
    if result.return_code == 0:
        metadata["files"] = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return GitHubResult(
        "pr_diff",
        False,
        command,
        result.return_code,
        result.stdout,
        result.stderr,
        blocked=result.return_code != 0,
        instructions=None if result.return_code == 0 else "Inspect `gh pr diff --name-only` output and resume after the PR diff is readable.",
        metadata=metadata,
    )


def get_pr_changed_files(
    pr_number: str | int,
    *,
    root: Path = ROOT,
    repo: str | None = None,
    runner: CommandRunner | None = None,
) -> list[str]:
    result = list_pr_diff_files(pr_number, root=root, runner=runner, repo=repo)
    if result.blocked:
        detail = result.instructions or result.stderr or "Could not read PR changed files."
        raise RuntimeError(detail)
    files = result.metadata.get("files") if isinstance(result.metadata, dict) else []
    return [str(item) for item in files] if isinstance(files, list) else []


def _metadata(
    *,
    base: str,
    head: str,
    head_owner: str | None = None,
    branch_pushed: bool | None = None,
    remote_sha: str | None = None,
    local_sha: str | None = None,
    body_file: Path | None = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {"head": head, "base": base}
    if head_owner:
        data["head_owner"] = head_owner
    if branch_pushed is not None:
        data["branch_pushed"] = branch_pushed
    if remote_sha is not None:
        data["remote_sha"] = remote_sha
    if local_sha is not None:
        data["local_sha"] = local_sha
    if body_file is not None:
        data["body_file"] = str(body_file)
    return data


def _env_forces_dry_run(name: str) -> bool | None:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return None
    return raw.lower() not in {"1", "true", "yes", "on"}


def _pr_create_command(*, base: str, head: str, title: str, body_file: Path) -> list[str]:
    return ["gh", "pr", "create", "--base", base, "--head", head, "--title", title, "--body-file", str(body_file)]


def _pr_number_from_url(url: str) -> int | None:
    tail = url.rstrip("/").rsplit("/", 1)[-1]
    return int(tail) if tail.isdigit() else None


def _should_retry_with_owner(result: Any) -> bool:
    text = f"{getattr(result, 'stdout', '')}\n{getattr(result, 'stderr', '')}".lower()
    tokens = (
        "head sha can't be blank",
        "base sha can't be blank",
        "head ref must be a branch",
        "no commits between",
        "could not resolve to a branch",
    )
    return any(token in text for token in tokens)


def create_pr(
    *,
    title: str,
    body: str,
    base: str,
    head: str | None = None,
    body_file: Path | None = None,
    head_owner: str | None = None,
    branch_pushed: bool | None = None,
    remote_sha: str | None = None,
    local_sha: str | None = None,
    root: Path = ROOT,
    dry_run: bool = True,
    runner: CommandRunner | None = None,
) -> GitHubResult:
    head = head or current_branch(root)
    body_file = body_file or (root / "pr_body.md")
    body_file.parent.mkdir(parents=True, exist_ok=True)
    body_file.write_text(body, encoding="utf-8")
    requested_head = f"{head_owner}:{head}" if head_owner else head
    command = _pr_create_command(base=base, head=requested_head, title=title, body_file=body_file)
    metadata = _metadata(
        base=base,
        head=head,
        head_owner=head_owner,
        branch_pushed=branch_pushed,
        remote_sha=remote_sha,
        local_sha=local_sha,
        body_file=body_file,
    )
    forced = _env_forces_dry_run("FRONTIER_CREATE_PR")
    effective_dry_run = dry_run if forced is None else forced
    if effective_dry_run:
        return GitHubResult("create_pr", True, command, metadata=metadata)

    auth = gh_auth_status(root=root, runner=runner)
    if auth.blocked:
        return GitHubResult(
            "create_pr",
            False,
            command,
            auth.return_code,
            auth.stdout,
            auth.stderr,
            blocked=True,
            instructions=auth.instructions,
            metadata=metadata,
        )

    existing = find_existing_pr(requested_head, base=base, root=root, runner=runner)
    if existing:
        metadata.update({"existing": True, "pr": existing, "number": existing.get("number")})
        return GitHubResult(
            "create_pr",
            False,
            command,
            metadata=metadata,
        )

    result = _run_gh(command, root=root, runner=runner, timeout_seconds=300)
    url = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""
    if url:
        metadata["url"] = url
        number = _pr_number_from_url(url)
        if number is not None:
            metadata["number"] = number
    if result.return_code == 0:
        created = find_existing_pr(requested_head, base=base, root=root, runner=runner)
        if created:
            metadata["pr"] = created
            metadata["number"] = created.get("number")
    elif head_owner is None and _should_retry_with_owner(result):
        repo = detect_repo_owner_name(root)
        if repo is not None:
            owner, _name = repo
            owner_head = f"{owner}:{head}"
            owner_existing = find_existing_pr(owner_head, base=base, root=root, runner=runner)
            if owner_existing:
                metadata.update(
                    {
                        "existing": True,
                        "pr": owner_existing,
                        "number": owner_existing.get("number"),
                        "head_owner": owner,
                        "initial_return_code": result.return_code,
                        "initial_stderr": result.stderr,
                    }
                )
                retry_command = _pr_create_command(base=base, head=owner_head, title=title, body_file=body_file)
                return GitHubResult("create_pr", False, retry_command, metadata=metadata)
            retry_command = _pr_create_command(base=base, head=owner_head, title=title, body_file=body_file)
            retry = _run_gh(retry_command, root=root, runner=runner, timeout_seconds=300)
            metadata.update(
                {
                    "head_owner": owner,
                    "initial_return_code": result.return_code,
                    "initial_stdout": result.stdout,
                    "initial_stderr": result.stderr,
                }
            )
            retry_url = retry.stdout.strip().splitlines()[-1] if retry.stdout.strip() else ""
            if retry_url:
                metadata["url"] = retry_url
                number = _pr_number_from_url(retry_url)
                if number is not None:
                    metadata["number"] = number
            if retry.return_code == 0:
                created = find_existing_pr(owner_head, base=base, root=root, runner=runner)
                if created:
                    metadata["pr"] = created
                    metadata["number"] = created.get("number")
            return GitHubResult(
                "create_pr",
                False,
                retry_command,
                retry.return_code,
                retry.stdout,
                retry.stderr,
                blocked=retry.return_code != 0,
                instructions=None
                if retry.return_code == 0
                else "Fix `gh pr create` output above, then resume the run.",
                metadata=metadata,
            )
    return GitHubResult(
        "create_pr",
        False,
        command,
        result.return_code,
        result.stdout,
        result.stderr,
        blocked=result.return_code != 0,
        instructions=None
        if result.return_code == 0
        else "Fix `gh pr create` output above, then resume the run.",
        metadata=metadata,
    )


def write_pr_create_artifacts(phase_dir: Path, result: GitHubResult) -> None:
    phase_dir.mkdir(parents=True, exist_ok=True)
    (phase_dir / "pr_create.json").write_text(
        json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    metadata = result.metadata if isinstance(result.metadata, dict) else {}
    lines = [
        "# PR Creation",
        "",
        f"Dry run: {str(result.dry_run).lower()}",
        f"Blocked: {str(result.blocked).lower()}",
        f"Return code: {result.return_code}",
        f"Base: {metadata.get('base', '')}",
        f"Head: {metadata.get('head', '')}",
        f"Head owner: {metadata.get('head_owner', '') or 'not used'}",
        f"Branch pushed: {str(metadata.get('branch_pushed', False)).lower()}",
        f"Local SHA: {metadata.get('local_sha', '') or 'unknown'}",
        f"Remote SHA: {metadata.get('remote_sha', '') or 'unknown'}",
        f"Existing PR: {str(metadata.get('existing', False)).lower()}",
        f"PR number: {metadata.get('number', '') or 'unknown'}",
        f"Command: `{' '.join(result.command)}`",
    ]
    if result.instructions:
        lines.extend(["", "## Instructions", "", result.instructions])
    if result.stdout:
        lines.extend(["", "## stdout", "", "```text", result.stdout.rstrip(), "```"])
    if result.stderr:
        lines.extend(["", "## stderr", "", "```text", result.stderr.rstrip(), "```"])
    (phase_dir / "pr_create.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def list_pr_checks(
    pr: str | int,
    *,
    root: Path = ROOT,
    runner: CommandRunner | None = None,
) -> list[dict[str, Any]]:
    command = [
        "gh",
        "pr",
        "checks",
        str(pr),
        "--json",
        "name,state,link,bucket,workflow,event,startedAt,completedAt,description",
    ]
    result = _run_gh(command, root=root, runner=runner, timeout_seconds=120)
    if result.return_code != 0:
        return [
            {
                "name": "gh pr checks",
                "state": "ERROR",
                "bucket": "fail",
                "stderr": result.stderr,
                "return_code": result.return_code,
            }
        ]
    try:
        data = json.loads(result.stdout or "[]")
    except json.JSONDecodeError:
        return [{"name": "gh pr checks", "state": "ERROR", "bucket": "fail", "stdout": result.stdout}]
    return data if isinstance(data, list) else []


def get_pr_checks(pr: str, *, root: Path = ROOT, runner: CommandRunner | None = None) -> list[dict[str, Any]]:
    return list_pr_checks(pr, root=root, runner=runner)


def _check_name(check: Mapping[str, Any]) -> str:
    return str(check.get("name") or check.get("workflow") or "").strip()


def classify_ci_checks(
    checks: list[dict[str, Any]],
    *,
    required_checks: list[str] | None = None,
    timed_out: bool = False,
) -> CIStatusResult:
    required = [name for name in (required_checks or []) if name]
    if timed_out:
        return CIStatusResult(CI_TIMED_OUT, checks, required, [], [], True, "Timed out waiting for CI.")
    if not checks:
        return CIStatusResult(CI_NOT_FOUND, checks, required, required, [], False, "No check runs were found.")

    by_name = {_check_name(check): check for check in checks if _check_name(check)}
    missing = [name for name in required if name not in by_name]
    relevant = [by_name[name] for name in required if name in by_name] if required else checks
    if missing:
        return CIStatusResult(CI_NOT_FOUND, checks, required, missing, missing, False, "Required checks were not found.")
    if not relevant:
        return CIStatusResult(CI_NOT_FOUND, checks, required, required, [], False, "No relevant check runs were found.")

    blocking: list[str] = []
    pending = False
    for check in relevant:
        name = _check_name(check) or "unnamed check"
        state = str(check.get("state") or "").lower()
        bucket = str(check.get("bucket") or "").lower()
        conclusion = str(check.get("conclusion") or "").lower()
        primary_tokens = {token for token in (state, bucket) if token}
        fallback_token = conclusion
        if (
            primary_tokens.intersection(FAILING_CONCLUSIONS | {"error", "fail", "failed", "cancel"})
            or fallback_token in FAILING_CONCLUSIONS
        ):
            blocking.append(name)
        elif (
            primary_tokens.intersection(PASSING_CONCLUSIONS | {"pass", "passed", "skip", "skipping"})
            or fallback_token in PASSING_CONCLUSIONS
        ):
            continue
        elif (
            primary_tokens.intersection(PENDING_STATES)
            or fallback_token in PENDING_STATES
            or not (primary_tokens or fallback_token)
        ):
            pending = True
        else:
            pending = True
    if blocking:
        return CIStatusResult(CI_FAILURE, checks, required, [], blocking, False, "One or more checks failed.")
    if pending:
        return CIStatusResult(CI_PENDING, checks, required, [], [], False, "One or more checks are still pending.")
    return CIStatusResult(CI_SUCCESS, checks, required, [], [], False, "All required checks passed.")


def checks_green(checks: list[dict[str, Any]]) -> bool:
    return classify_ci_checks(checks).success


def wait_for_ci(
    pr: str | int,
    *,
    timeout_seconds: int = 900,
    poll_seconds: int = 15,
    required_checks: list[str] | None = None,
    root: Path = ROOT,
    runner: CommandRunner | None = None,
) -> CIStatusResult:
    deadline = time.monotonic() + timeout_seconds
    last_checks: list[dict[str, Any]] = []
    while time.monotonic() <= deadline:
        last_checks = list_pr_checks(pr, root=root, runner=runner)
        status = classify_ci_checks(last_checks, required_checks=required_checks)
        if status.state not in {CI_PENDING, CI_NOT_FOUND}:
            return status
        time.sleep(poll_seconds)
    return classify_ci_checks(last_checks, required_checks=required_checks, timed_out=True)


def write_ci_status_artifacts(phase_dir: Path, result: CIStatusResult) -> None:
    phase_dir.mkdir(parents=True, exist_ok=True)
    (phase_dir / "ci_status.json").write_text(
        json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# CI Status",
        "",
        f"State: {result.state}",
        f"Timed out: {str(result.timed_out).lower()}",
        f"Required checks: {', '.join(result.required_checks) or 'none configured'}",
        f"Missing required checks: {', '.join(result.missing_required) or 'none'}",
        f"Blocking checks: {', '.join(result.blocking_checks) or 'none'}",
        "",
        result.message,
    ]
    (phase_dir / "ci_status.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def inspect_branch_protection(
    *,
    branch: str,
    required_checks: list[str] | None = None,
    require_branch_protection: bool = True,
    root: Path = ROOT,
    runner: CommandRunner | None = None,
    dry_run: bool = False,
) -> BranchProtectionResult:
    configured = [name for name in (required_checks or []) if name]
    if dry_run:
        return BranchProtectionResult(
            "DRY_RUN",
            False,
            branch,
            [],
            configured,
            [],
            dry_run=True,
            message="Branch protection inspection skipped in dry-run mode.",
        )

    repo = detect_repo_owner_name(root)
    if repo is None:
        return BranchProtectionResult(
            "BLOCKED",
            False,
            branch,
            [],
            configured,
            configured,
            message="Could not detect GitHub owner/repo from origin remote.",
        )
    auth = gh_auth_status(root=root, runner=runner)
    if auth.blocked:
        return BranchProtectionResult(
            "BLOCKED",
            False,
            branch,
            [],
            configured,
            configured,
            permission_error=True,
            message=auth.instructions or "GitHub CLI is not authenticated.",
        )

    owner, name = repo
    command = ["gh", "api", f"repos/{owner}/{name}/branches/{branch}/protection"]
    result = _run_gh(command, root=root, runner=runner, timeout_seconds=120)
    if result.return_code != 0:
        stderr = result.stderr.lower()
        permission_error = "resource not accessible" in stderr or "forbidden" in stderr or "403" in stderr
        if require_branch_protection:
            return BranchProtectionResult(
                "BLOCKED",
                False,
                branch,
                [],
                configured,
                configured,
                permission_error=permission_error,
                message=result.stderr.strip() or "Branch protection is missing or inaccessible.",
            )
        return BranchProtectionResult(
            "WARN",
            False,
            branch,
            [],
            configured,
            configured,
            permission_error=permission_error,
            message=result.stderr.strip() or "Branch protection is missing or inaccessible.",
        )

    try:
        raw = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return BranchProtectionResult(
            "BLOCKED",
            False,
            branch,
            [],
            configured,
            configured,
            message="Could not parse branch protection response.",
        )
    status_checks = raw.get("required_status_checks") if isinstance(raw, dict) else {}
    contexts = status_checks.get("contexts", []) if isinstance(status_checks, dict) else []
    checks = status_checks.get("checks", []) if isinstance(status_checks, dict) else []
    required = [str(item) for item in contexts if item]
    for check in (checks if isinstance(checks, list) else []):
        if isinstance(check, dict) and check.get("context"):
            required.append(str(check["context"]))
    required = sorted(set(required))
    missing = [name for name in configured if name not in required]
    if missing:
        return BranchProtectionResult(
            "BLOCKED",
            True,
            branch,
            required,
            configured,
            missing,
            message="Configured required checks are not enforced by branch protection.",
            raw=raw if isinstance(raw, dict) else {},
        )
    return BranchProtectionResult(
        "PASS",
        True,
        branch,
        required,
        configured,
        [],
        message="Branch protection requirements match Frontier configuration.",
        raw=raw if isinstance(raw, dict) else {},
    )


def write_branch_protection_artifacts(phase_dir: Path, result: BranchProtectionResult) -> None:
    phase_dir.mkdir(parents=True, exist_ok=True)
    (phase_dir / "branch_protection.json").write_text(
        json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Branch Protection",
        "",
        f"Status: {result.status}",
        f"Branch: {result.branch}",
        f"Protected: {str(result.protected).lower()}",
        f"Permission error: {str(result.permission_error).lower()}",
        f"Configured required checks: {', '.join(result.configured_required_checks) or 'none'}",
        f"Protected required checks: {', '.join(result.required_checks) or 'none'}",
        f"Missing required checks: {', '.join(result.missing_required_checks) or 'none'}",
        "",
        result.message,
    ]
    (phase_dir / "branch_protection.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").lower() in {"1", "true", "yes", "on"}


def _pr_data_from_result(result: GitHubResult) -> dict[str, Any]:
    data = result.metadata.get("pr") if isinstance(result.metadata, dict) else {}
    return data if isinstance(data, dict) else {}


def _pr_is_merged(data: Mapping[str, Any]) -> bool:
    return str(data.get("state") or "").upper() == "MERGED" or bool(data.get("mergedAt"))


def _merge_text(stdout: str, stderr: str) -> str:
    return f"{stdout}\n{stderr}".lower()


def _classify_merge_failure(stdout: str, stderr: str) -> tuple[str, str]:
    text = _merge_text(stdout, stderr)
    if "already merged" in text or "pull request already merged" in text:
        return "already_merged", ALREADY_MERGED
    if "draft" in text:
        return "draft", MERGE_DRAFT_BLOCKED
    if "merge conflict" in text or "merge conflicts" in text or "conflict" in text:
        return "merge_conflict", MERGE_CONFLICT
    if "permission" in text or "resource not accessible" in text or "not authorized" in text:
        return "permission", MERGE_PERMISSION_BLOCKED
    if (
        "base branch policy prohibits the merge" in text
        or "add the `--auto` flag" in text
        or "add --auto" in text
        or "required status check" in text
        or "requirements have been met" in text
        or "merge queue" in text
    ):
        return "branch_policy_timing", MERGE_RETRYABLE
    if "not mergeable" in text:
        return "not_mergeable", MERGE_RETRYABLE
    return "merge_execution_failed", MERGE_EXECUTION_BLOCKED


def _merge_metadata(
    *,
    status: str,
    classification: str,
    command: list[str],
    direct_result: Any | None = None,
    pre_view: GitHubResult | None = None,
    verify_view: GitHubResult | None = None,
    retry_command: list[str] | None = None,
    retry_result: Any | None = None,
    retry_view: GitHubResult | None = None,
    merged: bool = False,
    already_merged: bool = False,
    auto_merge_armed: bool = False,
    direct_merge_performed: bool = False,
    warning: str | None = None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "status": status,
        "classification": classification,
        "merged": merged,
        "already_merged": already_merged,
        "auto_merge_armed": auto_merge_armed,
        "direct_merge_performed": direct_merge_performed,
        "command": command,
    }
    if warning:
        metadata["warning"] = warning
    if pre_view is not None:
        metadata.update(
            {
                "pre_view_command": pre_view.command,
                "pre_view_return_code": pre_view.return_code,
                "pre_view_stdout": pre_view.stdout,
                "pre_view_stderr": pre_view.stderr,
                "pre_pr": _pr_data_from_result(pre_view),
            }
        )
    if direct_result is not None:
        metadata.update(
            {
                "direct_command": command,
                "direct_return_code": getattr(direct_result, "return_code", 0),
                "direct_stdout": getattr(direct_result, "stdout", ""),
                "direct_stderr": getattr(direct_result, "stderr", ""),
            }
        )
    if verify_view is not None:
        metadata.update(
            {
                "verify_command": verify_view.command,
                "verify_return_code": verify_view.return_code,
                "verify_stdout": verify_view.stdout,
                "verify_stderr": verify_view.stderr,
                "verify_pr": _pr_data_from_result(verify_view),
                "verified_merged": _pr_is_merged(_pr_data_from_result(verify_view)),
            }
        )
    if retry_command is not None:
        metadata["retry_command"] = retry_command
    if retry_result is not None:
        metadata.update(
            {
                "retry_return_code": getattr(retry_result, "return_code", 0),
                "retry_stdout": getattr(retry_result, "stdout", ""),
                "retry_stderr": getattr(retry_result, "stderr", ""),
            }
        )
    if retry_view is not None:
        metadata.update(
            {
                "retry_view_command": retry_view.command,
                "retry_view_return_code": retry_view.return_code,
                "retry_view_stdout": retry_view.stdout,
                "retry_view_stderr": retry_view.stderr,
                "retry_pr": _pr_data_from_result(retry_view),
                "retry_verified_merged": _pr_is_merged(_pr_data_from_result(retry_view)),
            }
        )
    return metadata


def _already_merged_result(command: list[str], view: GitHubResult, *, dry_run: bool = False) -> GitHubResult:
    return GitHubResult(
        "merge_pr",
        dry_run,
        command,
        view.return_code,
        view.stdout,
        view.stderr,
        blocked=False,
        metadata=_merge_metadata(
            status=ALREADY_MERGED,
            classification="already_merged",
            command=command,
            pre_view=view,
            merged=True,
            already_merged=True,
        ),
    )


def merge_pr(
    pr: str | int,
    *,
    method: str = "squash",
    root: Path = ROOT,
    dry_run: bool = True,
    runner: CommandRunner | None = None,
) -> GitHubResult:
    command = ["gh", "pr", "merge", str(pr), f"--{method}", "--delete-branch"]
    if os.environ.get("FRONTIER_DISABLE_AUTOMERGE") == "1":
        return GitHubResult(
            "merge_pr",
            dry_run,
            command,
            blocked=True,
            instructions="FRONTIER_DISABLE_AUTOMERGE=1 prevented merge execution.",
            metadata=_merge_metadata(
                status=MERGE_EXECUTION_BLOCKED,
                classification="automerge_disabled",
                command=command,
            ),
        )
    if os.environ.get("FRONTIER_MERGE_DRY_RUN") == "1" or dry_run:
        return GitHubResult(
            "merge_pr",
            True,
            command,
            metadata=_merge_metadata(
                status="DRY_RUN",
                classification="dry_run",
                command=command,
            ),
        )

    auth = gh_auth_status(root=root, runner=runner)
    if auth.blocked:
        return GitHubResult(
            "merge_pr",
            False,
            command,
            auth.return_code,
            auth.stdout,
            auth.stderr,
            blocked=True,
            instructions=auth.instructions,
            metadata={
                **_merge_metadata(
                    status=MERGE_PERMISSION_BLOCKED,
                    classification="auth_blocked",
                    command=command,
                ),
                "auth_command": auth.command,
                "auth_return_code": auth.return_code,
                "auth_stdout": auth.stdout,
                "auth_stderr": auth.stderr,
            },
        )

    pre_view = view_pr(pr, root=root, runner=runner)
    if pre_view.blocked:
        return GitHubResult(
            "merge_pr",
            False,
            command,
            pre_view.return_code,
            pre_view.stdout,
            pre_view.stderr,
            blocked=True,
            instructions=pre_view.instructions,
            metadata=_merge_metadata(
                status=MERGE_EXECUTION_BLOCKED,
                classification="pr_view_blocked",
                command=command,
                pre_view=pre_view,
            ),
        )
    pre_data = _pr_data_from_result(pre_view)
    if _pr_is_merged(pre_data):
        return _already_merged_result(command, pre_view)
    if bool(pre_data.get("isDraft")):
        return GitHubResult(
            "merge_pr",
            False,
            command,
            1,
            pre_view.stdout,
            pre_view.stderr,
            blocked=True,
            instructions="PR is a draft. Mark it ready for review before merge execution.",
            metadata=_merge_metadata(
                status=MERGE_DRAFT_BLOCKED,
                classification="draft",
                command=command,
                pre_view=pre_view,
            ),
        )

    result = _run_gh(command, root=root, runner=runner, timeout_seconds=300)
    if result.return_code == 0:
        verify = view_pr(pr, root=root, runner=runner)
        verified = _pr_is_merged(_pr_data_from_result(verify)) if not verify.blocked else False
        classification = "direct_merged" if verified else "direct_success_unverified"
        return GitHubResult(
            "merge_pr",
            False,
            command,
            result.return_code,
            result.stdout,
            result.stderr,
            blocked=False,
            metadata=_merge_metadata(
                status=MERGED,
                classification=classification,
                command=command,
                direct_result=result,
                pre_view=pre_view,
                verify_view=verify,
                merged=True,
                direct_merge_performed=True,
            ),
        )

    classification, status = _classify_merge_failure(result.stdout, result.stderr)
    post_failure_view = view_pr(pr, root=root, runner=runner)
    post_failure_data = _pr_data_from_result(post_failure_view)
    if _pr_is_merged(post_failure_data) or status == ALREADY_MERGED:
        warning = None if status == ALREADY_MERGED else "Merge command failed, but PR is merged; branch deletion may have failed."
        return GitHubResult(
            "merge_pr",
            False,
            command,
            0,
            result.stdout,
            result.stderr,
            blocked=False,
            instructions=None,
            metadata=_merge_metadata(
                status=ALREADY_MERGED if status == ALREADY_MERGED else MERGED,
                classification="already_merged" if status == ALREADY_MERGED else "direct_failed_pr_merged",
                command=command,
                direct_result=result,
                pre_view=pre_view,
                verify_view=post_failure_view,
                merged=True,
                already_merged=status == ALREADY_MERGED,
                direct_merge_performed=status != ALREADY_MERGED,
                warning=warning,
            ),
        )

    retryable_by_policy = classification in {"branch_policy_timing", "not_mergeable"} or status == MERGE_RETRYABLE
    if retryable_by_policy and _env_flag("FRONTIER_ALLOW_AUTOMERGE"):
        retry_command = ["gh", "pr", "merge", str(pr), "--auto", f"--{method}", "--delete-branch"]
        retry = _run_gh(retry_command, root=root, runner=runner, timeout_seconds=300)
        retry_view = view_pr(pr, root=root, runner=runner)
        retry_merged = _pr_is_merged(_pr_data_from_result(retry_view)) if not retry_view.blocked else False
        if retry.return_code == 0:
            return GitHubResult(
                "merge_pr",
                False,
                command,
                retry.return_code,
                result.stdout,
                result.stderr,
                blocked=False,
                instructions=None
                if retry_merged
                else "Auto-merge is armed. Resume after GitHub merges the PR.",
                metadata=_merge_metadata(
                    status=MERGED if retry_merged else AUTO_MERGE_ARMED,
                    classification="branch_policy_auto_merged" if retry_merged else "branch_policy_auto_armed",
                    command=command,
                    direct_result=result,
                    pre_view=pre_view,
                    retry_command=retry_command,
                    retry_result=retry,
                    retry_view=retry_view,
                    merged=retry_merged,
                    auto_merge_armed=not retry_merged,
                ),
            )
        if retry_merged:
            return GitHubResult(
                "merge_pr",
                False,
                command,
                0,
                result.stdout,
                result.stderr,
                blocked=False,
                metadata=_merge_metadata(
                    status=MERGED,
                    classification="auto_retry_failed_pr_merged",
                    command=command,
                    direct_result=result,
                    pre_view=pre_view,
                    retry_command=retry_command,
                    retry_result=retry,
                    retry_view=retry_view,
                    merged=True,
                    warning="Auto-merge retry returned nonzero, but PR is merged.",
                ),
            )
        retry_classification, retry_status = _classify_merge_failure(retry.stdout, retry.stderr)
        return GitHubResult(
            "merge_pr",
            False,
            command,
            retry.return_code,
            result.stdout,
            result.stderr,
            blocked=True,
            instructions="Auto-merge fallback failed. Inspect command diagnostics and resume after the PR is mergeable.",
            metadata=_merge_metadata(
                status=retry_status,
                classification=f"auto_retry_{retry_classification}",
                command=command,
                direct_result=result,
                pre_view=pre_view,
                retry_command=retry_command,
                retry_result=retry,
                retry_view=retry_view,
            ),
        )

    instructions = "Inspect `gh pr merge` output and resume after the PR is mergeable."
    if retryable_by_policy and not _env_flag("FRONTIER_ALLOW_AUTOMERGE"):
        instructions = (
            "Merge execution hit a retryable branch-policy condition. "
            "Set FRONTIER_ALLOW_AUTOMERGE=1 to arm GitHub auto-merge on retry, or merge manually after requirements settle."
        )
    return GitHubResult(
        "merge_pr",
        False,
        command,
        result.return_code,
        result.stdout,
        result.stderr,
        blocked=True,
        instructions=instructions,
        metadata=_merge_metadata(
            status=status,
            classification=classification,
            command=command,
            direct_result=result,
            pre_view=pre_view,
            verify_view=post_failure_view,
        ),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GitHub utilities for Frontier Workflow 2.")
    parser.add_argument("--detect-repo", action="store_true")
    parser.add_argument("--default-branch", action="store_true")
    parser.add_argument("--preview-pr", action="store_true")
    parser.add_argument("--base", default="main")
    parser.add_argument("--head")
    parser.add_argument("--title", default="Frontier automated PR")
    args = parser.parse_args(argv)
    if args.detect_repo:
        print(detect_repo_remote(ROOT) or "")
        return 0
    if args.default_branch:
        print(detect_default_branch(root=ROOT))
        return 0
    if args.preview_pr:
        result = create_pr(
            title=args.title,
            body="Dry-run preview.",
            base=args.base,
            head=args.head,
            dry_run=True,
        )
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
