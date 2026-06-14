# Idea Verdict Report

## Idea Summary
- alpha_spec_id: aspec_9bfafd0949001c03e4a9360f
- mechanism_id: mech_0e5ba214d6d586fdcbc2417b
- setup_spec_id: setup_23c888a54486d417f15415c8
- hypothesis_id: hyp_5289cc1a0acf0f425473c1c7
- source: research/idea_to_verdict_loop_v0/dogfood/track_b_es2024_120m.idea.yaml

## Study Kind
- study_kind: context_not_equal_trigger

## Slice
- slice_id: ES_2024_120m
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
- path_label_two_class: DATA_GAP - path-label slice has fewer than two distinct classes
- n_eff_mde_plausible_and_dedup_known: PASS - N_eff/MDE metadata are plausible and duplicate exposure is declared
- available_ts_and_surrogate_fdr_known: PASS - available_ts is satisfiable and surrogate-FDR requirement is known

## Fast Readout
- status: INCONCLUSIVE
- issue_code: DATA_GAP
- engine: n/a
- class_count: 1
- minority_count: 26184
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
- reason_code: DATA_QUALITY
- why: Path-label slice has fewer than two distinct classes.
- next_action: Choose or repair a bounded slice with at least two observed classes.
