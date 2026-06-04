# ADF1 Databento ES/NQ/RTY OHLCV+BBO Deep History Handoff

Status: **SCAFFOLD_READY_FOR_PHASE_B_PLACEHOLDERS**. Run 3b implemented the
offline metadata ingest, cross-source diagnostic comparison, docs, tests, and
this handoff scaffold. Live Databento submission, download, canonicalization,
registration, and report values remain operator-supervised Phase B work.

## Dependency And Environment Status

- Databento SDK dependency: PLACEHOLDER after operator install.
- DBN reader dependency: PLACEHOLDER after operator install.
- Optional pandas/pyarrow availability: PLACEHOLDER after operator install.
- `ALPHA_DATA_ROOT`: PLACEHOLDER, must resolve outside the repository.
- Databento credential status: env-only; no secret value belongs in this file.
- CI posture: Databento live flow must not run in CI.

## Dataset Scope

- Dataset: `GLBX.MDP3`.
- Symbols: `ES.v.0`, `NQ.v.0`, `RTY.v.0`.
- `stype_in`: `continuous`.
- Schemas: `ohlcv-1m`, `bbo-1m`, `definition`, `statistics`, `status`.
- Start: PLACEHOLDER.
- End: PLACEHOLDER.
- Continuous provenance: provider continuous front-month, unadjusted,
  `not_roll_truth`.

## Cost And Jobs

- Cost by schema: PLACEHOLDER.
- Total cost: PLACEHOLDER, must be at or below the `$110` hard cap before paid
  submit.
- Cost manifest path: PLACEHOLDER.
- Cost manifest hash: PLACEHOLDER.
- Job IDs by schema: PLACEHOLDER.
- Jobs manifest path: PLACEHOLDER.
- Jobs manifest hash: PLACEHOLDER.

## Local Artifact Roots

- Raw DBN/Zstd root: PLACEHOLDER under `ALPHA_DATA_ROOT`.
- Canonical root: PLACEHOLDER under
  `ALPHA_DATA_ROOT/databento/canonical/glbx_mdp3`.
- Metadata root: PLACEHOLDER under
  `ALPHA_DATA_ROOT/databento/metadata/glbx_mdp3`.
- Registry path: PLACEHOLDER local-only SQLite path.
- File manifest path: PLACEHOLDER.
- File manifest hash: PLACEHOLDER.

## DatasetVersion IDs

- OHLCV DatasetVersion ID: PLACEHOLDER.
- BBO DatasetVersion ID: PLACEHOLDER.
- Metadata ref version ID: PLACEHOLDER.
- IBKR overlap DatasetVersion IDs: PLACEHOLDER.

## Quality, Coverage, BBO, And Metadata Summaries

- OHLCV quality summary: PLACEHOLDER.
- OHLCV coverage summary: PLACEHOLDER.
- BBO quality summary: PLACEHOLDER.
- BBO coverage summary: PLACEHOLDER.
- Missing BBO row count: PLACEHOLDER.
- Definition metadata summary: PLACEHOLDER.
- Statistics metadata summary: PLACEHOLDER.
- Status metadata summary: PLACEHOLDER.
- Metadata warnings: PLACEHOLDER.

## Cross-Source Diagnostic Notes

- Databento vs IBKR overlap status: PLACEHOLDER.
- Close alignment: PLACEHOLDER.
- Volume differences: PLACEHOLDER.
- Timestamp/session coverage differences: PLACEHOLDER.
- Missing intervals on each side: PLACEHOLDER.
- BBO availability note: PLACEHOLDER, Databento-only.
- Source merge status: no Databento/IBKR merge; diagnostic report only.

## Warnings

- PLACEHOLDER for live-run warnings.
- Sparse metadata schemas are warnings, not hard failures.
- Cross-source differences are warnings/diagnostics, not equality failures.

## Resume, Poll, And Download Commands

Load env in the operator shell only:

```bash
set -a
. ~/.databento_env
set +a
export PYTHONPATH=src:$HOME/.alpha_databento_libs
```

Re-run or resume from request spec:

```bash
python -m alpha_system.data.databento.request_spec \
  --start <START_PLACEHOLDER> \
  --end <END_PLACEHOLDER> \
  --symbols ES.v.0 NQ.v.0 RTY.v.0 \
  --stype-in continuous \
  --schemas ohlcv-1m bbo-1m definition statistics status \
  --output "$ALPHA_DATA_ROOT/manifests/databento/request_spec.json"
```

Refresh cost proof:

```bash
python -m alpha_system.data.databento.cost_check \
  --request-spec "$ALPHA_DATA_ROOT/manifests/databento/request_spec.json" \
  --output "$ALPHA_DATA_ROOT/manifests/databento/cost.json" \
  --max-cost-usd 110
```

Submit only after supervised approval:

