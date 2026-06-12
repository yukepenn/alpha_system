"""Evidence-accrual requeue planning records and deterministic scan helpers.

This module is deliberately isolated from promotion gates. The planning-prior
power estimator below is a value-free heuristic for deciding when an
UNDERPOWERED INCONCLUSIVE verdict is worth manually retesting:

    t ~= SR_prior * sqrt(years_of_accepted_data)

When N_eff metadata is supplied as ``n_eff`` plus ``observation_count``, the
calendar years are scaled by ``n_eff / observation_count``. When that metadata
is absent, the estimator uses calendar years and reports that absence
explicitly. The estimate is never a promotion criterion and must not be
imported by gate code.
"""

from __future__ import annotations

import json
import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from alpha_system.governance.serialization import JsonValue, canonical_serialize, deserialize
from alpha_system.governance.validation import (
    ExpectedType,
    GovernanceValidationError,
    ValidationIssue,
    require_mapping,
    validate_schema,
)
from alpha_system.governance.verdict_reason_code import (
    VerdictReasonCode,
    validate_verdict_reason_code,
)

REQUEUE_REASON = "UNDERPOWERED_EVIDENCE_ACCRUAL"
MATERIALITY_MIN_ACCRUED_MONTHS = 6
MATERIALITY_MIN_POWER_DELTA = 0.25
REQUEUE_SCAN_SCHEMA = "alpha_system.governance.requeue_scan.v1"
REQUEUED_VERDICT_RECORD_REQUIRED_FIELDS = (
    "original_verdict_ref",
    "requeue_reason",
    "prior_power_estimate",
    "new_power_estimate",
    "data_accrued_months",
    "eligible",
    "created_at",
)
REQUEUED_VERDICT_RECORD_FIELD_TYPES: dict[str, ExpectedType] = {
    "original_verdict_ref": str,
    "requeue_reason": str,
    "prior_power_estimate": (int, float),
    "new_power_estimate": (int, float),
    "data_accrued_months": int,
    "eligible": bool,
    "created_at": str,
}
_UTC_SECONDS_SUFFIX = "Z"
_ESTIMATE_PRECISION = 6
_N_EFF_METADATA_ABSENT = "N_EFF_METADATA_ABSENT"
_N_EFF_METADATA_USED = "N_EFF_METADATA_USED"
_N_EFF_METADATA_PARTIAL = "N_EFF_METADATA_PARTIAL"


@dataclass(frozen=True, slots=True)
class PlanningPowerEstimate:
    """Value-free planning heuristic output for requeue eligibility only."""

    estimate: float
    sr_prior: float
    data_months: int
    effective_years: float
    n_eff_ratio: float | None
    metadata_status: str

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "estimate": self.estimate,
            "sr_prior": self.sr_prior,
            "data_months": self.data_months,
            "effective_years": self.effective_years,
            "n_eff_ratio": self.n_eff_ratio,
            "metadata_status": self.metadata_status,
        }


@dataclass(frozen=True, slots=True)
class RequeuedVerdictRecord:
    """Validated record emitted by an evidence-accrual requeue scan."""

    original_verdict_ref: str
    requeue_reason: str
    prior_power_estimate: float
    new_power_estimate: float
    data_accrued_months: int
    eligible: bool
    created_at: str

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> RequeuedVerdictRecord:
        """Build a validated record from a mapping."""

        return validate_requeued_verdict_record(payload)

    @classmethod
    def from_canonical_json(cls, text: str) -> RequeuedVerdictRecord:
        """Deserialize canonical JSON and validate the resulting record."""

        value = deserialize(text)
        mapping = require_mapping(value, object_name="RequeuedVerdictRecord")
        return validate_requeued_verdict_record(mapping)

    def to_dict(self) -> dict[str, JsonValue]:
        """Return the exact public record schema."""

        return {
            "original_verdict_ref": self.original_verdict_ref,
            "requeue_reason": self.requeue_reason,
            "prior_power_estimate": self.prior_power_estimate,
            "new_power_estimate": self.new_power_estimate,
            "data_accrued_months": self.data_accrued_months,
            "eligible": self.eligible,
            "created_at": self.created_at,
        }

    def to_canonical_json(self) -> str:
        """Serialize through the governance canonical JSON primitive."""

        return canonical_serialize(self.to_dict())


