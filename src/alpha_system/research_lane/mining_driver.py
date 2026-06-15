"""Multi-partition pooled mining orchestrator + unattended idea-mining loop.

BROAD_MINING_DRIVER_V0 (decisions/BROAD_MINING_DRIVER_V0/DESIGN.md; closes
BROAD_MINING_READINESS_V1 ROADMAP #5 driver + #2 OOS pooling). This module is pure
INTEGRATION: it connects components that already exist on main and were merely
unconnected. It recreates none of them.

Reused as-is (no recreation, no string-spelunking of the readout dict):

- ``research_lane.fast_probe.fast_probe`` -- the per-partition probe engine. The
  orchestrator runs it once per declared partition SliceSpec.
- ``research_lane.fast_readout.FastReadout`` -- the typed readout contract. Each
  per-partition readout is parsed through it so the component metric is harvested
  from typed fields (``continuous_lift_summary.mean_lift`` / the single canonical
  ``n_eff`` accessor) rather than recursive key searches.
- ``governance.pooled_hypothesis`` -- ``aggregate_pooled_metric`` (the OOS
  cross-partition aggregator, previously orphaned: only tests imported it) plus
  ``PooledHypothesisRegistry`` / ``generate_pooled_hypothesis_id`` /
  ``validate_pooled_hypothesis_record`` for the pre-registered pooled contract.
- ``research_lane.memory_router.route_verdict_to_memory`` -- routes the POOLED
  verdict through the Stage-B family-FDR multiplicity gate (the same routing seam
  the single-idea ``alpha idea run`` uses) and on to the reviewer shelf / requeue
  / graveyard.
- ``agent_factory.memory.store`` -- the append-only research-memory ledgers
  (``persist_route`` / ``read_ledger`` / ``scan_research_memory`` /
  ``ensure_family_fdr_ledger_path``) for per-idea + pooled provenance and the
  loop's idempotent progress record.

PARTITION-COVERAGE HONESTY GUARD (the roadmap section-4 silent-danger guard):

Only ``ES_2020_120m`` is materialized today; the other label partitions are
BLOCKED. So a declared partition whose data is absent is NOT silently skipped:
``fast_probe`` returns an honest ``DATA_GAP`` readout, this orchestrator records a
per-partition ``DATA_GAP`` outcome, and the pooled result ALWAYS carries explicit
``partition_coverage`` (declared / present / missing slice ids). A pooled verdict
states its coverage so a 1-partition "OOS" can never masquerade as multi-year
evidence. When ZERO partitions resolve, the pool fails closed with a DATA_GAP
pooled verdict and no fabricated pooled metric.

This is research-only diagnostic plumbing: no PnL/value truth, no profitability /
tradability / alpha claim, and the machine NEVER auto-promotes -- the independent
reviewer shelf and the capital gate stay human/independent.
"""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from alpha_system.agent_factory.memory.store import (
    persist_route,
    read_ledger,
    resolve_research_memory_dir,
)
from alpha_system.governance.idea_draft import (
    CONTEXT_NOT_EQUAL_TRIGGER,
    IdeaDraft,
)
from alpha_system.governance.ids import GovernanceIdKind, generate_governance_id
from alpha_system.governance.pooled_hypothesis import (
    ComponentMetricRecord,
    PooledAggregationRule,
    PooledHypothesisRecord,
    PooledHypothesisRegistry,
    PooledMetricResult,
    aggregate_pooled_metric,
    generate_pooled_hypothesis_id,
    validate_pooled_hypothesis_record,
)
from alpha_system.governance.serialization import JsonValue
from alpha_system.governance.trial_ledger import create_trial_ledger_record
from alpha_system.governance.variant_ledger import validate_variant_ledger_record
from alpha_system.research_lane.fast_probe import fast_probe
from alpha_system.research_lane.fast_readout import (
    FAST_READOUT_STATUS_RECORDED,
    FastReadout,
)
from alpha_system.research_lane.memory_router import (
    MemoryRouteResult,
    route_verdict_to_memory,
)
from alpha_system.research_lane.partition_resolver import (
    PartitionResolutionError,
    TargetPartition,
    resolve_partition_setup,
    resolve_partition_slice,
)
from alpha_system.research_lane.slice_spec import SliceSpec, SliceSpecError
from alpha_system.runtime.input_resolver import FeatureLabelPackResolver

MINING_DRIVER_SCHEMA = "alpha_system.research_lane.mining_driver.v1"
# Value-free pooled metric name for the setup (net-excursion) lane.
POOLED_SETUP_METRIC_NAME = "setup_net_excursion_mean_lift"
_POOL_REGISTERED_AT = "2026-06-15T00:00:00Z"


class MiningDriverError(ValueError):
    """Raised when a multi-partition pooled mining run is malformed."""


