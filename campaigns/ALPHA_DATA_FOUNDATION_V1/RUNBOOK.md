# ALPHA_DATA_FOUNDATION_V1 Runbook

## 1. Runbook Purpose

This runbook is the operator manual for executing the `ALPHA_DATA_FOUNDATION_V1`
campaign under Frontier Harness Generic v3.0 Workflow 2. It covers preflight, the
Windows/WSL2 IBKR setup, the read-only IBKR connection and clientId safety policy, the
manifest/pacing/resume protocol, raw and canonical data inspection, dataset versioning,
STOP/resume, blocked-phase handling, raw/heavy commit prevention, Green/Yellow/Red lane
behavior, the Red authorization protocol for external IBKR pulls, and closeout.

The campaign builds the read-only, provenance-rich, quality-gated historical futures data
foundation for ES/NQ/RTY research. IBKR is a bootstrap historical data source **only**.
The data foundation never places orders, never queries accounts, never touches
paper/live trading, and never claims alpha, profitability, or tradability. Real data is
dangerous until it is versioned, quality-checked, provenance-labeled, and local-only.
Keep that boundary in mind at every state.

The 25 phases `DATA-P00 … DATA-P24` are all YELLOW except `DATA-P22` and `DATA-P23`,
which are RED. RED here means **external IBKR historical calls and heavy local writes**.
RED never means trading, orders, accounts, paper, or live.

## 2. Preflight Checklist

### 2.1 Required Repo Path
The active repo and all worktrees must be under `~/projects/alpha_system` on the WSL2
Linux filesystem. Forbidden active locations: `/mnt/c`, `/mnt/d`, `/mnt/e`, OneDrive,
Dropbox, Google Drive, Windows-synced folders, network drives, and temporary directories.

```bash
cd ~/projects/alpha_system
pwd                 # must be /home/<user>/projects/alpha_system
git status -sb
```

### 2.2 Required Campaign Files
```bash
test -f ACTIVE_CAMPAIGN.md
test -f campaigns/ALPHA_DATA_FOUNDATION_V1/GOAL.md
test -f campaigns/ALPHA_DATA_FOUNDATION_V1/PHASE_PLAN.md
test -f campaigns/ALPHA_DATA_FOUNDATION_V1/campaign.yaml
test -f campaigns/ALPHA_DATA_FOUNDATION_V1/ACCEPTANCE.md
test -f campaigns/ALPHA_DATA_FOUNDATION_V1/RISK_REGISTER.md
test -f campaigns/ALPHA_DATA_FOUNDATION_V1/RUNBOOK.md
test ! -f campaigns/ALPHA_DATA_FOUNDATION_V1/ACTIVE_CAMPAIGN.md
grep -q "ALPHA_DATA_FOUNDATION_V1" ACTIVE_CAMPAIGN.md
```

### 2.3 YAML Parse and Gate Coverage
```bash
python - <<'PY'
from pathlib import Path
import yaml
p = Path("campaigns/ALPHA_DATA_FOUNDATION_V1/campaign.yaml")
data = yaml.safe_load(p.read_text())
assert data["campaign_id"] == "ALPHA_DATA_FOUNDATION_V1"
assert "phases" in data and data["phases"]
assert "acceptance_gates" in data and data["acceptance_gates"]
phase_ids = [ph["id"] for ph in data["phases"]]
covered = []
for g in data["acceptance_gates"].values():
    covered.extend(g.get("phases", []))
assert set(phase_ids) == set(covered), "acceptance gate coverage mismatch"
# every phase covered exactly once
assert len(covered) == len(set(covered)), "phase covered by more than one gate"
print(f"campaign.yaml parses; {len(phase_ids)} phases; gate coverage complete and unique")
PY
```

### 2.4 Git and Artifact Preflight
```bash
git status --short
git ls-files runs                       # must be empty
find data -type f ! -name README.md ! -name ".gitkeep" -print     # must be empty
find metadata -type f ! -name README.md ! -name ".gitkeep" -print # must be empty
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
python tools/verify.py --smoke
```

