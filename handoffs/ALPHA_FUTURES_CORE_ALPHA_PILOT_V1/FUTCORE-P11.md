# FUTCORE-P11 Handoff

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P11`  
Executor: Codex  
Date: 2026-06-07

## Summary

Drafted the BBO tradability / top-book confirmation AlphaSpec batch under the
`FUTCORE-P05` protocol and the `bbo_tradability_confirmation: 0.10` family
budget.

- Draft count: `4`.
- Quota adherence: minimum `3`, target `4`, maximum `4`; this batch uses the
  target count and does not reallocate unused slots.
- Each draft contains exactly one governance `AlphaSpec` JSON payload with the
  required top-level fields, a content-derived `alpha_spec_id`, a valid
  `hyp_` id, ES/NQ/RTY-only target instruments, BBO diagnostics, timestamp and
  no-lookahead assumptions, P04 cost-profile declarations, duplicate-exposure
  notes, and value-free later-review criteria.
- No AlphaSpec was implemented, run, reviewed, promoted, or converted into a
  StudySpec in this phase.

## Explicit File List For Ralph

Codex staged no files, per executor safety instructions. The files for Ralph to
stage explicitly are:

- `research/futures_core_alpha_pilot_v1/alpha_specs/bbo_tradability/FUTCORE-P11_bbo_tradability_01.md`
- `research/futures_core_alpha_pilot_v1/alpha_specs/bbo_tradability/FUTCORE-P11_bbo_tradability_02.md`
- `research/futures_core_alpha_pilot_v1/alpha_specs/bbo_tradability/FUTCORE-P11_bbo_tradability_03.md`
- `research/futures_core_alpha_pilot_v1/alpha_specs/bbo_tradability/FUTCORE-P11_bbo_tradability_04.md`
- `docs/futures_core_alpha_pilot/alpha_specs/bbo_tradability.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P11.md`

No `runs/**` path is commit-eligible for this phase.

## Drafts

| File | AlphaSpec id | Hypothesis id | Instruments | Idea |
| --- | --- | --- | --- | --- |
| `FUTCORE-P11_bbo_tradability_01.md` | `aspec_1284e49b083df11eeb0481ea` | `hyp_f598b58b133d59a56d557a08` | ES, NQ, RTY | Spread-zscore plus top-book depth filter for confirmation or risk control. |
| `FUTCORE-P11_bbo_tradability_02.md` | `aspec_cfb2aad22b43bc23391a7806` | `hyp_38f323cff1a4daea065cffed` | ES, NQ, RTY | Microprice-minus-mid and top-book imbalance confirmation overlay. |
| `FUTCORE-P11_bbo_tradability_03.md` | `aspec_857ea832d75aa4fc23b376d6` | `hyp_70727d83baa99c852e1d552b` | ES, NQ, RTY | Top-book depth and imbalance risk-control or confirmation filter. |
| `FUTCORE-P11_bbo_tradability_04.md` | `aspec_89fa98eb6439f131de4151cb` | `hyp_3d3e3f9ea18a6150b14ab5e3` | ES, NQ, RTY | Missing-BBO, bad-quote, wide-spread, and low-depth quarantine overlay. |

## Declared Diagnostics

All four drafts declare the mandatory BBO-family diagnostics for later phases:

- valid BBO requirements for bid, ask, bid/ask size, mid, spread,
  `spread_ticks`, quality flags, and `available_ts`;
- spread-zscore, microprice-minus-mid, top-book imbalance, displayed depth, and
  quote-quality framing;
- stale, crossed, missing, quarantined, invalid-size, and unavailable-quote
  exclusions;
- confirmation or risk-control overlay role only, with explicit rejection of
  standalone edge, profitability, fill-capacity, paper/live, broker, production,
  capital, or readiness conclusions;
- primary `5m`/`10m`/`15m`/`30m` horizon declarations, `1m`/`3m`
  diagnostic-only limitations, extended-horizon caveats, and maintenance-break
  flatness;
- P04 cost-model binding to
  `cmv_futcore_pilot_three_layer_session_stress_v1` with exactly `zero_cost`,
  `base`, `stress_1`, `stress_2`, and `double_cost`; `zero_cost` is
  diagnostic-only and absent from every `promotion_criteria` list;
- thin-session overlays for `ETH_only`, `ETH_evening`, `ETH_overnight`,
  `pre_RTH`, and `post_RTH`.

## Duplicate-Exposure Notes

- Draft 01 overlaps cost-stress, VWAP/session, and liquidity/PA filters because
  spread and depth can become broad market-quality gates.
- Draft 02 overlaps generic imbalance, regime pressure, and cross-market
  confirmation ideas; the distinguishing feature is signed microprice
  displacement from mid.
- Draft 03 overlaps liquidity/PA and volume/activity overlays because displayed
  depth is a liquidity proxy; it is limited to risk-control or confirmation use.
- Draft 04 intentionally overlaps all other BBO drafts as the quote-quality
  quarantine gate they depend on; it must remain a data-quality overlay rather
  than a duplicate spread, depth, or microprice hypothesis.

## Validation

| Command | Result |
| --- | --- |
| `test ! -f runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/phases/FUTCORE-P11/STOP` | Passed; no phase STOP file was present. The specified run artifact directory was absent in this worktree, so no run-local handoff was written. |
| `git status --short` | Not run. The executor prompt explicitly forbade Codex from running `git status`; Ralph owns authoritative working-tree validation. |
| `python -c "import alpha_system.governance.alpha_spec"` | Failed with `ModuleNotFoundError: No module named 'alpha_system'`; this shell did not have the repo `src` path on `PYTHONPATH` for the exact command. |
| `PYTHONPATH=src python -c "import alpha_system.governance.alpha_spec"` | Passed; no output. Supplemental environment-specific import check. |
| `PYTHONPATH=src python - <<'PY' ... validate_alpha_spec(...) ... PY` | Passed; printed `bbo_alpha_specs_validated=4` and the four content-derived `aspec_` ids. Each BBO draft had exactly one JSON payload, exact required top-level fields, and `zero_cost` absent from `promotion_criteria`. |
| `python tools/verify.py --smoke` | Passed; no output. |
| `test -d research/futures_core_alpha_pilot_v1/alpha_specs/bbo_tradability` | Passed; directory exists. |
| `test -f docs/futures_core_alpha_pilot/alpha_specs/bbo_tradability.md` | Passed; file exists. |
| `test -f handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P11.md` | Passed after this handoff was written. |
| `grep -q "FUTCORE-P11" README.md` | Passed; README contains the phase marker. |
| `git ls-files runs` | Passed; empty output. |
| `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.dbn' '**/*.zst'` | Passed; empty output. |

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
- Run the Yellow-lane review and verdict handling through the Ralph-owned
  workflow.
