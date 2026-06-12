# Adversarial Review: P085900_CALIBRATION_STAGING_INTEGRITY

- Campaign: FUTSUB_KILLSHOT_READINESS_OPS_V1
- Phase: P085900_CALIBRATION_STAGING_INTEGRITY (declared factor, fver-filtered, hash-verified staging)
- Reviewer: fresh adversarial Claude (WF1), worktree `alpha_system-wf1-staging-integrity`, branch `wf1/staging-integrity`, reviewed commit `f7869a1`
- Diff reviewed: `git diff origin/main` — 6 files, +1523/-133 (tool +782/-133; `feature_lock_validation.py` +125; `surrogate_run.py` +20; test file +499; spec + handoff)
- Verdict: **PASS_WITH_WARNINGS**

## What this phase had to make impossible

1. Factor chosen as `sorted(candidates)[0]` over ALL sspec feature locks (the
   "vwap" calibration staged `session_calendar_roll_minutes_to_roll`).
2. Whole-Parquet loads with no fver filter and no content-hash check (clobbered
   2019 bbo packs silently staged `spread_zscore` values stamped
   `bad_quote_flag`).

Both classes are now structurally closed. Evidence below.

## 1. ONE TRUTH — runtime StudyConfig path (PASS)

- `surrogate_run.py` diff is purely additive (+20): `_study_config_for_surrogate`
  now delegates verbatim to the new public `study_config_for_surrogate_scope`;
  the payload-construction body is the same physical lines (context-only in the
  diff). `run_surrogate_study` behavior is identical pre/post refactor.
- Existing runtime tests untouched (`git diff origin/main --name-only -- tests/`
  shows only the tool test changed) and green:
  `tests/unit/governance/test_surrogate_run.py` → 20 passed.
- The tool routes every staged sub-config through the genuine runtime
  constructor: `_runtime_factor_id` reads the staged spec's `surrogate_fdr`
  scope via `study_config_for_surrogate_scope(...).factor_id` and fails closed
  (`runtime_factor_id_mismatch`) if it differs from the lock's `feature_id`.
- No second derivation rule remains: the old `_feature_lock_sort_key` heuristic
  is DELETED; remaining `sorted()` calls in the tool are error-message
  formatting (:396) and fail-closed file enumeration that raises on >1 record
  (:879). There is no ordering-based factor choice anywhere — ALL declared
  factors in the under-test family are staged, so there is no "choice" to get
  wrong.
- Caveat (W1): the runtime probe is partially self-referential.
  `_surrogate_study_spec` writes `surrogate_fdr.factor_id` from the resolved
  registry record, which `_assert_feature_record_factor` already forces equal
  to the lock. So the probe only detects normalization drift inside the runtime
  constructor, not an independent re-derivation. This is acceptable because the
  runtime itself has no StudySpec→factor rule other than reading the
  `surrogate_fdr` scope (`_surrogate_scope` confirmed); the genuine integrity
  guarantee is structural (stage-all + fail-closed), and the probe pins the
  constructor in the loop. Noted, not blocking.

## 2. "One non-support feature family" rule (PASS with warnings)

- `_declared_feature_family`: derives the under-test family as the unique
  non-support `feature_family` among `feature_pack_locks`; fail-closed BOTH
  ways (`declared_factor_family_missing` / `declared_factor_family_ambiguous`).
  Support set = `{base_ohlcv, session_calendar_maintenance}` plus
  `session_calendar*` prefix — the original failure (staging a
  `session_calendar_roll_*` feature for a vwap study) is now structurally
  impossible: those locks are excluded as support, and any residual ambiguity
  refuses rather than picks.
- Verified against the committed sspecs directly: each of the six rerun sspecs
  carries exactly three lock families (`base_ohlcv`,
  `session_calendar_maintenance`, plus exactly one under-test family:
  `vwap_session_auction` / `regime_volatility_compression` /
  `liquidity_sweep_pa_structure` x2 / `bbo_tradability_top_book`).
