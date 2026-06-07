# FUTCORE-P09 Handoff

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P09`  
Executor: Codex  
Date: 2026-06-07

## Summary

Drafted the regime-gated momentum-versus-reversion AlphaSpec batch under the
`FUTCORE-P05` protocol and the `regime_momentum_reversion: 0.15` family budget.

- Draft count: `6`.
- Quota adherence: minimum `4`, target `6`, maximum `6`; this batch uses the
  target count and does not reallocate unused slots.
- Each draft contains exactly one governance `AlphaSpec` JSON payload with the
  required top-level fields, a content-derived `alpha_spec_id`, a Hypothesis
  Scout drafter id, point-in-time regime activation logic, horizon/session/cost
  declarations, expected failure modes, duplicate-exposure notes, and
  value-free later-review criteria.
- No AlphaSpec was implemented, run, reviewed, promoted, or converted into a
  StudySpec in this phase.

## Explicit File List For Ralph

Codex staged no files, per executor safety instructions. The files for Ralph to
stage explicitly are:

- `research/futures_core_alpha_pilot_v1/alpha_specs/regime/FUTCORE-P09_regime_01.md`
- `research/futures_core_alpha_pilot_v1/alpha_specs/regime/FUTCORE-P09_regime_02.md`
- `research/futures_core_alpha_pilot_v1/alpha_specs/regime/FUTCORE-P09_regime_03.md`
- `research/futures_core_alpha_pilot_v1/alpha_specs/regime/FUTCORE-P09_regime_04.md`
- `research/futures_core_alpha_pilot_v1/alpha_specs/regime/FUTCORE-P09_regime_05.md`
- `research/futures_core_alpha_pilot_v1/alpha_specs/regime/FUTCORE-P09_regime_06.md`
- `docs/futures_core_alpha_pilot/alpha_specs/regime.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P09.md`

No `runs/**` path is commit-eligible for this phase.

## Drafts

| File | AlphaSpec id | Hypothesis id | Instruments | Activation logic |
| --- | --- | --- | --- | --- |
| `FUTCORE-P09_regime_01.md` | `aspec_eb962fc197eaf3955c5e4711` | `hyp_2ec78fe9f0947242f88c0413` | ES, NQ, RTY | High trendiness with non-stressed volatility gates momentum; low trendiness or range compression after failed extension gates reversion. |
| `FUTCORE-P09_regime_02.md` | `aspec_7db3a23e98ca7ff99b1805c6` | `hyp_393c3bb221369b0358821e11` | NQ, RTY | Volatility/ATR expansion with rising trendiness gates momentum; volatility contraction with compressed range gates reversion. |
| `FUTCORE-P09_regime_03.md` | `aspec_edc47c5593bcaaf6d2d8c42b` | `hyp_071664b41c10dccc28fbd65d` | ES, NQ | Completed ETH direction agreeing with early RTH high trendiness gates momentum; early RTH rejection of completed ETH context gates reversion. |
| `FUTCORE-P09_regime_04.md` | `aspec_d26b7959b12be5b53f969067` | `hyp_69d273adbd7a6145f5d78b6b` | ES, NQ, RTY | Range compression release beyond causal boundaries gates momentum; failed release or close back inside causal range gates reversion. |
| `FUTCORE-P09_regime_05.md` | `aspec_f2de85c342e1bc2018297ff7` | `hyp_b546ba17d1763c2c3cfff616` | RTY, ES | Allowed session transition with high trendiness and volatility expansion gates momentum; low trendiness, volatility contraction, or compression after transition gates reversion. |
| `FUTCORE-P09_regime_06.md` | `aspec_ad998ced05be1a90c92bee1e` | `hyp_e3f92fc321263008ab748040` | ES, NQ, RTY | Point-in-time VWAP distance expansion with high trendiness gates momentum; extended VWAP distance with low trendiness or compression gates reversion. |

## Declared Diagnostics

All six drafts declare the mandatory regime-family diagnostics for later phases:

- computable point-in-time regime inputs and activation rules;
- explicit momentum, reversion, and inactive transition states;
- per-regime sample and coverage caveats by instrument, session, and horizon;
- regime-transition instability near thresholds and session boundaries;
- duplicate exposure versus broad trend filters, broad volatility filters,
  VWAP/session context, liquidity/PA compression, and other regime drafts;
- valid `available_ts` and `label_available_ts` usage;
- P04 cost model binding with `zero_cost`, `base`, `stress_1`, `stress_2`, and
  `double_cost`, with `zero_cost` diagnostic-only and absent from every
  `promotion_criteria` list.

## Duplicate-Exposure Notes

- Drafts 01 and 02 intentionally overlap broad trend and volatility filters;
  later critique must verify that the combined regime gates are distinct.
- Draft 03 overlaps completed ETH / RTH session context and must not collapse
  into a VWAP/session-auction draft.
- Draft 04 overlaps liquidity/PA range-compression and failed-release
  primitives; the distinguishing contract is the regime gate.
- Draft 05 overlaps session-transition and volatility filters; transition time
  is only a gate, not a standalone session filter.
- Draft 06 overlaps VWAP/session context and broad trend filters; VWAP distance
  is only a gate for choosing momentum versus reversion.

## Validation

| Command | Result |
| --- | --- |
| `test ! -f runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/phases/FUTCORE-P09/STOP` | Passed; no phase STOP file was present. The specified phase run directory was also absent in this worktree, so no run-local artifacts were created. |
| `git status --short` | Not run. The executor prompt explicitly forbade Codex from running `git status`; Ralph owns authoritative working-tree validation. |
| `python -c "import alpha_system.governance.alpha_spec"` | Failed with `ModuleNotFoundError: No module named 'alpha_system'`; this shell did not have the package import path set for the exact command. |
| `PYTHONPATH=src python -c "import alpha_system.governance.alpha_spec"` | Passed; no output. Additional environment-specific check to confirm the module imports when the repo source path is set. |
| `PYTHONPATH=src python - <<'PY' ... validate_alpha_spec(...) ... PY` | Passed; printed `regime_alpha_specs_validated=6`. Each regime draft had exactly one JSON payload, exact required top-level fields, and a matching content-derived `alpha_spec_id`. |
| `python tools/verify.py --smoke` | Passed; no output. |
| `python tools/verify.py --lint` | Failed. Ruff reported repository-wide pre-existing formatting/lint issues outside this phase scope, including `316 files would be reformatted` and `Found 1388 errors`; Codex did not edit consumed primitives or tests to repair unrelated lint. |
| `python tools/verify.py --typecheck` | Passed; ran `/usr/bin/python -m compileall -q src tests tools`. |
| `python tools/verify.py --test` | Passed; `2809 passed, 7 skipped in 43.85s`. |
| `python tools/hooks/canary_runner.py` | Passed; all Frontier canaries passed. |
| `test -d research/futures_core_alpha_pilot_v1/alpha_specs/regime` | Passed; directory exists. |
| `test -f docs/futures_core_alpha_pilot/alpha_specs/regime.md` | Passed; file exists. |
| `test -f handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P09.md` | Passed after this handoff was written. |
| `git ls-files runs` | Passed; empty output. |
| `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.dbn' '**/*.zst'` | Passed; empty output. |