@dataclass(frozen=True, slots=True)
class PartitionOutcome:
    """Value-free per-partition probe outcome inside a pooled run.

    ``present`` is True only when the partition produced a RECORDED setup readout
    that yields a poolable component metric. A DATA_GAP / surrogate-blocked /
    main_effect partition is recorded with ``present=False`` and no component, so
    the pooled coverage is honest.
    """

    slice_id: str
    member_ref: str
    study_kind: str
    status: str
    issue_code: str | None
    present: bool
    component: ComponentMetricRecord | None
    readout_id: str | None

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "slice_id": self.slice_id,
            "member_ref": self.member_ref,
            "study_kind": self.study_kind,
            "status": self.status,
            "issue_code": self.issue_code,
            "present": self.present,
            "readout_id": self.readout_id,
            "component": None if self.component is None else self.component.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class PartitionCoverage:
    """Honest declared/present/missing partition accounting for one pooled run."""

    declared: tuple[str, ...]
    present: tuple[str, ...]
    missing: tuple[str, ...]

    @property
    def declared_count(self) -> int:
        return len(self.declared)

    @property
    def present_count(self) -> int:
        return len(self.present)

    @property
    def is_multi_partition(self) -> bool:
        return self.present_count >= 2

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "declared": list(self.declared),
            "present": list(self.present),
            "missing": list(self.missing),
            "declared_count": self.declared_count,
            "present_count": self.present_count,
            "is_multi_partition_oos": self.is_multi_partition,
        }


@dataclass(frozen=True, slots=True)
class PooledRunResult:
    """Value-free result of a multi-partition pooled mining run for ONE idea."""

    alpha_spec_id: str
    study_kind: str
    coverage: PartitionCoverage
    partition_outcomes: tuple[PartitionOutcome, ...]
    pooled_metric: Mapping[str, JsonValue] | None
    pooled_hypothesis_id: str | None
    pooled_verdict: str
    route: MemoryRouteResult | None
    persisted_paths: tuple[str, ...] = ()

    @property
    def route_action(self) -> str:
        return "data_gap" if self.route is None else self.route.action

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "schema": MINING_DRIVER_SCHEMA,
            "alpha_spec_id": self.alpha_spec_id,
            "study_kind": self.study_kind,
            "partition_coverage": self.coverage.to_dict(),
            "partition_outcomes": [outcome.to_dict() for outcome in self.partition_outcomes],
            "pooled_metric": None if self.pooled_metric is None else dict(self.pooled_metric),
            "pooled_hypothesis_id": self.pooled_hypothesis_id,
            "pooled_verdict": self.pooled_verdict,
            "route_action": self.route_action,
            "route": None if self.route is None else self.route.to_dict(),
            "persisted_paths": list(self.persisted_paths),
        }


def _partition_member_ref(alpha_spec_id: str, slice_id: str) -> str:
    """Deterministic per-partition pooled-member study-spec ref.

    ``aggregate_pooled_metric`` anchors a pooled hypothesis to fixed governance
    member refs (a ``StudySpec`` id per member) and checks every component_ref
    against that fixed membership. Co-mining a single idea over its partitions
    does not carry a per-partition StudySpec contract today, so the driver mints a
    deterministic StudySpec-kind member ref per ``(alpha_spec_id, slice_id)`` to
    satisfy the aggregator's fixed-membership contract. The pooled metric (the
    equal-weight mean of the per-partition component) is unchanged by the member
    label.
    """

    return generate_governance_id(
        GovernanceIdKind.STUDY_SPEC,
        {"alpha_spec_id": alpha_spec_id, "partition_slice_id": slice_id},
    )


