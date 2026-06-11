# Structural Backlog (deferred, non-blocking)

Cleanups identified during `PRE_FEATURE_REPO_CONSOLIDATION_V1` that are **real but
deliberately deferred** — each needs a scoped phase with characterization tests,
not a quick patch. **None block `ALPHA_FEATURE_LABEL_FOUNDATION_V1`.** See also
`docs/harness/HARNESS_NOTES.md` for the harness-code backlog.

## 1. Finish the provider-boundary extraction (high value)

Seven Databento modules (`register_dataset`, `canonicalize`, `dense_grid`,
`coverage`, `compare_sources`, `metadata_ingest`, `manifest_files`) import
provider-neutral private helpers — `_repo_root`, `_validate_data_root`,
`_load_calendar`, `_settings_for_symbols`, `_partition_plan`, `_expected_intervals`
— from `data/ibkr/materialize.py`. So the PRIMARY provider (Databento) cannot import
without IBKR being importable. Round 1 fixed the `json_ready` half of this leak; this
half remains.

A clean fix moves a **~300-line closure** (the `InstrumentSettings` dataclass,
`_instrument_entries`, `_trading_sessions_for_window`, the calendar dataclasses /
overrides / constants) into `data/foundation/`, **and parameterizes the
IBKR-flavored defaults** in `_settings_for_symbols` (`inst_ibkr_…` / `series_ibkr_…`).
That is a redesign of the live canonicalization pipeline, so it needs its own phase
with characterization tests. A partial move would leave an inconsistent split and is
not recommended.

## 2. Legacy `data/*` vs canonical `data/foundation/*` (documented; consolidation deferred)

Two data layers coexist: the older ASV1 flat layer (`data/contracts.py::OneMinuteBar`,
`data/versions.py::DatasetVersion`, `data/sessions.py`) and the ADF1 canonical layer
(`data/foundation/{bars,quotes,datasets,sessions}`). **Feature/Label work should use
the canonical `data/foundation/*` layer** (see `docs/FEATURE_LABEL_FOUNDATION_ENTRY_CONTRACT.md`).
Consolidating the two `DatasetVersion` definitions is behavior-bearing — both are wired
(`data/versions.py` into `cli/data.py` + adapters) — so it is deferred.

## 3. Smaller items

- `core/instrument_master.py` imports `data.contracts` — a `core` → `data` inverted
  dependency (provider-agnostic, so not a provider leak, but a layering smell).
- Long files to split when authorized: `data/foundation/datasets.py` (~3.2k LOC),
  `requests.py`, `instruments.py`, `bars.py`; `data/ibkr/{materialize,backfill}.py`;
  `data/databento/{register_dataset,coverage}.py`.
- Optional test merge: the six `*_no_tradability_claims` / `*_prohibited_claims`
  modules could parameterize into one (coverage-preserving); left as-is this pass.

## 4. `FEATURE_LABEL_PARQUET_SINK_V1` (deferred follow-up; see ADR-0006)

Feature/label materialization writes deterministic JSONL (`values.jsonl`) — the
audit/small tier of [ADR-0006](../decisions/0006-feature-label-value-storage.md).
The intended research-scale tier is local Parquet (read via DuckDB/Polars), and
it is **not** implemented. A scoped follow-up should:

- write feature/label values to local Parquet under `ALPHA_DATA_ROOT` through the
  existing optional-dependency pattern (`require_dependency("polars")` /
  `_optional_module("pyarrow")`), keeping JSONL as the small/audit tier;
- record a `parquet_path` pointer (alongside the optional jsonl path),
  `value_count`, content hash, and schema version in `features.sqlite` /
  `labels.sqlite` registry records;
- generalize the JSONL-only reader gate at `features/reports.py:865`
  (`UNSUPPORTED_MATERIALIZATION_FORMAT`) to accept Parquet;
- add synthetic-fixture tests (tiny tmp_path Parquet; no committed binaries).

It should land before any large-scale, value-consuming Agent Factory study.
Until then, multi-year value matrices should not be forced through JSONL.

## 5. Dataset registry does not persist quality/coverage reports (coupling gap)

`persist_dataset_version` stores only the quality/coverage **hashes** in
`datasets.sqlite` (`metadata_json`), not the report objects, and
`resolve_dataset_version` returns only the `DatasetVersion`. Because
`require_versioned_prerequisites` requires a `DataQualityReport` that reproduces
the stored hash, an accepted DatasetVersion **cannot be re-resolved** for
downstream feature/label materialization without re-supplying its original
reports (which are not stored). The seed materialization operator works around
this by deriving and running the real quality/coverage builders over exactly the
materialized partition and constructing the consumption handle directly. A clean
fix would persist the reports (or add a `load_accepted_dataset_version` /
report re-derivation helper) so the registry-resolve path works end to end. This
is data-foundation scope; see ADR-0006 §4.

## 6. Reference-engine label families have no parallel throughput path (post-LCFP)

The accepted LCFP per-family engine policy keeps `fixed_extended`, `close_out`,
and `cost_adjusted` on the per-row reference engine because the P08 benchmark
measured reference faster than the V1 fast pack for those families (best fast
cells 0.55x / 0.40x / 0.72x; profile: per-row cost-kernel Decimal arithmetic +
record validation + value-store writes, not vectorizable panel math). Reference
compute for those families is currently **single-threaded per family** — fine
for year-appends (~minutes) but slow for any future full-window backfill or new
cost-label/index grids (FUTSUB-P19's historical tail ran ~2-3h).

If reference-family throughput becomes a real bottleneck again (new cost
profiles, new derived indexes, large backfills), two recorded upgrades, in
preference order:

1. **Unit-level parallelism for the reference engine** (cheap, semantics-safe):
   reuse the LCFP-P06 worker pattern — parallelize compute over independent
   `label_group x symbol x dataset_version/year` units with the existing single
   serial keystone registry writer; same engine, same code, no parity re-proof
   needed. Expect ~6-7x at 8 workers on the unit grid.
2. **Cost-kernel vectorization to make V1 win** (riskier): batch
   Decimal-or-float cost arithmetic + batched LabelValueRecord validation in
   the fast pack; requires fresh parity + benchmark gate before the per-family
   policy flips (precision semantics feed the truth chain).

Trigger: adopt (1) the first time a reference-family materialization is
projected > ~1h wall-clock. Evidence basis:
`research/label_compute_fast_path_v1/benchmark/benchmark_summary.md`,
`reviews/LABEL_COMPUTE_FAST_PATH_V1/P172002_LCFP_P08_PANEL_CACHE_SPEEDUP-review.md`.
