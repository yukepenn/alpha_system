# Runbook — ALPHA_IDEA_TO_VERDICT_LOOP_V0 (IVL)

> Shape source: `campaigns/000-template/RUNBOOK.md` (Commands + Rollback intent),
> authored in the comprehensive shape of `campaigns/DIFFERENTIATED_KILLSHOT_V1/RUNBOOK.md`
> (Preconditions / Validation / Launch / per-phase checks / STOP-resume / Hard stops).
> All commands are copied from the live `justfile` and `tools/`; research-only language —
> this loop produces governed diagnostics and verdicts, never alpha/profit/tradability/production claims.

This campaign is **assembly + consolidation** over an intact reuse spine: it wires a researcher-
facing front door (`alpha idea`) onto the existing governance trunk (AlphaSpec / MechanismCard /
SetupSpec / StudySpec / TrialLedger / RejectedIdea / PromotionDecision) and a new fast exploratory
lane that loads **already-materialized** Parquet (load-only). No new mechanism, feature, label, data,
or downstream module is built. Lanes are GREEN/YELLOW only — no RED (no paid data, broker, live,
paper, order, or new universe).

## Preconditions
- `python tools/frontier/status_doctor.py` → no other campaign RUNNING (live status authority;
  never trust a committed pointer for in-flight phase).
- Git `main`-only and clean; `git ls-files runs` returns empty.
- The 6 bundle files are on `main`:
  `campaigns/ALPHA_IDEA_TO_VERDICT_LOOP_V0/{GOAL.md,PHASE_PLAN.md,campaign.yaml,ACCEPTANCE.md,RISK_REGISTER.md,RUNBOOK.md}`
  (exactly these 6 per `tools/frontier/campaign_schema.py` `REQUIRED_CAMPAIGN_FILES`; no second
  `ACTIVE_CAMPAIGN.md` inside the campaign dir — root pointer only).
- The 7 phase specs are on `main`:
  `specs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P0n-<slug>.md` for n=0..6.
- The 8 legacy Track-A cards are present read-only as the migration reference:
  `research/differentiated_substrate_v1/cards/*.json` (migration outputs land under a NEW canonical
  dir; the cards are NOT edited).
- `ACTIVE_CAMPAIGN.md` repointed to `ALPHA_IDEA_TO_VERDICT_LOOP_V0` (coordinator-only, serial, at launch).
- IVL has no prior run, so validation uses a fresh mock run (no `RUN_REFUSED_INCOMPLETE_RUN_EXISTS`
  guard to clear).

## Validation (no providers / no network / no merge)
```bash
# 1. repo clean + no run artifacts staged
git status --porcelain
git ls-files runs            # must be empty

# 2. campaign.yaml parses as YAML
python -c "import yaml; yaml.safe_load(open('campaigns/ALPHA_IDEA_TO_VERDICT_LOOP_V0/campaign.yaml'))"

# 3. read-only DAG plan: 7 sequential waves (IVL-P00..IVL-P06), parallelizable:false
just frontier-plan ALPHA_IDEA_TO_VERDICT_LOOP_V0

# 4. fresh mock parallel run (mock providers, no network, no merge); max_parallel 3 but
#    the linear DAG linearizes to 1 phase per wave
just frontier-run-parallel-mock ALPHA_IDEA_TO_VERDICT_LOOP_V0 3

# 5. smoke + canary gate
python tools/verify.py --smoke
python tools/hooks/canary_runner.py
```

## Launch (Workflow 2, provider-wired, parallel max 3)
```bash
# coordinator repoints ACTIVE_CAMPAIGN.md first (serial), then:
just frontier-run-parallel ALPHA_IDEA_TO_VERDICT_LOOP_V0 3
# IVL-P00 -> IVL-P01 -> IVL-P02 -> IVL-P03 -> IVL-P04 -> IVL-P05 -> IVL-P06 ; serial merge queue.
# The linear dependency chain means each wave holds one phase even at max_parallel 3.
```
(The in-driver provider-watchdog carries hang auto-recovery on a continuous-stall window; keep an
external progress-watchdog armed as a belt-and-suspenders fallback. Resume an interrupted run with
`python tools/frontier/ralph_driver.py resume --run-dir runs/<RID> --provider-wired` —
**NEVER `run`** (a fresh `run --campaign-id` mints a new run and re-executes from IVL-P00).)

