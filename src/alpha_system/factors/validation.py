"""FactorSpec structural, hash, lifecycle, and registry validation."""

from __future__ import annotations

import json
import sys
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from alpha_system.core.enums import FactorStatus
from alpha_system.core.hashing import hash_code_paths
from alpha_system.core.registry import is_local_only_registry_path
from alpha_system.data.fixture_policy import (
    FixturePolicyError,
    assert_generated_output_allowed,
    assert_registry_path_allowed,
)
from alpha_system.factors.dependency_spec import (
    FactorDependencyError,
    validate_declared_dependencies,
)
from alpha_system.factors.lifecycle import (
    requires_recorded_validation_review,
    requires_review_backed_promotion,
)
from alpha_system.factors.registry import (
    FactorRegistryError,
    has_review_backed_promotion,
    has_reviewed_validation,
    register_factor_spec,
)
from alpha_system.factors.spec import (
    FactorSpec,
    FactorSpecError,
    compute_factor_config_hash,
)


VALIDATION_FAILURE_EXIT_CODE = 1
CONFIG_ERROR_EXIT_CODE = 2
DEFAULT_FACTOR_REGISTRY_PATH = Path("/tmp/alpha_system/factor_registry.sqlite3")


class FactorValidationConfigError(RuntimeError):
    """Raised for deterministic CLI configuration or artifact-policy errors."""


@dataclass(frozen=True, slots=True)
class FactorValidationIssue:
    code: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


@dataclass(frozen=True, slots=True)
class FactorValidationSummary:
    factor_id: str | None
    version: str | None
    status: str | None
    valid: bool
    issue_counts: Mapping[str, int]
    issues: tuple[FactorValidationIssue, ...] = field(default_factory=tuple)
    code_hash: str | None = None
    computed_code_hash: str | None = None
    config_hash: str | None = None
    computed_config_hash: str | None = None
    registry_path: str | None = None
    registry_written: bool = False
    validation_summary_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code_hash": self.code_hash,
            "computed_code_hash": self.computed_code_hash,
            "computed_config_hash": self.computed_config_hash,
            "config_hash": self.config_hash,
            "factor_id": self.factor_id,
            "issue_counts": dict(self.issue_counts),
            "issues": [issue.to_dict() for issue in self.issues],
            "registry_path": self.registry_path,
            "registry_written": self.registry_written,
            "status": self.status,
            "valid": self.valid,
            "validation_summary_path": self.validation_summary_path,
            "version": self.version,
        }


def load_factor_spec_config(path: str | Path) -> dict[str, Any]:
    """Load a JSON FactorSpec config without adding external dependencies."""
    config_path = Path(path)
    if not config_path.exists():
        msg = f"factor spec config does not exist: {config_path.as_posix()}"
        raise FactorValidationConfigError(msg)
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        msg = f"factor spec config must be JSON for this phase: {config_path.as_posix()}"
        raise FactorValidationConfigError(msg) from exc
    if not isinstance(payload, Mapping):
        msg = f"factor spec config root must be a mapping: {config_path.as_posix()}"
        raise FactorValidationConfigError(msg)
    return dict(payload)


def compute_factor_code_hash(paths: Sequence[str | Path]) -> str:
    """Compute a deterministic code hash for files or directories."""
    files: list[Path] = []
    for item in paths:
        path = Path(item)
        if path.is_dir():
            files.extend(sorted(child for child in path.rglob("*.py") if child.is_file()))
        elif path.is_file():
            files.append(path)
        else:
            msg = f"code path does not exist: {path.as_posix()}"
            raise FactorValidationConfigError(msg)
    if not files:
        msg = "at least one code file is required for code-hash computation"
        raise FactorValidationConfigError(msg)
    return hash_code_paths(files)


