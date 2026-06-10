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
| **PR-5 (B5, this)** | `phase.py status` → delegate to `status_doctor` | The old subcommand dumped the *lagging* `ACTIVE_CAMPAIGN.md` pointer (contradicting the live-status-authority rule); now delegates to the single authoritative reader. CLI-only, no test breaks, canaries pass. |

## Deliberately NOT executed (with reasons — these are the honest deltas from the plan)

- **B3 — collapse the WF2 state-machine literal in `AGENTS.md`/`CLAUDE.md`.**
  Those are the constitution files agents read directly; an inline state machine is
  useful at-a-glance. *Uncertain ⇒ keep.*

- **PR-ARCHIVE — move closed-campaign handoffs/reviews into `_archive/`.**
  **Stopped on counter-evidence:** the plan's claim that closed-campaign artifacts
  are referenced only by closed campaigns is **wrong** for two of them —
  `ALPHA_RESEARCH_GOVERNANCE_MVP` (live `tests/unit/governance/test_reviewer_verdict.py`,
  `tests/integration/governance/test_end_to_end_dry_run.py`) and `ALPHA_SYSTEM_V1`
  (live `tests/tools/test_artifact_guard.py`, `tests/unit/test_promotion_decision_schema.py`,
  `tests/integration/test_registry_all_tables_exercised.py`). Moving them would break
  live tests. The move is reversible and high-churn; deferred until it can be done
  deliberately (and tests updated) rather than during a pivot.

- **B6 — unify `verify.check_required_files()` and `bootstrap.doctor()` file checks.**
  **Evaluated → skipped.** The plan's premise ("both validate the same 3 core files")
  is **false**: `verify` checks `REQUIRED_HARNESS_FILES` (files) while `bootstrap.doctor`
  checks a *different* set including **directories** (campaigns/specs/handoffs/reviews)
  with a different message. The only shared code is a one-line list comprehension over
  *different* inputs; a unifying `include_dirs` helper would add parametrization for zero
  real dedup. *Uncertain ⇒ keep.*

- **PR-POST — FUTSUB-adjacent `src` touches** (`git mv handoffs/FUTSUB-P04/P12` into
  the FUTSUB subdir; `InstrumentMasterRecord` rename; in-flight placeholder docstrings).
  **Gated on FUTSUB being done** precisely to avoid colliding with in-flight FUTSUB
  work — and FUTSUB is paused mid-pivot, the exact collision the gate guards against.
  Held until the aggressive approach's scope is known.

## Net

Five PRs merged: docs consolidation (#314), dead `review_schema.py` (#315), clarity
docs (#316), dead config keys B1/B2 (#317), and `phase status` delegation B5 (PR-5).
B6 was evaluated and **correctly skipped** (its dedup premise was false). The audit's
broader conclusion holds and is reinforced: **the repo is already lean where it matters.**
The only remaining items are the **archive move** (reversible, but with newly-found
live-test references — do it deliberately, not during a pivot) and the **FUTSUB-collision
`src` touches (PR-POST)**, which must wait for the FUTSUB run to close.
`src/alpha_system` (oracle, parity, resolver/identity, registry, governance,
in-flight fast/scaleout) was not touched.
