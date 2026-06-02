# Cost And Slippage

`alpha_system.backtest.costs`, `slippage`, `liquidity`, and `fill_models`
define deterministic, local-only research execution assumptions for the Tier 1
reference 1-minute backtest engine. They are not broker schedules, order
routing code, paper trading, live trading, or production execution advice.

## Cost Models

Supported cost components are:

- fixed commission per fill;
- per-share or per-contract commission;
- basis-point cost on fill notional;
- half-spread and full-spread assumptions when spread data is present;
- explicit fixture-only zero cost.

Non-test defaults are conservative and non-zero. `default_execution_config()`
uses non-zero bps cost and non-zero bps slippage. A zero-cost model must be
created through `fixture_zero_cost_execution_config()` or a config payload with
`zero_cost_fixture: true`, `cost_model.model: "zero_cost"`, and
`fixture_only: true`.

## Slippage Models

Supported slippage components are:

- fixed bps slippage that moves the fill price adversely;
- spread-sensitive slippage that scales with observed bid/ask spread;
- an adverse-selection proxy hook that calls a configured local function and
  applies its returned bps adversely.

The proxy hook is a research extension point for deterministic local fixtures
or reviewed offline studies. It is not a broker model, market-impact engine, or
live execution signal.

## Liquidity Controls

`LiquidityPolicy` applies a simple volume participation cap. It can cap fill
quantity, reject fills that exceed the cap, or add a deterministic penalty when
quantity is capped. This is a local research approximation only; it is not L2
queue modeling or passive-fill simulation.

## Reference Integration

`ExecutionConfig` exposes the same timing/accounting fields that the P15
reference runner already consumes and adds cost, slippage, liquidity, and
missing-quote metadata to `to_dict()`. The reference runner includes this
payload in the config hash and run manifest, preserving reproducibility without
creating a second PnL truth.

The current P15 fill path consumes `ExecutionConfig.cost_model.cost_for_notional`
for deterministic cost accounting. The full `ConservativeFillModel` resolves
spread-aware fill prices, adverse slippage, liquidity controls, and cost
breakdowns for unit-level semantics. Future engine wiring must continue to
defer accounting truth to the reference engine.

## Fixture Limits

All tests use tiny synthetic correctness fixtures. They are not market evidence
and must not be used to claim alpha, tradability, or production readiness.
