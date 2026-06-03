# Study Budget Protocol

`ARGOV-P07` makes variant-budget control explicit before diagnostics can be
allowed. The protocol is accounting metadata only; it does not run variants,
execute diagnostics, choose parameters, optimize a strategy, or compute research
results.

## Declared Budget

Every `StudySpec` must declare `variant_budget` as a positive integer cap. The
budget is part of the deterministic `sspec_...` content ID, so changing the cap
changes the governed study plan.

The validator rejects:

- missing or null `variant_budget`;
- zero or negative budgets;
- booleans, floats, strings, or other non-integer values;
- textual unbounded budgets such as `unbounded` or `unlimited`.

This prevents a study plan from silently allowing open-ended variant mining.

## Accounting Helper

`evaluate_variant_budget(variant_budget, observed_count)` is a pure function
over the declared cap and an observed variant count. It returns
`StudyBudgetCheck` metadata:

- `status`: `RESPECTED` or `OVERRUN`;
- `respected`: derived boolean;
- `overrun`: derived boolean;
- `variants_remaining`;
- `overrun_by`.

Observed counts at or below the cap are `RESPECTED`. Counts above the cap are
`OVERRUN` and expose the overrun amount explicitly. The helper performs no IO,
does not mutate a ledger, and does not run a study.

`check_variant_budget(...)` is an alias for the same accounting behavior.

## Later Consumers

ARGOV-P08 will use TrialLedger records to accumulate variants and record failed
runs. ARGOV-P11 will later use promotion gates and contamination metadata. This
phase only defines the declared budget and pure overrun calculation that those
later phases can consume.

## Boundary

Budget status is not evidence quality. A respected budget does not mean
diagnostics passed, and an overrun is not silently accepted. Both states are
metadata that future governance phases must inspect before allowing downstream
state transitions.
