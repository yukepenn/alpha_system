# Runbook — STRATEGY_SHAPED_RESEARCH_LANE_V0

## Preconditions
- `python tools/frontier/status_doctor.py` → no other campaign RUNNING (SHIP_REFIT_V1 COMPLETE).
- Git main-only and clean; `git ls-files runs` empty.
- `ACTIVE_CAMPAIGN.md` repointed to STRATEGY_SHAPED_RESEARCH_LANE_V0 (coordinator-only, serial, at launch).

## Validation (no providers / network / merge)
```bash
python -c "import yaml; yaml.safe_load(open('campaigns/STRATEGY_SHAPED_RESEARCH_LANE_V0/campaign.yaml'))"
just frontier-plan STRATEGY_SHAPED_RESEARCH_LANE_V0
just frontier-run-parallel-mock STRATEGY_SHAPED_RESEARCH_LANE_V0 1
python tools/verify.py --smoke && python tools/hooks/canary_runner.py
```

## Launch (Workflow 2, provider-wired, serial)
```bash
# coordinator repoints ACTIVE_CAMPAIGN first (serial), then:
just frontier-run-parallel STRATEGY_SHAPED_RESEARCH_LANE_V0 1
# P00 -> P01 -> P02 -> P03 -> P04 ; serial merge queue
```
(With SHIP_REFIT-P01's in-driver watchdog now on main, this run carries hang auto-recovery;
the coordinator still keeps an external progress-watchdog armed as a belt-and-suspenders fallback.)

## Standard per-phase checks
```bash
python tools/verify.py --smoke
python tools/verify.py --all
python tools/hooks/canary_runner.py
```

## Phase-specific verification
- **P01** SetupSpec/MechanismCard validation tests; `event_trigger` separate from `entry_context`.
- **P02** (load-bearing): a context≠trigger SetupSpec compiles + runs an EXPLORATORY probe over a
  path label; **trusted/promotion path refuses EXPLORATORY artifacts** (canary); `grep` proves
  `research/` does not import backtest/management/fast_path; single-factor path byte-unchanged;
  surrogate-FDR + power attached.
- **P03** one context≠trigger idea end-to-end on a small slice, EXPLORATORY + ledgered; de-stack
  diagnostic recorded; no promotion.
- **P04** handoff scaffold emits trusted-lane gaps without promoting; happy-path + naming docs.

## STOP / resume
`runs/<RID>/STOP` = active stop request (checked before each stage). Terminal STOP
("stopped safely, all phases completed") = completion marker.

## Hard stops
No paid data; no broker/live/order/capital; no non-regenerable deletion; no committing
data/DB/Parquet/secrets; no truth-chain weakening; no sequence encoder / sim-bridge (deferred);
no broad PA library / strategy zoo.
