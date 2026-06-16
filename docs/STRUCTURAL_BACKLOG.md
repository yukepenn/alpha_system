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

Status as of RLPC-P04: option 1 was delivered as engineering but
**NOT_RELEASED as production policy**. RLPC-P01/P02 landed an explicit opt-in
unit-parallel reference-worker path with parity, resume, and single-writer
guards; default reference workers remain 1. RLPC-P03 then measured the bounded
real `cost_adjusted` ES/2024 grid and recorded `NOT_RELEASED`: workers=8 reached
2.14x versus workers=1, below the 3.0x release gate. Evidence:
`research/reference_label_parallel_compute_v1/benchmark/benchmark_summary.md`.

The accepted LCFP per-family engine policy keeps `fixed_extended`, `close_out`,
and `cost_adjusted` on the per-row reference engine because the P08 benchmark
measured reference faster than the V1 fast pack for those families (best fast
cells 0.55x / 0.40x / 0.72x; profile: per-row cost-kernel Decimal arithmetic +
record validation + value-store writes, not vectorizable panel math). Reference
compute for those families is currently **single-threaded per family** — fine
for year-appends (~minutes) but slow for any future full-window backfill or new
cost-label/index grids (FUTSUB-P19's historical tail ran ~2-3h).

If reference-family throughput becomes a real bottleneck again (new cost
profiles, new derived indexes, large backfills), the recorded status is:

1. **Unit-level parallelism for the reference engine** (cheap, semantics-safe):
   delivered as an opt-in path (`--workers` / `ALPHA_LABEL_CPU_WORKERS`) but not
   adopted as FUTSUB or production policy. The RLPC-P03 sweep measured workers
   1/2/4/8 at 1.00x / 1.36x / 1.83x / 2.14x on the same 9-unit bounded real
   grid, with determinism PASS at every worker count and production registry
   delta 0. Because workers=8 missed the 3.0x release gate, reference-family
   policy remains serial/default workers=1.
2. **Cost-kernel vectorization to make V1 win** (riskier): batch
   Decimal-or-float cost arithmetic + batched LabelValueRecord validation in
   the fast pack; requires fresh parity + benchmark gate before the per-family
   policy flips (precision semantics feed the truth chain). This stays backlog
   as the standing escalation. The next attempt must account for the measured
   RLPC-P03 ceiling: parent-side serial registration was 86.077229 s,
   86.172520 s, and 90.097791 s at workers 2/4/8 versus 3.515340 s at workers=1,
   while worker compute fell from 526.587762 s to 157.706309 s.

Original evidence basis:
`research/label_compute_fast_path_v1/benchmark/benchmark_summary.md`,
`reviews/LABEL_COMPUTE_FAST_PATH_V1/P172002_LCFP_P08_PANEL_CACHE_SPEEDUP-review.md`.

## 7. Session 2026-06-15 deferred defects (recorded, not yet fixed)

Surfaced while auditing the runner rail after the broad-mining-readiness gates
landed. Each is **deferred, not blocking** — recorded here by SYMBOL (cite the
symbol, not just the line, which drifts). Code fixes are out of scope for the
artifact-consolidation doc pass; this is the recording. None weakens a guard.

1. **`research_lane/verdict_report.py::_n_eff_mde` — untyped MDE-spelling fallback.**
   `_n_eff_mde` (verdict_report.py:355) still resolves the detectable-effect via a
   `detail.get('minimum_detectable_effect')` / `minimum_detectable_abs_ic` spelling
   fallback (see the comment at :360-364). This is the same untyped-seam class as
   `FAST_READOUT_CONTRACT_V1` (the gate detail is a dict glue seam consumed by
   string-spelling). Fix = type the gate-detail seam and use one canonical accessor;
   do not add a third spelling.

2. **`research_lane/mining_driver.py` — hardcoded pool literals.** mining_driver.py:593
   hardcodes `"pool_kind": "cross_symbol"` and :596 `"horizons": ["120m"]` in the
   pooled-result assembly. These should derive from the idea / SliceSpec, not be
   pinned literals — a single non-`cross_symbol` / non-`120m` idea would silently
   mislabel its pool. Fix = thread the real pool_kind/horizons from the resolved
   partitions.

3. **`governance/canaries/registry_event_ts_grid.py::id_prefix` — `cost_adjusted`
   family has an empty `id_prefix`.** The canary's `EventTsGridCase.id_prefix`
   (registry_event_ts_grid.py:30) gates registration-id/pack-id matching (:40-42).
   The `bbo_tradability_` case (:121) sets a prefix but the `cost_adjusted` family
   case (:130) has no matching `id_prefix`, so its prefix guard is effectively a
   no-op. Fix = give `cost_adjusted` a real `id_prefix` so the guard actually binds.

4. **`research/conditional_probe.py::_continuous_label_value` — silent drop on
   unparseable values.** `_continuous_label_value` (conditional_probe.py:803, used at
   :323/:824/:825/:859) returns `None` for unparseable label values; downstream the
   `None` is dropped silently rather than surfaced as a typed coverage/DATA_GAP
   signal, so a partially-unparseable slice can quietly shrink n without a recorded
   reason. Fix = count and surface dropped values (coverage telemetry), don't
   swallow them.

5. **mine-vs-run resolver split** (`research_lane/partition_resolver.py::resolve_partition_slice`
   at :280 / `resolve_partition_setup` at :454 vs the embedded-slice path used by
   `alpha idea run`). `alpha idea mine` resolves partitions by registry
   `feature_id`/`label_id` (unambiguous, per-partition), while `alpha idea run`
   carries an embedded SliceSpec with pinned hashes. The two resolution vocabularies
   are a known two-path hazard (the broader two-vocabulary `from_mapping` debt noted
   in memory). Fix = converge on the registry-keyed resolution as the single path or
   document the split as intentional with a guard; recorded as a question, not a
   delete.

6. **`research/first_light.py` manifest path literal** (`"values.parquet.manifest.json"`
   at first_light.py:55/63/70, schema `FIRST_LIGHT_SCHEMA`). The manifest filename is
   a hardcoded literal. Per the current ground truth this path is **KEEP-INTENTIONAL**
   (it is a deliberate, code-referenced manifest pointer, caught once before as a
   false "safe to change" target). Recorded here only as a **question to revisit if
   the manifest convention is ever centralized** — do NOT delete or relocate it on
   suspicion (uncertain ⇒ keep).
