"""Fail-closed runtime entry contract for governed research requests.

This module is the pre-execution boundary only. It validates references and
metadata shape before a later resolver may touch registries, FeatureStore,
LabelStore, or DatasetVersion records.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from alpha_system.governance.ids import (
    GovernanceIdError,
    GovernanceIdKind,
    prefix_for_kind,
    validate_governance_id,
)
from alpha_system.governance.serialization import JsonValue
from alpha_system.governance.study_input_pack import StudyInputPack, validate_study_input_pack
from alpha_system.governance.validation import GovernanceValidationError

ACCEPTED_DATASET_VERSION_LIFECYCLE_STATES: frozenset[str] = frozenset(
    {"VERSIONED", "READY_FOR_RESEARCH"}
)
RAW_PROVIDER_FILE_SUFFIXES: tuple[str, ...] = (
    ".dbn",
    ".zst",
    ".parquet",
    ".arrow",
    ".feather",
)
RAW_PROVIDER_METADATA_KEYS: frozenset[str] = frozenset(
    {
        "external_provider_call",
        "external_provider_call_requested",
        "provider_call",
        "provider_call_requested",
        "provider_source",
        "raw_provider",
        "raw_provider_source",
        "raw_source",
    }
)
LOCKED_TEST_MARKERS: tuple[str, ...] = (
    "locked_test",
    "locked-test",
    "locked test",
)


class RuntimeEntryStatus(StrEnum):
    """Pre-execution decision states produced by the runtime front door."""

    INPUTS_RESOLVED = "INPUTS_RESOLVED"
    INPUTS_BLOCKED = "INPUTS_BLOCKED"
    INPUTS_INCONCLUSIVE = "INPUTS_INCONCLUSIVE"


RuntimeEntryOutcome = RuntimeEntryStatus


@dataclass(frozen=True, slots=True)
class RuntimeEntryReason:
    """RejectionReasonRecord-shaped reason for an entry decision."""

    code: str
    message: str
    field: str
    decision_state: RuntimeEntryStatus
    expected: str
    actual: str

    def to_dict(self) -> dict[str, str]:
        """Return a stable JSON-compatible reason payload."""

        return {
            "code": self.code,
            "message": self.message,
            "field": self.field,
            "decision_state": self.decision_state.value,
            "expected": self.expected,
            "actual": self.actual,
        }


@dataclass(frozen=True, slots=True)
class RuntimeEntryRequest:
    """Reference-only request admitted through the research runtime front door."""

    alpha_spec_ref: str | None
    study_spec_ref: str | None
    study_input_pack: StudyInputPack | Mapping[str, Any] | None
    target_dataset_version_id: str | None
    dataset_scope: Mapping[str, Any] | None
    partition_scope: Mapping[str, Any] | None = None
    expected_dataset_lifecycle_state: str | None = None
    dataset_version_source_family: str | None = None
    requested_dataset_version_source_families: Sequence[str] = ()
    raw_provider_source: str | None = None
    raw_file_path: str | None = None
    external_provider_call_requested: bool = False
    request_metadata: Mapping[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class RuntimeEntryResult:
    """Contract-level admission result with exactly one pre-execution state."""

    status: RuntimeEntryStatus
    reasons: tuple[RuntimeEntryReason, ...]
    alpha_spec_ref: str | None
    study_spec_ref: str | None
    study_input_pack: StudyInputPack | None
    target_dataset_version_id: str | None
    dataset_scope: dict[str, JsonValue] | None

    @property
    def resolved(self) -> bool:
        """Return true only for the admitted pre-execution state."""

        return self.status is RuntimeEntryStatus.INPUTS_RESOLVED

    @property
    def blocked(self) -> bool:
        """Return true only for a fail-closed blocking decision."""

        return self.status is RuntimeEntryStatus.INPUTS_BLOCKED

    @property
    def inconclusive(self) -> bool:
        """Return true only when required metadata is under-determined."""

        return self.status is RuntimeEntryStatus.INPUTS_INCONCLUSIVE

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-compatible result payload."""

        return {
            "status": self.status.value,
            "reasons": [reason.to_dict() for reason in self.reasons],
            "alpha_spec_ref": self.alpha_spec_ref,
            "study_spec_ref": self.study_spec_ref,
            "study_input_pack": (
                None if self.study_input_pack is None else self.study_input_pack.to_dict()
            ),
            "target_dataset_version_id": self.target_dataset_version_id,
            "dataset_scope": self.dataset_scope,
        }


