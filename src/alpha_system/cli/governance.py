"""Governance CLI commands."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast

from alpha_system.governance.alpha_spec import AlphaSpec, validate_alpha_spec
from alpha_system.governance.canaries.negative_control_result import (
    validate_negative_control_result,
)
from alpha_system.governance.evidence_bundle import EvidenceBundle, validate_evidence_bundle
from alpha_system.governance.feature_request import validate_feature_request
from alpha_system.governance.hypothesis_card import (
    HypothesisCard,
    validate_hypothesis_card,
)
from alpha_system.governance.ids import (
    GovernanceIdError,
    GovernanceIdKind,
    resolve_governance_id_kind,
)
from alpha_system.governance.label_spec import validate_label_spec
from alpha_system.governance.promotion import (
    PromotionDecision,
    PromotionLifecycleState,
    validate_promotion_decision,
)
from alpha_system.governance.promotion_gate import (
    PromotionGateContext,
    validate_governance_transition,
)
from alpha_system.governance.registry import GovernanceRegistry, GovernanceRegistryEntry
from alpha_system.governance.rejected_idea import validate_rejected_idea_record
from alpha_system.governance.requeue import (
    scan_requeue_candidates,
    write_requeue_records,
)
from alpha_system.governance.reviewer_verdict import ReviewerVerdict, validate_reviewer_verdict
from alpha_system.governance.serialization import (
    GovernanceSerializationError,
    JsonValue,
    deserialize,
)
from alpha_system.governance.study_spec import StudySpec, validate_study_spec
from alpha_system.governance.trial_ledger import TrialLedgerRecord, validate_trial_ledger_record
from alpha_system.governance.validation import (
    GovernanceValidationError,
    ValidationIssue,
    require_mapping,
)
from alpha_system.governance.variant_ledger import (
    VariantLedger,
    validate_budget_amendment_record,
)


class _ValidatedGovernanceRecord(Protocol):
    """Structural type shared by governance records returned from validators."""

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a strict JSON-compatible mapping."""


type _ObjectValidator = Callable[[Mapping[str, Any]], _ValidatedGovernanceRecord]


@dataclass(frozen=True, slots=True)
class _ObjectAdapter:
    kind: GovernanceIdKind
    id_attribute: str
    validate: _ObjectValidator


@dataclass(frozen=True, slots=True)
class ValidatedGovernanceObject:
    """Summary of a fail-closed governance object validation."""

    object_kind: str
    object_id: str
    record: _ValidatedGovernanceRecord

    def to_dict(self) -> dict[str, object]:
        return {
            "object_kind": self.object_kind,
            "object_id": self.object_id,
            "payload": self.record.to_dict(),
        }


_OBJECT_ADAPTERS: Mapping[str, _ObjectAdapter] = {
    GovernanceIdKind.HYPOTHESIS_CARD.value: _ObjectAdapter(
        GovernanceIdKind.HYPOTHESIS_CARD,
        "hypothesis_id",
        validate_hypothesis_card,
    ),
    GovernanceIdKind.ALPHA_SPEC.value: _ObjectAdapter(
        GovernanceIdKind.ALPHA_SPEC,
        "alpha_spec_id",
        validate_alpha_spec,
    ),
    GovernanceIdKind.FEATURE_REQUEST.value: _ObjectAdapter(
        GovernanceIdKind.FEATURE_REQUEST,
        "feature_request_id",
        validate_feature_request,
    ),
    GovernanceIdKind.LABEL_SPEC.value: _ObjectAdapter(
        GovernanceIdKind.LABEL_SPEC,
        "label_spec_id",
        validate_label_spec,
    ),
    GovernanceIdKind.STUDY_SPEC.value: _ObjectAdapter(
        GovernanceIdKind.STUDY_SPEC,
        "study_spec_id",
        validate_study_spec,
    ),
    GovernanceIdKind.TRIAL_LEDGER_RECORD.value: _ObjectAdapter(
        GovernanceIdKind.TRIAL_LEDGER_RECORD,
        "trial_id",
        validate_trial_ledger_record,
    ),
    GovernanceIdKind.EVIDENCE_BUNDLE.value: _ObjectAdapter(
        GovernanceIdKind.EVIDENCE_BUNDLE,
        "evidence_bundle_id",
        validate_evidence_bundle,
    ),
    GovernanceIdKind.REJECTED_IDEA_RECORD.value: _ObjectAdapter(
        GovernanceIdKind.REJECTED_IDEA_RECORD,
        "rejected_id",
        validate_rejected_idea_record,
    ),
    GovernanceIdKind.PROMOTION_DECISION.value: _ObjectAdapter(
        GovernanceIdKind.PROMOTION_DECISION,
        "promotion_id",
        validate_promotion_decision,
    ),
    GovernanceIdKind.REVIEWER_VERDICT.value: _ObjectAdapter(
        GovernanceIdKind.REVIEWER_VERDICT,
        "reviewer_verdict_id",
        validate_reviewer_verdict,
    ),
    GovernanceIdKind.NEGATIVE_CONTROL_RESULT.value: _ObjectAdapter(
        GovernanceIdKind.NEGATIVE_CONTROL_RESULT,
        "canary_id",
        validate_negative_control_result,
    ),
}