@dataclass(frozen=True, slots=True)
class RequeueEligibilityRow:
    """Internal value-free scan row rendered to stdout and record JSON."""

    study_spec_id: str
    original_verdict_ref: str
    prior_power_estimate: float
    new_power_estimate: float
    data_accrued_months: int
    eligible: bool
    requeue_reason: str
    metadata_status: str

    def to_record(self, *, created_at: str) -> RequeuedVerdictRecord:
        return RequeuedVerdictRecord.from_dict(
            {
                "original_verdict_ref": self.original_verdict_ref,
                "requeue_reason": self.requeue_reason,
                "prior_power_estimate": self.prior_power_estimate,
                "new_power_estimate": self.new_power_estimate,
                "data_accrued_months": self.data_accrued_months,
                "eligible": self.eligible,
                "created_at": created_at,
            }
        )

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "study_spec_id": self.study_spec_id,
            "original_verdict_ref": self.original_verdict_ref,
            "prior_power_estimate": self.prior_power_estimate,
            "new_power_estimate": self.new_power_estimate,
            "data_accrued_months": self.data_accrued_months,
            "eligible": self.eligible,
            "requeue_reason": self.requeue_reason,
            "metadata_status": self.metadata_status,
        }


@dataclass(frozen=True, slots=True)
class RequeueScanResult:
    """Deterministic scan output with both table rows and records."""

    rows: tuple[RequeueEligibilityRow, ...]
    records: tuple[RequeuedVerdictRecord, ...]
    materiality_rule: dict[str, JsonValue]
    created_at: str

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "schema": REQUEUE_SCAN_SCHEMA,
            "created_at": self.created_at,
            "materiality_rule": dict(self.materiality_rule),
            "eligibility_rows": [row.to_dict() for row in self.rows],
            "requeued_verdict_records": [record.to_dict() for record in self.records],
        }

    def records_json(self) -> str:
        """Return deterministic, parseable records JSON."""

        return json.dumps(
            {
                "schema": REQUEUE_SCAN_SCHEMA,
                "created_at": self.created_at,
                "materiality_rule": self.materiality_rule,
                "requeued_verdict_records": [record.to_dict() for record in self.records],
            },
            sort_keys=True,
            indent=2,
        )

    def render_table(self) -> str:
        """Render a stable value-free eligibility table."""

        header = (
            "| study_spec_id | original_verdict_ref | prior_power_estimate | "
            "new_power_estimate | data_accrued_months | eligible | requeue_reason | "
            "metadata_status |"
        )
        divider = (
            "|---|---|---:|---:|---:|---|---|---|"
        )
        lines = [header, divider]
        for row in self.rows:
            lines.append(
                "| "
                + " | ".join(
                    (
                        row.study_spec_id,
                        row.original_verdict_ref,
                        f"{row.prior_power_estimate:.6f}",
                        f"{row.new_power_estimate:.6f}",
                        str(row.data_accrued_months),
                        str(row.eligible).lower(),
                        row.requeue_reason,
                        row.metadata_status,
                    )
                )
                + " |"
            )
        return "\n".join(lines)

    def render_text(self) -> str:
        """Render table plus RequeuedVerdictRecords for stdout."""

        return (
            "Requeue Eligibility\n"
            f"{self.render_table()}\n\n"
            "RequeuedVerdictRecords\n"
            f"{self.records_json()}"
        )


def materiality_rule() -> dict[str, JsonValue]:
    """Return the declared, visible requeue materiality rule."""

    return {
        "requeue_reason": REQUEUE_REASON,
        "min_accrued_accepted_months": MATERIALITY_MIN_ACCRUED_MONTHS,
        "min_power_estimate_delta": MATERIALITY_MIN_POWER_DELTA,
        "eligibility_logic": (
            "eligible when accrued accepted months are at least "
            f"{MATERIALITY_MIN_ACCRUED_MONTHS} and new-prior planning power "
            f"is at least {MATERIALITY_MIN_POWER_DELTA}"
        ),
    }


