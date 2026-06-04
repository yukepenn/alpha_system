# Local Backfill Runbook And Resume Drill

`DATA-P23` adds a guarded local resume-drill entry point for historical IBKR
backfill orchestration:

```bash
python -m alpha_system.data.ibkr.backfill --mode synthetic --max-chunks 2 --interrupt-after-chunks 1
```

The command is an operator entry point, not a CI job. Use the repository's
normal editable install from `docs/ONBOARDING.md`; without that install, prefix
local module invocations with `PYTHONPATH=src`.

## What The Drill Demonstrates

The drill plans a small manifest-backed historical pull, completes the first
chunk, records an interruption ledger, resumes from that ledger's
`resume_token`, and requests only the non-complete chunks. It writes a second
ledger for the resumed state.

The summary is curated. It contains aggregate counts, chunk IDs, coverage
status, ledger statuses, and resume-token transitions. It does not print raw
bars, provider response bodies, account information, credentials, or full
payload dumps.

No output from a real drill is commit-eligible.

## Modes

The entry point is driven by `DataAccessMode`.

| Mode | External API | Local raw write | CI allowed | Use |
| --- | --- | --- | --- | --- |
| `dry_run` | no | no | yes | validate command shape and optional manifest/pacing inputs |
| `synthetic` | no | no repo write | yes | deterministic fixture resume drill |
| `authorized_pull` | read-only historical only | `$ALPHA_DATA_ROOT` only | no | operator-run local IBKR historical resume drill |

Synthetic mode uses `tests/fixtures/data/synthetic_backfill_resume_drill.json`
unless a manifest is supplied programmatically. It performs no network call.

## Live Read-Only Connector (Real Pull)

An optional lazy read-only IBKR historical connector now exists. It registers
only `reqHistoricalData`; no generic IB client escapes the adapter; broker,
order, account, position, paper, and live surfaces remain forbidden. Real pulls
are operator-only and never run in CI.

Install the optional dependency in a local venv:

```bash
python -m venv .venv && .venv/bin/pip install -e ".[ibkr]"
```

Fallback for an operator machine without a venv:

```bash
python -m pip install --target ~/.alpha_ibkr_libs ib_insync
export PYTHONPATH=src:~/.alpha_ibkr_libs
```

Arm all four authorization gates with true values and configure the exact IBKR
endpoint and local data root:

```bash
export ALPHA_DATA_PULL_AUTHORIZED=1
export ALPHA_ALLOW_EXTERNAL_IBKR=1
export ALPHA_IBKR_READ_ONLY_MODE=1
export ALPHA_ALLOW_RAW_LOCAL_WRITE=1
export ALPHA_IBKR_HOST=127.0.0.1
export ALPHA_IBKR_PORT=4002
export ALPHA_IBKR_CLIENT_ID=201
export ALPHA_DATA_ROOT=~/alpha_data/alpha_system
```

Run the bounded smoke connector:

```bash
python -m alpha_system.data.ibkr.smoke_connect --batch mini_main --max-chunks 1
```

This connector is read-only historical data only. It requests one tiny ES
historical chunk, keeps raw output under `ALPHA_DATA_ROOT`, does not register a
dataset version, and must never run in CI.

## Task 1B: Full Local Backfill (Operator-Supervised)

This is the real-pull operator path for ADF1 Task 1B. It is read-only
historical data only, writes raw/canonical/registry artifacts only under
`ALPHA_DATA_ROOT`, and must never run in CI. No raw, canonical, registry,
cache, log, DB, Parquet, Arrow, or Feather output is commit-eligible.

Prerequisites:

- Install the optional IBKR dependency with
  `python -m venv .venv && .venv/bin/pip install -e ".[ibkr]"`, or use the
  `~/.alpha_ibkr_libs` target-install fallback above.
- Arm all eight authorization/connection values:
  `ALPHA_DATA_PULL_AUTHORIZED=1`, `ALPHA_ALLOW_EXTERNAL_IBKR=1`,
  `ALPHA_IBKR_READ_ONLY_MODE=1`, `ALPHA_ALLOW_RAW_LOCAL_WRITE=1`,
  `ALPHA_IBKR_HOST`, `ALPHA_IBKR_PORT`, `ALPHA_IBKR_CLIENT_ID`, and
  `ALPHA_DATA_ROOT`.
- Confirm the configured gateway is reachable at the exact host/port and that
  the client id is in the allowed data-client range.

Generate the recent-slice and full dated-FUT manifests:

```bash
python -m alpha_system.data.ibkr.manifest_builder \
  --output-dir "$ALPHA_DATA_ROOT/manifests" \
  --full-end-date <YYYY-MM-DD>
```

This emits `recent_slice_manifest.json` and `full_backfill_manifest.json`. The
full manifest uses dated quarterly `FUT` contracts because IBKR `CONTFUT`
cannot backfill pre-roll history and rejects `endDateTime`.

Run the proven recent slice:

```bash
python -m alpha_system.data.ibkr.backfill_connect \
  --manifest "$ALPHA_DATA_ROOT/manifests/recent_slice_manifest.json" \
  --pacing-policy configs/data/request_pacing_policy_to_be_verified.json
```

Register the first DatasetVersion from a complete ETH session:

```bash
python -m alpha_system.data.ibkr.materialize \
  --symbols ES,NQ,RTY \
  --registry-path "$ALPHA_DATA_ROOT/registry/datasets.sqlite" \
  --data-version <id> \
  --partition latest_shadow_candidate \
  --start-ts <session open Z> \
  --end-ts <session close Z>
```

The materialize window must bracket exactly one contiguous full ETH session.
For the recent complete CME index session during Central Daylight Time, that is
the prior CME trading day's `22:00:00Z`→`21:00:00Z` window.

