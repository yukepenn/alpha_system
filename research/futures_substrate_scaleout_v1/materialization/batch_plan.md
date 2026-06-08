# Materialization Batch Plan

Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
Phase: `FUTSUB-P05`

This value-free plan pins the batch units, budgets, checkpoint scheme, serial
registry guard, and dry-run identity preview for the full-window FeaturePack and
LabelPack materialization phases. It does not materialize values, read provider
files, write Parquet, write SQLite, or create checkpoint markers.

## Execution Gate

Every downstream batch must resolve an exact DatasetVersion id through the local
acceptance lock and fail closed unless the resolved state is `ACCEPTED` or
`ACCEPTED_WITH_WARNINGS`. The committed FUTSUB-P02 summary currently records
`0` accepted, `0` accepted-with-warnings, and `27` blocked DatasetVersions, so
this P05 plan intentionally does not declare any executable batch from the
committed summary alone. Later materialization phases must use the local
registry lock state, not registered-only ids, before executing.

The plan remains useful before that gate because it fixes the governed unit
grid, budgets, identities, checkpoints, and serial registry contract.

## Batch Unit Contract

Each batch unit is content-addressed from value-free metadata:

```text
unit_id = mbu_<sha256(canonical_json(
  schema,
  campaign_id,
  pack_kind,
  family,
  symbol or target_symbol,
  year,
  horizon or event_horizon where applicable,
  input_schemas,
  exact DatasetVersion id or ids after acceptance-lock resolution,
  value_store_format = parquet
))>
```

The unit grain is deliberately bounded:

- Feature units: `family x symbol x year` for all eight governed families.
- Cross-market units: `family x target_symbol x year`, with ES/NQ/RTY as the
  aligned input universe and no cross-instrument forward-fill.
- Label units: `family x symbol x year x horizon` or
  `family x symbol x year x event_horizon`.

Each completed unit must be recognizable on resume by the same `unit_id`, the
same registry version id, the same DatasetVersion id or ids, and the same value
content hash recorded in its completion marker.

## Feature Batch Budgets

The per-unit row budget is a conservative full-year cap for one-minute futures
data. The 2026 partial year may consume less, but the unit budget remains the
same so the scheduler can reason about worst-case work.

| Config | Phase | Input schemas | Unit count | Row budget / unit | Aggregate row budget | Parquet files / unit |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `configs/features/scaleout/base_ohlcv.json` | `FUTSUB-P06` | `ohlcv_1m` | 27 | 550,000 | 14,850,000 | 1 |
| `configs/features/scaleout/session_calendar_maintenance.json` | `FUTSUB-P07` | `ohlcv_1m`, `ohlcv_dense_research_grid` | 27 | 550,000 | 14,850,000 | 1 |
| `configs/features/scaleout/vwap_session_auction.json` | `FUTSUB-P08` | `ohlcv_1m` | 27 | 550,000 | 14,850,000 | 1 |
| `configs/features/scaleout/regime_volatility_compression.json` | `FUTSUB-P09` | `ohlcv_1m` | 27 | 550,000 | 14,850,000 | 1 |
| `configs/features/scaleout/liquidity_sweep_pa_structure.json` | `FUTSUB-P10` | `ohlcv_1m` | 27 | 550,000 | 14,850,000 | 1 |
| `configs/features/scaleout/volume_activity.json` | `FUTSUB-P11` | `ohlcv_1m` | 27 | 550,000 | 14,850,000 | 1 |
| `configs/features/scaleout/bbo_tradability_top_book.json` | `FUTSUB-P12` | `bbo_1m` | 27 | 550,000 | 14,850,000 | 1 |
| `configs/features/scaleout/cross_market_alignment.json` | `FUTSUB-P13` | `ohlcv_1m`, `ohlcv_dense_research_grid` | 27 | 550,000 output / 1,650,000 input | 14,850,000 output / 44,550,000 input | 1 |

Total governed feature budget: `216` batch units, `118,800,000` output rows,
and `216` Parquet value files.

## Label Batch Budgets

