"""EvidenceBundle contract, manifest validation, and evidence-ready gate."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, cast

from alpha_system.governance.canaries.catalog import REQUIRED_NEGATIVE_CONTROL_TYPES
from alpha_system.governance.canaries.negative_control_result import (
    NegativeControlPassFail,
    NegativeControlResult,
    validate_negative_control_result,
)
from alpha_system.governance.ids import (
    GovernanceIdError,
    GovernanceIdKind,
    generate_governance_id,
    validate_governance_id,
)
from alpha_system.governance.serialization import (
    GovernanceSerializationError,
    JsonValue,
    canonical_serialize,
    deserialize,
)
from alpha_system.governance.validation import (
    ExpectedType,
    GovernanceValidationError,
    ValidationIssue,
    require_mapping,
    validate_required_fields,
    validate_schema,
)
from alpha_system.governance.verdict_reason_code import (
    VerdictReasonCode,
    missing_inconclusive_reason_issue,
    validate_optional_verdict_reason_code,
    validate_verdict_reason_code,
)

EVIDENCE_BUNDLE_REQUIRED_FIELDS = (
    "evidence_bundle_id",
    "alpha_spec_id",
    "study_spec_id",
    "trial_ids",
    "data_version",
    "factor_version",
    "label_version",
    "code_hash",
    "config_hash",
    "diagnostics_summary",
    "negative_control_results",
    "limitations",
    "artifact_manifest",
    "reviewer_verdict_reference",
)
EVIDENCE_BUNDLE_OPTIONAL_FIELDS = ("reason_code",)
EVIDENCE_BUNDLE_ALLOWED_FIELDS = EVIDENCE_BUNDLE_REQUIRED_FIELDS + EVIDENCE_BUNDLE_OPTIONAL_FIELDS
EVIDENCE_BUNDLE_ID_COMPONENT_FIELDS = tuple(
    field for field in EVIDENCE_BUNDLE_ALLOWED_FIELDS if field != "evidence_bundle_id"
)
ARTIFACT_MANIFEST_ENTRY_REQUIRED_FIELDS = (
    "logical_name",
    "role",
    "reference",
    "content_hash",
)
EVIDENCE_BUNDLE_FIELD_TYPES: dict[str, ExpectedType] = {
    "evidence_bundle_id": str,
    "alpha_spec_id": str,
    "study_spec_id": str,
    "trial_ids": list,
    "data_version": str,
    "factor_version": str,
    "label_version": str,
    "code_hash": str,
    "config_hash": str,
    "diagnostics_summary": dict,
    "negative_control_results": list,
    "limitations": list,
    "artifact_manifest": list,
    "reviewer_verdict_reference": str,
    "reason_code": (str, VerdictReasonCode),
}
ARTIFACT_MANIFEST_ENTRY_FIELD_TYPES: dict[str, ExpectedType] = {
    "logical_name": str,
    "role": str,
    "reference": str,
    "content_hash": str,
}
DIAGNOSTICS_RUN_STATE = "DIAGNOSTICS_RUN"
EVIDENCE_READY_STATE = "EVIDENCE_READY"
INCONCLUSIVE_DIAGNOSTICS_STATUS = "INCONCLUSIVE"

_SHA256_HEX_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_WINDOWS_ABSOLUTE_PATH_PATTERN = re.compile(r"^[A-Za-z]:[\\/]")
_VAGUE_TEXT = {
    "",
    "-",
    "n/a",
    "na",
    "none",
    "null",
    "tbd",
    "todo",
    "unknown",
    "placeholder",
    "to be defined",
    "to be determined",
}


@dataclass(frozen=True, slots=True)
class EvidenceArtifactManifestEntry:
    """Validated local-only evidence artifact manifest metadata."""

    logical_name: str
    role: str
    reference: str
    content_hash: str

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, Any],
    ) -> EvidenceArtifactManifestEntry:
        """Build a manifest entry after fail-closed validation."""

        return validate_artifact_manifest_entry(payload)

    def to_dict(self) -> dict[str, JsonValue]:
        """Return the canonical manifest-entry representation."""

        return {
            "logical_name": self.logical_name,
            "role": self.role,
            "reference": self.reference,
            "content_hash": self.content_hash,
        }


@dataclass(frozen=True, slots=True)
class EvidenceBundle:
    """Validated evidence package metadata required before evidence-ready status."""

    evidence_bundle_id: str
    alpha_spec_id: str
    study_spec_id: str
    trial_ids: list[str]
    data_version: str
    factor_version: str
    label_version: str
    code_hash: str
    config_hash: str
    diagnostics_summary: dict[str, JsonValue]
    negative_control_results: list[dict[str, JsonValue]]
    limitations: list[str]
    artifact_manifest: list[EvidenceArtifactManifestEntry]
    reviewer_verdict_reference: str
    reason_code: VerdictReasonCode | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> EvidenceBundle:
        """Build an `EvidenceBundle` from a mapping after validation."""

        return validate_evidence_bundle(payload)

    @classmethod
    def from_canonical_json(cls, text: str) -> EvidenceBundle:
        """Deserialize canonical JSON and validate the resulting bundle."""

        value = deserialize(text)
        mapping = require_mapping(value, object_name="EvidenceBundle")
        return validate_evidence_bundle(mapping)

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a strict JSON-compatible representation."""

        payload: dict[str, JsonValue] = {
            "evidence_bundle_id": self.evidence_bundle_id,
            "alpha_spec_id": self.alpha_spec_id,
            "study_spec_id": self.study_spec_id,
            "trial_ids": list(self.trial_ids),
            "data_version": self.data_version,
            "factor_version": self.factor_version,
            "label_version": self.label_version,
            "code_hash": self.code_hash,
            "config_hash": self.config_hash,
            "diagnostics_summary": dict(self.diagnostics_summary),
            "negative_control_results": [dict(result) for result in self.negative_control_results],
            "limitations": list(self.limitations),
            "artifact_manifest": [entry.to_dict() for entry in self.artifact_manifest],
            "reviewer_verdict_reference": self.reviewer_verdict_reference,
        }
        if self.reason_code is not None:
            payload["reason_code"] = self.reason_code.value
        return payload

    def to_canonical_json(self) -> str:
        """Serialize the validated bundle through the canonical primitive."""

        return canonical_serialize(self.to_dict())


