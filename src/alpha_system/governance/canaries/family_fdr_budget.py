"""Cross-idea multiplicity canary for the family-FDR correction (Stage A).

Guards ``governance/family_fdr_correction.py`` against silent drift in the
multiplicity math. It asserts three things the independent reviewer rail relies
on:

1. **Textbook BH / Bonferroni.** On the classic Benjamini-Hochberg (1995)
   p-value vector, the step-up BH correction at FDR alpha=0.05 rejects exactly
   the first four nulls, and Bonferroni at FWER alpha=0.05 rejects exactly the
   first three. Hardcoded expected rejection sets.

2. **The historical pa_setup REWORK reproduces deterministically.** The first
   shelved setup signal (``prior_session_high_sweep_and_reclaim``, ES_2020_120m,
   net_excursion) was 1 of a co-mined batch of m=7 sibling pa_setup ideas with a
   per-test surrogate p ``(0+1)/(64+1) = 0.0153846`` at run_count=64. The
   reviewer adjudicated REWORK because 64 surrogates cannot even RESOLVE a passing
   corrected p (finest resolvable p ``1/65`` > Bonferroni ``0.05/7 = 0.0071``).
   This canary asserts the gate now reaches the SAME conclusion without a human:
   ``resolution_adequate == False`` AND ``eligible == False``. It checks both the
   m=7 (all siblings) and m=5 (net_excursion-only) interpretations -- the signal
   is not-eligible under both; m=7 is the reviewer's primary reading.

3. **Non-vacuity.** A clearly-significant, resolution-adequate idea (p=0.0001,
   run_count=10000, m=5) is ``eligible == True`` -- the gate is not a constant
   reject.

4. **Co-mined batch GROUPING (the gate-weakening defect).** N co-mined variants
   that DECLARE one shared ``family_id`` but carry DISTINCT ``alpha_spec_id`` s must
   co-correct as ONE m=N family (BH threshold tightened to ``alpha*k/N``), driven
   through the REAL pooled mining-driver path (per-partition probe -> pooled readout
   -> router -> ledger). The historical defect dropped the declared
   ``duplicate_exposure`` in the pooled readout AND anchored the batch key on
   ``alpha_spec_id``, so each variant became a family-of-ONE that paid NO
   cross-variant multiplicity tax (under-correction). This check also asserts the
   COMPLEMENT -- two variants with DIFFERENT declared families stay separate (no
   false-merge).

This is research-only diagnostic plumbing. A passing canary validates the
correction math only and implies NO alpha, profitability, or tradability claim.
The gate is a deterministic RECORD; the machine never auto-promotes.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from alpha_system.governance.family_fdr_correction import (
    FDR_METHOD_BENJAMINI_HOCHBERG,
    FDR_METHOD_BONFERRONI,
    correct_family,
    resolution_adequate,
    surrogate_p_upper_bound,
)

# Classic Benjamini-Hochberg (1995) ordered p-value vector (m = 15).
_BH_1995_P_VALUES: tuple[float, ...] = (
    0.0001,
    0.0004,
    0.0019,
    0.0095,
    0.0201,
    0.0278,
    0.0298,
    0.0344,
    0.0459,
    0.3240,
    0.4262,
    0.5719,
    0.6528,
    0.7590,
    1.0000,
)
# BH step-up at FDR alpha=0.05 rejects the first four (ranks 1..4).
_BH_EXPECTED_REJECTED = frozenset(f"i{index}" for index in range(4))
# Bonferroni at FWER alpha=0.05 (threshold 0.05/15 = 0.003333) rejects the first three.
_BONFERRONI_EXPECTED_REJECTED = frozenset(f"i{index}" for index in range(3))

# Historical pa_setup REWORK numbers (reviewer-confirmed).
_REWORK_SIGNAL_KEY = "prior_session_high_sweep_and_reclaim"
_REWORK_RUN_COUNT = 64
_REWORK_GATE_PASS_COUNT = 0
_REWORK_FAMILY_SIZE_PRIMARY = 7  # all co-mined siblings (reviewer's primary reading)
_REWORK_FAMILY_SIZE_NET_EXCURSION = 5  # the net_excursion-only subset
_REWORK_ALPHA = 0.05
_REWORK_EXPECTED_P = 1.0 / 65.0  # (0 + 1) / (64 + 1) = 0.0153846...


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _check_textbook_corrections() -> None:
    entries = [
        {"idea_key": f"i{index}", "p_value": p_value, "run_count": 1_000_000}
        for index, p_value in enumerate(_BH_1995_P_VALUES)
    ]

    bh_verdicts = correct_family(entries, alpha_fw=0.05, method=FDR_METHOD_BENJAMINI_HOCHBERG)
    bh_rejected = frozenset(v.idea_key for v in bh_verdicts if v.rejected_null)
    _assert(
        bh_rejected == _BH_EXPECTED_REJECTED,
        f"BH textbook mismatch: rejected {sorted(bh_rejected)} != {sorted(_BH_EXPECTED_REJECTED)}",
    )

    bonferroni_verdicts = correct_family(entries, alpha_fw=0.05, method=FDR_METHOD_BONFERRONI)
    bonferroni_rejected = frozenset(v.idea_key for v in bonferroni_verdicts if v.rejected_null)
    _assert(
        bonferroni_rejected == _BONFERRONI_EXPECTED_REJECTED,
        f"Bonferroni textbook mismatch: rejected {sorted(bonferroni_rejected)} != "
        f"{sorted(_BONFERRONI_EXPECTED_REJECTED)}",
    )


def _rework_batch(family_size: int) -> list[dict[str, object]]:
    """Build the historical batch: the signal + (family_size - 1) null siblings.

    The siblings are non-significant by construction (gate_pass_count high) so
    the batch shape matches the reviewer's: one candidate signal among siblings.
    """

    entries: list[dict[str, object]] = [
        {
            "idea_key": _REWORK_SIGNAL_KEY,
            "gate_pass_count": _REWORK_GATE_PASS_COUNT,
            "run_count": _REWORK_RUN_COUNT,
        }
    ]
    for sibling in range(family_size - 1):
        entries.append(
            {
                "idea_key": f"sibling_{sibling}",
                "gate_pass_count": 20,
                "run_count": _REWORK_RUN_COUNT,
            }
        )
    return entries


def _check_historical_rework() -> None:
    # The per-test surrogate p is exactly the reviewer's 1/65.
    observed_p = surrogate_p_upper_bound(_REWORK_GATE_PASS_COUNT, _REWORK_RUN_COUNT)
    _assert(
        abs(observed_p - _REWORK_EXPECTED_P) < 1e-12,
        f"REWORK per-test p {observed_p} != expected 1/65 = {_REWORK_EXPECTED_P}",
    )

    for family_size in (_REWORK_FAMILY_SIZE_PRIMARY, _REWORK_FAMILY_SIZE_NET_EXCURSION):
        # 64 surrogates cannot resolve the corrected per-test threshold.
        _assert(
            resolution_adequate(_REWORK_RUN_COUNT, family_size, _REWORK_ALPHA) is False,
            f"REWORK m={family_size}: 64 surrogates should be resolution-inadequate",
        )
        verdicts = correct_family(
            _rework_batch(family_size),
            alpha_fw=_REWORK_ALPHA,
            method=FDR_METHOD_BONFERRONI,
        )
        signal = next(v for v in verdicts if v.idea_key == _REWORK_SIGNAL_KEY)
        _assert(
            signal.family_size == family_size,
            f"REWORK m={family_size}: family_size {signal.family_size} mismatch",
        )
        _assert(
            abs(signal.p_value - _REWORK_EXPECTED_P) < 1e-12,
            f"REWORK m={family_size}: signal p {signal.p_value} != 1/65",
        )
        _assert(
            signal.resolution_adequate is False,
            f"REWORK m={family_size}: signal must be resolution-inadequate",
        )
        _assert(
            signal.eligible is False,
            f"REWORK m={family_size}: signal must be NOT eligible (reviewer REWORK)",
        )
        _assert(
            "resolution_inadequate" in signal.reason,
            f"REWORK m={family_size}: reason must cite resolution inadequacy; "
            f"got {signal.reason!r}",
        )


def _check_non_vacuous_eligible() -> None:
    # A clearly-significant, resolution-adequate idea in a small family is eligible.
    entries = [{"idea_key": "strong", "p_value": 0.0001, "run_count": 10_000}]
    for sibling in range(4):  # m = 5
        entries.append({"idea_key": f"weak_{sibling}", "p_value": 0.9, "run_count": 10_000})
    verdicts = correct_family(entries, alpha_fw=0.05, method=FDR_METHOD_BENJAMINI_HOCHBERG)
    strong = next(v for v in verdicts if v.idea_key == "strong")
    _assert(strong.family_size == 5, f"non-vacuous: family_size {strong.family_size} != 5")
    _assert(
        strong.resolution_adequate is True,
        "non-vacuous: 10000 surrogates must be resolution-adequate for m=5",
    )
    _assert(strong.rejected_null is True, "non-vacuous: p=0.0001 must reject the null")
    _assert(strong.eligible is True, "non-vacuous: strong signal must be eligible")


# ---------------------------------------------------------------------------
# Co-mined batch GROUPING canary (the gate-weakening defect this guards)
# ---------------------------------------------------------------------------
#
# The math above is correct; the historical defect was that N co-mined variants
# that DECLARED one shared family co-corrected as N families-of-ONE instead of one
# m=N family (no cross-variant multiplicity tax = under-correction). Two surfaces:
#   1. mining_driver._build_pooled_readout DROPPED the declared
#      mechanism_card.duplicate_exposure (it carries family_id), so the router fell
#      back to the per-variant alpha_spec_id family.
#   2. family_fdr_ledger.family_batch_key anchored the batch on alpha_spec_id, so
#      even a shared family_id split variants with distinct alpha_spec_ids.
# This check exercises the FULL pooled path (readout build -> router -> ledger) and
# asserts m=N grouping AND no false-merge of distinct declared families. It FAILS on
# the pre-fix code (family_size==1, threshold==alpha) and PASSES on the fix.

_GROUPING_ALPHA = 0.10
_GROUPING_FAMILY_SIZE = 4
_GROUPING_SLICES = ("ES_2020_120m", "ES_2021_120m")
_GROUPING_TIMESTAMP = "2026-06-15T00:00:00Z"


def _grouping_slice_payload(slice_id: str) -> dict[str, object]:
    return {
        "slice_id": slice_id,
        "study_kind": "context_not_equal_trigger",
        "dataset_version_id": "dsv_canary",
        "partition_id": slice_id,
        "instrument_id": "ES",
        "session_id": "ES:RTH",
        "data_version": "dsv_canary",
        "features": [
            {"role": "context", "factor_id": "ctx", "factor_version": "v1", "pack_ref": "f1"},
            {"role": "trigger", "factor_id": "trg", "factor_version": "v1", "pack_ref": "f2"},
        ],
        "labels": [{"role": "path", "label_id": "p", "pack_ref": "l1"}],
    }


def _grouping_partition_readout(slice_id: str) -> dict[str, object]:
    """A synthetic per-partition RECORDED setup readout (high-resolution surrogate)."""

    return {
        "schema": "alpha_system.research_lane.fast_probe.v1",
        "readout_id": f"canary_{slice_id}",
        "status": "RECORDED",
        "study_kind": "context_not_equal_trigger",
        "stamp": "EXPLORATORY",
        "promotion_eligible": False,
        "mechanism_card": {"required_features": ["trg"]},
        "slice_spec": {"slice_id": slice_id, "study_kind": "context_not_equal_trigger"},
        "row_access": {"status": "resolved_local_only", "fabricated_values": False},
        "power": {"n_eff": 500, "mde_abs_ic": 0.08},
        "surrogate_fdr_gate": {
            "gate_status": "PASSED",
            "threshold_verdict": "zero-pass-met",
            "run_count": 2000,
            "gate_pass_count": 0,
            "error_count": 0,
            "promotion_evidence": False,
        },
        "readout": {
            "diagnostics": {
                "continuous_outcome_mean_lift": {
                    "outcome_label_type": "net_excursion",
                    "conditioned_mean": 0.02,
                    "base_mean": 0.0,
                    "mean_lift": 0.02,
                    "conditioned_n": 500,
                    "base_n": 500,
                }
            }
        },
    }


def _grouping_idea_and_card(*, family_id: str, variant_index: int):
    """One co-mined variant: DISTINCT alpha_spec_id, SHARED declared family_id."""

    from dataclasses import replace

    from alpha_system.governance.idea_draft import build_idea_validation_bundle
    from alpha_system.governance.ids import GovernanceIdKind, generate_governance_id

    # Repo-root-anchored so the canary is CWD-independent (the canary runner
    # executes from a scratch tmp dir). __file__ is at
    # <root>/src/alpha_system/governance/canaries/family_fdr_budget.py.
    repo_root = Path(__file__).resolve().parents[4]
    fixture = repo_root / "research/idea_to_verdict_loop_v0/fixtures/day_of_week.idea.yaml"
    import json

    bundle = build_idea_validation_bundle(
        json.loads(fixture.read_text(encoding="utf-8")), source=fixture.as_posix()
    )
    mechanism = bundle.mechanism_card
    duplicate = dict(mechanism.duplicate_exposure)
    duplicate["family_id"] = family_id  # the DECLARED counted-variant group
    mechanism = replace(mechanism, duplicate_exposure=duplicate)
    idea = replace(
        bundle.idea_draft,
        alpha_spec_id=generate_governance_id(
            GovernanceIdKind.ALPHA_SPEC, {"family": family_id, "variant": variant_index}
        ),
        mechanism_id=generate_governance_id(
            GovernanceIdKind.MECHANISM_CARD, {"family": family_id, "variant": variant_index}
        ),
    )
    return idea, mechanism, bundle.setup_spec


def _route_grouping_variant(*, family_id: str, variant_index: int, ledger_path: Path):
    """Drive ONE variant through the REAL pooled mining path into the shared ledger."""

    from alpha_system.research_lane import mining_driver as md

    idea, mechanism, setup_spec = _grouping_idea_and_card(
        family_id=family_id, variant_index=variant_index
    )
    readouts = {sid: _grouping_partition_readout(sid) for sid in _GROUPING_SLICES}

    def _stub_probe(card, setup, slice_spec, *, resolver=None, env=None):
        return readouts[slice_spec.slice_id]

    original = md.fast_probe
    md.fast_probe = _stub_probe
    try:
        result = md.run_multi_partition_pool(
            {"slices": {sid: _grouping_slice_payload(sid) for sid in _GROUPING_SLICES}},
            idea,
            mechanism,
            setup_spec,
            list(_GROUPING_SLICES),
            created_at=_GROUPING_TIMESTAMP,
            family_fdr_ledger_path=ledger_path,
        )
    finally:
        md.fast_probe = original
    return result


def _check_comined_family_grouping() -> None:
    from alpha_system.governance.family_fdr_correction import DEFAULT_FDR_ALPHA
    from alpha_system.governance.family_fdr_ledger import FamilyFdrLedger
    from alpha_system.research_lane.mining_driver import _build_pooled_readout

    # The pooled mining path routes with the standing policy alpha (no override),
    # so the threshold assertion below uses it as the family-wise alpha.
    _assert(
        abs(DEFAULT_FDR_ALPHA - _GROUPING_ALPHA) < 1e-12,
        f"grouping canary assumes alpha={_GROUPING_ALPHA}; policy default is {DEFAULT_FDR_ALPHA}",
    )
    family_id = "canary_comined_family"

    # (1) The pooled readout builder MUST propagate the declared
    # duplicate_exposure.family_id (fails on old code that dropped it).
    from alpha_system.research_lane.mining_driver import PartitionCoverage

    idea, mechanism, _ = _grouping_idea_and_card(family_id=family_id, variant_index=0)
    coverage = PartitionCoverage(declared=_GROUPING_SLICES, present=_GROUPING_SLICES, missing=())

    class _PooledStub:
        point_estimate = 0.02
        n_eff = 500

        def to_dict(self):
            return {"point_estimate": 0.02, "n_eff": 500}

    pooled_readout = _build_pooled_readout(
        study_kind="context_not_equal_trigger",
        pooled=_PooledStub(),
        coverage=coverage,
        outcomes=(),
        alpha_spec_id=idea.alpha_spec_id,
        mechanism_card=mechanism,
    )
    carried = pooled_readout["mechanism_card"].get("duplicate_exposure", {})  # type: ignore[union-attr]
    _assert(
        isinstance(carried, dict) and carried.get("family_id") == family_id,
        "pooled readout dropped the declared duplicate_exposure.family_id "
        f"(carried {carried!r}) -> family-FDR would fall back to a family-of-one",
    )

    # (2) N variants with DISTINCT alpha_spec_ids + the SAME declared family_id
    # co-correct as ONE m=N family with the BH threshold tightened to alpha*k/N.
    with tempfile.TemporaryDirectory() as tmp:
        ledger_path = Path(tmp) / "family_fdr_ledger.jsonl"
        ledger_path.touch()
        last = None
        for index in range(_GROUPING_FAMILY_SIZE):
            last = _route_grouping_variant(
                family_id=family_id, variant_index=index, ledger_path=ledger_path
            )
        _assert(last is not None and last.route is not None, "grouping: no route result")
        family = last.route.memory_record.get("family_fdr_verdict")
        _assert(family is not None, "co-mined grouping: no family_fdr_verdict attached")
        _assert(
            family["family_size"] == _GROUPING_FAMILY_SIZE,
            f"co-mined grouping: family_size {family['family_size']} != "
            f"{_GROUPING_FAMILY_SIZE} (UNDER-CORRECTION: variants paid no "
            "cross-variant multiplicity tax)",
        )
        records = FamilyFdrLedger(ledger_path).load_records()
        batch_keys = {r.batch_key for r in records}
        _assert(
            len(batch_keys) == 1,
            f"co-mined grouping: {len(batch_keys)} batch_keys for one declared "
            f"family (must be 1): {sorted(batch_keys)}",
        )
        # Re-correct the full batch (the binding cross-idea correction) and assert
        # the BH line is multiplicity-tightened: the tightest (rank-1) corrected
        # threshold is alpha/N, not alpha. An m=1 family-of-one (the gate-weakening
        # the defect produced) would leave EVERY corrected threshold at alpha.
        entries = [
            {"idea_key": r.idea_key, "p_value": r.p_value, "run_count": r.run_count}
            for r in records
        ]
        verdicts = correct_family(
            entries, alpha_fw=_GROUPING_ALPHA, method=FDR_METHOD_BENJAMINI_HOCHBERG
        )
        _assert(
            all(v.family_size == _GROUPING_FAMILY_SIZE for v in verdicts),
            "co-mined grouping: re-corrected batch family_size != N",
        )
        tightest = min(v.corrected_threshold for v in verdicts)
        _assert(
            abs(tightest - _GROUPING_ALPHA / _GROUPING_FAMILY_SIZE) < 1e-12,
            f"co-mined grouping: tightest BH threshold {tightest} != "
            f"alpha/N = {_GROUPING_ALPHA / _GROUPING_FAMILY_SIZE} "
            "(threshold not multiplicity-corrected -> m=1 under-correction)",
        )

    # (3) No false-merge: two variants with DIFFERENT declared family_ids stay in
    # separate families of one.
    with tempfile.TemporaryDirectory() as tmp:
        ledger_path = Path(tmp) / "family_fdr_ledger.jsonl"
        ledger_path.touch()
        for fam in ("canary_family_A", "canary_family_B"):
            _route_grouping_variant(family_id=fam, variant_index=0, ledger_path=ledger_path)
        records = FamilyFdrLedger(ledger_path).load_records()
        batch_keys = {r.batch_key for r in records}
        _assert(
            len(batch_keys) == 2,
            f"no-false-merge: distinct declared families merged into {len(batch_keys)} "
            "batch_keys (must be 2)",
        )
        _assert(
            all(r.verdict.family_size == 1 for r in records),
            "no-false-merge: distinct families must each stay m=1",
        )


def run_family_fdr_budget_canary() -> None:
    """Run all multiplicity assertions; raise on the first failure."""

    _check_textbook_corrections()
    _check_historical_rework()
    _check_non_vacuous_eligible()
    _check_comined_family_grouping()


def main(argv: list[str] | None = None) -> int:
    try:
        run_family_fdr_budget_canary()
    except AssertionError as exc:
        print(f"FAIL family_fdr_budget: {exc}", file=sys.stderr)
        return 1
    print(
        "family_fdr_budget OK: BH/Bonferroni textbook, pa_setup REWORK reproduced "
        "(m=7 & m=5, p=1/65, run_count=64 -> not eligible), non-vacuous eligible, "
        "co-mined declared family groups as m=N across distinct alpha_specs "
        "(no false-merge)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
