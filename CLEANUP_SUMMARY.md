# CLEANUP_SUMMARY.md

Execution record for the cleanup defined in `CLEANUP_PLAN.md`. Run **2026-06-10**
by the coordinator while FUTSUB was paused for a more aggressive approach (so this
was a safe, no-active-driver window for `main` edits). Prime directive honored:
**preserve every capability; delete only what is proven unreferenced; uncertain ⇒ keep.**

## Executed (merged to main)

| PR | Concern | Result |
|----|---------|--------|
| **#314 (PR-1)** | Docs: fold + delete `CLI_COMMANDS_TARGET.md`, `RESEARCH_WORKFLOW.md`, `HARNESS_WORKFLOW_2.md`; fix `docs/README.md` links | Merged. Unique content folded into `CLI_REFERENCE.md` / `RESEARCHER_GUIDE.md`; `HARNESS_WORKFLOW_2.md` was fully duplicated by `AGENTS.md`. Zero live refs re-verified on current main; closed `ALPHA_SYSTEM_V1` history left immutable. |
| **#315 (PR-2)** | Remove dead `tools/frontier/review_schema.py` | Merged. Zero importers re-verified; `verdict.py` is the live authority; 284 verdict/review/ralph/config tests pass. |
| **#316 (PR-3)** | Clarity docs: expand `handoffs/README.md` to index all campaigns + flag the FUTSUB-P04/P12 misplacement; add `configs/factors/README.md` (parity with features/labels); this summary | Merged. |
| **#317 (PR-4, B1/B2)** | Remove dead lane-level config keys (`max_micro_loops`, `max_phase_minutes`, `required_checks`) + `workflow2.worktree_mode_recommended` | Merged. Keys + `REQUIRED_*_KEYS` + the non-obvious per-lane type-validation + fixtures removed; top-level live copies untouched; `validate_config` clean, 81 tests + canaries pass. |
| **PR-5 (B5)** | `phase.py status` → delegate to `status_doctor` | Merged. The old subcommand dumped the *lagging* `ACTIVE_CAMPAIGN.md` pointer (contradicting the live-status-authority rule); now delegates to the single authoritative reader. CLI-only, no test breaks, canaries pass. |
| **#319 (PR-7, B-P2-1)** | `git mv` FUTSUB-P04/P12 into the campaign subdir | Merged. Relocated the two misplaced FUTSUB handoffs into `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/` (history preserved). No committed ref to the old top-level path; user confirmed FUTSUB going fresh → no resume collision. |

## Deliberately NOT executed (with reasons — these are the honest deltas from the plan)

- **B3 — collapse the WF2 state-machine literal in `AGENTS.md`/`CLAUDE.md`.**
  Those are the constitution files agents read directly; an inline state machine is
  useful at-a-glance. *Uncertain ⇒ keep.*

- **PR-ARCHIVE — move closed-campaign handoffs/reviews into `_archive/`.**
  **Attempted, then abandoned as net-negative.** The plan assumed a small "link-check
  gate"; the reality is the handoffs/reviews are referenced by **62 committed files** —
  every archived campaign's contract (`campaign.yaml`, ACCEPTANCE/PHASE_PLAN/RUNBOOK/
  CLOSEOUT), ~15 `docs/`, research evidence, and evals. Moving them breaks all 62; the
  only "fix" is rewriting 30+ **immutable** closed-campaign contracts, which the prime
  directive forbids. The tidiness gain (a shorter top-level listing) is dwarfed by
  shattering the navigability of the whole historical record. The move was made on a
  branch, the breakage measured, then fully reverted. A future "better way" is a
  tooling/index or redirect approach — not a physical move. (The 5 live *test* refs
  are fine — they are pattern/data fixtures, not existence checks — but the 62-file
  contract/doc web is the blocker.)

- **B6 — unify `verify.check_required_files()` and `bootstrap.doctor()` file checks.**
  **Evaluated → skipped.** The plan's premise ("both validate the same 3 core files")
  is **false**: `verify` checks `REQUIRED_HARNESS_FILES` (files) while `bootstrap.doctor`
  checks a *different* set including **directories** (campaigns/specs/handoffs/reviews)
  with a different message. The only shared code is a one-line list comprehension over
  *different* inputs; a unifying `include_dirs` helper would add parametrization for zero
  real dedup. *Uncertain ⇒ keep.*

- **PR-POST — remaining FUTSUB-adjacent `src` touches.** The handoff relocation
  (FUTSUB-P04/P12) is now **done** (#319). Still held: the **`InstrumentMasterRecord`
  rename** — it renames a core `src` identity type the materialization path uses, so it
  must be parity-gated and done when the aggressive FUTSUB run is not active — and the
  in-flight placeholder docstrings (several sit in frozen fast/scaleout code).

## Net

Six PRs merged: docs consolidation (#314), dead `review_schema.py` (#315), clarity
docs (#316), dead config keys B1/B2 (#317), `phase status` delegation B5 (#318), and
the FUTSUB-P04/P12 handoff relocation (#319). B6 was **correctly skipped** (dedup
premise false), and the **archive move was attempted and reverted** as net-negative
(62-file reference web). The audit's broader conclusion holds and is reinforced:
**the repo is already lean where it matters** — almost every "cleanup" target turned
out to be load-bearing or densely referenced. The only remaining item is the
**`InstrumentMasterRecord` rename** (core `src`, parity-gate when FUTSUB is idle).
`src/alpha_system` (oracle, parity, resolver/identity, registry, governance,
in-flight fast/scaleout) was not touched.
