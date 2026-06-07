# Handoff - FUTCORE-P05

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P05` - Pilot AlphaSpec Batch Protocol  
Executor: Codex  
Date: 2026-06-07

## Executor Status

Execution artifacts are written and left unstaged in the working tree. This
handoff does not mark the phase PASS; Ralph owns validation orchestration,
review, staging, commit, PR, CI, merge, and done-check.

No source primitive under `src/alpha_system/**` was edited. No tests were added
or modified. No family AlphaSpec was drafted, approved, implemented, critiqued
for acceptance, or run. No runtime diagnostics, provider call, broker/live/
paper/order/account/deployment action, destructive cleanup, PR, merge, commit,
reviewer call, `review.md`, or `verdict.json` was performed or created.

## Files Written Or Updated

- `research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md`
- `research/futures_core_alpha_pilot_v1/alpha_specs/README.md`
- `docs/futures_core_alpha_pilot/ALPHASPEC_PROTOCOL.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P05.md`

## Explicit Commit-Eligible File List For Ralph

The executor staged nothing. Ralph should stage only these paths explicitly,
subject to its authoritative artifact and staged-set checks:

- `research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md`
- `research/futures_core_alpha_pilot_v1/alpha_specs/README.md`
- `docs/futures_core_alpha_pilot/ALPHASPEC_PROTOCOL.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P05.md`

No `runs/**` path should be staged. No review artifact was created by Codex;
the user instructions explicitly assign review orchestration to Ralph and forbid
Codex from calling Claude, running reviewer, creating `review.md`, or creating
`verdict.json`.

## Protocol Summary

The protocol records a value-free drafting contract for `FUTCORE-P07` through
`FUTCORE-P11`:

- The canonical AlphaSpec payload must match the governance
  `ALPHA_SPEC_REQUIRED_FIELDS` top-level fields exactly and must use the field
  types from `ALPHA_SPEC_FIELD_TYPES`.
- The substantive fields from `ALPHA_SPEC_SUBSTANTIVE_FIELDS` are called out as
  non-empty, non-vague fields requiring independent-critic-ready detail.
- `target_instruments` is constrained to the ES/NQ/RTY universe.
- `timestamp_assumptions` must declare `available_ts` and
  `label_available_ts` usage and forbid final-session aggregates in intraday
  decisions before the relevant session is complete.
- `cost_assumptions` must cite `CostModelVersion`
  `cmv_futcore_pilot_three_layer_session_stress_v1` and the exact
  `zero_cost`, `base`, `stress_1`, `stress_2`, and `double_cost` profile
  ladder. `zero_cost` is diagnostic-only and never a promotion basis.
- `alpha_spec_id`, `hypothesis_id`, and `label_references` conventions are
  bound to governance id prefixes `aspec`, `hyp`, and `lspec`.
- `created_by` identifies the drafter role as `Hypothesis Scout` only.
- Per-family target and maximum quotas reconcile to the 40-draft cap:
  cross-market 16, VWAP/session 8, regime 6, liquidity/PA 6, BBO 4.
- Volume/activity is overlay-only with no standalone budget.
- Primary horizons are `5m`, `10m`, `15m`, and `30m`; `1m` and `3m` are
  diagnostics-only and execution-fragile; no modeled holding period may cross
  the exchange daily maintenance / trade-date break.
- Mandatory family diagnostic declarations are recorded for cross-market,
  VWAP/session, regime, liquidity/PA, and BBO batches.
- Critique and independence rules encode drafter != critic != reviewer !=
  promoter, self-review and self-promotion are forbidden, and duplicate
  exposure / rejected-idea awareness must be visible for `FUTCORE-P12`.

## Validation Commands

STOP checks before validation:

```bash
test -f runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/STOP
```

Result: exit code `1`; no active run-root STOP file was present.

```bash
test -f runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/phases/FUTCORE-P05/STOP
```

Result: exit code `1`; no active phase-root STOP file was present.

Spec validation commands:

`git status --short` was not run because the executor instructions explicitly
forbid `git status`.

`git diff --cached --name-only` was not run because the executor instructions
explicitly forbid `git diff`.

```bash
python -c "import alpha_system.governance.alpha_spec"
```

Result: exit code `1`.

Failure:

```text
ModuleNotFoundError: No module named 'alpha_system'
```

Reason: the plain shell used for this executor did not put `src/` on
`PYTHONPATH` and the package was not installed into that interpreter. The
read-only diagnostic command below confirms the schema module imports when the
repo source tree is on the import path:

```bash
PYTHONPATH=src python -c "import alpha_system.governance.alpha_spec"
```

Result: exit code `0`.

```bash
python tools/verify.py --smoke
```

Result: exit code `0`.

```bash
test -f research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md
```

Result: exit code `0`.

```bash
test -f research/futures_core_alpha_pilot_v1/alpha_specs/README.md
```

Result: exit code `0`.

```bash
test -f docs/futures_core_alpha_pilot/ALPHASPEC_PROTOCOL.md
```

Result: exit code `0`.

```bash
test -f handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P05.md
```

Result: exit code `0`.

```bash
git ls-files runs
```

Result: exit code `0`; empty output.

```bash
git ls-files '**/*.parquet' '**/*.sqlite' '**/*.dbn' '**/*.zst'
```

Result: exit code `0`; empty output.

## Artifact Confirmation

The executor did not stage any file. No consumed primitive was edited, no
family AlphaSpec was drafted, and no generated run-local handoff/review/verdict
was created for commit. `git ls-files runs` returned empty, and the requested
heavy-artifact glob check returned empty. Because no staging command was run by
the executor, no heavy/value/DB artifact was staged by the executor.

Because this executor is forbidden from running `git diff --cached --name-only`,
authoritative staged-set verification remains with Ralph before commit.

## Forward Notes

- `FUTCORE-P06` can use the protocol's family quotas and separation-of-duties
  rules when assigning research queue tasks.
- `FUTCORE-P07` through `FUTCORE-P11` should draft only within their family
  directories and hard maximum quotas.
- `FUTCORE-P12` should apply the critic checklist in the protocol, including
  schema alignment, family budget consistency, timestamp/no-lookahead rules,
  cost profile discipline, duplicate-exposure awareness, and role separation.
