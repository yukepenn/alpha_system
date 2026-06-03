# Architecture

## Platform Shape

`alpha_system` is a local-first Alpha Research Platform for offline research.
It is designed around domain separation, point-in-time data semantics,
reproducible runs, and one canonical v1 backtest truth.

The architecture is intentionally broader than a backtester. Backtesting is one
research validation layer after data, factor, label, signal, strategy, and
portfolio boundaries have been respected.

## Logical Layers

```text
local storage and registry
data validation and canonical bars
factor definitions and factor values
label generation
diagnostics and studies
signals
strategies
portfolio management
Reference backtest truth
Fast path acceleration
reports and review bundles
Workflow 2 orchestration
```

Each layer has a distinct contract. A later phase may implement a layer only
inside its approved spec.

## Storage And Registry

Large datasets are stored locally as Parquet. SQLite is the intended local
metadata and registry source of truth. DuckDB queries local Parquet files, and
Polars supports lazy dataframe pipelines. Generated data, local DB files,
reports, and run state remain local-only unless a later phase explicitly
authorizes a tiny synthetic fixture under `tests/fixtures/**`.

## Domain Boundaries

The architecture treats boundaries as enforceable invariants:

- Data is not factor.
- Factor is not signal.
- Signal is not strategy.
- Strategy is not portfolio.
- Portfolio is not execution.
- Backtest is not live trading.
- Fast research simulation is not execution truth.

Draft factor values may be used for exploratory diagnostics, but they are not
automatically long-term stored. Only validated and reviewed factors may be
materialized into the long-term factor store.

## Backtest Truth

Tier 1 is the Reference 1-minute bar execution truth for v1. It is
conservative, deterministic, point-in-time, and the single canonical PnL truth.
There must never be two conflicting PnL truths.

The Fast path uses NumPy and Numba for acceleration only. It must match the
Reference behavior on fixtures before use and must never become a second truth.

Tier 3 event-driven execution truth and Tier 4 L2/L3 replay are future
design-readiness concepts only for this campaign.

## Timestamp Model

Research data must distinguish `event_ts`, `bar_start_ts`, `bar_end_ts`,
`receive_ts`, `available_ts`, and `label_available_ts`. Completed bars become
usable only after `bar_end_ts` plus configured latency. Signals on bar `t`
cannot execute inside bar `t` by default. The default is conservative next-bar
execution with conservative same-bar stop and target handling.

## Reports

Reports are local Markdown, CSV, and optional static HTML. They require no
server. Report language must distinguish diagnostics, candidates, review state,
and limitations without unsupported claims.

## Onboarding Documents

The practical operating guides for this architecture are:

- `docs/ONBOARDING.md`
- `docs/RESEARCHER_GUIDE.md`
- `docs/AI_AGENT_GUIDE.md`
- `docs/CLI_REFERENCE.md`
- `docs/EXAMPLE_WORKFLOWS.md`
- `docs/TROUBLESHOOTING.md`
- `docs/RESEARCH_INTERPRETATION_POLICY.md`

## Workflow 2 Boundary

Ralph owns validation orchestration, review routing, verdict parsing, PR/CI,
merge gates, done-checks, and STOP/resume. Codex executes generated phase specs
and writes truthful handoffs. Yellow phases require review before merge
eligibility.

No broker, paper trading, live trading, order routing, or production execution
layer exists in v1.
