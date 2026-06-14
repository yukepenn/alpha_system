# ALPHA_IDEA_TO_VERDICT_LOOP_V0 — Phase Specs (IVL-P00 .. IVL-P06)

> Shape source: these specs follow the live phase-spec shape used by `specs/DIFFERENTIATED_KILLSHOT_V1/DK-P00..DK-P05` — YAML front-matter (`campaign_id, phase_id, lane, status, dependencies, executor, reviewer, verifier`) then the `tools/frontier/spec_schema.py:REQUIRED_SECTIONS` (Purpose, Context, Scope, Non-Goals, Expected Files, Forbidden Changes, Validation, Done Criteria, Handoff Requirements, Review Requirements) plus the DK convention sections (Interfaces/Contracts, Allowed Paths, Allowed Test Paths, Artifact Policy, Auto-Merge/Review Policy, Repair-or-Rollback). `REQUIRED_SECTIONS` is a review convention, not an automated gate; the enforced gates are `require_campaign_files` (6-file bundle), `load_campaign_yaml` + `parse_campaign_phases` (`just frontier-plan ALPHA_IDEA_TO_VERDICT_LOOP_V0`), and a fresh mock run.
>
> Research-only language throughout: no alpha / profitability / tradability / production claims. Lanes GREEN/YELLOW only — no RED. Allowed verdict outputs: REJECT / DATA_GAP / INCONCLUSIVE / WATCH / CANDIDATE. `runs/**` is local-only and never staged.
>
> **Shared `forbidden_paths` (YAML anchor in `campaign.yaml`):** `src/alpha_system/execution/**`, `broker/**`, `live/**`, `portfolio/**`, `management/**`, `backtest/**`, `l2/**`, `agent_factory/**`, `src/alpha_system/core/value_store.py` (import allowed, EDITS forbidden), `src/alpha_system/strategies/templates.py`, `src/alpha_system/research/conditional_probe.py` semantics (additive guard only — see IVL-P02), `src/alpha_system/research/track_a_scorer.py`, `tools/differentiated_killshot_v1/**`, `research/futures_substrate_scaleout_v1/**`, `research/futures_core_alpha_pilot_v1/**`, all `data/**`, any `*.sqlite`/`*.db`/`*.parquet`/`*.arrow`/`*.feather`/`*.dbn`/`*.zst`.
> **Shared commit-eligible globs (every phase):** `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/<PHASE_ID>.md`, `reviews/ALPHA_IDEA_TO_VERDICT_LOOP_V0/<PHASE_ID>/**`. `campaign.yaml` `allowed_paths` MAY list `runs/**`; the spec's Allowed Paths MUST NOT (local-only; `git ls-files runs` stays empty).

---
---

---

# IVL-P00 — Role-Unification ADR + Canonical Idea-Object Schema Map

---
campaign_id: ALPHA_IDEA_TO_VERDICT_LOOP_V0
phase_id: IVL-P00
lane: YELLOW
status: draft
dependencies: []
executor: Codex GPT-5.5 high
reviewer: Claude Opus 4.8 xhigh
verifier: Claude Sonnet 4.6
---

## Purpose

Write the load-bearing architecture decision the entire V0 loop depends on, **as documents only — no code, no behavior change, no metric.** Record, as an ADR + a schema map, that:

1. **AlphaSpec is the front-door trunk** (always minted); **MechanismCard** and (optionally) **SetupSpec** are emitted **sub-objects**, linked at the intake/orchestration layer — never by mutating any frozen governance dataclass.
2. The optional **`study_kind` discriminator** (`main_effect | context_not_equal_trigger`) lives on a NEW intake/IdeaDraft wrapper, not on any existing governance record.
3. The 8 Track-A doc-convention cards (`research/differentiated_substrate_v1/cards/*.json`) are a **legacy schema marked migrate-then-retire** into the canonical line — **no second card class** survives.

This phase is YELLOW because the ADR pins the trunk, the lane routing, and the migration contract that IVL-P01..P05 implement; an error here mis-shapes every later phase.

## Context

Verified against live code this session (cite-and-trust, re-verify before building):