### 2.5 STOP File Preflight
```bash
ls runs/*/STOP 2>/dev/null || echo "no active STOP file"
```

### 2.6 Non-Negotiable Preflight Questions
* Is the worktree under the WSL2 path? If not, STOP at RUN_INIT.
* Does `campaign.yaml` parse and cover every phase in exactly one gate? If not, block.
* Is any forbidden artifact (raw/canonical data, parquet, DB, provider response, account
  info, heavy artifact) already staged? If so, unstage before starting.
* Is any broker/order/account/paper/live scope present anywhere? If so, STOP and escalate.
* For a RED phase (`DATA-P22`/`DATA-P23`): are all scope and data authorization env vars
  present, scope-matched, and unexpired, with explicit human authorization? If not, do not
  attempt the external pull.

## 3. WSL2 / Windows IBKR Setup

The host is Windows and runs TWS or IB Gateway. The primary runtime is WSL2 Ubuntu. WSL2
may **not** be able to reach the Windows host at `127.0.0.1`/`localhost` the way a native
Windows process would; depending on networking mode, the Windows host is reachable at a
different address (for example the WSL2 default-gateway/host IP) and the TWS/IB Gateway API
must be configured to accept connections from the WSL2 client.

* The connection doctor (section 5) must **detect and report** host/port reachability
  rather than silently retrying into the wrong host.
* Do not hardcode assumptions about `127.0.0.1` reachability across the WSL2 boundary. If
  the doctor cannot reach the configured host/port, it must report a clear diagnostic and
  the operator resolves it before any pull.
* TWS / IB Gateway must have API connections enabled and the read-only API setting on; the
  configured clientId must be in the data namespace (section 6).

## 4. TWS / IB Gateway Assumptions

* Historical data only. No orders, no account trading, no positions, no paper, no live.
* Default port `4002` (IB Gateway). Default host `127.0.0.1` (adjust per section 3).
* Default clientId `201`. `read_only_mode = true` is the default connection posture.
* clientId `101` and `102` are **forbidden** — reserved for paper-account
  (`paperaccountclient`) separation. A connection profile that accepts `101` or `102`
  fails closed (section 6).
* A connection doctor must run before any pull. External provider calls require RED-lane
  authorization and never run in CI.

## 5. Connection Doctor

Run the connection doctor before any historical pull. It reports host/port reachability
and the validated connection profile; it must not expose any order or account API surface.

```bash
export ALPHA_IBKR_HOST=127.0.0.1
export ALPHA_IBKR_PORT=4002
export ALPHA_IBKR_CLIENT_ID=201
# connection doctor only; no orders, no account access (TARGET command, future phase)
python -m alpha_system.data.ibkr.doctor --host "$ALPHA_IBKR_HOST" --port "$ALPHA_IBKR_PORT" --client-id "$ALPHA_IBKR_CLIENT_ID"
```

The doctor module is implemented across `DATA-P03`/`DATA-P04` and exercised under RED only
in `DATA-P22`/`DATA-P23`. Until those phases land, the command above is a TARGET command,
not a currently working command. A failed reachability check must report clearly and must
not silently retry into a wrong host.

## 6. clientId Safety Check

clientId policy is a fail-closed validation, not a warning.

```text
clientId 101: FORBIDDEN  (reserved for paper account / paperaccountclient separation)
clientId 102: FORBIDDEN  (reserved for paper account / paperaccountclient separation)

DATA_HIST_CLIENT_ID_BASE = 201
default clientId          = 201
allowed data namespace    = 201-209
optional worker IDs       = 201 = ES, 202 = NQ, 203 = RTY
collision policy          = fail_closed
hard fail                 = clientId in {101, 102}
```

The connector design must explicitly log and validate clientId. clientId uniqueness is not
optional. Any connection profile that accepts `101` or `102`, or a clientId outside
`201–209`, must fail closed and block the connection. This is checked by client-id guard
tests and Claude review.

## 7. Read-Only Boundary Check

The data module must not be able to place an order, query positions, or touch
account-trading paths. The read-only boundary (`DATA-P04`) provides an order-method kill
switch: order/account methods on the underlying TWS API are blocked at the boundary so the
data module cannot reach them.