Labels use the same row cap per output unit. Extended, cost-adjusted, and path
labels also carry overlap or compute metadata requirements; rows are not
independent samples.

| Config | Phase | Horizons | Unit count | Row budget / unit | Aggregate row budget | Parquet files / unit |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `configs/labels/scaleout/fixed_horizon.json` | `FUTSUB-P16` | `1m`, `3m`, `5m`, `10m`, `15m`, `30m` | 162 | 550,000 | 89,100,000 | 1 |
| `configs/labels/scaleout/extended_horizon.json` | `FUTSUB-P17` | `60m`, `120m`, `240m` | 81 | 550,000 | 44,550,000 | 1 |
| `configs/labels/scaleout/session_close_maintenance_flat.json` | `FUTSUB-P18` | `session_close`, `maintenance_flat` | 54 | 550,000 | 29,700,000 | 1 |
| `configs/labels/scaleout/cost_adjusted.json` | `FUTSUB-P19` | `1m`, `3m`, `5m`, `10m`, `15m`, `30m`, `60m`, `120m`, `240m` | 243 | 550,000 output / 1,100,000 input | 133,650,000 output / 267,300,000 input | 1 |
| `configs/labels/scaleout/path.json` | `FUTSUB-P20` | `5m`, `10m`, `15m`, `30m`, `60m`, `120m`, `240m` | 189 | 550,000 rows / 2,200,000 path metric evaluations | 103,950,000 rows / 415,800,000 evaluations | 1 |

Total governed label budget: `729` batch units, `400,950,000` output rows, and
`729` Parquet value files. Total governed materialization budget across feature
and label phases is `945` batch units and `945` research-scale Parquet value
files.

## Checkpoint Scheme

All checkpoints are local-only under `ALPHA_DATA_ROOT` and are expressed in the
configs as `ALPHA_DATA_ROOT`-relative paths. No marker, manifest, backup,
Parquet file, or SQLite registry is commit-eligible.

For each family:

- checkpoint root:
  `materialization/futures_substrate_scaleout_v1/checkpoints/{features|labels}/{family}`;
- per-unit marker:
  `.../units/{unit_id}.json`;
- completed manifest:
  `.../completed_units.jsonl`;
- inflight marker:
  `.../inflight/{unit_id}.json`;
- recovery notes:
  `.../recovery/{unit_id}.json`.

A unit is complete only after all of the following are true:

- the materialized Parquet value file exists under the configured value
  namespace;
- the value content hash matches the value-store handle;
- the shared SQLite registry has the exact feature or label version id with
  `value_store_format`, `parquet_path`, `value_content_hash`,
  `value_schema_version`, `dataset_version_id`, and the feature or label version
  id;
- the completion marker has been atomically written after registry commit.

Resume order:

1. Load the completed manifest and all per-unit completion markers.
2. Recompute each planned unit id from the config and accepted DatasetVersion
   ids.
3. Skip a unit only when marker, registry record, DatasetVersion id, and value
   content hash agree.
4. Treat an inflight unit without a valid completion marker as incomplete.
5. For an incomplete unit, run the recovery procedure before retrying the unit.

The completed manifest is append-only. The per-unit marker is authoritative for
idempotent skip decisions because it carries the full content-addressed unit
identity and registry/value-store hash tuple.

## Serial Registry Resource Guard

The Workflow 2 scheduler serializes registry-writing materialization phases via
`resource_class: materialization_registry`; the family configs repeat the
contract with `parallel_safe: false`. A single phase run must also serialize
within its batch loop:

1. Acquire the local registry guard before any write to
   `registry/features.sqlite` or `registry/labels.sqlite`.
2. Write or verify the Parquet value file before the registry transaction, but
   do not write the completion marker yet.
3. Back up the target registry under
   `materialization/futures_substrate_scaleout_v1/registry_backups/{features|labels}/{timestamp}_{unit_id}.sqlite`.
4. Register metadata through the sanctioned feature or label materialization
   path in one SQLite transaction.
