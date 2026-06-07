# Agent Factory Operator Guide

This guide is for operating the Agent Factory contract layer as it exists after
AGENT-P20. It documents available read-only checks and planned target surfaces.
It does not introduce a command, instantiate an agent, start a continuous
runner, run alpha search, or authorize paper, live, broker, order, account, or
deployment behavior.

## Preflight Gates

The sanctioned entry contract is documented in
[PREFLIGHT_GATES.md](PREFLIGHT_GATES.md). It evaluates four gates and returns a
structured `PREFLIGHT_PASS`, `PREFLIGHT_WARN`, or `PREFLIGHT_BLOCKED` result:

1. Seed FeaturePack and LabelPack registry marker files exist under
   `$ALPHA_DATA_ROOT`.
2. The recorded Research Runtime real smoke status is
   `real_dataset_version_smoke_ran: true`.
3. `FEATURE_LABEL_PARQUET_SINK_V1` status is checked.
4. `SESSION_LABEL_GUARD_FIX_V1` status is checked.

The gates are fail-closed: an explicitly unsatisfied prerequisite must not be
reported as satisfied. The clean-checkout and CI exception is local registry
absence under `$ALPHA_DATA_ROOT`; because those registries are local-only, the
entry contract degrades truthfully to `PREFLIGHT_WARN` with limitations instead
of crashing or pretending the registry contents exist.

## Running The Bounded Non-Alpha Dry-Run

The bounded Agent Factory dry-run harness is planned for AGENT-P22 and
AGENT-P23. Until those phases land, the following command names are TARGET
surfaces only and must not be treated as built commands:

```bash
# TARGET, not yet built:
alpha agent preflight
alpha agent dry-run --mode synthetic
alpha agent dry-run --mode seed-pack --bounded
alpha agent dry-run summarize --request-id <request_id>
```

The read-only validation commands that exist today are:

```bash
python tools/verify.py --smoke
test -f docs/agent_factory/GUIDE.md
test -f docs/agent_factory/OPERATOR.md
test -f docs/agent_factory/NEXT_CORE_ALPHA_PILOT_READINESS.md
test -f README.md
git ls-files runs
```

Operators can also use the existing Research Runtime CLI help and summary
surfaces when working with local runtime payloads:

```bash
alpha runtime --help
alpha runtime plan --help
alpha runtime validate-inputs --help
alpha runtime summarize --help
```

The runtime CLI is documented in
[../research_runtime/CLI.md](../research_runtime/CLI.md). It remains the runtime
surface the future bridge consumes; this operator guide does not add an
alternate runtime path.

## Reading `AgentToolResult`

Every agent-facing tool result is documented in [TOOLS.md](TOOLS.md) and uses a
single value-free envelope. The fields are:

- `status`
- `role`
- `request_id`
- `alpha_spec_id`
- `study_spec_id`
- `dataset_version_id`
- `feature_pack_refs`
- `label_pack_refs`
- `runtime_run_id`
- `diagnostics_summary`
- `cost_summary`
- `rejection_reasons`
- `blocking_findings`
- `next_required_gate`
- `artifacts`
- `limitations`

These fields carry ids, refs, statuses, short summaries, reasons, blocker refs,
artifact refs, limitations, and next gates only. Results never embed raw market
data, canonical data, feature values, label values, runtime value tables,
provider payloads, local registry rows, SQLite databases, parquet/arrow/feather
files, logs, caches, model binaries, or other heavy data.

## Interpretation Discipline

Use the language in
[../RESEARCH_INTERPRETATION_POLICY.md](../RESEARCH_INTERPRETATION_POLICY.md)
when reading any dry-run or tool result:

- A seed-pack or synthetic dry-run is not alpha evidence.
- An `EvidenceDraft` is not a candidate.
- A `ReferenceCandidateHandoff` is not Reference validation.
- A runtime diagnostic `PASS` is not factor promotion.
- A reviewer verdict inside this campaign is not risk, capital, paper, live, or
  broker approval.

Large-scale value-consuming studies are blocked until
`FEATURE_LABEL_PARQUET_SINK_V1` lands or receives separate human authorization.
Session-context features (`rth_flag`, `eth_flag`, `session_minute`) are blocked
until `SESSION_LABEL_GUARD_FIX_V1` lands or those fields are explicitly marked
available by a reviewed follow-up.

## Artifact Locations

`runs/**` is local-only runtime state. It can contain Workflow 2 state, checks,
notes, local handoffs, reviews, repair attempts, and summaries, but it must not
be committed.

Raw, canonical, feature, label, runtime, and agent values stay local-only under
`$ALPHA_DATA_ROOT` or other local runtime locations authorized by the relevant
contract. Data-like artifacts, local DBs, provider responses, heavy binaries,
logs, and caches are not committed. Agent Factory docs and handoffs may commit
ids, refs, summaries, statuses, blockers, and limitations; they must not commit
values.
