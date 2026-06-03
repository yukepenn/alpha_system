"""Structured validation for review-bundle completeness."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any


REQUIRED_SECTIONS: tuple[str, ...] = (
    "run_manifest",
    "source_map",
    "config_hashes",
    "code_hashes",
    "versions",
    "registry_records",
    "warnings",
    "failed_steps",
    "promotion_decision_status",
    "no_lookahead_validation_status",
    "artifact_manifest",
    "known_limitations",
    "review_status",
)
REQUIRED_VERSION_FIELDS: tuple[str, ...] = (
    "data_version",
    "factor_versions",
    "label_versions",
    "engine_version",
)
REQUIRED_HASH_FIELDS: tuple[str, ...] = ("config_hashes", "code_hashes")
REQUIRED_FILE_REFS: tuple[str, ...] = ("run_manifest", "artifact_manifest")


@dataclass(frozen=True, slots=True)
class BundleValidationResult:
    """Structured review-bundle validation result."""

    valid: bool
    present_sections: tuple[str, ...]
    missing_sections: tuple[str, ...]
    present_required_versions: tuple[str, ...]
    missing_required_versions: tuple[str, ...]
    present_required_hashes: tuple[str, ...]
    missing_required_hashes: tuple[str, ...]
    present_required_files: tuple[str, ...]
    missing_required_files: tuple[str, ...]
    missing_artifacts: tuple[dict[str, Any], ...]
    surfaced_failed_runs: tuple[dict[str, Any], ...]
    surfaced_rejected_configs: tuple[dict[str, Any], ...]
    promotion_decision_status: str
    no_lookahead_validation_status: str
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return a stable dictionary representation."""
        payload = asdict(self)
        for key in (
            "present_sections",
            "missing_sections",
            "present_required_versions",
            "missing_required_versions",
            "present_required_hashes",
            "missing_required_hashes",
            "present_required_files",
            "missing_required_files",
            "warnings",
        ):
            payload[key] = list(payload[key])
        payload["missing_artifacts"] = [dict(item) for item in self.missing_artifacts]
        payload["surfaced_failed_runs"] = [dict(item) for item in self.surfaced_failed_runs]
        payload["surfaced_rejected_configs"] = [
            dict(item) for item in self.surfaced_rejected_configs
        ]
        return payload


def validate_bundle_completeness(bundle: Mapping[str, Any] | Any) -> BundleValidationResult:
    """Validate that a review bundle surfaces required governance evidence."""
    payload = _mapping(bundle)
    present_sections = tuple(section for section in REQUIRED_SECTIONS if _present(payload, section))
    missing_sections = tuple(section for section in REQUIRED_SECTIONS if section not in present_sections)

    versions = _mapping(payload.get("versions"))
    present_versions = tuple(
        field for field in REQUIRED_VERSION_FIELDS if _present(versions, field)
    )
    missing_versions = tuple(
        field for field in REQUIRED_VERSION_FIELDS if field not in present_versions
    )

    present_hashes = tuple(
        field for field in REQUIRED_HASH_FIELDS if _present(payload, field)
    )
    missing_hashes = tuple(field for field in REQUIRED_HASH_FIELDS if field not in present_hashes)

    present_files, missing_files = _file_ref_presence(payload)
    missing_artifacts = tuple(_artifact for _artifact in _missing_artifacts(payload))
    failed_runs = tuple(_normalize_dicts(payload.get("failed_runs", ())))
    failed_steps = tuple(_normalize_dicts(payload.get("failed_steps", ())))
    surfaced_failures = failed_runs or failed_steps
    rejected_configs = tuple(_normalize_dicts(payload.get("rejected_configs", ())))
    promotion_status = _status_text(payload.get("promotion_decision_status"))
    no_lookahead_status = _status_text(payload.get("no_lookahead_validation_status"))

    warnings = list(_warning_messages(payload))
    if missing_artifacts and not _warnings_include(warnings, "missing artifact"):
        warnings.append("missing artifacts were detected but not surfaced in warnings")
    if surfaced_failures and not _warnings_include(warnings, "failed"):
        warnings.append("failed runs or failed steps are surfaced for review")
    if rejected_configs and not _warnings_include(warnings, "rejected"):
        warnings.append("rejected configs are surfaced for review")
    if promotion_status in {"", "not_available"}:
        warnings.append("promotion decision status is missing")
    if no_lookahead_status in {"", "not_available"}:
        warnings.append("no-lookahead validation status is missing")

    hard_missing = (
        missing_sections
        or missing_versions
        or missing_hashes
        or missing_files
        or (missing_artifacts and not _warnings_include(warnings, "missing artifact"))
        or promotion_status in {"", "not_available"}
        or no_lookahead_status in {"", "not_available"}
    )
    return BundleValidationResult(
        valid=not hard_missing,
        present_sections=present_sections,
        missing_sections=missing_sections,
        present_required_versions=present_versions,
        missing_required_versions=missing_versions,
        present_required_hashes=present_hashes,
        missing_required_hashes=missing_hashes,
        present_required_files=present_files,
        missing_required_files=missing_files,
        missing_artifacts=missing_artifacts,
        surfaced_failed_runs=surfaced_failures,
        surfaced_rejected_configs=rejected_configs,
        promotion_decision_status=promotion_status or "not_available",
        no_lookahead_validation_status=no_lookahead_status or "not_available",
        warnings=tuple(dict.fromkeys(warnings)),
    )


