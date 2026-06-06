# Signal Probe Runtime

`alpha_system.runtime.probe` implements the Tier 1 Simple Signal Probe. It is a
fast descriptive screen for one already-approved `AlphaSpec` + `StudySpec`, one
resolved `RuntimeInputPack`, one target feature/signal, and one target
label/horizon. It is not strategy validation, not a backtest product, not a
candidate, and not a promotion decision.

## Contract

`SignalProbeSpec` is immutable and hashable. It binds references to:

- the approved `AlphaSpec` and `StudySpec`;
- the resolved, accepted `RuntimeInputPack`;
- one feature pack handle and one label pack handle from that input pack;
- a finite declared threshold neighborhood;
- a direction policy: `long_short_flat`, `long_flat`, or `short_flat`;
- a fill policy that forbids same-bar execution;
- a `CostStressSpec` whose profile set includes `double_cost`.

The spec fails closed when required references are missing, the feature or label
handle is absent from the input pack, `available_ts` / `label_available_ts`
metadata is missing, the threshold neighborhood is empty or unbounded, the fill
policy permits same-bar fills, cost stress is absent, or locked/shadow partition
use lacks governance contamination metadata.

## Fill Rule

The signal generated on observation `i` can first affect the position on
observation `i + delay_bars`. The default is `next_bar` with `delay_bars = 1`.
`delay_bars = 0` is rejected. A signal whose `available_ts` is later than the
eligible fill bar `event_ts` is rejected. This prevents same-bar optimistic
fills and proves availability ordering locally; the later `NoLookaheadRuntimeAudit`
phase owns the unified audit object.

## Report

`SignalProbeReport` is also immutable and scalar-only. It carries:

- position and trade summaries;
- trade count and turnover;
- cost-aware expectancy proxies across the cost profiles, including
  `double_cost`;
- a drawdown proxy;
- a bounded threshold-neighborhood stability summary;
- a reference to the attached `CostSensitivityReport`;
- explicit limitations and non-promotional flags.

A `SignalProbeReport` is invalid without an accompanying `CostSensitivityReport`
that includes `double_cost`. Zero-cost results remain diagnostic-only and are
never a promotion basis.

Valid successful reports use `SIGNAL_PROBE_COMPLETE` and attach
`COST_STRESS_COMPLETE` evidence. Failed screens remain visible as `REJECTED`,
`INCONCLUSIVE`, or `BLOCKED` with a descriptive probe-local reason. RT-P15 will
adapt those local reasons into the formal runtime decision-state contract.

## Boundaries

The probe consumes existing runtime surfaces by import. Cost math is reached only
through `alpha_system.runtime.cost`; the probe package does not import
`alpha_system.backtest.*` directly and does not duplicate research,
experiments, governance, cost, or slippage primitives.

No external provider calls, raw-provider reads, broker operations, paper/live
trading, order routing, portfolio construction, management grid, Reference
validation, or CLI surface is added here. Runtime values and any heavy outputs
remain local-only and uncommitted.

## Synthetic Template

`configs/runtime/probe/default_signal_probe.json` is a tiny synthetic-safe
template that references `tests/fixtures/runtime/probe/`. It is intended for
local tests and documentation only, not market-data evidence.
