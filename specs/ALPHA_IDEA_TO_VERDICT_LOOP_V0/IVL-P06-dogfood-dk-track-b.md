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

# IVL-P06 — Dogfood DK Track B Through the Loop (no new mechanism/feature/label/data, no sweep, no promotion)

---
campaign_id: ALPHA_IDEA_TO_VERDICT_LOOP_V0
phase_id: IVL-P06
lane: YELLOW
status: draft
dependencies: [IVL-P05]
executor: Codex GPT-5.5 high
reviewer: Claude Opus 4.8 xhigh
verifier: Claude Sonnet 4.6
---

## Purpose

Prove the loop end-to-end on a real existing idea **without** adding any mechanism, feature, label, data, geometry sweep, or promotion: run `alpha idea gate` on the **burned single-class ES_2024 120m** slice and expect a **Check-3 DATA_GAP PRE-TEST** (shot not spent) → requeue; then run on the **barrier-resolving ES_2020_120m** slice (verified two-class) and expect **Check-3 PASS** → `alpha idea run` emits a real probe readout + verdict + `REPORT.md`, with memory written and `promotion_eligible=false` throughout. This is also the subsumption proof for the IVL-P03 bridge (the bespoke bridges are now generalized; their retirement remains a later, out-of-V0 step).

YELLOW: the dogfood is the integration proof that the gate spends no shot on degenerate data and runs cleanly on resolving data.

## Context

Verified live:

- **Two slices, one verified two-class:** `research/futures_substrate_scaleout_v1/label_packs/path/coverage_matrix.json` records partition `ES_2020_120m` as `ACCEPTED`, `row_count 313156` (two-class target_before_stop, 309206 False / 3950 True). The ES_2024 120m slice used by the prior DK Track B run is the burned **single-class** degenerate slice (Check-3 must DATA_GAP it pre-test).
- **Local-only data:** the materialized packs live under `data/` / `labels/materialized/.../ES_2020_120m/` (local-only Parquet, not in git, FUTSUB-stamped). IVL reads them **load-only** via the IVL-P03 bridge (`load_parquet_values`); **no** materialize, recompute, scaleout-driver call, or registry write — FUTSUB is a STOPPED campaign and must not be touched.
- **Honest DATA_GAP if data absent:** if `ALPHA_DATA_ROOT` is unset / `polars` absent in the executor, the IVL-P03 fast_probe DATA_GAP fallback applies; acceptance tolerates an honest DATA_GAP and forbids fabricated values.
- **Loop components:** IVL-P01 (`validate`) → IVL-P02 (`testability`/`gate`) → IVL-P03 (`fast_probe`) → IVL-P04 (`report`) → IVL-P05 (`run` + memory). The DK Track B idea is `context_not_equal_trigger` (distinct context vs trigger); it rides the AlphaSpec trunk with MechanismCard/SetupSpec sidecars.

## Scope

1. **Dogfood idea + slice specs (no new mechanism/feature/label):** express the existing DK Track B context≠trigger idea as an `idea.yaml` whose features/labels/path-label already exist (no FeatureRequest, no materialization), and two `SliceSpec`s — the burned single-class ES_2024 120m and the barrier-resolving ES_2020_120m. Reuse the existing factor/label ids; do not author a new mechanism, feature, label, or geometry sweep.
2. **`alpha idea gate` on ES_2024 120m → DATA_GAP pre-test:** the testability gate's Check-3 (path-label ≥2-class) returns **DATA_GAP** before any probe (shot not spent); `alpha idea run` routes it to requeue.
3. **`alpha idea gate` on ES_2020_120m → PASS → `alpha idea run`:** Check-3 PASS; the loop runs the fast_probe (satisfying surrogate `ZERO_PASS_MET` + family-budget `RESPECTED` + ≥2-class internally, never bypassed), renders `REPORT.md`, writes a memory record, with `promotion_eligible=false` throughout.
4. **Honest DATA_GAP tolerance:** if the ES_2020 data does not resolve in the executor (`ALPHA_DATA_ROOT` unset / `polars` absent), record an honest DATA_GAP (no fabricated values) and document it; acceptance is met either way (PASS-with-readout or honest-DATA_GAP).
5. **Tests + runbook:** an integration test driving both slices through `alpha idea gate`/`run` asserting DATA_GAP-pre-test on the degenerate slice and PASS (or honest DATA_GAP) on ES_2020_120m, `REPORT.md` emitted, memory written, `promotion_eligible=false` throughout; a short dogfood runbook. Committed outputs are value-free (REPORT/readout text with ids/counts/gate outcomes only).

## Non-Goals

- Adding any new mechanism, feature, label, dataset, geometry/horizon sweep, or per-instrument split.
- Materializing/recomputing any feature/label, calling the scaleout driver, writing a registry entry, or editing any FUTSUB/DK artifact (`research/futures_substrate_scaleout_v1/**`, `tools/differentiated_killshot_v1/**` are STOPPED).
- Any promotion, PromotionDecision, FactorLibrary/AlphaBook entry, or flipping `promotion_eligible` to true.
- Retiring the bespoke bridges (later, out-of-V0, test-gated) or sourcing paid data.
- Any alpha/tradability/profitability claim.

