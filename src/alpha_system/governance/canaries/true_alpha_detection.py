"""Point-in-time planted-signal detection canary for the governance gate stack."""

from __future__ import annotations

import json
import math
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import MappingProxyType
from typing import Any, cast

from alpha_system.core.hashing import hash_config
from alpha_system.governance.canaries.catalog import (
    REQUIRED_NEGATIVE_CONTROL_TYPES,
    NegativeControlType,
    expected_failure_for_canary_type,
)
from alpha_system.governance.canaries.negative_control_result import (
    NegativeControlPassFail,
    create_negative_control_result,
)
from alpha_system.governance.evidence_bundle import (
    EvidenceBundle,
    create_evidence_bundle,
    validate_evidence_ready_gate,
)
from alpha_system.governance.ids import GovernanceIdKind, generate_governance_id
from alpha_system.governance.promotion import PromotionLifecycleState
from alpha_system.governance.promotion_gate import (
    PromotionGateContext,
    validate_governance_transition,
)
from alpha_system.governance.sealed_holdout import (
    SealedHoldoutStatus,
    create_sealed_holdout_window,
)
from alpha_system.governance.study_spec import StudySpec, create_study_spec
from alpha_system.governance.trial_ledger import (
    TrialLedgerRecord,
    TrialStatus,
    create_trial_ledger_record,
)
from alpha_system.governance.variant_ledger import validate_variant_and_family_budget
from alpha_system.research.diagnostics import compute_diagnostic_summary
from alpha_system.research.study_config import StudyConfig
from alpha_system.research.study_outputs import DiagnosticSummary

DEFAULT_TRUE_ALPHA_DETECTION_FIXTURE_PATHS: Mapping[str, Path] = MappingProxyType(
    {
        "strong": Path("evals/canaries/true_alpha_detection/strong_fixture.json"),
        "weak": Path("evals/canaries/true_alpha_detection/weak_fixture.json"),
    }
)
DEFAULT_PLANTED_FAKE_ALPHA_CLEAN_TWIN_FIXTURE_PATH = Path(
    "evals/canaries/planted_fake_alpha_clean_twin/synthetic_fixture.json"
)
DETECTION_DIAGNOSTIC = "directional.pearson_ic"
DETECTED = "DETECTED"
NOT_DETECTED = "NOT_DETECTED"
CREATED_AT = "2026-06-12T00:00:00Z"
CODE_HASH = "1" * 64
CONFIG_HASH = "2" * 64
FAMILY_ID = "family-true-alpha-detection-canary"
CLEAN_TWIN_FAMILY_ID = "family-planted-fake-alpha-clean-twin-canary"


@dataclass(frozen=True, slots=True)
class TrueAlphaDetectionCanaryResult:
    """Value-free result summary for one planted-signal detection fixture."""

    fixture_id: str
    strength: str
    expected_detection: bool
    detected: bool
    detection_outcome: str
    diagnostic_name: str
    measured_abs_pearson_ic: float
    detection_threshold_abs_pearson_ic: float
    declared_signal_to_noise: float
    declared_detectable_floor_signal_to_noise: float
    promotion_outcome: str
    evidence_transition: str
    diagnostics_status: str
    sample_count: int
    evidence_bundle_id: str
    trial_id: str
    study_spec_id: str

    @property
    def expectation_met(self) -> bool:
        """Return whether the diagnostic matched the fixture expectation."""

        return self.detected is self.expected_detection and self.promotion_outcome == "EVIDENCE_READY"

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible summary without raw feature or label rows."""

        return {
            "fixture_id": self.fixture_id,
            "strength": self.strength,
            "expected_detection": self.expected_detection,
            "detected": self.detected,
            "detection_outcome": self.detection_outcome,
            "diagnostic_name": self.diagnostic_name,
            "measured_abs_pearson_ic": self.measured_abs_pearson_ic,
            "detection_threshold_abs_pearson_ic": self.detection_threshold_abs_pearson_ic,
            "declared_signal_to_noise": self.declared_signal_to_noise,
            "declared_detectable_floor_signal_to_noise": (
                self.declared_detectable_floor_signal_to_noise
            ),
            "promotion_outcome": self.promotion_outcome,
            "evidence_transition": self.evidence_transition,
            "diagnostics_status": self.diagnostics_status,
            "sample_count": self.sample_count,
            "evidence_bundle_id": self.evidence_bundle_id,
            "trial_id": self.trial_id,
            "study_spec_id": self.study_spec_id,
        }


@dataclass(frozen=True, slots=True)
class PlantedFakeAlphaCleanTwinCanaryResult:
    """Value-free result summary for the clean twin of the P04 contaminated fixture."""

    fixture_id: str
    promotion_outcome: str
    evidence_transition: str
    blocked_issue_code: str
    evidence_bundle_id: str
    trial_id: str
    study_spec_id: str

    @property
    def passed_gate_stack(self) -> bool:
        """Return whether the clean twin reached evidence-ready without a block."""

        return self.promotion_outcome == "EVIDENCE_READY" and self.blocked_issue_code == "none"

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible value-free result summary."""

        return {
            "fixture_id": self.fixture_id,
            "promotion_outcome": self.promotion_outcome,
            "evidence_transition": self.evidence_transition,
            "blocked_issue_code": self.blocked_issue_code,
            "evidence_bundle_id": self.evidence_bundle_id,
            "trial_id": self.trial_id,
            "study_spec_id": self.study_spec_id,
        }


