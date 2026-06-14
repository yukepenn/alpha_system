# DK-P02 Handoff

Campaign: `DIFFERENTIATED_KILLSHOT_V1`  
Phase: `DK-P02`  
Lane: `YELLOW`  
Executor status: `COMPLETE` (codex executor delivered StudySpecs + admission + runbook; coordinator then materialized the DK-P01 flags, relocked, and ran the heavy surrogate-FDR calibrations out-of-loop).  
Branch: `auto/differentiated_killshot_v1/dk-p02-...` (staging/commit are driver/coordinator-owned).  
Commits: prepared by the coordinator on the phase branch (see "Files Changed"); the codex executor made no commits.

## Scope Delivered

- Added five Track A StudySpec declarations under `research/differentiated_substrate_v1/study_specs/`.
- Added the minimal declared-conditioning-family admission in `tools/discovery_rigor_floor/run_real_surrogate_calibration.py`.
- Added mutation-style admission coverage and DK-P02 StudySpec validation coverage.
- Added a value-free calibration runbook with pre-registered `K=60`, seeds, and exact CLI shapes.
- Coordinator (out-of-loop, after the codex executor handed off): materialized the five DK-P01 calendar flag feature packs, relocked the three previously-blocked StudySpecs, and ran the real per-study surrogate-FDR calibrations. Outcome: four studies reached `zero-pass-met`; `roll_week` is `CALIBRATION_BLOCKED` (DATA_GAP) because its sole conditioning flag is all-null across every partition.

## Coordinator Completion (out-of-loop)

The DK-P01 flag feature packs and the heavy surrogate-FDR calibrations were completed by the coordinator outside the codex loop, because the calibrations are heavy single-threaded background compute (about 2880 surrogate runs per study). The codex executor stopped at the substrate gap by design and did not fabricate any pass.

- **Materialization.** The coordinator materialized the five missing DK-P01 calendar flags via an additive 13-feature superset config (`configs/features/scaleout/session_calendar_maintenance_dk_p02_superset.json`, coordinator-infra) with `--force-recompute`. The eight pre-existing `session_calendar_roll` fvers were byte-preserved: the `session_calendar_maintenance` materialized record count moved `2192 -> 2312`, i.e. exactly `+120` new rows (the 5 new flags), and the `day_of_week` ES_2019 feature version `fver_fecafaf8e58ca3cea573d5bdcfc3c000d022f65fa9b1a60a2f17d61314895c38` is unchanged.
- **Relock.** `opex`, `month_end`, and `roll_week` were relocked against the repaired registry and are now `LOCKED` with new study_spec_ids (`opex` `sspec_4936b2ee6614d4b869ec2787`, `month_end` `sspec_c8669b6769a07d69ab897e58`, `roll_week` `sspec_61b60a8ca735bddea7feb9ff`). `day_of_week` and `open_close` were already `LOCKED` and were not re-minted.
- **Calibration verdicts.** `opex`, `month_end`, `day_of_week`, `open_close` = `zero-pass-met` (value-free reports under `research/differentiated_substrate_v1/surrogate_fdr/`). `roll_week` = `CALIBRATION_BLOCKED` / DATA_GAP with no pass claimed (value-free note `roll_week_calibration.md`).
- **Calendar-coverage caveat.** The `month_end`/`quarter_end` and `roll_week` conditioning flags are effectively populated only over the 2024-26 calendar window; earlier-year partitions are all-null and are excluded under the sanctioned `all_null_values` path (`month_end` excluded 30 partitions and still reached `zero-pass-met` on the surviving ones; `roll_week` had all 24 partitions excluded and so blocked).
- **Active testable surface.** Four mechanisms carry a clean surrogate-FDR gate into DK-P03 (`day_of_week_effect`, `opex_pinning`, `month_end_flow`, `open_close_auction_flow`). `roll_week_flow` is excluded from DK-P03 real-metric inspection (no clean gate on this substrate).

## StudySpecs

All five specs validate through `validate_study_spec`, declare `declared_conditioning_feature_family = session_calendar_roll`, pool `ES/NQ/RTY` as one test per mechanism, and set `real_metric_inspection_allowed_in_this_phase = false`.

