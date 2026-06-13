# Strategy-Shaped Research Lane V0 Scope Contract

STRATEGY_SHAPED_RESEARCH_LANE_V0 is a capability-investment bootstrap. It makes
strategy-shaped hypotheses expressible, bounded, ledgered, and honestly
rejectable as exploratory research artifacts. It does not claim alpha,
profitability, tradability, deployment readiness, paper-trading readiness,
live-trading readiness, or broker readiness.

## In Scope For V0

- `SetupSpec` and `MechanismCard` contracts that can declare a strategy-shaped
  hypothesis with entry context, event trigger separate from context,
  confirmation, invalidation, stop/target/hold-time intent, horizon, path-label
  binding, allowed variants, forbidden post-hoc changes, and mechanism identity.
- A bounded context != trigger conditional probe over existing path labels and
  the already-wired path-outcome diagnostics.
- EXPLORATORY quarantine for all probe outputs.
- VariantLedger and family-budget reuse for bounded variants.
- Surrogate-FDR and per-factor MDE/power reporting on readouts through the
  existing governance and diagnostics helpers.
- A trusted-handoff scaffold that can describe gaps for a future trusted rerun
  without promoting exploratory output.
- Value-free documentation and local evidence structure that does not contain
  generated values, raw data, DB files, Parquet/Arrow/Feather files, logs,
  secrets, caches, or run artifacts.

## Out Of Scope And Deferred

These are explicitly deferred behind a later trigger and are not part of V0:

- Multi-bar sequence state machine or sequence encoder.
- Target/stop geometry sweeps.
- Research-to-reference-sim bridge.
- Feature-research fast lane.
- FactorLibrary or AlphaBook.
- PA grammar pack.
- Strategy backtester.
- Paper trading, live trading, broker calls, order routing, capital interaction,
  deployment, or production operation.
- New paid data.
- New runtime dependency.
- Any change to the existing single-factor study path.
- Any new PnL or value-accounting implementation.
- Any grid search surface outside the pre-registered bounded variant budget.

## Hard Invariants

1. EXPLORATORY != promotion evidence. The trusted and promotion paths must refuse
   exploratory artifacts; exploratory readouts are not evidence for promotion.
2. No research-to-reference-sim bridge and no second PnL truth. The sanctioned
   reference engine remains the only value/accounting truth; V0 outcomes come
   from materialized path labels and diagnostics readouts.
3. The single-factor path is additive-only and unchanged. New conditional
   capability can be added alongside `SINGLE_FACTOR_THRESHOLD_TEMPLATE`, but the
   existing one-factor template and truth-chain invariants stay intact.
4. V0 is bounded and not a grid. Variants are pre-registered, ledgered, and
   family-budgeted; target/stop geometry sweeps, sequence state machines, and
   feature fast-lane expansion stay deferred.

## Promotion Boundary

V0 can produce exploratory, value-free research artifacts and trusted-handoff
gap descriptions. Promotion requires a separate trusted rerun through the
sanctioned governance path. The handoff scaffold never promotes, converts, or
endorses an exploratory result as trusted evidence.

## Phase Boundary

SSRL-P00 is documentation and bootstrap only. It confirms the campaign bundle
and writes this scope contract plus the reuse map. It introduces no code, no
engine change, no executable probe, no simulation, no tests, no dependency, and
no data artifact.