def load_governance_mapping(path: str | Path, *, object_name: str) -> Mapping[str, Any]:
    """Load a JSON governance mapping through canonical fail-closed deserialization."""

    source = Path(path)
    value = deserialize(source.read_text(encoding="utf-8"))
    return cast(Mapping[str, Any], require_mapping(value, object_name=object_name))


def validate_governance_object_file(
    path: str | Path,
    object_kind: GovernanceIdKind | str,
) -> ValidatedGovernanceObject:
    """Validate one governance object file using the canonical object validator."""

    kind = _coerce_kind(object_kind)
    adapter = _adapter_for_kind(kind)
    payload = load_governance_mapping(path, object_name=adapter.kind.value)
    record = adapter.validate(payload)
    object_id = getattr(record, adapter.id_attribute)
    if not isinstance(object_id, str):
        raise GovernanceValidationError(
            ValidationIssue(
                field=adapter.id_attribute,
                code="invalid_governance_object_id",
                message="validated governance object did not expose a string ID",
                expected="string governance ID",
                actual=type(object_id).__name__,
            )
        )
    return ValidatedGovernanceObject(
        object_kind=adapter.kind.value,
        object_id=object_id,
        record=record,
    )


def validate_alpha_spec_files(
    alpha_spec_path: str | Path,
    hypothesis_card_path: str | Path,
) -> tuple[HypothesisCard, AlphaSpec]:
    """Validate an AlphaSpec with its referenced HypothesisCard through the gate."""

    hypothesis_payload = load_governance_mapping(
        hypothesis_card_path,
        object_name=GovernanceIdKind.HYPOTHESIS_CARD.value,
    )
    alpha_payload = load_governance_mapping(
        alpha_spec_path,
        object_name=GovernanceIdKind.ALPHA_SPEC.value,
    )
    hypothesis = validate_hypothesis_card(hypothesis_payload)
    alpha = validate_alpha_spec(alpha_payload)
    validate_governance_transition(
        "DRAFT",
        "REGISTERED",
        PromotionGateContext(hypothesis_card=hypothesis, alpha_spec=alpha),
    )
    return hypothesis, alpha


def governance_exception_payload(command: str, exc: BaseException) -> dict[str, object]:
    """Format fail-closed governance exceptions as deterministic JSON payloads."""

    base: dict[str, object] = {
        "command": command,
        "status": "rejected",
        "error_type": type(exc).__name__,
    }
    if isinstance(exc, GovernanceValidationError):
        base["issues"] = [issue.to_dict() for issue in exc.issues]
        return base
    if isinstance(exc, GovernanceSerializationError):
        base["issues"] = [exc.to_dict()]
        return base
    if isinstance(exc, GovernanceIdError):
        base["issues"] = [exc.issue.to_dict()]
        return base
    if isinstance(exc, OSError):
        base["issues"] = [
            {
                "field": "path",
                "code": "file_io_error",
                "message": str(exc),
                "expected": "readable local governance JSON file or registry path",
                "actual": type(exc).__name__,
            }
        ]
        return base
    base["issues"] = [
        {
            "field": "command",
            "code": "governance_command_error",
            "message": str(exc),
            "expected": "valid governance command inputs",
            "actual": type(exc).__name__,
        }
    ]
    return base


