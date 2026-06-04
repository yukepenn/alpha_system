# Databento Ingestion Runbook

This is an operator-only flow. Never run it in CI. Do not commit raw DBN/Zstd,
canonical data, metadata refs, reports, local registries, logs, or secrets.

## Environment

Keep the Databento key in environment only. A local file such as
`~/.databento_env` may set names, but it must never be committed:

```bash
export DATABENTO_API_KEY=<operator-provided value>
export ALPHA_DATA_PULL_AUTHORIZED=true
export ALPHA_ALLOW_EXTERNAL_DATABENTO=true
export ALPHA_ALLOW_RAW_LOCAL_WRITE=true
export ALPHA_DATA_ROOT=$HOME/alpha_data/alpha_system
```

Load it only in the operator shell:

```bash
set -a
. ~/.databento_env
set +a
```

Install the optional SDK outside the repo:

```bash
python -m pip install --target ~/.alpha_databento_libs databento
export PYTHONPATH=src:$HOME/.alpha_databento_libs
```

After the supervised run is complete, rotate the Databento key.

## Ordered Flow

1. Request spec, offline:

```bash
python -m alpha_system.data.databento.request_spec \
  --start 2018-01-01T00:00:00Z \
  --end <explicit-end>Z \
  --symbols ES.v.0 NQ.v.0 RTY.v.0 \
  --stype-in continuous \
  --schemas ohlcv-1m bbo-1m definition statistics status \
  --output "$ALPHA_DATA_ROOT/manifests/databento/request_spec.json"
```

2. Cost check, FREE quote and budget gate:

```bash
python -m alpha_system.data.databento.cost_check \
  --request-spec "$ALPHA_DATA_ROOT/manifests/databento/request_spec.json" \
  --output "$ALPHA_DATA_ROOT/manifests/databento/cost.json" \
  --max-cost-usd 110
```

The hard cap is `$110`. A stale, over-budget, or mismatched cost manifest blocks
submission.

3. Submit batch, paid and gated:

```bash
python -m alpha_system.data.databento.submit_batch \
  --request-spec "$ALPHA_DATA_ROOT/manifests/databento/request_spec.json" \
  --cost-manifest "$ALPHA_DATA_ROOT/manifests/databento/cost.json" \
  --output "$ALPHA_DATA_ROOT/manifests/databento/jobs.json"
```

4. Download completed jobs to immutable local raw storage:

```bash
python -m alpha_system.data.databento.download_batch \
  --jobs-manifest "$ALPHA_DATA_ROOT/manifests/databento/jobs.json" \
  --output-root "$ALPHA_DATA_ROOT/raw/databento" \
  --download-manifest "$ALPHA_DATA_ROOT/manifests/databento/download.json"
```

5. Hash raw DBN/Zstd files:

```bash
python -m alpha_system.data.databento.manifest_files \
  --raw-root "$ALPHA_DATA_ROOT/raw/databento" \
  --output "$ALPHA_DATA_ROOT/manifests/databento/file_manifest.json"
```

6. Canonicalize OHLCV and BBO refs:

```bash
python -m alpha_system.data.databento.canonicalize \
  --file-manifest "$ALPHA_DATA_ROOT/manifests/databento/file_manifest.json" \
  --request-spec "$ALPHA_DATA_ROOT/manifests/databento/request_spec.json" \
  --output-root "$ALPHA_DATA_ROOT" \
  --instrument-config configs/data/databento_es_nq_rty_instruments.json \
  --calendar-config configs/data/session_templates_and_calendar.json \
  --validation-config configs/data/databento_materialize_validation.json
```

7. Ingest metadata refs:

```bash
python -m alpha_system.data.databento.metadata_ingest \
  --file-manifest "$ALPHA_DATA_ROOT/manifests/databento/file_manifest.json" \
  --output-root "$ALPHA_DATA_ROOT"
```

8. Register separate OHLCV and BBO DatasetVersions:

```bash
python -m alpha_system.data.databento.register_dataset \
  --canonical-root "$ALPHA_DATA_ROOT/databento/canonical/glbx_mdp3" \
  --request-spec "$ALPHA_DATA_ROOT/manifests/databento/request_spec.json" \
  --registry-path "$ALPHA_DATA_ROOT/registry/datasets.sqlite" \
  --ohlcv-data-version <dsv_databento_ohlcv_PLACEHOLDER> \
  --bbo-data-version <dsv_databento_bbo_PLACEHOLDER> \
  --partition <development_partition|validation_partition|locked_test_candidate> \
  --instrument-config configs/data/databento_es_nq_rty_instruments.json \
  --calendar-config configs/data/session_templates_and_calendar.json \
  --validation-config configs/data/databento_materialize_validation.json
```

9. Compare against local IBKR diagnostics when overlap exists:

```bash
python -m alpha_system.data.databento.compare_sources \
  --databento-canonical-root "$ALPHA_DATA_ROOT/databento/canonical/glbx_mdp3" \
  --ibkr-registry-path "$ALPHA_DATA_ROOT/registry/datasets.sqlite" \
  --ibkr-symbol-root "$ALPHA_DATA_ROOT/ibkr/canonical" \
  --output "$ALPHA_DATA_ROOT/reports/databento_ibkr_compare.json"
```

## Guardrails

DBN/Zstd raw files are immutable local artifacts. No command should print or
write the API key. No command should run without `ALPHA_DATA_ROOT` outside the
repository. Databento and IBKR DatasetVersions remain separate. Sparse
metadata schemas produce warnings, not hard failures. Quality, coverage,
no-lookahead, partition, and locked-test gates remain fail-closed.
