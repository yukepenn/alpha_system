# FUTSUB-P28 Handoff

Phase: `FUTSUB-P28` - Re-run Previously INCONCLUSIVE Core Pilot Studies  
Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Date: 2026-06-13  
Executor: Codex bounded repair attempt

## Scope Executed

- Read the P110000 V2 re-lock report at
  `research/futures_substrate_scaleout_v1/rerun/studyspec_relock.md`.
- Identified the six prior-INCONCLUSIVE V2 StudySpecs classified as P28 rerun
  candidates.
- Re-resolved every committed feature and label lock for those six StudySpecs
  through the local runtime resolver surfaces:
  `FeatureLabelPackResolver.resolve_feature_packs` and
  `FeatureLabelPackResolver.resolve_label_packs`.
- Re-executed the value replay under the Parquet-capable research interpreter:
  `/home/yuke_zhang/.venvs/alpha_system_research/bin/python`.
- Loaded locked feature and label values from local Parquet under
  `ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system`, joined runtime
  observations by exact `entity_id,event_ts`, and required feature
  `available_ts` before label `available_ts`.
- Invoked runtime factor diagnostics over all locked 5m, 10m, 15m, and 30m
  label horizons with purge gap 10 / embargo gap 10 walk-forward context.
- Invoked runtime label diagnostics and N_eff reporting.
- Wrote value-free docs and handoff artifacts only.

This handoff does not mark the phase complete, does not mark the phase pass,
and does not authorize `FUTSUB-P29` to refresh verdicts without Ralph/review
handling.

## Files Staged

None. Changes are intentionally unstaged for the Workflow 2 driver.

Current `git status --short`:

```text
 M README.md
?? docs/futures_substrate_scaleout/CORE_PILOT_RERUN.md
?? handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P28.md
?? research/futures_substrate_scaleout_v1/rerun/rerun_diagnostics_summary.md
```

## Files For Ralph To Stage If Accepted

