# FUTCORE-P20 Executor Handoff

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P20` - BBO Tradability Diagnostics  
Executor: Codex  
Run id: `2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`

## Scope Completed

Executed the approved BBO confirmation StudySpec diagnostics through the Research Runtime tool surface and wrote value-free report artifacts for the BBO diagnostics family. The runtime outcome is `INCONCLUSIVE` because the locked input pack resolves OHLCV/session FeaturePacks and `5m`/`10m`/`30m` LabelPacks, but no locked P15-G5 BBO FeaturePack resolves for top-book spread/depth quality fields.

No source primitive, runtime, feature, label, data, broker, live, paper, order-routing, execution, or CLI code was edited. No raw provider files, arbitrary provider paths, JSONL-scale scans, broker calls, paper trading, live trading, deployment, PR, merge, Claude call, reviewer run, `review.md`, or `verdict.json` were created by Codex.

## Study And Runtime Inputs

- AlphaSpec: `aspec_1284e49b083df11eeb0481ea`
- StudySpec: `sspec_9f6f741192a4b534f06e51c0`
- Family: `bbo_tradability`
- VariantBudget: `4`
- P15 governed gaps: `P15-G1`, `P15-G5`
- DatasetVersion: `dsv_databento_ohlcv_05404069799decb0`
- Resolved FeaturePacks: session-context OHLCV FeaturePacks only
- Resolved LabelPacks: `5m`, `10m`, `30m`
- Unresolved locked pack: P15-G5 BBO FeaturePack for spread, spread ticks, spread zscore, top-book depth, wide-spread, low-depth, missing-BBO, and bad-quote fields

Runtime surfaces exercised:

- `RuntimeEntryRequest` / `evaluate_runtime_entry_request`
- `resolve_runtime_input_pack`
- `resolve_dataset_version`
- `build_factor_diagnostics_run`
- `build_label_diagnostics_report`
- signal-probe contract construction through `SignalProbeSpec`
- `build_cost_sensitivity_report`
- `RuntimeToolResult`
- `RuntimeRunSummary`

## Value-Free Findings Summary

Runtime status: `INCONCLUSIVE`.

Resolved joined-horizon observations:

| Horizon | Joined observations | Runtime interpretation |
| --- | ---: | --- |
| `5m` | 6,862 | Locked LabelVersion resolved. |
| `10m` | 6,832 | Locked LabelVersion resolved. |
| `15m` | 0 | Governed LabelSpec exists, but no locked LabelVersion resolves in this pack. |
| `30m` | 6,712 | Locked LabelVersion resolved. |
| all resolved | 20,406 | Sum of resolved `5m`/`10m`/`30m` diagnostics cells. |

Session views recorded: `full_session`, `RTH_only`, `ETH_only`, `ETH_evening`, `ETH_overnight`, `pre_RTH`, `RTH`, `post_RTH`, and `RTH_with_ETH_context`.

BBO quality handling:

- valid BBO: zero observed because the locked BBO feature binding is absent;
- missing BBO: explicit fallback-required cell for the resolved-horizon denominator until a locked BBO pack resolves;
- crossed, locked, stale, quarantined, wide-spread, and thin-depth buckets: unresolved without a locked BBO FeaturePack;
- fabricated quotes: zero;
- no quote values were inferred, filled, substituted, or committed.

Cost diagnostics recorded the contracted nonzero profiles `base`, `stress_1`, `stress_2`, and `double_cost`, with BBO-unavailable fallback markers. `zero_cost` remains diagnostic-only context and is not used as a promotion basis. The `1m` and `3m` horizons are flagged fragile/diagnostic-only; the `5m` to `30m` zone is framed only as confirmation and risk evidence.

## Files For Ralph Explicit Staging

Codex did not stage any files. The user override forbids `git add`, `git commit`, `git push`, `git status`, and `git diff`, so `git diff --cached --name-only` was intentionally not run by Codex.

Commit-eligible files produced or updated for Ralph to stage explicitly:

- `research/futures_core_alpha_pilot_v1/diagnostics_reports/bbo_tradability/INDEX.md`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/bbo_tradability/FUTCORE-P20_bbo_tradability_summary.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/bbo_tradability/sspec_9f6f741192a4b534f06e51c0/runtime_reports.json`
- `docs/futures_core_alpha_pilot/diagnostics/bbo_tradability.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P20.md`

No `runs/` artifact, heavy data artifact, local database, cache, log, raw/canonical payload, row-level feature value, row-level label value, provider response, review artifact, or verdict artifact was intentionally created as commit-eligible output.

## Commands Run And Outcomes

- `test ! -f runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/STOP && test ! -f runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/phases/FUTCORE-P20/STOP` - passed; no active STOP file was present.
- `PYTHONPATH=src python - <<'PY' ... PY` runtime input-resolution checks - passed; resolved DatasetVersion, FeaturePack, LabelPack, and canonical input-view metadata through registry/runtime helpers.
- `PYTHONPATH=src python - <<'PY' ... PY` diagnostics generation script - passed; wrote the BBO diagnostics report index, summary JSON, runtime report JSON, docs page, and README snapshot.
- `PYTHONPATH=src python - <<'PY' ... PY` JSON parse checks for the generated report JSON files - passed; printed `json_parse_ok`.
- `python -c "import alpha_system.runtime.tool_results"` - passed.
- `python tools/verify.py --smoke` - passed.
- `test -d research/futures_core_alpha_pilot_v1/diagnostics_reports/bbo_tradability` - passed.
- `git ls-files runs` - passed with empty output.
- `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.dbn' '**/*.zst'` - passed with empty output.
- `rg -n "\.parquet|\.sqlite|\.dbn|\.zst|\.arrow|\.feather|\.db|\.wal|provider_response|raw_payload|data/raw|data/canonical|artifacts/|/home/yuke_zhang/alpha_data" research/futures_core_alpha_pilot_v1/diagnostics_reports/bbo_tradability docs/futures_core_alpha_pilot/diagnostics/bbo_tradability.md README.md` - no matches; `rg` returned its expected no-match exit code.
- `find reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1 -maxdepth 4 -type f | rg "FUTCORE-P20|review.md|verdict.json"` - could not run as a no-match scan because `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` does not exist in this worktree; this is consistent with the user override not to create review artifacts.
- `test ! -e reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P20/review.md` - passed.
- `test ! -e reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P20/verdict.json` - passed.

Spec-listed command not run by Codex due to the explicit user override:

- `git status --short`
- `git diff --cached --name-only`

## Boundary Confirmation

The generated artifacts are value-free summaries, ids, hashes, statuses, report references, and limitations only. The executor recorded no promotion, ranking, watch state, candidate state, alpha claim, profitability claim, production claim, capital-allocation claim, live/paper/broker action, reviewer verdict, PR, or merge action.

Ralph remains responsible for authoritative staging, commit, validation ledger, review routing, verdict parsing, PR, CI, merge gate, merge, and phase done-check.
