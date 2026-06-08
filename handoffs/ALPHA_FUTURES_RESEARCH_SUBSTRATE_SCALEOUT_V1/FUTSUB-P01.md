# FUTSUB-P01 Executor Handoff

Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Phase: `FUTSUB-P01` - Reality Report Lock and Core Pilot Handoff Ingestion  
Executor: Codex  
Lane: Yellow

## Status

Executor scope is complete for the documentation-ingestion and baseline-lock
portion of `FUTSUB-P01`. This handoff does not mark the phase PASS. Ralph owns
authoritative staging, commit, review routing, verdict parsing, PR, CI, merge,
and done-check actions.

No live trading, paper trading, broker operation, order routing, provider call,
runtime diagnostics run, primitive edit, value materialization, PR creation,
merge, reviewer call, `review.md`, or `verdict.json` was performed by Codex.

## Scope Completed

- Reconciled `docs/SUBSTRATE_REALITY_REPORT.md` and
  `research/futures_core_alpha_pilot_v1/closeout/SUBSTRATE_SCALEOUT_V1_HANDOFF.md`
  into `docs/futures_substrate_scaleout/REALITY_LOCK.md`.
- Recorded the inherited boundary:
  `4 REJECT / 6 INCONCLUSIVE / 0 WATCH / 0 CANDIDATE_RESEARCH`, with no
  FactorLibrary-ingestible survivor and no Strategy Reference candidate.
- Recorded the required substrate gaps: single-week ES-only OHLCV+session
  smoke value substrate; missing P18 regime values; missing P19 liquidity/PA
  primitives as values; missing P20 BBO top-book FeaturePack; missing full
  ES/NQ/RTY aligned cross-market values; `registered != accepted/locked`;
  unadjusted provider-continuous roll-splice gap with no materialized roll
  calendar; and `experiments/splits.py` not wired into runtime/N_eff reporting.
- Wrote the value-free preflight baseline at
  `research/futures_substrate_scaleout_v1/preflight/reality_baseline.md`.
- Confirmed consumed primitives import cleanly.
- Updated `README.md` per the README Snapshot Policy for the post-merge
  `FUTSUB-P01` state and next phase `FUTSUB-P02`.
- Wrote this commit-eligible handoff.

## Files Created Or Modified

Codex staged no files. Ralph stage candidates for this phase, by explicit path:

| Path | Outcome |
| --- | --- |
| `docs/futures_substrate_scaleout/REALITY_LOCK.md` | Created locked value-free reality baseline. |
| `research/futures_substrate_scaleout_v1/preflight/reality_baseline.md` | Created value-free preflight baseline. |
| `README.md` | Updated compact campaign snapshot for `FUTSUB-P01` and next phase `FUTSUB-P02`. |
| `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P01.md` | Created this commit-eligible handoff. |

No `reviews/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P01/**`
artifact was created by Codex because the executor prompt explicitly forbids
calling the reviewer, creating `review.md`, creating `verdict.json`, or marking
the phase PASS. Ralph owns Yellow-lane review routing.

## Git And Artifact Hygiene

- `git status --short`: not run. The executor prompt explicitly forbids
  `git status`; Ralph owns working-tree and staging hygiene.
- `git diff`, `git add`, `git commit`, `git push`, force push: not run.
- `git diff --cached --name-only`: not run. The executor prompt forbids
  `git diff`, and Codex staged no files.
- Staging: Codex performed no staging, so no `runs/` path, forbidden data path,
  DB/cache/log/heavy artifact, or `ACTIVE_CAMPAIGN.md` was staged by Codex.
- `git ls-files runs`: passed with empty output.
- `git ls-files '**/*.parquet' '**/*.arrow' '**/*.feather' '**/*.sqlite' '**/*.db' '**/*.dbn' '**/*.zst'`:
  passed with empty output.