def create_evidence_bundle(
    *,
    alpha_spec_id: str,
    study_spec_id: str,
    trial_ids: list[str],
    data_version: str,
    factor_version: str,
    label_version: str,
    code_hash: str,
    config_hash: str,
    diagnostics_summary: dict[str, JsonValue],
    negative_control_results: list[Mapping[str, JsonValue]],
    limitations: list[str],
    artifact_manifest: list[EvidenceArtifactManifestEntry | Mapping[str, JsonValue]],
    reviewer_verdict_reference: str,
    reason_code: VerdictReasonCode | str | None = None,
) -> EvidenceBundle:
    """Create a validated `EvidenceBundle` without materializing artifacts."""

    payload: dict[str, JsonValue] = {
        "alpha_spec_id": alpha_spec_id,
        "study_spec_id": study_spec_id,
        "trial_ids": list(trial_ids),
        "data_version": data_version,
        "factor_version": factor_version,
        "label_version": label_version,
        "code_hash": code_hash,
        "config_hash": config_hash,
        "diagnostics_summary": dict(diagnostics_summary),
        "negative_control_results": [dict(result) for result in negative_control_results],
        "limitations": list(limitations),
        "artifact_manifest": [_manifest_entry_to_dict(entry) for entry in artifact_manifest],
        "reviewer_verdict_reference": reviewer_verdict_reference,
    }
    if reason_code is not None:
        payload["reason_code"] = validate_optional_verdict_reason_code(reason_code).value
    payload["evidence_bundle_id"] = generate_evidence_bundle_id(payload)
    return validate_evidence_bundle(payload)


