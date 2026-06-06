# Handoff — POST_RUNTIME_FEATURE_LABEL_STORAGE_AND_SEED_PACKS_V1

Workflow 1. Architecture-convergence + operator-readiness task. Outcome:
**PASS_WITH_WARNINGS** (real-data runtime smoke now PASSES; two deliberate
deferrals + one guard follow-up are documented below).

## 1. Final storage architecture truth

The long-term agreed stack is **real and already implemented** for the data
foundation; the concern that the system "writes JSONL instead of Parquet" was
only partially correct.

- Canonical market data **is Parquet** (Hive-partitioned
  `schema=ohlcv_1m/root=<sym>/part-00000.parquet`), read via optional
  `pyarrow`/`polars`/`duckdb`; DuckDB SQL-over-Parquet (`data/query.py`),
  Polars (`data/storage.py`), NumPy/Numba hot loops (`backtest/fast_arrays.py`)
  all exist behind the optional-dependency pattern; core `dependencies = []`.
- SQLite is metadata/registry only. Three separate local registries:
  `datasets.sqlite` (DatasetVersions), `features.sqlite`, `labels.sqlite`.
  They store paths/hashes/counts/ts-ranges/lineage — **never value payloads**.
- The **narrow real divergence**: feature/label **values** are written as
  deterministic **JSONL** (`values.jsonl`), with no ADR reconciling this against
  the "large data = Parquet" intent. The Research Runtime resolver is
  **value-free** (metadata only), so JSONL did not block the runtime; it would
  bite large-scale value-consuming research.

## 2. JSONL vs Parquet decision

Codified in **[ADR-0006](../decisions/0006-feature-label-value-storage.md)** as a
two-tier policy: **JSONL = audit/small/MVP tier (current, acceptable)**;
**Parquet = research-scale tier (intended, deferred to
`FEATURE_LABEL_PARQUET_SINK_V1`)**. SQLite stays metadata-only. The Parquet sink
was **deliberately deferred** (no value-consumer exists yet; the runtime is
metadata-only) rather than faked. Follow-up scoped in
`docs/STRUCTURAL_BACKLOG.md` §4.

## 3. DatasetVersion used

`dsv_databento_ohlcv_05404069799decb0` — accepted Databento canonical
**TRADES** (`schema=ohlcv_1m`), ES/NQ/RTY, 1-min, 2024-01-01→2025-01-01,
resolved from the local `datasets.sqlite`. The seed used the **ES** symbol over a
small window **2024-01-02T00:00Z → 2024-01-09T00:00Z** (6,896 real 1-min bars,
all `session_label=ETH`). The dense-grid dsv was **not** used (it is a
`DenseGridBarRecord`, which the OHLCV feature input view does not consume).

## 4. Seed FeaturePack / LabelPack specs

Governed by `configs/seed_packs/es_ohlcv_2024_smoke_v1.json` (metadata only).

- **FeaturePack** `fset_es_ohlcv_session_smoke` — 6 distinct BASE_OHLCV features
  (a `FeatureSetSpec` requires unique feature ids): `returns`, `log_returns`,
  `rolling_volatility` (w=30), `rolling_range` (w=30), `volume_zscore` (w=30),
  `range_position`. Each admitted through the FLF-P05 FeatureRequest gate
  (APPROVED, empty-exposure notes).
- **LabelPack** `lset_es_fwd_returns_smoke` — 3 trade-price fixed-horizon labels:
  `fwd_ret_5m`, `fwd_ret_10m`, `fwd_ret_30m` (5–30m primary horizons; 1-min is a
  sampling frequency, not the primary alpha horizon). Each governed by a
  horizon-matched `LabelSpec` with `leakage_checks=[label_as_feature,
  availability_time]`.

## 5. Registry paths (local-only, never committed)

- Feature registry: `$ALPHA_DATA_ROOT/registry/features.sqlite`
- Label registry: `$ALPHA_DATA_ROOT/registry/labels.sqlite`
- Dataset registry (pre-existing): `$ALPHA_DATA_ROOT/registry/datasets.sqlite`

`$ALPHA_DATA_ROOT = ~/alpha_data/alpha_system`.

## 6. Materialized value paths + format (local-only, never committed)

Format: **JSONL** (`values.jsonl`). 7 files total — one per feature (the
operator materializes/registers per feature so the duplicate-exposure gate
admits distinct features) plus one combined label file:

- `$ALPHA_DATA_ROOT/features/materialized/fset_es_ohlcv_session_smoke/v1_<feature>/dsv_databento_ohlcv_05404069799decb0/development_partition/values.jsonl` (×6)
- `$ALPHA_DATA_ROOT/labels/materialized/<label_set_hash>/dsv_databento_ohlcv_05404069799decb0/development_partition/values.jsonl`

## 7. Value counts + timestamp ranges (no-lookahead verified)

- Features: each **6,896** records; `event_ts` 2024-01-02T00:01:00Z →
  2024-01-09T00:00:00Z; `available_ts` = `event_ts` + 5s (≥ event). Total 41,376.
- Labels: `fwd_ret_5m` 6,862; `fwd_ret_10m` 6,832; `fwd_ret_30m` 6,712 (forward
  horizons drop tail bars). `label_available_ts` is horizon-correct (e.g.
  fwd_ret_5m first label_available_ts 00:06:05Z for event 00:01:00Z) and never
  precedes the horizon end. Total 20,406.
- Real quality + coverage reports over the partition: **PASSING / non-blocking**.

## 8. Runtime real-data smoke result

