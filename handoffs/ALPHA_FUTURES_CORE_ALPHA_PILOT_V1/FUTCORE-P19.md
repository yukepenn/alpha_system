# FUTCORE-P19 Executor Handoff

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P19` - Liquidity Sweep / PA Diagnostics  
Executor: Codex  
Run id: `2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`

## Status

Executor diagnostics are complete and left unstaged in the working tree. Ralph
owns authoritative staging, commit, validation orchestration, review, verdict,
PR, CI, merge, and done-check actions.

No Claude review was run. No `review.md`, `verdict.json`, PR, merge, live
operation, paper operation, broker call, order routing, or deployment action was
created or performed by the executor. The phase was not marked PASS.

## Scope Completed

- Resolved the approved liquidity/PA StudySpecs:
  `sspec_27bf1262b0bd23d27191cc86` /
  `aspec_df2d040e45564c259ef3de6d`, and
  `sspec_02c400a561891171a33c0c66` /
  `aspec_39ffc190cfbfa6ba0b1a2a25`.
- Ran diagnostics only through the Research Runtime tool surface:
  runtime entry/input resolution, factor diagnostics, label diagnostics,
  session split diagnostics, spread/liquidity split diagnostics, signal-probe
  diagnostics, cost stress diagnostics, `RuntimeToolResult`, and
  `RuntimeRunSummary`.
- Wrote value-free liquidity/PA diagnostics report artifacts with scalar
  summaries, ids, hashes, statuses, and limitations only.
- Wrote the human-readable liquidity/PA diagnostics page and compact README
  snapshot.
- No consumed `src/alpha_system` primitive was edited.

## Runtime Outcome

Runtime status is `INCONCLUSIVE` for both StudySpecs.

RuntimeRunSummary references:

- `sspec_27bf1262b0bd23d27191cc86`:
  `2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1_sspec_27bf1262b0bd23d27191cc86`
- `sspec_02c400a561891171a33c0c66`:
  `2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1_sspec_02c400a561891171a33c0c66`

Resolved locked input references:

- DatasetVersion: `dsv_databento_ohlcv_05404069799decb0`
- FeaturePacks: 6 registered pack handles
- LabelPacks: 3 registered pack handles for `5m`, `10m`, and `30m`

Coverage summary per StudySpec:

- Joined `5m` rows: 6,862
- Joined `10m` rows: 20,406
- Joined `30m` rows: 20,406
- Joined rows across resolved horizons: 47,674
- Materialized entity coverage: ES only; NQ and RTY were zero-count cells and
  were not inferred, filled, or substituted.
- Primary `15m` horizon: unresolved because no registered 15m LabelPack
  resolves in the locked local registry.
- Fragile `1m` and `3m` horizons: diagnostic-only and not a promotion basis.

Family-specific summary:

- Exact objective-rule trigger counts remain unresolved because the locked
  packs do not expose materialized prior high/low sweep, close-back-inside,
  wick rejection, displacement, compression-breakout, or failed-breakout
  reversal flags.
- Each objective rule is recorded as an explicit unresolved count cell with
  `pilot_side_recomputation_performed: false`.
- Spread buckets remain unresolved because no locked BBO or spread FeaturePack
  is bound to these StudySpecs.
- Liquidity splits are descriptive activity-proxy buckets from the locked
  `base_ohlcv_volume_zscore` FeaturePack.
- All joined rows are ETH in this locked surface because the resolved RTH flag
  is zero throughout the pack; RTH cells are preserved as zero-count
  diagnostics.

Cost summary:

- Nonzero profiles carried through: `base`, `stress_1`, `stress_2`,
  `double_cost`.
- `zero_cost` is diagnostic-only context and is not a continuation or promotion
  basis.

## Files For Ralph Explicit Staging

Codex staged no files.

Commit-eligible files produced or updated for this phase:

- `research/futures_core_alpha_pilot_v1/diagnostics_reports/liquidity_pa/INDEX.md`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/liquidity_pa/FUTCORE-P19_liquidity_pa_summary.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/liquidity_pa/sspec_27bf1262b0bd23d27191cc86/runtime_reports.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/liquidity_pa/sspec_02c400a561891171a33c0c66/runtime_reports.json`
- `docs/futures_core_alpha_pilot/diagnostics/liquidity_pa.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P19.md`

No `runs/**` path, heavy artifact, local DB, cache, log, provider response, raw
data, feature value data, or label value data is intended for staging.

## Commands Run

Generation:

- `PYTHONPATH=src python - <<'PY' ... PY`
  - Result: passed.
  - Output summary: wrote the liquidity/PA diagnostics index, summary JSON, and
    two runtime report JSON files; both StudySpecs returned runtime status
    `INCONCLUSIVE`; joined rows per StudySpec were 47,674.
  - Note: earlier transient generation attempts failed before final report
    writes while resolving runtime module exports and the typed signal-probe
    cost-fill contract. The final command consumed the correct runtime modules
    and typed `SignalProbeObservation` objects.

Validation and inspection:

- `test ! -e runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/STOP`
  - Result: passed; output was `NO_STOP`.
- `python -c "import alpha_system.runtime.tool_results"`
  - Result: passed.
- `python tools/verify.py --smoke`
  - Result: passed.
- `test -d research/futures_core_alpha_pilot_v1/diagnostics_reports/liquidity_pa`
  - Result: passed.
- `git ls-files runs`
  - Result: passed; output was empty.
- `git ls-files '**/*.parquet'`
  - Result: passed; output was empty.
- JSON parse check for
  `research/futures_core_alpha_pilot_v1/diagnostics_reports/liquidity_pa/FUTCORE-P19_liquidity_pa_summary.json`,
  `research/futures_core_alpha_pilot_v1/diagnostics_reports/liquidity_pa/sspec_27bf1262b0bd23d27191cc86/runtime_reports.json`,
  and
  `research/futures_core_alpha_pilot_v1/diagnostics_reports/liquidity_pa/sspec_02c400a561891171a33c0c66/runtime_reports.json`
  - Result: passed.
- `test -f docs/futures_core_alpha_pilot/diagnostics/liquidity_pa.md && test -f handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P19.md`
  - Result: passed.
- Heavy/raw path token scan over liquidity/PA reports, liquidity/PA doc, and
  README.
  - Result: passed; no `.parquet`, `.sqlite`, `.dbn`, `.zst`, `.arrow`,
    `.feather`, `provider_response`, `raw_payload`, `data/raw`, or
    `artifacts/` tokens were present in those surfaces.
- `test ! -e runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/phases/FUTCORE-P19/review.md && test ! -e runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/phases/FUTCORE-P19/verdict.json`
  - Result: passed.

Commands intentionally not run by Codex due to executor override:

- `git status --short`
- `git diff --cached --name-only`
- `git add`, `git commit`, `git push`
- Claude review, reviewer, verdict parsing, PR creation, CI, merge, done-check

Because Codex ran no staging command and was forbidden to inspect cached diff,
the authoritative staged-set audit remains Ralph-owned. `git ls-files runs` and
`git ls-files '**/*.parquet'` were empty from the executor side.

Yellow-lane broader checks (`lint`, `typecheck`, `test`, `verify_canaries`) are
Ralph-owned for orchestration in this Workflow 2 turn.

## Boundaries

The diagnostics are value-free evidence for review only. They make no
profitability, tradability, deployment, live, paper, broker, order, capital, or
promotion claim. The unresolved exact PA trigger counts and unresolved 15m
horizon should be read as locked input limitations, not as support for either
liquidity/PA StudySpec.