def _mapping(value: Mapping[str, Any] | Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        value = value.to_dict()
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _present(payload: Mapping[str, Any], key: str) -> bool:
    value = payload.get(key)
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip()) and value.strip() != "not_available"
    if isinstance(value, Mapping | Sequence) and not isinstance(value, bytes | bytearray):
        return bool(value)
    return True


def _file_ref_presence(payload: Mapping[str, Any]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    present: list[str] = []
    missing: list[str] = []
    for field in REQUIRED_FILE_REFS:
        value = payload.get(field)
        if field == "artifact_manifest":
            entries = _artifact_manifest_entries(value)
            if entries:
                present.append(field)
            else:
                missing.append(field)
            continue
        if _path_or_mapping_present(value):
            present.append(field)
        else:
            missing.append(field)
    return tuple(present), tuple(missing)


def _artifact_manifest_entries(value: Any) -> tuple[dict[str, Any], ...]:
    if isinstance(value, Mapping):
        entries = value.get("entries")
        if entries is None and any(key in value for key in ("artifact_path", "path", "relative_path")):
            entries = (value,)
    else:
        entries = value
    return tuple(_normalize_dicts(entries or ()))


def _path_or_mapping_present(value: Any) -> bool:
    if isinstance(value, Mapping):
        if value.get("path") or value.get("run_manifest_path"):
            return True
        return bool(value)
    return bool(str(value or "").strip())


def _missing_artifacts(payload: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    explicit = tuple(_normalize_dicts(payload.get("missing_artifacts", ())))
    if explicit:
        return explicit
    missing: list[dict[str, Any]] = []
    for entry in _artifact_manifest_entries(payload.get("artifact_manifest")):
        exists = entry.get("exists")
        if exists is False:
            missing.append(entry)
        warnings = " ".join(str(item) for item in entry.get("warnings", ())).casefold()
        if "missing" in warnings or "unavailable" in warnings:
            missing.append(entry)
    deduped: dict[str, dict[str, Any]] = {}
    for entry in missing:
        key = str(entry.get("artifact_path") or entry.get("path") or entry.get("relative_path") or entry)
        deduped[key] = entry
    return tuple(deduped[key] for key in sorted(deduped))


def _warning_messages(payload: Mapping[str, Any]) -> tuple[str, ...]:
    messages: list[str] = []
    for warning in payload.get("warnings", ()) or ():
        if isinstance(warning, Mapping):
            messages.append(str(warning.get("message") or warning.get("code") or ""))
        else:
            messages.append(str(warning))
    return tuple(message for message in messages if message.strip())


def _warnings_include(warnings: Sequence[str], needle: str) -> bool:
    lowered = needle.casefold()
    return any(lowered in warning.casefold() for warning in warnings)


def _normalize_dicts(value: Any) -> tuple[dict[str, Any], ...]:
    if value is None:
        return ()
    if isinstance(value, Mapping):
        return (dict(value),)
    if not isinstance(value, Sequence) or isinstance(value, str | bytes | bytearray):
        return ()
    output: list[dict[str, Any]] = []
    for item in value:
        if hasattr(item, "to_dict"):
            item = item.to_dict()
        if isinstance(item, Mapping):
            output.append(dict(item))
    return tuple(output)


def _status_text(value: Any) -> str:
    text = str(value or "").strip()
    return text