def evaluate_runtime_entry_request(request: RuntimeEntryRequest) -> RuntimeEntryResult:
    """Evaluate a runtime entry request without resolving data or calling providers."""

    if not isinstance(request, RuntimeEntryRequest):
        reason = _reason(
            code="invalid_runtime_entry_request",
            message="runtime entry requires a RuntimeEntryRequest object",
            field="request",
            state=RuntimeEntryStatus.INPUTS_BLOCKED,
            expected="RuntimeEntryRequest",
            actual=type(request).__name__,
        )
        return _result(
            request=None,
            status=RuntimeEntryStatus.INPUTS_BLOCKED,
            reasons=(reason,),
            study_input_pack=None,
            dataset_scope=None,
        )

    blocked_reasons: list[RuntimeEntryReason] = []
    blocked_reasons.extend(_missing_required_reference_reasons(request))
    blocked_reasons.extend(_forbidden_provider_reasons(request))
    blocked_reasons.extend(_invalid_reference_reasons(request))

    study_input_pack, pack_reason = _coerce_study_input_pack(request.study_input_pack)
    if pack_reason is not None:
        blocked_reasons.append(pack_reason)

    dataset_scope = _coerce_dataset_scope(request.dataset_scope)
    if request.dataset_scope is not None and dataset_scope is None:
        blocked_reasons.append(
            _reason(
                code="invalid_dataset_scope",
                message="runtime entry dataset_scope must be an explicit mapping",
                field="dataset_scope",
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="non-empty mapping",
                actual=type(request.dataset_scope).__name__,
            )
        )

    if blocked_reasons:
        return _result(
            request=request,
            status=RuntimeEntryStatus.INPUTS_BLOCKED,
            reasons=tuple(blocked_reasons),
            study_input_pack=study_input_pack,
            dataset_scope=dataset_scope,
        )

    inconclusive_reasons = _inconclusive_reference_reasons(
        request,
        study_input_pack=study_input_pack,
        dataset_scope=dataset_scope,
    )
    if inconclusive_reasons:
        return _result(
            request=request,
            status=RuntimeEntryStatus.INPUTS_INCONCLUSIVE,
            reasons=tuple(inconclusive_reasons),
            study_input_pack=study_input_pack,
            dataset_scope=dataset_scope,
        )

    resolved_reason = _reason(
        code="runtime_entry_references_resolved",
        message=(
            "runtime entry references passed contract-level checks; DatasetVersion "
            "admissibility resolution remains delegated to the RuntimeInputPack resolver"
        ),
        field="request",
        state=RuntimeEntryStatus.INPUTS_RESOLVED,
        expected="governed references only",
        actual="governed references only",
    )
    return _result(
        request=request,
        status=RuntimeEntryStatus.INPUTS_RESOLVED,
        reasons=(resolved_reason,),
        study_input_pack=study_input_pack,
        dataset_scope=dataset_scope,
    )


def _missing_required_reference_reasons(
    request: RuntimeEntryRequest,
) -> list[RuntimeEntryReason]:
    required_fields = (
        ("alpha_spec_ref", request.alpha_spec_ref, "AlphaSpec reference"),
        ("study_spec_ref", request.study_spec_ref, "StudySpec reference"),
        ("study_input_pack", request.study_input_pack, "StudyInputPack"),
        (
            "target_dataset_version_id",
            request.target_dataset_version_id,
            "target accepted DatasetVersion id",
        ),
        ("dataset_scope", request.dataset_scope, "partition/dataset scope"),
    )
    reasons: list[RuntimeEntryReason] = []
    for field, value, expected in required_fields:
        if _is_missing(value):
            reasons.append(
                _reason(
                    code=f"missing_{field}",
                    message=f"runtime entry requires {expected}",
                    field=field,
                    state=RuntimeEntryStatus.INPUTS_BLOCKED,
                    expected=expected,
                    actual=_actual(value),
                )
            )
    return reasons