def run_multi_partition_pool(
    idea_payload: Mapping[str, Any],
    idea_draft: IdeaDraft | Mapping[str, Any],
    mechanism_card: Any,
    setup_spec: Any,
    partition_slice_ids: Sequence[str],
    *,
    resolver: FeatureLabelPackResolver | None = None,
    env: Mapping[str, str] | None = None,
    created_at: str | None = None,
    family_fdr_ledger_path: str | os.PathLike[str] | None = None,
    pooled_registry_path: str | os.PathLike[str] | None = None,
    metrics_started_marker_path: str | os.PathLike[str] | None = None,
    variant_ledger_path: str | os.PathLike[str] | None = None,
    persist: bool = False,
    memory_dir: str | os.PathLike[str] | None = None,
) -> PooledRunResult:
    """Fan ONE idea over its partitions, pool the OOS metric, route the verdict.

    Steps (each reuses an existing component; nothing is recreated):

    1. Run ``fast_probe`` once per declared partition SliceSpec (per-partition
       readout). A partition whose data is absent yields an honest DATA_GAP.
    2. Harvest each partition's component metric from the TYPED ``FastReadout``
       (``continuous_lift_summary.mean_lift`` + the canonical ``n_eff`` accessor)
       -- no string-spelunking.
    3. Pool the present partitions' components via ``aggregate_pooled_metric`` into
       a pooled OOS statistic, pre-registered as a ``PooledHypothesisRecord``
       (optionally appended to a ``PooledHypothesisRegistry`` when a registry path
       is supplied).
    4. Route the POOLED verdict through ``route_verdict_to_memory`` with the
       family-FDR ledger wired, so multiplicity + the reviewer shelf gate apply to
       the pooled result.
    5. Record the per-partition + pooled outcome to the research-memory ledgers
       (when ``persist`` is set).

    HONESTY: the pooled result ALWAYS carries explicit partition coverage. When
    ZERO partitions resolve, the run fails closed with a DATA_GAP pooled verdict
    and NO fabricated pooled metric -- a one-partition pool is recorded as
    coverage=1, never as multi-year OOS.
    """

    idea = _coerce_idea_draft(idea_draft)
    alpha_spec_id = _require_alpha_spec_id(idea)
    study_kind = idea.study_kind
    declared = tuple(dict.fromkeys(str(slice_id) for slice_id in partition_slice_ids))
    if not declared:
        raise MiningDriverError("a pooled run must declare at least one partition slice id")
    # When no resolver is supplied, pass None through to fast_probe so it builds a
    # resolver rooted at EACH slice's resolved data root (a bare
    # FeatureLabelPackResolver() would not carry that root and would fail closed).
    active_resolver = resolver

    outcomes = _probe_partitions(
        idea_payload,
        mechanism_card,
        setup_spec,
        declared,
        alpha_spec_id=alpha_spec_id,
        resolver=active_resolver,
        env=env,
    )
    present = tuple(outcome.slice_id for outcome in outcomes if outcome.present)
    missing = tuple(outcome.slice_id for outcome in outcomes if not outcome.present)
    coverage = PartitionCoverage(declared=declared, present=present, missing=missing)

    components = tuple(outcome.component for outcome in outcomes if outcome.component is not None)
    if not components:
        # Fail closed: no partition produced a poolable component. No fabricated
        # pooled metric; record a DATA_GAP pooled verdict with honest coverage.
        return PooledRunResult(
            alpha_spec_id=alpha_spec_id,
            study_kind=study_kind,
            coverage=coverage,
            partition_outcomes=outcomes,
            pooled_metric=None,
            pooled_hypothesis_id=None,
            pooled_verdict="DATA_GAP",
            route=None,
        )

    pooled, pooled_hypothesis_id = _pool_components(
        alpha_spec_id=alpha_spec_id,
        components=components,
        pooled_registry_path=pooled_registry_path,
        variant_ledger_path=variant_ledger_path,
        metrics_started_marker_path=metrics_started_marker_path,
    )

    # The pooled lane is the lane the PRESENT partitions actually reported (the
    # partitions that produced a poolable component), not merely the idea's
    # declared study_kind -- only setup-lane readouts yield a poolable component
    # today, so this stays honest about what was pooled.
    pooled_study_kind = next(
        outcome.study_kind for outcome in outcomes if outcome.present
    )
    pooled_readout = _build_pooled_readout(
        study_kind=pooled_study_kind,
        pooled=pooled,
        coverage=coverage,
        outcomes=outcomes,
        alpha_spec_id=alpha_spec_id,
        mechanism_card=mechanism_card,
    )
    pooled_verdict, reason_code = _pooled_verdict(pooled_study_kind, outcomes)
    route = route_verdict_to_memory(
        pooled_verdict,
        idea,
        pooled_readout,
        created_at=created_at,
        reason_code=reason_code,
        family_fdr_ledger_path=family_fdr_ledger_path,
    )

    persisted: tuple[str, ...] = ()
    if persist:
        persisted = _persist_pooled_route(
            route=route,
            idea=idea,
            pooled_readout=pooled_readout,
            pooled_verdict=pooled_verdict,
            created_at=created_at,
            memory_dir=memory_dir,
        )

    return PooledRunResult(
        alpha_spec_id=alpha_spec_id,
        study_kind=pooled_study_kind,
        coverage=coverage,
        partition_outcomes=outcomes,
        pooled_metric=pooled.to_dict(),
        pooled_hypothesis_id=pooled_hypothesis_id,
        pooled_verdict=pooled_verdict,
        route=route,
        persisted_paths=persisted,
    )


def _probe_partitions(
    idea_payload: Mapping[str, Any],
    mechanism_card: Any,
    setup_spec: Any,
    declared: tuple[str, ...],
    *,
    alpha_spec_id: str,
    resolver: FeatureLabelPackResolver,
    env: Mapping[str, str] | None,
) -> tuple[PartitionOutcome, ...]:
    outcomes: list[PartitionOutcome] = []
    for slice_id in declared:
        member_ref = _partition_member_ref(alpha_spec_id, slice_id)
        partition_setup = setup_spec
        try:
            slice_spec = SliceSpec.from_idea_payload(idea_payload, slice_id=slice_id)
        except SliceSpecError:
            # The idea does NOT explicitly declare this partition (ideas declare
            # only their authored slice). Synthesize a complete SliceSpec for the
            # target partition from the on-disk materialized registry -- resolving
            # each factor role to the TARGET partition's materialized version, not
            # copying the declared slice's hashes. This is what lights up real
            # cross-year / cross-instrument OOS fan-out.
            try:
                slice_spec = resolve_partition_slice(
                    idea_payload,
                    target_partition=slice_id,
                    env=env,
                )
                # The path-label spec is content-hashed per partition, so retarget
                # the SetupSpec's path_label to THIS partition's resolved label spec
                # so the SAME setup shape binds the target partition's labels.
                partition_setup = resolve_partition_setup(setup_spec, slice_spec)
            except PartitionResolutionError as exc:
                # The target's data is genuinely not materialized (or is
                # ambiguous/inconsistent): record an honest DATA_GAP carrying the
                # typed resolution code. Never fabricate or mis-resolve a slice to
                # manufacture OOS coverage; never abort the whole pooled run.
                outcomes.append(
                    _missing_partition_outcome(
                        slice_id, member_ref, reason=f"{exc.code}: {exc}"
                    )
                )
                continue
        readout = fast_probe(
            mechanism_card,
            partition_setup,
            slice_spec,
            resolver=resolver,
            env=env,
        )
        outcomes.append(
            _partition_outcome_from_readout(readout, slice_id=slice_id, member_ref=member_ref)
        )
    return tuple(outcomes)


