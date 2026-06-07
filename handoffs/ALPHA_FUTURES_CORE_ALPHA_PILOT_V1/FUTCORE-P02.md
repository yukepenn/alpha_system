# Handoff - FUTCORE-P02

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P02` - Pilot Scope, Universe, Sessions, Horizons, and Research Budget  
Executor: Codex  
Date: 2026-06-07

## Executor Status

Execution artifacts are written and left unstaged in the working tree. This
handoff does not mark the phase PASS; Ralph owns validation orchestration,
review, staging, commit, PR, CI, merge, and done-check.

No source primitive under `src/alpha_system/**` was edited. No tests were added
or modified. No review artifact, `review.md`, or `verdict.json` was created. No
live, paper, broker, order, account, deployment, provider acquisition, or
destructive operation was performed.

## Files Written Or Updated

- `docs/futures_core_alpha_pilot/SCOPE.md`
- `research/futures_core_alpha_pilot_v1/scope/scope_contract.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P02.md`

## Staged Files

None. The executor did not run `git add`, `git commit`, `git push`,
`git status`, or `git diff` per the explicit Workflow 2 executor instructions.

Ralph should stage only the commit-eligible files listed above, subject to its
authoritative artifact and staged-set checks. No `runs/**` path should be
staged.

## Scope Contract Summary

| Scope item | Recorded value |
| --- | --- |
| In-scope universe | `ES`, `NQ`, `RTY` |
| Deferred universe | `MES`, `MNQ`, `M2K`, rates, FX, commodities, vol products, options, equities, L1 eventstream, L2/L3 |
| Required sessions | `full_session`, `RTH_only`, `ETH_only`, `ETH_evening`, `ETH_overnight`, `pre_RTH`, `RTH`, `post_RTH`, `RTH_with_ETH_context` |
| Sampling horizon | `1m` |
| Fragile horizons | `1m`, `3m`; diagnostics only with stricter later gates |
| Primary horizons | `5m`, `10m`, `15m`, `30m` |
| Extended horizons | `60m`, `120m`, `240m`, `session_close` |
| Maintenance boundary | Flat before exchange daily maintenance / trade-date break; no crossing |
| Family budget | `0.40`, `0.20`, `0.15`, `0.15`, `0.10`; sum `1.00` |
| Research caps | `<=40` drafts, `<=10` approved AlphaSpecs, `<=5` new feature/label requests, `<=3` diagnostics survivors, `<=2` `WATCH` or `CANDIDATE_RESEARCH` |
| Overlay rule | Volume/activity overlay only; no standalone budget; existing primitives only |

The scope contract includes the required `campaign.yaml` cross-reference table
for the recorded values and risk guardrails `R-001`, `R-010`, `R-011`,
`R-012`, `R-022`, `R-023`, and `R-025`.

## Validation Commands

```bash
test ! -f runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/STOP
```

Result: exit code `0`; no active STOP file was present.

`git status --short` was not run because the executor instructions explicitly
forbid `git status`.

```bash
python tools/verify.py --smoke
```

Result: exit code `0`.

```bash
test -f docs/futures_core_alpha_pilot/SCOPE.md && test -f research/futures_core_alpha_pilot_v1/scope/scope_contract.md && test -f README.md
```

Result: exit code `0`; all required files exist.

```bash
git ls-files runs
```

Result: exit code `0`; empty output.

```bash
git ls-files '**/*.parquet' '**/*.sqlite' '**/*.dbn' '**/*.zst'
```

Result: exit code `0`; empty output.

## Blockers Or Escalations

No scope blocker was recorded.

Executor safety exceptions / ownership notes:

- `git status --short` was skipped by explicit user instruction.
- No staged-set inspection was performed because the executor was instructed not
  to run `git diff`; the executor staged nothing.
- The prompt-provided run-local phase directory
  `runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/phases/FUTCORE-P02`
  was not present during execution. No run-local file was written.
- Yellow-lane review artifacts were not created by the executor. Ralph owns
  reviewer invocation and any commit-eligible review promotion.

## Artifact Confirmation

- `git ls-files runs` returned empty.
- Tracked heavy-artifact globs for `*.parquet`, `*.sqlite`, `*.dbn`, and `*.zst`
  returned empty.
- No `runs/**` file was written by this executor.
- No raw/canonical data, feature values, label values, Parquet, SQLite, provider
  responses, logs, caches, secrets, credentials, or local DB artifacts were
  written or committed by this executor.
