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
