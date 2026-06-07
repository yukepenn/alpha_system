# FUTCORE-P16 Handoff

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P16` - Cross-Market Diagnostics  
Executor: Codex GPT-5.5  
Lane: Yellow  
Status: executor work complete; Ralph review, validation orchestration, staging,
commit, PR, CI, merge, and done-check actions pending

## Scope Completed

- Ran the four approved `cross_market` StudySpecs through the existing Research
  Runtime tool surfaces: input resolver, cross-market diagnostics, factor
  diagnostics, label diagnostics, signal probe, cost stress, `RuntimeToolResult`,
  and `RuntimeRunSummary`.
- Produced one value-free JSON diagnostics report per StudySpec under
  `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/`.
- Added the research report index and the durable docs index.
- Updated `README.md` with a compact `FUTCORE-P16` snapshot.

Runtime outcome: every cross-market StudySpec reached the runtime surfaces, but
cross-market alignment rejected the runs because the locked materialized packs
supplied ES observations only. NQ and RTY observations were absent, so the
runtime created no aligned ES/NQ/RTY snapshot and did not infer or forward-fill
missing instruments.

No promotion, ranking, survivor state, review artifact, verdict, PR, merge,
live/paper/broker/order action, production deployment, or capital-allocation
claim was made.

## Files Written Or Updated

- `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/INDEX.md`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/sspec_ac883ec0b962f4ae4f25e190.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/sspec_16f6de31387d8289d0fbb394.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/sspec_fc7b0408e59a83f2e69714d3.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/sspec_6fe5fa12b333d19ea95915d2.json`
- `docs/futures_core_alpha_pilot/diagnostics/cross_market.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P16.md`

## Staging Status

Codex staged no files. The user override explicitly directed Codex not to run
`git add`, `git commit`, `git push`, `git status`, or `git diff`. Ralph owns
authoritative staging and commit.

Exact file paths staged by Codex:

- None.

Commit-eligible file paths for Ralph explicit staging:

- `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/INDEX.md`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/sspec_ac883ec0b962f4ae4f25e190.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/sspec_16f6de31387d8289d0fbb394.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/sspec_fc7b0408e59a83f2e69714d3.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/sspec_6fe5fa12b333d19ea95915d2.json`
- `docs/futures_core_alpha_pilot/diagnostics/cross_market.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P16.md`

No `runs/**` path should be staged.

## Runtime Diagnostics Summary

| StudySpec | AlphaSpec | Category | Runtime outcome |
| --- | --- | --- | --- |
| `sspec_ac883ec0b962f4ae4f25e190` | `aspec_0ebd90cecfd475607685b445` | lead-lag | `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` |
| `sspec_16f6de31387d8289d0fbb394` | `aspec_8d9e272e4b78eedcd27f0bec` | beta-residual | `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` |
| `sspec_fc7b0408e59a83f2e69714d3` | `aspec_a41dcccac5552de945aba825` | rotation | `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` |
| `sspec_6fe5fa12b333d19ea95915d2` | `aspec_fa4895a43a80d4eef0a607a4` | confirmation-divergence | `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` |

Each report references the originating runtime report refs, `RuntimeToolResult`
run id, `RuntimeRunSummary`, and locked pack ids/hashes. The reports include
timestamp-alignment summaries, per-symbol cross-market missingness splits,
cross-instrument availability statements, factor diagnostics, label diagnostics,
signal-probe summaries, and cost diagnostics over `base`, `stress_1`,
`stress_2`, and `double_cost`. `zero_cost` is recorded as diagnostic-only and
not a promotion basis.

## Validation Run By Codex

```bash
test ! -e runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/STOP
```

Result: exit code `0`; no active STOP file was present.

```bash
python -c "import alpha_system.runtime.tool_results"
```

Result: exit code `0`.

```bash
PYTHONPATH=src python -c "import alpha_system.runtime.tool_results"
```

Result: exit code `0`.

```bash
python tools/verify.py --smoke
```

Result: exit code `0`; no stdout.

```bash
test -d research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market
```

Result: exit code `0`.

```bash
test -f docs/futures_core_alpha_pilot/diagnostics/cross_market.md
```

Result: exit code `0`.

```bash
jq -e '.schema and .runtime_tool_result and .runtime_run_summary and .cross_market_alignment and .standard_diagnostics' research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/*.json >/dev/null
```

Result: exit code `0`.

```bash
git ls-files runs
```

Result: exit code `0`; empty output.

```bash
git ls-files '**/*.parquet'
```

Result: exit code `0`; empty output.

```bash
git ls-files '**/*.parquet' '**/*.sqlite' '**/*.dbn' '**/*.zst'
```

Result: exit code `0`; empty output.

```bash
rg -n '/home/|\.parquet|\.sqlite|\.dbn|\.zst|provider_payload|provider_response|raw_values|value_table|dataframe|alpha validated|validated alpha|profitable|live ready|paper ready|production ready|strategy ready|factor promoted|candidate approved|tradable' research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market docs/futures_core_alpha_pilot/diagnostics/cross_market.md
```

Result: exit code `1`; expected no-match result and no stdout.

Validation intentionally not run by Codex:

- `git status --short`: not run because the user explicitly forbade
  `git status`; no Codex git-status summary is available.
- `git diff --cached --name-only`: not run because the user explicitly forbade
  `git diff`, and Codex staged nothing.
- `git add`, `git commit`, and `git push`: not run because the user explicitly
  forbade staging and committing.
- Fresh Yellow-lane Claude review: not run because the user explicitly forbade
  calling Claude or running reviewer.
- `review.md` and `verdict.json`: not created because the user explicitly
  forbade creating them. Ralph owns review orchestration and verdict parsing.
- Full Yellow-lane `lint`, `typecheck`, `test`, and `verify_canaries`: not run
  by Codex in this executor pass; Ralph owns broader CHECKS_RUN orchestration.

## Artifact And Boundary Confirmation

- Diagnostics ran through existing `src/alpha_system/runtime` surfaces only.
- No file under `src/alpha_system/runtime/**` or any consumed primitive path was
  edited.
- Reports are value-free scalar summaries and references only; no row-level
  market, feature, label, signal, provider, cache, DB, or heavy artifact payload
  is embedded.
- Codex staged no files; no `runs/**` path was staged by Codex.
- `git ls-files runs` returned empty.
- Tracked heavy-glob checks returned empty.
- No live trading, paper trading, broker operation, order routing, account
  operation, deployment, PR creation, merge, reviewer call, review artifact, or
  verdict action was performed.
