# FUTCORE-P17 Handoff - VWAP / Session Diagnostics

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`
Phase: `FUTCORE-P17`
Family: `vwap_session`
Lane: Yellow

## Scope Completed

Generated value-free VWAP/session diagnostics artifacts for the two
`vwap_session` StudySpecs selected from the FUTCORE-P14 StudySpec pack:

- `sspec_ab3cbb830a2cede5485de19b` / `aspec_b40aee52d4399dd5b855a6ed`
- `sspec_8b8037013e7b3c14fd5b2844` / `aspec_43cd6c154bca2fcc419eee83`

Diagnostics ran through the Research Runtime tool surface:

- `RuntimeInputPack` resolver
- `build_factor_diagnostics_run`
- `build_label_diagnostics_report`
- `build_session_split_report`
- `SignalProbeSpec` contract gate
- `build_cost_sensitivity_report`
- `RuntimeToolResult`
- `RuntimeRunSummary`

The runtime resolved the locked P03/P14 DatasetVersion, the two session-context
FeaturePacks, and the locked 5m LabelPack. Research-scale values were loaded
from registry-resolved Parquet packs in memory. No raw provider path, external
provider call, arbitrary data path, consumed primitive edit, source primitive
change, broker call, live/paper action, PR, merge, or reviewer call was made.

## Runtime Outcome

- Label diagnostics completed for the locked 5m LabelPack.
- Session split diagnostics are value-free and inconclusive where split samples
  are thin or unavailable.
- VWAP factor diagnostics failed descriptively because no locked running or
  completed VWAP FeaturePack is bound to the RuntimeInputPack.
- Signal-probe diagnostics are blocked by the runtime contract for the same
  missing locked VWAP FeaturePack.
- The 10m, 15m, and 30m horizon cells are blocked for evidence because P15
  created governed LabelSpecs but the P03/P14 locked input pack does not bind
  Parquet LabelPacks for those horizons.
- Cost diagnostics cover `zero_cost` as diagnostic-only plus `base`,
  `stress_1`, `stress_2`, and `double_cost`; thin-session penalty metadata is
  recorded for ETH/pre_RTH/post_RTH style views. Zero-cost is not a promotion
  basis.

## Running vs Final VWAP Handling

Running VWAP was treated as admissible only if supplied as a point-in-time
running aggregate with `available_ts` not later than the decision timestamp.
Final-session VWAP was not used intraday. Completed ETH VWAP may be used only
after the ETH session completes. Because the locked input pack does not bind a
running or completed VWAP FeaturePack, P17 did not approximate VWAP from bars or
session metadata and marked the factor/signal outputs blocked instead.

The session guard was respected: session-context FeaturePacks were used only as
runtime-resolved point-in-time inputs, and label `label_available_ts` remained an
outcome guard rather than an intraday feature.

## Files Written Or Updated

Codex staged no files. Ralph should stage only explicit allowed paths if this
phase proceeds.

- `README.md`
- `docs/futures_core_alpha_pilot/diagnostics/vwap_session.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P17.md`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/INDEX.md`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/summary.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/session_horizon_matrix.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/cost_profile_matrix.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_ab3cbb830a2cede5485de19b/runtime_input_resolution.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_ab3cbb830a2cede5485de19b/factor_diagnostics.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_ab3cbb830a2cede5485de19b/label_diagnostics.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_ab3cbb830a2cede5485de19b/session_split_diagnostics.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_ab3cbb830a2cede5485de19b/signal_probe_blocked.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_ab3cbb830a2cede5485de19b/cost_stress.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_ab3cbb830a2cede5485de19b/runtime_tool_result.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_ab3cbb830a2cede5485de19b/runtime_run_summary.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_ab3cbb830a2cede5485de19b/session_horizon_matrix.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_8b8037013e7b3c14fd5b2844/runtime_input_resolution.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_8b8037013e7b3c14fd5b2844/factor_diagnostics.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_8b8037013e7b3c14fd5b2844/label_diagnostics.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_8b8037013e7b3c14fd5b2844/session_split_diagnostics.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_8b8037013e7b3c14fd5b2844/signal_probe_blocked.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_8b8037013e7b3c14fd5b2844/cost_stress.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_8b8037013e7b3c14fd5b2844/runtime_tool_result.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_8b8037013e7b3c14fd5b2844/runtime_run_summary.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_8b8037013e7b3c14fd5b2844/session_horizon_matrix.json`

No `runs/**` artifact was written for commit eligibility. No review artifact,
`review.md`, or `verdict.json` was created by Codex per executor instructions;
Ralph owns review routing.

## Commands Run

All commands ran from
`/home/yuke_zhang/projects/alpha_system-alpha_futures_core_alpha_pilot_v1-futcore-p17`.

1. STOP check:

   ```bash
   test ! -f runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/STOP && test ! -f runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/phases/FUTCORE-P17/STOP
   ```

   Result: exit 0.

2. Runtime diagnostics driver:

   ```bash
   PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python - <<'PY'
   # inline FUTCORE-P17 runtime diagnostics driver
   PY
   ```

   Result: exit 0. The inline driver resolved both StudySpecs through the
   runtime input resolver, loaded registry-resolved Parquet values in memory,
   invoked the runtime diagnostics/tool-result surfaces listed above, and wrote
   value-free reports. Summary output:

   ```json
   {"joined_5m_observation_count": 6862, "output_dir": "research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session", "status": "generated", "study_count": 2}
   ```

3. Runtime aggregate cost-marker sync:

   ```bash
   PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python - <<'PY'
   # structured JSON sync of cost refs and zero_cost_diagnostic_only markers
   PY
   ```

   Result: exit 0. Updated both `runtime_tool_result.json` and
   `runtime_run_summary.json` files so their cost report refs and
   `zero_cost_diagnostic_only` markers match the standalone cost reports.

4. Spec command skipped by executor override:

   ```bash
   git status --short
   ```

   Result: skipped. The user executor instructions explicitly forbade Codex from
   running `git status`.

5. Runtime import check, exact spec command:

   ```bash
   python -c "import alpha_system.runtime.tool_results"
   ```

   Result: exit 1. Default interpreter does not have the package installed:
   `ModuleNotFoundError: No module named 'alpha_system'`.

6. Runtime import check, repo source path fallback:

   ```bash
   PYTHONPATH=src python -c "import alpha_system.runtime.tool_results"
   ```

   Result: exit 0.

7. Runtime import check, research venv fallback:

   ```bash
   PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -c "import alpha_system.runtime.tool_results"
   ```

   Result: exit 0.

8. Smoke verification:

   ```bash
   python tools/verify.py --smoke
   ```

   Result: exit 0, no output.

9. Canary verification:

   ```bash
   python tools/hooks/canary_runner.py
   ```

   Result: exit 0. Output ended with `All Frontier canaries passed.`

10. Diagnostics directory exists:

    ```bash
    test -d research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session
    ```

    Result: exit 0.

11. Family diagnostics doc exists:

    ```bash
    test -f docs/futures_core_alpha_pilot/diagnostics/vwap_session.md
    ```

    Result: exit 0.

12. Commit-eligible handoff exists:

    ```bash
    test -f handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P17.md
    ```

    Result: exit 0.

13. Run artifact audit:

    ```bash
    git ls-files runs
    ```

    Result: exit 0, empty output.

14. Required heavy/provider tracked-file audit:

    ```bash
    git ls-files '**/*.parquet' '**/*.sqlite' '**/*.dbn' '**/*.zst'
    ```

    Result: exit 0, empty output.

15. Extended heavy tracked-file audit:

    ```bash
    git ls-files '**/*.arrow' '**/*.feather' '**/*.sqlite3' '**/*.db' '**/*.db-journal' '**/*.wal'
    ```

    Result: exit 0, empty output.

16. P17 report-tree heavy-file audit:

    ```bash
    find research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session -type f \( -name '*.parquet' -o -name '*.arrow' -o -name '*.feather' -o -name '*.sqlite' -o -name '*.sqlite3' -o -name '*.db' -o -name '*.dbn' -o -name '*.zst' -o -name '*.wal' -o -name '*.log' \) -print
    ```

    Result: exit 0, empty output.

17. Value-payload marker audit:

    ```bash
    rg -n "feature_value|label_value|raw_values|value_table|value_array|per_row_values|per_row_payloads_embedded\": true" research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session docs/futures_core_alpha_pilot/diagnostics/vwap_session.md
    ```

    Result: exit 1 with empty output, meaning no matches.

18. Review artifact check:

    ```bash
    find reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P17 -maxdepth 3 -type f -print
    ```

    Result: exit 1, path does not exist. No review artifacts were created by
    Codex, per executor instructions.

19. Cached-diff audit skipped by executor override:

    ```bash
    git diff --cached --name-only
    ```

    Result: skipped. The user executor instructions explicitly forbade Codex from
    running `git diff`; Codex also ran no staging command. Ralph must perform the
    authoritative staged-set audit before any commit or merge-gate evaluation.
