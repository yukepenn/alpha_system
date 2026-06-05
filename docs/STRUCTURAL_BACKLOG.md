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
