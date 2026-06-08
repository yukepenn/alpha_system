# Futures Research Substrate Scaleout Overview

`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` is a bounded research-only
substrate campaign. It consumes the existing ES/NQ/RTY DatasetVersion,
feature, label, runtime, roll-contract, and split primitives and prepares a
full-window research substrate for later reviewed campaigns.

The campaign bundle is the source of truth. If this overview disagrees with
`campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`, the campaign bundle
wins and the disagreement should stop execution until repaired.

## Mission

The campaign closes substrate gaps exposed by the prior Core Pilot: accepted
DatasetVersion contracts, roll-splice and maintenance-crossing guards,
full-window feature and label materialization plans, resolver-smoke discipline,
coverage and quality matrices, N_eff and walk-forward wiring inputs, and a
bounded rerun of existing Core Pilot StudySpecs where the substrate becomes
resolvable.

This is substrate engineering. It does not create a new hypothesis batch,
promote factors, validate strategies, or authorize paper trading, live trading,
broker operations, order routing, deployment, capital allocation, profitability
claims, or tradability claims.

## Phase Map

The authoritative phase map is in:

- `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/PHASE_PLAN.md`
- `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/campaign.yaml`

The campaign has 34 phases, `FUTSUB-P00` through `FUTSUB-P33`. `FUTSUB-P00` is
Green bootstrap work. Later phases are Yellow unless a generated and reviewed
phase spec says otherwise. The campaign expects no Red scope.

## Boundaries

- Inputs resolve through approved registry and runtime tool surfaces.
- Raw provider access, external provider calls, and re-pulls are out of scope
  unless a later phase proves corruption and authorizes repair.
- Feature values, label values, local registries, roll-calendar data, heavy
  artifacts, logs, caches, secrets, and credentials remain local-only.
- BBO is treated only as a top-book proxy in this campaign, not execution truth.
- Roll metadata is a leakage guard and analytic contract, not a live roll engine
  or tradable contract resolver.
- Cross-market work preserves per-instrument availability and does not
  forward-fill across instruments.
- Diagnostics and reruns must use runtime tool contracts and conservative report
  language.

## Source Of Truth

- Campaign contract: `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`
- Active pointer: `ACTIVE_CAMPAIGN.md`
- Commit-eligible research evidence root:
  `research/futures_substrate_scaleout_v1/`
- Commit-eligible handoffs:
  `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`
- Optional commit-eligible reviews:
  `reviews/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`
