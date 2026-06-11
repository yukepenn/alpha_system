# SYSTEM_LEGIBILITY_PLAN — how Claude and Codex "know" alpha_system (2026-06-10)

Everything in §1–§2 marked BUILT was executed in this pass; grounding for every
claim is a real file read this session.

## 1. THE MAP — BUILT

**Problem proven, not hypothesized:** the hand-written `docs/AGENT_CONTEXT_MAP.md`
claimed "Next campaign: ALPHA_FEATURE_LABEL_FOUNDATION_V1 (not yet authored)" —
five campaigns stale. A hand-maintained map rots within one campaign.

**Design (as built):**
- `docs/SYSTEM_MAP.md` is **generated** by `tools/frontier/system_map.py` from the
  repo itself. Content is deliberately structure-level so it churns only when the
  system's shape changes: 18 load-bearing anchors (reference engine, parity
  harness, feature/label registries, value store, input resolver, promotion gate,
  trial ledger, claims guard, canary harness, splits, CLI, Ralph driver,
  status_doctor, verify, hooks, canary gate), the do-not-touch set, the 19 src
  packages (purpose pulled from real `__init__` docstrings), lanes+models from
  `frontier.yaml`, the `justfile` command surface, and the canary list.
- **Drift guard:** `tests/tools/test_system_map.py` regenerates and compares —
  CI's required `validate` check fails on any drift. A missing anchor is a hard
  generation error (relocations force a conscious ANCHORS edit, never silent rot).
  Regen is one command: `just system-map`.
- **Status is structurally excluded.** The map's header says live status comes
  only from `status_doctor`. Same fix applied to `AGENT_CONTEXT_MAP.md`,
  `NEXT_CAMPAIGN_CANDIDATES.md`: orientation docs now carry zero campaign status.
- Entry chain after this pass: `CRITICAL.md` (invariants + live-truth pointer) →
  `SYSTEM_MAP.md` (structure, generated) → `status_doctor` (live state) →
  `docs/README.md` (deep docs on demand).

**Known weakness + cheap fix:** most package `__init__` docstrings say
"placeholder", so the generated Purpose column is thin. Improving ~19 one-line
docstrings upgrades the map automatically — a good Green-lane micro-phase.

## 2. CODE GRAPH / SEMANTIC INDEX — SKIP, with trigger

**Verdict: SKIP now.** Honest assessment for THIS repo:
- Scale: 1,051 py files / ~158k LOC, but topology is hub-and-spoke around ~6
  modules (registries, resolver, reference engine, value store) that the map now
  names. Grep + the map + 1M context handles navigation; the explorations for
  this plan answered deep cross-module questions in minutes without an index.
- The historical error pattern here is **not** impact-analysis misses. Review
  findings across 5 campaigns were env/config/convention issues (`__all__`
  conformance, pytest importlib, env-var leakage), which an import graph would
  not have caught.
- Cost side: an LSP/SCIP/MCP index is a service to keep healthy, version, and
  teach two different agents to query. That's real maintenance against a
  navigation problem the map already cut.

**Adopt when (any one):**
1. Two or more review/repair findings in a single campaign are "edited X without
   updating caller Y" cross-module impact errors;
2. A refactor campaign renames hub modules (e.g., a broad InstrumentMaster
   restructuring beyond the pending one-class rename);
3. Repo exceeds ~2,500 py files or a second source root appears.

**Lightest viable form when triggered:** extend `system_map.py` with `--graph`
emitting package-level import edges (AST walk, JSON + a markdown table). It rides
the existing drift guard, costs ~100 lines, needs no server, and both providers
consume it as a file. Do NOT start with symbol-level SCIP/LSP; package-level
answers "what depends on the resolver" which is the actual question asked here.

## 3. SHARED KNOWLEDGE ACROSS PROVIDERS — BUILT (no new store)

Claude and Codex now read the **same three artifacts**, all updated inside the
normal loop, none requiring a separate chore:

| Layer | Artifact | How it stays current |
|---|---|---|
| Constitution | `AGENTS.md` (Codex reads natively; CLAUDE.md imports it) | Already the governed policy file |
| Structure | `docs/SYSTEM_MAP.md` (generated) | CI drift test; `just system-map` |
| Experience | `.claude/skills/project-skill/lessons.md` | Written at closeout (existing habit); now **injected into all five WF2 provider prompts** — spec-gen, executor, review, done-check, repair — via `lessons_prompt_section()`, so Codex receives Claude-curated lessons without a Codex-side copy |

Deliberately NOT built: a second lessons store under `.codex/`, an interface doc
generator for the reference engine (docs/CONTRACTS.md is hand-maintained but
contract-stable — it documents schema primitives that change via ADR, not per
phase), or any sync mechanism. One file per layer, one writer per file.

## 4. MEMORY WIRING — BUILT

**Assessment:** the stores existed and were healthy (`decisions/` = 9 ADRs;
`lessons.md` = 218 lines of validated, file:line-cited lessons) but lessons were
**write-only**: zero code paths loaded them; Ralph's prompts listed AGENTS.md,
CLAUDE.md, frontier.yaml, campaign files — never lessons. Hard-won corrections
survived across sessions only when the human re-supplied them.

**Wiring (as built):**
- Lessons → all five WF2 prompts (12k-char compaction cap, ~3k tokens/call; the
  highest-value tokens in the prompt). Framed explicitly as *data, not policy*
  to respect the headless trust boundary; AGENTS/frontier override; missing file
  never blocks a run. Pinned by `tests/tools/test_ralph_lessons.py` so the wiring
  cannot silently regress.
- Recurring human corrections → `.claude/rules/discipline.md` (auto-loaded each
  Claude session). Rules are for *behavioral* corrections; lessons are for
  *operational* run knowledge; ADRs for *architectural* decisions. Three stores,
  three distinct moments of load, no overlap.
- Convention to keep injection cheap: prune `lessons.md` at campaign closeout
  (the existing project-skill step) — retire lessons that got encoded into code
  or guards. Budget: stay under the 12k cap so nothing is ever truncated.

**SKIP:** retrieval/relevance ranking ("load lessons when relevant"). At 218
lines, loading everything beats building a ranker. Trigger to revisit: lessons.md
exceeding the 12k cap twice after honest pruning.
