"""Pooled cross-partition OOS SE canary for the family-FDR rail (Stage A).

Guards ``governance/pooled_hypothesis.py::aggregate_pooled_metric`` against the
silent-independence bug: pooling correlated / overlapping components (overlapping
horizons on the same bars, contemporaneously correlated index symbols) with a
naive ``sqrt(sum se^2)/K`` SE and ``sum(n_eff)`` UNDERSTATES the pooled SE and
OVERSTATES power, inflating the pooled z and waving noise through the gate. This
is the #474 overlap sin one layer up.

It asserts three things the independent reviewer rail relies on:

1. **Independent back-compat.** With an explicit ``pooled_correlation=0.0`` the
   pooled SE is exactly the historical independent ``sqrt(sum se^2)/K`` and the
   effective N is the independent sum. A genuinely-uncorrelated pool is unchanged.

2. **The rail is no longer silently defeated.** A set of overlapping components
   whose naive (rho=0) pooled z CLEARS a fixed significance bar does NOT clear
   under the corrected, conservative pool-kind default rho. The corrected pooled
   SE is strictly larger and the corrected effective N strictly smaller, so the
   inflated significance is withdrawn -- without a human.

3. **Worst-case collapse + fail-loud.** CROSS_HORIZON defaults to rho=1.0, where
   the pooled SE collapses to ``mean(se_i)`` and effective N is floored at the
   weakest single member; an out-of-range correlation input fails closed.

This is research-only diagnostic plumbing. A passing canary validates the
correlation-aware pooling math only and implies NO alpha, profitability, or
tradability claim. The gate is a deterministic RECORD; the machine never
auto-promotes.
"""

from __future__ import annotations

import math
import sys

from alpha_system.governance.ids import GovernanceIdKind, generate_governance_id
from alpha_system.governance.pooled_hypothesis import (
    DEFAULT_POOL_CORRELATION,
    PoolKind,
    aggregate_pooled_metric,
    generate_pooled_hypothesis_id,
)
from alpha_system.governance.trial_ledger import create_trial_ledger_record
from alpha_system.governance.validation import GovernanceValidationError
from alpha_system.governance.variant_ledger import validate_variant_ledger_record

# Synthetic fixed governance refs (content-addressed StudySpec-kind members).
_MEMBERS: tuple[str, ...] = (
    "sspec_f6cbd88caa0445f0f56d81fd",
    "sspec_1604b063f3a3401208ee0239",
    "sspec_dec89a327a9c50957adca780",
)
_ALPHA_SPEC_ID = generate_governance_id(
    GovernanceIdKind.ALPHA_SPEC,
    {"name": "pooled-se-poolkind-canary"},
)
_REGISTERED_AT = "2026-06-15T00:00:00Z"

# Overlapping components with a comfortably-significant naive pooled z.
# Equal point estimate 0.30 with small SEs so the naive sqrt(sum se^2)/K SE is
# tiny and z = estimate / SE clears any reasonable bar.
_POINT_ESTIMATE = 0.30
_COMPONENT_SES: tuple[float, ...] = (0.05, 0.05, 0.05)
_COMPONENT_N_EFF: tuple[int, ...] = (300, 300, 300)
# A z bar the naive pool clears but the corrected pool must not, for the test to
# be non-vacuous. Naive SE = 0.05/sqrt(3) ~= 0.02887 -> z ~= 10.39. Worst-case SE
# (rho=1) = 0.05 -> z = 6.0. We assert the *inequality* (corrected SE strictly
# larger / corrected z strictly smaller), which is the rail-defeat guard.


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _variant_ledger_record(anchor: str) -> dict[str, object]:
    trial = create_trial_ledger_record(
        alpha_spec_id=_ALPHA_SPEC_ID,
        study_spec_id=anchor,
        run_id="pooled-se-poolkind-canary",
        variant_id="pooled-se-poolkind-canary",
        status="PLANNED",
        parameters={"registration": "pooled_se_poolkind_canary"},
        metrics_summary={},
        failure_reason=None,
        oos_touched_flag=False,
        locked_test_contamination_flag=False,
        code_hash="0" * 64,
        config_hash="0" * 64,
    )
    return validate_variant_ledger_record(
        {
            "variant_id": "pooled-se-poolkind-canary",
            "alpha_spec_id": _ALPHA_SPEC_ID,
            "study_spec_id": anchor,
            "family_id": "pooled-se-poolkind-canary",
            "attempt_count": 1,
            "trial_ids": [trial.trial_id],
            "status": "PLANNED",
            "created_at": _REGISTERED_AT,
        }
    ).to_dict()


def _payload(*, pool_kind: str, symbols: tuple[str, ...], horizons: tuple[str, ...]):
    payload: dict[str, object] = {
        "mechanism_rationale": (
            "Synthetic pooled-SE canary ties one predeclared mechanism to fixed "
            "members before any Track-A metrics, to guard pooled SE correctness."
        ),
        "pool_kind": pool_kind,
        "members": list(_MEMBERS),
        "aggregation_rule": "equal_weight_mean",
        "horizons": list(horizons),
        "sessions": ["rth"],
        "symbols": list(symbols),
        "registered_at": _REGISTERED_AT,
        "registered_before_metrics": True,
        "variant_ledger_record": _variant_ledger_record(_MEMBERS[0]),
    }
    payload["pooled_hypothesis_id"] = generate_pooled_hypothesis_id(payload)
    return payload


