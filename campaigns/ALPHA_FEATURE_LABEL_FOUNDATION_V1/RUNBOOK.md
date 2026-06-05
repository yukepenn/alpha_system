# ALPHA_FEATURE_LABEL_FOUNDATION_V1 Runbook

## Runbook purpose

This runbook is the operator manual for executing the
`ALPHA_FEATURE_LABEL_FOUNDATION_V1` campaign under Frontier Harness Generic v3.0
Workflow 2 with the DAG-wave parallel scheduler. It covers preflight, the
DatasetVersion consumption posture, the no-raw-data boundary, the DAG wave plan,
the parallel-mock then parallel-live protocol, the serial merge queue, STOP in
parallel mode, the FeatureRequest / FeatureSpec / LabelSpec workflows,
materialization, the quality / leakage / duplicate-exposure / BBO-missingness /
partition-contamination audits, synthetic fixtures, the small real Databento
DatasetVersion dry run, handoff validation, Claude review, the bounded repair
loop, CI wait, the merge gate, resume, artifact inspection, closeout, and
next-campaign readiness for the Agent Factory.

This campaign is **contract generation and substrate construction only**. It
builds a versioned, no-lookahead-safe Feature/Label research substrate that
consumes **accepted DatasetVersions** through the sanctioned registry API. It
does **not** run alpha research, call Databento or IBKR, pull data, or commit
raw, canonical, feature, or label values. State it plainly and keep it true: a
feature is not alpha; a label is not alpha; a FeatureStore is not a factor
library; a materialized FeatureSet is not a promoted candidate; a good
diagnostic is not production readiness; an accepted DatasetVersion does not imply
alpha validated.

All 32 phases `FLF-P00 … FLF-P31` are GREEN or YELLOW. `FLF-P00` and `FLF-P29`
are GREEN (docs / mechanical, no Claude review). The other 30 are YELLOW
(material engineering with fresh Claude Opus 4.8 xhigh review and auto-merge).
This campaign has **no RED-lane phases** and makes **no external provider
calls**: the data is already pulled and the Feature/Label layer only consumes
local accepted DatasetVersions. The RED lane definition is retained for harness
completeness only.

## Preflight checklist

### Required repo path
The active repo and all Workflow 2 worktrees must be under
`~/projects/alpha_system` on the WSL2 Linux filesystem. Forbidden active
locations: `/mnt/c`, `/mnt/d`, `/mnt/e`, OneDrive, Dropbox, Google Drive,
Windows-synced folders, network drives, and temporary directories.

```bash
cd ~/projects/alpha_system
pwd                 # must be /home/<user>/projects/alpha_system
git status -sb
```

### Non-negotiable preflight questions
* Is the worktree under the WSL2 path? If not, STOP at `RUN_INIT`.
* Does `campaign.yaml` parse, declare `scheduler.mode == dag_wave`, and cover
  every phase in exactly one acceptance gate? If not, block.
* Is any forbidden artifact already staged (raw/canonical data, feature or label
  values, parquet/arrow/feather, DB/WAL, provider response)? If so, unstage
  before starting.
* Is any broker / order / account / paper / live / strategy / backtest /
  portfolio scope present anywhere? If so, STOP and escalate.
* Has `just frontier-plan` been run for this campaign, and has a
  `frontier-run-parallel-mock` completed before any first live parallel run?
  If not, do those first (DAG wave plan + parallel mock sections below).

### Smoke preflight
```bash
python tools/verify.py --smoke
ls runs/*/STOP 2>/dev/null || echo "no active STOP file"
```

## Repo clean check

```bash
cd ~/projects/alpha_system
git status --short
git status -sb
```

A non-clean baseline before `RUN_INIT` should be reconciled or explained before
starting. Stage explicit paths only; never `git add .` / `git add -A`. Never
force push. `runs/**` is local-only and must never appear in `git status` as a
staged path.

## Campaign file checks

The campaign contract is the source of truth. All seven control files must be
present, and there must be no campaign-local `ACTIVE_CAMPAIGN.md`.