def load_default_true_alpha_detection_fixture(strength: str) -> Mapping[str, Any]:
    """Load one tiny point-in-time planted-signal detection fixture."""

    fixture_path = _repo_root() / DEFAULT_TRUE_ALPHA_DETECTION_FIXTURE_PATHS[
        _strength_key(strength)
    ]
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        msg = f"true-alpha detection fixture root must be a mapping: {fixture_path}"
        raise ValueError(msg)
    return cast(Mapping[str, Any], payload)


def load_default_planted_fake_alpha_clean_twin_fixture() -> Mapping[str, Any]:
    """Load the clean twin for the P04 planted-fake-alpha fixture."""

    fixture_path = _repo_root() / DEFAULT_PLANTED_FAKE_ALPHA_CLEAN_TWIN_FIXTURE_PATH
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        msg = f"planted-fake-alpha clean-twin fixture root must be a mapping: {fixture_path}"
        raise ValueError(msg)
    return cast(Mapping[str, Any], payload)


def run_true_alpha_detection_canary(
    strength: str,
    fixture: Mapping[str, Any] | None = None,
    *,
    workspace: str | Path | None = None,
) -> TrueAlphaDetectionCanaryResult:
    """Run one planted-signal fixture through diagnostics and real governance gates."""

    active_fixture = fixture or load_default_true_alpha_detection_fixture(strength)
    if workspace is None:
        with tempfile.TemporaryDirectory(prefix=f"true-alpha-detection-{strength}-") as raw_tmp:
            return _run_true_alpha_detection_canary(active_fixture, Path(raw_tmp))
    return _run_true_alpha_detection_canary(active_fixture, Path(workspace))


def run_planted_fake_alpha_clean_twin_canary(
    fixture: Mapping[str, Any] | None = None,
    *,
    workspace: str | Path | None = None,
) -> PlantedFakeAlphaCleanTwinCanaryResult:
    """Run the P04 clean twin through the same evidence-ready gate stack."""

    active_fixture = fixture or load_default_planted_fake_alpha_clean_twin_fixture()
    if workspace is None:
        with tempfile.TemporaryDirectory(prefix="planted-fake-alpha-clean-twin-") as raw_tmp:
            return _run_planted_fake_alpha_clean_twin_canary(active_fixture, Path(raw_tmp))
    return _run_planted_fake_alpha_clean_twin_canary(active_fixture, Path(workspace))