- **Disconnected siblings today.** `ALPHA_SPEC_REQUIRED_FIELDS` (`src/alpha_system/governance/alpha_spec.py:31-45`) carries only `hypothesis_id` as a parent link — no `mechanism_id`/`setup_spec_id`. `MECHANISM_CARD_REQUIRED_FIELDS` (`governance/mechanism_card.py:31-45`) has no `alpha_spec_id`. `STUDY_SPEC_REQUIRED_FIELDS` (`governance/study_spec.py:31-43`) links only `alpha_spec_id` + `label_spec_id`.
- **The "kill-trunk" is already AlphaSpec-keyed.** `TrialLedger`, `EvidenceBundle`, `PromotionDecision` all key off `alpha_spec_id`; `RejectedIdea` keys off the dual field `alpha_spec_id_or_hypothesis_id` (`governance/rejected_idea.py:36`).
- **Closed schemas / content-hash IDs.** AlphaSpec/MechanismCard/SetupSpec are frozen, slotted, `allowed_fields == required_fields` dataclasses whose deterministic ID hashes every non-id field (`generate_alpha_spec_id` `alpha_spec.py:148`; `generate_mechanism_id` `mechanism_card.py:186`). Adding a field re-hashes every locked ID and breaks validation — confirmed hazard.
- **`study_kind` is greenfield.** `grep -rn study_kind src/alpha_system/governance/` is empty.
- **Track-A cards are pure documents.** No `.py` under `src/`, `tests/`, or `tools/` loads `cards/*.json`; their distinctive field names (`economic_rationale`, `conditioning_variable`, `expected_orthogonality_to_dead_mechanisms`, `lookahead_risk`, `data_dependency`, `value_free_status`, `capacity_turnover_note`) appear in zero `.py` files. The only downstream seam is the bare `mechanism_id` STRING carried in `study_spec.dataset_scope['mechanism_id']`, read by STOPPED DK tooling (`tools/differentiated_killshot_v1/**`) — do not touch.

## Scope

This phase writes **documents only**.

1. **`decisions/ADR-IVL-0001-role-unification.md`** recording, with cited evidence:
   - The per-object role contract table (idea.yaml/IdeaDraft → AlphaSpec front-door → MechanismCard/SetupSpec sub-objects → FeatureRequest/LabelSpec → StudySpec → EvidenceBundle/ReviewerVerdict/TrialLedger → Rejected/Requeue/Candidate/FactorLibrary).
   - **Conflict resolution 1 (`study_kind`):** lives only on the new IdeaDraft wrapper; routes lanes (`main_effect → build_factor_diagnostics_run`; `context_not_equal_trigger → evaluate_setup_conditional_probe`). Rationale: frozen closed-schema id-hash hazard.
   - **Conflict resolution 2 (no shape→StudySpec link):** the front door **always mints an AlphaSpec trunk** even for shape-bearing ideas; MechanismCard(+SetupSpec) ride as lineage sidecars at the orchestration layer. No StudySpec schema change in V0.
   - **Conflict resolution 3 (graveyard key gap):** because an AlphaSpec is always minted, `REJECT → graveyard` writes via `alpha_spec_id_or_hypothesis_id`; IVL-P05 must assert an AlphaSpec ID exists before any graveyard write (fail closed otherwise).
   - The note that an AlphaSpec is constructed via `validate_alpha_spec` + `generate_alpha_spec_id` (there is **no** `create_alpha_spec` factory) and links via `hypothesis_id`; the wrapper supplies/derives that id.