def utc_now_seconds() -> str:
    """Return an injectable-compatible UTC timestamp for scan records."""

    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_requeued_verdict_record(
    payload: Mapping[str, Any],
) -> RequeuedVerdictRecord:
    """Validate a `RequeuedVerdictRecord` mapping fail-closed."""

    mapping = validate_schema(
        payload,
        required_fields=REQUEUED_VERDICT_RECORD_REQUIRED_FIELDS,
        field_types=REQUEUED_VERDICT_RECORD_FIELD_TYPES,
        allowed_fields=REQUEUED_VERDICT_RECORD_REQUIRED_FIELDS,
        object_name="RequeuedVerdictRecord",
    )
    issues: list[ValidationIssue] = []
    for field in ("original_verdict_ref", "requeue_reason", "created_at"):
        if _is_blank_text(mapping[field]):
            issues.append(
                ValidationIssue(
                    field=field,
                    code="empty_required_field",
                    message=f"RequeuedVerdictRecord.{field} must be explicit",
                    expected="non-empty string",
                    actual=str(mapping[field]),
                )
            )
    if mapping.get("requeue_reason") != REQUEUE_REASON:
        issues.append(
            ValidationIssue(
                field="requeue_reason",
                code="invalid_requeue_reason",
                message=(
                    "RequeuedVerdictRecord.requeue_reason must cite the "
                    "evidence-accrual trigger"
                ),
                expected=REQUEUE_REASON,
                actual=str(mapping.get("requeue_reason")),
            )
        )
    for field in ("prior_power_estimate", "new_power_estimate"):
        issues.extend(_validate_non_negative_finite_number(mapping[field], field=field))
    if type(mapping["data_accrued_months"]) is not int or mapping["data_accrued_months"] < 0:
        issues.append(
            ValidationIssue(
                field="data_accrued_months",
                code="invalid_data_accrued_months",
                message="RequeuedVerdictRecord.data_accrued_months must be a non-negative integer",
                expected="integer >= 0",
                actual=str(mapping["data_accrued_months"]),
            )
        )
    if not str(mapping["created_at"]).endswith(_UTC_SECONDS_SUFFIX):
        issues.append(
            ValidationIssue(
                field="created_at",
                code="invalid_utc_timestamp",
                message="RequeuedVerdictRecord.created_at must be a UTC seconds timestamp",
                expected="YYYY-MM-DDTHH:MM:SSZ",
                actual=str(mapping["created_at"]),
            )
        )
    issues.extend(_validate_canonical_serializable(cast(Mapping[str, Any], mapping)))
    if issues:
        raise GovernanceValidationError(issues)

    return RequeuedVerdictRecord(
        original_verdict_ref=mapping["original_verdict_ref"],
        requeue_reason=mapping["requeue_reason"],
        prior_power_estimate=_round_estimate(float(mapping["prior_power_estimate"])),
        new_power_estimate=_round_estimate(float(mapping["new_power_estimate"])),
        data_accrued_months=mapping["data_accrued_months"],
        eligible=mapping["eligible"],
        created_at=mapping["created_at"],
    )


