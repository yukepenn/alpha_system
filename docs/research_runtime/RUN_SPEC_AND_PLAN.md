# StudyRunSpec and RuntimePlan Contracts

`alpha_system.runtime.contracts` defines the RT-P04 pre-execution contracts for
bounded research runtime jobs. These contracts describe a requested job and a
validated plan only. They do not run diagnostics, signal probes, grids, cost
stress, audits, backtests, or any broker, paper, live, order, or account flow.

## Contract Surface

- `RuntimeRequest` in `alpha_system.runtime.contracts.run_spec`
- `RuntimePlan` and `validate_runtime_plan` in
  `alpha_system.runtime.contracts.plan`
- `StudyRunSpec` in `alpha_system.runtime.contracts.run_spec`

The objects are frozen dataclasses with deterministic content hashes and stable
JSON-compatible `to_dict()` payloads for reproducibility lineage. Their success
path is limited to:

```text
RUNTIME_REQUESTED -> INPUTS_RESOLVED -> PLAN_VALIDATED
```

Blocked or inconclusive validations reuse the existing
`RuntimeEntryReason` / `RuntimeEntryStatus` shape from the runtime entry
contract instead of adding a parallel rejection model.

## RuntimeRequest

`RuntimeRequest` binds a prospective job to already governed references:

- an approved `AlphaSpec` at `IMPLEMENTATION_ALLOWED`;
- an approved `StudySpec` at `DIAGNOSTICS_ALLOWED`;
- the governance `StudyInputPack` surface that ties those specs to feature,
  label, and dataset-scope handles;
- one target accepted `DatasetVersion` id;
- one value-free `RuntimeInputPack` produced by the RT-P03 resolver.

Construction fails closed when any required reference is missing, malformed, or
inconsistent. The request cross-checks that the `RuntimeInputPack` matches the
approved AlphaSpec, StudySpec, StudyInputPack, target DatasetVersion, accepted
DatasetVersion lifecycle, and dataset scope. It records handles and hashes only;
it does not resolve registries, open provider files, materialize feature or
label values, or imply any result.

## RuntimePlan

`RuntimePlan` validates bounded execution intent before any runtime work can
execute. A valid plan reaches `PLAN_VALIDATED`; invalid plans fail closed through
`RuntimePlanValidationResult` when using `validate_runtime_plan`.

The plan enforces these invariants:

- every plan must declare a bounded job;
- plan partition and session scope must match the resolved `RuntimeInputPack`;
- partition windows must match the campaign contract:
  - `development`: `2018-01-01..2022-12-31`;
  - `validation`: `2023-01-01..2024-12-31`;
  - `locked_test_candidate`: `2025-01-01..as_of_run`;
  - `latest_shadow_candidate`: `2025-01-01..as_of_run`;
- a signal-probe plan must declare a bounded variant-grid reference;
- a signal-probe plan must carry a finite
  `alpha_system.experiments.limits.CombinationLimit` budget reference;
- a signal-probe plan must include a `double_cost` cost-stress profile;
- `locked_test_candidate` and `latest_shadow_candidate` require substantive
  governance contamination metadata;
- locked-test selection semantics are refused.

RT-P04 only records that a finite experiment budget reference is present. Full
variant-budget accounting and bounded-grid enforcement remain scoped to later
runtime integration phases.

## StudyRunSpec

`StudyRunSpec` joins a `RuntimeRequest` with a matching `RuntimePlan` only after
the plan has reached `PLAN_VALIDATED`. It is still a pre-execution object: the
serialized payload carries `execution_outcome: null` and makes no alpha,
tradability, profitability, strategy, backtest, portfolio, or production
readiness claim.

## Boundary

These contracts consume existing governance, experiment-limit, and RT-P03
runtime-input surfaces. They do not duplicate or edit those primitive domains.
They do not add an `alpha runtime` CLI; that remains scoped to RT-P18. They also
do not access raw provider files, local data values, registry databases, feature
values, label values, heavy artifacts, external providers, or broker systems.