def run_validate_spec(args: argparse.Namespace) -> int:
    """Run ``alpha governance validate-spec``."""

    def _execute() -> dict[str, object]:
        hypothesis, alpha = validate_alpha_spec_files(
            args.alpha_spec,
            args.hypothesis_card,
        )
        return {
            "status": "ok",
            "command": "validate-spec",
            "alpha_spec_id": alpha.alpha_spec_id,
            "hypothesis_id": hypothesis.hypothesis_id,
            "validated_transition": "DRAFT->REGISTERED",
        }

    return _run_json_command("validate-spec", _execute)


def run_register_trial(args: argparse.Namespace) -> int:
    """Run ``alpha governance register-trial``."""

    def _execute() -> dict[str, object]:
        registry = GovernanceRegistry(args.registry_path)
        record = validate_trial_ledger_record(
            load_governance_mapping(
                args.trial_ledger_record,
                object_name=GovernanceIdKind.TRIAL_LEDGER_RECORD.value,
            )
        )
        entry = registry.save(
            record,
            "DIAGNOSTICS_RUN",
            status_message=args.status_message or "",
        )
        return _registry_success_payload("register-trial", entry, args.registry_path)

    return _run_json_command("register-trial", _execute)


def run_build_evidence(args: argparse.Namespace) -> int:
    """Run ``alpha governance build-evidence``."""

    def _execute() -> dict[str, object]:
        registry = GovernanceRegistry(args.registry_path)
        bundle = validate_evidence_bundle(
            load_governance_mapping(
                args.evidence_bundle,
                object_name=GovernanceIdKind.EVIDENCE_BUNDLE.value,
            )
        )
        study_spec = cast(
            StudySpec,
            registry.get_object(bundle.study_spec_id, object_kind=GovernanceIdKind.STUDY_SPEC),
        )
        trial_records: list[TrialLedgerRecord] = []
        for trial_id in bundle.trial_ids:
            trial_records.append(
                cast(
                    TrialLedgerRecord,
                    registry.get_object(
                        trial_id,
                        object_kind=GovernanceIdKind.TRIAL_LEDGER_RECORD,
                    ),
                )
            )
        validate_governance_transition(
            "DIAGNOSTICS_RUN",
            "EVIDENCE_READY",
            PromotionGateContext(
                evidence_bundle=bundle,
                study_spec=study_spec,
                trial_ledger_records=tuple(trial_records),
                trial_ledger_path=args.trial_ledger_path,
                family_id=args.family_id,
                variant_ledger_path=args.variant_ledger_path,
                budget_amendments=_load_budget_amendments(args.budget_amendment),
            ),
        )
        entry = registry.save(
            bundle,
            "EVIDENCE_READY",
            status_message=args.status_message or "",
        )
        payload = _registry_success_payload("build-evidence", entry, args.registry_path)
        payload["resolved_trial_ids"] = list(bundle.trial_ids)
        payload["resolved_study_spec_id"] = bundle.study_spec_id
        payload["resolved_trial_ledger_path"] = str(Path(args.trial_ledger_path))
        payload["resolved_variant_ledger_path"] = str(Path(args.variant_ledger_path))
        payload["validated_transition"] = "DIAGNOSTICS_RUN->EVIDENCE_READY"
        return payload

    return _run_json_command("build-evidence", _execute)


