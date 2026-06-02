"""Small safe Git helpers for Frontier runtime tools."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

from tools.frontier.artifact_policy import curate_commit_paths


ROOT = Path(__file__).resolve().parents[2]
SLUG_RE = re.compile(r"[^A-Za-z0-9_.-]+")


@dataclass(frozen=True)
class GitPhaseResult:
    dry_run: bool
    branch: str
    changed_files: list[str]
    staged_files: list[str]
    blocked_files: list[str]
    commit_sha: str | None = None
    pushed: bool = False
    commands: list[list[str]] = field(default_factory=list)
    status_before: str = ""
    status_after: str = ""
    diff_stat: str = ""
    message: str = ""
    base_sha: str | None = None
    diff_files: list[str] = field(default_factory=list)
    source: str = "uncommitted_changes"

    @property
    def ok(self) -> bool:
        return not self.blocked_files and bool(self.dry_run or self.commit_sha)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BranchPrepareResult:
    dry_run: bool
    requested_branch: str
    branch: str
    base_ref: str
    base_sha: str
    previous_branch: str
    previous_head_sha: str
    head_sha: str
    branch_existed: bool
    remote_tracking_ref: str | None = None
    used_unique_branch: bool = False
    commands: list[list[str]] = field(default_factory=list)
    status_before: str = ""
    status_after: str = ""
    message: str = ""

    @property
    def ok(self) -> bool:
        return bool(self.branch and self.base_sha and (self.dry_run or self.head_sha == self.base_sha))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PushBranchResult:
    dry_run: bool
    branch: str
    remote: str
    command: list[str]
    return_code: int = 0
    stdout: str = ""
    stderr: str = ""
    pushed: bool = False
    instructions: str | None = None

    @property
    def ok(self) -> bool:
        return self.dry_run or (self.return_code == 0 and self.pushed)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RemoteBranchResult:
    exists: bool
    remote_sha: str
    local_sha: str
    matches: bool
    stdout: str
    stderr: str
    return_code: int
    branch: str = ""
    remote: str = "origin"
    command: list[str] = field(default_factory=list)
    dry_run: bool = False

    @property
    def ok(self) -> bool:
        return self.dry_run or (self.return_code == 0 and self.exists and self.matches)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    blocked = {
        ("reset", "--hard"),
        ("clean", "-fd"),
        ("clean", "-fdx"),
        ("push", "--force"),
        ("push", "-f"),
    }
    if len(args) >= 2 and tuple(args[:2]) in blocked:
        raise ValueError(f"Refusing destructive git command: git {' '.join(args)}")
    if len(args) >= 2 and args[0] == "add" and args[1] in {".", "-A"}:
        raise ValueError(f"Refusing broad git staging command: git {' '.join(args)}")
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)


def current_branch(root: Path = ROOT) -> str:
    result = git(root, "branch", "--show-current")
    return result.stdout.strip()


def rev_parse(root: Path, ref: str = "HEAD") -> str | None:
    result = git(root, "rev-parse", "--verify", ref + "^" + "{commit}")
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def local_commit_exists(root: Path, commit_sha: str | None) -> bool:
    if not commit_sha:
        return False
    result = git(root, "cat-file", "-e", commit_sha + "^" + "{commit}")
    return result.returncode == 0


def ref_exists(root: Path, ref: str) -> bool:
    result = git(root, "rev-parse", "--verify", "--quiet", ref)
    return result.returncode == 0


def local_branch_exists(root: Path, branch: str) -> bool:
    validate_branch_name(branch)
    return ref_exists(root, f"refs/heads/{branch}")


def remote_tracking_ref(root: Path, branch: str, *, remote: str = "origin") -> str | None:
    validate_branch_name(branch)
    ref = f"refs/remotes/{remote}/{branch}"
    return ref if ref_exists(root, ref) else None


def resolve_base_ref(root: Path, default_branch: str = "main", *, remote: str = "origin") -> tuple[str, str]:
    branch = validate_branch_name(default_branch)
    candidates = [f"{remote}/{branch}", branch, "HEAD"]
    for candidate in candidates:
        sha = rev_parse(root, candidate)
        if sha:
            return candidate, sha
    raise RuntimeError(f"Could not resolve a base commit for default branch {default_branch!r}.")


def repo_name(root: Path = ROOT) -> str:
    return root.resolve().name


def sanitize_component(value: str, *, fallback: str = "frontier") -> str:
    cleaned = SLUG_RE.sub("-", value.strip()).strip(".-_/").lower()
    return cleaned[:80] or fallback


def validate_branch_name(branch: str) -> str:
    if not branch or branch.strip() != branch:
        raise ValueError("Branch name must be non-empty and must not contain surrounding whitespace.")
    if branch in {"HEAD", "@", "."} or branch.startswith("-"):
        raise ValueError(f"Unsafe branch name: {branch!r}")
    forbidden_tokens = ("..", "//", "@{")
    forbidden_chars = set(" ~^:?*[\\")
    if any(token in branch for token in forbidden_tokens) or any(char in forbidden_chars for char in branch):
        raise ValueError(f"Unsafe branch name: {branch!r}")
    if branch.startswith("/") or branch.endswith("/") or branch.endswith("."):
        raise ValueError(f"Unsafe branch name: {branch!r}")
    for component in branch.split("/"):
        if component in {"", ".", ".."} or component.startswith(".") or component.endswith(".lock"):
            raise ValueError(f"Unsafe branch name: {branch!r}")
    return branch


def _status_paths(status_text: str) -> list[str]:
    paths: list[str] = []
    for line in status_text.splitlines():
        if not line:
            continue
        payload = line[3:] if len(line) > 3 else line
        if " -> " in payload:
            payload = payload.split(" -> ", 1)[1]
        paths.append(payload.strip())
    return paths


def status_porcelain(root: Path = ROOT) -> str:
    result = git(root, "status", "--porcelain", "--untracked-files=all")
    return result.stdout if result.returncode == 0 else ""


def changed_files(root: Path = ROOT) -> list[str]:
    return _status_paths(status_porcelain(root))


def staged_files(root: Path = ROOT) -> list[str]:
    result = git(root, "diff", "--cached", "--name-only")
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line]


def diff_stat(root: Path = ROOT) -> str:
    result = git(root, "diff", "--stat", "HEAD")
    return result.stdout if result.returncode == 0 else ""


def diff_stat_between(root: Path, base_sha: str, head_ref: str = "HEAD") -> str:
    result = git(root, "diff", "--stat", f"{base_sha}..{head_ref}")
    return result.stdout if result.returncode == 0 else ""


def diff_files_between(root: Path, base_sha: str, head_ref: str = "HEAD") -> list[str]:
    result = git(root, "diff", "--name-only", f"{base_sha}..{head_ref}")
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def remote_url(root: Path = ROOT, remote: str = "origin") -> str | None:
    result = git(root, "remote", "get-url", remote)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _unique_retry_branch(root: Path, branch: str, *, remote: str = "origin") -> str:
    for index in range(2, 1000):
        candidate = f"{branch}-retry-{index}"
        if not local_branch_exists(root, candidate) and remote_tracking_ref(root, candidate, remote=remote) is None:
            return candidate
    raise RuntimeError(f"Could not find an unused retry branch for {branch}.")


def prepare_phase_branch(
    root: Path,
    branch: str,
    *,
    base_ref: str,
    dry_run: bool = False,
    remote: str = "origin",
) -> BranchPrepareResult:
    requested_branch = validate_branch_name(branch)
    base_sha = rev_parse(root, base_ref)
    if not base_sha:
        raise RuntimeError(f"Could not resolve base ref {base_ref!r} before preparing phase branch.")
    previous_branch = current_branch(root)
    previous_head_sha = rev_parse(root, "HEAD") or ""
    status_before = status_porcelain(root)
    branch_existed = local_branch_exists(root, requested_branch)
    tracking_ref = remote_tracking_ref(root, requested_branch, remote=remote)
    final_branch = requested_branch
    used_unique_branch = False
    if tracking_ref is not None:
        final_branch = _unique_retry_branch(root, requested_branch, remote=remote)
        used_unique_branch = True
    command = ["git", "checkout", "-B", final_branch, base_ref]
    commands = [command]
    if dry_run:
        head_sha = base_sha
        status_after = status_before
    else:
        result = git(root, "checkout", "-B", final_branch, base_ref)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        head_sha = rev_parse(root, "HEAD") or ""
        status_after = status_porcelain(root)
    message = (
        f"Prepared {final_branch} from {base_ref}."
        if not used_unique_branch
        else f"Prepared retry branch {final_branch} from {base_ref} because {tracking_ref} already exists."
    )
    return BranchPrepareResult(
        dry_run=dry_run,
        requested_branch=requested_branch,
        branch=final_branch,
        base_ref=base_ref,
        base_sha=base_sha,
        previous_branch=previous_branch,
        previous_head_sha=previous_head_sha,
        head_sha=head_sha,
        branch_existed=branch_existed,
        remote_tracking_ref=tracking_ref,
        used_unique_branch=used_unique_branch,
        commands=commands,
        status_before=status_before,
        status_after=status_after,
        message=message,
    )


def checkout_or_create_branch(root: Path, branch: str, *, dry_run: bool = False, base_ref: str | None = None) -> list[list[str]]:
    command = ["git", "checkout", "-B", branch]
    if base_ref:
        command.append(base_ref)
    commands = [command]
    if not dry_run:
        result = git(root, "checkout", "-B", branch, *([base_ref] if base_ref else []))
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return commands


def stage_paths(root: Path, paths: list[str], *, dry_run: bool = False) -> list[list[str]]:
    commands: list[list[str]] = []
    for path in paths:
        command = ["git", "add", "--", path]
        commands.append(command)
        if not dry_run:
            result = git(root, "add", "--", path)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return commands


def commit_staged(root: Path, message: str, *, dry_run: bool = False) -> tuple[str | None, list[list[str]]]:
    command = ["git", "commit", "-m", message]
    if dry_run:
        return None, [command]
    result = git(root, "commit", "-m", message)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    sha = git(root, "rev-parse", "HEAD").stdout.strip()
    return sha or None, [command]


def push_phase_branch(root: Path, branch: str, *, remote: str = "origin", dry_run: bool = False) -> PushBranchResult:
    validate_branch_name(branch)
    if not remote or remote.startswith("-") or any(char.isspace() for char in remote):
        raise ValueError(f"Unsafe git remote name: {remote!r}")
    command = ["git", "push", "-u", remote, f"HEAD:refs/heads/{branch}"]
    if dry_run:
        return PushBranchResult(True, branch, remote, command, pushed=False)
    result = git(root, "push", "-u", remote, f"HEAD:refs/heads/{branch}")
    instructions = None
    if result.returncode != 0:
        instructions = "Network/auth push failed. Fix git push output and resume the run."
    return PushBranchResult(
        False,
        branch,
        remote,
        command,
        result.returncode,
        result.stdout,
        result.stderr,
        pushed=result.returncode == 0,
        instructions=instructions,
    )


def verify_remote_branch(root: Path, branch: str, *, remote: str = "origin") -> RemoteBranchResult:
    validate_branch_name(branch)
    if not remote or remote.startswith("-") or any(char.isspace() for char in remote):
        raise ValueError(f"Unsafe git remote name: {remote!r}")
    local = git(root, "rev-parse", branch)
    local_sha = local.stdout.strip() if local.returncode == 0 else ""
    local_error = local.stderr.strip() or local.stdout.strip()
    if not local_sha:
        head = git(root, "rev-parse", "HEAD")
        if head.returncode == 0 and head.stdout.strip():
            local_sha = head.stdout.strip()
            local_error = ""
    ref = f"refs/heads/{branch}"
    command = ["git", "ls-remote", "--heads", remote, ref]
    result = git(root, "ls-remote", "--heads", remote, ref)
    remote_sha = ""
    exists = False
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            sha, _, name = line.partition("\t")
            if name == ref and sha:
                remote_sha = sha.strip()
                exists = True
                break
    stderr = result.stderr
    return_code = result.returncode
    if local_error:
        stderr = (stderr + "\n" if stderr else "") + local_error
        return_code = local.returncode if return_code == 0 else return_code
    return RemoteBranchResult(
        exists=exists,
        remote_sha=remote_sha,
        local_sha=local_sha,
        matches=bool(exists and remote_sha and local_sha and remote_sha == local_sha),
        stdout=result.stdout,
        stderr=stderr,
        return_code=return_code,
        branch=branch,
        remote=remote,
        command=command,
    )


def push_branch(root: Path, branch: str, *, dry_run: bool = False) -> tuple[bool, list[list[str]]]:
    result = push_phase_branch(root, branch, dry_run=dry_run)
    if not result.ok and not dry_run:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.pushed, [result.command]


def commit_phase_changes(
    *,
    root: Path,
    campaign_id: str,
    phase_id: str,
    summary: str,
    branch: str,
    config: Mapping[str, Any],
    dry_run: bool,
    push: bool,
    base_sha: str | None = None,
) -> GitPhaseResult:
    artifacts = config.get("artifacts") if isinstance(config.get("artifacts"), Mapping) else {}
    allow_patterns = list(artifacts.get("allow_commit", [])) if isinstance(artifacts, Mapping) else []
    forbid_patterns = list(artifacts.get("forbid_commit", [])) if isinstance(artifacts, Mapping) else []
    placeholder_exceptions = artifacts.get("placeholder_exceptions") if isinstance(artifacts, Mapping) else None
    placeholder_dirs = artifacts.get("placeholder_dirs") if isinstance(artifacts, Mapping) else None
    if not isinstance(placeholder_exceptions, list):
        placeholder_exceptions = None
    if not isinstance(placeholder_dirs, list):
        placeholder_dirs = None
    validate_branch_name(branch)
    status_before = status_porcelain(root)
    files = changed_files(root)
    commands: list[list[str]] = []
    message = f"{campaign_id}/{phase_id}: {summary}"
    current_head = rev_parse(root, "HEAD")

    if not dry_run:
        active_branch = current_branch(root)
        if active_branch and active_branch != branch:
            return GitPhaseResult(
                dry_run=dry_run,
                branch=branch,
                changed_files=files,
                staged_files=[],
                blocked_files=[f"git branch {active_branch} is not expected phase branch {branch}"],
                commit_sha=None,
                pushed=False,
                commands=commands,
                status_before=status_before,
                status_after=status_porcelain(root),
                diff_stat=diff_stat(root),
                message=message,
                base_sha=base_sha,
                diff_files=[],
                source="wrong_branch",
            )

    allowed, blocked = curate_commit_paths(
        files,
        allow_patterns=allow_patterns,
        forbid_patterns=forbid_patterns,
        placeholder_exceptions=placeholder_exceptions,
        placeholder_dirs=placeholder_dirs,
    )
    if blocked:
        return GitPhaseResult(
            dry_run=dry_run,
            branch=branch,
            changed_files=files,
            staged_files=allowed,
            blocked_files=blocked,
            commit_sha=None,
            pushed=False,
            commands=commands,
            status_before=status_before,
            status_after=status_porcelain(root),
            diff_stat=diff_stat(root),
            message=message,
            base_sha=base_sha,
            diff_files=files,
            source="uncommitted_changes_blocked",
        )

    if not files and base_sha and current_head and current_head != base_sha:
        diff_files = diff_files_between(root, base_sha, "HEAD")
        diff_allowed, diff_blocked = curate_commit_paths(
            diff_files,
            allow_patterns=allow_patterns,
            forbid_patterns=forbid_patterns,
            placeholder_exceptions=placeholder_exceptions,
            placeholder_dirs=placeholder_dirs,
        )
        return GitPhaseResult(
            dry_run=dry_run,
            branch=branch,
            changed_files=diff_files,
            staged_files=diff_allowed,
            blocked_files=diff_blocked,
            commit_sha=None if diff_blocked else current_head,
            pushed=False,
            commands=commands,
            status_before=status_before,
            status_after=status_porcelain(root),
            diff_stat=diff_stat_between(root, base_sha, "HEAD"),
            message=message,
            base_sha=base_sha,
            diff_files=diff_files,
            source="existing_head_commit",
        )

    if not files:
        return GitPhaseResult(
            dry_run=dry_run,
            branch=branch,
            changed_files=[],
            staged_files=[],
            blocked_files=[],
            commit_sha=None,
            pushed=False,
            commands=commands,
            status_before=status_before,
            status_after=status_porcelain(root),
            diff_stat=diff_stat_between(root, base_sha, "HEAD") if base_sha else diff_stat(root),
            message=message,
            base_sha=base_sha,
            diff_files=[],
            source="no_phase_commit",
        )

    commands.extend(stage_paths(root, allowed, dry_run=dry_run))
    if not dry_run:
        cached_allowed, cached_blocked = curate_commit_paths(
            staged_files(root),
            allow_patterns=allow_patterns,
            forbid_patterns=forbid_patterns,
            placeholder_exceptions=placeholder_exceptions,
            placeholder_dirs=placeholder_dirs,
        )
        if cached_blocked:
            blocked_list = ", ".join(cached_blocked)
            return GitPhaseResult(
                dry_run=dry_run,
                branch=branch,
                changed_files=files,
                staged_files=cached_allowed,
                blocked_files=cached_blocked,
                commit_sha=None,
                pushed=False,
                commands=commands,
                status_before=status_before,
                status_after=status_porcelain(root),
                diff_stat=diff_stat(root),
                message=f"Blocked forbidden paths in git diff --cached --name-only before commit: {blocked_list}",
                base_sha=base_sha,
                diff_files=files,
                source="cached_diff_blocked",
            )
        allowed = cached_allowed
    stat = diff_stat(root)
    sha: str | None = None
    pushed = False
    source = "uncommitted_changes"
    if allowed:
        commit_sha, commit_commands = commit_staged(root, message, dry_run=dry_run)
        sha = commit_sha
        commands.extend(commit_commands)
        if base_sha and not dry_run:
            files = diff_files_between(root, base_sha, "HEAD")
            stat = diff_stat_between(root, base_sha, "HEAD")
        if push:
            pushed, push_commands = push_branch(root, branch, dry_run=dry_run)
            commands.extend(push_commands)
    status_after = status_porcelain(root)
    return GitPhaseResult(
        dry_run=dry_run,
        branch=branch,
        changed_files=files,
        staged_files=allowed,
        blocked_files=blocked,
        commit_sha=sha,
        pushed=pushed,
        commands=commands,
        status_before=status_before,
        status_after=status_after,
        diff_stat=stat,
        message=message,
        base_sha=base_sha,
        diff_files=files,
        source=source,
    )


def write_branch_prepare_artifacts(phase_dir: Path, result: BranchPrepareResult) -> None:
    phase_dir.mkdir(parents=True, exist_ok=True)
    (phase_dir / "branch_prepare.json").write_text(
        json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (phase_dir / "branch_prepare.md").write_text(
        "\n".join(
            [
                "# Branch Prepare",
                "",
                f"Requested branch: {result.requested_branch}",
                f"Prepared branch: {result.branch}",
                f"Base ref: {result.base_ref}",
                f"Base SHA: {result.base_sha}",
                f"Previous branch: {result.previous_branch or 'detached'}",
                f"Previous HEAD: {result.previous_head_sha or 'unknown'}",
                f"Retry branch: {str(result.used_unique_branch).lower()}",
                "",
                result.message,
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (phase_dir / "branch.txt").write_text(result.branch + "\n", encoding="utf-8")
    (phase_dir / "base_sha.txt").write_text(result.base_sha + "\n", encoding="utf-8")


def write_git_phase_artifacts(phase_dir: Path, result: GitPhaseResult) -> None:
    phase_dir.mkdir(parents=True, exist_ok=True)
    (phase_dir / "git_phase.json").write_text(
        json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (phase_dir / "changed_files.txt").write_text("\n".join(result.changed_files) + "\n", encoding="utf-8")
    (phase_dir / "diff_files.txt").write_text("\n".join(result.diff_files) + "\n", encoding="utf-8")
    (phase_dir / "diff_stat.txt").write_text(result.diff_stat, encoding="utf-8")
    (phase_dir / "git_status_before_commit.txt").write_text(result.status_before, encoding="utf-8")
    (phase_dir / "git_status_after_commit.txt").write_text(result.status_after, encoding="utf-8")
    (phase_dir / "branch.txt").write_text(result.branch + "\n", encoding="utf-8")
    if result.base_sha:
        (phase_dir / "base_sha.txt").write_text(result.base_sha + "\n", encoding="utf-8")
    if result.commit_sha:
        (phase_dir / "commit_sha.txt").write_text(result.commit_sha + "\n", encoding="utf-8")
    else:
        (phase_dir / "commit_sha.txt").write_text("", encoding="utf-8")


def write_push_branch_artifacts(phase_dir: Path, result: PushBranchResult) -> None:
    phase_dir.mkdir(parents=True, exist_ok=True)
    (phase_dir / "push_branch.json").write_text(
        json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Branch Push",
        "",
        f"Branch: {result.branch}",
        f"Remote: {result.remote}",
        f"Dry run: {str(result.dry_run).lower()}",
        f"Pushed: {str(result.pushed).lower()}",
        f"Return code: {result.return_code}",
        f"Command: `{' '.join(result.command)}`",
        "",
    ]
    if result.instructions:
        lines.extend(["## Instructions", "", result.instructions, ""])
    if result.stdout:
        lines.extend(["## stdout", "", "```text", result.stdout.rstrip(), "```", ""])
    if result.stderr:
        lines.extend(["## stderr", "", "```text", result.stderr.rstrip(), "```", ""])
    (phase_dir / "push_branch.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_remote_branch_artifacts(phase_dir: Path, result: RemoteBranchResult) -> None:
    phase_dir.mkdir(parents=True, exist_ok=True)
    (phase_dir / "remote_branch.json").write_text(
        json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Remote Branch",
        "",
        f"Branch: {result.branch}",
        f"Remote: {result.remote}",
        f"Dry run: {str(result.dry_run).lower()}",
        f"Exists: {str(result.exists).lower()}",
        f"Matches local: {str(result.matches).lower()}",
        f"Local SHA: {result.local_sha or 'unknown'}",
        f"Remote SHA: {result.remote_sha or 'unknown'}",
        f"Return code: {result.return_code}",
    ]
    (phase_dir / "remote_branch.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
