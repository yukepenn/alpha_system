# ALPHA_SYSTEM_V1 Campaign Contract Review

**Reviewer:** Claude Opus 4.8 (semantic / cross-provider review)
**Mode:** Review-only. No contract files modified. No Workflow 2 run. No source implementation.
**Date:** 2026-05-31
**Base commit observed:** `bc572e6`
**Scope under review:** Minimal consistency repair described in
`handoffs/ALPHA_SYSTEM_V1/CAMPAIGN_CONTRACT_CONSISTENCY_REPAIR.md`

## Verdict

**PASS_WITH_WARNINGS**

The repaired campaign contract is internally consistent and machine-loadable.
`campaign.yaml` parses, contains exactly `ASV1-P00` through `ASV1-P29` once each,
and phase IDs/names/lanes/dependencies align with `PHASE_PLAN.md`. Lane, review,
merge, artifact, and acceptance policies are coherent across files. No blocking
defect was found. Three minor warnings remain (one corrupted check command, one
stray duplicate file, one cosmetic scope-enumeration gap). None block starting
Workflow 2; W-1 and W-2 should be cleaned up early (W-1 ideally inside ASV1-P03,
W-2 inside or before ASV1-P00).

## Checklist Results

| # | Review item | Result |
|---|-------------|--------|
| 1 | YAML parse validity | PASS — `yaml.safe_load` succeeds; all 21 expected top-level keys present (`campaign_id`…`phases`,`acceptance_gates`,`risk_controls`,`stop_conditions`). |
| 2 | Phase IDs P00–P29 present exactly once | PASS — 30 phases, no duplicates, no missing, exact order. |
| 3 | Phase names match PHASE_PLAN ↔ campaign.yaml | PASS — all 30 names identical; 30 detailed `## ASV1-Pxx` sections in PHASE_PLAN match the table and YAML. |
| 4 | Dependencies match | PASS — linear chain plus fan-ins (P06←P04,P05; P08←P06,P07; P09/P10←P05,P08; P11←P09,P10; P14←P11,P13) identical in both files. |
| 5 | Lane policy consistency | PASS — all phases YELLOW except P28 GREEN, consistent across table, YAML, RUNBOOK §30, and Acceptance. GREEN/YELLOW/RED definitions agree across GOAL, YAML `lane_policy`, and RUNBOOK. |
| 6 | Review/merge policy consistency | PASS — YELLOW requires fresh Claude Opus review + `PASS`/`PASS_WITH_WARNINGS`; merge gates in `merge_policy`, `review_policy`, RUNBOOK §19–20, and Acceptance agree. Verdict vocabulary consistent (`PASS`,`PASS_WITH_WARNINGS`,`REWORK`,`BLOCKED`). |
| 7 | Acceptance gates cover all phases | PASS — 7 `acceptance_gates` groups partition all 30 phases with no gaps and no overlaps. Mirrors PHASE_PLAN "Acceptance Gate Summary". |
| 8 | Artifact policy consistency | PASS — `never_commit` / `local_only_by_default` / `commit_allowed` in YAML align with GOAL, PHASE_PLAN global rules, ACCEPTANCE artifact audit, and RUNBOOK §27/§29. Per-phase `forbidden_paths` consistently block data/*, metadata DBs, parquet, logs, artifacts. |
| 9 | Tiny fixture exception clarity | PASS — `path_policy.exceptions_apply_before_forbidden_globs: true`; `tiny_fixture_exceptions` scoped to `tests/fixtures/**` with explicit requirements (synthetic/tiny/documented/below threshold/not real data/not alpha evidence). R-039 explicitly requires fixture exception to apply *after* the documented tiny-synthetic exception ordering — consistent. |
| 10 | No raw data / heavy artifact loophole | PASS — global + per-phase forbidden globs cover `data/raw|canonical|factors|labels|cache/**`, `metadata/*.sqlite|*.db|*.wal|*.db-journal`, `**/*.parquet|*.arrow|*.feather` (fixture-excepted), pickles, model binaries, logs, caches. `stop_conditions` block staged raw/heavy artifacts. |
| 11 | No broker/live trading scope | PASS — `broker_live_trading_in_scope:false`, `paper_trading_in_scope:false`; forbidden globs for `execution/broker*`,`execution/live*`,`execution/paper*`,`execution/order_router*`,`broker/**`,`live/**` (global + repeated per-phase); GOAL "What the Platform Is Not", RISK R-022, RUNBOOK §34, ACCEPTANCE all reinforce. |
| 12 | No alpha/tradability claims | PASS — `production_trading_claims_allowed:false`, `alpha_tradability_claims_allowed_without_evidence:false`; dedicated no-tradability-claim tests in P12/P20/P21/P23; `no_alpha_claims` risk control; ACCEPTANCE prohibited-claim language. |
| 13 | Reference truth vs fast-path parity boundary | PASS — single canonical Tier-1 reference truth (P15); fast path (P19) is acceleration-only and parity-gated; `risk_controls.reference_truth` + `fast_path_requires_parity`; P04 note defers reference engine to P15; R-009/R-010/R-035 enforce "no second PnL truth" and "no fast path before parity". |
| 14 | Risk register coverage | PASS — R-001…R-040 with severity/likelihood/owner/detection/blocking; per-phase + gate-level cadence maps risks to phases; ASV1-P29 must classify all 40. Cross-references to phases are coherent. |
| 15 | Runbook consistency with campaign.yaml | PASS — RUNBOOK state machine (19 states), run/phase artifacts, lane/merge gates, STOP semantics, Red env vars (`PROJECT_OP_AUTHORIZED|SCOPE|EXPIRES`), and required `campaign.yaml` key list all match the YAML. (See W-1: one RUNBOOK/PHASE_PLAN check command differs from the YAML copy.) |
| 16 | ACTIVE_CAMPAIGN points to ALPHA_SYSTEM_V1 | PASS — top-level `ACTIVE_CAMPAIGN.md` sets Campaign `campaigns/ALPHA_SYSTEM_V1`, phase pointer `ASV1-P00`, workflow `workflow2`, and restates out-of-scope boundaries. |
| 17 | Bundle ready before starting Workflow 2 | PASS_WITH_WARNINGS — contract is load-ready and contradiction-free; resolve W-1/W-2 to avoid avoidable friction, but neither blocks `CAMPAIGN_LOAD`/`PHASE_SELECT`. |

## Warnings (non-blocking)

### W-1 — Corrupted check command in `campaign.yaml` (P03)
`campaigns/ALPHA_SYSTEM_V1/campaign.yaml:748`:

```
- python -c "import alpha_system; print(alpha_system.**name**)"
```

`**name**` is a leftover Markdown-bold corruption of the Python dunder `__name__`.
As written the command raises `SyntaxError` if executed literally. The
corresponding `PHASE_PLAN.md` check (line ~1107) correctly uses `__name__`, so
this is a PHASE_PLAN↔campaign.yaml check-level mismatch and an instance of the
exact "generated-markdown artifact" class the repair set out to remove. It is a
valid YAML string (does not break parse), so it is a warning, not a blocker.
**Recommendation:** restore `__name__` during ASV1-P03 (or a follow-up contract
touch-up); do not let Ralph run the check verbatim.

### W-2 — Stray duplicate `ACTIVE_CAMPAIGN.md` inside campaign directory
`campaigns/ALPHA_SYSTEM_V1/ACTIVE_CAMPAIGN.md` (~11 KB, tracked) is a second,
differently-formatted "Active Campaign" document distinct from the canonical
top-level `ACTIVE_CAMPAIGN.md`. It names the same campaign (`ALPHA_SYSTEM_V1`),
so there is no contradiction, but it is not one of the seven intended campaign
contract files and is a documented-but-unresolved leftover (handoff "Remaining
Risks"). Two Active-Campaign sources of truth risk pointer drift during
`CAMPAIGN_LOAD`/`NEXT_PHASE`. **Recommendation:** remove or reconcile this file
(prefer the single top-level pointer) before or during ASV1-P00. Not blocking.

### W-3 — P04 scope enumeration vs allowed_paths (cosmetic)
`campaign.yaml` ASV1-P04 `allowed_paths` includes
`src/alpha_system/backtest/contracts.py` and the phase note references
`BacktestSpec`, but the `PHASE_PLAN.md` P04 Scope file list enumerates only
`experiments/contracts.py` and `l2/contracts.py` (no `backtest/contracts.py`).
Both descriptions agree that P04 is contract/schema-only with the reference
engine deferred to P15, so this is a non-contradictory enumeration gap, not a
scope conflict. **Recommendation:** add `backtest/contracts.py` to the PHASE_PLAN
P04 scope list (or drop it from YAML) for exact parity. Low priority.

## Scope Confirmation

The change set remained limited to campaign-contract repair. No source modules,
data, SQLite/Parquet, broker/live/paper code, or Workflow 2 execution were
introduced. Pre-existing unrelated working-tree edits (`PROGRESS.md`,
`PROJECT_STATUS.md`, `frontier.yaml`) are outside this review's scope and were
not assessed here.

## Reviewer Validation Performed (read-only)

- `yaml.safe_load(campaign.yaml)` → parses; 30 phases, exact ID set, no dups,
  in order; 21 top-level keys present.
- Acceptance-gate phase partition → covers P00–P29 with no gap/overlap.
- Phase names/lanes/dependencies → cross-checked YAML vs PHASE_PLAN table.
- Forbidden-path / fixture-exception / broker / alpha-claim controls → grep audit
  across YAML, GOAL, PHASE_PLAN, ACCEPTANCE, RISK_REGISTER, RUNBOOK.
- Risk register R-001…R-040 and gate cadence → present and phase-mapped.
- Delimiter / PART-marker sweep → none found (clean).

## Recommendation

Accept the consistency repair as **PASS_WITH_WARNINGS**. The bundle is
contradiction-free and load-ready for the human-gated Workflow 2 entry. Address
W-1 and W-2 as early low-risk contract touch-ups (W-1 during ASV1-P03, W-2 during
or before ASV1-P00); W-3 is optional polish. Proceed only through the normal
human-gated campaign workflow.
