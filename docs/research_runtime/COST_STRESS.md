# Cost Stress Runtime

RT-P11 adds a local, descriptive cost-stress layer under
`alpha_system.runtime.cost`. It records a `CostModelVersion`, validates a
`CostStressSpec`, and builds a `CostSensitivityReport` across `base`,
`stress_1`, `stress_2`, and `double_cost`.

The runtime orchestrates `alpha_system.backtest.costs` and
`alpha_system.backtest.slippage`. It constructs primitive models through their
mapping/default surfaces, feeds `CostInput` and `SlippageInput`, and then only
scales and aggregates returned primitive amounts by profile and configured
session multipliers. It does not implement a venue, realized fills, broker
behavior, order routing, live execution, paper execution, deployment behavior,
or a strategy result.

## Versioning

`CostModelVersion` is immutable and hashable. Its identifier is derived from
the normalized primitive cost-model descriptor, primitive slippage-model
descriptor, `slippage_is_proxy = true`, BBO availability, and zero-cost
diagnostic metadata. Slippage is always labeled as a proxy. A zero-cost fixture
reference is diagnostic-only and has `promotion_basis_allowed = false`.

## Profiles And Sessions

The default sample config is
`configs/runtime/cost/default_cost_stress.json`. It is config data, not runtime
logic. It contains the required ordered profile set:

- `base`
- `stress_1`
- `stress_2`
- `double_cost`

`CostStressSpec` fails closed when `double_cost` is absent or when
`requires_double_cost` is not true. The same config also carries RTH, ETH, and
ILLIQUID session multipliers. ETH and ILLIQUID penalties are higher than RTH in
the sample config.

## BBO Handling

When BBO context is supplied and the recorded cost version uses spread-aware
primitive components, the report marks BBO spread crossing as used. When BBO
context is absent, the runtime uses the configured bps proxy descriptors and
records the fallback marker. It never fabricates a spread.

## Report Semantics

`CostSensitivityReport` wraps the RT-P06 `DiagnosticsReport` shape for the
`COST` diagnostics family. It emits scalar profile summaries, session
breakdowns, the required `double_cost` summary, gradient summaries, BBO usage
markers, limitations, status, and visible `RunRejectionReason` records for
fragile or low-sample conditions.

This report is a sensitivity description only. It is not alpha validation, not
strategy validation, not market evidence, and not a basis for factor or
strategy promotion. Fixture outputs are correctness checks only.
