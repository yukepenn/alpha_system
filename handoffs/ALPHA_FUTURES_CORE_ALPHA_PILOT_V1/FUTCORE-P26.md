# FUTCORE-P26 Executor Handoff

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P26` - TrialLedger / RejectedIdeaLedger Recording  
Executor: Codex  
Date: 2026-06-07

## Scope Completed

- Created value-free TrialLedger artifacts under `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/**`.
- Created value-free RejectedIdeaLedger artifacts under `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/**`.
- Wrote `research/futures_core_alpha_pilot_v1/ledgers/INDEX.md` with detailed reconciliation and record paths.
- Wrote `docs/futures_core_alpha_pilot/LEDGERS.md` with totals-only durable documentation.
- Updated `README.md` with the P26 snapshot and next phase pointer.
- Did not create reviewer artifacts, `review.md`, `verdict.json`, PRs, merges, commits, or staging actions.

## Reconciliation Result

| Item | Count |
| --- | ---: |
| AlphaSpec drafts reconciled | 40 |
| StudySpecs reconciled | 10 |
| TrialLedger records | 16 |
| P12 non-accepted AlphaSpecs recorded as rejected | 30 |
| Accepted StudySpecs rejected before P25 | 4 |
| P25 reviewer-rejected ideas | 0 |
| RejectedIdeaLedger records | 34 |
| P25 `INCONCLUSIVE` verdicts carried forward without P26 promotion | 6 |
| P24 explicit observed variant cells | 8 |
| Declared StudySpec variant slots | 40 |

The union of P12 non-accepted AlphaSpecs and StudySpec-bound accepted AlphaSpecs accounts for all 40 AlphaSpec drafts. TrialLedger records cover every StudySpec-bound accepted idea; RejectedIdeaLedger records cover every P12 non-accepted idea and every accepted StudySpec rejected before P25. P25 contributed no reviewer-rejected records.

Trial status counts: `FAILED=8`, `ABANDONED=4`, `COMPLETED=4`.
Rejected idea reason counts: `duplicate=30`, `failed_diagnostics=4`.

## Commit-Eligible Files Left For Ralph To Stage

- `README.md`
- `docs/futures_core_alpha_pilot/LEDGERS.md`
- `research/futures_core_alpha_pilot_v1/ledgers/INDEX.md`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_0175c1657e62c90cc2266540.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_06647e1d25ff8b1fbed873b1.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_09a5984328920eb6569e65e4.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_1b16a258b6e3bdf8f844ff1b.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_20d88b59ce09f47d364fd529.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_279ba6379332d9f899780922.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_39942b4314a2d73d6b2d6806.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_3f230dd99e4378773d549458.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_47e465bbe40d78562f0705d8.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_57e5257eb6c885c6254cf45e.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_5c5d0ffd83e6fef6b7b7b42a.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_637bd1497ff024f9a212faa3.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_7107e99008c6a7aaf7d2d5b4.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_720b132bcff3939fbf54b81e.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_74bd9f3de2307470f9a9205e.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_79fb93c524e01205571be326.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_8c41a68d8e95409fb821be78.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_932d2686b8670d5f21a2a4ca.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_9ed40aaf995f1f70f5f94cdf.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_9f8dd7ff8159f5b50645721e.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_a0475fcf4c9aa26eb43e503d.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_a047b6106811559925518ea4.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_a8832777786ac88bbe434900.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_af5723443be70254b18dbfef.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_af75aeaef690e7c6bed5ffac.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_af9540c3abafe6b474cb4256.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_b6525bbd50dcd3c0618596d9.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_ba018932c70418dd1c62cc73.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_c27b447c282967db390ff10d.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_cf1b3dcfd7a25f222ef38522.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_e0a173b02edb0e71d249725f.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_edeac064bfc49a96e4a561e4.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_f1aa6cbbba90096cbe920125.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_fa471f1ddeaa066dc4a95feb.json`
- `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/rejected_idea_ledger.json`
- `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/trial_13c98257a704ce5641a51626.json`
- `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/trial_1fc87c34cf31d8055d3d224d.json`
- `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/trial_2ae03a839098b6ff741b2f84.json`
- `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/trial_2c32c84a140e6e99f67f5aa8.json`
- `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/trial_3a61fa6378614054674171ec.json`
- `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/trial_3b8f60dd0f4793288360159e.json`
- `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/trial_45df4e0c5999da63a57ff9b2.json`
- `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/trial_4ee4909066d85d4abcdfaa42.json`
- `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/trial_587d6da288aa8ff2ca25fa37.json`
- `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/trial_58fdb5456d910efccdd95b7b.json`
- `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/trial_666433ac863d5adb1368a3d1.json`
- `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/trial_94781614f100a2aa0878aae4.json`
- `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/trial_b4e25da7c409809fc1cb54b7.json`
- `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/trial_bdbfa08dcf63fe1fe8e5921d.json`
- `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/trial_fce335815b1bda26eb898aed.json`
- `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/trial_fffbb48dc4111caeabcc55c9.json`
- `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/trial_ledger.json`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P26.md`

Reviewer-owned paths under `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P26/**` were not created by this executor.

## Validation

| Command | Outcome |
| --- | --- |
| `python -c "import alpha_system.governance.trial_ledger, alpha_system.governance.rejected_idea"` | Passed. |
| `test -d research/futures_core_alpha_pilot_v1/ledgers` | Passed. |
| `git ls-files runs` | Passed; printed nothing. |
| `PYTHONPATH=src python - <<'PY' ... ledger schema/count validation ... PY` | Passed; validated 16 TrialLedger records, 34 RejectedIdea records, TrialLedger aggregate count, and ResearchGraveyardLedger aggregate count. |
| `python tools/verify.py --smoke` | Passed. |
| `python tools/verify.py --lint` | Exit 0, but lint was skipped because `ruff` is not installed (`pip install -e ".[dev]"` needed). |
| `python tools/verify.py --typecheck` | Passed; verifier ran compileall over `src`, `tests`, and `tools`. |
| `python tools/verify.py --test` | Failed: 4 failed, 2840 passed in 47.90s. Failures: `tests/integration/test_duckdb_query_fixture.py::test_duckdb_query_over_tiny_csv_fixture`; `tests/integration/test_polars_lazy_fixture.py::test_polars_lazy_transformation_over_tiny_fixture`; `tests/unit/data/test_databento_canonicalize.py::test_databento_canonicalize_quality_coverage_and_register_offline`; `tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only`. |
| `python tools/hooks/canary_runner.py` | Passed; all Frontier canaries passed. |
| `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.dbn' '**/*.zst'` | Passed; printed nothing. |
| `find research/futures_core_alpha_pilot_v1/ledgers -type f \( -name '*.parquet' -o -name '*.arrow' -o -name '*.feather' -o -name '*.sqlite' -o -name '*.sqlite3' -o -name '*.db' -o -name '*.dbn' -o -name '*.zst' -o -name '*.pkl' -o -name '*.pickle' -o -name '*.joblib' -o -name '*.onnx' -o -name '*.npy' -o -name '*.npz' \) -print` | Passed; printed nothing. |

Not run by executor due explicit instruction: `git status --short`, `git diff --cached --name-only`, `git add`, `git commit`, and `git push`.

## Artifact And Boundary Confirmation

- No `runs/**` files were created, edited, staged, or committed by this executor.
- No staging command was run; all created or edited files are left for Ralph to stage explicitly by path.
- No heavy, raw, provider-response, value, DB, cache, model, secret, credential, broker, live, paper-trading, order-routing, deployment, test, or consumed `src/alpha_system/**` primitive files were edited.
- Ledger records are value-free: ids, statuses, reason categories, duplicate-exposure group hints, counts, hashes, and repo-relative evidence paths only.
- This handoff does not mark the phase PASS; Ralph owns review, verdict parsing, staging, commit, PR, CI, merge, and done-check actions.