```bash
test -f ACTIVE_CAMPAIGN.md
test -f campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1/GOAL.md
test -f campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1/PHASE_PLAN.md
test -f campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1/campaign.yaml
test -f campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1/ACCEPTANCE.md
test -f campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1/RISK_REGISTER.md
test -f campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1/RUNBOOK.md
test '!' -f campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1/ACTIVE_CAMPAIGN.md
grep -q "ALPHA_FEATURE_LABEL_FOUNDATION_V1" ACTIVE_CAMPAIGN.md
```

## YAML parse

The campaign YAML must parse, identify itself, list phases and acceptance gates,
and declare the DAG-wave scheduler. The assertion below also confirms gate
coverage is complete and unique and that no RED phase exists.

```bash
python - <<'PY'
from pathlib import Path
import yaml
data = yaml.safe_load(
    Path("campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1/campaign.yaml").read_text()
)
assert data["campaign_id"] == "ALPHA_FEATURE_LABEL_FOUNDATION_V1"
phases = data["phases"]
assert phases, "no phases"
assert "acceptance_gates" in data and data["acceptance_gates"], "no acceptance_gates"
wf2 = data["workflow2"]
assert wf2["scheduler"]["mode"] == "dag_wave", "scheduler.mode must be dag_wave"
assert wf2["scheduler"]["parallel_execution"] is True
assert wf2["scheduler"]["merge_queue"] == "serial"
phase_ids = [ph["id"] for ph in phases]
covered = []
for g in data["acceptance_gates"].values():
    covered.extend(g.get("phases", []))
assert set(phase_ids) == set(covered), "acceptance gate coverage mismatch"
assert len(covered) == len(set(covered)), "phase covered by more than one gate"
red = {ph["id"] for ph in phases if ph["lane"] == "RED"}
assert red == set(), f"unexpected RED phases: {red}"
print(
    f"OK: {len(phase_ids)} phases; dag_wave + serial merge; "
    f"{len(data['acceptance_gates'])} gates cover phase set exactly once; no RED phases"
)
PY
```

## Accepted DatasetVersion check

The Feature/Label layer consumes **only accepted DatasetVersions**, never raw
provider files. Admissibility is a DatasetVersion lifecycle state in
`{VERSIONED, READY_FOR_RESEARCH}` with non-blocking quality and coverage. The
sanctioned consumption API is
`alpha_system.data.foundation.version_registry.resolve_dataset_version(registry_path, id)`,
which returns DatasetVersion metadata. Records are reconstructed through
`CanonicalBarRecord.from_mapping`, `CanonicalBBORecord.from_mapping`, and
`DenseGridBarRecord.from_mapping`. Databento and IBKR DatasetVersions are
**never merged**.

```bash
export ALPHA_DATA_ROOT=~/alpha_data/alpha_system
# registry DB is local-only under $ALPHA_DATA_ROOT/registry/datasets.sqlite
ls "$ALPHA_DATA_ROOT/registry/datasets.sqlite" 2>/dev/null \
  || echo "note: no local registry yet; consumption uses synthetic fixtures in tests"

# TARGET: resolve and inspect an accepted DatasetVersion (FLF-P01 consumption adapter)
# TARGET: alpha feature dataset show --id dsv_databento_ohlcv_<hex>
```

A locked-test partition DatasetVersion may only be consumed with governance
contamination metadata via
`require_governance_metadata_for_locked_partition_use(...)` (see partition
contamination audit). The consumption adapter must reject any DatasetVersion id
that is not in an admissible lifecycle state.

## Local data root check

Raw, canonical, feature, and label values are local-only and live **outside**
the repo. The suggested data root is `~/alpha_data/alpha_system`, configured via
`ALPHA_DATA_ROOT`.

```bash
export ALPHA_DATA_ROOT=~/alpha_data/alpha_system
case "$ALPHA_DATA_ROOT" in
  "$(pwd)"*) echo "ERROR: data root inside repo" ;;
  /mnt/*|*OneDrive*|*Dropbox*|*"Google Drive"*) echo "ERROR: data root on forbidden/synced path" ;;
  *) echo "data root OK (local, outside repo): $ALPHA_DATA_ROOT" ;;
esac
mkdir -p "$ALPHA_DATA_ROOT"
```

Feature and label values, when materialized, are written under
`$ALPHA_DATA_ROOT`, never into the repo tree.

## No raw data access check

