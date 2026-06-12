from __future__ import annotations

from copy import deepcopy

import pytest

from alpha_system.governance.evidence_bundle import (
    ARTIFACT_MANIFEST_ENTRY_REQUIRED_FIELDS,
    DIAGNOSTICS_RUN_STATE,
    EVIDENCE_BUNDLE_REQUIRED_FIELDS,
    EVIDENCE_READY_STATE,
    EvidenceArtifactManifestEntry,
    EvidenceBundle,
    create_evidence_bundle,
    generate_evidence_bundle_id,
    validate_artifact_manifest_entry,
    validate_evidence_bundle,
    validate_evidence_ready_gate,
)
from alpha_system.governance.canaries import (
    REQUIRED_NEGATIVE_CONTROL_TYPES,
    NegativeControlPassFail,
    create_negative_control_result,
    expected_failure_for_canary_type,
)
from alpha_system.governance.serialization import canonical_serialize, deserialize
from alpha_system.governance.validation import GovernanceValidationError
from alpha_system.governance.verdict_reason_code import VerdictReasonCode

ALPHA_SPEC_ID = "aspec_af848bc999a4c4b11a421bd0"
STUDY_SPEC_ID = "sspec_438ceffd40855205de5497f0"
TRIAL_ID = "trial_e49649b00c617b1f713df3fa"
SECOND_TRIAL_ID = "trial_4c82b590a90a7d4971ac48c6"
CODE_HASH = "a" * 64
CONFIG_HASH = "b" * 64
MANIFEST_HASH = "c" * 64
STALE_STUDY_SPEC_ID = "sspec_000000000000000000000000"


def valid_manifest_entry() -> dict[str, object]:
    return {
        "logical_name": "diagnostics summary",
        "role": "diagnostics_summary",
        "reference": "local/evidence/diagnostics-summary.json",
        "content_hash": MANIFEST_HASH,
    }


def valid_negative_control_results(
    *,
    related_study_or_evidence: str = STUDY_SPEC_ID,
    failed_controls: tuple[str, ...] = (),
    omitted_controls: tuple[str, ...] = (),
) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for control_type in REQUIRED_NEGATIVE_CONTROL_TYPES:
        if control_type in omitted_controls:
            continue
        expected_failure = expected_failure_for_canary_type(control_type)
        failed = control_type in failed_controls
        results.append(
            create_negative_control_result(
                canary_type=control_type,
                expected_failure=expected_failure,
                observed_result=(
                    f"guard_accepted_known_bad_{control_type}"
                    if failed
                    else expected_failure
                ),
                pass_fail=(
                    NegativeControlPassFail.FAIL
                    if failed
                    else NegativeControlPassFail.PASS
                ),
                related_study_or_evidence=related_study_or_evidence,
                notes=f"Synthetic {control_type} control result for evidence gate tests.",
            ).to_dict()
        )
    return results


def valid_bundle_payload() -> dict[str, object]:
    payload: dict[str, object] = {
        "alpha_spec_id": ALPHA_SPEC_ID,
        "study_spec_id": STUDY_SPEC_ID,
        "trial_ids": [TRIAL_ID, SECOND_TRIAL_ID],
        "data_version": "synthetic-data-v1",
        "factor_version": "synthetic-factor-v1",
        "label_version": "synthetic-label-v1",
        "code_hash": CODE_HASH,
        "config_hash": CONFIG_HASH,
        "diagnostics_summary": {
            "diagnostics_run_ref": "diagnostics-run-001",
            "sample_count": 120,
            "metric_set": "synthetic governance smoke metrics",
        },
        "negative_control_results": valid_negative_control_results(),
        "limitations": [
            "synthetic metadata fixture only",
            "reviewer verdict is referenced but not resolved in this phase",
        ],
        "artifact_manifest": [valid_manifest_entry()],
        "reviewer_verdict_reference": "opaque-reviewer-verdict-reference-001",
    }
    payload["evidence_bundle_id"] = generate_evidence_bundle_id(payload)
    return payload


def payload_with_generated_id(payload: dict[str, object]) -> dict[str, object]:
    updated = deepcopy(payload)
    updated["evidence_bundle_id"] = generate_evidence_bundle_id(updated)
    return updated


