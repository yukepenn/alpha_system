# Validation Governance Handoff

`FUTSUB-P31` adds the value-free requirement handoff from
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` to
`ALPHA_VALIDATION_GOVERNANCE_V1`.

Primary handoff:
`handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/VALIDATION_GOVERNANCE_HANDOFF.md`

The downstream campaign owns implementation of:

- multiple-testing / false-discovery correction over the declared study
  population;
- sealed-holdout access policy and contamination ledger;
- random-target, permuted-target, planted-fake-alpha, and leakage-sentinel
  negative controls;
- promotion eligibility using only `REJECT`, `INCONCLUSIVE`, `WATCH`, and
  `CANDIDATE_RESEARCH`;
- DSR/PBO/PSR or documented alternatives for any survivor candidate.

FUTSUB supplies the inputs only: P24 purged/embargoed walk-forward fold
metadata, P25 N_eff reporting metadata, P15/P23/P26 coverage and quality
matrices, feature/label resolver-smoke reports, and the P29 honest verdict
refresh. Rows remain raw observation counts; N_eff is the overlap-aware
effective-sample input. The `STRUCTURAL`, `MEDIUM`, and `FAST` half-life hooks
are split-routing metadata, not validity or promotion claims.

This document and the primary handoff do not implement governance logic, do not
materialize values, do not run diagnostics, and make no profit, trade-readiness,
promotion, deployment, or capital decision.
