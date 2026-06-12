# P043653_TBBO_SCHEMA_SUPPORT Handoff

Campaign: `TBBO_COST_CALIBRATION_V1`
Phase: `P043653_TBBO_SCHEMA_SUPPORT`
Branch: `wf1/tbbo-schema-support`

## Scope Completed

- Added `tbbo` to the shared Databento request-spec schema allowlist and CLI help.
- Extended Databento canonicalize routing to load, normalize, partition, and manifest `tbbo`
  rows offline.
- Added a local `CanonicalTBBORecord` shape carrying event timestamp, trade price, trade
  size, aggressor side, bid/ask prices, bid/ask sizes, provenance, availability timestamp,
  and session metadata.
- Kept TBBO canonicalization composed with existing data-root validation, DBN decode
  loading, session filtering, `_write_schema_records`, and dataset manifest writing.
- Added tests for request-spec acceptance, non-allowlisted rejection coverage already
  present for `trades`, TBBO canonical partition/manifest/round-trip fields, real DBN row
  loader routing via a fake module, and raw file manifest schema inference.

## Module Audit

Touched:

- `src/alpha_system/data/databento/request_spec.py`
- `src/alpha_system/data/databento/canonicalize.py`
- `tests/unit/data/test_databento_canonicalize.py`
- `tests/unit/data/test_databento_ingest_clis.py`

Already schema-generic through the shared allowlist or `spec.schemas` iteration:

- `src/alpha_system/data/databento/cost_check.py` quotes one cost per requested schema;
  `DEFAULT_MAX_COST_USD` remains unchanged at `110.0`.
- `src/alpha_system/data/databento/submit_batch.py` submits one job per requested schema;
  submit hard-cap semantics remain unchanged.
- `src/alpha_system/data/databento/download_batch.py` stores downloads under
  `.../<schema>/<job_id>/` from each job manifest entry.
- `src/alpha_system/data/databento/manifest_files.py` infers schemas from
  `DATABENTO_ALLOWED_SCHEMAS`; the shared allowlist change is sufficient.

Not schema-generic and intentionally not changed for this pull-pipeline phase:

- `src/alpha_system/data/databento/coverage.py`
- `src/alpha_system/data/databento/quality.py`
- `src/alpha_system/data/databento/register_dataset.py`

Those modules remain OHLCV/BBO/dense-grid dataset-versioning and quality gates. This phase
enabled the offline paid-pull path through canonicalize and did not introduce TBBO
registration, quality, coverage, or research-readiness claims.

## Validation

- `~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/data -q`
  - Result: PASS
  - Output count: `440 passed in 5.16s`
- `~/.venvs/alpha_system_research/bin/python tools/hooks/canary_runner.py`
  - Result: PASS
  - Output count: 25 `PASS` lines; final line `All Frontier canaries passed.`
- `~/.venvs/alpha_system_research/bin/python tools/verify.py --smoke`
  - Result: PASS
  - Output count: no stdout/stderr; exit code 0.
- `PATH="$HOME/.venvs/alpha_system_research/bin:$PATH" just ci-parity`
  - Result: PASS
  - Output count: `3288 passed, 75 skipped in 83.41s (0:01:23)`
  - Bootstrap detail: `ci_parity.py` used
    `/home/yuke_zhang/.venvs/alpha_system_ci/bin/python -m pytest`.

Additional checks:

- `~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/data/test_databento_canonicalize.py tests/unit/data/test_databento_ingest_clis.py -q`
  - Result: PASS
  - Output count: `22 passed in 3.21s`
- `~/.venvs/alpha_system_research/bin/python -m py_compile src/alpha_system/data/databento/request_spec.py src/alpha_system/data/databento/canonicalize.py tests/unit/data/test_databento_canonicalize.py tests/unit/data/test_databento_ingest_clis.py`
  - Result: PASS
  - Output count: no stdout/stderr; exit code 0.
- `git diff --check`
  - Result: PASS
  - Output count: no stdout/stderr; exit code 0.
- `git ls-files runs`
  - Result: PASS
  - Output count: empty.

Attempted non-spec sanity check:

- `~/.venvs/alpha_system_research/bin/python -m ruff check src/alpha_system/data/databento/request_spec.py src/alpha_system/data/databento/canonicalize.py tests/unit/data/test_databento_canonicalize.py tests/unit/data/test_databento_ingest_clis.py`
  - Result: not run; `ruff` is not installed in the requested research venv.
  - Exact output: `/home/yuke_zhang/.venvs/alpha_system_research/bin/python: No module named ruff`

## Notes

- No network calls, credentials, purchases, Databento SDK imports, or raw data artifacts were
  used.
- No changes were made under `src/alpha_system/{features,labels,runtime,governance}/**`.
- Review artifacts under `reviews/TBBO_COST_CALIBRATION_V1/` remain pending for the fresh
  reviewer; this executor did not self-review.