```bash
python -m alpha_system.data.databento.submit_batch \
  --request-spec "$ALPHA_DATA_ROOT/manifests/databento/request_spec.json" \
  --cost-manifest "$ALPHA_DATA_ROOT/manifests/databento/cost.json" \
  --output "$ALPHA_DATA_ROOT/manifests/databento/jobs.json"
```

Poll/download completed jobs by re-running download; it blocks with the current
state if a job is not done:

```bash
python -m alpha_system.data.databento.download_batch \
  --jobs-manifest "$ALPHA_DATA_ROOT/manifests/databento/jobs.json" \
  --output-root "$ALPHA_DATA_ROOT/raw/databento" \
  --download-manifest "$ALPHA_DATA_ROOT/manifests/databento/download.json"
```

Hash, canonicalize, ingest metadata, register, and compare:

```bash
python -m alpha_system.data.databento.manifest_files \
  --raw-root "$ALPHA_DATA_ROOT/raw/databento" \
  --output "$ALPHA_DATA_ROOT/manifests/databento/file_manifest.json"

python -m alpha_system.data.databento.canonicalize \
  --file-manifest "$ALPHA_DATA_ROOT/manifests/databento/file_manifest.json" \
  --request-spec "$ALPHA_DATA_ROOT/manifests/databento/request_spec.json" \
  --output-root "$ALPHA_DATA_ROOT" \
  --instrument-config configs/data/databento_es_nq_rty_instruments.json \
  --calendar-config configs/data/session_templates_and_calendar.json \
  --validation-config configs/data/databento_materialize_validation.json

python -m alpha_system.data.databento.metadata_ingest \
  --file-manifest "$ALPHA_DATA_ROOT/manifests/databento/file_manifest.json" \
  --output-root "$ALPHA_DATA_ROOT"

python -m alpha_system.data.databento.register_dataset \
  --canonical-root "$ALPHA_DATA_ROOT/databento/canonical/glbx_mdp3" \
  --request-spec "$ALPHA_DATA_ROOT/manifests/databento/request_spec.json" \
  --registry-path "$ALPHA_DATA_ROOT/registry/datasets.sqlite" \
  --ohlcv-data-version <OHLCV_DSV_PLACEHOLDER> \
  --bbo-data-version <BBO_DSV_PLACEHOLDER> \
  --partition <PARTITION_PLACEHOLDER> \
  --instrument-config configs/data/databento_es_nq_rty_instruments.json \
  --calendar-config configs/data/session_templates_and_calendar.json \
  --validation-config configs/data/databento_materialize_validation.json

python -m alpha_system.data.databento.compare_sources \
  --databento-canonical-root "$ALPHA_DATA_ROOT/databento/canonical/glbx_mdp3" \
  --ibkr-registry-path "$ALPHA_DATA_ROOT/registry/datasets.sqlite" \
  --ibkr-symbol-root "$ALPHA_DATA_ROOT/ibkr/canonical" \
  --output "$ALPHA_DATA_ROOT/reports/databento_ibkr_compare.json"
```

## Files Changed In Run 3b

- `src/alpha_system/data/databento/metadata_ingest.py`
- `src/alpha_system/data/databento/compare_sources.py`
- `src/alpha_system/data/databento/canonicalize.py`
- `tests/unit/data/test_databento_metadata_compare.py`
- `docs/data_foundation/databento/README.md`
- `docs/data_foundation/databento/INGESTION_RUNBOOK.md`
- `docs/data_foundation/databento/CONSUMPTION.md`
- `docs/data_foundation/DATASET_CONSUMPTION.md`
- `handoffs/ADF1_DATABENTO_ES_NQ_RTY_OHLCV_BBO_DEEP_HISTORY.md`

## Artifact Audit Result

Run 3b expected result: no API key committed, no raw Databento committed, no
canonical Databento committed, no metadata market data committed, no local DB
committed, no report bundle committed, no `runs/**` committed. Final command
results:

- `python -m compileall src/alpha_system/data/databento tests/unit/data`: PASS.
- `python -m ruff check <changed Python files>`: PASS.
- `python -m pytest tests/unit/data/test_databento_metadata_compare.py -q`: PASS
  (`4 passed`).
- `CI=true python -m pytest -q`: PASS (`1797 passed`).
- Secret-pattern scan for `db-...` in changed files: PASS, no matches.
- Heavy-artifact scan for DBN/Zstd, SQLite/DB, Parquet, Arrow, Feather, and
  raw files: PASS, no matches.
- Generated Python bytecode caches from validation were removed.

Codex did not run git for this task because the executor instructions forbid
all git commands.

## Explicit Scope Statements

- No API key committed.
- No raw Databento committed.
- No alpha search.
- No Feature/Label materialization.
- No broker, live, paper, account, or order scope.
- No Databento/IBKR merged DatasetVersion.
- ES/NQ/RTY only.