def _run_true_alpha_detection_canary(
    fixture: Mapping[str, Any],
    workspace: Path,
) -> TrueAlphaDetectionCanaryResult:
    workspace.mkdir(parents=True, exist_ok=True)
    fixture_id = _required_text(fixture, "fixture_id")
    strength = _required_text(fixture, "strength")
    expected_detection = _required_bool(fixture, "expected_detection")
    threshold = _required_number(fixture, "detection_threshold_abs_pearson_ic")
    declared_snr = _required_number(fixture, "declared_signal_to_noise")
    floor_snr = _required_number(fixture, "declared_detectable_floor_signal_to_noise")
    study_spec = _detection_study_spec(fixture)
    summary = _diagnostic_summary(fixture, workspace=workspace)
    measured = abs(_pearson_ic(summary))
    detected = measured >= threshold
    outcome = DETECTED if detected else NOT_DETECTED
    diagnostics_status = _diagnostics_status(summary)
    trial = _detection_trial_record(
        study_spec,
        fixture=fixture,
        summary=summary,
        detected=detected,
        measured_abs_pearson_ic=measured,
    )
    evidence_bundle = _detection_evidence_bundle(
        study_spec,
        trial,
        fixture=fixture,
        summary=summary,
        detected=detected,
        measured_abs_pearson_ic=measured,
        diagnostics_status=diagnostics_status,
    )
    validate_evidence_ready_gate(evidence_bundle)

    trial_ledger_path = _trial_ledger_file(workspace, (trial,))
    variant_ledger_path = _variant_ledger_file(workspace)
    sealed_holdout_path = _sealed_holdout_registry_file(
        workspace,
        fixture_id=fixture_id,
        family="true_alpha_detection_synthetic_fixture",
    )
    validate_variant_and_family_budget(
        study_spec,
        trial_ledger_records=(trial,),
        family_id=FAMILY_ID,
        variant_ledger_path=variant_ledger_path,
        created_at=CREATED_AT,
    )
    transition = validate_governance_transition(
        PromotionLifecycleState.DIAGNOSTICS_RUN,
        PromotionLifecycleState.EVIDENCE_READY,
        PromotionGateContext(
            evidence_bundle=evidence_bundle,
            study_spec=study_spec,
            trial_ledger_records=(trial,),
            trial_ledger_path=trial_ledger_path,
            family_id=FAMILY_ID,
            variant_ledger_path=variant_ledger_path,
            sealed_holdout_registry_path=sealed_holdout_path,
            require_sealed_holdout=True,
        ),
    )
    return TrueAlphaDetectionCanaryResult(
        fixture_id=fixture_id,
        strength=strength,
        expected_detection=expected_detection,
        detected=detected,
        detection_outcome=outcome,
        diagnostic_name=DETECTION_DIAGNOSTIC,
        measured_abs_pearson_ic=round(measured, 6),
        detection_threshold_abs_pearson_ic=threshold,
        declared_signal_to_noise=declared_snr,
        declared_detectable_floor_signal_to_noise=floor_snr,
        promotion_outcome=transition.next_state.value,
        evidence_transition=f"{transition.previous_state.value}->{transition.next_state.value}",
        diagnostics_status=diagnostics_status,
        sample_count=summary.sample_size,
        evidence_bundle_id=evidence_bundle.evidence_bundle_id,
        trial_id=trial.trial_id,
        study_spec_id=study_spec.study_spec_id,
    )


def _run_planted_fake_alpha_clean_twin_canary(
    fixture: Mapping[str, Any],
    workspace: Path,
) -> PlantedFakeAlphaCleanTwinCanaryResult:
    workspace.mkdir(parents=True, exist_ok=True)
    fixture_id = _required_text(fixture, "fixture_id")
    if _fixture_has_lookahead_contamination(fixture):
        msg = "clean twin fixture must not contain future-bar contamination"
        raise ValueError(msg)
    study_spec = _clean_twin_study_spec(fixture)
    trial = _clean_twin_trial_record(study_spec, fixture_id=fixture_id)
    evidence_bundle = _clean_twin_evidence_bundle(study_spec, trial)
    validate_evidence_ready_gate(evidence_bundle)

    trial_ledger_path = _trial_ledger_file(workspace, (trial,))
    variant_ledger_path = _variant_ledger_file(workspace)
    sealed_holdout_path = _sealed_holdout_registry_file(
        workspace,
        fixture_id=fixture_id,
        family="planted_fake_alpha_clean_twin_synthetic_fixture",
    )
    validate_variant_and_family_budget(
        study_spec,
        trial_ledger_records=(trial,),
        family_id=CLEAN_TWIN_FAMILY_ID,
        variant_ledger_path=variant_ledger_path,
        created_at=CREATED_AT,
    )
    transition = validate_governance_transition(
        PromotionLifecycleState.DIAGNOSTICS_RUN,
        PromotionLifecycleState.EVIDENCE_READY,
        PromotionGateContext(
            evidence_bundle=evidence_bundle,
            study_spec=study_spec,
            trial_ledger_records=(trial,),
            trial_ledger_path=trial_ledger_path,
            family_id=CLEAN_TWIN_FAMILY_ID,
            variant_ledger_path=variant_ledger_path,
            sealed_holdout_registry_path=sealed_holdout_path,
            require_sealed_holdout=True,
        ),
    )
    return PlantedFakeAlphaCleanTwinCanaryResult(
        fixture_id=fixture_id,
        promotion_outcome=transition.next_state.value,
        evidence_transition=f"{transition.previous_state.value}->{transition.next_state.value}",
        blocked_issue_code="none",
        evidence_bundle_id=evidence_bundle.evidence_bundle_id,
        trial_id=trial.trial_id,
        study_spec_id=study_spec.study_spec_id,
    )