def validate_factor_spec_mapping(
    payload: Mapping[str, Any],
    *,
    code_paths: Sequence[str | Path] = (),
    registry_path: str | Path | None = None,
    register: bool = False,
    used_fields: Iterable[str] = (),
) -> FactorValidationSummary:
    """Validate structure, dependencies, hashes, lifecycle gates, and registry state."""
    issues: list[FactorValidationIssue] = []
    computed_config_hash = compute_factor_config_hash(payload)
    computed_code_hash: str | None = None

    try:
        spec = FactorSpec.from_mapping(payload)
    except FactorSpecError as exc:
        issues.append(FactorValidationIssue("spec_invalid", str(exc)))
        return _summary_from_payload(
            payload,
            issues,
            computed_config_hash=computed_config_hash,
            computed_code_hash=computed_code_hash,
            registry_path=registry_path,
        )

    try:
        validate_declared_dependencies(spec.input_fields, used_fields=used_fields)
    except FactorDependencyError as exc:
        issues.append(FactorValidationIssue("dependency_invalid", str(exc)))

    if computed_config_hash != spec.config_hash:
        issues.append(
            FactorValidationIssue(
                "config_hash_mismatch",
                (
                    "config_hash mismatch: "
                    f"expected {spec.config_hash}, computed {computed_config_hash}"
                ),
            )
        )

    if code_paths:
        computed_code_hash = compute_factor_code_hash(code_paths)
        if computed_code_hash != spec.code_hash:
            issues.append(
                FactorValidationIssue(
                    "code_hash_mismatch",
                    (
                        "code_hash mismatch: "
                        f"expected {spec.code_hash}, computed {computed_code_hash}"
                    ),
                )
            )

    active_registry_path = Path(registry_path) if registry_path is not None else None
    if requires_recorded_validation_review(spec.status):
        if active_registry_path is None:
            issues.append(
                FactorValidationIssue(
                    "validation_review_missing",
                    f"{spec.status.value} factors require registry validation review",
                )
            )
        elif not has_reviewed_validation(active_registry_path, spec):
            issues.append(
                FactorValidationIssue(
                    "validation_review_missing",
                    "no reviewed factor_validation_runs entry matched this factor version",
                )
            )

    if requires_review_backed_promotion(spec.status):
        if active_registry_path is None:
            issues.append(
                FactorValidationIssue(
                    "promotion_review_missing",
                    "approved factors require a registry promotion_decisions entry",
                )
            )
        elif not has_review_backed_promotion(active_registry_path, spec):
            issues.append(
                FactorValidationIssue(
                    "promotion_review_missing",
                    "no review-backed promotion decision matched this factor version",
                )
            )

    registry_written = False
    if (
        register
        and active_registry_path is not None
        and spec.status in {FactorStatus.DRAFT, FactorStatus.CANDIDATE}
        and not issues
    ):
        try:
            register_factor_spec(active_registry_path, spec)
        except FactorRegistryError as exc:
            issues.append(FactorValidationIssue("registry_invalid", str(exc)))
        else:
            registry_written = True

    return _summary_from_spec(
        spec,
        issues,
        computed_config_hash=computed_config_hash,
        computed_code_hash=computed_code_hash,
        registry_path=active_registry_path,
        registry_written=registry_written,
    )


def validate_factor_spec_file(
    spec_path: str | Path,
    *,
    code_paths: Sequence[str | Path] = (),
    validation_artifact_path: str | Path | None = None,
    registry_path: str | Path | None = None,
    register: bool = False,
    used_fields: Iterable[str] = (),
) -> FactorValidationSummary:
    """Load and validate a FactorSpec config file."""
    payload = load_factor_spec_config(spec_path)
    if validation_artifact_path is not None:
        payload["validation_artifact_path"] = Path(validation_artifact_path).as_posix()
    return validate_factor_spec_mapping(
        payload,
        code_paths=code_paths,
        registry_path=registry_path,
        register=register,
        used_fields=used_fields,
    )


def run_factor_validate_command(
    *,
    spec_path: str | Path,
    registry_path: str | Path | None = None,
    code_paths: Sequence[str | Path] = (),
    validation_artifact_path: str | Path | None = None,
    summary_out: str | Path | None = None,
    used_fields: Iterable[str] = (),
) -> FactorValidationSummary:
    """Run the CLI validation command and optional temp/local registry write."""
    active_registry_path = (
        Path(registry_path) if registry_path is not None else DEFAULT_FACTOR_REGISTRY_PATH
    )
    if active_registry_path is not None:
        active_registry_path = assert_registry_path_allowed(active_registry_path)
    if active_registry_path is not None and not is_local_only_registry_path(active_registry_path):
        msg = f"{active_registry_path.as_posix()} is not an allowed local registry path"
        raise FactorValidationConfigError(msg)

    summary = validate_factor_spec_file(
        spec_path,
        code_paths=code_paths,
        validation_artifact_path=validation_artifact_path,
        registry_path=active_registry_path,
        register=active_registry_path is not None,
        used_fields=used_fields,
    )
    if summary_out is not None:
        summary = write_validation_summary(summary, summary_out)
    return summary


