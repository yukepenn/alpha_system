# Active Campaign

Project: `alpha_system`

Campaign: `campaigns/ALPHA_IDEA_TO_VERDICT_LOOP_V0`
Workflow: `workflow2`

> **Live phase / run / pass-count: do not read it here.** This committed pointer
> lags the running campaign and intentionally states no `Current phase` / `N/M`
> count — baking a number into committed prose is the exact live-status rot the
> anti-rot guard forbids. The single source of truth is
> `python tools/frontier/status_doctor.py` (+ `runs/<run_id>/state.json`). Ralph
> updates the live state every loop; between runs the coordinator keeps only this
> pointer's *campaign identity* synced to post-run truth.

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

Research-state context (NOT live status — verify via `status_doctor` + the research
ledger `decisions/POWERED_DISCOVERY_BATCH_V0/RESEARCH_TRUTH_RECONCILIATION.md`):
simple per-instrument IC is a confirmed cross-partition NULL and conditional-setup
regime mining is WELL_POWERED_NULL — survivor gate remains 0. BBO order-flow
microstructure is the ready-to-author next probe (zero new materialization). All
downstream factory modules stay trigger-gated behind the survivor gate.
