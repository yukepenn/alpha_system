# FUTCORE-P20 BBO Tradability Diagnostics Reports

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`
Phase: `FUTCORE-P20`
Artifact type: value-free runtime diagnostics report index

The reports in this directory were produced through the Research Runtime tool surface from registry-resolved locked pack references. They contain scalar summaries, ids, hashes, statuses, and limitations only; no row-level market, feature, label, signal, provider, registry, or local Parquet payloads are embedded.

| StudySpec | AlphaSpec | Runtime outcome | BBO binding | Resolved horizons | Report |
| --- | --- | --- | --- | --- | --- |
| `sspec_9f6f741192a4b534f06e51c0` | `aspec_1284e49b083df11eeb0481ea` | `INCONCLUSIVE` | `MISSING_LOCKED_BBO_FEATUREPACK` | `5m`, `10m`, `30m` | [`sspec_9f6f741192a4b534f06e51c0/runtime_reports.json`](sspec_9f6f741192a4b534f06e51c0/runtime_reports.json) |

Family-level result: the approved BBO confirmation StudySpec reached runtime entry/input resolution, factor diagnostics, label diagnostics, cost diagnostics, and the signal-probe contract surface. Runtime resolution found the locked OHLCV/session FeaturePacks and `5m`/`10m`/`30m` LabelPacks, but no locked P15-G5 BBO FeaturePack. The diagnostics therefore keep BBO missingness and bad-quote buckets as explicit unresolved cells rather than inferring quotes, filling spread/depth, or substituting another feature.

The primary `15m` horizon remains unresolved for runtime diagnostics because no locked `15m` LabelPack is present in the input pack. The `1m` and `3m` horizons are recorded as diagnostic-only fragile views requiring stricter spread and liquidity gates.

Cost stress records the nonzero profiles `base`, `stress_1`, `stress_2`, and `double_cost` with BBO-unavailable fallback markers. `zero_cost` is diagnostic-only context and is not a promotion basis.

No promotion, ranking, watch state, candidate state, strategy validation, paper/live/broker action, PR, merge, review artifact, or verdict is recorded here.