def test_valid_evidence_bundle_contains_all_required_fields() -> None:
    payload = valid_bundle_payload()

    bundle = validate_evidence_bundle(payload)

    assert isinstance(bundle, EvidenceBundle)
    assert tuple(bundle.to_dict()) == EVIDENCE_BUNDLE_REQUIRED_FIELDS
    assert bundle.evidence_bundle_id == generate_evidence_bundle_id(payload)
    assert bundle.evidence_bundle_id.startswith("evb_")
    assert bundle.alpha_spec_id.startswith("aspec_")
    assert bundle.study_spec_id.startswith("sspec_")
    assert bundle.trial_ids == [TRIAL_ID, SECOND_TRIAL_ID]
    assert isinstance(bundle.artifact_manifest[0], EvidenceArtifactManifestEntry)
    assert tuple(bundle.artifact_manifest[0].to_dict()) == (ARTIFACT_MANIFEST_ENTRY_REQUIRED_FIELDS)
    assert bundle.reviewer_verdict_reference == "opaque-reviewer-verdict-reference-001"


def test_create_evidence_bundle_generates_content_bound_id() -> None:
    payload = valid_bundle_payload()

    bundle = create_evidence_bundle(
        alpha_spec_id=str(payload["alpha_spec_id"]),
        study_spec_id=str(payload["study_spec_id"]),
        trial_ids=list(payload["trial_ids"]),
        data_version=str(payload["data_version"]),
        factor_version=str(payload["factor_version"]),
        label_version=str(payload["label_version"]),
        code_hash=str(payload["code_hash"]),
        config_hash=str(payload["config_hash"]),
        diagnostics_summary=dict(payload["diagnostics_summary"]),
        negative_control_results=list(payload["negative_control_results"]),
        limitations=list(payload["limitations"]),
        artifact_manifest=list(payload["artifact_manifest"]),
        reviewer_verdict_reference=str(payload["reviewer_verdict_reference"]),
    )

    assert bundle.evidence_bundle_id == payload["evidence_bundle_id"]
    assert bundle.evidence_bundle_id.startswith("evb_")


@pytest.mark.parametrize("field", EVIDENCE_BUNDLE_REQUIRED_FIELDS)
def test_evidence_bundle_rejects_each_missing_required_field(field: str) -> None:
    payload = valid_bundle_payload()
    del payload[field]

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_evidence_bundle(payload)

    assert exc_info.value.issues[0].code == "missing_required_field"
    assert exc_info.value.issues[0].field == field


@pytest.mark.parametrize("field", EVIDENCE_BUNDLE_REQUIRED_FIELDS)
def test_evidence_bundle_rejects_each_null_required_field(field: str) -> None:
    payload = valid_bundle_payload()
    payload[field] = None

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_evidence_bundle(payload)

    assert exc_info.value.issues[0].code == "null_required_field"
    assert exc_info.value.issues[0].field == field


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("evidence_bundle_id", "", "malformed_id"),
        ("alpha_spec_id", "", "malformed_id"),
        ("study_spec_id", "", "malformed_id"),
        ("trial_ids", [], "empty_required_field"),
        ("data_version", "", "empty_required_field"),
        ("factor_version", "", "empty_required_field"),
        ("label_version", "", "empty_required_field"),
        ("code_hash", "", "invalid_content_hash"),
        ("config_hash", "", "invalid_content_hash"),
        ("diagnostics_summary", {}, "empty_required_field"),
        ("negative_control_results", [], "empty_required_field"),
        ("limitations", [], "empty_required_field"),
        ("artifact_manifest", [], "empty_required_field"),
        ("reviewer_verdict_reference", "", "empty_required_field"),
    ],
)
def test_evidence_bundle_rejects_empty_required_fields(
    field: str,
    value: object,
    code: str,
) -> None:
    payload = valid_bundle_payload()
    payload[field] = value

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_evidence_bundle(payload)

    assert exc_info.value.issues[0].code == code
    assert exc_info.value.issues[0].field.startswith(field)


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("evidence_bundle_id", "trial_e49649b00c617b1f713df3fa", "unexpected_kind"),
        ("alpha_spec_id", "trial_e49649b00c617b1f713df3fa", "unexpected_kind"),
        ("study_spec_id", "aspec_af848bc999a4c4b11a421bd0", "unexpected_kind"),
        ("trial_ids", ["aspec_af848bc999a4c4b11a421bd0"], "unexpected_kind"),
        ("trial_ids", [TRIAL_ID, TRIAL_ID], "duplicate_trial_id"),
        ("data_version", "unknown", "empty_required_field"),
        ("factor_version", "tbd", "empty_required_field"),
        ("label_version", "n/a", "empty_required_field"),
        ("code_hash", "A" * 64, "invalid_content_hash"),
        ("config_hash", "not-a-sha256", "invalid_content_hash"),
        ("diagnostics_summary", {"summary": None}, "null_required_field"),
        ("negative_control_results", [{}], "empty_required_field"),
        ("negative_control_results", [{"result": "unknown"}], "vague_required_field"),
        ("limitations", ["n/a"], "empty_required_field"),
        ("reviewer_verdict_reference", "placeholder", "empty_required_field"),
    ],
)
def test_evidence_bundle_rejects_malformed_required_fields(
    field: str,
    value: object,
    code: str,
) -> None:
    payload = valid_bundle_payload()
    payload[field] = value

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_evidence_bundle(payload)

    assert exc_info.value.issues[0].code == code
    assert exc_info.value.issues[0].field.startswith(field)