2. **`docs/IDEA_TO_VERDICT_SCHEMA_MAP.md`** recording the full Track-A → canonical field map and the four fail-closed gaps:
   - `hypothesis.economic_rationale → rationale`; `hypothesis.statement → expected_mechanism`; `expected_sign → expected_direction`; `expected_horizon[list] → horizon[str]` (collapse rule: one MechanismCard per horizon **or** a pre-registered primary horizon — multi-horizon cards force a documented 1:N decision); `expected_session → session`; `required_features.existing → required_features[list[str]]`; `required_labels.existing → required_labels[list[str]]`.
   - Lookahead / orthogonality / conditioning material → `AlphaSpec.timestamp_assumptions` / `exclusion_rules` / `expected_failure_modes` / `promotion_criteria` + `data_assumptions`.
   - **Four fail-closed gaps (no doc-card source):** `source`, `cost_sensitivity`, `variant_budget`, `duplicate_exposure`. Record that `source` carries the kebab slug as lineage (`track_a:<slug>`); `mechanism_id` cannot migrate verbatim (canonical = `mech_<24-hex>` content hash, `ids.py`), so the slug becomes `MechanismCard.source` and **must stay attached** so the STOPPED DK `dataset_scope['mechanism_id']` linkage is unbroken.
   - **`data_dependency.class` partition:** `existing_substrate` = `day_of_week_effect` (sole live `main_effect` exemplar); `derivable_from_exchange_calendar` ×5 → DATA_GAP/requeue (need new FeatureRequest); `needs_paid_data` ×2 (`fomc_drift`, `cpi_surprise_reversion`) → record-only, never tested in V0 (RED-deferred, out of scope).
   - Mark `cards/*.json` legacy-to-migrate; retirement is a later (out-of-V0) step gated on a canonical-vs-card parity test (added in IVL-P01) — never deleted on suspicion.

## Non-Goals

- Any code, engine change, CLI registration, test, or real-data metric (IVL-P01+).
- Editing any governance dataclass, the cards JSON, the FDR budget docs, or any FUTSUB/DK artifact.
- Charters for any downstream module (Mining V2, FactorLibrary, AlphaBook, Strategy Sandbox, PA grammar).
- Promoting `fomc`/`cpi` off DEFERRED or sourcing paid data.

## Expected Files (illustrative, not prescriptive)

- `decisions/ADR-IVL-0001-role-unification.md` — new (the role contract + 3 conflict resolutions).
- `docs/IDEA_TO_VERDICT_SCHEMA_MAP.md` — new (field map + 4 gaps + data_dependency partition + legacy-to-migrate mark).
- `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P00.md` — new (commit-eligible handoff).
- `reviews/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P00/**` — new (commit-eligible YELLOW review artifacts).

No `runs/` path appears here.

## Interfaces / Contracts

- The ADR is a decision **document**, not a record object; it creates no governance ID and changes no schema.
- The schema map must cite each canonical target by `file:symbol` (e.g. `governance/mechanism_card.py:MECHANISM_CARD_REQUIRED_FIELDS`) so IVL-P01 implements against verified targets.
- The `mech_<24-hex>` content-hash rule and the slug→`source` lineage rule are stated so IVL-P01 does not break the STOPPED `dataset_scope` seam.

## Forbidden Changes

- Editing any path under `forbidden_paths`.
- Writing any code, test, or metric (IVL-P00 is documents-only).
- Adding a runtime dependency (`numpy`/`pandas`/`polars` stay unimportable here); committing secrets, data, DBs, caches, or heavy artifacts.
- `git add .` / `git add -A`, force push, auto-merge, deployment, PR self-approval, or any broker/live call.
- Any alpha/tradability/profitability claim, FactorLibrary promotion, or second-PnL truth.

## Validation

Run from the repo root; all local-only, no provider/network/merge calls.

```bash
test -f decisions/ADR-IVL-0001-role-unification.md
test -f docs/IDEA_TO_VERDICT_SCHEMA_MAP.md
python tools/verify.py --smoke
python tools/hooks/canary_runner.py
git ls-files runs            # must print nothing
git diff --stat              # only decisions/ + docs/ changed (no src/, no tests/)
```

Broaden to `python tools/verify.py --all` only if a shared check appears affected; run in a clean shell with `FRONTIER_*` env unset (known driver-env false negative). Record skipped checks + reasons in the handoff.

## Artifact Policy

`runs/**` is local-only runtime state and must never be staged. Commit-eligible handoff at `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P00.md`; review notes/verdict under `reviews/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P00/**`. Never commit `runs/**`, parquet/arrow/feather/dbn/zst/sqlite/db, `data/raw/**`, `data/canonical/**`, secrets, `**/*.key`. `git ls-files runs` empty.

### Allowed Paths (commit-eligible — explicit staging only)

- `decisions/ADR-IVL-0001-role-unification.md`
- `docs/IDEA_TO_VERDICT_SCHEMA_MAP.md`
- `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P00.md`
- `reviews/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P00/**`

