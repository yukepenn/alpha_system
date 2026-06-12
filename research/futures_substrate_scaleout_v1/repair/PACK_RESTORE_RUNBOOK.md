# Damaged FeaturePack Restore Runbook

Campaign: `FUTSUB_KILLSHOT_READINESS_OPS_V1`
Phase: `P094500_DAMAGED_PACK_RESTORE_PLAN`
Data root: `/home/yuke_zhang/alpha_data/alpha_system`

This runbook is value-free. It records registry ids, content hashes, counts, and
commands only.

## Current Finding

The active registry-vs-disk stale set is 408 `REGISTERED` FeatureVersion rows:

| Family | Active rows | Disk-present/hash-identical | Stale |
| --- | ---: | ---: | ---: |
| `session_calendar_maintenance` | 240 | 120 | 120 |
| `regime_volatility_compression` | 120 | 72 | 48 |
| `bbo_tradability_top_book` | 264 | 24 | 240 |

The complete 408-row provenance table is
`research/futures_substrate_scaleout_v1/repair/damaged_pack_provenance.csv`.

## Proof Partition

Proof partition: `ES_2019_full_year`.

| Family | Baseline stale fvers | Proof result | Baseline hash identity |
| --- | ---: | --- | ---: |
| `session_calendar_maintenance` | 5 | Not executed. The union config dry-run fails closed because current scaleout rejects `bars_to_roll` and `minutes_to_roll` as offline/non-causal. | 0 |
| `regime_volatility_compression` | 2 | Not executed. The current union config preview does not target either stale baseline fver; executing would create non-restoring fvers. | 0 |
| `bbo_tradability_top_book` | 10 | Executed with the sanctioned scaleout CLI. All 10 baseline stale fvers are now present on disk, but the pack hash is new by design. | 0 |

Proof results are in
`research/futures_substrate_scaleout_v1/repair/ES_2019_proof_results.csv`.

BBO proof command:

```bash
ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system \
PYTHONPATH=src \
~/.venvs/alpha_system_research/bin/python -m alpha_system.cli scaleout feature-pack \
  --config configs/features/scaleout/repair/bbo_tradability_top_book_union_restore.json \
  --rollout full-window \
  --execute \
  --force-recompute \
  --symbols ES \
  --years 2019 \
  --alpha-data-root "$ALPHA_DATA_ROOT" \
  --dataset-registry "$ALPHA_DATA_ROOT/registry/datasets.sqlite" \
  --json
```

Measured BBO ES_2019 duration: `97.64` seconds. Full BBO grid estimate:
approximately `39.1` minutes for 24 serial partitions, before operator
overhead.

## Verification

Pre/post audit command:

```bash
PYTHONPATH=src \
~/.venvs/alpha_system_research/bin/python tools/futures_substrate_scaleout/pack_restore_audit.py \
  --alpha-data-root /home/yuke_zhang/alpha_data/alpha_system \
  --baseline-provenance research/futures_substrate_scaleout_v1/repair/damaged_pack_provenance.csv \
  --proof-out research/futures_substrate_scaleout_v1/repair/full_grid_proof_results.csv \
  --summary-out research/futures_substrate_scaleout_v1/repair/damaged_pack_post_restore_audit.md
```

For the ES_2019 proof partition only:

```bash
PYTHONPATH=src \
~/.venvs/alpha_system_research/bin/python tools/futures_substrate_scaleout/pack_restore_audit.py \
  --alpha-data-root /home/yuke_zhang/alpha_data/alpha_system \
  --partition ES_2019_full_year \
  --baseline-provenance research/futures_substrate_scaleout_v1/repair/damaged_pack_provenance.csv \
  --proof-out research/futures_substrate_scaleout_v1/repair/ES_2019_proof_results.csv \
  --summary-out research/futures_substrate_scaleout_v1/repair/ES_2019_post_proof_audit.md
```

## Full-Grid Commands

Do not run the session or regime full-grid commands until their blockers below
are repaired. They are included as exact command templates for the coordinator
after those blockers are cleared.

### BBO Tradability Top Book

BBO restore should be treated as a new-content repair. The ES_2019 proof wrote
pack hash `sha256:fd92da6790af4d95cea1f649e5f90164982c87a4eb409b1cbb313d923440645d`;
the baseline stale BBO rows expected
`sha256:da3ae4b38572266ff0f71f52945d05e3faecdd3d9951000e91a1bba91e99bbf0`.
The `sspec_6088f0` family must be re-locked after BBO full-grid execution.

```bash
ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system \
PYTHONPATH=src \
~/.venvs/alpha_system_research/bin/python -m alpha_system.cli scaleout feature-pack \
  --config configs/features/scaleout/repair/bbo_tradability_top_book_union_restore.json \
  --rollout full-window \
  --execute \
  --force-recompute \
  --alpha-data-root "$ALPHA_DATA_ROOT" \
  --dataset-registry "$ALPHA_DATA_ROOT/registry/datasets.sqlite" \
  --json
```

Expected duration: about `39.1` minutes serial for 24 partitions, based on the
ES_2019 proof.

### Regime Volatility Compression

Blocked. Current dry-run preview for ES_2019 emits these two replacement fvers
for the stale slots:

- `range_expansion` / `base_ohlcv_rolling_range`: current preview
  `fver_8eadbbf78450fc563380dad80469abc3cff4cc5446c0d022cdc8129cb0c96cea`;
  baseline stale fver
  `fver_082cbb1b6cf5bfdfebd744c7e1959cf93a1984bdadaee05e746bac591fcc8160`.
- `momentum_reversion_state` / `base_ohlcv_returns`: current preview
  `fver_33907b24924fe90263dad2c42de580d41c920b9bfaa1bda7f2cad45792d17a9f`;
  baseline stale fver
  `fver_01471d627567885984a20a18a7291e2cbeaf5e6f525cfd76cfe5d89b496b3533`.

Do not run this until the stale fvers are again the dry-run preview target or a
reviewed migration/re-lock plan replaces them.

```bash
ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system \
PYTHONPATH=src \
~/.venvs/alpha_system_research/bin/python -m alpha_system.cli scaleout feature-pack \
  --config configs/features/scaleout/repair/regime_volatility_compression_union_restore.json \
  --rollout full-window \
  --execute \
  --force-recompute \
  --alpha-data-root "$ALPHA_DATA_ROOT" \
  --dataset-registry "$ALPHA_DATA_ROOT/registry/datasets.sqlite" \
  --json
```

Expected duration: not measured because execute is intentionally blocked by
identity drift.

### Session Calendar Maintenance

Blocked. The 10-name union config fails dry-run with:
`session_calendar_maintenance scaleout excludes offline/non-causal features:
bars_to_roll, minutes_to_roll`.

The current 8-name committed config also does not target the three stale
non-countdown ES_2019 fvers (`day_of_week`, `minutes_to_expiration`,
`halt_status_flag`); it previews replacement fvers instead. Do not run a full
grid until the offline-countdown and identity-drift decisions are reviewed.

```bash
ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system \
PYTHONPATH=src \
~/.venvs/alpha_system_research/bin/python -m alpha_system.cli scaleout feature-pack \
  --config configs/features/scaleout/repair/session_calendar_maintenance_union_restore.json \
  --rollout full-window \
  --execute \
  --force-recompute \
  --alpha-data-root "$ALPHA_DATA_ROOT" \
  --dataset-registry "$ALPHA_DATA_ROOT/registry/datasets.sqlite" \
  --json
```

Expected duration: not measured because execute is blocked by the current
offline-feature guard and identity drift.
