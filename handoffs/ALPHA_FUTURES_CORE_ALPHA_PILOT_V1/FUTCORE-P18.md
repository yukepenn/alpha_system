# FUTCORE-P18 Executor Handoff

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P18` - Regime Momentum/Reversion Diagnostics  
Executor: Codex  
Run id: `2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`

## Status

Executor diagnostics are complete and left unstaged in the working tree. Ralph
owns authoritative staging, commit, validation orchestration, review, verdict,
PR, CI, merge, and done-check actions.

No Claude review was run. No `review.md`, `verdict.json`, PR, merge, live
operation, paper operation, broker call, order routing, or deployment action was
created or performed by the executor.

## Scope Completed

- Resolved the approved regime-family StudySpec
  `sspec_267cc052e37668339c38d179` / AlphaSpec
  `aspec_eb962fc197eaf3955c5e4711`.
- Ran diagnostics only through the Research Runtime tool surface:
  runtime entry/input resolution, factor diagnostics, label diagnostics,
  session split diagnostics, regime split diagnostics, signal-probe diagnostics,
  cost stress diagnostics, `RuntimeToolResult`, and `RuntimeRunSummary`.
- Wrote value-free regime diagnostics report artifacts with scalar summaries,
  ids, hashes, statuses, and limitations only.
- Wrote the human-readable regime diagnostics page and compact README snapshot.
- No consumed `src/alpha_system` primitive was edited.

## Runtime Outcome

Runtime status is `INCONCLUSIVE`.

Resolved locked input references:

- DatasetVersion: `dsv_databento_ohlcv_05404069799decb0`
- FeaturePacks: 5 registered pack handles
- LabelPacks: 3 registered pack handles for `5m`, `10m`, and `30m`

Coverage summary:

- Joined 5m observations: 6,862
- Joined observations across resolved `5m`, `10m`, and `30m` horizons: 20,406
- Materialized entity coverage: ES only; NQ and RTY were zero-count cells and
  were not inferred, filled, or substituted.
- Primary `15m` horizon: unresolved because no registered 15m LabelPack
  resolves in the locked local registry.
- Fragile `1m` and `3m` horizons: diagnostic-only and not a promotion basis.

Regime/stability summary:

- Exact StudySpec gate activation remains inconclusive because the locked packs
  do not expose the materialized trendiness input, explicit range-compression
  activation binding, or failed directional extension state.
- Trend/chop and momentum/reversion gate cells are visible inconclusive cells.
- Available high/low volatility and range-compression split summaries are
  descriptive diagnostics only and do not substitute for the unresolved gate.
- Declared `VariantBudget` is four; four predeclared cells were recorded:
  momentum and reversion modes over short and long trailing gate windows.
- No post-diagnostic variants were added.
- Binary signal probes used completed-bar direction threshold `0.5`; no
  return-magnitude grid search was run.

Cost summary:

- Nonzero profiles carried through: `base`, `stress_1`, `stress_2`,
  `double_cost`.
- `zero_cost` is diagnostic-only context and is not a continuation or promotion
  basis.

## Files For Ralph Explicit Staging

Codex staged no files.

Commit-eligible files produced or updated for this phase:

- `research/futures_core_alpha_pilot_v1/diagnostics_reports/regime/INDEX.md`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/regime/FUTCORE-P18_regime_summary.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/regime/sspec_267cc052e37668339c38d179/runtime_reports.json`
- `docs/futures_core_alpha_pilot/diagnostics/regime.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P18.md`

No `runs/**` path, heavy artifact, local DB, cache, log, provider response, raw
data, feature value data, or label value data is intended for staging.

## Commands Run

Generation:

- `PYTHONPATH=src python - <<'PY' ... PY`
  - Result: passed.
  - Output summary: wrote the regime diagnostics index, summary JSON, and
    runtime report JSON; `rows_5m=6862`,
    `rows_all_resolved_horizons=20406`, `runtime_status=INCONCLUSIVE`.

Validation and inspection:

- `test ! -e runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/STOP`
  - Result: passed; no active STOP file was present before execution.
- `python -c "import alpha_system.runtime.tool_results"`
  - Result: passed.
- `python tools/verify.py --smoke`
  - Result: passed.
- `test -d research/futures_core_alpha_pilot_v1/diagnostics_reports/regime`
  - Result: passed.
- `test -f docs/futures_core_alpha_pilot/diagnostics/regime.md`
  - Result: passed.
- `test -f handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P18.md`
  - Result before this handoff was written: failed, exit code 1.
  - Follow-up after handoff creation: passed.
- JSON parse check for
  `research/futures_core_alpha_pilot_v1/diagnostics_reports/regime/FUTCORE-P18_regime_summary.json`
  and
  `research/futures_core_alpha_pilot_v1/diagnostics_reports/regime/sspec_267cc052e37668339c38d179/runtime_reports.json`
  - Result: passed.
- Runtime report assertions for runtime-tool-only flags, no promotion, no
  consumed primitive edits, no external provider call, no raw/heavy embedding,
  `INCONCLUSIVE` runtime status, four observed variant cells, unresolved `15m`,
  and `zero_cost` not being a promotion basis.
  - Result: passed.
- Heavy/raw path token scan over regime reports, regime doc, and README.
  - Result: passed; no `.parquet`, `.sqlite`, `.dbn`, `.zst`, `.arrow`,
    `.feather`, `provider_response`, `raw_payload`, `data/raw`, or
    `artifacts/` tokens were present.
- Forbidden-state token scan over regime reports, regime doc, and README.
  - Result: passed; no forbidden promotion or approval state tokens were found.
- `git ls-files runs`
  - Result: passed; output was empty.
- `git ls-files '**/*.parquet'`
  - Result: passed; output was empty.
- `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.dbn' '**/*.zst'`
  - Result: passed; output was empty.
- `git ls-files '**/*.arrow' '**/*.feather' '**/*.db' '**/*.wal' '**/*.log'`
  - Result: passed; output was empty.
- `test ! -e runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/phases/FUTCORE-P18/review.md`
  - Result: passed.
- `test ! -e runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/phases/FUTCORE-P18/verdict.json`
  - Result: passed.
- Final JSON parse check for the regime summary and runtime report.
  - Result: passed.

Commands intentionally not run by Codex due to executor override:

- `git status --short`
- `git diff --cached --name-only`
- `git add`, `git commit`, `git push`
- Claude review, reviewer, verdict parsing, PR creation, CI, merge, done-check

Yellow-lane broader checks (`lint`, `typecheck`, `test`, `verify_canaries`) are
Ralph-owned for orchestration in this Workflow 2 turn.

## Boundaries

The diagnostics are value-free evidence for review only. They make no
profitability, tradability, deployment, live, paper, broker, order, capital, or
promotion claim. The unresolved exact regime gate should be read as a locked
input limitation, not as support for either momentum or reversion.