| StudySpec | `study_spec_id` | mechanism | declared conditioning feature id(s) | horizon(s) | `variant_budget` | `family_budget` | lock status | feature locks | label locks | missing feature locks |
|---|---|---|---|---|---:|---:|---|---:|---:|---:|
| `day_of_week.json` | `sspec_2ec71d30dadc48e237f9d04c` | `day_of_week_effect` | `session_calendar_roll_day_of_week` | `30m` | 1 | 4 | `LOCKED` | 24 | 24 | 0 |
| `opex.json` | `sspec_4936b2ee6614d4b869ec2787` | `opex_pinning` | `session_calendar_roll_is_opex_day_flag`, `session_calendar_roll_is_quad_witch_day_flag` | `30m` | 1 | 6 | `LOCKED` | 48 | 24 | 0 |
| `month_end.json` | `sspec_c8669b6769a07d69ab897e58` | `month_end_flow` | `session_calendar_roll_is_month_end_session_flag`, `session_calendar_roll_is_quarter_end_session_flag` | `30m` | 1 | 6 | `LOCKED` | 48 | 24 | 0 |
| `roll_week.json` | `sspec_61b60a8ca735bddea7feb9ff` | `roll_week_flow` | `session_calendar_roll_in_roll_window_flag` | `30m` | 1 | 4 | `LOCKED` | 24 | 24 | 0 |
| `open_close.json` | `sspec_0c3386a2dd45451970547acd` | `open_close_auction_flow` | `session_calendar_roll_minutes_from_rth_open`, `session_calendar_roll_minutes_to_rth_close` | `5m`, `30m` | 2 | 4 | `LOCKED` | 48 | 48 | 0 |

All five StudySpecs are now relocked to `LOCKED` after coordinator materialization; the `opex`/`month_end`/`roll_week` study_spec_ids above are the post-materialization relocked ids.

Resolver-smoke (post-materialization):

- `day_of_week.json`: PASS, feature locks `24`, label locks `24`.
- `open_close.json`: PASS, feature locks `48`, label locks `48`.
- `opex.json`: PASS, feature locks `48`, label locks `24` (relocked after DK-P01 flag materialization).
- `month_end.json`: PASS, feature locks `48`, label locks `24` (relocked after DK-P01 flag materialization).
- `roll_week.json`: PASS, feature locks `24`, label locks `24` (relocked); the lock resolves, but calibration later blocked on degenerate (all-null) conditioning values, see Calibration outcome.

## Admission Change

`tools/discovery_rigor_floor/run_real_surrogate_calibration.py` now recognizes two explicit StudySpec dataset-scope fields:

- `declared_conditioning_feature_family`
- `declared_conditioning_feature_ids`

The behavior is additive and fail-closed:

- Without an explicit declaration, `session_calendar_*` families are still support families and still fail as `declared_factor_family_missing`.
- With an explicit declaration, only the declared family is admissible as the signal family.
- Non-declared non-support families alongside the declared family raise `declared_factor_family_ambiguous`.
- `declared_conditioning_feature_ids` limits staged calibration locks to the declared feature ids, so incidental same-family support locks are not scored.
- The staged `factor_id` identity is preserved against `study_config_for_surrogate_scope(...)`; `runtime_factor_id_mismatch` remains intact.

Mutation-test evidence is in `tests/unit/discovery_rigor_floor/test_real_surrogate_calibration_tool.py`:

- Explicit `session_calendar_roll` declaration is admitted.
- Non-declared `session_calendar_roll` remains support and fails closed.
- Incidental same-family support locks are not staged as factor-under-test.
- A non-declared signal family beside the declaration raises `declared_factor_family_ambiguous`.
- Synthetic calibration reaches `zero-pass-met` with a value-free report path.

## Calibration Commands

Pre-registered runbook: `research/differentiated_substrate_v1/study_specs/RUNBOOK.md`  
K per perturbation config: `60`  
Required gate: `zero-pass-met`  
Reports: `research/differentiated_substrate_v1/surrogate_fdr/<mechanism>_calibration.md`