def generate_evidence_bundle_id(payload: Mapping[str, Any]) -> str:
    """Generate the deterministic `EvidenceBundle` ID from content fields."""

    mapping = validate_required_fields(
        payload,
        tuple(
            field
            for field in EVIDENCE_BUNDLE_ID_COMPONENT_FIELDS
            if field in EVIDENCE_BUNDLE_REQUIRED_FIELDS
        ),
        object_name="EvidenceBundle",
    )
    diagnostics_summary = mapping["diagnostics_summary"]
    if (
        isinstance(diagnostics_summary, Mapping)
        and _diagnostics_status_is_inconclusive(diagnostics_summary)
        and "reason_code" not in mapping
    ):
        raise GovernanceValidationError(
            missing_inconclusive_reason_issue(
                state_field="EvidenceBundle.diagnostics_summary.diagnostics_status"
            )
        )
    components = {
        field: _normalize_id_component(field, mapping[field])
        for field in EVIDENCE_BUNDLE_ID_COMPONENT_FIELDS
        if field in mapping
    }
    return generate_governance_id(GovernanceIdKind.EVIDENCE_BUNDLE, components)


def validate_artifact_manifest_entry(
    payload: Mapping[str, Any],
) -> EvidenceArtifactManifestEntry:
    """Validate one artifact manifest entry and return typed metadata."""

    entries, issues = _validate_artifact_manifest([payload])
    if issues:
        raise GovernanceValidationError([_unprefix_manifest_issue(issue) for issue in issues])
    return entries[0]


def validate_evidence_bundle(payload: Mapping[str, Any]) -> EvidenceBundle:
    """Validate an `EvidenceBundle` mapping fail-closed and return a record."""

    mapping = validate_schema(
        payload,
        required_fields=EVIDENCE_BUNDLE_REQUIRED_FIELDS,
        field_types=EVIDENCE_BUNDLE_FIELD_TYPES,
        allowed_fields=EVIDENCE_BUNDLE_ALLOWED_FIELDS,
        object_name="EvidenceBundle",
    )

    issues: list[ValidationIssue] = []
    issues.extend(_validate_ids(mapping))
    issues.extend(_validate_trial_ids(mapping["trial_ids"]))
    for field in (
        "data_version",
        "factor_version",
        "label_version",
        "reviewer_verdict_reference",
    ):
        issues.extend(_validate_text_field(mapping, field))
    for field in ("code_hash", "config_hash"):
        issues.extend(_validate_hash_field(mapping, field))
    issues.extend(_validate_metadata_mapping(mapping, "diagnostics_summary"))
    issues.extend(_validate_negative_control_results(mapping["negative_control_results"]))
    issues.extend(_validate_limitations(mapping["limitations"]))
    manifest_entries, manifest_issues = _validate_artifact_manifest(mapping["artifact_manifest"])
    issues.extend(manifest_issues)
    reason_code = _parse_optional_reason_code(mapping, issues)
    if _diagnostics_status_is_inconclusive(mapping["diagnostics_summary"]) and reason_code is None:
        issues.append(
            missing_inconclusive_reason_issue(
                state_field="EvidenceBundle.diagnostics_summary.diagnostics_status"
            )
        )
    issues.extend(_validate_canonical_serializable(mapping))

    if not issues:
        expected_id = generate_evidence_bundle_id(mapping)
        if mapping["evidence_bundle_id"] != expected_id:
            issues.append(
                ValidationIssue(
                    field="evidence_bundle_id",
                    code="evidence_bundle_id_mismatch",
                    message=(
                        "EvidenceBundle.evidence_bundle_id must match "
                        "deterministic EvidenceBundle content"
                    ),
                    expected=expected_id,
                    actual=str(mapping["evidence_bundle_id"]),
                )
            )

    if issues:
        raise GovernanceValidationError(issues)

    return EvidenceBundle(
        evidence_bundle_id=mapping["evidence_bundle_id"],
        alpha_spec_id=mapping["alpha_spec_id"],
        study_spec_id=mapping["study_spec_id"],
        trial_ids=list(mapping["trial_ids"]),
        data_version=mapping["data_version"],
        factor_version=mapping["factor_version"],
        label_version=mapping["label_version"],
        code_hash=mapping["code_hash"],
        config_hash=mapping["config_hash"],
        diagnostics_summary=dict(mapping["diagnostics_summary"]),
        negative_control_results=[dict(result) for result in mapping["negative_control_results"]],
        limitations=list(mapping["limitations"]),
        artifact_manifest=manifest_entries,
        reviewer_verdict_reference=mapping["reviewer_verdict_reference"],
        reason_code=reason_code,
    )


