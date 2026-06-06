Review complete. All artifacts examined and cross-checked against spec and policy.

---

# Claude Opus Review — RT-P12: Simple Signal Probe Runtime

## Summary

RT-P12 adds `src/alpha_system/runtime/probe/` (`__init__`, `spec`, `fills`, `report`, `runner`) plus tests, a tiny synthetic fixture, config, doc, README snapshot, and a commit-eligible handoff. The phase implements a Tier 1 descriptive signal probe as an orchestration layer over `runtime.cost` / diagnostics / contracts / input_resolver. Static review confirms the implementation matches the spec scope tightly and enforces every named safety invariant fail-closed.

## Scope & boundary compliance ✓

- `git status` shows **only** `README.md` modified plus the expected untracked probe paths. No forbidden domain (`backtest/**`, `governance/**`, `research/**`, `signals/**`, `strategies/**`, `execution/**`, data paths) was edited. Pre-existing tracked `test_input_resolver_available_ts.py` is untouched.
- No direct `backtest.*` import in the probe package — cost math is reached only via `runtime.cost.build_cost_sensitivity_report` (verified by grep; the only "backtest" hits are non-promotional `not_a_backtest` flags/docstrings).
- `git ls-files runs` empty; no `runs/` path in the handoff staging list; fixture is tiny synthetic JSON.

## Safety invariants enforced (fail-closed) ✓

- **No same-bar optimistic fill:** `FillPolicy.__post_init__` rejects `delay_bars < 1` ("same-bar optimistic fill is forbidden") and `allow_same_bar_fill != False`; `build_next_bar_position_series` rejects a signal whose `available_ts` post-dates the eligible fill bar `event_ts`. Independently-provided `verify-canaries` shows **`PASS governance_optimistic_fill`**.
- **Cost stress with `double_cost` required:** `SignalProbeSpec` rejects a `CostStressSpec` lacking `double_cost`; `SignalProbeReport` requires an accompanying `CostSensitivityReport` and `SIGNAL_PROBE_COMPLETE` requires its status be `DIAGNOSTICS_COMPLETE`.
- **Bounded threshold set:** `MAX_THRESHOLD_COUNT = 9`, empty/duplicate/unbounded rejected.
- **Locked-partition selection denied** without governance contamination metadata; label-as-feature tokens rejected on `signal_name`; `available_ts` / `label_available_ts` metadata required; AlphaSpec+StudySpec must match the resolved `RuntimeInputPack`.
- **Non-promotional framing** is pervasive (`fast_path`, `not_strategy_validation`, `not_a_candidate`, `not_a_backtest`, `promotion_basis_allowed: False`). Terminal failure states (`REJECTED`/`INCONCLUSIVE`/`BLOCKED`) require ≥1 visible rejection reason — failed probes stay visible, no silent drop.
- No broker/live/paper/order/account, no strategy/backtest/portfolio, no provider/network access, no prohibited MVP state.

## Artifacts ✓

Doc, config, fixture, and README snapshot are factual, compact, synthetic-only, and free of alpha/tradability claims. Handoff is truthful: it accurately records the `PYTHONPATH=src` import caveat, the skipped `verify.py --all` with a reason, and the deferred `RT-P15`/`RT-P14` scope.

## Independent validation
`just frontier-doctor` → pass; `just verify-canaries` → all 16 canaries pass (including `forbidden_scope_drift`, `forbidden_boundary_import`, `governance_optimistic_fill`).

## Warnings (non-blocking)

1. **Test pass is executor-reported, not re-run in review.** I was permission-blocked from re-executing `pytest`. The independent harness block confirms canaries + doctor only; the `13 passed` / `146 passed` unit and no-lookahead results come from the executor handoff. They are consistent with the code under static review, but were not independently reproduced here.
2. **Trivial dead branch:** `runner._probe_status` lines 337–339 — both the `if cost_report.status is DIAGNOSTICS_FAILED` branch and its `else` return `REJECTED`. Cosmetic; no behavioral impact.
3. `SignalProbePositionSeries.cost_fill_mappings` is a property that always raises, steering callers to `to_cost_fill_mappings(observations)`. Intentional guard, but an unusual API shape worth a follow-up tidy.

None of these weaken tests, violate artifact policy, or affect the safety guards.

VERDICT: PASS_WITH_WARNINGS
