# Canary: pooled_partition_factor_id_drift (multi-partition OOS fan-out)

Purpose: guard the cross-partition OOS pooling rail against a SILENT degeneracy
to a single partition caused by a `factor_id` <-> `feature_id` naming drift.

## The defect

An idea declares a feature `factor_id` (e.g. `regime_range_contraction_state`),
but the registry's canonical `feature_id` for that materialized pack differs
(e.g. `liquidity_structure_range_contraction`).

- On the AUTHORED partition this was harmless: the runtime input resolver
  (`runtime/input_resolver.py::resolve_feature_packs`) resolves features BY
  `pack_ref` (the `fver_...` content-hash version id), not by name.
- But `research_lane/partition_resolver.py` fanned the OOS lookup out by the
  idea's declared `factor_id` against a registry index keyed on the canonical
  `record.feature_spec.feature_id`. A lookup by the drifted `factor_id` for ANY
  partition found 0 candidates, raised
  `PartitionResolutionError("feature_not_materialized_for_partition")`, and the
  mining driver recorded that partition as a `DATA_GAP`.
- Net: every "cross-year / cross-instrument pooled OOS" run silently degenerated
  to `coverage <= 1` (a one-partition "pool") even though ES/NQ/RTY x 2019-2026
  were materialized. The pooled verdict was VACUOUS but looked honest.

Four real `regime_*` conditional-setup ideas exhibited the live drift
(`regime_range_contraction_state`, `regime_atr_volatility_state`,
`regime_rolling_range_state`, `regime_trendiness_state`).

## The fix

`partition_resolver.py::_RegistryIndex` now also maps each `feature_version_id`
to the registry's canonical `(feature_id, feature_set_id)` identity. The resolver
recovers that identity ONCE from the AUTHORED partition's declared `pack_ref`
(a unique content-hash), then fans the target-partition lookup out by that
identity. `feature_set_id` is part of the identity because a single canonical
`feature_id` can be materialized by MULTIPLE feature sets at one partition (the
pair is unique per partition), so the lookup never resolves a wrong pack. Labels
get the analogous `label_version_id -> canonical label_id` mapping. When a
declared `pack_ref` is absent/unknown the resolver falls back to the declared
id, preserving prior behaviour for packref-less ideas.

## What the canary asserts

Runner: `src/alpha_system/governance/canaries/pooled_partition_factor_id_drift.py`,
registered in `tools/hooks/canary_runner.py`. It loads the bundled drifted idea
fixture (`drifted_idea_fixture.json`, a copy of a real regime idea whose declared
`factor_id` differs from its canonical `feature_id`) and builds synthetic,
value-free fake registries across ES/NQ/RTY x 2019/2020/2021. A second feature
set deliberately shares each canonical `feature_id` so the lookup is genuinely
ambiguous unless `feature_set_id` pins it.

1. **No silent single-partition degeneracy.** The drifted idea fanned over the
   9 partitions yields `PooledRunResult.coverage.present_count >= 2` AND
   `is_multi_partition_oos == True` (it resolves all 9). On the pre-fix resolver
   this collapses to `coverage == 1` -- the regression signature this canary
   turns into a caught failure.

2. **No wrong-pack resolution.** Re-resolving the AUTHORED partition recovers
   EXACTLY its declared `pack_ref`s (identity preserved); a cross-instrument
   partition resolves DISJOINT `pack_ref`s + its own dataset version and the
   PRIMARY feature set's pack, never the decoy set sharing the `feature_id`.

3. **Real gaps STILL fail closed.** When the primary context feature is dropped
   for one partition, resolution raises
   `feature_not_materialized_for_partition` and the driver records that partition
   as MISSING -- the degeneracy is not "fixed" by masking real gaps.

The fixture and the synthetic registries carry NO real market data, factor
values, labels, or scores. A passing canary validates the partition-resolution
identity contract only and implies NO alpha, profitability, or tradability
claim. The verdict is a deterministic RECORD; the machine never auto-promotes.