def validate_evidence_ready_gate(
    evidence_bundle: EvidenceBundle | Mapping[str, Any] | None,
    *,
    from_state: str = DIAGNOSTICS_RUN_STATE,
    to_state: str = EVIDENCE_READY_STATE,
) -> EvidenceBundle:
    """Block `DIAGNOSTICS_RUN -> EVIDENCE_READY` unless a bundle validates."""

    issues: list[ValidationIssue] = []
    if from_state != DIAGNOSTICS_RUN_STATE or to_state != EVIDENCE_READY_STATE:
        issues.append(
            ValidationIssue(
                field="transition",
                code="unsupported_evidence_ready_gate_transition",
                message=("evidence-ready gate only evaluates DIAGNOSTICS_RUN -> EVIDENCE_READY"),
                expected=f"{DIAGNOSTICS_RUN_STATE}->{EVIDENCE_READY_STATE}",
                actual=f"{from_state}->{to_state}",
            )
        )
    if evidence_bundle is None:
        issues.append(
            ValidationIssue(
                field="evidence_bundle",
                code="missing_evidence_bundle",
                message="valid EvidenceBundle is required before evidence-ready status",
                expected="validated EvidenceBundle",
                actual="missing",
            )
        )

    if issues:
        raise GovernanceValidationError(issues)
    if isinstance(evidence_bundle, EvidenceBundle):
        bundle = validate_evidence_bundle(evidence_bundle.to_dict())
    else:
        bundle = validate_evidence_bundle(evidence_bundle)
    control_issues = _validate_required_negative_controls_for_evidence_ready(bundle)
    if control_issues:
        raise GovernanceValidationError(control_issues)
    return bundle


def assert_evidence_ready(
    evidence_bundle: EvidenceBundle | Mapping[str, Any] | None,
) -> EvidenceBundle:
    """Alias for the pure no-EvidenceBundle-no-candidate precondition."""

    return validate_evidence_ready_gate(evidence_bundle)


def _validate_ids(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    id_checks = (
        ("evidence_bundle_id", GovernanceIdKind.EVIDENCE_BUNDLE),
        ("alpha_spec_id", GovernanceIdKind.ALPHA_SPEC),
        ("study_spec_id", GovernanceIdKind.STUDY_SPEC),
    )
    for field, kind in id_checks:
        try:
            validate_governance_id(mapping[field], expected_kind=kind)
        except GovernanceIdError as exc:
            issues.append(
                ValidationIssue(
                    field=field,
                    code=exc.issue.code,
                    message=exc.issue.message,
                    expected=kind.value,
                    actual=str(exc.issue.value),
                )
            )
    return issues


def _validate_trial_ids(trial_ids: list[Any]) -> list[ValidationIssue]:
    if not trial_ids:
        return [
            ValidationIssue(
                field="trial_ids",
                code="empty_required_field",
                message="EvidenceBundle.trial_ids must contain at least one trial",
                expected="non-empty list of TrialLedgerRecord IDs",
                actual="empty list",
            )
        ]

    issues: list[ValidationIssue] = []
    seen: set[str] = set()
    for index, trial_id in enumerate(trial_ids):
        field = f"trial_ids[{index}]"
        if type(trial_id) is not str:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="invalid_item_type",
                    message=f"EvidenceBundle.{field} must be a string",
                    expected="TrialLedgerRecord ID string",
                    actual=type(trial_id).__name__,
                )
            )
            continue
        try:
            validate_governance_id(
                trial_id,
                expected_kind=GovernanceIdKind.TRIAL_LEDGER_RECORD,
            )
        except GovernanceIdError as exc:
            issues.append(
                ValidationIssue(
                    field=field,
                    code=exc.issue.code,
                    message=exc.issue.message,
                    expected=GovernanceIdKind.TRIAL_LEDGER_RECORD.value,
                    actual=str(exc.issue.value),
                )
            )
            continue
        if trial_id in seen:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="duplicate_trial_id",
                    message="EvidenceBundle.trial_ids must be a set of unique trials",
                    expected="unique TrialLedgerRecord IDs",
                    actual=trial_id,
                )
            )
        seen.add(trial_id)
    return issues