```bash
# read-only boundary and kill-switch behavior are covered by unit tests
python -m pytest tests/unit/data -q
```

If the data module can import or invoke any order/account-trading API, this is a global
blocker: `block_merge_and_escalate`.

## 8. Campaign File Checks

```bash
test -f ACTIVE_CAMPAIGN.md
test -f campaigns/ALPHA_DATA_FOUNDATION_V1/GOAL.md
test -f campaigns/ALPHA_DATA_FOUNDATION_V1/PHASE_PLAN.md
test -f campaigns/ALPHA_DATA_FOUNDATION_V1/campaign.yaml
test -f campaigns/ALPHA_DATA_FOUNDATION_V1/ACCEPTANCE.md
test -f campaigns/ALPHA_DATA_FOUNDATION_V1/RISK_REGISTER.md
test -f campaigns/ALPHA_DATA_FOUNDATION_V1/RUNBOOK.md
test ! -f campaigns/ALPHA_DATA_FOUNDATION_V1/ACTIVE_CAMPAIGN.md
```

## 9. YAML Parse

```bash
python - <<'PY'
from pathlib import Path
import yaml
data = yaml.safe_load(Path("campaigns/ALPHA_DATA_FOUNDATION_V1/campaign.yaml").read_text())
assert data["campaign_id"] == "ALPHA_DATA_FOUNDATION_V1"
phases = data["phases"]
assert phases, "no phases"
phase_ids = {ph["id"] for ph in phases}
gates = data["acceptance_gates"]
covered = []
for g in gates.values():
    covered.extend(g.get("phases", []))
assert phase_ids == set(covered), "gate coverage != phase set"
assert len(covered) == len(set(covered)), "phase in more than one gate"
red = {ph["id"] for ph in phases if ph["lane"] == "RED"}
assert red == {"DATA-P22", "DATA-P23"}, f"unexpected RED phases: {red}"
print(f"OK: {len(phase_ids)} phases, RED={sorted(red)}, gates cover phase set exactly once")
PY
```

## 10. Local Data Root Check

Raw and canonical real market data are local-only and live **outside** the repo. The
suggested data root is `~/alpha_data/alpha_system`, configured via `ALPHA_DATA_ROOT`.

```bash
export ALPHA_DATA_ROOT=~/alpha_data/alpha_system
# The data root must be local, outside the repo, and gitignored.
case "$ALPHA_DATA_ROOT" in
  "$(pwd)"*) echo "ERROR: data root inside repo"; ;;
  /mnt/*|*OneDrive*|*Dropbox*|*"Google Drive"*) echo "ERROR: data root on forbidden/synced path"; ;;
  *) echo "data root OK (local, outside repo): $ALPHA_DATA_ROOT" ;;
esac
mkdir -p "$ALPHA_DATA_ROOT"
git check-ignore -q "$ALPHA_DATA_ROOT" 2>/dev/null && echo "data root path ignored" || echo "note: data root is outside the repo tree (not tracked)"
```

`LocalDataRootPolicy` must enforce: data root is local, must be ignored, has forbidden
repo paths, and lists allowed subdirs. A missing local-data-root policy blocks raw writes.

## 11. Artifact Policy Check

```bash
git status --short
git ls-files runs                       # must remain empty
find data -type f ! -name README.md ! -name ".gitkeep" -print     # must be empty
find metadata -type f ! -name README.md ! -name ".gitkeep" -print # must be empty
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
# also reject committed DB/log/heavy formats outside fixtures
git ls-files | grep -E '\.(sqlite|sqlite3|db|db-journal|wal|parquet|arrow|feather|log)$' \
  | grep -v '^tests/fixtures/' || echo "no committed heavy/db/log artifacts"
```

If any forbidden path is staged, unstage it and repair the handoff before merge. Stage
explicit paths only; never `git add .` / `git add -A`.

## 12. Mini Batch Plan

The mini main batch is the primary panel: ES, NQ, RTY, `1 min`, `TRADES`,
`2018-01-01 → present`, ETH-capable canonical bars with derived RTH views.