def _forbidden_provider_reasons(request: RuntimeEntryRequest) -> list[RuntimeEntryReason]:
    reasons: list[RuntimeEntryReason] = []
    if request.external_provider_call_requested:
        reasons.append(
            _reason(
                code="external_provider_call_requested",
                message="runtime entry must not request an external provider call",
                field="external_provider_call_requested",
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="False",
                actual="True",
            )
        )

    if not _is_missing(request.raw_provider_source):
        reasons.append(
            _reason(
                code="raw_provider_source_requested",
                message="runtime entry must not name a raw provider source",
                field="raw_provider_source",
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="accepted DatasetVersion reference",
                actual=str(request.raw_provider_source),
            )
        )

    raw_file = _first_raw_file_reference(request)
    if raw_file is not None:
        field, value = raw_file
        reasons.append(
            _reason(
                code="raw_provider_file_requested",
                message="runtime entry must not name raw provider or heavy data files",
                field=field,
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="accepted DatasetVersion reference",
                actual=value,
            )
        )

    metadata_provider = _first_forbidden_provider_metadata(request.request_metadata)
    if metadata_provider is not None:
        field, value = metadata_provider
        reasons.append(
            _reason(
                code="provider_metadata_requested",
                message="runtime entry metadata must not request provider source access",
                field=field,
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="accepted DatasetVersion reference",
                actual=value,
            )
        )
    return reasons


def _invalid_reference_reasons(request: RuntimeEntryRequest) -> list[RuntimeEntryReason]:
    reasons: list[RuntimeEntryReason] = []
    if not _is_missing(request.alpha_spec_ref):
        reason = _validate_governance_reference(
            request.alpha_spec_ref,
            field="alpha_spec_ref",
            expected_kind=GovernanceIdKind.ALPHA_SPEC,
        )
        if reason is not None:
            reasons.append(reason)

    if not _is_missing(request.study_spec_ref):
        reason = _validate_governance_reference(
            request.study_spec_ref,
            field="study_spec_ref",
            expected_kind=GovernanceIdKind.STUDY_SPEC,
        )
        if reason is not None:
            reasons.append(reason)

    if not _is_missing(request.target_dataset_version_id):
        target_id = request.target_dataset_version_id
        if not isinstance(target_id, str) or not target_id.strip().startswith("dsv_"):
            reasons.append(
                _reason(
                    code="invalid_dataset_version_reference",
                    message="runtime entry requires a DatasetVersion id reference",
                    field="target_dataset_version_id",
                    state=RuntimeEntryStatus.INPUTS_BLOCKED,
                    expected="dsv_ DatasetVersion id",
                    actual=_actual(target_id),
                )
            )

    if not _is_missing(request.expected_dataset_lifecycle_state):
        lifecycle_state = str(request.expected_dataset_lifecycle_state).strip().upper()
        if lifecycle_state not in ACCEPTED_DATASET_VERSION_LIFECYCLE_STATES:
            allowed = ", ".join(sorted(ACCEPTED_DATASET_VERSION_LIFECYCLE_STATES))
            reasons.append(
                _reason(
                    code="inadmissible_dataset_lifecycle_state",
                    message="runtime entry may only admit accepted DatasetVersion states",
                    field="expected_dataset_lifecycle_state",
                    state=RuntimeEntryStatus.INPUTS_BLOCKED,
                    expected=allowed,
                    actual=str(request.expected_dataset_lifecycle_state),
                )
            )

    source_families = _normalized_source_families(request)
    if {"databento", "ibkr"}.issubset(source_families):
        reasons.append(
            _reason(
                code="merged_dataset_version_sources_requested",
                message="Databento and IBKR DatasetVersions must not be merged",
                field="requested_dataset_version_source_families",
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="one DatasetVersion provenance family",
                actual=",".join(sorted(source_families)),
            )
        )
    return reasons


def _inconclusive_reference_reasons(
    request: RuntimeEntryRequest,
    *,
    study_input_pack: StudyInputPack | None,
    dataset_scope: dict[str, JsonValue] | None,
) -> tuple[RuntimeEntryReason, ...]:
    reasons: list[RuntimeEntryReason] = []
    if study_input_pack is not None and request.alpha_spec_ref != study_input_pack.alpha_spec_id:
        reasons.append(
            _reason(
                code="alpha_spec_ref_mismatch",
                message="AlphaSpec reference must match StudyInputPack.alpha_spec_id",
                field="alpha_spec_ref",
                state=RuntimeEntryStatus.INPUTS_INCONCLUSIVE,
                expected=study_input_pack.alpha_spec_id,
                actual=str(request.alpha_spec_ref),
            )
        )

    if study_input_pack is not None and dataset_scope is not None:
        pack_scope = study_input_pack.dataset_scope
        if dataset_scope != pack_scope:
            reasons.append(
                _reason(
                    code="dataset_scope_mismatch",
                    message="runtime entry dataset_scope must match the governance StudyInputPack",
                    field="dataset_scope",
                    state=RuntimeEntryStatus.INPUTS_INCONCLUSIVE,
                    expected=str(pack_scope),
                    actual=str(dataset_scope),
                )
            )

    if _locked_test_without_governance_metadata(request):
        reasons.append(
            _reason(
                code="locked_test_governance_metadata_missing",
                message=(
                    "locked-test partition use requires governance contamination metadata "
                    "before runtime execution"
                ),
                field="partition_scope",
                state=RuntimeEntryStatus.INPUTS_INCONCLUSIVE,
                expected="governance contamination metadata",
                actual="missing",
            )
        )
    return tuple(reasons)