def _validate_text_field(
    mapping: Mapping[str, Any],
    field: str,
) -> list[ValidationIssue]:
    value = mapping[field]
    if _normalize_text(value) not in _VAGUE_TEXT:
        return []
    return [
        ValidationIssue(
            field=field,
            code="empty_required_field",
            message=f"EvidenceBundle.{field} must be explicit",
            expected="non-empty explicit string",
            actual=str(value),
        )
    ]


def _validate_hash_field(mapping: Mapping[str, Any], field: str) -> list[ValidationIssue]:
    value = mapping[field]
    if _SHA256_HEX_PATTERN.fullmatch(value) is not None:
        return []
    return [
        ValidationIssue(
            field=field,
            code="invalid_content_hash",
            message=f"EvidenceBundle.{field} must be a lowercase SHA-256 hex digest",
            expected="64 lowercase hexadecimal characters",
            actual=value,
        )
    ]


def _validate_metadata_mapping(
    mapping: Mapping[str, Any],
    field: str,
) -> list[ValidationIssue]:
    value = mapping[field]
    if not value:
        return [
            ValidationIssue(
                field=field,
                code="empty_required_field",
                message=f"EvidenceBundle.{field} must contain explicit metadata",
                expected="non-empty mapping",
                actual="empty mapping",
            )
        ]

    issues: list[ValidationIssue] = []
    for key, item in value.items():
        if not isinstance(key, str) or _normalize_text(key) in _VAGUE_TEXT:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="invalid_metadata_key",
                    message=f"EvidenceBundle.{field} keys must be explicit strings",
                    expected="non-empty explicit string key",
                    actual=str(key),
                )
            )
        issues.extend(_validate_substantive_value(item, field=f"{field}.{key}"))
    return issues


def _validate_negative_control_results(values: list[Any]) -> list[ValidationIssue]:
    if not values:
        return [
            ValidationIssue(
                field="negative_control_results",
                code="empty_required_field",
                message=(
                    "EvidenceBundle.negative_control_results must contain at least one result"
                ),
                expected="non-empty list of result metadata",
                actual="empty list",
            )
        ]

    issues: list[ValidationIssue] = []
    for index, item in enumerate(values):
        field = f"negative_control_results[{index}]"
        if not isinstance(item, Mapping):
            issues.append(
                ValidationIssue(
                    field=field,
                    code="invalid_item_type",
                    message=f"EvidenceBundle.{field} must be a mapping",
                    expected="result metadata mapping",
                    actual=type(item).__name__,
                )
            )
            continue
        if not item:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="empty_required_field",
                    message=f"EvidenceBundle.{field} must contain explicit metadata",
                    expected="non-empty result metadata mapping",
                    actual="empty mapping",
                )
            )
            continue
        for key, value in item.items():
            if not isinstance(key, str) or _normalize_text(key) in _VAGUE_TEXT:
                issues.append(
                    ValidationIssue(
                        field=field,
                        code="invalid_metadata_key",
                        message=f"EvidenceBundle.{field} keys must be explicit strings",
                        expected="non-empty explicit string key",
                        actual=str(key),
                    )
                )
            issues.extend(_validate_substantive_value(value, field=f"{field}.{key}"))
    return issues


