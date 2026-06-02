# Local Fixture Policy

`tests/fixtures/` may contain only tiny, deterministic, synthetic correctness
fixtures. Fixtures are not raw market data, are not market evidence, and must
not be used for alpha, profitability, robustness, or tradability claims.

## Allowed Data Fixtures

Data fixtures for this phase live under:

```text
tests/fixtures/data/
```

The data CLI fixture policy enforces:

- fixture files must resolve under `tests/fixtures/data/`;
- each fixture must be at or below `64 KiB`;
- text content must document that it is synthetic;
- text content must document deterministic correctness-only purpose;
- build inputs outside the fixture tree are refused unless an explicit local
  config sets `allow_non_fixture_input: true`;
- non-fixture generated outputs must not be written under committed source,
  test, docs, config, handoff, review, metadata, artifact, or run paths.

The existing `tests/fixtures/data/synthetic_1min_bars.csv` fixture is a
hand-authored correctness fixture for schema, validation, and CLI tests. Its
values are fabricated and are never evidence about any real venue, instrument,
or market behavior.

## Generated Outputs

Generated raw, canonical, registry, validation, manifest, Parquet, CSV, JSON,
log, cache, and report outputs are local-only. Tests must write generated files
to temporary directories. Developer runs may write under a local `data/`
directory, but those files remain non-commit-eligible artifacts.

Registry writes from the data CLI must target a temp/local SQLite path outside
the repository. Generated SQLite, DB journal, and WAL files must not be staged
or committed.
