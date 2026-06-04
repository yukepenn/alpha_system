# Roll Policy and Roll Calendar

DATA-P13 defines local-only roll policy and roll calendar records for derived
dated-contract futures series. The records are design and validation contracts
only. They do not stitch real bars, adjust real prices, pull provider data, or
describe execution quality.

## RollPolicy

`RollPolicy` records how a future derived or stitched dated-contract series is
selected.

Required fields:

```text
roll_policy_id
method
roll_trigger
adjustment_method
fallback_rule
uses_volume
uses_open_interest
source
```

Validation is fail-closed:

- `method` is a closed set:
  `calendar_days_before_expiration`, `volume_crossover`,
  `open_interest_crossover`, or `volume_open_interest_hybrid`.
- `roll_trigger` is explicit and must match the method:
  `calendar`, `volume`, `open_interest`, or
  `volume_open_interest_hybrid`.
- `uses_volume` and `uses_open_interest` must match the trigger. Calendar
  policies use neither field; volume, open-interest, and hybrid policies must
  set the corresponding booleans.
- `adjustment_method` is required and closed:
  `none`, `back_adjusted`, or `ratio_adjusted`.
- `fallback_rule` is required and closed:
  `no_roll_without_evidence`, `calendar_fallback_unvalidated`, or
  `manual_review_required`.
- `source` must be a `dsrc_` provenance identifier and must not claim
  exchange/CME finality unless reconciled.

## Adjusted vs Unadjusted

`adjustment_method = none` represents the unadjusted state. Adjusted states are
represented only by explicit `back_adjusted` or `ratio_adjusted` values.

There is no implicit adjustment default. A missing or ambiguous adjustment
method is a validation error. `RollPolicy.adjusted_vs_unadjusted` returns
`unadjusted` only for `none`; otherwise it returns `adjusted`.

## RollCalendarRecord

`RollCalendarRecord` records one specific roll-date transition between two
dated `FuturesContractRecord` identities.

Required fields:

```text
roll_calendar_id
root_symbol
from_contract
to_contract
roll_date
method
evidence
validation_status
```

Validation is fail-closed:

- `root_symbol` must be one of `ES`, `NQ`, `RTY`, `MES`, `MNQ`, or `M2K` and
  must exist in the futures instrument master.
- `from_contract` and `to_contract` must validate as dated
  `FuturesContractRecord` objects or mappings.
- The two contracts must match `root_symbol`.
- The two contracts must be distinct by `contract_id`; discovered `con_id`
  values must also be distinct when both are present.
- `roll_date` must be an ISO date or `datetime.date`, not a datetime.
- `method` uses the same closed set as `RollPolicy.method`.
- `evidence` is a required non-empty mapping.
- `validation_status` is required and closed:
  `unvalidated`, `discovered`, or `reconciled`.

`RollCalendarRecord.validate_against_policy()` and
`require_roll_calendar_matches_policy()` fail closed unless the calendar method
matches a concrete `RollPolicy.method`.

## Evidence and Status

Roll calendar evidence must be recorded on every calendar entry. Empty evidence
is invalid, and missing `evidence`, `method`, or `validation_status` is a hard
error.

`validation_status = unvalidated` is the conservative starting state. A
`discovered` or `reconciled` value records only the status of the roll-date
metadata; it does not certify venue finality or execution quality.

## Continuous vs Derived Rolls

Provider-continuous history, including `CONTFUT` diagnostic series, remains
separate from derived or stitched dated-contract rolls.

`RollPolicy` and `RollCalendarRecord` describe derived dated-contract roll
metadata only. They reject provider-continuous and `CONTFUT` labels, and they
do not turn a provider-continuous series into dated-contract truth.

## Non-Claims

DATA-P13 does not define a tradable roll, best-execution roll, fill model,
slippage model, order timing rule, broker route, paper-trading behavior, live
trading behavior, alpha signal, profitability claim, or production-readiness
claim.

Roll discontinuities, quality checks, canonical bar construction, and dataset
versioning remain later-phase concerns.
