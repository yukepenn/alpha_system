# REUSE MAP - DIFFERENTIATED_KILLSHOT_V1

Status: DK-P00 scope lock. This document names existing machinery that later
phases must reuse. It is documentation only: no code, no engine change, no
metric, and no new dependency.

## Governance Machinery

Later phases must reuse the existing governance objects instead of rebuilding
parallel versions:

- `src/alpha_system/governance/study_spec.py`
- `src/alpha_system/governance/variant_ledger.py`
- `src/alpha_system/governance/surrogate_run.py`
- `src/alpha_system/governance/setup_spec.py`
- `src/alpha_system/governance/mechanism_card.py`
- `src/alpha_system/governance/trial_ledger.py`
- `src/alpha_system/governance/pooled_hypothesis.py`
- `src/alpha_system/governance/feature_request.py`

The FDR active subset is recorded by
`research/differentiated_substrate_v1/FDR_ACTIVE_SUBSET_RESTATEMENT.md`, not by a
new budget object. Strictly increasing budget growth remains governed by the
existing budget-amendment path.

## Study And Probe Machinery

Track A must reuse the existing StudySpec, VariantLedger, surrogate-FDR, trial
ledger, pooled-hypothesis, and runtime diagnostics path.

Track B must reuse `src/alpha_system/research/conditional_probe.py`. The probe
remains pure research logic over caller-supplied observations; it must not grow
a value loader, reference-sim bridge, or promotion path.

## Feature And Label Substrate

Later phases must reuse the existing session/calendar/roll substrate and guards:

- `src/alpha_system/features/families/session/**`
- `src/alpha_system/features/fast/session_calendar_roll.py`
- `src/alpha_system/labels/roll_guard.py`
- `src/alpha_system/labels/roll_guard.py::classify_roll_window`

New zero-feed calendar flags, if authored in later phases, must extend the
existing `SESSION_CALENDAR_ROLL` family additively and stay parity-gated. The
offline-only countdown features must not be recast as live conditioners.

## Calibration And Diagnostics

Later phases must reuse:

- `tools/discovery_rigor_floor/run_real_surrogate_calibration.py`
- `src/alpha_system/runtime/diagnostics/factor/**`
- `src/alpha_system/runtime/diagnostics/splits/**`
- `src/alpha_system/runtime/diagnostics/power.py`

Surrogate-FDR zero-pass remains the pre-real-metric gate for Track A. Runtime
factor diagnostics remain the post-gate readout path.

## Value Loader Boundary

`src/alpha_system/core/value_store.py::load_parquet_values` is pinned as a
tools/runtime-only loader. It may be used by tools or runtime harnesses that
inject rows into pure research functions.

`research/` must not import `core/value_store.py`, `backtest`, `management`, or
fast-path value/accounting code. This campaign does not create a second PnL or
value-accounting truth.

## No Rebuild Rule

If a later phase needs behavior covered by the objects above, it must reuse the
existing object and add only the scoped, reviewed extension authorized by that
phase. Rebuilding a parallel ledger, FDR object, surrogate runner, diagnostics
path, session family, roll guard, value loader, or probe engine is out of scope
for this campaign.
