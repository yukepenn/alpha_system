# FUTCORE-P16 Handoff

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P16` - Cross-Market Diagnostics  
Executor: Codex GPT-5.5  
Lane: Yellow  
Status: executor work complete; Ralph review, validation orchestration,
authoritative staging, commit, PR, CI, merge, and done-check actions pending

## Scope Completed

- Refreshed the cross-market diagnostics reports for the four current
  `FUTCORE-P14` `cross_market` StudySpecs:
  `sspec_dde3e64667fe158f9bad527d`,
  `sspec_c671fbeeb143512cbc03bc5b`,
  `sspec_90b28233d828128664588a9a`, and
  `sspec_7c8fb13628843890c171b122`.
- Resolved inputs through the Research Runtime input resolver and registry
  facades against the locked `FUTCORE-P03` DatasetVersion, FeaturePack, and
  LabelPack references; research-scale scans read registry-resolved Parquet
  values in memory and wrote only scalar summaries.
- Invoked the existing Research Runtime cross-market, factor, label,
  signal-probe, cost, `RuntimeToolResult`, and `RuntimeRunSummary` surfaces.
- Recorded timestamp-alignment summaries per instrument pair and
  cross-market missingness splits by required instrument and session view.
- Recorded cost diagnostics for `base`, `stress_1`, `stress_2`, and
  `double_cost`; `zero_cost` is recorded as diagnostic-only and not a
  promotion basis.
- Updated the durable cross-market diagnostics doc and compact README snapshot.

Runtime outcome: all four StudySpecs reached the runtime surfaces, but the
registry-resolved materialized packs exposed ES observations in the diagnostics
view and no NQ or RTY value rows. Cross-market alignment therefore rejected the
family diagnostics for missing cross-market legs rather than inferring,
forward-filling, or reusing another instrument's values.

The `sspec_90b28233d828128664588a9a` primary `15m` horizon has a P15 LabelSpec
record but no locked materialized Parquet LabelPack in the P03/P14 input pack.
The report records that limitation without substituting an unlocked 15m pack.

No promotion, ranking, survivor state, review artifact, verdict, PR, merge,
live/paper/broker/order action, production deployment, or capital-allocation
claim was made.

## Files Written, Updated, Or Removed

Codex staged no files. The user override explicitly directed Codex not to run
`git add`, `git commit`, `git push`, `git status`, or `git diff`. Ralph owns
authoritative staging and commit.

Written or updated:

- `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/INDEX.md`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/sspec_dde3e64667fe158f9bad527d.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/sspec_c671fbeeb143512cbc03bc5b.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/sspec_90b28233d828128664588a9a.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/sspec_7c8fb13628843890c171b122.json`
- `docs/futures_core_alpha_pilot/diagnostics/cross_market.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P16.md`

Removed stale report files whose filenames did not match the current P14
StudySpec ids:

- `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/sspec_ac883ec0b962f4ae4f25e190.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/sspec_16f6de31387d8289d0fbb394.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/sspec_fc7b0408e59a83f2e69714d3.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/sspec_6fe5fa12b333d19ea95915d2.json`

Exact file paths staged by Codex:

- None.

No `runs/**` path should be staged.

## Runtime Diagnostics Summary

| StudySpec | AlphaSpec | Category | Runtime outcome |
| --- | --- | --- | --- |
| `sspec_dde3e64667fe158f9bad527d` | `aspec_0ebd90cecfd475607685b445` | lead-lag | `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` |
| `sspec_c671fbeeb143512cbc03bc5b` | `aspec_8d9e272e4b78eedcd27f0bec` | beta-residual | `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` |
| `sspec_90b28233d828128664588a9a` | `aspec_a41dcccac5552de945aba825` | rotation | `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` |
| `sspec_7c8fb13628843890c171b122` | `aspec_fa4895a43a80d4eef0a607a4` | confirmation-divergence | `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` |

Each report references the originating runtime report refs,
`RuntimeToolResult`, `RuntimeRunSummary`, and locked pack ids/hashes. The
reports include scalar summaries only; no row-level market, feature, label,
signal, provider, registry, local Parquet path, or DB payload is embedded.

## Validation Run By Codex

```bash
test ! -e runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/STOP
```

Result: exit code `0`; no active run-level STOP file was present.

```bash
python -c "import alpha_system.runtime.tool_results"
```

Result: exit code `0`; no stdout.

```bash
python tools/verify.py --smoke
```

Result: exit code `0`; no stdout.

```bash
test -d research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market
test -f docs/futures_core_alpha_pilot/diagnostics/cross_market.md
test -f handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P16.md
```

Result: each command exited `0`.

```bash
git ls-files runs
```

Result: exit code `0`; empty output.

```bash
git ls-files '**/*.parquet' '**/*.sqlite' '**/*.dbn' '**/*.zst'
```

Result: exit code `0`; empty output.

```bash
jq -s -e 'length == 4 and ([.[].study_spec.study_spec_id] | sort == (["sspec_7c8fb13628843890c171b122","sspec_90b28233d828128664588a9a","sspec_c671fbeeb143512cbc03bc5b","sspec_dde3e64667fe158f9bad527d"] | sort))' research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/sspec_*.json >/dev/null
```

Result: exit code `0`; current StudySpec ids confirmed.

```bash
jq -s -e 'all(.[]; .value_free == true and .raw_or_heavy_data_embedded == false and .promotion_decision_made == false and .boundary_confirmations.runtime_tools_only == true and (.cross_market_alignment.symbol_session_missingness_splits | length > 0) and (.cross_market_alignment.pair_timestamp_alignment | length == 3))' research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/sspec_*.json >/dev/null
```

Result: exit code `0`; report safety fields, session missingness splits, and
pair timestamp-alignment summaries were present.

```bash
rg -n '/home/|\.parquet|\.sqlite|\.dbn|\.zst|provider_payload|provider_response|raw_values|value_table|dataframe|alpha validated|validated alpha|profitable|live ready|paper ready|production ready|strategy ready|factor promoted|candidate approved|tradable' research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market docs/futures_core_alpha_pilot/diagnostics/cross_market.md README.md
```

Result: exit code `1`; expected no-match result and no stdout.

```bash
test ! -e reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P16/review.md
test ! -e reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P16/verdict.json
```

Result: both commands exited `0`; Codex created no review or verdict artifacts.

Validation intentionally not run by Codex:

- `git status --short`: not run because the user explicitly forbade
  `git status`.
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
- Reports are value-free scalar summaries and references only.
- Codex staged no files; no `runs/**` path was staged by Codex.
- `git ls-files runs` returned empty.
- Tracked heavy-glob checks returned empty.
- No live trading, paper trading, broker operation, order routing, account
  operation, deployment, PR creation, merge, reviewer call, review artifact, or
  verdict action was performed.