def estimate_planning_prior_power(
    *,
    sr_prior: float,
    data_months: int,
    n_eff: float | None = None,
    observation_count: float | None = None,
) -> PlanningPowerEstimate:
    """Estimate planning-prior power; this is not a governance gate."""

    issues: list[ValidationIssue] = []
    issues.extend(_validate_non_negative_finite_number(sr_prior, field="sr_prior"))
    if type(data_months) is not int or data_months <= 0:
        issues.append(
            ValidationIssue(
                field="data_months",
                code="invalid_data_months",
                message="planning power requires a positive integer month count",
                expected="integer > 0",
                actual=str(data_months),
            )
        )
    ratio: float | None = None
    metadata_status = _N_EFF_METADATA_ABSENT
    if n_eff is not None or observation_count is not None:
        if n_eff is None or observation_count is None:
            metadata_status = _N_EFF_METADATA_PARTIAL
        else:
            issues.extend(_validate_positive_finite_number(n_eff, field="n_eff"))
            issues.extend(
                _validate_positive_finite_number(
                    observation_count,
                    field="observation_count",
                )
            )
            if not issues and n_eff > observation_count:
                issues.append(
                    ValidationIssue(
                        field="n_eff",
                        code="n_eff_exceeds_observation_count",
                        message="n_eff must not exceed observation_count",
                        expected="n_eff <= observation_count",
                        actual=f"{n_eff}>{observation_count}",
                    )
                )
            if not issues:
                ratio = n_eff / observation_count
                metadata_status = _N_EFF_METADATA_USED
    if issues:
        raise GovernanceValidationError(issues)

    calendar_years = data_months / 12.0
    effective_years = calendar_years if ratio is None else calendar_years * ratio
    estimate = sr_prior * math.sqrt(effective_years)
    return PlanningPowerEstimate(
        estimate=_round_estimate(estimate),
        sr_prior=_round_estimate(sr_prior),
        data_months=data_months,
        effective_years=_round_estimate(effective_years),
        n_eff_ratio=None if ratio is None else _round_estimate(ratio),
        metadata_status=metadata_status,
    )


def scan_requeue_candidates(
    *,
    verdict_paths: Sequence[str | Path] = (),
    annotation_paths: Sequence[str | Path] = (),
    acceptance_evidence_path: str | Path,
    created_at: str | None = None,
) -> RequeueScanResult:
    """Scan UNDERPOWERED verdict evidence and return deterministic requeue rows."""

    timestamp = created_at or utc_now_seconds()
    if not timestamp.endswith(_UTC_SECONDS_SUFFIX):
        raise GovernanceValidationError(
            ValidationIssue(
                field="created_at",
                code="invalid_utc_timestamp",
                message="requeue scan timestamp must be a UTC seconds timestamp",
                expected="YYYY-MM-DDTHH:MM:SSZ",
                actual=str(timestamp),
            )
        )
    inputs = _load_scan_inputs(verdict_paths=verdict_paths, annotation_paths=annotation_paths)
    acceptance = _load_acceptance_evidence(acceptance_evidence_path)

    candidates = [_candidate_from_mapping(item) for item in inputs if _is_underpowered(item)]
    rows = tuple(
        sorted(
            (_build_row(candidate, acceptance) for candidate in candidates),
            key=lambda row: (row.study_spec_id, row.original_verdict_ref),
        )
    )
    records = tuple(row.to_record(created_at=timestamp) for row in rows)
    return RequeueScanResult(
        rows=rows,
        records=records,
        materiality_rule=materiality_rule(),
        created_at=timestamp,
    )


def write_requeue_records(path: str | Path, result: RequeueScanResult) -> None:
    """Write deterministic scan records only to the caller-supplied output path."""

    Path(path).write_text(result.records_json() + "\n", encoding="utf-8")


@dataclass(frozen=True, slots=True)
class _Candidate:
    study_spec_id: str
    original_verdict_ref: str
    sr_prior: float
    prior_data_months: int
    prior_n_eff: float | None
    prior_observation_count: float | None


@dataclass(frozen=True, slots=True)
class _AcceptanceEvidence:
    accepted_data_months: int
    n_eff: float | None
    observation_count: float | None


def _load_scan_inputs(
    *,
    verdict_paths: Sequence[str | Path],
    annotation_paths: Sequence[str | Path],
) -> tuple[Mapping[str, Any], ...]:
    files = _json_files(verdict_paths) + _json_files(annotation_paths)
    if not files:
        raise GovernanceValidationError(
            ValidationIssue(
                field="verdicts",
                code="missing_requeue_scan_inputs",
                message="requeue scan requires at least one verdict or annotation JSON input",
                expected="one or more JSON files or directories",
                actual="missing",
            )
        )
    mappings: list[Mapping[str, Any]] = []
    for path in sorted(set(files), key=lambda item: item.as_posix()):
        value = deserialize(path.read_text(encoding="utf-8"))
        mappings.append(require_mapping(value, object_name=f"requeue input {path}"))
    return tuple(mappings)