def write_validation_summary(
    summary: FactorValidationSummary,
    summary_out: str | Path,
) -> FactorValidationSummary:
    """Write a small local-only JSON or Markdown validation summary."""
    output = assert_generated_output_allowed(summary_out)
    output.parent.mkdir(parents=True, exist_ok=True)
    updated = replace(summary, validation_summary_path=output.as_posix())
    if output.suffix.lower() == ".json":
        output.write_text(
            json.dumps(updated.to_dict(), sort_keys=True, indent=2),
            encoding="utf-8",
        )
    elif output.suffix.lower() in {".md", ".markdown"}:
        output.write_text(_summary_markdown(updated), encoding="utf-8")
    else:
        msg = "factor validation summary-out must end in .json or .md"
        raise FactorValidationConfigError(msg)
    return updated


def print_validation_summary(
    summary: FactorValidationSummary,
    *,
    emit_json: bool = False,
) -> None:
    """Emit a stable console summary."""
    if emit_json:
        print(json.dumps(summary.to_dict(), sort_keys=True, indent=2))
        return
    print("Factor command: validate")
    print(f"Factor: {summary.factor_id or 'unknown'}")
    print(f"Version: {summary.version or 'unknown'}")
    print(f"Status: {summary.status or 'unknown'}")
    print(f"Validation: {'OK' if summary.valid else 'INVALID'}")
    if summary.registry_path is not None:
        print(f"Registry: {summary.registry_path}")
        print(f"Registry written: {'yes' if summary.registry_written else 'no'}")
    if summary.validation_summary_path is not None:
        print(f"Summary: {summary.validation_summary_path}")
    if summary.issue_counts:
        print(f"Issues: {dict(summary.issue_counts)}")
    for issue in summary.issues[:10]:
        print(f"- {issue.code}: {issue.message}")


def run_cli_with_error_handling(callback: Any, *, emit_json: bool = False) -> int:
    """Run a factor CLI callback and convert errors into stable exit codes."""
    try:
        summary = callback()
    except (
        FactorValidationConfigError,
        FixturePolicyError,
        FactorRegistryError,
        OSError,
    ) as exc:
        print(f"factor command error: {exc}", file=sys.stderr)
        return CONFIG_ERROR_EXIT_CODE
    print_validation_summary(summary, emit_json=emit_json)
    return 0 if summary.valid else VALIDATION_FAILURE_EXIT_CODE


def _summary_from_spec(
    spec: FactorSpec,
    issues: Sequence[FactorValidationIssue],
    *,
    computed_config_hash: str,
    computed_code_hash: str | None,
    registry_path: str | Path | None,
    registry_written: bool = False,
) -> FactorValidationSummary:
    return FactorValidationSummary(
        factor_id=spec.factor_id,
        version=spec.version,
        status=spec.status.value,
        valid=not issues,
        issue_counts=_issue_counts(issues),
        issues=tuple(issues),
        code_hash=spec.code_hash,
        computed_code_hash=computed_code_hash,
        config_hash=spec.config_hash,
        computed_config_hash=computed_config_hash,
        registry_path=None if registry_path is None else Path(registry_path).as_posix(),
        registry_written=registry_written,
    )


def _summary_from_payload(
    payload: Mapping[str, Any],
    issues: Sequence[FactorValidationIssue],
    *,
    computed_config_hash: str,
    computed_code_hash: str | None,
    registry_path: str | Path | None,
) -> FactorValidationSummary:
    return FactorValidationSummary(
        factor_id=_optional_text(payload.get("factor_id")),
        version=_optional_text(payload.get("version")),
        status=_optional_text(payload.get("status")),
        valid=False,
        issue_counts=_issue_counts(issues),
        issues=tuple(issues),
        code_hash=_optional_text(payload.get("code_hash")),
        computed_code_hash=computed_code_hash,
        config_hash=_optional_text(payload.get("config_hash")),
        computed_config_hash=computed_config_hash,
        registry_path=None if registry_path is None else Path(registry_path).as_posix(),
        registry_written=False,
    )


def _issue_counts(issues: Sequence[FactorValidationIssue]) -> dict[str, int]:
    counts: Counter[str] = Counter(issue.code for issue in issues)
    return dict(counts)


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _summary_markdown(summary: FactorValidationSummary) -> str:
    lines = [
        "# Factor Validation Summary",
        "",
        f"- Factor: `{summary.factor_id or 'unknown'}`",
        f"- Version: `{summary.version or 'unknown'}`",
        f"- Status: `{summary.status or 'unknown'}`",
        f"- Valid: `{'yes' if summary.valid else 'no'}`",
    ]
    if summary.issue_counts:
        lines.append(f"- Issues: `{dict(summary.issue_counts)}`")
    return "\n".join(lines) + "\n"