def run_variant_ledger_summary(args: argparse.Namespace) -> int:
    """Run ``alpha governance variant-ledger-summary``."""

    def _execute() -> dict[str, object]:
        ledger = VariantLedger(args.ledger_path)
        payload: dict[str, object] = {
            "status": "ok",
            "command": "variant-ledger-summary",
            **ledger.summary(),
        }
        if (args.family_id is None) != (args.family_budget is None):
            raise GovernanceValidationError(
                ValidationIssue(
                    field="family_budget",
                    code="incomplete_family_budget_request",
                    message=(
                        "family budget status requires both --family-id and "
                        "--family-budget"
                    ),
                    expected="both family-id and family-budget, or neither",
                    actual="one argument missing",
                )
            )
        if args.family_id is not None and args.family_budget is not None:
            payload["family_budget_check"] = ledger.family_budget_check(
                family_id=args.family_id,
                family_budget=args.family_budget,
            ).to_dict()
        return payload

    return _run_json_command("variant-ledger-summary", _execute)


def run_review(args: argparse.Namespace) -> int:
    """Run ``alpha governance review``."""

    def _execute() -> dict[str, object]:
        registry = GovernanceRegistry(args.registry_path)
        verdict = validate_reviewer_verdict(
            load_governance_mapping(
                args.reviewer_verdict,
                object_name=GovernanceIdKind.REVIEWER_VERDICT.value,
            )
        )
        context = PromotionGateContext(
            reviewer_verdict=verdict,
            implementer_id=args.implementer_id,
            implementer_role=args.implementer_role,
        )
        entry = registry.save(
            verdict,
            "REVIEWED",
            gate_context=context,
            status_message=args.status_message or "",
        )
        payload = _registry_success_payload("review", entry, args.registry_path)
        payload["validated_transition"] = "EVIDENCE_READY->REVIEWED"
        return payload

    return _run_json_command("review", _execute)


def run_promote(args: argparse.Namespace) -> int:
    """Run ``alpha governance promote``."""

    def _execute() -> dict[str, object]:
        registry = GovernanceRegistry(args.registry_path)
        decision = validate_promotion_decision(
            load_governance_mapping(
                args.promotion_decision,
                object_name=GovernanceIdKind.PROMOTION_DECISION.value,
            )
        )
        context = _promotion_context_from_registry(registry, decision, args)
        entry = registry.save(
            decision,
            decision.next_state,
            gate_context=context,
            status_message=args.status_message or "",
        )
        payload = _registry_success_payload("promote", entry, args.registry_path)
        payload["validated_transition"] = f"REVIEWED->{decision.next_state.value}"
        payload["promotion_decision_id"] = decision.promotion_id
        return payload

    return _run_json_command("promote", _execute)