## Standard per-phase checks
```bash
python tools/verify.py --smoke
python tools/verify.py --all
python tools/hooks/canary_runner.py
git ls-files runs            # must stay empty
```
Run the narrowest meaningful test first (the phase's own unit/integration test), then broaden to
`--all` when shared behavior changed. Record any skipped check with its reason in the handoff.

## Phase-specific verification
- **IVL-P00** (role-unification ADR + schema map): doc/ADR only — `git diff --stat` touches only
  `decisions/ADR-IVL-0001-role-unification.md` and `docs/IDEA_TO_VERDICT_SCHEMA_MAP.md`; **no behavior
  change**. ADR records AlphaSpec as the front-door trunk, the 3 conflict resolutions
  (`study_kind` on the new wrapper only; AlphaSpec always minted so shape-bearing ideas ride the
  trunk; graveyard requires an AlphaSpec id), per-object role contract, the full Track-A field map,
  the 4 fail-closed gaps (`source`, `cost_sensitivity`, `variant_budget`, `duplicate_exposure`),
  the mechanism-id lineage rule (kebab slug → `MechanismCard.source`), and the `data_dependency.class`
  partition. REUSE-MAP re-confirms each cited governance symbol against current code (verify before
  believing).
- **IVL-P01** (intake validator + `alpha idea validate`):
  ```bash
  python -m pytest tests/unit/governance/test_idea_draft.py tests/unit/governance/test_track_a_migration.py tests/unit/cli/test_idea_cli.py -q
  ```
  `alpha idea validate <idea.yaml>` emits a canonical AlphaSpec + MechanismCard (+ SetupSpec when
  `study_kind=context_not_equal_trigger`); the optional `study_kind` discriminator validates on the
  new IdeaDraft wrapper (greenfield); all 8 Track-A cards migrate (day_of_week as the `main_effect`
  exemplar, `mech_<24-hex>` minted, slug preserved as `source`); validation **fails closed** when any
  of the 4 gap fields cannot populate; a parity test asserts the canonical-vs-card field map; the
  `idea` group registers in `build_parser()`.
- **IVL-P02** (testability gate + `alpha idea testability`):
  ```bash
  python -m pytest tests/unit/research_lane/test_testability_gate.py tests/unit/research/test_conditional_probe_class_guard.py -q
  alpha idea testability <idea.yaml>   # -> PASS | FAIL | DATA_GAP (PRE-TEST verdict)
  ```
  5 fail-closed checks return PASS/FAIL/**DATA_GAP** (DATA_GAP is a PRE-TEST verdict — the shot is not
  spent): features materialized; labels/path-labels exist; path-label ≥2-class non-degeneracy;
  N_eff/MDE plausible; dedup known; no-lookahead/`available_ts` satisfiable; surrogate-FDR requirement
  known. The new ≥2-distinct-class precondition is added to the `conditional_probe.py` empty-set
  guards (reusing the label-runtime class-count summary). The gate orchestrator lives in
  `src/alpha_system/research_lane/` (NOT under `research/`).
- **IVL-P03** (fast exploratory lane bridge): one generic
  `fast_probe(card, setup, slice_spec)` in `src/alpha_system/research_lane/` loads a bounded EXISTING
  slice via `core.value_store.load_parquet_values` + `runtime.input_resolver.FeatureLabelPackResolver`,
  maps to governance rows, and feeds `build_factor_diagnostics_run` | `evaluate_setup_conditional_probe`
  in-memory. `promotion_eligible=False`; no materialization, no scaleout driver call, no second value
  loader. Fails closed with DATA_GAP when polars is absent or rows are unloadable (no fabricated values).
  ```bash
  python -m pytest tests/unit/research_lane/test_fast_probe.py -q
  # boundary guard MUST stay green (bridge is in research_lane/, not research/):
  python -m pytest tests/unit/research/test_research_no_value_engine.py -q
  python tools/verify.py --boundaries
  ```
- **IVL-P04** (verdict `REPORT.md` renderer):
  ```bash
  python -m pytest tests/unit/research_lane/test_verdict_report.py -q
  ```
  Golden-file test asserts the rendered `REPORT.md` shows idea summary, `study_kind`, slice,
  data/features/labels used, dedup outcome, the 5 gate verdicts, the fast readout (incl.
  `class_count`/`minority_count` so single-class is self-evident), N_eff/MDE, surrogate state, and the
  verdict (REJECT/DATA_GAP/INCONCLUSIVE/WATCH/CANDIDATE) + why + next action, citing
  `VerdictReasonCode`.
- **IVL-P05** (memory wiring + `alpha idea run`):
  ```bash
  python -m pytest tests/unit/research_lane/test_memory_router.py tests/unit/cli/test_idea_cli.py -q
  ```
  `alpha idea run` maps verdict → memory: REJECT → `create_rejected_idea_record` (via `alpha_spec_id`,
  asserted present, fail closed); DATA_GAP → requeue (`validate_requeued_verdict_record`);
  WATCH/CANDIDATE → `create_promotion_decision` (requires `reviewer_verdict_id`, never auto).
  FactorLibrary stays survivor-only; the exploratory readout is never auto-promoted —
  `reject_exploratory_promotion_artifact` fails closed on any `EXPLORATORY`-stamped artifact reaching
  a trusted input.
- **IVL-P06** (dogfood DK Track B through the loop): no new mechanism/feature/label/data, no
  geometry sweep, no promotion.
  ```bash
  python -m pytest tests/integration/test_ivl_dogfood_track_b.py -q
  ```
  Acceptance proof (see Dogfood steps below): DATA_GAP on the degenerate slice, PASS on
  ES_2020_120m, `REPORT.md` emitted, memory written, `promotion_eligible=false` throughout.

## `alpha idea` CLI smoke (after IVL-P01..P05 merge)
```bash
alpha idea --help                      # idea group registered (validate / testability / run / gate)
alpha idea validate <idea.yaml>        # emits AlphaSpec + MechanismCard (+SetupSpec) ; exit 0
alpha idea testability <idea.yaml>     # PASS | FAIL | DATA_GAP (pre-test) ; exit 0
alpha idea run <idea.yaml>             # end-to-end: validate -> testability -> fast_probe ->
                                       # REPORT.md -> memory ; promotion_eligible=false throughout
```
Handlers delegate to existing governance/research-lane library functions and return exit code 2 on
domain errors (mirrors `cli/study.py`). No business logic lives in the CLI layer.

## Dogfood steps (IVL-P06)
```bash
# 1. degenerate (burned) single-class ES_2024 120m slice -> Check-3 DATA_GAP (PRE-TEST, shot not spent)
alpha idea gate <idea_track_b.yaml> --slice ES_2024_120m
#    expect: testability Check-3 (path-label >=2-class) -> DATA_GAP -> requeue ; no real metric run

# 2. barrier-resolving ES_2020_120m slice (verified two-class 309206/3950 ; coverage matrix
#    row_count 313156, ACCEPTED) -> Check-3 PASS -> real probe readout + verdict
alpha idea gate <idea_track_b.yaml> --slice ES_2020_120m   # expect Check-3 PASS
alpha idea run  <idea_track_b.yaml> --slice ES_2020_120m   # emits REPORT.md + writes memory
```
- The ES_2020_120m Parquet is **local-only** (`labels/materialized/.../ES_2020_120m/`, not in git).
  If `ALPHA_DATA_ROOT` is unset in the executor, the loop must return an honest **DATA_GAP** (the
  `first_light` DATA_GAP branch), never fabricated values — acceptance tolerates this.
- Load-only: NO `alpha feature|label materialize`, NO `--force-recompute`, NO scaleout driver call,
  NO registry write. The FUTSUB-stamped packs are read, never recomputed.

## Canary + smoke gate (each phase, before commit/merge-gate)
```bash
python tools/verify.py --smoke
python tools/hooks/canary_runner.py     # safety canaries must PASS (fail when a guard is bypassed)
```

## Artifact audit (before any commit or merge-gate evaluation)
```bash
git ls-files runs                       # MUST be empty (runs/** is local-only, never staged)
git diff --cached --name-only           # confirm staged set: no runs/, no data/parquet/sqlite/
                                        # arrow/feather/log/cache/secret/model-binary path
python tools/verify.py --artifacts      # artifact-policy guard over the diff
python tools/verify.py --boundaries     # boundary guard (research/ must not import the value engine)
```
- Stage explicit paths only — `git add .` / `git add -A` are forbidden. No force push.
- Commit-eligible handoffs live under `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/<PHASE_ID>.md`;
  commit-eligible reviews under `reviews/ALPHA_IDEA_TO_VERDICT_LOOP_V0/<PHASE_ID>/**`.
  Run-local `handoff.md`, `review.md`, `verdict.json`, `checks.json`, and repair attempts stay under
  `runs/<RID>/**` and are never staged.

## Closeout (campaign done)
```bash
python tools/frontier/status_doctor.py        # IVL run reports complete; no other RUNNING campaign
python tools/verify.py --all && python tools/hooks/canary_runner.py
git ls-files runs                              # still empty
just frontier-lessons <RUN_ID>                 # emit runs/<RID>/LESSONS_CANDIDATES.md (local) for
                                               # the lessons flywheel
```
- All 7 phases merged on `main`; acceptance criteria in `ACCEPTANCE.md` satisfied; a campaign
  `RUN_SUMMARY` (or equivalent) exists; durable lessons added to `project-skill` when applicable.
- Coordinator repoints `ACTIVE_CAMPAIGN.md` away from IVL at closeout; prune any leftover worktrees
  (investigate uncommitted worktree changes before pruning — uncertain ⇒ keep).
- Verdict-language check: the dogfood `REPORT.md` and all artifacts use research-only language
  (diagnostics + gates decide; no alpha/profit/tradability/production claims).

## STOP / resume
- `runs/<RID>/STOP` is an active stop request, checked before each stage (provider calls, phase
  select, execute, validation, review, PR, CI, merge gate, merge, done-check, next-phase).
- Resume requires the STOP condition removed/resolved, then
  `python tools/frontier/ralph_driver.py resume --run-dir runs/<RID> --provider-wired` resumes from
  recorded run state — it does NOT regenerate completed work. Never relaunch with `run --campaign-id`
  (mints a fresh run from IVL-P00).
- A terminal STOP ("stopped safely, all phases completed") is a completion marker, not a failure.

## Rollback / recovery
- Failed or out-of-scope phase: Ralph routes a bounded in-scope repair; on contradictory scope,
  repeated failure, missing authorization, or impossible validation, mark the phase **blocked** and
  stop (do not silently expand scope).
- IVL-P01..P05 are additive (new `cli/idea.py`, new `research_lane/` package, new IdeaDraft wrapper,
  new tests); rollback = revert the phase branch. The single in-place edit (the ≥2-distinct-class
  guard added to `conditional_probe.py` in IVL-P02) is a guard-tightening; rollback = revert that
  hunk and re-run `tests/unit/research/`.
- Migrate-then-retire safety: the 8 legacy Track-A cards stay in place until the canonical line
  reproduces all 8 AND the parity test is green; retirement is a LATER phase, not part of V0. Do NOT
  edit or delete `tools/differentiated_killshot_v1/**` or `research/futures_substrate_scaleout_v1/**`
  (STOPPED campaigns) — they are forbidden_paths.
- Never delete on suspicion; when retention is ambiguous, keep and record the question.

## Hard stops
No paid data/feed (incl. fomc/cpi card onboarding — those cards migrate as records only, never
tested in V0); no broker/live/paper/order/capital; no new universe; no non-regenerable deletion; no
committing data/DB/Parquet/SQLite/Arrow/Feather/logs/caches/secrets/registries/model binaries; no
truth-chain / no-lookahead / ledger / FDR / surrogate ZERO_PASS_MET / no-second-PnL weakening; no
chartering or building any downstream module (Mining V2, FactorLibrary, AlphaBook, Strategy Sandbox,
PA grammar); no feature/label materialize, `--force-recompute`, scaleout driver call, or registry
write; no editing the forbidden FUTSUB/DK STOPPED-campaign paths or `core/value_store.py` (import
allowed, edits forbidden); no auto-promotion of any exploratory readout (surface for the
reviewer-gated survivor decision; survivor count is 0 today).