def _validate_required_negative_controls_for_evidence_ready(
    bundle: EvidenceBundle,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    results_by_type: dict[str, NegativeControlResult] = {}
    allowed_refs = {bundle.study_spec_id, bundle.evidence_bundle_id}

    for index, item in enumerate(bundle.negative_control_results):
        field = f"negative_control_results[{index}]"
        try:
            result = validate_negative_control_result(item)
        except GovernanceValidationError as exc:
            issues.extend(
                _prefix_negative_control_issues(exc.issues, parent_field=field)
            )
            continue

        control_type = result.canary_type.value
        if control_type in results_by_type:
            issues.append(
                ValidationIssue(
                    field=f"{field}.canary_type",
                    code="duplicate_required_negative_control_result",
                    message=(
                        "Evidence-ready gate requires one current result per "
                        "required negative-control type"
                    ),
                    expected="unique required negative-control canary_type",
                    actual=control_type,
                )
            )
        results_by_type.setdefault(control_type, result)

        if result.pass_fail is not NegativeControlPassFail.PASS:
            issues.append(
                ValidationIssue(
                    field=f"{field}.pass_fail",
                    code="failed_required_negative_control_result",
                    message=(
                        "Evidence-ready gate requires every required negative "
                        f"control to PASS; {control_type} did not pass"
                    ),
                    expected=f"{control_type}:PASS",
                    actual=f"{control_type}:{result.pass_fail.value}",
                )
            )
        if result.related_study_or_evidence not in allowed_refs:
            issues.append(
                ValidationIssue(
                    field=f"{field}.related_study_or_evidence",
                    code="stale_required_negative_control_result",
                    message=(
                        "Evidence-ready gate requires negative-control results "
                        f"to reference this study or evidence bundle; {control_type} "
                        "is stale"
                    ),
                    expected=" or ".join(sorted(allowed_refs)),
                    actual=result.related_study_or_evidence,
                )
            )

    for control_type in REQUIRED_NEGATIVE_CONTROL_TYPES:
        if control_type not in results_by_type:
            issues.append(
                ValidationIssue(
                    field="negative_control_results",
                    code="missing_required_negative_control_result",
                    message=(
                        "Evidence-ready gate requires a PASS result for every "
                        f"required negative-control type; missing {control_type}"
                    ),
                    expected=control_type,
                    actual="missing",
                )
            )
    return issues


def _prefix_negative_control_issues(
    issues: list[ValidationIssue],
    *,
    parent_field: str,
) -> list[ValidationIssue]:
    return [
        ValidationIssue(
            field=f"{parent_field}.{issue.field}",
            code=issue.code,
            message=issue.message,
            expected=issue.expected,
            actual=issue.actual,
        )
        for issue in issues
    ]


def _validate_limitations(values: list[Any]) -> list[ValidationIssue]:
    if not values:
        return [
            ValidationIssue(
                field="limitations",
                code="empty_required_field",
                message="EvidenceBundle.limitations must contain declared limitations",
                expected="non-empty list of explicit limitation strings",
                actual="empty list",
            )
        ]

    issues: list[ValidationIssue] = []
    for index, item in enumerate(values):
        field = f"limitations[{index}]"
        if type(item) is not str:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="invalid_item_type",
                    message=f"EvidenceBundle.{field} must be a string",
                    expected="explicit limitation string",
                    actual=type(item).__name__,
                )
            )
            continue
        if _normalize_text(item) in _VAGUE_TEXT:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="empty_required_field",
                    message=f"EvidenceBundle.{field} must be explicit",
                    expected="non-empty explicit limitation",
                    actual=item,
                )
            )
    return issues


def _validate_artifact_manifest(
    values: list[Any],
) -> tuple[list[EvidenceArtifactManifestEntry], list[ValidationIssue]]:
    if not values:
        return [], [
            ValidationIssue(
                field="artifact_manifest",
                code="empty_required_field",
                message="EvidenceBundle.artifact_manifest must contain at least one entry",
                expected="non-empty list of artifact manifest entries",
                actual="empty list",
            )
        ]

    entries: list[EvidenceArtifactManifestEntry] = []
    issues: list[ValidationIssue] = []
    for index, item in enumerate(values):
        field = f"artifact_manifest[{index}]"
        if isinstance(item, EvidenceArtifactManifestEntry):
            entry_mapping: Mapping[str, Any] = item.to_dict()
        elif isinstance(item, Mapping):
            entry_mapping = item
        else:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="invalid_item_type",
                    message=f"EvidenceBundle.{field} must be a mapping",
                    expected="artifact manifest entry mapping",
                    actual=type(item).__name__,
                )
            )
            continue

        try:
            validate_schema(
                entry_mapping,
                required_fields=ARTIFACT_MANIFEST_ENTRY_REQUIRED_FIELDS,
                field_types=ARTIFACT_MANIFEST_ENTRY_FIELD_TYPES,
                allowed_fields=ARTIFACT_MANIFEST_ENTRY_REQUIRED_FIELDS,
                object_name="EvidenceBundle.artifact_manifest entry",
            )
        except GovernanceValidationError as exc:
            issues.extend(_prefix_manifest_issues(exc.issues, field))
            continue

        entry_issues: list[ValidationIssue] = []
        for text_field in ("logical_name", "role", "reference"):
            entry_issues.extend(_validate_manifest_text_field(entry_mapping, text_field, field))
        entry_issues.extend(
            _validate_manifest_reference(entry_mapping["reference"], f"{field}.reference")
        )
        entry_issues.extend(
            _validate_manifest_hash(entry_mapping["content_hash"], f"{field}.content_hash")
        )

        if entry_issues:
            issues.extend(entry_issues)
            continue

        entries.append(
            EvidenceArtifactManifestEntry(
                logical_name=entry_mapping["logical_name"],
                role=entry_mapping["role"],
                reference=entry_mapping["reference"],
                content_hash=entry_mapping["content_hash"],
            )
        )
    return entries, issues