- The six-spec test (`test_real_surrogate_declared_factor_resolution_for_six_rerun_specs`)
  asserts the ACTUAL factor-id tuples per sspec (vwap sspecs → the 6
  vwap_session_auction factors, bbo sspec → the 11 `bbo_tradability_*`
  factors), not just "no exception", plus sub-config counts =
  len(label_locks) x len(factors). It PASSED locally during this review.
- **W2**: the tool never consults or cross-checks the sspec's explicit
  `dataset_scope.family` (present in all six: `vwap_session`,
  `bbo_tradability`, `regime`, `liquidity_pa`, `cross_market`). No trivial
  prefix rule exists (`liquidity_pa` vs `liquidity_sweep_pa_structure`), so the
  omission is defensible, but a residual hole remains: a FUTURE sspec whose
  true under-test family is in the hardcoded support set while carrying exactly
  one other non-support family would be silently mis-resolved with no error.
  For the six committed sspecs the pinned test forecloses this. Recommend a
  follow-up: explicit scope.family → lock-family mapping cross-check.
- **W3**: the six-spec test is gated behind
  `skip_unless_local_registry(.../registry/features.sqlite)` yet reads only
  committed JSON files — it silently skips in CI and only runs where private
  local data exists. The spec sanctioned the skip idiom, but as written the
  gate is vestigial; removing it would let CI pin the six factor sets.

## 3. Hash verification (PASS with warning)

- `_load_value_rows` calls
  `verify_registered_value_store_content_hash(record, ...)` BEFORE loading any
  rows. Mismatch raises `FeatureLockValidationError` naming path + expected +
  actual hashes. The refusal fixture
  (`test_real_surrogate_calibration_refuses_value_hash_mismatch`) exists and
  passes; mutation B (below) proves it is load-bearing.
- What is hashed: for JSONL the helper RECOMPUTES
  `compute_value_content_hash` over the actual file rows (true content hash).
  For Parquet/Dual it reads `content_hash` from the sidecar manifest written
  atomically by `write_parquet_values` and compares to the registry's
  `value_content_hash`. The live clobber class (re-materialization, e.g. the
  2026-06-12T02:01Z spread_zscore overwrite of 2019 bbo packs) rewrites the
  sidecar with the new content hash → caught.
- **W4 (vacuous-pass subclass)**: for Parquet the "actual" hash is NOT
  recomputed from the parquet rows; a parquet file replaced WITHOUT touching
  its sidecar manifest passes the hash check vacuously. Two independent nets
  reduce this: (a) the new fver/lver row filter — a foreign pack's rows carry a
  different version id, so staging fails closed with
  `locked_value_rows_not_found`; (b) `_assert_record_matches_lock` /
  `_assert_feature_record_factor` pin the registry record to the lock. A
  same-fver row-content corruption with a stale sidecar would still slip
  through. Recommend follow-up: recompute
  `compute_value_content_hash(load_parquet_values(path))` for Parquet stores.
- Required-field guards (`_required_text`) prevent empty-hash vacuous passes;
  missing registry hash or manifest hash fails closed.

## 4. fver/lver filtering (PASS)

- `_filter_rows_by_version` filters staged rows by the locked
  `feature_version_id` / `label_version_id`; rows missing the version field
  fail closed (`value_row_version_field_missing`); zero matching rows fail
  closed (`locked_value_rows_not_found`).
- Multi-fver Parquet fixture
  (`test_real_surrogate_calibration_filters_locked_versions_from_parquet`)
  proves only declared-version rows are staged, for features AND labels, and
  pins the staged/total counts in the rendered report
  (`6/12`-style assertions). Mutation C proves it is load-bearing.
- Partition/data-version scope is enforced one level up:
  `_assert_record_matches_lock` requires the resolved record's
  `dataset_version_id` and `partition_id` to equal the lock before any load.

## 5. Mutation tests (all KILLED, tree restored)

