# Research Runtime Synthetic Fixtures

RT-P20 adds tiny synthetic runtime fixtures under `tests/fixtures/runtime/`.
They are hand-constructed metadata and scalar examples only. They are not real
market data, provider responses, runtime output values, alpha evidence, or
profitability/tradability evidence.

## Fixture Inventory

`tests/fixtures/runtime/fail_closed/invalid_shortcuts.json`

- Synthetic size target: less than 1 MB.
- Construction: hand-written JSON with invented governance ids, timestamps,
  scalar probe rows, invalid request shapes, invalid partition metadata, invalid
  cost profiles, invalid grid shapes, and artifact descriptors.
- Safety: contains no provider payloads, no raw/canonical/feature/label tables,
  no heavy format, and no real market observations.
- Purpose: drives RT-P20 fail-closed tests for missing `AlphaSpec` /
  `StudySpec`, inadmissible `DatasetVersion` lifecycle states, missing
  `available_ts`, missing `label_available_ts`, label-as-feature leakage,
  same-bar probe fills, unbounded grid and `VariantBudget` overage, locked-test
  metadata failures, missing `double_cost`, prohibited MVP states, and
  raw/heavy artifact descriptors.

`tests/fixtures/runtime/fail_closed/README.md`

- Synthetic size target: less than 1 MB.
- Construction: plain text fixture note.
- Safety: describes the fixture bundle and repeats that it is not market data
  or alpha evidence.
- Purpose: keeps the fixture directory self-describing for reviewers and future
  test authors.

The existing synthetic runtime fixtures remain in their earlier directories:

- `tests/fixtures/runtime/cost/`
- `tests/fixtures/runtime/probe/`
- `tests/fixtures/runtime/diagnostics/splits/`
- `tests/fixtures/runtime/diagnostics/cross_market/`

Those fixtures are also tiny synthetic test inputs. RT-P20 does not change their
meaning; it adds the fail-closed bundle for invalid shortcut cases.

## Fixture Rules

- Keep files small, textual, deterministic, and reviewable.
- Do not copy provider responses or real market data into runtime fixtures.
- Do not store raw, canonical, feature, label, or runtime value tables.
- Do not add parquet, Arrow, Feather, DBN, ZST, SQLite, DB, WAL, logs, caches,
  model weights, or generated report bundles.
- Do not describe any fixture as alpha evidence or as a tradability,
  profitability, strategy, portfolio, live, paper, or production result.
