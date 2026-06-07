# FUTCORE-P30 Closeout Summary

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P30`  
Final campaign verdict: `COMPLETE_WITH_WARNINGS` (coordinator resolution;
autonomous closeout recorded `BLOCKED` on a local-only, CI-green verifier
failure — see
`campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/CLOSEOUT_COORDINATOR_RESOLUTION.md`
and `SUBSTRATE_SCALEOUT_V1_HANDOFF.md` in this directory)

This directory holds the human-facing closeout summary for the Futures Core
Alpha Pilot V1. The authoritative criterion-by-criterion audit is
`campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/CLOSEOUT.md`.

## Summary

The pilot completed one bounded evidence-gated research loop over the Data,
Feature/Label, Research Runtime, and Agent Factory stack, but terminal closeout
is blocked because `python tools/verify.py --all` failed during P30 validation.
The final promotion state is:

- 10 accepted StudySpecs entered the evidence gate;
- 4 ended as `REJECT`;
- 6 ended as `INCONCLUSIVE`;
- 0 ended as `WATCH`;
- 0 ended as `CANDIDATE_RESEARCH`;
- no idea is eligible for FactorLibrary ingestion or Strategy Reference
  validation from this pilot.

The campaign audit also carries unresolved timing, label-pack, cross-instrument
availability, cost/proxy, thin-session, RTH-comparator, and
variant-count-format limitations. Those warnings are preserved in the ledgers,
reviewer verdicts, promotion decisions, and downstream handoffs. They do not
override the validation blocker.

## Primary Closeout Artifacts

- Campaign audit: `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/CLOSEOUT.md`
- Durable docs summary: `docs/futures_core_alpha_pilot/CLOSEOUT.md`
- Promotion decisions:
  `research/futures_core_alpha_pilot_v1/promotion/PROMOTION_DECISIONS.md`
- Reviewer verdicts:
  `research/futures_core_alpha_pilot_v1/reviewer_verdicts/INDEX.md`
- Statistical review record:
  `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/statistical/FUTCORE-P25.md`
- Ledgers: `research/futures_core_alpha_pilot_v1/ledgers/INDEX.md`
- Downstream handoffs:
  `research/futures_core_alpha_pilot_v1/downstream_handoffs/README.md`
- Commit-eligible P30 handoff:
  `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P30.md`

## Boundaries

This closeout records research evidence only. It does not create a reviewer
artifact, verdict JSON, PR, merge, staged set, live/paper/broker/order
operation, deployment, FactorLibrary promotion, Strategy Reference validation,
capital decision, profitability claim, or tradability claim.
