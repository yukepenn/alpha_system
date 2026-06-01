"""Frontier merge gate and lane-based auto-merge policy."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.frontier.config import load_config
from tools.frontier.github_utils import BranchProtectionResult, GitHubResult, merge_pr
from tools.frontier.verdict import VALID_VERDICTS


PASSING = {"PASS", "PASS_WITH_WARNINGS"}


@dataclass(frozen=True)
class MergeGateResult:
    status: str
    merge_allowed: bool
    reasons: list[str]
    campaign_id: str
    phase_id: str
    lane: str
    ci_status: str
    verdict: str
    dry_run: bool = True
    auto_pr_allowed: bool = False
    auto_merge_configured: bool = False
    merge_method: str = "squash"
    merge_command: list[str] = field(default_factory=list)
    branch_protection_status: str | None = None
    critical_findings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _lane_policy(config: Mapping[str, Any], lane: str) -> Mapping[str, Any]:
    lanes = config.get("lanes", {})
    if isinstance(lanes, Mapping):
        policy = lanes.get(lane.lower(), {})
        if isinstance(policy, Mapping):
            return policy
    return {}


def _nested(mapping: Mapping[str, Any], *keys: str, default: Any = None) -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, Mapping):
            return default
        current = current.get(key)
    return default if current is None else current


def _verdict_from_file(path: Path | None) -> tuple[str, list[str], str]:
    if path is None:
        return "BLOCKED", [], "critical"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "BLOCKED", ["Could not read verdict JSON."], "critical"
    verdict = data.get("verdict")
    if verdict not in VALID_VERDICTS:
        return "BLOCKED", ["Verdict JSON did not contain a valid verdict."], "critical"
    findings = [str(item) for item in data.get("findings", []) if item]
    severity = str(data.get("severity", "none"))
    return verdict, findings, severity


def _ci_green(ci_status: str) -> bool:
    return ci_status.upper() in {"SUCCESS", "GREEN", "PASSED", "PASS", "OK"} or ci_status.lower() in {
        "success",
        "green",
        "passed",
        "pass",
        "ok",
    }


def _env_flag(env: Mapping[str, str], name: str) -> bool:
    return env.get(name, "").lower() in {"1", "true", "yes", "on"}


def _red_scope_authorized(env: Mapping[str, str], policy: Mapping[str, Any], phase_id: str) -> bool:
    if not _env_flag(env, "FRONTIER_RED_AUTHORIZED"):
        return False
    scope = env.get("FRONTIER_RED_SCOPE") or env.get("PROJECT_OP_SCOPE") or ""
    if not bool(_nested(policy, "merge_policy", "require_operation_scope_match", default=False)):
        return True
    allowed_scopes = policy.get("authorized_scopes")
    if isinstance(allowed_scopes, list) and allowed_scopes:
        return any(str(item) in scope for item in allowed_scopes)
    return phase_id in scope or scope == "*"


def evaluate_merge_gate(
    *,
    campaign_id: str,
    phase_id: str,
    lane: str,
    verdict: str,
    ci_status: str,
    changed_files: list[str] | None = None,
    artifact_policy: Mapping[str, Any] | None = None,
    config: Mapping[str, Any] | None = None,
    env: Mapping[str, str] | None = None,
    dry_run: bool = True,
    branch_protection: BranchProtectionResult | Mapping[str, Any] | None = None,
    critical_findings: list[str] | None = None,
    stop_requested: bool = False,
) -> MergeGateResult:
    changed_files = changed_files or []
    config = config or load_config(ROOT / "frontier.yaml")
    env = env or os.environ
    lane_key = lane.lower()
    policy = _lane_policy(config, lane_key)
    reasons: list[str] = []
    critical = critical_findings or []

    merge_policy = policy.get("merge_policy") if isinstance(policy.get("merge_policy"), Mapping) else {}
    allow_warnings = bool(merge_policy.get("allow_pass_with_warnings", True))
    block_on_critical = bool(merge_policy.get("block_on_critical", True))
    auto_pr_allowed = bool(policy.get("auto_pr", False)) and bool(_nested(config, "workflow2", "auto_pr", default=True))
    auto_merge_configured = bool(policy.get("auto_merge", False))
    if lane_key == "red":
        auto_merge_configured = bool(policy.get("auto_merge", False) or policy.get("can_auto_merge_when_authorized", False))

    if verdict not in PASSING:
        reasons.append(f"Verdict is {verdict}.")
    if verdict == "PASS_WITH_WARNINGS" and not allow_warnings:
        reasons.append("Lane policy does not allow PASS_WITH_WARNINGS.")
    if not _ci_green(ci_status):
        reasons.append(f"CI status is {ci_status}.")
    if stop_requested:
        reasons.append("STOP was requested.")
    if block_on_critical and critical:
        reasons.append("Critical findings are present.")
    max_changed = policy.get("max_changed_files")
    if max_changed is not None and len(changed_files) > int(max_changed):
        reasons.append(f"Changed files exceed lane limit: {len(changed_files)} > {max_changed}.")

    artifact_ok = True if artifact_policy is None else bool(artifact_policy.get("ok", True))
    if not artifact_ok:
        reasons.append("Artifact policy failed.")

    bp_status: str | None = None
    if branch_protection is not None:
        if isinstance(branch_protection, BranchProtectionResult):
            bp_status = branch_protection.status
            bp_ok = branch_protection.ok or (dry_run and branch_protection.status == "DRY_RUN")
        else:
            bp_status = str(branch_protection.get("status", "UNKNOWN"))
            bp_ok = bp_status in {"PASS", "DRY_RUN"} and (not branch_protection.get("missing_required_checks"))
        if not bp_ok:
            reasons.append(f"Branch protection status is {bp_status}.")

    github_config = config.get("github") if isinstance(config.get("github"), Mapping) else {}
    if not dry_run and bool(github_config.get("require_branch_protection", True)) and branch_protection is None:
        reasons.append("Branch protection validation did not run.")

    if lane_key == "red" and not _red_scope_authorized(env, policy, phase_id):
        reasons.append("Red lane requires FRONTIER_RED_AUTHORIZED=1 and matching scope.")
    if _env_flag(env, "FRONTIER_DISABLE_AUTOMERGE"):
        reasons.append("FRONTIER_DISABLE_AUTOMERGE=1 is set.")
    if _env_flag(env, "FRONTIER_MERGE_DRY_RUN"):
        dry_run = True
    if not auto_merge_configured:
        reasons.append("Lane policy does not enable auto_merge.")

    status = "BLOCKED" if reasons else verdict
    merge_method = str(_nested(config, "github", "merge_method", default="squash"))
    merge_command = ["gh", "pr", "merge", "<number>", f"--{merge_method}", "--delete-branch"]
    merge_allowed = status in PASSING and auto_merge_configured and not dry_run
    if status in PASSING and dry_run:
        reasons.append("Dry-run mode prevented real merge.")

    return MergeGateResult(
        status=status,
        merge_allowed=merge_allowed,
        reasons=reasons,
        campaign_id=campaign_id,
        phase_id=phase_id,
        lane=lane_key,
        ci_status=ci_status,
        verdict=verdict,
        dry_run=dry_run or not merge_allowed,
        auto_pr_allowed=auto_pr_allowed,
        auto_merge_configured=auto_merge_configured,
        merge_method=merge_method,
        merge_command=merge_command,
        branch_protection_status=bp_status,
        critical_findings=critical,
    )


def write_merge_gate_artifacts(run_dir: Path, result: MergeGateResult) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    data = result.to_dict()
    (run_dir / "merge_gate.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Merge Gate",
        "",
        f"Campaign: {result.campaign_id}",
        f"Phase: {result.phase_id}",
        f"Lane: {result.lane}",
        f"Status: {result.status}",
        f"Auto PR allowed: {str(result.auto_pr_allowed).lower()}",
        f"Auto merge configured: {str(result.auto_merge_configured).lower()}",
        f"Merge allowed: {str(result.merge_allowed).lower()}",
        f"Dry run: {str(result.dry_run).lower()}",
        "",
        "## Reasons",
        "",
    ]
    lines.extend(f"- {reason}" for reason in result.reasons)
    if not result.reasons:
        lines.append("- No blocking reasons.")
    text = "\n".join(lines) + "\n"
    (run_dir / "merge_gate.md").write_text(text, encoding="utf-8")
    (run_dir / "dry_run_summary.md").write_text(text, encoding="utf-8")


def perform_merge(
    *,
    pr_number: str | int,
    gate: MergeGateResult,
    root: Path = ROOT,
    runner: Any = None,
) -> GitHubResult:
    return merge_pr(
        pr_number,
        method=gate.merge_method,
        root=root,
        dry_run=not gate.merge_allowed,
        runner=runner,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate Frontier merge policy.")
    parser.add_argument("--campaign-id", default="UNKNOWN")
    parser.add_argument("--phase-id", "--phase", dest="phase_id", default="current")
    parser.add_argument("--lane", default="green")
    parser.add_argument("--verdict-json", type=Path)
    parser.add_argument("--ci-status", default="SUCCESS")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--apply", action="store_true", help="Allow real merge when config/lane/CI/verdict pass.")
    parser.add_argument("--dry-run", action="store_true", help="Force dry-run output.")
    args = parser.parse_args(argv)

    verdict, findings, severity = _verdict_from_file(args.verdict_json)
    critical = findings if severity == "critical" else []
    result = evaluate_merge_gate(
        campaign_id=args.campaign_id,
        phase_id=args.phase_id,
        lane=args.lane,
        verdict=verdict,
        ci_status=args.ci_status,
        dry_run=args.dry_run or not args.apply,
        critical_findings=critical,
    )
    if args.run_dir:
        write_merge_gate_artifacts(args.run_dir, result)
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0 if result.status in PASSING else 1


if __name__ == "__main__":
    raise SystemExit(main())
