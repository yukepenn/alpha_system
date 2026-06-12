"""Surrogate-FDR calibration runs over label-shuffled study inputs."""

from __future__ import annotations

import json
import random
import re
import stat
import tempfile
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, cast

from alpha_system.core.hashing import hash_config
from alpha_system.core.run_ids import generate_run_id
from alpha_system.data.fixture_policy import repository_root_from_module
from alpha_system.data.paths import assert_local_wsl_path
from alpha_system.governance.evidence_bundle import create_evidence_bundle
from alpha_system.governance.ids import (
    GovernanceIdError,
    GovernanceIdKind,
    generate_governance_id,
    validate_governance_id,
)
from alpha_system.governance.promotion_gate import (
    PromotionGateContext,
    validate_governance_transition,
)
from alpha_system.governance.serialization import (
    GovernanceSerializationError,
    JsonValue,
    canonical_serialize,
    content_hash,
    deserialize,
)
from alpha_system.governance.study_spec import StudySpec, validate_study_spec
from alpha_system.governance.trial_ledger import (
    TrialLedgerRecord,
    TrialStatus,
    create_trial_ledger_record,
)
from alpha_system.governance.validation import (
    ExpectedType,
    GovernanceValidationError,
    ValidationIssue,
    require_mapping,
    validate_schema,
)
from alpha_system.governance.verdict_reason_code import VerdictReasonCode
from alpha_system.research.diagnostics import DiagnosticsError, compute_diagnostic_summary
from alpha_system.research.study_config import StudyConfig, StudyConfigError
from alpha_system.research.study_outputs import (
    StudyOutputError,
    StudyRunResult,
    write_study_outputs,
)


class SurrogatePerturbationType(StrEnum):
    """Declared surrogate perturbations for calibration runs."""

    LABEL_SHUFFLE = "label_shuffle"
    RANDOM_TARGET = "random_target"


class SurrogateGateStatus(StrEnum):
    """Gate outcome statuses persisted on a SurrogateStudyRun."""

    PASSED = "PASSED"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


