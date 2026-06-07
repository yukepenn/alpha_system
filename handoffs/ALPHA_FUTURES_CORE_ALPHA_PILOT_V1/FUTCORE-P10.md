# FUTCORE-P10 Handoff

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P10`  
Executor: Codex  
Date: 2026-06-07

## Summary

Drafted the liquidity sweep / failed-breakout / objective price-action
AlphaSpec batch under the `FUTCORE-P05` protocol and the
`liquidity_sweep_failed_breakout: 0.15` family budget.

- Draft count: `6`.
- Quota adherence: minimum `4`, target `6`, maximum `6`; this batch uses the
  target count and does not reallocate unused slots.
- Each draft contains exactly one governance `AlphaSpec` JSON payload with the
  required top-level fields, a content-derived `alpha_spec_id`, a Hypothesis
  Scout drafter id, objective and computable PA rule definitions, timestamped
  level availability, horizon/session/cost declarations, expected failure
  modes, duplicate-exposure notes, and value-free later-review criteria.
- No AlphaSpec was implemented, run, reviewed, promoted, or converted into a
  StudySpec in this phase.

## Explicit File List For Ralph

Codex staged no files, per executor safety instructions. The files for Ralph to
stage explicitly are:

- `research/futures_core_alpha_pilot_v1/alpha_specs/liquidity_pa/FUTCORE-P10_liquidity_pa_01.md`
- `research/futures_core_alpha_pilot_v1/alpha_specs/liquidity_pa/FUTCORE-P10_liquidity_pa_02.md`
- `research/futures_core_alpha_pilot_v1/alpha_specs/liquidity_pa/FUTCORE-P10_liquidity_pa_03.md`
- `research/futures_core_alpha_pilot_v1/alpha_specs/liquidity_pa/FUTCORE-P10_liquidity_pa_04.md`
- `research/futures_core_alpha_pilot_v1/alpha_specs/liquidity_pa/FUTCORE-P10_liquidity_pa_05.md`
- `research/futures_core_alpha_pilot_v1/alpha_specs/liquidity_pa/FUTCORE-P10_liquidity_pa_06.md`
- `docs/futures_core_alpha_pilot/alpha_specs/liquidity_pa.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P10.md`

No `runs/**` path is commit-eligible for this phase.

## Drafts

| File | AlphaSpec id | Hypothesis id | Instruments | Focus |
| --- | --- | --- | --- | --- |
| `FUTCORE-P10_liquidity_pa_01.md` | `aspec_1c1cfee8bedf55ced10a391e` | `hyp_001f84bc9c9e33365e1a7346` | ES, NQ, RTY | Prior high/low liquidity sweep against a causal 20-bar range. |
| `FUTCORE-P10_liquidity_pa_02.md` | `aspec_df2d040e45564c259ef3de6d` | `hyp_575a2af3b0d0d6c6b7788722` | ES, NQ, RTY | Sweep followed by close back inside the fixed prior range. |
| `FUTCORE-P10_liquidity_pa_03.md` | `aspec_928e60d5096d2383a25f66c6` | `hyp_849b1622d91691c40417acb8` | ES, NQ, RTY | Wick rejection beyond a prior level with fixed body/wick ratios. |
| `FUTCORE-P10_liquidity_pa_04.md` | `aspec_bc9bbcd07669384e51b1661f` | `hyp_84420e7ea623fad31b6d9b21` | ES, NQ, RTY | Post-sweep reversal displacement relative to prior median true range. |
| `FUTCORE-P10_liquidity_pa_05.md` | `aspec_55c1351d04054c943c2c3721` | `hyp_beab96767e05d5b0964afe9b` | ES, NQ, RTY | Compression breakout from a fixed 8-bar compression boundary. |
| `FUTCORE-P10_liquidity_pa_06.md` | `aspec_39ffc190cfbfa6ba0b1a2a25` | `hyp_1978a01ab95fd2c53d564929` | ES, NQ, RTY | Failed-breakout reversal back inside a fixed boundary. |

## Objective Rule Coverage

All six drafts carry an objective rule catalog for:

- prior high/low reference levels with `available_ts` from completed
  contributing bars;
- liquidity sweep beyond a prior level by at least one instrument minimum tick;
- close-back-inside by the sweep bar close or the next completed bar;
- wick rejection with `wick/range >= 0.60` and `body/range <= 0.35`;
- displacement with `abs(close_t - close_t_minus_1) >= 1.50` times prior
  20-bar median true range;
- compression with an 8-bar range width no greater than `0.65` times the
  median prior 8-bar range width from 60 completed bars;
- breakout beyond a fixed compression boundary by at least one tick;
- failed breakout within two completed bars with an opposite move at least
  `1.00` times prior 20-bar median true range.

Each draft excludes missing, stale, degenerate, cross-boundary, and ambiguous
reference levels. The P19 diagnostic declarations require trigger counts,
missing-level exclusions, side, instrument, session view, horizon, and
duplicate-exposure grouping without committing per-row values.

## Duplicate-Exposure Notes

- Draft 01 may overlap generic breakout or range-position exposure unless the
  stop-run sweep event remains distinct in later diagnostics.
- Draft 02 may overlap generic mean-reversion unless the sweep distance and
  close-back deadline remain visible.
- Draft 03 may overlap close-back-inside and thin-session range artifacts unless
  wick/body ratio buckets are audited.
- Draft 04 may overlap regime momentum/reversion or volatility expansion unless
  the sweep prerequisite remains visible.
- Draft 05 may overlap the P09 compression-release regime draft unless fixed
  PA boundaries are kept separate from regime activation.
- Draft 06 may overlap close-back-inside or wick rejection unless fixed-boundary
  breakout failure is separated in later diagnostics.

## Validation

| Command | Result |
| --- | --- |
| `test ! -f runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/STOP` | Passed; no run-level STOP file was present. |
| `find runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/phases/FUTCORE-P10 -maxdepth 2 -type f -print` | Failed before edits because the specified phase run directory was absent in this worktree; no run-local artifacts were created. |
| `git status --short` | Not run. The executor prompt explicitly forbade Codex from running `git status`; Ralph owns authoritative working-tree validation. |
| `python -c "import alpha_system.governance.alpha_spec"` | Failed with `ModuleNotFoundError: No module named 'alpha_system'`; this shell did not have the repo `src` path on `PYTHONPATH` for the exact command. |
| `PYTHONPATH=src python -c "import alpha_system.governance.alpha_spec"` | Passed; no output. |
| `PYTHONPATH=src python - <<'PY' ... validate_alpha_spec(...) ... PY` | Passed; printed `liquidity_pa_alpha_specs_validated=6` and the six `aspec_*` ids. Each draft had exactly one JSON payload, exact required top-level fields, a matching content-derived `alpha_spec_id`, and no `zero_cost` mention in `promotion_criteria`. |
| `python tools/verify.py --smoke` | Passed; no output. |
| `test -d research/futures_core_alpha_pilot_v1/alpha_specs/liquidity_pa` | Passed; directory exists. |
| `test -f docs/futures_core_alpha_pilot/alpha_specs/liquidity_pa.md` | Passed; file exists. |
| `test -f handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P10.md` | Passed after this handoff was written. |
| `test "$(ls -1 research/futures_core_alpha_pilot_v1/alpha_specs/liquidity_pa/*.md 2>/dev/null \| wc -l)" -ge 4` | Passed; draft count is `6`. |
| `test "$(ls -1 research/futures_core_alpha_pilot_v1/alpha_specs/liquidity_pa/*.md 2>/dev/null \| wc -l)" -le 6` | Passed; draft count is `6`. |
| `git ls-files runs` | Passed; empty output. |
| `git ls-files '**/*.parquet' '**/*.arrow' '**/*.feather' '**/*.dbn' '**/*.zst' '**/*.sqlite' '**/*.db'` | Passed; empty output. |
| `find reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P10 -maxdepth 2 -type f -print` | Passed; empty output, and no review artifact was created by Codex. |
| `LC_ALL=C grep -RIn '[^ -~]' README.md docs/futures_core_alpha_pilot/alpha_specs/liquidity_pa.md handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P10.md research/futures_core_alpha_pilot_v1/alpha_specs/liquidity_pa` | Passed; no non-ASCII text found. |

## Safety Confirmations

- No Claude or reviewer was called by Codex.
- No `review.md` or `verdict.json` was created by Codex.
- No PR was created and no merge was attempted.
- No `git add`, `git commit`, `git push`, `git status`, or `git diff` command
  was run by Codex.
- No consumed `src/alpha_system/**` primitive was edited.
- `ACTIVE_CAMPAIGN.md` was not touched.
- No raw provider data, feature values, label values, diagnostics values,
  Parquet, Arrow, Feather, SQLite, DBN, Zstd, logs, caches, or local DB
  artifacts were created or committed by Codex.
- No broker, live, paper, order-routing, deployment, account, or capital action
  was performed.

## Open Items For Ralph

- Run authoritative `git status --short` validation, because Codex was
  explicitly prohibited from running it.
- Stage only the explicit paths listed above.
- Run Yellow-lane review, verdict handling, PR, CI, merge gate, merge, and
  done-check through the Ralph-owned workflow.
