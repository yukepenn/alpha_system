# Data Validation CLI

ASV1-P08 introduces the `alpha data` command group for local, fixture-scale
data validation and bar building. The commands wrap the ASV1-P06 canonical bar
validation primitives and the ASV1-P07 calendar/session/quality helpers. They
do not add vendor ingestion, cloud storage, broker scope, live scope, factors,
labels, signals, strategies, or alpha/tradability claims.

## `alpha data validate`

Purpose: validate a local CSV canonical bar input against the 1-minute schema,
timestamp availability rules, duplicate-key checks, OHLC/spread sanity, version
presence, and optional calendar/session quality checks.

Inputs:

- `--config`: flat JSON/YAML config with `available_latency_seconds` and
  optional `calendar_config`;
- `--input`: local CSV input path;
- `--schema-id`: reported schema identifier, default
  `canonical_1min_bars_v1`;
- `--calendar-id`: optional expected calendar id when `calendar_config` is
  supplied;
- `--registry-path`: optional temp/local SQLite registry path outside the repo;
- `--summary-out`: optional local-only `.json`, `.md`, or `.csv` summary path;
- `--json`: machine-readable console summary.

Outputs:

- console validation summary;
- quality-flag counts;
- validation and quality issue counts;
- optional explicit summary file;
- optional dataset-version entry in a temp/local registry.

Exit codes:

- `0`: validation passed;
- `1`: validation or quality checks found issues;
- `2`: argument, config, fixture-policy, dependency, or artifact-policy error.

## `alpha data build-bars`

Purpose: convert an allowed tiny synthetic CSV fixture into canonical 1-minute
bars, assign sessions with the ASV1-P07 calendar layer, validate the result,
and write explicit local-only outputs.

Inputs:

- `--input`: allowed fixture under `tests/fixtures/data/`, unless explicitly
  configured otherwise;
- `--instrument-config`: flat JSON/YAML local instrument/build config;
- `--calendar-config`: JSON calendar config;
- `--output`: generated output path under a local-only `data/` directory;
- `--data-version`: data version stamped onto built rows;
- `--registry-path`: optional temp/local SQLite registry path outside the repo;
- `--validation-config`: optional flat validation config;
- `--json`: machine-readable console summary.

Outputs:

- local-only built bars at the requested output path;
- a small `*.manifest.json`;
- a small `*.validation_summary.json`;
- optional temp/local registry entry.

Parquet output uses the existing local Polars-backed writer when that optional
dependency is installed. For deterministic dependency-free fixture tests, the
command also accepts a `.csv` output path and writes canonical columns in
schema order. Both formats are generated artifacts and must not be committed.

## Artifact Restrictions

The data CLI must not write generated outputs under committed source, docs,
config, handoff, review, metadata, artifact, run, or fixture paths. `build-bars`
outputs must resolve under a local `data/` directory. Tests must use temporary
directories and leave repository `data/`, `metadata/`, and `artifacts/` clean
except for placeholder files.

Fixtures are correctness data only. They are never raw market data and never
evidence for alpha, profitability, robustness, tradability, or production
readiness.
