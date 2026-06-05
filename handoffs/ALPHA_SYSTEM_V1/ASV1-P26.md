# ASV1-P26 Handoff — L2-Derived Feature Pipeline Skeleton

## Scope Completed

Implemented a design-only, fixture-only L2-derived feature skeleton that consumes
the ASV1-P25 L2 snapshot/delta timestamp and validation contracts. The new
surface is limited to declarative draft feature specs, tiny synthetic fixtures,
deterministic in-memory transforms, validation guards, docs, config examples,
and targeted tests.

No replay engine, order-book reconstruction, queue-position model, passive-fill
simulation, latency model, real L2 ingestion, live feed, broker, paper-trading,
order-routing, persistence, registry migration, factor-store materialization, or
strategy/execution validation scope was introduced.

## Feature Skeleton Summary

New modules:

- `src/alpha_system/l2/feature_specs.py` declares draft L2 feature specs.
- `src/alpha_system/l2/features.py` computes synthetic fixture-only feature
  values in memory.
- `src/alpha_system/l2/fixtures.py` provides tiny deterministic synthetic L2
  snapshot and delta rows.
- `src/alpha_system/l2/quality.py` defines feature-level quality flag helpers.
- `src/alpha_system/l2/feature_validation.py` enforces synthetic-only input
  scope, no label leakage, availability checks, declaration validation, and
  no materialization by default.

The skeleton covers top-of-book spread, top-1/top-5 imbalance, depth by side,
order count by level, microprice, quote update intensity, liquidity regime tags,
and future order-flow placeholders.

## FactorSpec And Factor Value Compatibility

Every L2 feature declaration wraps an existing `FactorSpec` with:

- `domain="l2"` input fields;
- `status="draft"`;
- `validation_artifact_path=null`;
- `availability_lag=0`;
- `fixture_only=true`;
- `materialize_by_default=false`.

The in-memory transforms emit rows using the existing `FactorValue` schema order:

```text
factor_id, factor_version, instrument_id, event_ts, available_ts, session_id,
bar_index, value, normalized_value, quality_flags, data_version, compute_version
```

These specs are not registered, promoted, approved, validated for alpha use, or
materialized into a factor store.

## Synthetic Fixture Behavior

The fixture data version prefix is `l2:synthetic:`. Feature transforms reject
non-synthetic data versions. The fixture rows are tiny in-code mappings with
ASV1-P25 fields and are correctness fixtures only, not market evidence.

Implemented deterministic fixture transforms:

- spread: `ask_price_level_1 - bid_price_level_1`;
- imbalance: `(bid_size - ask_size) / displayed_size_total`;
- depth by side: displayed-size sum through the requested depth;
- order count: displayed order count for one side/level;
- microprice: `(ask_price * bid_size + bid_price * ask_size) / total_size`;
- event rate: visible quote-update count per second ordered by `available_ts`;
- liquidity regime tag: conservative categorical fixture tag.

## Timing And No-Lookahead

Derived feature `available_ts` is the latest `available_ts` among the L2 input
rows actually used by the derived value. Event-rate features sort with the
ASV1-P25 research order key, which starts with `available_ts`. Tests assert that
feature values cannot be read before `available_ts` and that event-rate values do
not count future-available deltas.

Labels and `label_available_ts` values are rejected as L2 feature inputs.

## Quality And Missing-Level Behavior

Input `quality_flags` propagate to derived feature values. Additional flags mark
fixture-only scope, missing sides, missing book levels, missing order counts,
zero denominators, and incomplete top of book.

Missing top-of-book sides produce null spread/microprice values with quality
flags. Missing inner depth levels are not fabricated; available displayed depth
can be used for fixture calculations while the output carries a missing-level
quality flag.

## Materialization Policy

L2 feature materialization is disabled by default. Materialization requests fail
closed through `L2FeatureMaterializationError`. No CLI, persistence layer,
factor-store output, Parquet/Arrow/Feather, DB/SQLite file, generated L2 data, or
heavy artifact was added.

## Files Changed And Explicit Staged Set

Commit-eligible paths changed and intended for explicit staging:

