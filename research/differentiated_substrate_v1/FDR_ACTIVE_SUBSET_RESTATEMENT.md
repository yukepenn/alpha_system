# FDR Active-Subset Restatement - DIFFERENTIATED_KILLSHOT_V1

Status: VALUE-FREE pre-registration restatement NOTE. This document is created
before any DK-P00 variant attempt, StudySpec scoring attempt, surrogate run, or
real-data metric inspection in this campaign chain. It contains no real-data IC,
return, bucket, walk-forward, N_eff, power, diagnostic, alpha, profitability, or
tradability value.

- campaign_id: `DIFFERENTIATED_KILLSHOT_V1`
- phase_id: `DK-P00`
- created_at: `2026-06-14T03:45:38Z`
- provenance:
  - `research/differentiated_substrate_v1/FDR_BUDGET.md`
  - `research/differentiated_substrate_v1/FDR_BUDGET_PRIORITY_2_3.md`
  - `research/differentiated_substrate_v1/SUBSTRATE_GROUNDING.md`
  - `research/differentiated_substrate_v1/cards/**`
  - `campaigns/DIFFERENTIATED_KILLSHOT_V1/{GOAL.md,PHASE_PLAN.md,campaign.yaml,ACCEPTANCE.md,RISK_REGISTER.md,RUNBOOK.md}`

## Vehicle Choice

This artifact is a pre-registration restatement NOTE, not a
`BudgetAmendmentRecord`.

The prior budget machinery remains authoritative for budget growth:
`create_budget_amendment_record(...)` requires `new_budget > prior_budget`.
That object is intentionally strictly increasing and cannot encode a downward
active-subset re-scope. DK-P00 therefore uses this value-free note to pin the
active surface for this run while carrying the existing family budgets unchanged.
No new governance object is instantiated here.

## Active Surface For This Run

The active mechanisms for `DIFFERENTIATED_KILLSHOT_V1` are:

| Mechanism | Family placement | Treatment in this run | variant_budget |
|---|---|---|---:|
| `day_of_week_effect` | flow-seasonality | Active pooled mechanism | 1 |
| `opex_pinning` | event-calendar | Active pooled mechanism | 1 |
| `month_end_flow` | event-calendar | Active pooled mechanism; `month_end_rebalance_flow` is folded into this one month-end hypothesis | 1 |
| `roll_week_flow` | flow-seasonality | Active pooled mechanism | 1 |
| `open_close_auction_flow` | flow-seasonality | Active pooled mechanism | 2 |

`month_end_rebalance_flow` is not counted as an additional active mechanism. It
is the close-proximity specification of the already-counted month-end pooled
hypothesis, per the de-duplication rule in
`FDR_BUDGET_PRIORITY_2_3.md`.

## Deferred Surface

The following mechanisms are deferred and are not exercised in this run:

| Mechanism or family | Status | Reason |
|---|---|---|
| `fomc_drift` | DEFERRED | `needs_paid_data`; out this round |
| `cpi_surprise_reversion` | DEFERRED | `needs_paid_data`; out this round |
| Governed overnight family | DEFERRED | Not exercised; no overnight mechanism cards this round |

## Family Budgets Carried Unchanged

The family budgets are not amended by this note:

| Family | Source | family_budget |
|---|---|---:|
| event-calendar | `FDR_BUDGET.md` | 6 |
| flow-seasonality | `FDR_BUDGET_PRIORITY_2_3.md` | 4 |

These are the existing pre-registered family caps. This active-subset
restatement does not lower or raise them; it only identifies which mechanisms
are active for this run before any metric exists.

## Active Effective Pooled Surface Arithmetic

Pooling is across ES/NQ/RTY as one test per mechanism/horizon surface. There is
no per-instrument split in this run.

Active event-calendar surface:

- `opex_pinning`: 1 pooled horizon
- `month_end_flow`: 1 pooled horizon
- event-calendar active subtotal: 1 + 1 = 2

Active flow-seasonality surface:

- `day_of_week_effect`: 1 pooled horizon
- `roll_week_flow`: 1 pooled horizon
- `open_close_auction_flow`: 2 pooled horizons
- flow-seasonality active subtotal: 1 + 1 + 2 = 4

Active effective pooled surface:

```text
event-calendar{opex 1 + month_end 1} = 2
flow-seasonality{day_of_week 1 + roll_week 1 + open_close 2} = 4
2 + 4 = 6
```

Therefore the active effective pooled surface for this run is **6**.

## Pre-Metric Lock

This note is the DK-P00 FDR-before-metric gate. It must predate any later
variant attempt, real-data scoring attempt, or diagnostic artifact in the
campaign. Later phases may cite this note as the active-subset lock, but they
must not reinterpret it as evidence.

No real-data IC, return, bucket, walk-forward, N_eff, power, diagnostic value,
or trading result appears in this document or anywhere in DK-P00.