Feature and label code must never read `.dbn`, `.zst`, parquet, arrow, feather,
or any provider file directly. The only sanctioned input path is an accepted
DatasetVersion resolved through the registry API and reconstructed via the
canonical `from_mapping` constructors.

```bash
# no forbidden provider/file readers in feature or label code (heuristic scan)
grep -REn "\.dbn|\.zst|read_parquet|pyarrow|databento|ib_insync|\.feather" \
  src/alpha_system/features src/alpha_system/labels 2>/dev/null \
  | grep -v "from_mapping\|resolve_dataset_version" \
  || echo "no direct provider/file readers found in feature/label code"
```

If feature or label code reads raw provider data, bypasses
`resolve_dataset_version`, or merges Databento with IBKR DatasetVersions, that is
a global merge blocker: `block_merge_and_escalate`.

## DAG wave plan check

Before any execution, run the read-only DAG plan. It prints the dependency
graph, ready waves, run-alone phases, and any path / resource conflicts. A phase
is parallel-safe only if `parallel_safe: true` **and** `must_run_alone: false`
**and** it has disjoint `allowed_paths` **and** touches no global/coordinator
file **and** is not RED. A phase that omits `parallel_safe: true` or
`allowed_paths` runs alone.

```bash
just frontier-plan ALPHA_FEATURE_LABEL_FOUNDATION_V1
```

Expected wave shape for this campaign (waves w0–w6):

```text
w0  FLF-P00..P07  sequential bootstrap + core contracts (each runs alone)
w1  FLF-P08..P12  PARALLEL feature families (ohlcv, bbo, session, cross_market, structure)
w2  FLF-P13..P15  sequential feature integration (engine, store/registry, reports)
w3  FLF-P16        LabelSpec/LabelVersion contracts (runs alone)
    FLF-P17..P20  PARALLEL label families (fixed_horizon, cost_adjusted, path, event)
w4  FLF-P21..P23  sequential label integration (engine, store/registry, leakage audits)
w5  FLF-P24,P25,P27,P29  PARTIAL-PARALLEL diagnostics / fixtures / governance / docs
    FLF-P26,P28          run alone (small real dry run, CLI surface)
w6  FLF-P30,P31  sequential end-to-end dry run + acceptance audit / closeout
```

Parallel waves (w1, the label-family fan-out in w3, and the parallel subset of
w5) build concurrently in isolated worktrees, capped at
`max_parallel_phases = 3`. Verify in the plan output that every parallel phase
in a wave has disjoint `allowed_paths` and that none writes a global file. If
the plan reports a path or resource conflict, that wave does not run in parallel.

## Parallel mock run

Run the parallel mock at least once before the first live parallel run. The mock
exercises the DAG-wave scheduler, the worktree isolation, and the serial merge
queue with **no providers, no network, and no merge** (`FRONTIER_MOCK_PROVIDERS`).

```bash
just frontier-run-parallel-mock ALPHA_FEATURE_LABEL_FOUNDATION_V1 3
```

Confirm from the mock output that waves form as expected, that parallel phases
build concurrently in separate worktrees, and that merges are serialized one PR
at a time. The mock must not call Databento or IBKR and must not create real PRs
or merges.

## Parallel live run

After a clean plan and a successful mock, the live parallel run executes
concurrently in isolated worktrees with a serial merge queue. This is the
default execution path for this campaign.

```bash
# Live DAG-wave parallel run (concurrent build in isolated worktrees, serial merge).
# Run only after `just frontier-plan` is clean and a parallel mock has passed.
# just frontier-run-parallel ALPHA_FEATURE_LABEL_FOUNDATION_V1 3
```

The live run still makes **no external provider calls** — every phase consumes
local accepted DatasetVersions or synthetic fixtures. `max_parallel = 3` matches
`workflow2.scheduler.max_parallel_phases`. Phase branches use the `auto/` branch
prefix.

## Serial merge queue behavior

Build is parallel; **merge is always serial** (`merge_queue: serial`,
`parallel_build_serial_merge: true`). The coordinator merges one PR at a time,
re-validating the merge gate against the freshly updated `main` before each
merge. Only the coordinator updates `ACTIVE_CAMPAIGN.md`
(`update_active_campaign: coordinator_only`); a phase branch that writes
`ACTIVE_CAMPAIGN.md` in parallel mode is a global blocker. A merge that occurs
outside the serial merge queue is a global blocker.