def _diagnostic_summary(fixture: Mapping[str, Any], *, workspace: Path) -> DiagnosticSummary:
    fixture_id = _required_text(fixture, "fixture_id")
    rows_dir = workspace / fixture_id / "inputs"
    rows_dir.mkdir(parents=True, exist_ok=True)
    factor_path = rows_dir / "factor_values.jsonl"
    label_path = rows_dir / "labels.jsonl"
    factor_rows, label_rows = _factor_and_label_rows(fixture)
    _write_jsonl(factor_path, factor_rows)
    _write_jsonl(label_path, label_rows)
    sample_count = _required_int(fixture, "sample_count")
    config = StudyConfig.from_mapping(
        {
            "study_id": f"{fixture_id}-diagnostics",
            "factor_id": _required_text(fixture, "feature_id"),
            "factor_version": "synthetic:true-alpha-detection:v1",
            "label_id": _required_text(fixture, "label_id"),
            "label_version": "synthetic:true-alpha-detection-label:v1",
            "data_version": "synthetic:true-alpha-detection-data:v1",
            "factor_values_path": factor_path.as_posix(),
            "labels_path": label_path.as_posix(),
            "horizon_seconds": 60,
            "sample_size_thresholds": {
                "min_total": sample_count,
                "min_bucket": 1,
                "min_event": 1,
                "max_missing_label_rate": 0.0,
                "max_missing_factor_rate": 0.0,
            },
            "diagnostic_types": ["directional"],
            "bucket_count": 2,
        }
    )
    return compute_diagnostic_summary(config, run_id=f"{fixture_id}-diagnostics")


