# ES/NQ/RTY Mini Main-Batch Plan

`DATA-P10` defines the root-level batch plan for the ES/NQ/RTY mini historical
data foundation. It is declarative planning only: it performs no IBKR
connection, no external provider call, no pull, no raw write, and no statement
that data exists or that a pull is authorized.

## Symbol Batch Plan

`SymbolBatchPlan` lives in `src/alpha_system/data/foundation/batches.py`.

Required fields:

- `plan_id`
- `mini_main`
- `micro_secondary`
- `max_concurrent_roots`
- `do_not_mix_mini_and_micro_batches`

The canonical DATA-P10 plan is:

```text
plan_id: sbp_mini_main_es_nq_rty_v1
mini_main: ES, NQ, RTY
micro_secondary: MES, MNQ, M2K
max_concurrent_roots: 3
do_not_mix_mini_and_micro_batches: true
```

Validation is fail-closed. The mini and micro root sets must be disjoint, the
mini set must equal ES/NQ/RTY, the micro set must equal MES/MNQ/M2K, the
concurrency limit must equal `3`, and the separation flag must be true. Any
batch or manifest root set that contains both mini and micro roots is rejected;
this is the R-018 control.

The record is not a pull authorization. `implies_pull_authorization` is always
false, and the batch-plan mapping does not carry an authorization state.

## Primary Common Panel

The mini main-batch primary panel is the modern common panel:

```text
roots: ES, NQ, RTY
start_date: 2018-01-01
end_date: present_as_of_run
bar_size: 1 min
what_to_show: TRADES
session_views: ETH_canonical, RTH_derived
manifest_contract: HistoricalRequestManifest
pacing_policy_id: rpp_ibkr_historical_conservative_tobeverified_v1
```

The panel references the DATA-P07 `HistoricalRequestManifest` contract and the
DATA-P08 `RequestPacingPolicy`. It is still only planned coverage metadata; it
is not a coverage report, a quality result, or evidence that historical data has
been pulled.

## Optional Secondary Panels

Optional secondary panels are labeled QA or diagnostic panels and must not be
silently merged into the primary common panel.

| Panel | Roots | Window | Label |
| --- | --- | --- | --- |
| `mini_optional_es_nq_long_qa_panel` | ES, NQ | `2015-01-01` to `present_as_of_run` | ES/NQ long-panel data-QA and regime baseline; provider-continuous if needed |
| `mini_optional_rty_transition_qa_panel` | RTY | `2017-07-10` to `2017-12-31` | RTY CME transition QA only |
| `mini_optional_contract_truth_diagnostic_panel` | ES, NQ, RTY | rolling available expired window | Contract-truth diagnostic for discovered dated FUT availability only |

The contract-truth panel does not assume full expired-contract availability.
Availability is discovered and recorded by later contract/provenance phases.

## Synthetic Manifest

`templates/data/synthetic_mini_batch_manifest.json` is a tiny synthetic sample
manifest for the primary mini panel. It reuses the DATA-P07
`HistoricalRequestManifest` fields and deterministic `manifest_hash` semantics,
with DATA-P08 pacing policy id
`rpp_ibkr_historical_conservative_tobeverified_v1`.

The sample manifest uses fake planning metadata only. It marks:

- `synthetic: true`
- `sample_manifest: true`
- `coverage_status: planned_only_not_requested`
- `real_coverage_claim: false`
- `authorization_claim: false`
- `pull_authorization: false`
- `data_exists_claim: false`

It includes only ES/NQ/RTY request specs and no MES/MNQ/M2K roots.

## Boundaries

DATA-P10 does not implement `MicroBatchPolicy`; DATA-P19 owns that separate
secondary path. DATA-P10 also does not add parser, canonicalization, quality,
coverage, roll, session, dataset-version, broker, order, account, paper, live,
real-time, alpha, profitability, tradability, or production-readiness scope.

Real market data remains local-only under `ALPHA_DATA_ROOT` and must not be
committed. Run-local Workflow 2 artifacts remain under `runs/**` and must not be
staged.
