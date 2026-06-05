# Session / Calendar / Roll Feature Family

`alpha_system.features.families.session` defines the FLF-P10 Session /
Calendar / Roll feature family. It is substrate code for research feature
definitions and in-memory fixture calculations only. It does not materialize
feature values, read raw provider files, call external providers, persist
registries, or make alpha, tradability, profitability, broker, paper, live, or
production claims.

## Inputs And Gates

The family consumes canonical OHLCV input views from
`alpha_system.features.input_views`. Rows are ordered by `available_ts`, and
every returned `FeatureValueRecord` carries the current input row's
`available_ts`.

Each feature definition must be built through
`build_session_feature_definition(...)` with an approved governance
`FeatureRequest`. The function consumes the FLF-P05 request gate and duplicate
exposure check. Missing, invalid, unapproved, duplicate-blocked, or
registry-unchecked requests fail closed before a `FeatureSpec` can become
implementation eligible.

Every definition is represented by an FLF-P06 `FeatureSpec` with
`FeatureInputSpec`, `TransformSpec`, `WindowSpec`, and `NormalizationSpec`, and
the deterministic `FeatureVersion` is derived from that contract. The family
also exposes `build_session_feature_set_spec(...)`, which returns an FLF-P06
`FeatureSetSpec` grouping for approved session-family definitions. Live
features use only causal, non-offline windows anchored on `available_ts`.

## Runtime Metadata

The required schedule and definition context is supplied as in-memory
`SessionCalendarMetadata` / `SessionCalendarEntry` objects or equivalent
mappings. This metadata is schedule or contract-definition context, not future
trade or quote observations. The feature code does not load provider files or
call a provider to obtain it.

When a required metadata field is absent, the family emits a `None` value with
an explicit quality flag, for example `rth_schedule_unavailable`,
`roll_metadata_unavailable`, `expiration_metadata_unavailable`,
`status_unavailable`, or `halt_unavailable`. It does not fabricate roll,
expiration, status, or halt values.

## Feature Coverage

The FLF-P10 family covers:

- `session_id`;
- `minutes_from_rth_open` and `minutes_to_rth_close`;
- RTH and ETH segment flags;
- `day_of_week`;
- roll and expiration proximity in minutes;
- market status and halt flags where supplied by metadata.

`minutes_to_rth_close`, roll proximity, and expiration proximity are derived
from schedule or contract metadata. They do not scan later trade or quote rows
to discover the close, roll, or expiration.

## Dense-Grid And BBO Semantics

The family uses FLF-P04 trade-bar semantics when classifying OHLCV rows. Rows
carrying the canonical `no_trade` quality flag remain flagged in returned
records and are not treated as trade bars. The calculations are session and
calendar context features, so no price, volume, or quote value is forward-filled
or inferred from synthetic rows.

The family does not compute BBO-derived values. It does not fill, interpolate,
or carry forward missing or quarantined BBO rows.

## Causality

Feature rows are calculated in `available_ts` order. A feature value at time `t`
uses the current input row and deterministic schedule or contract-definition
metadata only. Centered and future windows are rejected for live Session /
Calendar / Roll definitions. The family does not expose offline-looking
variants.

## Configuration

`configs/features/families/session/README.md` is a placeholder for future
declarative feature-set selections. FLF-P10 does not add materialization config,
registry config, provider config, or execution behavior.
