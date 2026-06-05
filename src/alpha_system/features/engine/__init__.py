"""Feature materialization engine for approved feature sets.

The engine consumes accepted DatasetVersion handles, canonical in-memory row
mappings, and approved family definitions. It does not read provider files,
call external providers, register features, or write values inside the repo.
"""

from alpha_system.features.engine.materialization import (
    FeatureMaterializationError,
    FeatureMaterializationInputs,
    FeatureMaterializationPlan,
    FeatureMaterializationResult,
    build_feature_materialization_plan,
    materialize_features,
    resolve_feature_materialization_dataset,
)

__all__ = [
    "FeatureMaterializationError",
    "FeatureMaterializationInputs",
    "FeatureMaterializationPlan",
    "FeatureMaterializationResult",
    "build_feature_materialization_plan",
    "materialize_features",
    "resolve_feature_materialization_dataset",
]
