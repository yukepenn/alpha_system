# FUTCORE-P22 Handoff

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P22` - Session / Horizon / Regime Matrix Consolidation  
Executor: Codex  
Lane: Yellow

## Scope Completed

Created the value-free P22 session x horizon x regime matrix by consolidating
the already-committed P16-P21 diagnostics and cost-stress evidence by reference.
No new diagnostics were run and no source primitive was edited.

Commit-eligible files for Ralph to stage:

- `research/futures_core_alpha_pilot_v1/matrix/session_horizon_regime_matrix.md`
- `docs/futures_core_alpha_pilot/MATRIX.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P22.md`

Files staged by Codex: none. The executor instructions explicitly forbade
`git add`, `git commit`, `git push`, `git status`, and `git diff`; all changes
were left unstaged for Ralph.

## Consolidated Ideas And Flags

P22 consolidated the six non-rejected P17-P20 StudySpecs as
`diagnostic_survivors_for_consolidation`; this is not a promotion state:

| StudySpec | Family | Runtime status | `narrow_cell_only` | Fragile horizon flag | Thin-session flag | P21 carried flags |
| --- | --- | --- | --- | --- | --- | --- |
| `sspec_69c22ec5847395ac8e81b5b6` | `vwap_session` | `INCONCLUSIVE` | `false_no_stable_cells_recorded` | `1m`, `3m` diagnostics-only | ETH/pre/post research-only | `MATERIAL_COST_STRESS_GRADIENT`, `BBO_PROXY_FALLBACK` |
| `sspec_aff70fcbc4b7ff226fcc8149` | `vwap_session` | `INCONCLUSIVE` | `false_no_stable_cells_recorded` | `1m`, `3m` diagnostics-only | ETH/pre/post research-only | `MATERIAL_COST_STRESS_GRADIENT`, `BBO_PROXY_FALLBACK` |
| `sspec_267cc052e37668339c38d179` | `regime` | `INCONCLUSIVE` | `false_no_stable_cells_recorded` | `1m`, `3m` diagnostics-only | ETH/pre/post research-only | `MATERIAL_COST_STRESS_GRADIENT`, `THIN_SESSION_ONLY_COST_BREAKDOWN`, `BBO_PROXY_FALLBACK` |
| `sspec_27bf1262b0bd23d27191cc86` | `liquidity_pa` | `INCONCLUSIVE` | `false_no_stable_cells_recorded` | `1m`, `3m` diagnostics-only | `ETH_only`; thin subsegments unresolved | `MATERIAL_COST_STRESS_GRADIENT`, `THIN_SESSION_ONLY_COST_BREAKDOWN`, `BBO_PROXY_FALLBACK` |
| `sspec_02c400a561891171a33c0c66` | `liquidity_pa` | `INCONCLUSIVE` | `false_no_stable_cells_recorded` | `1m`, `3m` diagnostics-only | `ETH_only`; thin subsegments unresolved | `MATERIAL_COST_STRESS_GRADIENT`, `THIN_SESSION_ONLY_COST_BREAKDOWN`, `BBO_PROXY_FALLBACK` |
| `sspec_9f6f741192a4b534f06e51c0` | `bbo_tradability` | `INCONCLUSIVE` | `false_no_stable_cells_recorded` | `1m`, `3m` diagnostics-only | ETH/pre/post research-only; RTH gap | `MATERIAL_COST_STRESS_GRADIENT`, `THIN_SESSION_RTH_GAP`, `BBO_PROXY_FALLBACK` |

The four P16 cross-market StudySpecs were retained as rejected-source context,
not survivor matrices:

- `sspec_dde3e64667fe158f9bad527d`
- `sspec_c671fbeeb143512cbc03bc5b`
- `sspec_90b28233d828128664588a9a`
- `sspec_7c8fb13628843890c171b122`

All four remain `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` and carry P21
`COST_COVERAGE_GAP` plus `BBO_PROXY_FALLBACK`.

## Validation

| Command | Outcome |
| --- | --- |
| `git status --short` | Not run: explicitly forbidden by executor instructions for this turn. |
| `python tools/verify.py --smoke` | Passed, exit code `0`; command produced no output. |
| `test -f research/futures_core_alpha_pilot_v1/matrix/session_horizon_regime_matrix.md` | Passed, exit code `0`. |
| `test -f docs/futures_core_alpha_pilot/MATRIX.md` | Passed, exit code `0`. |
| `git ls-files runs` | Passed, exit code `0`; output empty. |
| `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.dbn' '**/*.zst'` | Passed, exit code `0`; output empty. |

## Artifact And Boundary Confirmation

- No `runs/**` file was created, copied, staged, or committed by Codex.
- No heavy/value/DB artifact was created or staged by Codex.
- No consumed primitive under `src/alpha_system/**` was modified.
- No broker/live/paper/order/deployment surface was modified.
- `ACTIVE_CAMPAIGN.md` was not modified.
- No tests were added, removed, weakened, skipped, or changed.
- No review artifact, `review.md`, `verdict.json`, PR, merge, or PASS marking
  was created by Codex.
- Matrix content is value-free: ids, hashes, statuses, coverage counts,
  diagnostic flags, and metadata only.
- The matrix makes no alpha, profitability, tradability, production,
  paper/live, broker, deployment, or capital-allocation claim.