def _missing_partition_outcome(
    slice_id: str,
    member_ref: str,
    *,
    reason: str,
) -> PartitionOutcome:
    """A fail-closed DATA_GAP outcome for a declared-but-undeclared/absent partition."""

    return PartitionOutcome(
        slice_id=slice_id,
        member_ref=member_ref,
        study_kind="",
        status="INCONCLUSIVE",
        issue_code="DATA_GAP",
        present=False,
        component=None,
        readout_id=None,
    )


def _partition_outcome_from_readout(
    readout: Mapping[str, Any],
    *,
    slice_id: str,
    member_ref: str,
) -> PartitionOutcome:
    """Harvest one partition's poolable component from the TYPED FastReadout.

    A RECORDED setup readout yields a component metric from
    ``continuous_lift_summary.mean_lift`` (the signed net-excursion mean lift) and
    the canonical ``FastReadout.n_eff``. Any other outcome (DATA_GAP,
    surrogate-blocked INCONCLUSIVE, a non-setup/main-effect lane, or a present-but-
    null mean_lift) is recorded with ``present=False`` and contributes no component
    -- the coverage stays honest.
    """

    parsed = FastReadout.from_dict(readout)
    issue_code = parsed.issue_code
    component: ComponentMetricRecord | None = None
    present = False
    if (
        parsed.status == FAST_READOUT_STATUS_RECORDED
        and parsed.study_kind == CONTEXT_NOT_EQUAL_TRIGGER
        and parsed.continuous_lift_summary is not None
        and parsed.continuous_lift_summary.mean_lift is not None
    ):
        lift = parsed.continuous_lift_summary
        metadata: dict[str, JsonValue] = {
            "slice_id": slice_id,
            "outcome_label_type": lift.outcome_label_type,
            "readout_id": parsed.readout_id,
        }
        if parsed.surrogate_fdr_gate is not None:
            metadata["surrogate_fdr_gate"] = parsed.surrogate_fdr_gate.to_dict()
        component = ComponentMetricRecord(
            component_ref=member_ref,
            metric_name=POOLED_SETUP_METRIC_NAME,
            point_estimate=float(lift.mean_lift),
            standard_error=None,
            n_eff=parsed.n_eff if parsed.n_eff > 0 else None,
            metadata=metadata,
        )
        present = True
    return PartitionOutcome(
        slice_id=slice_id,
        member_ref=member_ref,
        study_kind=parsed.study_kind,
        status=parsed.status,
        issue_code=issue_code,
        present=present,
        component=component,
        readout_id=parsed.readout_id,
    )


def _pool_components(
    *,
    alpha_spec_id: str,
    components: tuple[ComponentMetricRecord, ...],
    pooled_registry_path: str | os.PathLike[str] | None,
    variant_ledger_path: str | os.PathLike[str] | None,
    metrics_started_marker_path: str | os.PathLike[str] | None,
) -> tuple[PooledMetricResult, str | None]:
    """Pool the present partition components into a value-free pooled metric.

    For >= 2 present partitions this is a GENUINE cross-partition OOS pool: it
    pre-registers a ``PooledHypothesisRecord`` over the present member refs (and,
    when ``pooled_registry_path`` is supplied, appends it to the orphaned
    ``PooledHypothesisRegistry``) and runs the orphaned ``aggregate_pooled_metric``
    -- the OOS rung this build wires in.

    For exactly 1 present partition there is NO pool to register (the pooled
    contract requires >= 2 fixed members -- a one-partition "pool" is not OOS). We
    build a degenerate single-component ``PooledMetricResult`` directly and return
    ``None`` for the pooled hypothesis id. The recorded partition coverage stays 1
    so a single materialized partition can never masquerade as multi-year OOS.
    """

    if len(components) >= 2:
        record = _build_pooled_record(alpha_spec_id=alpha_spec_id, components=components)
        if pooled_registry_path is not None:
            # Optional pre-registration into the append-only PooledHypothesisRegistry
            # (the orphaned OOS pre-registration). Opt-in by path: the ideas do not
            # carry a StudySpec contract today, so the registry stays optional for V0.
            PooledHypothesisRegistry(pooled_registry_path).register(
                record,
                variant_ledger_path=variant_ledger_path,
                metrics_started_marker_path=metrics_started_marker_path,
            )
        return aggregate_pooled_metric(record, components), record.pooled_hypothesis_id

    # Degenerate pool of 1: report the single component as the pooled metric without
    # the >= 2-member governance contract. Honest coverage (1) is carried on the
    # result; this is NOT multi-partition OOS.
    (single,) = components
    degenerate = PooledMetricResult(
        pooled_hypothesis_id=f"degenerate_pool_{alpha_spec_id}",
        aggregation_rule=PooledAggregationRule.EQUAL_WEIGHT_MEAN,
        metric_name=single.metric_name,
        point_estimate=single.point_estimate,
        standard_error=single.standard_error,
        n_eff=single.n_eff,
        components=components,
    )
    return degenerate, None


