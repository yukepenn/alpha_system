# Fresh Adversarial Review — P035000_REAL_FEE_CONSTANTS

- Campaign: DISCOVERY_RIGOR_FLOOR_V1
- Phase: P035000_REAL_FEE_CONSTANTS (lane: yellow)
- Reviewer: Claude (fresh adversarial, WF1)
- Date: 2026-06-11
- Worktree: `/home/yuke_zhang/projects/alpha_system-wf1-ci-selfheal`, branch `feat/real-fee-constants`, diff UNCOMMITTED
- Worktree HEAD: `819c153` (origin/main at review time: `97cf79d` — 2 commits ahead, both docs/campaign-only: compass v4.4 #385, P07 amendment #386)
- Spec: `specs/DISCOVERY_RIGOR_FLOOR_V1/P035000_REAL_FEE_CONSTANTS-cme-broker-fee-truth.md`

## Verdict: PASS_WITH_WARNINGS

All six review checks pass on deterministic evidence. Warnings are
disclosure-quality and follow-up items, not spec violations.

## Check 1 — Scope: fee constants + version plumbing only

PASS.

- `git diff --name-only` (9 modified + 2 untracked-new): `futures_fees.py` (new),
  `costs.py`, `model_version.py`, `runtime.py`, `dry_run.py`,
  `synthetic_signal_probe_rows.json`, `test_cost_model_version.py`,
  `test_real_fee_schedule.py` (new), 3 docs.
- `src/alpha_system/backtest/slippage.py`: **not in the diff** (only
  slippage-named path touched is `docs/COST_AND_SLIPPAGE.md`).
- `src/alpha_system/backtest/costs.py` diff contains **zero deletion lines**
  (verified `git diff costs.py | grep '^-'` → empty): purely additive
  (new `FuturesFeeScheduleCost` component, `futures_fee_schedule` mapping
  branch, `_symbol` helper). `SpreadCost`, `BpsCost`,
  `conservative_default_cost_model()`, and `execution_config.py`
  (`default_execution_config`) are byte-unchanged.
- `model_version.py`: slippage descriptor branches untouched. Cost descriptor
  defaults changed exactly at the Layer-1 placeholder: BBO branch
  `spread_cost + bps_cost(1.0)` → `futures_fee_schedule(ES) + spread_cost`
  (spread layer retained verbatim); non-BBO branch previously fell through to
  `conservative_default_cost_model()` = `BpsCost(1.0)` only, now
  `futures_fee_schedule(ES)` only. The replaced `bps_cost 1.0` is the
  documented Layer-1 hard-fee placeholder (per `COST_MODEL.md` "Layer 1 -
  hard transaction cost ... placeholders"), so this is the in-scope
  replacement, not a spread/slippage change.
- `runtime.py`: additive symbol passthrough on `CostStressFill`
  (`symbol` field → `CostInput.metadata`), no spread/slippage math touched.
- No network calls in code or tests (constants are literals; tests import only).

## Check 2 — Versioning: append-only history, base consumes NEW, zero_cost stays zero

PASS.

- New version `fee_schedule_cme_equity_index_retail_discount_v2_2026_06_11`
  (semantic 2.0.0, as-of 2026-06-11) is `ACTIVE_FEE_SCHEDULE_VERSION_ID`.
- Old placeholder `fee_schedule_futcore_pilot_placeholder_v1` retained in
  `_FEE_SCHEDULES` and resolvable via
  `fee_schedule_by_version(PLACEHOLDER_FEE_SCHEDULE_VERSION_ID)` →
  `.placeholder is True` (asserted in
  `test_real_fee_schedule_pins_symbol_all_in_totals_and_keeps_history`).
  Placeholder is history-only: `FuturesFeeScheduleCost.__post_init__` raises
  `CostModelError("placeholder fee schedules are retained for history only")`
  if anything tries to consume it for cost math — guard observed firing in
  mutation B.
- Base profile consumption:
  `test_default_base_profile_consumes_real_fee_version_and_zero_cost_stays_zero`
  asserts the default `CostModelVersion` descriptor carries
  `schedule_version_id == REAL_FEE_SCHEDULE_VERSION_ID` and
  `base` multiplier 1.0 / `double_cost` 2.0; the descriptor pins the version
  id explicitly (enters `content_hash` → reproducible).
- zero_cost path: untouched in the diff; same test asserts the fixture-only
  zero model still yields `zero_cost_diagnostic_only is True`,
  `fixture_zero_cost is True`, component `zero_cost`.

## Check 3 — Sanity of constants and sourcing

PASS (with warning W2).

Per-side all-in (pinned in `EXPECTED_ALL_IN_PER_SIDE` and in
`futures_fees.py`):

| Symbol | exchange | clearing | NFA | broker | all-in | spec range | in range |
|---|---|---|---|---|---|---|---|
| ES/NQ/RTY | 1.38 | 0.00 | 0.02 | 0.59 | **1.99** | 1.50–3.00 | yes |
| MES/MNQ/M2K | 0.25 | 0.00 | 0.02 | 0.09 | **0.36** | 0.25–0.85 | yes |

- micros < minis per matched symbol: asserted in
  `test_micro_fees_are_below_matching_mini_fees` and arithmetically true
  (0.36 < 1.99).
- Every constant carries a source-citation comment with an as-of date
  ("offline as-of 2026-06-11") and an explicit "verify before any
  paper/live/broker use" caveat. The clearing line is honestly recorded as
  0.00 with a comment that the public retail-facing schedules used fold
  clearing into the quoted exchange amount — disclosed, not fabricated.
  NFA $0.02/side matches the public NFA assessment fee. Magnitudes are
  consistent with publicly circulated non-member CME equity-index rows and a
  representative discount-broker tier; no fake decimal precision beyond
  cents. Honest-sourcing requirement satisfied (see W2 for the residual gap).

## Check 4 — Mutation tests (restore byte-identical)

PASS. Baseline `sha256(futures_fees.py)` =
`4f570e292ee1f36ba11ed9adf5be3b387dd9a8e7e5f26773508c719b14bae3df`.

- **Mutation A** (silent constant drift): `ES_CME_EXCHANGE_FEE_PER_SIDE`
   1.38 → 1.37. Result: **2 FAILED**
  (`test_real_fee_schedule_pins_symbol_all_in_totals_and_keeps_history`,
  `test_fee_schedule_cost_breakdown_uses_components_per_contract[ES]`),
  7 passed. Restored; sha256 matches baseline exactly
  (`RESTORE_A_BYTE_IDENTICAL`).
- **Mutation B** (base profile back at placeholder):
  `ACTIVE_FEE_SCHEDULE_VERSION_ID = PLACEHOLDER_FEE_SCHEDULE_VERSION_ID`.
  Result: **10 FAILED**, 3 passed — including
  `test_default_base_profile_consumes_real_fee_version_and_zero_cost_stays_zero`
  and `test_cost_model_version_defaults_to_spread_when_bbo_is_available`;
  failures driven both by the version-pin assertion and by the
  placeholder-refusal guard in `FuturesFeeScheduleCost.__post_init__`
  (layered defense). Restored; sha256 matches baseline exactly
  (`RESTORE_B_BYTE_IDENTICAL`).

## Check 5 — Validation runs (venv `~/.venvs/alpha_system_research`)

PASS — exact counts, all matching the stated baseline:

- `pytest tests/unit -k "cost or fee" -q`: **91 passed, 2669 deselected** (1.44s).
- `pytest tests/unit/governance tests/integration -q`: **723 passed, 2 failed**
  (27.18s). The 2 failures are the known-env baseline pair
  (`test_duckdb_query_fixture.py::test_duckdb_query_over_tiny_csv_fixture`,
  `test_polars_lazy_fixture.py::test_polars_lazy_transformation_over_tiny_fixture`)
  — optional-dependency fixture-shape mismatches with no fee/cost code in
  their import path; matches the prescribed 723/2 baseline exactly.
- `tools/hooks/canary_runner.py`: **23 PASS** ("All Frontier canaries
  passed", exit 0) — including `planted_fake_alpha`,
  `governance_optimistic_fill`, `governance_permuted_labels`.
- `tools/verify.py --smoke`: exit **0**.

## Check 6 — Git hygiene

PASS.

- `git diff --cached --name-only | wc -l` → **0** (nothing staged).
- `git ls-files runs | wc -l` → **0** (empty).
- No commit made; no `runs/` or data artifacts in the worktree diff.

## Warnings

- **W1 (fixture retune, disclosed).** `tests/fixtures/runtime/probe/
  synthetic_signal_probe_rows.json` label magnitudes scaled 3x
  (±0.3/±0.25 → ±0.9/±0.75) so the synthetic dry-run smoke stays
  net-positive under real MES double-cost fees (fixture prices are 1, so the
  $0.36/side fee dwarfs the old labels). The dry-run test assertions
  themselves are unchanged (`test_dry_run.py` not in diff; 4 passed) and the
  fixture is synthetic plumbing-smoke data, not evidence — acceptable, but
  future cost-magnitude changes will couple to this fixture again.
- **W2 (citation granularity).** Source comments cite source *type* + an
  offline "as-of 2026-06-11" authoring date, not the schedule's published
  effective date or document identifier, and constants were not
  network-verified this phase (executor disclosed this; spec explicitly
  allows it: "honest sourcing beats fake precision"). An online
  re-verification pass is required before any paper/live/broker-adjacent
  use — the code comments already mandate this.
- **W3 (default-magnitude direction, intended).** Replacing the symbolic
  1.0-bps Layer-1 placeholder with hard fees makes the non-BBO default
  Layer-1 charge *smaller* for large-notional minis (e.g., ES at ~$250k
  notional: ~$25/side placeholder → $1.99/side real). This is precisely the
  spec's purpose (real constants over symbolic), spread/slippage layers are
  unchanged, and stress profiles still multiply it — but downstream net-edge
  numbers will move in the optimistic direction versus the old placeholder.
  Research diagnostics only; no tradability claim.
- **W4 (branch base).** Worktree HEAD `819c153` is 2 commits behind
  origin/main `97cf79d` (both docs/campaign-only, no code overlap). Rebase or
  merge before PR; no conflict expected.
- **O1 (observation).** Fills without symbol metadata fall back to
  `default_symbol="ES"` fees in the default descriptors; runtime
  `CostStressFill` gained symbol passthrough (`symbol`/`root_symbol`/
  `instrument_id`) so callers can route micros correctly.

## Evidence basis

Full uncommitted diff read; `futures_fees.py` and `test_real_fee_schedule.py`
read in full; original `model_version.py`/`costs.py` defaults diffed against
HEAD; both mutations executed and reverted with sha256 byte-identity proof;
all four spec validation commands executed with exact counts recorded above.
