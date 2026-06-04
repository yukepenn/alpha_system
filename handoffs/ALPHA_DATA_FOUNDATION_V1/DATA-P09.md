# DATA-P09 Handoff - Raw Local Data Lake Layout

## Scope Executed

Implemented the DATA-P09 raw local data lake contract under
`src/alpha_system/data/foundation/bars.py`.

`RawDataObject` is now a frozen, fail-closed metadata record with mapping
round-trip support and the required fields:

- `raw_object_id`
- `source`
- `request_id`
- `chunk_id`
- `path`
- `content_hash`
- `schema_hint`
- `retrieved_at`
- `row_count`

Validation requires `content_hash` to use `sha256:<64 hex digest>`, `source` to
link to a `DataSourceProfile.source_id`, `request_id` and `chunk_id` to be
present path-safe ids, `retrieved_at` to be timezone-aware, and `row_count` to be
non-negative. `schema_hint` is provider-shape metadata only and is rejected if it
claims canonical truth. `RawDataObject.raw_object_ref` derives the DATA-P08
compatible `raw://sha256/<digest>` reference from `content_hash`.

## Raw Lake Layout And Immutability

Added `RawDataLakeLayoutPolicy`, `resolve_raw_object_storage_path()`,
`require_raw_data_lake_layout_policy()`, `raw_object_ref_for_content_hash()`, and
`assert_raw_slot_immutable()`.

`RawDataLakeLayoutPolicy` delegates root validation to `LocalDataRootPolicy`.
A missing local-root policy or raw-layout policy fails closed before path
resolution. Resolved paths stay under `ALPHA_DATA_ROOT/raw/` and use a
content-addressed, source/request/chunk-linked shape:

```text
$ALPHA_DATA_ROOT/raw/source=<source>/request=<request_id>/chunk=<chunk_id>/sha256=<first2>/<digest>.raw
```

`assert_raw_slot_immutable()` protects the logical raw slot
`(source, request_id, chunk_id)` and rejects attempts to bind a different
`content_hash` to an existing slot. Reusing the same content hash for the same
slot is allowed; a different slot can use a different content hash.

## Documentation And README Snapshot

Added `docs/data_foundation/RAW_DATA_LAKE.md` describing the raw object fields,
local-only content-addressed layout, no-overwrite guard, request/chunk linkage,
repo placeholder boundary, and the fact that raw objects are not canonical truth.

Updated `README.md` with the DATA-P09 snapshot: current campaign progress through
DATA-P09, next phase DATA-P10, the new raw record/layout helpers/doc, and the
unchanged safety boundaries.

## Validation Results

No required checks were skipped.

| Command | Result |
| --- | --- |
| `test ! -f runs/2026-06-03T215249Z_ALPHA_DATA_FOUNDATION_V1/STOP && python -m pytest tests/unit/data/test_raw_data_lake.py -q` | Passed before formatting: `15 passed in 0.04s`. Passed again after formatting: `15 passed in 0.04s`. |
| `test ! -f runs/2026-06-03T215249Z_ALPHA_DATA_FOUNDATION_V1/STOP && python -m pytest tests/unit/data -q` | Passed before formatting: `195 passed in 0.14s`. Passed again after formatting: `195 passed in 0.14s`. |
| `test ! -f runs/2026-06-03T215249Z_ALPHA_DATA_FOUNDATION_V1/STOP && python tools/verify.py --smoke` | Passed with no output before and after formatting. |
| `test ! -f runs/2026-06-03T215249Z_ALPHA_DATA_FOUNDATION_V1/STOP && python tools/hooks/canary_runner.py` | Passed before and after formatting; output ended with `All Frontier canaries passed.` |
| `test -f docs/data_foundation/RAW_DATA_LAKE.md` | Passed with no output. |
| `test -f README.md` | Passed with no output. |
| `find data -type f '!' -name README.md '!' -name .gitkeep -print` | Passed with empty output; only allowed placeholders remain in the repo `data` tree. |
| `git status --short` | Passed before handoff/staging; showed only DATA-P09 commit-eligible README/source/doc/test changes. |
| `git ls-files runs` | Passed with empty output. |
| `find metadata -type f '!' -name README.md '!' -name .gitkeep -print` | Passed with empty output. |
| `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print` | Passed with empty output. |
| `git diff --check` | Passed with no output. |
| `git add README.md src/alpha_system/data/foundation/__init__.py src/alpha_system/data/foundation/bars.py docs/data_foundation/RAW_DATA_LAKE.md tests/unit/data/test_raw_data_lake.py handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P09.md && git diff --cached --name-only` | Failed with exit 128: `fatal: Unable to create '/home/yuke_zhang/projects/alpha_system/.git/index.lock': Read-only file system`. Reason: this execution sandbox exposes `.git` as read-only, so Codex could not stage despite using explicit paths only. |
| `git diff --cached --name-only` | Passed after the failed staging attempt with empty output; no hidden staged files are present. |