Exact CLI invocations recorded for resume:

```bash
python tools/discovery_rigor_floor/run_real_surrogate_calibration.py --study-spec /home/yuke_zhang/projects/alpha_system-differentiated_killshot_v1-dk-p02/research/differentiated_substrate_v1/study_specs/day_of_week.json --alpha-data-root /home/yuke_zhang/alpha_data/alpha_system --namespace /home/yuke_zhang/alpha_data/alpha_system/rigor_p05_surrogate_dk_p02_day_of_week --runs-per-config 60 --base-seed 42020 --report-out research/differentiated_substrate_v1/surrogate_fdr/day_of_week_calibration.md
python tools/discovery_rigor_floor/run_real_surrogate_calibration.py --study-spec /home/yuke_zhang/projects/alpha_system-differentiated_killshot_v1-dk-p02/research/differentiated_substrate_v1/study_specs/opex.json --alpha-data-root /home/yuke_zhang/alpha_data/alpha_system --namespace /home/yuke_zhang/alpha_data/alpha_system/rigor_p05_surrogate_dk_p02_opex --runs-per-config 60 --base-seed 42021 --report-out research/differentiated_substrate_v1/surrogate_fdr/opex_calibration.md
python tools/discovery_rigor_floor/run_real_surrogate_calibration.py --study-spec /home/yuke_zhang/projects/alpha_system-differentiated_killshot_v1-dk-p02/research/differentiated_substrate_v1/study_specs/month_end.json --alpha-data-root /home/yuke_zhang/alpha_data/alpha_system --namespace /home/yuke_zhang/alpha_data/alpha_system/rigor_p05_surrogate_dk_p02_month_end --runs-per-config 60 --base-seed 42022 --report-out research/differentiated_substrate_v1/surrogate_fdr/month_end_calibration.md
python tools/discovery_rigor_floor/run_real_surrogate_calibration.py --study-spec /home/yuke_zhang/projects/alpha_system-differentiated_killshot_v1-dk-p02/research/differentiated_substrate_v1/study_specs/roll_week.json --alpha-data-root /home/yuke_zhang/alpha_data/alpha_system --namespace /home/yuke_zhang/alpha_data/alpha_system/rigor_p05_surrogate_dk_p02_roll_week --runs-per-config 60 --base-seed 42023 --report-out research/differentiated_substrate_v1/surrogate_fdr/roll_week_calibration.md
python tools/discovery_rigor_floor/run_real_surrogate_calibration.py --study-spec /home/yuke_zhang/projects/alpha_system-differentiated_killshot_v1-dk-p02/research/differentiated_substrate_v1/study_specs/open_close.json --alpha-data-root /home/yuke_zhang/alpha_data/alpha_system --namespace /home/yuke_zhang/alpha_data/alpha_system/rigor_p05_surrogate_dk_p02_open_close --runs-per-config 60 --base-seed 42024 --report-out research/differentiated_substrate_v1/surrogate_fdr/open_close_calibration.md
```

Calibration outcome (coordinator out-of-loop bg compute, ~2880 surrogate runs/study, single-threaded):

- `day_of_week` (`sspec_2ec71d30dadc48e237f9d04c`): `zero-pass-met` — `day_of_week_calibration.md`.
- `opex` (`sspec_4936b2ee6614d4b869ec2787`): `zero-pass-met` — `opex_calibration.md`.
- `month_end` (`sspec_c8669b6769a07d69ab897e58`): `zero-pass-met` — `month_end_calibration.md` (30 all-null partitions excluded under the sanctioned `all_null_values` path; the surviving 2024-26-coverage partitions cleared the gate).
- `open_close` (`sspec_0c3386a2dd45451970547acd`): `zero-pass-met` — `open_close_calibration.md`.
- `roll_week` (`sspec_61b60a8ca735bddea7feb9ff`): `CALIBRATION_BLOCKED` / DATA_GAP, no report-pass — `roll_week_calibration.md`. The sole conditioning flag `session_calendar_roll_in_roll_window_flag` is all-null/zero-variance across all 24 partitions, so every partition was excluded and the tool fail-closed with `no_numeric_declared_factors_for_surrogate` ("no declared factor with numeric content after recorded all-null exclusions"). This is consistent with the R-036 offline-roll-metadata constraint and the 2024-26 calendar coverage.
- No `LEAKAGE_BLOCKED` result was observed. No alpha/profitability/tradability claim is made; the gate outcomes decide.
- Reports are value-free (ids/counts/seeds/gate-outcome/declared-threshold only; no IC/return/diagnostic/signal/cost values).