def _validate_manifest_text_field(
    mapping: Mapping[str, Any],
    text_field: str,
    parent_field: str,
) -> list[ValidationIssue]:
    value = mapping[text_field]
    if _normalize_text(value) not in _VAGUE_TEXT:
        return []
    return [
        ValidationIssue(
            field=f"{parent_field}.{text_field}",
            code="empty_required_field",
            message=f"EvidenceBundle.{parent_field}.{text_field} must be explicit",
            expected="non-empty explicit string",
            actual=str(value),
        )
    ]


def _validate_manifest_reference(value: str, field: str) -> list[ValidationIssue]:
    normalized = _normalize_text(value)
    if normalized in _VAGUE_TEXT:
        return []
    if (
        value.startswith(("/", "\\", "~"))
        or "\\" in value
        or _WINDOWS_ABSOLUTE_PATH_PATTERN.match(value) is not None
        or ".." in value.split("/")
    ):
        return [
            ValidationIssue(
                field=field,
                code="invalid_manifest_reference",
                message=(
                    "EvidenceBundle artifact references must be relative "
                    "local-only paths or opaque local references"
                ),
                expected="relative local-only reference",
                actual=value,
            )
        ]
    if "://" in value or normalized.startswith("data:"):
        return [
            ValidationIssue(
                field=field,
                code="external_or_embedded_manifest_reference",
                message=(
                    "EvidenceBundle artifact references must not be external "
                    "URLs or embedded content"
                ),
                expected="local-only reference metadata",
                actual=value,
            )
        ]
    return []


def _validate_manifest_hash(value: str, field: str) -> list[ValidationIssue]:
    if _SHA256_HEX_PATTERN.fullmatch(value) is not None:
        return []
    return [
        ValidationIssue(
            field=field,
            code="invalid_content_hash",
            message="EvidenceBundle artifact manifest content_hash must be SHA-256",
            expected="64 lowercase hexadecimal characters",
            actual=value,
        )
    ]


def _validate_substantive_value(value: Any, *, field: str) -> list[ValidationIssue]:
    if value is None:
        return [
            ValidationIssue(
                field=field,
                code="null_required_field",
                message=f"EvidenceBundle.{field} must not be null",
                expected="explicit metadata value",
                actual="NoneType",
            )
        ]
    if isinstance(value, str):
        if _normalize_text(value) in _VAGUE_TEXT:
            return [
                ValidationIssue(
                    field=field,
                    code="vague_required_field",
                    message=f"EvidenceBundle.{field} must be explicit, not vague",
                    expected="substantive explicit value",
                    actual=value,
                )
            ]
        return []
    if isinstance(value, list):
        if not value:
            return [
                ValidationIssue(
                    field=field,
                    code="empty_required_field",
                    message=f"EvidenceBundle.{field} must not be an empty list",
                    expected="non-empty value",
                    actual="empty list",
                )
            ]
        issues: list[ValidationIssue] = []
        for index, item in enumerate(value):
            issues.extend(_validate_substantive_value(item, field=f"{field}[{index}]"))
        return issues
    if isinstance(value, dict):
        if not value:
            return [
                ValidationIssue(
                    field=field,
                    code="empty_required_field",
                    message=f"EvidenceBundle.{field} must not be an empty mapping",
                    expected="non-empty value",
                    actual="empty mapping",
                )
            ]
        issues = []
        for key, item in value.items():
            if not isinstance(key, str) or _normalize_text(key) in _VAGUE_TEXT:
                issues.append(
                    ValidationIssue(
                        field=field,
                        code="invalid_metadata_key",
                        message=(f"EvidenceBundle.{field} nested keys must be explicit strings"),
                        expected="non-empty explicit string key",
                        actual=str(key),
                    )
                )
            issues.extend(_validate_substantive_value(item, field=f"{field}.{key}"))
        return issues
    return []


