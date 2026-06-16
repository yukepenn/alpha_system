"""Promotion-gate canary: IC (rank order) alone can NEVER promote a study.

Encodes the campaign's hardest-won lesson as a fail-closed negative control. The
``top_book_imbalance`` proof: that factor had a real, year-stable, replicating
rank-IC (+0.0314 @5m, 2.9x its MDE) yet EVERY decile mean was negative after the
half-spread (top decile significantly < 0). IC measures RANK ORDER; promotion
requires a tradeable POST-COST economic LEVEL. So a study whose only evidence is a
strong IC on a non-cost-adjusted outcome must NOT reach the promotable
``SIGNAL_PENDING_REVIEWER`` shelf; it caps at a non-promoting verdict.

This canary asserts, against the real ``verdict_report`` derivation (no mock of
the gate), that:

1. A main_effect readout with a STRONG, well-powered IC (3x its MDE, same sign)
   but NO post-cost level routes to a NON-promoting verdict (NOT
   SIGNAL_PENDING_REVIEWER) -- fail-on-old, pass-on-new.
2. The SAME readout WITH a contract-valid ``clears_cost=true`` post-cost level
   reaches SIGNAL_PENDING_REVIEWER (the gate is not a blanket block; a genuine
   post-cost-cleared signal still promotes).
3. A post-cost level present but ``clears_cost=false`` does NOT promote (the level
   must actually clear cost, not merely be measured).
4. The setup (context_not_equal_trigger) net_excursion SIGNAL path is gated the
   same way: a surrogate-gated signed asymmetry with no post-cost level does NOT
   promote.
5. The post-cost contract REFUSES a missing ``n_legs`` (a single-leg cost on a
   multi-leg study is a second-truth accounting bug) -- the typed seam raises and
   the gate then denies promotion (fail-closed).

The fixtures are SHAPE FIXTURES: small committed dicts mirroring the verified
producer key shapes. They carry no real market data, factor values, labels, or
study values -- only the structural keys the gate reads. This is research-only
diagnostic plumbing; it defines no PnL/value truth and makes no profitability,
tradability, or alpha claim.
"""

from __future__ import annotations

import sys
from collections.abc import Mapping
from typing import Any

from alpha_system.governance.verdict_reason_code import VerdictReasonCode
from alpha_system.research_lane.fast_readout import FastReadout, FastReadoutContractError
from alpha_system.research_lane.verdict_report import render_verdict_report

_EXPLORATORY = "EXPLORATORY"
_SCHEMA = "alpha_system.research_lane.fast_probe.v1"

# A well-powered IC at 3x the detectable floor, same sign (the strong-signal case).
_STRONG_IC = 0.36
_MDE = 0.12
_N_EFF = 9


def _passing_gate() -> dict[str, Any]:
    """A testability gate with two classes and an overall PASS (no pre-test block)."""

    return {
        "overall_status": "PASS",
        "checks": [
            {
                "check_id": "path_label_two_class",
                "status": "PASS",
                "detail": {"class_balance": {"class_count": 2, "minority_class_count": 40}},
            }
        ],
    }


# Governance IDs are ``<prefix>_<24-hex-token>``; these are fixed synthetic tokens
# (no content hash needed -- the renderer only echoes the ids, it does not verify
# the content-address). They carry no market data or study values.
_HEX = "0123456789abcdef01234567"


def _idea() -> dict[str, Any]:
    return {
        "study_kind": "main_effect",
        "source": "ic_only_postcost_promotion_canary",
        "alpha_spec_id": f"aspec_{_HEX}",
        "mechanism_id": f"mech_{_HEX}",
        "hypothesis_id": f"hyp_{_HEX}",
    }


def _setup_idea() -> dict[str, Any]:
    return {
        "study_kind": "context_not_equal_trigger",
        "source": "ic_only_postcost_promotion_canary",
        "alpha_spec_id": f"aspec_{_HEX}",
        "mechanism_id": f"mech_{_HEX}",
        "hypothesis_id": f"hyp_{_HEX}",
        "setup_spec_id": f"setup_{_HEX}",
    }


