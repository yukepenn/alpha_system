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

The complete 408-row provenance table is the value-free Markdown table
`research/futures_substrate_scaleout_v1/repair/damaged_pack_provenance.md`.

## Proof Partition

Proof partition: `ES_2019_full_year`.

| Family | Baseline stale fvers | Proof result | Baseline hash identity |
| --- | ---: | --- | ---: |
| `session_calendar_maintenance` | 5 | Not executed. The union config dry-run fails closed because current scaleout rejects `bars_to_roll` and `minutes_to_roll` as offline/non-causal. | 0 |
| `regime_volatility_compression` | 2 | Not executed. The current union config preview does not target either stale baseline fver; executing would create non-restoring fvers. | 0 |
| `bbo_tradability_top_book` | 10 | Executed with the sanctioned scaleout CLI. All 10 baseline stale fvers are now present on disk, but the pack hash is new by design. | 0 |

Proof results are in the value-free Markdown table
`research/futures_substrate_scaleout_v1/repair/ES_2019_proof_results.md`.

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

## Required Execution Order

1. Deprecate unrestorable `REGISTERED` fvers before session/regime
   re-materialization.
2. Run full BBO re-materialization only after the executing branch contains
   the P085901 bar-grid fix from PR #401, which is now merged on `origin/main`.
3. Run verification and then re-lock affected StudySpecs.

The BBO ES_2019 proof in this phase was written before PR #401. It is proof of
the sanctioned CLI path and blast radius only; it is superseded by the full BBO
re-materialization after the grid fix. The post-PR-401 BBO run is the content
that must feed the `sspec_6088f0` re-lock.

## Deprecate-First Step

Before any session/regime full-grid re-materialization, deprecate the
unrestorable active rows through the sanctioned FeatureStore/FeatureRegistry
API. Do not edit SQLite manually. This follows the mechanism used by the
P235500 coordinator data-op: `FeatureStore.deprecate_feature(...)` delegates to
`FeatureRegistry.deprecate_feature(...)`, which updates `lifecycle_state` and
writes a `feature_deprecation_records` row. The live P235500 evidence records
496 rows with `deprecated_by=coordinator/P235500_data_op`, reason
`P235500 session-reset truth repoint (PR #376): ...`, and metadata backup
`registry/backups/session_reset_repair_20260612T002901Z`.

Deprecate exactly these `168` rows before proceeding:

| Cause | Feature ids | Partitions | Rows | Replacement pointer |
| --- | --- | ---: | ---: | --- |
| R-036 offline/non-causal countdowns | `session_calendar_roll_bars_to_roll`, `session_calendar_roll_minutes_to_roll` | 24 | 48 | none unless a reviewed successor exists |
| Session template identity migration from commit `6018f1a` | `session_calendar_roll_day_of_week`, `session_calendar_roll_minutes_to_expiration`, `session_calendar_roll_halt_status_flag` | 24 | 72 | current dry-run replacement fver for the same feature/partition |
| Session template identity migration from commit `6018f1a` | `base_ohlcv_returns`, `base_ohlcv_rolling_range` inside `regime_volatility_compression` packs | 24 | 48 | current dry-run replacement fver for the same feature/partition |

Prepare a reviewed mapping file outside git, for example
`/tmp/p094500_deprecate_first_pairs.json`, with one object per old fver:

```json
[
  {
    "deprecated_feature_version_id": "fver_old_registered_id",
    "replacement_feature_version_id": "fver_new_preview_or_registered_id",
    "feature_id": "session_calendar_roll_day_of_week",
    "partition_id": "ES_2019_full_year",
    "cause": "6018f1a transform.parameters session-template identity migration"
  },
  {
    "deprecated_feature_version_id": "fver_old_registered_countdown_id",
    "replacement_feature_version_id": "",
    "feature_id": "session_calendar_roll_minutes_to_roll",
    "partition_id": "ES_2019_full_year",
    "cause": "R-036 offline/non-causal countdown"
  }
]
```

Create the registry backup before the transition:

```bash
export ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system
TS=$(date -u +%Y%m%dT%H%M%SZ)
export BACKUP_NAME="pack_restore_deprecate_first_${TS}"
mkdir -p "$ALPHA_DATA_ROOT/registry/backups/$BACKUP_NAME"
cp "$ALPHA_DATA_ROOT/registry/features.sqlite" \
  "$ALPHA_DATA_ROOT/registry/backups/$BACKUP_NAME/features.sqlite"
```

Run the sanctioned deprecation API in the same shell so `BACKUP_NAME` is
available in deprecation metadata. This is the write step; it must be run only
by the coordinator/operator with the reviewed mapping:

