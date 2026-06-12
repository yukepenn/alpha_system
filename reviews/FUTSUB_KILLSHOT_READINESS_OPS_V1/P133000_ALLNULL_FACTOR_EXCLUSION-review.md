# Adversarial Review: P133000_ALLNULL_FACTOR_EXCLUSION

- Campaign: `FUTSUB_KILLSHOT_READINESS_OPS_V1`
- Phase: `P133000_ALLNULL_FACTOR_EXCLUSION`
- Branch: `wf1/allnull-factor-exclusion` (commit `a95d719`, one ahead of `origin/main`)
- Reviewer: fresh adversarial Claude review (Workflow 1)
- Date: 2026-06-12
- Stance: prime risk = integrity weakening — this phase relaxes a fail-closed
  staging check (`non_numeric_feature_pack_for_surrogate`) into a recorded
  exclusion. The review's job was to prove real defects (hash mismatch, missing
  fver, mislabeled data) cannot slip through as "exclusions".

## Verdict

**PASS_WITH_WARNINGS**

The implementation is correct and integrity-preserving — verified by code
trace AND by direct runtime probes, not just by the shipped tests. However,
two of the three required mutation kills FAILED at the test-suite level
(details below): the hash-mismatch-refusal test is `polars`-gated and skips in
every enforced environment, and no test pins the not-all-null boundary. Both
survived mutations are test-coverage gaps, not code defects; the prime-risk
properties themselves were proven by direct probes during this review. The
hash-test skip is pre-existing on `origin/main`, not introduced by this diff.

## MUST-CHECK results

### 1. Exclusion scope is EXACTLY all-null, ordered AFTER integrity checks — PASS

Verified order in `tools/discovery_rigor_floor/run_real_surrogate_calibration.py`:

1. `_resolve_records` (lines ~623–670): resolver lock matching, registry
   record presence (`resolved_pack_record_missing`), record-vs-lock assertion,
   factor-id assertion — all raise before any staging.
2. `_materialize_factor_jsonl` line ~680: `_load_value_rows` calls
   `verify_registered_value_store_content_hash` FIRST
   (`src/alpha_system/governance/feature_lock_validation.py:191`) — raises
   `FeatureLockValidationError` (a `ValueError` subclass) on hash mismatch,
   for both Parquet (manifest hash) and JSONL (recomputed hash) packs.
3. `_filter_rows_by_version` (line ~1418): raises
   `value_row_version_field_missing` when a row lacks its fver field and
   `locked_value_rows_not_found` when ZERO rows match the locked fver. This
   also makes the empty-staged-set corner (`null_count == len(staged_rows)`
   with both zero) unreachable — an all-rows-filtered factor is fatal, not an
   exclusion.
4. Only then, at line ~728: `if numeric_count == 0:` → exclusion ONLY when
   `null_count == len(staged_rows)` (every staged row is literally null);
   otherwise the original fatal `non_numeric_feature_pack_for_surrogate` is
   preserved (mixed null + non-numeric-string packs stay fatal).

Direct probe (restored code, JSONL pack, corrupted registry hash): raises
`FeatureLockValidationError: feature value content hash mismatch for fver_…` —
hash mismatch is NOT excludable.

### 2. Not-all-null factor proceeds — PASS (code), WARNING (coverage)

Direct probe: a 50%-null factor (3 of 6 rows null) on restored code stages
normally — `surrogate_study_spec_count == 1`, `excluded_factors == []`. The
exclusion condition requires `numeric_count == 0` AND 100% nulls, so any
factor with ≥1 numeric value proceeds to calibration. But NO test pins this
boundary (mutation B survived — see below).

### 3. Zero-numeric-factors fail-closed — PASS

`_raise_if_no_numeric_declared_factors` raises structured
`GovernanceValidationError` with distinct code
`no_numeric_declared_factors_for_surrogate`, asserted by
`test_real_surrogate_calibration_refuses_when_all_declared_factors_all_null`
(test line 545). Test run: PASS. Mutation C killed (below). Defense in depth:
even with the new raise neutralized, the staging path still fail-closes via
the (now otherwise dead) `no_declared_factor_sub_configs` raise — no vacuous
zero-pass report is reachable.

### 4. Report honesty — PASS

`## excluded_factors` section is value-free: factor_id, feature_version_id,
partition, reason, total_rows, null_rows, numeric_rows only. No values,
labels, returns, or signals. The excluded factor's staged
`factor-values.jsonl` is deleted (`path.unlink()`), and the new test asserts
only the included factor's rows remain on disk. Included-factor semantics
unchanged: declared-K (`declared_runs_per_config`), the bound statement
(`render_value_free_calibration_report`, untouched), and the staged
sub-config-count line all keep their prior meaning; the only header addition
is the excluded-partition count line. The local staging manifest
(`staging_manifest.json`, isolated namespace, never committed) is likewise
ids/counts only.

### 5. Rescore consistency — PASS (test exists)

`test_real_surrogate_calibration_records_all_null_factor_exclusion` runs
`--rescore-existing` against the same namespace and asserts `run_count` and
`excluded_factors` equal the original staging result. Rescore loads exclusions
from the staging manifest (schema + study_spec_id validated, malformed
records fail closed) and applies the same
`no_numeric_declared_factors_for_surrogate` guard; legacy namespaces without a
manifest fall back to the declared expected count (old behavior).

