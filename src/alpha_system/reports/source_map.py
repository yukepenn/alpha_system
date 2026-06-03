"""Source-map assembly for review bundles."""

from __future__ import annotations

import csv
import io
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from alpha_system.core.hashing import hash_file
from alpha_system.data.fixture_policy import repository_root_from_module
from alpha_system.data.paths import assert_local_wsl_path


DEFAULT_SOURCE_PATTERNS: tuple[str, ...] = (
    "src/alpha_system/reports/review_bundle.py",
    "src/alpha_system/reports/source_map.py",
    "src/alpha_system/reports/audit_report.py",
    "src/alpha_system/reports/release_report.py",
    "src/alpha_system/reports/bundle_validation.py",
    "src/alpha_system/reports/claim_checks.py",
    "src/alpha_system/cli/report.py",
)
DEFAULT_CONFIG_PATTERNS: tuple[str, ...] = ("configs/reports/review_bundle.yaml",)
DEFAULT_TEST_PATTERNS: tuple[str, ...] = (
    "tests/unit/reports/**/*.py",
    "tests/unit/test_source_map*.py",
    "tests/unit/test_review_bundle*.py",
    "tests/integration/test_report_build_cli_help.py",
    "tests/integration/test_review_bundle*.py",
)


@dataclass(frozen=True, slots=True)
class SourceMapFile:
    """One source-map file entry."""

    path: str
    kind: str
    exists: bool
    content_hash: str = ""
    size_bytes: int | None = None
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return a stable dictionary representation."""
        payload = asdict(self)
        payload["warnings"] = list(self.warnings)
        return payload


@dataclass(frozen=True, slots=True)
class SourceMapArtifactRef:
    """One artifact reference included in a source map."""

    artifact_key: str
    path: str
    exists: bool | None = None
    content_hash: str = ""
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return a stable dictionary representation."""
        payload = asdict(self)
        payload["warnings"] = list(self.warnings)
        return payload


