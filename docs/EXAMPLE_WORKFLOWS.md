# Example Workflows

## Scope

These examples are narrative, fixture-based flows for local orientation. They
show how the pieces fit together without supplying production data, broker
instructions, paper trading, live trading, deployment, or order-routing steps.

Use `--help` on each command for exact flags. Fixture results are correctness
validation only. They are not market evidence and do not support alpha,
profitability, robustness, tradability, approval, or production-readiness
claims.

## Data To Canonical Bars

Start with tiny synthetic or temp/local input data. Validate before building
canonical bars:

```bash
alpha data validate --help
alpha data build-bars --help
```

The validation step checks schema, calendar, quality, and availability
semantics. The build step stamps a data version and writes canonical bar output
to a local-only path. Do not commit raw input data, canonical generated data,
registry DBs, summaries, or generated table files.

Safe interpretation: a successful fixture build means the path can produce
schema-compatible bars for the tiny case. It does not say the data source is
complete, clean for research, or suitable for a claim.

## Factor To Diagnostics

Validate a factor spec before using it:

```bash
alpha factor validate --help
alpha factor materialize --help
```

Validation checks declared inputs, factor/label separation, hashes, lifecycle
eligibility, and optional registry recording. Materialization computes local
factor values only when the spec and command policy allow it. Draft or
exploratory factor values should stay temporary unless later review justifies a
more durable local store.

Then run diagnostics:

```bash
alpha study run --help
```

Diagnostics compare versioned factor values with versioned labels under
point-in-time alignment. Preserve warnings, missing coverage, low sample-size
signals, and run manifests. A diagnostic summary can guide the next question,
but it is not PnL truth or approval.

## Diagnostic Report To Factor Card

Build a factor card or study report from local diagnostic summaries:

```bash
alpha report build --help
```

The report should separate:

- observed diagnostics
- warnings and missing evidence
- versions and hashes
- recommendation text, if present
- review status
- known limitations

Use `docs/RESEARCH_INTERPRETATION_POLICY.md` before writing narrative
interpretation. A recommendation is not approval.

## Strategy Grid To Reference Backtest

After diagnostics justify a specific question, define signal and strategy
intent, then run a bounded grid:

```bash
alpha grid run --help
```

Use finite parameter lists and configured bounds. Keep rejected configs,
warnings, failed steps, manifests, and cost sensitivity visible. The default
engine should remain the Reference path. Fast mode is acceleration only and
requires parity for the selected feature set.

Finalist validation returns to the Reference engine:

```bash
alpha backtest run --help
```

The Reference engine is the single PnL truth for the v0.1 1-minute path. It
does not establish live, paper, broker, order-routing, deployment, or promotion
scope.

## Survivor Management Flow

Management grids are survivor-gated:

```bash
alpha management grid --help
```

Use this only after a previous strategy grid has produced an eligible survivor
record with review status, source metadata, baseline configs, warning state,
and allowed grid scope. The management grid explores post-entry rules such as
stops, targets, partials, cooldowns, trailing rules, and end-of-day behavior.

Generated outputs remain local-only and must preserve rejected configs and
failed steps.

## ML Fixture Flow

ML runs consume versioned factor inputs and labels under leakage controls:

```bash
alpha ml run --help
```

Features must reference factor versions. Labels are never features. Splits are
chronological, with purge and embargo controls where configured. ML scores are
research outputs and not promotion decisions.

## Review Bundle Flow

After a research run has local manifests and evidence artifacts, assemble a
review bundle:

```bash
alpha report build --help
```

The review bundle should surface source maps, config/code hashes, registry
records, diagnostics, optional backtest sections, missing artifacts, rejected
configs, failed steps, warnings, promotion decision status, review status, and
known limitations.

Generated bundles are local-only. They support review and audit but do not
change lifecycle state.

## Registry Inspection

Use registry status to inspect local records:

```bash
alpha registry status --help
```

Do not commit registry DBs. If a registry path points under `metadata/` or a
temp directory, the DB remains local-only.