```bash
ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system \
PYTHONPATH=src \
~/.venvs/alpha_system_research/bin/python - <<'PY'
import json
import os
from pathlib import Path

from alpha_system.features.registry import FeatureRegistry
from alpha_system.features.store import FeatureStore

alpha_data_root = Path(os.environ["ALPHA_DATA_ROOT"])
backup_name = os.environ["BACKUP_NAME"]
pairs_path = Path("/tmp/p094500_deprecate_first_pairs.json")
registry_path = alpha_data_root / "registry" / "features.sqlite"

store = FeatureStore(FeatureRegistry(registry_path))
pairs = json.loads(pairs_path.read_text(encoding="utf-8"))
reason = (
    "P094500 damaged-pack restore deprecate-first: unrestorable REGISTERED "
    "fvers superseded before guarded session/regime re-materialization"
)
for item in pairs:
    store.deprecate_feature(
        item["deprecated_feature_version_id"],
        reason=reason,
        deprecated_by="coordinator/P094500_deprecate_first",
        replacement_feature_version_id=item.get("replacement_feature_version_id", ""),
        deprecation_metadata={
            "backup": f"registry/backups/{backup_name}",
            "spec": "specs/FUTSUB_KILLSHOT_READINESS_OPS_V1/P094500_DAMAGED_PACK_RESTORE_PLAN-provenance-union-runbook.md",
            "review": "reviews/FUTSUB_KILLSHOT_READINESS_OPS_V1/P094500_DAMAGED_PACK_RESTORE_PLAN-review.md",
            "cause": item.get("cause", ""),
            "feature_id": item.get("feature_id", ""),
            "partition_id": item.get("partition_id", ""),
            "identity_migration_commit": "6018f1a",
        },
    )
print(f"deprecated={len(pairs)}")
PY
```

Verify through the registry API, not manual SQLite:

```bash
ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system \
PYTHONPATH=src \
~/.venvs/alpha_system_research/bin/python - <<'PY'
import json
import os
from pathlib import Path

from alpha_system.features.registry import FeatureRegistry, FeatureRegistryLifecycleState

alpha_data_root = Path(os.environ["ALPHA_DATA_ROOT"])
pairs = json.loads(Path("/tmp/p094500_deprecate_first_pairs.json").read_text(encoding="utf-8"))
registry = FeatureRegistry(alpha_data_root / "registry" / "features.sqlite")
for item in pairs:
    fver = item["deprecated_feature_version_id"]
    record = registry.resolve_feature(fver, include_deprecated=True)
    deprecation = registry.resolve_deprecation(fver)
    assert record is not None, f"missing deprecated record: {fver}"
    assert record.lifecycle_state is FeatureRegistryLifecycleState.DEPRECATED, fver
    assert deprecation is not None, f"missing deprecation row: {fver}"
    expected_replacement = item.get("replacement_feature_version_id", "")
    assert deprecation.replacement_feature_version_id == expected_replacement, fver
print(f"verified_deprecated={len(pairs)}")
PY
```

## Verification

Pre/post audit command:

```bash
PYTHONPATH=src \
~/.venvs/alpha_system_research/bin/python tools/futures_substrate_scaleout/pack_restore_audit.py \
  --alpha-data-root /home/yuke_zhang/alpha_data/alpha_system \
  --baseline-provenance research/futures_substrate_scaleout_v1/repair/damaged_pack_provenance.md \
  --proof-out research/futures_substrate_scaleout_v1/repair/full_grid_proof_results.md \
  --summary-out research/futures_substrate_scaleout_v1/repair/damaged_pack_post_restore_audit.md
```

For the ES_2019 proof partition only:

```bash
PYTHONPATH=src \
~/.venvs/alpha_system_research/bin/python tools/futures_substrate_scaleout/pack_restore_audit.py \
  --alpha-data-root /home/yuke_zhang/alpha_data/alpha_system \
  --partition ES_2019_full_year \
  --baseline-provenance research/futures_substrate_scaleout_v1/repair/damaged_pack_provenance.md \
  --proof-out research/futures_substrate_scaleout_v1/repair/ES_2019_proof_results.md \
  --summary-out research/futures_substrate_scaleout_v1/repair/ES_2019_post_proof_audit.md
```

## Full-Grid Commands

Do not run the session or regime full-grid commands until their blockers below
are repaired. They are included as exact command templates for the coordinator
after those blockers are cleared.

### BBO Tradability Top Book

BBO restore should be treated as a new-content repair. Run the full-grid command
only after the executing branch contains the P085901 bar-grid fix from PR #401
(now merged on `origin/main`). The pre-PR-401 ES_2019 proof wrote pack hash
`sha256:fd92da6790af4d95cea1f649e5f90164982c87a4eb409b1cbb313d923440645d`;
the baseline stale BBO rows expected
`sha256:da3ae4b38572266ff0f71f52945d05e3faecdd3d9951000e91a1bba91e99bbf0`.
That proof content is superseded by the post-grid-fix full BBO run. The
`sspec_6088f0` family must be re-locked after BBO full-grid execution.

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
