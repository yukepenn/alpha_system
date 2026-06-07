# FUTCORE-P17 Handoff

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P17` - VWAP / Session Diagnostics  
Executor: Codex GPT-5.5  
Lane: Yellow  
Status: executor diagnostics complete; Ralph review, validation orchestration, staging, commit, PR, CI, merge, and done-check actions pending

## Scope Completed

Ran the VWAP/session StudySpecs through the Research Runtime tool surface only.
The runtime reports cover:

- `sspec_ab3cbb830a2cede5485de19b` / `aspec_b40aee52d4399dd5b855a6ed`
- `sspec_8b8037013e7b3c14fd5b2844` / `aspec_43cd6c154bca2fcc419eee83`

Runtime surfaces used: runtime entry/input resolution, factor diagnostics,
label diagnostics, session split diagnostics, cost stress diagnostics,
`RuntimeToolResult`, and `RuntimeRunSummary`.

The locked P03/P14 registry state resolved the two session-context FeaturePacks
and the locked 5m LabelPack. No locked running VWAP, completed ETH VWAP, VWAP
trigger, or 10m/15m/30m LabelVersion pack resolved in this phase, so the
VWAP-specific signal-probe and longer-horizon cells are explicitly
`INCONCLUSIVE` rather than substituted.

## Files Changed For Ralph Explicit Staging

Codex staged no files.

Staged files by Codex:

- None.

Commit-eligible files changed for Ralph explicit staging:

- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/README.md`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/FUTCORE-P17_vwap_session_summary.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_ab3cbb830a2cede5485de19b/runtime_reports.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_8b8037013e7b3c14fd5b2844/runtime_reports.json`
- `docs/futures_core_alpha_pilot/diagnostics/vwap_session.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P17.md`

No `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P17/**` artifact was
created by Codex because the executor prompt explicitly forbade reviewer
execution and review/verdict artifact creation.

## Diagnostics Summary

The generated reports contain 6,862 joined 5m observations from the locked
development partition. In this lock, all joined observations classify outside
RTH:

- `full_session`: 6,862
- `ETH_only`: 6,862
- `ETH_evening`: 1,783
- `ETH_overnight`: 2,399
- `pre_RTH`: 450
- `post_RTH`: 280
- `RTH`: 0
- `RTH_only`: 0
- `RTH_with_ETH_context`: 0

Each report records all required session views and the primary `5m`/`10m`/`15m`/`30m`
session x horizon matrix. The 5m cells resolve through the locked LabelPack.
The `10m`, `15m`, and `30m` cells are unresolved label-pack cells. The `1m` and
`3m` horizons are flagged diagnostic-only.

Cost diagnostics used the pinned nonzero profiles `base`, `stress_1`,
`stress_2`, and `double_cost`. Thin-session stress was represented through the
runtime `ETH` and `ILLIQUID` session penalties for ETH, pre-RTH, and post-RTH
views where supported. `zero_cost` is recorded only as diagnostic context and
is not a promotion basis.

Running VWAP and running session aggregates are treated as point-in-time inputs
that must carry `available_ts`. Final-session VWAP, high, and low are treated as
completed-session context only and are not used intraday before the relevant
session completes. No final-session current-context aggregate was used
intraday. Session-minute and RTH-flag diagnostics are reported as context
diagnostics only and not as substitutes for a VWAP trigger signal.

## Validation Run By Codex

```bash
test ! -e runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/STOP && printf 'STOP absent\n'
```

Result: exit code `0`; output `STOP absent`.

```bash
PYTHONPATH=src python /tmp/futcore_p17_generate.py
```

Result: exit code `0`; wrote the four diagnostics report artifacts under
`research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/` and
reported `joined_observation_count: 6862`.

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

Initial result: exit code `0`; no stdout.

Rerun after docs and handoff edits:

```bash
python tools/verify.py --smoke
```

Result: exit code `0`; no stdout.

```bash
test -d research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session
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
git ls-files '**/*.sqlite' '**/*.db' '**/*.dbn' '**/*.zst'
```

Result: exit code `0`; empty output.

```bash
git ls-files '**/*.arrow' '**/*.feather' '**/*.wal' '**/*.log'
```

Result: exit code `0`; empty output.

```bash
python - <<'PY'
import json
from pathlib import Path
root = Path('research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session')
for path in sorted(root.rglob('*.json')):
    json.loads(path.read_text())
print('json ok', len(list(root.rglob('*.json'))))
PY
```

Result: exit code `0`; output `json ok 3`.

```bash
rg -n "\.parquet|\.sqlite|\.dbn|\.zst|\.arrow|\.feather|/home/yuke_zhang/alpha_data|value_json|provider_response|raw_payload|raw_values|feature_values|label_values|data/raw|artifacts/" research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session docs/futures_core_alpha_pilot/diagnostics/vwap_session.md README.md || true
```

Result: exit code `0`; empty output.

```bash
test -f docs/futures_core_alpha_pilot/diagnostics/vwap_session.md
```

Result: exit code `0`.

```bash
test -f handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P17.md
```

Result: exit code `0`.

```bash
test ! -e reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P17
```

Result: exit code `0`; no review artifact directory was created by Codex.

```bash
test -f research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/FUTCORE-P17_vwap_session_summary.json && test -f research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_ab3cbb830a2cede5485de19b/runtime_reports.json && test -f research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_8b8037013e7b3c14fd5b2844/runtime_reports.json
```

Result: exit code `0`.

```bash
find research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session docs/futures_core_alpha_pilot/diagnostics handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1 -maxdepth 3 -type f | sort | rg 'vwap_session|FUTCORE-P17'
```

Result: exit code `0`; output listed only the six P17 report/doc/handoff paths
expected for this executor pass.

```bash
python - <<'PY'
import json
from pathlib import Path
root = Path('research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session')
summary = json.loads((root / 'FUTCORE-P17_vwap_session_summary.json').read_text())
assert summary['runtime_tools_only'] is True
assert summary['promotion_performed'] is False
assert summary['coverage_counts']['joined_observation_count'] == 6862
for path in root.rglob('runtime_reports.json'):
    data = json.loads(path.read_text())
    assert data['runtime_tool_result']['status'] == 'INCONCLUSIVE'
    assert len(data['session_horizon_matrix']) == 36
    assert data['running_vs_final_vwap_treatment']['final_current_session_aggregate_used_intraday'] is False
print('final diagnostics assertions ok')
PY
```

Result: exit code `0`; output `final diagnostics assertions ok`.

Validation intentionally not run by Codex:

- `git status --short`: not run because the user explicitly forbade
  `git status`. Therefore no `git status --short` snapshot was collected by
  Codex.
- `git diff --cached --name-only`: not run because the user explicitly forbade
  `git diff`, and Codex staged nothing.
- `git add`, `git commit`, and `git push`: not run because the user explicitly
  forbade staging and committing.
- Fresh Yellow-lane Claude review: not run because the user explicitly forbade
  calling Claude or running reviewer.
- `review.md` and `verdict.json`: not created because the user explicitly
  forbade creating them. Ralph owns reviewer artifacts and verdict parsing.
- Full Yellow-lane lint, typecheck, test, and canary orchestration: not run by
  Codex in this executor pass; the generated spec assigns Yellow-lane
  orchestration to Ralph at `CHECKS_RUN`.

## Artifact And Boundary Confirmation

- `git ls-files runs` returned empty.
- Tracked Parquet, SQLite, DB, DBN, Zst, Arrow, Feather, WAL, and log globs
  returned empty.
- Codex staged nothing, so no heavy/value/DB artifact was staged by Codex.
- No `runs/**` path was edited or made commit-eligible.
- No raw/canonical market data, provider responses, row-level feature values,
  row-level label values, local registries, heavy artifacts, logs, caches,
  secrets, or credentials were added.
- No consumed `src/alpha_system/**` primitive was edited.
- No promotion, live trading, paper trading, broker/order call, account
  operation, deployment, PR creation, merge, reviewer call, review artifact, or
  verdict action was performed by Codex.

The outputs are value-free research diagnostics and make no profitability,
tradability, deployment, broker, paper/live, or capital-allocation claim.
