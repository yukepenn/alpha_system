# DATA-P23 Handoff - Local Backfill Runbook and Resume Drill

## Branch And Commit State

- Branch: `auto/alpha_data_foundation_v1/data-p23-local-backfill-runbook-and-resume-drill`
- Base observed during execution: `a8a1411`
- Commits by Codex in this execution: none. Files are explicitly staged for
  Ralph-owned downstream validation/review/PR/merge gates.

## Scope Executed

Implemented the DATA-P23 local backfill resume-drill entry point under
`src/alpha_system/data/ibkr/backfill.py`. The entry point composes the existing
`DataAccessMode`, `IBKRConnectionProfile`, `IBKRClientIdPolicy`,
`IBKRReadOnlyApiBoundary`, `HistoricalRequestManifest`,
`RequestPacingPolicy`, `HistoricalChunkRecord`, `HistoricalPullLedger`,
`ProviderErrorRecord`, and content-addressed `RawDataObject` machinery.

The drill supports:

- `dry_run`: no external API and no raw write;
- `synthetic`: deterministic fixture drill, CI-safe, no network call, no repo
  data write;
- `authorized_pull`: operator-run only, outside CI, with data-pull env armed
  before a read-only historical handler can run.

The synthetic drill completes one planned chunk, records an interrupted ledger,
resumes from that ledger's `resume_token`, requests only the pending chunk, and
writes a resumed ledger with no missing expected chunks. The summary is
curated: aggregate counts, chunk IDs, ledger statuses, coverage status, and
resume-token transitions only.

## Authorization Gates And Local Outputs

Authorized mode fails closed unless `ALPHA_DATA_PULL_AUTHORIZED`,
`ALPHA_ALLOW_EXTERNAL_IBKR`, `ALPHA_IBKR_READ_ONLY_MODE`,
`ALPHA_ALLOW_RAW_LOCAL_WRITE`, `ALPHA_IBKR_HOST`, `ALPHA_IBKR_PORT`,
`ALPHA_IBKR_CLIENT_ID`, and `ALPHA_DATA_ROOT` are present and valid; `CI` is
false/unset; no configured STOP file exists; the connection doctor passes; the
clientId is in `201-209`; and a read-only `reqHistoricalData` handler is
registered. clientId `101` and `102` remain hard-blocked.

Real authorized outputs are local-only under `$ALPHA_DATA_ROOT`, outside the
repo:

```text
$ALPHA_DATA_ROOT/raw/...
$ALPHA_DATA_ROOT/metadata/ibkr_backfill_resume_drill/ledgers/...
$ALPHA_DATA_ROOT/metadata/ibkr_backfill_resume_drill/provider_errors/...
```

Raw payload slots remain immutable by `(source, request_id, chunk_id)` and
content hash. A different hash for the same logical slot is rejected. Completed
chunks are skipped during resume and are not regenerated.

No real IBKR pull or authorized resume drill was run during this execution.
Only the synthetic fixture drill was run locally.

## Documentation And README Snapshot

Added `docs/data_foundation/BACKFILL_RUNBOOK.md` with the local synthetic and
authorized operator procedure, authorization gates, connection-doctor and
clientId preconditions, `$ALPHA_DATA_ROOT` output locations, resume-token
behavior, no-overwrite behavior, and artifact audit.

Updated `docs/data_foundation/README.md` to link the new runbook.

Updated `README.md` with a compact DATA-P23 snapshot: campaign progress through
DATA-P23, next phase DATA-P24, new backfill resume-drill module/runbook, and
unchanged safety boundaries. The README adds no alpha/profitability/tradability
claim and no broker/live/paper/order/account scope.

## Tests Added

Added `tests/unit/data/test_ibkr_backfill_resume_drill.py` and the tiny
synthetic fixture
`tests/fixtures/data/synthetic_backfill_resume_drill.json`.

Coverage includes:

- synthetic interruption and resume from `HistoricalPullLedger.resume_token`;
- completed chunk skipped during resume and pending chunk requested;
- no hidden manifest chunks, preventing silent gaps;
- raw-slot no-overwrite rejection for a changed payload hash;
- authorized-pull env missing blocks before the historical handler;
- authorized-pull mode is not CI-allowed;
- no order/account-style methods exposed by the backfill path.

## Validation Results

No required validation command was skipped. The real authorized resume drill was
not part of validation and was not run.

| Command | Result |
| --- | --- |
| `git status --short` | Passed; showed only DATA-P23 working-tree changes before staging. |
| `python -m pytest tests/unit/data/test_ibkr_backfill_resume_drill.py -q` | Passed: `6 passed in 0.07s` after final edits. |
| `python -m ruff check src/alpha_system/data/ibkr/backfill.py tests/unit/data/test_ibkr_backfill_resume_drill.py` | Passed: `All checks passed!`. |
| `python -m ruff format --check src/alpha_system/data/ibkr/backfill.py tests/unit/data/test_ibkr_backfill_resume_drill.py` | Passed: `2 files already formatted`. |
| `python tools/verify.py --smoke` | Passed with no output after final edits. |
| `python -m pytest tests/unit/data -q` | Passed after final edits: `340 passed in 0.28s`. |
| `test -f docs/data_foundation/BACKFILL_RUNBOOK.md` | Passed with no output. |
| `find data -type f '!' -name README.md '!' -name .gitkeep -print` | Passed with empty output. |
| `git ls-files runs` | Passed with empty output. |
| `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` | Passed with empty output. |
| `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print` | Passed with empty output. |
| `git diff --check` | Passed with no output. |
| `PYTHONPATH=src python -m alpha_system.data.ibkr.backfill --mode synthetic --max-chunks 2 --interrupt-after-chunks 1` | Passed; emitted `SYNTHETIC_COMPLETE`, `external_call_attempted: false`, `chunks_requested_on_resume: 1`, `resumed_ledger_status: COMPLETE`. |
| `python tools/verify.py --artifacts` | Passed with no output after explicit staging. |
| `git diff --cached --name-only` | Passed; matched the exact staged file set below. |
| `git diff --cached --name-only \| rg '^runs/'` | Passed by returning no matches; no `runs/**` path is staged. |

## Artifact Audit

- `git ls-files runs` returned empty.
- Repo-local `data/` and `metadata/` audits returned empty.
- The Parquet audit returned empty.
- No raw data, canonical data, provider response, account information, local
  DB, SQLite/WAL/journal file, log, cache, Parquet/Arrow/Feather file, model
  file, secret, credential, or heavy artifact was produced or staged.
- No run-local handoff, review, verdict, checks, or repair artifact was staged.

## Exact Staged File Set

The explicit staged set for DATA-P23 is:

```text
README.md
docs/data_foundation/BACKFILL_RUNBOOK.md
docs/data_foundation/README.md
handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P23.md
src/alpha_system/data/ibkr/backfill.py
tests/fixtures/data/synthetic_backfill_resume_drill.json
tests/unit/data/test_ibkr_backfill_resume_drill.py
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

## Risks And Review Focus

Review should focus on whether the authorized external leg is sufficiently
gated before any handler invocation, whether the synthetic drill proves resume
without regenerating completed chunks, whether no-gap/no-overwrite behavior is
enforced at orchestration and store levels, and whether the runbook accurately
keeps real outputs local-only.

## Next Recommended Step

Ralph should validate the handoff/staged set, run the configured YELLOW checks
as needed, then route the phase to fresh Claude review. No review artifact was
created by Codex.
