# CLEANUP_PLAN.md — Aggressive-but-safe cleanup & optimization

**Status:** AUTONOMOUS — operator granted full authority to proceed on judgment (no approval gate).
Two **safety** preconditions remain before any PR executes: (1) the deep structure audit (`whxf2856i`)
lands and is folded in, and (2) FCFP closes at 16/16 (touching `main` mid-run would collide).
Standing rule still in force: stop-and-report only on a real contradiction, a gate that would change,
or an in-flight collision — that is a safety report, not an approval request.
This file is uncommitted/untracked working scratch.

**Live-run state at authoring:** FCFP `FEATURE_COMPUTE_FAST_PATH_V1` = 13/16 (P13 benchmark, RUNNING, no STOP).
FUTSUB `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` = P14–P33 pending (resume owed).
**Execution precondition:** FCFP at 16/16, P15 verified, driver exited, no STOP. In-flight code frozen until the relevant run closes.

**Prime directive honored:** preserve every capability; delete only what is *proven* unreferenced; optimize only behind a green parity/behavior gate; uncertain ⇒ Bucket C (keep). Every claim below was **independently re-verified against the live repo this session** (the audit's agents had two wrong delete calls — both caught and demoted to KEEP).

**Headline (honest):** the safe hard-delete set is **4 files**; the safe behind-a-gate set is **~6 changes**; the entire `src/alpha_system` application layer is **Bucket C (keep)** — it is either the correctness oracle, governance, or in-flight optimization (the V1 fast path). There is no safe aggressive `src` refactor right now, and manufacturing one would be high-risk/zero-payoff. "Aggressive" here = decisive on a small, proven cruft set; reverent on everything load-bearing.

---

## BUCKET A — HARD DELETE (proven zero live callers)

| # | Item | Evidence (re-verified this session) | Action |
|---|------|-------------------------------------|--------|
| A1 | `tools/frontier/review_schema.py` | `grep -rn "review_schema\|REQUIRED_REVIEW_SECTIONS" --include=*.py` → **only the file's own definition line**; zero importers. `verdict.py` (imported by `merge_gate.py` + `ralph_driver.py`) is the live verdict authority. | `git rm` in PR-2 |
| A2 | `docs/CLI_COMMANDS_TARGET.md` | Live refs: only `docs/README.md` (index) + **closed-campaign immutable history** (`campaigns/ALPHA_SYSTEM_V1/*`, `handoffs/…AGENT-P20.md`, `…ASV1-P02.md`). No `*.py` / `frontier.yaml` / test refs. | Fold "Planned" content into `docs/CLI_REFERENCE.md`, then `git rm`; fix `docs/README.md` link only (PR-1) |
| A3 | `docs/RESEARCH_WORKFLOW.md` | Live refs: only `docs/README.md` + closed `ALPHA_SYSTEM_V1` history. | Fold human-flow → `RESEARCHER_GUIDE.md`, WF2 → `AI_AGENT_GUIDE.md`, then `git rm`; fix `docs/README.md` (PR-1) |
| A4 | `docs/HARNESS_WORKFLOW_2.md` | Live refs: only `docs/README.md` + closed `ALPHA_SYSTEM_V1` history. | Fold into `docs/AI_AGENT_GUIDE.md`, then `git rm`; fix `docs/README.md` (PR-1) |

**Rule applied:** closed-campaign artifacts that mention these docs are **immutable phase history** — not rewritten. Only the live `docs/README.md` index links are updated.

**Candidates the audit put in A but I DEMOTED to KEEP (uncertain/live-ref ⇒ core):**
- `PROGRESS.md` — **live reference** at `tools/frontier/dag_scheduler.py:55` (and read by `status_doctor.py:50`). Not provably safe → **KEEP** (already carries the HISTORICAL banner).
- `docs/PLAN.md` — only `ACTIVE_CAMPAIGN.md` + campaign artifacts reference it (the `campaign_schema.py` hit was `PHASE_PLAN.md`, a false match). Low payoff, non-zero risk → **KEEP for now** (revisit post-close only if `ACTIVE_CAMPAIGN.md` is confirmed not to point at it).
- `.claude/agents/{architect,researcher,release_manager,harness_maintainer,done_checker}.md`, `.claude/hooks/notification.sh`, `evals/behaviors/heldout_behavior_00{1,2}.md`, `scripts/ralph/**`, `configs/**` — all have live wiring (`.claude/settings.json`, `frontier.yaml` roles/`heldout_behavior_check_required`, justfile, `campaign.yaml` scope globs, 10+ importers). **KEEP all.**

---

## BUCKET B — OPTIMIZE / MERGE / REFACTOR (behind a green gate; results identical before & after)

Gate for **every** B item: `python tools/verify.py --all` **and** `python tools/hooks/canary_runner.py` green before and after, plus the per-item test below — captured both times.

| # | Item | Why safe / what changes | Gate (must match before↔after) |
|---|------|-------------------------|--------------------------------|
| B1 | Remove dead **lane-level** keys from `frontier.yaml`: `max_phase_minutes`, `max_micro_loops`, `required_checks` (green/yellow/red) | Driver reads `workflow2.max_phase_minutes` (`ralph_driver.py:603-604,649`), `max_micro_loops_default`, and `github.required_checks` (`phase_required_checks` `ralph_driver.py:2467-2469`). Lane copies are **validation-only** (`config.py`). Remove key **and** its `REQUIRED_LANE_KEYS` entry + test fixtures in the same PR. | `pytest tests/test_frontier_config.py tests/test_ralph_driver.py -q`; `status_doctor.py --json` |
| B2 | Remove dead `workflow2.worktree_mode_recommended` | Zero non-`config.py` readers (verified). Remove key + `REQUIRED_WORKFLOW2_KEYS` entry + test together. | `pytest tests/test_frontier_config.py -q` |
| B3 | Collapse the **triplicated WF2 state-machine literal** in `AGENTS.md`, `CLAUDE.md`, `docs/AI_AGENT_GUIDE.md` → one-line pointer "See `frontier.yaml workflow2.states`". Keep the YAML array as the single source of truth; keep prose/headers. | Pure docs; no code reads the prose copies. | grep shows the literal only in `frontier.yaml`; `verify --all` |
| B4 | Doc index: `README.md`/`docs/README.md` point to `just --list` + the one canonical AGENTS index instead of re-listing commands/docs that drift. | Pure docs. | manual link check; `verify --all` |
| B5 | `tools/frontier/phase.py` `status` subcommand → delegate to `status_doctor` (no programmatic callers; CLI-only). Keep `new`/`new_phase`. | Removes a 2nd status reader; behavior-preserving. | `pytest tests/…/test_phase*.py -q`; run `phase.py status` before/after, diff output intent |
| B6 | Unify duplicated file-checks between `verify.check_required_files()` and `bootstrap.doctor()` into one helper (`include_dirs` flag). Byte-identical behavior per caller. | True duplication (both validate the same 3 core files). | `pytest tests/test_bootstrap.py tests/tools/test_verify.py -q`; `verify --all` + `bootstrap doctor` identical |

**Deferred B (not in first wave):** `worktree_mode` vs `default_worktree_mode` synonym collapse — both read in `provider_config.py:191-192`, both `false`; removing the fallback is a behavior change with low payoff. Defer to a dedicated later PR.

**Explicitly NOT consolidated (distinct responsibilities — audit agrees):** `verdict.py`, `boundary_guard.py`, `artifact_guard.py`, `status_doctor.py`, `verify.check_artifacts/check_canaries/check_status_consistency`, `frontier-audit` vs `frontier-review`. Merging these would *lose* capability or distinct gating — forbidden by the prime directive.

---

## BUCKET C — DO NOT TOUCH (core / uncertain / in-flight; may be read, behavior never changes)

- **Reference / correctness oracle:** `backtest/{reference,accounting,costs,slippage,fills,fill_models,liquidity,conservative_semantics,equity,results,engine_config,execution_config,orders,trades}.py`, **`data/build_bars.py`** (imported by `backtest/reference.py:38` — audit's delete call was WRONG).
- **Parity harness:** `backtest/{parity,parity_cases,fast_path,fast_arrays,fixtures}.py`, all `tests/no_lookahead/**`, all `-k parity` suites.
- **Resolver / identity / serial registry:** `runtime/input_resolver.py`, `features/registry.py`, `labels/registry.py`, `features/contracts.py`, `labels/contracts.py`, `core/**` (hashing/run-ids/instrument master/migrations), `materialization_registry` serial resource.
- **Governance / gates:** `governance/**`, `labels/{leakage_audit,roll_guard,alignment}.py`, `features/semantics.py`, `request_gate.py`, all `evals/canaries/**`, `tools/hooks/{canary_runner,boundary_guard,artifact_guard,secret_scan,test_tamper_guard,forbidden_pattern_guard,pre_commit,pre_push}.py`.
- **Live-status authority:** `tools/frontier/status_doctor.py`.
- **Config keys that ARE read (audit said delete — WRONG):** `lanes.<lane>.max_changed_files` (`merge_gate.py:172`), `lanes.<lane>.max_repair_attempts` (`ralph_driver.py:2478`), all `workflow2.scheduler.*` (`resolve_scheduler_config`), `trading_enabled`/`broker_enabled` (descriptive, ADR-0008).
- **Live-referenced docs/files kept:** `PROGRESS.md` (dag_scheduler), `docs/PLAN.md` (ACTIVE_CAMPAIGN), `PROJECT_STATUS.md`/`CHANGELOG.md`, the `.claude/agents/*` + hooks + `scripts/ralph/**` + `configs/**` + `evals/behaviors/**`.
- **In-flight (frozen until run close):** `features/fast/**`, `labels/fast/**`, `features/scaleout/**`, `labels/scaleout/**`, `cli/scaleout.py`, `configs/**/scaleout/**`, `docs/feature_compute_fast_path/**`.
- **Reference engines retained as oracle:** `features/engine/materialization.py`, `labels/engine.py`, `features/families/**`, `labels/families/**`.

---

## STAGED PR PLAN (one concern per PR; each CI-green before the next; pause for go/no-go between stages)

| PR | Concern | Bucket | Touches in-flight? | Risk |
|----|---------|--------|--------------------|------|
| **PR-1** | Docs: A2/A3/A4 merge→delete + B3 state-machine de-dup + B4 index; fix `docs/README.md` links | A + B | No | LOW |
| **PR-2** | Dead harness file: A1 `rm review_schema.py` | A | No | LOW |
| **PR-3** | Dead config keys: B1 + B2 (key + `REQUIRED_*_KEYS` + tests together) | B | No (control-plane edit; only dead keys) | LOW-MED |
| **PR-4** | Harness-code dedup: B5 + B6, behavior-preserving | B | No | MED |
| **PR-5+** | `src/alpha_system` optimization | — | **All Bucket C / in-flight** | **DEFERRED — no safe item exists now** |

PR-1..PR-4 touch **no** in-flight code, so they may run after **FCFP** closes even while FUTSUB resumes. The `src`/scaleout/fast re-check happens only after **both** runs close (post-close checklist below). Every PR: explicit `git add <path>`, CI green (`validate` + canaries + guards), revert SHA recorded, no `runs/**` staged.

### Post-close re-check (after FCFP **and** FUTSUB DONE) — audit, don't pre-stage
- `features/fast/**`, `labels/fast/**` — confirm parity-gated before any dedup.
- `features/scaleout/**`, `labels/scaleout/**`, `cli/scaleout.py`, `configs/**/scaleout/**` — confirm merged + green before cleanup; re-check orphaned scaleout configs once P33 closes.
- `docs/feature_compute_fast_path/**` — fold into the docs index (PR-1 follow-up).
- `worktree_mode`/`default_worktree_mode` synonym collapse (deferred B).
- `README.md` campaign-specificity → move FCFP detail to `ACTIVE_CAMPAIGN.md`.

---

## NET ASSESSMENT

Aggressive cleanup that *preserves every capability* reduces to: **4 hard-deletes, ~6 gated edits, 0 src refactors.** That is not a small-effort finding — it is the audit *confirming the system is already lean where it matters*. The biggest wins are clarity (one doc index, one state-machine source of truth, dead config keys gone) not demolition. I recommend executing PR-1→PR-4 after FCFP closes, each gated and reversible, and leaving `src` alone.

---

# PASS 2 DELTA (deep structure / ad-hoc / test / goal-alignment audit `whxf2856i`)

**Net-new hard deletes: ZERO.** Every pass-2 deletion candidate is referenced (counter-evidence below). Pass 2's value is structural-clarity docs + two reference-integrity fixes — not dead-code removal. Two thorough multi-agent passes converge on: **the repo is already lean.**

### Demotions (probe said cut → evidence says KEEP)
- `src/alpha_system/execution/` placeholder pkg — listed in `tests/unit/test_package_import_surface.py:25` (`IMPORTABLE_MODULES`); deleting breaks a live test. **KEEP.**
- `signals/contracts.py::SignalRecord` — one live importer (`tests/no_lookahead/test_contract_timestamps.py:11`). **KEEP.**
- The 4 same-basename test pairs (`test_dry_run`, `test_label_leakage_guard`, `test_label_available_ts`, `test_registry`) — distinct modules, both collected under `--import-mode=importlib`. **KEEP all 8.**
- **No test deletions. No new src deletions.**

### New SAFE-NOW items (docs only; fold into the docs PR)
- **B-P2-2** Add `configs/factors/README.md` (parity gap: `configs/features/` + `configs/labels/` have one, `factors/` doesn't).
- **B-P2-3** Expand `handoffs/README.md` (lists 3 of ~12 campaigns — the doc debt that caused the P04/P12 misplacement).
- **Structural docs** in `docs/ARCHITECTURE.md`: (1) a "Pipeline Sequence" section ordering `data→features→labels→backtest(oracle)→governance/promotion` with each src package named; (2) a Package-Tier table (Tier-1 core / Tier-2 research / Tier-3 future); (3) registry/store ownership model (`core/registry` schema+conn vs domain registries vs `Store` facade vs `governance/registry`).
- **README note**: root `/factors` + `/strategies` are researcher-output `.gitkeep` scaffolding; code is in `src/alpha_system/{factors,strategies}/`.

### New ARCHIVE item (move, never delete)
- **PR-ARCHIVE** Consolidate **closed-campaign** `handoffs/ALPHA_*` + `reviews/ALPHA_*` into `handoffs/_archive/` + `reviews/_archive/` with an index. Exclude `FEATURE_COMPUTE_FAST_PATH_V1` and FUTSUB (in-flight). Gate: link-check + `git ls-files runs` empty.

### POST-CLOSE items (after BOTH FCFP and FUTSUB reach CAMPAIGN_DONE)
- **B-P2-1** `git mv handoffs/FUTSUB-P04.md handoffs/FUTSUB-P12.md` → `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/` — these are misplaced **uniques** (subdir copies absent) and specs already point at the subdir path, so the move **repairs a dangling reference**. Defer until FUTSUB done (the resuming driver may read them).
- Rename one of the two `InstrumentMasterRecord` (`core/instrument_master.py:40` general vs `data/foundation/instruments.py:392` futures) → `FuturesInstrumentMasterRecord`. Touches src + FUTSUB-adjacent → post-close, parity-gated.
- Fix the 14 placeholder `__init__.py` docstrings that contradict real package contents → post-close (several are in-flight).

### HUMAN-GATED (no auto-change)
- `frontier.yaml:14 trading_enabled: true` — grep confirms **no `tools/` reader** (cosmetic/descriptive, per ADR-0008), so I will **leave it as-is** with its ADR note rather than flip a control-plane flag with no code effect. Surface only.

---

# CONSOLIDATED STAGED EXECUTION (autonomous once FCFP closes)

| PR | Concern | Touches in-flight? | When |
|----|---------|--------------------|------|
| **PR-A Docs delete** | merge→delete `CLI_COMMANDS_TARGET`/`RESEARCH_WORKFLOW`/`HARNESS_WORKFLOW_2`; collapse WF2 state-machine literal → pointer; one canonical doc index; fix links | No | after FCFP close |
| **PR-B Dead file** | `rm tools/frontier/review_schema.py` | No | after FCFP close |
| **PR-C Dead config keys** | lane-level `max_phase_minutes`/`max_micro_loops`/`required_checks` + `worktree_mode_recommended` (+ `REQUIRED_*_KEYS` + tests) | No (only dead keys) | after FCFP close |
| **PR-D Harness dedup** | `phase status`→`status_doctor`; unify `verify`/`bootstrap` file-checks (behavior-preserving) | No | after FCFP close |
| **PR-E Clarity docs** | ARCHITECTURE pipeline+tier+ownership sections; README scaffolding note; `configs/factors/README.md`; `handoffs/README.md` expansion | No | after FCFP close |
| **PR-ARCHIVE** | closed-campaign handoffs/reviews → `_archive/` + index | No (excludes live campaigns) | after FCFP close |
| **PR-POST** | FUTSUB-P04/P12 move; `InstrumentMasterRecord` rename; placeholder docstrings | **Yes / src** | after BOTH runs close, parity-gated |

Each PR: one concern, explicit `git add`, CI green (`validate` + canaries + guards), revert SHA recorded, `uncertain ⇒ keep` absolute. The DO-NOT-TOUCH floor (oracle, parity, resolver/identity, registry, governance, in-flight) is frozen across all of it.

**Net across both audits:** ~4 hard deletes + ~6 gated harness/config edits + ~5 clarity docs + 1 archive move + 3 post-close src touches. No capability lost. The biggest win is *legibility*, not demolition.