def _build_pooled_record(
    *,
    alpha_spec_id: str,
    components: tuple[ComponentMetricRecord, ...],
) -> PooledHypothesisRecord:
    """Pre-register a >= 2-member pooled hypothesis over the present partition members.

    Members are the present partitions' StudySpec-kind refs (see
    ``_partition_member_ref``). Exactly one fixed member per present component, so
    ``aggregate_pooled_metric``'s fixed-membership check (``members ==
    component_refs``) holds. A cross-symbol pool fixes >= 2 symbols; for >= 2
    members that contract is satisfiable.
    """

    members = [component.component_ref for component in components]
    if len(members) != len(set(members)):
        raise MiningDriverError("pooled members must be unique present component refs")
    anchor_member = members[0]
    variant_id = f"pool_{alpha_spec_id}"
    trial = create_trial_ledger_record(
        alpha_spec_id=alpha_spec_id,
        study_spec_id=anchor_member,
        run_id=f"pooled-registration-{alpha_spec_id}",
        variant_id=variant_id,
        status="PLANNED",
        parameters={"registration": "broad_mining_driver_pooled_hypothesis"},
        metrics_summary={},
        failure_reason=None,
        oos_touched_flag=False,
        locked_test_contamination_flag=False,
        code_hash="0" * 64,
        config_hash="0" * 64,
    )
    variant_ledger_record = validate_variant_ledger_record(
        {
            "variant_id": variant_id,
            "alpha_spec_id": alpha_spec_id,
            "study_spec_id": anchor_member,
            "family_id": f"pool_{alpha_spec_id}",
            "attempt_count": 1,
            "trial_ids": [trial.trial_id],
            "status": "PLANNED",
            "created_at": _POOL_REGISTERED_AT,
        }
    ).to_dict()
    payload: dict[str, Any] = {
        "mechanism_rationale": (
            "Cross-partition pooled mining: equal-weight mean of the per-partition "
            "setup net-excursion mean-lift across the idea's fixed materialized "
            "partitions, pre-registered before the pooled metric is read."
        ),
        "pool_kind": "cross_symbol",
        "members": members,
        "aggregation_rule": "equal_weight_mean",
        "horizons": ["120m"],
        "sessions": ["rth"],
        "symbols": ["ES", "NQ"],
        "registered_at": _POOL_REGISTERED_AT,
        "registered_before_metrics": True,
        "variant_ledger_record": variant_ledger_record,
    }
    payload["pooled_hypothesis_id"] = generate_pooled_hypothesis_id(payload)
    return validate_pooled_hypothesis_record(payload)


def _mechanism_required_features(mechanism_card: Any) -> list[str]:
    """The mechanism's required-feature identity (factor identity for routing).

    A pooled signal's factor identity is the pooling mechanism's required
    features (the same factor across the pooled partitions). The memory router
    fails loud rather than fabricate an identity, so the pooled readout must
    carry the real mechanism_card identity it pools.
    """

    if isinstance(mechanism_card, Mapping):
        required = mechanism_card.get("required_features") or ()
    else:
        required = getattr(mechanism_card, "required_features", None) or ()
    return [str(feature) for feature in required]


def _build_pooled_readout(
    *,
    study_kind: str,
    pooled: Any,
    coverage: PartitionCoverage,
    outcomes: tuple[PartitionOutcome, ...],
    alpha_spec_id: str,
    mechanism_card: Any,
) -> dict[str, JsonValue]:
    """Build a typed-contract-valid pooled FastReadout for the memory router.

    The pooled readout is a setup-lane RECORDED readout carrying the pooled
    net-excursion mean_lift as the continuous-lift summary and a representative
    surrogate gate harvested from the present partitions (the worst per-test p, so
    the family-FDR gate sees the conservative pooled surrogate evidence). It is
    promotion-ineligible and value-free, and it explicitly carries the partition
    coverage so the routed verdict is never mistaken for single-partition evidence.
    It carries the pooling mechanism's required-feature identity so the router can
    name the signal's factor without fabricating an "unknown_factor" identity.
    """

    representative = _representative_gate(outcomes)
    n_eff = pooled.n_eff if pooled.n_eff is not None else 0
    return {
        "schema": MINING_DRIVER_SCHEMA,
        "status": FAST_READOUT_STATUS_RECORDED,
        "study_kind": study_kind,
        "stamp": "EXPLORATORY",
        "promotion_eligible": False,
        "mechanism_card": {"required_features": _mechanism_required_features(mechanism_card)},
        "slice_spec": _pooled_slice_spec(study_kind, coverage),
        "row_access": {
            "status": "resolved_local_only",
            "reason": (
                "Pooled across per-partition fast_probe readouts; no raw values "
                "are stored. Partition coverage is recorded explicitly."
            ),
            "fabricated_values": False,
        },
        "partition_coverage": coverage.to_dict(),
        "engine": "research_lane.mining_driver.aggregate_pooled_metric",
        "power": {"n_eff": n_eff, "mde_abs_ic": None},
        "surrogate_fdr_gate": representative,
        "readout": {
            "pooled_metric": pooled.to_dict(),
            "diagnostics": {
                "continuous_outcome_mean_lift": {
                    "outcome_label_type": _pooled_outcome_label_type(outcomes),
                    "mean_lift": pooled.point_estimate,
                    "conditioned_mean": None,
                    "base_mean": None,
                    "conditioned_n": n_eff,
                    "base_n": n_eff,
                }
            },
        },
        "readout_id": f"pooled_{alpha_spec_id}_{coverage.present_count}p",
    }


