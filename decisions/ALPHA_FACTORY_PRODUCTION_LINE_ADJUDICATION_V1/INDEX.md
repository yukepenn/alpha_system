# ALPHA_FACTORY_PRODUCTION_LINE_ADJUDICATION_V1

Research-only governance/decision bundle. No alpha, profitability, tradability, or
production claims appear or are implied. Diagnostics and gates decide outcomes; priors
do not. These are INTENT/contract documents and lag live run status — for the in-flight
phase read `runs/<run_id>/state.json` or run `python tools/frontier/status_doctor.py`.

## Purpose

Post-DK (two fired kill-shots, **0 survivors**) adjudication and charter of the *generic*
alpha factory production line — Idea → MechanismCard/SetupSpec → REUSE/duplicate check →
feature/label/path-label discovery → testability gate → EXPLORATORY vs TRUSTED lane →
diagnostics/probe → VariantLedger/TrialLedger/surrogate-FDR/power → verdict → rejected or
survivor memory. It does **not** authorize building any downstream factory module; those
remain trigger-gated behind the survivor gate (currently 0).

## Artifacts (a co-authored bundle — read together)

| File | What it decides |
|---|---|
| [`POST_DK_ADJUDICATION.md`](POST_DK_ADJUDICATION.md) | What DK ruled out (Track A calendar/flow main-effect context = well-powered clean null, 4× REJECT), what remains unanswered (context≠trigger on a non-degenerate path-label slice — never tested; roll_week DATA_GAP), and why (the single-class degenerate slice). |
| [`FACTORY_LINE_CHARTER.md`](FACTORY_LINE_CHARTER.md) | The end-to-end production line, each stage mapped to its LIVE repo component (file:line) or a GAP + smallest REUSE-MAP upgrade; the EXPLORATORY/TRUSTED lane policy; and the survivor-gated no-build table. |
| [`IDEA_INTAKE_SCHEMA.md`](IDEA_INTAKE_SCHEMA.md) | The unified MechanismCard/SetupSpec intake checklist + the Track-A/Track-B card-schema reconciliation (single card class + shape discriminator; no second card class). |
| [`TESTABILITY_GATE.md`](TESTABILITY_GATE.md) | The pre-probe precondition that the DK degeneracy motivates — feature/label/path-label substrate-ready, ≥2-class non-degeneracy, N_eff-vs-MDE, surrogate-FDR ZERO_PASS_MET — turning DATA_GAP into an explicit *pre-test* verdict. |
| [`NEXT_SHOT_SELECTION_RULE.md`](NEXT_SHOT_SELECTION_RULE.md) | How to rank MechanismCards for the next narrow shot (ES/NQ/RTY existing data only); position 0 is fixed = the Track B gap-closure. |

## Provenance & trust calibration

Authored by a repo-grounded **war council** (16 agents: 5 ground readers mapping each
production-line stage to live code, 5 doc-writers, 6 adversarial critics incl. a cross-doc
coherence critic). Every per-doc and the coherence critic returned **PASS_WITH_FIXES** (no
REVISE / no blockers).

- **Two MAJOR issues were verified against live code and fixed**: (1) the `librarian.py`
  citation path (corrected to `src/alpha_system/agent_factory/roles/librarian.py`);
  (2) a cross-doc mismatch in the "exhausted shapes" example (the four *scored* Track A
  REJECTs are day_of_week / opex / month_end / open_close_auction_flow — `quarter_end` was
  a declared flag but not a separately-scored mechanism).
- **Citation precision caveat:** `file:line` anchors were adversarially spot-checked and are
  accurate at the symbol level (the function/class names are verified correct), but some
  line-number anchors may drift by a few lines as code changes — treat the **symbol name** as
  the durable anchor and grep if a line number does not match.

These are decisions, not live status. The compass (`docs/OPERATING_COMPASS_V4.md`) and
`AGENTS.md` remain the binding policy; this bundle is consistent with both.
