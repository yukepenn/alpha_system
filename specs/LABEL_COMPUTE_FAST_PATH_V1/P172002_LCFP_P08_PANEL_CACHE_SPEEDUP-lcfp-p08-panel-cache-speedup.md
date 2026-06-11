---
campaign_id: LABEL_COMPUTE_FAST_PATH_V1
phase_id: P172002_LCFP_P08_PANEL_CACHE_SPEEDUP
lane: yellow
status: in_progress
---

# P172002_LCFP_P08_PANEL_CACHE_SPEEDUP: lcfp-p08-panel-cache-speedup

## Purpose

Remove the redundant per-unit panel-load overhead that makes the fast label
path slower than the per-row reference engine for cheap families on the
LCFP-P08 bounded benchmark slice (`BLOCKED_SPEEDUP`: fixed_extended 0.36–0.53x,
close_out, cost_adjusted 0.34–0.73x), while leaving correctness gates
(parity, resolver smoke, guards, label_available_ts, identity) untouched.

Evidence (research/label_compute_fast_path_v1/benchmark/benchmark_summary.md,
2026-06-10T17:18Z run): each materialization unit loads its own copy of the
same bounded-slice canonical panel (e.g. cost_adjusted = 9 units × the same
26,304-row OHLCV+BBO panel) while the reference denominator computes over
pre-built views. Panel load + input adaptation dominates fast_compute for
families with cheap kernels.

## Scope

- Add a per-(symbol, year/window, dataset_version pair) shared panel-frame
  cache so independent units executed by the same worker process reuse one
  loaded canonical panel instead of reloading per unit.
  Surfaces: `src/alpha_system/labels/fast/panel.py`,
  `src/alpha_system/labels/fast/materializer.py`,
  `src/alpha_system/features/scaleout/driver.py` (unit execution path only),
  `tools/label_compute_fast_path/benchmark_gate.py` (wire cache through the
  per-worker-count cell; cells stay cold-start isolated from each other).
- Cache must be process-local (no cross-process shared state), bounded
  (evict by symbol-year key; no unbounded growth), and inert for the
  reference engine path.
- Cold-start behavior per benchmark cell preserved: each (family,
  worker-count) cell starts with an empty cache, as the methodology section
  documents; amortization is measured within a cell only.
- Regression test: same unit set executed twice through the cached path
  yields identical record sets and registry-eligible payloads as the uncached
  path (cache must be semantically invisible).
- Re-run the full LCFP-P08 benchmark gate (coordinator-owned background run)
  and regenerate the committed value-free summary.

## Non-goals

- No kernel/algorithm changes to any label family.
- No changes to parity comparisons, thresholds, or the "materially faster"
  done-criterion of LCFP-P08 (if families remain slower after this fix, that
  outcome is reported honestly and the production engine policy decision goes
  to the LCFP-P08 re-review).
- No reference-engine edits (read-only oracle).
- No registry schema, identity, guard, or availability changes.
- No parallel SQLite writes; serial keystone registry writer unchanged.

## Validation

- `pytest tests/unit/label_compute_fast_path/ tests/unit/futures_substrate_scaleout/labels/ tests/unit/feature_compute_fast_path/` (research venv, polars present)
- `pytest tests/no_lookahead/feature_label/test_synthetic_fail_closed.py tests/unit/test_fast_path_artifact_policy.py`
- `python tools/verify.py --smoke`
- `python tools/hooks/canary_runner.py`
- Full benchmark gate re-run with workers 1/2/4/8 on the bounded slice;
  parity + resolver smoke PASS for all families; summary regenerated.

## Acceptance

- Cache demonstrably removes redundant panel loads (per-family fast_compute
  at workers=1 improves materially vs the 2026-06-10T17:18Z summary).
- All correctness gates unchanged and green.
- Honest summary committed regardless of whether every family clears the
  speedup bar; remaining slow families documented with component timings.

## Review

Adversarial review (frontier-review discipline) of the combined
`repair/lcfp-p08-blockers` diff before merge; reviewer must check for cache
staleness/leak across dataset versions, hidden engine-default changes, and
any weakening of parity/guard semantics.