## STOP behavior in parallel mode

Create `runs/<run_id>/STOP` with a short reason. Ralph checks STOP before
provider calls, phase selection, Codex execution, validation, review, PR
creation, CI waiting, the merge gate, merge, the done-check, and next-phase
selection.

```bash
echo "operator stop: <reason>" > runs/<run_id>/STOP
```

In parallel mode, a STOP request halts new wave dispatch and pauses the serial
merge queue at the next checkpoint. In-flight worktree builds may finish their
current step, but no new phase is dispatched and no further merge proceeds while
STOP is active. `runs/**` is local-only and must never be staged or committed.
Codex must not ignore an active STOP file inside a Workflow 2 run.

## FeatureRequest workflow

Every feature begins as a governance `FeatureRequest` (id prefix `freq_`), which
this campaign **consumes** — it does not re-implement the governance object
(R-022). The FeatureRequest carries `requested_inputs`, `formula_sketch`,
`availability_assumptions`, `duplicate_or_equivalent_exposure_notes`,
`data_requirements`, and `approval_status` in
`{PENDING, BLOCKED_DUPLICATE, NEEDS_REVIEW, APPROVED}`. The FeatureRequest gate
(`FLF-P05`) wires to `src/alpha_system/governance/feature_request.py` and the
duplicate-exposure guard; it must not duplicate them.

```bash
python -c "import alpha_system.features.request_gate"   # FLF-P05
# TARGET: alpha feature request submit --freq freq_<id>   (CLI surface lands in FLF-P28)
```

No feature may advance to `IMPLEMENTATION_ALLOWED` without an `APPROVED`
FeatureRequest. The prohibited MVP states (`ALPHA_VALIDATED`, `STRATEGY_READY`,
`LIVE_READY`, `PROFITABLE`, `TRADABLE`, `PRODUCTION_READY`) must never be
reachable.

## FeatureSpec workflow

A `FeatureSpec` and its `FeatureVersion` (`FLF-P06`) are required before any
feature value exists. Every feature value carries `available_ts`; no feature may
use a future or centered live window (centered/future windows are offline-only
for labels). Feature lifecycle states are `REQUESTED → SPEC_DRAFTED →
SPEC_VALIDATED → IMPLEMENTATION_ALLOWED → IMPLEMENTED → MATERIALIZATION_PLANNED →
MATERIALIZED_DRAFT → QUALITY_CHECKED → REGISTERED → READY_FOR_STUDY`, with
`REJECTED`, `QUARANTINED`, and `DEPRECATED` as off-ramps.

```bash
python -c "import alpha_system.features.contracts"      # FLF-P06
python -c "import alpha_system.features.primitives"     # FLF-P07 (causal transforms/windows)
# TARGET: alpha feature spec validate --spec <feature_spec_id>
```

Feature families fan out in parallel in w1: Base OHLCV (`FLF-P08`), BBO
tradability (`FLF-P09`), Session/Calendar/Roll (`FLF-P10`), Cross-Market
ES/NQ/RTY (`FLF-P11`), and Liquidity Sweep / Structure primitives (`FLF-P12`).
Required feature objects to name include FeatureSpec, FeatureFamily,
FeatureInputSpec, TransformSpec, WindowSpec, NormalizationSpec, FeatureSetSpec,
FeatureVersion, BBOFeatureSpec, SpreadFeatureSpec, MicropriceFeatureSpec,
TopBookImbalanceFeatureSpec, and LiquidityQualityFeatureSpec.

## LabelSpec workflow

A governance `LabelSpec` (id prefix `lspec_`) is required before any label
value. This campaign **consumes** the governance LabelSpec and
`label_leakage_guard`; it does not duplicate them (R-022). The LabelSpec carries
`horizon`, `path_rules`, `cost_model`, `target_stop_rules`, `availability_time`,
`forbidden_feature_overlap`, and `leakage_checks` (including `label_as_feature`
and `availability_time`). `FLF-P16` provides LabelSpec/LabelVersion contracts;
label families fan out in parallel in w3.

