# Active Campaign

Project: `alpha_system`

Campaign: `campaigns/DIFFERENTIATED_KILLSHOT_V1` (COMPLETE 6/6)
Workflow: `workflow2`
Run: `complete` — DIFFERENTIATED_KILLSHOT_V1 finished 6/6 on 2026-06-14
Status: `no live Workflow 2 run` — post-DK factory adjudication

Current phase: `none` (no live run)
Last completed phase: `DK-P05` — verdict aggregation + closeout
Last completed status: `PASS_WITH_WARNINGS`
Passing phases: `6/6`

## Post-DK state (verify live via `python tools/frontier/status_doctor.py`)

DIFFERENTIATED_KILLSHOT_V1 is COMPLETE 6/6 with **0 survivors** — the second clean
kill-shot after FUTSUB:

- **Track A** (calendar/flow conditioning factors as main-effect context):
  WELL-POWERED CLEAN NULL — 4 mechanisms scored `ZERO_PASS_MET`, all REJECT.
- **Track B** (`context != trigger` conditional probe, EXPLORATORY lane):
  SUBSTRATE-GAP, UNTESTED — it ran on a single-class (degenerate) 120m
  `target_before_stop` slice, so it is **not** a null; it is a closable DATA_GAP.
- **roll_week**: honest DATA_GAP (`in_roll_window_flag` all-null).

Survivor gate = **0**. No promotion. No downstream factory module (broad Mining V2,
FactorLibrary as survivor memory, AlphaBook, Strategy Sandbox, PA grammar), no
universe expansion, and no paid data are authorized — all remain trigger-gated
behind the survivor gate.

Next state: post-DK **factory production-line adjudication** (charter the generic
Idea → MechanismCard/SetupSpec → testability gate → diagnostics/probe → verdict →
rejected/survivor memory line), then a **narrow Track B substrate gap-closure**
(same pre-registered SetupSpec, existing `ES_2020_120m` barrier-resolving slice,
no new mechanisms, no geometry/horizon sweep, no promotion), then a fresh narrow
shot from a ranked MechanismCard queue. ES/NQ/RTY existing data only.

Ralph updates this pointer through reviewed phase commits during a live Workflow 2
run; between runs the coordinator keeps it synced to post-run truth.

Broker/live trading, paper trading, order routing, raw data commits, heavy artifact
commits, local DB commits, and alpha/tradability claims without evidence remain out
of scope.
