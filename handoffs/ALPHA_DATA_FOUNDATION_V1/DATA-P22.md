# DATA-P22 Handoff - Small Authorized IBKR Smoke Pull

## Scope Executed

Implemented the DATA-P22 guarded smoke-pull entry point under
`src/alpha_system/data/ibkr/`. The entry point composes the existing
`IBKRConnectionProfile`, `IBKRClientIdPolicy`, `DataAccessMode`,
`IBKRReadOnlyApiBoundary`, `HistoricalRequestManifest`, `RequestPacingPolicy`,
`RawDataObject`, `HistoricalChunkRecord`, `HistoricalPullLedger`, and
`ProviderErrorRecord` contracts.

No real IBKR pull was run during this execution.

## Authorization Gates

The executable pull path fails closed unless:

- `DataAccessMode.authorized_pull()` validates and is outside CI;
- `ALPHA_DATA_PULL_AUTHORIZED`, `ALPHA_ALLOW_EXTERNAL_IBKR`,
  `ALPHA_IBKR_READ_ONLY_MODE`, and `ALPHA_ALLOW_RAW_LOCAL_WRITE` are true;
- `ALPHA_DATA_ROOT` is present and validates through the local data-root/raw
  layout policy;
- the connection profile validates, including clientId namespace `201-209`;
- the connection doctor reachability probe passes before handler invocation;
- a validated one-chunk `HistoricalRequestManifest` and matching
  `RequestPacingPolicy` are present.

Missing env, CI, failed doctor, reserved clientId `101`/`102`, missing manifest,
missing pacing policy, missing registered historical handler, and max-chunk
expansion all block before any read-only handler can run.

## Smoke Scope And Read-Only Posture

The pull is bounded to exactly `--max-chunks 1`. The CLI can build a runtime
one-chunk ES `TRADES` smoke manifest when an authorized smoke attempt is made
without an explicit manifest. That runtime manifest is not committed.

The smoke path invokes only a registered `reqHistoricalData` handler through
`IBKRReadOnlyApiBoundary`. The committed code does not import a generic IBKR
client library and does not expose broker, order, position, paper, live, or
account methods. Unit tests assert the forbidden method names are not reachable
from the smoke-pull path.

## Local-Only Outputs

On a successful registered-handler response, raw bytes are written only under
`$ALPHA_DATA_ROOT/raw` through `RawDataLakeLayoutPolicy` and `RawDataObject`.
The raw object path is content-addressed by SHA-256. Before writing, the store
checks the source/request/chunk slot and refuses a different existing content
hash, preserving the no-overwrite rule.

Ledgers and provider-error records are written only under
`$ALPHA_DATA_ROOT/metadata/ibkr_smoke_pull`. The stdout summary is curated and
contains only aggregate status, counts, doctor status, ledger status, and
resume token. It does not include raw bars, provider response bodies,
credentials, or account information.

## Tests Added

Added `tests/unit/data/test_ibkr_smoke_pull.py`. The tests use fake doctor
probes, fake read-only historical handlers, and an in-memory artifact store.
They perform no network call and no local raw write.

Coverage includes:

- authorized success through the read-only historical boundary;
- missing data-pull env blocks before handler invocation;
- failed doctor blocks before handler invocation;
- clientId `101`/`102` hard-block before handler invocation;
- missing manifest and missing pacing policy block;
- `authorized_pull` is not CI-allowed;
- missing registered historical handler blocks;
- provider exceptions produce redacted `ProviderErrorRecord` and quarantined
  ledger state;
- no forbidden order/account-style method is reachable.

## Documentation And README Snapshot

Added `docs/data_foundation/SMOKE_PULL.md` documenting the authorization gates,
read-only posture, bounded one-chunk scope, local-only outputs, never-in-CI
rule, and artifact audit.

Updated `docs/data_foundation/README.md` to link the new doc.

Updated `README.md` with a compact DATA-P22 executor snapshot and next phase
`DATA-P23` - Local Backfill Runbook and Resume Drill. The README keeps the
unchanged safety boundaries: read-only IBKR, clientId `101`/`102` hard-block,
never-in-CI external pulls, and local-only data artifacts.

## Validation Results

No required validation command was skipped. The real authorized smoke pull was
not part of validation and was not run.

| Command | Result |
| --- | --- |
| `git status --short` | Passed; showed only DATA-P22 working-tree changes before staging. |
| `python -m pytest tests/unit/data/test_ibkr_smoke_pull.py -q` | Passed: `10 passed in 0.05s` after final edits. |
| `python tools/verify.py --smoke` | Passed with no output after final edits. |
| `python -m pytest tests/unit/data -q` | Passed after final edits: `334 passed in 0.27s`. |
| `test -f docs/data_foundation/SMOKE_PULL.md` | Passed with no output. |
| `git ls-files runs` | Passed with empty output. |
| `find data -type f '!' -name README.md '!' -name .gitkeep -print` | Passed with empty output. |
| `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` | Passed with empty output. |
| `find artifacts -type f -size +1M -print` | Passed with empty output. |
| `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print` | Passed with empty output. |
| `git diff --check` | Passed with no output. |
| `PYTHONPATH=src python -m alpha_system.data.ibkr.pull --dry-run --max-chunks 1` | Passed; emitted `DRY_RUN`, `external_call_attempted: false`, `raw_objects_written: 0`. |

Additional note: running `python -m alpha_system.data.ibkr.pull --dry-run
--max-chunks 1` without editable install or `PYTHONPATH=src` failed with
`ModuleNotFoundError: No module named 'alpha_system'`, which is the repository's
standard src-layout behavior documented in `docs/ONBOARDING.md`.

## Artifact Audit

- `git ls-files runs` returned empty.
- The repo-local `data/`, `metadata/`, and `artifacts/` audits returned empty.
- The Parquet audit returned empty.
- No raw data, canonical data, provider response, account information, local DB,
  SQLite/WAL/journal file, log, cache, Parquet/Arrow/Feather file, model file,
  secret, credential, or heavy artifact was produced or staged.
- No run-local handoff, review, verdict, checks, or repair artifact was staged.

## Exact Staged File Set

The explicit staged set for DATA-P22 is:

```text
README.md
docs/data_foundation/README.md
docs/data_foundation/SMOKE_PULL.md
handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P22.md
src/alpha_system/data/ibkr/__init__.py
src/alpha_system/data/ibkr/pull.py
tests/unit/data/test_ibkr_smoke_pull.py
```

No `runs/**` path is staged.

## Scope Boundary Confirmation

Codex did not call Claude, run a reviewer, create review artifacts, create
`review.md`, create `verdict.json`, create a PR, merge, mark the phase PASS,
perform a real IBKR pull, place orders, query account or position data, touch
broker/paper/live paths, deploy, or make alpha, profitability, tradability, or
production-readiness claims.

Review, verdict parsing, semantic done-check, PR, CI, merge gate, merge, and
final phase outcome remain Ralph-owned.
