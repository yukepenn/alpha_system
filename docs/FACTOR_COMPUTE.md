# Factor Compute SDK MVP

ASV1-P11 adds a scoped compute SDK for deterministic factor calculation over
canonical 1-minute bars. It is an SDK and controlled local materialization
surface only. Factors computed here are not labels, signals, strategies,
portfolios, backtests, or execution instructions.

## Factor Value Schema

Every computed factor value uses this required schema in stable order:

```text
factor_id
factor_version
instrument_id
event_ts
available_ts
session_id
bar_index
value
normalized_value
quality_flags
data_version
compute_version
```

`event_ts` is the bar event timestamp. `available_ts` is the input bar
`available_ts` plus the factor spec's `availability_lag`; it is not copied from
future data and is never earlier than the input availability timestamp.

## Dependency Rules

Factor implementations receive only the `input_fields` declared in
`FactorSpec`. For the MVP, those fields must come from the canonical
1-minute bar contract and must use the `bar` input domain. The resolver rejects:

- undeclared implementation inputs;
- ad-hoc columns outside the canonical bar contract;
- missing declared input columns;
- label-like fields and label domains.

Labels remain research targets. They are not factor inputs and are not strategy
inputs.

## Compute Semantics

The compute driver is deterministic for the same spec, bars, parameters, and
compute version. It sorts local bars by instrument, data version, session,
bar index, and event timestamp before emitting values.

Warmup is session-aware. If a factor has insufficient warmup bars, the output
`value` and `normalized_value` are null and the quality flags include
`insufficient_warmup`.

When `session_reset` is true, compute history is keyed by instrument, data
version, and session. State does not leak across sessions. When it is false,
history may carry across sessions for the same instrument and data version.

Normalization is point-in-time safe. The default method is identity. The
optional rolling z-score normalizer uses only prior factor values plus the
current value; it does not inspect future values.

Quality flags from canonical bars are propagated to factor values. Additional
factor quality flags represent warmup and normalization conditions.

## Materialization Policy

`alpha factor materialize` computes factor values and can either run as a
dry-run or persist to a local-only factor store. Persistence is lifecycle gated:

- draft factors are blocked by default;
- candidate factors are not long-term materialization eligible by default;
- validated factors require reviewed validation evidence in a temp/local
  registry;
- approved factors also require review-backed promotion evidence;
- this command never approves or promotes a factor.

The command records `data_version`, `compute_version`, `code_hash`, and
`config_hash` in the run manifest and optional temp/local registry entry.

## Local-Only Output Policy

Default factor output paths resolve under `/tmp/alpha_system/factors`.
Explicit output directories, run manifests, and registry paths must resolve to
local WSL paths outside the repository. The SDK writes JSONL factor values and
small JSON manifests only. It does not write Parquet, Arrow, Feather, raw data,
canonical data, label values, or repository-local SQLite files.

## Example Fixture

`configs/factors/examples/correctness_fixture_close_delta.json` defines a tiny
deterministic close-delta fixture for correctness tests. It is synthetic,
fixture-only configuration and is not evidence of a useful, profitable,
robust, tradable, or deployable factor.