5. Verify the registry record matches the value-store handle and accepted
   DatasetVersion id.
6. Atomically write the per-unit completion marker, then append the completed
   manifest.
7. Release the registry guard.

The guard is a serial-write contract, not a permission to bypass DatasetVersion
acceptance, value-store hash checks, or artifact locality.

## Restart-Safe Recovery

If the process stops before the registry write starts, the next run deletes or
supersedes the stale inflight marker and recomputes the unit. If the Parquet file
exists but no marker exists, the next run verifies its content hash before
deciding whether to reuse it or overwrite through the value-store path.

If interruption happens during or after a registry write:

- inspect the per-unit inflight marker and local registry backup;
- verify SQLite integrity for the target registry;
- verify whether the exact registry record exists and matches the value-store
  hash and DatasetVersion id;
- if the record is absent or mismatched and the backup is valid, restore the
  local-only registry backup before retrying;
- if the record is valid but the completion marker is missing, write the marker
  after re-verifying the value hash;
- if the registry cannot be proven valid or restored, stop the phase and record
  the failed unit rather than proceeding to another registry write.

This procedure prevents double-writing completed units and keeps corrupt or
partial SQLite writes from silently contaminating later resolver checks.

## Dry-Run Identity Preview

The preview below is value-free. It was derived from canonical JSON unit
descriptors and hash formulas in this plan; no `alpha feature materialize
--execute`, `alpha label materialize --execute`, registry write, Parquet write,
provider read, or checkpoint write was run.

The `dataset_version_id_preview` values are representative ids from the P02
inventory. They are not treated as executable unless the local acceptance lock
resolves them to an eligible state.

| Kind | Family | Symbol | Year | Variant | Unit id | Plan id preview | Version id preview |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| feature | `base_ohlcv` | `ES` | 2024 | `full_year` | `mbu_7b0557507c0a752391b01652` | `fmat_52b755e02092aad364a26478` | `fver_preview_4becfbd4e7c5c6451d69` |
| feature | `bbo_tradability_top_book` | `NQ` | 2024 | `full_year` | `mbu_a5813a5d38bbab128f565055` | `fmat_a5b5149a5af75931d3978cd8` | `fver_preview_474eabb715b8d0bee1fd` |
| feature | `cross_market_alignment` | `RTY` | 2024 | `full_year` | `mbu_649f69a98d3ce0ad392a46da` | `fmat_08ecdee80a1e294a5a6bceb0` | `fver_preview_f3ce80dbc47cd5ad4df7` |
| label | `fixed_horizon` | `ES` | 2024 | `5m` | `mbu_47797ab6f9871a3945d7709f` | `lmat_140efbcdd0d626099b38ff60` | `lver_preview_4482fcb23f2b9464470d` |
| label | `extended_horizon` | `NQ` | 2024 | `240m` | `mbu_261af5d4c9fab961c6f45555` | `lmat_5de2dadb8dc7372bfdf8239e` | `lver_preview_7a2c91e22d4758f5fe08` |
| label | `session_close_maintenance_flat` | `RTY` | 2024 | `maintenance_flat` | `mbu_f791cf293c412cc1cff01379` | `lmat_4146983a8ba738d95df4591e` | `lver_preview_2562823b74d73f60b611` |
| label | `cost_adjusted` | `ES` | 2024 | `30m` | `mbu_28ef22dffe7489b838372519` | `lmat_380e1a9b1d2071a61c0afadf` | `lver_preview_9b59d67f65ba1ffc9e06` |
| label | `path` | `NQ` | 2024 | `60m_triple_barrier` | `mbu_07e128c12bcf174fb2d9598f` | `lmat_9cd2d2bc777127966cd76077` | `lver_preview_adc4f803f84a2580c4ba` |

## Boundaries

This phase made no materialization write and no production, paper, live, broker,
order, deployment, profitability, tradability, or capital-allocation claim.
JSONL remains audit/small/smoke tier only. Research-scale values are Parquet and
local-only under `ALPHA_DATA_ROOT`; SQLite registries are metadata only and are
never committed.
