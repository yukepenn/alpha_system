# FCFP-P14 Integration Report

- Campaign: `FEATURE_COMPUTE_FAST_PATH_V1`
- Phase: `FCFP-P14`
- Status: `EXECUTOR_COMPLETE`
- Generated at: `2026-06-09T06:20:00+00:00`
- Value policy: value-free summary only; no feature, label, price, Parquet,
  SQLite, or row-level values are included.

## Engine Routing

The scaleout driver now selects the V1 producer path by default:

```text
--engine v1
```

The reference engine remains selectable:

```text
--engine reference
```

Engine selection does not change governed identity. V1 feature materialization
uses the existing content-addressed `feature_version_id` values derived from the
governed `FeatureSpec`; V1 label materialization uses the existing
content-addressed `label_version_id` values derived from the governed
`LabelContractSpec`.

## Bounded-Real Slice

The representative smoke used a local-only isolated data root under
`ALPHA_DATA_ROOT` to avoid mutating the shared feature/label registries while
still reading the real accepted canonical inputs and the official DatasetVersion
registry.

| Family | Input | Symbol | Year | Feature locks | Label locks | Feature result | Label result |
| --- | --- | --- | ---: | ---: | ---: | --- | --- |
| `base_ohlcv` | OHLCV accepted DatasetVersion | `ES` | 2024 | 1 | 1 | completed | completed |
| `bbo_tradability_top_book` | BBO accepted DatasetVersion | `ES` | 2024 | 1 | 1 | completed | completed |

Additional diagnostic materialization was run for the dense-grid
`session_calendar_maintenance` `day_of_week` feature and matching OHLCV label.
It was not part of the final resolver pass set because the current runtime
resolver blocks `session_label`-named feature inputs without explicit
field-role metadata; the resolver was not weakened in this phase.

## Resolver Smoke

Official runtime resolution was run through `evaluate_runtime_entry_request`
and `resolve_runtime_input_pack` with the official `FeatureStore`,
`LabelRegistry`, and DatasetVersion resolver.

| Check | Count | Result |
| --- | ---: | --- |
| Required positive feature/label lock pairs | 2 | resolved |
| Positive resolver gaps | 0 | none |
| Stale feature lock controls | 1 | fail-closed |
| Stale label lock controls | 1 | fail-closed |
| Fuzzy label-name controls | 1 | fail-closed |

Negative controls failed closed with exact-id resolver reasons:
`feature_pack_not_found`, `label_pack_not_found`, and
`invalid_label_pack_ref`. No fuzzy-name fallback or substitution was observed.

## Idempotency

The representative V1 feature units were rerun against the same local-only
smoke registry after successful materialization. Both reruns skipped completed
units through checkpoint plus registry truth:

| Family | Rerun completed | Rerun skipped | Rerun failed |
| --- | ---: | ---: | ---: |
| `base_ohlcv` | 0 | 1 | 0 |
| `bbo_tradability_top_book` | 0 | 1 | 0 |

The engine-aware registry-resume guard requires the resolved registry record to
match the selected producer engine. Existing reference-produced records for the
same governed identity are not accepted as V1 completion evidence.

## Registry And Identity

Feature writes went through `PackMaterializer.register_pack` and
`FeatureStore`. Label writes went through `FastLabelMaterializer.register_pack`
and `LabelRegistry`. No manual SQLite writes were performed.

Feature records carry V1 producer provenance:

```text
alpha_system.features.fast.pack_materializer.v1
alpha_system.features.fast.values.v1
```

Label records carry V1 producer provenance through label registry metadata and
lineage:

```text
alpha_system.labels.fast.pack_materializer.v1
alpha_system.labels.fast.values.v1
```

Serial registry writes remain enforced by the V1 materializers' registry write
locks and the official keystone registration paths.