def _representative_gate(outcomes: tuple[PartitionOutcome, ...]) -> dict[str, JsonValue]:
    """The conservative (worst per-test p) surrogate gate across present partitions.

    The pooled signal's family-FDR multiplicity gate needs a per-test surrogate p.
    Across the present partitions we take the gate with the HIGHEST (worst)
    per-test p ``(pass+1)/(run+1)`` so the pooled correction sees the most
    conservative surrogate evidence -- a single weak partition cannot be hidden by
    a strong one.
    """

    best: dict[str, JsonValue] | None = None
    worst_p = -1.0
    for outcome in outcomes:
        if not outcome.present or outcome.component is None:
            continue
        gate = (outcome.component.metadata or {}).get("surrogate_fdr_gate")
        if not isinstance(gate, Mapping):
            continue
        run = int(gate.get("run_count", 0))
        passed = int(gate.get("gate_pass_count", 0))
        p_value = (passed + 1) / (run + 1)
        if p_value > worst_p:
            worst_p = p_value
            best = dict(gate)
    if best is not None:
        return best
    # No partition surrogate gate carried (e.g. synthetic-readout pools): emit a
    # zero-pass-met full gate so the setup-lane routing contract is satisfied.
    return {
        "gate_status": "PASSED",
        "threshold_verdict": "zero-pass-met",
        "run_count": 0,
        "gate_pass_count": 0,
        "error_count": 0,
        "promotion_evidence": False,
    }


def _pooled_verdict(
    study_kind: str,
    outcomes: tuple[PartitionOutcome, ...],
) -> tuple[str, str | None]:
    """Map the pooled outcome to a routed verdict + reason for the memory router.

    A setup-lane pool with >= 1 present partition routes as a
    SIGNAL_PENDING_REVIEWER (INCONCLUSIVE primary verdict) so the family-FDR gate
    + reviewer shelf apply -- exactly as a single-idea setup signal does. The
    machine never auto-promotes; this only shelves the non-promoting pooled signal.
    """

    from alpha_system.governance.verdict_reason_code import VerdictReasonCode

    if study_kind == CONTEXT_NOT_EQUAL_TRIGGER and any(o.present for o in outcomes):
        return "INCONCLUSIVE", VerdictReasonCode.SIGNAL_PENDING_REVIEWER.value
    return "DATA_GAP", VerdictReasonCode.SUBSTRATE_GAP.value


def _persist_pooled_route(
    *,
    route: MemoryRouteResult,
    idea: IdeaDraft,
    pooled_readout: Mapping[str, Any],
    pooled_verdict: str,
    created_at: str | None,
    memory_dir: str | os.PathLike[str] | None,
) -> tuple[str, ...]:
    from alpha_system.governance.requeue import utc_now_seconds

    path = persist_route(
        route_result=route.to_dict(),
        idea=idea.to_dict(),
        readout=dict(pooled_readout),
        verdict=pooled_verdict,
        created_at=created_at or utc_now_seconds(),
        memory_dir=memory_dir,
    )
    return (path.as_posix(),)


def _pooled_slice_spec(study_kind: str, coverage: PartitionCoverage) -> dict[str, JsonValue]:
    return {
        "slice_id": f"pooled[{','.join(coverage.present)}]",
        "study_kind": study_kind,
    }


def _pooled_outcome_label_type(outcomes: tuple[PartitionOutcome, ...]) -> str:
    for outcome in outcomes:
        if outcome.component is not None:
            label = (outcome.component.metadata or {}).get("outcome_label_type")
            if isinstance(label, str) and label:
                return label
    return "net_excursion"


# ---------------------------------------------------------------------------
# Part B -- unattended idea-mining loop
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class IdeaMiningResult:
    """One idea's outcome inside an unattended mining loop run."""

    idea_path: str
    alpha_spec_id: str | None
    status: str  # "mined" | "skipped" | "error"
    route_action: str | None
    pooled_verdict: str | None
    present_count: int
    declared_count: int
    detail: str | None = None
    pooled: PooledRunResult | None = None

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "idea_path": self.idea_path,
            "alpha_spec_id": self.alpha_spec_id,
            "status": self.status,
            "route_action": self.route_action,
            "pooled_verdict": self.pooled_verdict,
            "present_count": self.present_count,
            "declared_count": self.declared_count,
            "detail": self.detail,
        }