Run the full 2018→present local backfill:

```bash
python -m alpha_system.data.ibkr.backfill_connect \
  --manifest "$ALPHA_DATA_ROOT/manifests/full_backfill_manifest.json" \
  --pacing-policy configs/data/request_pacing_policy_to_be_verified.json \
  --max-chunks <N>
```

The full pull is resumable through the resume token and ledgers under
`$ALPHA_DATA_ROOT/metadata`; re-run the connector to resume pending chunks. For
the 2018→2026 ES/NQ/RTY scope, the generated full manifest contains 108 dated
quarterly `FUT` request specs: three symbols times nine years times four
quarterly contracts. At runtime the runner expands dated `1 min` `FUT` specs
into stable one-day sub-chunks before provider requests and ledgers are built.
`CONTFUT` recent slices are not sub-chunked and still use `endDateTime=""`.

This is a multi-day, pacing-limited, operator-supervised job. The runner
enforces the configured `RequestPacingPolicy` immediately before each real
provider request, retries provider exceptions with deterministic backoff, and
continues later chunks after quarantining an exhausted chunk.

## Authorization Gates

A real authorized resume drill fails closed unless all runtime gates pass:

- `ALPHA_DATA_PULL_AUTHORIZED=true`
- `ALPHA_ALLOW_EXTERNAL_IBKR=true`
- `ALPHA_IBKR_READ_ONLY_MODE=true`
- `ALPHA_ALLOW_RAW_LOCAL_WRITE=true`
- `ALPHA_IBKR_HOST`, `ALPHA_IBKR_PORT`, and `ALPHA_IBKR_CLIENT_ID` present
- `ALPHA_IBKR_CLIENT_ID` is in `201-209`; `101` and `102` are hard-blocked
- `ALPHA_DATA_ROOT` present, local, outside the repository, and not a synced,
  mounted, network, or temporary path
- `CI` is false or unset
- no configured Frontier STOP file exists
- connection doctor passes against exactly the configured host/port
- a validated `HistoricalRequestManifest` and matching `RequestPacingPolicy`
  are present
- the read-only boundary has a registered `reqHistoricalData` handler

The committed connector imports `ib_insync` lazily only on real connector
paths. It registers only the historical `reqHistoricalData` callable on
`IBKRReadOnlyApiBoundary`. Broker, order, position, paper, live, and account
methods are not exposed.

## Local Output Locations

Authorized mode writes only under `$ALPHA_DATA_ROOT`, outside the repo:

```text
$ALPHA_DATA_ROOT/raw/source=<source>/request=<request_id>/chunk=<chunk_id>/sha256=<prefix>/<digest>.raw
$ALPHA_DATA_ROOT/metadata/ibkr_backfill_resume_drill/ledgers/<pull_id>.json
$ALPHA_DATA_ROOT/metadata/ibkr_backfill_resume_drill/provider_errors/<error_id>.json
```

Raw payloads are content-addressed with SHA-256. The logical raw slot is
`(source, request_id, chunk_id)`. If that slot is already bound to a different
content hash, the drill refuses to continue. Resuming a completed chunk skips
the chunk rather than regenerating its raw object.

## Resume Drill Procedure

1. Confirm the repo is under the WSL2 Linux filesystem:

```bash
pwd
```

2. Run the local synthetic drill:

```bash
PYTHONPATH=src python -m alpha_system.data.ibkr.backfill --mode synthetic --max-chunks 2 --interrupt-after-chunks 1
```

Expected shape: `external_call_attempted=false`, one interrupted ledger, one
resumed ledger, first chunk listed as skipped during resume, second chunk listed
as resumed, and final ledger status `COMPLETE`. This is fixture-only and does
not assert real coverage or quality.

3. For an authorized local drill, arm the runtime env outside CI:

```bash
export ALPHA_DATA_PULL_AUTHORIZED=true
export ALPHA_ALLOW_EXTERNAL_IBKR=true
export ALPHA_IBKR_READ_ONLY_MODE=true
export ALPHA_ALLOW_RAW_LOCAL_WRITE=true
export ALPHA_IBKR_HOST=127.0.0.1
export ALPHA_IBKR_PORT=4002
export ALPHA_IBKR_CLIENT_ID=201
export ALPHA_DATA_ROOT=~/alpha_data/alpha_system
```

4. Run the connection doctor through the authorized entry point or local
operator wrapper. The doctor must probe exactly the configured host/port. Do
not retry a different host silently.

5. Run the authorized drill with a small validated manifest and the conservative
pacing policy:

```bash
PYTHONPATH=src python -m alpha_system.data.ibkr.backfill \
  --mode authorized_pull \
  --manifest "$ALPHA_DATA_ROOT/manifests/<validated-small-backfill-manifest>.json" \
  --pacing-policy configs/data/request_pacing_policy_to_be_verified.json \
  --max-chunks 2 \
  --interrupt-after-chunks 1
```

The real external leg is read-only historical data only. It must never run in
CI and must never write inside the repository.

## Artifact Audit

After any drill, run the repo audit before staging:

```bash
git ls-files runs
find data -type f '!' -name README.md '!' -name .gitkeep -print
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
```

Expected result: empty output for tracked `runs/**`, no repo-local data files
beyond placeholders, no metadata DB/log/cache files, and no Parquet/Arrow/
Feather artifacts outside approved fixtures.

## Boundaries

This runbook does not authorize orders, positions, account queries, paper
trading, live trading, broker operations, real-time market data, alpha search,
factor or label research, deployment, or production-readiness claims. A
completed drill is only evidence that the guarded local resume path accounted
for planned chunks and preserved raw immutability; it is not a claim that real
data is fully pulled, quality accepted, or ready for research use.