def _main_effect_strong_ic_readout() -> dict[str, Any]:
    """main_effect RECORDED with a strong, well-powered, same-sign IC."""

    return {
        "schema": _SCHEMA,
        "status": "RECORDED",
        "study_kind": "main_effect",
        "stamp": _EXPLORATORY,
        "promotion_eligible": False,
        "mechanism_card": {"mechanism_id": "mech_canary"},
        "setup_spec": None,
        "slice_spec": {"slice_id": "slice_canary"},
        "row_access": {"status": "resolved_local_only", "fabricated_values": False},
        "resolved_handles": {"feature_handles": [], "label_handles": []},
        "engine": "build_factor_diagnostics_run",
        "readout": {
            "factor_diagnostics_report": {
                "quality_summary": {
                    "diagnostic_pass": True,
                    "quality_gate_count": 3,
                    "failing_gate_count": 0,
                    "pearson_ic": _STRONG_IC,
                    "rank_ic": _STRONG_IC,
                    "bucket_rank_correlation": 0.6,
                    "ic_power_mde_abs_ic": _MDE,
                    "ic_power_n_eff": _N_EFF,
                    "ic_power_statement": "synthetic",
                },
            },
            "diagnostics_run_record": {"run_id": "diag_canary"},
        },
        "readout_id": "fpmain_canary",
    }


def _post_cost_level(*, clears_cost: bool, n_legs: int = 1) -> dict[str, Any]:
    # When the level clears, the post-cost mean exceeds n_legs * round_trip_cost; when
    # it does not, it is below. round_trip_cost is per-leg, so the hurdle scales with
    # n_legs (a multi-leg study cannot understate the hurdle with a single-leg cost).
    rt = 2.0
    mean = (n_legs * rt) + 1.0 if clears_cost else (n_legs * rt) - 1.0
    return {
        "n_legs": n_legs,
        "round_trip_cost_bps": rt,
        "traded_bucket_post_cost_mean_bps": mean,
        "clears_cost": clears_cost,
    }


def _setup_net_excursion_readout() -> dict[str, Any]:
    """context_not_equal_trigger ZERO_PASS_MET with a signed net_excursion lift."""

    return {
        "schema": _SCHEMA,
        "status": "RECORDED",
        "study_kind": "context_not_equal_trigger",
        "stamp": _EXPLORATORY,
        "promotion_eligible": False,
        "mechanism_card": {"mechanism_id": "mech_canary"},
        "setup_spec": {"setup_spec_id": "setup_canary"},
        "slice_spec": {"slice_id": "slice_canary"},
        "row_access": {"status": "resolved_local_only", "fabricated_values": False},
        "resolved_handles": {"feature_handles": [], "label_handles": []},
        "engine": "evaluate_setup_conditional_probe",
        "readout": {
            "readout_id": "cprobe_canary",
            "setup_spec_id": "setup_canary",
            "path_label": "path_canary",
            "variant_id": "v0",
            "diagnostics": {
                "continuous_outcome_mean_lift": {
                    "outcome_label_type": "net_excursion",
                    "conditioned_mean": 0.002,
                    "base_mean": 0.001,
                    "mean_lift": 0.001,
                    "conditioned_n": 40,
                    "base_n": 120,
                },
            },
            "counts": {},
            "surrogate_fdr_gate": {
                "gate_status": "PASSED",
                "threshold_verdict": "ZERO_PASS_MET",
                "run_count": 200,
                "gate_pass_count": 0,
                "error_count": 0,
                "promotion_evidence": False,
            },
        },
        "surrogate_fdr_gate": {
            "gate_status": "PASSED",
            "threshold_verdict": "ZERO_PASS_MET",
            "run_count": 200,
            "gate_pass_count": 0,
            "error_count": 0,
            "promotion_evidence": False,
            "conditioned_n_eff": 7,
            "observed_effect": 0.001,
        },
        "power": {
            "schema": "alpha_system.runtime.diagnostics.ic_power_statement.v1",
            "scope": "per_factor",
            "n_eff": 7,
            "se_ic": 0.4,
            "mde_abs_ic": 0.8,
            "z_multiple": 2.0,
            "statement": "synthetic",
            "statistical_validity_claim": False,
        },
        "readout_id": "cprobe_canary",
    }


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _reason_code(readout: Mapping[str, Any], idea: Mapping[str, Any] | None = None) -> str:
    report = render_verdict_report(idea or _idea(), _passing_gate(), readout)
    for line in report.splitlines():
        if line.startswith("- reason_code:"):
            return line.split(":", 1)[1].strip()
    raise AssertionError("verdict report did not emit a reason_code line")


def _is_promotable(reason_code: str) -> bool:
    return reason_code == VerdictReasonCode.SIGNAL_PENDING_REVIEWER.value


def _check_main_effect_ic_only_does_not_promote() -> None:
    readout = _main_effect_strong_ic_readout()
    reason = _reason_code(readout)
    _assert(
        not _is_promotable(reason),
        "IC-only main_effect (strong 3x-MDE IC, no post-cost level) PROMOTED to "
        f"SIGNAL_PENDING_REVIEWER -- the IC-only-promotion lesson is not enforced "
        f"(got reason_code={reason})",
    )
    _assert(
        reason == VerdictReasonCode.COST_FRAGILE.value,
        f"IC-only main_effect should cap at COST_FRAGILE; got {reason}",
    )


