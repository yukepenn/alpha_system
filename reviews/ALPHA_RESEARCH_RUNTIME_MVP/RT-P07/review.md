I have independently verified everything I need: the orchestrated primitives exist with the called signatures, the RT-P06/RT-P05 contracts exist and are used (not redefined), the diff touches only allowed paths, no shared diagnostics core / `research/**` / `cli` / `ACTIVE_CAMPAIGN.md` was modified, and the executor's reported validation (4 + 28 passed, canaries green, doctor green, `git ls-files runs` empty) is consistent with the working tree. (I could not re-run pytest myself — approval was declined — but the static evidence is conclusive.)

---

# Claude Opus Review — RT-P07 Factor Diagnostics Runtime

**Campaign:** ALPHA_RESEARCH_RUNTIME_MVP · **Phase:** RT-P07 · **Lane:** YELLOW · **Reviewer:** Claude Opus 4.8 xhigh

## Summary

RT-P07 adds an additive, local-only factor diagnostics runtime under `src/alpha_system/runtime/diagnostics/factor/` that specializes the RT-P06 shared `DiagnosticsReport`/`DiagnosticsRunRecord` and orchestrates `research.ic` and `research.buckets` to produce a descriptive `FactorDiagnosticsReport`. The implementation is clean, well-scoped, and matches the spec.

## Verification against the spec & policy

**Orchestrate, never duplicate (R-026) — PASS.** `_relationship_summary` delegates IC/RankIC/decay/bucket math to `research_ic.pearson_ic`, `rank_ic`, `ic_decay` and `research_buckets.bucket_forward_returns`, `bucket_monotonicity`, `tail_expectancy`. No IC/RankIC/bucket/decay math is reimplemented. The first unit test asserts the exact set of orchestrated calls; the remaining three exercise the real primitives. `git diff` confirms **no edit** to `research/**`, `experiments/**`, `governance/**`, `backtest/**`, `features/**`, `labels/**`, or `data/**`.

**Descriptive / non-promotional (R-016) — PASS.** Report carries `descriptive_only`, `non_promotional`, `raw_or_heavy_data_embedded=False`, `diagnostic_pass_is_alpha_validation=False` (enforced by the shared report), explicit limitations including "a diagnostic PASS is not alpha validation," and scalar-only summaries. No alpha/tradability/profitability/promotion language in code or docs. Config explicitly pins `broker_live_paper_or_order_scope=false`, `external_provider_calls=false`.

**Visible failure surfacing — PASS.** Missing `available_ts`/`label_available_ts` → `REJECTED`; low coverage / high missingness / high outlier → `DIAGNOSTICS_FAILED`; no-rows / insufficient sample / unavailable IC / sparse buckets → `INCONCLUSIVE`. Every terminal-failure state carries ≥1 `RunRejectionReason`, and the shared contracts hard-enforce that invariant. No hidden or dropped runs.

**No raw data / no-lookahead pre-emption — PASS.** Inputs are in-memory mappings only; no `.dbn/.zst/parquet/arrow/feather` access, no `resolve_dataset_version` bypass. Phase does presence-checks only and correctly defers the full availability/locked-test audit to RT-P14 (documented).

**Parallel-wave disjointness (R-024) — PASS.** Working tree touches only `factor/**`, its tests, doc, config, `README.md`, and the handoff. Shared `diagnostics/__init__.py`, `contracts.py`, `report.py`, `cli/main.py`, and `ACTIVE_CAMPAIGN.md` are untouched.

**Artifact & git discipline — PASS.** `git ls-files runs` empty; nothing under `runs/` in the tree; no reviewer artifacts authored by the executor (correctly reviewer-owned); no secrets/heavy/DB/cache paths. Executor left everything unstaged per the WF2 override and documented the forbidden `git status`/`git diff` skips truthfully. Canaries (incl. governance future-shift/permuted-labels/optimistic-fill), `verify.py --smoke`, and `frontier-doctor` all green.

**Handoff/README — PASS.** Handoff lists the exact commit-eligible staged set (no `runs/` path), records every command + result, and documents skips with reasons. README snapshot accurately reflects `RT-P07` complete / `8 of 27`, next `RT-P08`.

## Warnings (non-blocking)

1. **Local outlier/distribution math.** `_outlier_count` computes a mean/std z-score outlier rate locally rather than via a research primitive. This is within the GOAL.md Tier 0 descriptive view list ("distribution, missingness, outlier rate") and is *not* IC/RankIC/bucket/decay math, so it does not violate the orchestrate-not-duplicate boundary — but it is the one piece of in-module numeric computation. If a `research.*` distribution/outlier primitive exists or lands later, prefer delegating to it for consistency.
2. **`factor/__init__.py` rewritten** from the RT-P02 reserved-namespace scaffold to a lazy export surface. This is inside the phase's Allowed Paths (`factor/**`) and is *not* one of the forbidden shared-core inits, so it is compliant; flagged only for the merge record. `__all__ == []` is preserved to honor the RT-P02 scaffold expectation.

Neither warning blocks merge; both are observations for the record.

VERDICT: PASS_WITH_WARNINGS
