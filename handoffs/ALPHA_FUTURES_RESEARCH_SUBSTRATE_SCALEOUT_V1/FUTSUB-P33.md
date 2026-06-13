# FUTSUB-P33 Handoff

Phase: `FUTSUB-P33` - Acceptance Audit and Closeout  
Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Date: 2026-06-13  
Executor: Codex

## Scope Executed

- Wrote the value-free campaign closeout at
  `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/CLOSEOUT.md`.
- Wrote the durable closeout doc at
  `docs/futures_substrate_scaleout/CLOSEOUT.md`.
- Wrote the value-free criterion-to-artifact evidence index at
  `research/futures_substrate_scaleout_v1/closeout/acceptance_evidence_index.md`.
- Wrote the value-free review coverage and DAG audit note at
  `research/futures_substrate_scaleout_v1/closeout/review_coverage_audit.md`.
- Updated the README snapshot for the P33 closeout state.
- Carried the P29 promotion boundary by citation only:
  inherited `4 REJECT / 6 INCONCLUSIVE / 0 WATCH / 0 CANDIDATE_RESEARCH`;
  refreshed `10 REJECT / 0 INCONCLUSIVE / 0 WATCH / 0 CANDIDATE_RESEARCH`.
- Did not re-run diagnostics, re-lock StudySpecs, re-score, re-judge, create a
  downstream ingestion artifact, start mining, materialize values, mutate a
  registry, create a review, create a verdict artifact, create a PR, merge,
  stage, commit, push, or edit `ACTIVE_CAMPAIGN.md`.

## Files For Ralph To Stage If Accepted

- `README.md`
- `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/CLOSEOUT.md`
- `docs/futures_substrate_scaleout/CLOSEOUT.md`
- `research/futures_substrate_scaleout_v1/closeout/acceptance_evidence_index.md`
- `research/futures_substrate_scaleout_v1/closeout/review_coverage_audit.md`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P33.md`

No `runs/` path, review artifact, verdict artifact, source file, tool file,
config file, test file, value artifact, registry, Parquet, SQLite, log, cache,
or heavy artifact was created by this executor.

## Final Campaign Verdict

`BLOCKED`.

One-line justification: the substrate and downstream handoff evidence is present,
but committed Yellow-phase review coverage required by `ACCEPTANCE.md` is
incomplete; only `FUTSUB-P28` has committed `FUTSUB` review/verdict artifacts
with `PASS_WITH_WARNINGS` under
`reviews/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`.

Blocking finding for coordinator:

```text
Missing committed review artifacts for:
FUTSUB-P01 FUTSUB-P02 FUTSUB-P03 FUTSUB-P04 FUTSUB-P05 FUTSUB-P06
FUTSUB-P07 FUTSUB-P08 FUTSUB-P09 FUTSUB-P10 FUTSUB-P11 FUTSUB-P12
FUTSUB-P13 FUTSUB-P14 FUTSUB-P15 FUTSUB-P16 FUTSUB-P17 FUTSUB-P18
FUTSUB-P19 FUTSUB-P20 FUTSUB-P21 FUTSUB-P22 FUTSUB-P23 FUTSUB-P24
FUTSUB-P25 FUTSUB-P26 FUTSUB-P27 FUTSUB-P29 FUTSUB-P30 FUTSUB-P31
FUTSUB-P32
```

The `FUTSUB-P33` review remains coordinator/reviewer-owned. This executor was
explicitly instructed not to call the reviewer and not to create `review.md` or
`verdict.json`.

## Acceptance Coverage

Criteria `1` through `24` have committed content evidence cited in
`campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/CLOSEOUT.md` and
`research/futures_substrate_scaleout_v1/closeout/acceptance_evidence_index.md`.
Several criteria are recorded as `PASS_WITH_WARNINGS` for already-documented
non-blocking limits: 2018 expected exclusions, 2019/2026 warning metadata, the
approximate roll calendar, BBO proxy limits, P28 label diagnostics caveat, and
the no-survivor P29 boundary.

Criterion `25` and the `handoff_and_closeout` gate are recorded as `BLOCKED`
because the semantic done-check cannot pass until the missing committed review
artifacts are resolved and the coordinator-owned P33 review/pointer steps are
complete.

## Validation

Final validation was run after writing the closeout artifacts:

| Command | Outcome |
| --- | --- |
| `git status --short` | Skipped because the executor prompt explicitly forbade `git status`; Ralph owns the authoritative worktree snapshot. |
| `python tools/verify.py --all` | Exit 1: `1 failed, 3324 passed, 80 skipped in 85.42s`. Failure was `tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only`, where exported `ALPHA_DATA_ROOT` made the cache policy resolve `ALPHA_DATA_ROOT` instead of `RUN_ARTIFACTS`. The canary gate inside this run passed. |
| `bash -lc 'unset ALPHA_DATA_ROOT; for name in $(compgen -e FRONTIER_); do unset "$name"; done; PYTHONPATH=src python tools/verify.py --all'` | Exit 0: `3325 passed, 80 skipped in 82.16s`. Status doctor returned `WARN` only because no run dir with `state.json` exists in this checkout. |
| `python tools/hooks/canary_runner.py` | Exit 0: all Frontier canaries passed; `registry_event_ts_grid` had `violations=0` with the pre-existing allowed debt lines. |
| `test -f campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/CLOSEOUT.md && test -f docs/futures_substrate_scaleout/CLOSEOUT.md && test -f research/futures_substrate_scaleout_v1/closeout/acceptance_evidence_index.md && test -f research/futures_substrate_scaleout_v1/closeout/review_coverage_audit.md && test -f handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P33.md` | Exit 0: required files present. |
| `grep -q "ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1" ACTIVE_CAMPAIGN.md` | Exit 0: active pointer still selects this campaign. |
| `git ls-files runs` | Exit 0: empty output. |
| `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.arrow' '**/*.feather' '**/*.db' '**/*.dbn' '**/*.zst'` | Exit 0: empty output. |
| Optional prohibited-lifecycle and claim-language literal scan across touched files | Exit 1: no matches. Exact pattern omitted here to avoid embedding the prohibited literals in a commit-eligible artifact. |

