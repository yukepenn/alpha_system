# FUTCORE-P15 FeatureRequest / LabelSpec Decision

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P15`  
Decision: **Minimal additions**

## Basis

`FUTCORE-P13` recorded five P15 gap-list items in
`research/futures_core_alpha_pilot_v1/audits/data_contract/gap_list.md`.
`FUTCORE-P14` carried those gap ids into the approved StudySpec pack under
`research/futures_core_alpha_pilot_v1/study_specs/study_specs.json`.

The locked P03 pack still resolves only:

- FeaturePack members `base_ohlcv_rth_flag` and
  `base_ohlcv_session_minute`.
- LabelPack member `fwd_ret_5m`.

The P14 StudySpecs still require `10m`, `15m`, and `30m` primary-horizon label
bindings plus derived OHLCV and BBO confirmation feature bindings. Therefore
this phase is not a no-op.

## Minimal Additions

Exactly five governed primitive budget items are added, matching the P13 cap
and adding no speculative primitive.

| Gap id | Governed record | Required by StudySpec(s) | Implementation outcome |
| --- | --- | --- | --- |
| `P15-G1` | `research/futures_core_alpha_pilot_v1/label_specs/fwd_ret_10m.json` (`lspec_297ba9c00b50043020a1945e`) | `sspec_16f6de31387d8289d0fbb394`; horizon matrix StudySpecs `sspec_ab3cbb830a2cede5485de19b`, `sspec_8b8037013e7b3c14fd5b2844`, `sspec_28e943d62d4b2eb29a8c445f`, `sspec_b4f5d27095d4f419c078bbcc`, `sspec_62f0ef13ec4f47c2f8c1c784`, `sspec_98d73578b6891eefe52eece5` | Existing fixed-horizon implementation already supported `fwd_ret_10m`; no `src/**` change needed for this item. |
| `P15-G2` | `research/futures_core_alpha_pilot_v1/label_specs/fwd_ret_15m.json` (`lspec_c9e388fde3d860ae012b2ad0`) | `sspec_fc7b0408e59a83f2e69714d3`; the same horizon matrix StudySpecs | Added minimal `fwd_ret_15m` support to `src/alpha_system/labels/families/fixed_horizon/family.py` and focused unit coverage. |
| `P15-G3` | `research/futures_core_alpha_pilot_v1/label_specs/fwd_ret_30m.json` (`lspec_85a5a466430a814f6a608b2c`) | `sspec_6fe5fa12b333d19ea95915d2`; the same horizon matrix StudySpecs | Existing fixed-horizon implementation already supported `fwd_ret_30m`; no `src/**` change needed for this item. |
| `P15-G4` | `research/futures_core_alpha_pilot_v1/feature_requests/p15_g4_causal_ohlcv_derived.json` (`freq_ef650ea8306d52dd9edfb6a3`) | `sspec_16f6de31387d8289d0fbb394`, `sspec_fc7b0408e59a83f2e69714d3`, `sspec_6fe5fa12b333d19ea95915d2`, `sspec_ab3cbb830a2cede5485de19b`, `sspec_8b8037013e7b3c14fd5b2844`, `sspec_28e943d62d4b2eb29a8c445f`, `sspec_b4f5d27095d4f419c078bbcc`, `sspec_62f0ef13ec4f47c2f8c1c784` | Existing OHLCV and structure feature families cover the grouped causal primitives; no new feature code needed. |
| `P15-G5` | `research/futures_core_alpha_pilot_v1/feature_requests/p15_g5_bbo_top_book_confirmation.json` (`freq_5ed19554444f449b7c2da377`) | `sspec_98d73578b6891eefe52eece5` | Existing BBO feature family covers the grouped top-book confirmation primitives; no new feature code needed. |

## Boundaries

The additions are governance records and one minimal label-family extension.
They do not materialize feature or label values, edit consumed primitive
packages outside `src/alpha_system/labels/**`, write registry files, read raw
provider data, add diagnostics, or make any alpha, profitability, tradability,
paper/live, broker, production, or capital-allocation claim.
