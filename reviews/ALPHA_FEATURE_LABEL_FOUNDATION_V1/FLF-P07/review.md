I have completed a thorough review against the actual repository artifacts. Here is my review.

---

# Claude Opus Review — FLF-P07: Transform / Window / Normalization Primitives

**Campaign:** `ALPHA_FEATURE_LABEL_FOUNDATION_V1` · **Lane:** YELLOW · **Reviewer:** Claude Opus 4.8

## Method

I read the full implementation (`causal.py` 1064 lines, `offline.py`, `__init__.py`), both test files, the docs, README diff, and handoff — not just the executor summary. I independently confirmed the FLF-P04/P06 imports resolve to real symbols, and that no governance/contract files were touched. Pytest required interactive approval in this review environment, so I relied on the executor + validation output for the run results (8 unit / 56 combined passing, canaries green, ruff clean) while verifying correctness directly from the code.

## Scope & Boundary Compliance ✅

- **Changed files** (`git status`): only `src/alpha_system/features/primitives/**`, the two test files, `docs/feature_label_foundation/PRIMITIVES.md`, `README.md`, and the commit-eligible handoff. Exactly the Allowed Paths; nothing outside.
- **Governance consumed, not duplicated (R-022):** `contracts.py`, `semantics.py`, `input_views.py`, and all governance modules are **unmodified**. FLF-P06 `TransformSpec`/`WindowSpec`/`NormalizationSpec` and FLF-P04 `is_real_trade_bar`/`has_missing_or_abnormal_bbo` are imported and reused.
- **No `ACTIVE_CAMPAIGN.md` write** (coordinator-only, dag_wave) — confirmed.
- **Artifact policy clean:** `git ls-files runs` empty; no `runs/` path staged; no heavy/DB/raw-data artifacts; explicit staging left to Ralph.
- **No forbidden scope:** no broker/live/paper/order/account, no strategy/backtest/portfolio, no external provider calls, no materialization. README claim-scan shows only pre-existing disclaimers and module names — **no new alpha/tradability claims**.

## Causality / No-Lookahead (R-006, R-007) ✅

- `_ordered_points` sorts strictly by `(available_ts, original_index)`; `_causal_window_points` slices `points[start : index+1]` — **trailing-only**, never reaching forward. `source_available_ts` is asserted ≤ output `available_ts` in tests.
- The no-lookahead suite proves the strong property: a late-`available_ts` value (event_ts in the past) does **not** alter any earlier output (`test_late_available_future_value_cannot_change_prior_outputs`), and ordering uses `available_ts` not `event_ts`.
- **Offline isolation is structural and double-layered:** `_require_live_window_spec` fails closed on `centered`/`future`/`offline_only` windows (raising `PrimitiveSpecError`), offline helpers live in a separate `primitives.offline` module that is **not exported from the package root** (`assert not hasattr(primitives, "offline_future_mean")`), and the FLF-P06 `FeatureSpec` independently rejects a live feature bound to such a window (`FeatureContractError`). A live feature cannot reach a centered/future window through any public entry point.

## Missingness Semantics (R-011 / R-012) ✅

- `points_from_trade_rows`/`bars_from_trade_rows` emit no-trade rows as gaps (value `None` + `no_trade` flag), never as trade bars.
- `points_from_bbo_rows` surfaces missing/quarantined BBO as gaps — **no silent forward-fill**.
- `_rolling_reduce` propagates `input_gap` rather than imputing when any window member is a gap; session-reset paths block cross-session windows.

## Handoff Truthfulness ✅

The handoff is accurate and complete. Notably, it **honestly records** that the spec's bare `python -c "import ..."` command failed (`ModuleNotFoundError`, src-layout/PYTHONPATH) and documents the `PYTHONPATH=src` workaround that passed — this is a transparent environment note, not a hidden failed run. Staging is correctly deferred to Ralph; no review/verdict/PR/merge was performed by the executor.

## Findings

**Warning (non-blocking, cosmetic):** `simple_returns` (causal.py:445–453) passes `math.log1p` into `_return_values` as the `transform` callable, but when `log_return=False` the value is computed directly as `point.value / prior.value - 1.0` and the callable is never used. The argument is dead/misleading. No correctness impact (tests confirm correct simple-return values); worth a one-line cleanup in a later pass.

**Reviewer limitation:** I could not re-execute pytest in this sandbox (commands needed approval). Correctness was verified by full code read + independent import resolution + ruff/canary output; the passing claim is well corroborated but not re-run by me.

## Conclusion

A genuinely well-engineered, fail-closed substrate phase: causal-by-construction, structurally offline-isolated, missingness-honest, governance-consuming, and artifact-clean. The single finding is cosmetic.

VERDICT: PASS_WITH_WARNINGS
