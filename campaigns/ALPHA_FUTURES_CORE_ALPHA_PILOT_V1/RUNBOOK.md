# RUNBOOK — ALPHA_FUTURES_CORE_ALPHA_PILOT_V1

Operational runbook for the Workflow 2 (`dag_wave`) Core Alpha Pilot. All paths
are relative to `~/projects/alpha_system`. The active repo and worktrees must
stay on the WSL2 Linux filesystem; never run from `/mnt/c`, `/mnt/d`, `/mnt/e`,
OneDrive, Dropbox, Google Drive, Windows-synced, network, or temp paths.

## 0. Preflight

```bash
cd ~/projects/alpha_system
git status --short
python tools/verify.py --all
python tools/hooks/canary_runner.py
```

Confirm the consumed stack imports and the entry gates hold:

```bash
python -c "import alpha_system.governance, alpha_system.runtime, alpha_system.agent_factory"
```

Entry gates (recorded in `FUTCORE-P01`):

- `FEATURE_LABEL_PARQUET_SINK_V1` complete (dual JSONL+Parquet sink; registries
  record `value_store_format`/`parquet_path`/`value_content_hash`/
  `value_schema_version`).
- `SESSION_LABEL_GUARD_FIX_V1` complete (role-aware `session_label` guard).
- Research Runtime real-data smoke status recorded.
- Agent Factory preflight recorded.
- An accepted Databento ES/NQ/RTY DatasetVersion and Parquet FeaturePack/LabelPack
  resolve through registry tools.

## 1. Repo clean check

```bash
git status --short
git ls-files runs            # must be empty
git ls-files '**/*.parquet' '**/*.sqlite' '**/*.dbn' '**/*.zst'   # must be empty
```

## 2. Campaign file checks

```bash
test -f ACTIVE_CAMPAIGN.md
test -f campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/GOAL.md
test -f campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/PHASE_PLAN.md
test -f campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/campaign.yaml
test -f campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/ACCEPTANCE.md
test -f campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/RISK_REGISTER.md
test -f campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/RUNBOOK.md
test '!' -f campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/ACTIVE_CAMPAIGN.md
grep -q "ALPHA_FUTURES_CORE_ALPHA_PILOT_V1" ACTIVE_CAMPAIGN.md
```

## 3. YAML parse + consistency

```bash
python -c "import yaml; yaml.safe_load(open('campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/campaign.yaml'))"
```

Consistency expectations (also enforced by stop_conditions):

- phase ids/names/lanes/dependencies/DAG fields match between `PHASE_PLAN.md` and
  `campaign.yaml`;
- `acceptance_gates` cover all 31 phases exactly once;
- parallel phases have disjoint `allowed_paths`; `must_run_alone` phases are not
  `parallel_safe`; no parallel phase declares a global/coordinator path.

## 4. Plan the DAG (read-only)

```bash
just frontier-plan ALPHA_FUTURES_CORE_ALPHA_PILOT_V1
```

Expected wave shape (with `max_parallel_phases: 3`):

```text
Sequential : P00 P01 P02 P03 P04 P05 P06
Parallel   : [P07 P08 P09] [P10 P11]
Sequential : P12 P13 P14 P15
Parallel   : [P16 P17 P18] [P19 P20]
Sequential : P21 P22 P23 P24 P25 P26 P27 P28 P29 P30
```

No `conflicts`, no `blocked`. `unsafe` lists only the `must_run_alone` phases
(expected).

## 5. Mock run (no providers, no merges)

```bash
just frontier-run-parallel-mock ALPHA_FUTURES_CORE_ALPHA_PILOT_V1 3
```

Confirms wave packing, STOP checks, and the serial merge queue end-to-end with
mocked providers before any live cost is incurred.

## 6. Live parallel run

```bash
just frontier-run-parallel ALPHA_FUTURES_CORE_ALPHA_PILOT_V1 3
```

Ralph builds each wave in isolated worktrees, runs checks, routes Claude review,
parses verdicts, opens PRs, waits for CI, evaluates the merge gate, and merges
one PR at a time. Resume / next / overnight variants:

