# FUTSUB-P29 Handoff

Phase: `FUTSUB-P29` - Honest Verdict Refresh and Scaleout Evidence Summary  
Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Date: 2026-06-13  
Executor: Codex

## Scope Executed

- Consumed the committed `FUTSUB-P27` re-lock and `FUTSUB-P28` rerun evidence.
- Wrote the value-free refreshed verdict summary at
  `research/futures_substrate_scaleout_v1/rerun/verdict_refresh.md`.
- Wrote the durable docs mirror at
  `docs/futures_substrate_scaleout/VERDICT_REFRESH.md`.
- Updated the README snapshot for the post-`FUTSUB-P29` merge state.
- Assigned only allowed states: `REJECT`, `INCONCLUSIVE`, `WATCH`, and
  `CANDIDATE_RESEARCH`.
- Refreshed the boundary from inherited `4 REJECT / 6 INCONCLUSIVE / 0 WATCH /
  0 CANDIDATE_RESEARCH` to `10 REJECT / 0 INCONCLUSIVE / 0 WATCH /
  0 CANDIDATE_RESEARCH`.
- Did not assign any `WATCH` or `CANDIDATE_RESEARCH` state, so this executor did
  not create an independent reviewer verdict artifact. Yellow-lane fresh review
  remains Ralph/reviewer-owned.

This handoff does not mark the phase `PASS`, does not create a review, does not
create a verdict artifact, does not create a PR, and does not stage or commit
anything.

## Files For Ralph To Stage If Accepted

- `README.md`
- `research/futures_substrate_scaleout_v1/rerun/verdict_refresh.md`
- `docs/futures_substrate_scaleout/VERDICT_REFRESH.md`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P29.md`

No `runs/` path, review artifact, value artifact, registry, Parquet, SQLite, or
heavy artifact was created by this executor.

## Verdict Summary

| Universe | `REJECT` | `INCONCLUSIVE` | `WATCH` | `CANDIDATE_RESEARCH` |
| --- | ---: | ---: | ---: | ---: |
| Inherited Core Pilot | 4 | 6 | 0 | 0 |
| P29 refreshed boundary | 10 | 0 | 0 | 0 |

The six `FUTSUB-P28` rerun StudySpecs are refreshed to `REJECT` based on
resolver-clean P28 evidence, complete factor diagnostics, near-zero aggregate IC
summaries, false bucket monotonicity for every rerun, duplicate within-family
exposure caveats, and the retained label diagnostics fail-closed caveat. The
four prior cross-market `REJECT` states remain unchanged audit-only inputs.

## Residual Warnings

- Label diagnostics still returned `DIAGNOSTICS_FAILED` with `weak_diagnostics`
  at `label_coverage_missingness_gate` because no separate feature/label audit
  bundle was supplied. P29 carries that caveat and does not call label
  diagnostics a clean pass.
- P28 N_eff is first-order horizon-overlap metadata over registered label rows.
  It is not session-clustered or autocorrelation-adjusted and must not be
  conflated with the capped factor-diagnostics observation samples.
- Liquidity/PA and VWAP/session paired reruns have identical within-family
  factor summaries and are not independent survivor evidence.
- BBO remains a time-sampled, forward-filled top-of-book proxy, not execution
  truth or passive-fill, queue-position, or impact evidence.
- No run-local directory was present in this checkout; `runs/` was not edited,
  and `git ls-files runs` returned empty output.

## Validation

| Command | Outcome |
| --- | --- |
| `python tools/verify.py --smoke` | PASS, exit 0, no output |
| `test -f research/futures_substrate_scaleout_v1/rerun/verdict_refresh.md` | PASS, exit 0, no output |
| `test -f docs/futures_substrate_scaleout/VERDICT_REFRESH.md` | PASS, exit 0, no output |
| `test -f README.md` | PASS, exit 0, no output |
| `test -f handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P29.md` | PASS, exit 0, no output |
| `git ls-files runs` | PASS, exit 0, empty output |
| `git ls-files '**/*.parquet' '**/*.arrow' '**/*.feather' '**/*.sqlite' '**/*.db' '**/*.dbn' '**/*.zst'` | PASS, exit 0, empty output |

An optional forbidden uppercase lifecycle-state literal scan was run across the
research verdict refresh, durable doc, README, and this handoff after the final
handoff patch; it returned no matches (`rg` exit 1). The exact optional scan
command is not reproduced in this handoff to avoid embedding the prohibited
literals in a commit-eligible artifact.

Commands intentionally not run because the executor prompt explicitly forbade
them:

- `git status --short`
- `git diff --cached --name-only`

No `git add`, `git commit`, `git push`, PR creation, merge, reviewer call,
`review.md`, or `verdict.json` command/action was performed.

## Artifact Policy Confirmation

- No source file under `src/**` was edited.
- No forbidden execution, broker, live, signal, strategy, portfolio,
  management, L2, backtest, or agent-factory path was edited.
- No new AlphaSpec, StudySpec, feature family, label family, parameter search,
  materialization, registry mutation, Strategy Reference validation,
  FactorLibrary ingestion, AlphaBook behavior, paper/live/broker/order action,
  deployment action, capital-allocation decision, profitability claim, or
  tradability claim was created.
- No feature values, label values, raw/canonical data, provider payload,
  Parquet, Arrow, Feather, DBN/ZST, SQLite/DB, model artifact, cache, log,
  secret, or local data artifact was created inside the repository.
- All repository changes are intentionally unstaged for Ralph.
