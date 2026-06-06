# Workflow 2 DAG Integration

`ALPHA_RESEARCH_RUNTIME_MVP` consumes the already-built
`WF2_PARALLEL_DAG_SCHEDULER_MVP` scheduler. This document records how the
campaign is scheduled; it does not change scheduler code, phase metadata,
runtime code, data access, or campaign contracts.

## Scheduler Settings

The campaign contract sets:

- `workflow2.scheduler.mode: dag_wave`
- `workflow2.scheduler.parallel_execution: true`
- `workflow2.scheduler.max_parallel_phases: 3`
- `workflow2.scheduler.merge_queue: serial`
- `workflow2.scheduler.update_active_campaign: coordinator_only`

The scheduler is conservative by default: phases that do not prove path
isolation run alone.

## Dependency Shape

The human-facing wave plan is grouped into five campaign bands:

| Campaign wave | Phases | Shape |
| --- | --- | --- |
| `w0` | `RT-P00 -> RT-P01 -> RT-P02 -> RT-P03 -> RT-P04 -> RT-P05 -> RT-P06` | Sequential bootstrap and runtime contracts; every phase runs alone. |
| `w1` | `RT-P07`, `RT-P08`, `RT-P09`, `RT-P10`, `RT-P11` after `RT-P06` | Parallel diagnostics fan-out with disjoint allowed paths. With `max_parallel_phases: 3`, Ralph schedules this as two parallel batches. |
| `w2` | `RT-P12 -> RT-P13/RT-P14 -> RT-P15 -> RT-P16 -> RT-P17 -> RT-P18 -> RT-P19` | Sequential integration; every phase runs alone. |
| `w3` | `RT-P20`, `RT-P22`, `RT-P23` after `RT-P19` | Parallel tests, tool contracts, and docs/templates with disjoint allowed paths. |
| `w4` | `RT-P21 -> RT-P24 -> RT-P25 -> RT-P26` | Sequential closeout; every phase runs alone. |

The dependency graph intentionally allows only two parallel bands: diagnostics
after shared contracts, and test/tool/docs work after integration. Closeout does
not run in parallel.

## Parallel-Safety Rule

A phase is parallel-safe only when all of these are true:

- it sets `parallel_safe: true`;
- it sets `must_run_alone: false`;
- it declares `allowed_paths` that are disjoint from every co-running phase;
- it declares no global or coordinator-owned file;
- it is not a RED-lane phase.

Otherwise, the phase runs alone. Omitting `parallel_safe` or omitting
`allowed_paths` is not enough to co-run.

## Disjoint Path Guarantees

The diagnostics band is parallel-safe because each phase owns a separate runtime
or documentation surface:

- `RT-P07`: factor diagnostics runtime, tests, config, and
  `docs/research_runtime/diagnostics/factor.md`.
- `RT-P08`: label diagnostics runtime, tests, config, and
  `docs/research_runtime/diagnostics/label.md`.
- `RT-P09`: split diagnostics runtime, tests, config, and
  `docs/research_runtime/diagnostics/splits.md`.
- `RT-P10`: cross-market diagnostics runtime, tests, config, and
  `docs/research_runtime/diagnostics/cross_market.md`.
- `RT-P11`: cost runtime, tests, config, and
  `docs/research_runtime/COST_STRESS.md`.

Those diagnostics phases explicitly do not touch shared diagnostic core or
global files:

- `src/alpha_system/runtime/diagnostics/__init__.py`
- `src/alpha_system/runtime/diagnostics/contracts.py`
- `src/alpha_system/runtime/diagnostics/report.py`
- `src/alpha_system/cli/main.py`
- `ACTIVE_CAMPAIGN.md`

The tests/tools/docs band is also disjoint:

- `RT-P20`: tiny synthetic runtime fixtures, fail-closed tests,
  no-lookahead runtime tests, `FIXTURES.md`, and `TESTING.md`.
- `RT-P22`: `RuntimeToolResult` / `RuntimeRunSummary` contracts, tests,
  config, and `TOOL_RESULTS.md`.
- `RT-P23`: runtime report-card rendering, report tests, `REPORTS.md`,
  templates, and report-card docs.