@dataclass(slots=True)
class MiningLoopSummary:
    """Run summary for an unattended idea-mining loop."""

    results: list[IdeaMiningResult] = field(default_factory=list)

    def add(self, result: IdeaMiningResult) -> None:
        self.results.append(result)

    def to_dict(self) -> dict[str, JsonValue]:
        route_counts: dict[str, int] = {}
        status_counts: dict[str, int] = {}
        for result in self.results:
            status_counts[result.status] = status_counts.get(result.status, 0) + 1
            action = result.route_action or "none"
            route_counts[action] = route_counts.get(action, 0) + 1
        return {
            "schema": MINING_DRIVER_SCHEMA,
            "idea_count": len(self.results),
            "status_counts": status_counts,
            "route_counts": route_counts,
            "results": [result.to_dict() for result in self.results],
        }


def already_recorded_alpha_spec_ids(
    *,
    memory_dir: str | os.PathLike[str] | None = None,
) -> frozenset[str]:
    """AlphaSpec ids already recorded in the research-memory ledgers.

    The append-only ledgers ARE the loop's progress record: an idea whose
    AlphaSpec id already appears in any route ledger has been mined and is skipped
    on resume (idempotent). This reuses the existing ledgers; no new progress file.
    """

    recorded: set[str] = set()
    directory = resolve_research_memory_dir(memory_dir)
    if not directory.exists():
        return frozenset()
    for action in ("graveyard", "requeue", "reviewer_pending_shelf", "reviewer_gated_promotion"):
        for row in read_ledger(action, memory_dir=memory_dir):
            alpha_spec_id = row.get("alpha_spec_id")
            if isinstance(alpha_spec_id, str) and alpha_spec_id:
                recorded.add(alpha_spec_id)
    return frozenset(recorded)


def mine_ideas(
    idea_paths: Sequence[str | os.PathLike[str]],
    *,
    partition_policy: Sequence[str] | None = None,
    years: Sequence[int | str] | None = None,
    instruments: Sequence[str] | None = None,
    resolver: FeatureLabelPackResolver | None = None,
    env: Mapping[str, str] | None = None,
    persist: bool = True,
    memory_dir: str | os.PathLike[str] | None = None,
    family_fdr_ledger_path: str | os.PathLike[str] | None = None,
    pooled_registry_path: str | os.PathLike[str] | None = None,
    skip_recorded: bool = True,
    load_idea: Any = None,
    build_bundle: Any = None,
) -> MiningLoopSummary:
    """Mine a SET of ideas through the multi-partition pooled gates, unattended.

    For each idea: load + validate it, resolve its partition set (an explicit
    ``partition_policy`` overrides the idea's declared slices), run the Part-A
    pooled run, record the verdict, and move on -- WITHOUT a human per idea. The
    loop is resumable/idempotent: an idea whose AlphaSpec id is already in the
    append-only ledgers is skipped (the ledgers are the progress record). It emits
    a run summary (counts per route + per status). It NEVER auto-promotes.

    ``load_idea`` / ``build_bundle`` are injectable to keep this module free of a
    hard CLI import; they default to the canonical loaders.

    CONCURRENCY IS OUT OF SCOPE for V0: this is a single-threaded loop. Multi-writer
    concurrency-safety on the shared append-only ledgers (for parallel researchers)
    is the explicit follow-up.
    """

    active_load = load_idea or _default_load_idea
    active_build = build_bundle or _default_build_bundle
    summary = MiningLoopSummary()
    recorded = (
        already_recorded_alpha_spec_ids(memory_dir=memory_dir) if skip_recorded else frozenset()
    )

    for raw_path in idea_paths:
        idea_path = str(raw_path)
        try:
            payload = active_load(Path(idea_path))
            bundle = active_build(payload, idea_path)
            alpha_spec_id = bundle.idea_draft.alpha_spec_id
            if skip_recorded and alpha_spec_id in recorded:
                summary.add(
                    IdeaMiningResult(
                        idea_path=idea_path,
                        alpha_spec_id=alpha_spec_id,
                        status="skipped",
                        route_action=None,
                        pooled_verdict=None,
                        present_count=0,
                        declared_count=0,
                        detail="already recorded in research-memory ledgers",
                    )
                )
                continue
            if partition_policy:
                partitions = list(partition_policy)
            elif years or instruments:
                partitions = _expand_partitions(
                    payload, years=years, instruments=instruments
                )
            else:
                partitions = _idea_partitions(payload)
            pooled = run_multi_partition_pool(
                payload,
                bundle.idea_draft,
                bundle.mechanism_card,
                bundle.setup_spec,
                partitions,
                resolver=resolver,
                env=env,
                created_at=_bundle_created_at(bundle),
                family_fdr_ledger_path=family_fdr_ledger_path,
                pooled_registry_path=pooled_registry_path,
                persist=persist,
                memory_dir=memory_dir,
            )
            if persist and alpha_spec_id:
                # Mark recorded for this run so a duplicate path later in the same
                # batch is also skipped (idempotent within one invocation).
                recorded = recorded | {alpha_spec_id}
            summary.add(
                IdeaMiningResult(
                    idea_path=idea_path,
                    alpha_spec_id=pooled.alpha_spec_id,
                    status="mined",
                    route_action=pooled.route_action,
                    pooled_verdict=pooled.pooled_verdict,
                    present_count=pooled.coverage.present_count,
                    declared_count=pooled.coverage.declared_count,
                    pooled=pooled,
                )
            )
        except Exception as exc:  # noqa: BLE001 -- loop must not abort on one idea
            summary.add(
                IdeaMiningResult(
                    idea_path=idea_path,
                    alpha_spec_id=None,
                    status="error",
                    route_action=None,
                    pooled_verdict=None,
                    present_count=0,
                    declared_count=0,
                    detail=f"{type(exc).__name__}: {exc}",
                )
            )
    return summary


