---
campaign_id: ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1
phase_id: P022000_FUTSUB_RELOCK_RERUN
lane: yellow
status: in_progress
---

# P022000_FUTSUB_RELOCK_RERUN: re-lock Core Pilot StudySpecs against the session-truth substrate

## Purpose

P235500 (PR #376) repointed the remaining session-conditioned families to the
shared session truth; the coordinator data-op then sanctioned-deprecated 496
contract-divergent rows (backup `registry/backups/session_reset_repair_20260612T002901Z`)
and re-materialized the affected packs to NEW identities (liquidity 27/27,
cross_market 9/9, regime-scope 27/27, bbo-scope 27/27 units, 0 failures;
23 feature_ids, 400 REGISTERED rows; `base_ohlcv_rolling_volume` intentionally
deferred — it appears in no StudySpec). Consequence: the FUTSUB-P27 committed
re-locks now point at DEPRECATED records and must be re-issued. The role-marker
condition that GAPPED 2 of 6 prior-INCONCLUSIVE studies
(`label_as_feature_input:feature_pack_refs[0]:session_label` on
`liquidity_structure_range_contraction` and `bbo_tradability_spread_zscore`
records) is fixed at the source: the new records carry
`field_roles: {"session_label": "SESSION_METADATA"}`.

## Scope (in-bounds)

Re-run the FUTSUB-P27 re-lock methodology EXACTLY (read
`runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/phases/FUTSUB-P27/spec.md`
and `docs/futures_substrate_scaleout/CORE_PILOT_RELOCK.md` first; mirror the
bounded re-lock discipline):

1. Re-resolve the dataset-scope DatasetVersion/feature/label locks for all 10
   original Core Pilot StudySpecs against the live registry via
   `runtime.input_resolver.FeatureLabelPackResolver.resolve_feature_packs` /
   `resolve_label_packs` and validate with
   `alpha_system.governance.feature_lock_validation.validate_feature_locks`.
2. Do NOT edit AlphaSpecs or LabelSpecs in place (ids cascade). Re-issue locks
   and StudyInputPack references only. Hold fixed: alpha_spec_id, top-level
   label_spec_id, split_protocol, metrics, costs, variant budget, locked-test
   policy, negative controls, stopping rules.
3. SUPERSEDE the prior re-lock artifacts in
   `research/futures_substrate_scaleout_v1/rerun/study_specs/` (new sspec ids
   replace the old files; remove superseded JSONs in the same commit) and
   REWRITE `research/futures_substrate_scaleout_v1/rerun/studyspec_relock.md`
   with the new value-free report (counts, per-study table, named gaps if any,
   deliberate unresolvable probe).
4. Update `tests/unit/futures_substrate_scaleout/test_studyspec_relock_smoke.py`
   to validate the new artifacts (same smoke discipline: resolver + lock
   validator over every committed lock; no values embedded).
5. EXPECTED OUTCOME: 6/6 prior-INCONCLUSIVE studies RELOCKED (regime
   sspec_267cc052e37668339c38d179 and bbo sspec_9f6f741192a4b534f06e51c0 no
   longer GAPPED) + 4 prior-REJECT cross_market audit-only re-locks. If ANY
   study still gaps, record the named gap with the exact failing condition
   string and STOP — do not hand-patch locks, mutate registries, or weaken
   resolver semantics.

## Hard constraints

- READ-ONLY against registries and values: this phase materializes nothing,
  deprecates nothing, mutates no registry row.
- FORBIDDEN: `src/alpha_system/**` code changes, `runs/**` staging,
  `research/futures_core_alpha_pilot_v1/**` mutation (read-only input).
- Value-free artifacts only (ids, counts, conditions; no market/feature/label
  values).
- No `git worktree` commands; no .git config edits; explicit staging only.
- Research-only language; no alpha/tradability claims.

## Validation

```bash
ALPHA_DATA_ROOT=~/alpha_data/alpha_system ~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/futures_substrate_scaleout/test_studyspec_relock_smoke.py -q
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/futures_substrate_scaleout -q
python tools/verify.py --smoke
python tools/hooks/canary_runner.py
```

Exact counts in the handoff (feature locks resolved, label locks resolved,
per-study classification).

## Done criteria

- All 10 studies classified with deterministic evidence; 6/6
  prior-INCONCLUSIVE RELOCKED (or honestly GAPPED with exact conditions);
  smoke green against committed artifacts; prior re-lock artifacts superseded
  in-commit; truthful handoff; fresh adversarial review PASS or
  PASS_WITH_WARNINGS under `reviews/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`.
