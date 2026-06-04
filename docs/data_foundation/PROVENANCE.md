# Futures Series Provenance

DATA-P11 defines the provenance records that keep continuous futures and dated
futures structurally separate. These records validate labels and availability
metadata only. They do not fetch data, build bars, stitch contracts, compute
rolls, or authorize trading.

## Provenance Kinds

The data foundation keeps these futures-series kinds distinct:

- `provider_continuous`: provider-supplied continuous history, such as a
  `CONTFUT` diagnostic series.
- `dated_contract`: one or more logged `FUT` dated-contract records.
- `canonical_stitched`: a future canonical series assembled by explicit roll
  policy and roll calendar rules.
- `roll_adjusted`: a future adjusted series whose adjustment method is
  recorded explicitly.
- `unadjusted`: a dated or derived series whose prices are not adjusted.

DATA-P11 implements `ContinuousFuturesSeriesRecord` and
`DatedFuturesSeriesRecord`. It exposes constants and guards for the other
labels, but DATA-P13 owns roll policy, roll calendars, stitching decisions, and
roll adjustment computation.

## Continuous Is Diagnostic Only

A `ContinuousFuturesSeriesRecord` must carry this full label set:

```text
provider_continuous
non_orderable
not_dated_contract_truth
research_diagnostics_only
```

The record also requires `provenance_label = provider_continuous`,
`orderable = false`, and `dated_truth = false`. This is the R-006 guard:
provider-continuous history can be useful for diagnostics, but it is never a
dated `FUT` contract record and never evidence that IBKR returned dated-contract
history for that window.

The `roll_adjustment_note` must describe the provider or diagnostic nature of
the continuous adjustment and must state the negative boundary. A continuous
series cannot be converted into dated-contract truth through a helper or guard.

## Dated Availability Is Logged

A `DatedFuturesSeriesRecord` carries a non-empty `contract_universe` of
`FuturesContractRecord` records or mappings that validate into those records.
All contracts must match the series root.

The `availability_window` must include:

```text
start
end
availability_source = discovered_not_assumed
```

The record rejects full-history markers such as `full_history`,
`assumed_full_history`, or `full_historical_availability`, even when such a key
is set to `false`. This is the R-007 guard: expired-contract availability is
discovered and logged from actual discovery evidence; it is not inferred from a
root symbol, a roll policy id, or a provider-continuous comparison.

## Adjustment Is Explicit

`DatedFuturesSeriesRecord.adjustment_method` is a closed-set field:

- `unadjusted`
- `back_adjusted`
- `ratio_adjusted`

Unadjusted and adjusted series are never implicit. The record exposes
`adjusted_vs_unadjusted` for reporting, and it rejects any ambiguous adjustment
label.

## Boundaries

DATA-P11 has no provider-call, IBKR-connection, raw-write, parser,
canonicalization, session, roll-calendar, roll-computation, broker, order,
account, paper, live, real-time, deployment, alpha, profitability, or
tradability scope.

The provenance records are validation surfaces for later phases. They are not
proof that data exists, that a historical pull ran, that quality passed, that a
roll is executable, or that a dataset is ready for research.
