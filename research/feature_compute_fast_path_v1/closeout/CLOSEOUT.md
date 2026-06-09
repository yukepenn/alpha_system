# FEATURE_COMPUTE_FAST_PATH_V1 Closeout

- Campaign: `FEATURE_COMPUTE_FAST_PATH_V1`
- Phase: `FCFP-P16`
- Verdict: `COMPLETE_WITH_WARNINGS`
- Value policy: value-free closeout only. This document cites committed
  summaries, handoffs, docs, and tests. It includes no per-row feature values,
  label values, prices, Parquet payloads, SQLite content, provider responses, or
  alpha/profitability/tradability claim.

## Verdict Rationale

`FEATURE_COMPUTE_FAST_PATH_V1` completed the V1 producer compute path required
to resume FUTSUB on V1: the `PackMaterializer` engine core, governed feature
packs, governed fixed-horizon label pack, targeted/incremental scaleout, engine
provenance/reconciliation, bounded-real benchmark gate, default V1 producer
integration, resolver smoke, and benchmark-driven CPU worker parallelism are
present and supported by committed value-free evidence. The closeout is
`COMPLETE_WITH_WARNINGS` because several phase handoffs carry documented
environment or scope caveats: broad `verify.py --test` / `verify.py --all`
failures outside the touched paths, missing `ruff` in some executor
environments, absent run-local `state.json` directories in this checkout, the
P03 present-metadata deferral, the P10 longer-horizon governance gap, and P14's
`session_label` diagnostic resolver caveat. Those caveats do not invalidate the
V1 parity, benchmark, registry, integration, or worker evidence, but they must
not be silently dropped.

## Status Fields

| Field | Status | Evidence |
| --- | --- | --- |
| `code_status` | `COMPLETE_WITH_WARNINGS` | P01-P15 code/docs/tests/handoffs landed under `handoffs/FEATURE_COMPUTE_FAST_PATH_V1/FCFP-P01.md` through `handoffs/FEATURE_COMPUTE_FAST_PATH_V1/FCFP-P15.md`; focused fast-path tests are under `tests/unit/feature_compute_fast_path/**`. Warnings are documented in those handoffs, especially broad-suite environment reds in `FCFP-P03.md`, `FCFP-P08.md`, `FCFP-P09.md`, and `FCFP-P14.md`. |
| `producer_fast_path_v1_status` | `COMPLETE` | Synthetic parity evidence exists for the engine/packs in `tests/unit/feature_compute_fast_path/**` and value-free reports under `research/feature_compute_fast_path_v1/parity/**` plus `research/feature_compute_fast_path_v1/label_packs/fixed_horizon_parity.md`. The bounded benchmark reports parity `PASS` for all measured packs in `research/feature_compute_fast_path_v1/benchmark/benchmark_summary.md`; worker parallelism reports parity, resolver smoke, deterministic hashes, and fastest stable worker count in `research/feature_compute_fast_path_v1/workers/worker_benchmark_summary.md`. |
| `execute_status` | `COMPLETE_WITH_WARNINGS` | The V1 execute path completed representative bounded-real materialization and idempotency checks in `research/feature_compute_fast_path_v1/integration/integration_report.md`, and the worker benchmark exercised requested workers `1,2,4,8` in `research/feature_compute_fast_path_v1/workers/worker_benchmark_summary.md`. Full FUTSUB accepted-window execution is intentionally not claimed here; it remains a FUTSUB coordinator action. |
| `registry_status` | `COMPLETE` | Producer provenance and value-schema versioning are recorded by policy and tests in `research/feature_compute_fast_path_v1/reconciliation/reconciliation_summary.md` and `docs/feature_compute_fast_path/ENGINE_PROVENANCE_RECONCILIATION.md`. P14 confirms V1 feature writes through `PackMaterializer.register_pack` / `FeatureStore`, label writes through `FastLabelMaterializer` / `LabelRegistry`, and serial official registry writes in `research/feature_compute_fast_path_v1/integration/integration_report.md`; P15 keeps worker registry writes parent-only and serial in `research/feature_compute_fast_path_v1/workers/worker_benchmark_summary.md`. |
| `consumer_query_status` | `COMPLETE_WITH_WARNINGS` | Runtime resolver smoke resolved representative V1-produced feature/label lock pairs and failed closed on stale/fuzzy controls in `research/feature_compute_fast_path_v1/integration/integration_report.md`. The P14 handoff documents one diagnostic `session_label` resolver-policy caveat that was not weakened in this campaign: `handoffs/FEATURE_COMPUTE_FAST_PATH_V1/FCFP-P14.md`. |
| `artifact_status` | `COMPLETE` | The committed evidence root is value-free by contract in `research/feature_compute_fast_path_v1/README.md`; benchmark, reconciliation, integration, and worker summaries all declare value-free scope. Prior phase handoffs record empty `git ls-files runs` and heavy-glob checks where run by the executor, and P16 re-runs those artifact audits before handoff. |

