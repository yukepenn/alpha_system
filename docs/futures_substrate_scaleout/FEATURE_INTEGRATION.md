# FeaturePack Integration

`FUTSUB-P14` integrates the eight governed futures FeaturePack families on the
V1 fast producer substrate. This document is value-free: it records the registry,
coverage, and resolver contract only, and does not embed feature values, Parquet
payloads, SQLite contents, provider responses, or local run artifacts.

## Integrated Families

The integrated FeaturePack families are:

- `base_ohlcv`
- `session_calendar_maintenance`
- `vwap_session_auction`
- `regime_volatility_compression`
- `liquidity_sweep_pa_structure`
- `volume_activity`
- `bbo_tradability_top_book`
- `cross_market_alignment`

Materialization uses the scaleout feature-pack CLI with the V1 fast producer
engine, serial registry writes, and worker-parallel value computation:

```bash
PYTHONPATH=src python -m alpha_system.cli scaleout feature-pack \
  --config configs/features/scaleout/<family>.json \
  --execute \
  --rollout full-window \
  --engine v1 \
  --workers 4 \
  --alpha-data-root "$ALPHA_DATA_ROOT" \
  --dataset-registry "$ALPHA_DATA_ROOT/registry/datasets.sqlite"
```

The bounded-real 2024 rollout was validated before full-window expansion. The
accepted full window excludes blocked 2018 DatasetVersions and includes only
`ACCEPTED` or `ACCEPTED_WITH_WARNINGS` locks. Cross-market units remain one
ES/NQ/RTY aligned panel per accepted year.

## Registry Contract

Registry writes flow through `FeatureStore.register_materialized_feature`; there
are no hand-written registry rows. The feature registry is the bridge between
dry-run identity, executed materialization, StudySpec feature locks, and runtime
resolver handles.

Required registry invariants:

- `feature_version_id` is derived from the governed `FeatureSpec` identity.
- `dataset_version_id`, partition id, FeatureRequest id, content hash, and
  `available_ts` are preserved from materialization to resolver handle.
- `producer_engine_id` records V1 fast producer provenance and does not enter
  feature identity.
- Every research-scale value store is Parquet-backed with a matching sidecar
  content hash.
- JSONL remains audit/checkpoint tier only.

The value-free audit evidence is
`research/futures_substrate_scaleout_v1/feature_packs/registry_consistency_audit.md`.

## Resolver Contract

Runtime feature locks resolve by exact `fver_...` id through
`FeatureLabelPackResolver.resolve_feature_packs`. Resolver smoke covers one
representative lock from each integrated family and verifies:

- exact feature-lock resolution with no fuzzy-name fallback,
- expected DatasetVersion, FeatureRequest id, and partition match,
- current Parquet sidecar hash for the registry row,
- fail-closed behavior for an absent exact lock.

The value-free resolver-smoke evidence is
`research/futures_substrate_scaleout_v1/feature_packs/feature_resolver_smoke.md`,
and the hermetic unit gate is
`tests/unit/futures_substrate_scaleout/features/test_feature_resolver_smoke.py`.

`session_label` is accepted by the resolver only as session metadata declared by
explicit `field_roles` or by a generic
`session_metadata_role: SESSION_METADATA_POINT_IN_TIME` marker that is converted
into ordinary `SESSION_METADATA` field roles. Future or label-target fields
remain fail-closed as live feature inputs.

## Boundaries

This integration is substrate engineering only. It does not add alpha ideas,
StudySpec reruns, diagnostics, promotions, broker/live/paper behavior, order
routing, production deployment, profitability claims, tradability claims, or
capital-allocation behavior.

BBO outputs are a time-sampled and forward-filled tradability proxy only; they
do not make execution-truth, passive-fill, queue-position, or impact claims.
Cross-market outputs preserve per-instrument availability semantics and do not
forward-fill one instrument across another instrument's missing timestamp.
