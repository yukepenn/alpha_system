# PATTERNS_TO_CODIFY — interaction-history mining (2026-06-10)

Metric: net time saved = (time saved per occurrence × expected frequency) − maintenance.
Status column: **BUILT** = executed in this pass (PR referenced in CLEANUP/PR log),
**CANDIDATE** = authored as campaign candidate, **SKIP** = deliberately not codified.

## Ranked table

| # | Pattern | How it shows up | Artifact | Est. saving × freq | Maintenance | Status |
|---|---------|-----------------|----------|--------------------|-------------|--------|
| 1 | Hard-won run lessons get re-learned | Every live WF2 run re-hits known failure modes (FRONTIER_* env false negative, head-mismatch resume, pytest importlib, `__all__` conformance, reviews promotion). Lessons were written to `lessons.md` but **no prompt ever loaded them** — write-only memory. | `lessons_prompt_section()` in `tools/frontier/ralph_driver.py`: lessons injected into all 5 provider prompts (spec-gen, executor, review, done-check, repair), framed as data-not-policy, 12k-char cap, fail-open. Pinned by `tests/tools/test_ralph_lessons.py`. | 30–120 min × every run (repair loops avoided) | ~0 (file already maintained at closeout) | **BUILT** |
| 2 | Agents re-discover repo structure every session | Each session starts with spelunking for the reference engine, registries, gates, commands; the hand-written map (`AGENT_CONTEXT_MAP.md`) had rotted 5 campaigns stale ("FLF not yet authored"). | `tools/frontier/system_map.py` → generated `docs/SYSTEM_MAP.md` (anchors, do-not-touch set, packages, lanes/models, commands, canaries) + CI drift test `tests/tools/test_system_map.py` + `just system-map`. Anchor relocation = hard generation error. | 5–15 min × every session, both providers | One ANCHORS list edit per relocation (test forces it) | **BUILT** |
| 3 | Recurring corrections I keep giving Claude | "Don't trust an audit claim, re-verify" (fabricated README finding; the 62-file archive-move reversal), "test before apply" (caught random_target canary, spurious `--strict`), "uncertain ⇒ keep", "no silent aggressive changes", "ask before FUTSUB". | `.claude/rules/discipline.md` — auto-loaded into every Claude session (rules dir is injected into the system prompt). One home, never said again. | 5–20 min + error risk × weekly | ~0; prune when a rule stops being true | **BUILT** |
| 4 | Status-pointer rot poisons orientation docs | `AGENT_CONTEXT_MAP.md`, `NEXT_CAMPAIGN_CANDIDATES.md`, `docs/README.md` all carried stale "current/next campaign" prose. | De-rot: status content removed from orientation docs, replaced with pointers to `status_doctor` / `ACTIVE_CAMPAIGN.md` / generated map. Convention: **orientation docs carry zero campaign status**. | 10–30 min × per campaign (mis-orientation avoided) | ~0 | **BUILT** |
| 5 | "Review this for overfit/leakage" has no statistical teeth | Reviewer + canaries check plumbing (lookahead, label leakage, optimistic fill) but nothing corrects for multiple testing, no sealed holdout, no end-to-end fake-alpha control, crowding informational-only. | `RESEARCH_RIGOR_V1` candidate in `docs/NEXT_CAMPAIGN_CANDIDATES.md` (deflated-Sharpe from trial ledger, resolver-enforced sealed holdout, planted-fake-alpha canary, mechanical crowding gate, decay persistence). Implementation via spec'd Yellow campaign — Codex executes, not inline edits. | Prevents the worst loss possible: a false CANDIDATE | Owned by campaign | **CANDIDATE** |
| 6 | "Where are we?" reconciliation | Asked at the start of most sessions. | Already frontier-grade: `status_doctor.py` + `just agent-preflight`. Nothing new needed. | — | — | **SKIP** (exists) |
| 7 | Campaign author→mock→live→closeout loop | Same shape 6 campaigns running. | Covered by `frontier-campaign` / `frontier-spec` / `frontier-ralph` skills + memory. | — | — | **SKIP** (exists) |
| 8 | Verdict/done-check text scraping fragility | One real incident (AGENT-P16 Markdown-bold false negative). | Parser already hardened (`verdict.py` `_VERDICT_WRAP`, ambiguity→BLOCKED). | — | — | **SKIP** until a second parse failure; then switch reviewer contract to a fenced JSON block |

## Explicitly NOT worth codifying

- **A "repo cleanup" skill** — cleanup is rare, judgment-heavy, and the last campaign's lesson was that the biggest planned cleanup was net-negative. A skill would encode the wrong instinct.
- **Spec-section enforcement gate** (`spec_schema.py` is currently unenforced) — specs are generated from a prompt that lists the sections; no malformed spec has ever slipped through review. Trigger to revisit: the first one that does.
- **Handoff schema validation** — the semantic done-check already reads the handoff with full context; a schema check would catch only what the done-check already catches. Trigger: a dishonest handoff surviving done-check.
- **More generated docs beyond SYSTEM_MAP** — 74 docs already exist; generating more creates churn without a reader. The map is the one page with a guaranteed reader (every session).
- **Memory MCP / vector store** — at one-operator scale, `lessons.md` (now injected) + Claude auto-memory + `decisions/` cover it. A retrieval layer adds infra to maintain with no recall problem to solve.
- **New slash commands for status/preflight** — `just` recipes are already the command surface both providers share; duplicating them as skills creates two sources of truth.
- **Hand-wiring the cost ledger** — real provider cost APIs aren't plumbed; time ceilings (`max_run_minutes`/`max_phase_minutes`) + supervision are the effective gate. Arm `max_estimated_usd` only when provider adapters return real cost.

## Disciplines codified (1c)

All three "saved us" disciplines now live in `.claude/rules/discipline.md` (auto-loaded):
test-before-apply (random_target / `--strict` saves), verify-before-believing
(fabricated README, archive-move reversal), uncertain⇒keep. The self-flagging
secret scan needs no change — it already fails closed in `tools/hooks/pre_commit.py`.
