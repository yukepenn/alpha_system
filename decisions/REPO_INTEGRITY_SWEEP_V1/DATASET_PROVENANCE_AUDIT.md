# Repo Integrity Sweep V1 - Dataset Provenance Audit

## Read-Only Registry Facts

Commands used:

- `python tools/frontier/data_inventory.py`
- read-only SQLite queries against
  `/home/yuke_zhang/alpha_data/alpha_system/registry/features.sqlite`
  and `labels.sqlite`

Observed registry lifecycle counts:

| Registry | REGISTERED | DEPRECATED |
| --- | ---: | ---: |
| Feature registry | 1384 | 928 |
| Label registry | 1404 | 1005 |

Observed materialized inventory:

- Data root: `/home/yuke_zhang/alpha_data/alpha_system`
- `values.parquet` partitions present: 2168
- Instruments: ES, NQ, RTY
- Years: 2019..2026
- Features: 838 on-disk partitions
- Labels: 1330 on-disk partitions
- 24 config-lock vs disk-presence disagreements are flagged by the inventory
  tool as `config_blocked_but_disk_present`; this is ambiguity to reconcile, not
  deletion authority.

## BBO / OHLCV Boundary

| Surface | Observed state | Allowed | Blocked | Reason |
| --- | --- | --- | --- | --- |
| BBO tradability features | REGISTERED BBO records exist for top-book fields; `bbo_tradability_spread_zscore` has both DEPRECATED and REGISTERED BBO records. | Same BBO `dataset_version_id` + same partition + REGISTERED lifecycle. | Stale DEPRECATED feature pins. | Runtime resolver rejects deprecated lifecycle and DatasetVersion mismatch. |
| Cost/spread labels on BBO | REGISTERED BBO labels exist only on `dsv_databento_bbo_8772e3b47aa5fb98` and `dsv_databento_bbo_f9e1d70a04d9dae4` (9 each per label family). | Same exact BBO `dataset_version_id` + partition + REGISTERED lifecycle. | Any BBO feature slice paired with OHLCV label pack. | Single-DatasetVersion invariant. |
| Cost/spread labels on OHLCV | REGISTERED OHLCV labels exist across 8 OHLCV DatasetVersions, 216 records per label family. | OHLCV feature/label slices on the same OHLCV DatasetVersion. | Auto-replacement from BBO stale label to OHLCV registered label. | Cross-DatasetVersion replacement changes provenance. |
| Deprecated BBO cost/spread labels | 478 DEPRECATED BBO `cost_adjusted_fwd_ret` and 478 DEPRECATED BBO `spread_adjusted_fwd_ret` records point to OHLCV replacements. | Surface replacement info to the author. | Auto-adopt replacement. | Replacement crosses BBO -> OHLCV; validate must fail loud. |

## Decisions

- A replacement candidate is advisory unless it preserves DatasetVersion,
  partition, label semantics, and provenance.
- Cross-DatasetVersion replacement is surfaced as
  `DATASET_VERSION_MISMATCH` / `DEPRECATED_PACK_PIN`, never silently applied.
- No new BBO labels were materialized in this sweep.
- No multi-dataset slice support was introduced.

## Next Safe Action

For any future BBO idea, author the feature and label pins on the same exact BBO
DatasetVersion and run `alpha idea validate` before gate/run. If a deprecated BBO
label only offers an OHLCV replacement, re-author the slice deliberately or
materialize a same-BBO registered label through a separate approved task.
