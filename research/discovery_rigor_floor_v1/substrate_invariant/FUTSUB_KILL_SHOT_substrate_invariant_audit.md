# FUTSUB Kill-Shot Substrate-Invariant Audit (Live Registries)

- Date: `2026-06-12`
- Auditor: coordinator-dispatched read-only audit
- Closes: `research/discovery_rigor_floor_v1/KILL_SHOT_READINESS.md` row 9;
  `handoffs/DISCOVERY_RIGOR_FLOOR_V1/FUTSUB_KILL_SHOT_RESUME.md` step 7
- Run context: repo `main` @ `fe3f652`; `ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system`;
  FUTSUB run `2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
  remains STOPPED before P28; this audit performed zero writes to registries,
  values, run state, or git (the only write is this artifact file).
- Registries audited (read-only, `sqlite3.connect("file:...?mode=ro", uri=True)`
  via `~/.venvs/alpha_system_research/bin/python`):
  - `$ALPHA_DATA_ROOT/registry/features.sqlite` (2072 `feature_registry_records` rows)
  - `$ALPHA_DATA_ROOT/registry/labels.sqlite` (2373 `label_registry_records` rows)
  - `$ALPHA_DATA_ROOT/registry/datasets.sqlite` (29 `dataset_versions` rows)
- Lock corpus: all 10 committed re-locked StudySpecs under
  `research/futures_substrate_scaleout_v1/rerun/study_specs/*.json`
  (4560 feature pack locks, 840 label pack locks, 24 distinct locked
  DatasetVersions). The 6 kill-shot rerun candidates are
  `sspec_652fcc23a6f725b405612b8e`, `sspec_676a012a4a4cdf3d169cd981`,
  `sspec_1d87dfbe3d24810720f75014`, `sspec_c2114a3c6c90595350151af0`,
  `sspec_950ad6bb7063928d9ff8ea4f`, `sspec_6088f0ed5b02b161bfb54943`.
- This file is value-free: statuses, counts, ids, schema/column names, issue
  codes, commands, and code citations only. No feature, label, return, market,
  signal, or cost values appear here.

## Predicate 1 — No constant-valued flag columns: PASS

Scope: schema columns of the registry metadata record tables in the three
live registries (not value payloads). Flag-like = column name matching
`^is_|_flag$|^has_|_enabled$` or boolean-typed columns.

Method: `PRAGMA table_info` over every table in `datasets.sqlite`,
`features.sqlite`, `labels.sqlite`; for each flag-like column with rows,
`SELECT COUNT(DISTINCT col)`.

Evidence:

- Flag-like columns found: exactly one name, `git_dirty` (boolean-intent
  `INTEGER`), present in 8 `datasets.sqlite` tables (`factor_versions`,
  `factor_validation_runs`, `label_versions`, `study_runs`,
  `strategy_versions`, `grid_runs`, `ml_runs`, `backtest_runs`).
  All 8 tables have 0 rows -> not evaluable for constancy, no finding.
- `features.sqlite.feature_registry_records` and
  `labels.sqlite.label_registry_records` contain no `*_flag` / `is_*` /
  boolean-typed columns.
- Issue code `constant_flag_column`: 0 occurrences.

Supplementary (status-like enum columns, reported for transparency, not
flag-like): `feature_registry_records.lifecycle_state` distinct=2 (1312 + 760
rows), `duplicate_exposure_status` distinct=2 (1980 + 92);
`label_registry_records.lifecycle_state` distinct=2 (1368 + 1005),
`exposure_status` distinct=3 (2356 + 14 + 3). `value_store_format` is
single-valued (`parquet`) across both record tables by current storage policy
(ADR-0006 successor state); it is a format enum, not a flag, and is not a
`constant_flag_column` finding.

## Predicate 2 — >=2 session values per trading day: PASS

How session labels are recorded (verified in code before measuring):

- The canonical-parquet column `session_label` is a per-partition dataset
  coverage descriptor copied from pull settings at canonicalization
  (`src/alpha_system/data/databento/canonicalize.py:449` sets
  `foundation_session_label = settings.session_label`; `:485` writes it to
  every `CanonicalBarRecord`). It is constant within a partition by
  construction and is NOT per-bar session truth. Structural check confirmed:
  distinct count = 1 on every canonical partition (vocabulary drawn from
  `SUPPORTED_SESSION_TYPES`, `src/alpha_system/data/foundation/sessions.py:56-63`).
  This constancy is by documented construction, not a substrate defect.
- Per-bar session truth is timestamp-derived through the session template
  clock (`src/alpha_system/features/session_truth.py`;
  `load_session_template_by_id` -> template
  `session_cme_index_futures_eth`, timezone `America/Chicago`). The producer
  classifier is `_template_session_label`
  (`src/alpha_system/features/fast/vwap_session_auction.py:645-648`,
  built on `_is_rth` at `:638-642`), a 2-way vocabulary.
- Registry side: session-conditioned records declare the role through
  `feature_spec.inputs.input_metadata.field_roles.session_label =
  SESSION_METADATA` or the `session_metadata_role` marker (consumed at
  `src/alpha_system/runtime/input_resolver.py:1811-1846`).

Verification performed (counts only, no value reads — only the structural
`bar_start_ts` column was read from canonical parquet):

1. Registry metadata check over the 6 kill-shot StudySpecs: 3408 feature pack
   locks resolved against `feature_registry_records`; 2208 of them declare
   `session_label` as an input field and 2208/2208 carry the
   `SESSION_METADATA` role marker (0 unmarked). Per spec
   (locks / session-declaring / role-marked): `sspec_1d87dfbe…` 504/264/264,
   `sspec_6088f0ed…` 648/264/264, `sspec_652fcc23…` 528/384/384,
   `sspec_676a012a…` 528/384/384, `sspec_950ad6bb…` 600/456/456,
   `sspec_c2114a3c…` 600/456/456.
2. Structural per-trading-day check over every canonical partition locked by
   the 6 kill-shot specs (24 DatasetVersions x 3 roots = 72 partitions,
   23,216,215 rows scanned via `polars.scan_parquet`, column `bar_start_ts`
   only): trading day assigned with the repo's own clock
   (`America/Chicago` local + 7h date, i.e. evening bars roll to the next
   trading day), session class derived with the repo's own
   `_template_session_label` expression.
   - Trading-day cells evaluated: 17,073
   - Cells with distinct derived-session count >= 2: 17,055
   - Cells with distinct count < 2: 18 (issue code
     `single_session_holiday_cell`, informational) — confined to exactly 3
     exchange-calendar dates, each affecting the 6 sparse (non-dense)
     partitions of its year: `2021-04-02`, `2023-04-07` (Good Friday
     holiday sessions), `2025-01-09` (special market-closure date). Dense
     `ohlcv_1m_dense` partitions exclude these dates entirely (0 such cells).
   - Global distinct derived-session vocabulary count: 2.

Verdict: every regular trading day in every kill-shot-locked partition shows
exactly 2 distinct session values; the only sub-2 days are exchange-calendar
holiday/closure sessions, which are calendar truth rather than substrate
degeneracy. PASS.

## Predicate 3 — Role-marker WARN documented: WARN (tolerated, re-verified)

Known WARN re-verified against the live `features.sqlite`:

- Current count: exactly **648** `feature_registry_records` rows carry no
  `field_roles` and no `session_metadata_role` marker anywhere in their
  metadata (`feature_spec.inputs.input_metadata`, `registry_metadata`,
  `feature_spec.contract_metadata`). Breakdown by `lifecycle_state`:
  552 `REGISTERED` + 96 `DEPRECATED`. This matches the previously recorded
  WARN count of 648. Issue code: `missing_field_roles_legacy_rows`.
- All 648 rows declare **no** `session_label` (or other session) input field,
  so no role marker is semantically required for them.
- A further 96 rows DO declare `session_label` without any role marker; all
  96 are `DEPRECATED` (0 `REGISTERED`) and none is referenced by any
  committed lock (see Predicate 4). These are the superseded pre-marker
  counterparts noted in
  `reviews/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/P022000_FUTSUB_RELOCK_RERUN-review.md:88-90`.
- `label_registry_records` carry no `field_roles` by design (2373/2373);
  `field_roles` is a feature-input concept consumed only on the feature side
  of the resolver.

Why tolerated (code path): the resolver falls back to an empty role map when
`field_roles` is absent —
`src/alpha_system/runtime/input_resolver.py:1824-1828`
(`_field_roles_from_metadata` returns `{}` when the key is missing or not a
mapping), assembled in `_field_roles_from_record` at `:1811-1821`. With an
empty role map the name-based fail-closed guard still applies
(`_looks_like_label_feature_field` at `:1795-1808` rejects label-like fields
via `_reject_label_as_live_feature` at `:1214-1240`), and the session
exemption at `:1870-1895` is only granted when an explicit `SESSION_METADATA`
role is present. Markerless legacy rows therefore get strictly LESS
permission, never more; the 96 markerless session-declaring rows would
fail-close if resolved, and they are additionally unreachable because all
committed locks point at marker-carrying `REGISTERED` records.

Status: WARN, documented and tolerated; count unchanged at 648.

## Predicate 4 — Zero locks referencing DEPRECATED records: PASS

Status vocabulary (from registry code): feature lifecycle =
`{REGISTERED, DEPRECATED}` (`src/alpha_system/features/registry.py:68-72`);
label lifecycle = `{REGISTERED, DEPRECATED}`
(`src/alpha_system/labels/registry.py:64-69`); deprecations also mirrored in
`feature_deprecation_records` / `label_deprecation_records`. Dataset
acceptance vocabulary observed in `dataset_versions.metadata_json
.dataset_acceptance_lock.state`: `{ACCEPTED, ACCEPTED_WITH_WARNINGS, BLOCKED}`
(plus 2 legacy rows without an acceptance lock).

Method: extracted every `feature_version_id`, `label_version_id`, and
`dataset_version_id` lock from all 10 committed re-locked StudySpecs and
joined each against the live registries (read-only).

Evidence:

- Feature locks checked: 4560/4560 resolve to live `feature_registry_records`
  rows with `lifecycle_state = REGISTERED`; 0 `DEPRECATED`; 0 unresolved;
  0 present in `feature_deprecation_records` (760 deprecation rows exist in
  the registry, none referenced by any lock).
- Label locks checked: 840/840 resolve to `lifecycle_state = REGISTERED`;
  0 `DEPRECATED`; 0 unresolved; 0 present in `label_deprecation_records`
  (1005 deprecation rows exist, none referenced).
- DatasetVersion locks: 24/24 distinct locked `dataset_version_id`s resolve in
  `dataset_versions`; acceptance-state census of the locked set: 19
  `ACCEPTED` + 5 `ACCEPTED_WITH_WARNINGS`; 0 `BLOCKED`; 0 missing-lock; and
  0 mismatches between each spec's recorded `acceptance_state` and the live
  registry state. The registry's 2 `BLOCKED` and 2 no-acceptance-lock
  DatasetVersions are not referenced by any committed lock.
- Issue codes `feature_lock_lifecycle_DEPRECATED`,
  `label_lock_lifecycle_DEPRECATED`, `*_lock_in_deprecation_table`,
  `*_unresolved`, `dataset_version_blocked`: 0 occurrences each.

## Roll-Up

| # | Predicate | Status | Key counts | Issue codes raised |
|---:|---|---|---|---|
| 1 | No constant-valued flag columns | `PASS` | 1 flag-like column name (`git_dirty`) across 8 tables, all 0-row; 0 constant flag columns in populated record tables | none (`constant_flag_column`: 0) |
| 2 | >=2 session values per trading day | `PASS` | 2208/2208 kill-shot session-declaring locks role-marked; 17,055/17,073 trading-day cells with 2 distinct derived sessions; 18 holiday/closure cells on 3 calendar dates; vocabulary count 2 | `single_session_holiday_cell`: 18 (informational, exchange calendar) |
| 3 | Role-marker WARN documented | `WARN` (tolerated) | 648 legacy rows without `field_roles` (552 REGISTERED + 96 DEPRECATED, none session-declaring); 96 markerless session-declaring rows all DEPRECATED and lock-unreferenced | `missing_field_roles_legacy_rows`: 648 |
| 4 | Zero locks referencing DEPRECATED records | `PASS` | 4560 feature + 840 label locks all `REGISTERED`; 24/24 DatasetVersions `ACCEPTED`/`ACCEPTED_WITH_WARNINGS`; 0 deprecated/unresolved/blocked references | none |

Overall: GREEN (PASS, PASS, WARN-documented-tolerated, PASS). No FAIL. The
single WARN is the pre-existing, re-verified 648-row legacy role-marker gap,
tolerated by the resolver's strictly-less-permissive fallback cited above.

## Reproduction Notes

All registry reads used read-only URIs
(`sqlite3.connect("file:<db>?mode=ro", uri=True)`) under
`~/.venvs/alpha_system_research/bin/python`; lock extraction read the 10
committed JSON StudySpecs; the only data-file reads were
`polars.scan_parquet(...).select(["bar_start_ts"])` over the canonical
partitions of the 24 kill-shot-locked DatasetVersions under
`$ALPHA_DATA_ROOT/databento/canonical/glbx_mdp3/<dsv>/schema=*/root=*/`,
plus one one-row schema probe (`pyarrow.parquet.read_schema`) on one feature
and one label values parquet to confirm payload columns were never read.
Session classification reused the repo's own
`alpha_system.features.fast.vwap_session_auction._session_clock` /
`_template_session_label` expressions.

## Attestation

This artifact is value-free: it contains statuses, counts, identifiers,
schema/column names, calendar dates, issue codes, commands, and code
citations only. No feature values, label values, returns, prices, spreads,
signals, or cost numbers were read into this audit's outputs or are recorded
here. No alpha, profitability, tradability, execution-quality, or
production-readiness claim is made.
