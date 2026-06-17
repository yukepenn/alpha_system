# Repo Integrity Sweep V1 - Validation Report

Status: complete.

## Completed Checks

| Command | Result |
| --- | --- |
| `pytest tests/unit/cli/test_idea_cli.py tests/unit/research_lane/test_fast_probe.py tests/unit/research_lane/test_testability_gate.py tests/unit/research_lane/test_environment_preflight.py -q` | PASS, 69 passed |
| `ruff check src/alpha_system/research_lane/pack_pin_audit.py src/alpha_system/research_lane/fast_probe.py src/alpha_system/research_lane/testability_gate.py src/alpha_system/cli/idea.py tests/unit/cli/test_idea_cli.py tests/unit/research_lane/test_fast_probe.py tests/unit/research_lane/test_testability_gate.py` | PASS |
| `PYTHONPATH=src python -m alpha_system.governance.canaries.pack_pin_validate_not_datagap` | PASS |
| `python tools/hooks/canary_runner.py` | PASS |
| `python tools/frontier/status_doctor.py` | PASS / VERDICT OK |
| `python tools/frontier/data_inventory.py` | PASS; 2168 materialized partitions, 24 config-lock vs disk-presence disagreements flagged |
| `python tools/verify.py --smoke` | PASS |
| `pytest tests/unit/test_l2_artifact_policy.py::test_no_l2_db_or_columnar_artifacts_are_present -q` | PASS after local run-log suffix cleanup |
| `python tools/verify.py --all` | PASS; 3884 passed, 80 skipped; canaries passed |
| `git ls-files runs` | PASS; no tracked `runs/**` |

## Notes

The first `python tools/verify.py --all` run failed one artifact-policy test due
to old ignored `runs/**.log` files. Those logs were preserved as `.log.txt`;
the targeted test then passed and the second full `verify --all` passed.

`research/intraday_system_custody_v0/` is preserved as untracked, unrelated
research/custody content and intentionally not staged.