```bash
just frontier-resume ALPHA_FUTURES_CORE_ALPHA_PILOT_V1
just frontier-next   ALPHA_FUTURES_CORE_ALPHA_PILOT_V1 1
just frontier-overnight ALPHA_FUTURES_CORE_ALPHA_PILOT_V1
```

STOP / heartbeat / tail / summary / promote-reviews:

```bash
just frontier-stop <run_id>
just frontier-heartbeat <run_id>
just frontier-tail <run_id>
just frontier-summary <run_id>
just frontier-promote-reviews <run_id> ALPHA_FUTURES_CORE_ALPHA_PILOT_V1
```

## 7. Per-stage research workflows (what each phase does)

- **DatasetVersion check** — `FUTCORE-P03` locks the accepted DatasetVersion and
  Parquet FeaturePack/LabelPack by id/hash via registry tools (no value commits).
- **FeaturePack / LabelPack Parquet check** — `FUTCORE-P13` maps each accepted
  AlphaSpec to available primitives with valid `available_ts`; produces a minimal
  gap list.
- **Runtime smoke check** — recorded in `FUTCORE-P01`; diagnostics phases call
  the runtime tool surface only.
- **Agent Factory preflight check** — recorded in `FUTCORE-P01`; queue + roles
  set in `FUTCORE-P06`.
- **session guard check** — canaries in `FUTCORE-P23` (and P01) confirm
  point-in-time session-context behavior.
- **AlphaSpec batch workflow** — `FUTCORE-P05` protocol; `FUTCORE-P07…P11`
  family batches (parallel).
- **AlphaSpec critique workflow** — `FUTCORE-P12` independent critique + family
  budget audit.
- **StudySpec workflow** — `FUTCORE-P14` approved StudySpec pack.
- **diagnostics workflow** — `FUTCORE-P16…P20` family diagnostics via runtime
  tools (parallel, read-only over locked packs).
- **cost stress workflow** — `FUTCORE-P21` consolidation incl. thin-session.
- **session/horizon/regime matrix** — `FUTCORE-P22`.
- **no-lookahead audit** — `FUTCORE-P23`.
- **variant budget audit** — `FUTCORE-P24`.
- **reviewer verdict workflow** — `FUTCORE-P25` independent verdicts.
- **TrialLedger / RejectedIdea workflow** — `FUTCORE-P26`.
- **EvidenceDraft workflow** — `FUTCORE-P27` survivors only.
- **promotion decision workflow** — `FUTCORE-P28` (`REJECT | INCONCLUSIVE |
  WATCH | CANDIDATE_RESEARCH`).
- **downstream handoff** — `FUTCORE-P29`.
- **artifact audit + closeout** — `FUTCORE-P30`.

## 8. Artifact audit (before every merge)

```bash
git status --short
git diff --cached --name-only
git ls-files runs
git ls-files '**/*.parquet' '**/*.sqlite' '**/*.dbn' '**/*.zst'
```

Stage explicit paths only. Never `git add .` / `git add -A`. Never force-push.
Heavy/raw/value/DB artifacts stay local-only (gitignored + never-commit globs).

## 9. STOP / Resume

A `runs/<run_id>/STOP` file is an active stop request. Ralph checks it before
phase selection, Codex execution, checks, review, PR, CI, merge gate, merge,
done-check, and next-phase. To resume, remove/resolve the STOP and re-run
`frontier-resume`; Ralph continues from recorded run state.

## 10. Closeout

`FUTCORE-P30` runs the acceptance audit + semantic done-check, writes
`campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/CLOSEOUT.md` with a verdict in
`{COMPLETE, COMPLETE_WITH_WARNINGS, BLOCKED}`, updates the coordinator
`ACTIVE_CAMPAIGN.md`, and emits the downstream handoffs. Final gates:

```bash
python tools/verify.py --all
python tools/hooks/canary_runner.py
```

## 11. Handoff to next campaigns

`FUTCORE-P29` produces failure-mode-driven requirement handoffs to
`ALPHA_VALIDATION_GOVERNANCE_V1`, `ALPHA_FACTOR_LIBRARY_V1`, and
`ALPHA_STRATEGY_REFERENCE_VALIDATION_V1`. Survivors (if any) carry
FactorLibrary-ready EvidenceDrafts; this pilot hands off candidates and never
validates, papers, or lives any of them.