## Phase Roll-Up

| Phase | What Landed | Parity / Evidence Status | Warnings Carried |
| --- | --- | --- | --- |
| `FCFP-P00` | Campaign pointer, docs index, value-free evidence root. | Contract/bundle checks and smoke passed in `handoffs/FEATURE_COMPUTE_FAST_PATH_V1/FCFP-P00.md`. | No pack parity yet; `git status` skipped by executor instruction. |
| `FCFP-P01` | `PackMaterializer` engine core, fast declaration/pack contracts, reusable parity harness. | Demonstrator reference parity and focused fast-path tests passed; see `handoffs/FEATURE_COMPUTE_FAST_PATH_V1/FCFP-P01.md` and `tests/unit/feature_compute_fast_path/parity_harness.py`. | No production pack in P01; Polars was available in that executor environment. |
| `FCFP-P02` | `base_ohlcv` Polars pack and fail-closed pack resolver. | Value, `available_ts`, gap/flag, and identity parity passed with documented `volume_zscore` tolerance; see `research/feature_compute_fast_path_v1/parity/base_ohlcv/FCFP-P02_PARITY.md`. | Initial test failures were repaired in scope; no Polars skip. |
| `FCFP-P03` | `session_calendar_roll` pack. | Exact synthetic parity for ten governed features; see `research/feature_compute_fast_path_v1/parity/session_calendar_roll/FCFP-P03_PARITY.md`. | Present expiration/status metadata projection is deferred to the reference oracle; `verify.py --test` showed four broad-suite failures outside P03 scope in `handoffs/FEATURE_COMPUTE_FAST_PATH_V1/FCFP-P03.md`. |
| `FCFP-P04` | `vwap_session_auction` pack. | Synthetic parity passed with documented `1e-12` tolerance for cumulative VWAP reductions; see `research/feature_compute_fast_path_v1/parity/vwap_session_auction/FCFP-P04_PARITY.md`. | No Polars skip; no broad-suite red recorded for this phase. |
| `FCFP-P05` | `regime_vol_compression` pack. | Synthetic parity passed for ATR, trendiness, and range contraction; see `research/feature_compute_fast_path_v1/parity/regime_vol_compression/FCFP-P05_PARITY.md`. | Initial helper error repaired in scope. |
| `FCFP-P06` | `liquidity_pa_structure` pack. | Synthetic parity/materialization-provenance tests passed; reconciliation classification later covered the family in `research/feature_compute_fast_path_v1/reconciliation/reconciliation_summary.md`. | Floating tolerance limited to documented OHLC ratio reductions; no real backfill run. |
| `FCFP-P07` | `volume_activity` pack. | Synthetic parity test passed; reconciliation classification later covered the family in `research/feature_compute_fast_path_v1/reconciliation/reconciliation_summary.md`. | Floating tolerance limited to finite reductions/ratios; no Polars skip. |
| `FCFP-P08` | `bbo_tradability` pack. | Synthetic parity passed, with `spread_zscore` tolerance; benchmark real-data parity later passed in `research/feature_compute_fast_path_v1/benchmark/benchmark_summary.md`. | `ruff` absent in the executor environment; broad `verify.py --test` had four unrelated failures, documented in `handoffs/FEATURE_COMPUTE_FAST_PATH_V1/FCFP-P08.md`. |
| `FCFP-P09` | `cross_market` aligned-panel pack. | Synthetic strict-intersection/asof parity passed; see `research/feature_compute_fast_path_v1/parity/cross_market/FCFP-P09_PARITY.md`. | Broad `verify.py --test` had the same four unrelated failures; some git artifact checks were skipped by that executor's stricter git-command prompt, documented in `handoffs/FEATURE_COMPUTE_FAST_PATH_V1/FCFP-P09.md`. |
| `FCFP-P10` | `fixed_horizon` label pack and fast label materializer. | Exact governed-label parity passed; see `research/feature_compute_fast_path_v1/label_packs/fixed_horizon_parity.md`. | Longer FUTSUB narrative horizons beyond the governed enum remain a governance gap; this phase did not create new labels or identities. |
| `FCFP-P11` | Targeted/incremental `alpha scaleout feature-pack` selection, dry-run estimates, execute-selected-only, checkpoint plus registry truth skip. | Behavioral tests passed; see `tests/unit/feature_compute_fast_path/test_scaleout_cli_targeting.py` and `handoffs/FEATURE_COMPUTE_FAST_PATH_V1/FCFP-P11.md`. | Label selectors are accepted as target metadata but no separate label scaleout command was invented in P11. |
| `FCFP-P12` | `producer_engine_id` / `value_schema_version` provenance and no-silent-engine-mixing reconciliation policy. | Reconciliation summary classifies existing reference outputs as identical or within documented tolerance and keeps them as parity reference; see `research/feature_compute_fast_path_v1/reconciliation/reconciliation_summary.md`. | `status_doctor.py` warned that this checkout lacked a live run `state.json`; no full backfill or overwrite was run. |
| `FCFP-P13` | Bounded-real benchmark gate. | Current committed benchmark summary is `COMPLETE` and reports parity `PASS`, speedup, rows/sec, canonical reads, outputs/read, and full-window estimates for all measured packs: `research/feature_compute_fast_path_v1/benchmark/benchmark_summary.md`. | The P13 handoff preserves an earlier `BLOCKED_PARITY` executor attempt; the committed summary reflects the repaired/completed benchmark evidence. |
| `FCFP-P14` | V1 default producer path, `--engine reference` fallback, bounded-real integration smoke, resolver smoke, engine-aware idempotency. | Integration report shows representative V1 feature/label materialization, official resolver positives, fail-closed controls, and serial official registry paths: `research/feature_compute_fast_path_v1/integration/integration_report.md`. | `verify.py --all` had four broad-suite failures outside P14 scope; diagnostic `session_label` resolver-policy gap was not weakened. |
| `FCFP-P15` | CPU worker parallelism for V1 compute with parent-only serial registry writes and `{1,2,4,8}` worker benchmark. | Worker summary reports parity `PASS`, resolver smoke `PASS`, deterministic hashes, stable worker reductions, and fastest stable requested worker count `4`: `research/feature_compute_fast_path_v1/workers/worker_benchmark_summary.md`. | Handoff records an initial sandbox benchmark stall and subsequent coordinator-resolved benchmark completion; run-local phase directory was absent in this checkout. |

## Boundaries Held

- The reference feature/label engine remains the correctness oracle and was not
  deleted or weakened.
- V1 emits values for existing governed definitions only. It preserves exact
  `feature_version_id` and `label_version_id` identity; producer provenance and
  request provenance do not enter identity.
- Official registry writes remain serial. Worker processes compute values and
  deterministic manifests only; parent/official paths own registration.
- Existing valid reference outputs are preserved and reconciled per ADR-0007 /
  FCFP-P12. No silent reference/V1 engine mixing inside one logical value series
  is allowed.
- No raw data, canonical data, feature values, label values, SQLite registries,
  Parquet/Arrow/Feather/DB/DBN/Zstd heavy artifacts, provider responses, logs,
  caches, model artifacts, or `runs/**` artifacts are commit-eligible.
- No live trading, paper trading, broker operation, order routing, production
  deployment, external provider call, new alpha ideation, parameter search, or
  profitability/tradability claim is made.

## Closeout Result

The campaign is closed as `COMPLETE_WITH_WARNINGS`: V1 is ready for the
coordinator-owned FUTSUB resume-on-V1 flow, while the documented caveats above
remain visible for review and downstream planning.
