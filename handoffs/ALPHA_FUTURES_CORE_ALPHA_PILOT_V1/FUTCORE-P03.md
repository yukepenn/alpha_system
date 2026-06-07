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
live, paper, broker, order, account, deployment, provider acquisition, registry
write, destructive operation, PR, merge, or commit was performed.

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

## Input Pack Lock Summary

| Item | Locked reference |
| --- | --- |
| DatasetVersion | `dsv_databento_ohlcv_05404069799decb0` |
| Dataset source | `dsrc_databento_historical` |
| Universe | `ES`, `NQ`, `RTY` |
| Bar size / feed view | `1 min` / `TRADES` |
| FeaturePack refs | `fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f`, `fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978` |
| LabelPack refs | `lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395` |
| Partition | `development_partition` |
| Registry-reported storage | `dual`; the lock binds the Parquet pointer/hash/schema fields for research-scale use and treats JSONL as audit/smoke/small-tier only. |

The full lock records each pack's `value_store_format`, registry-reported
`parquet_path` reference string, `value_content_hash`, and
`value_schema_version`.

## Resolution Commands

```bash
test -f runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/STOP; printf '%s\n' "$?"
```

Result: exit code `0`; output `1`, so no active STOP file was present.

```bash
test -f /home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/datasets.sqlite; printf 'datasets_sqlite_test_status=%s\n' "$?"
test -f /home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/features.sqlite; printf 'features_sqlite_test_status=%s\n' "$?"
test -f /home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/labels.sqlite; printf 'labels_sqlite_test_status=%s\n' "$?"
```

Result: each command exited `0`; outputs were
`datasets_sqlite_test_status=0`, `features_sqlite_test_status=0`, and
`labels_sqlite_test_status=0`.

```bash
PYTHONPATH=src python - <<'PY'
import json
from alpha_system.data.foundation.version_registry import resolve_dataset_version
record = resolve_dataset_version(
    "/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/datasets.sqlite",
    "dsv_databento_ohlcv_05404069799decb0",
)
payload = record.to_mapping() if record is not None else {}
print(json.dumps({
    "resolved": record is not None,
    "dataset_version_id": payload.get("dataset_version_id"),
    "source": payload.get("source"),
    "symbol_universe": payload.get("symbol_universe"),
    "bar_size": payload.get("bar_size"),
    "what_to_show": payload.get("what_to_show"),
    "manifest_hash": payload.get("manifest_hash"),
    "code_hash": payload.get("code_hash"),
    "config_hash": payload.get("config_hash"),
    "quality_report_hash": payload.get("quality_report_hash"),
    "coverage_report_hash": payload.get("coverage_report_hash"),
    "created_at": payload.get("created_at"),
}, indent=2, sort_keys=True))
PY
```

Result: exit code `0`; `resolved=true`; id
`dsv_databento_ohlcv_05404069799decb0`; source
`dsrc_databento_historical`; symbols `ES`, `NQ`, `RTY`; bar size `1 min`;
what-to-show `TRADES`; manifest/config/code/quality hashes recorded in the lock.
The resolver returned `coverage_report_hash=null`, carried forward as a
`FUTCORE-P13` audit observation.

```bash
PYTHONPATH=src python -m alpha_system.cli.main feature list --registry-path /home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/features.sqlite --json
```

Result: exit code `0`; `record_count=2`; refs
`fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f` and
`fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978`.
Python emitted a `runpy` RuntimeWarning about `alpha_system.cli.main` already
being in `sys.modules`; the command still exited `0` and returned JSON.

```bash
PYTHONPATH=src python -m alpha_system.cli.main label list --registry-path /home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/labels.sqlite --json
```

Result: exit code `0`; `record_count=1`; ref
`lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395`.
Python emitted the same `runpy` RuntimeWarning; the command still exited `0` and
returned JSON.

