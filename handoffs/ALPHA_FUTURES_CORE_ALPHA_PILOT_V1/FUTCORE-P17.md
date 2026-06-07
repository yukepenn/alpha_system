# FUTCORE-P17 Handoff

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P17` - VWAP / Session Diagnostics  
Executor: Codex GPT-5.5  
Lane: Yellow  
Status: executor diagnostics complete; Ralph review, validation orchestration,
authoritative staging, commit, PR, CI, merge, and done-check actions pending

## Scope Completed

Ran the two canonical P14 `vwap_session` StudySpecs through the Research
Runtime tool surface only:

- `sspec_69c22ec5847395ac8e81b5b6` /
  `aspec_b40aee52d4399dd5b855a6ed`
- `sspec_aff70fcbc4b7ff226fcc8149` /
  `aspec_43cd6c154bca2fcc419eee83`

Runtime surfaces used: `RuntimeEntryRequest` /
`evaluate_runtime_entry_request`, `resolve_runtime_input_pack`, factor
diagnostics, label diagnostics, session split diagnostics, cost stress
diagnostics, `RuntimeToolResult`, and `RuntimeRunSummary`.

The locked registry resolved six P14 FeaturePacks and three LabelPacks
(`5m`, `10m`, `30m`) from the P03/P13/P14 pack. The P15 `15m` LabelSpec has no
locked LabelVersion in this pack, so all `15m` matrix cells are recorded as
unresolved. No locked running VWAP, completed ETH VWAP, distance-to-VWAP, or
VWAP trigger FeaturePack resolved, so VWAP-specific signal-probe diagnostics
are `INCONCLUSIVE`; no session-minute, range-position, or RTH-flag context was
substituted as a VWAP signal.

No promotion, ranking, survivor state, review artifact, verdict, PR, merge,
live/paper/broker/order action, production deployment, or capital-allocation
claim was made.

## Staging Status

Codex staged no files. The executor prompt explicitly forbade Codex from
running `git add`, `git commit`, `git push`, `git status`, or `git diff`.
Ralph owns authoritative staging and commit.

Exact file paths staged by Codex:

- None.

Commit-eligible file paths for Ralph explicit staging:

- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/README.md`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/FUTCORE-P17_vwap_session_summary.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_69c22ec5847395ac8e81b5b6/runtime_reports.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_aff70fcbc4b7ff226fcc8149/runtime_reports.json`
- `docs/futures_core_alpha_pilot/diagnostics/vwap_session.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P17.md`

Commit-eligible stale report deletions for Ralph explicit staging:

- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_ab3cbb830a2cede5485de19b/runtime_reports.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_8b8037013e7b3c14fd5b2844/runtime_reports.json`

No `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P17/**` artifact was
created by Codex because the executor prompt explicitly forbade reviewer
execution and review/verdict artifact creation.

## Diagnostics Coverage

Per-study report artifacts contain:

- factor diagnostics for session-minute and range-position context;
- label diagnostics across locked `5m`, `10m`, and `30m` LabelVersions;
- required session split diagnostics for `full_session`, `RTH_only`,
  `ETH_only`, `ETH_evening`, `ETH_overnight`, `pre_RTH`, `RTH`, `post_RTH`,
  and `RTH_with_ETH_context`;
- a 36-cell session x primary-horizon matrix over `5m`, `10m`, `15m`, and
  `30m`;
- cost diagnostics for `base`, `stress_1`, `stress_2`, and `double_cost`, with
  `zero_cost` recorded as diagnostic-only;
- explicit running-vs-final VWAP treatment confirming no active-session final
  VWAP/high/low is visible intraday before session completion.

Joined observations by primary horizon:

| Horizon | Joined observations | Status |
| --- | ---: | --- |
| `5m` | 6,862 | Locked LabelVersion resolved. |
| `10m` | 6,832 | Locked LabelVersion resolved. |
| `15m` | 0 | No locked LabelVersion in the pack. |
| `30m` | 6,712 | Locked LabelVersion resolved. |

In the locked development partition, all joined observations classify outside
RTH. The `RTH`, `RTH_only`, and `RTH_with_ETH_context` cells are therefore
zero-count diagnostic cells. The `1m` and `3m` horizons are labeled
diagnostic-only and are not a promotion basis.

## Running-Vs-Final VWAP Confirmation

Running VWAP and running session aggregates are treated as point-in-time inputs
only and must carry `available_ts`. Final-session VWAP, high, and low are
completed-session context only and were not used intraday before the relevant
session completed.

