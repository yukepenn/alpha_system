"""End-to-end planted-fake-alpha canary for the governance evidence gate."""

from __future__ import annotations

import json
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from alpha_system.governance.canaries.catalog import (
    REQUIRED_NEGATIVE_CONTROL_TYPES,
    NegativeControlType,
    expected_failure_for_canary_type,
)
from alpha_system.governance.canaries.negative_control_result import (
    NegativeControlPassFail,
    NegativeControlResult,
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
from alpha_system.governance.rejected_idea import (
    RejectedIdeaReasonCategory,
    create_rejected_idea_record,
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
from alpha_system.governance.validation import GovernanceValidationError
from alpha_system.governance.variant_ledger import validate_variant_and_family_budget

DEFAULT_PLANTED_FAKE_ALPHA_FIXTURE_PATH = Path(
    "evals/canaries/planted_fake_alpha/synthetic_fixture.json"
)
EXPECTED_BLOCK_CODE = "locked_test_contamination_blocks_evidence_ready"
CODE_HASH = "d" * 64
CONFIG_HASH = "e" * 64
MANIFEST_HASH = "f" * 64
CREATED_AT = "2026-06-11T22:36:43Z"
FAMILY_ID = "family-planted-fake-alpha-canary"


@dataclass(frozen=True, slots=True)
class PlantedFakeAlphaStudyCanaryResult:
    """Value-free result summary for the planted-fake-alpha canary."""

    negative_control_result: NegativeControlResult
    rejected: bool
    promotion_outcome: str
    blocked_gate: str
    blocked_issue_code: str
    contamination_mechanism: str
    evidence_bundle_id: str
    trial_id: str
    study_spec_id: str

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible value-free result summary."""

        return {
            "negative_control_result": self.negative_control_result.to_dict(),
            "rejected": self.rejected,
            "promotion_outcome": self.promotion_outcome,
            "blocked_gate": self.blocked_gate,
            "blocked_issue_code": self.blocked_issue_code,
            "contamination_mechanism": self.contamination_mechanism,
            "evidence_bundle_id": self.evidence_bundle_id,
            "trial_id": self.trial_id,
            "study_spec_id": self.study_spec_id,
        }


def load_default_planted_fake_alpha_fixture() -> Mapping[str, Any]:
    """Load the tiny synthetic planted-fake-alpha fixture."""

    fixture_path = _repo_root() / DEFAULT_PLANTED_FAKE_ALPHA_FIXTURE_PATH
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        msg = f"planted-fake-alpha fixture root must be a mapping: {fixture_path}"
        raise ValueError(msg)
    return cast(Mapping[str, Any], payload)


def run_planted_fake_alpha_canary(
    fixture: Mapping[str, Any] | None = None,
    *,
    workspace: str | Path | None = None,
) -> PlantedFakeAlphaStudyCanaryResult:
    """Run the planted lookahead study through the real evidence/promotion gates."""

    active_fixture = fixture or load_default_planted_fake_alpha_fixture()
    if workspace is None:
        with tempfile.TemporaryDirectory(prefix="planted-fake-alpha-canary-") as raw_tmp:
            return _run_planted_fake_alpha_canary(active_fixture, Path(raw_tmp))
    return _run_planted_fake_alpha_canary(active_fixture, Path(workspace))


def _run_planted_fake_alpha_canary(
    fixture: Mapping[str, Any],
    workspace: Path,
) -> PlantedFakeAlphaStudyCanaryResult:
    workspace.mkdir(parents=True, exist_ok=True)
    fixture_id = _required_text(fixture, "fixture_id")
    contaminated = _fixture_has_lookahead_contamination(fixture)
    mechanism = _contamination_mechanism(fixture, contaminated=contaminated)
    study_spec = _study_spec(fixture)
    trial = _trial_record(study_spec, fixture_id=fixture_id, contaminated=contaminated)
    evidence_bundle = _evidence_bundle(study_spec, trial)
    validate_evidence_ready_gate(evidence_bundle)

    trial_ledger_path = _trial_ledger_file(workspace)
    variant_ledger_path = _variant_ledger_file(workspace)
    sealed_holdout_path = _sealed_holdout_registry_file(workspace)
    validate_variant_and_family_budget(
        study_spec,
        trial_ledger_records=(trial,),
        family_id=FAMILY_ID,
        variant_ledger_path=variant_ledger_path,
        created_at=CREATED_AT,
    )

    try:
        validate_governance_transition(
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
    except GovernanceValidationError as exc:
        issue_codes = tuple(issue.code for issue in exc.issues)
        if EXPECTED_BLOCK_CODE in issue_codes:
            rejection = create_rejected_idea_record(
                alpha_spec_id_or_hypothesis_id=study_spec.alpha_spec_id,
                reason_category=RejectedIdeaReasonCategory.LEAKAGE,
                evidence_references=[evidence_bundle.evidence_bundle_id, trial.trial_id],
                duplicate_links=[study_spec.study_spec_id],
                leakage_cost_weakness_notes=[
                    "Synthetic planted-fake-alpha labels use future bar information.",
                    "The EVIDENCE_READY transition blocked locked-test contamination.",
                ],
                reviewer="governance-canary:planted-fake-alpha",
                created_at=CREATED_AT,
            )
            validate_governance_transition(
                PromotionLifecycleState.DIAGNOSTICS_RUN,
                PromotionLifecycleState.REJECTED,
                PromotionGateContext(
                    rejected_idea_record=rejection,
                    rejection_reason=(
                        "Planted lookahead-contaminated synthetic study was rejected."
                    ),
                ),
            )
            return _result(
                study_spec=study_spec,
                trial=trial,
                evidence_bundle=evidence_bundle,
                rejected=True,
                promotion_outcome="REJECTED",
                blocked_gate="DIAGNOSTICS_RUN->EVIDENCE_READY",
                blocked_issue_code=EXPECTED_BLOCK_CODE,
                contamination_mechanism=mechanism,
            )
        return _result(
            study_spec=study_spec,
            trial=trial,
            evidence_bundle=evidence_bundle,
            rejected=False,
            promotion_outcome="UNEXPECTED_BLOCK",
            blocked_gate="DIAGNOSTICS_RUN->EVIDENCE_READY",
            blocked_issue_code=issue_codes[0] if issue_codes else "unknown_block",
            contamination_mechanism=mechanism,
        )

    return _result(
        study_spec=study_spec,
        trial=trial,
        evidence_bundle=evidence_bundle,
        rejected=False,
        promotion_outcome="SURVIVED",
        blocked_gate="none",
        blocked_issue_code="none",
        contamination_mechanism=mechanism,
    )


def _result(
    *,
    study_spec: StudySpec,
    trial: TrialLedgerRecord,
    evidence_bundle: EvidenceBundle,
    rejected: bool,
    promotion_outcome: str,
    blocked_gate: str,
    blocked_issue_code: str,
    contamination_mechanism: str,
) -> PlantedFakeAlphaStudyCanaryResult:
    expected_failure = expected_failure_for_canary_type(NegativeControlType.FUTURE_SHIFT)
    observed_result = (
        expected_failure
        if rejected and blocked_issue_code == EXPECTED_BLOCK_CODE
        else f"planted_fake_alpha_{promotion_outcome.lower()}"
    )
    return PlantedFakeAlphaStudyCanaryResult(
        negative_control_result=create_negative_control_result(
            canary_type=NegativeControlType.FUTURE_SHIFT,
            expected_failure=expected_failure,
            observed_result=observed_result,
            pass_fail=(
                NegativeControlPassFail.PASS
                if observed_result == expected_failure
                else NegativeControlPassFail.FAIL
            ),
            related_study_or_evidence=study_spec.study_spec_id,
            notes=(
                "PlantedFakeAlphaStudyCanary records the full-pipeline "
                f"outcome {promotion_outcome}; {contamination_mechanism}"
            ),
        ),
        rejected=rejected,
        promotion_outcome=promotion_outcome,
        blocked_gate=blocked_gate,
        blocked_issue_code=blocked_issue_code,
        contamination_mechanism=contamination_mechanism,
        evidence_bundle_id=evidence_bundle.evidence_bundle_id,
        trial_id=trial.trial_id,
        study_spec_id=study_spec.study_spec_id,
    )


def _study_spec(fixture: Mapping[str, Any]) -> StudySpec:
    fixture_id = _required_text(fixture, "fixture_id")
    alpha_spec_id = generate_governance_id(
        GovernanceIdKind.ALPHA_SPEC,
        {"fixture_id": fixture_id, "canary": "planted_fake_alpha"},
    )
    label_spec_id = generate_governance_id(
        GovernanceIdKind.LABEL_SPEC,
        {"fixture_id": fixture_id, "label": "future_bar_planted_label"},
    )
    return create_study_spec(
        alpha_spec_id=alpha_spec_id,
        label_spec_id=label_spec_id,
        dataset_scope={
            "source": "tiny synthetic planted-fake-alpha fixture metadata",
            "time_range": "2026-01-02 through 2026-01-08 synthetic bars",
            "real_market_data": False,
        },
        split_protocol={
            "train": "first synthetic bars",
            "validation": "middle synthetic bars",
            "locked_test": "final synthetic bars remain sealed",
        },
        metrics=["governance_rejection_outcome"],
        cost_assumptions={
            "commission": "synthetic nonzero placeholder for governance metadata",
            "slippage": "synthetic nonzero placeholder for governance metadata",
        },
        variant_budget=1,
        locked_test_policy={
            "contamination_handling": "any future-bar label source blocks promotion",
            "locked_test_access": "no locked-test evaluation is authorized",
        },
        negative_controls=list(REQUIRED_NEGATIVE_CONTROL_TYPES),
        stopping_rules=["stop when planted lookahead contamination is detected"],
    )


def _trial_record(
    study_spec: StudySpec,
    *,
    fixture_id: str,
    contaminated: bool,
) -> TrialLedgerRecord:
    return create_trial_ledger_record(
        alpha_spec_id=study_spec.alpha_spec_id,
        study_spec_id=study_spec.study_spec_id,
        run_id=f"{fixture_id}-diagnostics",
        variant_id="planted-fake-alpha-variant",
        status=TrialStatus.COMPLETED,
        parameters={
            "fixture_id": fixture_id,
            "label_construction": "label_t_uses_future_bar_t_plus_k",
        },
        metrics_summary={
            "diagnostics_status": "synthetic_canary_complete",
            "score_values_recorded": False,
        },
        failure_reason=None,
        oos_touched_flag=False,
        locked_test_contamination_flag=contaminated,
        code_hash=CODE_HASH,
        config_hash=CONFIG_HASH,
    )


def _evidence_bundle(study_spec: StudySpec, trial: TrialLedgerRecord) -> EvidenceBundle:
    return create_evidence_bundle(
        alpha_spec_id=study_spec.alpha_spec_id,
        study_spec_id=study_spec.study_spec_id,
        trial_ids=[trial.trial_id],
        data_version="synthetic-planted-fake-alpha-data-v1",
        factor_version="synthetic-planted-fake-alpha-factor-v1",
        label_version="synthetic-planted-fake-alpha-lookahead-label-v1",
        code_hash=CODE_HASH,
        config_hash=CONFIG_HASH,
        diagnostics_summary={
            "diagnostics_run_ref": trial.run_id,
            "metric_set": "governance rejection outcome only",
            "score_values_recorded": False,
        },
        negative_control_results=_required_pass_results(study_spec.study_spec_id),
        limitations=[
            "Synthetic canary metadata only.",
            "No alpha, profitability, tradability, or production claim is made.",
        ],
        artifact_manifest=[
            {
                "logical_name": "planted fake alpha fixture",
                "role": "synthetic_canary_fixture",
                "reference": str(DEFAULT_PLANTED_FAKE_ALPHA_FIXTURE_PATH),
                "content_hash": MANIFEST_HASH,
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
                "Synthetic planted-fake-alpha evidence bundle carries the "
                f"required {control_type} negative-control PASS record."
            ),
        ).to_dict()
        for control_type in REQUIRED_NEGATIVE_CONTROL_TYPES
    ]


def _fixture_has_lookahead_contamination(fixture: Mapping[str, Any]) -> bool:
    bars = _required_sequence(fixture, "bars")
    labels = _required_sequence(fixture, "labels")
    if not labels:
        return False
    bar_index: dict[str, int] = {}
    for index, bar in enumerate(bars):
        mapping = _require_mapping(bar, field=f"bars[{index}]")
        bar_index[_required_text(mapping, "bar_id")] = index

    for index, label in enumerate(labels):
        mapping = _require_mapping(label, field=f"labels[{index}]")
        label_bar_id = _required_text(mapping, "bar_id")
        source_bar_id = _required_text(mapping, "source_bar_id")
        lookahead_k = _required_int(mapping, "lookahead_k")
        construction = _required_text(mapping, "construction")
        if lookahead_k < 1 or "future" not in construction.lower():
            return False
        if label_bar_id not in bar_index or source_bar_id not in bar_index:
            return False
        if bar_index[source_bar_id] - bar_index[label_bar_id] != lookahead_k:
            return False
    return True


def _contamination_mechanism(
    fixture: Mapping[str, Any],
    *,
    contaminated: bool,
) -> str:
    lookahead_k = _required_int(fixture, "lookahead_k")
    if contaminated:
        return f"label at bar t is computed from bar t+{lookahead_k} information."
    return "fixture does not preserve the required future-bar label contamination."


def _trial_ledger_file(workspace: Path) -> Path:
    path = workspace / "trial-ledger.json"
    path.write_text(
        json.dumps({"schema": "synthetic-trial-ledger-v1", "records": []}),
        encoding="utf-8",
    )
    return path


def _variant_ledger_file(workspace: Path) -> Path:
    path = workspace / "variant-ledger.jsonl"
    path.write_text("", encoding="utf-8")
    return path


def _sealed_holdout_registry_file(workspace: Path) -> Path:
    path = workspace / "sealed-holdout.json"
    window = create_sealed_holdout_window(
        partition_spec={
            "dataset_family": "planted_fake_alpha_synthetic_fixture",
            "symbols": ["SYNTH"],
            "split_role": "locked_test",
        },
        start_date="2026-01-02",
        end_date="2026-01-08",
        status=SealedHoldoutStatus.SEALED,
        declared_at=CREATED_AT,
        sealed_by="governance-canary",
        provenance={"phase": "RIGOR-P04", "fixture": "planted_fake_alpha"},
    )
    path.write_text(json.dumps(window.to_dict(), sort_keys=True, indent=2), encoding="utf-8")
    return path


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "evals" / "canaries").is_dir():
            return parent
    msg = "could not locate repository root containing evals/canaries"
    raise FileNotFoundError(msg)


def _required_sequence(fixture: Mapping[str, Any], field: str) -> Sequence[Any]:
    value = fixture.get(field)
    if isinstance(value, str) or not isinstance(value, Sequence):
        msg = f"planted-fake-alpha fixture field {field!r} must be a sequence"
        raise ValueError(msg)
    return value


def _require_mapping(value: Any, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        msg = f"planted-fake-alpha fixture field {field!r} must be a mapping"
        raise ValueError(msg)
    return cast(Mapping[str, Any], value)


def _required_text(fixture: Mapping[str, Any], field: str) -> str:
    value = fixture.get(field)
    if not isinstance(value, str) or not value.strip():
        msg = f"planted-fake-alpha fixture field {field!r} must be a non-empty string"
        raise ValueError(msg)
    return value.strip()


def _required_int(fixture: Mapping[str, Any], field: str) -> int:
    value = fixture.get(field)
    if type(value) is not int:
        msg = f"planted-fake-alpha fixture field {field!r} must be an integer"
        raise ValueError(msg)
    return value


__all__ = [
    "DEFAULT_PLANTED_FAKE_ALPHA_FIXTURE_PATH",
    "EXPECTED_BLOCK_CODE",
    "PlantedFakeAlphaStudyCanaryResult",
    "load_default_planted_fake_alpha_fixture",
    "run_planted_fake_alpha_canary",
]
