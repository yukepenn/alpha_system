# Repo Integrity Sweep V1 - Precondition vs DATA_GAP Fix

## Contract

`DATA_GAP` must mean a real substrate/value absence. It must not mean wrong
Python, missing dependency, unresolved data root, unavailable registry, stale
pack lifecycle, or DatasetVersion mismatch.

## Implemented Behavior

| Cause | Public classification |
| --- | --- |
| Missing `polars` / wrong interpreter | `MISSING_DEPENDENCY` or `ENVIRONMENT_NOT_CONFIGURED` preflight result |
| Missing/unresolvable data root | `ALPHA_DATA_ROOT_MISSING` or `ENVIRONMENT_NOT_CONFIGURED` preflight result |
| Feature/label registry unavailable | `REGISTRY_UNAVAILABLE` / `ENVIRONMENT_NOT_CONFIGURED` depending typed resolver reason |
| Deprecated fver/lver pin | `DEPRECATED_PACK_PIN` |
| Feature/label DatasetVersion mismatch | `DATASET_VERSION_MISMATCH` |
| Registered pack exists but parquet value file missing | `VALUE_FILE_MISSING` |
| Pack/reference genuinely absent from registry | `TRUE_DATA_GAP` |
| Research effect fails after valid inputs | not `DATA_GAP`; remains research verdict/null path |

## Code Paths Changed

- `alpha idea validate` now audits versioned pack refs through the registry after
  environment preflight, without loading parquet values.
- `fast_probe` now emits an unresolved readout with a cause-specific `issue_code`
  at both top level and `row_access.issue_code`.
- `testability_gate` now maps resolver precondition/registry errors away from
  `DATA_GAP`, maps deprecated/mismatched pack pins to `FAIL`, and prevents `FAIL`
  from being masked by later `DATA_GAP` checks.

## Guard Coverage

- `tests/unit/cli/test_idea_cli.py`
- `tests/unit/research_lane/test_environment_preflight.py`
- `tests/unit/research_lane/test_fast_probe.py`
- `tests/unit/research_lane/test_testability_gate.py`
- `src/alpha_system/governance/canaries/precondition_not_datagap.py`
- `src/alpha_system/governance/canaries/pack_pin_validate_not_datagap.py`

## Residual Boundary

Some older data tools still have their own CLI-specific preflight behavior. This
sweep hardened the idea validate/gate/run and fast-probe paths that were causing
research misclassification. Future work should migrate remaining data-touching
commands to the same public classification vocabulary before expanding compute.