```text
mini_main:            ES, NQ, RTY
max_concurrent_roots: 3
worker clientIds:     201 = ES, 202 = NQ, 203 = RTY
```

```bash
# manifest dry run for the mini main batch; no API calls (TARGET command, future phase)
python -m alpha_system.data.ibkr.plan --batch mini_main --start 2018-01-01 --end present --bar-size "1 min" --what TRADES --dry-run
```

## 13. Micro Batch Plan

The micro batch is a **separate** secondary path: MES, MNQ, M2K,
`2020-01-01 or earliest clean → present`. It is never mixed with the mini batch in the
same run, and `max_concurrent_roots` remains 3.

```text
micro_secondary:               MES, MNQ, M2K
separate_batch:                true
do_not_mix_mini_and_micro:     true
```

```bash
# separate micro-batch manifest dry run; no API calls (TARGET command, future phase)
python -m alpha_system.data.ibkr.plan --batch micro_secondary --start 2020-01-01 --end present --bar-size "1 min" --what TRADES --dry-run
```

## 14. IBKR Authorization Env Vars

External IBKR pulls (RED phases `DATA-P22`/`DATA-P23`) require both the harness scope
variables and the data authorization variables present, scope-matched, and unexpired,
plus explicit human authorization. The modules below do **not** exist yet — these are
TARGET commands for future phases, not currently working commands.

```bash
# harness RED scope (must be scope-matched and unexpired)
export PROJECT_OP_AUTHORIZED=1
export PROJECT_OP_SCOPE="ALPHA_DATA_FOUNDATION_V1:DATA-P22:external_ibkr_historical_smoke"
export PROJECT_OP_EXPIRES="2026-12-31T00:00:00Z"

# data authorization + connection + data root
export ALPHA_DATA_PULL_AUTHORIZED=1
export ALPHA_ALLOW_EXTERNAL_IBKR=1
export ALPHA_IBKR_HOST=127.0.0.1
export ALPHA_IBKR_PORT=4002
export ALPHA_IBKR_CLIENT_ID=201
export ALPHA_DATA_ROOT=~/alpha_data/alpha_system
export ALPHA_IBKR_READ_ONLY_MODE=1
export ALPHA_ALLOW_RAW_LOCAL_WRITE=1

# connection doctor only; no orders (TARGET command, future phase)
python -m alpha_system.data.ibkr.doctor --host "$ALPHA_IBKR_HOST" --port "$ALPHA_IBKR_PORT" --client-id "$ALPHA_IBKR_CLIENT_ID"
```

`DataAccessMode` gates which mode (dry-run, synthetic, smoke, authorized pull) allows
external API and raw writes. CI never allows external pulls. `ALPHA_IBKR_CLIENT_ID` must
satisfy the clientId safety check (section 6) before connection.

## 15. Dry-Run Manifest Generation

Manifest generation makes **no API calls**. It produces a `HistoricalRequestManifest`
(manifest id, batch id, request specs, chunk count, expected coverage, pacing policy id,
data root, manifest hash) from synthetic/declarative inputs. A missing manifest blocks any
provider pull.

```bash
# manifest dry run; no API calls (TARGET command, future phase)
python -m alpha_system.data.ibkr.plan --batch mini_main --start 2018-01-01 --end present --bar-size "1 min" --what TRADES --dry-run
```

Sample manifests committed to the repo must use fake or synthetic data only.

## 16. Request Chunk Plan

Each request is decomposed into chunks with `request_spec_id`, `chunk_id`,
`provider_request_id`, `start_ts`/`end_ts`, status, and attempt count
(`HistoricalChunkRecord`). The planner enforces duplicate-request detection and request-id
tracking. A chunk plan is a precondition for an authorized pull.

```bash
# show the planned chunk set for a manifest; no API calls (TARGET command, future phase)
python -m alpha_system.data.ibkr.plan --batch mini_main --bar-size "1 min" --what TRADES --show-chunks --dry-run
```

## 17. Pacing Guard

