"""Pre-test idea testability gate for value-free research-lane routing."""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from alpha_system.governance.alpha_spec import AlphaSpec, validate_alpha_spec
from alpha_system.governance.family_fdr_correction import (
    DEFAULT_FDR_ALPHA,
    DEFAULT_FDR_METHOD,
)
from alpha_system.governance.idea_draft import (
    CONTEXT_NOT_EQUAL_TRIGGER,
    MAIN_EFFECT,
    IdeaDraft,
    validate_idea_draft,
)
from alpha_system.governance.mechanism_card import MechanismCard, validate_mechanism_card
from alpha_system.governance.setup_spec import SetupSpec, validate_setup_spec
from alpha_system.governance.surrogate_run import ZERO_PASS_MET
from alpha_system.research_lane.conditioned_power import (
    PLAUSIBLE_CONDITIONED_ABS_IC_FLOOR,
    ConditionedPowerPreconditionError,
    compute_conditioned_power,
    conditioned_power_verdict,
)
from alpha_system.research_lane.slice_spec import SliceSpec, SliceSpecError
from alpha_system.runtime.diagnostics.label.runtime import (
    _class_balance_summary,
    _distribution_summary,
)
from alpha_system.runtime.input_resolver import (
    DATA_ROOT_PRECONDITION_CODE,
    FeatureLabelPackResolver,
    FeaturePackHandle,
    LabelPackHandle,
    RuntimeInputResolverError,
)

CHECK_FEATURES_MATERIALIZED = "features_materialized"
CHECK_LABELS_EXIST = "labels_path_labels_exist"
CHECK_PATH_LABEL_TWO_CLASS = "path_label_two_class"
CHECK_N_EFF_MDE_DEDUP = "n_eff_mde_plausible_and_dedup_known"
CHECK_NO_LOOKAHEAD_SURROGATE = "available_ts_and_surrogate_fdr_known"

CHECK_ORDER = (
    CHECK_FEATURES_MATERIALIZED,
    CHECK_LABELS_EXIST,
    CHECK_PATH_LABEL_TWO_CLASS,
    CHECK_N_EFF_MDE_DEDUP,
    CHECK_NO_LOOKAHEAD_SURROGATE,
)


class GateStatus(StrEnum):
    """Allowed pre-test gate statuses."""

    PASS = "PASS"
    FAIL = "FAIL"
    DATA_GAP = "DATA_GAP"
    # Distinct from DATA_GAP: an unmet ENVIRONMENT/config precondition (e.g. an
    # unresolvable ALPHA_DATA_ROOT) surfaced by the resolver. This must never be
    # read as a research/data finding. It outranks DATA_GAP in the rollup so a
    # broken env is reported as a misconfiguration, not an absent-data outcome.
    ENVIRONMENT_NOT_CONFIGURED = "ENVIRONMENT_NOT_CONFIGURED"


class TestabilityGateError(ValueError):
    """Raised when testability-gate inputs are malformed."""


@dataclass(frozen=True, slots=True)
class GateCheckResult:
    """One value-free testability check result."""

    check_id: str
    status: GateStatus
    detail: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "status": self.status.value,
            "detail": _jsonish(self.detail),
        }


@dataclass(frozen=True, slots=True)
class TestabilityGateResult:
    """Structured PASS / FAIL / DATA_GAP pre-test result."""

    overall_status: GateStatus
    checks: tuple[GateCheckResult, ...]
    idea_draft_id: str
    slice_id: str | None
    pre_test: bool = True
    probe_invoked: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_status": self.overall_status.value,
            "verdict": self.overall_status.value,
            "pre_test": self.pre_test,
            "shot_spent": False,
            "probe_invoked": self.probe_invoked,
            "idea_draft": self.idea_draft_id,
            "slice_id": self.slice_id,
            "checks": [check.to_dict() for check in self.checks],
        }