@dataclass(frozen=True, slots=True)
class SourceMap:
    """Deterministic review-bundle source map."""

    run_id: str
    source_root: str
    source_files: tuple[SourceMapFile, ...]
    config_files: tuple[SourceMapFile, ...]
    test_files: tuple[SourceMapFile, ...]
    run_manifest_path: str
    registry_record_reference: str
    artifact_references: tuple[SourceMapArtifactRef, ...]
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return a stable dictionary representation."""
        return {
            "run_id": self.run_id,
            "source_root": self.source_root,
            "source_files": [entry.to_dict() for entry in self.source_files],
            "config_files": [entry.to_dict() for entry in self.config_files],
            "test_files": [entry.to_dict() for entry in self.test_files],
            "run_manifest_path": self.run_manifest_path,
            "registry_record_reference": self.registry_record_reference,
            "artifact_references": [entry.to_dict() for entry in self.artifact_references],
            "warnings": list(self.warnings),
        }


def build_source_map(
    *,
    run_id: str,
    source_root: str | Path | None = None,
    run_manifest_path: str | Path | None = None,
    registry_record_reference: str | None = None,
    artifact_references: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None = None,
    source_files: Sequence[str | Path] | None = None,
    config_files: Sequence[str | Path] | None = None,
    test_files: Sequence[str | Path] | None = None,
    source_patterns: Sequence[str] | None = None,
    config_patterns: Sequence[str] | None = None,
    test_patterns: Sequence[str] | None = None,
) -> SourceMap:
    """Build a deterministic source map from explicit roots and references."""
    active_root = assert_local_wsl_path(source_root or repository_root_from_module())
    source_entries = _file_entries(
        active_root,
        paths=source_files,
        patterns=source_patterns or DEFAULT_SOURCE_PATTERNS,
        kind="source",
    )
    config_entries = _file_entries(
        active_root,
        paths=config_files,
        patterns=config_patterns or DEFAULT_CONFIG_PATTERNS,
        kind="config",
    )
    test_entries = _file_entries(
        active_root,
        paths=test_files,
        patterns=test_patterns or DEFAULT_TEST_PATTERNS,
        kind="test",
    )
    warnings: list[str] = []
    if not source_entries:
        warnings.append("source map contains no source files")
    if not config_entries:
        warnings.append("source map contains no config files")

    return SourceMap(
        run_id=_text(run_id, "run_id"),
        source_root=active_root.as_posix(),
        source_files=source_entries,
        config_files=config_entries,
        test_files=test_entries,
        run_manifest_path=_path_text(run_manifest_path),
        registry_record_reference=registry_record_reference or "not_available",
        artifact_references=_artifact_refs(artifact_references, active_root),
        warnings=tuple(warnings),
    )


def render_source_map_markdown(source_map: SourceMap) -> str:
    """Render the source map as compact Markdown."""
    sections = [
        f"# Source Map: {source_map.run_id}",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| source_root | `{source_map.source_root}` |",
        f"| run_manifest_path | `{source_map.run_manifest_path}` |",
        f"| registry_record_reference | `{source_map.registry_record_reference}` |",
        "",
        "## Source Files",
        _files_table(source_map.source_files),
        "",
        "## Config Files",
        _files_table(source_map.config_files),
        "",
        "## Test Files",
        _files_table(source_map.test_files),
        "",
        "## Artifact References",
        _artifact_table(source_map.artifact_references),
        "",
        "## Warnings",
        _bullets(source_map.warnings),
    ]
    return "\n".join(sections).rstrip() + "\n"


def render_source_map_csv(source_map: SourceMap) -> str:
    """Render the source map as stable section/field/value CSV."""
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(("section", "field", "value"))
    writer.writerow(("metadata", "run_id", source_map.run_id))
    writer.writerow(("metadata", "source_root", source_map.source_root))
    writer.writerow(("metadata", "run_manifest_path", source_map.run_manifest_path))
    writer.writerow(("metadata", "registry_record_reference", source_map.registry_record_reference))
    for section, entries in (
        ("source_files", source_map.source_files),
        ("config_files", source_map.config_files),
        ("test_files", source_map.test_files),
    ):
        for entry in entries:
            writer.writerow((section, entry.path, entry.content_hash))
    for entry in source_map.artifact_references:
        writer.writerow(("artifact_references", entry.artifact_key, entry.path))
    for warning in source_map.warnings:
        writer.writerow(("warnings", "warning", warning))
    return output.getvalue()


def _file_entries(
    root: Path,
    *,
    paths: Sequence[str | Path] | None,
    patterns: Sequence[str],
    kind: str,
) -> tuple[SourceMapFile, ...]:
    discovered: list[str | Path] = []
    if paths is None:
        for pattern in patterns:
            matches = sorted(root.glob(pattern))
            if matches:
                discovered.extend(matches)
            elif not any(char in pattern for char in "*?["):
                discovered.append(root / pattern)
    else:
        discovered.extend(paths)

    normalized: dict[str, Path] = {}
    for item in discovered:
        path = Path(item)
        resolved = path if path.is_absolute() else root / path
        display = _display_path(resolved, root)
        normalized[display] = resolved
    return tuple(_file_entry(path, display, kind) for display, path in sorted(normalized.items()))


def _file_entry(path: Path, display_path: str, kind: str) -> SourceMapFile:
    exists = path.is_file()
    warnings = () if exists else ("file missing at source-map build time",)
    return SourceMapFile(
        path=display_path,
        kind=kind,
        exists=exists,
        content_hash=hash_file(path) if exists else "",
        size_bytes=path.stat().st_size if exists else None,
        warnings=warnings,
    )


def _artifact_refs(
    artifact_references: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None,
    root: Path,
) -> tuple[SourceMapArtifactRef, ...]:
    if artifact_references is None:
        return ()
    refs: list[SourceMapArtifactRef] = []
    if isinstance(artifact_references, Mapping):
        iterable = [
            {"artifact_key": str(key), "path": value}
            for key, value in sorted(artifact_references.items(), key=lambda item: str(item[0]))
        ]
    else:
        iterable = list(artifact_references)
    for item in iterable:
        key = str(item.get("artifact_key") or item.get("key") or item.get("artifact_id") or "")
        path_value = item.get("path") or item.get("artifact_path") or item.get("relative_path") or ""
        path = str(path_value)
        exists: bool | None = None
        content_hash = str(item.get("content_hash") or "")
        if path:
            candidate = Path(path)
            resolved = candidate if candidate.is_absolute() else root / candidate
            exists = resolved.is_file()
            if exists and not content_hash:
                content_hash = hash_file(resolved)
        warnings = tuple(str(value) for value in item.get("warnings", ()) if str(value).strip())
        refs.append(
            SourceMapArtifactRef(
                artifact_key=key or "artifact",
                path=path,
                exists=exists,
                content_hash=content_hash,
                warnings=warnings,
            )
        )
    return tuple(sorted(refs, key=lambda ref: (ref.artifact_key, ref.path)))


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(root.resolve(strict=False)).as_posix()
    except ValueError:
        return path.as_posix()


def _path_text(path: str | Path | None) -> str:
    if path is None:
        return "not_available"
    return Path(path).as_posix()


def _text(value: str, field_name: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    return text


def _files_table(entries: Sequence[SourceMapFile]) -> str:
    if not entries:
        return "None recorded."
    output = ["| path | exists | hash |", "| --- | --- | --- |"]
    for entry in entries:
        digest = entry.content_hash[:16] if entry.content_hash else ""
        output.append(f"| `{entry.path}` | {entry.exists} | `{digest}` |")
    return "\n".join(output)


def _artifact_table(entries: Sequence[SourceMapArtifactRef]) -> str:
    if not entries:
        return "None recorded."
    output = ["| artifact_key | path | exists |", "| --- | --- | --- |"]
    for entry in entries:
        output.append(f"| `{entry.artifact_key}` | `{entry.path}` | {entry.exists} |")
    return "\n".join(output)


def _bullets(values: Sequence[str]) -> str:
    if not values:
        return "None recorded."
    return "\n".join(f"- {value}" for value in values)