- The advertised run phase directory
  `runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/phases/FUTSUB-P01`
  was not present when inspected. Codex did not create a run-local
  `handoff.md`, `review.md`, or `verdict.json`.
- No value artifact, heavy artifact, local DB, provider response, secret,
  credential, raw data, canonical data, feature value, label value, or
  roll-calendar data was created.

## Validation

Commands run from the provided WSL2 worktree root:

| Command | Result |
| --- | --- |
| `test ! -f runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/STOP` | PASS; STOP absent. |
| `git status --short` | Not run; forbidden by executor safety override in the prompt. |
| `python -c "import alpha_system.runtime, alpha_system.features, alpha_system.labels, alpha_system.experiments.splits, alpha_system.data.foundation.rolls, alpha_system.core.value_store"` | PASS; exit code `0`; no output. |
| `python tools/verify.py --smoke` | PASS; exit code `0`; no output. |
| `python tools/verify.py --lint` | ENV-ONLY SKIP; exit code `0`; output: `ruff is not installed; run pip install -e ".[dev]" to enable lint. Skipping.` |
| `python tools/verify.py --typecheck` | PASS; exit code `0`; ran `/home/yuke_zhang/.venvs/alpha_system_research/bin/python -m compileall -q src tests tools`. |
| `python tools/verify.py --test` | FAIL; exit code `1`; summary: `4 failed, 2840 passed in 48.68s`. Failures: `tests/integration/test_duckdb_query_fixture.py::test_duckdb_query_over_tiny_csv_fixture` expected a list and received a tuple; `tests/integration/test_polars_lazy_fixture.py::test_polars_lazy_transformation_over_tiny_fixture` expected a list and received a tuple; `tests/unit/data/test_databento_canonicalize.py::test_databento_canonicalize_quality_coverage_and_register_offline` found `ohlcv_rows` empty; `tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only` expected `RuntimeCacheStorageKind.RUN_ARTIFACTS` and received `RuntimeCacheStorageKind.ALPHA_DATA_ROOT`. These match the prior documented Core Pilot closeout failures and were not repaired because source/test repair is out of this phase scope. |
| `python tools/hooks/canary_runner.py` | PASS; exit code `0`; output ended with `All Frontier canaries passed.` |
| `test -f docs/futures_substrate_scaleout/REALITY_LOCK.md` | PASS; exit code `0`; no output. |
| `test -f research/futures_substrate_scaleout_v1/preflight/reality_baseline.md` | PASS; exit code `0`; no output. |
| `test -f README.md` | PASS; exit code `0`; no output. |
| `git ls-files runs` | PASS; exit code `0`; output empty. |
| `git ls-files '**/*.parquet' '**/*.arrow' '**/*.feather' '**/*.sqlite' '**/*.db' '**/*.dbn' '**/*.zst'` | PASS; exit code `0`; output empty. |

## Entry-Gate Note For FUTSUB-P02

- Consumed primitives import cleanly: `runtime`, `features`, `labels`,
  `experiments.splits`, `data.foundation.rolls`, and `core.value_store`.
- Resolver-smoke/fail-closed discipline is intact by reference from the Core
  Pilot and campaign goal: downstream feature, label, and StudySpec locks must
  resolve to real registry-backed Parquet values and must fail closed on stale
  or unresolvable locks. This phase did not rerun diagnostics.
- The inherited boundary is locked:
  `4 REJECT / 6 INCONCLUSIVE / 0 WATCH / 0 CANDIDATE_RESEARCH`.
- `registered != accepted/locked`; `FUTSUB-P02` must not treat registered
  DatasetVersions as accepted coverage verdicts.

## Boundary Confirmation

No consumed primitive under `runtime`, `features`, `labels`,
`experiments.splits`, `data.foundation.rolls`, or `core.value_store` was edited.
No value, registry, roll-calendar, provider, heavy, cache, log, raw, canonical,
feature-value, label-value, broker/live/paper/order, deployment, PR, merge, or
review artifact was touched by Codex.
