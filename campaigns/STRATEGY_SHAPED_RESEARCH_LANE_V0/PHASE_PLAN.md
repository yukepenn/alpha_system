# PHASE_PLAN — STRATEGY_SHAPED_RESEARCH_LANE_V0

5 phases (`SSRL-P00` … `SSRL-P04`) on a `dag_wave` scheduler with a serial merge queue.
Phases have linear dependencies and overlapping `src/` footprints (governance / research /
strategies), so the DAG **linearizes to sequential**: `P00 → P01 → P02 → P03 → P04`. Phase
ids/lanes/deps/allowed_paths are authoritative in `campaign.yaml`; this file mirrors them.
Disagreement between the two files is a STOP condition.

## Scheduler Wave Map

```text
Wave 0 : SSRL-P00  Bootstrap + REUSE-MAP/scope lock (GREEN, run-alone)
Wave 1 : SSRL-P01  SetupSpec + MechanismCard contract classes (YELLOW)
Wave 2 : SSRL-P02  Context!=trigger conditional probe — additive, path-label outcomes, EXPLORATORY (YELLOW)
Wave 3 : SSRL-P03  First-light strategy-shaped example on a small slice + de-stack probe (YELLOW)
Wave 4 : SSRL-P04  Trusted-handoff scaffold + AI-researcher happy-path + PA_GRAMMAR naming docs (YELLOW)
```

## Phase contracts

### SSRL-P00 — Bootstrap + REUSE-MAP/Scope Lock (GREEN)
Land the bundle + pointer; write `docs/strategy_shaped_lane/REUSE_MAP.md` + `V0_SCOPE.md`
pinning the reused engines (path labels, path-outcome diagnostics `diagnostics.py:451-452/938-991`,
`SINGLE_FACTOR_THRESHOLD_TEMPLATE`, governance spec chain + ledgers) and the explicit
OUT-of-scope list (sequence, geometry sweeps, sim-bridge, feature fast lane). No code.

### SSRL-P01 — SetupSpec + MechanismCard Contracts (YELLOW)
The verified-missing objects. `MechanismCard` (source/rationale/mechanism/horizon/session/
required-features/required-labels/cost/variant_budget/duplicate-note) + `SetupSpec`
(entry_context, **event_trigger SEPARATE from context**, regime_filter, confirmation,
invalidation, stop/target/hold_time, horizon, path_label binding, allowed_variants,
forbidden_post_hoc_changes, mechanism_id). Content-addressed, validated, EXPLORATORY-stampable.
Reuse `governance/study_spec.py` conventions; do not duplicate AlphaSpec/StudySpec. Schema + tests only.

### SSRL-P02 — Context≠Trigger Conditional Probe (YELLOW) — the core capability
**Add** a conditional template *alongside* `SINGLE_FACTOR_THRESHOLD_TEMPLATE` (never modify it);
compile a SetupSpec → a probe scoring a **separate** trigger factor conditioned on a **separate**
context-bucket, over **existing** path labels + the already-wired path-outcome diagnostics.
**Fixed geometry; no sequence; no sim-bridge (research/ must not import backtest/management/fast_path);
outcomes from path labels only.** Every output EXPLORATORY-stamped; the trusted/promotion path
**refuses** EXPLORATORY artifacts (fail-closed guard + canary). Variants bounded via VariantLedger/
family_budget; surrogate-FDR zero-pass + per-factor MDE/power (`power.py`) on every readout.

### SSRL-P03 — First-Light Example + De-Stack Probe (YELLOW)
One context≠trigger idea (e.g. range-contraction context + prior-high-sweep-then-reclaim trigger,
target = path-label target-before-stop, hold ≤120m) end-to-end on a small real slice, EXPLORATORY,
variant-ledgered. Plus the cheap unexhausted **de-stack** read (settler-flagged
`vwap_session.factor_session_minute` IC +0.068 @ n=6862 vs ~0 stacked) on the existing engine,
zero new code. Value-free evidence only; no promotion.

### SSRL-P04 — Trusted-Handoff Scaffold + Docs (YELLOW)
From a promising EXPLORATORY probe, emit the AlphaSpec/StudySpec/FeatureRequest/LabelSpec **gaps**
for a trusted rerun (promotion requires that rerun; scaffold never promotes). + AI-researcher
happy-path doc + `PA_GRAMMAR_SUBSTRATE_V1` naming/positioning note (FactorLibrary = surviving-alpha
memory only; shape-split factor-first vs setup-first).

## If this is too much
Collapse to P00–P03 (drop P04 to a later docs PR). P00–P02 are the load-bearing capability;
P03 is the proof; P04 is the handoff/docs.
