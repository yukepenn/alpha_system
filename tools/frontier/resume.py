"""Workflow 2 stage checkpoints and resume precondition checks."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


WORKFLOW2_STAGES = (
    "spec",
    "execute",
    "validate",
    "review",
    "done_check",
    "commit",
    "push",
    "pr",
    "ci",
    "branch_protection",
    "merge_gate",
    "merge",
    "complete",
)
DETERMINISTIC_RERUN_STAGES = {"ci", "branch_protection", "merge_gate", "merge"}
PASSING_VERDICTS = {"PASS", "PASS_WITH_WARNINGS"}
CI_SUCCESS = "SUCCESS"
RESUME_PRECONDITION_FAILED = "RESUME_PRECONDITION_FAILED"
MERGED = "MERGED"
ALREADY_MERGED = "ALREADY_MERGED"
AUTO_MERGE_ARMED = "AUTO_MERGE_ARMED"


@dataclass(frozen=True)
class StageCheckpoint:
    stage: str
    complete: bool
    artifacts: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    invalid: list[str] = field(default_factory=list)
    note: str = ""

    @property
    def ok(self) -> bool:
        return self.complete and not self.missing and not self.invalid

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResumePrecondition:
    ok: bool
    from_stage: str
    checked_stages: list[StageCheckpoint]
    missing: list[str]
    invalid: list[str]
    rerun_stages: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "from_stage": self.from_stage,
            "checked_stages": [item.to_dict() for item in self.checked_stages],
            "missing": self.missing,
            "invalid": self.invalid,
            "rerun_stages": self.rerun_stages,
        }


def stage_index(stage: str) -> int:
    if stage not in WORKFLOW2_STAGES:
        raise ValueError(f"Unknown Workflow 2 stage: {stage}")
    return WORKFLOW2_STAGES.index(stage)


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _nonempty(path: Path) -> bool:
    try:
        return path.is_file() and bool(path.read_text(encoding="utf-8").strip())
    except OSError:
        return False


def _rel(path: Path, phase_dir: Path) -> str:
    try:
        return str(path.relative_to(phase_dir))
    except ValueError:
        return str(path)


def _checkpoint(
    stage: str,
    *,
    complete: bool,
    artifacts: list[str],
    missing: list[str] | None = None,
    invalid: list[str] | None = None,
    note: str = "",
) -> StageCheckpoint:
    return StageCheckpoint(
        stage=stage,
        complete=complete,
        artifacts=artifacts,
        missing=missing or [],
        invalid=invalid or [],
        note=note,
    )


def _require_files(stage: str, phase_dir: Path, names: list[str]) -> StageCheckpoint:
    missing = [name for name in names if not _nonempty(phase_dir / name)]
    return _checkpoint(stage, complete=not missing, artifacts=names, missing=missing)


def _verdict_value(data: dict[str, Any] | None) -> str | None:
    if not isinstance(data, dict):
        return None
    value = data.get("verdict", data.get("result"))
    return str(value) if value is not None else None


def recover_pr_number(phase_dir: Path, phase: dict[str, Any], state: dict[str, Any]) -> int | None:
    candidates: list[Any] = [
        phase.get("pr_number"),
        state.get("pr_number"),
    ]
    pr_create = _read_json(phase_dir / "pr_create.json") or {}
    metadata = pr_create.get("metadata") if isinstance(pr_create.get("metadata"), dict) else {}
    nested_pr = metadata.get("pr") if isinstance(metadata.get("pr"), dict) else {}
    candidates.extend([metadata.get("number"), nested_pr.get("number"), pr_create.get("number")])
    for candidate in candidates:
        try:
            number = int(str(candidate))
        except (TypeError, ValueError):
            continue
        if number > 0:
            return number
    return None


def validate_stage_complete(
    stage: str,
    phase_dir: Path,
    phase: dict[str, Any],
    state: dict[str, Any],
    *,
    allow_deterministic_rerun: bool = False,
) -> StageCheckpoint:
    if stage == "spec":
        return _require_files(stage, phase_dir, ["spec.md"])

    if stage == "execute":
        return _require_files(stage, phase_dir, ["executor_output.md"])

    if stage == "validate":
        return _require_files(stage, phase_dir, ["validation.md"])

    if stage == "review":
        required = ["review.md", "verdict.json"]
        missing = [name for name in required if not _nonempty(phase_dir / name)]
        invalid: list[str] = []
        verdict = _verdict_value(_read_json(phase_dir / "verdict.json"))
        if "verdict.json" not in missing and verdict not in PASSING_VERDICTS:
            invalid.append("verdict.json must contain PASS or PASS_WITH_WARNINGS")
        return _checkpoint(stage, complete=not missing and not invalid, artifacts=required, missing=missing, invalid=invalid)

    if stage == "done_check":
        required = ["done_check.json"]
        missing = [name for name in required if not _nonempty(phase_dir / name)]
        invalid: list[str] = []
        verdict = _verdict_value(_read_json(phase_dir / "done_check.json"))
        if "done_check.json" not in missing and verdict not in PASSING_VERDICTS:
            invalid.append("done_check.json must contain PASS or PASS_WITH_WARNINGS")
        return _checkpoint(stage, complete=not missing and not invalid, artifacts=required, missing=missing, invalid=invalid)

    if stage == "commit":
        artifacts = ["git_phase.json", "commit_sha.txt"]
        git_phase = _read_json(phase_dir / "git_phase.json")
        missing = []
        if git_phase is None:
            missing.append("git_phase.json")
        commit_sha = (
            phase.get("commit_sha")
            or state.get("commit_sha")
            or (git_phase or {}).get("commit_sha")
            or ((phase_dir / "commit_sha.txt").read_text(encoding="utf-8").strip() if (phase_dir / "commit_sha.txt").exists() else "")
        )
        if not str(commit_sha or "").strip():
            missing.append("commit_sha.txt")
        return _checkpoint(stage, complete=not missing, artifacts=artifacts, missing=missing)

    if stage == "push":
        artifacts = ["push_branch.json", "remote_branch.json"]
        push = _read_json(phase_dir / "push_branch.json")
        remote = _read_json(phase_dir / "remote_branch.json")
        push_ok = bool(push and (push.get("dry_run") or push.get("pushed") or push.get("return_code") == 0))
        remote_ok = bool(remote and (remote.get("dry_run") or (remote.get("exists") and remote.get("matches"))))
        missing = [] if push_ok or remote_ok else ["push_branch.json or remote_branch.json"]
        return _checkpoint(stage, complete=not missing, artifacts=artifacts, missing=missing)

    if stage == "pr":
        artifacts = ["pr_create.json"]
        number = recover_pr_number(phase_dir, phase, state)
        missing = [] if number is not None else ["pr_create.json"]
        invalid = [] if number is not None else ["pr_create.json must contain a valid PR number"]
        return _checkpoint(stage, complete=number is not None, artifacts=artifacts, missing=missing, invalid=invalid)

    if stage == "ci":
        artifacts = ["ci_status.json"]
        data = _read_json(phase_dir / "ci_status.json")
        if data and str(data.get("state", "")).upper() == CI_SUCCESS:
            return _checkpoint(stage, complete=True, artifacts=artifacts)
        if allow_deterministic_rerun:
            return _checkpoint(stage, complete=True, artifacts=artifacts, note="CI will be rechecked during resume.")
        missing = [] if data else ["ci_status.json"]
        invalid = [] if not data else ["ci_status.json state must be SUCCESS"]
        return _checkpoint(stage, complete=False, artifacts=artifacts, missing=missing, invalid=invalid)

    if stage == "branch_protection":
        artifacts = ["branch_protection.json"]
        data = _read_json(phase_dir / "branch_protection.json")
        if data and data.get("status") == "PASS":
            return _checkpoint(stage, complete=True, artifacts=artifacts)
        if allow_deterministic_rerun:
            return _checkpoint(
                stage,
                complete=True,
                artifacts=artifacts,
                note="Branch protection will be inspected during resume.",
            )
        missing = [] if data else ["branch_protection.json"]
        invalid = [] if not data else ["branch_protection.json status must be PASS"]
        return _checkpoint(stage, complete=False, artifacts=artifacts, missing=missing, invalid=invalid)

    if stage == "merge_gate":
        artifacts = ["merge_gate.json"]
        data = _read_json(phase_dir / "merge_gate.json")
        if data and bool(data.get("merge_allowed")):
            return _checkpoint(stage, complete=True, artifacts=artifacts)
        if allow_deterministic_rerun:
            return _checkpoint(stage, complete=True, artifacts=artifacts, note="Merge gate will be reevaluated during resume.")
        missing = [] if data else ["merge_gate.json"]
        invalid = [] if not data else ["merge_gate.json must allow merge"]
        return _checkpoint(stage, complete=False, artifacts=artifacts, missing=missing, invalid=invalid)

    if stage == "merge":
        artifacts = ["merge_result.json"]
        data = _read_json(phase_dir / "merge_result.json")
        metadata = data.get("metadata") if isinstance(data, dict) and isinstance(data.get("metadata"), dict) else {}
        status = str(metadata.get("status") or "")
        merged = bool(
            data
            and data.get("action") == "merge_pr"
            and not data.get("dry_run")
            and not data.get("blocked")
            and (
                status in {MERGED, ALREADY_MERGED}
                or bool(metadata.get("merged"))
                or (not status and int(data.get("return_code", 1)) == 0)
            )
        )
        auto_merge_armed = bool(data and data.get("action") == "merge_pr" and status == AUTO_MERGE_ARMED)
        if merged or phase.get("merged") or state.get("merged"):
            return _checkpoint(stage, complete=True, artifacts=artifacts)
        if auto_merge_armed and allow_deterministic_rerun:
            return _checkpoint(stage, complete=True, artifacts=artifacts, note="Auto-merge is armed and will be checked during resume.")
        if allow_deterministic_rerun:
            return _checkpoint(stage, complete=True, artifacts=artifacts, note="Merge will be retried if gates allow it.")
        missing = [] if data else ["merge_result.json"]
        invalid = [] if not data else ["merge_result.json must show a successful non-dry-run merge"]
        return _checkpoint(stage, complete=False, artifacts=artifacts, missing=missing, invalid=invalid)

    if stage == "complete":
        ok = phase.get("status") in PASSING_VERDICTS
        return _checkpoint(
            stage,
            complete=ok,
            artifacts=[],
            invalid=[] if ok else ["phase status must be PASS or PASS_WITH_WARNINGS"],
        )

    raise ValueError(f"Unknown Workflow 2 stage: {stage}")


def validate_resume_preconditions(
    *,
    phase_dir: Path,
    phase: dict[str, Any],
    state: dict[str, Any],
    from_stage: str,
    allow_deterministic_rerun: bool = True,
) -> ResumePrecondition:
    start = stage_index(from_stage)
    checked: list[StageCheckpoint] = []
    rerun_stages: list[str] = []
    missing: list[str] = []
    invalid: list[str] = []
    for stage in WORKFLOW2_STAGES[:start]:
        allow_rerun = allow_deterministic_rerun and stage in DETERMINISTIC_RERUN_STAGES
        check = validate_stage_complete(
            stage,
            phase_dir,
            phase,
            state,
            allow_deterministic_rerun=allow_rerun,
        )
        checked.append(check)
        if check.note and allow_rerun:
            rerun_stages.append(stage)
        missing.extend(f"{stage}: {item}" for item in check.missing)
        invalid.extend(f"{stage}: {item}" for item in check.invalid)
    return ResumePrecondition(not missing and not invalid, from_stage, checked, missing, invalid, rerun_stages)


def changed_files_from_artifacts(phase_dir: Path) -> list[str]:
    git_phase = _read_json(phase_dir / "git_phase.json") or {}
    changed = git_phase.get("changed_files")
    if isinstance(changed, list):
        return [str(item) for item in changed if str(item).strip()]
    changed_path = phase_dir / "changed_files.txt"
    if changed_path.exists():
        return [line.strip() for line in changed_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return []


def summarize_resume_failure(precondition: ResumePrecondition) -> str:
    details: list[str] = []
    if precondition.missing:
        details.append("missing artifacts: " + ", ".join(precondition.missing))
    if precondition.invalid:
        details.append("invalid artifacts: " + ", ".join(precondition.invalid))
    return "; ".join(details) or "resume preconditions failed"