def _load_acceptance_evidence(path: str | Path) -> dict[str, _AcceptanceEvidence]:
    source = Path(path)
    value = deserialize(source.read_text(encoding="utf-8"))
    mapping = require_mapping(value, object_name="requeue acceptance evidence")
    entries = mapping.get("accepted_data")
    if isinstance(entries, str) or not isinstance(entries, list) or not entries:
        raise GovernanceValidationError(
            ValidationIssue(
                field="accepted_data",
                code="invalid_accepted_data_evidence",
                message="acceptance evidence must contain a non-empty accepted_data list",
                expected="non-empty list",
                actual=type(entries).__name__,
            )
        )
    result: dict[str, _AcceptanceEvidence] = {}
    for index, entry in enumerate(entries):
        entry_mapping = require_mapping(
            entry,
            object_name=f"requeue acceptance evidence accepted_data[{index}]",
        )
        evidence = _acceptance_evidence_from_mapping(entry_mapping, index=index)
        for key in _acceptance_keys(entry_mapping):
            if key in result:
                raise GovernanceValidationError(
                    ValidationIssue(
                        field=f"accepted_data[{index}]",
                        code="duplicate_acceptance_evidence_key",
                        message="acceptance evidence keys must be unique",
                        expected="unique original_verdict_ref or study_spec_id",
                        actual=key,
                    )
                )
            result[key] = evidence
    return result


def _acceptance_evidence_from_mapping(
    mapping: Mapping[str, Any],
    *,
    index: int,
) -> _AcceptanceEvidence:
    if "accepted_data_months" not in mapping:
        raise GovernanceValidationError(
            ValidationIssue(
                field=f"accepted_data[{index}].accepted_data_months",
                code="missing_accepted_data_months",
                message="accepted data evidence must declare accepted_data_months",
                expected="integer month count",
                actual="missing",
            )
        )
    months = _required_int(
        mapping["accepted_data_months"],
        field=f"accepted_data[{index}].accepted_data_months",
    )
    n_eff = _optional_float(mapping, "n_eff", field=f"accepted_data[{index}].n_eff")
    observation_count = _optional_float(
        mapping,
        "observation_count",
        field=f"accepted_data[{index}].observation_count",
    )
    return _AcceptanceEvidence(
        accepted_data_months=months,
        n_eff=n_eff,
        observation_count=observation_count,
    )


def _candidate_from_mapping(mapping: Mapping[str, Any]) -> _Candidate:
    scan_metadata = mapping.get("requeue_scan", {})
    if scan_metadata is None:
        scan_metadata = {}
    scan_mapping = require_mapping(scan_metadata, object_name="requeue_scan")
    study_spec_id = _first_text(mapping, scan_mapping, field="study_spec_id")
    original_verdict_ref = _first_text(
        mapping,
        scan_mapping,
        field="original_verdict_ref",
        aliases=("original_verdict_path", "reviewer_verdict_id"),
    )
    sr_prior = _required_float(
        _first_present(scan_mapping, mapping, fields=("sr_prior", "planning_sr_prior")),
        field="sr_prior",
    )
    prior_data_months = _required_int(
        _first_present(
            scan_mapping,
            mapping,
            fields=("accepted_data_months_at_verdict", "prior_accepted_data_months"),
        ),
        field="accepted_data_months_at_verdict",
    )
    return _Candidate(
        study_spec_id=study_spec_id,
        original_verdict_ref=original_verdict_ref,
        sr_prior=sr_prior,
        prior_data_months=prior_data_months,
        prior_n_eff=_optional_float(
            scan_mapping,
            "n_eff_at_verdict",
            fallback_key="prior_n_eff",
            field="n_eff_at_verdict",
        ),
        prior_observation_count=_optional_float(
            scan_mapping,
            "observation_count_at_verdict",
            fallback_key="prior_observation_count",
            field="observation_count_at_verdict",
        ),
    )


