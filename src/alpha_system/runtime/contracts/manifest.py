"""Immutable reproducibility manifest contracts for study runs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

from alpha_system.governance.serialization import JsonValue
from alpha_system.governance.serialization import content_hash as governance_content_hash

STUDY_RUN_MANIFEST_SCHEMA = "alpha_system.runtime.study_run_manifest.v1"
STUDY_RUN_MANIFEST_ID_PREFIX = "smanifest"


class StudyRunManifestContractError(ValueError):
    """Raised when a study-run manifest is missing reproducibility lineage."""


@dataclass(frozen=True, slots=True)
class FeaturePackVersionRef:
    """Reference-only feature-pack version lineage."""

    pack_id: str
    content_hash: str
    lineage_ref: str
    available_ts_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "pack_id", _manifest_hash_string(self.pack_id, field="pack_id"))
        object.__setattr__(
            self,
            "content_hash",
            _manifest_hash_string(self.content_hash, field="content_hash"),
        )
        object.__setattr__(
            self,
            "lineage_ref",
            _manifest_hash_string(self.lineage_ref, field="lineage_ref"),
        )
        object.__setattr__(
            self,
            "available_ts_ref",
            _availability_ref(
                self.available_ts_ref, field="available_ts_ref", marker="available_ts"
            ),
        )

    def to_dict(self) -> dict[str, str]:
        """Return a stable reference payload."""

        return {
            "pack_id": self.pack_id,
            "content_hash": self.content_hash,
            "lineage_ref": self.lineage_ref,
            "available_ts_ref": self.available_ts_ref,
        }


@dataclass(frozen=True, slots=True)
class LabelPackVersionRef:
    """Reference-only label-pack version lineage."""

    pack_id: str
    content_hash: str
    lineage_ref: str
    label_available_ts_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "pack_id", _manifest_hash_string(self.pack_id, field="pack_id"))
        object.__setattr__(
            self,
            "content_hash",
            _manifest_hash_string(self.content_hash, field="content_hash"),
        )
        object.__setattr__(
            self,
            "lineage_ref",
            _manifest_hash_string(self.lineage_ref, field="lineage_ref"),
        )
        object.__setattr__(
            self,
            "label_available_ts_ref",
            _availability_ref(
                self.label_available_ts_ref,
                field="label_available_ts_ref",
                marker="label_available_ts",
            ),
        )

    def to_dict(self) -> dict[str, str]:
        """Return a stable reference payload."""

        return {
            "pack_id": self.pack_id,
            "content_hash": self.content_hash,
            "lineage_ref": self.lineage_ref,
            "label_available_ts_ref": self.label_available_ts_ref,
        }


@dataclass(frozen=True, slots=True, init=False)
class StudyRunManifest:
    """Reference-only reproducibility evidence for a study run."""

    manifest_id: str
    run_id: str
    dataset_version_id: str
    dataset_version_hash: str
    dataset_lineage_ref: str
    dataset_admissibility_state: str
    feature_pack_versions: tuple[FeaturePackVersionRef, ...]
    label_pack_versions: tuple[LabelPackVersionRef, ...]
    code_version: str
    code_content_hash: str
    config_version: str
    config_hash: str
    cost_model_version: str | None
    cost_model_hash: str | None
    manifest_hash: str

    def __init__(
        self,
        *,
        run_id: str,
        dataset_version_id: str,
        dataset_version_hash: str,
        dataset_lineage_ref: str,
        dataset_admissibility_state: str,
        feature_pack_versions: Sequence[FeaturePackVersionRef | Mapping[str, Any]],
        label_pack_versions: Sequence[LabelPackVersionRef | Mapping[str, Any]],
        code_version: str,
        code_content_hash: str,
        config_version: str,
        config_hash: str,
        cost_model_version: str | None = None,
        cost_model_hash: str | None = None,
    ) -> None:
        normalized_run_id = _required_string(run_id, field="run_id")
        feature_refs = tuple(_coerce_feature_ref(ref) for ref in feature_pack_versions)
        label_refs = tuple(_coerce_label_ref(ref) for ref in label_pack_versions)
        if not feature_refs:
            raise StudyRunManifestContractError("feature_pack_versions must not be empty")
        if not label_refs:
            raise StudyRunManifestContractError("label_pack_versions must not be empty")

        normalized_cost_version = _optional_manifest_hash_string(
            cost_model_version,
            field="cost_model_version",
        )
        normalized_cost_hash = _optional_manifest_hash_string(
            cost_model_hash,
            field="cost_model_hash",
        )
        if (normalized_cost_version is None) != (normalized_cost_hash is None):
            raise StudyRunManifestContractError(
                "cost_model_version and cost_model_hash must be supplied together"
            )

        fields = {
            "run_id": normalized_run_id,
            "dataset_version_id": _manifest_hash_string(
                dataset_version_id,
                field="dataset_version_id",
            ),
            "dataset_version_hash": _manifest_hash_string(
                dataset_version_hash,
                field="dataset_version_hash",
            ),
            "dataset_lineage_ref": _manifest_hash_string(
                dataset_lineage_ref,
                field="dataset_lineage_ref",
            ),
            "dataset_admissibility_state": _manifest_hash_string(
                dataset_admissibility_state,
                field="dataset_admissibility_state",
            ),
            "code_version": _manifest_hash_string(code_version, field="code_version"),
            "code_content_hash": _manifest_hash_string(
                code_content_hash,
                field="code_content_hash",
            ),
            "config_version": _manifest_hash_string(config_version, field="config_version"),
            "config_hash": _manifest_hash_string(config_hash, field="config_hash"),
        }
        hash_payload = _manifest_hash_payload(
            dataset_version_id=fields["dataset_version_id"],
            dataset_version_hash=fields["dataset_version_hash"],
            dataset_lineage_ref=fields["dataset_lineage_ref"],
            dataset_admissibility_state=fields["dataset_admissibility_state"],
            feature_pack_versions=feature_refs,
            label_pack_versions=label_refs,
            code_version=fields["code_version"],
            code_content_hash=fields["code_content_hash"],
            config_version=fields["config_version"],
            config_hash=fields["config_hash"],
            cost_model_version=normalized_cost_version,
            cost_model_hash=normalized_cost_hash,
        )
        digest = governance_content_hash(cast(JsonValue, hash_payload))

        object.__setattr__(self, "manifest_id", f"{STUDY_RUN_MANIFEST_ID_PREFIX}_{digest[:24]}")
        object.__setattr__(self, "run_id", fields["run_id"])
        object.__setattr__(self, "dataset_version_id", fields["dataset_version_id"])
        object.__setattr__(self, "dataset_version_hash", fields["dataset_version_hash"])
        object.__setattr__(self, "dataset_lineage_ref", fields["dataset_lineage_ref"])
        object.__setattr__(
            self,
            "dataset_admissibility_state",
            fields["dataset_admissibility_state"],
        )
        object.__setattr__(self, "feature_pack_versions", feature_refs)
        object.__setattr__(self, "label_pack_versions", label_refs)
        object.__setattr__(self, "code_version", fields["code_version"])
        object.__setattr__(self, "code_content_hash", fields["code_content_hash"])
        object.__setattr__(self, "config_version", fields["config_version"])
        object.__setattr__(self, "config_hash", fields["config_hash"])
        object.__setattr__(self, "cost_model_version", normalized_cost_version)
        object.__setattr__(self, "cost_model_hash", normalized_cost_hash)
        object.__setattr__(self, "manifest_hash", digest)

    def to_dict(self) -> dict[str, object]:
        """Return stable, reference-only reproducibility evidence."""

        return {
            "schema": STUDY_RUN_MANIFEST_SCHEMA,
            "manifest_id": self.manifest_id,
            "run_id": self.run_id,
            "dataset_version_id": self.dataset_version_id,
            "dataset_version_hash": self.dataset_version_hash,
            "dataset_lineage_ref": self.dataset_lineage_ref,
            "dataset_admissibility_state": self.dataset_admissibility_state,
            "feature_pack_versions": [ref.to_dict() for ref in self.feature_pack_versions],
            "label_pack_versions": [ref.to_dict() for ref in self.label_pack_versions],
            "code_version": self.code_version,
            "code_content_hash": self.code_content_hash,
            "config_version": self.config_version,
            "config_hash": self.config_hash,
            "cost_model_version": self.cost_model_version,
            "cost_model_hash": self.cost_model_hash,
            "manifest_hash": self.manifest_hash,
            "value_free": True,
        }


def _manifest_hash_payload(
    *,
    dataset_version_id: str,
    dataset_version_hash: str,
    dataset_lineage_ref: str,
    dataset_admissibility_state: str,
    feature_pack_versions: tuple[FeaturePackVersionRef, ...],
    label_pack_versions: tuple[LabelPackVersionRef, ...],
    code_version: str,
    code_content_hash: str,
    config_version: str,
    config_hash: str,
    cost_model_version: str | None,
    cost_model_hash: str | None,
) -> dict[str, object]:
    return {
        "schema": STUDY_RUN_MANIFEST_SCHEMA,
        "dataset_version_id": dataset_version_id,
        "dataset_version_hash": dataset_version_hash,
        "dataset_lineage_ref": dataset_lineage_ref,
        "dataset_admissibility_state": dataset_admissibility_state,
        "feature_pack_versions": [ref.to_dict() for ref in feature_pack_versions],
        "label_pack_versions": [ref.to_dict() for ref in label_pack_versions],
        "code_version": code_version,
        "code_content_hash": code_content_hash,
        "config_version": config_version,
        "config_hash": config_hash,
        "cost_model_version": cost_model_version,
        "cost_model_hash": cost_model_hash,
    }


def _coerce_feature_ref(value: FeaturePackVersionRef | Mapping[str, Any]) -> FeaturePackVersionRef:
    if isinstance(value, FeaturePackVersionRef):
        return value
    if not isinstance(value, Mapping):
        raise StudyRunManifestContractError(
            f"feature pack reference must be a mapping, got {type(value).__name__}"
        )
    _reject_extra_keys(
        value,
        allowed={"pack_id", "content_hash", "lineage_ref", "available_ts_ref"},
        field="feature_pack_versions",
    )
    return FeaturePackVersionRef(
        pack_id=value.get("pack_id"),
        content_hash=value.get("content_hash"),
        lineage_ref=value.get("lineage_ref"),
        available_ts_ref=value.get("available_ts_ref"),
    )


def _coerce_label_ref(value: LabelPackVersionRef | Mapping[str, Any]) -> LabelPackVersionRef:
    if isinstance(value, LabelPackVersionRef):
        return value
    if not isinstance(value, Mapping):
        raise StudyRunManifestContractError(
            f"label pack reference must be a mapping, got {type(value).__name__}"
        )
    _reject_extra_keys(
        value,
        allowed={"pack_id", "content_hash", "lineage_ref", "label_available_ts_ref"},
        field="label_pack_versions",
    )
    return LabelPackVersionRef(
        pack_id=value.get("pack_id"),
        content_hash=value.get("content_hash"),
        lineage_ref=value.get("lineage_ref"),
        label_available_ts_ref=value.get("label_available_ts_ref"),
    )


def _reject_extra_keys(value: Mapping[str, Any], *, allowed: set[str], field: str) -> None:
    extra = set(value) - allowed
    if extra:
        raise StudyRunManifestContractError(
            f"{field} contains non-reference fields: {', '.join(sorted(extra))}"
        )


def _availability_ref(value: object, *, field: str, marker: str) -> str:
    text = _manifest_hash_string(value, field=field)
    if marker not in text:
        raise StudyRunManifestContractError(f"{field} must reference {marker} metadata")
    return text


def _required_string(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StudyRunManifestContractError(f"{field} is required")
    return value.strip()


def _manifest_hash_string(value: object, *, field: str) -> str:
    text = _required_string(value, field=field)
    if "runs" in text.replace("\\", "/").split("/"):
        raise StudyRunManifestContractError(f"{field} must not include a runs path")
    return text


def _optional_manifest_hash_string(value: object, *, field: str) -> str | None:
    if value is None:
        return None
    return _manifest_hash_string(value, field=field)


__all__ = [
    "FeaturePackVersionRef",
    "LabelPackVersionRef",
    "StudyRunManifest",
    "StudyRunManifestContractError",
]
