# P022000_FUTSUB_RELOCK_RERUN — Fresh Adversarial Review

Verdict: **PASS_WITH_WARNINGS** — originally REWORK (one bounded required repair;
the relock substance itself verified true); repair verified by fresh re-review,
see "## REWORK resolution (re-review)" at the end of this file.

Reviewed: uncommitted diff in `/home/yuke_zhang/projects/alpha_system-wf1-relock`
(branch `repair/futsub-relock-rerun` off origin/main @4b81915), 2026-06-11.
Environment: `ALPHA_DATA_ROOT=$HOME/alpha_data/alpha_system`,
`~/.venvs/alpha_system_research/bin/python`.

## Blocking Findings

### F1 (BLOCKING): new committed smoke test is deterministically red in CI

`tests/unit/futures_substrate_scaleout/test_studyspec_relock_smoke.py:125-145`
(`test_committed_locks_resolve_against_live_registry_and_feature_validator`)
hard-asserts `($ALPHA_DATA_ROOT|~/alpha_data/alpha_system)/registry/features.sqlite`
exists (line 129) and resolves all 4560+840 locks against the live registry.
`.github/workflows/frontier-ci.yml:34` runs bare `python -m pytest` on
`ubuntu-latest` with no data root and no env injection; there is no skip guard
in any conftest, and no other test in the suite requires a populated local
data root (verified by grep — all other ALPHA_DATA_ROOT tests use
tmp_path/fixtures or assert unset-behavior). Reproduced deterministically:

```
ALPHA_DATA_ROOT=/tmp/ci_sim_empty pytest ...::test_committed_locks_resolve_... 
→ FAILED test_studyspec_relock_smoke.py:129 AssertionError
```

Consequence: the phase PR is guaranteed CI-red, which fails the merge gate and
the phase done criteria. Required repair (bounded): guard ONLY this test with a
loud `pytest.mark.skipif`/`pytest.skip` when the registry file is absent
(reason must name the missing registry path), keeping it mandatory in the
phase's local validation commands where ALPHA_DATA_ROOT is set. Do not weaken
or remove the resolver/validator assertions themselves; the other 5 tests are
data-root-free and must remain unguarded.

## Verified Clean (deterministic evidence)

1. **Scope**: diff is exactly 10 tracked files (8 superseded P27 JSONs deleted,
   report rewritten, smoke test updated) + 10 untracked new JSONs, all under
   `research/futures_substrate_scaleout_v1/rerun/**` and the smoke test. Zero
   `src/**` changes (`git diff origin/main -- src/` empty);
   `src/alpha_system/runtime/input_resolver.py` blob sha `778fa371e90a…` is
   byte-identical to `origin/main` — the formerly-GAPPED resolution is NOT a
   resolver change. Nothing staged; `git ls-files runs` empty.
2. **Registry read-only**: `features.sqlite` mtime 2026-06-12T02:03:16Z equals
   `MAX(registered_at)` over the whole table (last write of the prior
   coordinator re-materialization, before the executor ran; executor notes
   mtime 02:23Z). `MAX(deprecated_at)` = 2026-06-12T00:29:28Z (the sanctioned
   496-row deprecation, reason cites P235500/PR #376 +
   `session_reset_repair_20260612T002901Z` backup, which exists).
   `labels.sqlite` mtime 2026-06-11T16:15Z (untouched). Affected set = exactly
   24 feature_ids (23 re-materialized + `base_ohlcv_rolling_volume` with 0
   REGISTERED rows = deferred as stated); lifecycle counts for the set:
   DEPRECATED=496, REGISTERED=**400** (matches spec/claim exactly).
3. **Lock truth**: smoke run by reviewer: `6 passed in 21.71s` with live
   resolution. Independent cross-check: 4560 feature + 840 label locks total;
   1216 unique fvers, 96 unique lvers; **0** committed fvers in the deprecation
   table, **0** in non-REGISTERED state, **0** absent from the registry.
   Per-study lock counts match the report table for all 10 studies; family
   sums (4560/840) re-derived independently.
4. **Contract fidelity** (3 samples: vwap `sspec_69c22ec5…`→`sspec_652fcc23…`,
   regime `sspec_267cc052…`→`sspec_1d87dfbe…`, bbo `sspec_9f6f7411…`→
   `sspec_6088f0ed…`): all 9 held-fixed fields (`alpha_spec_id`,
   `label_spec_id`, `split_protocol`, `metrics`, `cost_assumptions`,
   `variant_budget`, `locked_test_policy`, `negative_controls`,
   `stopping_rules`) byte-equal to
   `research/futures_core_alpha_pilot_v1/study_specs/study_specs.json`; only
   `study_spec_id` + `dataset_scope` differ; provenance records
   `relock_phase_id=P022000_FUTSUB_RELOCK_RERUN` + original id.
5. **Mutation tests** (both restored byte-identical, sha256-verified):
   - (a) flipped one hex char in one fver of `sspec_652fcc23…json` → smoke
     FAILED at the governance layer
     (`src/alpha_system/governance/study_spec.py:276`,
     "study_spec_id must match deterministic StudySpec content") — the sspec id
     is content-addressed, so ANY hand-patched lock fails before resolution.
     Defense-in-depth stronger than expected.
   - (b) pointed the regime study's `liquidity_structure_range_contraction`
     ES_2019 lock at DEPRECATED `fver_96c95feb…322f` AND recomputed the
     content-addressed id to bypass layer (a) → resolver failed closed:
     `RuntimeInputResolverError: feature_pack lifecycle_state must be
     REGISTERED` (`feature_pack_deprecated`,
     `src/alpha_system/runtime/input_resolver.py:1353`). Lifecycle gate real.