@pytest.mark.parametrize(
    ("entry_update", "code", "field_suffix"),
    [
        ({"reference": None}, "null_required_field", "reference"),
        ({"content_hash": None}, "null_required_field", "content_hash"),
        ({"reference": ""}, "empty_required_field", "reference"),
        ({"content_hash": "not-a-sha256"}, "invalid_content_hash", "content_hash"),
        (
            {"reference": "/tmp/evidence/diagnostics.json"},
            "invalid_manifest_reference",
            "reference",
        ),
        (
            {"reference": "https://example.invalid/evidence.json"},
            "external_or_embedded_manifest_reference",
            "reference",
        ),
        ({"extra": "not declared"}, "unknown_field", "extra"),
    ],
)
def test_evidence_bundle_rejects_malformed_manifest_entries(
    entry_update: dict[str, object],
    code: str,
    field_suffix: str,
) -> None:
    payload = valid_bundle_payload()
    entry = valid_manifest_entry()
    entry.update(entry_update)
    payload["artifact_manifest"] = [entry]

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_evidence_bundle(payload)

    assert exc_info.value.issues[0].code == code
    assert exc_info.value.issues[0].field.endswith(field_suffix)


@pytest.mark.parametrize("missing_field", ["reference", "content_hash"])
def test_evidence_bundle_rejects_manifest_entries_missing_reference_or_hash(
    missing_field: str,
) -> None:
    payload = valid_bundle_payload()
    entry = valid_manifest_entry()
    del entry[missing_field]
    payload["artifact_manifest"] = [entry]

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_evidence_bundle(payload)

    assert exc_info.value.issues[0].code == "missing_required_field"
    assert exc_info.value.issues[0].field == f"artifact_manifest[0].{missing_field}"


def test_artifact_manifest_entry_validator_returns_typed_entry() -> None:
    entry = validate_artifact_manifest_entry(valid_manifest_entry())

    assert isinstance(entry, EvidenceArtifactManifestEntry)
    assert entry.reference == "local/evidence/diagnostics-summary.json"
    assert entry.content_hash == MANIFEST_HASH


def test_evidence_bundle_rejects_id_that_does_not_match_content() -> None:
    payload = valid_bundle_payload()
    changed = deepcopy(payload)
    changed["data_version"] = "synthetic-data-v2"

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_evidence_bundle(changed)

    assert exc_info.value.issues[0].code == "evidence_bundle_id_mismatch"
    assert exc_info.value.issues[0].field == "evidence_bundle_id"


def test_evidence_bundle_canonical_round_trip_is_deterministic() -> None:
    payload = valid_bundle_payload()
    reordered = dict(reversed(list(payload.items())))

    bundle = validate_evidence_bundle(payload)
    serialized = bundle.to_canonical_json()
    round_tripped = EvidenceBundle.from_canonical_json(serialized)

    assert round_tripped == bundle
    assert deserialize(serialized) == bundle.to_dict()
    assert canonical_serialize(reordered) == serialized


def test_evidence_ready_gate_accepts_only_complete_bundle() -> None:
    payload = valid_bundle_payload()

    bundle = validate_evidence_ready_gate(payload)

    assert bundle == validate_evidence_bundle(payload)


def test_evidence_ready_gate_blocks_without_bundle() -> None:
    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_evidence_ready_gate(None)

    issue = exc_info.value.issues[0]
    assert issue.code == "missing_evidence_bundle"
    assert issue.field == "evidence_bundle"


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("trial_ids", [], "empty_required_field"),
        ("artifact_manifest", [], "empty_required_field"),
    ],
)
def test_evidence_ready_gate_blocks_incomplete_bundle(
    field: str,
    value: object,
    code: str,
) -> None:
    payload = valid_bundle_payload()
    payload[field] = value

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_evidence_ready_gate(payload)

    assert exc_info.value.issues[0].code == code
    assert exc_info.value.issues[0].field == field


