# DatasetVersion Acceptance-Lock Contract

`FUTSUB-P02` adds a persisted, local-only acceptance-lock for registered
Databento DatasetVersions. A registered DatasetVersion is not accepted until an
explicit lock records one of:

- `ACCEPTED`
- `ACCEPTED_WITH_WARNINGS`
- `BLOCKED`

No other state is valid. These states are data-substrate gates only. They do
not imply research approval, tradability, profitability, paper/live readiness,
production readiness, or capital allocation.

## Scope

The campaign policy in
`configs/data/dataset_acceptance/futsub_p02_policy.json` covers:

- schemas: `ohlcv_1m`, `ohlcv_dense_research_grid`, `bbo_1m`;
- symbols: `ES`, `NQ`, `RTY`;
- yearly DatasetVersions from 2018 through the partial 2026 window;
- exact registry resolution through DatasetVersion ids, with no fuzzy fallback.

Inventory reads only the local DatasetVersion registry and the registry's
value-free metadata artifacts. It does not read raw provider files, canonical
data files, feature values, label values, Parquet files, or network resources.

## Coverage Dimensions

Each lock carries a value-free coverage report with these dimensions:

- schema presence and exact source/schema match;
- symbol coverage against the expected universe;
- year/date-range coverage;
- row-count and expected-bar sanity evidence;
- gap coverage evidence;
- required-field evidence for canonical timestamps, `available_ts`,
  `exchange_trade_date`, `session_segment`, continuous provenance, roll-boundary
  metadata, quality flags, and missingness flags;
- missingness and quality-flag evidence;
- continuous-series provenance for `ES.v.0`, `NQ.v.0`, and `RTY.v.0`;
- roll policy and approximate roll-boundary metadata evidence;
- exact registry resolution metadata.

Missing required coverage evidence fails closed. It yields `BLOCKED` when the
policy requires that dimension, never `ACCEPTED`.

## CLI Surface

Read-only inventory:

```bash
alpha registry dataset-acceptance inventory \
  --registry-path "$ALPHA_DATA_ROOT/registry/datasets.sqlite" \
  --config configs/data/dataset_acceptance/futsub_p02_policy.json \
  --summary-out research/futures_substrate_scaleout_v1/dataset_acceptance/acceptance_summary.md
```

Persist local locks:

```bash
alpha data accept-datasets \
  --registry-path "$ALPHA_DATA_ROOT/registry/datasets.sqlite" \
  --config configs/data/dataset_acceptance/futsub_p02_policy.json \
  --summary-out research/futures_substrate_scaleout_v1/dataset_acceptance/acceptance_summary.md
```

Show one persisted lock:

```bash
alpha registry dataset-acceptance show \
  --registry-path "$ALPHA_DATA_ROOT/registry/datasets.sqlite" \
  --dataset-version-id <exact_dataset_version_id>
```

## Locality Policy

Persisted acceptance locks live in the local DatasetVersion registry under
`$ALPHA_DATA_ROOT`; that SQLite file is never committed. The committed
acceptance summary is value-free metadata only: per-version state, schema/year,
and coverage reason counts. It contains no per-row prices, quotes, volumes,
feature values, label values, provider responses, heavy artifacts, or local
database content.