**PASS.** `python -m alpha_system.runtime.smoke` with
`ALPHA_DATA_ROOT`, `ALPHA_DATASET_VERSION_ID=dsv_databento_ohlcv_05404069799decb0`,
`ALPHA_DATASET_LIFECYCLE_STATE=VERSIONED`, `ALPHA_RUNTIME_SMOKE_PARTITION_ID=development_partition`,
`ALPHA_FEATURE_PACK_REFS=<6 fver_…>`, `ALPHA_LABEL_PACK_REFS=<3 lver_…>`:

- `status: PASS`, `input_resolution_status: INPUTS_RESOLVED`,
  `real_dataset_version_smoke_ran: true`, no rejections.
- Generated `RuntimeRunSummary` + `RuntimeToolResult`
  (`status: EVIDENCE_DRAFT_READY`, `next_required_gate: fresh_yellow_lane_review_before_merge`),
  with factor/label/cost diagnostics referenced (scalar summaries only).
- `external_provider_call: false`, `raw_file_read: false`,
  `raw_or_heavy_data_embedded: false`.

The tiny-sample factor IC and the "DIAGNOSTICS_FAILED" label gate are
descriptive artifacts of a 4-pair diagnostic and are **not** alpha/quality
claims; the smoke proves the loop runs, nothing more.

## 9. Environment

Isolated venv `~/.venvs/alpha_system_research` (not committed): Python 3.12.3,
pip bootstrapped via `get-pip.py` (system `python3-venv` lacks `ensurepip`),
then `polars 1.41.2`, `pyarrow 24.0.0`, `duckdb 1.5.3`, and an editable install
of `alpha_system`. No global installs. No `pyproject` core-dependency changes.
The repo test/lint suite runs on system Python via `PYTHONPATH=src` (stdlib
substrate); only the real Parquet-backed seed run needs the venv.

## 10. What was implemented (committed, curated)

- `decisions/0006-feature-label-value-storage.md` (ADR) + index.
- Doc reconciliations: `docs/ARCHITECTURE.md`, `FEATURE_MATERIALIZATION.md`,
  `LABEL_MATERIALIZATION.md`; new `docs/feature_label_foundation/RESEARCH_RESOLUTION.md`.
- `src/alpha_system/data/foundation/canonical_loader.py` — dependency-guarded
  canonical-Parquet → bar-rows loader (polars via `require_dependency`).
- `src/alpha_system/cli/seed_pack.py` — generic governed seed operator (load →
  REAL quality/coverage over the partition → AcceptedDatasetVersion → materialize
  → register). Placed in the CLI/orchestration layer (NOT `features/`) so the
  provider-boundary guard stays satisfied.
- `alpha feature materialize --execute` / `alpha label materialize --execute`
  wiring (default remains dry-run plan).
- `configs/seed_packs/es_ohlcv_2024_smoke_v1.json` + README.
- Tests: `tests/unit/data/test_canonical_loader.py`,
  `tests/integration/features/test_seed_pack_execute.py`.
- `docs/STRUCTURAL_BACKLOG.md` §4 (Parquet sink) + §5 (registry-reports gap).
- `.gitignore`: `*.egg-info/`.

## 11. Warnings / deferrals (PASS_WITH_WARNINGS basis)

1. **Parquet research-scale sink deferred** → `FEATURE_LABEL_PARQUET_SINK_V1`
   (ADR-0006; backlog §4). JSONL is the current audit/small tier.
2. **Session-context features deferred** (`rth_flag`, `eth_flag`,
   `session_minute`). They read the canonical `session_label` input field, and
   the runtime leakage guard `_reject_label_as_live_feature`
   (`runtime/input_resolver.py`) false-positives on any field ending in
   `_label`. `session_label` is a point-in-time categorical (RTH/ETH), not a
   forward label — a guard over-match, not real leakage. Follow-up: narrow the
   heuristic (exclude known canonical fields) with no-lookahead tests. The guard
   was **not** modified in this task (hard "no weakening guards" constraint).
3. **Dataset registry persists only report hashes**, not the reports, so an
   accepted dsv cannot be registry-resolved for materialization without its
   original reports. The operator works around this by running the REAL QA
   builders over the materialized partition and constructing the consumption
   handle directly (ADR-0006 §4; backlog §5).

## 12. Compliance statements

- **No raw data committed.** Raw/canonical Databento data stays under
  `$ALPHA_DATA_ROOT` (Parquet), never in the repo; `git ls-files` shows no
  `.dbn/.zst/.parquet/.sqlite/.jsonl` data artifacts.
- **No real values committed.** All `values.jsonl` and the
  `features.sqlite`/`labels.sqlite` registries live under `$ALPHA_DATA_ROOT`
  (outside the repo), gitignored, never staged.
- **No alpha/factor/tradability/profitability claim.** No factor promotion, no
  strategy/backtest/portfolio work, no paper/live/broker action.
- **No external provider calls.** The loader reads already-canonical local
  Parquet only.

## 13. Validation

- `python tools/verify.py --all`: **2444 passed, 1 skipped, rc=0** (incl.
  `compileall`); `ruff check`: clean; canonical-loader test skips without polars
  (verified separately in the venv); seed-pack execute test passes.
- Real seed materialization + runtime smoke executed in the venv (above).
- CLI `--execute` validated end-to-end against a temp root reading real Parquet.
- Artifact audit clean (no `runs/`, no heavy/data artifacts tracked).

## 14. Next action

**`ALPHA_AGENT_FACTORY_MVP`** is the next campaign — the real-data runtime smoke
is now closed with actual evidence and registered seed packs exist. Recommended
to land `FEATURE_LABEL_PARQUET_SINK_V1` (and optionally the `session_label`
guard fix) before any large-scale, value-consuming Agent Factory study.
