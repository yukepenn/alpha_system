# Session / Calendar / Roll Feature Family

`alpha_system.features.families.session` defines the FLF-P10 Session /
Calendar / Roll feature family. It is substrate code for research feature
definitions and in-memory fixture calculations only. It does not materialize
feature values, read raw provider files, call external providers, persist
registries, or make alpha, tradability, profitability, broker, paper, live, or
production claims.

## Inputs And Gates

The family consumes canonical OHLCV input views from
`alpha_system.features.input_views`. Dense-grid rows may also be supplied as
canonical `DenseGridBarRecord` objects reconstructed by the accepted
DatasetVersion consumption boundary. Rows are validated and ordered by
`available_ts`, and every returned `FeatureValueRecord` carries the current
input row's `available_ts`.

Each feature definition must be built through
`build_session_feature_definition(...)` with an approved governance
`FeatureRequest`. The function consumes the FLF-P05 request gate and duplicate
exposure check. Missing, invalid, unapproved, duplicate-blocked, or
registry-unchecked requests fail closed before a `FeatureSpec` can become
implementation eligible.

Every definition is represented by an FLF-P06 `FeatureSpec` with
`FeatureInputSpec`, `TransformSpec`, `WindowSpec`, and `NormalizationSpec`, and
the deterministic `FeatureVersion` is derived from that contract. Live features
use only causal, non-offline windows anchored on `available_ts`.

## Feature Coverage

The FLF-P10 family covers:

- session id;
- minutes from the configured RTH open and minutes to the configured RTH close;
- RTH and ETH segment flags;
- day of week;
- bars and minutes to the next contract or series transition;
- minutes to expiration when expiration metadata is supplied;
- halt-status flag when status metadata is supplied.

The calculations return in-memory `FeatureValueRecord` tuples. Missing roll
transitions, missing expiration metadata, missing status metadata, and clock
values outside RTH are represented as `None` values with quality flags rather
than filled or fabricated.

## Metadata Absence

Expiration and status features are available only when canonical metadata is
present in the accepted DatasetVersion inputs or supplied metadata bundle. If a
contract has no expiration timestamp, `minutes_to_expiration` returns `None`
with `expiration_metadata_absent`. If a row has no status metadata,
`halt_status_flag` returns `None` with `status_metadata_absent`.

## Dense-Grid No-Trade Semantics

The family uses FLF-P04 trade-bar predicates. A synthetic dense-grid no-trade
row still has a well-defined session id, calendar position, and RTH/ETH segment.
Those records preserve their `no_trade` quality flag and add
`synthetic_no_trade_position_only`, so downstream consumers cannot treat them as
real trade bars.

No synthetic no-trade row is used as price movement, volume, liquidity, or
tradability evidence.

## Causality

Feature rows are calculated in `available_ts` order. A feature value at time `t`
uses the current row's availability timestamp and does not substitute
`event_ts` or `ingested_at`. Contract roll proximity is derived from contract
or series transitions in the accepted DatasetVersion as roll/calendar metadata,
not from future prices or labels. Centered and future windows are rejected for
live Session / Calendar / Roll definitions. The family does not expose
offline-looking variants.

## Configuration

`configs/features/families/session/README.md` is a placeholder for future
declarative feature-set selections. FLF-P10 does not add materialization config,
registry config, provider config, or execution behavior.
