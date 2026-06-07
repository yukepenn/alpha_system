# Agent Factory Dry Run Results

## Outcome

Recorded verdict: `PASS_WITH_WARNINGS`.

Path run in this executor environment: synthetic fixture fallback. `ALPHA_DATA_ROOT`
was unset, so the integration dry run recorded the missing local seed registry
markers as warnings and used the deterministic synthetic resolver path.

Reproduce command:

```bash
python -m pytest tests/integration/agent_factory -q
```

## What Was Exercised

The integration test drives the bounded Agent Factory dry-run harness through
the non-alpha lifecycle: scoped task, draft refs, critique, DatasetVersion
resolution gate, feature/label refs, runtime bridge adaptation, no-lookahead
review, statistical rejection, and rejected-idea memory.

It asserts that role tool invocations resolve through the registered tool
contracts, tool outputs are structured `AgentToolResult` envelopes, the most
advanced forward state is `REFERENCE_HANDOFF_RECORDED`, no promotion state is
reachable, and rejected ideas remain visible through memory records.

## Limitations

This result proves machinery only. A seed-pack or synthetic dry run is not alpha
evidence. An `EvidenceDraft` is not a candidate, and a
`ReferenceCandidateHandoff` is not Reference validation.

The dry run uses ids, refs, summaries, statuses, warnings, rejection reasons,
artifact refs, and next gates only. It does not consume raw or heavy data, make
external provider calls, materialize feature or label values, instantiate an
autonomous agent, start a continuous research runner, promote a factor, route
orders, or use broker/live/paper/account scope.
