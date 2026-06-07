# FUTCORE-P24 Handoff

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P24` - Bounded Grid / Variant Budget Audit  
Executor: Codex  
Lane: Yellow

## Scope Completed

Created the value-free bounded-grid / VariantBudget audit over committed
`FUTCORE-P14` through `FUTCORE-P23` evidence only. The audit reconciles every
approved StudySpec's declared `variant_budget: 4` against explicit variant-grid
cells recorded or reached by the P16-P20 diagnostics, then records locked-test
tuning and repeated-OOS-selection checks.

No diagnostics were rerun. No StudySpec, AlphaSpec, diagnostics report,
`src/alpha_system/**` primitive, review artifact, verdict artifact, run-local
handoff, PR, merge, staging action, commit, push, broker/live/paper/order
surface, deployment surface, or phase PASS marking was created by Codex.

Commit-eligible files for Ralph to stage explicitly:

- `research/futures_core_alpha_pilot_v1/audits/variant_budget/variant_budget_audit.md`
- `docs/futures_core_alpha_pilot/VARIANT_BUDGET_AUDIT.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P24.md`

Files staged by Codex: none. The executor instructions explicitly forbade
`git add`, `git commit`, `git push`, `git status`, and `git diff`; all changes
were left unstaged for Ralph.

No `runs/**` path should be staged.

## Audit Disposition Summary

Per-study dispositions:

| Disposition | Study count | StudySpecs |
| --- | ---: | --- |
| `PASS` | 2 | `sspec_267cc052e37668339c38d179`, `sspec_9f6f741192a4b534f06e51c0` |
| `WARN` | 8 | four `cross_market`, two `vwap_session`, and two `liquidity_pa` StudySpecs whose diagnostics were rejected or blocked before variant-grid execution and lacked explicit `observed_variant_count` fields |
| `FAIL` | 0 | none |

Campaign rollup:

- Approved StudySpec cap held: 10 of 10.
- Declared total variant cap: 40.
- Explicit actual variant-grid cells recorded or reached in committed
  diagnostics: 8.
- No StudySpec exceeded its declared VariantBudget.
- No locked-test tuning was detected.
- No repeated OOS selection was detected.

WARN findings are evidence-format gaps, not favorable-evidence claims:

- `VB-P24-W1`: P16 cross-market reports lack explicit `observed_variant_count`
  after pre-grid rejection.
- `VB-P24-W2`: P17 VWAP reports lack explicit `observed_variant_count` after
  signal-probe blocking.
- `VB-P24-W3`: P19 liquidity/PA reports lack explicit `observed_variant_count`
  after trigger-grid blocking.

## Validation

Commands run from the provided WSL2 worktree root:

| Command | Outcome |
| --- | --- |
| `test ! -e runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/STOP` | Passed, exit code `0`; no active run-level STOP file was present. |
| `python tools/verify.py --smoke` | Passed, exit code `0`; command produced no output. |
| `test -f research/futures_core_alpha_pilot_v1/audits/variant_budget/variant_budget_audit.md` | Passed, exit code `0`; command produced no output. |
| `test -f docs/futures_core_alpha_pilot/VARIANT_BUDGET_AUDIT.md` | Passed, exit code `0`; command produced no output. |
| `test -f handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P24.md` | Passed, exit code `0`; command produced no output. |
| `git ls-files runs` | Passed, exit code `0`; output empty. |
| `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.dbn' '**/*.zst'` | Passed, exit code `0`; output empty. |
| `test ! -e reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P24/review.md` | Passed, exit code `0`; no review artifact created by Codex. |
| `test ! -e reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P24/verdict.json` | Passed, exit code `0`; no verdict artifact created by Codex. |
| `test ! -e runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/phases/FUTCORE-P24/review.md` | Passed, exit code `0`; no run-local review artifact created by Codex. |
| `test ! -e runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/phases/FUTCORE-P24/verdict.json` | Passed, exit code `0`; no run-local verdict artifact created by Codex. |

Supporting local sanity check:

- `if LC_ALL=C grep -nP '[^\x00-\x7F]' research/futures_core_alpha_pilot_v1/audits/variant_budget/variant_budget_audit.md docs/futures_core_alpha_pilot/VARIANT_BUDGET_AUDIT.md README.md handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P24.md; then exit 1; else exit 0; fi`
  passed, exit code `0`; no non-ASCII bytes were found.

Spec-listed commands intentionally not run by Codex due to the explicit user
override:

- `git status --short`
- `git diff --cached --name-only`
- `git add`, `git commit`, and `git push`
- Claude review, reviewer execution, `review.md`, `verdict.json`, PR creation,
  CI, merge, merge gate, verdict parsing, and done-check

Yellow-lane broader checks (`lint`, `typecheck`, `test`, `verify_canaries`) are
Ralph-owned for orchestration in `CHECKS_RUN`.

## Artifact And Boundary Confirmation

- The audit and docs page are value-free: ids, counts, statuses, references,
  paths, and dispositions only.
- No raw/canonical market data, provider response, row-level feature value,
  row-level label value, signal value, Parquet, SQLite, DB, cache, log, model
  binary, local registry payload, or run-local artifact was created or copied.
- No `runs/**` file was created, staged, or committed by Codex.
- No consumed primitive under `src/alpha_system/**` was modified.
- No external provider call, raw provider read, arbitrary Parquet/SQLite read,
  feature materialization, label materialization, or runtime diagnostics rerun
  was performed.
- No broker/live/paper/order/account/deployment behavior was touched.
- No alpha, profitability, tradability, production, paper/live, broker,
  deployment, or capital-allocation claim is made.

Ralph remains responsible for authoritative staging, commit, validation ledger,
review routing, verdict parsing, PR, CI, merge gate, merge, and phase
done-check.