6. **Formerly-GAPPED explanation verified at the source**: new REGISTERED
   `liquidity_structure_range_contraction` and `bbo_tradability_spread_zscore`
   records carry `feature_spec.inputs.input_metadata.field_roles =
   {"session_label": "SESSION_METADATA"}`; their DEPRECATED counterparts have
   no `field_roles`. Resolution comes from new registry records, not weakened
   resolution (see also input_resolver sha above).
7. **Value-free**: locks carry ids/hashes/counts/ts-windows only; grep for
   `/home/|/mnt/|parquet_path|materialization_output_path|provider_path`
   over all new JSONs + report: clean. No alpha/profitability/tradability
   claims in the report (family name `bbo_tradability` is pre-existing
   nomenclature).
8. **Suite + canaries**: full
   `pytest tests/unit/futures_substrate_scaleout -q` = `132 passed`;
   `python tools/verify.py --smoke` exit 0;
   `python tools/hooks/canary_runner.py` = all canaries PASS.
9. **Report accuracy**: counts (10 classified, 10 written, 6/6
   prior-INCONCLUSIVE RELOCKED, 4/4 audit-only, 4560/840, 0 gaps) all match
   independent measurement; supersession section accurate (8 old JSONs deleted
   in-diff, dir now contains exactly the 10 new files).

## Warnings (non-blocking)

- W1: The report line "DatasetVersion policy: all committed locks point to
  ACCEPTED or ACCEPTED_WITH_WARNINGS DatasetVersions" is attested by the
  committed `acceptance_state` fields and the structural test, not re-checked
  live against `datasets.sqlite` by the smoke. Same posture as P27; noted for
  a future hardening pass, not a regression.
- W2: Executor could not read the run-local P27 spec (`runs/` absent in the
  worktree) and used the committed methodology docs instead — honestly
  disclosed in the notes; methodology outcome matches CORE_PILOT_RELOCK.md
  discipline.

## Required Repairs

1. Make `test_committed_locks_resolve_against_live_registry_and_feature_validator`
   CI-safe via a loud registry-absent skip guard (see F1). No other change.
   Re-run the smoke locally with ALPHA_DATA_ROOT set (must still execute, not
   skip) and the CI simulation (`ALPHA_DATA_ROOT=/tmp/empty`) must skip, not
   fail.

## REWORK resolution (re-review)

Re-reviewed 2026-06-12T03:05Z by a fresh re-reviewer against the uncommitted
diff in `/home/yuke_zhang/projects/alpha_system-wf1-relock`
(branch `repair/futsub-relock-rerun` off origin/main @4b81915).

**F1 resolved. Final verdict: PASS_WITH_WARNINGS** (W1/W2 stand unchanged as
non-blocking warnings).

### Repair verified

`test_committed_locks_resolve_against_live_registry_and_feature_validator`
now opens with a condition-driven guard (test file lines 129-134):

```python
if not feature_registry.exists():
    pytest.skip(
        "live local registry absent (CI environment): "
        f"{feature_registry} -- lock resolution validated locally; "
        "see studyspec_relock.md report"
    )
```

The skip is loud and names the missing registry path. No assertion was
weakened or removed: `assert label_registry.exists()`, the per-study
`_resolve_feature_locks`/`_resolve_label_locks` resolver loops, and
`report.ok` / `lock_count == 4560` / `resolved_count == 4560` /
`stale_lock_count == 0` are all intact, and the other 5 tests remain
unguarded exactly as required.

### Scope verified (repair-only change since review)

- The smoke test is the ONLY file in the worktree with an mtime after the
  REWORK review artifacts (test 2026-06-11T22:35:33-04 vs review 22:33);
  every other diff file carries the executor-batch mtime 22:20:52.
- The two mutation-restored JSONs re-hash to the verdict-recorded sha256s
  (`71ebe672bc6e…` for sspec_652fcc23…, `681fbea0c9ff…` for sspec_1d87dfbe…).
- The guard occupies exactly the position of the former hard assert
  (old line 129); the rest of the test matches the reviewed version
  line-for-line (+5 lines net). Nothing staged; `git ls-files runs` empty.

### Deterministic evidence

1. Live root (`ALPHA_DATA_ROOT=$HOME/alpha_data/alpha_system`):
   **6 passed, 0 skipped in 21.65s** — the live resolution test executes,
   it does not skip.
2. CI simulation (`ALPHA_DATA_ROOT=/tmp/definitely_absent_root`):
   **5 passed, 1 skipped in 0.63s**; skip reason printed loudly:
   `live local registry absent (CI environment):
   /tmp/definitely_absent_root/registry/features.sqlite -- lock resolution
   validated locally; see studyspec_relock.md report`.
3. Guard mutation test: inverted the condition (skip when the registry
   EXISTS) and re-ran (1) → the live test **SKIPPED** (5 passed, 1 skipped),
   proving the skip is driven by `feature_registry.exists()` and not
   unconditional. Restored byte-identical
   (sha256 `fc0ca12d98ddffafd4f50caa6ba20ad3fcde776c0c41c0dd37ae788daaea42c4`
   pre == post) and re-ran (1) → **6 passed in 21.78s**.
