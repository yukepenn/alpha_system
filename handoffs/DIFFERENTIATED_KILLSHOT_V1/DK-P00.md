# Handoff - DIFFERENTIATED_KILLSHOT_V1 DK-P00

## Scope Executed

DK-P00 was executed as a documentation/governance-only phase. No code, tests,
engine behavior, runtime dependency, broker/live/paper path, review artifact,
verdict artifact, PR, merge, or run-local handoff was created.

Files written or updated:

- `research/differentiated_substrate_v1/FDR_ACTIVE_SUBSET_RESTATEMENT.md`
- `docs/differentiated_killshot_v1/REUSE_MAP.md`
- `docs/differentiated_killshot_v1/SCOPE.md`
- `README.md`
- `handoffs/DIFFERENTIATED_KILLSHOT_V1/DK-P00.md`

`ACTIVE_CAMPAIGN.md` already pointed at `DIFFERENTIATED_KILLSHOT_V1` and was
left unchanged.

## Bundle And Pointer Confirmation

- The six-file campaign bundle is present:
  `GOAL.md`, `PHASE_PLAN.md`, `campaign.yaml`, `ACCEPTANCE.md`,
  `RISK_REGISTER.md`, and `RUNBOOK.md`.
- `campaign.yaml` parses successfully.
- `campaign.yaml` phase ids and dependencies linearize to:
  `DK-P00 -> DK-P01 -> DK-P02 -> DK-P03 -> DK-P04 -> DK-P05`.
- `PHASE_PLAN.md` agrees with that linear order.
- `ACTIVE_CAMPAIGN.md` contains `DIFFERENTIATED_KILLSHOT_V1`.
- Prep inputs are present in this worktree:
  `FDR_BUDGET.md`, `FDR_BUDGET_PRIORITY_2_3.md`,
  `SUBSTRATE_GROUNDING.md`, and the differentiated-substrate cards.

## Documents Written

- `FDR_ACTIVE_SUBSET_RESTATEMENT.md` records the value-free pre-registration
  restatement note, not a `BudgetAmendmentRecord`. It documents that
  `create_budget_amendment_record(...)` is strictly increasing and cannot encode
  a downward active-subset re-scope.
- The active mechanisms are pinned to `day_of_week_effect`, `opex_pinning`,
  `month_end_flow` with `month_end_rebalance_flow` folded into it,
  `roll_week_flow`, and `open_close_auction_flow`.
- Deferred items are pinned to `fomc_drift` and `cpi_surprise_reversion`
  (`needs_paid_data`) plus the governed overnight family.
- Per-mechanism `variant_budget` is pinned to horizon count:
  day-of-week 1, opex 1, month-end 1, roll-week 1, open/close 2.
- Family budgets are carried unchanged: event-calendar 6 and
  flow-seasonality 4.
- Active effective pooled-surface arithmetic is explicit:
  event-calendar 2 plus flow-seasonality 4 equals active effective pooled
  surface 6, pooled across ES/NQ/RTY as one surface with no per-instrument split.
- `REUSE_MAP.md` pins the existing governance, research, feature, label,
  surrogate-calibration, runtime-diagnostics, and tools/runtime value-loader
  machinery that later phases must reuse.
- `SCOPE.md` records the explicit out-of-scope list, including `fomc/cpi` until
  feed onboarding, the overnight family, per-instrument splits, geometry/horizon
  sweeps, single-factor-template edits, FUTSUB/core-pilot artifact edits, and
  any second PnL truth or research-to-reference-sim bridge.
- `README.md` was updated with a compact DK-P00 snapshot and unchanged safety
  boundaries.

No real-data IC, return, bucket, walk-forward, N_eff, power, diagnostic,
profitability, tradability, alpha, or trading value was produced or reported.

## Validation Commands And Outcomes

Pre-flight STOP checks:

- `test ! -e runs/2026-06-14T034219Z_DIFFERENTIATED_KILLSHOT_V1/phases/DK-P00/STOP && printf 'NO_STOP\n' || { printf 'STOP_PRESENT\n'; exit 2; }`
  - PASS: printed `NO_STOP`.
- `test ! -e runs/2026-06-14T034219Z_DIFFERENTIATED_KILLSHOT_V1/STOP && printf 'NO_RUN_STOP\n' || { printf 'RUN_STOP_PRESENT\n'; exit 2; }`
  - PASS: printed `NO_RUN_STOP`.

Bundle, pointer, and prep-input confirmations:

- `test -f campaigns/DIFFERENTIATED_KILLSHOT_V1/GOAL.md`
  - PASS.
- `test -f campaigns/DIFFERENTIATED_KILLSHOT_V1/campaign.yaml`
  - PASS.
- `python -c "import yaml; yaml.safe_load(open('campaigns/DIFFERENTIATED_KILLSHOT_V1/campaign.yaml'))"`
  - PASS.