def test_evidence_ready_gate_requires_all_required_negative_controls() -> None:
    payload = valid_bundle_payload()
    payload["negative_control_results"] = valid_negative_control_results(
        omitted_controls=("random_target",)
    )
    payload["evidence_bundle_id"] = generate_evidence_bundle_id(payload)

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_evidence_ready_gate(payload)

    assert any(
        issue.code == "missing_required_negative_control_result"
        and issue.expected == "random_target"
        for issue in exc_info.value.issues
    )


def test_evidence_ready_gate_blocks_failed_negative_control_result() -> None:
    payload = valid_bundle_payload()
    payload["negative_control_results"] = valid_negative_control_results(
        failed_controls=("random_target",)
    )
    payload["evidence_bundle_id"] = generate_evidence_bundle_id(payload)

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_evidence_ready_gate(payload)

    assert any(
        issue.code == "failed_required_negative_control_result"
        and issue.actual == "random_target:FAIL"
        for issue in exc_info.value.issues
    )


def test_evidence_ready_gate_blocks_stale_negative_control_result() -> None:
    payload = valid_bundle_payload()
    payload["negative_control_results"] = valid_negative_control_results(
        related_study_or_evidence=STALE_STUDY_SPEC_ID
    )
    payload["evidence_bundle_id"] = generate_evidence_bundle_id(payload)

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_evidence_ready_gate(payload)

    assert any(
        issue.code == "stale_required_negative_control_result"
        and issue.actual == STALE_STUDY_SPEC_ID
        for issue in exc_info.value.issues
    )


def test_evidence_ready_gate_rejects_other_transitions() -> None:
    payload = valid_bundle_payload()

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_evidence_ready_gate(
            payload,
            from_state="DIAGNOSTICS_ALLOWED",
            to_state="DIAGNOSTICS_RUN",
        )

    issue = exc_info.value.issues[0]
    assert issue.code == "unsupported_evidence_ready_gate_transition"
    assert issue.expected == f"{DIAGNOSTICS_RUN_STATE}->{EVIDENCE_READY_STATE}"


def test_payload_with_generated_id_helper_recomputes_when_content_changes() -> None:
    payload = valid_bundle_payload()
    payload["data_version"] = "synthetic-data-v2"

    updated = payload_with_generated_id(payload)

    assert validate_evidence_bundle(updated).data_version == "synthetic-data-v2"


def test_evidence_bundle_diagnostics_inconclusive_requires_reason_code() -> None:
    payload = valid_bundle_payload()
    payload["diagnostics_summary"] = {
        "diagnostics_run_ref": "diagnostics-run-001",
        "diagnostics_status": "INCONCLUSIVE",
        "metric_set": "synthetic governance smoke metrics",
    }
    payload["evidence_bundle_id"] = "evb_aaaaaaaaaaaaaaaaaaaaaaaa"

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_evidence_bundle(payload)

    assert any(
        issue.code == "missing_reason_code_for_inconclusive"
        for issue in exc_info.value.issues
    )


def test_evidence_bundle_rejects_free_text_reason_code() -> None:
    payload = valid_bundle_payload()
    payload["reason_code"] = "substrate missing"
    payload["evidence_bundle_id"] = "evb_aaaaaaaaaaaaaaaaaaaaaaaa"

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_evidence_bundle(payload)

    assert any(issue.code == "invalid_verdict_reason_code" for issue in exc_info.value.issues)


def test_evidence_bundle_accepts_reason_coded_inconclusive_diagnostics() -> None:
    payload = valid_bundle_payload()
    payload["diagnostics_summary"] = {
        "diagnostics_run_ref": "diagnostics-run-001",
        "diagnostics_status": "INCONCLUSIVE",
        "metric_set": "synthetic governance smoke metrics",
    }
    payload["reason_code"] = VerdictReasonCode.SUBSTRATE_GAP.value
    payload["evidence_bundle_id"] = generate_evidence_bundle_id(payload)

    bundle = validate_evidence_bundle(payload)

    assert bundle.reason_code is VerdictReasonCode.SUBSTRATE_GAP
    assert bundle.to_dict()["reason_code"] == "SUBSTRATE_GAP"


def test_evidence_bundle_present_reason_code_changes_id_without_affecting_absent_id() -> None:
    without_reason = validate_evidence_bundle(valid_bundle_payload())
    with_reason_payload = valid_bundle_payload()
    with_reason_payload["reason_code"] = VerdictReasonCode.DATA_QUALITY.value
    with_reason_payload["evidence_bundle_id"] = generate_evidence_bundle_id(with_reason_payload)

    with_reason = validate_evidence_bundle(with_reason_payload)

    assert "reason_code" not in without_reason.to_dict()
    assert with_reason.reason_code is VerdictReasonCode.DATA_QUALITY
    assert with_reason.evidence_bundle_id != without_reason.evidence_bundle_id
