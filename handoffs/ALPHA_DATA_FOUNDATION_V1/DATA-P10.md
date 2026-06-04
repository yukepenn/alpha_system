# DATA-P10 Handoff - ES/NQ/RTY Main Batch Pull Plan

## Scope Completed

Implemented `SymbolBatchPlan` in
`src/alpha_system/data/foundation/batches.py` as a frozen, fail-closed record
with the required DATA-P10 fields:

- `plan_id`
- `mini_main`
- `micro_secondary`
- `max_concurrent_roots`
- `do_not_mix_mini_and_micro_batches`

Validation enforces exact ES/NQ/RTY mini roots, exact MES/MNQ/M2K micro roots,
disjoint mini/micro sets, `max_concurrent_roots = 3`, and
`do_not_mix_mini_and_micro_batches = true`. `validate_batch_roots(...)` and
`validate_manifest_roots(...)` reject any root set that mixes mini and micro
roots, which is the R-018 fail-closed guard. The planning record does not imply
pull authorization; `implies_pull_authorization` is always false.

Defined the ES/NQ/RTY mini main-batch pull plan in the same module:

- primary common panel: ES/NQ/RTY, `2018-01-01 -> present_as_of_run`, `1 min`,
  `TRADES`, ETH-capable canonical bars with derived RTH views;
- optional ES/NQ long QA panel: `2015-01-01 -> present_as_of_run`;
- optional RTY transition QA panel: `2017-07-10 -> 2017-12-31`;
- optional contract-truth diagnostic panel: rolling available expired window,
  with availability discovered, not assumed.

All panels reference the DATA-P07 `HistoricalRequestManifest` contract and the
DATA-P08 `RequestPacingPolicy` id
`rpp_ibkr_historical_conservative_tobeverified_v1`. Optional secondary panels
are explicitly labeled QA/diagnostic and have
`merge_into_primary_common_panel = false`.

Added `templates/data/synthetic_mini_batch_manifest.json`, a fake/sample
mini-only manifest that validates through the DATA-P07
`HistoricalRequestManifest` hash semantics. It includes only ES/NQ/RTY request
specs, uses synthetic planning metadata, and marks `synthetic`,
`sample_manifest`, `real_coverage_claim = false`, `authorization_claim = false`,
`pull_authorization = false`, and `data_exists_claim = false`.

Added `docs/data_foundation/MINI_BATCH_PLAN.md` and updated
`docs/data_foundation/README.md` plus the repository `README.md` snapshot for
DATA-P10. `MicroBatchPolicy` remains a DATA-P19 placeholder; no micro-batch
policy implementation was added.

## Validation

All requested local-only checks passed.

```text
git status --short
```

Result before staging: only DATA-P10 commit-eligible files were modified or
created.

```text
python -m pytest tests/unit/data/test_mini_batch_plan.py -q
```

Result: `6 passed in 0.03s`.

```text
python -m pytest tests/unit/data -q
```

Result: `201 passed in 0.14s`.

```text
python tools/verify.py --smoke
```

Result: passed with exit code 0 and no output.

```text
python tools/hooks/canary_runner.py
```

Result: all Frontier canaries passed.

```text
test -f docs/data_foundation/MINI_BATCH_PLAN.md
test -f README.md
```

Result: both files exist.

```text
git ls-files runs
```

Result: empty.

```text
find data -type f '!' -name README.md '!' -name .gitkeep -print
find metadata -type f '!' -name README.md '!' -name .gitkeep -print
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
```

Result: all four artifact audits returned empty output.

```text
git diff --check
```

Result: clean.

Skipped checks: none.

## Explicit Staging Set

Curated commit-eligible paths for explicit staging:

- `README.md`
- `docs/data_foundation/README.md`
- `docs/data_foundation/MINI_BATCH_PLAN.md`
- `src/alpha_system/data/foundation/batches.py`
- `templates/data/synthetic_mini_batch_manifest.json`
- `tests/unit/data/test_mini_batch_plan.py`
- `handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P10.md`

No `runs/**` path is included. No review artifact, `review.md`, or
`verdict.json` was created by the executor.

## Artifact And Scope Confirmation

No external provider call, IBKR connection, historical pull, raw write, broker
operation, order/account/paper/live/real-time behavior, production deployment,
PR creation, merge, reviewer call, or phase PASS marking was performed.

No parser, canonicalization, dataset-version, quality, coverage, session, roll,
provenance, alpha, profitability, tradability, or production-readiness claim was
introduced. No real data, provider response, account artifact, DB/SQLite/WAL,
log, cache, parquet/arrow/feather/npy/pickle, heavy artifact, secret, or
credential file was added.

The phase is ready for Ralph-owned handoff validation and independent Yellow
review.
