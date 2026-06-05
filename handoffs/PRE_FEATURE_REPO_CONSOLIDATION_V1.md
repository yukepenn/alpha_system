# PRE_FEATURE_REPO_CONSOLIDATION_V1 — Handoff

**Workflow 1.** Pre-Feature/Label repo consolidation so `ALPHA_FEATURE_LABEL_FOUNDATION_V1`
starts from a clean, agent-navigable, non-contradictory baseline. **Consolidation,
not expansion.** No feature/label/alpha code, no data pull, no risky rewrite.

Branch `task/pre-feature-consolidation-v1`. Executed after the Databento Phase B
work merged to `main` (PR #107, `703a502`). Almost entirely docs/navigation; the
only product-code change is one behavior-preserving provider-boundary extraction.

## Commits (logical patches)

| Patch | Commit | Summary |
| --- | --- | --- |
| P1 | `4bfce58` | Reconcile status/source-of-truth docs for the dual-provider data foundation; archive 2 stub duplicates; L2 design-only banners. |
| P2 | `a832afd` | Add `docs/AGENT_CONTEXT_MAP.md` + `docs/README.md`; expand campaigns/decisions/handoffs/specs READMEs into indexes; de-dup stray `handoffs/DATA-P21.md`. |
| P3 | `206e185` | Add `docs/FEATURE_LABEL_FOUNDATION_ENTRY_CONTRACT.md`. |
| P4 | `ff9ab1b` | `docs/harness/HARNESS_NOTES.md` backlog note; `tests/README.md`; `.gitignore` `**/*.raw` + harness lock; justfile auto-merge warning. |
| P5 | `c1f3f74` | Extract `json_ready`/`json_ready_base` to provider-neutral `data/foundation/serialization.py`; re-point 13 importers; shim retained. |

## Repo inventory (verified)

- src: 246 modules (~74.5k LOC), incl. Phase-B additions `data/databento/dense_grid.py`
  + `data/foundation/grid.py` (`DenseGridBarRecord`). Providers isolated under
  `data/databento` / `data/ibkr`; canonical contracts in `data/foundation`.
- tests: 423 `test_*.py` modules; external providers gated; all fail-closed safety tests present.
- docs: ~72 top-level + `data_foundation/` (incl. `databento/`) + `governance/` + new `_historical/` + `harness/`.

## Source-of-truth / docs changes (P1, P2, P3)

- README, PROJECT_STATUS, PROGRESS, CHANGELOG, `data_foundation/{README,DATA_FOUNDATION_OVERVIEW}`
  now state the **dual-provider** reality: Databento PRIMARY deep-history (Phase B,
  27 local-only DatasetVersions, 2018–2026, sparse + dense research grid); IBKR
  read-only broker-validation. `NEXT_CAMPAIGN_CANDIDATES` points at the decided next campaign.
- New agent entry points: `docs/AGENT_CONTEXT_MAP.md` (single front door) and
  `docs/README.md` (grouped index of all docs — links only, **no docs moved**).
- Audit-trail indexes: `campaigns/`, `decisions/`, `handoffs/`, `specs/` READMEs expanded.
- New `docs/FEATURE_LABEL_FOUNDATION_ENTRY_CONTRACT.md` names the exact inputs for
  the next campaign (resolve_dataset_version; CanonicalBarRecord/CanonicalBBORecord/
  DenseGridBarRecord; available_ts>=bar_end; governance gates; partition + locked-test
  contamination; BBO tradability proxies) and the may/may-not boundaries.

## Files moved / archived / deleted

- Archived (history-preserving `git mv`): `docs/architecture.md` and
  `docs/artifact_policy.md` → `docs/_historical/` (thin stub duplicates of the
  authoritative UPPERCASE docs; the one live reference in
  `.claude/skills/frontier-campaign/SKILL.md` was repointed to `docs/ARCHITECTURE.md`).
- Deleted: `handoffs/DATA-P21.md` — byte-identical stray duplicate; canonical copy
  retained at `handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P21.md` (no information lost).

## Data architecture change (P5)

- `json_ready` / `json_ready_base` moved from the IBKR namespace
  (`data/ibkr/_json_utils.py`) to provider-neutral `data/foundation/serialization.py`.
  Databento (6 modules) and `foundation/dry_run.py` no longer import IBKR internals.
  All 13 importers repointed; `_json_utils.py` kept as a thin back-compat shim.
  Functions copied verbatim — behavior unchanged. **Executed by Codex, reviewed by Claude Opus.**

## Artifact-guard / config change

- `.gitignore`: added global `**/*.raw` (parity with `artifact_guard.py`) and ignored
  the Claude Code harness lock `.claude/scheduled_tasks.lock`. No guard-logic change.

## Tests

- No tests deleted or weakened. `tests/README.md` added (taxonomy + gating policy).
  No new product tests (P5 is behavior-identical and covered by existing callers via the shim).

## Validation results

- `python -m pytest -q` → **1812 passed**. `CI=true python -m pytest -q` → **1812 passed**.
- `python -m compileall src tests tools` → OK. `ruff check` on all changed files → clean.
- `python tools/hooks/canary_runner.py` → all canaries pass.
- `python tools/verify.py --smoke` → OK (run after each patch).
- Artifact audit: `git ls-files runs` = 0; tracked heavy artifacts = 0; `data`/`metadata` = READMEs only; secret-shaped tokens = 0.

## Feature/Label readiness

`ALPHA_FEATURE_LABEL_FOUNDATION_V1` can resolve accepted local-only DatasetVersions
(27 Databento across dev/validation/locked partitions, plus IBKR) and consume the
provider-agnostic `CanonicalBarRecord`, `CanonicalBBORecord`, and `DenseGridBarRecord`
(synthetic no-trade rows explicitly flagged non-executable) under `available_ts`/
governance/partition rules — see `docs/FEATURE_LABEL_FOUNDATION_ENTRY_CONTRACT.md`.
Provider serialization is now neutral, so the feature/label layer and future
providers never import IBKR internals.

## Intentional non-changes (do-not-touch honored)

- Did **not** move the 74 flat docs into subdirectories (index-only).
- Did **not** move or rewrite the ASV1 flat handoffs / `PHASE_PLAN.md` (38 frozen references).
- Did **not** edit `ralph_driver.py`, `frontier.yaml` lane logic, or the Ralph state
  machine — captured as a deferred backlog in `docs/harness/HARNESS_NOTES.md`.
- Did **not** touch core data-foundation/governance contracts or hard guards (beyond the additive `.gitignore` line).

## Deferred items

- Harness refactor (split `ralph_driver.py`; de-dup guard constants) — needs
  characterization tests; tracked in `docs/harness/HARNESS_NOTES.md`.
- A full physical `docs/` subdirectory reorg (kept to index-only this pass, per owner).

## Operator action required (security)

- **Rotate the Databento API key.** Per the Databento handoff, the key transited the
  operator shell during the Phase-B setup and must be rotated in the Databento portal.
  It is environment-only and was never written/logged/committed.

## Explicit statements

No data pull was run. No raw/canonical/provider data or secrets were committed. No
Feature/Label implementation was added. No alpha search was run. No broker/live/paper/
order scope was added. No alpha/tradability/profitability/production claim is made.