## Validation

Passed:

```bash
PYTHONPATH=src python -m pytest tests/unit/discovery_rigor_floor/test_real_surrogate_calibration_tool.py -k "declared_session_calendar or session_calendar_support" -q
# 4 passed, 21 deselected

PYTHONPATH=src python -m pytest tests/unit/differentiated_killshot/test_dk_p02_study_specs.py tests/unit/discovery_rigor_floor/test_real_surrogate_calibration_tool.py -k "dk_p02 or declared_session_calendar or session_calendar_support" -q
# 5 passed, 21 deselected

PYTHONPATH=src python -m pytest tests -k "study_spec or surrogate or variant_ledger or family_budget or calibrat" -q
# 141 passed, 4 skipped, 3435 deselected

PYTHONPATH=src python tools/verify.py --smoke
# passed

PYTHONPATH=src python tools/hooks/canary_runner.py
# all Frontier canaries passed

env -u ALPHA_DATA_ROOT -u FRONTIER_CREATE_PR -u FRONTIER_ALLOW_AUTOMERGE -u FRONTIER_MERGE_DRY_RUN -u FRONTIER_PARALLEL -u FRONTIER_MAX_PARALLEL_PHASES PYTHONPATH=src python tools/verify.py --all
# 3500 passed, 80 skipped; compileall passed; canaries passed
# status_doctor warning only: no live run dir with state.json found for this campaign in this checkout

git ls-files research/differentiated_substrate_v1/surrogate_fdr | grep -E "futures_(core_alpha_pilot|substrate_scaleout)_v1|registry|metadata|artifacts|/runs/" && echo "FORBIDDEN NAMESPACE" && exit 1 || echo "namespace ok"
# namespace ok

grep -rEn "import +(alpha_system\.)?(backtest|management|fast_path|core\.value_store)|from +(alpha_system\.)?(backtest|management|fast_path|core\.value_store)" --include=*.py src/alpha_system/research && echo "FORBIDDEN IMPORT" && exit 1 || echo "research import-clean"
# research import-clean

python -c "import importlib.util,sys; bad=[m for m in ('numpy','pandas','polars') if importlib.util.find_spec(m)]; sys.exit('forbidden dependency importable: '+','.join(bad) if bad else 0)"
# passed

git ls-files runs
# printed nothing
```

Coordinator-run (out-of-loop, after the codex handoff; heavy bg compute, not codex-inline):

- DK-P01 calendar-flag materialization via the additive 13-feature superset config with `--force-recompute` (existing 8 fvers byte-preserved; record count `2192 -> 2312`, exactly `+120`).
- Relock of `opex`/`month_end`/`roll_week` to `LOCKED`.
- Per-study real surrogate-FDR calibration for all five StudySpecs (~2880 surrogate runs/study, single-threaded), producing the four `zero-pass-met` reports and the `roll_week` `CALIBRATION_BLOCKED` note.

Skipped / not run by the codex executor (per executor prompt):

- The codex executor did not materialize, relock, or run real calibration; it stopped at the substrate gap by design. Those steps were completed by the coordinator out-of-loop (above).
- `git diff -- src/alpha_system/strategies/templates.py` was skipped because the executor prompt explicitly forbade `git diff`. The executor did not edit `src/alpha_system/strategies/templates.py` or `core/value_store.py`.
- Reviewer and verdict are owned by the harness; merge/state-surgery/resume are coordinator-owned and are not performed in this handoff/PR-preparation step.

## Artifact And Safety Notes

