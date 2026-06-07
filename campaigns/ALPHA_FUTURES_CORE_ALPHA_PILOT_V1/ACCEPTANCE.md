# ACCEPTANCE — ALPHA_FUTURES_CORE_ALPHA_PILOT_V1

This file defines the acceptance criteria for the campaign and for each
acceptance gate. A phase is **done** only when its lane checks pass, its handoff
exists, its review artifacts exist (Yellow), the artifact policy holds, and the
semantic done-check passes. The campaign is **done** only when every gate's exit
requirement is met, the final semantic done-check passes, and `CLOSEOUT.md`
records a verdict in `{COMPLETE, COMPLETE_WITH_WARNINGS, BLOCKED}`.

## Campaign-Level Acceptance

1. **Campaign contract completeness** — `GOAL.md`, `PHASE_PLAN.md`,
   `campaign.yaml`, `ACCEPTANCE.md`, `RISK_REGISTER.md`, `RUNBOOK.md` present and
   mutually consistent. No campaign-local `ACTIVE_CAMPAIGN.md`. Root
   `ACTIVE_CAMPAIGN.md` selects this campaign.
2. **Preflight readiness** — `FEATURE_LABEL_PARQUET_SINK_V1` and
   `SESSION_LABEL_GUARD_FIX_V1` complete; runtime real-data smoke status recorded;
   Agent Factory preflight recorded; consumed primitives import; `verify.py
   --smoke` passes.
3. **DatasetVersion / FeaturePack / LabelPack lock** — locked by reference
   (ids/hashes) through registry tools; no value data committed.
4. **Parquet value access** — research-scale scans use registry-resolved Parquet
   values; JSONL used only for audit/smoke/small; no arbitrary path reads.
5. **session_label guard** — session-context features used only when declared
   point-in-time `SESSION_METADATA`; role-aware guard respected; canaries pass.
6. **Runtime smoke** — diagnostics run only through the runtime tool surface;
   runtime package not edited.
7. **Agent Factory preflight** — roles/permissions/queue contracts drive the
   pilot; no autonomous agent instantiation; separation of duties enforced.
8. **AlphaSpec batch quality** — five family batches drafted within per-family
   quotas using the P05 protocol, each declaring family-specific diagnostics.
9. **StudySpec quality** — one StudySpec per accepted AlphaSpec, binding
   packs/sessions/horizons/cost profiles/variant budget.
10. **Family budget adherence** — approved specs honor 40/20/15/15/10; volume is
    overlay-only with no standalone budget.
11. **Diagnostics outputs** — factor, label, signal-probe, and cost diagnostics
    produced per study via runtime tools; reports value-free.
12. **Cost stress** — `base`, `stress_1`, `stress_2`, `double_cost` produced;
    `zero_cost` diagnostic only; no zero-cost promotion basis.
13. **Thin-session stress** — ETH/pre_RTH/post_RTH carry stricter
    spread/slippage/capacity stress; fragile survivors flagged.
14. **Session / horizon matrix** — session × horizon × regime matrix produced;
    narrow-cell-only survivors flagged.
15. **No-lookahead / leakage audit** — `available_ts`/`label_available_ts`
    validity confirmed; no final-session aggregates intraday; cross-instrument
    availability enforced; no same-bar optimism.
16. **TrialLedger completeness** — every run recorded.
17. **RejectedIdeaLedger completeness** — every rejection recorded with a reason;
    duplicate-exposure hints present.
18. **EvidenceDraft quality** — survivors carry FactorLibrary-ready EvidenceDrafts
    referencing diagnostics, cost, stability, audits, verdict, rejected-idea links.
19. **Reviewer verdict independence** — one independent Statistical Reviewer
    verdict per survivor; reviewer is not the implementer; no self-review.
20. **Promotion boundary** — decisions use only `REJECT | INCONCLUSIVE | WATCH |
    CANDIDATE_RESEARCH`; `WATCH`/`CANDIDATE_RESEARCH` require a reviewer verdict;
    at most 2 survivors; no forbidden state.
21. **DAG scheduler consistency** — parallel phases have disjoint `allowed_paths`;
    `must_run_alone` phases are not `parallel_safe`; serial merge respected; phase
    branches never write `ACTIVE_CAMPAIGN.md`.
