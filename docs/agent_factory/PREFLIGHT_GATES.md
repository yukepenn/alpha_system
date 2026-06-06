# Agent Factory Preflight Gates

`alpha_system.agent_factory.entry_contract` is the single sanctioned Agent
Factory entry contract. It evaluates four local-first gates and returns a
structured `PREFLIGHT_PASS`, `PREFLIGHT_WARN`, or `PREFLIGHT_BLOCKED` result.

The contract is an entry check only. It does not instantiate an agent, start a
runner, read raw provider files, open registry contents, query market data, call
an external provider, or edit runtime/governance/registry primitives. Passing
entry means only that the declared gate inputs are satisfied for the requested
scope. It does not mean any agent has run, any diagnostic passed, or any alpha
exists.

## Result Shape

`AgentFactoryPreflightResult` carries:

- `status`: top-level `PREFLIGHT_PASS`, `PREFLIGHT_WARN`, or
  `PREFLIGHT_BLOCKED`;
- `gates`: one structured `GateResult` for each gate;
- `blocking_findings`: the subset that forced `PREFLIGHT_BLOCKED`;
- `limitations`: truthful warnings and scope constraints;
- `next_required_gate`: the next gate an operator must satisfy, or `None`.

All fields are value-free. They contain gate names, status strings, reasons,
scope blockers, and follow-up identifiers, not DB rows, raw/heavy data, provider
payloads, or registry values.

## Gates

### 1. Seed FeaturePack/LabelPack Registries

Input: `$ALPHA_DATA_ROOT/registry/features.sqlite` and
`$ALPHA_DATA_ROOT/registry/labels.sqlite`, with paths overridable through the
preflight config.

Semantics:

- `PASS`: both registry marker files exist.
- `WARN`: `ALPHA_DATA_ROOT` is unset, or one or both marker files are absent.
- `BLOCKED`: not used for clean-checkout absence.

This gate performs existence checks only. It never opens either registry and
never reads rows or market data. Clean checkouts and CI commonly lack local
registries, so absence degrades truthfully to `PREFLIGHT_WARN`.

### 2. Runtime Real Smoke

Input: recorded `real_dataset_version_smoke_ran` status from declarative config
or an injected marker source. The runtime is not re-run by this contract.

Semantics:

- `PASS`: the recorded status is `true`.
- `WARN`: the status source is unknown or absent.
- `BLOCKED`: the recorded status is `false` or the configured marker is
  malformed.

An explicit unsatisfied status fails closed because Agent Factory entry must not
claim the runtime real smoke gate is satisfied when it is not.

### 3. `FEATURE_LABEL_PARQUET_SINK_V1`

Input: declared `parquet_sink_landed` status, defaulting to `false`.

Semantics:

- `PASS`: `FEATURE_LABEL_PARQUET_SINK_V1` is marked landed.
- `WARN`: the follow-up is not landed at plain session entry.
- `BLOCKED`: a large-scale value-consuming study is requested before the
  follow-up lands and no explicit human approval flag is recorded.

The warning carries the hard scope blocker: large-scale value-consuming studies
remain blocked until `FEATURE_LABEL_PARQUET_SINK_V1` lands or explicit human
approval is recorded.

### 4. `SESSION_LABEL_GUARD_FIX_V1`

Input: declared `session_label_guard_fixed` status, defaulting to `false`.

Semantics:

- `PASS`: `SESSION_LABEL_GUARD_FIX_V1` is marked fixed.
- `WARN`: the follow-up is not fixed at plain session entry.
- `BLOCKED`: `rth_flag`, `eth_flag`, or `session_minute` is requested before
  the guard fix lands or those fields are explicitly marked available.

The warning carries the hard scope blocker: session-context features remain
blocked because the runtime guard currently false-positives on the canonical
`session_label` field.

## Fail-Closed Policy

The contract never reports a gate as satisfied unless its declared inputs prove
that state. Explicitly unsatisfied prerequisites return `PREFLIGHT_BLOCKED`.
Local-only seed registries are the clean-checkout exception: absence is reported
as `PREFLIGHT_WARN` with a limitation because the checkout can still evaluate
contracts without local registry contents.

## Default Config

`configs/agent_factory/preflight.toml` supplies value-free defaults:

- registry marker paths relative to `$ALPHA_DATA_ROOT`;
- `real_dataset_version_smoke_ran = true` from the recorded runtime smoke;
- `parquet_sink_landed = false`;
- `session_label_guard_fixed = false`;
- request-scope flags defaulted to false/empty.

Tests may inject every input with `AgentFactoryPreflightConfig` or a mapping, so
the gate behavior is deterministic on synthetic fixtures.

