# Runbook — DIFFERENTIATED_KILLSHOT_V1

## Preconditions
- `python tools/frontier/status_doctor.py` → no other campaign RUNNING (SSRL COMPLETE).
- Git main-only and clean; `git ls-files runs` empty.
- The five differentiated-substrate prep docs/cards are on main
  (`research/differentiated_substrate_v1/{FDR_BUDGET.md,FDR_BUDGET_PRIORITY_2_3.md,SUBSTRATE_GROUNDING.md,cards/**}`).
- `ACTIVE_CAMPAIGN.md` repointed to `DIFFERENTIATED_KILLSHOT_V1` (coordinator-only, serial, at launch).

## Validation (no providers / network / merge)
```bash
python -c "import yaml; yaml.safe_load(open('campaigns/DIFFERENTIATED_KILLSHOT_V1/campaign.yaml'))"
just frontier-plan DIFFERENTIATED_KILLSHOT_V1
just frontier-run-parallel-mock DIFFERENTIATED_KILLSHOT_V1 1
python tools/verify.py --smoke && python tools/hooks/canary_runner.py
```

## Launch (Workflow 2, provider-wired, serial)
```bash
# coordinator repoints ACTIVE_CAMPAIGN first (serial), then:
just frontier-run-parallel DIFFERENTIATED_KILLSHOT_V1 1
# DK-P00 -> DK-P01 -> DK-P02 -> DK-P03 -> DK-P04 -> DK-P05 ; serial merge queue
```
(The in-driver provider-watchdog (SHIP_REFIT-P01, continuous-stall window) carries hang
auto-recovery; the coordinator also keeps an external progress-watchdog armed as a
belt-and-suspenders fallback. Resume an interrupted run with
`ralph_driver.py resume --run-dir runs/<RID> --provider-wired` — NEVER `run` (mints a fresh run).)

## Standard per-phase checks
```bash
python tools/verify.py --smoke
python tools/verify.py --all
python tools/hooks/canary_runner.py
git ls-files runs   # must be empty
```

## Phase-specific verification
- **DK-P00** (FDR gate): `FDR_ACTIVE_SUBSET_RESTATEMENT.md` value-free, predates any variant,
  `fomc/cpi` DEFERRED, active surface arithmetic = 6; REUSE_MAP/SCOPE committed.
- **DK-P01** (substrate): five new flags in BOTH reference + fast path, value-identical under the
  parity gate; APPROVED FeatureRequest; no-lookahead audits pass; flags materialized ES/NQ/RTY
  (uncommitted); no offline countdown features reused.
- **DK-P02** (Track A gate): five StudySpecs locked (resolver-smoke); declared-conditioning-factor
  admission minimal + mutation-tested; surrogate-FDR `ZERO_PASS_MET` per study (reports value-free);
  no real metric inspected.
- **DK-P03** (Track A evidence): five mechanisms scored post-gate; `primary_state + reason_code +
  N_eff/power`; `verdict_refresh.md`; research never imports the value engine.
- **DK-P04** (Track B): one context≠trigger EXPLORATORY SetupSpec (genuinely distinct signals)
  over path labels via the injected-row harness; `EVIDENCE.json` EXPLORATORY/`promotion_eligible:false`
  (or honest `DATA_GAP`); promotion path refuses it; `conditional_probe.py` byte-unchanged.
- **DK-P05** (verdict): `CAMPAIGN_VERDICT.md` aggregates all items with reason codes; survivor gate
  applied; evidence summary + `RUN_SUMMARY`; no promotion.

## STOP / resume
`runs/<RID>/STOP` = active stop request (checked before each stage). Terminal STOP
("stopped safely, all phases completed") = completion marker. Resume with `resume --run-dir`,
never `run`.

## Hard stops
No paid data / feed (incl. `fomc/cpi` onboarding); no broker/live/order/capital; no non-regenerable
deletion; no committing data/DB/Parquet/SQLite/secrets/registries; no truth-chain / no-lookahead /
ledger / FDR / no-second-PnL weakening; no overnight family or sequence/geometry engine (deferred);
no promotion of any survivor (surface it for the survivor-gate decision).