def _components() -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "component_ref": ref,
            "metric_name": "synthetic_net_excursion_lift",
            "point_estimate": _POINT_ESTIMATE,
            "standard_error": se,
            "n_eff": n_eff,
            "metadata": {"source": ref},
        }
        for ref, se, n_eff in zip(
            _MEMBERS, _COMPONENT_SES, _COMPONENT_N_EFF, strict=True
        )
    )


def _check_independent_back_compat() -> None:
    payload = _payload(pool_kind="cross_symbol", symbols=("ES", "NQ", "RTY"), horizons=("5m",))
    result = aggregate_pooled_metric(payload, _components(), pooled_correlation=0.0)
    naive_se = math.sqrt(sum(se**2 for se in _COMPONENT_SES)) / len(_COMPONENT_SES)
    _assert(
        result.standard_error is not None
        and abs(result.standard_error - naive_se) < 1e-12,
        f"independent back-compat: SE {result.standard_error} != naive {naive_se}",
    )
    _assert(
        result.n_eff == sum(_COMPONENT_N_EFF),
        f"independent back-compat: n_eff {result.n_eff} != sum {sum(_COMPONENT_N_EFF)}",
    )
    _assert(
        result.assumed_correlation == 0.0,
        "independent back-compat: assumed_correlation must be the explicit 0.0",
    )


def _check_rail_not_silently_defeated() -> None:
    """Overlapping components that clear under naive rho=0 must NOT clear corrected."""

    payload = _payload(pool_kind="cross_symbol", symbols=("ES", "NQ", "RTY"), horizons=("5m",))
    components = _components()
    naive = aggregate_pooled_metric(payload, components, pooled_correlation=0.0)
    corrected = aggregate_pooled_metric(payload, components)  # conservative default

    _assert(
        corrected.assumed_correlation == DEFAULT_POOL_CORRELATION[PoolKind.CROSS_SYMBOL],
        "corrected pool must surface the conservative default rho",
    )
    _assert(
        naive.standard_error is not None and corrected.standard_error is not None,
        "both pooled SEs must be defined",
    )
    # Corrected SE strictly larger -> pooled z strictly smaller: the inflated
    # naive significance is withdrawn. This is the rail-defeat guard.
    naive_z = naive.point_estimate / naive.standard_error
    corrected_z = corrected.point_estimate / corrected.standard_error
    _assert(
        corrected.standard_error > naive.standard_error,
        f"rail defeated: corrected SE {corrected.standard_error} <= naive "
        f"{naive.standard_error} -- noise would clear the gate",
    )
    _assert(
        corrected_z < naive_z,
        f"rail defeated: corrected z {corrected_z} >= naive z {naive_z}",
    )
    # Corrected effective N strictly smaller than the naive independent sum.
    _assert(
        corrected.n_eff is not None
        and naive.n_eff is not None
        and corrected.n_eff < naive.n_eff,
        f"rail defeated: corrected n_eff {corrected.n_eff} not discounted below "
        f"naive sum {naive.n_eff}",
    )


def _check_worst_case_and_fail_loud() -> None:
    payload = _payload(
        pool_kind="cross_horizon",
        symbols=("ES",),
        horizons=("60m", "120m", "240m"),
    )
    components = _components()
    result = aggregate_pooled_metric(payload, components)  # CROSS_HORIZON default rho=1.0
    mean_se = sum(_COMPONENT_SES) / len(_COMPONENT_SES)
    _assert(
        result.assumed_correlation == 1.0,
        "CROSS_HORIZON default must be the worst-case rho=1.0",
    )
    _assert(
        result.standard_error is not None
        and abs(result.standard_error - mean_se) < 1e-12,
        f"worst case: SE {result.standard_error} != mean(se_i) {mean_se}",
    )
    _assert(
        result.n_eff == min(_COMPONENT_N_EFF),
        f"worst case: n_eff {result.n_eff} != min {min(_COMPONENT_N_EFF)}",
    )

    # Out-of-range correlation must fail closed.
    try:
        aggregate_pooled_metric(payload, components, pooled_correlation=1.5)
    except GovernanceValidationError as exc:
        codes = {issue.code for issue in exc.issues}
        _assert(
            "invalid_pooled_correlation" in codes,
            f"fail-loud: expected invalid_pooled_correlation, got {sorted(codes)}",
        )
    else:
        raise AssertionError("fail-loud: rho=1.5 was not rejected")


def run_pooled_se_poolkind_canary() -> None:
    """Run all pooled-SE assertions; raise on the first failure."""

    _check_independent_back_compat()
    _check_rail_not_silently_defeated()
    _check_worst_case_and_fail_loud()


def main(argv: list[str] | None = None) -> int:
    try:
        run_pooled_se_poolkind_canary()
    except AssertionError as exc:
        print(f"FAIL pooled_se_poolkind: {exc}", file=sys.stderr)
        return 1
    print(
        "pooled_se_poolkind OK: independent rho=0 back-compat, correlated pool no "
        "longer silently defeats the rail (corrected SE larger / z smaller / n_eff "
        "discounted), worst-case rho=1 collapses SE to mean and floors n_eff, "
        "out-of-range rho fails closed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