def run_validate_feature_locks(args: argparse.Namespace) -> int:
    """Run ``alpha governance validate-feature-locks``."""

    from alpha_system.governance.feature_lock_validation import (
        FeatureLockValidationError,
        validate_feature_locks,
    )

    def _execute() -> dict[str, object]:
        locks = _load_feature_pack_locks(args.locks)
        report = validate_feature_locks(locks, registry_path=args.registry_path)
        return {
            "status": "ok",
            "command": "validate-feature-locks",
            **report.to_dict(),
        }

    try:
        payload = _execute()
    except (
        FeatureLockValidationError,
        GovernanceValidationError,
        GovernanceSerializationError,
        OSError,
        ValueError,
    ) as exc:
        print(
            json.dumps(
                governance_exception_payload("validate-feature-locks", exc),
                sort_keys=True,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(payload, sort_keys=True, indent=2))
    return 0


def run_requeue_scan(args: argparse.Namespace) -> int:
    """Run ``alpha governance requeue-scan``."""

    def _execute():
        result = scan_requeue_candidates(
            verdict_paths=args.verdicts,
            annotation_paths=args.annotations,
            acceptance_evidence_path=args.acceptance_evidence,
            created_at=args.created_at,
        )
        if args.out:
            write_requeue_records(args.out, result)
        return result

    try:
        result = _execute()
    except (
        GovernanceValidationError,
        GovernanceSerializationError,
        GovernanceIdError,
        OSError,
        ValueError,
    ) as exc:
        print(
            json.dumps(
                governance_exception_payload("requeue-scan", exc),
                sort_keys=True,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2
    print(result.render_text())
    return 0


def _load_feature_pack_locks(path: str | Path) -> list[Mapping[str, Any] | str]:
    """Load a generic feature-pack-locks JSON document.

    The JSON root may be a list of locks (mappings with ``feature_version_id``
    or bare id strings), or a mapping carrying a ``feature_pack_locks`` list.
    """

    value = deserialize(Path(path).read_text(encoding="utf-8"))
    if isinstance(value, Mapping):
        locks = value.get("feature_pack_locks")
    else:
        locks = value
    if isinstance(locks, str) or not isinstance(locks, list):
        raise GovernanceValidationError(
            ValidationIssue(
                field="feature_pack_locks",
                code="invalid_feature_pack_locks",
                message="locks JSON must be a list or a mapping with feature_pack_locks list",
                expected="list of feature-pack locks",
                actual=type(locks).__name__,
            )
        )
    return list(locks)


def _load_budget_amendments(paths: list[str]) -> tuple[Mapping[str, Any], ...]:
    return tuple(
        validate_budget_amendment_record(
            load_governance_mapping(path, object_name="BudgetAmendmentRecord")
        ).to_dict()
        for path in paths
    )


def register_subparser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the ``alpha governance`` command group."""

    governance_parser = subparsers.add_parser(
        "governance",
        help="Validate and persist governance metadata through fail-closed gates.",
    )
    governance_subparsers = governance_parser.add_subparsers(dest="governance_command")

    validate_parser = governance_subparsers.add_parser(
        "validate-spec",
        help="Validate an AlphaSpec with its referenced HypothesisCard.",
    )
    validate_parser.add_argument("alpha_spec", help="Path to an AlphaSpec JSON file.")
    validate_parser.add_argument(
        "--hypothesis-card",
        required=True,
        help="Path to the referenced HypothesisCard JSON file.",
    )
    validate_parser.set_defaults(handler=run_validate_spec)

    trial_parser = governance_subparsers.add_parser(
        "register-trial",
        help="Persist a TrialLedgerRecord under DIAGNOSTICS_RUN.",
    )
    _add_registry_path_argument(trial_parser)
    trial_parser.add_argument(
        "trial_ledger_record",
        help="Path to a TrialLedgerRecord JSON file.",
    )
    _add_status_message_argument(trial_parser)
    trial_parser.set_defaults(handler=run_register_trial)

    evidence_parser = governance_subparsers.add_parser(
        "build-evidence",
        help="Validate and persist an EvidenceBundle from existing registry refs.",
    )
    _add_registry_path_argument(evidence_parser)
    evidence_parser.add_argument(
        "--trial-ledger-path",
        default=None,
        help=(
            "Path to an existing writable trial ledger JSON file required by the "
            "fail-closed evidence-ready promotion gate."
        ),
    )
    evidence_parser.add_argument(
        "evidence_bundle",
        help="Path to an EvidenceBundle JSON file.",
    )
    evidence_parser.add_argument(
        "--variant-ledger-path",
        help="Path to the append-friendly VariantLedger JSONL file.",
    )
    evidence_parser.add_argument(
        "--family-id",
        help="Family ID used for VariantLedger family roll-up enforcement.",
    )
    evidence_parser.add_argument(
        "--budget-amendment",
        action="append",
        default=[],
        help="Optional BudgetAmendmentRecord JSON file. May be supplied multiple times.",
    )
    _add_status_message_argument(evidence_parser)
    evidence_parser.set_defaults(handler=run_build_evidence)

    ledger_summary_parser = governance_subparsers.add_parser(
        "variant-ledger-summary",
        help="Read-only summary of a VariantLedger JSONL file.",
    )
    ledger_summary_parser.add_argument(
        "--ledger-path",
        required=True,
        help="Path to the VariantLedger JSONL file.",
    )
    ledger_summary_parser.add_argument(
        "--family-id",
        help="Optional family ID for a family-budget status check.",
    )
    ledger_summary_parser.add_argument(
        "--family-budget",
        type=int,
        help="Optional family budget used with --family-id for status output.",
    )
    ledger_summary_parser.set_defaults(handler=run_variant_ledger_summary)

    review_parser = governance_subparsers.add_parser(
        "review",
        help="Persist an independent ReviewerVerdict under REVIEWED.",
    )
    _add_registry_path_argument(review_parser)
    review_parser.add_argument(
        "reviewer_verdict",
        help="Path to a ReviewerVerdict JSON file.",
    )
    _add_reviewer_context_arguments(review_parser)
    _add_status_message_argument(review_parser)
    review_parser.set_defaults(handler=run_review)

    promote_parser = governance_subparsers.add_parser(
        "promote",
        help="Persist a PromotionDecision only after the promotion gate accepts it.",
    )
    _add_registry_path_argument(promote_parser)
    promote_parser.add_argument(
        "promotion_decision",
        help="Path to a PromotionDecision JSON file.",
    )
    _add_reviewer_context_arguments(promote_parser)
    promote_parser.add_argument(
        "--locked-test-contamination-metadata",
        help="Optional JSON mapping documenting recorded locked-test contamination.",
    )
    promote_parser.add_argument(
        "--rejected-idea-record",
        help="Optional RejectedIdeaRecord JSON file required by rejected transitions.",
    )
    promote_parser.add_argument(
        "--rejection-reason",
        help="Explicit rejection reason required by rejected transitions.",
    )
    _add_status_message_argument(promote_parser)
    promote_parser.set_defaults(handler=run_promote)

    locks_parser = governance_subparsers.add_parser(
        "validate-feature-locks",
        help=(
            "Fail-closed: assert every feature-pack lock feature_version_id "
            "resolves in the sanctioned local feature registry."
        ),
    )
    locks_parser.add_argument(
        "--locks",
        required=True,
        help=(
            "Path to a JSON document of feature-pack locks: a list of "
            "{feature_version_id, ...} mappings (or bare id strings), or a "
            "mapping with a feature_pack_locks list."
        ),
    )
    locks_parser.add_argument(
        "--registry-path",
        required=True,
        help="Path to the sanctioned local feature registry SQLite file.",
    )
    locks_parser.set_defaults(handler=run_validate_feature_locks)

    requeue_parser = governance_subparsers.add_parser(
        "requeue-scan",
        help=(
            "Deterministically scan UNDERPOWERED verdicts for evidence-accrual "
            "retest eligibility."
        ),
    )
    requeue_parser.add_argument(
        "--verdicts",
        nargs="*",
        default=(),
        help="Reviewer verdict JSON files or directories to scan read-only.",
    )
    requeue_parser.add_argument(
        "--annotations",
        nargs="*",
        default=(),
        help="Verdict annotation JSON files or directories to scan read-only.",
    )
    requeue_parser.add_argument(
        "--acceptance-evidence",
        required=True,
        help="JSON file declaring current accepted data months for UNDERPOWERED candidates.",
    )
    requeue_parser.add_argument(
        "--created-at",
        help="Optional UTC seconds timestamp for deterministic test output.",
    )
    requeue_parser.add_argument(
        "--out",
        help="Optional output path for RequeuedVerdictRecords JSON; stdout still prints the table.",
    )
    requeue_parser.set_defaults(handler=run_requeue_scan)


def _run_json_command(command: str, execute: Callable[[], dict[str, object]]) -> int:
    try:
        payload = execute()
    except (
        GovernanceValidationError,
        GovernanceSerializationError,
        GovernanceIdError,
        OSError,
        ValueError,
    ) as exc:
        print(
            json.dumps(governance_exception_payload(command, exc), sort_keys=True, indent=2),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(payload, sort_keys=True, indent=2))
    return 0


def _registry_success_payload(
    command: str,
    entry: GovernanceRegistryEntry,
    registry_path: str | Path,
) -> dict[str, object]:
    return {
        "status": "ok",
        "command": command,
        "registry_path": str(Path(registry_path)),
        "entry": entry.to_dict(),
    }


def _promotion_context_from_registry(
    registry: GovernanceRegistry,
    decision: PromotionDecision,
    args: argparse.Namespace,
) -> PromotionGateContext:
    verdict = cast(
        ReviewerVerdict,
        registry.get_object(
            decision.reviewer_verdict_id,
            object_kind=GovernanceIdKind.REVIEWER_VERDICT,
        ),
    )
    evidence_bundle = None
    trial_records: tuple[TrialLedgerRecord, ...] = ()
    if decision.next_state in {
        PromotionLifecycleState.CANDIDATE,
        PromotionLifecycleState.VALIDATED,
    }:
        evidence_bundle = cast(
            EvidenceBundle,
            registry.get_object(
                decision.evidence_bundle_id,
                object_kind=GovernanceIdKind.EVIDENCE_BUNDLE,
            ),
        )
        trial_records = _trial_records_for_bundle(registry, evidence_bundle)

    rejected_idea_record = None
    if args.rejected_idea_record:
        rejected_idea_record = validate_rejected_idea_record(
            load_governance_mapping(
                args.rejected_idea_record,
                object_name=GovernanceIdKind.REJECTED_IDEA_RECORD.value,
            )
        )

    return PromotionGateContext(
        evidence_bundle=evidence_bundle,
        trial_ledger_records=trial_records,
        reviewer_verdict=verdict,
        implementer_id=args.implementer_id,
        implementer_role=args.implementer_role,
        promotion_decision=decision,
        rejected_idea_record=rejected_idea_record,
        rejection_reason=args.rejection_reason,
        locked_test_contamination_metadata=_load_optional_mapping(
            args.locked_test_contamination_metadata,
            object_name="locked_test_contamination_metadata",
        ),
    )


def _trial_records_for_bundle(
    registry: GovernanceRegistry,
    evidence_bundle: EvidenceBundle,
) -> tuple[TrialLedgerRecord, ...]:
    records: list[TrialLedgerRecord] = []
    for entry in registry.list_by_lifecycle_state(
        "DIAGNOSTICS_RUN",
        object_kind=GovernanceIdKind.TRIAL_LEDGER_RECORD,
    ):
        record = cast(TrialLedgerRecord, entry.payload)
        if (
            record.alpha_spec_id == evidence_bundle.alpha_spec_id
            and record.study_spec_id == evidence_bundle.study_spec_id
        ):
            records.append(record)
    return tuple(records)


def _load_optional_mapping(
    path: str | Path | None, *, object_name: str
) -> Mapping[str, Any] | None:
    if path is None:
        return None
    return load_governance_mapping(path, object_name=object_name)


def _coerce_kind(value: GovernanceIdKind | str) -> GovernanceIdKind:
    try:
        return resolve_governance_id_kind(value)
    except GovernanceIdError as exc:
        raise GovernanceValidationError(
            ValidationIssue(
                field="object_kind",
                code=exc.issue.code,
                message=exc.issue.message,
                expected="canonical governance object kind",
                actual=str(exc.issue.value),
            )
        ) from exc


def _adapter_for_kind(kind: GovernanceIdKind) -> _ObjectAdapter:
    adapter = _OBJECT_ADAPTERS.get(kind.value)
    if adapter is None:
        raise GovernanceValidationError(
            ValidationIssue(
                field="object_kind",
                code="unsupported_governance_object_kind",
                message="governance CLI does not validate this object kind",
                expected="supported governance object kind",
                actual=kind.value,
            )
        )
    return adapter


def _add_registry_path_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--registry-path",
        required=True,
        help="Path to a local SQLite governance registry. Tests should use a temp path.",
    )


def _add_reviewer_context_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--implementer-id",
        required=True,
        help="Implementer identity used for reviewer-independence enforcement.",
    )
    parser.add_argument(
        "--implementer-role",
        required=True,
        help="Implementer role used for reviewer-independence enforcement.",
    )


def _add_status_message_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--status-message",
        help="Optional local registry lifecycle status message.",
    )
