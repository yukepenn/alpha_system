# Strategy-Shaped Research Lane V0 Scope Contract

`STRATEGY_SHAPED_RESEARCH_LANE_V0` is a capability campaign. It makes a bounded
strategy-shaped research lane expressible, ledgered, and honestly rejectable as
EXPLORATORY research. It does not claim alpha, profitability, tradability,
deployment readiness, paper-trading readiness, live-trading readiness, or broker
readiness.

## In Scope

- `SetupSpec` and `MechanismCard` contracts for declaring entry context,
  event trigger separate from context, confirmation, invalidation,
  stop/target/hold-time intent, horizon, path-label binding, allowed variants,
  forbidden post-hoc changes, and mechanism identity.
- One bounded context!=trigger conditional probe over existing path labels and
  the already-wired path-outcome diagnostics.
- EXPLORATORY quarantine for every probe output.
- Reuse of `VariantLedger` and family-budget accounting for bounded variants.
- Surrogate-FDR zero-pass and per-factor MDE/power reporting on readouts.
- Value-free first-light evidence and trusted-handoff scaffolding that can name
  gaps for a future trusted rerun without promoting exploratory output.

## Out Of Scope

These items are deferred behind a later explicit trigger and are not part of V0:

- Multi-bar sequence state machine or sequence encoder.
- Target/stop geometry sweeps.
- Research-to-reference-sim bridge.
- Feature fast lane.
- FactorLibrary or AlphaBook.
- PA grammar pack.
- Broad PA library or strategy zoo.
- Strategy backtester.
- Paper trading, live trading, broker calls, order routing, capital
  interaction, deployment, or production operation.
- New paid data.
- New runtime dependency.
- Any change to the existing single-factor study path.
- Any new PnL or value-accounting implementation.
- Any grid search surface outside the pre-registered bounded variant budget.

## Hard Invariants

1. EXPLORATORY != promotion evidence. Trusted and promotion paths must refuse
   exploratory artifacts; exploratory readouts cannot be promotion evidence.
2. No research-to-reference-sim bridge. `research/` must not import `backtest`,
   `management`, or `fast_path`; outcomes come from materialized path labels.
3. The sanctioned reference engine remains the only PnL/value truth. V0 does not
   create a second accounting implementation.
4. The single-factor path remains byte-unchanged and additive-only.
   `SINGLE_FACTOR_THRESHOLD_TEMPLATE` is not modified; later strategy-shaped
   templates must be added alongside it.
5. V0 is bounded, not a grid. Variants are pre-registered, ledgered, and
   family-budgeted; sequence state machines, geometry sweeps, sim-bridge work,
   and feature fast-lane expansion stay deferred.

## Promotion Boundary

V0 can produce EXPLORATORY, value-free research artifacts and trusted-handoff
gap descriptions. Promotion requires a separate trusted rerun through the
sanctioned governance path. The handoff scaffold never promotes, converts, or
endorses an exploratory result as trusted evidence.

## SSRL-P00 Boundary

`SSRL-P00` is documentation and bootstrap only. It confirms the campaign bundle,
confirms the coordinator-owned active campaign pointer already names this
campaign, and writes this scope contract plus the reuse map. It introduces no
code, no engine change, no executable probe, no simulation, no tests, no
dependency, and no data artifact.
