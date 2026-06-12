# Review: P033000_HOLDOUT_WINDOW_COVERAGE — kill-shot input coverage for the sealed holdout

- Campaign: `DISCOVERY_RIGOR_FLOOR_V1`
- Phase: `P033000_HOLDOUT_WINDOW_COVERAGE`
- Lane: yellow
- Reviewer: fresh adversarial Claude review (no executor context)
- Worktree reviewed: `/home/yuke_zhang/projects/alpha_system-wf1-relock` (branch `repair/holdout-window-coverage`, HEAD `819c1537` == `origin/main`, diff UNCOMMITTED)
- Diff: 4 files, +388/-21 — `research/discovery_rigor_floor_v1/sealed_holdout/kill_shot_sealed_holdout_window.json`, `src/alpha_system/governance/sealed_holdout.py`, `tests/unit/discovery_rigor_floor/test_rigor_p03_sealed_holdout_declaration.py`, `tests/unit/governance/test_sealed_holdout.py`
- Verdict: **PASS_WITH_WARNINGS**

## 1. Boundary integrity — PASS

- Locked-test temporal boundary did NOT move backward: `start_date` stays `2025-01-01`; the only temporal change is `end_date: "2026-06-11"` (frozen) → `end_date: null` + `rolling: true` (open-ended forward = widening). Discovery/validation split dates unchanged (`compass_window_doctrine` string `2019-2021 discovery / 2022-2024 validation / 2025-latest locked test` byte-identical in the diff).
- `_partitions_intersect` (sealed_holdout.py:1339–1353) is NOT in the diff — byte-identical to origin/main. Semantics confirmed by reading: any shared key with disjoint non-empty value sets returns False; no weakening.
- Line-by-line on the matcher path: the only behavior change in `access_intersects_holdout` is end-date defaulting via new `_effective_holdout_end` (returns `date.max` for rolling/open windows, `date.fromisoformat(end_date)` otherwise). For every previously-valid (non-rolling, end-dated) window the date-overlap math is identical to origin/main. The widening happens in the DECLARATION (rolling marker), not the matcher. One stricter side-effect: an empty-string `access_end_date` previously fell back to the window end (falsy `or`), now it is parsed and raises a validation error — fail-closed, acceptable.
- Schema extension is fail-closed: `end_date: null` without explicit `rolling: true` raises `missing_non_rolling_holdout_end_date` (verified by new governance unit test and by Mutation A's tooling, which hit exactly this error when run against the un-patched main-repo module).
- Old declaration preserved verbatim under `superseded_declaration` (old `window_id holdwin_d5cba50af19976275ab26f34`, old `symbols=[ES]`, old frozen `end_date`), with `redeclaration_reason` naming `P033000_HOLDOUT_WINDOW_COVERAGE`. Scope-correction framing is accurate.
- `generate_sealed_holdout_window_id` now skips absent component fields; legacy IDs are unaffected because `end_date` was previously required (always present), and `rolling` is only included when declared. See W2.

## 2. Coverage truth — PASS

- The contract test `test_kill_shot_window_intersects_every_relocked_locked_test_input` loads the REAL committed re-locked StudySpecs: `git ls-files research/futures_substrate_scaleout_v1/rerun/study_specs` = 10 files, all loaded through `StudySpec.from_mapping`, and the test asserts `len(specs) == 10`.
- It asserts intersection through the REAL matcher code path: `access_intersects_holdout(...)` imported from `alpha_system.governance.sealed_holdout`, which calls the unmodified `_partitions_intersect`. No reimplementation.
- Reviewer independently re-derived the vocabulary from the 10 committed spec JSONs (separate script, not the test): symbols exactly {ES, NQ, RTY}; 32 unique 2025+ locked-test partitions; schemas {bbo_1m, ohlcv_1m, ohlcv_dense_research_grid}; sources {dsrc_databento_historical}; families {bbo_tradability, cross_market, liquidity_pa, regime, vwap_session}. Every set is exactly equal to the redeclared `partition_spec` vocabulary. Counts in provenance (10 specs / 32 partitions) match.
- Filter integrity: locks are classified locked-test by `start_ts >= 2025-01-01T00:00:00`; reviewer verified 0 of the 126 pre-2025 locks contain any 2025+ partition name, so no locked-test input is silently dropped by the filter (see W5 for a format caveat).
- Negative non-vacuity case exists and exercises a genuinely non-intersecting input through shared-key disjointness (`dataset_family=outside_research_family`, `symbols/target_instruments=[CL]`, `futsub_study_families=[outside_family]`) — not an empty/no-shared-key spec (which would vacuously return True). Plus a 2024 temporal negative and a post-2026-06-11 rolling positive ("latest means latest").
- Per-partition checks pass each partition individually (`futsub_locked_test_partitions: [partition]`), so a future StudySpec referencing a partition outside the declared vocabulary makes CI fail through the matcher, which is the load-bearing guarantee.

## 3. Mutation tests — ALL BEHAVED AS REQUIRED

Baseline `git diff | sha256sum` = `52c9fed27069340a6078ef4500883a1b09534a7ca19b97b45aba0ab138f1543c`. Each mutation regenerated a VALID `window_id` (via the worktree's `generate_sealed_holdout_window_id`) so failures come from coverage, not ID mismatch.

| Mutation | Expected | Observed |
|---|---|---|
| (a) Re-narrow declaration to `symbols=[ES]`, `target_instruments=[ES]` | contract test FAILS | FAILED: `test_kill_shot_window_intersects_every_relocked_locked_test_input` — `AssertionError: sspec_1d87dfbe…; assert False = access_intersects_holdout(..., symbols=['NQ'])` (2 failed, 1 passed) |
| (b) Re-freeze `end_date=2026-06-11` (equivalent mutation: drop `rolling`, set end_date — schema encodes open-endedness as `end_date:null + rolling:true`) | contract test FAILS (locked-test must mean latest) | FAILED: `test_kill_shot_window_contract_is_non_vacuous_and_temporally_bounded` — `assert False = access_intersects_holdout(..., access_start_date='2026-06-12', access_end_date='2027-01-01', ...)` (2 failed, 1 passed) |
| (c) Weaken `_partitions_intersect` to always-True | negative non-vacuity test FAILS | FAILED: `test_kill_shot_window_contract_is_non_vacuous_and_temporally_bounded` — `assert not True` on `dataset_family='outside_research_family'` (1 failed, 2 passed) |

Restoration verified byte-identical: post-restore `git diff | sha256sum` = `52c9fed2…` (exact match with baseline); pristine file sha256s match (`d8825d39…` JSON, `567d1f12…` sealed_holdout.py).

## 4. Access-log / contamination semantics — UNTOUCHED

- `emit_holdout_access_if_intersects`, `HoldoutAccessLog` append path, `contamination_detected` logic, and `fail_on_unauthorized_locked_test` are not in the diff.
- `require_sealed_holdout: bool = False` default lives in `src/alpha_system/governance/promotion_gate.py:121` — file not modified. `planted_fake_alpha` canary still passes `require_sealed_holdout=True` and the canary suite passes.

## 5. Validation (post-restore re-run by reviewer, exact counts)

| Command | Result |
|---|---|
| `pytest tests/unit/governance -k "holdout or sealed" -q` | 13 passed, 594 deselected |
| `ALPHA_DATA_ROOT=$HOME/alpha_data/alpha_system pytest tests/unit/discovery_rigor_floor tests/unit/futures_substrate_scaleout/test_studyspec_relock_smoke.py -q` | 23 passed |
| `tools/hooks/canary_runner.py` | 23 PASS lines, "All Frontier canaries passed.", exit 0 |
| `tools/verify.py --smoke` | exit 0 |

Executor-reported `verify.py --all` = 3 failed / 3306 passed / 1 skipped; the 3 failures are the known pre-existing env failures (duckdb fixture, polars fixture, databento-canonicalize) outside the touched files — consistent with the known-failure list provided to this review.

## 6. Artifact policy — PASS

- Nothing staged (`git diff --cached --name-only` empty); `git ls-files runs` empty; changed-file set is exactly the 4 declared files; no untracked additions; no `src/alpha_system/runtime/**` changes; declaration JSON is value-free (`value_free: true`, names/counts only, validated by the value-free canonical checks in `validate_sealed_holdout_window`).

## Warnings (non-blocking)

- **W1 — rolling overrides explicit end_date**: `_effective_holdout_end` returns `date.max` whenever `rolling=True`, even if an explicit `end_date` is also present (such a payload validates). Direction is widening-only (more accesses intersect → more logging/gating), i.e. fail-safe, and for THIS window the declaration test pins `end_date is None`, but a future declaration carrying both would silently treat the end as open. Consider a validation issue forbidding `rolling=true` + non-null `end_date`.
- **W2 — looser ID-component contract**: `generate_sealed_holdout_window_id` now skips absent component fields. Legacy IDs unaffected (end_date was required); null-vs-absent produce different canonical components, so no collision found — but the component set is no longer fixed-shape. Acceptable, worth knowing.
- **W3 — doc drift**: `research/discovery_rigor_floor_v1/sealed_holdout/GATE_INVENTORY.md:8` still cites the superseded `holdwin_d5cba50af19976275ab26f34`. The RIGOR-P03 handoff is a historical record and correctly untouched, but GATE_INVENTORY is a live inventory — recommend a one-line follow-up update.
- **W4 — env trap (reviewer-discovered)**: the research venv's installed `alpha_system` resolves to the MAIN repo `src/`, not the worktree; ad-hoc `python -c` imports in the worktree silently get old code. pytest is safe (`pythonpath = ["src"]` in pyproject), so all phase validation results are genuine — but ad-hoc scripts in worktrees must set `PYTHONPATH=<worktree>/src`.
- **W5 — string-compare lock filter**: the contract test classifies locked-test locks via `str(lock["start_ts"]) >= "2025-01-01T00:00:00"`. Correct for the current ISO `+00:00` timestamps (verified: 0 misclassified across all 136 locks), but a non-zero-padded timestamp would misclassify silently. Low risk given StudySpec timestamp validation.

## Verdict

**PASS_WITH_WARNINGS** — the scope-correction is real and correctly bounded: coverage widened in the declaration only, matcher untouched, temporal boundary only extended forward, the contract test is non-vacuous and kills all three required mutations through the real code path, and the declared vocabulary is exactly derivable from the 10 committed re-locked StudySpecs. Warnings W1–W5 are non-blocking hardening/doc follow-ups.