Naive request loops are forbidden. The `RequestPacingPolicy` requires conservative,
configurable throttling: min seconds between identical requests, max requests per window,
window seconds, backoff policy, and `bid_ask_counts_double` (BID_ASK pulls count heavier
than TRADES). A missing pacing guard blocks a pull.

```text
naive_loop_forbidden:               true
conservative_throttling_required:   true
verify_against_current_docs_or_local_smoke: true
bid_ask_counts_heavier:             true
```

Hardcoded pacing values are not treated as current truth without verification. Verify the
configured pacing against current IBKR documentation or a local smoke run before any
larger pull; record the verification source in the handoff.

## 18. Resume After Interruption

The `HistoricalPullLedger` provides an audit and resume ledger with a `resume_token`,
chunk records, coverage summary, and error summary. On interruption, resume from the
recorded ledger state.

* No silent gaps: every planned chunk is accounted for as complete, incomplete, failed, or
  quarantined.
* No raw overwrite: raw objects are immutable and content-addressed; resume never
  overwrites existing raw objects.
* Resume continues from the `resume_token` rather than regenerating completed chunks.

```bash
# resume an interrupted pull from the ledger; local-only (TARGET command, future phase)
python -m alpha_system.data.ibkr.pull --batch mini_main --resume --max-chunks 1
```

## 19. Provider Error Inspection

Every IBKR error and incomplete response is logged permanently in a `ProviderErrorRecord`
(error id, provider, request id, chunk id, error code, message, retryable, attempt,
timestamp, resolution). Errors are not fatal unless classified. Retryable errors back off
and retry; non-retryable errors quarantine the chunk and surface in the coverage/error
summary. Inspect the error ledger via the local ledger artifacts (local-only, never
committed).

## 20. Raw Data Inspection

Raw provider responses are immutable `RawDataObject`s under `$ALPHA_DATA_ROOT` — local-only
and never committed.

```bash
export ALPHA_DATA_ROOT=~/alpha_data/alpha_system
# inspect local raw objects (outside repo); never commit these
find "$ALPHA_DATA_ROOT" -maxdepth 3 -type f -print 2>/dev/null | head -n 50
# confirm nothing leaked into the repo
find data -type f ! -name README.md ! -name ".gitkeep" -print
git status --short
```

## 21. Canonicalization

Canonical silver 1-minute bars (`CanonicalBarRecord`) normalize symbols, sessions, and
contracts and must carry distinct timestamp fields per the V1 no-lookahead semantics:

```text
event_ts       = the event time of the completed bar
bar_start_ts   = bar interval start
bar_end_ts     = bar interval end
available_ts   = when the completed bar would have been usable in research/backtest
                 (NOT merely when the historical API returned it)
ingested_at    = when it was ingested locally (separate from available_ts)
```

`event_ts`, `bar_end_ts`, and `available_ts` must never be conflated. A missing
`available_ts` blocks canonicalization and blocks merge. Continuous (`CONTFUT`) history is
labeled `provider_continuous` / `non_orderable` / `not_dated_contract_truth` /
`research_diagnostics_only` and is never treated as dated-contract truth.

```bash
python -m pytest tests/no_lookahead -q   # DATA-P15
```

## 22. Data Quality Report

`DataQualityReport` is a fail-closed audit covering gaps, duplicates, non-monotonic
timestamps, OHLC errors, zero/negative prices, zero-volume anomalies, DST anomalies,
session coverage, roll discontinuities, and provider-error summary. Silent gaps fail
closed (block versioning and merge). The report does not imply alpha readiness.

```bash
test -f docs/data_foundation/DATA_QUALITY.md
python -m pytest tests/unit/data -q
```

## 23. Coverage Audit

`CoverageReport` reports coverage by symbol, contract, session, and partition, plus missing
intervals and incomplete chunks. Coverage does not imply quality unless linked to a quality
report. Any silent gap is a fail-closed condition.

```bash
test -f docs/data_foundation/COVERAGE_REPORT.md
python -m pytest tests/unit/data -q
```

## 24. Dataset Version Registration