Additional local consistency checks:

| Command | Result |
| --- | --- |
| `PYTHONPATH=src python - <<'PY' ... assert zero_cost absent from promotion_criteria ... PY` | Passed; printed `zero_cost_absent_from_promotion_criteria=6`. |
| `LC_ALL=C grep -RIn '[^ -~]' README.md docs/futures_core_alpha_pilot/alpha_specs/regime.md handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P09.md research/futures_core_alpha_pilot_v1/alpha_specs/regime || true` | Passed; empty output. |

## Safety Confirmations

- No Claude or reviewer was called by Codex.
- No `review.md` or `verdict.json` was created by Codex.
- No PR was created and no merge was attempted.
- No `git add`, `git commit`, `git push`, `git status`, or `git diff` command
  was run by Codex.
- No consumed `src/alpha_system/**` primitive was edited.
- `ACTIVE_CAMPAIGN.md` was not touched.
- No raw provider data, feature values, label values, diagnostics values,
  Parquet, SQLite, DBN, Zstd, logs, caches, or local DB artifacts were created
  or committed by Codex.
- No broker, live, paper, order-routing, deployment, account, or capital action
  was performed.

## Open Items For Ralph

- Run authoritative `git status --short` validation, because Codex was
  explicitly prohibited from running it.
- Stage only the explicit paths listed above.
- Decide how to route the existing repository-wide lint failures; Codex left
  them untouched because they are outside the P09 allowed paths and consumed
  primitive scope.
- Run the Yellow-lane review and verdict handling through the Ralph-owned
  workflow.
