# MES/MNQ/M2K Micro Batch Policy

`DATA-P19` defines `MicroBatchPolicy` for the MES/MNQ/M2K micro futures roots.
This is a separate secondary data-foundation path. It is declarative planning
only: it performs no IBKR connection, no external provider call, no manifest
pull, no raw or canonical write, and no statement that data exists or has passed
quality review.

## Required Policy Fields

`MicroBatchPolicy` lives in `src/alpha_system/data/foundation/batches.py`.

Required fields:

- `batch_id`
- `symbols`
- `start_date`
- `separate_batch`
- `parity_check_targets`

The canonical DATA-P19 policy is:

```text
batch_id: mbp_micro_secondary_mes_mnq_m2k_v1
symbols: MES, MNQ, M2K
start_date: 2020-01-01
separate_batch: true
parity_check_targets: ES->MES, NQ->MNQ, RTY->M2K
```

`start_date = 2020-01-01` is a planning default to be verified against clean
available data in a later authorized workflow. It is not a data-availability,
coverage, quality, or provider-support claim. If a later authorized discovery
workflow establishes an earlier clean available date, that must be recorded as
verified provenance before it can replace the planning default.

## Separate-Batch Guarantee

Validation is fail-closed:

- `symbols` must equal `MES/MNQ/M2K`.
- Mini roots `ES/NQ/RTY` are rejected from the micro policy and from micro
  manifest-root validation.
- `separate_batch` must be `true`.
- The policy references the DATA-P10 `SymbolBatchPlan` separation contract,
  including `do_not_mix_mini_and_micro_batches = true` and
  `max_concurrent_roots = 3`.

The micro batch cannot represent a mixed mini/micro batch. It is not merged into
the ES/NQ/RTY mini main-batch plan.

## Contract-Economics Reference

The micro policy references the DATA-P05 `InstrumentMasterRecord` economics for
`MES`, `MNQ`, and `M2K`. It does not duplicate point values, tick sizes, tick
values, multipliers, or production-certification status. DATA-P05 remains the
owner of those instrument-economics anchors.

## Parity-Check Targets

The declared mini-to-micro parity-check targets are:

| Mini root | Micro root |
| --- | --- |
| `ES` | `MES` |
| `NQ` | `MNQ` |
| `RTY` | `M2K` |

These are target declarations only. They are not parity results, quality
findings, tradability findings, or evidence that micro data has been pulled.

## V1 Role And Boundaries

Micros are not a primary alpha source in V1. They are a secondary path for
future bounded checks and diagnostics after the main mini data foundation is
controlled.

DATA-P19 does not add parser, canonicalization, quality, coverage, roll,
session, dataset-version, broker, order, account, paper, live, real-time, alpha
search, factor research, label research, strategy research, profitability,
tradability, or production-readiness scope.

Real market data remains local-only under `ALPHA_DATA_ROOT` and must not be
committed. Run-local Workflow 2 artifacts remain under `runs/**` and must not be
staged.
