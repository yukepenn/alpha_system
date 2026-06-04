# DATA-P11 Handoff - Continuous Futures vs Dated Futures Provenance

## Scope Completed

Implemented DATA-P11 provenance records in
`src/alpha_system/data/foundation/series.py`.

`ContinuousFuturesSeriesRecord` is now a frozen, fail-closed record with the
campaign-required fields:

- `series_id`
- `root_symbol`
- `provider`
- `provenance_label`
- `orderable`
- `dated_truth`
- `roll_adjustment_note`
- `source_retrieved_at`

Validation requires `provenance_label = provider_continuous`, the full
mandatory label set `provider_continuous` / `non_orderable` /
`not_dated_contract_truth` / `research_diagnostics_only`, `orderable = false`,
`dated_truth = false`, a recognized futures root from the DATA-P05 instrument
master, and a non-empty roll-adjustment note that states the provider or
diagnostic nature plus the negative boundary. The record exposes only
conservative disclaimer properties such as `implies_dated_contract_truth =
False`, `implies_orderability = False`, and `implies_tradability = False`.

`DatedFuturesSeriesRecord` is now a frozen, fail-closed record with the
campaign-required fields:

- `series_id`
- `root_symbol`
- `contract_universe`
- `roll_policy_id`
- `adjustment_method`
- `availability_window`
- `validation_status`

Validation requires a non-empty `contract_universe` of DATA-P06
`FuturesContractRecord` records or mappings, root consistency across the series
and contracts, a non-empty `roll_policy_id`, a closed-set adjustment method
(`unadjusted`, `back_adjusted`, `ratio_adjusted`), a closed-set validation
status (`unvalidated`, `discovered`, `reconciled`), and an availability window
with `availability_source = discovered_not_assumed`.

## Provenance Separation

The module defines canonical provenance constants for `provider_continuous`,
`dated_contract`, `canonical_stitched`, `roll_adjusted`, and `unadjusted`.

`require_dated_contract_truth()` refuses to accept a
`ContinuousFuturesSeriesRecord` as dated-contract truth. The
`reject_mixed_series_provenance_labels()` guard rejects continuous-only labels
on dated/stiched/adjusted/unadjusted series kinds, and
`DatedFuturesSeriesRecord.from_mapping()` rejects supplied continuous labels.

Continuous records cannot be orderable, tradable, or dated truth. Dated records
do not imply full historical availability, best-execution roll, or tradability.

## Availability And Adjustment Rules

Dated availability is logged, not assumed. `availability_window` must carry
`start`, `end`, and `availability_source = discovered_not_assumed`. Full-history
markers such as `full_history`, `assumed_full_history`, and
`full_historical_availability` are rejected even when supplied as false
metadata.

Adjusted-vs-unadjusted state is explicit through the closed-set
`adjustment_method`. `unadjusted` reports as unadjusted; `back_adjusted` and
`ratio_adjusted` report as adjusted. No roll policy, roll calendar, stitching,
or adjustment computation was implemented.

## Documentation And README Snapshot

Added `docs/data_foundation/PROVENANCE.md`, documenting the five provenance
kinds, continuous diagnostic labels and R-006 boundary, discovered-not-assumed
availability and R-007 boundary, explicit adjustment status, and the DATA-P11
records-only boundary.

Updated `docs/data_foundation/README.md` to index `PROVENANCE.md`.

Updated the repository `README.md` snapshot for DATA-P11: the snapshot records
the new series-provenance records and provenance doc, identifies DATA-P12
(`Session Templates and Trading Calendar`) as next, and restates the unchanged
safety boundaries including IBKR read-only historical scope, no
broker/order/account/paper/live scope, continuous futures never dated-contract
truth, real data local-only, and explicit staging only.

## Validation Results

No checks were skipped.

```text
git status --short
```

Result before handoff/staging:

```text
 M README.md
 M docs/data_foundation/README.md
 M src/alpha_system/data/foundation/series.py
?? docs/data_foundation/PROVENANCE.md
?? tests/unit/data/test_provenance.py
```

```text
python -m pytest tests/unit/data/test_provenance.py -q
```

Result:

```text
13 passed in 0.03s
```

```text
python tools/verify.py --smoke
```

Result: passed with exit code 0 and no output.

```text
python -m pytest tests/unit/data -q
```

Result:

```text
214 passed in 0.17s
```

```text
python tools/hooks/canary_runner.py
```

Result:

```text
PASS forbidden_git_add_dot
PASS policy_doc_mentions_forbidden_command
PASS forbidden_test_tamper
PASS forbidden_secret
PASS forbidden_large_binary
PASS forbidden_destructive_op
PASS forbidden_boundary_import
PASS forbidden_raw_data_commit
PASS forbidden_cache_data_commit
PASS forbidden_local_artifacts
PASS forbidden_scope_drift
PASS generated_scaffold_allowed
PASS governance_future_shift
PASS governance_permuted_labels
PASS governance_optimistic_fill
All Frontier canaries passed.
```

```text
test -f docs/data_foundation/PROVENANCE.md
test -f README.md
```

Result: both passed with exit code 0 and no output.

```text
git ls-files runs
```

Result: passed with empty output.

```text
find data -type f '!' -name README.md '!' -name .gitkeep -print
find metadata -type f '!' -name README.md '!' -name .gitkeep -print
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
```

Result: all four artifact audits passed with empty output.

```text
git diff --check
```

Result: passed with empty output.

## Explicit Staging Set

Curated commit-eligible paths for explicit staging:

```text
README.md
docs/data_foundation/PROVENANCE.md
docs/data_foundation/README.md
handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P11.md
src/alpha_system/data/foundation/series.py
tests/unit/data/test_provenance.py
```

No `runs/**` path is included. `git add .` and `git add -A` were not used. The
run-local handoff path
`runs/2026-06-03T215249Z_ALPHA_DATA_FOUNDATION_V1/phases/DATA-P11/handoff.md`
remains local-only and was not staged.

## Artifact And Scope Confirmation

- `git ls-files runs` returned empty.
- No `runs/**` path is in the curated staging set.
- No tests under existing paths were weakened, skipped, or stripped of
  assertions.
- No tiny synthetic fixture was needed for this phase.
- No real data, raw data, canonical data, factor data, label data, cache data,
  provider response, account artifact, SQLite/DB/WAL file, log, Parquet, Arrow,
  Feather, pickle, NumPy artifact, model artifact, secret, credential, or heavy
  artifact was created or staged.
- No external call, provider pull, IBKR connection, broker operation, order
  routing, account access, position access, paper trading, live trading,
  real-time behavior, production deployment, PR creation, merge, reviewer call,
  review artifact, `verdict.json`, or phase PASS marking was performed.
- No parser, canonicalization, session template, roll policy, roll calendar,
  stitching, roll computation, alpha, profitability, tradability, or
  production-readiness claim was introduced.

## Review Status

Codex did not call Claude, run a reviewer, create `review.md`, create
`verdict.json`, create a PR, merge, or mark the phase PASS. Ralph owns
handoff validation, independent Yellow review, verdict parsing, done-checks,
PR, CI, merge gate, and final phase outcome.