Parallel branches must not add shared-core files to their `allowed_paths` during
execution. If a phase needs a shared file, it must be scheduled as run-alone in a
later contract update.

## Serial Merge Queue

Parallel execution means parallel build and validation in isolated worktrees,
not parallel merge. `merge_queue: serial` requires Ralph to merge one PR at a
time, then re-run the merge gate against the freshly updated `main` before the
next PR is eligible.

`ACTIVE_CAMPAIGN.md` is coordinator-owned because
`update_active_campaign: coordinator_only`. Phase branches read the pointer but
do not write it in parallel mode. A phase branch that writes
`ACTIVE_CAMPAIGN.md`, or any merge outside the serial queue, blocks the workflow.

## Preflight Protocol

Before any live parallel run, use the read-only plan and a mock run:

```bash
just frontier-plan ALPHA_RESEARCH_RUNTIME_MVP
just frontier-run-parallel-mock ALPHA_RESEARCH_RUNTIME_MVP 3
```

The plan command previews waves without dispatching execution. The mock command
exercises DAG scheduling, isolated worktree setup, and serial queue behavior
without provider calls, live execution, PR creation, or merge.

## RT-P24 Plan Confirmation

RT-P24 ran the read-only preview:

```bash
python tools/frontier/ralph_driver.py plan-dag --campaign-id ALPHA_RESEARCH_RUNTIME_MVP
```

Output:

```text
Campaign: ALPHA_RESEARCH_RUNTIME_MVP
Scheduler mode: dag_wave   max_parallel_phases: 3
Waves: 22   max width: 3   parallelizable: true
  Wave 0 [single ]: RT-P00
  Wave 1 [single ]: RT-P01
  Wave 2 [single ]: RT-P02
  Wave 3 [single ]: RT-P03
  Wave 4 [single ]: RT-P04
  Wave 5 [single ]: RT-P05
  Wave 6 [single ]: RT-P06
  Wave 7 [parallel]: RT-P07, RT-P08, RT-P09
  Wave 8 [parallel]: RT-P10, RT-P11
  Wave 9 [single ]: RT-P12
  Wave 10 [single ]: RT-P13
  Wave 11 [single ]: RT-P14
  Wave 12 [single ]: RT-P15
  Wave 13 [single ]: RT-P16
  Wave 14 [single ]: RT-P17
  Wave 15 [single ]: RT-P18
  Wave 16 [single ]: RT-P19
  Wave 17 [parallel]: RT-P20, RT-P22, RT-P23
  Wave 18 [single ]: RT-P21
  Wave 19 [single ]: RT-P24
  Wave 20 [single ]: RT-P25
  Wave 21 [single ]: RT-P26
Run-alone / not parallel-safe:
  - RT-P00: declared must_run_alone
  - RT-P01: declared must_run_alone
  - RT-P02: declared must_run_alone
  - RT-P03: declared must_run_alone
  - RT-P04: declared must_run_alone
  - RT-P05: declared must_run_alone
  - RT-P06: declared must_run_alone
  - RT-P12: declared must_run_alone
  - RT-P13: declared must_run_alone
  - RT-P14: declared must_run_alone
  - RT-P15: declared must_run_alone
  - RT-P16: declared must_run_alone
  - RT-P17: declared must_run_alone
  - RT-P18: declared must_run_alone
  - RT-P19: declared must_run_alone
  - RT-P21: declared must_run_alone
  - RT-P24: declared must_run_alone
  - RT-P25: declared must_run_alone
  - RT-P26: declared must_run_alone
```

This matches the campaign wave shape: `w0` maps to scheduler waves 0-6, `w1`
maps to waves 7-8 because the width cap is 3, `w2` maps to waves 9-16, `w3`
maps to wave 17, and `w4` maps to waves 18-21. The preview emitted no
`Conflicts` or `Blocked` sections, and the declared parallel-safe phases
(`RT-P07` through `RT-P11`, `RT-P20`, `RT-P22`, and `RT-P23`) are absent from
the run-alone list. That confirms the scheduled parallel batches have declared
allowed paths, no global/coordinator path, disjoint paths, and no shared
resource conflict under the current contract.