```bash
python -c "import alpha_system.labels.version"          # FLF-P16
# TARGET: alpha label spec validate --spec lspec_<id>
```

Label lifecycle states are `LABEL_REQUESTED → LABEL_SPEC_DRAFTED →
LABEL_SPEC_VALIDATED → MATERIALIZATION_ALLOWED → MATERIALIZED_DRAFT →
LEAKAGE_AUDITED → QUALITY_CHECKED → REGISTERED → READY_FOR_STUDY`, with
`REJECTED`, `QUARANTINED`, `DEPRECATED`. Label families: Fixed-Horizon / Midprice
Forward (`FLF-P17`), Cost-Adjusted / Spread-Adjusted (`FLF-P18`), Path:
MFE/MAE/Triple Barrier (`FLF-P19`), Strategy-Agnostic Event labels (`FLF-P20`).
Required label objects include LabelSpec, LabelFamily, LabelHorizonSpec,
LabelPathSpec, BarrierSpec, CostAdjustmentSpec, LabelVersion, and
LabelAvailabilityPolicy. A label value must never be exposed as a live feature.

## Materialization workflow

Materialization is planned then drafted, always local-only. The feature
materialization engine (`FLF-P13`) consumes accepted DatasetVersions and a
validated FeatureSpec to produce `FeatureValueRecord`s under `$ALPHA_DATA_ROOT`;
the FeatureStore/FeatureRegistry integration (`FLF-P14`) registers
`FeatureVersion` / `FeatureRegistryRecord` / `FeatureLineageRecord`. The label
materialization engine (`FLF-P21`) and LabelStore/LabelRegistry integration
(`FLF-P22`) mirror this for labels.

```bash
python -c "import alpha_system.features.engine"         # FLF-P13
python -c "import alpha_system.features.registry"       # FLF-P14
python -c "import alpha_system.labels.engine"           # FLF-P21
python -c "import alpha_system.labels.registry"         # FLF-P22
# TARGET: alpha feature materialize --spec <id> --dataset dsv_databento_ohlcv_<hex> --dry-run
# TARGET: alpha label materialize   --spec lspec_<id> --dataset dsv_databento_ohlcv_<hex> --dry-run
```

Materialized feature and label **values are never committed**. The FeatureStore
and LabelStore are not dumping grounds: duplicate or equivalent exposure must be
recorded (`DuplicateExposureReport` / `EquivalentFeatureGroup`).

## Feature quality report

Feature quality and coverage reports (`FLF-P15`) produce `FeatureQualityReport`
and `FeatureCoverageReport`. A good quality report is not production readiness.

```bash
python -c "import alpha_system.features.reports"        # FLF-P15
test -f docs/feature_label_foundation/FEATURE_REPORTS.md
# TARGET: alpha feature report --spec <id> --dataset dsv_databento_ohlcv_<hex>
```

Reports describe coverage and quality of the substrate only; they make no
alpha, tradability, or profitability claim.

## Label quality report

Label quality and coverage reports produce `LabelQualityReport` and
`LabelCoverageReport`, alongside the leakage audit report below. Label reports
must surface availability and horizon coverage without exposing future
information as a feature.

```bash
# TARGET: alpha label report --spec lspec_<id> --dataset dsv_databento_ohlcv_<hex>
test -f docs/feature_label_foundation/LABEL_STORE.md
```

## Leakage audit

Label leakage and availability audits (`FLF-P23`) produce a
`LabelLeakageAuditReport` and enforce the `label_leakage_guard`: no
label-as-feature, and `label_available_ts` present and respected for every
label. Future data is permitted **only** inside labels (never as a live
feature), and centered/future windows are offline-only.

```bash
python -c "import alpha_system.labels.leakage_audit"    # FLF-P23
test -f docs/feature_label_foundation/LABEL_LEAKAGE_AUDIT.md
python -m pytest tests/no_lookahead/feature_label -q
# TARGET: alpha label leakage-audit --spec lspec_<id>
```

A label exposed as a live feature, a missing `label_available_ts`, or a
future/centered live-window feature is a global merge blocker.

## Duplicate exposure audit

