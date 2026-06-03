# Label Leakage Guard

`ARGOV-P06` adds a fail-closed guard for checking feature references against a
validated `LabelSpec`.

The guard reasons only over injected governance metadata: the `LabelSpec` and
feature-reference mappings supplied by the caller. It does not read real data,
materialize labels, compute feature values, run diagnostics, run a backtest,
register a factor, grant candidate status, or make trading decisions.

## Checks

`check_label_leakage(label_spec, feature_references)` returns a
`LabelLeakageResult` with:

- `findings`
- `features_checked`
- `clean`
- `blocked`

Findings are blocking and structured:

- `kind`: `LABEL_AS_FEATURE` or `LOOKAHEAD`
- `severity`: `BLOCKING`
- `offending_reference`
- `rationale`

`clean` is true only when there are no findings. Blocking findings cannot be
coerced into a clean result because the boolean status is derived from the
finding list.

## Label-As-Feature Overlap

The guard blocks a feature reference when it matches a label reference, alias,
or transform declared in `LabelSpec.forbidden_feature_overlap`.

This covers direct label-as-feature overlap and declared trivial transforms such
as a rank or z-score of the label reference. The declaration is conservative
metadata; it does not prove that any feature or label has predictive value.

## Availability-Time Look-Ahead

The guard blocks a feature when its `information_time` is at or after
`LabelSpec.availability_time`.

Feature metadata may use an accepted availability key such as
`information_time`, `feature_information_time`, `feature_availability_time`,
`availability_time`, `available_at`, or `as_of`. The value must be a
timezone-aware ISO-8601 timestamp. Equal timestamps are blocked because the
feature is not available strictly before the label availability time.

## Fail-Closed Default

Ambiguous or missing feature availability metadata produces a blocking
`LOOKAHEAD` finding. Non-iterable feature inputs and missing feature-reference
sets also block. The guard does not silently pass a feature set when it cannot
establish availability ordering from metadata.

## Canary Coverage

`ARGOV-P06` introduces `tests/no_lookahead/` with injected synthetic leakage
faults. Later `ARGOV-P14` can exercise these same guard behaviors in the canary
harness: a direct label feature, a declared transform, and a feature available
at or after the label time must all be caught, while a clean synthetic feature
set must remain clean.
