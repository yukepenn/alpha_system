# Idea Verdict Report

## Idea Summary
- alpha_spec_id: aspec_0bf430d4c156de9217823445
- mechanism_id: mech_0e5ba214d6d586fdcbc2417b
- setup_spec_id: setup_491c134e723a8c9c0e7d8c1d
- hypothesis_id: hyp_b39f83b4667bf4757811b382
- source: research/idea_to_verdict_loop_v0/dogfood/track_b_es2020_120m.idea.yaml

## Study Kind
- study_kind: context_not_equal_trigger

## Slice
- slice_id: ES_2020_120m
- instrument: n/a
- session: n/a
- window: n/a
- dataset_version_id: n/a
- partition_id: n/a
- feature_pack_refs: none
- label_pack_refs: none

## Data / Features / Labels Used
- data_version: n/a
- features:
  - none
- labels:
  - none

## Dedup Outcome
- family_id: dk_p04_track_b_range_contraction_failed_high_breakout
- status: bounded
- variant_id: baseline_range_contraction_failed_high_breakout

## Testability Gates
- features_materialized: DATA_GAP - feature packs are not resolvable
- labels_path_labels_exist: PASS - label pack handles resolved without materializing values
- path_label_two_class: PASS - path-label slice has at least two distinct classes
- n_eff_mde_plausible_and_dedup_known: PASS - N_eff/MDE metadata are plausible and duplicate exposure is declared
- available_ts_and_surrogate_fdr_known: PASS - available_ts is satisfiable and surrogate-FDR requirement is known

## Fast Readout
- status: INCONCLUSIVE
- issue_code: DATA_GAP
- engine: n/a
- class_count: 2
- minority_count: 3950
- row_access: status=unresolved; fabricated_values=false; reason=pre-test gate returned DATA_GAP

## N_eff / MDE
- n_eff: 0
- mde: n/a

## Surrogate State
- state: BLOCKED
- threshold_verdict: CALIBRATION_BLOCKED
- gate_status: BLOCKED

## Final Verdict
- verdict: DATA_GAP
- reason_code: SUBSTRATE_GAP
- why: Pre-test gate reports DATA_GAP at features_materialized.
- next_action: Resolve the missing substrate or metadata before interpretation.