def _factor_and_label_rows(
    fixture: Mapping[str, Any],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    fixture_id = _required_text(fixture, "fixture_id")
    feature_id = _required_text(fixture, "feature_id")
    label_id = _required_text(fixture, "label_id")
    feature_values = _number_sequence(fixture, "feature_values")
    noise_values = _number_sequence(fixture, "label_noise_values")
    sample_count = _required_int(fixture, "sample_count")
    coefficient = _required_number(fixture, "label_signal_coefficient")
    if len(feature_values) != len(noise_values) or len(feature_values) != sample_count:
        msg = "feature_values, label_noise_values, and sample_count must agree"
        raise ValueError(msg)

    factor_rows: list[dict[str, object]] = []
    label_rows: list[dict[str, object]] = []
    for index, (feature_value, noise_value) in enumerate(zip(feature_values, noise_values, strict=True)):
        event_ts = datetime(2026, 1, 2, 14, 30 + index, tzinfo=UTC)
        horizon_end = event_ts + timedelta(seconds=60)
        session_id = "SYNTH:2026-01-02:regular"
        label_value = coefficient * feature_value + noise_value
        factor_rows.append(
            {
                "factor_id": feature_id,
                "factor_version": "synthetic:true-alpha-detection:v1",
                "instrument_id": "SYNTH",
                "event_ts": _text(event_ts),
                "available_ts": _text(event_ts + timedelta(seconds=5)),
                "session_id": session_id,
                "bar_index": index,
                "value": feature_value,
                "normalized_value": feature_value,
                "quality_flags": ["synthetic", "point_in_time_clean"],
                "data_version": "synthetic:true-alpha-detection-data:v1",
                "compute_version": "synthetic-canary-v1",
            }
        )
        label_rows.append(
            {
                "label_id": label_id,
                "instrument_id": "SYNTH",
                "event_ts": _text(event_ts),
                "horizon": 60,
                "label_type": "forward_return_1m",
                "value": round(label_value, 10),
                "path_metadata": {
                    "fixture_id": fixture_id,
                    "horizon_end_ts": _text(horizon_end),
                    "label_version": "synthetic:true-alpha-detection-label:v1",
                    "observed_future_bars": 1,
                    "required_future_bars": 1,
                    "session_id": session_id,
                },
                "data_version": "synthetic:true-alpha-detection-data:v1",
                "label_available_ts": _text(horizon_end + timedelta(seconds=5)),
            }
        )
    return factor_rows, label_rows


def _detection_study_spec(fixture: Mapping[str, Any]) -> StudySpec:
    fixture_id = _required_text(fixture, "fixture_id")
    alpha_spec_id = generate_governance_id(
        GovernanceIdKind.ALPHA_SPEC,
        {"fixture_id": fixture_id, "canary": "true_alpha_detection"},
    )
    label_spec_id = generate_governance_id(
        GovernanceIdKind.LABEL_SPEC,
        {"fixture_id": fixture_id, "label": _required_text(fixture, "label_id")},
    )
    return create_study_spec(
        alpha_spec_id=alpha_spec_id,
        label_spec_id=label_spec_id,
        dataset_scope={
            "fixture_id": fixture_id,
            "real_market_data": False,
            "source": "tiny synthetic point-in-time planted-signal fixture",
            "time_range": "2026-01-02 synthetic minute rows",
        },
        split_protocol={
            "train": "synthetic rows 0-3",
            "validation": "synthetic rows 4-7",
            "locked_test": "synthetic rows 8-11 remain sealed",
        },
        metrics=[DETECTION_DIAGNOSTIC, "detection_outcome"],
        cost_assumptions={
            "commission": "not applicable to synthetic detection canary",
            "slippage": "not applicable to synthetic detection canary",
        },
        variant_budget=1,
        locked_test_policy={
            "contamination_handling": "any locked-test contamination blocks promotion",
            "locked_test_access": "no locked-test evaluation is authorized",
        },
        negative_controls=list(REQUIRED_NEGATIVE_CONTROL_TYPES),
        stopping_rules=["stop when strong fixture detection or weak fixture no-detection regresses"],
    )


def _clean_twin_study_spec(fixture: Mapping[str, Any]) -> StudySpec:
    fixture_id = _required_text(fixture, "fixture_id")
    alpha_spec_id = generate_governance_id(
        GovernanceIdKind.ALPHA_SPEC,
        {"fixture_id": fixture_id, "canary": "planted_fake_alpha_clean_twin"},
    )
    label_spec_id = generate_governance_id(
        GovernanceIdKind.LABEL_SPEC,
        {"fixture_id": fixture_id, "label": "current_bar_noise_only"},
    )
    return create_study_spec(
        alpha_spec_id=alpha_spec_id,
        label_spec_id=label_spec_id,
        dataset_scope={
            "fixture_id": fixture_id,
            "real_market_data": False,
            "source": "tiny synthetic planted-fake-alpha clean-twin metadata",
            "time_range": "2026-01-02 through 2026-01-05 synthetic bars",
        },
        split_protocol={
            "train": "first synthetic bars",
            "validation": "middle synthetic bars",
            "locked_test": "final synthetic bars remain sealed",
        },
        metrics=["clean_twin_gate_outcome"],
        cost_assumptions={
            "commission": "not applicable to synthetic clean-twin canary",
            "slippage": "not applicable to synthetic clean-twin canary",
        },
        variant_budget=1,
        locked_test_policy={
            "contamination_handling": "any future-bar label source blocks promotion",
            "locked_test_access": "no locked-test evaluation is authorized",
        },
        negative_controls=list(REQUIRED_NEGATIVE_CONTROL_TYPES),
        stopping_rules=["stop if clean twin is falsely blocked"],
    )


def _detection_trial_record(
    study_spec: StudySpec,
    *,
    fixture: Mapping[str, Any],
    summary: DiagnosticSummary,
    detected: bool,
    measured_abs_pearson_ic: float,
) -> TrialLedgerRecord:
    return create_trial_ledger_record(
        alpha_spec_id=study_spec.alpha_spec_id,
        study_spec_id=study_spec.study_spec_id,
        run_id=summary.run_id,
        variant_id=f"true-alpha-detection-{_required_text(fixture, 'strength')}",
        status=TrialStatus.COMPLETED,
        parameters={
            "declared_detectable_floor_signal_to_noise": _required_number(
                fixture, "declared_detectable_floor_signal_to_noise"
            ),
            "declared_signal_to_noise": _required_number(fixture, "declared_signal_to_noise"),
            "detection_threshold_abs_pearson_ic": _required_number(
                fixture, "detection_threshold_abs_pearson_ic"
            ),
            "expected_detection": _required_bool(fixture, "expected_detection"),
            "fixture_id": _required_text(fixture, "fixture_id"),
            "strength": _required_text(fixture, "strength"),
        },
        metrics_summary={
            "detected": detected,
            "diagnostic": DETECTION_DIAGNOSTIC,
            "diagnostics_status": _diagnostics_status(summary),
            "measured_abs_pearson_ic": round(measured_abs_pearson_ic, 6),
            "sample_size": summary.sample_size,
            "score_values_recorded": False,
        },
        failure_reason=None,
        oos_touched_flag=False,
        locked_test_contamination_flag=False,
        code_hash=CODE_HASH,
        config_hash=CONFIG_HASH,
    )


def _clean_twin_trial_record(
    study_spec: StudySpec,
    *,
    fixture_id: str,
) -> TrialLedgerRecord:
    return create_trial_ledger_record(
        alpha_spec_id=study_spec.alpha_spec_id,
        study_spec_id=study_spec.study_spec_id,
        run_id=f"{fixture_id}-diagnostics",
        variant_id="planted-fake-alpha-clean-twin-variant",
        status=TrialStatus.COMPLETED,
        parameters={
            "declared_signal": "not_planted",
            "fixture_id": fixture_id,
            "label_construction": "label_t_uses_current_bar_noise_only",
        },
        metrics_summary={
            "diagnostics_status": "PASS",
            "gate_outcome": "clean_twin_expected_to_pass",
            "score_values_recorded": False,
        },
        failure_reason=None,
        oos_touched_flag=False,
        locked_test_contamination_flag=False,
        code_hash=CODE_HASH,
        config_hash=CONFIG_HASH,
    )


def _detection_evidence_bundle(
    study_spec: StudySpec,
    trial: TrialLedgerRecord,
    *,
    fixture: Mapping[str, Any],
    summary: DiagnosticSummary,
    detected: bool,
    measured_abs_pearson_ic: float,
    diagnostics_status: str,
) -> EvidenceBundle:
    fixture_id = _required_text(fixture, "fixture_id")
    detection_outcome = DETECTED if detected else NOT_DETECTED
    return create_evidence_bundle(
        alpha_spec_id=study_spec.alpha_spec_id,
        study_spec_id=study_spec.study_spec_id,
        trial_ids=[trial.trial_id],
        data_version=summary.data_version,
        factor_version=summary.factor_version,
        label_version=summary.label_version,
        code_hash=CODE_HASH,
        config_hash=CONFIG_HASH,
        diagnostics_summary={
            "declared_detectable_floor_signal_to_noise": _required_number(
                fixture, "declared_detectable_floor_signal_to_noise"
            ),
            "declared_signal_to_noise": _required_number(fixture, "declared_signal_to_noise"),
            "detected": detected,
            "detection_outcome": detection_outcome,
            "detection_threshold_abs_pearson_ic": _required_number(
                fixture, "detection_threshold_abs_pearson_ic"
            ),
            "diagnostics_run_ref": summary.run_id,
            "diagnostics_status": diagnostics_status,
            "measured_abs_pearson_ic": round(measured_abs_pearson_ic, 6),
            "metric_set": "synthetic point-in-time detection canary",
            "sample_size": summary.sample_size,
            "score_values_recorded": False,
        },
        negative_control_results=_required_pass_results(study_spec.study_spec_id),
        limitations=[
            "Synthetic canary metadata only.",
            "This is not evidence of alpha validity, profitability, tradability, or production readiness.",
        ],
        artifact_manifest=[
            {
                "logical_name": "true alpha detection fixture",
                "role": "synthetic_canary_fixture",
                "reference": str(DEFAULT_TRUE_ALPHA_DETECTION_FIXTURE_PATHS[_strength_key(_required_text(fixture, "strength"))]),
                "content_hash": hash_config({"fixture_id": fixture_id}),
            }
        ],
        reviewer_verdict_reference=generate_governance_id(
            GovernanceIdKind.REVIEWER_VERDICT,
            {"fixture": study_spec.study_spec_id, "status": "not_reviewed_canary"},
        ),
    )


def _clean_twin_evidence_bundle(
    study_spec: StudySpec,
    trial: TrialLedgerRecord,
) -> EvidenceBundle:
    return create_evidence_bundle(
        alpha_spec_id=study_spec.alpha_spec_id,
        study_spec_id=study_spec.study_spec_id,
        trial_ids=[trial.trial_id],
        data_version="synthetic-planted-fake-alpha-clean-twin-data-v1",
        factor_version="synthetic-planted-fake-alpha-clean-twin-factor-v1",
        label_version="synthetic-planted-fake-alpha-clean-twin-label-v1",
        code_hash=CODE_HASH,
        config_hash=CONFIG_HASH,
        diagnostics_summary={
            "diagnostics_run_ref": trial.run_id,
            "diagnostics_status": "PASS",
            "metric_set": "clean twin gate outcome only",
            "score_values_recorded": False,
        },
        negative_control_results=_required_pass_results(study_spec.study_spec_id),
        limitations=[
            "Synthetic canary metadata only.",
            "This is not evidence of alpha validity, profitability, tradability, or production readiness.",
        ],
        artifact_manifest=[
            {
                "logical_name": "planted fake alpha clean twin fixture",
                "role": "synthetic_canary_fixture",
                "reference": str(DEFAULT_PLANTED_FAKE_ALPHA_CLEAN_TWIN_FIXTURE_PATH),
                "content_hash": hash_config({"fixture": "planted_fake_alpha_clean_twin"}),
            }
        ],
        reviewer_verdict_reference=generate_governance_id(
            GovernanceIdKind.REVIEWER_VERDICT,
            {"fixture": study_spec.study_spec_id, "status": "not_reviewed_canary"},
        ),
    )


def _required_pass_results(study_spec_id: str) -> list[dict[str, object]]:
    return [
        create_negative_control_result(
            canary_type=control_type,
            expected_failure=expected_failure_for_canary_type(control_type),
            observed_result=expected_failure_for_canary_type(control_type),
            pass_fail=NegativeControlPassFail.PASS,
            related_study_or_evidence=study_spec_id,
            notes=(
                "Synthetic true-signal detection evidence bundle carries the "
                f"required {control_type} negative-control PASS record."
            ),
        ).to_dict()
        for control_type in REQUIRED_NEGATIVE_CONTROL_TYPES
    ]


def _pearson_ic(summary: DiagnosticSummary) -> float:
    directional = summary.diagnostics.get("directional")
    if not isinstance(directional, Mapping):
        msg = "directional diagnostics are required for detection canary"
        raise ValueError(msg)
    value = directional.get("pearson_ic")
    if isinstance(value, Mapping):
        value = value.get("ic")
    if not isinstance(value, int | float) or not math.isfinite(float(value)):
        msg = "directional.pearson_ic must be a finite number"
        raise ValueError(msg)
    return float(value)


def _diagnostics_status(summary: DiagnosticSummary) -> str:
    return "INCONCLUSIVE" if summary.warnings else "PASS"


def _fixture_has_lookahead_contamination(fixture: Mapping[str, Any]) -> bool:
    bars = _required_sequence(fixture, "bars")
    labels = _required_sequence(fixture, "labels")
    bar_index: dict[str, int] = {}
    for index, bar in enumerate(bars):
        mapping = _require_mapping(bar, field=f"bars[{index}]")
        bar_index[_required_text(mapping, "bar_id")] = index

    for index, label in enumerate(labels):
        mapping = _require_mapping(label, field=f"labels[{index}]")
        label_bar_id = _required_text(mapping, "bar_id")
        source_bar_id = _required_text(mapping, "source_bar_id")
        lookahead_k = _required_int(mapping, "lookahead_k")
        if label_bar_id not in bar_index or source_bar_id not in bar_index:
            return True
        if bar_index[source_bar_id] - bar_index[label_bar_id] != lookahead_k:
            return True
        if lookahead_k > 0:
            return True
    return False


def _trial_ledger_file(workspace: Path, records: tuple[TrialLedgerRecord, ...]) -> Path:
    path = workspace / "trial-ledger.json"
    path.write_text(
        json.dumps(
            {
                "records": [record.to_dict() for record in records],
                "schema": "synthetic-canary-trial-ledger-v1",
            },
            sort_keys=True,
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def _variant_ledger_file(workspace: Path) -> Path:
    path = workspace / "variant-ledger.jsonl"
    path.write_text("", encoding="utf-8")
    return path


def _sealed_holdout_registry_file(workspace: Path, *, fixture_id: str, family: str) -> Path:
    path = workspace / "sealed-holdout.json"
    window = create_sealed_holdout_window(
        partition_spec={
            "dataset_family": family,
            "fixture_id": fixture_id,
            "symbols": ["SYNTH"],
            "split_role": "locked_test",
        },
        start_date="2026-01-02",
        end_date="2026-01-02",
        status=SealedHoldoutStatus.SEALED,
        declared_at=CREATED_AT,
        sealed_by="governance-canary",
        provenance={"phase": "P040500_TRUE_ALPHA_DETECTION_CANARY", "fixture": fixture_id},
    )
    path.write_text(json.dumps(window.to_dict(), sort_keys=True, indent=2), encoding="utf-8")
    return path


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "evals" / "canaries").is_dir():
            return parent
    msg = "could not locate repository root containing evals/canaries"
    raise FileNotFoundError(msg)


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(dict(row), sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _strength_key(value: str) -> str:
    key = value.strip().lower()
    if key not in DEFAULT_TRUE_ALPHA_DETECTION_FIXTURE_PATHS:
        supported = ", ".join(DEFAULT_TRUE_ALPHA_DETECTION_FIXTURE_PATHS)
        msg = f"unsupported detection fixture strength {value!r}; supported: {supported}"
        raise ValueError(msg)
    return key


def _required_sequence(fixture: Mapping[str, Any], field: str) -> Sequence[Any]:
    value = fixture.get(field)
    if isinstance(value, str) or not isinstance(value, Sequence):
        msg = f"true-alpha detection fixture field {field!r} must be a sequence"
        raise ValueError(msg)
    return value


def _number_sequence(fixture: Mapping[str, Any], field: str) -> tuple[float, ...]:
    values = _required_sequence(fixture, field)
    output: list[float] = []
    for index, value in enumerate(values):
        if isinstance(value, bool) or not isinstance(value, int | float):
            msg = f"true-alpha detection fixture field {field}[{index}] must be numeric"
            raise ValueError(msg)
        output.append(float(value))
    return tuple(output)


def _require_mapping(value: Any, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        msg = f"true-alpha detection fixture field {field!r} must be a mapping"
        raise ValueError(msg)
    return cast(Mapping[str, Any], value)


def _required_text(fixture: Mapping[str, Any], field: str) -> str:
    value = fixture.get(field)
    if not isinstance(value, str) or not value.strip():
        msg = f"true-alpha detection fixture field {field!r} must be a non-empty string"
        raise ValueError(msg)
    return value.strip()


def _required_int(fixture: Mapping[str, Any], field: str) -> int:
    value = fixture.get(field)
    if type(value) is not int:
        msg = f"true-alpha detection fixture field {field!r} must be an integer"
        raise ValueError(msg)
    return value


def _required_bool(fixture: Mapping[str, Any], field: str) -> bool:
    value = fixture.get(field)
    if type(value) is not bool:
        msg = f"true-alpha detection fixture field {field!r} must be a boolean"
        raise ValueError(msg)
    return value


def _required_number(fixture: Mapping[str, Any], field: str) -> float:
    value = fixture.get(field)
    if isinstance(value, bool) or not isinstance(value, int | float):
        msg = f"true-alpha detection fixture field {field!r} must be numeric"
        raise ValueError(msg)
    return float(value)


def _text(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


__all__ = [
    "DEFAULT_PLANTED_FAKE_ALPHA_CLEAN_TWIN_FIXTURE_PATH",
    "DEFAULT_TRUE_ALPHA_DETECTION_FIXTURE_PATHS",
    "DETECTED",
    "DETECTION_DIAGNOSTIC",
    "NOT_DETECTED",
    "PlantedFakeAlphaCleanTwinCanaryResult",
    "TrueAlphaDetectionCanaryResult",
    "load_default_planted_fake_alpha_clean_twin_fixture",
    "load_default_true_alpha_detection_fixture",
    "run_planted_fake_alpha_clean_twin_canary",
    "run_true_alpha_detection_canary",
]