## Expected Files (illustrative)

- `research/idea_to_verdict_loop_v0/dogfood/**` — new (the two idea/slice specs; value-free REPORT/readout outputs).
- `docs/IDEA_TO_VERDICT_DOGFOOD.md` — new (runbook + the two-slice expected outcomes).
- `tests/integration/test_ivl_dogfood_track_b.py` — new.
- `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P06.md`, `reviews/.../IVL-P06/**`.

USED unchanged: the entire IVL-P01..P05 loop; the existing ES_2020_120m local Parquet (load-only); the existing DK Track B factor/label ids (referenced, not edited).

## Interfaces / Contracts

- **Degenerate slice contract:** `alpha idea gate` on ES_2024 120m ⇒ Check-3 = DATA_GAP **pre-test** (probe not invoked, asserted by test) ⇒ `alpha idea run` requeues.
- **Resolving slice contract:** `alpha idea gate` on ES_2020_120m (verified two-class, `row_count 313156`) ⇒ Check-3 PASS ⇒ `alpha idea run` emits a value-free readout (surrogate `ZERO_PASS_MET` + family-budget `RESPECTED` + ≥2-class satisfied internally) + `REPORT.md` + memory record, `promotion_eligible=false`.
- **DATA_GAP tolerance:** if rows do not resolve (`ALPHA_DATA_ROOT` unset / `polars` absent), an honest DATA_GAP (no fabricated values) also satisfies acceptance.
- **No FUTSUB touch:** reads are load-only via `load_parquet_values`; no materialize/recompute/scaleout/registry; no edit under any FUTSUB/DK path.

## Forbidden Changes

- Adding a new mechanism/feature/label/dataset/sweep; materializing/recomputing; calling the scaleout driver; writing a registry entry; editing any FUTSUB/DK artifact.
- Any promotion / PromotionDecision / FactorLibrary entry; flipping `promotion_eligible` to true; letting an EXPLORATORY readout reach promotion.
- Fabricating values when rows do not resolve; sourcing paid data; un-deferring fomc/cpi.
- Editing the engines, `first_light.py`, the bespoke bridges, the single-factor template, or the value engine; importing a value loader into `research/`.
- Adding a runtime dependency beyond IVL-P03's optional polars; committing data/parquet/sqlite/secrets.
- `git add .` / `git add -A`, force push, auto-merge, deployment, PR self-approval, broker/live calls; weakening/skipping existing tests/canaries; any alpha/tradability/profitability claim.

## Validation

```bash
# 1) Integration dogfood (both slices).
python -m pytest tests/integration/test_ivl_dogfood_track_b.py -q
# 2) gate on burned single-class ES_2024 120m -> Check-3 DATA_GAP pre-test.
python -m alpha_system.cli.main idea gate research/idea_to_verdict_loop_v0/dogfood/track_b_es2024_120m.idea.yaml
# 3) gate on barrier-resolving ES_2020_120m -> Check-3 PASS (or honest DATA_GAP if data unset) -> run.
python -m alpha_system.cli.main idea gate research/idea_to_verdict_loop_v0/dogfood/track_b_es2020_120m.idea.yaml
python -m alpha_system.cli.main idea run  research/idea_to_verdict_loop_v0/dogfood/track_b_es2020_120m.idea.yaml
# 4) Smoke + canaries (forbidden_exploratory_promotion, forbidden_second_pnl_truth, forbidden_scope_drift).
python tools/verify.py --smoke
python tools/hooks/canary_runner.py
# 5) No research->sim bridge; engines/template byte-unchanged.
grep -rEn "import +(alpha_system\.)?(backtest|management|fast_path|core\.value_store)|from +(alpha_system\.)?(backtest|management|fast_path|core\.value_store)" src/alpha_system/research && echo "FORBIDDEN IMPORT FOUND" && exit 1 || echo "no forbidden research->sim imports"
git diff -- src/alpha_system/research/conditional_probe.py src/alpha_system/research/first_light.py src/alpha_system/strategies/templates.py
# 6) No FUTSUB/DK edit.
git diff -- research/futures_substrate_scaleout_v1 tools/differentiated_killshot_v1
# 7) Run-artifact discipline + no committed data.
git ls-files runs
git diff --cached --name-only | grep -E "\.(parquet|arrow|feather|dbn|zst|sqlite|db)$|^data/" && echo "FORBIDDEN DATA STAGED" && exit 1 || echo "no forbidden data staged"
```

Broaden to `python tools/verify.py --all` if shared probe/diagnostics/governance behavior appears affected; clean shell, `FRONTIER_*` unset. Record skipped checks + reasons (incl. an honest DATA_GAP if `ALPHA_DATA_ROOT` is unset).

## Artifact Policy