def _build_row(
    candidate: _Candidate,
    acceptance: Mapping[str, _AcceptanceEvidence],
) -> RequeueEligibilityRow:
    accepted = (
        acceptance.get(candidate.original_verdict_ref)
        or acceptance.get(candidate.study_spec_id)
    )
    if accepted is None:
        raise GovernanceValidationError(
            ValidationIssue(
                field="accepted_data",
                code="missing_candidate_acceptance_evidence",
                message="UNDERPOWERED candidate has no matching accepted data evidence",
                expected="accepted_data keyed by original_verdict_ref or study_spec_id",
                actual=candidate.original_verdict_ref,
            )
        )
    data_accrued_months = accepted.accepted_data_months - candidate.prior_data_months
    if data_accrued_months < 0:
        raise GovernanceValidationError(
            ValidationIssue(
                field="accepted_data_months",
                code="accepted_data_months_regressed",
                message="current accepted months must not be lower than verdict-time months",
                expected=f">= {candidate.prior_data_months}",
                actual=str(accepted.accepted_data_months),
            )
        )
    prior = estimate_planning_prior_power(
        sr_prior=candidate.sr_prior,
        data_months=candidate.prior_data_months,
        n_eff=candidate.prior_n_eff,
        observation_count=candidate.prior_observation_count,
    )
    new = estimate_planning_prior_power(
        sr_prior=candidate.sr_prior,
        data_months=accepted.accepted_data_months,
        n_eff=accepted.n_eff,
        observation_count=accepted.observation_count,
    )
    power_delta = new.estimate - prior.estimate
    eligible = (
        data_accrued_months >= MATERIALITY_MIN_ACCRUED_MONTHS
        and power_delta >= MATERIALITY_MIN_POWER_DELTA
    )
    metadata_status = (
        _N_EFF_METADATA_USED
        if prior.metadata_status == _N_EFF_METADATA_USED
        or new.metadata_status == _N_EFF_METADATA_USED
        else new.metadata_status
    )
    return RequeueEligibilityRow(
        study_spec_id=candidate.study_spec_id,
        original_verdict_ref=candidate.original_verdict_ref,
        prior_power_estimate=prior.estimate,
        new_power_estimate=new.estimate,
        data_accrued_months=data_accrued_months,
        eligible=eligible,
        requeue_reason=REQUEUE_REASON,
        metadata_status=metadata_status,
    )


def _json_files(paths: Sequence[str | Path]) -> list[Path]:
    files: list[Path] = []
    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists():
            raise GovernanceValidationError(
                ValidationIssue(
                    field="path",
                    code="missing_requeue_input_path",
                    message="requeue scan input path does not exist",
                    expected="existing JSON file or directory",
                    actual=str(path),
                )
            )
        if path.is_dir():
            files.extend(sorted(path.rglob("*.json"), key=lambda item: item.as_posix()))
        elif path.is_file():
            files.append(path)
        else:
            raise GovernanceValidationError(
                ValidationIssue(
                    field="path",
                    code="invalid_requeue_input_path",
                    message="requeue scan input path must be a file or directory",
                    expected="JSON file or directory",
                    actual=str(path),
                )
            )
    return files


def _is_underpowered(mapping: Mapping[str, Any]) -> bool:
    reason_value = mapping.get("reason_code")
    if reason_value is None and isinstance(mapping.get("judgement"), Mapping):
        reason_value = cast(Mapping[str, Any], mapping["judgement"]).get("reason_code")
    if reason_value is None:
        return False
    try:
        return validate_verdict_reason_code(reason_value) is VerdictReasonCode.UNDERPOWERED
    except GovernanceValidationError:
        raise


def _acceptance_keys(mapping: Mapping[str, Any]) -> tuple[str, ...]:
    keys = tuple(
        value
        for value in (
            mapping.get("original_verdict_ref"),
            mapping.get("original_verdict_path"),
            mapping.get("study_spec_id"),
        )
        if isinstance(value, str) and value.strip()
    )
    if not keys:
        raise GovernanceValidationError(
            ValidationIssue(
                field="accepted_data",
                code="missing_acceptance_evidence_key",
                message=(
                    "accepted data evidence must be keyed by original_verdict_ref "
                    "or study_spec_id"
                ),
                expected="non-empty key",
                actual="missing",
            )
        )
    return keys


