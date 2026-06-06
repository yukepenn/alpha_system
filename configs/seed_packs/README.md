# Seed Pack Configs

Governed seed FeaturePack / LabelPack configurations consumed by the local-only
seed materialization operator:

```bash
alpha feature materialize --execute --seed-config configs/seed_packs/<file>.json \
  --alpha-data-root "$ALPHA_DATA_ROOT" ...
alpha label   materialize --execute --seed-config configs/seed_packs/<file>.json \
  --alpha-data-root "$ALPHA_DATA_ROOT" ...
```

These files are **governance metadata only** (feature/label selection, horizons,
window, dataset-version binding). They contain no market data and no feature or
label values. Materialized values (`values.jsonl`) and registries
(`features.sqlite`, `labels.sqlite`) are written under `ALPHA_DATA_ROOT` and are
never committed.

Storage policy: see [ADR-0006](../../decisions/0006-feature-label-value-storage.md).
The seed packs use the JSONL audit/small tier; research-scale Parquet is the
deferred `FEATURE_LABEL_PARQUET_SINK_V1` follow-up.

Each config selects only **distinct** family features (a `FeatureSetSpec`
requires unique feature ids) and trade-price fixed-horizon labels at 5–30m
(the primary research horizons; 1-minute is a sampling frequency, not the
primary alpha horizon). BBO tradability and cross-market families are out of
scope for the smoke seed and belong to a later primary core pack.

Session-context features (`rth_flag`, `eth_flag`, `session_minute`) are
**deferred** from the smoke seed: they read the canonical `session_label`
input field, and the Research Runtime leakage guard
`_reject_label_as_live_feature` (`runtime/input_resolver.py`) false-positives on
any field ending in `_label` — so `session_label` is wrongly treated as a
forward-label input and blocks runtime input resolution. `session_label` is a
point-in-time categorical (RTH/ETH), not a forward label, so this is a guard
over-match, not real leakage. A scoped follow-up should narrow the heuristic
(exclude known canonical fields such as `session_label`) with no-lookahead
tests; until then the seed stays on the six base-OHLCV features. See
`docs/STRUCTURAL_BACKLOG.md`.