`runs/**` local-only, never staged. Commit-eligible handoff `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P06.md`; review under `reviews/.../IVL-P06/**`. Dogfood `REPORT.md`/readout outputs are value-free (ids/counts/gate outcomes only — no raw rows, parquet, registry, or DB; never under a FUTSUB/core-pilot namespace). Loaded materialized rows stay local-only/untracked. Never commit `runs/**`, parquet/arrow/feather/dbn/zst/sqlite/db, `data/raw/**`, `data/canonical/**`, secrets, `**/*.key`. `git ls-files runs` empty.

### Allowed Paths (commit-eligible — explicit staging only)

- `research/idea_to_verdict_loop_v0/dogfood/**`
- `docs/IDEA_TO_VERDICT_DOGFOOD.md`
- `tests/integration/test_ivl_dogfood_track_b.py`
- `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P06.md`
- `reviews/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P06/**`

### Local-only run artifacts (NOT commit-eligible, never staged)

- `runs/**` — local audit/resume only.

## Allowed Test Paths

- `tests/integration/test_ivl_dogfood_track_b.py`. Do not weaken/skip existing tests/canaries or add visible test-only branches.

## Done Criteria

- `alpha idea gate` on the burned single-class ES_2024 120m slice returns **Check-3 DATA_GAP pre-test** (probe not invoked, asserted) and `alpha idea run` requeues (shot not spent).
- `alpha idea gate` on barrier-resolving **ES_2020_120m** (verified two-class, `row_count 313156`) returns **Check-3 PASS** and `alpha idea run` emits a value-free probe readout + `REPORT.md` + memory record with `promotion_eligible=false` — **or** an honest DATA_GAP (no fabricated values) if `ALPHA_DATA_ROOT`/`polars` are unavailable.
- No new mechanism/feature/label/data/sweep; no materialize/recompute/scaleout/registry; no FUTSUB/DK edit (diff clean); no research→sim grep hit; engines/`first_light.py`/template byte-unchanged.
- `forbidden_exploratory_promotion` (and the other canaries) stay green; `promotion_eligible=false` throughout; smoke + canaries pass; `git ls-files runs` empty; no forbidden data staged; explicit staging; no `forbidden_paths` edits.
- Commit-eligible handoff written; YELLOW review artifacts present.

## Handoff Requirements

Write `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P06.md`: scope delivered; exact validation commands + results; skipped checks + reasons (incl. honest DATA_GAP if data unset); files changed by path; explicit confirmation that (a) the degenerate ES_2024 slice yields a Check-3 DATA_GAP **pre-test** (shot not spent) and requeues, (b) ES_2020_120m yields Check-3 PASS → readout + REPORT.md + memory (or honest DATA_GAP with no fabricated values), (c) `promotion_eligible=false` throughout and the exploratory readout never reaches promotion (canary green), (d) no new mechanism/feature/label/data/sweep and no materialize/recompute/scaleout/registry/FUTSUB-DK edit (load-only reads), (e) `git ls-files runs` empty, no forbidden data staged, explicit staging, no `forbidden_paths` edits. Run-local handoff stays local-only.

## Review Requirements

YELLOW fresh Claude Opus review under `reviews/.../IVL-P06/**`. Reviewer adversarially confirms: the degenerate ES_2024 slice is DATA_GAP'd **pre-test** (probe genuinely not invoked — asserted, not prose) and requeued; ES_2020_120m yields a Check-3 PASS readout (surrogate `ZERO_PASS_MET` + family-budget + ≥2-class satisfied, not bypassed) + REPORT.md + memory, or an honest DATA_GAP with zero fabricated values; `promotion_eligible=false` throughout and the EXPLORATORY readout is refused by the promotion path (canary green); no new mechanism/feature/label/data/geometry sweep; no materialize/recompute/scaleout-driver/registry write; no edit under any FUTSUB/DK path (reads are load-only); engines/`first_light.py`/single-factor template byte-unchanged; the bespoke bridges remain untouched (retirement correctly deferred); committed dogfood outputs are value-free and not under a FUTSUB namespace; no paid data; research-only language; smoke + canaries pass; `git ls-files runs` empty; no forbidden data staged; explicit staging.

## Auto-Merge / Review Policy

No PR creation, auto-merge, or deployment authorized. Merge gating is the Ralph driver's responsibility under YELLOW lane policy (block on critical / test-tamper / boundary violation / EXPLORATORY-leak / second-PnL-bridge / scope-drift) + human authorization. This is the campaign-closing phase; the campaign done-check + `RUN_SUMMARY.md` are the driver's responsibility, not this spec.

## Repair-or-Rollback

- **In-scope repair only:** fix the dogfood idea/slice specs, the integration test, or the runbook within Allowed Paths; no scope expansion.
- **Rollback:** additive dogfood specs + value-free outputs + one integration test + a runbook; revert to restore prior state with no migration/data change (all data is local-only/untracked; no FUTSUB/DK artifact is touched).
- **STOP / escalate:** any pressure to add a new mechanism/feature/label/data/sweep, materialize/recompute/call the scaleout driver/write a registry entry, edit a FUTSUB/DK artifact, fabricate values when rows do not resolve, promote a verdict or flip `promotion_eligible`, retire a bespoke bridge without the test-gated subsumption, add paid data, or commit a `runs/`/data/secret artifact — treat as out-of-scope and surface to the user.
