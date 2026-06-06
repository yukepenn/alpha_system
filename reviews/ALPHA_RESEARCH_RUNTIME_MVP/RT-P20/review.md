# Claude Review — RT-P20: Synthetic Runtime Fixtures and Fail-Closed Tests

## Summary

RT-P20 delivers exactly what the spec scopes: tiny synthetic runtime fixtures, a fail-closed test suite, one no-lookahead fixture-audit addition, and two durable docs (`FIXTURES.md`, `TESTING.md`), plus a compact README snapshot and a commit-eligible handoff. No runtime source or consumed-primitive module was modified. I verified the artifacts directly in the worktree.

## Verification Performed

| Check | Result |
| --- | --- |
| Scope: tests/fixtures/docs only, no `src/` change | ✅ `git status` shows only README + new test/fixture/doc/handoff paths; `git status src/` empty |
| No `runs/` tracked or staged | ✅ `git ls-files runs` empty; no `runs/` in handoff staging list |
| Fixtures tiny & synthetic | ✅ largest fixture 5066 B; `find … -size +1M` empty; explicit `market_data:false / provider_response:false / alpha_evidence:false` attestation |
| Fail-closed suite genuinely blocks | ✅ tests import the real runtime modules and assert real `INPUTS_BLOCKED`/`INPUTS_INCONCLUSIVE` states, `pytest.raises(..., match=…)`, and `GUARD_REJECTED`; test doubles only stand in for the data store, not the guard logic |
| No test weakening | ✅ only one **new** no-lookahead file added (`test_rt_p20_fixture_no_lookahead.py`); the three pre-existing no-lookahead files are untouched (still git-tracked, not in working set) |
| Canaries (independent) | ✅ all 16 pass, including `governance_optimistic_fill`, `governance_future_shift`, `governance_permuted_labels`, `forbidden_test_tamper`, `forbidden_scope_drift` |
| No broker/live/paper/order scope; no alpha/tradability/profitability claim | ✅ doc scan returns only no-claims/negation language ("does **not** mean … tradable, profitable, production-ready") |
| README snapshot factual & compact | ✅ progress 21/27, next-phase pointer, new modules listed, safety boundaries restated; no claims, no `runs/` paths |
| Executor stayed in lane | ✅ no `review.md`, `verdict.json`, PR, merge, or staging created by Codex (confirmed absent) |

I could **not** independently run `pytest` (gated in this review sandbox). I relied on the executor's reported `29 passed in 0.38s`, corroborated by the independent canary pass and my static read of the test code, which exercises real guards rather than gaming them.

## Warnings

1. **Broad `verify.py --test` shows 13 failures / `--lint` fails.** Honestly disclosed in the handoff as pre-existing Frontier/GitHub/Ralph-driver and repo-wide lint debt (baseline from RT-P19). I confirmed RT-P20 touches **no** ralph/github/driver/`src/` paths, so these failures are structurally unrelated to this phase. Smoke + typecheck + scoped Ruff + targeted suites pass.
2. **README is an additive deviation from stored campaign `allowed_paths`.** The spec author flagged this; `README.md` is a shared/global file reconciled through the **serial merge queue** at merge, consistent with prior phases (RT-P19 also edited README). Acceptable, but Ralph must apply the README edit single-writer against fresh `main`, never co-written with W3 siblings RT-P22/RT-P23.
3. **`RuntimeToolResult` / `RuntimeRunSummary` raw-data check deferred to RT-P22.** Those contract modules are not on `main` yet; the spec explicitly permitted recording this as a dependency rather than faking it. Properly handled.
4. **`git status --short` absent from handoff** by executor-safety override (Codex was forbidden from running `git`). Ralph owns the authoritative staging audit — must confirm the staged set matches the 8 curated paths and contains no `runs/` path before merge-gate.

## Required of Ralph before merge

- Stage **only** the 8 explicit paths in the handoff; verify no `runs/` path enters the index.
- A fresh independent Opus verdict (this review) plus required-check pass; the YELLOW lane is satisfied.

No prohibited scope, no destructive operation, no hidden failed run, no test weakening, and no artifact-policy violation found.

VERDICT: PASS_WITH_WARNINGS