### Local-only run artifacts (NOT commit-eligible, never staged)

- `runs/**` — local audit/resume only. No `runs/` path appears under Allowed Paths.

## Allowed Test Paths

- None. IVL-P00 is documents-only and adds no tests. Do not weaken, skip, or add visible test-only branches to any existing test or canary.

## Done Criteria

- `decisions/ADR-IVL-0001-role-unification.md` committed: per-object role contract + the 3 conflict resolutions (study_kind on wrapper; always-mint-AlphaSpec; graveyard via `alpha_spec_id_or_hypothesis_id`); states AlphaSpec is built via `validate_alpha_spec`+`generate_alpha_spec_id` (no `create_alpha_spec`).
- `docs/IDEA_TO_VERDICT_SCHEMA_MAP.md` committed: full Track-A→canonical field map, 4 fail-closed gaps, slug→`source` lineage + `mech_<24-hex>` rule (DK seam preserved), `data_dependency.class` partition, cards marked legacy-to-migrate (retire later, parity-gated).
- `python tools/verify.py --smoke` + `python tools/hooks/canary_runner.py` pass; `git ls-files runs` empty; `git diff --stat` touches only `decisions/`+`docs/`; explicit staging; no `forbidden_paths` edits; no code/metric.
- Commit-eligible handoff written; YELLOW review artifacts present.

## Handoff Requirements

Write `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P00.md`: scope delivered; exact validation commands + results; any skipped check + reason; files changed by path; explicit confirmation that (a) no code/test/metric was written, (b) the ADR pins AlphaSpec as the always-minted trunk with study_kind on the wrapper, (c) the schema map records the 4 fail-closed gaps and the slug→`source`/`mech_<24-hex>` rule preserving the STOPPED DK `dataset_scope` seam, (d) cards are marked legacy-to-migrate (not deleted), (e) `git ls-files runs` empty with explicit staging and no `forbidden_paths` edits. Run-local `runs/<run_id>/.../handoff.md` stays local-only.

## Review Requirements

YELLOW requires fresh Claude Opus review under `reviews/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P00/**`. Reviewer adversarially confirms: the ADR is documents-only (no code/metric); the trunk decision matches live code (TrialLedger/EvidenceBundle/PromotionDecision are `alpha_spec_id`-keyed; RejectedIdea dual-key); `study_kind` is correctly placed on a new wrapper (the closed-schema id-hash hazard is stated, not violated); the field map is faithful and the 4 gaps + slug→`source`/`mech_<24-hex>` rule preserve the STOPPED DK seam; the data_dependency partition is correct (1 live exemplar, 5 DATA_GAP, 2 RED-deferred); research-only language; no downstream-module charter; smoke + canaries pass; `git ls-files runs` empty.

## Auto-Merge / Review Policy

No PR creation, auto-merge, or deployment authorized. Merge gating is the Ralph driver's responsibility under YELLOW lane policy + human authorization. `auto_pr`/`auto_merge` in `campaign.yaml` are driver hints, not a self-approval grant.

## Repair-or-Rollback

- **In-scope repair only:** fix the ADR/schema-map content within Allowed Paths; no scope expansion.
- **Rollback:** both deliverables are Markdown; revert to restore prior state with no code/data change.
- **STOP / escalate:** any pressure to write code/metrics here, mutate a governance dataclass, edit cards/FDR/FUTSUB/DK artifacts, un-defer fomc/cpi, or commit a `runs/`/data/secret artifact — surface to the user.

---
---

---

## ERRATA (coordinator review fix — HypothesisCard parent)
Minting a valid AlphaSpec requires a `hypothesis_id` of kind HYPOTHESIS_CARD (`governance/alpha_spec.py` `_validate_ids` -> `validate_governance_id(expected_kind=HYPOTHESIS_CARD)`). So this ADR MUST add **HypothesisCard** to the canonical hierarchy as AlphaSpec's parent (idea.yaml -> HypothesisCard -> AlphaSpec -> MechanismCard/SetupSpec sub-objects). Reuse the existing `governance/hypothesis_card.py`; do NOT add a new card class.

