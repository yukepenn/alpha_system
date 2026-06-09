# Targeted Scaleout Materialization

`FCFP-P11` extends the local `alpha scaleout feature-pack` surface with
metadata-only targeting for incremental materialization planning and execution.
`FCFP-P14` keeps that targeting contract and routes execute mode to the V1
producer path by default.

## Targeting Flags

The feature-pack command accepts these selectors:

- `--engine {v1,reference}`
- `--family`
- `--feature-id`
- `--feature-group`
- `--label-id`
- `--label-group`
- `--symbols`
- `--years`
- `--dataset-version-ids`

Flags compose by intersection across dimensions. For example, selecting one
feature, two symbols, one year, and one DatasetVersion builds only matching
accepted units. With no targeting flag, the command keeps the existing
single-family config grid.

The current scaleout command surface is `feature-pack`. Label selectors are
accepted as part of the shared targeting contract, but the feature-pack surface
does not invent a label materialization path; label selectors therefore select
no feature units until a reviewed label scaleout surface exists.

The default engine is `v1`. Use `--engine reference` to run the reference
producer as the oracle/fallback for selected feature units. Engine selection
does not change feature or label identity.

## Dry-Run Estimate

Dry-run remains the default when `--execute` is absent. `--dry-run` makes that
mode explicit and cannot be combined with `--execute`.

The dry-run summary is value-free. It includes:

- selected unit count
- planned stage count
- selected symbols and years
- selected DatasetVersion ids
- estimated rows per unit from the config row budget
- estimated total rows
- estimated seconds per unit and total seconds

Dry-run does not write feature values, label values, registry records, Parquet
payloads, SQLite files, checkpoint markers, or completed manifests.

## Execute Contract

`--execute` runs only the selected units that were produced by the targeted grid
builder. It never expands a narrowed feature selection back to the whole family
or to other families. Narrowed feature selections use distinct checkpoint unit
identities from full-family units while preserving feature-version identity.

## Skip-Completed Contract

Completed units are skipped only when both conditions hold:

- the checkpoint completed manifest has a valid completed record for the unit
- the official `FeatureStore` read path resolves the recorded
  `feature_version_id` entries to existing value files produced by the selected
  engine

If the checkpoint exists but registry truth is missing, the unit is not silently
skipped. If the checkpoint is missing but the official registry already proves
all previewed feature versions are present, the driver records a checkpoint
marker and skips the unit.

The driver does not hand-read SQLite, does not use fuzzy matching, does not
mix reference and V1 completion evidence, and does not change feature or label
identity derivation.