@dataclass(frozen=True, slots=True)
class TestabilitySlice:
    """Bounded value-free slice metadata used by the pre-test gate."""

    slice_id: str
    study_kind: str | None = None
    outcome_label_type: str | None = None
    dataset_version_id: str | None = None
    partition_id: str | None = None
    feature_pack_refs: tuple[str, ...] = ()
    label_pack_refs: tuple[str, ...] = ()
    feature_request_ids: tuple[str, ...] = ()
    label_spec_ids: tuple[str, ...] = ()
    path_label_observations: tuple[Mapping[str, Any], ...] = ()
    path_label_class_counts: Mapping[str, int] | None = None
    continuous_label_value_std: float | None = None
    continuous_label_nonzero_count: int | None = None
    continuous_label_sample_count: int | None = None
    n_eff: int | None = None
    minimum_detectable_effect: float | None = None
    available_ts_satisfiable: bool | None = None
    surrogate_fdr_requirement: str | None = None
    # CROSS_IDEA_FDR_BUDGET_V1: optional slice-level family-wise multiplicity policy.
    # An idea MAY pin its family-FDR method + alpha; absent, the standing policy
    # default applies (the enforcement lives in memory_router, not a gate CHECK), so
    # a missing declaration NEVER fails the gate.
    family_fdr_requirement: str = DEFAULT_FDR_METHOD
    family_fdr_alpha: float = DEFAULT_FDR_ALPHA

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> TestabilitySlice:
        mapping = dict(payload)
        slice_id = _optional_text(mapping.get("slice_id") or mapping.get("id"))
        if slice_id is None:
            slice_id = "default"
        surrogate_requirement = _optional_text(
            mapping.get("surrogate_fdr_requirement")
            or mapping.get("surrogate_requirement")
            or mapping.get("required_surrogate_gate")
        )
        if surrogate_requirement is None and mapping.get("surrogate_fdr_required") is True:
            surrogate_requirement = ZERO_PASS_MET
        continuous_summary = mapping.get("continuous_label_summary")
        continuous_summary = continuous_summary if isinstance(continuous_summary, Mapping) else {}
        return cls(
            slice_id=slice_id,
            study_kind=_optional_text(mapping.get("study_kind")),
            outcome_label_type=_optional_text(mapping.get("outcome_label_type")),
            dataset_version_id=_optional_text(mapping.get("dataset_version_id")),
            partition_id=_partition_id(mapping),
            feature_pack_refs=_text_tuple(
                mapping.get("feature_pack_refs") or mapping.get("feature_packs"),
                field="feature_pack_refs",
            ),
            label_pack_refs=_text_tuple(
                mapping.get("label_pack_refs") or mapping.get("label_packs"),
                field="label_pack_refs",
            ),
            feature_request_ids=_text_tuple(
                mapping.get("feature_request_ids"),
                field="feature_request_ids",
            ),
            label_spec_ids=_text_tuple(mapping.get("label_spec_ids"), field="label_spec_ids"),
            path_label_observations=_observation_tuple(
                mapping.get("path_label_observations")
                or mapping.get("label_observations")
                or mapping.get("observations")
            ),
            path_label_class_counts=_class_counts(
                mapping.get("path_label_class_counts") or mapping.get("class_counts")
            ),
            n_eff=_optional_int(mapping.get("n_eff") or mapping.get("effective_sample_size")),
            minimum_detectable_effect=_optional_float(
                mapping.get("minimum_detectable_effect")
                or mapping.get("minimum_detectable_abs_ic")
                or mapping.get("mde")
            ),
            continuous_label_value_std=_optional_float(
                continuous_summary.get("value_std")
                if continuous_summary
                else mapping.get("continuous_label_value_std")
            ),
            continuous_label_nonzero_count=_optional_int(
                continuous_summary.get("nonzero_count")
                if continuous_summary
                else mapping.get("continuous_label_nonzero_count")
            ),
            continuous_label_sample_count=_optional_int(
                continuous_summary.get("sample_count")
                if continuous_summary
                else mapping.get("continuous_label_sample_count")
            ),
            available_ts_satisfiable=_optional_bool(mapping.get("available_ts_satisfiable")),
            surrogate_fdr_requirement=surrogate_requirement,
            family_fdr_requirement=(
                _optional_text(mapping.get("family_fdr_requirement")) or DEFAULT_FDR_METHOD
            ),
            family_fdr_alpha=(
                _optional_float(mapping.get("family_fdr_alpha"))
                if mapping.get("family_fdr_alpha") is not None
                else DEFAULT_FDR_ALPHA
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "slice_id": self.slice_id,
            "study_kind": self.study_kind,
            "outcome_label_type": self.outcome_label_type,
            "dataset_version_id": self.dataset_version_id,
            "partition_id": self.partition_id,
            "feature_pack_refs": list(self.feature_pack_refs),
            "label_pack_refs": list(self.label_pack_refs),
            "feature_request_ids": list(self.feature_request_ids),
            "label_spec_ids": list(self.label_spec_ids),
            "path_label_observation_count": len(self.path_label_observations),
            "path_label_class_counts": (
                None if self.path_label_class_counts is None else dict(self.path_label_class_counts)
            ),
            "continuous_label_value_std": self.continuous_label_value_std,
            "continuous_label_nonzero_count": self.continuous_label_nonzero_count,
            "continuous_label_sample_count": self.continuous_label_sample_count,
            "n_eff": self.n_eff,
            "minimum_detectable_effect": self.minimum_detectable_effect,
            "available_ts_satisfiable": self.available_ts_satisfiable,
            "surrogate_fdr_requirement": self.surrogate_fdr_requirement,
            "family_fdr_requirement": self.family_fdr_requirement,
            "family_fdr_alpha": self.family_fdr_alpha,
        }


def evaluate_testability_gate(
    idea_draft: IdeaDraft | Mapping[str, Any],
    *,
    alpha_spec: AlphaSpec | Mapping[str, Any],
    mechanism_card: MechanismCard | Mapping[str, Any],
    setup_spec: SetupSpec | Mapping[str, Any] | None = None,
    slice_spec: TestabilitySlice | Mapping[str, Any] | None = None,
    conditioned_power_slice: SliceSpec | Mapping[str, Any] | None = None,
    resolver: FeatureLabelPackResolver | None = None,
    probe_runner: Callable[[], object] | None = None,
    env: Mapping[str, str] | None = None,
) -> TestabilityGateResult:
    """Evaluate testability checks before any probe or metric is run.

    ``conditioned_power_slice`` is the richer materialized-slice descriptor (the
    same ``SliceSpec`` the fast probe loads). When the study is a
    ``context_not_equal_trigger`` setup it lets the N_eff/MDE check recompute the
    honest CONDITIONED (context AND trigger) power and gate on a plausible-effect
    MDE floor, instead of accepting the author's UNCONDITIONED figure. When it is
    absent the check keeps its prior unconditioned-plausibility behavior for that
    study kind (e.g. unit fixtures that do not carry feature parquet rows).
    """

    active_idea = _coerce_idea_draft(idea_draft)
    active_alpha = _coerce_alpha_spec(alpha_spec)
    active_mechanism = _coerce_mechanism_card(mechanism_card)
    active_setup = _coerce_setup_spec(setup_spec)
    active_slice = _coerce_slice(slice_spec)
    active_conditioned_slice = _coerce_conditioned_power_slice(conditioned_power_slice)

    feature_check, feature_handles = _check_features_materialized(
        active_mechanism,
        active_slice,
        resolver,
    )
    label_check, label_handles = _check_labels_exist(
        active_alpha,
        active_mechanism,
        active_setup,
        active_slice,
        resolver,
    )
    checks = (
        feature_check,
        label_check,
        _check_outcome_non_degeneracy(active_slice),
        _check_n_eff_mde_and_dedup(
            active_mechanism,
            active_slice,
            setup_spec=active_setup,
            conditioned_power_slice=active_conditioned_slice,
            env=env,
        ),
        _check_available_ts_and_surrogate(active_slice, feature_handles, label_handles),
    )
    return TestabilityGateResult(
        overall_status=_overall_status(checks),
        checks=checks,
        idea_draft_id=f"{active_idea.alpha_spec_id}:{active_idea.mechanism_id}",
        slice_id=None if active_slice is None else active_slice.slice_id,
        pre_test=True,
        probe_invoked=False,
    )


def slice_spec_from_idea_payload(
    payload: Mapping[str, Any],
    *,
    slice_id: str | None = None,
) -> TestabilitySlice | None:
    """Extract an optional embedded value-free testability slice descriptor."""

    selected = _select_slice_payload(payload, slice_id=slice_id)
    if selected is None:
        if slice_id:
            raise TestabilityGateError(f"slice {slice_id!r} was not found in idea document")
        return None
    return TestabilitySlice.from_mapping(selected)


def summarize_label_class_balance(
    observations: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Return the label-runtime class-count summary for supplied observations."""

    rows = tuple(dict(row) for row in observations)
    distribution = _distribution_summary(rows)
    class_balance = _class_balance_summary(distribution)
    return {**distribution, **class_balance}


def _check_features_materialized(
    mechanism_card: MechanismCard,
    slice_spec: TestabilitySlice | None,
    resolver: FeatureLabelPackResolver | None,
) -> tuple[GateCheckResult, tuple[FeaturePackHandle, ...]]:
    if not mechanism_card.required_features:
        return _fail(
            CHECK_FEATURES_MATERIALIZED,
            "mechanism declares no required features",
        ), ()
    if slice_spec is None:
        return _data_gap(
            CHECK_FEATURES_MATERIALIZED,
            "bounded slice metadata is missing",
            required_features=mechanism_card.required_features,
        ), ()
    missing = _missing_slice_resolution_fields(slice_spec)
    if missing:
        return _data_gap(
            CHECK_FEATURES_MATERIALIZED,
            "slice cannot resolve feature packs without dataset and partition metadata",
            missing_fields=missing,
        ), ()
    if not slice_spec.feature_pack_refs:
        return _data_gap(
            CHECK_FEATURES_MATERIALIZED,
            "slice declares no feature pack refs",
            required_features=mechanism_card.required_features,
        ), ()
    if resolver is None:
        return _data_gap(
            CHECK_FEATURES_MATERIALIZED,
            "FeatureLabelPackResolver is not available",
        ), ()
    try:
        handles = resolver.resolve_feature_packs(
            slice_spec.feature_pack_refs,
            expected_dataset_version_id=str(slice_spec.dataset_version_id),
            expected_feature_request_ids=slice_spec.feature_request_ids,
            partition_id=str(slice_spec.partition_id),
            # Exploratory pre-test: horizon-agnostic features (<instr>_<year>_full_year)
            # legitimately serve a horizon-specific runtime partition; labels stay strict.
            allow_horizon_agnostic_partition=True,
        )
    except RuntimeInputResolverError as exc:
        return _resolver_rejection_check(
            CHECK_FEATURES_MATERIALIZED,
            "feature packs are not resolvable",
            exc,
        ), ()
    if not handles:
        return _data_gap(CHECK_FEATURES_MATERIALIZED, "no feature pack handles resolved"), ()
    return _pass(
        CHECK_FEATURES_MATERIALIZED,
        "feature pack handles resolved without materializing values",
        handle_count=len(handles),
    ), handles


def _check_labels_exist(
    alpha_spec: AlphaSpec,
    mechanism_card: MechanismCard,
    setup_spec: SetupSpec | None,
    slice_spec: TestabilitySlice | None,
    resolver: FeatureLabelPackResolver | None,
) -> tuple[GateCheckResult, tuple[LabelPackHandle, ...]]:
    expected_label_ids = _expected_label_spec_ids(alpha_spec, setup_spec, slice_spec)
    if not mechanism_card.required_labels and not expected_label_ids:
        return _fail(
            CHECK_LABELS_EXIST,
            "idea declares no required labels or label references",
        ), ()
    if slice_spec is None:
        return _data_gap(
            CHECK_LABELS_EXIST,
            "bounded slice metadata is missing",
            required_labels=mechanism_card.required_labels,
            expected_label_spec_ids=expected_label_ids,
        ), ()
    missing = _missing_slice_resolution_fields(slice_spec)
    if missing:
        return _data_gap(
            CHECK_LABELS_EXIST,
            "slice cannot resolve label packs without dataset and partition metadata",
            missing_fields=missing,
        ), ()
    if not slice_spec.label_pack_refs:
        return _data_gap(
            CHECK_LABELS_EXIST,
            "slice declares no label pack refs",
            required_labels=mechanism_card.required_labels,
            expected_label_spec_ids=expected_label_ids,
        ), ()
    if resolver is None:
        return _data_gap(CHECK_LABELS_EXIST, "FeatureLabelPackResolver is not available"), ()
    try:
        handles = resolver.resolve_label_packs(
            slice_spec.label_pack_refs,
            expected_dataset_version_id=str(slice_spec.dataset_version_id),
            expected_label_spec_ids=expected_label_ids,
            partition_id=str(slice_spec.partition_id),
        )
    except RuntimeInputResolverError as exc:
        return _resolver_rejection_check(
            CHECK_LABELS_EXIST,
            "label packs are not resolvable",
            exc,
        ), ()
    if not handles:
        return _data_gap(CHECK_LABELS_EXIST, "no label pack handles resolved"), ()
    resolved_label_spec_ids = {handle.label_spec_id for handle in handles}
    if setup_spec is not None and setup_spec.path_label not in resolved_label_spec_ids:
        return _data_gap(
            CHECK_LABELS_EXIST,
            "resolved label packs do not include SetupSpec.path_label",
            path_label=setup_spec.path_label,
        ), ()
    return _pass(
        CHECK_LABELS_EXIST,
        "label pack handles resolved without materializing values",
        handle_count=len(handles),
    ), handles


def _check_outcome_non_degeneracy(slice_spec: TestabilitySlice | None) -> GateCheckResult:
    """Dispatch the outcome non-degeneracy pre-test by study kind.

    Path/binary outcomes (``context_not_equal_trigger``) require at least two
    observed classes. Continuous-outcome ``main_effect`` studies have no class
    structure, so the analogous guard is non-degeneracy of the continuous label
    (declared ``value_std`` strictly positive over an observed sample). Both
    cases report under the same ``CHECK_PATH_LABEL_TWO_CLASS`` slot so report
    rendering and check ordering stay stable.
    """

    # Continuous-outcome studies have no class structure, so the analogous guard
    # is continuous non-degeneracy: main_effect IC outcomes, OR a context!=trigger
    # setup that selects a continuous path outcome (outcome_label_type set; the
    # probe's _resolve_outcome_label_type guarantees it is a float path metric).
    if slice_spec is not None and (
        slice_spec.study_kind == MAIN_EFFECT or slice_spec.outcome_label_type is not None
    ):
        return _check_continuous_label_non_degenerate(slice_spec)
    return _check_path_label_two_class(slice_spec)


def _check_continuous_label_non_degenerate(
    slice_spec: TestabilitySlice | None,
) -> GateCheckResult:
    if slice_spec is None:
        return _data_gap(
            CHECK_PATH_LABEL_TWO_CLASS,
            "bounded slice metadata is missing",
        )
    study_kind = slice_spec.study_kind or MAIN_EFFECT
    value_std = slice_spec.continuous_label_value_std
    sample_count = slice_spec.continuous_label_sample_count
    if value_std is None or sample_count is None:
        return _data_gap(
            CHECK_PATH_LABEL_TWO_CLASS,
            "continuous-label non-degeneracy summary is missing",
            study_kind=study_kind,
        )
    if sample_count <= 0:
        return _data_gap(
            CHECK_PATH_LABEL_TWO_CLASS,
            "continuous-label outcome has no observed samples",
            study_kind=study_kind,
            continuous_label_sample_count=sample_count,
        )
    if not math.isfinite(value_std) or value_std <= 0:
        return _data_gap(
            CHECK_PATH_LABEL_TWO_CLASS,
            "continuous-label outcome is degenerate (non-positive value_std)",
            study_kind=study_kind,
            continuous_label_value_std=value_std,
            continuous_label_sample_count=sample_count,
        )
    return _pass(
        CHECK_PATH_LABEL_TWO_CLASS,
        "continuous-label outcome is non-degenerate (value_std > 0)",
        study_kind=study_kind,
        continuous_label_value_std=value_std,
        continuous_label_nonzero_count=slice_spec.continuous_label_nonzero_count,
        continuous_label_sample_count=sample_count,
    )


def _check_path_label_two_class(slice_spec: TestabilitySlice | None) -> GateCheckResult:
    if slice_spec is None:
        return _data_gap(
            CHECK_PATH_LABEL_TWO_CLASS,
            "bounded slice metadata is missing",
        )
    summary = _class_balance_for_slice(slice_spec)
    if summary is None:
        return _data_gap(
            CHECK_PATH_LABEL_TWO_CLASS,
            "path-label class observations or counts are missing",
        )
    observed = _int(summary.get("observed_outcome_count"))
    class_count = _int(summary.get("class_count"))
    if observed <= 0:
        return _data_gap(
            CHECK_PATH_LABEL_TWO_CLASS,
            "path-label outcomes contain no observed class",
            class_balance=summary,
        )
    if class_count < 2:
        return _data_gap(
            CHECK_PATH_LABEL_TWO_CLASS,
            "path-label slice has fewer than two distinct classes",
            class_balance=summary,
        )
    return _pass(
        CHECK_PATH_LABEL_TWO_CLASS,
        "path-label slice has at least two distinct classes",
        class_balance=summary,
    )


def _check_n_eff_mde_and_dedup(
    mechanism_card: MechanismCard,
    slice_spec: TestabilitySlice | None,
    *,
    setup_spec: SetupSpec | None = None,
    conditioned_power_slice: SliceSpec | None = None,
    env: Mapping[str, str] | None = None,
) -> GateCheckResult:
    dedup = dict(mechanism_card.duplicate_exposure)
    if not dedup:
        return _data_gap(
            CHECK_N_EFF_MDE_DEDUP,
            "duplicate_exposure declaration is missing",
        )
    dedup_status = str(dedup.get("status", "declared")).strip().lower()
    if dedup_status in {"unknown", "missing", "tbd", "todo", "none"}:
        return _data_gap(
            CHECK_N_EFF_MDE_DEDUP,
            "duplicate_exposure declaration is not known",
            duplicate_exposure=dedup,
        )
    if dedup_status in {
        "duplicate",
        "duplicates_known",
        "failed",
        "fail",
        "blocked",
        "not_distinct",
        "overlapping",
    }:
        return _fail(
            CHECK_N_EFF_MDE_DEDUP,
            "duplicate exposure declaration blocks a clean pre-test",
            duplicate_exposure=dedup,
        )
    if slice_spec is None:
        return _data_gap(
            CHECK_N_EFF_MDE_DEDUP,
            "bounded slice metadata is missing",
            duplicate_exposure=dedup,
        )
    if slice_spec.n_eff is None or slice_spec.minimum_detectable_effect is None:
        return _data_gap(
            CHECK_N_EFF_MDE_DEDUP,
            "N_eff and MDE metadata are required before a probe shot",
            n_eff=slice_spec.n_eff,
            minimum_detectable_effect=slice_spec.minimum_detectable_effect,
            duplicate_exposure=dedup,
        )
    if slice_spec.n_eff < 2:
        return _fail(
            CHECK_N_EFF_MDE_DEDUP,
            "N_eff is too small for a plausible pre-test",
            n_eff=slice_spec.n_eff,
        )
    mde = slice_spec.minimum_detectable_effect
    if not math.isfinite(mde) or mde <= 0 or mde > 1:
        return _fail(
            CHECK_N_EFF_MDE_DEDUP,
            "MDE must be finite and within (0, 1]",
            minimum_detectable_effect=mde,
        )
    # For a context_not_equal_trigger (conditional SETUP) study the author-supplied
    # n_eff/MDE above are the UNCONDITIONED full-slice figures; the real power is
    # governed by the CONDITIONED (context AND trigger) joint-firing event count,
    # collapsed to non-overlapping at the label horizon (the #474 rule applied to
    # the conditioned event series). Recompute the honest conditioned power and
    # gate on a plausible-effect MDE floor. main_effect is already
    # unconditioned-correct, so it keeps the unconditioned plausibility result.
    if slice_spec.study_kind == CONTEXT_NOT_EQUAL_TRIGGER:
        return _check_conditioned_power(
            dedup_status=dedup_status,
            slice_spec=slice_spec,
            setup_spec=setup_spec,
            conditioned_power_slice=conditioned_power_slice,
            env=env,
        )
    return _pass(
        CHECK_N_EFF_MDE_DEDUP,
        "N_eff/MDE metadata are plausible and duplicate exposure is declared",
        n_eff=slice_spec.n_eff,
        minimum_detectable_effect=mde,
        duplicate_exposure_status=dedup_status,
    )


def _check_conditioned_power(
    *,
    dedup_status: str,
    slice_spec: TestabilitySlice,
    setup_spec: SetupSpec | None,
    conditioned_power_slice: SliceSpec | None,
    env: Mapping[str, str] | None,
) -> GateCheckResult:
    """Gate a conditional SETUP on its honest CONDITIONED (context AND trigger) power.

    The conditioned N_eff is the joint-firing (context AND trigger) event count
    discounted to non-overlapping at the label horizon (#474). The MDE is
    recomputed from THAT N_eff and compared to a plausible-effect floor: a
    conditioned MDE ABOVE the floor means the setup cannot detect even a plausibly
    large conditional effect, so the check FAILS closed with a typed reason
    (``UNDERPOWERED_CONDITIONED``), distinct from DATA_GAP.

    When the richer conditioned-power slice or the setup is unavailable at gate
    time the prior unconditioned-plausibility PASS is preserved (no regression for
    fixtures/callers that do not provide it). When the slice IS provided but its
    conditioned-power inputs cannot be resolved, the check fails LOUD with a typed
    precondition reason -- never a silent pass and never a generic DATA_GAP.
    """

    if conditioned_power_slice is None or setup_spec is None:
        # No conditioned-power inputs supplied: keep the prior unconditioned PASS so
        # this composes additively. Record that the conditioned check was not run.
        return _pass(
            CHECK_N_EFF_MDE_DEDUP,
            "N_eff/MDE metadata are plausible and duplicate exposure is declared",
            n_eff=slice_spec.n_eff,
            minimum_detectable_effect=slice_spec.minimum_detectable_effect,
            duplicate_exposure_status=dedup_status,
            conditioned_power_evaluated=False,
            conditioned_power_reason="conditioned-power slice/setup not supplied to the gate",
        )

    try:
        conditioned = compute_conditioned_power(setup_spec, conditioned_power_slice, env=env)
    except ConditionedPowerPreconditionError as exc:
        # LOUD typed failure -- the conditioned-power compute could not resolve its
        # inputs. It must NEVER pass on the unconditioned figure. The env/precondition
        # law distinction: an unmet ENVIRONMENT precondition (unresolvable root,
        # malformed slice contract) surfaces as ENVIRONMENT_NOT_CONFIGURED; genuinely
        # absent/unreadable materialized feature values surface as a typed DATA_GAP
        # (distinct issue_code), never the conditioned-power UNDERPOWERED outcome.
        if exc.is_environment:
            return _environment_not_configured(
                CHECK_N_EFF_MDE_DEDUP,
                "conditioned-power environment precondition unmet (not a data gap)",
                issue_code="CONDITIONED_POWER_PRECONDITION_UNMET",
                reason=str(exc),
                study_kind=CONTEXT_NOT_EQUAL_TRIGGER,
            )
        return _data_gap(
            CHECK_N_EFF_MDE_DEDUP,
            "conditioned-power feature values are not resolvable at gate time",
            issue_code="CONDITIONED_POWER_DATA_GAP",
            reason=str(exc),
            study_kind=CONTEXT_NOT_EQUAL_TRIGGER,
        )

    verdict = conditioned_power_verdict(conditioned)
    detail: dict[str, Any] = {
        "conditioned_power": conditioned.to_dict(),
        "conditioned_mde_abs_ic": conditioned.conditioned_mde_abs_ic,
        "plausible_conditioned_abs_ic_floor": PLAUSIBLE_CONDITIONED_ABS_IC_FLOOR,
        "author_n_eff": slice_spec.n_eff,
        "author_minimum_detectable_effect": slice_spec.minimum_detectable_effect,
        "duplicate_exposure_status": dedup_status,
        "conditioned_power_evaluated": True,
    }
    if not verdict.passed:
        return _fail(
            CHECK_N_EFF_MDE_DEDUP,
            verdict.reason,
            issue_code=verdict.issue_code,
            **detail,
        )
    return _pass(
        CHECK_N_EFF_MDE_DEDUP,
        "conditioned N_eff/MDE are plausibly powered and duplicate exposure is declared",
        **detail,
    )


def _check_available_ts_and_surrogate(
    slice_spec: TestabilitySlice | None,
    feature_handles: Sequence[FeaturePackHandle],
    label_handles: Sequence[LabelPackHandle],
) -> GateCheckResult:
    if slice_spec is None:
        return _data_gap(
            CHECK_NO_LOOKAHEAD_SURROGATE,
            "bounded slice metadata is missing",
        )
    available = slice_spec.available_ts_satisfiable
    if available is None:
        available = _availability_satisfiable(feature_handles, label_handles)
    if available is None:
        return _data_gap(
            CHECK_NO_LOOKAHEAD_SURROGATE,
            "available_ts satisfiability is unknown",
        )
    if available is False:
        return _fail(
            CHECK_NO_LOOKAHEAD_SURROGATE,
            "feature available_ts cannot be satisfied before label availability",
        )
    if slice_spec.surrogate_fdr_requirement is None:
        return _data_gap(
            CHECK_NO_LOOKAHEAD_SURROGATE,
            "surrogate-FDR requirement is missing",
            expected=ZERO_PASS_MET,
        )
    if slice_spec.surrogate_fdr_requirement != ZERO_PASS_MET:
        return _fail(
            CHECK_NO_LOOKAHEAD_SURROGATE,
            "surrogate-FDR requirement must be ZERO_PASS_MET",
            expected=ZERO_PASS_MET,
            actual=slice_spec.surrogate_fdr_requirement,
        )
    return _pass(
        CHECK_NO_LOOKAHEAD_SURROGATE,
        "available_ts is satisfiable and surrogate-FDR requirement is known",
        surrogate_fdr_requirement=ZERO_PASS_MET,
    )


def _class_balance_for_slice(slice_spec: TestabilitySlice) -> dict[str, Any] | None:
    if slice_spec.path_label_observations:
        return summarize_label_class_balance(slice_spec.path_label_observations)
    if slice_spec.path_label_class_counts is None:
        return None
    counts = {
        str(key): int(value)
        for key, value in slice_spec.path_label_class_counts.items()
        if int(value) > 0
    }
    observed = sum(counts.values())
    majority = max(counts.values(), default=0)
    minority = min(counts.values(), default=0)
    return {
        "sample_count": observed,
        "observed_outcome_count": observed,
        "missing_outcome_count": 0,
        "missing_outcome_rate": 0.0 if observed else None,
        "class_count": len(counts),
        "majority_class_count": majority,
        "minority_class_count": minority,
        "majority_class_share": None if observed == 0 else majority / observed,
        "minority_class_share": None if observed == 0 else minority / observed,
    }


def _availability_satisfiable(
    feature_handles: Sequence[FeaturePackHandle],
    label_handles: Sequence[LabelPackHandle],
) -> bool | None:
    if not feature_handles or not label_handles:
        return None
    feature_available = [_datetime(handle.first_available_ts) for handle in feature_handles]
    label_available = [_datetime(handle.first_label_available_ts) for handle in label_handles]
    if any(value is None for value in feature_available + label_available):
        return None
    return max(value for value in feature_available if value is not None) <= min(
        value for value in label_available if value is not None
    )


def _expected_label_spec_ids(
    alpha_spec: AlphaSpec,
    setup_spec: SetupSpec | None,
    slice_spec: TestabilitySlice | None,
) -> tuple[str, ...]:
    ids: list[str] = []
    if slice_spec is not None:
        ids.extend(slice_spec.label_spec_ids)
    ids.extend(str(value) for value in alpha_spec.label_references)
    if setup_spec is not None:
        ids.append(setup_spec.path_label)
    return tuple(dict.fromkeys(value for value in ids if value))


def _missing_slice_resolution_fields(slice_spec: TestabilitySlice) -> tuple[str, ...]:
    missing: list[str] = []
    if not slice_spec.dataset_version_id:
        missing.append("dataset_version_id")
    if not slice_spec.partition_id:
        missing.append("partition_id")
    return tuple(missing)


def _overall_status(checks: Sequence[GateCheckResult]) -> GateStatus:
    statuses = {check.status for check in checks}
    # An unmet environment precondition outranks DATA_GAP: a broken env must be
    # reported as a misconfiguration, never collapsed into an absent-data outcome.
    if GateStatus.ENVIRONMENT_NOT_CONFIGURED in statuses:
        return GateStatus.ENVIRONMENT_NOT_CONFIGURED
    if GateStatus.DATA_GAP in statuses:
        return GateStatus.DATA_GAP
    if GateStatus.FAIL in statuses:
        return GateStatus.FAIL
    return GateStatus.PASS


def _select_slice_payload(
    payload: Mapping[str, Any],
    *,
    slice_id: str | None,
) -> Mapping[str, Any] | None:
    if isinstance(payload.get("testability_slice"), Mapping):
        candidate = payload["testability_slice"]
        if slice_id is None or _slice_id(candidate) == slice_id:
            return candidate
    slices = payload.get("testability_slices") or payload.get("slices")
    if isinstance(slices, Mapping):
        if slice_id is None:
            if "default" in slices and isinstance(slices["default"], Mapping):
                return slices["default"]
            if len(slices) == 1:
                only_value = next(iter(slices.values()))
                if isinstance(only_value, Mapping):
                    return only_value
            return None
        selected = slices.get(slice_id)
        return selected if isinstance(selected, Mapping) else None
    if isinstance(slices, Sequence) and not isinstance(slices, str | bytes | bytearray):
        candidates = [item for item in slices if isinstance(item, Mapping)]
        if slice_id is None:
            return candidates[0] if len(candidates) == 1 else None
        for candidate in candidates:
            if _slice_id(candidate) == slice_id:
                return candidate
    return None


def _slice_id(payload: Mapping[str, Any]) -> str | None:
    return _optional_text(payload.get("slice_id") or payload.get("id"))


def _coerce_idea_draft(value: IdeaDraft | Mapping[str, Any]) -> IdeaDraft:
    if isinstance(value, IdeaDraft):
        return validate_idea_draft(value.to_dict())
    return validate_idea_draft(value)


def _coerce_alpha_spec(value: AlphaSpec | Mapping[str, Any]) -> AlphaSpec:
    if isinstance(value, AlphaSpec):
        return validate_alpha_spec(value.to_dict())
    return validate_alpha_spec(value)


def _coerce_mechanism_card(value: MechanismCard | Mapping[str, Any]) -> MechanismCard:
    if isinstance(value, MechanismCard):
        return validate_mechanism_card(value.to_dict())
    return validate_mechanism_card(value)


def _coerce_setup_spec(value: SetupSpec | Mapping[str, Any] | None) -> SetupSpec | None:
    if value is None:
        return None
    if isinstance(value, SetupSpec):
        return validate_setup_spec(value.to_dict())
    return validate_setup_spec(value)


def _coerce_slice(value: TestabilitySlice | Mapping[str, Any] | None) -> TestabilitySlice | None:
    if value is None:
        return None
    if isinstance(value, TestabilitySlice):
        return value
    return TestabilitySlice.from_mapping(value)


def _coerce_conditioned_power_slice(
    value: SliceSpec | Mapping[str, Any] | None,
) -> SliceSpec | None:
    if value is None:
        return None
    if isinstance(value, SliceSpec):
        return value
    try:
        return SliceSpec.from_mapping(value)
    except SliceSpecError as exc:
        raise TestabilityGateError(
            f"conditioned_power_slice is malformed: {exc}"
        ) from exc


def _pass(check_id: str, message: str, **detail: Any) -> GateCheckResult:
    return GateCheckResult(check_id, GateStatus.PASS, {"message": message, **detail})


def _fail(check_id: str, message: str, **detail: Any) -> GateCheckResult:
    return GateCheckResult(check_id, GateStatus.FAIL, {"message": message, **detail})


def _data_gap(check_id: str, message: str, **detail: Any) -> GateCheckResult:
    return GateCheckResult(check_id, GateStatus.DATA_GAP, {"message": message, **detail})


def _environment_not_configured(
    check_id: str, message: str, **detail: Any
) -> GateCheckResult:
    return GateCheckResult(
        check_id,
        GateStatus.ENVIRONMENT_NOT_CONFIGURED,
        {"message": message, **detail},
    )


def _resolver_rejection_check(
    check_id: str, message: str, exc: RuntimeInputResolverError
) -> GateCheckResult:
    """Classify a resolver rejection: env-precondition vs genuine DATA_GAP.

    Defense-in-depth backstop for the entrypoint preflight. When the resolver's
    typed reason carries the data-root precondition code, the cause is an unmet
    ENVIRONMENT precondition (e.g. an unresolvable ALPHA_DATA_ROOT) and is
    classified ENVIRONMENT_NOT_CONFIGURED -- NOT DATA_GAP. A valid root with a
    genuinely-absent partition (any other reason code) still yields DATA_GAP, so
    the honest absent-data case is unchanged.
    """

    reason = exc.reason.to_dict()
    if reason.get("code") == DATA_ROOT_PRECONDITION_CODE:
        return _environment_not_configured(
            check_id,
            "data root environment precondition is unmet (not a data gap)",
            reason=reason,
        )
    return _data_gap(check_id, message, reason=reason)


def _partition_id(mapping: Mapping[str, Any]) -> str | None:
    direct = _optional_text(mapping.get("partition_id"))
    if direct is not None:
        return direct
    partition_scope = mapping.get("partition_scope")
    if isinstance(partition_scope, Mapping):
        return _optional_text(partition_scope.get("partition_id"))
    return None


def _text_tuple(value: object, *, field: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        text = _optional_text(value)
        return () if text is None else (text,)
    if not isinstance(value, Sequence) or isinstance(value, bytes | bytearray):
        raise TestabilityGateError(f"{field} must be a list of strings")
    output: list[str] = []
    for index, item in enumerate(value):
        text = _optional_text(item)
        if text is None:
            raise TestabilityGateError(f"{field}[{index}] must be non-empty text")
        output.append(text)
    return tuple(output)


def _observation_tuple(value: object) -> tuple[Mapping[str, Any], ...]:
    if value is None:
        return ()
    if not isinstance(value, Sequence) or isinstance(value, str | bytes | bytearray):
        raise TestabilityGateError("path_label_observations must be a list of mappings")
    rows: list[Mapping[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise TestabilityGateError(f"path_label_observations[{index}] must be a mapping")
        rows.append(dict(item))
    return tuple(rows)


def _class_counts(value: object) -> Mapping[str, int] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise TestabilityGateError("path_label_class_counts must be a mapping")
    counts: dict[str, int] = {}
    for key, item in value.items():
        try:
            count = int(item)  # type: ignore[arg-type]
        except (TypeError, ValueError) as exc:
            raise TestabilityGateError("path_label_class_counts values must be integers") from exc
        if count < 0:
            raise TestabilityGateError("path_label_class_counts values must be non-negative")
        counts[str(key)] = count
    return counts


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _optional_int(value: object) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _optional_float(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _optional_bool(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def _int(value: object) -> int:
    if isinstance(value, bool) or value is None:
        return 0
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def _datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        active = value
    elif isinstance(value, str):
        try:
            active = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if active.tzinfo is None or active.utcoffset() is None:
        return None
    return active.astimezone(UTC)


def _jsonish(value: object) -> object:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, Mapping):
        return {str(key): _jsonish(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, bytes | bytearray | str):
        return [_jsonish(item) for item in value]
    if hasattr(value, "to_dict"):
        return _jsonish(value.to_dict())  # type: ignore[no-any-return]
    return str(value)


__all__ = [
    "CHECK_FEATURES_MATERIALIZED",
    "CHECK_LABELS_EXIST",
    "CHECK_N_EFF_MDE_DEDUP",
    "CHECK_NO_LOOKAHEAD_SURROGATE",
    "CHECK_ORDER",
    "CHECK_PATH_LABEL_TWO_CLASS",
    "GateCheckResult",
    "GateStatus",
    "TestabilityGateError",
    "TestabilityGateResult",
    "TestabilitySlice",
    "evaluate_testability_gate",
    "slice_spec_from_idea_payload",
    "summarize_label_class_balance",
]
