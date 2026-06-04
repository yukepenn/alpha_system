# DATA-P22 IBKR Smoke Pull

`DATA-P22` adds a guarded entry point for a small read-only IBKR historical
smoke pull:

```bash
python -m alpha_system.data.ibkr.pull --batch mini_main --smoke --max-chunks 1
```

The command is an operator entry point, not a CI job. The phase implementation
does not run a real pull during validation. Use the repository's normal
editable install from `docs/ONBOARDING.md`; without that install, prefix local
module invocations with `PYTHONPATH=src`.

## Authorization Gates

A real smoke pull fails closed unless all runtime gates pass:

- `ALPHA_DATA_PULL_AUTHORIZED=true`
- `ALPHA_ALLOW_EXTERNAL_IBKR=true`
- `ALPHA_IBKR_READ_ONLY_MODE=true`
- `ALPHA_ALLOW_RAW_LOCAL_WRITE=true`
- `ALPHA_IBKR_HOST`, `ALPHA_IBKR_PORT`, and `ALPHA_IBKR_CLIENT_ID` present
- `ALPHA_DATA_ROOT` present and outside the repository
- `CI` is false or unset
- no configured Frontier STOP file exists

The active mode is `DataAccessMode.authorized_pull()`. It allows external API
reads and local raw writes, requires the env gates above, and is not
CI-allowed. Missing or false env values block before the read-only historical
handler can run.

## Read-Only Posture

The smoke pull uses `IBKRConnectionProfile`, `IBKRClientIdPolicy`, and
`IBKRReadOnlyApiBoundary`.

- clientId `101` and `102` remain hard-blocked.
- clientIds outside `201-209` fail closed.
- The connection doctor validates the configured profile and probes exactly the
  configured host/port before any provider call.
- There is no alternate-host retry.
- Only the registered historical `reqHistoricalData` boundary method can run.
- Broker, order, position, paper, live, and account surfaces are not exposed.

The committed entry point stores only the read-only boundary orchestration. It
does not import a generic IBKR client library or add a broker adapter.

## Bounded Pull

DATA-P22 is bounded to one smoke chunk:

```bash
--max-chunks 1
```

The runner requires a validated `HistoricalRequestManifest`, an armed
`RequestPacingPolicy`, matching manifest/pacing IDs, and a one-chunk manifest
before a handler invocation. If no manifest is supplied to the CLI during an
authorized smoke attempt, the command builds a runtime one-chunk ES `TRADES`
smoke manifest from the configured data root and clientId. This runtime
manifest is not committed.

## Local-Only Outputs

When a registered read-only handler returns a historical payload, raw bytes are
written only under `$ALPHA_DATA_ROOT/raw` through `RawDataLakeLayoutPolicy` and
`RawDataObject`. Paths are content-addressed by SHA-256. The raw slot is
checked before writing so a different content hash cannot overwrite an existing
source/request/chunk slot.

The runner records a `HistoricalChunkRecord` and a `HistoricalPullLedger` with
a `resume_token` under `$ALPHA_DATA_ROOT/metadata/ibkr_smoke_pull`. Provider
errors are redacted into `ProviderErrorRecord` files in the same local-only
metadata tree. These files are never commit-eligible.

The command emits only a curated summary: gate status, doctor status, chunk
counts, ledger status, and resume token. It does not print raw bars, provider
response bodies, credentials, or account information.

## Never In CI

CI must not run a real smoke pull. CI may run:

```bash
python tools/verify.py --smoke
python -m pytest tests/unit/data -q
```

Both commands are local-only for DATA-P22 and do not call IBKR. Unit tests use
fake read-only handlers and fake doctor probes.

## Artifact Audit

After any operator-run smoke pull, re-run the local artifact audit:

```bash
git ls-files runs
find data -type f '!' -name README.md '!' -name .gitkeep -print
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
```

Expected result: no `runs/**` tracked files and no repo-local raw, canonical,
provider, DB, cache, log, or heavy artifacts.