def _first_text(
    primary: Mapping[str, Any],
    secondary: Mapping[str, Any],
    *,
    field: str,
    aliases: Iterable[str] = (),
) -> str:
    value = _first_present(primary, secondary, fields=(field, *aliases))
    if not isinstance(value, str) or not value.strip():
        raise GovernanceValidationError(
            ValidationIssue(
                field=field,
                code="missing_required_text",
                message=f"UNDERPOWERED requeue metadata must declare {field}",
                expected="non-empty string",
                actual=type(value).__name__,
            )
        )
    return value


def _first_present(
    primary: Mapping[str, Any],
    secondary: Mapping[str, Any],
    *,
    fields: Iterable[str],
) -> Any:
    for field in fields:
        if field in primary:
            return primary[field]
        if field in secondary:
            return secondary[field]
    return None


def _required_int(value: Any, *, field: str) -> int:
    if type(value) is int and value >= 0:
        return value
    raise GovernanceValidationError(
        ValidationIssue(
            field=field,
            code="invalid_integer_months",
            message=f"{field} must be a non-negative integer",
            expected="integer >= 0",
            actual=str(value),
        )
    )


def _required_float(value: Any, *, field: str) -> float:
    if type(value) in (int, float):
        number = float(value)
        if math.isfinite(number):
            return number
    raise GovernanceValidationError(
        ValidationIssue(
            field=field,
            code="invalid_numeric_value",
            message=f"{field} must be a finite number",
            expected="finite number",
            actual=str(value),
        )
    )


def _optional_float(
    mapping: Mapping[str, Any],
    key: str,
    *,
    field: str,
    fallback_key: str | None = None,
) -> float | None:
    if key in mapping:
        return _required_float(mapping[key], field=field)
    if fallback_key is not None and fallback_key in mapping:
        return _required_float(mapping[fallback_key], field=field)
    return None


def _validate_non_negative_finite_number(value: Any, *, field: str) -> list[ValidationIssue]:
    if type(value) not in (int, float):
        return [
            ValidationIssue(
                field=field,
                code="invalid_numeric_value",
                message=f"{field} must be a finite non-negative number",
                expected="finite number >= 0",
                actual=type(value).__name__,
            )
        ]
    number = float(value)
    if math.isfinite(number) and number >= 0.0:
        return []
    return [
        ValidationIssue(
            field=field,
            code="invalid_numeric_value",
            message=f"{field} must be a finite non-negative number",
            expected="finite number >= 0",
            actual=str(value),
        )
    ]


def _validate_positive_finite_number(value: Any, *, field: str) -> list[ValidationIssue]:
    if type(value) not in (int, float):
        return [
            ValidationIssue(
                field=field,
                code="invalid_numeric_value",
                message=f"{field} must be a finite positive number",
                expected="finite number > 0",
                actual=type(value).__name__,
            )
        ]
    number = float(value)
    if math.isfinite(number) and number > 0.0:
        return []
    return [
        ValidationIssue(
            field=field,
            code="invalid_numeric_value",
            message=f"{field} must be a finite positive number",
            expected="finite number > 0",
            actual=str(value),
        )
    ]


def _validate_canonical_serializable(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    try:
        canonical_serialize(cast(JsonValue, dict(mapping)))
    except (TypeError, ValueError) as exc:
        return [
            ValidationIssue(
                field="$",
                code="not_canonical_serializable",
                message=str(exc),
                expected="strict JSON-compatible governance record",
                actual=type(exc).__name__,
            )
        ]
    return []


def _is_blank_text(value: Any) -> bool:
    return not isinstance(value, str) or not value.strip()


def _round_estimate(value: float) -> float:
    return round(value, _ESTIMATE_PRECISION)


__all__ = [
    "MATERIALITY_MIN_ACCRUED_MONTHS",
    "MATERIALITY_MIN_POWER_DELTA",
    "REQUEUE_REASON",
    "PlanningPowerEstimate",
    "RequeueEligibilityRow",
    "RequeueScanResult",
    "RequeuedVerdictRecord",
    "estimate_planning_prior_power",
    "materiality_rule",
    "scan_requeue_candidates",
    "utc_now_seconds",
    "validate_requeued_verdict_record",
    "write_requeue_records",
]
