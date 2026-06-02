"""Study diagnostic output models and local-only serialization."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from alpha_system.core.hashing import hash_config
from alpha_system.data.fixture_policy import repository_root_from_module
from alpha_system.data.paths import assert_local_wsl_path


DEFAULT_STUDY_OUTPUT_ROOT = Path("artifacts") / "factor_studies"


class StudyOutputError(ValueError):
    """Raised when study output paths or serialization are invalid."""


@dataclass(frozen=True, slots=True)
class DiagnosticSummary:
    run_id: str
    study_id: str
    factor_id: str
    factor_version: str
    label_id: str
    label_version: str
    data_version: str
    engine_version: str
    sample_size: int
    missing_label_count: int
    missing_factor_count: int
    warnings: tuple[str, ...]
    diagnostics: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["warnings"] = list(self.warnings)
        payload["diagnostics"] = dict(self.diagnostics)
        return payload


@dataclass(frozen=True, slots=True)
class StudyOutputPaths:
    output_dir: str
    summary_path: str
    manifest_path: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class StudyRunResult:
    summary: DiagnosticSummary
    output_paths: StudyOutputPaths
    registry_path: str | None
    registry_written: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary.to_dict(),
            "output_paths": self.output_paths.to_dict(),
            "registry_path": self.registry_path,
            "registry_written": self.registry_written,
        }


def resolve_study_output_dir(output_dir: str | Path | None) -> Path:
    """Resolve a local-only study output directory."""
    candidate = assert_local_wsl_path(output_dir or DEFAULT_STUDY_OUTPUT_ROOT)
    repo_root = repository_root_from_module()
    if _is_relative_to(candidate, repo_root):
        allowed = repo_root / DEFAULT_STUDY_OUTPUT_ROOT
        if not _is_relative_to(candidate, allowed):
            msg = "study outputs inside the repo must stay under artifacts/factor_studies"
            raise StudyOutputError(msg)
    return candidate


def resolve_study_manifest_path(manifest_path: str | Path | None, output_dir: Path) -> Path:
    """Resolve the manifest path using the study output path policy."""
    if manifest_path is None:
        return output_dir / "run_manifest.json"
    candidate = assert_local_wsl_path(manifest_path)
    repo_root = repository_root_from_module()
    if _is_relative_to(candidate, repo_root):
        allowed = repo_root / DEFAULT_STUDY_OUTPUT_ROOT
        if not _is_relative_to(candidate, allowed):
            msg = "study manifests inside the repo must stay under artifacts/factor_studies"
            raise StudyOutputError(msg)
    return candidate


def write_study_outputs(
    summary: DiagnosticSummary,
    *,
    output_dir: str | Path | None,
    manifest_path: str | Path | None,
    config_hash: str,
    config_payload: Mapping[str, Any],
) -> StudyOutputPaths:
    """Write a compact diagnostic summary and run manifest."""
    root = resolve_study_output_dir(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    summary_path = root / "diagnostic_summary.json"
    manifest = _manifest_payload(
        summary=summary,
        config_hash=config_hash,
        config_payload=config_payload,
        summary_path=summary_path,
    )
    active_manifest_path = resolve_study_manifest_path(manifest_path, root)
    active_manifest_path.parent.mkdir(parents=True, exist_ok=True)

    summary_path.write_text(
        json.dumps(summary.to_dict(), sort_keys=True, indent=2),
        encoding="utf-8",
    )
    active_manifest_path.write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )
    return StudyOutputPaths(
        output_dir=root.as_posix(),
        summary_path=summary_path.as_posix(),
        manifest_path=active_manifest_path.as_posix(),
    )


def _manifest_payload(
    *,
    summary: DiagnosticSummary,
    config_hash: str,
    config_payload: Mapping[str, Any],
    summary_path: Path,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "run_id": summary.run_id,
        "study_id": summary.study_id,
        "engine_version": summary.engine_version,
        "data_version": summary.data_version,
        "factor_versions": {summary.factor_id: summary.factor_version},
        "label_versions": {summary.label_id: summary.label_version},
        "config_hash": config_hash,
        "parameters": dict(config_payload),
        "artifact_paths": {"diagnostic_summary": summary_path.as_posix()},
        "warnings": list(summary.warnings),
        "status_message": "Tier 0 research diagnostics only; not strategy PnL truth.",
    }
    payload["manifest_hash"] = hash_config(
        {key: value for key, value in payload.items() if key != "manifest_hash"}
    )
    return payload


def no_forbidden_claims(payload: Mapping[str, Any] | Sequence[Any] | str) -> bool:
    """Return whether text avoids unsupported positive claim phrases."""
    text = json.dumps(payload, sort_keys=True).lower() if not isinstance(payload, str) else payload.lower()
    forbidden = (
        "tradable",
        "profitable",
        "production-ready",
        "robust alpha",
        "approved",
    )
    return not any(phrase in text for phrase in forbidden)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True