The FeatureRequest gate (`FLF-P05`) wires to the governance duplicate-exposure
guard. Equivalent exposures are grouped (`EquivalentFeatureGroup`) and recorded
(`DuplicateExposureReport`); a FeatureRequest that duplicates an existing
exposure resolves to `BLOCKED_DUPLICATE` and does not silently create a
redundant feature.

```bash
python -c "import alpha_system.features.request_gate"   # FLF-P05
# TARGET: alpha feature duplicate-audit --freq freq_<id>
```

Allowing duplicate exposure without a recorded
`DuplicateExposureReport`/`EquivalentFeatureGroup` is a global blocker.

## BBO missingness audit

BBO missingness is flagged, never silently forward-filled. The quality-flag
tokens in `quality_flags` are `missing_bbo` (missing/bad quote) and
`bbo_quarantined` (crossed/abnormal, non-blocking). There is **no**
`bad_quote_flag` column by that literal name. BBO invariants:
`mid == (bid + ask) / 2`, `spread == ask - bid`, `ask >= bid`,
`available_ts >= bar_end_ts`, and `bid <= microprice <= ask`. Microprice
requires valid bid/ask sizes.

```bash
python -c "import alpha_system.features.semantics"      # FLF-P04
python -m pytest tests/unit/features -q
test -f docs/feature_label_foundation/DENSE_GRID_AND_BBO_SEMANTICS.md
```

A silently forward-filled missing BBO, or a synthetic no-trade row treated as a
trade bar, is a global merge blocker. Dense-grid no-trade synthetic rows have
`has_trade = False`, `synthetic = True`, `fill_method = "previous_close"`,
`volume == 0`, the `no_trade` quality token, and `provider_bar_ref = None`; they
must never be treated as trade bars.

## Partition contamination audit

Partitions: development `2018-01-01..2022-12-31`, validation
`2023-01-01..2024-12-31`, locked_test_candidate `2025-01-01..as_of_run`, and an
optional latest_shadow_candidate. Any use of the locked-test partition requires
governance contamination metadata via
`require_governance_metadata_for_locked_partition_use(...)`; partition
contamination must be recorded.

```bash
# locked-test partition use must carry governance contamination metadata
# TARGET: alpha feature materialize --partition locked_test_candidate --require-contamination-metadata
```

Locked-test partition use without contamination metadata is a global blocker.

## Synthetic tests

Synthetic fixtures and fail-closed tests (`FLF-P25`) live under
`tests/fixtures/feature_label/**` and `tests/no_lookahead/feature_label/**`.
Fixtures are tiny, synthetic, deterministic, and documented — never real market
data and never alpha evidence. The no-lookahead suite asserts causal primitives,
`available_ts` keying, and fail-closed BBO/leakage behavior.

```bash
python -m pytest tests/no_lookahead/feature_label -q    # FLF-P25
python -m pytest tests/unit/features -q
test -f docs/feature_label_foundation/fixtures.md
python tools/hooks/canary_runner.py
```

Do not weaken tests, skip checks, or add visible test-only branches without spec
authorization; test weakening or gaming is a global blocker.

## Small real DatasetVersion dry run

`FLF-P26` (Small Real Databento DatasetVersion Dry Run) runs alone
(`must_run_alone: true`). It exercises the full path against **one small
accepted Databento DatasetVersion**, end to end, with **no external provider
call** — the DatasetVersion is already local and accepted. Outputs are
local-only under `$ALPHA_DATA_ROOT`; no values are committed.

```bash
export ALPHA_DATA_ROOT=~/alpha_data/alpha_system
python -m pytest tests/integration/feature_label -q     # FLF-P26
test -f docs/feature_label_foundation/DRY_RUN_DATABENTO.md
# TARGET: alpha feature dry-run --dataset dsv_databento_ohlcv_<hex> --small --local-only
```

After the dry run, re-run the artifact inspection below and confirm nothing
leaked into the repo.

## Handoff validation

