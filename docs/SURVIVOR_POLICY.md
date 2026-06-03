# Survivor Policy

Management grids require a survivor record. A survivor is a candidate that has
already passed factor diagnostics, a simple signal grid, and a simple management
baseline review. The record is input evidence for review, not a lifecycle
promotion.

## Required Fields

The survivor schema requires:

- `candidate_id`
- `source_run_id`
- `factor_versions`
- `label_versions`
- `strategy_version`
- `baseline_management_config`
- `baseline_portfolio_config`
- `source_grid_config_hash`
- `survivor_eligibility_reason`
- `warnings`
- `review_status`
- `allowed_management_grid_scope`

Human-readable keys from the phase spec, such as `candidate id` and
`review status`, are accepted and normalized to snake_case.

## Eligibility Gate

The gate requires:

- review status of `PASS`, `PASS_WITH_WARNINGS`, `REVIEWED`,
  `REVIEWED_WITH_WARNINGS`, or `ELIGIBLE_FOR_MANAGEMENT_GRID`,
- a non-empty survivor reason,
- source grid config hash,
- requested parameter paths within `allowed_management_grid_scope`,
- requested `max_combinations` no larger than the survivor scope when that
  bound is declared.

If a config lacks survivor evidence, or requests parameters outside the allowed
scope, execution fails with visible reasons. Validation-only legacy management
config checks may still run, but they do not execute a management grid.

## Scope Format

`allowed_management_grid_scope` is a mapping. It may declare:

```json
{
  "management_parameters": [
    "management.fixed_stop.stop_pct",
    "management.laddered_partial_take_profit.steps"
  ],
  "execution_parameters": ["execution.fixed_bps"],
  "max_combinations": 4
}
```

The wildcard `*` is not treated as a finite scope. Parameters must be listed
explicitly so reviewer scope and grid expansion remain auditable.

## Safety Boundaries

The management grid does not make promotion decisions, does not write full
trade logs, and does not introduce broker, live, paper, order-routing, or
deployment behavior. Its outputs are local review evidence with retained
warnings and rejected reasons.
