# Handoff - FUTCORE-P03

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P03` - Data / Feature / Label Input Pack Lock  
Executor: Codex  
Date: 2026-06-07

## Executor Status

Execution artifacts are written and left unstaged in the working tree. This
handoff does not mark the phase PASS; Ralph owns validation orchestration,
review, staging, commit, PR, CI, merge, and done-check.

No source primitive under `src/alpha_system/**` was edited. No tests were added
or modified. No review artifact, `review.md`, or `verdict.json` was created. No
live, paper, broker, order, account, deployment, provider acquisition,
destructive operation, PR, merge, staging, commit, or push was performed.

## Files Written Or Updated

- `research/futures_core_alpha_pilot_v1/input_pack/input_pack_lock.md`
- `docs/futures_core_alpha_pilot/INPUT_PACK.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P03.md`

## Explicit Commit-Eligible File List For Ralph

The executor staged nothing. Ralph should stage only these paths explicitly,
subject to its authoritative artifact and staged-set checks:

- `research/futures_core_alpha_pilot_v1/input_pack/input_pack_lock.md`
- `docs/futures_core_alpha_pilot/INPUT_PACK.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P03.md`

No `runs/**` path should be staged.

## Locked DatasetVersion

| Field | Locked reference |
| --- | --- |
| DatasetVersion id | `dsv_databento_ohlcv_05404069799decb0` |
| Source | `dsrc_databento_historical` |
| Universe | `ES`, `NQ`, `RTY` |
| Bar size / feed view | `1 min` / `TRADES` |
| Manifest hash | `abbf9ebbecfe97f2c4b31900d9ae44421549e08a65e90ec64e235a958c1d2d31` |
| Code hash | `87fb8de7760c3635fb883948971bc12ee21ed64562713975bb20028ae3f92139` |
| Config hash | `206bc27869bcedfde89e483828534c5778bb72cf7e66b69a9d3304c7e7f03b5b` |
| Quality report hash | `7e46966bdc6921a0bb338097fa82ec94fcdf401e1913d81b288052bd6c9c66b4` |

## Locked FeaturePacks

All locked FeaturePack records bind to DatasetVersion
`dsv_databento_ohlcv_05404069799decb0`, partition
`development_partition`, `value_store_format=dual`, and
`value_schema_version=alpha_system.features.materialization.v1`.

| Feature id | FeatureVersion id | `value_content_hash` |
| --- | --- | --- |
| `base_ohlcv_log_returns` | `fver_7ac2429f12ce6f7d494b7c0ab968446f2455da51863ebe471ddd8a224b6fa9f9` | `sha256:5958b475409b9275c5982935de6d3487d2c01fe6845f31eee5781b3f1f0d812a` |
| `base_ohlcv_range_position` | `fver_862f9b2d36e10b58d362afffe69c72cfc4231e562d96e1cb923aca649c1b2f5d` | `sha256:7056759e0577f5a3f57426944f48602bf6f5589d7d79597270e7db543aa8dc73` |
| `base_ohlcv_returns` | `fver_a6390d478bc31576bce270eadb93f8adfe215833ab403aba2e69af53e120eb8a` | `sha256:0a8d29b9284d85e5306d76e0482ce6925c8384e9bb28247dc9564be02360ed90` |
| `base_ohlcv_rolling_range` | `fver_74ba4d642ce7b24dbdc06bc5bd16ce9c05bae3def8052056c439b3b6cdbc9169` | `sha256:c9e133ed324b2b2ea168fa2b2672e99050161c91e34ea919f82eae2be2f96077` |
| `base_ohlcv_rolling_volatility` | `fver_18b5841a0d7f2fd7b86e5d650a21742190c1517dacc40dbb90854a1188191147` | `sha256:1ad59e668cbed859460cb3dc672293cfc03f55d600d185477b46cfe1e9c1ec67` |
| `base_ohlcv_rth_flag` | `fver_acbfa7833cb2a07338a91abe750c934d9e9922477ad96e3ea3e0c001970573f9` | `sha256:29a64bad4966f696b1c18e72432ef2e5e00fff9ed767b6cd968493a7d4a6fa79` |
| `base_ohlcv_session_minute` | `fver_fd739ad918a557d2f4ca45d54c9ea700cc0168ad9c6fec90151d87479bf1b858` | `sha256:94430bbd52270daf8a7e043c9a0e1c45b98e1f84b0f9ff0439d7119ddb3ef0ad` |
| `base_ohlcv_volume_zscore` | `fver_759ee1b9da77fefb78aa5440b3de66dd217922ac576241858960cf1e8cef8a91` | `sha256:5c4ff7e2cbcbe4165a25c654d01466937c74b52560a53193f9c422256c84bbdf` |

Each record also carries a registry-reported `parquet_path` pointer in
`input_pack_lock.md`; no Parquet file was opened or committed.

## Locked LabelPacks

All locked LabelPack records bind to DatasetVersion
`dsv_databento_ohlcv_05404069799decb0`, partition
`development_partition`, `value_store_format=dual`, and
`value_schema_version=alpha_system.labels.materialization.v1`.

| Label id | LabelVersion id | `value_content_hash` |
| --- | --- | --- |
| `fwd_ret_5m` | `lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395` | `sha256:abb5f53c7ede5f359a79541b237d71d44e79304ebbb6333a101a3c0588e32a9f` |
| `fwd_ret_10m` | `lver_4170332f366d6945a37cfe8980395626c393b40c2e1c36944ffb784b88cc7941` | `sha256:d691193911a2f72a821da02846dbc3bab377ad810b67b0761de72b83bbac1489` |
| `fwd_ret_30m` | `lver_69c9900cbac5e679f8d97d350e30f493f30a498eb3d47463e6ab9995f1c0310a` | `sha256:d691193911a2f72a821da02846dbc3bab377ad810b67b0761de72b83bbac1489` |

Each record also carries a registry-reported `parquet_path` pointer in
`input_pack_lock.md`; no Parquet file was opened or committed.

## Coverage And Gap Notes For P13/P14

- Universe: the DatasetVersion resolves with symbol universe `ES`, `NQ`, `RTY`.
  FeaturePack and LabelPack records bind to that DatasetVersion and
  `development_partition`; symbol-level value coverage is not inspected here.
- `available_ts`: present for all eight locked FeaturePack records.
- `label_available_ts`: present for all three locked LabelPack records.
- Session provenance: locked session features expose `session_label` with role
  `SESSION_METADATA`. This is the registry naming used for session-segment
  provenance in the locked pack metadata.
- `exchange_trade_date`: not exposed as a named FeaturePack or LabelPack input
  field in the locked registry contracts. P13/P14 must confirm any required
  exchange-trade-date binding before diagnostics rely on it.
- Quality and missingness flags: `quality_flags` is present in every locked
  FeaturePack and LabelPack input contract; gap semantics are recorded through
  input metadata, not through a separate materialized missingness summary.
- Primary label horizons: `5m`, `10m`, and `30m` resolve. `15m` does not
  resolve in the locked LabelPack set and must be routed around or planned for
  by later authorized work.

## Resolution Commands

Run directory / STOP check:

```bash
find runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1 -maxdepth 1 -name STOP -print
```

Result: exit code `1`; the prompt-provided run directory was not present in
this worktree, so no STOP file existed at that path. No run-local file was
created.

DatasetVersion scalar resolution:

```bash
PYTHONPATH=src python - <<'PY'
from alpha_system.data.foundation.version_registry import resolve_dataset_version
record = resolve_dataset_version('/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/datasets.sqlite','dsv_databento_ohlcv_05404069799decb0')
payload = record.to_mapping()
for key in sorted(payload):
    print(f'{key}={payload[key]!r}')
PY
```

Result: exit code `0`; resolved the DatasetVersion and printed the scalar
fields recorded in the lock.

FeaturePack list:

```bash
PYTHONPATH=src python -m alpha_system.cli.main feature list --registry-path /home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/features.sqlite --json
```

Result: exit code `0`; `record_count=8`. Python emitted a `runpy`
RuntimeWarning about `alpha_system.cli.main` already being in `sys.modules`; the
command still returned JSON and exited `0`.

LabelPack list:

```bash
PYTHONPATH=src python -m alpha_system.cli.main label list --registry-path /home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/labels.sqlite --json
```

Result: exit code `0`; `record_count=3`. Python emitted the same `runpy`
RuntimeWarning; the command still returned JSON and exited `0`.

Metadata and explicit-facade runtime handle resolution:

```bash
PYTHONPATH=src python - <<'PY'
from pathlib import Path
from alpha_system.cli.feature import _feature_records
from alpha_system.labels.registry import LabelRegistry
from alpha_system.features.registry import FeatureRegistry
from alpha_system.features.store import FeatureStore
from alpha_system.runtime.input_resolver import FeatureLabelPackResolver

feature_registry = Path('/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/features.sqlite')
label_registry = '/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/labels.sqlite'
features = _feature_records(feature_registry)
labels = LabelRegistry(label_registry).read_label_records()
resolver = FeatureLabelPackResolver(
    feature_store=FeatureStore(FeatureRegistry(feature_registry)),
    label_registry=LabelRegistry(label_registry),
)
feature_handles = resolver.resolve_feature_packs(
    [r.feature_version_id for r in features],
    expected_dataset_version_id='dsv_databento_ohlcv_05404069799decb0',
    expected_feature_request_ids=[r.feature_request_id for r in features],
    partition_id='development_partition',
)
label_handles = resolver.resolve_label_packs(
    [r.label_version_id for r in labels],
    expected_dataset_version_id='dsv_databento_ohlcv_05404069799decb0',
    expected_label_spec_ids=[r.label_spec_id for r in labels],
    partition_id='development_partition',
)
print(len(feature_handles), len(label_handles))
PY
```

Result: exit code `0`; output `8 3`.

Exploratory failure recorded for transparency: an earlier runtime resolver call
using `FeatureLabelPackResolver(alpha_data_root='/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke')`
with stale FeatureVersion ids from the pre-existing lock exited `1` with
`RuntimeInputResolverError: FeatureStore did not resolve the requested feature
pack`. The lock was corrected by re-listing the current registry refs and using
the explicit local registry facades above.

## Validation Commands

`git status --short` was not run because the executor instructions explicitly
forbid `git status`.

```bash
python tools/verify.py --smoke
```

Result: exit code `0`.

```bash
test -f research/futures_core_alpha_pilot_v1/input_pack/input_pack_lock.md
```

Result: exit code `0`.

```bash
test -f docs/futures_core_alpha_pilot/INPUT_PACK.md
```

Result: exit code `0`.

```bash
test -f handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P03.md
```

Result: exit code `0`.

```bash
git ls-files runs
```

Result: exit code `0`; empty output.

```bash
git ls-files '**/*.parquet' '**/*.sqlite'
```

Result: exit code `0`; empty output.

## Executor Safety Exceptions / Ownership Notes

- `git status --short` was skipped by explicit user instruction.
- No staged-set inspection was performed because the executor was instructed not
  to run `git diff`; the executor staged nothing.
- The prompt-provided run-local phase directory
  `runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/phases/FUTCORE-P03`
  was not present during execution. No run-local file was written.
- Yellow-lane review artifacts were not created by the executor. Ralph owns
  reviewer invocation and any commit-eligible review promotion.

## Artifact Confirmation

- `git ls-files runs` returned empty.
- Tracked heavy-artifact globs for `*.parquet` and `*.sqlite` returned empty.
- No `runs/**` file was written by this executor.
- No raw/canonical data, feature values, label values, Parquet, SQLite, provider
  responses, logs, caches, secrets, credentials, or local DB artifacts were
  written or committed by this executor.