Every phase writes a commit-eligible handoff under
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/<PHASE_ID>.md` plus a local-only
`runs/<run_id>/phases/<phase_id>/handoff.md`. The handoff must list explicit
staged paths, record `git status --short`, document any skipped checks with the
reason, and state the artifact-policy result. A handoff that omits the explicit
file list or hides forbidden paths fails validation.

```bash
cat handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/<PHASE_ID>.md
ls runs/<run_id>/phases/<phase_id>/
```

A `BLOCKED` verdict, missing authorization, contradictory scope, or impossible
validation produces a **truthful** blocked handoff; dependent phases are
blocked; fake completion is forbidden.

## Claude review

Every YELLOW phase requires a fresh Claude Opus 4.8 xhigh review before merge;
the implementer cannot self-approve. GREEN phases (`FLF-P00`, `FLF-P29`) do not
require review unless the phase requests it. The review writes
`runs/<run_id>/phases/<phase_id>/review.md` and `verdict.json` for local audit,
and a commit-eligible review under
`reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/<PHASE_ID>/**` when commit-eligible.
Allowed verdicts: `PASS`, `PASS_WITH_WARNINGS`, `REWORK`, `BLOCKED`. Only `PASS`
or `PASS_WITH_WARNINGS` are merge-eligible.

Review must check: phase scope; feature/label object completeness; no raw
provider access from feature/label code; only accepted DatasetVersions consumed
via `resolve_dataset_version`; FeatureRequest gate and duplicate-exposure guard
wired to governance (not re-implemented); FeatureSpec/LabelSpec present before
values with `available_ts` / `label_available_ts`; no label-as-feature and no
future/centered live windows; BBO missingness flagged with no silent
forward-fill and synthetic no-trade rows never treated as trades; locked-test
partition use carries contamination metadata; no FeatureStore/LabelStore dumping
ground; governance objects consumed not duplicated; DAG metadata correctness
(parallel phases have disjoint `allowed_paths`, no global files); serial merge
queue respected and no phase-branch `ACTIVE_CAMPAIGN.md` write in parallel mode;
artifact policy compliance; no broker/live/paper/order/account or
strategy/backtest/portfolio scope; no alpha/tradability/profitability claims; no
test weakening; handoff completeness and semantic done criteria.

```bash
ls reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/
cat runs/<run_id>/phases/<phase_id>/verdict.json
```

## Repair loop

A `REWORK` or check `FAIL` routes to the bounded repair loop
(`max_repair_attempts_default = 2`). Each attempt is recorded under
`runs/<run_id>/phases/<phase_id>/repair_attempts/`. Codex repairs only valid,
in-scope findings; it must not weaken tests or fake completion. Exceeding the
repair limit, contradictory scope, or repeated failure produces a truthful
blocked handoff and escalation rather than a fake pass.

```bash
ls runs/<run_id>/phases/<phase_id>/repair_attempts/
```

## CI wait

After PR creation Ralph waits on CI when CI is configured
(`ci_pass_if_configured`). CI runs only CI-safe checks — `python tools/verify.py
--smoke`, the relevant `pytest` suites, and the canary runner — and never makes
an external provider call or a real data pull. A failing CI run routes back to
the repair loop or a blocked handoff.

```bash
python tools/verify.py --smoke
python tools/hooks/canary_runner.py
```

## Merge gate

YELLOW phases auto-merge through the serial merge queue once **all** of the
following hold: checks pass; handoff valid; Claude review complete with a `PASS`
or `PASS_WITH_WARNINGS` verdict; artifact policy passes; no forbidden paths; no
STOP file; semantic done-check passes; and CI passes if configured. GREEN phases
auto-merge on the same gate minus the Claude-review requirement. Re-validate the
artifact audit immediately before each merge.

```bash
git status --short
git ls-files runs
find data -type f ! -name README.md ! -name .gitkeep -print
find metadata -type f ! -name README.md ! -name .gitkeep -print
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
```

Global merge blockers include: STOP file present; forbidden / raw / canonical /
feature-or-label-value / provider-response / heavy / local-DB path staged;
external provider call attempted; raw provider data read by feature/label code;
accepted DatasetVersion bypassed; feature without `available_ts`; label without
`label_available_ts`; label values exposed as live features; future/centered
live window used as a feature; FeatureRequest/FeatureSpec/LabelSpec bypassed;
duplicate exposure without a record; missing BBO silently forward-filled;
synthetic no-trade row treated as a trade bar; locked-test partition used without
contamination metadata; broker/live/paper/order/account or strategy/backtest/
portfolio scope introduced; unsupported alpha/tradability claim; a parallel phase
lacking disjoint `allowed_paths`; a phase branch writing `ACTIVE_CAMPAIGN.md` in
parallel mode; a merge outside the serial merge queue; test weakening; or a
failed semantic done-check.

## Resume behavior

Remove or resolve the STOP condition, then resume. Ralph resumes from recorded
run state and does not regenerate completed, merged work. In parallel mode it
re-derives ready waves from the DAG and the merge ledger rather than restarting
the campaign.

```bash
rm runs/<run_id>/STOP
# resume the live parallel run (only after a clean plan and prior mock):
# just frontier-run-parallel ALPHA_FEATURE_LABEL_FOUNDATION_V1 3
```

For a partially merged wave, resume continues from the serial merge queue
position; already-merged phases are not rebuilt.

## Artifact inspection

`runs/**` is local-only runtime state and must never be staged or committed.
Raw, canonical, feature, and label values stay local-only under
`$ALPHA_DATA_ROOT`. Run this audit at preflight, before every merge, and after
the small real dry run.

```bash
git ls-files runs .frontier/upgrade_reports
find data -type f ! -name README.md ! -name .gitkeep -print
find metadata -type f ! -name README.md ! -name .gitkeep -print
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
# reject committed DB/log/heavy formats outside fixtures
git ls-files | grep -E '\.(sqlite|sqlite3|db|db-journal|wal|parquet|arrow|feather|dbn|zst|log)$' \
  | grep -v '^tests/fixtures/' || echo "no committed heavy/db/log artifacts"
```

If any forbidden path is staged, unstage it and repair the handoff before merge.
Stage explicit paths only; never `git add .` / `git add -A`. Never force push.

## Final closeout

`FLF-P30` (End-to-End Feature/Label Dry Run, runs alone) and `FLF-P31`
(Workflow 2 Acceptance Audit and Closeout, runs alone) finish the campaign.

```bash
python tools/verify.py --smoke
python tools/verify.py --all
python -m pytest tests/integration/feature_label -q
python tools/hooks/canary_runner.py
test -f docs/feature_label_foundation/E2E_DRY_RUN.md
test -f campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1/CLOSEOUT.md
git ls-files runs
find data -type f ! -name README.md ! -name .gitkeep -print
find metadata -type f ! -name README.md ! -name .gitkeep -print
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
```

At closeout: run the synthetic end-to-end dry run (no external pull); run the
acceptance audit across all nine gates (`ACCEPTANCE.md`); run the final semantic
done-check; write
`campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1/CLOSEOUT.md` with the final verdict
(`COMPLETE`, `COMPLETE_WITH_WARNINGS`, or `BLOCKED`); update
`ACTIVE_CAMPAIGN.md` (coordinator-only); and add durable lessons to
`project-skill` when applicable. The campaign is done only when all gates pass
(or a truthful `BLOCKED` is recorded), the artifact audit is clean, and no
prohibited scope or claim exists.

## Next campaign readiness for Agent Factory

This campaign is the substrate that the future `ALPHA_AGENT_FACTORY_MVP`
consumes: future AI Alpha Researchers read a FeatureSet plus a LabelSet through a
governance `StudySpec` (`sspec_`, referencing an AlphaSpec `aspec_` and a
LabelSpec `lspec_` plus dataset_scope, split_protocol, metrics, cost_assumptions,
variant_budget, locked_test_policy, negative_controls, and stopping_rules). The
StudySpec Input Pack delivered in `FLF-P27`
(`alpha_system.governance.study_input_pack`) is a **new additive helper** that
bundles `freq_` / `lspec_` / `aspec_` handles plus a dataset_scope that a
StudySpec references; it must **not** modify the StudySpec schema or existing
governance modules.

Roadmap: Data Foundation → Feature/Label Foundation → Agent Factory → Core Alpha
→ Strategy/Portfolio. Readiness for the Agent Factory means the substrate exists
and is governed; it does **not** mean any feature or label is alpha, profitable,
tradable, strategy-ready, production-ready, or paper/live/broker-ready. Each
downstream campaign proceeds only under its own authorized contract. Use precise
wording: a feature is not alpha, a label is not alpha, a FeatureStore is not a
factor library, and an accepted DatasetVersion does not imply alpha validated.
