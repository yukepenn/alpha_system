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
| **PR-3 (this)** | Clarity docs: expand `handoffs/README.md` to index all campaigns + flag the FUTSUB-P04/P12 misplacement; add `configs/factors/README.md` (parity with features/labels); this summary | — |

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

- **B1/B2 — remove dead lane-level config keys + `worktree_mode_recommended`.**
  Verified dead (only `config.py` validation reads them) and CI-gated, but they edit
  the live `frontier.yaml` / `config.py` control plane that the imminent aggressive
  FUTSUB relaunch uses. Tiny benefit, non-zero timing risk → deferred to a separate
  batch after the relaunch settles.

- **B5/B6 — harness dedup (`phase status`→`status_doctor`; unify verify/bootstrap
  file-checks).** Behavior-preserving but control-plane code; same rationale —
  deferred to a post-relaunch batch.

- **PR-POST — FUTSUB-adjacent `src` touches** (`git mv handoffs/FUTSUB-P04/P12` into
  the FUTSUB subdir; `InstrumentMasterRecord` rename; in-flight placeholder docstrings).
  **Gated on FUTSUB being done** precisely to avoid colliding with in-flight FUTSUB
  work — and FUTSUB is paused mid-pivot, the exact collision the gate guards against.
  Held until the aggressive approach's scope is known.

## Net

Two clean PRs merged (docs consolidation + one dead file) plus clarity-doc fixes.
The audit's broader conclusion holds and is reinforced: **the repo is already lean
where it matters.** The remaining plan items are either control-plane edits not worth
touching immediately before a relaunch, a reversible archive move with newly-found
live-test references, or FUTSUB-collision items that must wait for the run to close.
`src/alpha_system` (oracle, parity, resolver/identity, registry, governance,
in-flight fast/scaleout) was not touched.