ZERO_PASS_MET = "zero-pass-met"
LEAKAGE_BLOCKED = VerdictReasonCode.LEAKAGE_BLOCKED.value
CALIBRATION_BLOCKED = "CALIBRATION_BLOCKED"
SURROGATE_STUDY_RUN_FIELDS = (
    "surrogate_id",
    "original_study_spec_id",
    "perturbation_type",
    "seed",
    "trial_ids",
    "gate_outcome",
    "created_at",
)
SURROGATE_STUDY_RUN_FIELD_TYPES: dict[str, ExpectedType] = {
    "surrogate_id": str,
    "original_study_spec_id": str,
    "perturbation_type": (str, SurrogatePerturbationType),
    "seed": int,
    "trial_ids": list,
    "gate_outcome": dict,
    "created_at": str,
}
SURROGATE_STUDY_RUN_ID_COMPONENT_FIELDS = tuple(
    field for field in SURROGATE_STUDY_RUN_FIELDS if field != "surrogate_id"
)
SURROGATE_SCOPE_KEY = "surrogate_fdr"
DEFAULT_SURROGATE_FAMILY_ID = "family-rigor-p05-surrogate-fdr"
_UTC_SECOND_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_HEAVY_SUFFIXES = {
    ".arrow",
    ".db",
    ".dbn",
    ".feather",
    ".log",
    ".parquet",
    ".sqlite",
    ".sqlite3",
    ".zst",
}
_FORBIDDEN_REPO_NAMESPACE_ROOTS = (
    ("registry",),
    ("metadata",),
    ("data", "raw"),
    ("data", "canonical"),
    ("artifacts",),
    ("runs",),
    ("research", "futures_core_alpha_pilot_v1"),
    ("research", "futures_substrate_scaleout_v1"),
)
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
class SurrogateStudyRun:
    """Validated record for one label-shuffled full-pipeline calibration run."""

    surrogate_id: str
    original_study_spec_id: str
    perturbation_type: SurrogatePerturbationType
    seed: int
    trial_ids: tuple[str, ...]
    gate_outcome: dict[str, JsonValue]
    created_at: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> SurrogateStudyRun:
        """Build a SurrogateStudyRun from a mapping after fail-closed validation."""

        return validate_surrogate_study_run(payload)

    @classmethod
    def from_canonical_json(cls, text: str) -> SurrogateStudyRun:
        """Deserialize canonical JSON and validate the resulting record."""

        value = deserialize(text)
        mapping = require_mapping(value, object_name="SurrogateStudyRun")
        return validate_surrogate_study_run(mapping)

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a strict JSON-compatible representation."""

        return {
            "surrogate_id": self.surrogate_id,
            "original_study_spec_id": self.original_study_spec_id,
            "perturbation_type": self.perturbation_type.value,
            "seed": self.seed,
            "trial_ids": list(self.trial_ids),
            "gate_outcome": dict(self.gate_outcome),
            "created_at": self.created_at,
        }

    def to_canonical_json(self) -> str:
        """Serialize the validated run through the canonical primitive."""

        return canonical_serialize(self.to_dict())


@dataclass(frozen=True, slots=True)
class SurrogateRunPaths:
    """Local-only paths written for one surrogate run."""

    namespace: str
    shuffled_labels_path: str
    study_output_dir: str
    trial_ledger_path: str
    variant_ledger_path: str
    surrogate_record_path: str

    def to_dict(self) -> dict[str, JsonValue]:
        """Return local-only path metadata for audit records."""

        return {
            "namespace": self.namespace,
            "shuffled_labels_path": self.shuffled_labels_path,
            "study_output_dir": self.study_output_dir,
            "trial_ledger_path": self.trial_ledger_path,
            "variant_ledger_path": self.variant_ledger_path,
            "surrogate_record_path": self.surrogate_record_path,
        }


@dataclass(frozen=True, slots=True)
class SurrogateRunResult:
    """Completed surrogate run plus local-only audit paths."""

    run: SurrogateStudyRun
    paths: SurrogateRunPaths

    @property
    def passed(self) -> bool:
        """Return true only when the shuffled run passed the calibrated gate."""

        return self.run.gate_outcome.get("passed") is True

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a JSON-compatible local audit summary."""

        return {
            "run": self.run.to_dict(),
            "paths": self.paths.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class SurrogateCalibrationReport:
    """Value-free aggregate for N seeded surrogate calibration runs."""

    run_count: int
    error_count: int
    gate_pass_count: int
    gate_pass_rate: float
    threshold_verdict: str
    per_run: tuple[dict[str, JsonValue], ...]

    @property
    def accepted(self) -> bool:
        """Return true only when zero pass and zero errors were observed."""

        return self.threshold_verdict == ZERO_PASS_MET

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a value-free JSON-compatible report."""

        return {
            "run_count": self.run_count,
            "error_count": self.error_count,
            "gate_pass_count": self.gate_pass_count,
            "gate_pass_rate": self.gate_pass_rate,
            "threshold_verdict": self.threshold_verdict,
            "per_run": [dict(row) for row in self.per_run],
        }


def create_surrogate_study_run(
    *,
    original_study_spec_id: str,
    perturbation_type: SurrogatePerturbationType | str,
    seed: int,
    trial_ids: Iterable[str],
    gate_outcome: Mapping[str, JsonValue],
    created_at: str,
) -> SurrogateStudyRun:
    """Create a content-addressed SurrogateStudyRun record."""

    payload: dict[str, JsonValue] = {
        "original_study_spec_id": original_study_spec_id,
        "perturbation_type": SurrogatePerturbationType(perturbation_type).value,
        "seed": _validate_seed(seed),
        "trial_ids": list(trial_ids),
        "gate_outcome": dict(gate_outcome),
        "created_at": created_at,
    }
    payload["surrogate_id"] = generate_surrogate_study_run_id(payload)
    return validate_surrogate_study_run(payload)


def generate_surrogate_study_run_id(payload: Mapping[str, Any]) -> str:
    """Generate the deterministic SurrogateStudyRun ID from content fields."""

    mapping = require_mapping(payload, object_name="SurrogateStudyRun")
    components = {
        field: _surrogate_id_component(field, mapping[field])
        for field in SURROGATE_STUDY_RUN_ID_COMPONENT_FIELDS
        if field in mapping
    }
    return generate_governance_id(GovernanceIdKind.SURROGATE_STUDY_RUN, components)


def validate_surrogate_study_run(payload: Mapping[str, Any]) -> SurrogateStudyRun:
    """Validate a SurrogateStudyRun mapping fail-closed."""

    mapping = validate_schema(
        payload,
        required_fields=SURROGATE_STUDY_RUN_FIELDS,
        field_types=SURROGATE_STUDY_RUN_FIELD_TYPES,
        allowed_fields=SURROGATE_STUDY_RUN_FIELDS,
        object_name="SurrogateStudyRun",
    )
    issues: list[ValidationIssue] = []
    issues.extend(_validate_surrogate_ids(mapping))
    perturbation_type = _parse_perturbation_type(mapping["perturbation_type"], issues)
    seed = _parse_seed(mapping["seed"], issues)
    trial_ids = _validate_trial_ids(mapping["trial_ids"], issues)
    gate_outcome = _validate_gate_outcome(mapping["gate_outcome"], issues)
    issues.extend(_validate_created_at(mapping["created_at"]))
    issues.extend(_validate_canonical_serializable(mapping))
    if not issues:
        expected_id = generate_surrogate_study_run_id(mapping)
        if mapping["surrogate_id"] != expected_id:
            issues.append(
                ValidationIssue(
                    field="surrogate_id",
                    code="surrogate_id_mismatch",
                    message=(
                        "SurrogateStudyRun.surrogate_id must match deterministic "
                        "SurrogateStudyRun content"
                    ),
                    expected=expected_id,
                    actual=str(mapping["surrogate_id"]),
                )
            )

    if issues:
        raise GovernanceValidationError(issues)
    assert perturbation_type is not None
    assert seed is not None
    return SurrogateStudyRun(
        surrogate_id=mapping["surrogate_id"],
        original_study_spec_id=mapping["original_study_spec_id"],
        perturbation_type=perturbation_type,
        seed=seed,
        trial_ids=trial_ids,
        gate_outcome=gate_outcome,
        created_at=mapping["created_at"],
    )


def run_surrogate_study(
    study_spec: StudySpec | Mapping[str, Any],
    *,
    seed: int,
    namespace: str | Path,
    perturbation_type: SurrogatePerturbationType | str = SurrogatePerturbationType.LABEL_SHUFFLE,
    family_id: str = DEFAULT_SURROGATE_FAMILY_ID,
    created_at: str | None = None,
) -> SurrogateRunResult:
    """Execute one seeded label-shuffled study through the real governance gates."""

    active_type = SurrogatePerturbationType(perturbation_type)
    if active_type is not SurrogatePerturbationType.LABEL_SHUFFLE:
        raise GovernanceValidationError(
            ValidationIssue(
                field="perturbation_type",
                code="unsupported_surrogate_execution",
                message="RIGOR-P05 executes only label_shuffle surrogate runs",
                expected=SurrogatePerturbationType.LABEL_SHUFFLE.value,
                actual=active_type.value,
            )
        )

    active_seed = _validate_seed(seed)
    active_created_at = created_at or deterministic_created_at(active_seed)
    _raise_if_issues(_validate_created_at(active_created_at))
    active_namespace = require_isolated_namespace(namespace)
    active_study_spec = _coerce_study_spec(study_spec)
    run_root = active_namespace / f"seed_{active_seed}"
    labels_dir = run_root / "labels"
    study_dir = run_root / "study_outputs"
    ledgers_dir = run_root / "ledgers"
    records_dir = run_root / "surrogate_runs"
    for directory in (labels_dir, study_dir, ledgers_dir, records_dir):
        directory.mkdir(parents=True, exist_ok=True)

    scope = _surrogate_scope(active_study_spec)
    original_labels_path = _scope_path(scope, "labels_path")
    shuffled_labels_path = labels_dir / "label_shuffle.jsonl"
    shuffle_summary = write_label_shuffled_copy(
        original_labels_path,
        shuffled_labels_path,
        seed=active_seed,
    )
    study_config = _study_config_for_surrogate(
        active_study_spec,
        scope=scope,
        seed=active_seed,
        shuffled_labels_path=shuffled_labels_path,
        output_dir=study_dir,
    )
    study_result = _run_study_deterministic(study_config, seed=active_seed)
    diagnostics_status = _diagnostics_status(study_result.summary.warnings)
    reason_code = (
        VerdictReasonCode.UNDERPOWERED
        if diagnostics_status == "INCONCLUSIVE"
        else None
    )
    code_hash = content_hash(
        {
            "engine_version": study_result.summary.engine_version,
            "surrogate_runner": "RIGOR-P05",
        }
    )
    config_hash = hash_config(study_config.to_dict())
    trial_record = create_trial_ledger_record(
        alpha_spec_id=active_study_spec.alpha_spec_id,
        study_spec_id=active_study_spec.study_spec_id,
        run_id=study_result.summary.run_id,
        variant_id=f"surrogate-seed-{active_seed}",
        status=TrialStatus.COMPLETED,
        parameters={
            "perturbation_type": active_type.value,
            "seed": active_seed,
            "shuffle_group_count": shuffle_summary["group_count"],
            "shuffled_record_count": shuffle_summary["record_count"],
        },
        metrics_summary={
            "diagnostics_status": diagnostics_status,
            "sample_size": study_result.summary.sample_size,
            "warning_count": len(study_result.summary.warnings),
            "diagnostic_group_count": len(study_result.summary.diagnostics),
        },
        failure_reason=None,
        oos_touched_flag=False,
        locked_test_contamination_flag=False,
        code_hash=code_hash,
        config_hash=config_hash,
        surrogate_flag=True,
    )
    trial_ledger_path = ledgers_dir / "trial-ledger.json"
    variant_ledger_path = ledgers_dir / "variant-ledger.jsonl"
    _write_trial_ledger(trial_ledger_path, (trial_record,))
    variant_ledger_path.write_text("", encoding="utf-8")
    evidence_bundle = create_evidence_bundle(
        alpha_spec_id=active_study_spec.alpha_spec_id,
        study_spec_id=active_study_spec.study_spec_id,
        trial_ids=[trial_record.trial_id],
        data_version=study_result.summary.data_version,
        factor_version=study_result.summary.factor_version,
        label_version=f"surrogate-label-shuffle-seed-{active_seed}",
        code_hash=code_hash,
        config_hash=config_hash,
        diagnostics_summary={
            "diagnostics_run_ref": study_result.summary.run_id,
            "diagnostics_status": diagnostics_status,
            "sample_size": study_result.summary.sample_size,
            "warning_count": len(study_result.summary.warnings),
            "diagnostic_groups": sorted(study_result.summary.diagnostics),
        },
        negative_control_results=[
            {
                "control_name": "label_shuffle_surrogate",
                "result": "executed",
                "summary": "label values were deterministically permuted before diagnostics",
            }
        ],
        limitations=[
            "surrogate-FDR calibration metadata only; no alpha claim is made",
        ],
        artifact_manifest=[
            {
                "logical_name": "surrogate diagnostic summary",
                "role": "diagnostics_summary",
                "reference": f"surrogate/{active_seed}/diagnostic_summary.json",
                "content_hash": hash_config(study_result.summary.to_dict()),
            }
        ],
        reviewer_verdict_reference="surrogate-calibration-not-reviewed",
        reason_code=reason_code,
    )
    validate_governance_transition(
        "DIAGNOSTICS_ALLOWED",
        "DIAGNOSTICS_RUN",
        PromotionGateContext(
            study_spec=active_study_spec,
            trial_ledger_records=(trial_record,),
            family_id=family_id,
            variant_ledger_path=variant_ledger_path,
        ),
    )
    evidence_transition = validate_governance_transition(
        "DIAGNOSTICS_RUN",
        "EVIDENCE_READY",
        PromotionGateContext(
            evidence_bundle=evidence_bundle,
            study_spec=active_study_spec,
            trial_ledger_records=(trial_record,),
            trial_ledger_path=trial_ledger_path,
            family_id=family_id,
            variant_ledger_path=variant_ledger_path,
        ),
    )
    passed = diagnostics_status == "PASS"
    gate_status = SurrogateGateStatus.PASSED if passed else SurrogateGateStatus.BLOCKED
    gate_outcome: dict[str, JsonValue] = {
        "status": gate_status.value,
        "passed": passed,
        "reason_code": None if passed else VerdictReasonCode.UNDERPOWERED.value,
        "evidence_transition": f"{evidence_transition.previous_state.value}->"
        f"{evidence_transition.next_state.value}",
        "diagnostics_status": diagnostics_status,
        "warning_count": len(study_result.summary.warnings),
    }
    run = create_surrogate_study_run(
        original_study_spec_id=active_study_spec.study_spec_id,
        perturbation_type=active_type,
        seed=active_seed,
        trial_ids=(trial_record.trial_id,),
        gate_outcome=gate_outcome,
        created_at=active_created_at,
    )
    surrogate_record_path = records_dir / f"{run.surrogate_id}.json"
    _write_canonical_json(surrogate_record_path, run.to_dict())
    paths = SurrogateRunPaths(
        namespace=active_namespace.as_posix(),
        shuffled_labels_path=shuffled_labels_path.as_posix(),
        study_output_dir=study_dir.as_posix(),
        trial_ledger_path=trial_ledger_path.as_posix(),
        variant_ledger_path=variant_ledger_path.as_posix(),
        surrogate_record_path=surrogate_record_path.as_posix(),
    )
    return SurrogateRunResult(run=run, paths=paths)


def calibrate_surrogate_fdr(
    study_specs: Iterable[StudySpec | Mapping[str, Any]],
    *,
    run_budget: int,
    base_seed: int,
    namespace: str | Path,
    family_id: str = DEFAULT_SURROGATE_FAMILY_ID,
) -> SurrogateCalibrationReport:
    """Run N seeded label-shuffled studies and aggregate a zero-pass verdict."""

    active_namespace = require_isolated_namespace(namespace)
    active_run_budget = _validate_run_budget(run_budget)
    active_base_seed = _validate_seed(base_seed)
    validated_specs = tuple(_coerce_study_spec(spec) for spec in study_specs)
    if not validated_specs:
        raise GovernanceValidationError(
            ValidationIssue(
                field="study_specs",
                code="missing_study_specs",
                message="surrogate calibration requires at least one StudySpec",
                expected="one or more StudySpec mappings",
                actual="empty",
            )
        )

    rows: list[dict[str, JsonValue]] = []
    for spec_index, study_spec in enumerate(validated_specs):
        for run_index in range(active_run_budget):
            seed = active_base_seed + spec_index * active_run_budget + run_index
            try:
                result = run_surrogate_study(
                    study_spec,
                    seed=seed,
                    namespace=active_namespace,
                    family_id=family_id,
                )
            except (
                DiagnosticsError,
                GovernanceSerializationError,
                GovernanceValidationError,
                OSError,
                StudyConfigError,
                StudyOutputError,
                ValueError,
            ) as exc:
                rows.append(_error_row(study_spec, seed=seed, exc=exc))
                continue
            rows.append(
                {
                    "study_spec_id": study_spec.study_spec_id,
                    "seed": seed,
                    "surrogate_id": result.run.surrogate_id,
                    "gate_status": str(result.run.gate_outcome["status"]),
                    "passed": result.passed,
                    "reason_code": result.run.gate_outcome.get("reason_code"),
                }
            )

    run_count = len(rows)
    error_count = sum(1 for row in rows if row["gate_status"] == SurrogateGateStatus.ERROR.value)
    gate_pass_count = sum(1 for row in rows if row.get("passed") is True)
    pass_rate = 0.0 if run_count == 0 else gate_pass_count / run_count
    if gate_pass_count > 0:
        threshold_verdict = LEAKAGE_BLOCKED
    elif error_count > 0:
        threshold_verdict = CALIBRATION_BLOCKED
    else:
        threshold_verdict = ZERO_PASS_MET
    return SurrogateCalibrationReport(
        run_count=run_count,
        error_count=error_count,
        gate_pass_count=gate_pass_count,
        gate_pass_rate=pass_rate,
        threshold_verdict=threshold_verdict,
        per_run=tuple(rows),
    )


def render_value_free_calibration_report(
    report: SurrogateCalibrationReport,
    *,
    title: str = "RIGOR-P05 Synthetic Surrogate-FDR Calibration",
) -> str:
    """Render a commit-eligible value-free Markdown calibration report."""

    lines = [
        f"# {title}",
        "",
        "This report is value-free: it records run counts, seeds, gate outcomes, "
        "and the declared threshold only. It contains no label, feature, return, "
        "or diagnostic values.",
        "",
        "## Threshold",
        "",
        "- Declared threshold: zero shuffled runs may pass the promotion gate.",
        f"- Threshold verdict: `{report.threshold_verdict}`.",
        "- Any shuffled pass is `LEAKAGE_BLOCKED` and requires diagnosis before "
        "the kill-shot resumes.",
        "- Errored runs block calibration success and are not counted as non-passes.",
        "",
        "## Synthetic Calibration Summary",
        "",
        f"- Run count: {report.run_count}",
        f"- Error count: {report.error_count}",
        f"- Gate pass count: {report.gate_pass_count}",
        f"- Gate pass rate: {report.gate_pass_rate:.6f}",
        "",
        "## Per-Run Seeds And Outcomes",
        "",
        "| StudySpec | Seed | Outcome | Surrogate ID | Reason |",
        "|---|---:|---|---|---|",
    ]
    for row in report.per_run:
        lines.append(
            "| {study_spec_id} | {seed} | {gate_status} | {surrogate_id} | {reason} |".format(
                study_spec_id=row.get("study_spec_id", ""),
                seed=row.get("seed", ""),
                gate_status=row.get("gate_status", ""),
                surrogate_id=row.get("surrogate_id", ""),
                reason=row.get("reason_code") or row.get("error_type") or "",
            )
        )
    lines.extend(
        [
            "",
            "## Machinery Inventory",
            "",
            "- `SurrogateStudyRun` schema and deterministic serialization live in "
            "`src/alpha_system/governance/surrogate_run.py`.",
            "- `surrogate_flag` is threaded through `TrialLedgerRecord`; true "
            "surrogate trials are excluded from production variant/family counts.",
            "- `alpha governance surrogate-calibrate` runs seeded label-shuffled "
            "calibrations in caller-supplied isolated namespaces.",
            "- Real-data calibration over the kill-shot StudySpec remains a "
            "coordinator runbook step before FUTSUB-P28 kill-shot resume.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_value_free_calibration_report(
    path: str | Path,
    report: SurrogateCalibrationReport,
) -> Path:
    """Write a value-free Markdown report to a commit-eligible path."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_value_free_calibration_report(report), encoding="utf-8")
    return output


def write_label_shuffled_copy(
    labels_path: str | Path,
    output_path: str | Path,
    *,
    seed: int,
) -> dict[str, JsonValue]:
    """Write a deterministic label-value shuffle to an isolated JSONL path."""

    active_seed = _validate_seed(seed)
    source = assert_local_wsl_path(labels_path)
    output = assert_local_wsl_path(output_path)
    if not source.is_file():
        raise GovernanceValidationError(
            ValidationIssue(
                field="labels_path",
                code="missing_label_values",
                message="label-shuffle surrogate requires an existing label JSONL file",
                expected="existing local label JSONL file",
                actual=source.as_posix(),
            )
        )
    labels = _read_jsonl_mappings(source)
    if not labels:
        raise GovernanceValidationError(
            ValidationIssue(
                field="labels_path",
                code="empty_label_values",
                message="label-shuffle surrogate requires at least one label row",
                expected="non-empty label JSONL file",
                actual=source.as_posix(),
            )
        )
    shuffled = [dict(label) for label in labels]
    moved_count = 0
    groups = _label_groups(labels)
    for group_key, indices in groups.items():
        if len(indices) < 2:
            continue
        permutation = _deranged_indices(
            len(indices),
            seed=active_seed + _stable_group_offset(group_key),
        )
        for target_position, source_position in enumerate(permutation):
            target_index = indices[target_position]
            source_index = indices[source_position]
            shuffled[target_index]["value"] = labels[source_index].get("value")
            if target_index != source_index:
                moved_count += 1
    if moved_count == 0:
        raise GovernanceValidationError(
            ValidationIssue(
                field="labels_path",
                code="insufficient_label_rows_for_shuffle",
                message="label-shuffle surrogate must move at least one label value",
                expected="at least two labels in one label group",
                actual=f"{len(labels)} label rows across {len(groups)} groups",
            )
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in shuffled),
        encoding="utf-8",
    )
    return {
        "record_count": len(labels),
        "group_count": len(groups),
        "moved_count": moved_count,
    }


