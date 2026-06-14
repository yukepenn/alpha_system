# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing
and validating offline research substrate under Frontier Harness Generic
`0.3.0-rc1`.

## Current Snapshot

The repository-level campaign pointer targets `DIFFERENTIATED_KILLSHOT_V1`,
which is **COMPLETE 6/6** (2026-06-14) with **0 survivors** — the second clean
kill-shot after FUTSUB. Campaign state is tracked in `ACTIVE_CAMPAIGN.md`, which
is coordinator-owned between Workflow 2 runs.

- **Track A** (calendar/flow conditioning factors as main-effect context) is a
  WELL-POWERED CLEAN NULL: 4 mechanisms scored `ZERO_PASS_MET`, all REJECT.
- **Track B** (the EXPLORATORY `context != trigger` conditional probe) is a
  SUBSTRATE-GAP, UNTESTED result: it ran on a single-class (degenerate) 120m
  `target_before_stop` slice, so it is **not** a null — it is a closable DATA_GAP.
- `roll_week` is an honest DATA_GAP (`in_roll_window_flag` all-null).

The survivor gate is at **0**: there is no promotion, and no downstream factory
module (broad Mining V2, FactorLibrary as survivor memory, AlphaBook, Strategy
Sandbox, PA grammar), no universe expansion, and no paid data are authorized —
all remain trigger-gated behind the survivor gate. The next state is a post-DK
**factory production-line adjudication** (charter the generic
Idea → MechanismCard → testability gate → diagnostics → verdict → rejected/
survivor memory line), followed by a NARROW Track B substrate gap-closure (same
pre-registered SetupSpec, existing `ES_2020_120m` barrier-resolving slice, no new
mechanisms, no geometry/horizon sweep, no promotion), then a fresh narrow shot
from a ranked MechanismCard queue. ES/NQ/RTY existing data only.

Safety boundaries are unchanged: this is research-only; no alpha/profitability/
tradability claim, no second value/accounting truth, no research-to-reference-sim
bridge, no value-engine edit, no new dependency, no new paid data, no live
trading, no paper trading, no broker operation, no order routing, and no
deployment. `fomc`, `cpi`, and the overnight family remain deferred (paid data).

The committed campaign pointer and README are snapshots. For authoritative
in-flight Workflow 2 state, use `python tools/frontier/status_doctor.py` or the
run-local state owned by Ralph.

## Source Of Truth

- Root campaign pointer: `ACTIVE_CAMPAIGN.md`
- Active campaign bundle: `campaigns/DIFFERENTIATED_KILLSHOT_V1/`
- Campaign overview docs: `docs/differentiated_killshot_v1/`
- Value-free research prep root: `research/differentiated_substrate_v1/`
- Commit-eligible handoffs: `handoffs/DIFFERENTIATED_KILLSHOT_V1/`
- Strategy and roadmap compass: `docs/OPERATING_COMPASS_V4.md`

## Safety Boundaries

The project remains research-only and local-first.
`DIFFERENTIATED_KILLSHOT_V1` authorizes a differentiated-substrate research
kill-shot only. It does not authorize live trading, paper trading, broker
operations, order routing, deployment, account operations, funding decisions, or
autonomous trading behavior.

Artifact discipline is unchanged: explicit staging only and value-free evidence
only. `runs/**` is local-only and never committed. Raw or canonical data,
feature or label values, provider responses, heavy artifacts, local databases,
logs, caches, secrets, and credentials are never committed.

This campaign does not authorize FactorLibrary ingestion, AlphaBook
construction, paper/live behavior, broker access, deployment, economic-use
claims, execution-readiness claims, paid-feed onboarding, or promotion.
`pyproject.toml` dependencies remain empty, so numpy, pandas, and polars stay
absent. Truth-chain invariants are preserved, including the sanctioned reference
engine as the only value/accounting truth. Workflow 2 orchestration, validation
routing, review, staging, commit, PR, CI, merge, and done-check actions are owned
by Ralph.
