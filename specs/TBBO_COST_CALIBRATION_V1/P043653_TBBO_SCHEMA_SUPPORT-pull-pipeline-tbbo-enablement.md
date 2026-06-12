---
campaign_id: TBBO_COST_CALIBRATION_V1
phase_id: P043653_TBBO_SCHEMA_SUPPORT
lane: yellow
status: in_progress
---

# P043653_TBBO_SCHEMA_SUPPORT: enable the `tbbo` schema in the gated Databento pull pipeline

## Purpose

USER-APPROVED TBBO sample-month purchase (compass v4.4 Stage I cost-truth
item): calibrate the cost stack's spread/slippage assumptions against real
trade+BBO prints for ~3 ES sample months. The gated pull pipeline
(request_spec → cost_check → submit → download → canonicalize) currently
rejects `tbbo` at the schema allowlist. This phase makes the PIPELINE able to
carry tbbo end-to-end, offline-only. The actual paid pull is NOT in scope —
the coordinator executes it separately under the env-gated Red-lane flow
with the in-repo $110 hard cap.

## Scope (in-bounds)

1. `src/alpha_system/data/databento/request_spec.py`: add `"tbbo"` to
   `DATABENTO_ALLOWED_SCHEMAS` (line ~31). No other request_spec semantics
   change.
2. `src/alpha_system/data/databento/canonicalize.py`: route `tbbo` rows the
   way `ohlcv-1m`/`bbo-1m` are routed today (study lines 54-57 and the
   `_write_schema_records` call sites ~174-221; COMPOSE, don't fork):
   `TBBO_SCHEMA = "tbbo"`, `TBBO_PARTITION_SCHEMA = "tbbo"`; a normalized
   canonical row for tbbo records carrying at minimum: event timestamp,
   trade price, trade size, aggressor side, and the contemporaneous bid/ask
   price+size, with the same timestamp/partition discipline the existing
   schemas use. Derive field names from the Databento TBBO (`tbbo`) DBN
   record layout as exposed by the existing decode path
   (`download_batch.py` / `client.py` — inspect how ohlcv/bbo rows reach
   `_load_rows_by_schema`, mirror it). The dataset-version manifest
   (`canonical_dataset_version.v1`) must list the tbbo partition exactly as
   it lists ohlcv/bbo partitions.
3. If any intermediate stage (submit_batch, download_batch, coverage,
   quality, register_dataset) hard-codes the two existing schemas, extend it
   minimally and symmetrically; report in the handoff which modules needed
   touches and which were already schema-generic.
4. Tests (mirror `tests/unit/data/test_databento_canonicalize.py` +
   request-spec tests): synthetic tbbo fixture rows (no network, no SDK
   import) → request spec accepts `tbbo`; canonicalize writes the tbbo
   partition; manifest lists it; round-trip read returns the normalized
   fields; a NON-allowlisted schema still refuses (negative, proves the
   allowlist still gates).

## Hard constraints

- Offline only: no network calls, no Databento SDK objects in code or tests
  (existing module docstring discipline), no credentials, no purchases.
- Do not change cost_check semantics or the $110 `DEFAULT_MAX_COST_USD` cap.
- Do not touch `src/alpha_system/{features,labels,runtime,governance}/**`.
- Explicit staging; no values/SQLite/runs committed; research-only language.

## Validation

```bash
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/data -q
python tools/hooks/canary_runner.py
python tools/verify.py --smoke
just ci-parity
```

## Done criteria

`tbbo` flows request_spec→canonicalize offline with tests proving partition
+ manifest + normalized fields + still-gated allowlist; untouched modules
reported as already-generic; validation green incl. ci-parity; truthful
handoff; fresh adversarial review PASS/PASS_WITH_WARNINGS under
reviews/TBBO_COST_CALIBRATION_V1/.