| Mutation | Change | Expected killer | Result |
|---|---|---|---|
| A | `_declared_feature_family`: raise only when empty, `return sorted(candidate_families)[0]` on ambiguity | ambiguity test | **KILLED** — `test_..._refuses_ambiguous_declared_factor_family` FAILED (:497) |
| B | `verify_registered_value_store_content_hash`: mismatch raise disabled (`if False and ...`) | hash-mismatch test | **KILLED** — `test_..._refuses_value_hash_mismatch` FAILED (DID NOT RAISE, :437) |
| C | `_filter_rows_by_version`: early `return [dict(row) for row in rows]` | multi-fver test | **KILLED** — `test_..._filters_locked_versions_from_parquet` FAILED (staged count, :372) |

Each mutation was applied alone, run against the focused test file
(remaining 7 tests stayed green each time, confirming the kill is the targeted
test), then restored via `git checkout --`. Final `git status --short` clean;
focused suite re-run green (8 passed) on the restored tree.

## 6. Rescore mode (PASS, minor note)

- `test_real_surrogate_calibration_rescores_existing_seed_outputs` and the
  missing-summary error test pass. Fresh-vs-rescore result equality holds under
  the new multi-spec seed grid (verified `calibrate_surrogate_fdr` seeds
  `base + spec_index*budget + run_index` and the tool offsets configs by
  `n_specs*budget` — the rescore reconstruction matches exactly).
- Rescore is subject to the same declared-family derivation (it runs BEFORE the
  rescore branch), so ambiguous/missing-family sspecs fail closed in rescore
  mode too. Rescore stages no values, so hash/fver checks are N/A by design;
  it reuses only the derived sub-config count for seed-grid parity.
- **W5 (minor)**: namespaces produced by the PRE-fix tool use the old
  single-spec seed grid and will not rescore cleanly under the new grid
  (missing-seed error rows → BLOCKED). Acceptable — those namespaces are
  exactly the invalid wrong-factor runs this phase exists to invalidate.

## 7. Scope, artifact policy, handoff truthfulness (PASS)

- Changed files: spec, handoff, `feature_lock_validation.py` (+125, all
  additive: verification helper + dataclass), `surrogate_run.py` (+20, pure
  extraction), tool, tool test. No `features/**`, `labels/**`, `runtime/**`
  behavior changes; `detection_statistic`, diagnostics join semantics,
  perturbation writers, and gates untouched.
- `git ls-files runs` → empty. No runtime artifacts staged. Research-only
  language throughout; report remains value-free (ids, counts, seeds,
  verdicts; off-grid event_ts surfaced as counts only).
- Handoff claims re-run and ALL verified in this worktree
  (`PYTHONPATH=$PWD/src`):
  - focused tool tests: **8 passed** (claimed 8)
  - `tests/unit/governance tests/unit/discovery_rigor_floor`: **681 passed** (claimed 681)
  - `tests/unit/research`: **6 passed** (claimed 6)
  - `canary_runner.py`: **25 PASS** (claimed 25, "All Frontier canaries passed")
  - `verify.py --smoke`: exit 0
  - `just ci-parity`: **3306 passed, 77 skipped** (claimed 3306/77)
- Handoff's six-sspec factor tables match the committed sspec JSONs (checked
  directly against `research/futures_substrate_scaleout_v1/rerun/study_specs/`).

## Minor notes (non-blocking)

- Dead branch in `_load_value_rows`: the inner
  `if not record.parquet_path: raise` is unreachable under the outer condition.
- Spec front-matter still says `status: in_progress` — coordinator bookkeeping.
- `_off_grid_event_ts_count` counts over staged (post-filter) label rows; the
  spec asked to surface off-grid event_ts for locked packs — counts-only and
  adequate for the stated diagnostic purpose.

## Verdict

**PASS_WITH_WARNINGS** — both live defect classes are structurally closed and
mutation-proven; warnings W2 (no dataset_scope.family cross-check), W3
(six-spec regression test skipped in CI), and W4 (Parquet hash trusts sidecar
manifest; recommend recomputing from rows) are recorded for follow-up and do
not block: each residual hole is covered by at least one independent
fail-closed net for the committed rerun sspecs.