- `README.md`
- `research/futures_substrate_scaleout_v1/rerun/rerun_diagnostics_summary.md`
- `docs/futures_substrate_scaleout/CORE_PILOT_RERUN.md`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P28.md`

No review artifact, verdict artifact, run-local handoff, PR, merge, staging, or
commit was created by the executor.

## Bounded Repair Notes

- No fresh Claude review exists in this worktree, and this repair attempt did
  not create one. The executor therefore does not claim `PASS`,
  `PASS_WITH_WARNINGS`, or phase completion; Ralph must route fresh review and
  reconcile any prior rejected review provenance.
- The R-019 N_eff concern is now documented against the P25 runtime surface:
  `build_n_eff_sample_report` with explicit horizon-overlap metadata,
  `coerce_horizon_overlap_metadata` fail-closed validation, formula
  `floor(rows / discount_factor)`, and P24 fold attachment through
  `attach_n_eff_to_walk_forward_metadata`. The scratch replay summary preserved
  registered rows, discount factors, rows-not-independent markers,
  session/day aggregation, compact fold count, purge gap 10, and embargo gap
  10.
- Label diagnostics remain a real residual caveat: all six studies returned
  `DIAGNOSTICS_FAILED` at `label_coverage_missingness_gate` because no separate
  feature/label audit bundle was supplied. Numeric label rows loaded and
  availability checks passed, but `FUTSUB-P29` must not treat this as a clean
  label-diagnostics rerun.

## Re-run Set And Outcomes

| Family | Original StudySpec | V2 StudySpec | Feature locks | Label locks | Outcome |
| --- | --- | --- | ---: | ---: | --- |
| `regime` | `sspec_267cc052e37668339c38d179` | `sspec_dec89a327a9c50957adca780` | 456/456 | 96/96 | resolver clean; Parquet replay complete for factor diagnostics |
| `liquidity_pa` | `sspec_27bf1262b0bd23d27191cc86` | `sspec_840e8342564226f2c3257903` | 552/552 | 96/96 | resolver clean; Parquet replay complete for factor diagnostics |
| `liquidity_pa` | `sspec_02c400a561891171a33c0c66` | `sspec_c237c6a8ce40c2585836fae0` | 552/552 | 96/96 | resolver clean; Parquet replay complete for factor diagnostics |
| `bbo_tradability` | `sspec_9f6f741192a4b534f06e51c0` | `sspec_533f665ec4ac063dbb664a54` | 600/600 | 96/96 | resolver clean; Parquet replay complete for factor diagnostics |
| `vwap_session` | `sspec_aff70fcbc4b7ff226fcc8149` | `sspec_1604b063f3a3401208ee0239` | 480/480 | 96/96 | resolver clean; Parquet replay complete for factor diagnostics |
| `vwap_session` | `sspec_69c22ec5847395ac8e81b5b6` | `sspec_f6cbd88caa0445f0f56d81fd` | 480/480 | 96/96 | resolver clean; Parquet replay complete for factor diagnostics |

The re-locked cross-market StudySpecs were not rerun because the V2 re-lock
report classifies them as prior-REJECT audit-only inputs, not prior-INCONCLUSIVE
P28 rerun candidates.

## Diagnostics Observed

Runtime factor diagnostics returned `DIAGNOSTICS_COMPLETE` for all six
StudySpecs. All figures are aggregate value-free summaries from runtime reports.

| V2 StudySpec | Family | Rows | Numeric pairs | Coverage | Missingness | Pearson IC | Rank IC | WF folds |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `sspec_dec89a327a9c50957adca780` | `regime` | 74,592 | 72,441 | 0.9712 | 0.0288 | -0.0204 | -0.0002 | 67 |
| `sspec_840e8342564226f2c3257903` | `liquidity_pa` | 74,304 | 72,595 | 0.9770 | 0.0230 | 0.0072 | 0.0008 | 67 |
| `sspec_c237c6a8ce40c2585836fae0` | `liquidity_pa` | 74,304 | 72,595 | 0.9770 | 0.0230 | 0.0072 | 0.0008 | 67 |
| `sspec_533f665ec4ac063dbb664a54` | `bbo_tradability` | 74,976 | 66,877 | 0.8920 | 0.1080 | -0.0050 | 0.0008 | 61 |
| `sspec_1604b063f3a3401208ee0239` | `vwap_session` | 74,880 | 66,067 | 0.8823 | 0.1177 | 0.0033 | -0.0011 | 61 |
| `sspec_f6cbd88caa0445f0f56d81fd` | `vwap_session` | 74,880 | 66,067 | 0.8823 | 0.1177 | 0.0033 | -0.0011 | 61 |

Label rows loaded for all six StudySpecs. A corrected label replay used the
runtime's established observation-summary configuration for supplied label
observations without a separate feature/label audit bundle. Runtime label
diagnostics returned `DIAGNOSTICS_FAILED` with `weak_diagnostics` because the
`label_coverage_missingness_gate` fails closed without that separate audit
bundle. Each run had 74,976 label observations, 74,976 numeric outcomes, 4/4
horizon coverage, missing outcome rate 0, valid label availability timestamps,
and declared cost-model metadata. This is a real fail-closed caveat for
`FUTSUB-P29`; it is not a missing-reader or missing-substrate gap.

## N_eff Context

N_eff was produced through the P25 runtime reporting surface
`build_n_eff_sample_report`, using registered label row counts plus explicit
horizon-overlap metadata for the locked 5m/10m/15m/30m labels. The supplied
metadata used 1-minute sampling cadence and discount factors equal to the
horizon minutes. Runtime validation flows through
`coerce_horizon_overlap_metadata`; inconsistent or missing overlap metadata
would fail closed. The reported formula is `floor(rows / discount_factor)`,
bounded to `[0, rows]`, with `rows_are_not_independent_samples` marked true.

| Horizon | Registered rows | Overlap discount | N_eff |
| --- | ---: | ---: | ---: |
| `fwd_ret_5m` | 7,455,294 | 5 | 1,491,058 |
| `fwd_ret_10m` | 7,416,879 | 10 | 741,687 |
| `fwd_ret_15m` | 7,379,178 | 15 | 491,945 |
| `fwd_ret_30m` | 7,294,349 | 30 | 243,144 |

The scratch replay summary preserved compact P24/P25 provenance fields:
registered rows, discount factor, `rows_are_not_independent_samples`,
session/day aggregation, compact fold count, purge gap 10, and embargo gap 10.
The factor diagnostics replay used purge gap 10 and embargo gap 10
walk-forward context over the in-memory observation samples.

## Validation

| Command | Outcome |
| --- | --- |
| `python tools/frontier/status_doctor.py` | WARN, exit 0; core checks ok, no live run directory found for this campaign worktree |
| `git status --short` | RUN after repair; showed only P28 allowed-path changes |
| `ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python - <<'PY' ...` | PASS, exit 0; wrote `/tmp/futsub_p28_repair_rerun.json`; all six StudySpecs resolver-clean and real rows loaded |
| `ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python - <<'PY' ...` | PASS, exit 0; wrote `/tmp/futsub_p28_all_horizon_factor.json`; all six factor diagnostics returned `DIAGNOSTICS_COMPLETE` over all locked horizons |
| `ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python - <<'PY' ...` | PASS, exit 0; wrote `/tmp/futsub_p28_label_repair_rerun.json`; all six label diagnostics loaded numeric rows and returned only the fail-closed coverage/missingness warning |
| `PYTHONPATH=src python tools/verify.py --smoke` | PASS, exit 0, no output |
| `PYTHONPATH=src python -c "import alpha_system.runtime, alpha_system.experiments.splits"` | PASS, exit 0, no output |
| `python tools/hooks/canary_runner.py` | PASS, exit 0; all Frontier canaries passed |
| `test -f research/futures_substrate_scaleout_v1/rerun/rerun_diagnostics_summary.md` | PASS, exit 0, no output |
| `test -f docs/futures_substrate_scaleout/CORE_PILOT_RERUN.md` | PASS, exit 0, no output |
| `git ls-files runs` | PASS, empty output |
| `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.arrow' '**/*.feather' '**/*.dbn' '**/*.zst'` | PASS, empty output |
| `git ls-files '**/*.db' '**/*.duckdb' '**/*.log'` | PASS, empty output |
| `git diff --cached --name-only` | PASS, empty output; nothing staged |
| `git diff --check` | PASS, exit 0, no output |