def require_isolated_namespace(namespace: str | Path) -> Path:
    """Require an existing writable namespace that cannot be a production target."""

    candidate = assert_local_wsl_path(namespace)
    issues: list[ValidationIssue] = []
    if candidate.suffix.lower() in _HEAVY_SUFFIXES:
        issues.append(
            ValidationIssue(
                field="namespace",
                code="surrogate_namespace_must_be_directory",
                message="surrogate namespace must be a directory, not a data or DB file",
                expected="existing isolated directory",
                actual=candidate.as_posix(),
            )
        )
    if not candidate.exists():
        issues.append(
            ValidationIssue(
                field="namespace",
                code="missing_surrogate_namespace",
                message="surrogate calibration requires an existing isolated namespace",
                expected="existing writable directory",
                actual=candidate.as_posix(),
            )
        )
    elif not candidate.is_dir():
        issues.append(
            ValidationIssue(
                field="namespace",
                code="surrogate_namespace_must_be_directory",
                message="surrogate namespace must be an existing directory",
                expected="directory",
                actual=candidate.as_posix(),
            )
        )
    else:
        mode = candidate.stat().st_mode
        if mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH) == 0:
            issues.append(
                ValidationIssue(
                    field="namespace",
                    code="unwritable_surrogate_namespace",
                    message="surrogate namespace must be writable",
                    expected="writable isolated directory",
                    actual=candidate.as_posix(),
                )
            )
        if not _is_temp_namespace(candidate) and not candidate.name.startswith(
            "rigor_p05_surrogate_"
        ):
            issues.append(
                ValidationIssue(
                    field="namespace",
                    code="surrogate_namespace_not_declared_scratch",
                    message=(
                        "non-temp surrogate namespaces must use the "
                        "rigor_p05_surrogate_ scratch prefix"
                    ),
                    expected="pytest tmp path or ALPHA_DATA_ROOT/rigor_p05_surrogate_*",
                    actual=candidate.as_posix(),
                )
            )
    issues.extend(_validate_not_production_namespace(candidate))
    if issues:
        raise GovernanceValidationError(issues)
    return candidate