22. **Artifact policy** — explicit staging only; `git ls-files runs` empty; no
    raw/canonical/feature/label values, Parquet/Arrow/Feather, provider responses,
    or local DB files committed.
23. **Closeout handoff quality** — concrete failure-mode handoffs to
    `ALPHA_VALIDATION_GOVERNANCE_V1`, `ALPHA_FACTOR_LIBRARY_V1`, and
    `ALPHA_STRATEGY_REFERENCE_VALIDATION_V1`.

## Gate-Level Acceptance

### Gate `bootstrap_and_inputs` — FUTCORE-P00…P06
Campaign bundle present; no campaign-local `ACTIVE_CAMPAIGN.md`; preflight gates
recorded; scope/universe/session/horizon/budget contract pinned; input pack
locked by reference; cost model + stress profiles pinned; AlphaSpec batch
protocol and bounded research queue/role assignment set; artifact audit clean.

### Gate `alpha_spec_batches` — FUTCORE-P07…P11
All five family AlphaSpec batches drafted within per-family quotas using the P05
protocol, each declaring its family-specific diagnostics requirements; drafts
value-free; no spec self-approved, implemented, or run.

### Gate `spec_audit_and_packs` — FUTCORE-P12…P15
Independent AlphaSpec critique + family budget audit; data-contract /
FeaturePack / LabelPack audit mapping each accepted spec to available primitives
with a minimal gap list; approved StudySpec pack; minimal missing primitives (or
a recorded no-op) via FeatureRequest/LabelSpec with tests and `available_ts`.

### Gate `family_diagnostics` — FUTCORE-P16…P20
All five family diagnostics run via the runtime tool surface over locked Parquet
packs; value-free DiagnosticsReports with required factor/label/signal-probe/cost
outputs and family-specific splits; no value data committed; no promotion.

### Gate `consolidation_and_audits` — FUTCORE-P21…P24
Cost-stress + thin-session consolidation, session/horizon/regime matrix,
no-lookahead/leakage/same-bar audit, and bounded-grid/variant-budget audit
complete; fragile survivors flagged; no zero-cost promotion basis; no locked-test
tuning.

### Gate `evidence_ledger_promotion` — FUTCORE-P25…P28
Independent statistical reviewer verdicts; TrialLedger and RejectedIdeaLedger
populated with reasons and duplicate-exposure hints; EvidenceDrafts +
FactorLibrary-ready handoffs for survivors only; PromotionDecisions use only
allowed states with reviewer verdicts for `WATCH`/`CANDIDATE_RESEARCH` and ≤2
survivors.

### Gate `handoff_and_closeout` — FUTCORE-P29…P30
Concrete failure-mode handoffs to the three next campaigns; acceptance audit +
semantic done-check pass; `CLOSEOUT.md` records the final verdict; coordinator
updates `ACTIVE_CAMPAIGN.md`; `verify.py --all` and canaries pass.

Allowed final verdicts: `COMPLETE`, `COMPLETE_WITH_WARNINGS`, `BLOCKED`.

## Prohibited Shortcuts (any one fails acceptance)

- raw provider data read; external provider API call
- manual arbitrary Parquet path reading; JSONL used for large research scans
- diagnostics without a StudySpec; implementation without an AlphaSpec
- new feature without a FeatureRequest; new label without a LabelSpec
- no cost stress; zero-cost result used as a promotion basis
- no session split; no RTH/ETH split; no session × horizon matrix
- no VariantBudget; locked-test tuning; repeated selection on the same OOS
- rejected ideas omitted; duplicate exposure rediscovered silently
- self-review; self-promotion; `WATCH`/`CANDIDATE` without a reviewer verdict
- Strategy Reference / FactorLibrary V1 / AlphaBook scope creep
- strategy/live/paper/profitability/tradability/production claim
- candidate treated as capital allocation or paper/live readiness
- heavy/raw/value/DB data committed; `runs/**` staged
- parallel phase without disjoint `allowed_paths`; phase branch writes
  `ACTIVE_CAMPAIGN.md`; merge outside the serial merge queue

## Acceptance Evidence

The closeout phase (`FUTCORE-P30`) must cite, for every criterion above, the
artifact path(s) under `research/futures_core_alpha_pilot_v1/**`,
`handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/**`, and
`reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/**` that satisfy it, plus the final
`verify.py --all` and canary results.