## Artifact Policy Confirmation

- No source file under `src/**` was edited.
- No `execution/`, `broker/`, `live/`, `signals/`, `strategies/`,
  `portfolio/`, `management/`, `l2/`, `backtest/`, or `agent_factory/` path was
  edited.
- No new AlphaSpec, StudySpec, feature family, label family, parameter search,
  verdict refresh, promotion, Strategy Reference, AlphaBook, broker, paper,
  live, order, deployment, or capital-allocation behavior was created.
- No feature values, label values, raw/canonical data, provider payload,
  Parquet, Arrow, Feather, DBN/ZST, SQLite/DB, model artifact, cache, log,
  secret, or local data artifact was created inside the repository.
- `/tmp/futsub_p28_repair_rerun.json` and
  `/tmp/futsub_p28_all_horizon_factor.json` and
  `/tmp/futsub_p28_label_repair_rerun.json` are scratch execution summaries only
  and are not commit-eligible.
- All repository changes are unstaged for Ralph.

## Review / Next Phase

No Claude call was made, no reviewer was run, no `review.md` was created, and
no `verdict.json` was created, per the executor prompt.

Next planned phase remains `FUTSUB-P29` - Honest Verdict Refresh and Scaleout
Evidence Summary - only after Ralph validation and review handling. P29 must
carry the label coverage/missingness fail-closed caveat and must not consume
this handoff as a phase-pass verdict.