def _coerce_study_input_pack(
    value: StudyInputPack | Mapping[str, Any] | None,
) -> tuple[StudyInputPack | None, RuntimeEntryReason | None]:
    if value is None:
        return None, None
    try:
        if isinstance(value, StudyInputPack):
            return validate_study_input_pack(value.to_dict()), None
        if isinstance(value, Mapping):
            return validate_study_input_pack(value), None
    except GovernanceValidationError as exc:
        issue = exc.issues[0] if exc.issues else None
        code = "invalid_study_input_pack" if issue is None else issue.code
        message = (
            "StudyInputPack failed governance validation" if issue is None else issue.message
        )
        field = "study_input_pack" if issue is None else f"study_input_pack.{issue.field}"
        actual = "invalid" if issue is None else str(issue.actual)
        return None, _reason(
            code=code,
            message=message,
            field=field,
            state=RuntimeEntryStatus.INPUTS_BLOCKED,
            expected="valid governance StudyInputPack",
            actual=actual,
        )
    return None, _reason(
        code="invalid_study_input_pack_type",
        message="StudyInputPack must be the governance object or a mapping payload",
        field="study_input_pack",
        state=RuntimeEntryStatus.INPUTS_BLOCKED,
        expected="StudyInputPack or mapping",
        actual=type(value).__name__,
    )


def _coerce_dataset_scope(value: Mapping[str, Any] | None) -> dict[str, JsonValue] | None:
    if value is None or not isinstance(value, Mapping):
        return None
    return dict(value)


def _validate_governance_reference(
    value: str | None,
    *,
    field: str,
    expected_kind: GovernanceIdKind,
) -> RuntimeEntryReason | None:
    try:
        validate_governance_id(
            value,
            expected_kind=expected_kind,
            expected_prefix=prefix_for_kind(expected_kind),
        )
    except GovernanceIdError as exc:
        return _reason(
            code=exc.issue.code,
            message=exc.issue.message,
            field=field,
            state=RuntimeEntryStatus.INPUTS_BLOCKED,
            expected=expected_kind.value,
            actual=str(exc.issue.value),
        )
    return None


def _first_raw_file_reference(request: RuntimeEntryRequest) -> tuple[str, str] | None:
    values: tuple[tuple[str, object], ...] = (
        ("raw_file_path", request.raw_file_path),
        ("target_dataset_version_id", request.target_dataset_version_id),
        ("dataset_scope", request.dataset_scope),
        ("partition_scope", request.partition_scope),
        ("request_metadata", request.request_metadata),
    )
    for field, value in values:
        found = _find_raw_file_suffix(value, field=field)
        if found is not None:
            return found
    return None


def _find_raw_file_suffix(value: object, *, field: str) -> tuple[str, str] | None:
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized.endswith(RAW_PROVIDER_FILE_SUFFIXES):
            return field, value
        return None
    if isinstance(value, Mapping):
        for key, item in value.items():
            found = _find_raw_file_suffix(item, field=f"{field}.{key}")
            if found is not None:
                return found
    if isinstance(value, Sequence) and not isinstance(value, str):
        for index, item in enumerate(value):
            found = _find_raw_file_suffix(item, field=f"{field}[{index}]")
            if found is not None:
                return found
    return None


def _first_forbidden_provider_metadata(
    metadata: Mapping[str, Any] | None,
) -> tuple[str, str] | None:
    if metadata is None:
        return None
    for key, value in metadata.items():
        normalized_key = _normalize_token(str(key))
        if normalized_key in RAW_PROVIDER_METADATA_KEYS and _truthy_metadata(value):
            return f"request_metadata.{key}", str(value)
        if isinstance(value, Mapping):
            nested = _first_forbidden_provider_metadata(value)
            if nested is not None:
                nested_field, nested_value = nested
                return f"request_metadata.{key}.{nested_field.removeprefix('request_metadata.')}", (
                    nested_value
                )
    return None


