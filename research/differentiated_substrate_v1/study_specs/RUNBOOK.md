# DK-P02 Track A StudySpec Surrogate-FDR Runbook

Value-free runbook. It records ids, counts, seeds, CLI shapes, and gate requirements only; it contains no IC, return, diagnostic, signal, or cost values.

## Pre-Registered Calibration

- K per perturbation config: `60`.
- Perturbations: `trade_date_block_shuffle`, `trade_date_block_bootstrap`.
- Required gate: `zero-pass-met`.
- Reports: `research/differentiated_substrate_v1/surrogate_fdr/<mechanism>_calibration.md`.

## Study CLI Invocations

### day_of_week

```bash
python tools/discovery_rigor_floor/run_real_surrogate_calibration.py \
  --study-spec /home/yuke_zhang/projects/alpha_system-differentiated_killshot_v1-dk-p02/research/differentiated_substrate_v1/study_specs/day_of_week.json \
  --alpha-data-root /home/yuke_zhang/alpha_data/alpha_system \
  --namespace /home/yuke_zhang/alpha_data/alpha_system/rigor_p05_surrogate_dk_p02_day_of_week \
  --runs-per-config 60 --base-seed 42020 \
  --report-out research/differentiated_substrate_v1/surrogate_fdr/day_of_week_calibration.md
```

- StudySpec: `sspec_2ec71d30dadc48e237f9d04c`
- Feature locks: `24`
- Label locks: `24`
- Missing feature locks: `0`
- Lock status: `LOCKED`
- Calibration verdict: `zero-pass-met`

### opex

```bash
python tools/discovery_rigor_floor/run_real_surrogate_calibration.py \
  --study-spec /home/yuke_zhang/projects/alpha_system-differentiated_killshot_v1-dk-p02/research/differentiated_substrate_v1/study_specs/opex.json \
  --alpha-data-root /home/yuke_zhang/alpha_data/alpha_system \
  --namespace /home/yuke_zhang/alpha_data/alpha_system/rigor_p05_surrogate_dk_p02_opex \
  --runs-per-config 60 --base-seed 42021 \
  --report-out research/differentiated_substrate_v1/surrogate_fdr/opex_calibration.md
```

- StudySpec: `sspec_4936b2ee6614d4b869ec2787`
- Feature locks: `48`
- Label locks: `24`
- Missing feature locks: `0`
- Lock status: `LOCKED`
- Calibration verdict: `zero-pass-met`

### month_end

```bash
python tools/discovery_rigor_floor/run_real_surrogate_calibration.py \
  --study-spec /home/yuke_zhang/projects/alpha_system-differentiated_killshot_v1-dk-p02/research/differentiated_substrate_v1/study_specs/month_end.json \
  --alpha-data-root /home/yuke_zhang/alpha_data/alpha_system \
  --namespace /home/yuke_zhang/alpha_data/alpha_system/rigor_p05_surrogate_dk_p02_month_end \
  --runs-per-config 60 --base-seed 42022 \
  --report-out research/differentiated_substrate_v1/surrogate_fdr/month_end_calibration.md
```

- StudySpec: `sspec_c8669b6769a07d69ab897e58`
- Feature locks: `48`
- Label locks: `24`
- Missing feature locks: `0`
- Lock status: `LOCKED`
- Calibration verdict: `zero-pass-met` (30 all-null partitions excluded under the sanctioned `all_null_values` path; 2024-26-coverage partitions cleared the gate)

### roll_week

```bash
python tools/discovery_rigor_floor/run_real_surrogate_calibration.py \
  --study-spec /home/yuke_zhang/projects/alpha_system-differentiated_killshot_v1-dk-p02/research/differentiated_substrate_v1/study_specs/roll_week.json \
  --alpha-data-root /home/yuke_zhang/alpha_data/alpha_system \
  --namespace /home/yuke_zhang/alpha_data/alpha_system/rigor_p05_surrogate_dk_p02_roll_week \
  --runs-per-config 60 --base-seed 42023 \
  --report-out research/differentiated_substrate_v1/surrogate_fdr/roll_week_calibration.md
```

- StudySpec: `sspec_61b60a8ca735bddea7feb9ff`
- Feature locks: `24`
- Label locks: `24`
- Missing feature locks: `0`
- Lock status: `LOCKED`
- Calibration verdict: `CALIBRATION_BLOCKED` / DATA_GAP (all 24 partitions of `session_calendar_roll_in_roll_window_flag` are all-null/zero-variance; fail-closed `no_numeric_declared_factors_for_surrogate`; excluded from DK-P03)

### open_close

```bash
python tools/discovery_rigor_floor/run_real_surrogate_calibration.py \
  --study-spec /home/yuke_zhang/projects/alpha_system-differentiated_killshot_v1-dk-p02/research/differentiated_substrate_v1/study_specs/open_close.json \
  --alpha-data-root /home/yuke_zhang/alpha_data/alpha_system \
  --namespace /home/yuke_zhang/alpha_data/alpha_system/rigor_p05_surrogate_dk_p02_open_close \
  --runs-per-config 60 --base-seed 42024 \
  --report-out research/differentiated_substrate_v1/surrogate_fdr/open_close_calibration.md
```

- StudySpec: `sspec_0c3386a2dd45451970547acd`
- Feature locks: `48`
- Label locks: `48`
- Missing feature locks: `0`
- Lock status: `LOCKED`
- Calibration verdict: `zero-pass-met`

## Completion (coordinator, out-of-loop)

The DK-P01 calendar flags were materialized by the coordinator via an additive 13-feature superset config with `--force-recompute` (existing 8 fvers byte-preserved; record count `2192 -> 2312`, exactly `+120`), the three previously-blocked StudySpecs were relocked to `LOCKED`, and the five calibrations above were run as heavy single-threaded background compute (~2880 surrogate runs/study). Outcome: four mechanisms reached `zero-pass-met`; `roll_week` is `CALIBRATION_BLOCKED` / DATA_GAP (all-null conditioning flag). The active testable surface into DK-P03 is four mechanisms (`day_of_week`, `opex`, `month_end`, `open_close`). Reports are value-free.