def _check_main_effect_clears_cost_promotes() -> None:
    readout = _main_effect_strong_ic_readout()
    readout["traded_bucket_post_cost_level"] = _post_cost_level(clears_cost=True)
    reason = _reason_code(readout)
    _assert(
        _is_promotable(reason),
        "A well-powered IC WITH a post-cost level that clears cost should reach "
        f"SIGNAL_PENDING_REVIEWER; got {reason} (the gate over-blocks)",
    )


def _check_main_effect_not_clearing_does_not_promote() -> None:
    readout = _main_effect_strong_ic_readout()
    readout["traded_bucket_post_cost_level"] = _post_cost_level(clears_cost=False)
    reason = _reason_code(readout)
    _assert(
        not _is_promotable(reason),
        "A post-cost level that does NOT clear cost (clears_cost=false) must not "
        f"promote; got {reason}",
    )


def _check_setup_net_excursion_ic_only_does_not_promote() -> None:
    readout = _setup_net_excursion_readout()
    reason = _reason_code(readout, _setup_idea())
    _assert(
        not _is_promotable(reason),
        "A surrogate-gated net_excursion asymmetry with NO post-cost level promoted "
        f"to SIGNAL_PENDING_REVIEWER; got {reason}",
    )
    _assert(
        reason == VerdictReasonCode.COST_FRAGILE.value,
        f"setup net_excursion IC-only should cap at COST_FRAGILE; got {reason}",
    )


def _check_setup_clears_cost_promotes() -> None:
    readout = _setup_net_excursion_readout()
    readout["traded_bucket_post_cost_level"] = _post_cost_level(clears_cost=True)
    reason = _reason_code(readout, _setup_idea())
    _assert(
        _is_promotable(reason),
        "A surrogate-gated net_excursion asymmetry WITH a clearing post-cost level "
        f"should reach SIGNAL_PENDING_REVIEWER; got {reason}",
    )


def _check_missing_n_legs_is_second_truth_refused() -> None:
    # n_legs is REQUIRED: a relative-value / multi-leg study that silently charges a
    # single-leg cost understates the hurdle. The typed seam must RAISE on a missing
    # n_legs, and the gate must then deny promotion (fail-closed).
    bad = _main_effect_strong_ic_readout()
    bad["traded_bucket_post_cost_level"] = {
        "round_trip_cost_bps": 2.0,
        "traded_bucket_post_cost_mean_bps": 100.0,
        "clears_cost": True,
    }
    raised = False
    try:
        FastReadout.from_dict(bad)
    except FastReadoutContractError:
        raised = True
    _assert(raised, "post-cost level missing n_legs did not raise (single-leg cost second truth)")
    reason = _reason_code(bad)
    _assert(
        not _is_promotable(reason),
        "a malformed post-cost level (missing n_legs) must NOT promote (fail-closed); "
        f"got {reason}",
    )


def _check_multi_leg_hurdle_scales() -> None:
    # A 2-leg study whose post-cost mean clears only a SINGLE-leg cost must not promote:
    # the hurdle is n_legs * round_trip_cost, so a single-leg-sized mean is below it.
    readout = _main_effect_strong_ic_readout()
    rt = 2.0
    readout["traded_bucket_post_cost_level"] = {
        "n_legs": 2,
        "round_trip_cost_bps": rt,
        "traded_bucket_post_cost_mean_bps": rt + 0.5,  # clears 1 leg, not 2
        "clears_cost": False,
    }
    reason = _reason_code(readout)
    _assert(
        not _is_promotable(reason),
        "a 2-leg study clearing only a single-leg cost must not promote; "
        f"got {reason}",
    )


def run_ic_only_postcost_promotion_canary() -> None:
    """Run all promotion-gate assertions; raise on the first failure."""

    _check_main_effect_ic_only_does_not_promote()
    _check_main_effect_clears_cost_promotes()
    _check_main_effect_not_clearing_does_not_promote()
    _check_setup_net_excursion_ic_only_does_not_promote()
    _check_setup_clears_cost_promotes()
    _check_missing_n_legs_is_second_truth_refused()
    _check_multi_leg_hurdle_scales()


def main(argv: list[str] | None = None) -> int:
    try:
        run_ic_only_postcost_promotion_canary()
    except (AssertionError, FastReadoutContractError) as exc:
        print(f"FAIL ic_only_postcost_promotion: {exc}", file=sys.stderr)
        return 1
    print(
        "ic_only_postcost_promotion OK: IC-only cannot promote; clears_cost promotes; "
        "n_legs required; multi-leg hurdle scales"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