A `DatasetVersion` is registered only when quality, coverage, and manifest are present. It
records source, symbol universe, bar size, what_to_show, start/end, contract universe, roll
policy, and reproducible `manifest_hash` / `code_hash` / `config_hash` /
`quality_report_hash`. A dataset version does not imply research approval.

```bash
test -f docs/data_foundation/DATASET_VERSION.md
python -m pytest tests/integration/data -q
# the registry DB is local-only and never committed
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
```

## 25. STOP File Behavior

Create `runs/<run_id>/STOP` with a short reason. Ralph checks STOP before provider calls,
phase selection, Codex execution, validation, review, PR creation, CI waiting, the merge
gate, merge, the done-check, and next-phase selection, and halts at the next checkpoint.

```bash
echo "operator stop: <reason>" > runs/<run_id>/STOP
```

`runs/**` is local-only and must never be staged or committed. Codex must not ignore an
active STOP file inside a Workflow 2 run.

## 26. Resume Behavior

Remove or resolve the STOP condition, then resume the run. Ralph resumes from recorded run
state and does not regenerate completed, merged work.

```bash
rm runs/<run_id>/STOP
```

For a partially completed external pull, resume also follows the pull ledger and
`resume_token` (section 18): no silent gaps, no raw overwrite.

## 27. Blocked Phase Handling

A `BLOCKED` verdict, an exceeded repair limit (`max_repair_attempts = 3`), missing
authorization, contradictory scope, or impossible validation produces a **truthful** blocked
handoff under `handoffs/ALPHA_DATA_FOUNDATION_V1/<PHASE_ID>.md` plus the local-only
`runs/<run_id>/phases/<phase_id>/handoff.md`. Dependent phases are blocked. Fake completion
is forbidden. Escalate to the human, resolve the blocker, then resume.

## 28. Raw/Heavy Commit Prevention

```bash
git status --short
git diff --name-only
git ls-files runs
find data -type f ! -name README.md ! -name ".gitkeep" -print
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
```

If any forbidden path is staged (raw/canonical data, parquet/arrow/feather, DB/journal/WAL,
provider responses, account info, heavy artifacts, full report bundles, or any `runs/`
path), unstage it and repair the handoff before merge. Stage explicit paths only; never
`git add .` / `git add -A`. Never force push.

## 29. Green / Yellow / Red Lane Behavior

### Green
Not used by default in this campaign. If a pure-docs phase were ever marked GREEN it would
still require checks, handoff, and artifact policy.

### Yellow
`DATA-P00 … DATA-P21` and `DATA-P24` are YELLOW: automatic execute / repair / PR / merge
after fresh Claude Opus 4.8 xhigh review with a `PASS` or `PASS_WITH_WARNINGS` verdict and
all gates passing. No external provider call occurs in any YELLOW phase.

### Red
`DATA-P22` (Small Authorized IBKR Smoke Pull) and `DATA-P23` (Local Backfill Runbook and
Resume Drill) are RED. RED means external IBKR historical calls and heavy local writes —
**never** trading, orders, accounts, paper, or live. RED requires scoped authorization
(section 30), Claude review, no CI execution, local-only outputs, no auto-merge, and no
data artifacts committed.

## 30. Red Authorization for External IBKR Pulls

A RED external pull may proceed only when **all** of the following hold:

```text
PROJECT_OP_AUTHORIZED       present
PROJECT_OP_SCOPE            present and scope-matched to the RED phase
PROJECT_OP_EXPIRES          present and unexpired
ALPHA_DATA_PULL_AUTHORIZED  present
ALPHA_ALLOW_EXTERNAL_IBKR   present
+ explicit human authorization
+ connection doctor passes (section 5)
+ clientId safety check passes (section 6)
+ no active STOP file
```

* The pull never runs in CI (`real_data_pull_forbidden_in_ci`).
* Outputs are local-only under `$ALPHA_DATA_ROOT`; no raw/canonical/provider/account
  artifacts are committed; commit only smoke/backfill code, runbook docs, and
  curated synthetic-or-redacted summaries.
* `auto_merge = false` for RED; a human reviews and authorizes the merge.
* RED never authorizes orders, accounts, paper, or live scope in any lane.