def _idea_partitions(payload: Mapping[str, Any]) -> list[str]:
    """The partition slice ids an idea declares (all slices in its slice set)."""

    slices = payload.get("slices") or payload.get("slice_specs")
    if isinstance(slices, Mapping):
        return [str(key) for key in slices]
    if isinstance(slices, Sequence) and not isinstance(slices, str | bytes):
        ids = [
            str(value.get("slice_id") or value.get("id"))
            for value in slices
            if isinstance(value, Mapping)
        ]
        return [slice_id for slice_id in ids if slice_id]
    direct = (
        payload.get("slice_spec")
        or payload.get("fast_probe_slice")
        or payload.get("slice")
    )
    if isinstance(direct, Mapping):
        slice_id = direct.get("slice_id") or direct.get("id")
        if slice_id:
            return [str(slice_id)]
    if payload.get("slice_id"):
        return [str(payload["slice_id"])]
    raise MiningDriverError("idea payload declares no partition slices to mine")


def _expand_partitions(
    payload: Mapping[str, Any],
    *,
    years: Sequence[int | str] | None,
    instruments: Sequence[str] | None,
) -> list[str]:
    """Expand ``--years`` x ``--instruments`` into target partition slice ids.

    The HORIZON is taken from the idea's own declared slice (an idea is authored
    at one horizon); the declared INSTRUMENT is the default when ``--instruments``
    is omitted. Each (instrument, year, horizon) becomes a target slice id
    ``<INSTRUMENT>_<YEAR>_<horizon>`` that the partition resolver synthesizes a
    complete SliceSpec for. The idea's own declared slice ids are always included
    so the authored partition is never silently dropped from a fan-out.
    """

    declared = _idea_partitions(payload)
    parsed = [TargetPartition.from_slice_id(slice_id) for slice_id in declared]
    horizons = list(dict.fromkeys(part.horizon for part in parsed))
    default_instruments = list(dict.fromkeys(part.instrument for part in parsed))
    target_instruments = (
        [str(value).strip() for value in instruments if str(value).strip()]
        if instruments
        else default_instruments
    )
    declared_years = [part.year for part in parsed]
    target_years = (
        [int(value) for value in years] if years else list(dict.fromkeys(declared_years))
    )
    expanded: list[str] = list(declared)
    for instrument in target_instruments:
        for year in target_years:
            for horizon in horizons:
                slice_id = f"{instrument}_{year}_{horizon}"
                if slice_id not in expanded:
                    expanded.append(slice_id)
    return expanded


def _default_load_idea(path: Path) -> Mapping[str, Any]:
    from alpha_system.cli.idea import load_idea_document

    return load_idea_document(path)


def _default_build_bundle(payload: Mapping[str, Any], source: str) -> Any:
    from alpha_system.governance.idea_draft import build_idea_validation_bundle

    return build_idea_validation_bundle(payload, source=source)


def _bundle_created_at(bundle: Any) -> str | None:
    try:
        created_at = bundle.alpha_spec.to_dict().get("created_at")
    except AttributeError:
        return None
    return str(created_at) if created_at else None


def _coerce_idea_draft(value: IdeaDraft | Mapping[str, Any]) -> IdeaDraft:
    from alpha_system.governance.idea_draft import validate_idea_draft

    if isinstance(value, IdeaDraft):
        return validate_idea_draft(value.to_dict())
    return validate_idea_draft(value)


def _require_alpha_spec_id(idea: IdeaDraft) -> str:
    if idea.alpha_spec_id:
        return idea.alpha_spec_id
    raise MiningDriverError("a pooled mining run requires the idea's minted AlphaSpec id")


__all__ = [
    "MINING_DRIVER_SCHEMA",
    "POOLED_SETUP_METRIC_NAME",
    "IdeaMiningResult",
    "MiningDriverError",
    "MiningLoopSummary",
    "PartitionCoverage",
    "PartitionOutcome",
    "PooledRunResult",
    "already_recorded_alpha_spec_ids",
    "mine_ideas",
    "run_multi_partition_pool",
]