### 6. Mutation tests (all restored; `git status` clean; suite re-run green)

| ID | Mutation | Expected | Result |
|---|---|---|---|
| A | Exclusion branch also catches `ValueError` from hash verification (hash mismatch → recorded as `all_null_values` exclusion) | hash-mismatch-refusal test FAILS | **SURVIVED** — `test_real_surrogate_calibration_refuses_value_hash_mismatch` is `pytest.importorskip("polars")`-gated and SKIPS in the dev venv, the CI venv, and GitHub CI (`polars` absent from all three and from `pyproject.toml`/workflows). Full tool-test run under mutation: 8 passed, 2 skipped. Probe under mutation: corrupted-hash factor with a healthy sibling factor → run ACCEPTED, corruption silently recorded as `all_null_values`. Probe on restored code: correctly raises `FeatureLockValidationError`. Code correct; enforced coverage zero. |
| B | Exclude factors with ≥50% nulls (`numeric_count == 0` → `numeric_count == 0 or null_count * 2 >= len(staged_rows)`) | a not-all-null test FAILS | **SURVIVED** — full suite under mutation: 686 passed, 2 skipped. All fixtures are either all-numeric or all-null; no partial-null fixture exists, so the exact-all-null upper boundary is unpinned. Probe under mutation confirmed a 50%-null factor was wrongly excluded. Mitigant: such creep is visible in the value-free report (`null_rows < total_rows` under reason `all_null_values`). |
| C | Neutralize `_raise_if_no_numeric_declared_factors` (early `return`) | distinct-code test FAILS | **KILLED** — `test_real_surrogate_calibration_refuses_when_all_declared_factors_all_null` failed (got `no_declared_factor_sub_configs` instead of `no_numeric_declared_factors_for_surrogate`). |

### 7. No other behavior changes; handoff truthfulness — PASS (one nuance)

Diff vs `origin/main` touches exactly 4 files: the tool, its test module, the
phase spec, and the handoff. Perturbation configs, detection statistic,
surrogate_run engine, and all `src/` integrity code untouched. One behavioral
nuance beyond the spec text: when `surrogate_specs` is empty with zero
exclusions (zero matching locks), the error code changes from
`no_declared_factor_sub_configs` to `no_numeric_declared_factors_for_surrogate`
(the old raise is now dead code). Still fail-closed; no test asserted the old
code; recorded as W3.

Handoff numbers re-run and matched:

- `PYTHONPATH=$PWD:$PWD/src python -m pytest tests/unit/discovery_rigor_floor tests/unit/governance -q` → 686 passed, 2 skipped ✓ (handoff: 686+2)
- `PYTHONPATH=$PWD/src python tools/hooks/canary_runner.py` → "All Frontier canaries passed." ✓
- `PYTHONPATH=$PWD/src python tools/verify.py --smoke` → exit 0 ✓
- `just ci-parity` → 3315 passed, 80 skipped ✓ (handoff: 3315+80; re-run twice, second time on the verified-clean restored tree)

The handoff's commit-status note (read-only sandbox gitdir, coordinator
committed) is truthful and consistent with the worktree history. The
substrate-finding note (`bbo_tradability_spread_ticks` all-null everywhere →
kill-shot caveat register + refit first-light list) is present in the handoff
("Substrate Finding" section) as the spec's done-criteria require.

## Findings / Warnings

- **W1 (test gap, prime risk, pre-existing skip):** the only test that proves
  this tool refuses hash-mismatched packs is skipped in every enforced
  environment (`polars` not installed anywhere). Mutation A — swallowing hash
  mismatches into the new exclusion branch — survives the entire enforced
  suite. Follow-up (small): add a JSONL-based hash-mismatch refusal test
  (needs no polars; the probe in this review is a ready template) so the
  exclusion/refusal boundary is pinned in CI.
- **W2 (test gap, introduced boundary unpinned):** no partial-null fixture
  exists, so "exclusion is EXACTLY all-null" is enforced only by code, not by
  tests (mutation B survived 686 tests). Follow-up (small): add a 50%-null
  factor test asserting it stages with zero exclusions.
- **W3 (dead code / silent error-code change):** the
  `no_declared_factor_sub_configs` raise is unreachable — the new
  unconditional `_raise_if_no_numeric_declared_factors` fires first when
  `surrogate_specs` is empty, even with zero exclusions. Fail-closed either
  way; the misleading `actual="0 all-null factor partition exclusions"` text
  for a zero-lock failure is cosmetic.
- **W4 (rescore trust note):** rescore mode trusts the local manifest's
  `included_sub_config_count` without cross-checking
  `included + excluded == expected_sub_config_count` from the declared locks.
  Mitigated: manifest is tool-written into the isolated namespace, schema and
  study_spec_id validated, malformed records fail closed, and legacy
  namespaces fall back to the declared count.

## Verdict rationale

The relaxation is implemented exactly as scoped: hash, fver, lock-ambiguity,
resolver, and runtime-factor-id checks all fire before the exclusion branch
can be reached, and the branch itself triggers only on literally-100%-null
staged rows. The two survived mutations expose enforcement gaps in the test
suite (one inherited from `origin/main`), not defects in the change; both
prime-risk properties were independently proven by direct probes in this
review. PASS_WITH_WARNINGS, with W1/W2 as strongly recommended follow-up
tests before the kill-shot calibration is interpreted.
