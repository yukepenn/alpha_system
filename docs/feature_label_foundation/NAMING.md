# Feature/Label Naming Contract

FLF-P02 defines names and layout only. It does not define validation behavior,
contract behavior, computation, materialization, registry writes, or stored
feature/label values.

The Feature/Label layer consumes accepted DatasetVersions and existing
governance objects. It does not duplicate governance contracts.

## Feature Object Names

Later feature phases must use these object names exactly:

| Name | Naming role |
| ---- | ----------- |
| `FeatureRequest` | Governance request consumed by the feature layer. |
| `FeatureSpec` | Feature contract name. |
| `FeatureFamily` | Feature family contract name. |
| `FeatureInputSpec` | Feature input contract name. |
| `TransformSpec` | Transform contract name. |
| `WindowSpec` | Window contract name. |
| `NormalizationSpec` | Normalization contract name. |
| `FeatureSetSpec` | Feature-layer feature set contract name. |
| `FeatureMaterializationPlan` | Feature materialization plan name. |
| `FeatureValueRecord` | Feature value record name. |
| `FeatureVersion` | Feature version name. |
| `FeatureRegistryRecord` | Feature registry record name. |
| `FeatureStore` | Feature store name. |
| `FeatureLineageRecord` | Feature lineage record name. |
| `FeatureQualityReport` | Feature quality report name. |
| `FeatureCoverageReport` | Feature coverage report name. |
| `DuplicateExposureReport` | Duplicate exposure report name. |
| `EquivalentFeatureGroup` | Equivalent feature group name. |
| `FeatureDeprecationRecord` | Feature deprecation record name. |
| `BBOFeatureSpec` | BBO feature-family spec name. |
| `SpreadFeatureSpec` | Spread feature-family spec name. |
| `MicropriceFeatureSpec` | Microprice feature-family spec name. |
| `TopBookImbalanceFeatureSpec` | Top-book imbalance feature-family spec name. |
| `LiquidityQualityFeatureSpec` | Liquidity-quality feature-family spec name. |

## Label Object Names

Later label phases must use these object names exactly:

| Name | Naming role |
| ---- | ----------- |
| `LabelSpec` | Governance label spec consumed by the label layer. |
| `LabelFamily` | Label family contract name. |
| `LabelInputSpec` | Label input contract name. |
| `LabelHorizonSpec` | Label horizon contract name. |
| `LabelPathSpec` | Label path contract name. |
| `BarrierSpec` | Barrier label contract name. |
| `CostAdjustmentSpec` | Cost adjustment contract name. |
| `LabelMaterializationPlan` | Label materialization plan name. |
| `LabelValueRecord` | Label value record name. |
| `LabelVersion` | Label version name. |
| `LabelRegistryRecord` | Label registry record name. |
| `LabelStore` | Label store name. |
| `LabelLineageRecord` | Label lineage record name. |
| `LabelQualityReport` | Label quality report name. |
| `LabelCoverageReport` | Label coverage report name. |
| `LabelLeakageAuditReport` | Label leakage audit report name. |
| `LabelAvailabilityPolicy` | Label availability policy name. |

## Governance ID Prefixes

These prefixes are governance-owned. Feature/Label code consumes them and must
not redefine their governance meaning.

| Prefix | Governance object |
| ------ | ----------------- |
| `freq_` | `FeatureRequest` |
| `lspec_` | `LabelSpec` |
| `aspec_` | `AlphaSpec` |
| `sspec_` | `StudySpec` |

## Local Version Names

`FeatureVersion` and `LabelVersion` are reserved for deterministic local-version
records. The exact version payloads and hash algorithms are defined later in
FLF-P06 and FLF-P16. FLF-P02 only reserves the names and the intent that equal
canonical inputs produce equal local version identifiers.

## Directory Layout

Feature family phases must keep implementation, tests, docs, and configs scoped
to the family name:

```text
src/alpha_system/features/families/<family>/**
tests/unit/features/families/<family>/**
docs/feature_label_foundation/features/<family>.md
configs/features/families/<family>/**
```

Label family phases must use the label-family analogue:

```text
src/alpha_system/labels/families/<family>/**
tests/unit/labels/families/<family>/**
docs/feature_label_foundation/labels/<family>.md
configs/labels/families/<family>/**
```

Family names use lowercase `snake_case`. Python modules use lowercase
`snake_case.py`. Object names use the PascalCase names listed above. Family docs
use one Markdown file per family, named `<family>.md`.

## Collision Rule

The feature-layer `FeatureSetSpec` must be namespaced under
`alpha_system.features`. It must not be imported from, re-exported through, or
treated as interchangeable with the existing non-governance
`FeatureSetSpec` in `src/alpha_system/experiments/feature_sets.py`.