- `README.md`
- `configs/factors/microstructure/l2_feature_examples.yaml`
- `docs/L2_DERIVED_FEATURES.md`
- `docs/L2_FEATURE_SCOPE_POLICY.md`
- `handoffs/ASV1-P26.md`
- `src/alpha_system/l2/feature_specs.py`
- `src/alpha_system/l2/feature_validation.py`
- `src/alpha_system/l2/features.py`
- `src/alpha_system/l2/fixtures.py`
- `src/alpha_system/l2/quality.py`
- `tests/no_lookahead/test_l2_feature_available_ts.py`
- `tests/no_lookahead/test_l2_feature_no_label_leakage.py`
- `tests/unit/test_l2_depth_imbalance.py`
- `tests/unit/test_l2_event_rate_feature_contract.py`
- `tests/unit/test_l2_feature_artifact_policy.py`
- `tests/unit/test_l2_feature_design_only_scope.py`
- `tests/unit/test_l2_feature_no_materialization_by_default.py`
- `tests/unit/test_l2_feature_spec_schema.py`
- `tests/unit/test_l2_microprice.py`
- `tests/unit/test_l2_missing_level_handling.py`
- `tests/unit/test_l2_quality_flag_propagation.py`
- `tests/unit/test_l2_top1_imbalance.py`
- `tests/unit/test_l2_top5_imbalance.py`
- `tests/unit/test_l2_top_of_book_spread.py`

No `runs/**` path is included. No run-local `handoff.md`, `review.md`,
`verdict.json`, or repair artifact was created by Codex.

## Validation

Passed:

- `python -m pytest tests/unit tests/no_lookahead` — 548 passed.
- `python -m pytest tests/unit/test_l2_feature_spec_schema.py tests/unit/test_l2_top_of_book_spread.py tests/unit/test_l2_depth_imbalance.py tests/no_lookahead/test_l2_feature_available_ts.py` — 8 passed.
- `python -m compileall src` — passed.
- `git status --short` — listed only commit-eligible ASV1-P26 source/docs/config/test/handoff paths.
- `find data -path "*l2*" -type f -print || true` — no output.
- `find data/factors -type f ! -name README.md ! -name ".gitkeep" -print` — no output.
- `find artifacts -type f ! -name README.md ! -name ".gitkeep" -print 2>/dev/null || true` — no output.
- `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` — no output.
- `find . -path ./tests/fixtures -prune -o -type f \( -name "*.parquet" -o -name "*.arrow" -o -name "*.feather" \) -print` — no output.
- `find . -type f \( -name "*.sqlite" -o -name "*.sqlite3" -o -name "*.db" -o -name "*.db-journal" -o -name "*.wal" \) -print` — no output.
- `git ls-files runs` — no output.

Unavailable optional checks:

- `python -m ruff check src tests` — unavailable: `/usr/bin/python: No module named ruff`.
- `python -m mypy src` — unavailable: `/usr/bin/python: No module named mypy`.

## Artifact Policy Confirmation

Allowed commit-eligible paths are separated from local-only `runs/**` artifacts.
No real L2 data, order-book data, generated L2 feature store, materialized factor
values, replay output, SQLite/DB file, Parquet, Arrow, Feather, log, cache, or
heavy artifact was produced, staged, or committed by Codex.

`git ls-files runs` returned no output. No `runs/**` path is in the intended
staged set.

## README Snapshot

`README.md` was updated with the concise post-phase snapshot requested by the
spec: ASV1-P26 L2 feature skeleton, L2 readiness gate ASV1-P25 to ASV1-P26 in
design/fixture-only scope, next phase ASV1-P27, newly added L2 feature modules,
docs, config example, and unchanged safety boundaries.

## Design-Only Limitations And Deferred Work

Known limitations:

- No production L2 processing.
- No real data loader or canonical L2 dataset.
- No L2 replay or book reconstruction.
- No queue, passive-fill, or latency model.
- No factor-store materialization or registry migration.
- No executable L2 strategy validation.
- Fixture `bar_index` is a synthetic output ordinal until a future reviewed
  canonical alignment contract exists.

Deferred future work requires separate reviewed specs: source-specific L2
sequencing, replay assumptions, canonical alignment, validation evidence,
promotion criteria, and any persistence/materialization policy.

## Boundary Confirmations

- No replay/live/broker/paper/passive-fill/queue scope was introduced.
- No alpha, profitability, robustness, tradability, execution-completeness, or
  production-readiness claim was introduced.
- No real L2 data or L2 feature store was committed.
- No reviewer was called by Codex.
- No review artifact, verdict, PR, merge, or PASS marking was created by Codex.

## Review Focus

Reviewer should focus on FactorSpec compatibility, `available_ts` propagation,
event/receive/available timestamp semantics, label-input rejection, quality-flag
propagation, conservative missing-level behavior, no materialization by default,
artifact policy, absence of replay/queue/passive-fill/live/broker scope, README
factuality, and absence of alpha/tradability/execution claims.
