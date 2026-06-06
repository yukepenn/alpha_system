"""Immutable study-run outcome record contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, cast

from alpha_system.governance.serialization import JsonValue
from alpha_system.governance.serialization import content_hash as governance_content_hash
from alpha_system.runtime.contracts.artifacts import RuntimeArtifactEntry, RuntimeArtifactManifest
from alpha_system.runtime.contracts.manifest import StudyRunManifest
from alpha_system.runtime.contracts.run_spec import RuntimeLifecycleState, StudyRunSpec
from alpha_system.runtime.entry_contract import RuntimeEntryReason

STUDY_RUN_RECORD_SCHEMA = "alpha_system.runtime.study_run_record.v1"
STUDY_RUN_RECORD_ID_PREFIX = "srecord"


class StudyRunRecordContractError(ValueError):
    """Raised when a study-run record would hide an invalid outcome."""


class StudyRunResultState(StrEnum):
    """Legal runtime result states for descriptive StudyRunRecord objects."""

    RUNTIME_REQUESTED = RuntimeLifecycleState.RUNTIME_REQUESTED.value
    INPUTS_RESOLVED = RuntimeLifecycleState.INPUTS_RESOLVED.value
    PLAN_VALIDATED = RuntimeLifecycleState.PLAN_VALIDATED.value
    DIAGNOSTICS_READY = "DIAGNOSTICS_READY"
    DIAGNOSTICS_RUNNING = "DIAGNOSTICS_RUNNING"
    DIAGNOSTICS_COMPLETE = "DIAGNOSTICS_COMPLETE"
    DIAGNOSTICS_FAILED = "DIAGNOSTICS_FAILED"
    SIGNAL_PROBE_READY = "SIGNAL_PROBE_READY"
    SIGNAL_PROBE_COMPLETE = "SIGNAL_PROBE_COMPLETE"
    COST_STRESS_COMPLETE = "COST_STRESS_COMPLETE"
    EVIDENCE_DRAFT_READY = "EVIDENCE_DRAFT_READY"
    REFERENCE_HANDOFF_READY = "REFERENCE_HANDOFF_READY"
    REJECTED = "REJECTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    BLOCKED = "BLOCKED"


TERMINAL_FAILURE_STATES: frozenset[StudyRunResultState] = frozenset(
    {
        StudyRunResultState.REJECTED,
        StudyRunResultState.INCONCLUSIVE,
        StudyRunResultState.BLOCKED,
    }
)


@dataclass(frozen=True, slots=True)
class StudyRunSpecRef:
    """Reference to a bound StudyRunSpec without copying its payload."""

    study_run_spec_id: str
    content_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "study_run_spec_id",
            _required_string(self.study_run_spec_id, field="study_run_spec_id"),
        )
        object.__setattr__(
            self,
            "content_hash",
            _required_string(self.content_hash, field="content_hash"),
        )

    def to_dict(self) -> dict[str, str]:
        """Return a stable run-spec reference."""

        return {
            "study_run_spec_id": self.study_run_spec_id,
            "content_hash": self.content_hash,
        }


@dataclass(frozen=True, slots=True)
class RunRejectionReason:
    """Visible reason carried by rejected, inconclusive, or blocked run records."""

    code: str
    message: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "code", _required_string(self.code, field="code"))
        object.__setattr__(self, "message", _required_string(self.message, field="message"))

    def to_dict(self) -> dict[str, str]:
        """Return a stable reason payload."""

        return {
            "code": self.code,
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class RuntimeArtifactRef:
    """Reference into a RuntimeArtifactManifest entry."""

    artifact_id: str
    location: str
    content_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "artifact_id",
            _required_string(self.artifact_id, field="artifact_id"),
        )
        object.__setattr__(self, "location", _required_string(self.location, field="location"))
        object.__setattr__(
            self,
            "content_hash",
            _required_string(self.content_hash, field="content_hash"),
        )

    def to_dict(self) -> dict[str, str]:
        """Return a stable artifact reference."""

        return {
            "artifact_id": self.artifact_id,
            "location": self.location,
            "content_hash": self.content_hash,
        }


@dataclass(frozen=True, slots=True)
class ManifestRef:
    """Reference to the run reproducibility manifest."""

    manifest_id: str
    manifest_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "manifest_id",
            _required_string(self.manifest_id, field="manifest_id"),
        )
        object.__setattr__(
            self,
            "manifest_hash",
            _required_string(self.manifest_hash, field="manifest_hash"),
        )

    def to_dict(self) -> dict[str, str]:
        """Return a stable manifest reference."""

        return {
            "manifest_id": self.manifest_id,
            "manifest_hash": self.manifest_hash,
        }


@dataclass(frozen=True, slots=True, init=False)
class StudyRunRecord:
    """Durable, reference-only outcome record for a bounded runtime run."""

    record_id: str
    run_id: str
    study_run_spec_ref: StudyRunSpecRef
    result_state: StudyRunResultState
    rejection_reasons: tuple[RunRejectionReason, ...]
    artifact_refs: tuple[RuntimeArtifactRef, ...]
    manifest_ref: ManifestRef
    record_hash: str

    def __init__(
        self,
        *,
        run_id: str,
        study_run_spec_ref: StudyRunSpec | StudyRunSpecRef | Mapping[str, Any],
        result_state: StudyRunResultState | RuntimeLifecycleState | str,
        manifest_ref: StudyRunManifest | ManifestRef | Mapping[str, Any],
        rejection_reasons: Sequence[
            RunRejectionReason | RuntimeEntryReason | Mapping[str, Any]
        ] = (),
        artifact_refs: Sequence[
            RuntimeArtifactRef | RuntimeArtifactEntry | RuntimeArtifactManifest | Mapping[str, Any]
        ] = (),
    ) -> None:
        normalized_run_id = _required_string(run_id, field="run_id")
        normalized_spec_ref = _coerce_study_run_spec_ref(study_run_spec_ref)
        normalized_state = _coerce_result_state(result_state)
        normalized_reasons = tuple(_coerce_rejection_reason(reason) for reason in rejection_reasons)
        normalized_artifacts = tuple(
            artifact for ref in artifact_refs for artifact in _coerce_artifact_refs(ref)
        )
        normalized_manifest_ref = _coerce_manifest_ref(manifest_ref)

        if normalized_state in TERMINAL_FAILURE_STATES and not normalized_reasons:
            raise StudyRunRecordContractError(
                "terminal failure states require at least one visible rejection reason"
            )

        payload = _record_hash_payload(
            run_id=normalized_run_id,
            study_run_spec_ref=normalized_spec_ref,
            result_state=normalized_state,
            rejection_reasons=normalized_reasons,
            artifact_refs=normalized_artifacts,
            manifest_ref=normalized_manifest_ref,
        )
        digest = governance_content_hash(cast(JsonValue, payload))

        object.__setattr__(self, "record_id", f"{STUDY_RUN_RECORD_ID_PREFIX}_{digest[:24]}")
        object.__setattr__(self, "run_id", normalized_run_id)
        object.__setattr__(self, "study_run_spec_ref", normalized_spec_ref)
        object.__setattr__(self, "result_state", normalized_state)
        object.__setattr__(self, "rejection_reasons", normalized_reasons)
        object.__setattr__(self, "artifact_refs", normalized_artifacts)
        object.__setattr__(self, "manifest_ref", normalized_manifest_ref)
        object.__setattr__(self, "record_hash", digest)

    def to_dict(self) -> dict[str, object]:
        """Return a stable, value-free run outcome record."""

        return {
            "schema": STUDY_RUN_RECORD_SCHEMA,
            "record_id": self.record_id,
            "run_id": self.run_id,
            "study_run_spec_ref": self.study_run_spec_ref.to_dict(),
            "result_state": self.result_state.value,
            "rejection_reasons": [reason.to_dict() for reason in self.rejection_reasons],
            "artifact_refs": [artifact.to_dict() for artifact in self.artifact_refs],
            "manifest_ref": self.manifest_ref.to_dict(),
            "record_hash": self.record_hash,
            "value_free": True,
        }


def _record_hash_payload(
    *,
    run_id: str,
    study_run_spec_ref: StudyRunSpecRef,
    result_state: StudyRunResultState,
    rejection_reasons: tuple[RunRejectionReason, ...],
    artifact_refs: tuple[RuntimeArtifactRef, ...],
    manifest_ref: ManifestRef,
) -> dict[str, object]:
    return {
        "schema": STUDY_RUN_RECORD_SCHEMA,
        "run_id": run_id,
        "study_run_spec_ref": study_run_spec_ref.to_dict(),
        "result_state": result_state.value,
        "rejection_reasons": [reason.to_dict() for reason in rejection_reasons],
        "artifact_refs": [artifact.to_dict() for artifact in artifact_refs],
        "manifest_ref": manifest_ref.to_dict(),
    }


def _coerce_result_state(
    value: StudyRunResultState | RuntimeLifecycleState | str,
) -> StudyRunResultState:
    if isinstance(value, StudyRunResultState):
        return value
    if isinstance(value, RuntimeLifecycleState):
        return StudyRunResultState(value.value)
    if isinstance(value, str):
        return StudyRunResultState(value)
    raise StudyRunRecordContractError(f"unsupported result_state type: {type(value).__name__}")


def _coerce_study_run_spec_ref(
    value: StudyRunSpec | StudyRunSpecRef | Mapping[str, Any],
) -> StudyRunSpecRef:
    if isinstance(value, StudyRunSpecRef):
        return value
    if isinstance(value, StudyRunSpec):
        return StudyRunSpecRef(
            study_run_spec_id=value.study_run_spec_id,
            content_hash=value.content_hash,
        )
    if not isinstance(value, Mapping):
        raise StudyRunRecordContractError(
            f"study_run_spec_ref must be a reference mapping, got {type(value).__name__}"
        )
    _reject_extra_keys(
        value,
        allowed={"study_run_spec_id", "content_hash"},
        field="study_run_spec_ref",
    )
    return StudyRunSpecRef(
        study_run_spec_id=value.get("study_run_spec_id"),
        content_hash=value.get("content_hash"),
    )


def _coerce_rejection_reason(
    value: RunRejectionReason | RuntimeEntryReason | Mapping[str, Any],
) -> RunRejectionReason:
    if isinstance(value, RunRejectionReason):
        return value
    if isinstance(value, RuntimeEntryReason):
        return RunRejectionReason(code=value.code, message=value.message)
    if not isinstance(value, Mapping):
        raise StudyRunRecordContractError(
            f"rejection reason must be a reference mapping, got {type(value).__name__}"
        )
    _reject_extra_keys(value, allowed={"code", "message"}, field="rejection_reasons")
    return RunRejectionReason(
        code=value.get("code"),
        message=value.get("message"),
    )


def _coerce_artifact_refs(
    value: RuntimeArtifactRef | RuntimeArtifactEntry | RuntimeArtifactManifest | Mapping[str, Any],
) -> tuple[RuntimeArtifactRef, ...]:
    if isinstance(value, RuntimeArtifactRef):
        return (value,)
    if isinstance(value, RuntimeArtifactEntry):
        return (
            RuntimeArtifactRef(
                artifact_id=value.artifact_id,
                location=value.location,
                content_hash=value.content_hash,
            ),
        )
    if isinstance(value, RuntimeArtifactManifest):
        return tuple(
            RuntimeArtifactRef(
                artifact_id=entry.artifact_id,
                location=entry.location,
                content_hash=entry.content_hash,
            )
            for entry in value.entries
        )
    if not isinstance(value, Mapping):
        raise StudyRunRecordContractError(
            f"artifact ref must be a reference mapping, got {type(value).__name__}"
        )
    _reject_extra_keys(
        value, allowed={"artifact_id", "location", "content_hash"}, field="artifact_refs"
    )
    return (
        RuntimeArtifactRef(
            artifact_id=value.get("artifact_id"),
            location=value.get("location"),
            content_hash=value.get("content_hash"),
        ),
    )


def _coerce_manifest_ref(value: StudyRunManifest | ManifestRef | Mapping[str, Any]) -> ManifestRef:
    if isinstance(value, ManifestRef):
        return value
    if isinstance(value, StudyRunManifest):
        return ManifestRef(manifest_id=value.manifest_id, manifest_hash=value.manifest_hash)
    if not isinstance(value, Mapping):
        raise StudyRunRecordContractError(
            f"manifest_ref must be a reference mapping, got {type(value).__name__}"
        )
    _reject_extra_keys(value, allowed={"manifest_id", "manifest_hash"}, field="manifest_ref")
    return ManifestRef(
        manifest_id=value.get("manifest_id"),
        manifest_hash=value.get("manifest_hash"),
    )


def _reject_extra_keys(value: Mapping[str, Any], *, allowed: set[str], field: str) -> None:
    extra = set(value) - allowed
    if extra:
        raise StudyRunRecordContractError(
            f"{field} contains non-reference fields: {', '.join(sorted(extra))}"
        )


def _required_string(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StudyRunRecordContractError(f"{field} is required")
    return value.strip()


__all__ = [
    "ManifestRef",
    "RunRejectionReason",
    "RuntimeArtifactRef",
    "StudyRunRecord",
    "StudyRunRecordContractError",
    "StudyRunResultState",
    "StudyRunSpecRef",
    "TERMINAL_FAILURE_STATES",
]
