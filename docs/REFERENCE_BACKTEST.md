# Reference Backtest

## Scope

`alpha_system.backtest.reference` is the Tier 1 reference 1-minute bar backtest
engine for this campaign. It is a local, offline research engine for
deterministic strategy accounting over canonical 1-minute bars and declared
`SignalRecord` streams.

It is not a broker adapter, paper adapter, live adapter, order router, account
sync layer, or production execution lifecycle. It does not ingest data and does
not make claims about strategy quality.

## Timing Rules

The engine enforces point-in-time timing from availability fields:

- a bar is usable only when `available_ts >= bar_end_ts + data_latency_seconds`;
- a signal must reference an origin bar by `instrument_id`, `session_id`, and
  `bar_index`;
- a signal must have `available_ts >= origin_bar.available_ts`;
- a signal on bar `t` cannot execute inside bar `t`;
- default execution is `next_bar_conservative`, meaning the engine chooses the
  first later bar whose open time is not before the signal `available_ts`.

If these checks fail, the run raises a timing error instead of simulating an
early fill.

## Conservative Fills

Entries and signal exits fill on the selected next eligible bar. Long entries
use the ask when present and otherwise the open. Long exits use the bid when
present and otherwise the configured fallback. Short entries use the bid; short
exits use the ask.

The same-bar stop/target policy is `adverse_first`. When both a stop and target
are reachable in the same 1-minute bar, the stop is selected. This prevents the
engine from choosing an optimistic ordering that cannot be known from OHLC bars.

EOD flat behavior is optional. When enabled, any remaining position for the last
bar of a session is closed with a conservative EOD exit price.

## Costs

`ReferenceEngineConfig.cost_model` is a required wiring point. The campaign
default config uses a non-zero fixed-bps placeholder. ASV1-P16 hardens the full
cost model. Zero-cost runs are allowed only when explicitly configured for small
synthetic correctness fixtures.

## Trade Journal

Each closed position emits one trade journal row with stable fields:

`trade_id`, `run_id`, `instrument_id`, `session_id`, `strategy_id`,
`strategy_version`, `direction`, `quantity`, `entry_signal_id`,
`exit_signal_id`, `entry_order_id`, `exit_order_id`, `entry_ts`, `exit_ts`,
`entry_bar_index`, `exit_bar_index`, `entry_price`, `exit_price`, `gross_pnl`,
`costs`, `net_pnl`, `exit_reason`, `data_version`, `factor_versions`,
`quality_flags`.

## Equity Curve

The equity curve is emitted after each processed bar with stable fields:

`run_id`, `timestamp`, `bar_end_ts`, `instrument_id`, `session_id`,
`bar_index`, `cash`, `realized_pnl`, `unrealized_pnl`, `total_equity`,
`open_positions`.

The curve is deterministic for a fixed bar stream, signal stream, config, and
run id.

## Registry And Manifest

When a temp/local `registry_path` is provided, the engine initializes the
existing metadata registry and inserts one row into `backtest_runs`. It uses the
existing reproducibility fields: run id, git metadata, code hash, config hash,
data version, factor versions, engine version, parameters, artifact paths,
warnings, and decision status. No registry migration is added by this phase.

The run manifest records the same local run context and artifact paths.

## Artifact Policy

Full trade journals, equity curves, summaries, manifests, and registry files
are local-only. The default output root is `/tmp/alpha_system/backtests`.
Repository paths are rejected for full backtest outputs. SQLite/DB/WAL files,
Parquet/Arrow/Feather files, logs, generated data, and `runs/**` files must not
be staged or committed.
