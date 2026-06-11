# FRONTIER_ADOPTION — what's worth adopting for a one-operator multi-agent quant harness (2026-06-10)

Every row grounded in files read this session. "You already have the frontier
version" is used where true.

## Orchestration & harness techniques

| Technique | Verdict | Reason / trigger |
|---|---|---|
| Code-graph / impact-analysis index | **ADOPT WHEN** ≥2 cross-module impact errors per campaign, hub-module refactor campaign, or >2,500 py files | Map+grep+1M context covers today's topology; lightest form when triggered = `system_map.py --graph` package-level import edges (~100 lines, rides the existing drift test). Full reasoning in SYSTEM_LEGIBILITY_PLAN §2. |
| Initializer + isolated parallel workers, serial merge | **ALREADY FRONTIER** | `dag_wave` scheduler + worktree isolation + serial merge queue + auto-resume IS this pattern (`tools/frontier/dag_scheduler.py`, `merge_queue.py`). Three live campaigns ran on it. Don't add a second orchestration layer. |
| Parallel map-reduce over the codebase (audit fan-out) | **ALREADY AVAILABLE** | Claude-side subagents do this on demand (this plan's own research used 4 parallel explorers). No standing machinery needed; standing machinery would rot between rare audits. |
| Spec/plan-as-artifact | **ALREADY FRONTIER** | Campaign contracts (GOAL/PHASE_PLAN/ACCEPTANCE/RISK_REGISTER/RUNBOOK) + per-phase generated specs + ADRs. Gap intentionally left open: `spec_schema.py` sections are unenforced — skip until a malformed spec survives review. |
| Evals-as-gates | **ALREADY FRONTIER (plumbing)** | Canary gate is a required check (pre-push + CI; `canary_runner.py`); heldout behaviors exist (`evals/behaviors/`). The gap is statistical, not plumbing — see quant table. |
| Structured handoffs / machine-parseable verdicts | **ADOPT WHEN** a second parse failure occurs | `verdict.py` is already Markdown-bold-tolerant with ambiguity→BLOCKED fail-closed; verdict.json is emitted from the parse. Next step if it fails again: require a fenced JSON block in the reviewer contract instead of a VERDICT line. Don't pay the migration before the second incident. |
| Auto doc/map generation with drift guard | **ADOPTED NOW** | `tools/frontier/system_map.py` + CI drift test. Stop there: generating more docs than the one guaranteed-read page creates churn without readers. |
| Persistent agent memory, injected at decision time | **ADOPTED NOW** | Lessons now injected into all 5 WF2 prompts; corrections live in auto-loaded rules. Skip retrieval ranking until lessons.md outgrows its 12k cap twice. |
| Real cost accounting / budget gate | **ADOPT WHEN** provider adapters expose real cost | `max_estimated_usd: 50` is documented-inert (cost_usd hardcoded 0.0). Time ceilings + supervision are the effective gate today. Hand-estimating token costs would be maintenance with false precision. |

## Quant-rigor capability gaps (the ones that matter)

These are capability gaps, not cleanup — collected as `RESEARCH_RIGOR_V1` in
`docs/NEXT_CAMPAIGN_CANDIDATES.md`, to be implemented via spec'd Yellow phases.

| Capability | Status here | Verdict |
|---|---|---|
| Trial ledger / full trial accounting | **ALREADY HAVE** — `governance/trial_ledger.py` (statuses, contamination flags, code/config hashes) + variant budgets in `study_spec.py` | Keep; it's the substrate for the next row. |
| Multiple-testing correction (deflated Sharpe / SPA) | **MISSING** — ledger counts trials but nothing adjusts significance for the count | **ADOPT NOW** (top rigor priority). Pure post-processing of existing ledger + reference-engine outputs; promotion gate consumes it. No new PnL truth. |
| Sealed holdout the searcher cannot read | **MISSING** — walk-forward + purge/embargo + locked-partition *metadata* exist (`experiments/splits.py`, `datasets.py`), but nothing physically refuses resolution | **ADOPT NOW**. Enforce in `runtime/input_resolver.py`: locked partitions fail closed without armed governance metadata; unlocks ledgered. Cheap because the metadata already exists. |
| Planted-fake-alpha negative control (end-to-end) | **PARTIAL** — canaries (future_shift, permuted_labels, optimistic_fill, random_target) test guard plumbing, not pipeline outcome | **ADOPT NOW**. Inject a known-spurious signal through the full study pipeline; assert promotion gate REJECTs. Converts the canary suite from "guards fire" to "the system as a whole rejects noise". |
| Crowding / correlation gate | **PARTIAL** — `research/correlation.py` computes correlation-to-existing-factors but it's informational only | **ADOPT NOW** (cheapest of the four). Promotion gate takes a max-correlation threshold as a mechanical input. |
| Decay / regime monitoring over time | **PARTIAL** — per-run decay diagnostics exist; nothing persists across studies | **ADOPT WHEN** the first non-REJECT candidates exist (currently 0 CANDIDATE / 0 WATCH — nothing to monitor yet). |
| Claims/language enforcement | **ALREADY FRONTIER** — `governance/claims.py` (503 lines, fail-closed) enforces both language policies in code | Nothing to do. Rare. |

## Ordering opinion

Run `RESEARCH_RIGOR_V1` **before** rerunning the 6 INCONCLUSIVE Core-Pilot
studies in FUTSUB's tail: the rerun's conclusions are only as trustworthy as the
multiple-testing accounting and holdout seal behind them, and the planted-fake-
alpha control is the cheapest way to validate the whole evidence pipeline before
trusting any future CANDIDATE.

## The over-engineering check (Part 4, blunt)

- **Stop adding agents.** Seven definitions, all live-wired; the three in the
  WF2 loop carry the load. An eighth agent has no unclaimed job.
- **Stop adding skills.** Six cover the real workflows. New recurring corrections
  go into `rules/` or `lessons.md`, not new skills — a skill nobody invokes is rot.
- **No code-graph index yet** — trigger above. No vector memory. No MCP servers
  for navigation.
- **No spec/handoff schema gates yet** — the semantic reviewer + done-check
  already read these documents with more context than a schema check would have.
- **Don't hand-wire cost tracking** — wait for real provider cost.
- The harness itself is at the right size: the audit found exactly two genuine
  legibility defects (status rot in orientation docs; write-only lessons), both
  now fixed with ~350 lines total. The remaining real gap is **statistical
  rigor**, and it deserves a campaign, not more harness.