def _normalized_source_families(request: RuntimeEntryRequest) -> set[str]:
    sources = set()
    if request.dataset_version_source_family:
        sources.add(_normalize_source_family(request.dataset_version_source_family))
    for source in request.requested_dataset_version_source_families:
        if source:
            sources.add(_normalize_source_family(source))
    return {source for source in sources if source}


def _normalize_source_family(value: str) -> str:
    normalized = _normalize_token(value)
    if normalized in {"interactive_brokers", "ib", "ibkr"}:
        return "ibkr"
    if normalized == "databento":
        return "databento"
    return normalized


def _locked_test_without_governance_metadata(request: RuntimeEntryRequest) -> bool:
    if not _contains_locked_test_marker(request.dataset_scope) and not _contains_locked_test_marker(
        request.partition_scope
    ):
        return False
    return not any(
        _contains_contamination_metadata(value)
        for value in (
            request.dataset_scope,
            request.partition_scope,
            request.request_metadata,
        )
    )


def _contains_locked_test_marker(value: object) -> bool:
    if isinstance(value, str):
        normalized = value.strip().casefold()
        return any(marker in normalized for marker in LOCKED_TEST_MARKERS)
    if isinstance(value, Mapping):
        return any(
            _contains_locked_test_marker(key) or _contains_locked_test_marker(item)
            for key, item in value.items()
        )
    if isinstance(value, Sequence) and not isinstance(value, str):
        return any(_contains_locked_test_marker(item) for item in value)
    return False


def _contains_contamination_metadata(value: object) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized_key = _normalize_token(str(key))
            if "contamination" in normalized_key and not _is_missing(item):
                return True
            if normalized_key == "governance_metadata" and not _is_missing(item):
                return True
            if _contains_contamination_metadata(item):
                return True
    if isinstance(value, Sequence) and not isinstance(value, str):
        return any(_contains_contamination_metadata(item) for item in value)
    return False


def _truthy_metadata(value: object) -> bool:
    if value is False or value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    if isinstance(value, Sequence) and not isinstance(value, str) and not value:
        return False
    if isinstance(value, Mapping) and not value:
        return False
    return True


def _is_missing(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    if isinstance(value, Mapping) and not value:
        return True
    if isinstance(value, Sequence) and not isinstance(value, str) and not value:
        return True
    return False


def _actual(value: object) -> str:
    if value is None:
        return "None"
    if isinstance(value, str) and not value.strip():
        return "blank string"
    if isinstance(value, Mapping) and not value:
        return "empty mapping"
    if isinstance(value, Sequence) and not isinstance(value, str) and not value:
        return "empty sequence"
    return str(value)


def _normalize_token(value: str) -> str:
    return "_".join(value.strip().casefold().replace("-", "_").split())


def _reason(
    *,
    code: str,
    message: str,
    field: str,
    state: RuntimeEntryStatus,
    expected: str,
    actual: str,
) -> RuntimeEntryReason:
    return RuntimeEntryReason(
        code=code,
        message=message,
        field=field,
        decision_state=state,
        expected=expected,
        actual=actual,
    )


def _result(
    *,
    request: RuntimeEntryRequest | None,
    status: RuntimeEntryStatus,
    reasons: tuple[RuntimeEntryReason, ...],
    study_input_pack: StudyInputPack | None,
    dataset_scope: dict[str, JsonValue] | None,
) -> RuntimeEntryResult:
    return RuntimeEntryResult(
        status=status,
        reasons=reasons,
        alpha_spec_ref=None if request is None else request.alpha_spec_ref,
        study_spec_ref=None if request is None else request.study_spec_ref,
        study_input_pack=study_input_pack,
        target_dataset_version_id=None if request is None else request.target_dataset_version_id,
        dataset_scope=dataset_scope,
    )


__all__ = [
    "ACCEPTED_DATASET_VERSION_LIFECYCLE_STATES",
    "RuntimeEntryReason",
    "RuntimeEntryOutcome",
    "RuntimeEntryRequest",
    "RuntimeEntryResult",
    "RuntimeEntryStatus",
    "StudyInputPack",
    "evaluate_runtime_entry_request",
]
