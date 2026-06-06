# Bounded Grid Runtime

`alpha_system.runtime.grid` is the Tier 1 bounded-grid guard. It accepts a
declared variant space, an explicit `VariantBudget`, and a study/probe binding
reference, then decides whether the grid is allowed to proceed before any grid
execution starts.

The guard is descriptive infrastructure only. A bounded grid is not promotion,
not strategy validation, not a backtest product, and not evidence of
tradability or profitability.

## Contract

`BoundedGridSpec` is immutable and hashable. It binds:

- one reference-only `AlphaSpec` / `StudySpec` / study-run or signal-probe
  context;
- finite parameter axes and candidate values;
- a mandatory `VariantBudget`;
- the partition scope used for grid selection, defaulting to development and
  validation;
- optional governance metadata when a locked or shadow partition is referenced
  for a non-selection audit.

Construction fails closed when the budget is absent, non-positive, not finite,
or when the declared candidate space exceeds the effective budget.

## Primitive Boundary

The runtime grid package does not implement grid math, limit checking, or
overfit-control assessment. It delegates:

- candidate product counting to
  `alpha_system.experiments.limits.product_count`;
- hard combination enforcement to
  `alpha_system.experiments.limits.CombinationLimit`;
- overfit warning/control context to
  `alpha_system.experiments.overfit_controls.assess_management_overfit_controls`.

The runtime layer only normalizes references, records counts, translates
primitive rejections into runtime-shaped reasons, and blocks unsafe partition
scope.

## Locked-Test Rule

Selection on `locked_test_candidate` or `latest_shadow_candidate` is rejected.
Locked or shadow partition use for anything else requires substantive
governance contamination metadata and remains outside the normal Tier 1 grid
path.

Default grid selection scope is development plus validation. This keeps
locked-test selection unreachable by construction for ordinary bounded-grid
runs.

## Run Record

`BoundedGridRunRecord` is value-free. It stores:

- the bounded-grid spec reference;
- the study/probe binding reference;
- the `VariantBudget`;
- realized variant count;
- partition ids used;
- guard outcome;
- visible rejection reasons, when any;
- overfit assessment counts and control-key names;
- repeated-run index and previous run-record ids.

It does not store observations, feature values, label values, market data,
provider responses, local paths, databases, caches, or heavy artifacts.
Repeated runs receive their own records instead of replacing prior attempts.

## Synthetic Defaults

`configs/runtime/grid/default_budget.json` is a small synthetic-safe default for
local tests and examples. It is not market-data evidence and does not authorize
provider access, broker access, paper or live trading, deployment, selection on
locked-test data, or promotion behavior.