```bash
PYTHONPATH=src python - <<'PY'
import json
from pathlib import Path
from alpha_system.cli.feature import _feature_records
from alpha_system.labels.registry import LabelRegistry
feature_records = _feature_records(Path("/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/features.sqlite"))
label_records = LabelRegistry("/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/labels.sqlite").read_label_records()
print(json.dumps({
    "feature_packs": [
        {
            "feature_id": r.feature_spec.feature_id,
            "feature_request_id": r.feature_request_id,
            "feature_version_id": r.feature_version_id,
            "feature_set_id": r.feature_set_id,
            "feature_set_version": r.feature_set_version,
            "dataset_version_id": r.dataset_version_id,
            "partition_id": r.partition_id,
            "materialization_plan_id": r.materialization_plan_id,
            "lifecycle_state": getattr(r.lifecycle_state, "value", str(r.lifecycle_state)),
            "value_store_format": r.value_store_format,
            "parquet_path": r.parquet_path,
            "value_content_hash": r.value_content_hash,
            "value_schema_version": r.value_schema_version,
        }
        for r in feature_records
    ],
    "label_packs": [
        {
            "label_id": r.label_id,
            "label_spec_id": r.label_spec_id,
            "label_version_id": r.label_version_id,
            "dataset_version_id": r.dataset_version_id,
            "partition_id": r.partition_id,
            "materialization_plan_id": r.materialization_plan_id,
            "lifecycle_state": getattr(r.lifecycle_state, "value", str(r.lifecycle_state)),
            "value_store_format": r.value_store_format,
            "parquet_path": r.parquet_path,
            "value_content_hash": r.value_content_hash,
            "value_schema_version": r.value_schema_version,
        }
        for r in label_records
    ],
}, indent=2, sort_keys=True))
PY
```

Result: exit code `0`; printed two feature pack records and one label pack
record. All three records had `value_store_format=dual`, non-empty
`parquet_path`, non-empty `value_content_hash`, and non-empty
`value_schema_version`.

```bash
PYTHONPATH=src python - <<'PY'
import json
from alpha_system.runtime.input_resolver import FeatureLabelPackResolver
resolver = FeatureLabelPackResolver(alpha_data_root="/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke")
feature_handles = resolver.resolve_feature_packs(
    [
        "fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f",
        "fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978",
    ],
    expected_dataset_version_id="dsv_databento_ohlcv_05404069799decb0",
    expected_feature_request_ids=["freq_67991722245329f35c0fa612", "freq_76147d2e3318292d48004696"],
    partition_id="development_partition",
)
label_handles = resolver.resolve_label_packs(
    ["lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395"],
    expected_dataset_version_id="dsv_databento_ohlcv_05404069799decb0",
    expected_label_spec_ids=["lspec_cd6523694c850c9943b2067e"],
    partition_id="development_partition",
)
print(json.dumps({
    "feature_handles": [h.to_dict() for h in feature_handles],
    "label_handles": [h.to_dict() for h in label_handles],
}, indent=2, sort_keys=True))
PY
```

Result: exit code `0`; both FeaturePack handles and the LabelPack handle
resolved through the runtime resolver with matching DatasetVersion and
`development_partition`.

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

## Carried-Forward Observations

- Registry records report `value_store_format=dual`; `FUTCORE-P13` should audit
  that research-scale scans consume the Parquet side only and do not use JSONL.
- The feature set id is `fset_es_session_ctx_smoke`; `FUTCORE-P13` should audit
  ES/NQ/RTY symbol-level coverage before downstream StudySpecs rely on these
  refs beyond their registry binding.
- The locked records are for `development_partition`. Validation, locked, and
  shadow partition pack availability must be audited before use.
- Only the `fwd_ret_5m` label is locked here. Other P02 primary/extended
  horizons remain later FeatureRequest/LabelSpec or audit work; no gap was
  filled in this phase.

## Executor Safety Exceptions / Ownership Notes

- `git status --short` was skipped by explicit user instruction.
- No staged-set inspection was performed because the executor was instructed not
  to run `git diff`; the executor staged nothing.
- Yellow-lane review artifacts were not created by the executor. Ralph owns
  reviewer invocation and any commit-eligible review promotion.
- No run-local `handoff.md`, `review.md`, or `verdict.json` was written.

## Artifact Confirmation

- `git ls-files runs` returned empty.
- Tracked heavy-artifact globs for `*.parquet` and `*.sqlite` returned empty.
- No raw/canonical data, feature values, label values, Parquet, SQLite, provider
  responses, logs, caches, secrets, credentials, or local DB artifacts were
  written or committed by this executor.