- `grep -q "DIFFERENTIATED_KILLSHOT_V1" ACTIVE_CAMPAIGN.md`
  - PASS.
- `test -f campaigns/DIFFERENTIATED_KILLSHOT_V1/GOAL.md && test -f campaigns/DIFFERENTIATED_KILLSHOT_V1/PHASE_PLAN.md && test -f campaigns/DIFFERENTIATED_KILLSHOT_V1/campaign.yaml && test -f campaigns/DIFFERENTIATED_KILLSHOT_V1/ACCEPTANCE.md && test -f campaigns/DIFFERENTIATED_KILLSHOT_V1/RISK_REGISTER.md && test -f campaigns/DIFFERENTIATED_KILLSHOT_V1/RUNBOOK.md`
  - PASS.
- `test -f research/differentiated_substrate_v1/FDR_BUDGET.md && test -f research/differentiated_substrate_v1/FDR_BUDGET_PRIORITY_2_3.md && test -f research/differentiated_substrate_v1/SUBSTRATE_GROUNDING.md && test -d research/differentiated_substrate_v1/cards && test -f research/differentiated_substrate_v1/cards/day_of_week_effect.json && test -f research/differentiated_substrate_v1/cards/opex_pinning.json && test -f research/differentiated_substrate_v1/cards/month_end_flow.json && test -f research/differentiated_substrate_v1/cards/month_end_rebalance_flow.json && test -f research/differentiated_substrate_v1/cards/roll_week_flow.json && test -f research/differentiated_substrate_v1/cards/open_close_auction_flow.json && test -f research/differentiated_substrate_v1/cards/fomc_drift.json && test -f research/differentiated_substrate_v1/cards/cpi_surprise_reversion.json`
  - PASS.
- Command:

```bash
python - <<'PY'
import yaml
from pathlib import Path
path = Path('campaigns/DIFFERENTIATED_KILLSHOT_V1/campaign.yaml')
data = yaml.safe_load(path.read_text())
phases = data['phases']
ids = [p['id'] for p in phases]
deps = {p['id']: p.get('dependencies', []) for p in phases}
expected = ['DK-P00', 'DK-P01', 'DK-P02', 'DK-P03', 'DK-P04', 'DK-P05']
print('ids=' + ' -> '.join(ids))
print('deps=' + ', '.join(f"{k}:{'/'.join(v) if v else '-'}" for k, v in deps.items()))
if ids != expected:
    raise SystemExit(f'phase id order mismatch: {ids!r}')
for prev, cur in zip(expected, expected[1:]):
    if deps[cur] != [prev]:
        raise SystemExit(f'dependency mismatch for {cur}: {deps[cur]!r}')
if deps['DK-P00'] != []:
    raise SystemExit(f'DK-P00 dependency mismatch: {deps["DK-P00"]!r}')
print('linearization=DK-P00 -> DK-P01 -> DK-P02 -> DK-P03 -> DK-P04 -> DK-P05')
PY
```

  - PASS: output confirmed `ids=DK-P00 -> DK-P01 -> DK-P02 -> DK-P03 -> DK-P04 -> DK-P05`;
    dependencies are linear from each phase to the prior phase.

Phase deliverables:

- `test -f research/differentiated_substrate_v1/FDR_ACTIVE_SUBSET_RESTATEMENT.md`
  - PASS.
- `test -f docs/differentiated_killshot_v1/REUSE_MAP.md`
  - PASS.
- `test -f docs/differentiated_killshot_v1/SCOPE.md`
  - PASS.
- `test -f research/differentiated_substrate_v1/FDR_ACTIVE_SUBSET_RESTATEMENT.md && test -f docs/differentiated_killshot_v1/REUSE_MAP.md && test -f docs/differentiated_killshot_v1/SCOPE.md`
  - PASS.

Standard lane checks:

- `PYTHONPATH=src python tools/verify.py --smoke`
  - PASS.
- `PYTHONPATH=src python tools/hooks/canary_runner.py`
  - PASS: all Frontier canaries passed, including
    `planted_fake_alpha`, the true-alpha pair, `forbidden_second_pnl_truth`,
    `forbidden_exploratory_promotion`, `governance_random_target`, and
    `forbidden_scope_drift`.

Artifact discipline:

- `git ls-files runs`
  - PASS: printed nothing.

## Artifact And Boundary Confirmation

- No `runs/` path was created or edited by this execution.
- No run-local `handoff.md`, `review.md`, or `verdict.json` was created.
- No `reviews/` path was created.
- No forbidden data, DB, cache, log, model, or heavy artifact was created.
- No forbidden paths were touched, including:
  `src/alpha_system/core/value_store.py`,
  `src/alpha_system/strategies/templates.py`,
  FUTSUB/core-pilot research artifacts, execution/broker/live/portfolio/
  management/backtest/l2/agent-factory paths, data roots, metadata DBs,
  registry DBs, and `artifacts/**`.
- Changes are left unstaged for the Ralph driver to stage/commit explicitly.
