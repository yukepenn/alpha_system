# Workflow 2 DAG Integration and Parallel Plan

This document records how `ALPHA_AGENT_FACTORY_MVP` runs under Workflow 2 with
the DAG wave scheduler. It is documentation only: it changes no scheduler
configuration, campaign contract, Frontier tool, code module, test, runtime
primitive, or consumed primitive.

## Scheduler Configuration

`campaigns/ALPHA_AGENT_FACTORY_MVP/campaign.yaml` is the scheduler source of
truth. Its `workflow2.scheduler` block is:

```yaml
workflow2:
  scheduler:
    mode: dag_wave
    parallel_execution: true
    max_parallel_phases: 3
    merge_queue: serial
    update_active_campaign: coordinator_only
```

Those settings mean Ralph selects dependency-ready phases with the DAG wave
scheduler, may build conflict-free parallel-safe phases concurrently, limits
parallel width to three phases, and merges through a serial queue. The
repository-level `ACTIVE_CAMPAIGN.md` pointer is coordinator-owned.

## Wave Plan

`just frontier-plan ALPHA_AGENT_FACTORY_MVP` computes the exact scheduler waves
from dependencies plus DAG metadata. The intended campaign shape is:

- **W0 - sequential bootstrap + core contracts (run-alone):**
  `AGENT-P00 -> AGENT-P01 -> AGENT-P02 -> AGENT-P03 -> AGENT-P04 -> AGENT-P05 -> AGENT-P06`.
- **W1 - parallel role contracts (disjoint `allowed_paths`):**
  `AGENT-P07` through `AGENT-P15`, split into sub-waves of three because
  `max_parallel_phases: 3`.
- **W2 - sequential enforcement / records / memory (run-alone):**
  `AGENT-P16 -> AGENT-P17 -> AGENT-P18`.
- **W3 - parallel assets + runtime bridge (disjoint `allowed_paths`):**
  `AGENT-P19`, `AGENT-P20`, `AGENT-P21`.
- **W4 - sequential dry-run + closeout (run-alone):**
  `AGENT-P22 -> AGENT-P23 -> AGENT-P24 -> AGENT-P25`.

The current read-only planner preview expands that shape into these concrete
waves:

| Planner wave | Mode | Phases |
| --- | --- | --- |
| 0 | single | `AGENT-P00` |
| 1 | single | `AGENT-P01` |
| 2 | single | `AGENT-P02` |
| 3 | single | `AGENT-P03` |
| 4 | single | `AGENT-P04` |
| 5 | single | `AGENT-P05` |
| 6 | single | `AGENT-P06` |
| 7 | parallel | `AGENT-P07`, `AGENT-P08`, `AGENT-P09` |
| 8 | parallel | `AGENT-P10`, `AGENT-P11`, `AGENT-P12` |
| 9 | parallel | `AGENT-P13`, `AGENT-P14`, `AGENT-P15` |
| 10 | single | `AGENT-P16` |
| 11 | single | `AGENT-P17` |
| 12 | single | `AGENT-P18` |
| 13 | parallel | `AGENT-P19`, `AGENT-P20`, `AGENT-P21` |
| 14 | single | `AGENT-P22` |
| 15 | single | `AGENT-P23` |
| 16 | single | `AGENT-P24` |
| 17 | single | `AGENT-P25` |

The planner reports 18 waves, maximum width 3, and `parallelizable: true`.
Run-alone phases are declared `must_run_alone`.

## Parallel-Safety Rule

A phase is parallel-safe only when all of these are true:

- It sets `parallel_safe: true`.
- It sets `must_run_alone: false`.
- It declares disjoint `allowed_paths`.
- It declares no global or coordinator-owned file.
- It is not RED.

Any phase that omits `parallel_safe: true`, omits `allowed_paths`, declares a
shared or coordinator file, or is RED runs alone.

The only parallel-safe phases in this campaign are:

- `AGENT-P07` through `AGENT-P15` in merge group `agent_roles`.
- `AGENT-P19`, `AGENT-P20`, and `AGENT-P21` in merge group `assets`.

All other phases run alone, including bootstrap/core contracts
`AGENT-P00` through `AGENT-P06`, enforcement/records/memory `AGENT-P16`
through `AGENT-P18`, and dry-run/closeout `AGENT-P22` through `AGENT-P25`.

## Disjointness Guarantees

Parallel-safe phases write only their own disjoint files. The role-contract
fan-out writes per-role modules, per-role tests, per-role docs, per-role prompt
templates, the phase handoff, and that phase's review artifacts. Role phases do
not edit `src/alpha_system/agent_factory/roles/__init__.py` or
`src/alpha_system/agent_factory/roles/registry.py`; each role registers through
the existing registry contract.

The assets wave is also disjoint:

- `AGENT-P19` writes `templates/agent_factory/prompts/**` plus its handoff and
  review artifacts.
- `AGENT-P20` writes the Agent Factory guide/operator/readiness docs plus its
  handoff and review artifacts.
- `AGENT-P21` writes the runtime bridge module, its focused tests, the runtime
  bridge doc, and its handoff/review artifacts.

Parallel-safe phases omit `runs/**` from `allowed_paths` because run artifacts
are shared local-only state. They also omit `ACTIVE_CAMPAIGN.md` and any other
global/coordinator-owned file.

## Serial Merge Queue

Parallel-safe phases may build concurrently in isolated worktrees, but merges
do not happen concurrently. Ralph routes completed branches through
`merge_queue: serial`, merging one PR at a time and re-validating the merge
gate against the freshly updated `main` before the next merge. This preserves
the disjoint build benefits while keeping the authoritative branch state
linear and freshly checked at each merge boundary.

## Coordinator-Owned Pointer

`ACTIVE_CAMPAIGN.md` is owned by the Workflow 2 coordinator. Phase branches do
not write it in parallel mode, and no phase lists it in `allowed_paths`. Any
pointer update belongs to the coordinator after the relevant campaign state
transition, not to an executor phase branch.

## Operator Verification Commands

Before any live parallel run, operators use the read-only plan preview and the
mock no-merge parallel run:

```bash
just frontier-plan ALPHA_AGENT_FACTORY_MVP
just frontier-run-parallel-mock ALPHA_AGENT_FACTORY_MVP 3
```

`just frontier-plan ALPHA_AGENT_FACTORY_MVP` verifies the computed waves,
run-alone phases, and maximum width. `just frontier-run-parallel-mock
ALPHA_AGENT_FACTORY_MVP 3` exercises the parallel driver path with mock
providers and no merge. These commands are the verification path for the DAG
plan; they do not change the campaign safety boundary.

## Boundary

This DAG plan is a scheduling record for a contracts-only campaign. It does not
instantiate agents, start a continuous runner, call providers, route orders,
operate broker/live/paper/account surfaces, promote factors, validate
strategies, or state research efficacy.