For `sspec_69c22ec5847395ac8e81b5b6`, no locked running VWAP or reclaim-event
FeaturePack resolved. For `sspec_aff70fcbc4b7ff226fcc8149`, no locked
completed ETH VWAP or first-RTH running VWAP FeaturePack resolved. Both reports
therefore keep VWAP signal-probe status `INCONCLUSIVE` rather than substituting
another context field.

## Validation Run By Codex

```bash
test ! -e runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/STOP && test ! -e runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/phases/FUTCORE-P17/STOP
```

Result: exit code `0`; no active STOP file was present.

```bash
PYTHONPATH=src python /tmp/futcore_p17_generate.py
```

Initial result: exit code `1`; the consumed cost primitive rejected uppercase
`BUY` with `side must be buy or sell`. The local-only generator was repaired to
use lowercase `buy`, then rerun.

Final result: exit code `0`; output:

```text
{"joined_observation_count_by_horizon": {"10m": 6832, "15m": 0, "30m": 6712, "5m": 6862}, "report_count": 3, "study_specs": ["sspec_69c22ec5847395ac8e81b5b6", "sspec_aff70fcbc4b7ff226fcc8149"]}
```

```bash
python -c "import alpha_system.runtime.tool_results"
```

Result: exit code `0`.

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
git ls-files '**/*.sqlite' '**/*.db' '**/*.dbn' '**/*.zst' '**/*.arrow' '**/*.feather' '**/*.wal' '**/*.log'
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
python - <<'PY'
... assert canonical StudySpec ids, runtime INCONCLUSIVE status, 36 matrix cells,
    no intraday final-session aggregate, required cost profiles, and horizon counts ...
PY
```

Result: exit code `0`; output `diagnostics assertions ok`.

```bash
rg -n "sspec_ab3c|sspec_8b803|/home/|\.parquet|\.sqlite|\.dbn|\.zst|\.arrow|\.feather|value_json|provider_response|raw_payload|raw_values|feature_values|label_values|data/raw|artifacts/" research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session docs/futures_core_alpha_pilot/diagnostics/vwap_session.md README.md || true
```

Result: exit code `0`; empty output after the durable docs were updated to avoid
noncanonical StudySpec ids and forbidden path/value tokens.

```bash
test ! -e research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_ab3cbb830a2cede5485de19b/runtime_reports.json && test ! -e research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_8b8037013e7b3c14fd5b2844/runtime_reports.json
```

Result: exit code `0`; stale noncanonical report files are absent.

```bash
test -f research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/FUTCORE-P17_vwap_session_summary.json && test -f research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_69c22ec5847395ac8e81b5b6/runtime_reports.json && test -f research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_aff70fcbc4b7ff226fcc8149/runtime_reports.json && test -f docs/futures_core_alpha_pilot/diagnostics/vwap_session.md
```

Result: exit code `0`.

```bash
test ! -e reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P17 && test ! -e runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/phases/FUTCORE-P17/review.md && test ! -e runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/phases/FUTCORE-P17/verdict.json
```

Result: exit code `0`; Codex created no review or verdict artifact.

Validation intentionally not run by Codex:

- `git status --short`: not run because the executor prompt explicitly forbade
  `git status`; no Codex git-status snapshot is available.
- `git diff --cached --name-only`: not run because the executor prompt
  explicitly forbade `git diff`, and Codex staged nothing.
- `git add`, `git commit`, and `git push`: not run because the executor prompt
  explicitly forbade staging and committing.
- Fresh Yellow-lane Claude review: not run because the executor prompt
  explicitly forbade calling Claude or running reviewer.
- `review.md` and `verdict.json`: not created because the executor prompt
  explicitly forbade creating them. Ralph owns review orchestration and verdict
  parsing.

## Artifact And Boundary Confirmation

- `git ls-files runs` returned empty.
- Tracked Parquet, SQLite, DB, DBN, Zst, Arrow, Feather, WAL, and log globs
  returned empty.
- Codex staged nothing, so no heavy/value/DB artifact or `runs/**` path was
  staged by Codex.
- No raw/canonical market data, provider responses, row-level feature values,
  row-level label values, local registries, heavy artifacts, logs, caches,
  secrets, or credentials were added.
- No consumed `src/alpha_system/**` primitive was edited.
- No live trading, paper trading, broker operation, order routing, account
  operation, deployment, PR creation, merge, reviewer call, review artifact, or
  verdict action was performed.

The outputs are value-free research diagnostics and make no profitability,
tradability, deployment, broker, paper/live, production, or capital-allocation
claim.
