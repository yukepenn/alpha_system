# LCFP-P06 Integration Report

Value-free report for worker / checkpoint / registry / resolver integration.
No label values, raw rows, provider payloads, SQLite contents, or Parquet
payloads are included.

## Scope

- Fast label selection: `fixed_horizon` diagnostic group, built-in `base`
  horizon group.
- Selected bounded-real slice: `ES`, year `2024`,
  DatasetVersion `dsv_databento_ohlcv_05404069799decb0`.
- Selected units: `2` (`fwd_ret_1m`, `fwd_ret_3m`).
- Requested workers: `2`; effective workers on execute: `2`; threads per worker:
  `8`.
- Registry writer: single parent-process serial writer through
  `LabelRegistry.register_materialized_label` via `FastLabelMaterializer.register_pack`.

## Registry Backup

- Main label registry backup before registry-touching attempts:
  `/home/yuke_zhang/alpha_data/alpha_system/registry/labels.sqlite.bak_lcfp_20260610T132806Z`
- Main registry first attempt failed closed before registering fast rows:
  `existing registry record has a mismatched lineage`.
- Interpretation: the selected strict identities already existed in the main
  label registry with reference-engine lineage. The fast path refused to silently
  mix engines for those identities. Existing reference outputs were preserved.

## Isolated Bounded-Real Smoke

To prove end-to-end fast registration without mutating existing reference rows,
the bounded-real smoke used an isolated local-only data root:

`/home/yuke_zhang/alpha_data/alpha_system/lcfp_p06_smoke_20260610T133001Z`

The run read the real canonical root and dataset registry, but wrote label values,
worker manifests, checkpoints, and the label registry only under that smoke root.

## Dry-Run Evidence

Command:

```bash
PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m alpha_system.cli.main scaleout label-pack --config configs/labels/scaleout/fixed_horizon.json --dry-run --rollout bounded-real --bounded-year 2024 --label-group diagnostic --horizon-group base --symbols ES --years 2024 --dataset-version-ids dsv_databento_ohlcv_05404069799decb0 --workers 2 --json
```

Result:

- `dry_run`: `true`
- planned units: `2`
- estimated rows per unit: `550000`
- estimated total rows: `1100000`
- write evidence: planned records had no Parquet path and no content hash.
- previewed label versions: `2`

## Execute Evidence

Command:

```bash
ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system/lcfp_p06_smoke_20260610T133001Z PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m alpha_system.cli.main scaleout label-pack --config configs/labels/scaleout/fixed_horizon.json --execute --rollout bounded-real --bounded-year 2024 --label-group diagnostic --horizon-group base --symbols ES --years 2024 --dataset-version-ids dsv_databento_ohlcv_05404069799decb0 --workers 2 --alpha-data-root /home/yuke_zhang/alpha_data/alpha_system/lcfp_p06_smoke_20260610T133001Z --dataset-registry /home/yuke_zhang/alpha_data/alpha_system/registry/datasets.sqlite --canonical-root /home/yuke_zhang/alpha_data/alpha_system/databento/canonical/glbx_mdp3 --json
```

Result:

- accepted units: `2`
- completed units: `2`
- failed units: `0`
- skipped units: `0`
- output files written under local-only smoke root: `2` Parquet value files plus
  deterministic sidecar manifests and worker manifests.
- registry row delta in smoke registry: `+2`
- row counts recorded by registry/materialization metadata:
  `340876` (`fwd_ret_1m`) and `340368` (`fwd_ret_3m`).
- producer provenance recorded:
  `alpha_system.labels.fast.pack_materializer.v1`
- value schema version recorded:
  `alpha_system.labels.fast.values.v1`

## Checkpoint / Skip / Force Evidence

Restart command: same execute command as above, without `--force`.

Result:

- completed units: `0`
- skipped units: `2`
- skip reason: `completed unit skipped from checkpoint + registry truth`

Force command: same execute command with `--force`.

Result:

- `force_recompute`: `true`
- completed units: `2`
- skipped units: `0`
- label version identities and content hashes remained stable.

## Resolver Smoke

Command:

```bash
ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system/lcfp_p06_smoke_20260610T133001Z PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python - <<'PY'
from alpha_system.labels.registry import LabelRegistry
from alpha_system.labels.fast import FAST_LABEL_PRODUCER_ENGINE_ID, FAST_LABEL_VALUE_SCHEMA_VERSION
root = "/home/yuke_zhang/alpha_data/alpha_system/lcfp_p06_smoke_20260610T133001Z"
ids = (
    "lver_663227cc9655c6515c7f2f88417687504cb492f4cad463e2183541dc969266f5",
    "lver_f38e2e11ef95c5039045081e3c7a37e5b817a630697f39e0313c5cfd3961fef4",
)
registry = LabelRegistry.from_alpha_data_root(root)
for label_version_id in ids:
    record = registry.resolve_label_by_version(label_version_id)
    assert record is not None
    assert record.label_version_id == label_version_id
    assert record.producer_engine_id == FAST_LABEL_PRODUCER_ENGINE_ID
    assert record.value_schema_version == FAST_LABEL_VALUE_SCHEMA_VERSION
    assert record.value_store_format == "parquet"
    assert record.value_record_count > 0
assert registry.resolve_label_by_version("lver_" + "0" * 64) is None
print({"resolved_count": len(ids), "fail_closed_missing_id": True, "producer_engine_id": FAST_LABEL_PRODUCER_ENGINE_ID})
PY
```

Result:

- strict identity resolves: `2/2`
- missing strict identity fails closed: `true`
- resolved producer engine: `alpha_system.labels.fast.pack_materializer.v1`

## Status

- `code_status`: implemented
- `execute_status`: bounded-real smoke passed in isolated local-only data root;
  main registry attempt failed closed on reference-lineage conflict as intended.
- `registry_status`: serial writer path passed; main reference-engine rows were
  preserved; no manual SQLite writes.
- `artifact_status`: value-free report only; values, manifests, checkpoints, and
  SQLite files remain under `$ALPHA_DATA_ROOT`.