Additional local style checks:

| Command | Result |
| --- | --- |
| `python -m ruff format --check src/alpha_system/data/foundation/bars.py src/alpha_system/data/foundation/__init__.py tests/unit/data/test_raw_data_lake.py` | Initially failed: `bars.py` and `test_raw_data_lake.py` would be reformatted. After targeted formatting, passed: `3 files already formatted`. |
| `python -m ruff check src/alpha_system/data/foundation/bars.py src/alpha_system/data/foundation/__init__.py tests/unit/data/test_raw_data_lake.py` | Initially failed with one `E501` in `test_raw_data_lake.py`. After targeted formatting, passed: `All checks passed!`. |
| `python -m ruff format src/alpha_system/data/foundation/bars.py src/alpha_system/data/foundation/__init__.py tests/unit/data/test_raw_data_lake.py` | Passed; `2 files reformatted, 1 file left unchanged`. |

## Find Data Audit

`find data -type f '!' -name README.md '!' -name .gitkeep -print` returned
empty output. No real raw bytes, canonical data, provider responses, or heavy
data artifacts were introduced under the repo `data` tree.

## Explicit Staged File Set

Explicit staging was attempted with explicit paths only, but the sandbox exposes
`.git` as read-only and rejected index writes. `git diff --cached --name-only`
therefore returns the exact staged file set below:

```text
```

No `runs/**` path is included. `git add .` and `git add -A` were not used. The
intended explicit staging command was:

```bash
git add README.md src/alpha_system/data/foundation/__init__.py src/alpha_system/data/foundation/bars.py docs/data_foundation/RAW_DATA_LAKE.md tests/unit/data/test_raw_data_lake.py handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P09.md
```

## Artifact Policy Confirmation

- `git ls-files runs` returned empty.
- No `runs/**` path is in the staged set; the staged set is empty because `.git`
  is read-only in this execution sandbox.
- No run-local handoff, review, verdict, checks, or repair artifact was staged.
- No raw data, canonical data, factor data, label data, cache data, provider
  response, account artifact, DB file, SQLite/WAL/journal file, log,
  Parquet/Arrow/Feather file, pickle, NumPy artifact, model artifact, secret,
  credential, or heavy artifact was produced or staged.
- No local-only generated artifact was added under `runs/**`.
- Explicit staging was attempted only with listed commit-eligible paths. The
  attempt was blocked by the read-only `.git` sandbox restriction.

## Scope Boundaries

No external IBKR call, provider pull, real-data pull, broker, order, account,
position, paper, live, real-time, production deployment, parser,
canonicalization, dataset versioning, quality report, coverage report, alpha
search, factor/label research, profitability claim, tradability claim, or
production-readiness claim was introduced.

Codex did not call Claude, run a reviewer, create `review.md`, create
`verdict.json`, create a PR, merge, or mark the phase PASS. Ralph owns
validation orchestration, review, verdict parsing, done-checks, PR, CI, merge
gate, and final phase outcome.
