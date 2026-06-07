"""Feature materialization engine for approved feature sets.

The engine consumes accepted DatasetVersion handles, canonical in-memory row
mappings, and approved family definitions. It does not read provider files,
call external providers, register features, or write values inside the repo.
"""

from alpha_system.features.engine.dataset_version_dry_run import (
    DEFAULT_MAX_INPUT_ROWS,
    SMALL_DATASET_VERSION_DRY_RUN_PURPOSE,
    SMALL_DATASET_VERSION_DRY_RUN_STATUS,
    SMALL_DATASET_VERSION_DRY_RUN_WITH_WARNINGS,
    SmallDatasetVersionDryRunSummary,
    run_small_dataset_version_dry_run,
)
from alpha_system.features.engine.materialization import (
    FeatureMaterializationError,
    FeatureMaterializationInputs,
    FeatureMaterializationPlan,
    FeatureMaterializationResult,
    ValueStoreFormat,
    ValueStoreHandle,
    build_feature_materialization_plan,
    materialize_features,
    resolve_feature_materialization_dataset,
)

__all__ = [
    "DEFAULT_MAX_INPUT_ROWS",
    "FeatureMaterializationError",
    "FeatureMaterializationInputs",
    "FeatureMaterializationPlan",
    "FeatureMaterializationResult",
    "ValueStoreFormat",
    "ValueStoreHandle",
    "SMALL_DATASET_VERSION_DRY_RUN_PURPOSE",
    "SMALL_DATASET_VERSION_DRY_RUN_STATUS",
    "SMALL_DATASET_VERSION_DRY_RUN_WITH_WARNINGS",
    "SmallDatasetVersionDryRunSummary",
    "build_feature_materialization_plan",
    "materialize_features",
    "resolve_feature_materialization_dataset",
    "run_small_dataset_version_dry_run",
]