- No `runs/**` artifact was created or staged by the executor; the referenced run artifact directory was absent in this checkout.
- No `review.md` or `verdict.json` was created.
- No calibration report was written under a forbidden namespace.
- No raw data, canonical data, DB, SQLite, Parquet, Arrow, Feather, DBN, Zstandard, cache, secret, model, or log artifact was intentionally created.
- No real-data IC, return, diagnostic, signal, or cost metric was inspected or recorded.
- No live trading, paper trading, broker operation, order routing, deployment, PR, merge, or external provider call was performed.
- No alpha, profitability, tradability, or promotion claim is made.

## Files Changed

- `tools/discovery_rigor_floor/run_real_surrogate_calibration.py`
- `tests/unit/discovery_rigor_floor/test_real_surrogate_calibration_tool.py`
- `tests/unit/differentiated_killshot/test_dk_p02_study_specs.py`
- `research/differentiated_substrate_v1/study_specs/day_of_week.json`
- `research/differentiated_substrate_v1/study_specs/opex.json`
- `research/differentiated_substrate_v1/study_specs/month_end.json`
- `research/differentiated_substrate_v1/study_specs/roll_week.json`
- `research/differentiated_substrate_v1/study_specs/open_close.json`
- `research/differentiated_substrate_v1/study_specs/RUNBOOK.md`
- `research/differentiated_substrate_v1/surrogate_fdr/day_of_week_calibration.md` (coordinator, value-free, `zero-pass-met`)
- `research/differentiated_substrate_v1/surrogate_fdr/opex_calibration.md` (coordinator, value-free, `zero-pass-met`)
- `research/differentiated_substrate_v1/surrogate_fdr/month_end_calibration.md` (coordinator, value-free, `zero-pass-met`)
- `research/differentiated_substrate_v1/surrogate_fdr/open_close_calibration.md` (coordinator, value-free, `zero-pass-met`)
- `research/differentiated_substrate_v1/surrogate_fdr/roll_week_calibration.md` (coordinator, value-free, `CALIBRATION_BLOCKED` / DATA_GAP)
- `handoffs/DIFFERENTIATED_KILLSHOT_V1/DK-P02.md`

Coordinator-infra (separate labeled commit, not phase deliverable):

- `configs/features/scaleout/session_calendar_maintenance_dk_p02_superset.json` (the additive 13-feature superset used to materialize the five DK-P01 flags; copied into this worktree from the main worktree).

## Caveats / Risks

- DK-P02 surrogate-FDR done criteria are met for four of five mechanisms (`zero-pass-met` reports present). `roll_week_flow` is a recorded DATA_GAP (`CALIBRATION_BLOCKED`), not a pass and not a leakage event; it is excluded from DK-P03 real-metric inspection. The active testable surface into DK-P03 is four mechanisms.
- Calendar-coverage caveat: `month_end`/`quarter_end`/`roll_week` conditioning flags are effectively populated only over the 2024-26 window; earlier partitions are all-null and excluded under the sanctioned `all_null_values` path. `month_end` still cleared on the surviving partitions; `roll_week` had every partition excluded and so blocked.
- `runs/**` is local-only and is not staged/committed; no `runs/` path is part of this PR. Merge, `state.json` surgery, STOP handling, and resume are coordinator-owned and are not done here.

## Review Focus

If Ralph routes this to review after resolving the blocker, focus on:

- The declared-conditioning admission remains opt-in and fail-closed.
- Same-family incidental `session_calendar_roll` support locks are not treated as tested factors.
- `factor_id` identity remains preserved.
- The StudySpecs are value-free and pool ES/NQ/RTY with the intended horizons and budgets.
- No real metric or non-value-free report is present; all reports record gate outcomes and the declared threshold only.

## Next Recommended Step

DK-P02 is complete: four Track A mechanisms carry a clean value-free `zero-pass-met` surrogate-FDR gate and `roll_week` is a recorded DATA_GAP. Proceed to DK-P03 real-metric inspection on the four-mechanism active testable surface (`day_of_week_effect`, `opex_pinning`, `month_end_flow`, `open_close_auction_flow`), respecting the FDR budget restated to the active zero-feed subset. Do not re-admit `roll_week_flow` without a substrate carrying a non-degenerate roll-window conditioning feature.