def _validate_canonical_serializable(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    try:
        canonical_serialize(
            {
                field: _normalize_id_component(field, mapping[field])
                for field in EVIDENCE_BUNDLE_ALLOWED_FIELDS
                if field in mapping
            }
        )
    except GovernanceValidationError as exc:
        return list(exc.issues)
    except GovernanceSerializationError as exc:
        return [
            ValidationIssue(
                field=exc.issue.path,
                code=exc.issue.code,
                message=exc.issue.message,
                expected="canonical JSON-compatible EvidenceBundle",
                actual=exc.issue.path,
            )
        ]
    return []


def _normalize_id_component(field: str, value: Any) -> JsonValue:
    if field == "artifact_manifest":
        return [_manifest_entry_to_dict(entry) for entry in value]
    if field == "reason_code":
        return validate_verdict_reason_code(value).value
    return cast(JsonValue, value)


def _manifest_entry_to_dict(
    entry: EvidenceArtifactManifestEntry | Mapping[str, Any],
) -> dict[str, JsonValue]:
    if isinstance(entry, EvidenceArtifactManifestEntry):
        return entry.to_dict()
    return cast(dict[str, JsonValue], dict(entry))


def _prefix_manifest_issues(
    issues: tuple[ValidationIssue, ...],
    parent_field: str,
) -> list[ValidationIssue]:
    prefixed: list[ValidationIssue] = []
    for issue in issues:
        field = parent_field if issue.field == "$" else f"{parent_field}.{issue.field}"
        prefixed.append(
            ValidationIssue(
                field=field,
                code=issue.code,
                message=issue.message,
                expected=issue.expected,
                actual=issue.actual,
            )
        )
    return prefixed


def _unprefix_manifest_issue(issue: ValidationIssue) -> ValidationIssue:
    prefix = "artifact_manifest[0]."
    field = issue.field.removeprefix(prefix)
    return ValidationIssue(
        field=field,
        code=issue.code,
        message=issue.message,
        expected=issue.expected,
        actual=issue.actual,
    )


def _parse_optional_reason_code(
    mapping: Mapping[str, Any],
    issues: list[ValidationIssue],
) -> VerdictReasonCode | None:
    if "reason_code" not in mapping:
        return None
    try:
        return validate_optional_verdict_reason_code(mapping["reason_code"])
    except GovernanceValidationError as exc:
        issues.extend(exc.issues)
        return None


def _diagnostics_status_is_inconclusive(diagnostics_summary: Mapping[str, Any]) -> bool:
    return diagnostics_summary.get("diagnostics_status") == INCONCLUSIVE_DIAGNOSTICS_STATUS


def _normalize_text(value: object) -> str:
    if isinstance(value, str):
        return " ".join(value.strip().lower().split())
    return str(value).strip().lower()


__all__ = [
    "ARTIFACT_MANIFEST_ENTRY_REQUIRED_FIELDS",
    "DIAGNOSTICS_RUN_STATE",
    "EVIDENCE_BUNDLE_ALLOWED_FIELDS",
    "EVIDENCE_BUNDLE_ID_COMPONENT_FIELDS",
    "EVIDENCE_BUNDLE_OPTIONAL_FIELDS",
    "EVIDENCE_BUNDLE_REQUIRED_FIELDS",
    "EVIDENCE_READY_STATE",
    "EvidenceArtifactManifestEntry",
    "EvidenceBundle",
    "INCONCLUSIVE_DIAGNOSTICS_STATUS",
    "assert_evidence_ready",
    "create_evidence_bundle",
    "generate_evidence_bundle_id",
    "validate_artifact_manifest_entry",
    "validate_evidence_bundle",
    "validate_evidence_ready_gate",
]
