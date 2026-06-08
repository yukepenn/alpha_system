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

Inventory resolves DatasetVersions only through the local registry APIs. Coverage
evidence is computed from local canonical partitions through
`canonical_partition_path` / `load_canonical_ohlcv_rows` and each
DatasetVersion's canonical `manifest.json` row count. It does not read raw
provider files, feature values, label values, or network resources.

## Coverage Dimensions

Each lock carries a value-free coverage report with these dimensions:

- schema presence and exact source/schema match;
- symbol coverage against the expected universe;
- year/date-range coverage;
- row-count and expected-bar sanity evidence from the manifest count, per-symbol
  canonical row counts, and the on-disk symbol-minute grid;
- gap coverage evidence from distinct trading-day counts and each symbol's
  minute coverage against the union of canonical ES/NQ/RTY minutes;
- required-field evidence for canonical timestamps, `available_ts`,
  `exchange_trade_date`, `session_segment`, continuous provenance, roll-boundary
  metadata, quality flags, and missingness flags;
- missingness and quality-flag evidence;
- continuous-series provenance for `ES.v.0`, `NQ.v.0`, and `RTY.v.0`;
- roll policy and approximate roll-boundary metadata evidence;
- exact registry resolution metadata.

Missing required coverage evidence fails closed. It yields `BLOCKED` when the
policy requires that dimension, never `ACCEPTED`. The partial 2026 window yields
`ACCEPTED_WITH_WARNINGS` when the canonical evidence is otherwise within policy.

## Roll Metadata Defer

Exact approximate roll-boundary records are produced by `FUTSUB-P03`, which is
downstream of this phase. `FUTSUB-P02` therefore does not fabricate roll records.
The P02 policy sets `roll_metadata_required` to `false`; the roll dimension is
populated as `deferred_pending_FUTSUB_P03` and bound to the DatasetVersion
`roll_policy_id`. If a later policy requires roll records before P03 has
persisted them, the same dimension degrades to a warning rather than a uniform
blocked grid.

Roll metadata in this contract is an approximate research-data guard input, not
execution truth, back-adjustment truth, or a broker roll engine.

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
