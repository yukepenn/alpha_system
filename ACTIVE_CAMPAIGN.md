# Active Campaign

Project: `alpha_system`

Campaign: `campaigns/ALPHA_IDEA_TO_VERDICT_LOOP_V0`
Workflow: `workflow2`
Run: `launching` — live `frontier-run-parallel` build (IVL-P00..P06)
Status: `starting` — assembling the researcher idea→verdict product loop

Current phase: `IVL-P00` — Role-Unification ADR + Canonical Idea-Object Schema Map
Last completed phase: `none`
Last completed status: `none`
Passing phases: `0/7`

## What this campaign is (verify live via `python tools/frontier/status_doctor.py`)

`ALPHA_IDEA_TO_VERDICT_LOOP_V0` assembles the (already-trustworthy) governance/research
backend into ONE researcher-facing **product loop**: any idea (PA / VWAP / IC / event /
cross-market) → one canonical object → quick screen on a small EXISTING slice → testability
gate BEFORE any real metric → human-readable governed verdict → memory. This is **ASSEMBLY +
CONSOLIDATION over an intact reuse spine** — no new mechanism, feature, label, data, or
downstream module.

Canonical idea-object hierarchy: `idea.yaml` → **HypothesisCard → AlphaSpec (front-door
trunk)** → MechanismCard + optional SetupSpec (emitted sub-objects, linked at the orchestration
layer — frozen content-hashed schemas are NOT mutated) → StudySpec → verdict → memory. The
optional `study_kind` discriminator lives only on a new IdeaDraft intake wrapper. Track-A
doc-convention cards migrate into the canonical line (migrate-then-retire); no second card class.

Phases (sequential, IVL-P00→P06): P00 role ADR + schema map · P01 `alpha idea validate` intake ·
P02 executable testability gate + `alpha idea gate` (≥2-class non-degeneracy = the DK Track B fix) ·
P03 fast exploratory lane bridge (`fast_probe` over an existing materialized slice) · P04 verdict
`REPORT.md` renderer · P05 memory wiring + `alpha idea run` · P06 dogfood DK Track B through the loop.

Lanes GREEN/YELLOW only. KEEP the entire trust spine + test suite (reuse, never rebuild). No
downstream module (Mining V2 / FactorLibrary / AlphaBook / Sandbox / PA grammar), no universe
expansion, no paid data, no broker/paper/live — all remain trigger-gated. Allowed verdicts only:
REJECT / DATA_GAP / INCONCLUSIVE / WATCH / CANDIDATE_RESEARCH. No alpha/profitability/tradability
claim. `runs/**` local-only; explicit staging only.

Prior: DIFFERENTIATED_KILLSHOT_V1 COMPLETE 6/6, **0 survivors** (Track A clean null; Track B
substrate-gap DATA_GAP — now the IVL-P06 dogfood, not a standalone campaign).

Ralph updates this pointer through reviewed phase commits during the live run; between runs the
coordinator keeps it synced to post-run truth.