```bash
# authorized small smoke pull only; local-only; no CI; no data commit (TARGET command, future phase)
python -m alpha_system.data.ibkr.pull --batch mini_main --smoke --max-chunks 1
```

After any RED pull, re-run the artifact audit (section 11/28) and confirm `git ls-files
runs` is empty and no data leaked into the repo.

## 31. Final Closeout (DATA-P24)

At `DATA-P24` (End-to-End Data Foundation Dry Run and Closeout):

* Run the end-to-end data-foundation dry run (synthetic; no external pull).
* Run the acceptance audit across all gates (`ACCEPTANCE.md`).
* Run the final semantic done-check.
* Write `campaigns/ALPHA_DATA_FOUNDATION_V1/CLOSEOUT.md` with the final verdict
  (`COMPLETE`, `COMPLETE_WITH_WARNINGS`, or `BLOCKED`).
* Update `ACTIVE_CAMPAIGN.md`.
* Add durable lessons to `project-skill` when applicable.
* Record next-campaign readiness (feature/label foundation, agent factory, core alpha,
  AlphaBook, validation governance — each only under its own authorized contract).

```bash
python tools/verify.py --smoke
python tools/verify.py --all
python -m pytest tests/unit/data -q
python -m pytest tests/integration/data -q
test -f campaigns/ALPHA_DATA_FOUNDATION_V1/CLOSEOUT.md
test -f docs/data_foundation/END_TO_END_DRY_RUN.md
find data -type f ! -name README.md ! -name ".gitkeep" -print
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
find artifacts -type f -size +1M -print
git ls-files runs
```

The campaign is done only when all gates pass (or a truthful `BLOCKED` is recorded), the
artifact audit is clean, and no prohibited scope or claim exists.

## 32. Operator Quick Commands

### Repo and Campaign Checks
```bash
cd ~/projects/alpha_system
git status --short
git status -sb
test -f ACTIVE_CAMPAIGN.md
test -f campaigns/ALPHA_DATA_FOUNDATION_V1/campaign.yaml
grep -q "ALPHA_DATA_FOUNDATION_V1" ACTIVE_CAMPAIGN.md
```

### Artifact Audit
```bash
git ls-files runs
find data -type f ! -name README.md ! -name ".gitkeep" -print
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
```

### Tests and Static Checks
```bash
python tools/verify.py --smoke
python tools/verify.py --all
python -m pytest tests/unit/data -q
python -m pytest tests/integration/data -q
python -m pytest tests/no_lookahead -q
python tools/hooks/canary_runner.py
```

### Handoff / Review Inspection
```bash
cat handoffs/ALPHA_DATA_FOUNDATION_V1/<PHASE_ID>.md
ls reviews/ALPHA_DATA_FOUNDATION_V1/
ls runs/<run_id>/phases/<phase_id>/
```

### STOP File
```bash
echo "operator stop: <reason>" > runs/<run_id>/STOP
rm runs/<run_id>/STOP
```

### Git Safety
```bash
# Stage explicit paths only — never:
#   git add .
#   git add -A
# Never force push. Never commit raw/canonical data, parquet, DB, provider responses,
# account info, heavy artifacts, or any runs/ path.
git add <explicit/path/one> <explicit/path/two>
```

## 33. Final Reminder of Out-of-Scope Boundaries

This campaign installs a read-only data-admissibility foundation only. It must end with:
no real alpha search, no factor/label/strategy research, no portfolio allocation, no
broker/order/account/paper/live trading, no order routing, no production execution adapter,
no real-time/L1/L2/MBO/tick feed, no order-book replay, no ML/DL expansion, and no
alpha/profitability/tradability/production-readiness claims.

Be aggressive about data admissibility — manifests, pacing, resume ledgers, provenance,
timestamp semantics, fail-closed quality and coverage, versioning, and local-only artifact
policy. Be conservative about market claims and trading scope — IBKR is a read-only
historical data source, RED never means trading, and no result here is alpha, profitable,
tradable, or production/paper/live/broker-ready.
