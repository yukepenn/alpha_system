# Management Grid Workflow

`alpha management grid` runs bounded survivor-only position-management
exploration for local research review. The command is not a candidate decision
engine and does not change lifecycle state.

## Required Order

Management grids are only valid after the earlier workflow steps have produced
an eligible survivor record:

1. Factor diagnostics.
2. Simple signal grid.
3. Simple management baseline.
4. Survivor-only management grid.
5. Finalist execution validation in a later phase.

The ASV1-P21 engine enforces the fourth step by requiring a survivor record
with review status, source run metadata, baseline management and portfolio
configs, source grid config hash, survivor reason, warnings, and allowed grid
scope.

## Bounded Search

`ManagementGridSpec` requires explicit finite parameter lists and an explicit
`max_combinations` value. Expansion above that bound is rejected before
materialization and the rejection reason is retained. Open-ended values such as
`*`, empty lists, missing `values`, or scalar parameter declarations are
invalid.

Supported management-grid families include:

- fixed stop, R target, trailing stop, and breakeven stop parameters,
- laddered partial take-profit steps,
- max-holding and cooldown parameters,
- EOD, time-exit, and max-trades-per-day controls,
- execution cost sensitivity through fixed bps and minimum cost.

## Execution Truth

The reference 1-minute path remains the canonical PnL truth. Management-grid
execution uses the managed reference adapter, which reuses reference fills,
costs, accounting, equity, and trade-journal containers. Fast mode is an
acceleration request only: it must pass the existing P19 parity gate for the
requested feature set or route to reference fallback when allowed. Unsupported
fast feature sets fail closed when fallback is disabled.

Same-bar management ambiguity inherits the conservative management and
reference semantics: adverse stop outcomes are resolved before favorable exits.

## Outputs

Each run writes local-only management-study artifacts:

- `baseline_comparison.csv`
- `leaderboard.csv`
- `rejected_configs.csv`
- `monthly_breakdown.csv`
- `cost_sensitivity.csv`
- `run_manifest.json`
- `warnings.json`
- `survivor_eligibility_summary.json`

Rejected configs are never hidden. Output manifests record review-only status,
the survivor gate decision, overfit controls, warnings, failed steps, config
hashes, code hashes, input versions, and artifact paths.

Generated outputs are local-only and must not be committed. Tests and examples
use temp directories or tiny bounded configs.