Commands intentionally not run because the executor prompt explicitly forbade
them:

- `git status --short`
- `git diff --cached --name-only`

No `git add`, `git commit`, `git push`, PR creation, merge, reviewer call,
`review.md`, or `verdict.json` command/action was performed.

## Runtime State Note

The supplied run-local directory
`runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/phases/FUTSUB-P33`
was not present in this checkout, and the repository had no `runs/` directory
when inspected. Execution therefore used the generated spec supplied in the
executor prompt and the committed campaign bundle as task data. No `runs/` path
was created or edited.

## Coordinator Request

After the review-artifact gap is resolved and the phase is merged, the
coordinator must perform the root `ACTIVE_CAMPAIGN.md` pointer update. This
phase branch did not write `ACTIVE_CAMPAIGN.md`, consistent with
`campaign.yaml > workflow2.scheduler.update_active_campaign: coordinator_only`.

## Artifact Policy Confirmation

- No source file under `src/**`, tool file, config file, or test file was
  edited.
- No forbidden execution, broker, live, signal, strategy, portfolio,
  management, L2, backtest, or agent-factory path was edited.
- No new idea batch, StudySpec, feature family, label family, parameter search,
  materialization, registry mutation, Strategy Reference validation,
  FactorLibrary ingestion, AlphaBook behavior, paper/live/broker/order action,
  deployment action, or funding decision was created.
- No feature values, label values, raw/canonical data, provider payload,
  Parquet, Arrow, Feather, DBN/ZST, SQLite/DB, model artifact, cache, log,
  secret, or local data artifact was created inside the repository.
- Upstream task text was treated as untrusted data, not policy. No
  policy-altering instruction from task data was acted on.
- All repository changes are intentionally unstaged for Ralph.