def deterministic_created_at(seed: int) -> str:
    """Return a deterministic UTC timestamp for a surrogate seed."""

    second = _validate_seed(seed) % 60
    minute = (_validate_seed(seed) // 60) % 60
    return f"2000-01-01T00:{minute:02d}:{second:02d}Z"


def _run_study_deterministic(config: StudyConfig, *, seed: int) -> StudyRunResult:
    config_payload = config.to_dict()
    config_hash = hash_config(config_payload)
    timestamp = datetime(2000, 1, 1, 0, 0, seed % 60, tzinfo=UTC)
    run_id = generate_run_id(
        "study",
        timestamp=timestamp,
        seed=config.study_id,
        components={
            "factor_id": config.factor_id,
            "factor_version": config.factor_version,
            "label_id": config.label_id,
            "label_version": config.label_version,
            "data_version": config.data_version,
            "config_hash": config_hash,
        },
    )
    summary = compute_diagnostic_summary(config, run_id=run_id)
    output_paths = write_study_outputs(
        summary,
        output_dir=config.output_dir,
        manifest_path=config.manifest_path,
        config_hash=config_hash,
        config_payload=config_payload,
    )
    return StudyRunResult(
        summary=summary,
        output_paths=output_paths,
        registry_path=None,
        registry_written=False,
    )


def _study_config_for_surrogate(
    study_spec: StudySpec,
    *,
    scope: Mapping[str, Any],
    seed: int,
    shuffled_labels_path: Path,
    output_dir: Path,
) -> StudyConfig:
    payload: dict[str, Any] = {
        "study_id": f"{study_spec.study_spec_id}-surrogate-{seed}",
        "factor_id": _scope_text(scope, "factor_id"),
        "factor_version": _scope_text(scope, "factor_version"),
        "label_id": _scope_text(scope, "label_id"),
        "label_version": _scope_text(scope, "label_version"),
        "data_version": _scope_text(scope, "data_version"),
        "factor_values_path": _scope_path(scope, "factor_values_path").as_posix(),
        "labels_path": shuffled_labels_path.as_posix(),
        "output_dir": output_dir.as_posix(),
        "manifest_path": (output_dir / "manifest.json").as_posix(),
        "registry_path": None,
    }
    for key in (
        "horizon_seconds",
        "start_ts",
        "end_ts",
        "instruments",
        "sessions",
        "sample_size_thresholds",
        "diagnostic_types",
        "bucket_count",
        "engine_version",
    ):
        if key in scope:
            payload[key] = scope[key]
    return StudyConfig.from_mapping(payload)


def _surrogate_scope(study_spec: StudySpec) -> Mapping[str, Any]:
    scope = study_spec.dataset_scope.get(SURROGATE_SCOPE_KEY)
    if not isinstance(scope, Mapping):
        raise GovernanceValidationError(
            ValidationIssue(
                field=f"dataset_scope.{SURROGATE_SCOPE_KEY}",
                code="missing_surrogate_fdr_scope",
                message="StudySpec.dataset_scope must declare surrogate_fdr inputs",
                expected="mapping with factor_values_path and labels_path",
                actual=type(scope).__name__,
            )
        )
    return scope


def _scope_text(scope: Mapping[str, Any], key: str) -> str:
    value = scope.get(key)
    if not isinstance(value, str) or value.strip().lower() in _VAGUE_TEXT:
        raise GovernanceValidationError(
            ValidationIssue(
                field=f"dataset_scope.{SURROGATE_SCOPE_KEY}.{key}",
                code="missing_surrogate_scope_field",
                message=f"surrogate_fdr scope requires {key}",
                expected="non-empty string",
                actual=type(value).__name__ if value is not None else "missing",
            )
        )
    return value.strip()


def _scope_path(scope: Mapping[str, Any], key: str) -> Path:
    return assert_local_wsl_path(_scope_text(scope, key))


def _diagnostics_status(warnings: Iterable[str]) -> str:
    return "INCONCLUSIVE" if tuple(warnings) else "PASS"


def _write_trial_ledger(path: Path, records: tuple[TrialLedgerRecord, ...]) -> None:
    payload: dict[str, JsonValue] = {
        "schema": "surrogate-trial-ledger-v1",
        "records": [record.to_dict() for record in records],
    }
    _write_canonical_json(path, payload)


def _write_canonical_json(path: Path, payload: Mapping[str, JsonValue]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_serialize(dict(payload)) + "\n", encoding="utf-8")


def _read_jsonl_mappings(path: Path) -> list[dict[str, JsonValue]]:
    rows: list[dict[str, JsonValue]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise GovernanceValidationError(
            ValidationIssue(
                field="labels_path",
                code="label_values_read_failed",
                message="label values could not be read for surrogate shuffle",
                expected="readable label JSONL file",
                actual=f"{path}: {exc}",
            )
        ) from exc
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise GovernanceValidationError(
                ValidationIssue(
                    field=f"labels_path:{line_number}",
                    code="invalid_label_jsonl",
                    message="label JSONL row could not be parsed",
                    expected="JSON object line",
                    actual=exc.msg,
                )
            ) from exc
        if not isinstance(value, Mapping):
            raise GovernanceValidationError(
                ValidationIssue(
                    field=f"labels_path:{line_number}",
                    code="invalid_label_row_type",
                    message="label JSONL rows must be mappings",
                    expected="JSON object line",
                    actual=type(value).__name__,
                )
            )
        rows.append(cast(dict[str, JsonValue], dict(value)))
    return rows


def _label_groups(labels: list[dict[str, JsonValue]]) -> dict[tuple[str, str, str], list[int]]:
    groups: dict[tuple[str, str, str], list[int]] = {}
    for index, row in enumerate(labels):
        label_id = str(row.get("label_id", ""))
        label_type = str(row.get("label_type", label_id))
        data_version = str(row.get("data_version", ""))
        groups.setdefault((label_id, label_type, data_version), []).append(index)
    return groups


def _deranged_indices(length: int, *, seed: int) -> list[int]:
    indices = list(range(length))
    rng = random.Random(seed)
    rng.shuffle(indices)
    if length > 1 and all(position == value for position, value in enumerate(indices)):
        indices = indices[1:] + indices[:1]
    return indices


def _stable_group_offset(group_key: tuple[str, str, str]) -> int:
    return int(content_hash({"group_key": list(group_key)})[:8], 16)


def _coerce_study_spec(value: StudySpec | Mapping[str, Any]) -> StudySpec:
    if isinstance(value, StudySpec):
        return validate_study_spec(value.to_dict())
    if isinstance(value, Mapping):
        return validate_study_spec(value)
    raise GovernanceValidationError(
        ValidationIssue(
            field="study_spec",
            code="invalid_study_spec_type",
            message="study_spec must be a StudySpec or mapping",
            expected="StudySpec or mapping",
            actual=type(value).__name__,
        )
    )


def _error_row(study_spec: StudySpec, *, seed: int, exc: BaseException) -> dict[str, JsonValue]:
    return {
        "study_spec_id": study_spec.study_spec_id,
        "seed": seed,
        "surrogate_id": "",
        "gate_status": SurrogateGateStatus.ERROR.value,
        "passed": False,
        "reason_code": None,
        "error_type": type(exc).__name__,
    }


def _validate_not_production_namespace(path: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    repo_root = repository_root_from_module()
    try:
        relative = path.resolve(strict=False).relative_to(repo_root)
    except ValueError:
        return []
    parts = relative.parts
    for root_parts in _FORBIDDEN_REPO_NAMESPACE_ROOTS:
        if parts[: len(root_parts)] == root_parts:
            issues.append(
                ValidationIssue(
                    field="namespace",
                    code="production_namespace_forbidden",
                    message="surrogate runs must not target production repo namespaces",
                    expected="pytest tmp path or ALPHA_DATA_ROOT/rigor_p05_surrogate_*",
                    actual=path.as_posix(),
                )
            )
            break
    return issues


def _is_temp_namespace(path: Path) -> bool:
    temp_root = Path(tempfile.gettempdir()).resolve(strict=False)
    try:
        path.resolve(strict=False).relative_to(temp_root)
    except ValueError:
        return False
    return True


def _validate_surrogate_ids(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    checks = (
        ("surrogate_id", GovernanceIdKind.SURROGATE_STUDY_RUN),
        ("original_study_spec_id", GovernanceIdKind.STUDY_SPEC),
    )
    for field, kind in checks:
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


def _parse_perturbation_type(
    value: Any,
    issues: list[ValidationIssue],
) -> SurrogatePerturbationType | None:
    try:
        return SurrogatePerturbationType(value)
    except ValueError:
        issues.append(
            ValidationIssue(
                field="perturbation_type",
                code="invalid_surrogate_perturbation_type",
                message="SurrogateStudyRun.perturbation_type must be a declared value",
                expected=" | ".join(item.value for item in SurrogatePerturbationType),
                actual=str(value),
            )
        )
        return None


def _parse_seed(value: Any, issues: list[ValidationIssue]) -> int | None:
    try:
        return _validate_seed(value)
    except GovernanceValidationError as exc:
        issues.extend(exc.issues)
        return None


def _validate_seed(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise GovernanceValidationError(
            ValidationIssue(
                field="seed",
                code="invalid_surrogate_seed",
                message="surrogate seed must be a non-negative integer",
                expected="non-negative integer",
                actual=str(value),
            )
        )
    return value


def _validate_run_budget(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise GovernanceValidationError(
            ValidationIssue(
                field="run_budget",
                code="invalid_surrogate_run_budget",
                message="surrogate calibration run budget must be a positive integer",
                expected="positive integer",
                actual=str(value),
            )
        )
    return value


def _validate_trial_ids(values: list[Any], issues: list[ValidationIssue]) -> tuple[str, ...]:
    seen: set[str] = set()
    trial_ids: list[str] = []
    for index, trial_id in enumerate(values):
        field = f"trial_ids[{index}]"
        if type(trial_id) is not str:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="invalid_item_type",
                    message=f"SurrogateStudyRun.{field} must be a string",
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
                    message="SurrogateStudyRun.trial_ids must be unique",
                    expected="unique TrialLedgerRecord IDs",
                    actual=trial_id,
                )
            )
        seen.add(trial_id)
        trial_ids.append(trial_id)
    return tuple(trial_ids)


def _validate_gate_outcome(
    value: dict[str, Any],
    issues: list[ValidationIssue],
) -> dict[str, JsonValue]:
    if not value:
        issues.append(
            ValidationIssue(
                field="gate_outcome",
                code="empty_required_field",
                message="SurrogateStudyRun.gate_outcome must contain explicit metadata",
                expected="non-empty mapping",
                actual="empty mapping",
            )
        )
        return {}
    status = value.get("status")
    passed = value.get("passed")
    try:
        parsed_status = SurrogateGateStatus(status)
    except ValueError:
        issues.append(
            ValidationIssue(
                field="gate_outcome.status",
                code="invalid_surrogate_gate_status",
                message="gate_outcome.status must be a declared surrogate gate status",
                expected=" | ".join(item.value for item in SurrogateGateStatus),
                actual=str(status),
            )
        )
        parsed_status = None
    if type(passed) is not bool:
        issues.append(
            ValidationIssue(
                field="gate_outcome.passed",
                code="invalid_gate_pass_flag",
                message="gate_outcome.passed must be an explicit boolean",
                expected="boolean",
                actual=type(passed).__name__,
            )
        )
    if parsed_status is SurrogateGateStatus.PASSED and passed is not True:
        issues.append(
            ValidationIssue(
                field="gate_outcome.passed",
                code="gate_status_pass_flag_mismatch",
                message="PASSED surrogate gate status requires passed=true",
                expected="true",
                actual=str(passed),
            )
        )
    return cast(dict[str, JsonValue], dict(value))


def _validate_created_at(value: str) -> list[ValidationIssue]:
    if _UTC_SECOND_PATTERN.fullmatch(value) is not None:
        return []
    return [
        ValidationIssue(
            field="created_at",
            code="invalid_created_at",
            message="SurrogateStudyRun.created_at must be second-resolution UTC text",
            expected="YYYY-MM-DDTHH:MM:SSZ",
            actual=str(value),
        )
    ]


def _validate_canonical_serializable(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    try:
        canonical_serialize(cast(JsonValue, dict(mapping)))
    except GovernanceSerializationError as exc:
        return [
            ValidationIssue(
                field=exc.issue.path,
                code=exc.issue.code,
                message=exc.issue.message,
                expected="canonical JSON-compatible SurrogateStudyRun",
                actual=exc.issue.path,
            )
        ]
    return []


def _surrogate_id_component(field: str, value: Any) -> JsonValue:
    if field == "perturbation_type":
        return SurrogatePerturbationType(value).value
    return cast(JsonValue, value)


def _raise_if_issues(issues: list[ValidationIssue]) -> None:
    if issues:
        raise GovernanceValidationError(issues)


__all__ = [
    "CALIBRATION_BLOCKED",
    "LEAKAGE_BLOCKED",
    "ZERO_PASS_MET",
    "SurrogateCalibrationReport",
    "SurrogateGateStatus",
    "SurrogatePerturbationType",
    "SurrogateRunPaths",
    "SurrogateRunResult",
    "SurrogateStudyRun",
    "calibrate_surrogate_fdr",
    "create_surrogate_study_run",
    "deterministic_created_at",
    "generate_surrogate_study_run_id",
    "render_value_free_calibration_report",
    "require_isolated_namespace",
    "run_surrogate_study",
    "validate_surrogate_study_run",
    "write_label_shuffled_copy",
    "write_value_free_calibration_report",
]
