# DatasetVersion Consumption

Future feature/label campaigns consume data by resolving an accepted
`DatasetVersion` from the local registry, then applying their own campaign
contracts. Loading a dataset is a data-admissibility step only. It does not
imply alpha value, profitability, tradability, broker readiness, paper/live
readiness, production readiness, or permission to use locked partitions.

## Registry Lookup

For data-foundation DatasetVersions, use the DATA-P17 adapter:

```python
from alpha_system.data.foundation.version_registry import resolve_dataset_version

version = resolve_dataset_version(registry_path, "dsv_ibkr_es_nq_rty_eth_20260603_v1")
```

The real signature is:

```python
resolve_dataset_version(registry_path: str | Path, dataset_version_id: object) -> DatasetVersion | None
```

It validates the registry path as local-only, initializes the existing SQLite
registry schema if needed, reads the `dataset_versions` row, reconstructs the
full `alpha_system.data.foundation.datasets.DatasetVersion` from
`metadata_json`, and checks the row columns are still bound to the same object.

The older core registry helper in `alpha_system.data.versions` is:

```python
get_dataset_version(connection: sqlite3.Connection, data_version: str) -> DatasetVersion | None
```

That helper returns the core `alpha_system.data.versions.DatasetVersion` shape
from an existing SQLite connection. Future data-foundation consumers should use
`resolve_dataset_version(...)` when they need the full DATA-P17 object and
reproducibility bindings.

## First Real Local DatasetVersion

The first real local-only accepted DatasetVersion recorded by the ADF1
post-closeout backfill was:

```text
dsv_ibkr_es_nq_rty_eth_20260603_v1
```

Recorded scope: ES/NQ/RTY, 1-minute `TRADES`, one complete CME index ETH
session for `2026-06-02T22:00:00Z` through `2026-06-03T21:00:00Z`,
`latest_shadow_candidate`, quality `WARNING` for non-blocking zero-volume
overnight minutes, coverage `PASSING`. The local SQLite registry and all raw or
canonical data artifacts remain outside the repository under `ALPHA_DATA_ROOT`.

## Canonical Bar Contract

Feature/label code must consume canonical bars that satisfy
`CanonicalBarRecord` exactly. Required fields are:

```text
instrument_id
contract_id
series_id
bar_start_ts
bar_end_ts
event_ts
available_ts
ingested_at
open
high
low
close
volume
source
source_request_id
data_version
quality_flags
session_label
```

The five timestamp fields are distinct:

- `bar_start_ts`: inclusive one-minute interval start.
- `bar_end_ts`: exclusive one-minute interval end; must be after
  `bar_start_ts`.
- `event_ts`: completed-bar event time after canonical validation.
- `available_ts`: earliest time the completed bar may be used by research or
  backtest logic; it must be at or after `bar_end_ts` and is not the historical
  API return time.
- `ingested_at`: local ingestion/materialization timestamp, never a substitute
  for `available_ts`.

No-lookahead consumers must order usability by `available_ts`, not by
`event_ts`, provider timestamps, or local ingest time.

## Partition And Contamination Rules

Use `DatasetPartitionPlan.canonical()` for the DATA-P18 partition descriptor:

- `development_partition`: `2018-01-01` through `2022-12-31`.
- `validation_partition`: `2023-01-01` through `2024-12-31`.
- `locked_test_candidate`: `2025-01-01` through `as_of_run`.
- `latest_shadow_candidate`: optional rolling or explicit recent candidate.

Coverage QA may inspect partitions for data quality. Before any non-QA use of
`locked_test_candidate` or `latest_shadow_candidate`, call the guard with
substantive Governance contamination metadata:

```python
from alpha_system.data.foundation.datasets import (
    DatasetPartitionPlan,
    require_governance_metadata_for_locked_partition_use,
)

plan = DatasetPartitionPlan.canonical()
require_governance_metadata_for_locked_partition_use(
    partition_id="locked_test_candidate",
    purpose="feature_label_research",
    governance_metadata=metadata,
    plan=plan,
)
```

The guard signature is:

```python
require_governance_metadata_for_locked_partition_use(
    *,
    partition_id: object,
    purpose: object,
    governance_metadata: Mapping[str, object] | None = None,
    plan: DatasetPartitionPlan | None = None,
) -> bool
```

Missing, empty, vague, or non-mapping Governance metadata fails closed for
non-QA locked-partition use. The contamination rules explicitly do not imply
research approval.

## Local-Only Data Layout

`ALPHA_DATA_ROOT` is the only allowed root for real data artifacts. It must
resolve outside the repository. Raw IBKR payloads live under the raw lake shape:

```text
$ALPHA_DATA_ROOT/raw/source=<source>/request=<request_id>/chunk=<chunk_id>/sha256=<prefix>/<digest>.raw
```

The operator runbook uses a local registry path such as:

```text
$ALPHA_DATA_ROOT/registry/datasets.sqlite
```

Canonical materializations, if a later campaign writes them, must live under
`$ALPHA_DATA_ROOT/canonical/` or another explicitly allowed local-only data
root subdirectory. Raw data, canonical data, local registries, provider
responses, caches, logs, DB files, Parquet, Arrow, Feather, and generated data
bundles are never committed.

## Entry Points

Verified direct module entry points under `src/alpha_system/data/ibkr/`:

- `python -m alpha_system.data.ibkr.manifest_builder`
- `python -m alpha_system.data.ibkr.backfill_connect`
- `python -m alpha_system.data.ibkr.materialize`
- `python -m alpha_system.data.ibkr.smoke_connect`

Use `docs/data_foundation/BACKFILL_RUNBOOK.md` only when a backfill is
explicitly authorized. Dry-run, smoke, and synthetic modes are CI-safe; real
external pulls require the `ALPHA_IBKR_*` and data-pull authorization
environment gates and never run in CI.
