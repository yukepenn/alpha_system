# Real-Data Surrogate Calibration: sspec_840e8342564226f2c3257903

This coordinator report is value-free: it records ids, run counts, seeds, gate outcomes, and the declared threshold only. It contains no label, feature, return, diagnostic, signal, or cost values.

## Scope

- Declared K per perturbation config: 3
- Bound statement: zero passes in K bounds false-pass rate at about 3/K at 95%.
- Declared primary horizon used for this run: `5m`.
- Perturbation configs: trade_date_block_shuffle, trade_date_block_bootstrap.
- Runtime factor derivation path: `alpha_system.governance.surrogate_run.study_config_for_surrogate_scope` -> `StudyConfig.from_mapping`.
- Declared feature family: `liquidity_sweep_pa_structure`.
- Declared factor count: 9.
- Declared factors: `liquidity_structure_prior_high_distance`, `liquidity_structure_prior_low_distance`, `liquidity_structure_sweep_high_flag`, `liquidity_structure_sweep_low_flag`, `liquidity_structure_failed_high_breakout_flag`, `liquidity_structure_failed_low_breakout_flag`, `liquidity_structure_close_location_value`, `liquidity_structure_wick_rejection_score`, `liquidity_structure_range_contraction`.
- Excluded all-null factor partitions: 0.
- Declared label pack count: 24.
- Declared label versions: `lver_4f8fc4387649aba0f6bb997493c0392ed9326567c8e94ba8ab3c24a7aeb4983a`, `lver_e58ec699e639e16d4d9309bea1190d4a6bfd0ec1c4636059db8204307ed24e2e`, `lver_151b4d346a2390a33f28246c4602d31d536fd4123dc7297d9ea9c46caed72f64`, `lver_1a8a9097ddb8e84d8f9fd76f6f5f4854de61b0874167078127643827bf41c70a`, `lver_a0f823c60559951296952201f67afa8ea8f1b00802b417538d76f9a8ccd892b9`, `lver_3eda078c1fc017089c63450a273603f811ca5d5e74c89b976bdbf5177e094022`, `lver_e33cc3c199f363a9ce1f7e288c7ed5a590ca3297c3c7c51aa4a2578ea2b51fbb`, `lver_9fc589d03326280db97e1a703b0b9eaf9477c3ea2ca5ed77ac20c2bca2d496a3`, `lver_bc3706d77d1ecc827edc59776e8c0b54f1ea32c566297592dd39ea0268087c8b`, `lver_026fea7f94f6fd977ad2fa3e60bcc113b9a8a97589237536556d24e118feb031`, `lver_f43ffcef350cb5cc75004e9b09b185565dd161798df9727f05c849327034caf6`, `lver_3e558a545c10aac327f09ef8b1a5579b150e4a60322120b651678bfa5e7256b2`, `lver_788c5b36ea91d3ee218504edbb634215414ba79950066f4884361c13fe47b99b`, `lver_d55884d1e10337c320e8fe0f59a768b3d2850868b81fd74fb8c9c92fe67d0742`, `lver_e44dada099cdaab8716351d737918246c93535ad93e9e686f9c8d1ae21c27c57`, `lver_0dd4d33df9674717ddcff1f7e1b3d6cde33da721f2bb36b3ad8e22a2e72e6dce`, `lver_cde42aaecd43ea9b973fb1b9566dafd4ffd35696efa3f25a0723c3ad616a82da`, `lver_75f21845ff10f3e5fc301100a782f93563d078ed468a557dd7925016147a8515`, `lver_67b5dd02c7818d913feafdb73b6dfd347e287b510091d3a95699e6916e6ddfe0`, `lver_40d478b5c4351a28da47141a7158f69407abb7528f67c13aa99334a3b823665a`, `lver_5ab0e573cb33cad2ef08f86bf4a19a0e37e9df514855bf720658ce2d2d69933b`, `lver_07924603a1e7ed0e4288803aa93dd63569e14597f35e54a82bcfe0d4117c8276`, `lver_623e0fbb4a453462950fbb3e370820d6cd002e9358b8211c36992601b4112bce`, `lver_a33ae299ed3b794fad79f94a0a906ab858f071e4990c834e530061bc1c1a6f2b`.
- Staged surrogate sub-config count: 216.
- Off-grid locked label event_ts count: 0.
- Isolated namespace: `/home/yuke_zhang/alpha_data/alpha_system/rigor_p05_surrogate_v5_liq_840e83`.

## Staging Provenance

| Factor | Runtime Factor | Feature Version | Label Version | Feature Partition | Label Partition | Feature Rows | Label Rows | Off-Grid Label event_ts |
|---|---|---|---|---|---|---:|---:|---:|
| `liquidity_structure_prior_high_distance` | `liquidity_structure_prior_high_distance` | `fver_aaa20bef5dce091a7426439889723f2e6e72617ecc1462d0e17cc0a3b559444d` | `lver_4f8fc4387649aba0f6bb997493c0392ed9326567c8e94ba8ab3c24a7aeb4983a` | `ES_2019_full_year` | `ES_2019_fwd_ret_5m` | 349532/3145788 | 341120/341120 | 0 |
| `liquidity_structure_prior_low_distance` | `liquidity_structure_prior_low_distance` | `fver_2fda7856da138719754a416365b3a76199451c054c4d8feabbcc213257f26f98` | `lver_4f8fc4387649aba0f6bb997493c0392ed9326567c8e94ba8ab3c24a7aeb4983a` | `ES_2019_full_year` | `ES_2019_fwd_ret_5m` | 349532/3145788 | 341120/341120 | 0 |
| `liquidity_structure_sweep_high_flag` | `liquidity_structure_sweep_high_flag` | `fver_58696de5c25b08797a0d46cc260733243f9d64b6a798c0364839bcac4d39dc0a` | `lver_4f8fc4387649aba0f6bb997493c0392ed9326567c8e94ba8ab3c24a7aeb4983a` | `ES_2019_full_year` | `ES_2019_fwd_ret_5m` | 349532/3145788 | 341120/341120 | 0 |
| `liquidity_structure_sweep_low_flag` | `liquidity_structure_sweep_low_flag` | `fver_dd3053cac1e7642421ed8de6ee9d6e5cba4d5e185e12d5794e5fa57880dd802d` | `lver_4f8fc4387649aba0f6bb997493c0392ed9326567c8e94ba8ab3c24a7aeb4983a` | `ES_2019_full_year` | `ES_2019_fwd_ret_5m` | 349532/3145788 | 341120/341120 | 0 |
| `liquidity_structure_failed_high_breakout_flag` | `liquidity_structure_failed_high_breakout_flag` | `fver_ff84c3640b5b80479f75b5a4d14f88c5c078c71704fd7d05edc2b713d44b6919` | `lver_4f8fc4387649aba0f6bb997493c0392ed9326567c8e94ba8ab3c24a7aeb4983a` | `ES_2019_full_year` | `ES_2019_fwd_ret_5m` | 349532/3145788 | 341120/341120 | 0 |
| `liquidity_structure_failed_low_breakout_flag` | `liquidity_structure_failed_low_breakout_flag` | `fver_9b5bca87a78b59640428a1ee117f32089cdf37aeabcc7c7a78ff1ddc0a9b37af` | `lver_4f8fc4387649aba0f6bb997493c0392ed9326567c8e94ba8ab3c24a7aeb4983a` | `ES_2019_full_year` | `ES_2019_fwd_ret_5m` | 349532/3145788 | 341120/341120 | 0 |
| `liquidity_structure_close_location_value` | `liquidity_structure_close_location_value` | `fver_51bbc980ad6490c6a30989536159198384dd56a14946f9fb4a45bd58f33e64e2` | `lver_4f8fc4387649aba0f6bb997493c0392ed9326567c8e94ba8ab3c24a7aeb4983a` | `ES_2019_full_year` | `ES_2019_fwd_ret_5m` | 349532/3145788 | 341120/341120 | 0 |
| `liquidity_structure_wick_rejection_score` | `liquidity_structure_wick_rejection_score` | `fver_f41c1b371290c10c8cabf776a1790d16d034acd89824809e4848c1f08cbff995` | `lver_4f8fc4387649aba0f6bb997493c0392ed9326567c8e94ba8ab3c24a7aeb4983a` | `ES_2019_full_year` | `ES_2019_fwd_ret_5m` | 349532/3145788 | 341120/341120 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_6530df07edf4ca6314e56fc700eeb883777ac55a56111c3739d9fd0cf7b2ba8d` | `lver_4f8fc4387649aba0f6bb997493c0392ed9326567c8e94ba8ab3c24a7aeb4983a` | `ES_2019_full_year` | `ES_2019_fwd_ret_5m` | 349532/3145788 | 341120/341120 | 0 |
| `liquidity_structure_prior_high_distance` | `liquidity_structure_prior_high_distance` | `fver_6b3609de83ccbb41ad56d24d26c8e239f5bd8a72e81eac5fe38cfed3e5dc39af` | `lver_e58ec699e639e16d4d9309bea1190d4a6bfd0ec1c4636059db8204307ed24e2e` | `ES_2020_full_year` | `ES_2020_fwd_ret_5m` | 349608/3146472 | 341115/341115 | 0 |
| `liquidity_structure_prior_low_distance` | `liquidity_structure_prior_low_distance` | `fver_849c2bbebaebd7f5283da38654bc0614ec59cbf49d9d6f5a9b578559a46de26a` | `lver_e58ec699e639e16d4d9309bea1190d4a6bfd0ec1c4636059db8204307ed24e2e` | `ES_2020_full_year` | `ES_2020_fwd_ret_5m` | 349608/3146472 | 341115/341115 | 0 |
| `liquidity_structure_sweep_high_flag` | `liquidity_structure_sweep_high_flag` | `fver_af3dd414c0bcf1062955b34a1ffcf6ed44ce434aba0d9c96a5f816ce850d6059` | `lver_e58ec699e639e16d4d9309bea1190d4a6bfd0ec1c4636059db8204307ed24e2e` | `ES_2020_full_year` | `ES_2020_fwd_ret_5m` | 349608/3146472 | 341115/341115 | 0 |
| `liquidity_structure_sweep_low_flag` | `liquidity_structure_sweep_low_flag` | `fver_7393906276772ee63359f5b5c2ae935b8d55053d5c91bece9d0c446a6c65b3a0` | `lver_e58ec699e639e16d4d9309bea1190d4a6bfd0ec1c4636059db8204307ed24e2e` | `ES_2020_full_year` | `ES_2020_fwd_ret_5m` | 349608/3146472 | 341115/341115 | 0 |
| `liquidity_structure_failed_high_breakout_flag` | `liquidity_structure_failed_high_breakout_flag` | `fver_08e6f88675ba2d10c86e08a0ea1962918d82201aff2059a21711929d5a43436c` | `lver_e58ec699e639e16d4d9309bea1190d4a6bfd0ec1c4636059db8204307ed24e2e` | `ES_2020_full_year` | `ES_2020_fwd_ret_5m` | 349608/3146472 | 341115/341115 | 0 |
| `liquidity_structure_failed_low_breakout_flag` | `liquidity_structure_failed_low_breakout_flag` | `fver_69fde9d07db0a3f47b89dba1a3b312580e34b7fc8bd671a84e5b528727466456` | `lver_e58ec699e639e16d4d9309bea1190d4a6bfd0ec1c4636059db8204307ed24e2e` | `ES_2020_full_year` | `ES_2020_fwd_ret_5m` | 349608/3146472 | 341115/341115 | 0 |
| `liquidity_structure_close_location_value` | `liquidity_structure_close_location_value` | `fver_6eb1e2fcdd602e26e47dad9c58e5b0fb8e2406237765d183f7935388cbf0face` | `lver_e58ec699e639e16d4d9309bea1190d4a6bfd0ec1c4636059db8204307ed24e2e` | `ES_2020_full_year` | `ES_2020_fwd_ret_5m` | 349608/3146472 | 341115/341115 | 0 |
| `liquidity_structure_wick_rejection_score` | `liquidity_structure_wick_rejection_score` | `fver_f9004ef2483fa8f703d7e87ae853f296b112a422a6443a94a6915ef3f125f6bb` | `lver_e58ec699e639e16d4d9309bea1190d4a6bfd0ec1c4636059db8204307ed24e2e` | `ES_2020_full_year` | `ES_2020_fwd_ret_5m` | 349608/3146472 | 341115/341115 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_4530c519a4ade73356b77a3d865422fac611dfcbdfff59951e97de8ec99aa534` | `lver_e58ec699e639e16d4d9309bea1190d4a6bfd0ec1c4636059db8204307ed24e2e` | `ES_2020_full_year` | `ES_2020_fwd_ret_5m` | 349608/3146472 | 341115/341115 | 0 |
| `liquidity_structure_prior_high_distance` | `liquidity_structure_prior_high_distance` | `fver_4c90d2c16d96c902e7e6843253aaacc5204338012d668775f076bcdc57cadccd` | `lver_151b4d346a2390a33f28246c4602d31d536fd4123dc7297d9ea9c46caed72f64` | `ES_2021_full_year` | `ES_2021_fwd_ret_5m` | 353363/3180267 | 345881/345881 | 0 |
| `liquidity_structure_prior_low_distance` | `liquidity_structure_prior_low_distance` | `fver_642db39e1df1e46ed32ed1a4abf05bc10f98e4e3aa4de47872c365786399c340` | `lver_151b4d346a2390a33f28246c4602d31d536fd4123dc7297d9ea9c46caed72f64` | `ES_2021_full_year` | `ES_2021_fwd_ret_5m` | 353363/3180267 | 345881/345881 | 0 |
| `liquidity_structure_sweep_high_flag` | `liquidity_structure_sweep_high_flag` | `fver_3609c69c5a805dcd427c757fd24d5843239212a76193e3dbeef91f8055ffbaf8` | `lver_151b4d346a2390a33f28246c4602d31d536fd4123dc7297d9ea9c46caed72f64` | `ES_2021_full_year` | `ES_2021_fwd_ret_5m` | 353363/3180267 | 345881/345881 | 0 |
| `liquidity_structure_sweep_low_flag` | `liquidity_structure_sweep_low_flag` | `fver_04aea7adbc86d27eb40875defd70827c118b2f26f84195cca68fbaecbf5e9640` | `lver_151b4d346a2390a33f28246c4602d31d536fd4123dc7297d9ea9c46caed72f64` | `ES_2021_full_year` | `ES_2021_fwd_ret_5m` | 353363/3180267 | 345881/345881 | 0 |
| `liquidity_structure_failed_high_breakout_flag` | `liquidity_structure_failed_high_breakout_flag` | `fver_0e91f645634dec4d496bdf06a6b07d142424d1f9d74ffdf70ddeff3eb4d456bb` | `lver_151b4d346a2390a33f28246c4602d31d536fd4123dc7297d9ea9c46caed72f64` | `ES_2021_full_year` | `ES_2021_fwd_ret_5m` | 353363/3180267 | 345881/345881 | 0 |
| `liquidity_structure_failed_low_breakout_flag` | `liquidity_structure_failed_low_breakout_flag` | `fver_7d8023bcae2be849d4c87b51aec417b05de5aa90a5a022e66708963fc78aecd6` | `lver_151b4d346a2390a33f28246c4602d31d536fd4123dc7297d9ea9c46caed72f64` | `ES_2021_full_year` | `ES_2021_fwd_ret_5m` | 353363/3180267 | 345881/345881 | 0 |
| `liquidity_structure_close_location_value` | `liquidity_structure_close_location_value` | `fver_5704c7f54a5ddbe2b36b3e5df91b149d721f2e61208acd6d59fcb157250f1349` | `lver_151b4d346a2390a33f28246c4602d31d536fd4123dc7297d9ea9c46caed72f64` | `ES_2021_full_year` | `ES_2021_fwd_ret_5m` | 353363/3180267 | 345881/345881 | 0 |
| `liquidity_structure_wick_rejection_score` | `liquidity_structure_wick_rejection_score` | `fver_5cff9e1be51fc20c4b63009bdab1f38166a6244788ca3921e2f4d37da8c1604c` | `lver_151b4d346a2390a33f28246c4602d31d536fd4123dc7297d9ea9c46caed72f64` | `ES_2021_full_year` | `ES_2021_fwd_ret_5m` | 353363/3180267 | 345881/345881 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_e5a63cd9bdc3562b5c89352d10d11e61270788335b2fff1637e5275d5c025151` | `lver_151b4d346a2390a33f28246c4602d31d536fd4123dc7297d9ea9c46caed72f64` | `ES_2021_full_year` | `ES_2021_fwd_ret_5m` | 353363/3180267 | 345881/345881 | 0 |
| `liquidity_structure_prior_high_distance` | `liquidity_structure_prior_high_distance` | `fver_6d02cbc44ac2e103b4b6ca3305a32886806b9a702ab6cd96650b4fbcfe80a1e1` | `lver_1a8a9097ddb8e84d8f9fd76f6f5f4854de61b0874167078127643827bf41c70a` | `ES_2022_full_year` | `ES_2022_fwd_ret_5m` | 354119/3187071 | 347293/347293 | 0 |
| `liquidity_structure_prior_low_distance` | `liquidity_structure_prior_low_distance` | `fver_4e30c36da2d958f9b6596b692b18a25d5b718179297153cc88b627550164b463` | `lver_1a8a9097ddb8e84d8f9fd76f6f5f4854de61b0874167078127643827bf41c70a` | `ES_2022_full_year` | `ES_2022_fwd_ret_5m` | 354119/3187071 | 347293/347293 | 0 |
| `liquidity_structure_sweep_high_flag` | `liquidity_structure_sweep_high_flag` | `fver_f4b0e9df43c8386bd78106dc50f9c16c60d8ca0100cef9eb00130f9484033e2c` | `lver_1a8a9097ddb8e84d8f9fd76f6f5f4854de61b0874167078127643827bf41c70a` | `ES_2022_full_year` | `ES_2022_fwd_ret_5m` | 354119/3187071 | 347293/347293 | 0 |
| `liquidity_structure_sweep_low_flag` | `liquidity_structure_sweep_low_flag` | `fver_0d09bf4303b669b416a595cc8159e004f8879873a6a074327c4f7c4f05d2ce60` | `lver_1a8a9097ddb8e84d8f9fd76f6f5f4854de61b0874167078127643827bf41c70a` | `ES_2022_full_year` | `ES_2022_fwd_ret_5m` | 354119/3187071 | 347293/347293 | 0 |
| `liquidity_structure_failed_high_breakout_flag` | `liquidity_structure_failed_high_breakout_flag` | `fver_11ba6c8b9dc727aa8cfd82d8a292c775ea5cb787b942293ceeff74f740efd926` | `lver_1a8a9097ddb8e84d8f9fd76f6f5f4854de61b0874167078127643827bf41c70a` | `ES_2022_full_year` | `ES_2022_fwd_ret_5m` | 354119/3187071 | 347293/347293 | 0 |
| `liquidity_structure_failed_low_breakout_flag` | `liquidity_structure_failed_low_breakout_flag` | `fver_f13e3eb62551b80e8a199122aff565021d7f4932c9ae7ee7534acbfb774ab7d2` | `lver_1a8a9097ddb8e84d8f9fd76f6f5f4854de61b0874167078127643827bf41c70a` | `ES_2022_full_year` | `ES_2022_fwd_ret_5m` | 354119/3187071 | 347293/347293 | 0 |
| `liquidity_structure_close_location_value` | `liquidity_structure_close_location_value` | `fver_e35b1b72f8bfdee41860ce0cc4ae3a5bbe8289f1b214d09f779819e221ebd25d` | `lver_1a8a9097ddb8e84d8f9fd76f6f5f4854de61b0874167078127643827bf41c70a` | `ES_2022_full_year` | `ES_2022_fwd_ret_5m` | 354119/3187071 | 347293/347293 | 0 |
| `liquidity_structure_wick_rejection_score` | `liquidity_structure_wick_rejection_score` | `fver_2c8025d3c240df085f515a2a5481bc7861968f74c98518fd5ef692e352ebd3e9` | `lver_1a8a9097ddb8e84d8f9fd76f6f5f4854de61b0874167078127643827bf41c70a` | `ES_2022_full_year` | `ES_2022_fwd_ret_5m` | 354119/3187071 | 347293/347293 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_0ee89a321fcd7c9d07ae690d47d287278d9f2836ca8535af8e3384467561e9a6` | `lver_1a8a9097ddb8e84d8f9fd76f6f5f4854de61b0874167078127643827bf41c70a` | `ES_2022_full_year` | `ES_2022_fwd_ret_5m` | 354119/3187071 | 347293/347293 | 0 |
| `liquidity_structure_prior_high_distance` | `liquidity_structure_prior_high_distance` | `fver_e7ccca6968a6569ab2b34f022b72a8024d8d9bde160de4049630a6e183f6520e` | `lver_a0f823c60559951296952201f67afa8ea8f1b00802b417538d76f9a8ccd892b9` | `ES_2023_full_year` | `ES_2023_fwd_ret_5m` | 353153/3178377 | 346064/346064 | 0 |
| `liquidity_structure_prior_low_distance` | `liquidity_structure_prior_low_distance` | `fver_417e025862750b187d654d76d574dd9f9f600ba2d4a80d6ba1fd26b30de6d8e8` | `lver_a0f823c60559951296952201f67afa8ea8f1b00802b417538d76f9a8ccd892b9` | `ES_2023_full_year` | `ES_2023_fwd_ret_5m` | 353153/3178377 | 346064/346064 | 0 |
| `liquidity_structure_sweep_high_flag` | `liquidity_structure_sweep_high_flag` | `fver_3547697fbd5d51cfb8347a5afe017335e6334f4d72f39b4cd7f0d251753e774b` | `lver_a0f823c60559951296952201f67afa8ea8f1b00802b417538d76f9a8ccd892b9` | `ES_2023_full_year` | `ES_2023_fwd_ret_5m` | 353153/3178377 | 346064/346064 | 0 |
| `liquidity_structure_sweep_low_flag` | `liquidity_structure_sweep_low_flag` | `fver_30fc0bbf1aa6f03fcddf764973ab685a8ff5b5cac58d4eeadc72d95b08c8c56d` | `lver_a0f823c60559951296952201f67afa8ea8f1b00802b417538d76f9a8ccd892b9` | `ES_2023_full_year` | `ES_2023_fwd_ret_5m` | 353153/3178377 | 346064/346064 | 0 |
| `liquidity_structure_failed_high_breakout_flag` | `liquidity_structure_failed_high_breakout_flag` | `fver_deb8a277cbbea678aa62b76270ad60e083818f3908134b775cc337f0b56acf00` | `lver_a0f823c60559951296952201f67afa8ea8f1b00802b417538d76f9a8ccd892b9` | `ES_2023_full_year` | `ES_2023_fwd_ret_5m` | 353153/3178377 | 346064/346064 | 0 |
| `liquidity_structure_failed_low_breakout_flag` | `liquidity_structure_failed_low_breakout_flag` | `fver_8e6178b72667e810a530506eedf8a5353a324c2e4ab57b2118f9071c0b6de692` | `lver_a0f823c60559951296952201f67afa8ea8f1b00802b417538d76f9a8ccd892b9` | `ES_2023_full_year` | `ES_2023_fwd_ret_5m` | 353153/3178377 | 346064/346064 | 0 |
| `liquidity_structure_close_location_value` | `liquidity_structure_close_location_value` | `fver_e1cf56937840a9d7472c94ad564a9a117ef22935e6f15812b8c50854fa431fb9` | `lver_a0f823c60559951296952201f67afa8ea8f1b00802b417538d76f9a8ccd892b9` | `ES_2023_full_year` | `ES_2023_fwd_ret_5m` | 353153/3178377 | 346064/346064 | 0 |
| `liquidity_structure_wick_rejection_score` | `liquidity_structure_wick_rejection_score` | `fver_dfc4424ab0635c98257df6520eb8d253a39995404d4e31d9b7c8e264a2dc0b46` | `lver_a0f823c60559951296952201f67afa8ea8f1b00802b417538d76f9a8ccd892b9` | `ES_2023_full_year` | `ES_2023_fwd_ret_5m` | 353153/3178377 | 346064/346064 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_0b179a55a394268818b4ae1ad8fd5cbdf1bcc55dbdfbbb64d7ea3851b300cf6b` | `lver_a0f823c60559951296952201f67afa8ea8f1b00802b417538d76f9a8ccd892b9` | `ES_2023_full_year` | `ES_2023_fwd_ret_5m` | 353153/3178377 | 346064/346064 | 0 |
| `liquidity_structure_prior_high_distance` | `liquidity_structure_prior_high_distance` | `fver_69b560f8f5cd823aea6803f9dc9eeaf3a612d2dd78e2c0986f828fb621fd8a07` | `lver_3eda078c1fc017089c63450a273603f811ca5d5e74c89b976bdbf5177e094022` | `ES_2024_full_year` | `ES_2024_fwd_ret_5m` | 346858/3121722 | 339866/339866 | 0 |
| `liquidity_structure_prior_low_distance` | `liquidity_structure_prior_low_distance` | `fver_3af1cd0b51f515b64b7cb381252c033e09416cd681f6b0814ce35afc8bd1d30c` | `lver_3eda078c1fc017089c63450a273603f811ca5d5e74c89b976bdbf5177e094022` | `ES_2024_full_year` | `ES_2024_fwd_ret_5m` | 346858/3121722 | 339866/339866 | 0 |
| `liquidity_structure_sweep_high_flag` | `liquidity_structure_sweep_high_flag` | `fver_3532a4ddc5caf3f184f9356b0ca3724babb99f4b6fea4c8ccecc45599fa237db` | `lver_3eda078c1fc017089c63450a273603f811ca5d5e74c89b976bdbf5177e094022` | `ES_2024_full_year` | `ES_2024_fwd_ret_5m` | 346858/3121722 | 339866/339866 | 0 |
| `liquidity_structure_sweep_low_flag` | `liquidity_structure_sweep_low_flag` | `fver_eb6c6304ef6816adbca2c0d51f4b0cb75e0906ed0358209e5c2d63a3e5c4aac5` | `lver_3eda078c1fc017089c63450a273603f811ca5d5e74c89b976bdbf5177e094022` | `ES_2024_full_year` | `ES_2024_fwd_ret_5m` | 346858/3121722 | 339866/339866 | 0 |
| `liquidity_structure_failed_high_breakout_flag` | `liquidity_structure_failed_high_breakout_flag` | `fver_f5d041ab307a9a4e27b40365431de086f5b70a10fe9776eb34ef58a2534448cd` | `lver_3eda078c1fc017089c63450a273603f811ca5d5e74c89b976bdbf5177e094022` | `ES_2024_full_year` | `ES_2024_fwd_ret_5m` | 346858/3121722 | 339866/339866 | 0 |
| `liquidity_structure_failed_low_breakout_flag` | `liquidity_structure_failed_low_breakout_flag` | `fver_c6ea5c16d932ab72b042e2b64f8621daadf0ebeffc531f380e82be00a626a8ac` | `lver_3eda078c1fc017089c63450a273603f811ca5d5e74c89b976bdbf5177e094022` | `ES_2024_full_year` | `ES_2024_fwd_ret_5m` | 346858/3121722 | 339866/339866 | 0 |
| `liquidity_structure_close_location_value` | `liquidity_structure_close_location_value` | `fver_9e2c7b42d8c7fc8cd02a0625540c0f2c7d99d683d70fb06c0ccf41fa4ec3e136` | `lver_3eda078c1fc017089c63450a273603f811ca5d5e74c89b976bdbf5177e094022` | `ES_2024_full_year` | `ES_2024_fwd_ret_5m` | 346858/3121722 | 339866/339866 | 0 |
| `liquidity_structure_wick_rejection_score` | `liquidity_structure_wick_rejection_score` | `fver_fb7bb40ddfb06361db5162715f546c67acd13fe5997ac1bf9b4ae8c53282c2f7` | `lver_3eda078c1fc017089c63450a273603f811ca5d5e74c89b976bdbf5177e094022` | `ES_2024_full_year` | `ES_2024_fwd_ret_5m` | 346858/3121722 | 339866/339866 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_0871d0e9188f577adf859592dc7e1dd3fd09ddf8a9f93f92a1914f25027b165c` | `lver_3eda078c1fc017089c63450a273603f811ca5d5e74c89b976bdbf5177e094022` | `ES_2024_full_year` | `ES_2024_fwd_ret_5m` | 346858/3121722 | 339866/339866 | 0 |
| `liquidity_structure_prior_high_distance` | `liquidity_structure_prior_high_distance` | `fver_c97581630fa9e5c6f68f44056cde2361ceacdbfe0541a0af90b4d54049adf75d` | `lver_e33cc3c199f363a9ce1f7e288c7ed5a590ca3297c3c7c51aa4a2578ea2b51fbb` | `ES_2025_full_year` | `ES_2025_fwd_ret_5m` | 344561/3101049 | 337734/337734 | 0 |
| `liquidity_structure_prior_low_distance` | `liquidity_structure_prior_low_distance` | `fver_600adc78ace55580f42e8254f60b59c683c928cfaf75cdc4fcaced614bbca5da` | `lver_e33cc3c199f363a9ce1f7e288c7ed5a590ca3297c3c7c51aa4a2578ea2b51fbb` | `ES_2025_full_year` | `ES_2025_fwd_ret_5m` | 344561/3101049 | 337734/337734 | 0 |
| `liquidity_structure_sweep_high_flag` | `liquidity_structure_sweep_high_flag` | `fver_36f125949af209adf76d0bd52c9571f82758f70c785f904396351f03d16401f3` | `lver_e33cc3c199f363a9ce1f7e288c7ed5a590ca3297c3c7c51aa4a2578ea2b51fbb` | `ES_2025_full_year` | `ES_2025_fwd_ret_5m` | 344561/3101049 | 337734/337734 | 0 |
| `liquidity_structure_sweep_low_flag` | `liquidity_structure_sweep_low_flag` | `fver_2690d657ff5c8b690e0c38b69c9c69eba031f0bc61c2308f0bf5fc67df324b1d` | `lver_e33cc3c199f363a9ce1f7e288c7ed5a590ca3297c3c7c51aa4a2578ea2b51fbb` | `ES_2025_full_year` | `ES_2025_fwd_ret_5m` | 344561/3101049 | 337734/337734 | 0 |
| `liquidity_structure_failed_high_breakout_flag` | `liquidity_structure_failed_high_breakout_flag` | `fver_848f736f9538a757c4c7864aa9b72d24d481d75388577c771d7561f98d015cfc` | `lver_e33cc3c199f363a9ce1f7e288c7ed5a590ca3297c3c7c51aa4a2578ea2b51fbb` | `ES_2025_full_year` | `ES_2025_fwd_ret_5m` | 344561/3101049 | 337734/337734 | 0 |
| `liquidity_structure_failed_low_breakout_flag` | `liquidity_structure_failed_low_breakout_flag` | `fver_3bacc9cb6852da898aef28a18b9a5885382df8c7bdc5acdf8cee1991cfccd64c` | `lver_e33cc3c199f363a9ce1f7e288c7ed5a590ca3297c3c7c51aa4a2578ea2b51fbb` | `ES_2025_full_year` | `ES_2025_fwd_ret_5m` | 344561/3101049 | 337734/337734 | 0 |
| `liquidity_structure_close_location_value` | `liquidity_structure_close_location_value` | `fver_cddb7f55980957dd64f607f50a63720846a2cb932f4d4111f30130bc3887884b` | `lver_e33cc3c199f363a9ce1f7e288c7ed5a590ca3297c3c7c51aa4a2578ea2b51fbb` | `ES_2025_full_year` | `ES_2025_fwd_ret_5m` | 344561/3101049 | 337734/337734 | 0 |
| `liquidity_structure_wick_rejection_score` | `liquidity_structure_wick_rejection_score` | `fver_12fc1d27c728d390da3fd67eb56703b9b0b5eb6ae021832b64cc10ef9ecffa24` | `lver_e33cc3c199f363a9ce1f7e288c7ed5a590ca3297c3c7c51aa4a2578ea2b51fbb` | `ES_2025_full_year` | `ES_2025_fwd_ret_5m` | 344561/3101049 | 337734/337734 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_34ffd93a5a71752aca7e8cf8c1dee93256c006f45e5609c369399988add735c6` | `lver_e33cc3c199f363a9ce1f7e288c7ed5a590ca3297c3c7c51aa4a2578ea2b51fbb` | `ES_2025_full_year` | `ES_2025_fwd_ret_5m` | 344561/3101049 | 337734/337734 | 0 |
| `liquidity_structure_prior_high_distance` | `liquidity_structure_prior_high_distance` | `fver_143dbada9a18aafd3ddd47f37fde47f6a8a4ae3da216511bdedda5ef92a2f87d` | `lver_9fc589d03326280db97e1a703b0b9eaf9477c3ea2ca5ed77ac20c2bca2d496a3` | `ES_2026_full_year` | `ES_2026_fwd_ret_5m` | 140639/1265751 | 138748/138748 | 0 |
| `liquidity_structure_prior_low_distance` | `liquidity_structure_prior_low_distance` | `fver_393ab21e94d08dc904bd51389521581e7792fd6d6394390a80a13a3ae2557ee3` | `lver_9fc589d03326280db97e1a703b0b9eaf9477c3ea2ca5ed77ac20c2bca2d496a3` | `ES_2026_full_year` | `ES_2026_fwd_ret_5m` | 140639/1265751 | 138748/138748 | 0 |
| `liquidity_structure_sweep_high_flag` | `liquidity_structure_sweep_high_flag` | `fver_811b0e14402a9e3be2ee5498d7522292a55a3228bc6e4e57dee5739303b09d81` | `lver_9fc589d03326280db97e1a703b0b9eaf9477c3ea2ca5ed77ac20c2bca2d496a3` | `ES_2026_full_year` | `ES_2026_fwd_ret_5m` | 140639/1265751 | 138748/138748 | 0 |
| `liquidity_structure_sweep_low_flag` | `liquidity_structure_sweep_low_flag` | `fver_4360b36d7358d9cbfa0000478548401fa272a5b5796cc4d870b75328f1f7f6c4` | `lver_9fc589d03326280db97e1a703b0b9eaf9477c3ea2ca5ed77ac20c2bca2d496a3` | `ES_2026_full_year` | `ES_2026_fwd_ret_5m` | 140639/1265751 | 138748/138748 | 0 |
| `liquidity_structure_failed_high_breakout_flag` | `liquidity_structure_failed_high_breakout_flag` | `fver_c2beb7bada7039c086730ba69f2285b554a820018611abefa3680af1d4e17ff2` | `lver_9fc589d03326280db97e1a703b0b9eaf9477c3ea2ca5ed77ac20c2bca2d496a3` | `ES_2026_full_year` | `ES_2026_fwd_ret_5m` | 140639/1265751 | 138748/138748 | 0 |
| `liquidity_structure_failed_low_breakout_flag` | `liquidity_structure_failed_low_breakout_flag` | `fver_448caa6f7ab17e87417b18c78dee41bc07aa643fccc4d389cacdd4228c128534` | `lver_9fc589d03326280db97e1a703b0b9eaf9477c3ea2ca5ed77ac20c2bca2d496a3` | `ES_2026_full_year` | `ES_2026_fwd_ret_5m` | 140639/1265751 | 138748/138748 | 0 |
| `liquidity_structure_close_location_value` | `liquidity_structure_close_location_value` | `fver_45358d8a374510568ba617436bc2e346d55283bc01fe57208051ea15fbcf7686` | `lver_9fc589d03326280db97e1a703b0b9eaf9477c3ea2ca5ed77ac20c2bca2d496a3` | `ES_2026_full_year` | `ES_2026_fwd_ret_5m` | 140639/1265751 | 138748/138748 | 0 |
| `liquidity_structure_wick_rejection_score` | `liquidity_structure_wick_rejection_score` | `fver_df96889d1dde8fa6536010b57ce2b1f0d62309433324b87ca9aff012faed3364` | `lver_9fc589d03326280db97e1a703b0b9eaf9477c3ea2ca5ed77ac20c2bca2d496a3` | `ES_2026_full_year` | `ES_2026_fwd_ret_5m` | 140639/1265751 | 138748/138748 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_6cff1dea5e2585e56e3c4fa4e43fdcdc9d70de140b524871aa5d5aaf13f60962` | `lver_9fc589d03326280db97e1a703b0b9eaf9477c3ea2ca5ed77ac20c2bca2d496a3` | `ES_2026_full_year` | `ES_2026_fwd_ret_5m` | 140639/1265751 | 138748/138748 | 0 |
| `liquidity_structure_prior_high_distance` | `liquidity_structure_prior_high_distance` | `fver_183b4d7a50a9fad34ce1f4fa864702e64c1d768110c04a08a3d5bcfb75dc0a4b` | `lver_bc3706d77d1ecc827edc59776e8c0b54f1ea32c566297592dd39ea0268087c8b` | `NQ_2019_full_year` | `NQ_2019_fwd_ret_5m` | 349845/3148605 | 341715/341715 | 0 |
| `liquidity_structure_prior_low_distance` | `liquidity_structure_prior_low_distance` | `fver_33d33e1ea4090a8785b10faebf8eeb92fa20ad3a287e49ef902f6dae478f796a` | `lver_bc3706d77d1ecc827edc59776e8c0b54f1ea32c566297592dd39ea0268087c8b` | `NQ_2019_full_year` | `NQ_2019_fwd_ret_5m` | 349845/3148605 | 341715/341715 | 0 |
| `liquidity_structure_sweep_high_flag` | `liquidity_structure_sweep_high_flag` | `fver_2278e33fffda7d66e0711769f4b4ff1606498488cca90a15a4061971f137cb83` | `lver_bc3706d77d1ecc827edc59776e8c0b54f1ea32c566297592dd39ea0268087c8b` | `NQ_2019_full_year` | `NQ_2019_fwd_ret_5m` | 349845/3148605 | 341715/341715 | 0 |
| `liquidity_structure_sweep_low_flag` | `liquidity_structure_sweep_low_flag` | `fver_ac27dcf7d7c3b8899ad89ae043e2d7dbc9b9a64d39387b104e1a440fd2fdec1c` | `lver_bc3706d77d1ecc827edc59776e8c0b54f1ea32c566297592dd39ea0268087c8b` | `NQ_2019_full_year` | `NQ_2019_fwd_ret_5m` | 349845/3148605 | 341715/341715 | 0 |
| `liquidity_structure_failed_high_breakout_flag` | `liquidity_structure_failed_high_breakout_flag` | `fver_6323792ba60e6d35928c887c31f3eff1df1c3e8d042a2cc9059e966735f9b5ad` | `lver_bc3706d77d1ecc827edc59776e8c0b54f1ea32c566297592dd39ea0268087c8b` | `NQ_2019_full_year` | `NQ_2019_fwd_ret_5m` | 349845/3148605 | 341715/341715 | 0 |
| `liquidity_structure_failed_low_breakout_flag` | `liquidity_structure_failed_low_breakout_flag` | `fver_94a8b3e568db4b67170b34d350f55e426db99a55d728bb630629d08fb1a278c5` | `lver_bc3706d77d1ecc827edc59776e8c0b54f1ea32c566297592dd39ea0268087c8b` | `NQ_2019_full_year` | `NQ_2019_fwd_ret_5m` | 349845/3148605 | 341715/341715 | 0 |
| `liquidity_structure_close_location_value` | `liquidity_structure_close_location_value` | `fver_71a9b396a20722df8963e9ca2cfa90f70ee0c52dd8a2f0d93eb0ac72d2e8043e` | `lver_bc3706d77d1ecc827edc59776e8c0b54f1ea32c566297592dd39ea0268087c8b` | `NQ_2019_full_year` | `NQ_2019_fwd_ret_5m` | 349845/3148605 | 341715/341715 | 0 |
| `liquidity_structure_wick_rejection_score` | `liquidity_structure_wick_rejection_score` | `fver_3eee2e18f6ee72c59659bef53db21b9771974bb8cc4e496808d93b8ed7a223bb` | `lver_bc3706d77d1ecc827edc59776e8c0b54f1ea32c566297592dd39ea0268087c8b` | `NQ_2019_full_year` | `NQ_2019_fwd_ret_5m` | 349845/3148605 | 341715/341715 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_ddb5c3a5f31eea53d7bfa177c0387066fe6f6226ddb453fc793a35900e66511f` | `lver_bc3706d77d1ecc827edc59776e8c0b54f1ea32c566297592dd39ea0268087c8b` | `NQ_2019_full_year` | `NQ_2019_fwd_ret_5m` | 349845/3148605 | 341715/341715 | 0 |
| `liquidity_structure_prior_high_distance` | `liquidity_structure_prior_high_distance` | `fver_91a245b7b96045bc4865fdf3dc2bb0216845529a642c47fb1c42e8ef797a49f5` | `lver_026fea7f94f6fd977ad2fa3e60bcc113b9a8a97589237536556d24e118feb031` | `NQ_2020_full_year` | `NQ_2020_fwd_ret_5m` | 348929/3140361 | 340507/340507 | 0 |
| `liquidity_structure_prior_low_distance` | `liquidity_structure_prior_low_distance` | `fver_26528015addcb210d753fbba562ad5dd727031f5ab339f1638c6b576d8be1d04` | `lver_026fea7f94f6fd977ad2fa3e60bcc113b9a8a97589237536556d24e118feb031` | `NQ_2020_full_year` | `NQ_2020_fwd_ret_5m` | 348929/3140361 | 340507/340507 | 0 |
| `liquidity_structure_sweep_high_flag` | `liquidity_structure_sweep_high_flag` | `fver_6f30e8a2e622d8367e193d3a8456ba74c1e59efa239ebd9d438245f051d760ce` | `lver_026fea7f94f6fd977ad2fa3e60bcc113b9a8a97589237536556d24e118feb031` | `NQ_2020_full_year` | `NQ_2020_fwd_ret_5m` | 348929/3140361 | 340507/340507 | 0 |
| `liquidity_structure_sweep_low_flag` | `liquidity_structure_sweep_low_flag` | `fver_1a08fea5bc163e1d920214829c78822fa3d1b977d989996507f54f5b71e78498` | `lver_026fea7f94f6fd977ad2fa3e60bcc113b9a8a97589237536556d24e118feb031` | `NQ_2020_full_year` | `NQ_2020_fwd_ret_5m` | 348929/3140361 | 340507/340507 | 0 |
| `liquidity_structure_failed_high_breakout_flag` | `liquidity_structure_failed_high_breakout_flag` | `fver_bd77350d9c2e060c78f6c523466dc995490b4adf36d15566a2972c7cb60a3dc2` | `lver_026fea7f94f6fd977ad2fa3e60bcc113b9a8a97589237536556d24e118feb031` | `NQ_2020_full_year` | `NQ_2020_fwd_ret_5m` | 348929/3140361 | 340507/340507 | 0 |
| `liquidity_structure_failed_low_breakout_flag` | `liquidity_structure_failed_low_breakout_flag` | `fver_7ea948969c3fd8ec7d5388065eae2e12c1bdf528106aacb4721af8509fbea03f` | `lver_026fea7f94f6fd977ad2fa3e60bcc113b9a8a97589237536556d24e118feb031` | `NQ_2020_full_year` | `NQ_2020_fwd_ret_5m` | 348929/3140361 | 340507/340507 | 0 |
| `liquidity_structure_close_location_value` | `liquidity_structure_close_location_value` | `fver_4e84a63adcb14254d41445e829d3de2e7f031966d4c28ca7e5ca99149da2f0c2` | `lver_026fea7f94f6fd977ad2fa3e60bcc113b9a8a97589237536556d24e118feb031` | `NQ_2020_full_year` | `NQ_2020_fwd_ret_5m` | 348929/3140361 | 340507/340507 | 0 |
| `liquidity_structure_wick_rejection_score` | `liquidity_structure_wick_rejection_score` | `fver_fa312e5d783b1e72cb1f4207c2cafc2871b08a71682080cb267c21076cb4689d` | `lver_026fea7f94f6fd977ad2fa3e60bcc113b9a8a97589237536556d24e118feb031` | `NQ_2020_full_year` | `NQ_2020_fwd_ret_5m` | 348929/3140361 | 340507/340507 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_30a4f6570256606e1598752706a9733ac5e37b19065ef5756e5526069eed2613` | `lver_026fea7f94f6fd977ad2fa3e60bcc113b9a8a97589237536556d24e118feb031` | `NQ_2020_full_year` | `NQ_2020_fwd_ret_5m` | 348929/3140361 | 340507/340507 | 0 |
| `liquidity_structure_prior_high_distance` | `liquidity_structure_prior_high_distance` | `fver_731090d599c4f6816e6f5d18b7bbd9377bb8aec65a2ccde75c22c3af86600b04` | `lver_f43ffcef350cb5cc75004e9b09b185565dd161798df9727f05c849327034caf6` | `NQ_2021_full_year` | `NQ_2021_fwd_ret_5m` | 353393/3180537 | 345938/345938 | 0 |
| `liquidity_structure_prior_low_distance` | `liquidity_structure_prior_low_distance` | `fver_5140c9e2df2b5774dbd8fb8c944412474c9adbfa2fad91832fb26087dca68012` | `lver_f43ffcef350cb5cc75004e9b09b185565dd161798df9727f05c849327034caf6` | `NQ_2021_full_year` | `NQ_2021_fwd_ret_5m` | 353393/3180537 | 345938/345938 | 0 |
| `liquidity_structure_sweep_high_flag` | `liquidity_structure_sweep_high_flag` | `fver_5085e315efb803fdf601fb2eb9ff3d2ab648bd570e79699b271d852c7622432c` | `lver_f43ffcef350cb5cc75004e9b09b185565dd161798df9727f05c849327034caf6` | `NQ_2021_full_year` | `NQ_2021_fwd_ret_5m` | 353393/3180537 | 345938/345938 | 0 |
| `liquidity_structure_sweep_low_flag` | `liquidity_structure_sweep_low_flag` | `fver_0c715c1ccb6820ac0208dff81fab404c4aacee3551a1d12ff426e7e22e0767aa` | `lver_f43ffcef350cb5cc75004e9b09b185565dd161798df9727f05c849327034caf6` | `NQ_2021_full_year` | `NQ_2021_fwd_ret_5m` | 353393/3180537 | 345938/345938 | 0 |
| `liquidity_structure_failed_high_breakout_flag` | `liquidity_structure_failed_high_breakout_flag` | `fver_7ebc12838af95d561f1cbf6628313d0243661acf4047bb280660293bbad64ce4` | `lver_f43ffcef350cb5cc75004e9b09b185565dd161798df9727f05c849327034caf6` | `NQ_2021_full_year` | `NQ_2021_fwd_ret_5m` | 353393/3180537 | 345938/345938 | 0 |
| `liquidity_structure_failed_low_breakout_flag` | `liquidity_structure_failed_low_breakout_flag` | `fver_8ddc4abe3eabb7c9c3418a8e3b01134cef1d6f64263181c6c2049e3b3bdb5a98` | `lver_f43ffcef350cb5cc75004e9b09b185565dd161798df9727f05c849327034caf6` | `NQ_2021_full_year` | `NQ_2021_fwd_ret_5m` | 353393/3180537 | 345938/345938 | 0 |
| `liquidity_structure_close_location_value` | `liquidity_structure_close_location_value` | `fver_e42618e09bdfa6b30c87582cb19d698eeb16fd507dd0108bc7437adbc306491e` | `lver_f43ffcef350cb5cc75004e9b09b185565dd161798df9727f05c849327034caf6` | `NQ_2021_full_year` | `NQ_2021_fwd_ret_5m` | 353393/3180537 | 345938/345938 | 0 |
| `liquidity_structure_wick_rejection_score` | `liquidity_structure_wick_rejection_score` | `fver_662a260f81fa029de1f084206626fcf2fed0c82cd4149f13bfad02cbae6b5ae5` | `lver_f43ffcef350cb5cc75004e9b09b185565dd161798df9727f05c849327034caf6` | `NQ_2021_full_year` | `NQ_2021_fwd_ret_5m` | 353393/3180537 | 345938/345938 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_34035d7f4b18e6677d0396e51792eaf60beb0509cc4db2ac340cd26d699971a3` | `lver_f43ffcef350cb5cc75004e9b09b185565dd161798df9727f05c849327034caf6` | `NQ_2021_full_year` | `NQ_2021_fwd_ret_5m` | 353393/3180537 | 345938/345938 | 0 |
| `liquidity_structure_prior_high_distance` | `liquidity_structure_prior_high_distance` | `fver_aaf5d6e7fbd7397993ef5fafb991ba43793cef22deb41f6d269cc64eeb53fde5` | `lver_3e558a545c10aac327f09ef8b1a5579b150e4a60322120b651678bfa5e7256b2` | `NQ_2022_full_year` | `NQ_2022_fwd_ret_5m` | 354112/3187008 | 347280/347280 | 0 |
| `liquidity_structure_prior_low_distance` | `liquidity_structure_prior_low_distance` | `fver_09500f3ad4bc7ae12ae279428fa213b740dd603564c5fe8b61d6909bd1ad4cad` | `lver_3e558a545c10aac327f09ef8b1a5579b150e4a60322120b651678bfa5e7256b2` | `NQ_2022_full_year` | `NQ_2022_fwd_ret_5m` | 354112/3187008 | 347280/347280 | 0 |
| `liquidity_structure_sweep_high_flag` | `liquidity_structure_sweep_high_flag` | `fver_45886f90683a394bba4749d644d9543efb6dd6b51487a77764067cba51ffeb2e` | `lver_3e558a545c10aac327f09ef8b1a5579b150e4a60322120b651678bfa5e7256b2` | `NQ_2022_full_year` | `NQ_2022_fwd_ret_5m` | 354112/3187008 | 347280/347280 | 0 |
| `liquidity_structure_sweep_low_flag` | `liquidity_structure_sweep_low_flag` | `fver_1ee388c1194bc8f141cab9140b96b4e9b0251b0e4b36f61daa8d94d02120dd75` | `lver_3e558a545c10aac327f09ef8b1a5579b150e4a60322120b651678bfa5e7256b2` | `NQ_2022_full_year` | `NQ_2022_fwd_ret_5m` | 354112/3187008 | 347280/347280 | 0 |
| `liquidity_structure_failed_high_breakout_flag` | `liquidity_structure_failed_high_breakout_flag` | `fver_3738568527f5d2759a55bae71f4f9606ce45fbdb010f33dfc65309b8055e2b67` | `lver_3e558a545c10aac327f09ef8b1a5579b150e4a60322120b651678bfa5e7256b2` | `NQ_2022_full_year` | `NQ_2022_fwd_ret_5m` | 354112/3187008 | 347280/347280 | 0 |
| `liquidity_structure_failed_low_breakout_flag` | `liquidity_structure_failed_low_breakout_flag` | `fver_9ed5c34cc3a6d8432a42f47959a35eeba17e5255c9934bc350451da7d80514aa` | `lver_3e558a545c10aac327f09ef8b1a5579b150e4a60322120b651678bfa5e7256b2` | `NQ_2022_full_year` | `NQ_2022_fwd_ret_5m` | 354112/3187008 | 347280/347280 | 0 |
| `liquidity_structure_close_location_value` | `liquidity_structure_close_location_value` | `fver_f5267672ca3a359b4a81ffdb7768c20a8a40728ce6fc220afebeb905a4b836c2` | `lver_3e558a545c10aac327f09ef8b1a5579b150e4a60322120b651678bfa5e7256b2` | `NQ_2022_full_year` | `NQ_2022_fwd_ret_5m` | 354112/3187008 | 347280/347280 | 0 |
| `liquidity_structure_wick_rejection_score` | `liquidity_structure_wick_rejection_score` | `fver_c36f4f2742f282ff44a177d62fc25bcf8e02ef470e0af92fe218a295c7307ad7` | `lver_3e558a545c10aac327f09ef8b1a5579b150e4a60322120b651678bfa5e7256b2` | `NQ_2022_full_year` | `NQ_2022_fwd_ret_5m` | 354112/3187008 | 347280/347280 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_235d4e8a8607bfc02e95b046a330e5dcf2bb7f845a499c9b20f6383d0fffbac3` | `lver_3e558a545c10aac327f09ef8b1a5579b150e4a60322120b651678bfa5e7256b2` | `NQ_2022_full_year` | `NQ_2022_fwd_ret_5m` | 354112/3187008 | 347280/347280 | 0 |
| `liquidity_structure_prior_high_distance` | `liquidity_structure_prior_high_distance` | `fver_e700a64be05f6d09188d0bd76b1199000ee85adb56162ddf186345eef676df0f` | `lver_788c5b36ea91d3ee218504edbb634215414ba79950066f4884361c13fe47b99b` | `NQ_2023_full_year` | `NQ_2023_fwd_ret_5m` | 353358/3180222 | 346469/346469 | 0 |
| `liquidity_structure_prior_low_distance` | `liquidity_structure_prior_low_distance` | `fver_6e14fd99a47131715cf5b549f87f9d19c4c03634e3192097fbe3886f907fb4c4` | `lver_788c5b36ea91d3ee218504edbb634215414ba79950066f4884361c13fe47b99b` | `NQ_2023_full_year` | `NQ_2023_fwd_ret_5m` | 353358/3180222 | 346469/346469 | 0 |
| `liquidity_structure_sweep_high_flag` | `liquidity_structure_sweep_high_flag` | `fver_ddcf278400cbcd542e6dbefc56dc55b6b288628dd55c0a50bbab6e94341b2b5e` | `lver_788c5b36ea91d3ee218504edbb634215414ba79950066f4884361c13fe47b99b` | `NQ_2023_full_year` | `NQ_2023_fwd_ret_5m` | 353358/3180222 | 346469/346469 | 0 |
| `liquidity_structure_sweep_low_flag` | `liquidity_structure_sweep_low_flag` | `fver_1fae1d4e1460b60cd95a062f85cbbecfb4f296eb722506f3f60bded0ea411e65` | `lver_788c5b36ea91d3ee218504edbb634215414ba79950066f4884361c13fe47b99b` | `NQ_2023_full_year` | `NQ_2023_fwd_ret_5m` | 353358/3180222 | 346469/346469 | 0 |
| `liquidity_structure_failed_high_breakout_flag` | `liquidity_structure_failed_high_breakout_flag` | `fver_5d2421e0a72d8fba0c927c931da5fdc1eba0feee9516ce626b9ef49af546f02c` | `lver_788c5b36ea91d3ee218504edbb634215414ba79950066f4884361c13fe47b99b` | `NQ_2023_full_year` | `NQ_2023_fwd_ret_5m` | 353358/3180222 | 346469/346469 | 0 |
| `liquidity_structure_failed_low_breakout_flag` | `liquidity_structure_failed_low_breakout_flag` | `fver_ab3524bf29c313198d4bd52d803ce565c87e38a4265cf17b17ae98a9f6dc46ad` | `lver_788c5b36ea91d3ee218504edbb634215414ba79950066f4884361c13fe47b99b` | `NQ_2023_full_year` | `NQ_2023_fwd_ret_5m` | 353358/3180222 | 346469/346469 | 0 |
| `liquidity_structure_close_location_value` | `liquidity_structure_close_location_value` | `fver_bb8d1c8b272ca3d49b910e55d9d0bcd6092dda600e357de9c4d996f6180fefa5` | `lver_788c5b36ea91d3ee218504edbb634215414ba79950066f4884361c13fe47b99b` | `NQ_2023_full_year` | `NQ_2023_fwd_ret_5m` | 353358/3180222 | 346469/346469 | 0 |
| `liquidity_structure_wick_rejection_score` | `liquidity_structure_wick_rejection_score` | `fver_664f59fae14577649c3bb7961b4061b42f32bef0dece74d538746de42ee05208` | `lver_788c5b36ea91d3ee218504edbb634215414ba79950066f4884361c13fe47b99b` | `NQ_2023_full_year` | `NQ_2023_fwd_ret_5m` | 353358/3180222 | 346469/346469 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_92a8331be3d9af851acbdc4fae725ad77d41a1bcd1bbcf8b5bbe7ff9eb08d0e9` | `lver_788c5b36ea91d3ee218504edbb634215414ba79950066f4884361c13fe47b99b` | `NQ_2023_full_year` | `NQ_2023_fwd_ret_5m` | 353358/3180222 | 346469/346469 | 0 |
| `liquidity_structure_prior_high_distance` | `liquidity_structure_prior_high_distance` | `fver_5b60f06e85792e1fda964b4534b80e398492178fd95d212a0a4e9043fe86b215` | `lver_d55884d1e10337c320e8fe0f59a768b3d2850868b81fd74fb8c9c92fe67d0742` | `NQ_2024_full_year` | `NQ_2024_fwd_ret_5m` | 346992/3122928 | 340126/340126 | 0 |
| `liquidity_structure_prior_low_distance` | `liquidity_structure_prior_low_distance` | `fver_32787814b8c27a427ccf9049e3b13b4fdad44b4d52af923adb91ec7f6dcf55a2` | `lver_d55884d1e10337c320e8fe0f59a768b3d2850868b81fd74fb8c9c92fe67d0742` | `NQ_2024_full_year` | `NQ_2024_fwd_ret_5m` | 346992/3122928 | 340126/340126 | 0 |
| `liquidity_structure_sweep_high_flag` | `liquidity_structure_sweep_high_flag` | `fver_4d7c7d3b0b0c871af894850c8b05c51b0d585a7f0040fd23c6b095eec45860f5` | `lver_d55884d1e10337c320e8fe0f59a768b3d2850868b81fd74fb8c9c92fe67d0742` | `NQ_2024_full_year` | `NQ_2024_fwd_ret_5m` | 346992/3122928 | 340126/340126 | 0 |
| `liquidity_structure_sweep_low_flag` | `liquidity_structure_sweep_low_flag` | `fver_3a53fcd057a0e5611f5c500e70faf6772a78c5c08c423a15270e485e217680d1` | `lver_d55884d1e10337c320e8fe0f59a768b3d2850868b81fd74fb8c9c92fe67d0742` | `NQ_2024_full_year` | `NQ_2024_fwd_ret_5m` | 346992/3122928 | 340126/340126 | 0 |
| `liquidity_structure_failed_high_breakout_flag` | `liquidity_structure_failed_high_breakout_flag` | `fver_b18febc38332f8082e108b2d3000228860e51ae4dac4f0a8fe11dbccb6c9840d` | `lver_d55884d1e10337c320e8fe0f59a768b3d2850868b81fd74fb8c9c92fe67d0742` | `NQ_2024_full_year` | `NQ_2024_fwd_ret_5m` | 346992/3122928 | 340126/340126 | 0 |
| `liquidity_structure_failed_low_breakout_flag` | `liquidity_structure_failed_low_breakout_flag` | `fver_7e773a1c9f4830aad1f83269c806987c2b1be3d1f6e4bdc364ea8f8db8983d3d` | `lver_d55884d1e10337c320e8fe0f59a768b3d2850868b81fd74fb8c9c92fe67d0742` | `NQ_2024_full_year` | `NQ_2024_fwd_ret_5m` | 346992/3122928 | 340126/340126 | 0 |
| `liquidity_structure_close_location_value` | `liquidity_structure_close_location_value` | `fver_0c725973cb915e3694ff4de680efa73cf6fb8fb3439d3ab6cd87feee9d412275` | `lver_d55884d1e10337c320e8fe0f59a768b3d2850868b81fd74fb8c9c92fe67d0742` | `NQ_2024_full_year` | `NQ_2024_fwd_ret_5m` | 346992/3122928 | 340126/340126 | 0 |
| `liquidity_structure_wick_rejection_score` | `liquidity_structure_wick_rejection_score` | `fver_9942f29be5c46b7f5ac4b63ac84fa39ada709fcc1833372b9478b7e67559da0b` | `lver_d55884d1e10337c320e8fe0f59a768b3d2850868b81fd74fb8c9c92fe67d0742` | `NQ_2024_full_year` | `NQ_2024_fwd_ret_5m` | 346992/3122928 | 340126/340126 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_8958c929d21570b5ac5b01cac25f141bcc60169e601130b53790d9dbbcb5d0b5` | `lver_d55884d1e10337c320e8fe0f59a768b3d2850868b81fd74fb8c9c92fe67d0742` | `NQ_2024_full_year` | `NQ_2024_fwd_ret_5m` | 346992/3122928 | 340126/340126 | 0 |
| `liquidity_structure_prior_high_distance` | `liquidity_structure_prior_high_distance` | `fver_e563699ffe40cb891ee3b3cdffee2dc1579c7dd1fcaa4a900fbaeacc2374334a` | `lver_e44dada099cdaab8716351d737918246c93535ad93e9e686f9c8d1ae21c27c57` | `NQ_2025_full_year` | `NQ_2025_fwd_ret_5m` | 344529/3100761 | 337672/337672 | 0 |
| `liquidity_structure_prior_low_distance` | `liquidity_structure_prior_low_distance` | `fver_be01efae6e848630bd9495735919aa0d96755e2a63d7632f626b30cd0c5563fa` | `lver_e44dada099cdaab8716351d737918246c93535ad93e9e686f9c8d1ae21c27c57` | `NQ_2025_full_year` | `NQ_2025_fwd_ret_5m` | 344529/3100761 | 337672/337672 | 0 |
| `liquidity_structure_sweep_high_flag` | `liquidity_structure_sweep_high_flag` | `fver_9b5b2a8555ce1ff7c0aecdc323242644e0cf8810dc30ca108cb63e07a48b0e47` | `lver_e44dada099cdaab8716351d737918246c93535ad93e9e686f9c8d1ae21c27c57` | `NQ_2025_full_year` | `NQ_2025_fwd_ret_5m` | 344529/3100761 | 337672/337672 | 0 |
| `liquidity_structure_sweep_low_flag` | `liquidity_structure_sweep_low_flag` | `fver_752035589892f1d81e006c16c764a078841f82887fbede75c1c1942b96bed902` | `lver_e44dada099cdaab8716351d737918246c93535ad93e9e686f9c8d1ae21c27c57` | `NQ_2025_full_year` | `NQ_2025_fwd_ret_5m` | 344529/3100761 | 337672/337672 | 0 |
| `liquidity_structure_failed_high_breakout_flag` | `liquidity_structure_failed_high_breakout_flag` | `fver_8e16628fb27595fee7cc411d295cf7e053bb4847597c910bc3c9b9492dc15ca4` | `lver_e44dada099cdaab8716351d737918246c93535ad93e9e686f9c8d1ae21c27c57` | `NQ_2025_full_year` | `NQ_2025_fwd_ret_5m` | 344529/3100761 | 337672/337672 | 0 |
| `liquidity_structure_failed_low_breakout_flag` | `liquidity_structure_failed_low_breakout_flag` | `fver_4ff4bfe3910a7b4fab153479584f15124862fbe38ae53f601e2a5ff6021ffc21` | `lver_e44dada099cdaab8716351d737918246c93535ad93e9e686f9c8d1ae21c27c57` | `NQ_2025_full_year` | `NQ_2025_fwd_ret_5m` | 344529/3100761 | 337672/337672 | 0 |
| `liquidity_structure_close_location_value` | `liquidity_structure_close_location_value` | `fver_6a26d8e5a40d72d647698dd75140d51fec6df63e1c3ba71fae878263acea9e98` | `lver_e44dada099cdaab8716351d737918246c93535ad93e9e686f9c8d1ae21c27c57` | `NQ_2025_full_year` | `NQ_2025_fwd_ret_5m` | 344529/3100761 | 337672/337672 | 0 |
| `liquidity_structure_wick_rejection_score` | `liquidity_structure_wick_rejection_score` | `fver_59b7760413c57eb985d9869a588162d466b48f67fd590bdd770b186a47eb6b37` | `lver_e44dada099cdaab8716351d737918246c93535ad93e9e686f9c8d1ae21c27c57` | `NQ_2025_full_year` | `NQ_2025_fwd_ret_5m` | 344529/3100761 | 337672/337672 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_2ff1116da6fd63d7d1dc9f3203ec9534e5d2246f9b44e4996888ddc0504bd8c4` | `lver_e44dada099cdaab8716351d737918246c93535ad93e9e686f9c8d1ae21c27c57` | `NQ_2025_full_year` | `NQ_2025_fwd_ret_5m` | 344529/3100761 | 337672/337672 | 0 |
| `liquidity_structure_prior_high_distance` | `liquidity_structure_prior_high_distance` | `fver_fd5a35a7f2fcad83c7d2639bab1de635c3201b16369d75f9092228f9419af83b` | `lver_0dd4d33df9674717ddcff1f7e1b3d6cde33da721f2bb36b3ad8e22a2e72e6dce` | `NQ_2026_full_year` | `NQ_2026_fwd_ret_5m` | 140610/1265490 | 138694/138694 | 0 |
| `liquidity_structure_prior_low_distance` | `liquidity_structure_prior_low_distance` | `fver_94ee2c06f0bc7cbffa246e82614c6a0d8ded98d449b44fdbb820afd98005351b` | `lver_0dd4d33df9674717ddcff1f7e1b3d6cde33da721f2bb36b3ad8e22a2e72e6dce` | `NQ_2026_full_year` | `NQ_2026_fwd_ret_5m` | 140610/1265490 | 138694/138694 | 0 |
| `liquidity_structure_sweep_high_flag` | `liquidity_structure_sweep_high_flag` | `fver_2a7bff5d8e5f43ad3d536beed45807cbc53312256cb2d2dbb41f34302b7c8df6` | `lver_0dd4d33df9674717ddcff1f7e1b3d6cde33da721f2bb36b3ad8e22a2e72e6dce` | `NQ_2026_full_year` | `NQ_2026_fwd_ret_5m` | 140610/1265490 | 138694/138694 | 0 |
| `liquidity_structure_sweep_low_flag` | `liquidity_structure_sweep_low_flag` | `fver_f181389b7b70a7a10b2c245e44e2ae21802c50b0d374ac825b6a206b4c9c3f1c` | `lver_0dd4d33df9674717ddcff1f7e1b3d6cde33da721f2bb36b3ad8e22a2e72e6dce` | `NQ_2026_full_year` | `NQ_2026_fwd_ret_5m` | 140610/1265490 | 138694/138694 | 0 |
| `liquidity_structure_failed_high_breakout_flag` | `liquidity_structure_failed_high_breakout_flag` | `fver_1b3ce34f6f01c9329c8e3e4a723b7e4be006aacb53efa826a3e35264b41624c9` | `lver_0dd4d33df9674717ddcff1f7e1b3d6cde33da721f2bb36b3ad8e22a2e72e6dce` | `NQ_2026_full_year` | `NQ_2026_fwd_ret_5m` | 140610/1265490 | 138694/138694 | 0 |
| `liquidity_structure_failed_low_breakout_flag` | `liquidity_structure_failed_low_breakout_flag` | `fver_360d04493f162a6748815630d44c1861aefd4dc9a322c962600216d17432c045` | `lver_0dd4d33df9674717ddcff1f7e1b3d6cde33da721f2bb36b3ad8e22a2e72e6dce` | `NQ_2026_full_year` | `NQ_2026_fwd_ret_5m` | 140610/1265490 | 138694/138694 | 0 |
| `liquidity_structure_close_location_value` | `liquidity_structure_close_location_value` | `fver_967b801dc1ae97a96e2cbf52f49bb0f83982e45d5f150601055a151f302f45e2` | `lver_0dd4d33df9674717ddcff1f7e1b3d6cde33da721f2bb36b3ad8e22a2e72e6dce` | `NQ_2026_full_year` | `NQ_2026_fwd_ret_5m` | 140610/1265490 | 138694/138694 | 0 |
| `liquidity_structure_wick_rejection_score` | `liquidity_structure_wick_rejection_score` | `fver_5dd5c86e768e6737dc7c0c31cd428b07a589063b0f989480cb281e685e7774a9` | `lver_0dd4d33df9674717ddcff1f7e1b3d6cde33da721f2bb36b3ad8e22a2e72e6dce` | `NQ_2026_full_year` | `NQ_2026_fwd_ret_5m` | 140610/1265490 | 138694/138694 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_fcd8bb5459e27f98c7d106a860c6887b7a8a83ae058e7e92a53dfed3c660ed12` | `lver_0dd4d33df9674717ddcff1f7e1b3d6cde33da721f2bb36b3ad8e22a2e72e6dce` | `NQ_2026_full_year` | `NQ_2026_fwd_ret_5m` | 140610/1265490 | 138694/138694 | 0 |
| `liquidity_structure_prior_high_distance` | `liquidity_structure_prior_high_distance` | `fver_e72b2ae7f92714d99265a8668e7b9d6cca2eff47368da798f09922ec3f40f694` | `lver_cde42aaecd43ea9b973fb1b9566dafd4ffd35696efa3f25a0723c3ad616a82da` | `RTY_2019_full_year` | `RTY_2019_fwd_ret_5m` | 328841/2959569 | 305433/305433 | 0 |
| `liquidity_structure_prior_low_distance` | `liquidity_structure_prior_low_distance` | `fver_43dad08f4dc2b44f64bcc4acbfb645a3e56f4ee7089fa073a25d2fb45e6377ba` | `lver_cde42aaecd43ea9b973fb1b9566dafd4ffd35696efa3f25a0723c3ad616a82da` | `RTY_2019_full_year` | `RTY_2019_fwd_ret_5m` | 328841/2959569 | 305433/305433 | 0 |
| `liquidity_structure_sweep_high_flag` | `liquidity_structure_sweep_high_flag` | `fver_201f43eefc263565c081b63184c7bf7e16cf13bd86ef275c13f40b2f18fb7ffe` | `lver_cde42aaecd43ea9b973fb1b9566dafd4ffd35696efa3f25a0723c3ad616a82da` | `RTY_2019_full_year` | `RTY_2019_fwd_ret_5m` | 328841/2959569 | 305433/305433 | 0 |
| `liquidity_structure_sweep_low_flag` | `liquidity_structure_sweep_low_flag` | `fver_f76de43df6043bd1ef7b1c9aa0ddd284e67b4ee66abd5048dce37f39d0f69168` | `lver_cde42aaecd43ea9b973fb1b9566dafd4ffd35696efa3f25a0723c3ad616a82da` | `RTY_2019_full_year` | `RTY_2019_fwd_ret_5m` | 328841/2959569 | 305433/305433 | 0 |
| `liquidity_structure_failed_high_breakout_flag` | `liquidity_structure_failed_high_breakout_flag` | `fver_8f29e2785b0f622f6122a89f8f76b3227ddc3f2bac097d3e87778a436f2f851e` | `lver_cde42aaecd43ea9b973fb1b9566dafd4ffd35696efa3f25a0723c3ad616a82da` | `RTY_2019_full_year` | `RTY_2019_fwd_ret_5m` | 328841/2959569 | 305433/305433 | 0 |
| `liquidity_structure_failed_low_breakout_flag` | `liquidity_structure_failed_low_breakout_flag` | `fver_ea0856b6f16b169ca7ea2527039c645224fccc7d333faf612cf5d3f0e71b6388` | `lver_cde42aaecd43ea9b973fb1b9566dafd4ffd35696efa3f25a0723c3ad616a82da` | `RTY_2019_full_year` | `RTY_2019_fwd_ret_5m` | 328841/2959569 | 305433/305433 | 0 |
| `liquidity_structure_close_location_value` | `liquidity_structure_close_location_value` | `fver_c0537e090c201e30befb09dfac6e9e20347adbc42cec0031477ff0c011f1e29d` | `lver_cde42aaecd43ea9b973fb1b9566dafd4ffd35696efa3f25a0723c3ad616a82da` | `RTY_2019_full_year` | `RTY_2019_fwd_ret_5m` | 328841/2959569 | 305433/305433 | 0 |
| `liquidity_structure_wick_rejection_score` | `liquidity_structure_wick_rejection_score` | `fver_f4df2abd46f5ad48302b351a869acb129fe3c46e9e1c1a811badcbcb875ff6f5` | `lver_cde42aaecd43ea9b973fb1b9566dafd4ffd35696efa3f25a0723c3ad616a82da` | `RTY_2019_full_year` | `RTY_2019_fwd_ret_5m` | 328841/2959569 | 305433/305433 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_7a93b21c08d3f12b233eb5a4388371327a4fd394792a32ae96d9675850afb65a` | `lver_cde42aaecd43ea9b973fb1b9566dafd4ffd35696efa3f25a0723c3ad616a82da` | `RTY_2019_full_year` | `RTY_2019_fwd_ret_5m` | 328841/2959569 | 305433/305433 | 0 |
| `liquidity_structure_prior_high_distance` | `liquidity_structure_prior_high_distance` | `fver_f3d0c8922f0ed405239cbb870c6e98a048f14ddb28e4ed8b86566623003bc558` | `lver_75f21845ff10f3e5fc301100a782f93563d078ed468a557dd7925016147a8515` | `RTY_2020_full_year` | `RTY_2020_fwd_ret_5m` | 338085/3042765 | 322373/322373 | 0 |
| `liquidity_structure_prior_low_distance` | `liquidity_structure_prior_low_distance` | `fver_01b6421899bf838e03cf78f6b26387513dc353eb9036f88f1e85251a5afe6f00` | `lver_75f21845ff10f3e5fc301100a782f93563d078ed468a557dd7925016147a8515` | `RTY_2020_full_year` | `RTY_2020_fwd_ret_5m` | 338085/3042765 | 322373/322373 | 0 |
| `liquidity_structure_sweep_high_flag` | `liquidity_structure_sweep_high_flag` | `fver_e8e47166176d6074f295f17fa2092bdedfd22299b05fb96ef7260b5a60bd8b9c` | `lver_75f21845ff10f3e5fc301100a782f93563d078ed468a557dd7925016147a8515` | `RTY_2020_full_year` | `RTY_2020_fwd_ret_5m` | 338085/3042765 | 322373/322373 | 0 |
| `liquidity_structure_sweep_low_flag` | `liquidity_structure_sweep_low_flag` | `fver_21737129ba03898795443af742b764c0f4a00724e920f41fd89b42e2cbfb6857` | `lver_75f21845ff10f3e5fc301100a782f93563d078ed468a557dd7925016147a8515` | `RTY_2020_full_year` | `RTY_2020_fwd_ret_5m` | 338085/3042765 | 322373/322373 | 0 |
| `liquidity_structure_failed_high_breakout_flag` | `liquidity_structure_failed_high_breakout_flag` | `fver_39dad7eecb7371369b80a837a1969cff0235f2594eef1bb7fa1bbf5edb85c64c` | `lver_75f21845ff10f3e5fc301100a782f93563d078ed468a557dd7925016147a8515` | `RTY_2020_full_year` | `RTY_2020_fwd_ret_5m` | 338085/3042765 | 322373/322373 | 0 |
| `liquidity_structure_failed_low_breakout_flag` | `liquidity_structure_failed_low_breakout_flag` | `fver_cb1f73e4c4ccd05eb500c3e0bfb1ed1d09ce109c74b052f2e4c1dacbcab8399f` | `lver_75f21845ff10f3e5fc301100a782f93563d078ed468a557dd7925016147a8515` | `RTY_2020_full_year` | `RTY_2020_fwd_ret_5m` | 338085/3042765 | 322373/322373 | 0 |
| `liquidity_structure_close_location_value` | `liquidity_structure_close_location_value` | `fver_61dc71efddcd24784723b06c7080ab24192e48522f7d521956aafa7b312bd360` | `lver_75f21845ff10f3e5fc301100a782f93563d078ed468a557dd7925016147a8515` | `RTY_2020_full_year` | `RTY_2020_fwd_ret_5m` | 338085/3042765 | 322373/322373 | 0 |
| `liquidity_structure_wick_rejection_score` | `liquidity_structure_wick_rejection_score` | `fver_dcd6faf786ae1475c77cab8ac6ef47d6155591c8dda000f6f8dd29d66746824a` | `lver_75f21845ff10f3e5fc301100a782f93563d078ed468a557dd7925016147a8515` | `RTY_2020_full_year` | `RTY_2020_fwd_ret_5m` | 338085/3042765 | 322373/322373 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_fadd8911d5323b8854d08402a100f2ab8ebb09bf58f384a1ddba6314c0268326` | `lver_75f21845ff10f3e5fc301100a782f93563d078ed468a557dd7925016147a8515` | `RTY_2020_full_year` | `RTY_2020_fwd_ret_5m` | 338085/3042765 | 322373/322373 | 0 |
| `liquidity_structure_prior_high_distance` | `liquidity_structure_prior_high_distance` | `fver_32af9e6855d61536b9bcb47e2dcb77a5aea1e07b9d96637809ac9538ddf6d958` | `lver_67b5dd02c7818d913feafdb73b6dfd347e287b510091d3a95699e6916e6ddfe0` | `RTY_2021_full_year` | `RTY_2021_fwd_ret_5m` | 339895/3059055 | 322315/322315 | 0 |
| `liquidity_structure_prior_low_distance` | `liquidity_structure_prior_low_distance` | `fver_1926aef9114e3e00e8356988d306a82627a5c88c77d03699b040f7bd1f31f73b` | `lver_67b5dd02c7818d913feafdb73b6dfd347e287b510091d3a95699e6916e6ddfe0` | `RTY_2021_full_year` | `RTY_2021_fwd_ret_5m` | 339895/3059055 | 322315/322315 | 0 |
| `liquidity_structure_sweep_high_flag` | `liquidity_structure_sweep_high_flag` | `fver_6b4acae1e68595a37212a9fbb2609b012e9b5073764160317671342d26cba12b` | `lver_67b5dd02c7818d913feafdb73b6dfd347e287b510091d3a95699e6916e6ddfe0` | `RTY_2021_full_year` | `RTY_2021_fwd_ret_5m` | 339895/3059055 | 322315/322315 | 0 |
| `liquidity_structure_sweep_low_flag` | `liquidity_structure_sweep_low_flag` | `fver_93685e508aa6061a3ad5e0b092802883c5de08501446138d2b228f708c971e18` | `lver_67b5dd02c7818d913feafdb73b6dfd347e287b510091d3a95699e6916e6ddfe0` | `RTY_2021_full_year` | `RTY_2021_fwd_ret_5m` | 339895/3059055 | 322315/322315 | 0 |
| `liquidity_structure_failed_high_breakout_flag` | `liquidity_structure_failed_high_breakout_flag` | `fver_d64f9a9bdb62b2be42ad9615ef50505bb1a3dc296544d41582e6ff4a003dcefa` | `lver_67b5dd02c7818d913feafdb73b6dfd347e287b510091d3a95699e6916e6ddfe0` | `RTY_2021_full_year` | `RTY_2021_fwd_ret_5m` | 339895/3059055 | 322315/322315 | 0 |
| `liquidity_structure_failed_low_breakout_flag` | `liquidity_structure_failed_low_breakout_flag` | `fver_b9adb15f9964e3742d4a77fa1476afb4c52d1988c9fe35a204ec091d0a0c38e0` | `lver_67b5dd02c7818d913feafdb73b6dfd347e287b510091d3a95699e6916e6ddfe0` | `RTY_2021_full_year` | `RTY_2021_fwd_ret_5m` | 339895/3059055 | 322315/322315 | 0 |
| `liquidity_structure_close_location_value` | `liquidity_structure_close_location_value` | `fver_67766cb0051ad8ca790f6a756718695c05274e2661ea127bf05ff7a92f2d1707` | `lver_67b5dd02c7818d913feafdb73b6dfd347e287b510091d3a95699e6916e6ddfe0` | `RTY_2021_full_year` | `RTY_2021_fwd_ret_5m` | 339895/3059055 | 322315/322315 | 0 |
| `liquidity_structure_wick_rejection_score` | `liquidity_structure_wick_rejection_score` | `fver_e27e5a761a18d14476f140c839c4e9d4673279d226a4731101bbb5b73718467a` | `lver_67b5dd02c7818d913feafdb73b6dfd347e287b510091d3a95699e6916e6ddfe0` | `RTY_2021_full_year` | `RTY_2021_fwd_ret_5m` | 339895/3059055 | 322315/322315 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_655849c22a9d046cdadeb2da86cdd96c89ffb16fa9adbc2399732f7de859dc31` | `lver_67b5dd02c7818d913feafdb73b6dfd347e287b510091d3a95699e6916e6ddfe0` | `RTY_2021_full_year` | `RTY_2021_fwd_ret_5m` | 339895/3059055 | 322315/322315 | 0 |
| `liquidity_structure_prior_high_distance` | `liquidity_structure_prior_high_distance` | `fver_185a4fd9bf1cb0e42dbcc7549a65190dd131e3da04dcfe4dc00a038b10e4af2d` | `lver_40d478b5c4351a28da47141a7158f69407abb7528f67c13aa99334a3b823665a` | `RTY_2022_full_year` | `RTY_2022_fwd_ret_5m` | 345162/3106458 | 331308/331308 | 0 |
| `liquidity_structure_prior_low_distance` | `liquidity_structure_prior_low_distance` | `fver_b453da7a7630b79c52d41bdbee4bd20c57396c1efc06da63ad1ace7c7b25c0ff` | `lver_40d478b5c4351a28da47141a7158f69407abb7528f67c13aa99334a3b823665a` | `RTY_2022_full_year` | `RTY_2022_fwd_ret_5m` | 345162/3106458 | 331308/331308 | 0 |
| `liquidity_structure_sweep_high_flag` | `liquidity_structure_sweep_high_flag` | `fver_60bb852d94ec80c878a5f6a78bd2c018833dc7c45750c57b9e09602c26a2f09c` | `lver_40d478b5c4351a28da47141a7158f69407abb7528f67c13aa99334a3b823665a` | `RTY_2022_full_year` | `RTY_2022_fwd_ret_5m` | 345162/3106458 | 331308/331308 | 0 |
| `liquidity_structure_sweep_low_flag` | `liquidity_structure_sweep_low_flag` | `fver_f894186119ae631952a6fd5bcf8f303746448a4768cf686d7051b92f303f2e20` | `lver_40d478b5c4351a28da47141a7158f69407abb7528f67c13aa99334a3b823665a` | `RTY_2022_full_year` | `RTY_2022_fwd_ret_5m` | 345162/3106458 | 331308/331308 | 0 |
| `liquidity_structure_failed_high_breakout_flag` | `liquidity_structure_failed_high_breakout_flag` | `fver_26415ceebc70725c8b67f2b8a75808de9dc0a40407ac2a5ebdec27094c22cc27` | `lver_40d478b5c4351a28da47141a7158f69407abb7528f67c13aa99334a3b823665a` | `RTY_2022_full_year` | `RTY_2022_fwd_ret_5m` | 345162/3106458 | 331308/331308 | 0 |
| `liquidity_structure_failed_low_breakout_flag` | `liquidity_structure_failed_low_breakout_flag` | `fver_d7d4654100f5c1c5a2f4e5b48590bfdd5ac92f50bb6ff37cd62bda4c8ded4e99` | `lver_40d478b5c4351a28da47141a7158f69407abb7528f67c13aa99334a3b823665a` | `RTY_2022_full_year` | `RTY_2022_fwd_ret_5m` | 345162/3106458 | 331308/331308 | 0 |
| `liquidity_structure_close_location_value` | `liquidity_structure_close_location_value` | `fver_c6f35a8025ce0246d0189c32f6d9de608d68a17d8735759c213bad9546686ec9` | `lver_40d478b5c4351a28da47141a7158f69407abb7528f67c13aa99334a3b823665a` | `RTY_2022_full_year` | `RTY_2022_fwd_ret_5m` | 345162/3106458 | 331308/331308 | 0 |
| `liquidity_structure_wick_rejection_score` | `liquidity_structure_wick_rejection_score` | `fver_1543e48fb92af41b24930bd7e24e5a3343daba8a7ee5501619128e7983723276` | `lver_40d478b5c4351a28da47141a7158f69407abb7528f67c13aa99334a3b823665a` | `RTY_2022_full_year` | `RTY_2022_fwd_ret_5m` | 345162/3106458 | 331308/331308 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_74d235e6ea40419a62eaeec29d0ca6f884c2934d4c92f99389e8907c1411e6db` | `lver_40d478b5c4351a28da47141a7158f69407abb7528f67c13aa99334a3b823665a` | `RTY_2022_full_year` | `RTY_2022_fwd_ret_5m` | 345162/3106458 | 331308/331308 | 0 |
| `liquidity_structure_prior_high_distance` | `liquidity_structure_prior_high_distance` | `fver_fe35ebc080b6089cf19748bf77529907a6c9b5488beffea8ec62d6878284a77a` | `lver_5ab0e573cb33cad2ef08f86bf4a19a0e37e9df514855bf720658ce2d2d69933b` | `RTY_2023_full_year` | `RTY_2023_fwd_ret_5m` | 342436/3081924 | 327109/327109 | 0 |
| `liquidity_structure_prior_low_distance` | `liquidity_structure_prior_low_distance` | `fver_85e7af1ceeed374a613a4d81374af14d5102231b5adf9639a096ae45e0ccd284` | `lver_5ab0e573cb33cad2ef08f86bf4a19a0e37e9df514855bf720658ce2d2d69933b` | `RTY_2023_full_year` | `RTY_2023_fwd_ret_5m` | 342436/3081924 | 327109/327109 | 0 |
| `liquidity_structure_sweep_high_flag` | `liquidity_structure_sweep_high_flag` | `fver_008b4d8d5d706168d431a0400559718847f2d93ea9954fe57573813fa3aebd32` | `lver_5ab0e573cb33cad2ef08f86bf4a19a0e37e9df514855bf720658ce2d2d69933b` | `RTY_2023_full_year` | `RTY_2023_fwd_ret_5m` | 342436/3081924 | 327109/327109 | 0 |
| `liquidity_structure_sweep_low_flag` | `liquidity_structure_sweep_low_flag` | `fver_4248820037dffffb5c40f8c0c587f88cfc3bdda45c4a8d4e5d6ffe628c8e27de` | `lver_5ab0e573cb33cad2ef08f86bf4a19a0e37e9df514855bf720658ce2d2d69933b` | `RTY_2023_full_year` | `RTY_2023_fwd_ret_5m` | 342436/3081924 | 327109/327109 | 0 |
| `liquidity_structure_failed_high_breakout_flag` | `liquidity_structure_failed_high_breakout_flag` | `fver_00d833cef512d3216b82045846ae3b30489d8118cfb3ef50e882e43bb6d482fa` | `lver_5ab0e573cb33cad2ef08f86bf4a19a0e37e9df514855bf720658ce2d2d69933b` | `RTY_2023_full_year` | `RTY_2023_fwd_ret_5m` | 342436/3081924 | 327109/327109 | 0 |
| `liquidity_structure_failed_low_breakout_flag` | `liquidity_structure_failed_low_breakout_flag` | `fver_147bb5a2bf6c1b03586f75ea6caa3b0513ee84484cb1aba64b90f22c3e7642ec` | `lver_5ab0e573cb33cad2ef08f86bf4a19a0e37e9df514855bf720658ce2d2d69933b` | `RTY_2023_full_year` | `RTY_2023_fwd_ret_5m` | 342436/3081924 | 327109/327109 | 0 |
| `liquidity_structure_close_location_value` | `liquidity_structure_close_location_value` | `fver_a8f85d223708bf21b7307884cd1b33fc95642fe3b3b54c1b6769900bdceafae0` | `lver_5ab0e573cb33cad2ef08f86bf4a19a0e37e9df514855bf720658ce2d2d69933b` | `RTY_2023_full_year` | `RTY_2023_fwd_ret_5m` | 342436/3081924 | 327109/327109 | 0 |
| `liquidity_structure_wick_rejection_score` | `liquidity_structure_wick_rejection_score` | `fver_daf518cbb83aaa827f3586f098e0ac0546cca33785fc3b2aa6625ae4ec38c5aa` | `lver_5ab0e573cb33cad2ef08f86bf4a19a0e37e9df514855bf720658ce2d2d69933b` | `RTY_2023_full_year` | `RTY_2023_fwd_ret_5m` | 342436/3081924 | 327109/327109 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_7f9cdfc620eadfe6043f2f5f1176e798121c06c17854b95f36c7c46f153fc463` | `lver_5ab0e573cb33cad2ef08f86bf4a19a0e37e9df514855bf720658ce2d2d69933b` | `RTY_2023_full_year` | `RTY_2023_fwd_ret_5m` | 342436/3081924 | 327109/327109 | 0 |
| `liquidity_structure_prior_high_distance` | `liquidity_structure_prior_high_distance` | `fver_310210bc009fb027ca442c1b4c4357e27046b2eb4a9a9f102d86fd0c2e06b8ae` | `lver_07924603a1e7ed0e4288803aa93dd63569e14597f35e54a82bcfe0d4117c8276` | `RTY_2024_full_year` | `RTY_2024_fwd_ret_5m` | 333540/3001860 | 317000/317000 | 0 |
| `liquidity_structure_prior_low_distance` | `liquidity_structure_prior_low_distance` | `fver_c3714619d3103ce67994e345020ada5fa015a81b6e484cf50979f48d0b99631c` | `lver_07924603a1e7ed0e4288803aa93dd63569e14597f35e54a82bcfe0d4117c8276` | `RTY_2024_full_year` | `RTY_2024_fwd_ret_5m` | 333540/3001860 | 317000/317000 | 0 |
| `liquidity_structure_sweep_high_flag` | `liquidity_structure_sweep_high_flag` | `fver_aedd129301c5c40eb568d55b01bf70c35ac3f70d69345bb7d1d1eccdc2278d7a` | `lver_07924603a1e7ed0e4288803aa93dd63569e14597f35e54a82bcfe0d4117c8276` | `RTY_2024_full_year` | `RTY_2024_fwd_ret_5m` | 333540/3001860 | 317000/317000 | 0 |
| `liquidity_structure_sweep_low_flag` | `liquidity_structure_sweep_low_flag` | `fver_7d241b8a14d653c2de19058fa47065a9e30053562be8c67b4884350349a96a98` | `lver_07924603a1e7ed0e4288803aa93dd63569e14597f35e54a82bcfe0d4117c8276` | `RTY_2024_full_year` | `RTY_2024_fwd_ret_5m` | 333540/3001860 | 317000/317000 | 0 |
| `liquidity_structure_failed_high_breakout_flag` | `liquidity_structure_failed_high_breakout_flag` | `fver_0a00b5aa649f78651ccbb49ad256188ff3574b74ddb92ba5390ddfc613b0c518` | `lver_07924603a1e7ed0e4288803aa93dd63569e14597f35e54a82bcfe0d4117c8276` | `RTY_2024_full_year` | `RTY_2024_fwd_ret_5m` | 333540/3001860 | 317000/317000 | 0 |
| `liquidity_structure_failed_low_breakout_flag` | `liquidity_structure_failed_low_breakout_flag` | `fver_c5ff15815fdc32c058c89b79ade9f249a4a9096b2ce51b0255b3061be698effe` | `lver_07924603a1e7ed0e4288803aa93dd63569e14597f35e54a82bcfe0d4117c8276` | `RTY_2024_full_year` | `RTY_2024_fwd_ret_5m` | 333540/3001860 | 317000/317000 | 0 |
| `liquidity_structure_close_location_value` | `liquidity_structure_close_location_value` | `fver_62aa09d5184a1074f56c0c3a8935b39a0a3c8a81ad72222ba6fa1853e85db59e` | `lver_07924603a1e7ed0e4288803aa93dd63569e14597f35e54a82bcfe0d4117c8276` | `RTY_2024_full_year` | `RTY_2024_fwd_ret_5m` | 333540/3001860 | 317000/317000 | 0 |
| `liquidity_structure_wick_rejection_score` | `liquidity_structure_wick_rejection_score` | `fver_97f8253b842fc3706aa553aa5e06a4e52c3819db9a2b94a69351d4f7b3e49a2e` | `lver_07924603a1e7ed0e4288803aa93dd63569e14597f35e54a82bcfe0d4117c8276` | `RTY_2024_full_year` | `RTY_2024_fwd_ret_5m` | 333540/3001860 | 317000/317000 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_7185c9cba8f03fe0eff14e454ab658d4aa2270b88b7a5466a7a3dcfc5b853fd0` | `lver_07924603a1e7ed0e4288803aa93dd63569e14597f35e54a82bcfe0d4117c8276` | `RTY_2024_full_year` | `RTY_2024_fwd_ret_5m` | 333540/3001860 | 317000/317000 | 0 |
| `liquidity_structure_prior_high_distance` | `liquidity_structure_prior_high_distance` | `fver_e3493f5df20a9cd8c935cafd86985c1cd901483e9a7974f45f5a42c432d24563` | `lver_623e0fbb4a453462950fbb3e370820d6cd002e9358b8211c36992601b4112bce` | `RTY_2025_full_year` | `RTY_2025_fwd_ret_5m` | 333557/3002013 | 318544/318544 | 0 |
| `liquidity_structure_prior_low_distance` | `liquidity_structure_prior_low_distance` | `fver_e76bed9b742145d95ccb34f92d5ee369d53b1540822f657ca495b95da73e98e9` | `lver_623e0fbb4a453462950fbb3e370820d6cd002e9358b8211c36992601b4112bce` | `RTY_2025_full_year` | `RTY_2025_fwd_ret_5m` | 333557/3002013 | 318544/318544 | 0 |
| `liquidity_structure_sweep_high_flag` | `liquidity_structure_sweep_high_flag` | `fver_b61896f92f79a82ed64ce2e079829cc48218b701788e797f3a794a0f6753472b` | `lver_623e0fbb4a453462950fbb3e370820d6cd002e9358b8211c36992601b4112bce` | `RTY_2025_full_year` | `RTY_2025_fwd_ret_5m` | 333557/3002013 | 318544/318544 | 0 |
| `liquidity_structure_sweep_low_flag` | `liquidity_structure_sweep_low_flag` | `fver_0e999053a518996a391a41012d8517693a4add6f137aff3219b6037b47aad6f5` | `lver_623e0fbb4a453462950fbb3e370820d6cd002e9358b8211c36992601b4112bce` | `RTY_2025_full_year` | `RTY_2025_fwd_ret_5m` | 333557/3002013 | 318544/318544 | 0 |
| `liquidity_structure_failed_high_breakout_flag` | `liquidity_structure_failed_high_breakout_flag` | `fver_f5c5c3e619ca9d5d2629857a6894916bb0b18f46e9c35ffdf9f08e1d74a43cac` | `lver_623e0fbb4a453462950fbb3e370820d6cd002e9358b8211c36992601b4112bce` | `RTY_2025_full_year` | `RTY_2025_fwd_ret_5m` | 333557/3002013 | 318544/318544 | 0 |
| `liquidity_structure_failed_low_breakout_flag` | `liquidity_structure_failed_low_breakout_flag` | `fver_54cc528e0910c50589057f20d26c64b28b589395f8e0a554cdc14b28e4b193e8` | `lver_623e0fbb4a453462950fbb3e370820d6cd002e9358b8211c36992601b4112bce` | `RTY_2025_full_year` | `RTY_2025_fwd_ret_5m` | 333557/3002013 | 318544/318544 | 0 |
| `liquidity_structure_close_location_value` | `liquidity_structure_close_location_value` | `fver_4dfa072fc1bde35d37a42c5827f014e81d9e62143d64a0c5826bddc0a28294ff` | `lver_623e0fbb4a453462950fbb3e370820d6cd002e9358b8211c36992601b4112bce` | `RTY_2025_full_year` | `RTY_2025_fwd_ret_5m` | 333557/3002013 | 318544/318544 | 0 |
| `liquidity_structure_wick_rejection_score` | `liquidity_structure_wick_rejection_score` | `fver_002c40d18af2104c0ccb1fadb87448301f04a9dcfd1d20f3b68943b92f14c15c` | `lver_623e0fbb4a453462950fbb3e370820d6cd002e9358b8211c36992601b4112bce` | `RTY_2025_full_year` | `RTY_2025_fwd_ret_5m` | 333557/3002013 | 318544/318544 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_29cba4508ad48e8dece91536b627e2b0780d13fd6e09c97536427f6a4d28d395` | `lver_623e0fbb4a453462950fbb3e370820d6cd002e9358b8211c36992601b4112bce` | `RTY_2025_full_year` | `RTY_2025_fwd_ret_5m` | 333557/3002013 | 318544/318544 | 0 |
| `liquidity_structure_prior_high_distance` | `liquidity_structure_prior_high_distance` | `fver_28d6beaf53b153e0f78d25fddf8df3eab5bd2d2247d9dfdf35f4407b2aea4d1e` | `lver_a33ae299ed3b794fad79f94a0a906ab858f071e4990c834e530061bc1c1a6f2b` | `RTY_2026_full_year` | `RTY_2026_fwd_ret_5m` | 138593/1247337 | 134990/134990 | 0 |
| `liquidity_structure_prior_low_distance` | `liquidity_structure_prior_low_distance` | `fver_12f7823e2e74435fc41b98857104b5ae3478cdd5675bd92fe03f3552f0dcc897` | `lver_a33ae299ed3b794fad79f94a0a906ab858f071e4990c834e530061bc1c1a6f2b` | `RTY_2026_full_year` | `RTY_2026_fwd_ret_5m` | 138593/1247337 | 134990/134990 | 0 |
| `liquidity_structure_sweep_high_flag` | `liquidity_structure_sweep_high_flag` | `fver_79c79b7ff8268de66aac7f519c48001cb23d861ffe5cae75f03547d279f47d7e` | `lver_a33ae299ed3b794fad79f94a0a906ab858f071e4990c834e530061bc1c1a6f2b` | `RTY_2026_full_year` | `RTY_2026_fwd_ret_5m` | 138593/1247337 | 134990/134990 | 0 |
| `liquidity_structure_sweep_low_flag` | `liquidity_structure_sweep_low_flag` | `fver_8732aefa815738bb8dc409444e555cf7c0761dd696d403d366fdc3f0d37f00b5` | `lver_a33ae299ed3b794fad79f94a0a906ab858f071e4990c834e530061bc1c1a6f2b` | `RTY_2026_full_year` | `RTY_2026_fwd_ret_5m` | 138593/1247337 | 134990/134990 | 0 |
| `liquidity_structure_failed_high_breakout_flag` | `liquidity_structure_failed_high_breakout_flag` | `fver_ce34e72174deddc04934f1dea10df43c947fa490af11d10fc8b0e8628a465ac9` | `lver_a33ae299ed3b794fad79f94a0a906ab858f071e4990c834e530061bc1c1a6f2b` | `RTY_2026_full_year` | `RTY_2026_fwd_ret_5m` | 138593/1247337 | 134990/134990 | 0 |
| `liquidity_structure_failed_low_breakout_flag` | `liquidity_structure_failed_low_breakout_flag` | `fver_a888f15cc75f312e659d7526e238fcc4365395495c2309ef7d23d97eda551c31` | `lver_a33ae299ed3b794fad79f94a0a906ab858f071e4990c834e530061bc1c1a6f2b` | `RTY_2026_full_year` | `RTY_2026_fwd_ret_5m` | 138593/1247337 | 134990/134990 | 0 |
| `liquidity_structure_close_location_value` | `liquidity_structure_close_location_value` | `fver_e646be10b362e36c8c1bc5acf17847d166e8345b8539e30009f1143b7f68c6ea` | `lver_a33ae299ed3b794fad79f94a0a906ab858f071e4990c834e530061bc1c1a6f2b` | `RTY_2026_full_year` | `RTY_2026_fwd_ret_5m` | 138593/1247337 | 134990/134990 | 0 |
| `liquidity_structure_wick_rejection_score` | `liquidity_structure_wick_rejection_score` | `fver_b3bd04fd8f10ece612ca5c3c84a992801571de0d9b27489f78606108893b0905` | `lver_a33ae299ed3b794fad79f94a0a906ab858f071e4990c834e530061bc1c1a6f2b` | `RTY_2026_full_year` | `RTY_2026_fwd_ret_5m` | 138593/1247337 | 134990/134990 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_297f906750679aaf6895be25ef2a88ea7fcfce713894eef62b5403fd34723052` | `lver_a33ae299ed3b794fad79f94a0a906ab858f071e4990c834e530061bc1c1a6f2b` | `RTY_2026_full_year` | `RTY_2026_fwd_ret_5m` | 138593/1247337 | 134990/134990 | 0 |

## excluded_factors

- None.

This report is value-free: it records run counts, seeds, gate outcomes, and the declared threshold only. It contains no label, feature, return, or diagnostic values.

## Threshold

- Declared threshold: zero shuffled runs may clear the shared detection statistic.
- Statistic: `directional.pearson_ic` absolute value against threshold `0.950000`.
- Threshold verdict: `zero-pass-met`.
- Any shuffled statistic pass is `LEAKAGE_BLOCKED` and requires diagnosis before the kill-shot resumes.
- `eligibility_clean` records warning-free diagnostics as context only; it is not the pass criterion.
- Errored runs block calibration success and are not counted as non-passes.
- Bound statement: zero passes in K bounds false-pass rate at about 3/K at 95%.

## Synthetic Calibration Summary

- Run count: 1296
- Error count: 0
- Statistic pass count: 0
- Statistic pass rate: 0.000000
- Eligibility clean count: 1296

## Per-Perturbation Counts

| Perturbation | Runs | Errors | Statistic Passes | Eligibility Clean | Statistic Pass Rate | Verdict |
|---|---:|---:|---:|---:|---:|---|
| trade_date_block_bootstrap | 648 | 0 | 0 | 648 | 0.000000 | zero-pass-met |
| trade_date_block_shuffle | 648 | 0 | 0 | 648 | 0.000000 | zero-pass-met |

## Per-Run Seeds And Outcomes

| StudySpec | Perturbation | Seed | Outcome | Statistic Passed | Eligibility Clean | Surrogate ID | Reason |
|---|---|---:|---|---|---|---|---|
| sspec_826703e0c3bda24ffa0c177a | trade_date_block_shuffle | 9900 | BLOCKED | False | True | surrun_b1d1edabc401d5c856e9b83d | UNDERPOWERED |
| sspec_826703e0c3bda24ffa0c177a | trade_date_block_shuffle | 9901 | BLOCKED | False | True | surrun_1b24369ef0cd6d41925ca277 | UNDERPOWERED |
| sspec_826703e0c3bda24ffa0c177a | trade_date_block_shuffle | 9902 | BLOCKED | False | True | surrun_4ed135ba9ba9965f2d4bca92 | UNDERPOWERED |
| sspec_1b15c2a2daa8a208bff3dd24 | trade_date_block_shuffle | 9903 | BLOCKED | False | True | surrun_21c07d316031a1c8eb390e0e | UNDERPOWERED |
| sspec_1b15c2a2daa8a208bff3dd24 | trade_date_block_shuffle | 9904 | BLOCKED | False | True | surrun_bf9ea1ff4cd387e4440eb0c2 | UNDERPOWERED |
| sspec_1b15c2a2daa8a208bff3dd24 | trade_date_block_shuffle | 9905 | BLOCKED | False | True | surrun_332c9dcbc30ab58f7ab23cb0 | UNDERPOWERED |
| sspec_ccf030f6cedd52ed87a4db2d | trade_date_block_shuffle | 9906 | BLOCKED | False | True | surrun_b3b1b0f971a4bf8d09aca2cb | UNDERPOWERED |
| sspec_ccf030f6cedd52ed87a4db2d | trade_date_block_shuffle | 9907 | BLOCKED | False | True | surrun_f73bd0a442bfe8bf311eed76 | UNDERPOWERED |
| sspec_ccf030f6cedd52ed87a4db2d | trade_date_block_shuffle | 9908 | BLOCKED | False | True | surrun_31a319c93251f5c84f29f934 | UNDERPOWERED |
| sspec_138e2a56ef379a8bec8be7cb | trade_date_block_shuffle | 9909 | BLOCKED | False | True | surrun_091f686e692c8f234fa10aae | UNDERPOWERED |
| sspec_138e2a56ef379a8bec8be7cb | trade_date_block_shuffle | 9910 | BLOCKED | False | True | surrun_eeee0f2d728f4f20260071cf | UNDERPOWERED |
| sspec_138e2a56ef379a8bec8be7cb | trade_date_block_shuffle | 9911 | BLOCKED | False | True | surrun_213d8c0f4f8bce80848f1f48 | UNDERPOWERED |
| sspec_cb3241fb26096e2ad2cec8fe | trade_date_block_shuffle | 9912 | BLOCKED | False | True | surrun_a758dd28e8716b01783e1ca9 | UNDERPOWERED |
| sspec_cb3241fb26096e2ad2cec8fe | trade_date_block_shuffle | 9913 | BLOCKED | False | True | surrun_31f24131ff8b89b2039c7f16 | UNDERPOWERED |
| sspec_cb3241fb26096e2ad2cec8fe | trade_date_block_shuffle | 9914 | BLOCKED | False | True | surrun_70d41ca104a5e3d5511364d1 | UNDERPOWERED |
| sspec_0887c8742e0f50f4f918494d | trade_date_block_shuffle | 9915 | BLOCKED | False | True | surrun_9c827ab588b763b575bcacc4 | UNDERPOWERED |
| sspec_0887c8742e0f50f4f918494d | trade_date_block_shuffle | 9916 | BLOCKED | False | True | surrun_bc3326816b4c832752a9ca0f | UNDERPOWERED |
| sspec_0887c8742e0f50f4f918494d | trade_date_block_shuffle | 9917 | BLOCKED | False | True | surrun_dd259bbf4e8ffb8d1eba945d | UNDERPOWERED |
| sspec_330d88d217a0c0f4db9976f4 | trade_date_block_shuffle | 9918 | BLOCKED | False | True | surrun_687e0e740c2e6c8a2e58125e | UNDERPOWERED |
| sspec_330d88d217a0c0f4db9976f4 | trade_date_block_shuffle | 9919 | BLOCKED | False | True | surrun_87e338eec4e51017710119cc | UNDERPOWERED |
| sspec_330d88d217a0c0f4db9976f4 | trade_date_block_shuffle | 9920 | BLOCKED | False | True | surrun_fb7862e42a53a2624accd21a | UNDERPOWERED |
| sspec_d2e4ee5c838485c30222bb5c | trade_date_block_shuffle | 9921 | BLOCKED | False | True | surrun_3b7ff7279dc103d03a00af6d | UNDERPOWERED |
| sspec_d2e4ee5c838485c30222bb5c | trade_date_block_shuffle | 9922 | BLOCKED | False | True | surrun_3e47a4530e5192fb4aab8588 | UNDERPOWERED |
| sspec_d2e4ee5c838485c30222bb5c | trade_date_block_shuffle | 9923 | BLOCKED | False | True | surrun_fe2679feb0e80bab1bca67b6 | UNDERPOWERED |
| sspec_aac774de749e898e652fa424 | trade_date_block_shuffle | 9924 | BLOCKED | False | True | surrun_ce10c6deca4e5b93c2a5b132 | UNDERPOWERED |
| sspec_aac774de749e898e652fa424 | trade_date_block_shuffle | 9925 | BLOCKED | False | True | surrun_a6109c86bd512154418c0a19 | UNDERPOWERED |
| sspec_aac774de749e898e652fa424 | trade_date_block_shuffle | 9926 | BLOCKED | False | True | surrun_a91961c9f5860c29b97d8bb6 | UNDERPOWERED |
| sspec_5ff81a7fd42832a3991bf64d | trade_date_block_shuffle | 9927 | BLOCKED | False | True | surrun_9ac917535281f5df92999158 | UNDERPOWERED |
| sspec_5ff81a7fd42832a3991bf64d | trade_date_block_shuffle | 9928 | BLOCKED | False | True | surrun_3ad9fbce90d5a8d86796adb0 | UNDERPOWERED |
| sspec_5ff81a7fd42832a3991bf64d | trade_date_block_shuffle | 9929 | BLOCKED | False | True | surrun_82b0a6f9ffcfd1298ac1a7de | UNDERPOWERED |
| sspec_cf8454f7ec91d03c4e931cd5 | trade_date_block_shuffle | 9930 | BLOCKED | False | True | surrun_8217ae6bbcce15f7f330bcdf | UNDERPOWERED |
| sspec_cf8454f7ec91d03c4e931cd5 | trade_date_block_shuffle | 9931 | BLOCKED | False | True | surrun_0a69097c7030ff30f466a10b | UNDERPOWERED |
| sspec_cf8454f7ec91d03c4e931cd5 | trade_date_block_shuffle | 9932 | BLOCKED | False | True | surrun_6185de63ec9de401f702b8ca | UNDERPOWERED |
| sspec_38167f26fc520ba10729e8f7 | trade_date_block_shuffle | 9933 | BLOCKED | False | True | surrun_ef50778258ea58ef7c21b563 | UNDERPOWERED |
| sspec_38167f26fc520ba10729e8f7 | trade_date_block_shuffle | 9934 | BLOCKED | False | True | surrun_1fb5d270e4b93f7bd3db09de | UNDERPOWERED |
| sspec_38167f26fc520ba10729e8f7 | trade_date_block_shuffle | 9935 | BLOCKED | False | True | surrun_9230b939f809081eb2105888 | UNDERPOWERED |
| sspec_099ebb894df1f80527ffbcb9 | trade_date_block_shuffle | 9936 | BLOCKED | False | True | surrun_3414386cec5bb6885d2898d4 | UNDERPOWERED |
| sspec_099ebb894df1f80527ffbcb9 | trade_date_block_shuffle | 9937 | BLOCKED | False | True | surrun_3ee6e6eb63329b3570a09ed3 | UNDERPOWERED |
| sspec_099ebb894df1f80527ffbcb9 | trade_date_block_shuffle | 9938 | BLOCKED | False | True | surrun_206988dcabac17f3da31f389 | UNDERPOWERED |
| sspec_b475d6280235d7e431f7908e | trade_date_block_shuffle | 9939 | BLOCKED | False | True | surrun_f4e98d6769867f90ebe92b5c | UNDERPOWERED |
| sspec_b475d6280235d7e431f7908e | trade_date_block_shuffle | 9940 | BLOCKED | False | True | surrun_472bfdfec40ad5c4056a5096 | UNDERPOWERED |
| sspec_b475d6280235d7e431f7908e | trade_date_block_shuffle | 9941 | BLOCKED | False | True | surrun_f322bf9322ec54b5934ca31f | UNDERPOWERED |
| sspec_58ed6d2a649e5a2778c101cf | trade_date_block_shuffle | 9942 | BLOCKED | False | True | surrun_da918fccb64c4924c5816704 | UNDERPOWERED |
| sspec_58ed6d2a649e5a2778c101cf | trade_date_block_shuffle | 9943 | BLOCKED | False | True | surrun_98b5c2cca1da602da14e8c17 | UNDERPOWERED |
| sspec_58ed6d2a649e5a2778c101cf | trade_date_block_shuffle | 9944 | BLOCKED | False | True | surrun_89947e39d1d1293a18cb6131 | UNDERPOWERED |
| sspec_783f453b3cf5870b49bd71bf | trade_date_block_shuffle | 9945 | BLOCKED | False | True | surrun_5ecc65264bce3e226adff042 | UNDERPOWERED |
| sspec_783f453b3cf5870b49bd71bf | trade_date_block_shuffle | 9946 | BLOCKED | False | True | surrun_adec0dedfdc2475ae1e2a9b7 | UNDERPOWERED |
| sspec_783f453b3cf5870b49bd71bf | trade_date_block_shuffle | 9947 | BLOCKED | False | True | surrun_90b30e6a3d69c7edaf3ccbd5 | UNDERPOWERED |
| sspec_52a1c4e73ce56bd71021970f | trade_date_block_shuffle | 9948 | BLOCKED | False | True | surrun_5a44ee0f070e89f90930d4a2 | UNDERPOWERED |
| sspec_52a1c4e73ce56bd71021970f | trade_date_block_shuffle | 9949 | BLOCKED | False | True | surrun_cd5b99c2b182aa6fb5ea1149 | UNDERPOWERED |
| sspec_52a1c4e73ce56bd71021970f | trade_date_block_shuffle | 9950 | BLOCKED | False | True | surrun_4f9beee335d3008b8a4c615e | UNDERPOWERED |
| sspec_073369f01a3a50aed97e90b6 | trade_date_block_shuffle | 9951 | BLOCKED | False | True | surrun_9b429ab820e3f4ae4d3ca17a | UNDERPOWERED |
| sspec_073369f01a3a50aed97e90b6 | trade_date_block_shuffle | 9952 | BLOCKED | False | True | surrun_3f8303de7313079e6f758761 | UNDERPOWERED |
| sspec_073369f01a3a50aed97e90b6 | trade_date_block_shuffle | 9953 | BLOCKED | False | True | surrun_2231d9a7398b143038dfd542 | UNDERPOWERED |
| sspec_095f278394659374be2e4fb3 | trade_date_block_shuffle | 9954 | BLOCKED | False | True | surrun_7657eb1ec900e0a21a4251c7 | UNDERPOWERED |
| sspec_095f278394659374be2e4fb3 | trade_date_block_shuffle | 9955 | BLOCKED | False | True | surrun_ee94a3a022cddf1be9c0d013 | UNDERPOWERED |
| sspec_095f278394659374be2e4fb3 | trade_date_block_shuffle | 9956 | BLOCKED | False | True | surrun_98cf528d7a0e63ac819b4716 | UNDERPOWERED |
| sspec_beba467d3196bb17ce122be0 | trade_date_block_shuffle | 9957 | BLOCKED | False | True | surrun_8eb43a9c40ed68afb7143dae | UNDERPOWERED |
| sspec_beba467d3196bb17ce122be0 | trade_date_block_shuffle | 9958 | BLOCKED | False | True | surrun_9fd5946c9d8b39e6b24c180c | UNDERPOWERED |
| sspec_beba467d3196bb17ce122be0 | trade_date_block_shuffle | 9959 | BLOCKED | False | True | surrun_581f88996c86523f7a61a2e4 | UNDERPOWERED |
| sspec_68a0eceedbdcad42e563d20f | trade_date_block_shuffle | 9960 | BLOCKED | False | True | surrun_5c07e7678539d753aa883f44 | UNDERPOWERED |
| sspec_68a0eceedbdcad42e563d20f | trade_date_block_shuffle | 9961 | BLOCKED | False | True | surrun_f1033e3871e916b51b7d651c | UNDERPOWERED |
| sspec_68a0eceedbdcad42e563d20f | trade_date_block_shuffle | 9962 | BLOCKED | False | True | surrun_91dcae350d76862918932c42 | UNDERPOWERED |
| sspec_7fabf471b36a6d96810dc349 | trade_date_block_shuffle | 9963 | BLOCKED | False | True | surrun_623e0b5cd677837a94c13959 | UNDERPOWERED |
| sspec_7fabf471b36a6d96810dc349 | trade_date_block_shuffle | 9964 | BLOCKED | False | True | surrun_d845814e5d1a42c10b63a0c8 | UNDERPOWERED |
| sspec_7fabf471b36a6d96810dc349 | trade_date_block_shuffle | 9965 | BLOCKED | False | True | surrun_997e2f2bed5ee1cec81daf4d | UNDERPOWERED |
| sspec_be730f9cb7265d684309eefe | trade_date_block_shuffle | 9966 | BLOCKED | False | True | surrun_56fa488f3d70a59ef4de64f8 | UNDERPOWERED |
| sspec_be730f9cb7265d684309eefe | trade_date_block_shuffle | 9967 | BLOCKED | False | True | surrun_ad6627a95789fac0c9b5929c | UNDERPOWERED |
| sspec_be730f9cb7265d684309eefe | trade_date_block_shuffle | 9968 | BLOCKED | False | True | surrun_1c6af5dd58d982e48273fbca | UNDERPOWERED |
| sspec_a9d77fd7e5ebe47a2da05f30 | trade_date_block_shuffle | 9969 | BLOCKED | False | True | surrun_caf8cd1675a6393496c3d051 | UNDERPOWERED |
| sspec_a9d77fd7e5ebe47a2da05f30 | trade_date_block_shuffle | 9970 | BLOCKED | False | True | surrun_ccbaec062475e00c2d1af94e | UNDERPOWERED |
| sspec_a9d77fd7e5ebe47a2da05f30 | trade_date_block_shuffle | 9971 | BLOCKED | False | True | surrun_13c19fc5fa1857c88235edd8 | UNDERPOWERED |
| sspec_089d8c74665fea93209e2500 | trade_date_block_shuffle | 9972 | BLOCKED | False | True | surrun_f2749507bb4bedbd8b669b58 | UNDERPOWERED |
| sspec_089d8c74665fea93209e2500 | trade_date_block_shuffle | 9973 | BLOCKED | False | True | surrun_8a2b6784a3b36a501d936431 | UNDERPOWERED |
| sspec_089d8c74665fea93209e2500 | trade_date_block_shuffle | 9974 | BLOCKED | False | True | surrun_1a41298321f00f22554e8400 | UNDERPOWERED |
| sspec_b7f454b3f8f6991a16f02a10 | trade_date_block_shuffle | 9975 | BLOCKED | False | True | surrun_a70b376acfecb14288989056 | UNDERPOWERED |
| sspec_b7f454b3f8f6991a16f02a10 | trade_date_block_shuffle | 9976 | BLOCKED | False | True | surrun_bdc6e5d5f6d63c628bf7bcbc | UNDERPOWERED |
| sspec_b7f454b3f8f6991a16f02a10 | trade_date_block_shuffle | 9977 | BLOCKED | False | True | surrun_38f04a8239e3beb4ee9497d1 | UNDERPOWERED |
| sspec_4e64a42331bc4e491fd49dba | trade_date_block_shuffle | 9978 | BLOCKED | False | True | surrun_d98c0b73b37c653d20f530ec | UNDERPOWERED |
| sspec_4e64a42331bc4e491fd49dba | trade_date_block_shuffle | 9979 | BLOCKED | False | True | surrun_0b3f160d2a0f1b08f8f1f73c | UNDERPOWERED |
| sspec_4e64a42331bc4e491fd49dba | trade_date_block_shuffle | 9980 | BLOCKED | False | True | surrun_3d08d77aabb5773077f48239 | UNDERPOWERED |
| sspec_c33679741f62715b8ea90d61 | trade_date_block_shuffle | 9981 | BLOCKED | False | True | surrun_456ff1a96bd75e4a13789ba5 | UNDERPOWERED |
| sspec_c33679741f62715b8ea90d61 | trade_date_block_shuffle | 9982 | BLOCKED | False | True | surrun_daed2cb5c335f7b388fb35ec | UNDERPOWERED |
| sspec_c33679741f62715b8ea90d61 | trade_date_block_shuffle | 9983 | BLOCKED | False | True | surrun_c5eac21b1d1ed3f4d61ed144 | UNDERPOWERED |
| sspec_be4d9db0faa8bdea65bb4c04 | trade_date_block_shuffle | 9984 | BLOCKED | False | True | surrun_bbd8cf395646fa53268266ab | UNDERPOWERED |
| sspec_be4d9db0faa8bdea65bb4c04 | trade_date_block_shuffle | 9985 | BLOCKED | False | True | surrun_af5bc25ea1ea5306ed7ff6b7 | UNDERPOWERED |
| sspec_be4d9db0faa8bdea65bb4c04 | trade_date_block_shuffle | 9986 | BLOCKED | False | True | surrun_2b5fb6d1b628cf6654e9b490 | UNDERPOWERED |
| sspec_a979ab600ef726fee2415b56 | trade_date_block_shuffle | 9987 | BLOCKED | False | True | surrun_aaf80e19fe9cd3d588fafea5 | UNDERPOWERED |
| sspec_a979ab600ef726fee2415b56 | trade_date_block_shuffle | 9988 | BLOCKED | False | True | surrun_a695973c9d901c5bb726e121 | UNDERPOWERED |
| sspec_a979ab600ef726fee2415b56 | trade_date_block_shuffle | 9989 | BLOCKED | False | True | surrun_d8eab0a5ad89ef4fd370cbb2 | UNDERPOWERED |
| sspec_2820bcd83f89967ac47b91b3 | trade_date_block_shuffle | 9990 | BLOCKED | False | True | surrun_c000708c9dcfadf9b265079b | UNDERPOWERED |
| sspec_2820bcd83f89967ac47b91b3 | trade_date_block_shuffle | 9991 | BLOCKED | False | True | surrun_0dc5bc9f36c173afa23097af | UNDERPOWERED |
| sspec_2820bcd83f89967ac47b91b3 | trade_date_block_shuffle | 9992 | BLOCKED | False | True | surrun_79d42512b5d7b2738d7d4315 | UNDERPOWERED |
| sspec_737a02bf0d3784d835a31d55 | trade_date_block_shuffle | 9993 | BLOCKED | False | True | surrun_e735b73bcf50a15af7a736b3 | UNDERPOWERED |
| sspec_737a02bf0d3784d835a31d55 | trade_date_block_shuffle | 9994 | BLOCKED | False | True | surrun_639d9d4a4c7a3826b8b06476 | UNDERPOWERED |
| sspec_737a02bf0d3784d835a31d55 | trade_date_block_shuffle | 9995 | BLOCKED | False | True | surrun_c63a13f961bdd629713eee81 | UNDERPOWERED |
| sspec_ce24fd9629d6adf16d0f1734 | trade_date_block_shuffle | 9996 | BLOCKED | False | True | surrun_b205017bd5ce93bc8fcce2d9 | UNDERPOWERED |
| sspec_ce24fd9629d6adf16d0f1734 | trade_date_block_shuffle | 9997 | BLOCKED | False | True | surrun_aa287afc4065e2ac73103758 | UNDERPOWERED |
| sspec_ce24fd9629d6adf16d0f1734 | trade_date_block_shuffle | 9998 | BLOCKED | False | True | surrun_ddb93b0e95e248a07a49aceb | UNDERPOWERED |
| sspec_4e9c217e855268f3c79361d4 | trade_date_block_shuffle | 9999 | BLOCKED | False | True | surrun_cb45274ea354e6e1a791439c | UNDERPOWERED |
| sspec_4e9c217e855268f3c79361d4 | trade_date_block_shuffle | 10000 | BLOCKED | False | True | surrun_1ceae60ca98db4752aec85a7 | UNDERPOWERED |
| sspec_4e9c217e855268f3c79361d4 | trade_date_block_shuffle | 10001 | BLOCKED | False | True | surrun_0dcf7d6bcea4cbbaca3b8bfd | UNDERPOWERED |
| sspec_a7d7e93a369897385e7bb96a | trade_date_block_shuffle | 10002 | BLOCKED | False | True | surrun_fd6272b45fe6b4f0dc312f2f | UNDERPOWERED |
| sspec_a7d7e93a369897385e7bb96a | trade_date_block_shuffle | 10003 | BLOCKED | False | True | surrun_e7f7910a5ac59b56afbe7e91 | UNDERPOWERED |
| sspec_a7d7e93a369897385e7bb96a | trade_date_block_shuffle | 10004 | BLOCKED | False | True | surrun_2b58f4d8aad409480ae92365 | UNDERPOWERED |
| sspec_f1d1b3c24676a6d708b069eb | trade_date_block_shuffle | 10005 | BLOCKED | False | True | surrun_c71a648e03eb29611f16e86a | UNDERPOWERED |
| sspec_f1d1b3c24676a6d708b069eb | trade_date_block_shuffle | 10006 | BLOCKED | False | True | surrun_5907eb14e4b2932305c1a30d | UNDERPOWERED |
| sspec_f1d1b3c24676a6d708b069eb | trade_date_block_shuffle | 10007 | BLOCKED | False | True | surrun_ca80a57828b7f28623b1a849 | UNDERPOWERED |
| sspec_509da62dbc4657af555ebcf5 | trade_date_block_shuffle | 10008 | BLOCKED | False | True | surrun_f930aec781c026cc5c8ebe47 | UNDERPOWERED |
| sspec_509da62dbc4657af555ebcf5 | trade_date_block_shuffle | 10009 | BLOCKED | False | True | surrun_dcac1fb235ab962bde270eaf | UNDERPOWERED |
| sspec_509da62dbc4657af555ebcf5 | trade_date_block_shuffle | 10010 | BLOCKED | False | True | surrun_cdd11d9b0a63c372ef568350 | UNDERPOWERED |
| sspec_e78f59205bb1982685c0a133 | trade_date_block_shuffle | 10011 | BLOCKED | False | True | surrun_2bbbb04c5036694b983f98ec | UNDERPOWERED |
| sspec_e78f59205bb1982685c0a133 | trade_date_block_shuffle | 10012 | BLOCKED | False | True | surrun_848cfad299766dc1521b041f | UNDERPOWERED |
| sspec_e78f59205bb1982685c0a133 | trade_date_block_shuffle | 10013 | BLOCKED | False | True | surrun_8d0a9ce0249ff959b6bc068c | UNDERPOWERED |
| sspec_b950e2557bf418cb44a2fbf8 | trade_date_block_shuffle | 10014 | BLOCKED | False | True | surrun_ca82f74fe9b93e81c683e23f | UNDERPOWERED |
| sspec_b950e2557bf418cb44a2fbf8 | trade_date_block_shuffle | 10015 | BLOCKED | False | True | surrun_ca0bb611023591c2701dff6f | UNDERPOWERED |
| sspec_b950e2557bf418cb44a2fbf8 | trade_date_block_shuffle | 10016 | BLOCKED | False | True | surrun_6fddda9da61a2b3dddcadfb6 | UNDERPOWERED |
| sspec_97f21f92311d0d20ce745d25 | trade_date_block_shuffle | 10017 | BLOCKED | False | True | surrun_8ee58135c4bc2bcc1a694ae5 | UNDERPOWERED |
| sspec_97f21f92311d0d20ce745d25 | trade_date_block_shuffle | 10018 | BLOCKED | False | True | surrun_18b4e2653830ac11df43443f | UNDERPOWERED |
| sspec_97f21f92311d0d20ce745d25 | trade_date_block_shuffle | 10019 | BLOCKED | False | True | surrun_5793dcaa0bf7024a717223ef | UNDERPOWERED |
| sspec_48ae826bbc46b56a6b9deeef | trade_date_block_shuffle | 10020 | BLOCKED | False | True | surrun_3c04eed047a1d8b543a1970e | UNDERPOWERED |
| sspec_48ae826bbc46b56a6b9deeef | trade_date_block_shuffle | 10021 | BLOCKED | False | True | surrun_ebe68e46829980d89b3dc6ee | UNDERPOWERED |
| sspec_48ae826bbc46b56a6b9deeef | trade_date_block_shuffle | 10022 | BLOCKED | False | True | surrun_934fbf816ab1689c7d70c6ea | UNDERPOWERED |
| sspec_83ff56ac8fd2969f7aaed14f | trade_date_block_shuffle | 10023 | BLOCKED | False | True | surrun_61774d17520c441b8ecc3f38 | UNDERPOWERED |
| sspec_83ff56ac8fd2969f7aaed14f | trade_date_block_shuffle | 10024 | BLOCKED | False | True | surrun_5474b44b9a58691afd82d0c9 | UNDERPOWERED |
| sspec_83ff56ac8fd2969f7aaed14f | trade_date_block_shuffle | 10025 | BLOCKED | False | True | surrun_f9100022780089a4dcb03e23 | UNDERPOWERED |
| sspec_76a140bddd84aad12f1293ae | trade_date_block_shuffle | 10026 | BLOCKED | False | True | surrun_37957abab5d4b89709f5c335 | UNDERPOWERED |
| sspec_76a140bddd84aad12f1293ae | trade_date_block_shuffle | 10027 | BLOCKED | False | True | surrun_658dd1d9cf4321b0f7f417b2 | UNDERPOWERED |
| sspec_76a140bddd84aad12f1293ae | trade_date_block_shuffle | 10028 | BLOCKED | False | True | surrun_9aca0a28f26b1329a035a8ed | UNDERPOWERED |
| sspec_e00515e2e6131b8c5d5af6f9 | trade_date_block_shuffle | 10029 | BLOCKED | False | True | surrun_929499bc8e523cae39199db1 | UNDERPOWERED |
| sspec_e00515e2e6131b8c5d5af6f9 | trade_date_block_shuffle | 10030 | BLOCKED | False | True | surrun_047d8ef0ef921523b7751d2c | UNDERPOWERED |
| sspec_e00515e2e6131b8c5d5af6f9 | trade_date_block_shuffle | 10031 | BLOCKED | False | True | surrun_4801d8ff27bf947e696a7a06 | UNDERPOWERED |
| sspec_2ae821d0eda04ce3988ac24a | trade_date_block_shuffle | 10032 | BLOCKED | False | True | surrun_0d5b46d0ef967fd1bbd9f8a6 | UNDERPOWERED |
| sspec_2ae821d0eda04ce3988ac24a | trade_date_block_shuffle | 10033 | BLOCKED | False | True | surrun_f3d81ccb2b62f021ed8a4390 | UNDERPOWERED |
| sspec_2ae821d0eda04ce3988ac24a | trade_date_block_shuffle | 10034 | BLOCKED | False | True | surrun_9603fe8a3a5bc99cb0ad2ce5 | UNDERPOWERED |
| sspec_89ac002fad22d13a5f7577e1 | trade_date_block_shuffle | 10035 | BLOCKED | False | True | surrun_683da354d9d0d157132ce6ec | UNDERPOWERED |
| sspec_89ac002fad22d13a5f7577e1 | trade_date_block_shuffle | 10036 | BLOCKED | False | True | surrun_b0f1fbbeb090d2acf936a05e | UNDERPOWERED |
| sspec_89ac002fad22d13a5f7577e1 | trade_date_block_shuffle | 10037 | BLOCKED | False | True | surrun_8002847324349ae70b20fdee | UNDERPOWERED |
| sspec_c520510d66bedb107abe0269 | trade_date_block_shuffle | 10038 | BLOCKED | False | True | surrun_13c013032737457ade1ef06b | UNDERPOWERED |
| sspec_c520510d66bedb107abe0269 | trade_date_block_shuffle | 10039 | BLOCKED | False | True | surrun_7e22a05bade821fdcff1ebfd | UNDERPOWERED |
| sspec_c520510d66bedb107abe0269 | trade_date_block_shuffle | 10040 | BLOCKED | False | True | surrun_1c9be6ee3e7770859079a055 | UNDERPOWERED |
| sspec_5e66fbed683802d36cf78c78 | trade_date_block_shuffle | 10041 | BLOCKED | False | True | surrun_7a8713d3c26bdcd2b8c0c78a | UNDERPOWERED |
| sspec_5e66fbed683802d36cf78c78 | trade_date_block_shuffle | 10042 | BLOCKED | False | True | surrun_b01da3eea8f6b9739d86f205 | UNDERPOWERED |
| sspec_5e66fbed683802d36cf78c78 | trade_date_block_shuffle | 10043 | BLOCKED | False | True | surrun_2237077a777f368aa23cde73 | UNDERPOWERED |
| sspec_e9532065e877e419ed00a928 | trade_date_block_shuffle | 10044 | BLOCKED | False | True | surrun_14f56fb49b5850eaea775665 | UNDERPOWERED |
| sspec_e9532065e877e419ed00a928 | trade_date_block_shuffle | 10045 | BLOCKED | False | True | surrun_e35fff9e0bac55ae728a46f1 | UNDERPOWERED |
| sspec_e9532065e877e419ed00a928 | trade_date_block_shuffle | 10046 | BLOCKED | False | True | surrun_6d3f7ca6c7406f9cd91a3891 | UNDERPOWERED |
| sspec_3c5b1c2deac8886df2db6210 | trade_date_block_shuffle | 10047 | BLOCKED | False | True | surrun_6a36f06a83605a667291dc86 | UNDERPOWERED |
| sspec_3c5b1c2deac8886df2db6210 | trade_date_block_shuffle | 10048 | BLOCKED | False | True | surrun_8282c5067937a62f7e61ec22 | UNDERPOWERED |
| sspec_3c5b1c2deac8886df2db6210 | trade_date_block_shuffle | 10049 | BLOCKED | False | True | surrun_f91556cdcf85b8c098dd22b9 | UNDERPOWERED |
| sspec_9a6a2300dfac7e86e3fa1564 | trade_date_block_shuffle | 10050 | BLOCKED | False | True | surrun_89996f6f3e429dc94f8be5ab | UNDERPOWERED |
| sspec_9a6a2300dfac7e86e3fa1564 | trade_date_block_shuffle | 10051 | BLOCKED | False | True | surrun_4d25e582de1e0f1263281fe5 | UNDERPOWERED |
| sspec_9a6a2300dfac7e86e3fa1564 | trade_date_block_shuffle | 10052 | BLOCKED | False | True | surrun_3bc8929e9b52d31ad30cc18b | UNDERPOWERED |
| sspec_e54e46398cd54daf3788cc6e | trade_date_block_shuffle | 10053 | BLOCKED | False | True | surrun_d91eac6bcb51ac96f42b1f5f | UNDERPOWERED |
| sspec_e54e46398cd54daf3788cc6e | trade_date_block_shuffle | 10054 | BLOCKED | False | True | surrun_b2e28041ec6b327d1015bc34 | UNDERPOWERED |
| sspec_e54e46398cd54daf3788cc6e | trade_date_block_shuffle | 10055 | BLOCKED | False | True | surrun_603677fff38d36cac3c3bb3d | UNDERPOWERED |
| sspec_e1dc6dc58114c2b287ae547d | trade_date_block_shuffle | 10056 | BLOCKED | False | True | surrun_85a6dccefd804dca9f04d8fd | UNDERPOWERED |
| sspec_e1dc6dc58114c2b287ae547d | trade_date_block_shuffle | 10057 | BLOCKED | False | True | surrun_c1716521236002cf7ef8913e | UNDERPOWERED |
| sspec_e1dc6dc58114c2b287ae547d | trade_date_block_shuffle | 10058 | BLOCKED | False | True | surrun_d3d679a4faaa2b1a65c4203e | UNDERPOWERED |
| sspec_0c236ef9f77e9191f7b62936 | trade_date_block_shuffle | 10059 | BLOCKED | False | True | surrun_86608ccba45453cc2f46a087 | UNDERPOWERED |
| sspec_0c236ef9f77e9191f7b62936 | trade_date_block_shuffle | 10060 | BLOCKED | False | True | surrun_db462b4e73e09f0db641ed3e | UNDERPOWERED |
| sspec_0c236ef9f77e9191f7b62936 | trade_date_block_shuffle | 10061 | BLOCKED | False | True | surrun_f5fb0a9d3ddff9dd5ded8361 | UNDERPOWERED |
| sspec_05471b51e6fee2b7ca9e875b | trade_date_block_shuffle | 10062 | BLOCKED | False | True | surrun_d5fd7b0cfbdb4b0b0a461541 | UNDERPOWERED |
| sspec_05471b51e6fee2b7ca9e875b | trade_date_block_shuffle | 10063 | BLOCKED | False | True | surrun_8c72674f0915c0c68ae6c595 | UNDERPOWERED |
| sspec_05471b51e6fee2b7ca9e875b | trade_date_block_shuffle | 10064 | BLOCKED | False | True | surrun_dba61d6aa9f62b43d6fab833 | UNDERPOWERED |
| sspec_a08b2b489849bb619c996ae5 | trade_date_block_shuffle | 10065 | BLOCKED | False | True | surrun_bd9a0aa625068fccf0a7b21e | UNDERPOWERED |
| sspec_a08b2b489849bb619c996ae5 | trade_date_block_shuffle | 10066 | BLOCKED | False | True | surrun_2c6649a1ef371947ec1a4f55 | UNDERPOWERED |
| sspec_a08b2b489849bb619c996ae5 | trade_date_block_shuffle | 10067 | BLOCKED | False | True | surrun_a8b6f80279695d126187d650 | UNDERPOWERED |
| sspec_fa24fd829b877dcd7f34f539 | trade_date_block_shuffle | 10068 | BLOCKED | False | True | surrun_44e1894fc38460b547cb5cec | UNDERPOWERED |
| sspec_fa24fd829b877dcd7f34f539 | trade_date_block_shuffle | 10069 | BLOCKED | False | True | surrun_7dc51cc83434e30acf9f0ef9 | UNDERPOWERED |
| sspec_fa24fd829b877dcd7f34f539 | trade_date_block_shuffle | 10070 | BLOCKED | False | True | surrun_5929bcfb5fad95a65c693dfd | UNDERPOWERED |
| sspec_dc72f62576538ccd318a9803 | trade_date_block_shuffle | 10071 | BLOCKED | False | True | surrun_376f67743844f53c6acbfb56 | UNDERPOWERED |
| sspec_dc72f62576538ccd318a9803 | trade_date_block_shuffle | 10072 | BLOCKED | False | True | surrun_535c8ee67447b6fc27f55bde | UNDERPOWERED |
| sspec_dc72f62576538ccd318a9803 | trade_date_block_shuffle | 10073 | BLOCKED | False | True | surrun_44d0b322844bedf76c0ee9a3 | UNDERPOWERED |
| sspec_040153645920514cb66cf13a | trade_date_block_shuffle | 10074 | BLOCKED | False | True | surrun_7f6874af221a2f391b0eecee | UNDERPOWERED |
| sspec_040153645920514cb66cf13a | trade_date_block_shuffle | 10075 | BLOCKED | False | True | surrun_f2356f21387372bd88b503ec | UNDERPOWERED |
| sspec_040153645920514cb66cf13a | trade_date_block_shuffle | 10076 | BLOCKED | False | True | surrun_dfeda82d946dea02ae0ba054 | UNDERPOWERED |
| sspec_c6c25767a92fa953414a1934 | trade_date_block_shuffle | 10077 | BLOCKED | False | True | surrun_ca60f0b1e3e419472664ac92 | UNDERPOWERED |
| sspec_c6c25767a92fa953414a1934 | trade_date_block_shuffle | 10078 | BLOCKED | False | True | surrun_8a56543bd63ed56302b10c32 | UNDERPOWERED |
| sspec_c6c25767a92fa953414a1934 | trade_date_block_shuffle | 10079 | BLOCKED | False | True | surrun_0995c075cf55435fa6570688 | UNDERPOWERED |
| sspec_b9f4feca968f31fd8c1d2000 | trade_date_block_shuffle | 10080 | BLOCKED | False | True | surrun_3e44122e2c6066ece7f20f4e | UNDERPOWERED |
| sspec_b9f4feca968f31fd8c1d2000 | trade_date_block_shuffle | 10081 | BLOCKED | False | True | surrun_f76e77aca69f3c910989e6a7 | UNDERPOWERED |
| sspec_b9f4feca968f31fd8c1d2000 | trade_date_block_shuffle | 10082 | BLOCKED | False | True | surrun_3a937eed3bb9ad5df108d45c | UNDERPOWERED |
| sspec_83a7cd07438b812c800bee51 | trade_date_block_shuffle | 10083 | BLOCKED | False | True | surrun_8b74deb5d17054bc5ab71577 | UNDERPOWERED |
| sspec_83a7cd07438b812c800bee51 | trade_date_block_shuffle | 10084 | BLOCKED | False | True | surrun_2375bf4b01e97428add728bf | UNDERPOWERED |
| sspec_83a7cd07438b812c800bee51 | trade_date_block_shuffle | 10085 | BLOCKED | False | True | surrun_011907dd54211208bcd151ed | UNDERPOWERED |
| sspec_9a21f36d4081e500f653f25f | trade_date_block_shuffle | 10086 | BLOCKED | False | True | surrun_9b69e808ef94a1249815ca74 | UNDERPOWERED |
| sspec_9a21f36d4081e500f653f25f | trade_date_block_shuffle | 10087 | BLOCKED | False | True | surrun_f7cd7591f3311db5ee6fd879 | UNDERPOWERED |
| sspec_9a21f36d4081e500f653f25f | trade_date_block_shuffle | 10088 | BLOCKED | False | True | surrun_125a725ab9ed875fe67371b4 | UNDERPOWERED |
| sspec_990869ad8278a45aa4d7c826 | trade_date_block_shuffle | 10089 | BLOCKED | False | True | surrun_3e6663e071a7282456f5bb5e | UNDERPOWERED |
| sspec_990869ad8278a45aa4d7c826 | trade_date_block_shuffle | 10090 | BLOCKED | False | True | surrun_63e64d7f2279879d96647211 | UNDERPOWERED |
| sspec_990869ad8278a45aa4d7c826 | trade_date_block_shuffle | 10091 | BLOCKED | False | True | surrun_1c5b3028277842912f1656c0 | UNDERPOWERED |
| sspec_d49a2b49acee824065afeecb | trade_date_block_shuffle | 10092 | BLOCKED | False | True | surrun_ab0f12ad40dea757f4552813 | UNDERPOWERED |
| sspec_d49a2b49acee824065afeecb | trade_date_block_shuffle | 10093 | BLOCKED | False | True | surrun_63e3eb0ce45d075564cf68c5 | UNDERPOWERED |
| sspec_d49a2b49acee824065afeecb | trade_date_block_shuffle | 10094 | BLOCKED | False | True | surrun_3d4f983c35dae4cf26c74183 | UNDERPOWERED |
| sspec_9fb5bb6be944583adbbb777c | trade_date_block_shuffle | 10095 | BLOCKED | False | True | surrun_ea11b311430b5ff1cb686dad | UNDERPOWERED |
| sspec_9fb5bb6be944583adbbb777c | trade_date_block_shuffle | 10096 | BLOCKED | False | True | surrun_e89cdc729fca4a3ad5a21364 | UNDERPOWERED |
| sspec_9fb5bb6be944583adbbb777c | trade_date_block_shuffle | 10097 | BLOCKED | False | True | surrun_a893229305a5390f337cfb3a | UNDERPOWERED |
| sspec_b045d3594982c81d1689203e | trade_date_block_shuffle | 10098 | BLOCKED | False | True | surrun_92efefc0bab5bb6b22f24020 | UNDERPOWERED |
| sspec_b045d3594982c81d1689203e | trade_date_block_shuffle | 10099 | BLOCKED | False | True | surrun_5bf1e4f3c27f04ba21e663de | UNDERPOWERED |
| sspec_b045d3594982c81d1689203e | trade_date_block_shuffle | 10100 | BLOCKED | False | True | surrun_cf7300691bf86eb6b8b6ec0d | UNDERPOWERED |
| sspec_9bb382ff9c2c74f51651d599 | trade_date_block_shuffle | 10101 | BLOCKED | False | True | surrun_bfef7994c3e6252a9867d22d | UNDERPOWERED |
| sspec_9bb382ff9c2c74f51651d599 | trade_date_block_shuffle | 10102 | BLOCKED | False | True | surrun_d3d2e1598124f1baa1b0db18 | UNDERPOWERED |
| sspec_9bb382ff9c2c74f51651d599 | trade_date_block_shuffle | 10103 | BLOCKED | False | True | surrun_700ead51e236153746935765 | UNDERPOWERED |
| sspec_280a8dfe4461daecf124ffcd | trade_date_block_shuffle | 10104 | BLOCKED | False | True | surrun_456387b873b66b3e641dfa64 | UNDERPOWERED |
| sspec_280a8dfe4461daecf124ffcd | trade_date_block_shuffle | 10105 | BLOCKED | False | True | surrun_4391c50272c2560101f84c76 | UNDERPOWERED |
| sspec_280a8dfe4461daecf124ffcd | trade_date_block_shuffle | 10106 | BLOCKED | False | True | surrun_a912cf708b94160318110c93 | UNDERPOWERED |
| sspec_7beb2827c66016b2336b5f63 | trade_date_block_shuffle | 10107 | BLOCKED | False | True | surrun_b50099dfa6dd5d03deb7f486 | UNDERPOWERED |
| sspec_7beb2827c66016b2336b5f63 | trade_date_block_shuffle | 10108 | BLOCKED | False | True | surrun_72ff1d1cc7d7e0be62af8fcb | UNDERPOWERED |
| sspec_7beb2827c66016b2336b5f63 | trade_date_block_shuffle | 10109 | BLOCKED | False | True | surrun_d256c608b39d4f2087c0cc46 | UNDERPOWERED |
| sspec_862d44c0d9122cd6d7abaf4d | trade_date_block_shuffle | 10110 | BLOCKED | False | True | surrun_83f0611114ae5044a412f783 | UNDERPOWERED |
| sspec_862d44c0d9122cd6d7abaf4d | trade_date_block_shuffle | 10111 | BLOCKED | False | True | surrun_892d82c590c6a7aee3a2b2e9 | UNDERPOWERED |
| sspec_862d44c0d9122cd6d7abaf4d | trade_date_block_shuffle | 10112 | BLOCKED | False | True | surrun_0c52e0a1d65159d7e1c8d0ae | UNDERPOWERED |
| sspec_6bbdb23561c217d42c38a1fa | trade_date_block_shuffle | 10113 | BLOCKED | False | True | surrun_d778b56f9f817befeccd377c | UNDERPOWERED |
| sspec_6bbdb23561c217d42c38a1fa | trade_date_block_shuffle | 10114 | BLOCKED | False | True | surrun_89923d49b3a16c576af3c3ed | UNDERPOWERED |
| sspec_6bbdb23561c217d42c38a1fa | trade_date_block_shuffle | 10115 | BLOCKED | False | True | surrun_9a6196ab08cdb718052fcbd4 | UNDERPOWERED |
| sspec_755d980617a38be3475eedd2 | trade_date_block_shuffle | 10116 | BLOCKED | False | True | surrun_d0db0ddaefa5b16156724c6c | UNDERPOWERED |
| sspec_755d980617a38be3475eedd2 | trade_date_block_shuffle | 10117 | BLOCKED | False | True | surrun_d89f21d6e596f7cf38c57ca4 | UNDERPOWERED |
| sspec_755d980617a38be3475eedd2 | trade_date_block_shuffle | 10118 | BLOCKED | False | True | surrun_30de461e0232690a18823891 | UNDERPOWERED |
| sspec_97c4afb23a76ecd721df20b3 | trade_date_block_shuffle | 10119 | BLOCKED | False | True | surrun_a4757acf16e8c51e592d3f3e | UNDERPOWERED |
| sspec_97c4afb23a76ecd721df20b3 | trade_date_block_shuffle | 10120 | BLOCKED | False | True | surrun_ee8ce918e7285dc1506840dd | UNDERPOWERED |
| sspec_97c4afb23a76ecd721df20b3 | trade_date_block_shuffle | 10121 | BLOCKED | False | True | surrun_efc969341e710d0e9026350f | UNDERPOWERED |
| sspec_ed61d9465a629f60c3268bda | trade_date_block_shuffle | 10122 | BLOCKED | False | True | surrun_7f177bb1790310565d4b12d0 | UNDERPOWERED |
| sspec_ed61d9465a629f60c3268bda | trade_date_block_shuffle | 10123 | BLOCKED | False | True | surrun_9578be14e1df32933c45d58e | UNDERPOWERED |
| sspec_ed61d9465a629f60c3268bda | trade_date_block_shuffle | 10124 | BLOCKED | False | True | surrun_f293b5b5b626024387961b2f | UNDERPOWERED |
| sspec_7270b20010b09309e6c29317 | trade_date_block_shuffle | 10125 | BLOCKED | False | True | surrun_1b400873a1f4d9668c67e355 | UNDERPOWERED |
| sspec_7270b20010b09309e6c29317 | trade_date_block_shuffle | 10126 | BLOCKED | False | True | surrun_468ef8a38bbe1e765dbc3147 | UNDERPOWERED |
| sspec_7270b20010b09309e6c29317 | trade_date_block_shuffle | 10127 | BLOCKED | False | True | surrun_f0b962e61636efa3e0bd98e2 | UNDERPOWERED |
| sspec_a4913956ea5f67114bee127d | trade_date_block_shuffle | 10128 | BLOCKED | False | True | surrun_ebb6ce40c0b59e52cbcdc0f4 | UNDERPOWERED |
| sspec_a4913956ea5f67114bee127d | trade_date_block_shuffle | 10129 | BLOCKED | False | True | surrun_ac3fa50e476fac373605152f | UNDERPOWERED |
| sspec_a4913956ea5f67114bee127d | trade_date_block_shuffle | 10130 | BLOCKED | False | True | surrun_7ff18184ff0ecc32877b706d | UNDERPOWERED |
| sspec_42c1927fc60742b4c1473f5a | trade_date_block_shuffle | 10131 | BLOCKED | False | True | surrun_ee6b4202ea81fcd2c2909cf3 | UNDERPOWERED |
| sspec_42c1927fc60742b4c1473f5a | trade_date_block_shuffle | 10132 | BLOCKED | False | True | surrun_d207c64be8585920c69760cb | UNDERPOWERED |
| sspec_42c1927fc60742b4c1473f5a | trade_date_block_shuffle | 10133 | BLOCKED | False | True | surrun_92db06139b381d8e47765668 | UNDERPOWERED |
| sspec_9bf1f243048a6c8cf7befc8e | trade_date_block_shuffle | 10134 | BLOCKED | False | True | surrun_a6fb4e286b66e5fbdcc7200f | UNDERPOWERED |
| sspec_9bf1f243048a6c8cf7befc8e | trade_date_block_shuffle | 10135 | BLOCKED | False | True | surrun_237f885af156d7e60600c208 | UNDERPOWERED |
| sspec_9bf1f243048a6c8cf7befc8e | trade_date_block_shuffle | 10136 | BLOCKED | False | True | surrun_95eddc0215cfcdcce92b2359 | UNDERPOWERED |
| sspec_f4c3d55505198d2b5ff2409e | trade_date_block_shuffle | 10137 | BLOCKED | False | True | surrun_96add0db84d6b6cc74b7ef92 | UNDERPOWERED |
| sspec_f4c3d55505198d2b5ff2409e | trade_date_block_shuffle | 10138 | BLOCKED | False | True | surrun_e5f6ac93004646b531f8cbcb | UNDERPOWERED |
| sspec_f4c3d55505198d2b5ff2409e | trade_date_block_shuffle | 10139 | BLOCKED | False | True | surrun_44dae2a3cc80615ccde7f317 | UNDERPOWERED |
| sspec_3916fc01853676ba093c9272 | trade_date_block_shuffle | 10140 | BLOCKED | False | True | surrun_85f0195c1a6ce32ff950e7bc | UNDERPOWERED |
| sspec_3916fc01853676ba093c9272 | trade_date_block_shuffle | 10141 | BLOCKED | False | True | surrun_a26edc2189b04a80ddd3ac5e | UNDERPOWERED |
| sspec_3916fc01853676ba093c9272 | trade_date_block_shuffle | 10142 | BLOCKED | False | True | surrun_f91fef91fe9433f2ef757c1b | UNDERPOWERED |
| sspec_4c978ff1e143f380ebe4552c | trade_date_block_shuffle | 10143 | BLOCKED | False | True | surrun_786d3e65e6604340a989eacd | UNDERPOWERED |
| sspec_4c978ff1e143f380ebe4552c | trade_date_block_shuffle | 10144 | BLOCKED | False | True | surrun_d1f80ccc23c5bc8c08cc2f97 | UNDERPOWERED |
| sspec_4c978ff1e143f380ebe4552c | trade_date_block_shuffle | 10145 | BLOCKED | False | True | surrun_70421535a4f45801b60cd20c | UNDERPOWERED |
| sspec_e543501b83b61576c1866ca8 | trade_date_block_shuffle | 10146 | BLOCKED | False | True | surrun_336c726b2d474d1cb9518338 | UNDERPOWERED |
| sspec_e543501b83b61576c1866ca8 | trade_date_block_shuffle | 10147 | BLOCKED | False | True | surrun_edf17c18d449b3339a21f83d | UNDERPOWERED |
| sspec_e543501b83b61576c1866ca8 | trade_date_block_shuffle | 10148 | BLOCKED | False | True | surrun_2fbca7031c3dbe11a574bc11 | UNDERPOWERED |
| sspec_f6f831a9f002292d241b4c0e | trade_date_block_shuffle | 10149 | BLOCKED | False | True | surrun_19c13a7f254bcb46c881c717 | UNDERPOWERED |
| sspec_f6f831a9f002292d241b4c0e | trade_date_block_shuffle | 10150 | BLOCKED | False | True | surrun_7bff81cad0006f0f6029375f | UNDERPOWERED |
| sspec_f6f831a9f002292d241b4c0e | trade_date_block_shuffle | 10151 | BLOCKED | False | True | surrun_822ea9cfa3831cceeffbbc9c | UNDERPOWERED |
| sspec_aaa7b9fc3c19951d861e461c | trade_date_block_shuffle | 10152 | BLOCKED | False | True | surrun_1ef676ff6e56a878c92e80f5 | UNDERPOWERED |
| sspec_aaa7b9fc3c19951d861e461c | trade_date_block_shuffle | 10153 | BLOCKED | False | True | surrun_b20a399e9830b9df8d1ad040 | UNDERPOWERED |
| sspec_aaa7b9fc3c19951d861e461c | trade_date_block_shuffle | 10154 | BLOCKED | False | True | surrun_ac479b68c40ff3f5e234857f | UNDERPOWERED |
| sspec_734771a045dadd9ae2f1010b | trade_date_block_shuffle | 10155 | BLOCKED | False | True | surrun_3188b302c52f2f7f73fdc1e8 | UNDERPOWERED |
| sspec_734771a045dadd9ae2f1010b | trade_date_block_shuffle | 10156 | BLOCKED | False | True | surrun_157a5cd10dda84eb5c7543f6 | UNDERPOWERED |
| sspec_734771a045dadd9ae2f1010b | trade_date_block_shuffle | 10157 | BLOCKED | False | True | surrun_05d02206e58cb8bcee910199 | UNDERPOWERED |
| sspec_51b0c2d1a1d86d2de8ca8b8f | trade_date_block_shuffle | 10158 | BLOCKED | False | True | surrun_c77217251a04328555bc3ccd | UNDERPOWERED |
| sspec_51b0c2d1a1d86d2de8ca8b8f | trade_date_block_shuffle | 10159 | BLOCKED | False | True | surrun_0debde8763371c05f72077ed | UNDERPOWERED |
| sspec_51b0c2d1a1d86d2de8ca8b8f | trade_date_block_shuffle | 10160 | BLOCKED | False | True | surrun_54f2001ec30fd426ba9cad0d | UNDERPOWERED |
| sspec_868225d43c64c888b0566cc6 | trade_date_block_shuffle | 10161 | BLOCKED | False | True | surrun_973dd7635991af55b82a410e | UNDERPOWERED |
| sspec_868225d43c64c888b0566cc6 | trade_date_block_shuffle | 10162 | BLOCKED | False | True | surrun_f9e35423f8db823aad698a42 | UNDERPOWERED |
| sspec_868225d43c64c888b0566cc6 | trade_date_block_shuffle | 10163 | BLOCKED | False | True | surrun_6d8d0d47c69d61400207201a | UNDERPOWERED |
| sspec_cba016c20e3f88feb3aa65ca | trade_date_block_shuffle | 10164 | BLOCKED | False | True | surrun_ab3f0bd1d3a6ae3d78bb6812 | UNDERPOWERED |
| sspec_cba016c20e3f88feb3aa65ca | trade_date_block_shuffle | 10165 | BLOCKED | False | True | surrun_686414ac8e55273d358bcb66 | UNDERPOWERED |
| sspec_cba016c20e3f88feb3aa65ca | trade_date_block_shuffle | 10166 | BLOCKED | False | True | surrun_aec6159150a56f72d122020a | UNDERPOWERED |
| sspec_ef04ec11958032887aef641c | trade_date_block_shuffle | 10167 | BLOCKED | False | True | surrun_2392275f84414067758500c6 | UNDERPOWERED |
| sspec_ef04ec11958032887aef641c | trade_date_block_shuffle | 10168 | BLOCKED | False | True | surrun_58624305dd58582e7f5ce913 | UNDERPOWERED |
| sspec_ef04ec11958032887aef641c | trade_date_block_shuffle | 10169 | BLOCKED | False | True | surrun_3cc720216fe1d4e0de35e473 | UNDERPOWERED |
| sspec_06f2dfe145bb519416e70ece | trade_date_block_shuffle | 10170 | BLOCKED | False | True | surrun_15cb0d7f67380570049311f4 | UNDERPOWERED |
| sspec_06f2dfe145bb519416e70ece | trade_date_block_shuffle | 10171 | BLOCKED | False | True | surrun_28689f8307f9eb3aaef51764 | UNDERPOWERED |
| sspec_06f2dfe145bb519416e70ece | trade_date_block_shuffle | 10172 | BLOCKED | False | True | surrun_0d672be2f75ad348e0702437 | UNDERPOWERED |
| sspec_8e128caf257a2f37528df25f | trade_date_block_shuffle | 10173 | BLOCKED | False | True | surrun_5cddea13a771ebcf4bf0b812 | UNDERPOWERED |
| sspec_8e128caf257a2f37528df25f | trade_date_block_shuffle | 10174 | BLOCKED | False | True | surrun_a9d8a7ccd17f84552c9298ac | UNDERPOWERED |
| sspec_8e128caf257a2f37528df25f | trade_date_block_shuffle | 10175 | BLOCKED | False | True | surrun_a13c4d9beec0eb0134537680 | UNDERPOWERED |
| sspec_3847376fee593d3e5c339779 | trade_date_block_shuffle | 10176 | BLOCKED | False | True | surrun_9f3fa2894af5a1067443e642 | UNDERPOWERED |
| sspec_3847376fee593d3e5c339779 | trade_date_block_shuffle | 10177 | BLOCKED | False | True | surrun_36fc445cc9a9f1416d67ff2a | UNDERPOWERED |
| sspec_3847376fee593d3e5c339779 | trade_date_block_shuffle | 10178 | BLOCKED | False | True | surrun_5cf3e6a3f3b5e39e6e9f8854 | UNDERPOWERED |
| sspec_72ccb72047e196a033b539ee | trade_date_block_shuffle | 10179 | BLOCKED | False | True | surrun_9dfecc26574492d2e3a8225a | UNDERPOWERED |
| sspec_72ccb72047e196a033b539ee | trade_date_block_shuffle | 10180 | BLOCKED | False | True | surrun_4ccc9c4649c3554e217728c1 | UNDERPOWERED |
| sspec_72ccb72047e196a033b539ee | trade_date_block_shuffle | 10181 | BLOCKED | False | True | surrun_2d0a27b5b0fa1b7cef5bfbbd | UNDERPOWERED |
| sspec_7ad93c904580af339b305b89 | trade_date_block_shuffle | 10182 | BLOCKED | False | True | surrun_fa035c1431a191abca3d5aab | UNDERPOWERED |
| sspec_7ad93c904580af339b305b89 | trade_date_block_shuffle | 10183 | BLOCKED | False | True | surrun_5c669218602499f6b3a5b80d | UNDERPOWERED |
| sspec_7ad93c904580af339b305b89 | trade_date_block_shuffle | 10184 | BLOCKED | False | True | surrun_12f97120757812481af7178c | UNDERPOWERED |
| sspec_660d0400eddcfa0c9ecee620 | trade_date_block_shuffle | 10185 | BLOCKED | False | True | surrun_dacf13b691cab61e0158445c | UNDERPOWERED |
| sspec_660d0400eddcfa0c9ecee620 | trade_date_block_shuffle | 10186 | BLOCKED | False | True | surrun_a7d426bf047789153c8a9e8c | UNDERPOWERED |
| sspec_660d0400eddcfa0c9ecee620 | trade_date_block_shuffle | 10187 | BLOCKED | False | True | surrun_1a93c90925082ff313e2223d | UNDERPOWERED |
| sspec_c14388826d27968e6f2805ea | trade_date_block_shuffle | 10188 | BLOCKED | False | True | surrun_b7edd55c844e07735f689764 | UNDERPOWERED |
| sspec_c14388826d27968e6f2805ea | trade_date_block_shuffle | 10189 | BLOCKED | False | True | surrun_eb8c5b43da1d0902a57e51c1 | UNDERPOWERED |
| sspec_c14388826d27968e6f2805ea | trade_date_block_shuffle | 10190 | BLOCKED | False | True | surrun_e9c4a549f2a4f505541ca23f | UNDERPOWERED |
| sspec_5928c9c877f6b48943be0e18 | trade_date_block_shuffle | 10191 | BLOCKED | False | True | surrun_80d74d5d4c4ce0f7b4043219 | UNDERPOWERED |
| sspec_5928c9c877f6b48943be0e18 | trade_date_block_shuffle | 10192 | BLOCKED | False | True | surrun_9848fe72ea7bc1d1ce174b6d | UNDERPOWERED |
| sspec_5928c9c877f6b48943be0e18 | trade_date_block_shuffle | 10193 | BLOCKED | False | True | surrun_6d9c83864de7ba82b5da4b7a | UNDERPOWERED |
| sspec_341f0539ee4b783cd52a891e | trade_date_block_shuffle | 10194 | BLOCKED | False | True | surrun_3b58bc62fa6f8e59c9ec7b2b | UNDERPOWERED |
| sspec_341f0539ee4b783cd52a891e | trade_date_block_shuffle | 10195 | BLOCKED | False | True | surrun_5957ddcfe9e2a0c7dfebaf42 | UNDERPOWERED |
| sspec_341f0539ee4b783cd52a891e | trade_date_block_shuffle | 10196 | BLOCKED | False | True | surrun_471bfefdc51e38ba4e0b27d4 | UNDERPOWERED |
| sspec_e844231ca55c9c5668d4f1a0 | trade_date_block_shuffle | 10197 | BLOCKED | False | True | surrun_cd5b3b0717254808fe3cb480 | UNDERPOWERED |
| sspec_e844231ca55c9c5668d4f1a0 | trade_date_block_shuffle | 10198 | BLOCKED | False | True | surrun_004f06aed16dd41a8c58de4b | UNDERPOWERED |
| sspec_e844231ca55c9c5668d4f1a0 | trade_date_block_shuffle | 10199 | BLOCKED | False | True | surrun_3996e2514a7df9ba3eef52ec | UNDERPOWERED |
| sspec_5f2d607558658bc4dcca2682 | trade_date_block_shuffle | 10200 | BLOCKED | False | True | surrun_bdc0785f86aaa40bbe620fa5 | UNDERPOWERED |
| sspec_5f2d607558658bc4dcca2682 | trade_date_block_shuffle | 10201 | BLOCKED | False | True | surrun_2aa04454f41ecf9a2a9edef5 | UNDERPOWERED |
| sspec_5f2d607558658bc4dcca2682 | trade_date_block_shuffle | 10202 | BLOCKED | False | True | surrun_8e1dc7d8ba64a8ceffadc498 | UNDERPOWERED |
| sspec_c298bbf82f016129aa6a8d5d | trade_date_block_shuffle | 10203 | BLOCKED | False | True | surrun_f25aa8e848ba30e198dbf931 | UNDERPOWERED |
| sspec_c298bbf82f016129aa6a8d5d | trade_date_block_shuffle | 10204 | BLOCKED | False | True | surrun_5798b76289a75435da28e3da | UNDERPOWERED |
| sspec_c298bbf82f016129aa6a8d5d | trade_date_block_shuffle | 10205 | BLOCKED | False | True | surrun_d31df6e1222751f570a985a0 | UNDERPOWERED |
| sspec_615957e589b327ad9c219a0e | trade_date_block_shuffle | 10206 | BLOCKED | False | True | surrun_41068372a187d9ffb76f37be | UNDERPOWERED |
| sspec_615957e589b327ad9c219a0e | trade_date_block_shuffle | 10207 | BLOCKED | False | True | surrun_efffcce4ae6317405992ca17 | UNDERPOWERED |
| sspec_615957e589b327ad9c219a0e | trade_date_block_shuffle | 10208 | BLOCKED | False | True | surrun_d00f023a83cd2e924006444b | UNDERPOWERED |
| sspec_575988f1b3a222120b8ad483 | trade_date_block_shuffle | 10209 | BLOCKED | False | True | surrun_c8250c7145ee86625146ac68 | UNDERPOWERED |
| sspec_575988f1b3a222120b8ad483 | trade_date_block_shuffle | 10210 | BLOCKED | False | True | surrun_738b03218144af623ea899f9 | UNDERPOWERED |
| sspec_575988f1b3a222120b8ad483 | trade_date_block_shuffle | 10211 | BLOCKED | False | True | surrun_4d0b24579709d4268f7c9bc5 | UNDERPOWERED |
| sspec_c850eb8de037fdd42d6d9bd1 | trade_date_block_shuffle | 10212 | BLOCKED | False | True | surrun_cc0d660888efc84975d85ffc | UNDERPOWERED |
| sspec_c850eb8de037fdd42d6d9bd1 | trade_date_block_shuffle | 10213 | BLOCKED | False | True | surrun_f18bac62b1c0653209bd0b52 | UNDERPOWERED |
| sspec_c850eb8de037fdd42d6d9bd1 | trade_date_block_shuffle | 10214 | BLOCKED | False | True | surrun_de297c57ab88030d0105c211 | UNDERPOWERED |
| sspec_ac8ffcd655f016d13f7639d1 | trade_date_block_shuffle | 10215 | BLOCKED | False | True | surrun_3a483cd6f17834b8a5de5ee6 | UNDERPOWERED |
| sspec_ac8ffcd655f016d13f7639d1 | trade_date_block_shuffle | 10216 | BLOCKED | False | True | surrun_25b2d5673d35e6115baf53ec | UNDERPOWERED |
| sspec_ac8ffcd655f016d13f7639d1 | trade_date_block_shuffle | 10217 | BLOCKED | False | True | surrun_bb96512e9c1f5a128bc7eba7 | UNDERPOWERED |
| sspec_417d40d5149c0952f4d6b237 | trade_date_block_shuffle | 10218 | BLOCKED | False | True | surrun_772c7a517ec145c571bd1799 | UNDERPOWERED |
| sspec_417d40d5149c0952f4d6b237 | trade_date_block_shuffle | 10219 | BLOCKED | False | True | surrun_b1d6dadeabc1f02f3be2ceb8 | UNDERPOWERED |
| sspec_417d40d5149c0952f4d6b237 | trade_date_block_shuffle | 10220 | BLOCKED | False | True | surrun_f84554c607e669a72333104c | UNDERPOWERED |
| sspec_4c04b3d54a8eba6e4eda6442 | trade_date_block_shuffle | 10221 | BLOCKED | False | True | surrun_43bda1b37bc765256260f5c7 | UNDERPOWERED |
| sspec_4c04b3d54a8eba6e4eda6442 | trade_date_block_shuffle | 10222 | BLOCKED | False | True | surrun_ce8c0889a71ef061a2815ad3 | UNDERPOWERED |
| sspec_4c04b3d54a8eba6e4eda6442 | trade_date_block_shuffle | 10223 | BLOCKED | False | True | surrun_d331251987d3ecbea1054041 | UNDERPOWERED |
| sspec_8cfbe34372d380ea293c6180 | trade_date_block_shuffle | 10224 | BLOCKED | False | True | surrun_a942eab61f0759b6bac97ced | UNDERPOWERED |
| sspec_8cfbe34372d380ea293c6180 | trade_date_block_shuffle | 10225 | BLOCKED | False | True | surrun_247a6479b0e49119a86f7064 | UNDERPOWERED |
| sspec_8cfbe34372d380ea293c6180 | trade_date_block_shuffle | 10226 | BLOCKED | False | True | surrun_d6fc2f416d193c446c625dc6 | UNDERPOWERED |
| sspec_33e6978062420536604b589f | trade_date_block_shuffle | 10227 | BLOCKED | False | True | surrun_d0abcfca71695c4b1d5eb5f5 | UNDERPOWERED |
| sspec_33e6978062420536604b589f | trade_date_block_shuffle | 10228 | BLOCKED | False | True | surrun_5d9c10158d4fa96c81a48928 | UNDERPOWERED |
| sspec_33e6978062420536604b589f | trade_date_block_shuffle | 10229 | BLOCKED | False | True | surrun_12a43c7c66cf9f81bda70f4c | UNDERPOWERED |
| sspec_39aa4e0ad7853e043ef650c5 | trade_date_block_shuffle | 10230 | BLOCKED | False | True | surrun_25016b22993c32c68f7a742b | UNDERPOWERED |
| sspec_39aa4e0ad7853e043ef650c5 | trade_date_block_shuffle | 10231 | BLOCKED | False | True | surrun_9db633f04adce63e06f73f51 | UNDERPOWERED |
| sspec_39aa4e0ad7853e043ef650c5 | trade_date_block_shuffle | 10232 | BLOCKED | False | True | surrun_4097361a33a30aca069f933e | UNDERPOWERED |
| sspec_9f2098ad4b76e48651eb98fc | trade_date_block_shuffle | 10233 | BLOCKED | False | True | surrun_8521cc24df7181dc03b37b00 | UNDERPOWERED |
| sspec_9f2098ad4b76e48651eb98fc | trade_date_block_shuffle | 10234 | BLOCKED | False | True | surrun_7437a9e8e2c99804eb483a55 | UNDERPOWERED |
| sspec_9f2098ad4b76e48651eb98fc | trade_date_block_shuffle | 10235 | BLOCKED | False | True | surrun_c20a7f28b225939c5c6907aa | UNDERPOWERED |
| sspec_af6bfd804bff3b2a11043f54 | trade_date_block_shuffle | 10236 | BLOCKED | False | True | surrun_8fc6df2f1eb52245dc12029e | UNDERPOWERED |
| sspec_af6bfd804bff3b2a11043f54 | trade_date_block_shuffle | 10237 | BLOCKED | False | True | surrun_4cc6c647a42c176f7b0858a9 | UNDERPOWERED |
| sspec_af6bfd804bff3b2a11043f54 | trade_date_block_shuffle | 10238 | BLOCKED | False | True | surrun_00a4279a6518990327c4221e | UNDERPOWERED |
| sspec_a593dbc474b2e81188e14a04 | trade_date_block_shuffle | 10239 | BLOCKED | False | True | surrun_22cfe4a9ff43f718ce15a88a | UNDERPOWERED |
| sspec_a593dbc474b2e81188e14a04 | trade_date_block_shuffle | 10240 | BLOCKED | False | True | surrun_2e32eb8aadcf13440a73c0bb | UNDERPOWERED |
| sspec_a593dbc474b2e81188e14a04 | trade_date_block_shuffle | 10241 | BLOCKED | False | True | surrun_f0aff8df69d687737aba36c2 | UNDERPOWERED |
| sspec_420d57a91dacb91c9ad406e1 | trade_date_block_shuffle | 10242 | BLOCKED | False | True | surrun_b495c57aabfd6269e698b28a | UNDERPOWERED |
| sspec_420d57a91dacb91c9ad406e1 | trade_date_block_shuffle | 10243 | BLOCKED | False | True | surrun_11cd7b7a2f8882309b55ffab | UNDERPOWERED |
| sspec_420d57a91dacb91c9ad406e1 | trade_date_block_shuffle | 10244 | BLOCKED | False | True | surrun_7b98647005d787c6d10f7d0f | UNDERPOWERED |
| sspec_0ae0a2c8a5072f41b9586423 | trade_date_block_shuffle | 10245 | BLOCKED | False | True | surrun_922e1c8b70e4aa1cd91e1ccf | UNDERPOWERED |
| sspec_0ae0a2c8a5072f41b9586423 | trade_date_block_shuffle | 10246 | BLOCKED | False | True | surrun_90834486922481580410a3c2 | UNDERPOWERED |
| sspec_0ae0a2c8a5072f41b9586423 | trade_date_block_shuffle | 10247 | BLOCKED | False | True | surrun_15e03a796b5f27ee8479af9e | UNDERPOWERED |
| sspec_5009501499364fe94e7207ea | trade_date_block_shuffle | 10248 | BLOCKED | False | True | surrun_87aac00abf9bd478b7bfdb8f | UNDERPOWERED |
| sspec_5009501499364fe94e7207ea | trade_date_block_shuffle | 10249 | BLOCKED | False | True | surrun_5db16174a84d8a52b7a960ea | UNDERPOWERED |
| sspec_5009501499364fe94e7207ea | trade_date_block_shuffle | 10250 | BLOCKED | False | True | surrun_3672f105e53407f90fc500ed | UNDERPOWERED |
| sspec_b2c643ab396aa79e06278f1b | trade_date_block_shuffle | 10251 | BLOCKED | False | True | surrun_e0ff03dd4beefb8cba315949 | UNDERPOWERED |
| sspec_b2c643ab396aa79e06278f1b | trade_date_block_shuffle | 10252 | BLOCKED | False | True | surrun_7a8e66b2a734618215ff17d2 | UNDERPOWERED |
| sspec_b2c643ab396aa79e06278f1b | trade_date_block_shuffle | 10253 | BLOCKED | False | True | surrun_c26b67cd2ee147f54537dfa1 | UNDERPOWERED |
| sspec_daca54b0be689e1553a605e0 | trade_date_block_shuffle | 10254 | BLOCKED | False | True | surrun_e61d11146f3b9f28861059cb | UNDERPOWERED |
| sspec_daca54b0be689e1553a605e0 | trade_date_block_shuffle | 10255 | BLOCKED | False | True | surrun_ec26468eb2a11e886093e963 | UNDERPOWERED |
| sspec_daca54b0be689e1553a605e0 | trade_date_block_shuffle | 10256 | BLOCKED | False | True | surrun_e6cae5b416923cb36e8d7ba4 | UNDERPOWERED |
| sspec_cd094fc62c80c70ed9be7778 | trade_date_block_shuffle | 10257 | BLOCKED | False | True | surrun_43ac78096247808764084d41 | UNDERPOWERED |
| sspec_cd094fc62c80c70ed9be7778 | trade_date_block_shuffle | 10258 | BLOCKED | False | True | surrun_ce934970620b36cf352b02df | UNDERPOWERED |
| sspec_cd094fc62c80c70ed9be7778 | trade_date_block_shuffle | 10259 | BLOCKED | False | True | surrun_7b88d96617fa726dd0f7844e | UNDERPOWERED |
| sspec_e4de6c01c8194505f5b42faa | trade_date_block_shuffle | 10260 | BLOCKED | False | True | surrun_7309e35421941909315f1fb7 | UNDERPOWERED |
| sspec_e4de6c01c8194505f5b42faa | trade_date_block_shuffle | 10261 | BLOCKED | False | True | surrun_bacc2a7eccce9706d07d2f14 | UNDERPOWERED |
| sspec_e4de6c01c8194505f5b42faa | trade_date_block_shuffle | 10262 | BLOCKED | False | True | surrun_d9982008c49174917e7109ca | UNDERPOWERED |
| sspec_07a3d409ac7142f1af3c95dc | trade_date_block_shuffle | 10263 | BLOCKED | False | True | surrun_e3c0d8e280eebd35a29bbcfa | UNDERPOWERED |
| sspec_07a3d409ac7142f1af3c95dc | trade_date_block_shuffle | 10264 | BLOCKED | False | True | surrun_c4b1c0f273894becef0b6daa | UNDERPOWERED |
| sspec_07a3d409ac7142f1af3c95dc | trade_date_block_shuffle | 10265 | BLOCKED | False | True | surrun_3d20cb14c57db393ddb631d9 | UNDERPOWERED |
| sspec_1d6835a599361698f2b73809 | trade_date_block_shuffle | 10266 | BLOCKED | False | True | surrun_c5b9cfe06b0f34071a950e6e | UNDERPOWERED |
| sspec_1d6835a599361698f2b73809 | trade_date_block_shuffle | 10267 | BLOCKED | False | True | surrun_f5012e5f0efe2a6fc891074a | UNDERPOWERED |
| sspec_1d6835a599361698f2b73809 | trade_date_block_shuffle | 10268 | BLOCKED | False | True | surrun_513bf6535b70eb4ab2503335 | UNDERPOWERED |
| sspec_e79a366792fb3bb2fa9ebe97 | trade_date_block_shuffle | 10269 | BLOCKED | False | True | surrun_b3762df6a0949778183aa2c2 | UNDERPOWERED |
| sspec_e79a366792fb3bb2fa9ebe97 | trade_date_block_shuffle | 10270 | BLOCKED | False | True | surrun_830418eeef0593d41ce465c3 | UNDERPOWERED |
| sspec_e79a366792fb3bb2fa9ebe97 | trade_date_block_shuffle | 10271 | BLOCKED | False | True | surrun_55b5b682524e01def730f76d | UNDERPOWERED |
| sspec_ac0401f29a4f9684119b2910 | trade_date_block_shuffle | 10272 | BLOCKED | False | True | surrun_c516fead07991c1d8057abf3 | UNDERPOWERED |
| sspec_ac0401f29a4f9684119b2910 | trade_date_block_shuffle | 10273 | BLOCKED | False | True | surrun_8044b25aae39b386b9c49a67 | UNDERPOWERED |
| sspec_ac0401f29a4f9684119b2910 | trade_date_block_shuffle | 10274 | BLOCKED | False | True | surrun_f20859b5e611002548130141 | UNDERPOWERED |
| sspec_9facdedd053634452d17f373 | trade_date_block_shuffle | 10275 | BLOCKED | False | True | surrun_be433878c58855b3b6d9bdb5 | UNDERPOWERED |
| sspec_9facdedd053634452d17f373 | trade_date_block_shuffle | 10276 | BLOCKED | False | True | surrun_31782254791bd4c9854b17ab | UNDERPOWERED |
| sspec_9facdedd053634452d17f373 | trade_date_block_shuffle | 10277 | BLOCKED | False | True | surrun_f449493c2f5964daa190b731 | UNDERPOWERED |
| sspec_23341861e5b3b2389b1f1fc4 | trade_date_block_shuffle | 10278 | BLOCKED | False | True | surrun_2426dd3c6d503767ab996014 | UNDERPOWERED |
| sspec_23341861e5b3b2389b1f1fc4 | trade_date_block_shuffle | 10279 | BLOCKED | False | True | surrun_37979c559751d408f14bd5ee | UNDERPOWERED |
| sspec_23341861e5b3b2389b1f1fc4 | trade_date_block_shuffle | 10280 | BLOCKED | False | True | surrun_6dfe91932ffc29f2d1218f3a | UNDERPOWERED |
| sspec_1e0f13d7ec8645f8496d6d84 | trade_date_block_shuffle | 10281 | BLOCKED | False | True | surrun_1b09e238ee1148442e4b63e7 | UNDERPOWERED |
| sspec_1e0f13d7ec8645f8496d6d84 | trade_date_block_shuffle | 10282 | BLOCKED | False | True | surrun_d753b98b954333eaf7d03089 | UNDERPOWERED |
| sspec_1e0f13d7ec8645f8496d6d84 | trade_date_block_shuffle | 10283 | BLOCKED | False | True | surrun_b1d8ede74b3405a167835201 | UNDERPOWERED |
| sspec_591b6b5d749f72821cb96b7e | trade_date_block_shuffle | 10284 | BLOCKED | False | True | surrun_fabf7f30811cb72331c62f41 | UNDERPOWERED |
| sspec_591b6b5d749f72821cb96b7e | trade_date_block_shuffle | 10285 | BLOCKED | False | True | surrun_d0d082d2911eae5a6a3eb8d6 | UNDERPOWERED |
| sspec_591b6b5d749f72821cb96b7e | trade_date_block_shuffle | 10286 | BLOCKED | False | True | surrun_a300d6965d97ab54ecfc695b | UNDERPOWERED |
| sspec_59e66484f4bb184d90bf3898 | trade_date_block_shuffle | 10287 | BLOCKED | False | True | surrun_98efb4a0435a1b09f381567b | UNDERPOWERED |
| sspec_59e66484f4bb184d90bf3898 | trade_date_block_shuffle | 10288 | BLOCKED | False | True | surrun_42090327db92efee3ae7cd3a | UNDERPOWERED |
| sspec_59e66484f4bb184d90bf3898 | trade_date_block_shuffle | 10289 | BLOCKED | False | True | surrun_a097acd7020f94cce6815845 | UNDERPOWERED |
| sspec_d786109ea94d49258684c7e6 | trade_date_block_shuffle | 10290 | BLOCKED | False | True | surrun_5d93867ceb49c193f9c00acd | UNDERPOWERED |
| sspec_d786109ea94d49258684c7e6 | trade_date_block_shuffle | 10291 | BLOCKED | False | True | surrun_6dfc25cf1c644d665dd696b3 | UNDERPOWERED |
| sspec_d786109ea94d49258684c7e6 | trade_date_block_shuffle | 10292 | BLOCKED | False | True | surrun_0bd26aa7376805ed83adddd2 | UNDERPOWERED |
| sspec_bfb335e68a4e1c8420e18daf | trade_date_block_shuffle | 10293 | BLOCKED | False | True | surrun_bfcbfd1f8be1d191c8a7ea5f | UNDERPOWERED |
| sspec_bfb335e68a4e1c8420e18daf | trade_date_block_shuffle | 10294 | BLOCKED | False | True | surrun_26025032da1a9ac1a3a830c3 | UNDERPOWERED |
| sspec_bfb335e68a4e1c8420e18daf | trade_date_block_shuffle | 10295 | BLOCKED | False | True | surrun_ee416313cd32305b8ccac40e | UNDERPOWERED |
| sspec_b9b84430f273e368089a1c68 | trade_date_block_shuffle | 10296 | BLOCKED | False | True | surrun_6122437cb792421420ada42c | UNDERPOWERED |
| sspec_b9b84430f273e368089a1c68 | trade_date_block_shuffle | 10297 | BLOCKED | False | True | surrun_d188ef46e3e6bc5d77fd03f7 | UNDERPOWERED |
| sspec_b9b84430f273e368089a1c68 | trade_date_block_shuffle | 10298 | BLOCKED | False | True | surrun_6a5b22ef0105beef8b7e8b40 | UNDERPOWERED |
| sspec_06b2dafa18a5e2f1bf59857a | trade_date_block_shuffle | 10299 | BLOCKED | False | True | surrun_580cf6954031bb6eb70e3f70 | UNDERPOWERED |
| sspec_06b2dafa18a5e2f1bf59857a | trade_date_block_shuffle | 10300 | BLOCKED | False | True | surrun_bedc8ced1ac936521f2794d1 | UNDERPOWERED |
| sspec_06b2dafa18a5e2f1bf59857a | trade_date_block_shuffle | 10301 | BLOCKED | False | True | surrun_fc44663cdd595114977744f1 | UNDERPOWERED |
| sspec_f51256c420e3f4c5d4efe3cd | trade_date_block_shuffle | 10302 | BLOCKED | False | True | surrun_b1c29842371a144c047760cd | UNDERPOWERED |
| sspec_f51256c420e3f4c5d4efe3cd | trade_date_block_shuffle | 10303 | BLOCKED | False | True | surrun_d5a5f84d8a10b35d2c8c58ea | UNDERPOWERED |
| sspec_f51256c420e3f4c5d4efe3cd | trade_date_block_shuffle | 10304 | BLOCKED | False | True | surrun_8a3bba050a5a5ba3c599e4ae | UNDERPOWERED |
| sspec_04700db185f0c6daad6cb3c2 | trade_date_block_shuffle | 10305 | BLOCKED | False | True | surrun_e59424fe08efa115e3e9b263 | UNDERPOWERED |
| sspec_04700db185f0c6daad6cb3c2 | trade_date_block_shuffle | 10306 | BLOCKED | False | True | surrun_dc25435054a04e83afd1ee38 | UNDERPOWERED |
| sspec_04700db185f0c6daad6cb3c2 | trade_date_block_shuffle | 10307 | BLOCKED | False | True | surrun_572d44f61368902d71deca1c | UNDERPOWERED |
| sspec_a4078255986f31a6098cade6 | trade_date_block_shuffle | 10308 | BLOCKED | False | True | surrun_e36f0a463389a6bf3b9938c4 | UNDERPOWERED |
| sspec_a4078255986f31a6098cade6 | trade_date_block_shuffle | 10309 | BLOCKED | False | True | surrun_b2609ae5d9e085e557c732f3 | UNDERPOWERED |
| sspec_a4078255986f31a6098cade6 | trade_date_block_shuffle | 10310 | BLOCKED | False | True | surrun_2b60f129aef01e697d43265e | UNDERPOWERED |
| sspec_c7d1edcfbe2dc633b7019e51 | trade_date_block_shuffle | 10311 | BLOCKED | False | True | surrun_2dc7b70a58bac5c457d38f94 | UNDERPOWERED |
| sspec_c7d1edcfbe2dc633b7019e51 | trade_date_block_shuffle | 10312 | BLOCKED | False | True | surrun_b56ae67534c2dd0d21772398 | UNDERPOWERED |
| sspec_c7d1edcfbe2dc633b7019e51 | trade_date_block_shuffle | 10313 | BLOCKED | False | True | surrun_071e47b8054fafe01dd3733b | UNDERPOWERED |
| sspec_307dde451cbbad8eec5af21b | trade_date_block_shuffle | 10314 | BLOCKED | False | True | surrun_2bb8a80557434810362b05d8 | UNDERPOWERED |
| sspec_307dde451cbbad8eec5af21b | trade_date_block_shuffle | 10315 | BLOCKED | False | True | surrun_694add3e200a585e6fcfa65b | UNDERPOWERED |
| sspec_307dde451cbbad8eec5af21b | trade_date_block_shuffle | 10316 | BLOCKED | False | True | surrun_fd3931778e7cd4e3469807b1 | UNDERPOWERED |
| sspec_a12d8aa54c9448e28c59dc1a | trade_date_block_shuffle | 10317 | BLOCKED | False | True | surrun_586f97fe46500a7712426038 | UNDERPOWERED |
| sspec_a12d8aa54c9448e28c59dc1a | trade_date_block_shuffle | 10318 | BLOCKED | False | True | surrun_68e768139add11bb3bff54ce | UNDERPOWERED |
| sspec_a12d8aa54c9448e28c59dc1a | trade_date_block_shuffle | 10319 | BLOCKED | False | True | surrun_73523960c5a244c87d3d80b6 | UNDERPOWERED |
| sspec_7193d2d27a54308e250de2c9 | trade_date_block_shuffle | 10320 | BLOCKED | False | True | surrun_05e955cdbbbd78f5ba692752 | UNDERPOWERED |
| sspec_7193d2d27a54308e250de2c9 | trade_date_block_shuffle | 10321 | BLOCKED | False | True | surrun_469267a6cb58eaa891ac081b | UNDERPOWERED |
| sspec_7193d2d27a54308e250de2c9 | trade_date_block_shuffle | 10322 | BLOCKED | False | True | surrun_c24849c1b005a9398cf66e69 | UNDERPOWERED |
| sspec_bd962a893b60363f33d88d25 | trade_date_block_shuffle | 10323 | BLOCKED | False | True | surrun_d6136e50e1145adfa4b3602c | UNDERPOWERED |
| sspec_bd962a893b60363f33d88d25 | trade_date_block_shuffle | 10324 | BLOCKED | False | True | surrun_38f9a478322890136967360b | UNDERPOWERED |
| sspec_bd962a893b60363f33d88d25 | trade_date_block_shuffle | 10325 | BLOCKED | False | True | surrun_e571e40354fc6c355809f825 | UNDERPOWERED |
| sspec_47a1c2aa87504926b01084c7 | trade_date_block_shuffle | 10326 | BLOCKED | False | True | surrun_d5126f8dbc3c42d5e5e9256b | UNDERPOWERED |
| sspec_47a1c2aa87504926b01084c7 | trade_date_block_shuffle | 10327 | BLOCKED | False | True | surrun_f794a3883f43c464f6999334 | UNDERPOWERED |
| sspec_47a1c2aa87504926b01084c7 | trade_date_block_shuffle | 10328 | BLOCKED | False | True | surrun_a880c7e8a9464934129f012a | UNDERPOWERED |
| sspec_64f050bdf662b01329d2c031 | trade_date_block_shuffle | 10329 | BLOCKED | False | True | surrun_8b426f1f95f9596ffc056df6 | UNDERPOWERED |
| sspec_64f050bdf662b01329d2c031 | trade_date_block_shuffle | 10330 | BLOCKED | False | True | surrun_fe056d642b881cd55e546cd3 | UNDERPOWERED |
| sspec_64f050bdf662b01329d2c031 | trade_date_block_shuffle | 10331 | BLOCKED | False | True | surrun_2dc8a381e5955ea367258878 | UNDERPOWERED |
| sspec_12f70e2e5ce5c1257b485c40 | trade_date_block_shuffle | 10332 | BLOCKED | False | True | surrun_cffcc4aea62978cbc2e91ca4 | UNDERPOWERED |
| sspec_12f70e2e5ce5c1257b485c40 | trade_date_block_shuffle | 10333 | BLOCKED | False | True | surrun_32f9ea3bdf09886135ca6f14 | UNDERPOWERED |
| sspec_12f70e2e5ce5c1257b485c40 | trade_date_block_shuffle | 10334 | BLOCKED | False | True | surrun_3eb27821728518c0f080cf0a | UNDERPOWERED |
| sspec_8e3ab2a35800038d67f3a309 | trade_date_block_shuffle | 10335 | BLOCKED | False | True | surrun_2700439f50f5748055ee15de | UNDERPOWERED |
| sspec_8e3ab2a35800038d67f3a309 | trade_date_block_shuffle | 10336 | BLOCKED | False | True | surrun_f26295714dce6c79bfa0820c | UNDERPOWERED |
| sspec_8e3ab2a35800038d67f3a309 | trade_date_block_shuffle | 10337 | BLOCKED | False | True | surrun_6f008a531e5ac3bf96d7f846 | UNDERPOWERED |
| sspec_7ab597d4b06cdfb3eff89b47 | trade_date_block_shuffle | 10338 | BLOCKED | False | True | surrun_74b0c20338e9b227bc86f096 | UNDERPOWERED |
| sspec_7ab597d4b06cdfb3eff89b47 | trade_date_block_shuffle | 10339 | BLOCKED | False | True | surrun_49efd69903974b757074bc95 | UNDERPOWERED |
| sspec_7ab597d4b06cdfb3eff89b47 | trade_date_block_shuffle | 10340 | BLOCKED | False | True | surrun_6f15f89c39a52fca18cd7d9a | UNDERPOWERED |
| sspec_2e6d829119d863c0ea676fad | trade_date_block_shuffle | 10341 | BLOCKED | False | True | surrun_8a362fb84423116e70c56fd7 | UNDERPOWERED |
| sspec_2e6d829119d863c0ea676fad | trade_date_block_shuffle | 10342 | BLOCKED | False | True | surrun_87fac4f7c68d7de7476d8d0f | UNDERPOWERED |
| sspec_2e6d829119d863c0ea676fad | trade_date_block_shuffle | 10343 | BLOCKED | False | True | surrun_dd692eff6c059f146562489d | UNDERPOWERED |
| sspec_2fdc71ed9e0d2f4c54fadb7f | trade_date_block_shuffle | 10344 | BLOCKED | False | True | surrun_5ec40bc860ff7fa37bda9b4a | UNDERPOWERED |
| sspec_2fdc71ed9e0d2f4c54fadb7f | trade_date_block_shuffle | 10345 | BLOCKED | False | True | surrun_eaeabf16df9c1e95aa3257d5 | UNDERPOWERED |
| sspec_2fdc71ed9e0d2f4c54fadb7f | trade_date_block_shuffle | 10346 | BLOCKED | False | True | surrun_e91ede304088b37e4ca3d784 | UNDERPOWERED |
| sspec_26a958b1758bf3ba7740286a | trade_date_block_shuffle | 10347 | BLOCKED | False | True | surrun_60b90efee833af592f170803 | UNDERPOWERED |
| sspec_26a958b1758bf3ba7740286a | trade_date_block_shuffle | 10348 | BLOCKED | False | True | surrun_1bb8a21840a935de57da5ca1 | UNDERPOWERED |
| sspec_26a958b1758bf3ba7740286a | trade_date_block_shuffle | 10349 | BLOCKED | False | True | surrun_4d2f86c3341b55371306c3ef | UNDERPOWERED |
| sspec_6a674d0b92a02a4da79178da | trade_date_block_shuffle | 10350 | BLOCKED | False | True | surrun_483e67679e6d27727b0cf062 | UNDERPOWERED |
| sspec_6a674d0b92a02a4da79178da | trade_date_block_shuffle | 10351 | BLOCKED | False | True | surrun_2f98bd73b966216dc6d8c872 | UNDERPOWERED |
| sspec_6a674d0b92a02a4da79178da | trade_date_block_shuffle | 10352 | BLOCKED | False | True | surrun_43fc55002d8086003e45b375 | UNDERPOWERED |
| sspec_02d4c2d8fd2c64493f2cfcf1 | trade_date_block_shuffle | 10353 | BLOCKED | False | True | surrun_c3c7201006e6961c14a1b50d | UNDERPOWERED |
| sspec_02d4c2d8fd2c64493f2cfcf1 | trade_date_block_shuffle | 10354 | BLOCKED | False | True | surrun_7a7ddddc6332952c9aba2a99 | UNDERPOWERED |
| sspec_02d4c2d8fd2c64493f2cfcf1 | trade_date_block_shuffle | 10355 | BLOCKED | False | True | surrun_3f6d67b94b47894e61da1e3f | UNDERPOWERED |
| sspec_d0ae270919495c98929455ab | trade_date_block_shuffle | 10356 | BLOCKED | False | True | surrun_b0ed4ce8d4b155c61d5b4661 | UNDERPOWERED |
| sspec_d0ae270919495c98929455ab | trade_date_block_shuffle | 10357 | BLOCKED | False | True | surrun_e1e3da06e310893b11352387 | UNDERPOWERED |
| sspec_d0ae270919495c98929455ab | trade_date_block_shuffle | 10358 | BLOCKED | False | True | surrun_c0af878be789c99428aca069 | UNDERPOWERED |
| sspec_4ec8fddb8af0145752fc7ca3 | trade_date_block_shuffle | 10359 | BLOCKED | False | True | surrun_7f00b344d0944d980a1b9bee | UNDERPOWERED |
| sspec_4ec8fddb8af0145752fc7ca3 | trade_date_block_shuffle | 10360 | BLOCKED | False | True | surrun_371ae2b7c6dfda77f6d1ed64 | UNDERPOWERED |
| sspec_4ec8fddb8af0145752fc7ca3 | trade_date_block_shuffle | 10361 | BLOCKED | False | True | surrun_bdb6c670a95f9df02472a023 | UNDERPOWERED |
| sspec_009090848943c0de95a47341 | trade_date_block_shuffle | 10362 | BLOCKED | False | True | surrun_8d6ca14c85038bef9a1cece4 | UNDERPOWERED |
| sspec_009090848943c0de95a47341 | trade_date_block_shuffle | 10363 | BLOCKED | False | True | surrun_280762ae0e1ff32c8cb6123d | UNDERPOWERED |
| sspec_009090848943c0de95a47341 | trade_date_block_shuffle | 10364 | BLOCKED | False | True | surrun_8d1d66d52666fa1ce7ca5c36 | UNDERPOWERED |
| sspec_5e4046c2eb6f28e0f5371613 | trade_date_block_shuffle | 10365 | BLOCKED | False | True | surrun_7bcf18b61c63c06bf5df8da3 | UNDERPOWERED |
| sspec_5e4046c2eb6f28e0f5371613 | trade_date_block_shuffle | 10366 | BLOCKED | False | True | surrun_0df34bb96f79ffd38c3a8b2c | UNDERPOWERED |
| sspec_5e4046c2eb6f28e0f5371613 | trade_date_block_shuffle | 10367 | BLOCKED | False | True | surrun_4c93d46316df816c32b6a54a | UNDERPOWERED |
| sspec_f218192064c3697829ae5ae7 | trade_date_block_shuffle | 10368 | BLOCKED | False | True | surrun_811d4439d46ba61c48d42d7c | UNDERPOWERED |
| sspec_f218192064c3697829ae5ae7 | trade_date_block_shuffle | 10369 | BLOCKED | False | True | surrun_2f60e7e58bb6d007977f2ed1 | UNDERPOWERED |
| sspec_f218192064c3697829ae5ae7 | trade_date_block_shuffle | 10370 | BLOCKED | False | True | surrun_911aaaf437395ac412e741a8 | UNDERPOWERED |
| sspec_e3a5a2018e3b6e5bbc811569 | trade_date_block_shuffle | 10371 | BLOCKED | False | True | surrun_baa8faaa9b005fabe2c8f62b | UNDERPOWERED |
| sspec_e3a5a2018e3b6e5bbc811569 | trade_date_block_shuffle | 10372 | BLOCKED | False | True | surrun_edd9e29ff6950563122e9506 | UNDERPOWERED |
| sspec_e3a5a2018e3b6e5bbc811569 | trade_date_block_shuffle | 10373 | BLOCKED | False | True | surrun_e1c7db774717ecdc8b3486d8 | UNDERPOWERED |
| sspec_5ce1327071aea3730850cc90 | trade_date_block_shuffle | 10374 | BLOCKED | False | True | surrun_46347ce435b1075a11f2f7f7 | UNDERPOWERED |
| sspec_5ce1327071aea3730850cc90 | trade_date_block_shuffle | 10375 | BLOCKED | False | True | surrun_ab294a2f6495a5f0841fe6ce | UNDERPOWERED |
| sspec_5ce1327071aea3730850cc90 | trade_date_block_shuffle | 10376 | BLOCKED | False | True | surrun_d5fa0d769e9cc301c7763063 | UNDERPOWERED |
| sspec_cb2f0cb548f47610400c0246 | trade_date_block_shuffle | 10377 | BLOCKED | False | True | surrun_aaf9e4b81ccf445274b45299 | UNDERPOWERED |
| sspec_cb2f0cb548f47610400c0246 | trade_date_block_shuffle | 10378 | BLOCKED | False | True | surrun_813849e9c615410e32a6362d | UNDERPOWERED |
| sspec_cb2f0cb548f47610400c0246 | trade_date_block_shuffle | 10379 | BLOCKED | False | True | surrun_76e68486046ca7765428cf5e | UNDERPOWERED |
| sspec_60255b9607d91b315fa18998 | trade_date_block_shuffle | 10380 | BLOCKED | False | True | surrun_5d2c8c185eeb48e8e9a454a9 | UNDERPOWERED |
| sspec_60255b9607d91b315fa18998 | trade_date_block_shuffle | 10381 | BLOCKED | False | True | surrun_d90a0a0cd81be554c99c6ded | UNDERPOWERED |
| sspec_60255b9607d91b315fa18998 | trade_date_block_shuffle | 10382 | BLOCKED | False | True | surrun_b04986ff8eec6b82041c4c90 | UNDERPOWERED |
| sspec_b90e5b137dbdc9cd50f11b6f | trade_date_block_shuffle | 10383 | BLOCKED | False | True | surrun_33653a21e84d09c52066f1d3 | UNDERPOWERED |
| sspec_b90e5b137dbdc9cd50f11b6f | trade_date_block_shuffle | 10384 | BLOCKED | False | True | surrun_22217deeba09e445a87c9f35 | UNDERPOWERED |
| sspec_b90e5b137dbdc9cd50f11b6f | trade_date_block_shuffle | 10385 | BLOCKED | False | True | surrun_d8490d45f1ec122db163ff0e | UNDERPOWERED |
| sspec_f93cebb5da9ea1917e9bd437 | trade_date_block_shuffle | 10386 | BLOCKED | False | True | surrun_647fc9c26e9e4fa6d346a36a | UNDERPOWERED |
| sspec_f93cebb5da9ea1917e9bd437 | trade_date_block_shuffle | 10387 | BLOCKED | False | True | surrun_c3b20e856263e6376a1a02d7 | UNDERPOWERED |
| sspec_f93cebb5da9ea1917e9bd437 | trade_date_block_shuffle | 10388 | BLOCKED | False | True | surrun_b047646ee83f7e5e66e0d74f | UNDERPOWERED |
| sspec_1312fb9e82b3a2c651d7aab6 | trade_date_block_shuffle | 10389 | BLOCKED | False | True | surrun_f1ddfd5a4338108291ecca21 | UNDERPOWERED |
| sspec_1312fb9e82b3a2c651d7aab6 | trade_date_block_shuffle | 10390 | BLOCKED | False | True | surrun_38c5e7cf5a5c154233734bc8 | UNDERPOWERED |
| sspec_1312fb9e82b3a2c651d7aab6 | trade_date_block_shuffle | 10391 | BLOCKED | False | True | surrun_f4328020f1635c64322057ac | UNDERPOWERED |
| sspec_e6eb9f2669d4c44c0b917529 | trade_date_block_shuffle | 10392 | BLOCKED | False | True | surrun_3c142562468df7bb2035ab4d | UNDERPOWERED |
| sspec_e6eb9f2669d4c44c0b917529 | trade_date_block_shuffle | 10393 | BLOCKED | False | True | surrun_7d114d7125733368d930f0b9 | UNDERPOWERED |
| sspec_e6eb9f2669d4c44c0b917529 | trade_date_block_shuffle | 10394 | BLOCKED | False | True | surrun_facc69678af95135e2900748 | UNDERPOWERED |
| sspec_72abd692a99dd3745248b741 | trade_date_block_shuffle | 10395 | BLOCKED | False | True | surrun_0762b1e1d97e4fafc779d1f4 | UNDERPOWERED |
| sspec_72abd692a99dd3745248b741 | trade_date_block_shuffle | 10396 | BLOCKED | False | True | surrun_1a9f4a66c078d43793b38037 | UNDERPOWERED |
| sspec_72abd692a99dd3745248b741 | trade_date_block_shuffle | 10397 | BLOCKED | False | True | surrun_ef31f59953369b90fa87dc76 | UNDERPOWERED |
| sspec_00627f348df014c2af1ba8bb | trade_date_block_shuffle | 10398 | BLOCKED | False | True | surrun_fc9d38cdc7c57775c2d43491 | UNDERPOWERED |
| sspec_00627f348df014c2af1ba8bb | trade_date_block_shuffle | 10399 | BLOCKED | False | True | surrun_3b190e519eb195960a56d43d | UNDERPOWERED |
| sspec_00627f348df014c2af1ba8bb | trade_date_block_shuffle | 10400 | BLOCKED | False | True | surrun_0373f5ffd15a46983711c97f | UNDERPOWERED |
| sspec_9ab3b0dabedc16e1d1665eae | trade_date_block_shuffle | 10401 | BLOCKED | False | True | surrun_949f6d94af9b7a71a61f6a35 | UNDERPOWERED |
| sspec_9ab3b0dabedc16e1d1665eae | trade_date_block_shuffle | 10402 | BLOCKED | False | True | surrun_5c7c07055d97adafd7fa9dd0 | UNDERPOWERED |
| sspec_9ab3b0dabedc16e1d1665eae | trade_date_block_shuffle | 10403 | BLOCKED | False | True | surrun_971af3ba2feb610aa464a34a | UNDERPOWERED |
| sspec_0970761026880cf10ffb959e | trade_date_block_shuffle | 10404 | BLOCKED | False | True | surrun_b4d4c1bc5ee9e5eb9d38f6f8 | UNDERPOWERED |
| sspec_0970761026880cf10ffb959e | trade_date_block_shuffle | 10405 | BLOCKED | False | True | surrun_f14ae1e2bf304a9d4a20e43f | UNDERPOWERED |
| sspec_0970761026880cf10ffb959e | trade_date_block_shuffle | 10406 | BLOCKED | False | True | surrun_eda6f7135b69d80d9ec1581a | UNDERPOWERED |
| sspec_2960375e303e1437425b86e1 | trade_date_block_shuffle | 10407 | BLOCKED | False | True | surrun_579749f77296da86871c3149 | UNDERPOWERED |
| sspec_2960375e303e1437425b86e1 | trade_date_block_shuffle | 10408 | BLOCKED | False | True | surrun_82147853009a967664a47e08 | UNDERPOWERED |
| sspec_2960375e303e1437425b86e1 | trade_date_block_shuffle | 10409 | BLOCKED | False | True | surrun_8d3915afb4c129de2bbeff64 | UNDERPOWERED |
| sspec_06748cbab50a85b355c5a62b | trade_date_block_shuffle | 10410 | BLOCKED | False | True | surrun_2098c035a8fb0aa533aad27b | UNDERPOWERED |
| sspec_06748cbab50a85b355c5a62b | trade_date_block_shuffle | 10411 | BLOCKED | False | True | surrun_e3b4f2f713729033aa73abf5 | UNDERPOWERED |
| sspec_06748cbab50a85b355c5a62b | trade_date_block_shuffle | 10412 | BLOCKED | False | True | surrun_36d0a0c16c64f6fe8ef676e1 | UNDERPOWERED |
| sspec_d6d2c7ca067491cf6ff5fe1a | trade_date_block_shuffle | 10413 | BLOCKED | False | True | surrun_2790070cceae3293c9377f31 | UNDERPOWERED |
| sspec_d6d2c7ca067491cf6ff5fe1a | trade_date_block_shuffle | 10414 | BLOCKED | False | True | surrun_b443ac44cf7478ba97c746b5 | UNDERPOWERED |
| sspec_d6d2c7ca067491cf6ff5fe1a | trade_date_block_shuffle | 10415 | BLOCKED | False | True | surrun_886ed47821b1010f45487658 | UNDERPOWERED |
| sspec_fe20b5938195485f7c61bdd3 | trade_date_block_shuffle | 10416 | BLOCKED | False | True | surrun_ed049a6b1494dfbf8480667d | UNDERPOWERED |
| sspec_fe20b5938195485f7c61bdd3 | trade_date_block_shuffle | 10417 | BLOCKED | False | True | surrun_ef12c0006190d8c9a335bee4 | UNDERPOWERED |
| sspec_fe20b5938195485f7c61bdd3 | trade_date_block_shuffle | 10418 | BLOCKED | False | True | surrun_7742e12c955fc5f4cd6ae271 | UNDERPOWERED |
| sspec_a3d0e453d45a113ed040690d | trade_date_block_shuffle | 10419 | BLOCKED | False | True | surrun_7503452289ff6c4b79bd85ea | UNDERPOWERED |
| sspec_a3d0e453d45a113ed040690d | trade_date_block_shuffle | 10420 | BLOCKED | False | True | surrun_acc27c1cd6166e6e436aca1c | UNDERPOWERED |
| sspec_a3d0e453d45a113ed040690d | trade_date_block_shuffle | 10421 | BLOCKED | False | True | surrun_92cc06f70a69e9fb851cfa08 | UNDERPOWERED |
| sspec_79de468011b2905b326c7583 | trade_date_block_shuffle | 10422 | BLOCKED | False | True | surrun_caadd8671fd072f9a376d537 | UNDERPOWERED |
| sspec_79de468011b2905b326c7583 | trade_date_block_shuffle | 10423 | BLOCKED | False | True | surrun_19d6c58d1decadc49c0459d2 | UNDERPOWERED |
| sspec_79de468011b2905b326c7583 | trade_date_block_shuffle | 10424 | BLOCKED | False | True | surrun_b0cd914ea76d111bb4511486 | UNDERPOWERED |
| sspec_827ce07b25d95a62679fea13 | trade_date_block_shuffle | 10425 | BLOCKED | False | True | surrun_831c922fdf2d8db5b01df580 | UNDERPOWERED |
| sspec_827ce07b25d95a62679fea13 | trade_date_block_shuffle | 10426 | BLOCKED | False | True | surrun_d67fcab0a8e0229b7c85a1fb | UNDERPOWERED |
| sspec_827ce07b25d95a62679fea13 | trade_date_block_shuffle | 10427 | BLOCKED | False | True | surrun_b693151ecf3a0f97745877f0 | UNDERPOWERED |
| sspec_0af6d7c90cc243f35b395d07 | trade_date_block_shuffle | 10428 | BLOCKED | False | True | surrun_d4dc08099e6b0d82ab10be65 | UNDERPOWERED |
| sspec_0af6d7c90cc243f35b395d07 | trade_date_block_shuffle | 10429 | BLOCKED | False | True | surrun_7c7d0b83e368a5fb1f5e90b0 | UNDERPOWERED |
| sspec_0af6d7c90cc243f35b395d07 | trade_date_block_shuffle | 10430 | BLOCKED | False | True | surrun_5ef7a8a19729424cacd616d4 | UNDERPOWERED |
| sspec_8996fc26a21e74fd750567f4 | trade_date_block_shuffle | 10431 | BLOCKED | False | True | surrun_1f067e0291b41d67275f71c9 | UNDERPOWERED |
| sspec_8996fc26a21e74fd750567f4 | trade_date_block_shuffle | 10432 | BLOCKED | False | True | surrun_6cbe32816f1d1421a217aff4 | UNDERPOWERED |
| sspec_8996fc26a21e74fd750567f4 | trade_date_block_shuffle | 10433 | BLOCKED | False | True | surrun_45c54f5bed379546f6e96cb0 | UNDERPOWERED |
| sspec_4366258cb4ecd00e9c35fd4c | trade_date_block_shuffle | 10434 | BLOCKED | False | True | surrun_01ed63255c1c16db847f7b7c | UNDERPOWERED |
| sspec_4366258cb4ecd00e9c35fd4c | trade_date_block_shuffle | 10435 | BLOCKED | False | True | surrun_52352fd1276554e91881c7ff | UNDERPOWERED |
| sspec_4366258cb4ecd00e9c35fd4c | trade_date_block_shuffle | 10436 | BLOCKED | False | True | surrun_0aacaea66fb31abdfb6e265e | UNDERPOWERED |
| sspec_639bdfb95714fb09e2ed4d6b | trade_date_block_shuffle | 10437 | BLOCKED | False | True | surrun_5b4b53553a8372641b8e38d5 | UNDERPOWERED |
| sspec_639bdfb95714fb09e2ed4d6b | trade_date_block_shuffle | 10438 | BLOCKED | False | True | surrun_c45b9660ee4580212bad44ce | UNDERPOWERED |
| sspec_639bdfb95714fb09e2ed4d6b | trade_date_block_shuffle | 10439 | BLOCKED | False | True | surrun_fc8b41171aa3e7a9bc9ef130 | UNDERPOWERED |
| sspec_a78da21d358b646ce861e42e | trade_date_block_shuffle | 10440 | BLOCKED | False | True | surrun_0b7ee421e71d625b080b2d29 | UNDERPOWERED |
| sspec_a78da21d358b646ce861e42e | trade_date_block_shuffle | 10441 | BLOCKED | False | True | surrun_2aa108e16647015969ffa7ae | UNDERPOWERED |
| sspec_a78da21d358b646ce861e42e | trade_date_block_shuffle | 10442 | BLOCKED | False | True | surrun_2170d1647edfe7353bed1e48 | UNDERPOWERED |
| sspec_16cc672b15138b0ddfc82b65 | trade_date_block_shuffle | 10443 | BLOCKED | False | True | surrun_e78b997b2c35b725d305d1a1 | UNDERPOWERED |
| sspec_16cc672b15138b0ddfc82b65 | trade_date_block_shuffle | 10444 | BLOCKED | False | True | surrun_7970f77df81770b1e2f7b038 | UNDERPOWERED |
| sspec_16cc672b15138b0ddfc82b65 | trade_date_block_shuffle | 10445 | BLOCKED | False | True | surrun_613a8cf24a8919b7d2eb1228 | UNDERPOWERED |
| sspec_8e899c10d0e54a0096d9b8a9 | trade_date_block_shuffle | 10446 | BLOCKED | False | True | surrun_0091484baaf5cd0a0b97debe | UNDERPOWERED |
| sspec_8e899c10d0e54a0096d9b8a9 | trade_date_block_shuffle | 10447 | BLOCKED | False | True | surrun_0b404b68712b5799048dce43 | UNDERPOWERED |
| sspec_8e899c10d0e54a0096d9b8a9 | trade_date_block_shuffle | 10448 | BLOCKED | False | True | surrun_1ff35a1c98468b5e6cac0ea0 | UNDERPOWERED |
| sspec_b57116d359e6ab5127347d1e | trade_date_block_shuffle | 10449 | BLOCKED | False | True | surrun_b0af5a196db8731f9fecbefa | UNDERPOWERED |
| sspec_b57116d359e6ab5127347d1e | trade_date_block_shuffle | 10450 | BLOCKED | False | True | surrun_8fa54e1a1c7aee854324c184 | UNDERPOWERED |
| sspec_b57116d359e6ab5127347d1e | trade_date_block_shuffle | 10451 | BLOCKED | False | True | surrun_0656f73da210a9ac585ec1c2 | UNDERPOWERED |
| sspec_95b6778754f0fdbce91e7612 | trade_date_block_shuffle | 10452 | BLOCKED | False | True | surrun_3cbbee746fc1ff642b5577a6 | UNDERPOWERED |
| sspec_95b6778754f0fdbce91e7612 | trade_date_block_shuffle | 10453 | BLOCKED | False | True | surrun_60a2cefd502f9b257a6e9c2a | UNDERPOWERED |
| sspec_95b6778754f0fdbce91e7612 | trade_date_block_shuffle | 10454 | BLOCKED | False | True | surrun_0cefca34e3d75097b2345f84 | UNDERPOWERED |
| sspec_65871ccbf1b720b9adea6f02 | trade_date_block_shuffle | 10455 | BLOCKED | False | True | surrun_2c6eeacda258ae4e0dbacf14 | UNDERPOWERED |
| sspec_65871ccbf1b720b9adea6f02 | trade_date_block_shuffle | 10456 | BLOCKED | False | True | surrun_07c89c5bd3533acc6c4e60e2 | UNDERPOWERED |
| sspec_65871ccbf1b720b9adea6f02 | trade_date_block_shuffle | 10457 | BLOCKED | False | True | surrun_2f98f80e1ae021231cf30c8f | UNDERPOWERED |
| sspec_038ec2aae72d221d1a4b978e | trade_date_block_shuffle | 10458 | BLOCKED | False | True | surrun_e368b3a3a39c062ce01c5421 | UNDERPOWERED |
| sspec_038ec2aae72d221d1a4b978e | trade_date_block_shuffle | 10459 | BLOCKED | False | True | surrun_d4bcaca5d2ef5b44b9c07d1a | UNDERPOWERED |
| sspec_038ec2aae72d221d1a4b978e | trade_date_block_shuffle | 10460 | BLOCKED | False | True | surrun_9f84684401de517a906e79d5 | UNDERPOWERED |
| sspec_51427d9e9e56b14b1e2bd340 | trade_date_block_shuffle | 10461 | BLOCKED | False | True | surrun_a615d4c0722d3a5d4af06d1a | UNDERPOWERED |
| sspec_51427d9e9e56b14b1e2bd340 | trade_date_block_shuffle | 10462 | BLOCKED | False | True | surrun_77d831f034dfbb859d325c0f | UNDERPOWERED |
| sspec_51427d9e9e56b14b1e2bd340 | trade_date_block_shuffle | 10463 | BLOCKED | False | True | surrun_9c3848d52a02b9fb31295d66 | UNDERPOWERED |
| sspec_e3553e20303b2066d4b291c3 | trade_date_block_shuffle | 10464 | BLOCKED | False | True | surrun_7d2aeb17e6fccab4096679f6 | UNDERPOWERED |
| sspec_e3553e20303b2066d4b291c3 | trade_date_block_shuffle | 10465 | BLOCKED | False | True | surrun_f68fa29fca6e5645fd5136a2 | UNDERPOWERED |
| sspec_e3553e20303b2066d4b291c3 | trade_date_block_shuffle | 10466 | BLOCKED | False | True | surrun_a5ccb20b89d24ef1d3b8373d | UNDERPOWERED |
| sspec_11e48e92c22b6c92b5269508 | trade_date_block_shuffle | 10467 | BLOCKED | False | True | surrun_516b1ccb3419262ffa45a4f7 | UNDERPOWERED |
| sspec_11e48e92c22b6c92b5269508 | trade_date_block_shuffle | 10468 | BLOCKED | False | True | surrun_414b87dc8202d000d919338c | UNDERPOWERED |
| sspec_11e48e92c22b6c92b5269508 | trade_date_block_shuffle | 10469 | BLOCKED | False | True | surrun_1b82ef0e9b49d883e8643208 | UNDERPOWERED |
| sspec_552a07f2154c04e2049e189a | trade_date_block_shuffle | 10470 | BLOCKED | False | True | surrun_b476bb9067e4307a353ace89 | UNDERPOWERED |
| sspec_552a07f2154c04e2049e189a | trade_date_block_shuffle | 10471 | BLOCKED | False | True | surrun_8dd95f5dbb5fe186d5ff07df | UNDERPOWERED |
| sspec_552a07f2154c04e2049e189a | trade_date_block_shuffle | 10472 | BLOCKED | False | True | surrun_dff5337e61cf7abbe8046565 | UNDERPOWERED |
| sspec_7a07ad20f277d529a78e14d8 | trade_date_block_shuffle | 10473 | BLOCKED | False | True | surrun_aae1a30d80a8cb5ba185e79c | UNDERPOWERED |
| sspec_7a07ad20f277d529a78e14d8 | trade_date_block_shuffle | 10474 | BLOCKED | False | True | surrun_d89965f3590dff31af431057 | UNDERPOWERED |
| sspec_7a07ad20f277d529a78e14d8 | trade_date_block_shuffle | 10475 | BLOCKED | False | True | surrun_2b4ab6cd331155d6e8e68478 | UNDERPOWERED |
| sspec_60b3f72735a53d7fa5cc9020 | trade_date_block_shuffle | 10476 | BLOCKED | False | True | surrun_74e0ec538a61995de53d6039 | UNDERPOWERED |
| sspec_60b3f72735a53d7fa5cc9020 | trade_date_block_shuffle | 10477 | BLOCKED | False | True | surrun_00f0392f58264cbcae5ca837 | UNDERPOWERED |
| sspec_60b3f72735a53d7fa5cc9020 | trade_date_block_shuffle | 10478 | BLOCKED | False | True | surrun_9a2454eccbfd281110df6cc8 | UNDERPOWERED |
| sspec_8eaaaf1f4d25df4c7c3c811a | trade_date_block_shuffle | 10479 | BLOCKED | False | True | surrun_ff364f165f05d9497e88d7fb | UNDERPOWERED |
| sspec_8eaaaf1f4d25df4c7c3c811a | trade_date_block_shuffle | 10480 | BLOCKED | False | True | surrun_a8589755775812db88605954 | UNDERPOWERED |
| sspec_8eaaaf1f4d25df4c7c3c811a | trade_date_block_shuffle | 10481 | BLOCKED | False | True | surrun_ed48e0f12123b2f1901cc19d | UNDERPOWERED |
| sspec_a37e8e165dbd5de0eb5157ae | trade_date_block_shuffle | 10482 | BLOCKED | False | True | surrun_e36f17d00d4030e9b2da8cb0 | UNDERPOWERED |
| sspec_a37e8e165dbd5de0eb5157ae | trade_date_block_shuffle | 10483 | BLOCKED | False | True | surrun_948046aeddb91c47cefe14b9 | UNDERPOWERED |
| sspec_a37e8e165dbd5de0eb5157ae | trade_date_block_shuffle | 10484 | BLOCKED | False | True | surrun_25ffa47985a877c4486594b4 | UNDERPOWERED |
| sspec_bcc42ab9f3cd42d0104c4c95 | trade_date_block_shuffle | 10485 | BLOCKED | False | True | surrun_0b3a681170c3c8e7644c18b0 | UNDERPOWERED |
| sspec_bcc42ab9f3cd42d0104c4c95 | trade_date_block_shuffle | 10486 | BLOCKED | False | True | surrun_6234312355d34d3f5a4467a5 | UNDERPOWERED |
| sspec_bcc42ab9f3cd42d0104c4c95 | trade_date_block_shuffle | 10487 | BLOCKED | False | True | surrun_765abbdbff42bf5d0fecaf35 | UNDERPOWERED |
| sspec_c45cd85d0a99bca875f57f32 | trade_date_block_shuffle | 10488 | BLOCKED | False | True | surrun_a9e5feb56fa6f27036052801 | UNDERPOWERED |
| sspec_c45cd85d0a99bca875f57f32 | trade_date_block_shuffle | 10489 | BLOCKED | False | True | surrun_0b8706cc1cefb9acc935ff4f | UNDERPOWERED |
| sspec_c45cd85d0a99bca875f57f32 | trade_date_block_shuffle | 10490 | BLOCKED | False | True | surrun_00e452e31ea2c87b61bda241 | UNDERPOWERED |
| sspec_f260a67e6c160427683ad1d0 | trade_date_block_shuffle | 10491 | BLOCKED | False | True | surrun_c89ba50d9940c62c91507fd3 | UNDERPOWERED |
| sspec_f260a67e6c160427683ad1d0 | trade_date_block_shuffle | 10492 | BLOCKED | False | True | surrun_ce36f2f9de726a4a3cb0e63a | UNDERPOWERED |
| sspec_f260a67e6c160427683ad1d0 | trade_date_block_shuffle | 10493 | BLOCKED | False | True | surrun_d88250c7aa3ba901e136d1bd | UNDERPOWERED |
| sspec_37c7f6459057a9045ac9035e | trade_date_block_shuffle | 10494 | BLOCKED | False | True | surrun_62e667b8f522c545551a375a | UNDERPOWERED |
| sspec_37c7f6459057a9045ac9035e | trade_date_block_shuffle | 10495 | BLOCKED | False | True | surrun_f61f935c716cf49a6d09cf31 | UNDERPOWERED |
| sspec_37c7f6459057a9045ac9035e | trade_date_block_shuffle | 10496 | BLOCKED | False | True | surrun_0e9c4e48893cbc22059bfb0c | UNDERPOWERED |
| sspec_d2aeac8ec5d9bf87bb716b74 | trade_date_block_shuffle | 10497 | BLOCKED | False | True | surrun_74d55dcb82eea059c74eb149 | UNDERPOWERED |
| sspec_d2aeac8ec5d9bf87bb716b74 | trade_date_block_shuffle | 10498 | BLOCKED | False | True | surrun_39b6d145aa09c3d92e65e96e | UNDERPOWERED |
| sspec_d2aeac8ec5d9bf87bb716b74 | trade_date_block_shuffle | 10499 | BLOCKED | False | True | surrun_996a395d8e4b1bc3e692f89a | UNDERPOWERED |
| sspec_448496edfe67a7da2ed3b399 | trade_date_block_shuffle | 10500 | BLOCKED | False | True | surrun_f0a53929759114c7e1e4e62b | UNDERPOWERED |
| sspec_448496edfe67a7da2ed3b399 | trade_date_block_shuffle | 10501 | BLOCKED | False | True | surrun_a2afcc9d4fc8d4aac51ff62f | UNDERPOWERED |
| sspec_448496edfe67a7da2ed3b399 | trade_date_block_shuffle | 10502 | BLOCKED | False | True | surrun_00b6d9b45abcb924a21bb15b | UNDERPOWERED |
| sspec_6701b69418a43a53c84f8e3a | trade_date_block_shuffle | 10503 | BLOCKED | False | True | surrun_b077dab4b9a0453a8496f2a3 | UNDERPOWERED |
| sspec_6701b69418a43a53c84f8e3a | trade_date_block_shuffle | 10504 | BLOCKED | False | True | surrun_79cc3b89911be6328efdbfe6 | UNDERPOWERED |
| sspec_6701b69418a43a53c84f8e3a | trade_date_block_shuffle | 10505 | BLOCKED | False | True | surrun_bd0e4aed7ff2a324ae24b95b | UNDERPOWERED |
| sspec_b171816beb62a09b0d49f611 | trade_date_block_shuffle | 10506 | BLOCKED | False | True | surrun_c7b60242f44e23a9b7d6f227 | UNDERPOWERED |
| sspec_b171816beb62a09b0d49f611 | trade_date_block_shuffle | 10507 | BLOCKED | False | True | surrun_176bfbd26d03cdb6ffd0c5fb | UNDERPOWERED |
| sspec_b171816beb62a09b0d49f611 | trade_date_block_shuffle | 10508 | BLOCKED | False | True | surrun_8c04c3bdc501ae235990f0a1 | UNDERPOWERED |
| sspec_4d0cfac3ea2558d66fbd4e99 | trade_date_block_shuffle | 10509 | BLOCKED | False | True | surrun_8fb7f3ed378fde14b8c36540 | UNDERPOWERED |
| sspec_4d0cfac3ea2558d66fbd4e99 | trade_date_block_shuffle | 10510 | BLOCKED | False | True | surrun_dc108bc855fb43e1141d39d0 | UNDERPOWERED |
| sspec_4d0cfac3ea2558d66fbd4e99 | trade_date_block_shuffle | 10511 | BLOCKED | False | True | surrun_09efb4ab9be2e505cb661d51 | UNDERPOWERED |
| sspec_30195e4c44d85efc01457875 | trade_date_block_shuffle | 10512 | BLOCKED | False | True | surrun_ffa8b8c5a35f4e25056c6512 | UNDERPOWERED |
| sspec_30195e4c44d85efc01457875 | trade_date_block_shuffle | 10513 | BLOCKED | False | True | surrun_a6c33c35de6ee3943a58c0cd | UNDERPOWERED |
| sspec_30195e4c44d85efc01457875 | trade_date_block_shuffle | 10514 | BLOCKED | False | True | surrun_0cdf75f2e3dd4e63874479e8 | UNDERPOWERED |
| sspec_a205568209c2fcabcafd503b | trade_date_block_shuffle | 10515 | BLOCKED | False | True | surrun_da4a852608827e2b83ed4820 | UNDERPOWERED |
| sspec_a205568209c2fcabcafd503b | trade_date_block_shuffle | 10516 | BLOCKED | False | True | surrun_4ba9498b39efff948ecbfef2 | UNDERPOWERED |
| sspec_a205568209c2fcabcafd503b | trade_date_block_shuffle | 10517 | BLOCKED | False | True | surrun_73d98b73460ffd1c765cf80f | UNDERPOWERED |
| sspec_dd5dcc912cf4431f08c6278d | trade_date_block_shuffle | 10518 | BLOCKED | False | True | surrun_cd2b9ef2b9ed29097ecfe9e2 | UNDERPOWERED |
| sspec_dd5dcc912cf4431f08c6278d | trade_date_block_shuffle | 10519 | BLOCKED | False | True | surrun_fdd429c986734d83ecb02443 | UNDERPOWERED |
| sspec_dd5dcc912cf4431f08c6278d | trade_date_block_shuffle | 10520 | BLOCKED | False | True | surrun_ff69796c8e9e3ba10b667ae5 | UNDERPOWERED |
| sspec_c4f83d7236bfb8c23cc81c4e | trade_date_block_shuffle | 10521 | BLOCKED | False | True | surrun_b07d3aef1010e61e23d4f72c | UNDERPOWERED |
| sspec_c4f83d7236bfb8c23cc81c4e | trade_date_block_shuffle | 10522 | BLOCKED | False | True | surrun_aef80603b6d35e776dfbd1ab | UNDERPOWERED |
| sspec_c4f83d7236bfb8c23cc81c4e | trade_date_block_shuffle | 10523 | BLOCKED | False | True | surrun_6ff7deea14733341773bc7e7 | UNDERPOWERED |
| sspec_359b3427cab6452abc9e95df | trade_date_block_shuffle | 10524 | BLOCKED | False | True | surrun_aa3061947dc587dc23df4383 | UNDERPOWERED |
| sspec_359b3427cab6452abc9e95df | trade_date_block_shuffle | 10525 | BLOCKED | False | True | surrun_a2fe5893e3f015f10d1558fb | UNDERPOWERED |
| sspec_359b3427cab6452abc9e95df | trade_date_block_shuffle | 10526 | BLOCKED | False | True | surrun_0508eb21b63d7ed2490574a9 | UNDERPOWERED |
| sspec_512658d7802ea840d5a6a683 | trade_date_block_shuffle | 10527 | BLOCKED | False | True | surrun_dab41911aab5701497db9eb9 | UNDERPOWERED |
| sspec_512658d7802ea840d5a6a683 | trade_date_block_shuffle | 10528 | BLOCKED | False | True | surrun_4327c57dc98b00e55dd56ced | UNDERPOWERED |
| sspec_512658d7802ea840d5a6a683 | trade_date_block_shuffle | 10529 | BLOCKED | False | True | surrun_a242f3259bc31ae3ef0fa7b1 | UNDERPOWERED |
| sspec_a87cad813815f7514f2e41b8 | trade_date_block_shuffle | 10530 | BLOCKED | False | True | surrun_b7d770b6b00b2a60164c39ad | UNDERPOWERED |
| sspec_a87cad813815f7514f2e41b8 | trade_date_block_shuffle | 10531 | BLOCKED | False | True | surrun_76e3ae0ce367da679db45555 | UNDERPOWERED |
| sspec_a87cad813815f7514f2e41b8 | trade_date_block_shuffle | 10532 | BLOCKED | False | True | surrun_98aef5578080ebd1427f8af8 | UNDERPOWERED |
| sspec_17c44a30fdadd35e3b669bdb | trade_date_block_shuffle | 10533 | BLOCKED | False | True | surrun_f25e4d24a28e6653b9359aca | UNDERPOWERED |
| sspec_17c44a30fdadd35e3b669bdb | trade_date_block_shuffle | 10534 | BLOCKED | False | True | surrun_840e042297a82d848b3ec622 | UNDERPOWERED |
| sspec_17c44a30fdadd35e3b669bdb | trade_date_block_shuffle | 10535 | BLOCKED | False | True | surrun_3f7f1530a354336a18a683c2 | UNDERPOWERED |
| sspec_f136b38bd075254fb0cd5179 | trade_date_block_shuffle | 10536 | BLOCKED | False | True | surrun_d495b4888ee0eff883e5a935 | UNDERPOWERED |
| sspec_f136b38bd075254fb0cd5179 | trade_date_block_shuffle | 10537 | BLOCKED | False | True | surrun_4d2ff30cb6fc9fea9dd76d29 | UNDERPOWERED |
| sspec_f136b38bd075254fb0cd5179 | trade_date_block_shuffle | 10538 | BLOCKED | False | True | surrun_f181abc1ae48b042ebbb3225 | UNDERPOWERED |
| sspec_7a5fa340986da0095166a261 | trade_date_block_shuffle | 10539 | BLOCKED | False | True | surrun_e88490f69f348bf3f1cf513a | UNDERPOWERED |
| sspec_7a5fa340986da0095166a261 | trade_date_block_shuffle | 10540 | BLOCKED | False | True | surrun_0b4808caadf5587dcf473854 | UNDERPOWERED |
| sspec_7a5fa340986da0095166a261 | trade_date_block_shuffle | 10541 | BLOCKED | False | True | surrun_27fc2328613ad8dacbf55b75 | UNDERPOWERED |
| sspec_88d5a298d593652e8b9f6f0c | trade_date_block_shuffle | 10542 | BLOCKED | False | True | surrun_1fbafc30ca4bbee6ce00a526 | UNDERPOWERED |
| sspec_88d5a298d593652e8b9f6f0c | trade_date_block_shuffle | 10543 | BLOCKED | False | True | surrun_d9bc581866b4545f2a684daa | UNDERPOWERED |
| sspec_88d5a298d593652e8b9f6f0c | trade_date_block_shuffle | 10544 | BLOCKED | False | True | surrun_13a080c5ac6f8462f4fe0598 | UNDERPOWERED |
| sspec_5a1ecd95d4a899bbc9c11bb7 | trade_date_block_shuffle | 10545 | BLOCKED | False | True | surrun_7708c5ea7b736c5857714d63 | UNDERPOWERED |
| sspec_5a1ecd95d4a899bbc9c11bb7 | trade_date_block_shuffle | 10546 | BLOCKED | False | True | surrun_db8f4741dec860e1ab9ab87f | UNDERPOWERED |
| sspec_5a1ecd95d4a899bbc9c11bb7 | trade_date_block_shuffle | 10547 | BLOCKED | False | True | surrun_c8b86640415c167317858d2e | UNDERPOWERED |
| sspec_826703e0c3bda24ffa0c177a | trade_date_block_bootstrap | 10548 | BLOCKED | False | True | surrun_e857fc917301c74432dcf8b9 | UNDERPOWERED |
| sspec_826703e0c3bda24ffa0c177a | trade_date_block_bootstrap | 10549 | BLOCKED | False | True | surrun_2a2b46914ea5c02c7bd4f67a | UNDERPOWERED |
| sspec_826703e0c3bda24ffa0c177a | trade_date_block_bootstrap | 10550 | BLOCKED | False | True | surrun_1be482c0d27cfc66edbcaac9 | UNDERPOWERED |
| sspec_1b15c2a2daa8a208bff3dd24 | trade_date_block_bootstrap | 10551 | BLOCKED | False | True | surrun_596d45188b1e107abbf47131 | UNDERPOWERED |
| sspec_1b15c2a2daa8a208bff3dd24 | trade_date_block_bootstrap | 10552 | BLOCKED | False | True | surrun_8a5012985d05543ad53d3545 | UNDERPOWERED |
| sspec_1b15c2a2daa8a208bff3dd24 | trade_date_block_bootstrap | 10553 | BLOCKED | False | True | surrun_db84ae09368bf63865abb5e9 | UNDERPOWERED |
| sspec_ccf030f6cedd52ed87a4db2d | trade_date_block_bootstrap | 10554 | BLOCKED | False | True | surrun_56215eec5db29cea358c9880 | UNDERPOWERED |
| sspec_ccf030f6cedd52ed87a4db2d | trade_date_block_bootstrap | 10555 | BLOCKED | False | True | surrun_c6c25e151f617844b69c4b32 | UNDERPOWERED |
| sspec_ccf030f6cedd52ed87a4db2d | trade_date_block_bootstrap | 10556 | BLOCKED | False | True | surrun_25eab8446414e81dd5267548 | UNDERPOWERED |
| sspec_138e2a56ef379a8bec8be7cb | trade_date_block_bootstrap | 10557 | BLOCKED | False | True | surrun_c4610de1599f75f7916df69f | UNDERPOWERED |
| sspec_138e2a56ef379a8bec8be7cb | trade_date_block_bootstrap | 10558 | BLOCKED | False | True | surrun_60652fa3b20fa311b8e591a6 | UNDERPOWERED |
| sspec_138e2a56ef379a8bec8be7cb | trade_date_block_bootstrap | 10559 | BLOCKED | False | True | surrun_81c804b148a8439c5ed8230e | UNDERPOWERED |
| sspec_cb3241fb26096e2ad2cec8fe | trade_date_block_bootstrap | 10560 | BLOCKED | False | True | surrun_5b20c530419a2a03e8e785d7 | UNDERPOWERED |
| sspec_cb3241fb26096e2ad2cec8fe | trade_date_block_bootstrap | 10561 | BLOCKED | False | True | surrun_e49a0657937d0ba419fb6789 | UNDERPOWERED |
| sspec_cb3241fb26096e2ad2cec8fe | trade_date_block_bootstrap | 10562 | BLOCKED | False | True | surrun_ed076aeef137f799315e4339 | UNDERPOWERED |
| sspec_0887c8742e0f50f4f918494d | trade_date_block_bootstrap | 10563 | BLOCKED | False | True | surrun_5357242d145d0e10db5e82fc | UNDERPOWERED |
| sspec_0887c8742e0f50f4f918494d | trade_date_block_bootstrap | 10564 | BLOCKED | False | True | surrun_a3fc9fb211b78b571a30e710 | UNDERPOWERED |
| sspec_0887c8742e0f50f4f918494d | trade_date_block_bootstrap | 10565 | BLOCKED | False | True | surrun_e9ddf7af69b258974eacbd1c | UNDERPOWERED |
| sspec_330d88d217a0c0f4db9976f4 | trade_date_block_bootstrap | 10566 | BLOCKED | False | True | surrun_3b1857aeadcb6539f122dfaf | UNDERPOWERED |
| sspec_330d88d217a0c0f4db9976f4 | trade_date_block_bootstrap | 10567 | BLOCKED | False | True | surrun_59de6dd0d83b616a3feeb288 | UNDERPOWERED |
| sspec_330d88d217a0c0f4db9976f4 | trade_date_block_bootstrap | 10568 | BLOCKED | False | True | surrun_01725a2a24141a7650680141 | UNDERPOWERED |
| sspec_d2e4ee5c838485c30222bb5c | trade_date_block_bootstrap | 10569 | BLOCKED | False | True | surrun_b3d8dc48f375f152eed23878 | UNDERPOWERED |
| sspec_d2e4ee5c838485c30222bb5c | trade_date_block_bootstrap | 10570 | BLOCKED | False | True | surrun_337fdfdc179d202751ba0032 | UNDERPOWERED |
| sspec_d2e4ee5c838485c30222bb5c | trade_date_block_bootstrap | 10571 | BLOCKED | False | True | surrun_7deb4f77e39085bb564f392f | UNDERPOWERED |
| sspec_aac774de749e898e652fa424 | trade_date_block_bootstrap | 10572 | BLOCKED | False | True | surrun_31086a4a59844b52c9c3145e | UNDERPOWERED |
| sspec_aac774de749e898e652fa424 | trade_date_block_bootstrap | 10573 | BLOCKED | False | True | surrun_7aa60800c4d2f0f91cb0e1c5 | UNDERPOWERED |
| sspec_aac774de749e898e652fa424 | trade_date_block_bootstrap | 10574 | BLOCKED | False | True | surrun_cb6302aef84d3e33b87109ef | UNDERPOWERED |
| sspec_5ff81a7fd42832a3991bf64d | trade_date_block_bootstrap | 10575 | BLOCKED | False | True | surrun_6005e3b9f6981e268da41532 | UNDERPOWERED |
| sspec_5ff81a7fd42832a3991bf64d | trade_date_block_bootstrap | 10576 | BLOCKED | False | True | surrun_d4e11c6abd6dd4b86ddd280f | UNDERPOWERED |
| sspec_5ff81a7fd42832a3991bf64d | trade_date_block_bootstrap | 10577 | BLOCKED | False | True | surrun_e13deb6bbae03cae826fe8ff | UNDERPOWERED |
| sspec_cf8454f7ec91d03c4e931cd5 | trade_date_block_bootstrap | 10578 | BLOCKED | False | True | surrun_36d4248e413038f02b4ff783 | UNDERPOWERED |
| sspec_cf8454f7ec91d03c4e931cd5 | trade_date_block_bootstrap | 10579 | BLOCKED | False | True | surrun_233b61515ec6bcbd77f3b7ab | UNDERPOWERED |
| sspec_cf8454f7ec91d03c4e931cd5 | trade_date_block_bootstrap | 10580 | BLOCKED | False | True | surrun_fcb21dea970638c569c9be9b | UNDERPOWERED |
| sspec_38167f26fc520ba10729e8f7 | trade_date_block_bootstrap | 10581 | BLOCKED | False | True | surrun_7d4dbc67dca200dd325f59ea | UNDERPOWERED |
| sspec_38167f26fc520ba10729e8f7 | trade_date_block_bootstrap | 10582 | BLOCKED | False | True | surrun_f74de6d6fa2620b0ba61286d | UNDERPOWERED |
| sspec_38167f26fc520ba10729e8f7 | trade_date_block_bootstrap | 10583 | BLOCKED | False | True | surrun_acce3af4f5b009f26e93d1dd | UNDERPOWERED |
| sspec_099ebb894df1f80527ffbcb9 | trade_date_block_bootstrap | 10584 | BLOCKED | False | True | surrun_918e068f748cfec489adc415 | UNDERPOWERED |
| sspec_099ebb894df1f80527ffbcb9 | trade_date_block_bootstrap | 10585 | BLOCKED | False | True | surrun_470195c6a31b5a30e487748f | UNDERPOWERED |
| sspec_099ebb894df1f80527ffbcb9 | trade_date_block_bootstrap | 10586 | BLOCKED | False | True | surrun_b139b8b59fde4ebe594587ff | UNDERPOWERED |
| sspec_b475d6280235d7e431f7908e | trade_date_block_bootstrap | 10587 | BLOCKED | False | True | surrun_ba839cdb5e72c26a16d3341f | UNDERPOWERED |
| sspec_b475d6280235d7e431f7908e | trade_date_block_bootstrap | 10588 | BLOCKED | False | True | surrun_a6d6544fbd6f9f144029cb1f | UNDERPOWERED |
| sspec_b475d6280235d7e431f7908e | trade_date_block_bootstrap | 10589 | BLOCKED | False | True | surrun_bf3e9dd66aa57496c8b7d08b | UNDERPOWERED |
| sspec_58ed6d2a649e5a2778c101cf | trade_date_block_bootstrap | 10590 | BLOCKED | False | True | surrun_f216fcc540af2e72a2e0e763 | UNDERPOWERED |
| sspec_58ed6d2a649e5a2778c101cf | trade_date_block_bootstrap | 10591 | BLOCKED | False | True | surrun_6c0a265c7c93e9c62ba07bd3 | UNDERPOWERED |
| sspec_58ed6d2a649e5a2778c101cf | trade_date_block_bootstrap | 10592 | BLOCKED | False | True | surrun_19d747f98b1b8e50ada16000 | UNDERPOWERED |
| sspec_783f453b3cf5870b49bd71bf | trade_date_block_bootstrap | 10593 | BLOCKED | False | True | surrun_b50946dbc511a62fab0a9783 | UNDERPOWERED |
| sspec_783f453b3cf5870b49bd71bf | trade_date_block_bootstrap | 10594 | BLOCKED | False | True | surrun_db70c807c39fae1fec26969d | UNDERPOWERED |
| sspec_783f453b3cf5870b49bd71bf | trade_date_block_bootstrap | 10595 | BLOCKED | False | True | surrun_3562223022dc9cb730f05025 | UNDERPOWERED |
| sspec_52a1c4e73ce56bd71021970f | trade_date_block_bootstrap | 10596 | BLOCKED | False | True | surrun_49c04cb48d9f69272b1fd0c7 | UNDERPOWERED |
| sspec_52a1c4e73ce56bd71021970f | trade_date_block_bootstrap | 10597 | BLOCKED | False | True | surrun_7a923d7e327cae012913e5a4 | UNDERPOWERED |
| sspec_52a1c4e73ce56bd71021970f | trade_date_block_bootstrap | 10598 | BLOCKED | False | True | surrun_a0c54a4e8631a882a0e5162f | UNDERPOWERED |
| sspec_073369f01a3a50aed97e90b6 | trade_date_block_bootstrap | 10599 | BLOCKED | False | True | surrun_3f1a4f7cca28e74bc0f9d52f | UNDERPOWERED |
| sspec_073369f01a3a50aed97e90b6 | trade_date_block_bootstrap | 10600 | BLOCKED | False | True | surrun_648f20d5dbf0ec24b50a6815 | UNDERPOWERED |
| sspec_073369f01a3a50aed97e90b6 | trade_date_block_bootstrap | 10601 | BLOCKED | False | True | surrun_355fd2d70f7ae9ee3a536410 | UNDERPOWERED |
| sspec_095f278394659374be2e4fb3 | trade_date_block_bootstrap | 10602 | BLOCKED | False | True | surrun_6e2625c4bee30f85b9cfec1d | UNDERPOWERED |
| sspec_095f278394659374be2e4fb3 | trade_date_block_bootstrap | 10603 | BLOCKED | False | True | surrun_cdef1a7bef53150daf4d67ae | UNDERPOWERED |
| sspec_095f278394659374be2e4fb3 | trade_date_block_bootstrap | 10604 | BLOCKED | False | True | surrun_198f40505828ee717cb321d1 | UNDERPOWERED |
| sspec_beba467d3196bb17ce122be0 | trade_date_block_bootstrap | 10605 | BLOCKED | False | True | surrun_0ac5c992106306f38ef57dec | UNDERPOWERED |
| sspec_beba467d3196bb17ce122be0 | trade_date_block_bootstrap | 10606 | BLOCKED | False | True | surrun_46c3f2eddd470e34ce8245f9 | UNDERPOWERED |
| sspec_beba467d3196bb17ce122be0 | trade_date_block_bootstrap | 10607 | BLOCKED | False | True | surrun_b060a7fb25f382670aa54bf4 | UNDERPOWERED |
| sspec_68a0eceedbdcad42e563d20f | trade_date_block_bootstrap | 10608 | BLOCKED | False | True | surrun_64a82aa9456620f76a455ffd | UNDERPOWERED |
| sspec_68a0eceedbdcad42e563d20f | trade_date_block_bootstrap | 10609 | BLOCKED | False | True | surrun_abc95c5002ef72bb7c45e22e | UNDERPOWERED |
| sspec_68a0eceedbdcad42e563d20f | trade_date_block_bootstrap | 10610 | BLOCKED | False | True | surrun_806376bef31ea995433286ba | UNDERPOWERED |
| sspec_7fabf471b36a6d96810dc349 | trade_date_block_bootstrap | 10611 | BLOCKED | False | True | surrun_c30b313a7ea5e5ae052ee702 | UNDERPOWERED |
| sspec_7fabf471b36a6d96810dc349 | trade_date_block_bootstrap | 10612 | BLOCKED | False | True | surrun_4e085519dde97c5125a2c0a2 | UNDERPOWERED |
| sspec_7fabf471b36a6d96810dc349 | trade_date_block_bootstrap | 10613 | BLOCKED | False | True | surrun_2abfd2b745b656b8088e20e5 | UNDERPOWERED |
| sspec_be730f9cb7265d684309eefe | trade_date_block_bootstrap | 10614 | BLOCKED | False | True | surrun_5938ae57e22148c957bd6114 | UNDERPOWERED |
| sspec_be730f9cb7265d684309eefe | trade_date_block_bootstrap | 10615 | BLOCKED | False | True | surrun_1afa1b78bffc6b7d196be16b | UNDERPOWERED |
| sspec_be730f9cb7265d684309eefe | trade_date_block_bootstrap | 10616 | BLOCKED | False | True | surrun_114e1b27443f87da0a7e536b | UNDERPOWERED |
| sspec_a9d77fd7e5ebe47a2da05f30 | trade_date_block_bootstrap | 10617 | BLOCKED | False | True | surrun_c76466fd086add9c4f68400b | UNDERPOWERED |
| sspec_a9d77fd7e5ebe47a2da05f30 | trade_date_block_bootstrap | 10618 | BLOCKED | False | True | surrun_53dfea77b961c23e3831e4fc | UNDERPOWERED |
| sspec_a9d77fd7e5ebe47a2da05f30 | trade_date_block_bootstrap | 10619 | BLOCKED | False | True | surrun_3ecc951452be255b79308061 | UNDERPOWERED |
| sspec_089d8c74665fea93209e2500 | trade_date_block_bootstrap | 10620 | BLOCKED | False | True | surrun_fe05a7d742ea8f19e9955ca1 | UNDERPOWERED |
| sspec_089d8c74665fea93209e2500 | trade_date_block_bootstrap | 10621 | BLOCKED | False | True | surrun_7d91b9338507db3a1ef7f7f0 | UNDERPOWERED |
| sspec_089d8c74665fea93209e2500 | trade_date_block_bootstrap | 10622 | BLOCKED | False | True | surrun_d361c6b302219b622d885b03 | UNDERPOWERED |
| sspec_b7f454b3f8f6991a16f02a10 | trade_date_block_bootstrap | 10623 | BLOCKED | False | True | surrun_6d6899addbf22cf547dcad9f | UNDERPOWERED |
| sspec_b7f454b3f8f6991a16f02a10 | trade_date_block_bootstrap | 10624 | BLOCKED | False | True | surrun_aaef6b7dfaa8ee56a08a526d | UNDERPOWERED |
| sspec_b7f454b3f8f6991a16f02a10 | trade_date_block_bootstrap | 10625 | BLOCKED | False | True | surrun_95ec57298b781bded60b59b6 | UNDERPOWERED |
| sspec_4e64a42331bc4e491fd49dba | trade_date_block_bootstrap | 10626 | BLOCKED | False | True | surrun_13b13f340c54ed36598ed369 | UNDERPOWERED |
| sspec_4e64a42331bc4e491fd49dba | trade_date_block_bootstrap | 10627 | BLOCKED | False | True | surrun_83bdd084be7cb5e5f32a34cf | UNDERPOWERED |
| sspec_4e64a42331bc4e491fd49dba | trade_date_block_bootstrap | 10628 | BLOCKED | False | True | surrun_cd208cce50a31bb8ff7bf726 | UNDERPOWERED |
| sspec_c33679741f62715b8ea90d61 | trade_date_block_bootstrap | 10629 | BLOCKED | False | True | surrun_31d28b14965e0df698d761ab | UNDERPOWERED |
| sspec_c33679741f62715b8ea90d61 | trade_date_block_bootstrap | 10630 | BLOCKED | False | True | surrun_4a7badc9c160a74cdf116fbb | UNDERPOWERED |
| sspec_c33679741f62715b8ea90d61 | trade_date_block_bootstrap | 10631 | BLOCKED | False | True | surrun_6f1e8ec41279754bf0174b7a | UNDERPOWERED |
| sspec_be4d9db0faa8bdea65bb4c04 | trade_date_block_bootstrap | 10632 | BLOCKED | False | True | surrun_f2c03a2486357f2ccbcc152b | UNDERPOWERED |
| sspec_be4d9db0faa8bdea65bb4c04 | trade_date_block_bootstrap | 10633 | BLOCKED | False | True | surrun_1707e833c43dd72a9217a278 | UNDERPOWERED |
| sspec_be4d9db0faa8bdea65bb4c04 | trade_date_block_bootstrap | 10634 | BLOCKED | False | True | surrun_08130b3f5e53164d7c9efeb3 | UNDERPOWERED |
| sspec_a979ab600ef726fee2415b56 | trade_date_block_bootstrap | 10635 | BLOCKED | False | True | surrun_03083735b494af7bc1545497 | UNDERPOWERED |
| sspec_a979ab600ef726fee2415b56 | trade_date_block_bootstrap | 10636 | BLOCKED | False | True | surrun_8d3537f6d3b190f85ae15889 | UNDERPOWERED |
| sspec_a979ab600ef726fee2415b56 | trade_date_block_bootstrap | 10637 | BLOCKED | False | True | surrun_b3afb398c0011cd80de132f2 | UNDERPOWERED |
| sspec_2820bcd83f89967ac47b91b3 | trade_date_block_bootstrap | 10638 | BLOCKED | False | True | surrun_ade3278f33d21c68c32e39e5 | UNDERPOWERED |
| sspec_2820bcd83f89967ac47b91b3 | trade_date_block_bootstrap | 10639 | BLOCKED | False | True | surrun_570f2408977d3bf0ef99e496 | UNDERPOWERED |
| sspec_2820bcd83f89967ac47b91b3 | trade_date_block_bootstrap | 10640 | BLOCKED | False | True | surrun_5ee0c44f1c8a83f7d452742d | UNDERPOWERED |
| sspec_737a02bf0d3784d835a31d55 | trade_date_block_bootstrap | 10641 | BLOCKED | False | True | surrun_12d9b38f79dae2805bd90ba5 | UNDERPOWERED |
| sspec_737a02bf0d3784d835a31d55 | trade_date_block_bootstrap | 10642 | BLOCKED | False | True | surrun_0e8c46e1953a0150856c45c3 | UNDERPOWERED |
| sspec_737a02bf0d3784d835a31d55 | trade_date_block_bootstrap | 10643 | BLOCKED | False | True | surrun_18f8e4313accf78b9eb23b64 | UNDERPOWERED |
| sspec_ce24fd9629d6adf16d0f1734 | trade_date_block_bootstrap | 10644 | BLOCKED | False | True | surrun_21451ffe688d127ccba4d042 | UNDERPOWERED |
| sspec_ce24fd9629d6adf16d0f1734 | trade_date_block_bootstrap | 10645 | BLOCKED | False | True | surrun_4d05175bc248a9c226375a23 | UNDERPOWERED |
| sspec_ce24fd9629d6adf16d0f1734 | trade_date_block_bootstrap | 10646 | BLOCKED | False | True | surrun_c053f358bbe4e6899f6894bf | UNDERPOWERED |
| sspec_4e9c217e855268f3c79361d4 | trade_date_block_bootstrap | 10647 | BLOCKED | False | True | surrun_857fa11b77224c774e6e9745 | UNDERPOWERED |
| sspec_4e9c217e855268f3c79361d4 | trade_date_block_bootstrap | 10648 | BLOCKED | False | True | surrun_4a0ed0ac0190324a18ba8fdf | UNDERPOWERED |
| sspec_4e9c217e855268f3c79361d4 | trade_date_block_bootstrap | 10649 | BLOCKED | False | True | surrun_044e17b1492b0b2188f88402 | UNDERPOWERED |
| sspec_a7d7e93a369897385e7bb96a | trade_date_block_bootstrap | 10650 | BLOCKED | False | True | surrun_16f38c0244d9f28622cb4b1c | UNDERPOWERED |
| sspec_a7d7e93a369897385e7bb96a | trade_date_block_bootstrap | 10651 | BLOCKED | False | True | surrun_bcd7f817b709d4eda688ebcf | UNDERPOWERED |
| sspec_a7d7e93a369897385e7bb96a | trade_date_block_bootstrap | 10652 | BLOCKED | False | True | surrun_81c68256ac91e6cbfa77e7bc | UNDERPOWERED |
| sspec_f1d1b3c24676a6d708b069eb | trade_date_block_bootstrap | 10653 | BLOCKED | False | True | surrun_a972d9dc4278d7fdb6e6a2e3 | UNDERPOWERED |
| sspec_f1d1b3c24676a6d708b069eb | trade_date_block_bootstrap | 10654 | BLOCKED | False | True | surrun_761c10a3066989f534d47a3a | UNDERPOWERED |
| sspec_f1d1b3c24676a6d708b069eb | trade_date_block_bootstrap | 10655 | BLOCKED | False | True | surrun_b04405beaa34612de4082c1a | UNDERPOWERED |
| sspec_509da62dbc4657af555ebcf5 | trade_date_block_bootstrap | 10656 | BLOCKED | False | True | surrun_8e98b084f176c110268e31ca | UNDERPOWERED |
| sspec_509da62dbc4657af555ebcf5 | trade_date_block_bootstrap | 10657 | BLOCKED | False | True | surrun_525b0eb127fa8d2f41661b09 | UNDERPOWERED |
| sspec_509da62dbc4657af555ebcf5 | trade_date_block_bootstrap | 10658 | BLOCKED | False | True | surrun_9e142a9f43c436cb8cc02e7b | UNDERPOWERED |
| sspec_e78f59205bb1982685c0a133 | trade_date_block_bootstrap | 10659 | BLOCKED | False | True | surrun_d1e528aeee65691f7ea61a07 | UNDERPOWERED |
| sspec_e78f59205bb1982685c0a133 | trade_date_block_bootstrap | 10660 | BLOCKED | False | True | surrun_ed07ff4cc01ba09da6326008 | UNDERPOWERED |
| sspec_e78f59205bb1982685c0a133 | trade_date_block_bootstrap | 10661 | BLOCKED | False | True | surrun_061b5bfdb9c5454a33672ba5 | UNDERPOWERED |
| sspec_b950e2557bf418cb44a2fbf8 | trade_date_block_bootstrap | 10662 | BLOCKED | False | True | surrun_5e84cc3218a70d2492bc035d | UNDERPOWERED |
| sspec_b950e2557bf418cb44a2fbf8 | trade_date_block_bootstrap | 10663 | BLOCKED | False | True | surrun_04557190bb71ce0658102e32 | UNDERPOWERED |
| sspec_b950e2557bf418cb44a2fbf8 | trade_date_block_bootstrap | 10664 | BLOCKED | False | True | surrun_79ebc8f5e6f48be1e8f938a8 | UNDERPOWERED |
| sspec_97f21f92311d0d20ce745d25 | trade_date_block_bootstrap | 10665 | BLOCKED | False | True | surrun_91edee0046e04b07fba1c7f9 | UNDERPOWERED |
| sspec_97f21f92311d0d20ce745d25 | trade_date_block_bootstrap | 10666 | BLOCKED | False | True | surrun_b6aa39c6e11fbee7bcd3faf6 | UNDERPOWERED |
| sspec_97f21f92311d0d20ce745d25 | trade_date_block_bootstrap | 10667 | BLOCKED | False | True | surrun_8d6a39295b00d3c0323acdb4 | UNDERPOWERED |
| sspec_48ae826bbc46b56a6b9deeef | trade_date_block_bootstrap | 10668 | BLOCKED | False | True | surrun_fffa701338644f8d44f0df92 | UNDERPOWERED |
| sspec_48ae826bbc46b56a6b9deeef | trade_date_block_bootstrap | 10669 | BLOCKED | False | True | surrun_2444364e39cf4ce4ec1666b1 | UNDERPOWERED |
| sspec_48ae826bbc46b56a6b9deeef | trade_date_block_bootstrap | 10670 | BLOCKED | False | True | surrun_b5d69cf1173f28d825ca42a9 | UNDERPOWERED |
| sspec_83ff56ac8fd2969f7aaed14f | trade_date_block_bootstrap | 10671 | BLOCKED | False | True | surrun_32eac9f0d24b55f132e98c4d | UNDERPOWERED |
| sspec_83ff56ac8fd2969f7aaed14f | trade_date_block_bootstrap | 10672 | BLOCKED | False | True | surrun_d8de4f34b7296bf612d5c7be | UNDERPOWERED |
| sspec_83ff56ac8fd2969f7aaed14f | trade_date_block_bootstrap | 10673 | BLOCKED | False | True | surrun_00977168567993abaf0d4d35 | UNDERPOWERED |
| sspec_76a140bddd84aad12f1293ae | trade_date_block_bootstrap | 10674 | BLOCKED | False | True | surrun_d2a1e7bd433bcc57bb8d3ba2 | UNDERPOWERED |
| sspec_76a140bddd84aad12f1293ae | trade_date_block_bootstrap | 10675 | BLOCKED | False | True | surrun_b583c96e0f8372babcf057ee | UNDERPOWERED |
| sspec_76a140bddd84aad12f1293ae | trade_date_block_bootstrap | 10676 | BLOCKED | False | True | surrun_b1de68bd2420ee7abdadbffe | UNDERPOWERED |
| sspec_e00515e2e6131b8c5d5af6f9 | trade_date_block_bootstrap | 10677 | BLOCKED | False | True | surrun_027416eec475c05a8ed36440 | UNDERPOWERED |
| sspec_e00515e2e6131b8c5d5af6f9 | trade_date_block_bootstrap | 10678 | BLOCKED | False | True | surrun_b545960b78e9fd2c6b337701 | UNDERPOWERED |
| sspec_e00515e2e6131b8c5d5af6f9 | trade_date_block_bootstrap | 10679 | BLOCKED | False | True | surrun_c0429410ea03b12c93c62959 | UNDERPOWERED |
| sspec_2ae821d0eda04ce3988ac24a | trade_date_block_bootstrap | 10680 | BLOCKED | False | True | surrun_c45ff437d377d0bc2da7c4e0 | UNDERPOWERED |
| sspec_2ae821d0eda04ce3988ac24a | trade_date_block_bootstrap | 10681 | BLOCKED | False | True | surrun_8e1ff96e992bbbc2236f7892 | UNDERPOWERED |
| sspec_2ae821d0eda04ce3988ac24a | trade_date_block_bootstrap | 10682 | BLOCKED | False | True | surrun_2c7c082962cef20adfdfcea5 | UNDERPOWERED |
| sspec_89ac002fad22d13a5f7577e1 | trade_date_block_bootstrap | 10683 | BLOCKED | False | True | surrun_a675e35ba08a7a428bc581e5 | UNDERPOWERED |
| sspec_89ac002fad22d13a5f7577e1 | trade_date_block_bootstrap | 10684 | BLOCKED | False | True | surrun_6d0b1ebba998d417dba660ca | UNDERPOWERED |
| sspec_89ac002fad22d13a5f7577e1 | trade_date_block_bootstrap | 10685 | BLOCKED | False | True | surrun_f5618d525ef10dc28f5aeb29 | UNDERPOWERED |
| sspec_c520510d66bedb107abe0269 | trade_date_block_bootstrap | 10686 | BLOCKED | False | True | surrun_1a01e991fbddb8a7a22b84f0 | UNDERPOWERED |
| sspec_c520510d66bedb107abe0269 | trade_date_block_bootstrap | 10687 | BLOCKED | False | True | surrun_a605ec9953c1f4ba7b4b3f20 | UNDERPOWERED |
| sspec_c520510d66bedb107abe0269 | trade_date_block_bootstrap | 10688 | BLOCKED | False | True | surrun_d4e88b47d5d7a91ea1a782d5 | UNDERPOWERED |
| sspec_5e66fbed683802d36cf78c78 | trade_date_block_bootstrap | 10689 | BLOCKED | False | True | surrun_00d0352a14d775bd33ced5d5 | UNDERPOWERED |
| sspec_5e66fbed683802d36cf78c78 | trade_date_block_bootstrap | 10690 | BLOCKED | False | True | surrun_7f09c2285805824d227f120b | UNDERPOWERED |
| sspec_5e66fbed683802d36cf78c78 | trade_date_block_bootstrap | 10691 | BLOCKED | False | True | surrun_b7f1852d23034dbee3945f50 | UNDERPOWERED |
| sspec_e9532065e877e419ed00a928 | trade_date_block_bootstrap | 10692 | BLOCKED | False | True | surrun_177acccf80af90b3277472ca | UNDERPOWERED |
| sspec_e9532065e877e419ed00a928 | trade_date_block_bootstrap | 10693 | BLOCKED | False | True | surrun_bfdad8ab279355f9433be6dd | UNDERPOWERED |
| sspec_e9532065e877e419ed00a928 | trade_date_block_bootstrap | 10694 | BLOCKED | False | True | surrun_559d2b19ab69c19f7af08647 | UNDERPOWERED |
| sspec_3c5b1c2deac8886df2db6210 | trade_date_block_bootstrap | 10695 | BLOCKED | False | True | surrun_8e58b5215c8f82486ccb20f6 | UNDERPOWERED |
| sspec_3c5b1c2deac8886df2db6210 | trade_date_block_bootstrap | 10696 | BLOCKED | False | True | surrun_68b7ec3f66fa84d9e94ec820 | UNDERPOWERED |
| sspec_3c5b1c2deac8886df2db6210 | trade_date_block_bootstrap | 10697 | BLOCKED | False | True | surrun_12a3770a5daed32d0b4bd933 | UNDERPOWERED |
| sspec_9a6a2300dfac7e86e3fa1564 | trade_date_block_bootstrap | 10698 | BLOCKED | False | True | surrun_c8fcf949c10d236750c79cc1 | UNDERPOWERED |
| sspec_9a6a2300dfac7e86e3fa1564 | trade_date_block_bootstrap | 10699 | BLOCKED | False | True | surrun_1d9fe889855b6379a8ea3d64 | UNDERPOWERED |
| sspec_9a6a2300dfac7e86e3fa1564 | trade_date_block_bootstrap | 10700 | BLOCKED | False | True | surrun_6730bd4a4e0c33792a973032 | UNDERPOWERED |
| sspec_e54e46398cd54daf3788cc6e | trade_date_block_bootstrap | 10701 | BLOCKED | False | True | surrun_421a84d7b14bcfc0b64b0119 | UNDERPOWERED |
| sspec_e54e46398cd54daf3788cc6e | trade_date_block_bootstrap | 10702 | BLOCKED | False | True | surrun_93dd856233cc9047468ff08c | UNDERPOWERED |
| sspec_e54e46398cd54daf3788cc6e | trade_date_block_bootstrap | 10703 | BLOCKED | False | True | surrun_d3c7bd79aee3b0ca29da5d2e | UNDERPOWERED |
| sspec_e1dc6dc58114c2b287ae547d | trade_date_block_bootstrap | 10704 | BLOCKED | False | True | surrun_8dc7027cd4ee17250fe46b3c | UNDERPOWERED |
| sspec_e1dc6dc58114c2b287ae547d | trade_date_block_bootstrap | 10705 | BLOCKED | False | True | surrun_ca9f17d74b7de52122f591c7 | UNDERPOWERED |
| sspec_e1dc6dc58114c2b287ae547d | trade_date_block_bootstrap | 10706 | BLOCKED | False | True | surrun_06a664e919a4967f4fd94bd3 | UNDERPOWERED |
| sspec_0c236ef9f77e9191f7b62936 | trade_date_block_bootstrap | 10707 | BLOCKED | False | True | surrun_de21354154c9b722b23a2372 | UNDERPOWERED |
| sspec_0c236ef9f77e9191f7b62936 | trade_date_block_bootstrap | 10708 | BLOCKED | False | True | surrun_62481854fe081d90e1221a2e | UNDERPOWERED |
| sspec_0c236ef9f77e9191f7b62936 | trade_date_block_bootstrap | 10709 | BLOCKED | False | True | surrun_28e3a3f3f81eeb85bad1665a | UNDERPOWERED |
| sspec_05471b51e6fee2b7ca9e875b | trade_date_block_bootstrap | 10710 | BLOCKED | False | True | surrun_7b86b1334d970c920d05c918 | UNDERPOWERED |
| sspec_05471b51e6fee2b7ca9e875b | trade_date_block_bootstrap | 10711 | BLOCKED | False | True | surrun_5420bd6c37551e19b1a8cf33 | UNDERPOWERED |
| sspec_05471b51e6fee2b7ca9e875b | trade_date_block_bootstrap | 10712 | BLOCKED | False | True | surrun_f566b428e849b46d58de242d | UNDERPOWERED |
| sspec_a08b2b489849bb619c996ae5 | trade_date_block_bootstrap | 10713 | BLOCKED | False | True | surrun_c3f13a6333c5e0cb85edb40d | UNDERPOWERED |
| sspec_a08b2b489849bb619c996ae5 | trade_date_block_bootstrap | 10714 | BLOCKED | False | True | surrun_5ae0c481cf5d49361f50eaa2 | UNDERPOWERED |
| sspec_a08b2b489849bb619c996ae5 | trade_date_block_bootstrap | 10715 | BLOCKED | False | True | surrun_8bae1d80e9588d07b974d24a | UNDERPOWERED |
| sspec_fa24fd829b877dcd7f34f539 | trade_date_block_bootstrap | 10716 | BLOCKED | False | True | surrun_3046ff493071e4a6d6e3e298 | UNDERPOWERED |
| sspec_fa24fd829b877dcd7f34f539 | trade_date_block_bootstrap | 10717 | BLOCKED | False | True | surrun_35e9023080a0af05af63133b | UNDERPOWERED |
| sspec_fa24fd829b877dcd7f34f539 | trade_date_block_bootstrap | 10718 | BLOCKED | False | True | surrun_31aa9dba253d2fb88a699678 | UNDERPOWERED |
| sspec_dc72f62576538ccd318a9803 | trade_date_block_bootstrap | 10719 | BLOCKED | False | True | surrun_a3561d5835bf5a55782bd114 | UNDERPOWERED |
| sspec_dc72f62576538ccd318a9803 | trade_date_block_bootstrap | 10720 | BLOCKED | False | True | surrun_026b3a8bfc0289ded3985787 | UNDERPOWERED |
| sspec_dc72f62576538ccd318a9803 | trade_date_block_bootstrap | 10721 | BLOCKED | False | True | surrun_5a3fc333a99c1df7bba14354 | UNDERPOWERED |
| sspec_040153645920514cb66cf13a | trade_date_block_bootstrap | 10722 | BLOCKED | False | True | surrun_8df75b82d44708affd177b0a | UNDERPOWERED |
| sspec_040153645920514cb66cf13a | trade_date_block_bootstrap | 10723 | BLOCKED | False | True | surrun_ee6b2f0c9d6f4cf8e303364f | UNDERPOWERED |
| sspec_040153645920514cb66cf13a | trade_date_block_bootstrap | 10724 | BLOCKED | False | True | surrun_98d5691661d16d92a9f8fc5d | UNDERPOWERED |
| sspec_c6c25767a92fa953414a1934 | trade_date_block_bootstrap | 10725 | BLOCKED | False | True | surrun_c7a61d27e4ad03690f917ba0 | UNDERPOWERED |
| sspec_c6c25767a92fa953414a1934 | trade_date_block_bootstrap | 10726 | BLOCKED | False | True | surrun_bffd559e4c28269f92ea6666 | UNDERPOWERED |
| sspec_c6c25767a92fa953414a1934 | trade_date_block_bootstrap | 10727 | BLOCKED | False | True | surrun_4746ad396ae0fb4675674f91 | UNDERPOWERED |
| sspec_b9f4feca968f31fd8c1d2000 | trade_date_block_bootstrap | 10728 | BLOCKED | False | True | surrun_c5b047982a80a88d57b28e77 | UNDERPOWERED |
| sspec_b9f4feca968f31fd8c1d2000 | trade_date_block_bootstrap | 10729 | BLOCKED | False | True | surrun_84a301a23fe7412f837cdbdb | UNDERPOWERED |
| sspec_b9f4feca968f31fd8c1d2000 | trade_date_block_bootstrap | 10730 | BLOCKED | False | True | surrun_9c21c9fb66c2334070c3c0f1 | UNDERPOWERED |
| sspec_83a7cd07438b812c800bee51 | trade_date_block_bootstrap | 10731 | BLOCKED | False | True | surrun_b64e089324af51b36521aa77 | UNDERPOWERED |
| sspec_83a7cd07438b812c800bee51 | trade_date_block_bootstrap | 10732 | BLOCKED | False | True | surrun_bb10456a3c5894851ba7dc72 | UNDERPOWERED |
| sspec_83a7cd07438b812c800bee51 | trade_date_block_bootstrap | 10733 | BLOCKED | False | True | surrun_2b6fa46e990e914ad6781b7e | UNDERPOWERED |
| sspec_9a21f36d4081e500f653f25f | trade_date_block_bootstrap | 10734 | BLOCKED | False | True | surrun_62e68bad78c8de16d76808ae | UNDERPOWERED |
| sspec_9a21f36d4081e500f653f25f | trade_date_block_bootstrap | 10735 | BLOCKED | False | True | surrun_5ddda96921bec62a2ec8bc59 | UNDERPOWERED |
| sspec_9a21f36d4081e500f653f25f | trade_date_block_bootstrap | 10736 | BLOCKED | False | True | surrun_b36d1adf0eae32af223021cf | UNDERPOWERED |
| sspec_990869ad8278a45aa4d7c826 | trade_date_block_bootstrap | 10737 | BLOCKED | False | True | surrun_491303fc996c5c8136407c23 | UNDERPOWERED |
| sspec_990869ad8278a45aa4d7c826 | trade_date_block_bootstrap | 10738 | BLOCKED | False | True | surrun_cf3f41488b6586197de0a35b | UNDERPOWERED |
| sspec_990869ad8278a45aa4d7c826 | trade_date_block_bootstrap | 10739 | BLOCKED | False | True | surrun_119ebb543e62ae1f0a987653 | UNDERPOWERED |
| sspec_d49a2b49acee824065afeecb | trade_date_block_bootstrap | 10740 | BLOCKED | False | True | surrun_ca7cc190a0e8c0798d592ce2 | UNDERPOWERED |
| sspec_d49a2b49acee824065afeecb | trade_date_block_bootstrap | 10741 | BLOCKED | False | True | surrun_23dce87585e8214b857c39e2 | UNDERPOWERED |
| sspec_d49a2b49acee824065afeecb | trade_date_block_bootstrap | 10742 | BLOCKED | False | True | surrun_d0175511ef6fad886b0c8a64 | UNDERPOWERED |
| sspec_9fb5bb6be944583adbbb777c | trade_date_block_bootstrap | 10743 | BLOCKED | False | True | surrun_0c8949030fd076e341f77576 | UNDERPOWERED |
| sspec_9fb5bb6be944583adbbb777c | trade_date_block_bootstrap | 10744 | BLOCKED | False | True | surrun_981b90814006823ad8bd2d23 | UNDERPOWERED |
| sspec_9fb5bb6be944583adbbb777c | trade_date_block_bootstrap | 10745 | BLOCKED | False | True | surrun_5fce8fdd325441c081723e27 | UNDERPOWERED |
| sspec_b045d3594982c81d1689203e | trade_date_block_bootstrap | 10746 | BLOCKED | False | True | surrun_3f170775cd862a2c078e7414 | UNDERPOWERED |
| sspec_b045d3594982c81d1689203e | trade_date_block_bootstrap | 10747 | BLOCKED | False | True | surrun_18bca8b9a318dd27dc76b075 | UNDERPOWERED |
| sspec_b045d3594982c81d1689203e | trade_date_block_bootstrap | 10748 | BLOCKED | False | True | surrun_69f9a52513a295cff70a7a23 | UNDERPOWERED |
| sspec_9bb382ff9c2c74f51651d599 | trade_date_block_bootstrap | 10749 | BLOCKED | False | True | surrun_e86b81f71e7cd9ba7e2f74e1 | UNDERPOWERED |
| sspec_9bb382ff9c2c74f51651d599 | trade_date_block_bootstrap | 10750 | BLOCKED | False | True | surrun_9575c8b6b2b4293584c6bae3 | UNDERPOWERED |
| sspec_9bb382ff9c2c74f51651d599 | trade_date_block_bootstrap | 10751 | BLOCKED | False | True | surrun_c72784e3ca6fc0561397a288 | UNDERPOWERED |
| sspec_280a8dfe4461daecf124ffcd | trade_date_block_bootstrap | 10752 | BLOCKED | False | True | surrun_b42f76c55c4ad8868a863d48 | UNDERPOWERED |
| sspec_280a8dfe4461daecf124ffcd | trade_date_block_bootstrap | 10753 | BLOCKED | False | True | surrun_af13bb1e7a828320ed57373d | UNDERPOWERED |
| sspec_280a8dfe4461daecf124ffcd | trade_date_block_bootstrap | 10754 | BLOCKED | False | True | surrun_411067c437547a51abe3dcd1 | UNDERPOWERED |
| sspec_7beb2827c66016b2336b5f63 | trade_date_block_bootstrap | 10755 | BLOCKED | False | True | surrun_b9de6819e697ac75b07caf65 | UNDERPOWERED |
| sspec_7beb2827c66016b2336b5f63 | trade_date_block_bootstrap | 10756 | BLOCKED | False | True | surrun_b2be8028e1703684a6098984 | UNDERPOWERED |
| sspec_7beb2827c66016b2336b5f63 | trade_date_block_bootstrap | 10757 | BLOCKED | False | True | surrun_d5c3c2f37c097c55b06665bd | UNDERPOWERED |
| sspec_862d44c0d9122cd6d7abaf4d | trade_date_block_bootstrap | 10758 | BLOCKED | False | True | surrun_90f73c4c0101721270754bb8 | UNDERPOWERED |
| sspec_862d44c0d9122cd6d7abaf4d | trade_date_block_bootstrap | 10759 | BLOCKED | False | True | surrun_e78e8e9013775d1e32942753 | UNDERPOWERED |
| sspec_862d44c0d9122cd6d7abaf4d | trade_date_block_bootstrap | 10760 | BLOCKED | False | True | surrun_8b760adbed866fad9800e9a2 | UNDERPOWERED |
| sspec_6bbdb23561c217d42c38a1fa | trade_date_block_bootstrap | 10761 | BLOCKED | False | True | surrun_8718edfc737f4c9a33585b29 | UNDERPOWERED |
| sspec_6bbdb23561c217d42c38a1fa | trade_date_block_bootstrap | 10762 | BLOCKED | False | True | surrun_7d00f56f6ba795bd194ec20a | UNDERPOWERED |
| sspec_6bbdb23561c217d42c38a1fa | trade_date_block_bootstrap | 10763 | BLOCKED | False | True | surrun_c3f1e00d3ad82d8e5136746e | UNDERPOWERED |
| sspec_755d980617a38be3475eedd2 | trade_date_block_bootstrap | 10764 | BLOCKED | False | True | surrun_59c96453ee32d562767d06bc | UNDERPOWERED |
| sspec_755d980617a38be3475eedd2 | trade_date_block_bootstrap | 10765 | BLOCKED | False | True | surrun_c31f76a07c784b4b4f33ecd5 | UNDERPOWERED |
| sspec_755d980617a38be3475eedd2 | trade_date_block_bootstrap | 10766 | BLOCKED | False | True | surrun_a20a6f69d9644e01187bbc1d | UNDERPOWERED |
| sspec_97c4afb23a76ecd721df20b3 | trade_date_block_bootstrap | 10767 | BLOCKED | False | True | surrun_b44a203bd203fb7ed38e1e88 | UNDERPOWERED |
| sspec_97c4afb23a76ecd721df20b3 | trade_date_block_bootstrap | 10768 | BLOCKED | False | True | surrun_1a6df96e03d4325386e2ced2 | UNDERPOWERED |
| sspec_97c4afb23a76ecd721df20b3 | trade_date_block_bootstrap | 10769 | BLOCKED | False | True | surrun_68fa40f20d251c8b821085c5 | UNDERPOWERED |
| sspec_ed61d9465a629f60c3268bda | trade_date_block_bootstrap | 10770 | BLOCKED | False | True | surrun_c7bd4e60c25ff5445124a58d | UNDERPOWERED |
| sspec_ed61d9465a629f60c3268bda | trade_date_block_bootstrap | 10771 | BLOCKED | False | True | surrun_a549a0d2ed5fbfe212ae0f68 | UNDERPOWERED |
| sspec_ed61d9465a629f60c3268bda | trade_date_block_bootstrap | 10772 | BLOCKED | False | True | surrun_863cd1b2de2a35136570701e | UNDERPOWERED |
| sspec_7270b20010b09309e6c29317 | trade_date_block_bootstrap | 10773 | BLOCKED | False | True | surrun_f386a1a373672aff836634ef | UNDERPOWERED |
| sspec_7270b20010b09309e6c29317 | trade_date_block_bootstrap | 10774 | BLOCKED | False | True | surrun_65958434f4866b869be7f09d | UNDERPOWERED |
| sspec_7270b20010b09309e6c29317 | trade_date_block_bootstrap | 10775 | BLOCKED | False | True | surrun_ff17e6e5df150d2f5522fc24 | UNDERPOWERED |
| sspec_a4913956ea5f67114bee127d | trade_date_block_bootstrap | 10776 | BLOCKED | False | True | surrun_03e9e2ddcc3465afb40f96b8 | UNDERPOWERED |
| sspec_a4913956ea5f67114bee127d | trade_date_block_bootstrap | 10777 | BLOCKED | False | True | surrun_484ab68b14c34ea15a01b3de | UNDERPOWERED |
| sspec_a4913956ea5f67114bee127d | trade_date_block_bootstrap | 10778 | BLOCKED | False | True | surrun_193566acb5dff77b93f6bf65 | UNDERPOWERED |
| sspec_42c1927fc60742b4c1473f5a | trade_date_block_bootstrap | 10779 | BLOCKED | False | True | surrun_a83acb3a854b0e5a1159a84a | UNDERPOWERED |
| sspec_42c1927fc60742b4c1473f5a | trade_date_block_bootstrap | 10780 | BLOCKED | False | True | surrun_78097a2b095e77f4b37cb737 | UNDERPOWERED |
| sspec_42c1927fc60742b4c1473f5a | trade_date_block_bootstrap | 10781 | BLOCKED | False | True | surrun_20b8544da518cf6b0d0e9a24 | UNDERPOWERED |
| sspec_9bf1f243048a6c8cf7befc8e | trade_date_block_bootstrap | 10782 | BLOCKED | False | True | surrun_8b8354d7d1d0064cfa3f8a07 | UNDERPOWERED |
| sspec_9bf1f243048a6c8cf7befc8e | trade_date_block_bootstrap | 10783 | BLOCKED | False | True | surrun_cbcadda2ff3961cb317018a9 | UNDERPOWERED |
| sspec_9bf1f243048a6c8cf7befc8e | trade_date_block_bootstrap | 10784 | BLOCKED | False | True | surrun_d39ea3ab5accc1926baf6613 | UNDERPOWERED |
| sspec_f4c3d55505198d2b5ff2409e | trade_date_block_bootstrap | 10785 | BLOCKED | False | True | surrun_9ccb9654b2f73f24ac8803a5 | UNDERPOWERED |
| sspec_f4c3d55505198d2b5ff2409e | trade_date_block_bootstrap | 10786 | BLOCKED | False | True | surrun_9270a6a6b4971c29a83192d7 | UNDERPOWERED |
| sspec_f4c3d55505198d2b5ff2409e | trade_date_block_bootstrap | 10787 | BLOCKED | False | True | surrun_8b0ffe302025074c69ebc4c3 | UNDERPOWERED |
| sspec_3916fc01853676ba093c9272 | trade_date_block_bootstrap | 10788 | BLOCKED | False | True | surrun_fd887303c0b5bf8780468869 | UNDERPOWERED |
| sspec_3916fc01853676ba093c9272 | trade_date_block_bootstrap | 10789 | BLOCKED | False | True | surrun_4e1f4e058d7ff248198918ed | UNDERPOWERED |
| sspec_3916fc01853676ba093c9272 | trade_date_block_bootstrap | 10790 | BLOCKED | False | True | surrun_63f266116f800327d95173cc | UNDERPOWERED |
| sspec_4c978ff1e143f380ebe4552c | trade_date_block_bootstrap | 10791 | BLOCKED | False | True | surrun_cc474de6008d888c8a9a3b04 | UNDERPOWERED |
| sspec_4c978ff1e143f380ebe4552c | trade_date_block_bootstrap | 10792 | BLOCKED | False | True | surrun_fd288b67d92e643f66fcd5f5 | UNDERPOWERED |
| sspec_4c978ff1e143f380ebe4552c | trade_date_block_bootstrap | 10793 | BLOCKED | False | True | surrun_b8740effbaa2596d4c233fea | UNDERPOWERED |
| sspec_e543501b83b61576c1866ca8 | trade_date_block_bootstrap | 10794 | BLOCKED | False | True | surrun_b45b1874ab5a413a991b705a | UNDERPOWERED |
| sspec_e543501b83b61576c1866ca8 | trade_date_block_bootstrap | 10795 | BLOCKED | False | True | surrun_c5f80f99fdbd76be42acfbfc | UNDERPOWERED |
| sspec_e543501b83b61576c1866ca8 | trade_date_block_bootstrap | 10796 | BLOCKED | False | True | surrun_f6718315222d24c1695203d1 | UNDERPOWERED |
| sspec_f6f831a9f002292d241b4c0e | trade_date_block_bootstrap | 10797 | BLOCKED | False | True | surrun_d1245f6e66b668b7223ce6f8 | UNDERPOWERED |
| sspec_f6f831a9f002292d241b4c0e | trade_date_block_bootstrap | 10798 | BLOCKED | False | True | surrun_1bcc76e70e34c3c3d948ab84 | UNDERPOWERED |
| sspec_f6f831a9f002292d241b4c0e | trade_date_block_bootstrap | 10799 | BLOCKED | False | True | surrun_2e53370cfa3e76038d044889 | UNDERPOWERED |
| sspec_aaa7b9fc3c19951d861e461c | trade_date_block_bootstrap | 10800 | BLOCKED | False | True | surrun_8bc22f1612d338559d8b6dc5 | UNDERPOWERED |
| sspec_aaa7b9fc3c19951d861e461c | trade_date_block_bootstrap | 10801 | BLOCKED | False | True | surrun_34736a8e7f6ac72db73ed0a6 | UNDERPOWERED |
| sspec_aaa7b9fc3c19951d861e461c | trade_date_block_bootstrap | 10802 | BLOCKED | False | True | surrun_b47300ff38b69468695ba119 | UNDERPOWERED |
| sspec_734771a045dadd9ae2f1010b | trade_date_block_bootstrap | 10803 | BLOCKED | False | True | surrun_e01066a71665e7b1cdaca244 | UNDERPOWERED |
| sspec_734771a045dadd9ae2f1010b | trade_date_block_bootstrap | 10804 | BLOCKED | False | True | surrun_dc81ca178ae868bd3cb68ffa | UNDERPOWERED |
| sspec_734771a045dadd9ae2f1010b | trade_date_block_bootstrap | 10805 | BLOCKED | False | True | surrun_fac1ee1411d80d93e4540a33 | UNDERPOWERED |
| sspec_51b0c2d1a1d86d2de8ca8b8f | trade_date_block_bootstrap | 10806 | BLOCKED | False | True | surrun_9fa1267e2f03c7a58ec352cd | UNDERPOWERED |
| sspec_51b0c2d1a1d86d2de8ca8b8f | trade_date_block_bootstrap | 10807 | BLOCKED | False | True | surrun_2e7caf970c7c1d2ee1e6e6ed | UNDERPOWERED |
| sspec_51b0c2d1a1d86d2de8ca8b8f | trade_date_block_bootstrap | 10808 | BLOCKED | False | True | surrun_2a169f7dea1588452c4b74a6 | UNDERPOWERED |
| sspec_868225d43c64c888b0566cc6 | trade_date_block_bootstrap | 10809 | BLOCKED | False | True | surrun_2875bb814d11fc8f7ccef843 | UNDERPOWERED |
| sspec_868225d43c64c888b0566cc6 | trade_date_block_bootstrap | 10810 | BLOCKED | False | True | surrun_ed703b3af125763f2b5617a5 | UNDERPOWERED |
| sspec_868225d43c64c888b0566cc6 | trade_date_block_bootstrap | 10811 | BLOCKED | False | True | surrun_443148470ccb356f48bb55a5 | UNDERPOWERED |
| sspec_cba016c20e3f88feb3aa65ca | trade_date_block_bootstrap | 10812 | BLOCKED | False | True | surrun_a6f21a8a63b4db8f410892d0 | UNDERPOWERED |
| sspec_cba016c20e3f88feb3aa65ca | trade_date_block_bootstrap | 10813 | BLOCKED | False | True | surrun_c406d28058ae2947f549d08c | UNDERPOWERED |
| sspec_cba016c20e3f88feb3aa65ca | trade_date_block_bootstrap | 10814 | BLOCKED | False | True | surrun_cc77644569f07ff1bd4829c6 | UNDERPOWERED |
| sspec_ef04ec11958032887aef641c | trade_date_block_bootstrap | 10815 | BLOCKED | False | True | surrun_ccbe33009e9fd226c7358e4a | UNDERPOWERED |
| sspec_ef04ec11958032887aef641c | trade_date_block_bootstrap | 10816 | BLOCKED | False | True | surrun_b4423f9540fd2ef94dd265f1 | UNDERPOWERED |
| sspec_ef04ec11958032887aef641c | trade_date_block_bootstrap | 10817 | BLOCKED | False | True | surrun_bfaaa7bb22db29741c61a867 | UNDERPOWERED |
| sspec_06f2dfe145bb519416e70ece | trade_date_block_bootstrap | 10818 | BLOCKED | False | True | surrun_745ca9431bc4a35b32606273 | UNDERPOWERED |
| sspec_06f2dfe145bb519416e70ece | trade_date_block_bootstrap | 10819 | BLOCKED | False | True | surrun_e2fa7f3e8efdfb7b7d795f8b | UNDERPOWERED |
| sspec_06f2dfe145bb519416e70ece | trade_date_block_bootstrap | 10820 | BLOCKED | False | True | surrun_6f289fe4544b2e516540230e | UNDERPOWERED |
| sspec_8e128caf257a2f37528df25f | trade_date_block_bootstrap | 10821 | BLOCKED | False | True | surrun_63f737aa464fe548364ea922 | UNDERPOWERED |
| sspec_8e128caf257a2f37528df25f | trade_date_block_bootstrap | 10822 | BLOCKED | False | True | surrun_a764cb16b90ba8a1858e1a22 | UNDERPOWERED |
| sspec_8e128caf257a2f37528df25f | trade_date_block_bootstrap | 10823 | BLOCKED | False | True | surrun_a90ae06d96da6820a58c9c80 | UNDERPOWERED |
| sspec_3847376fee593d3e5c339779 | trade_date_block_bootstrap | 10824 | BLOCKED | False | True | surrun_60f10eba8ac17aa30d70e197 | UNDERPOWERED |
| sspec_3847376fee593d3e5c339779 | trade_date_block_bootstrap | 10825 | BLOCKED | False | True | surrun_2e6a67ac4d45b5c0988c7542 | UNDERPOWERED |
| sspec_3847376fee593d3e5c339779 | trade_date_block_bootstrap | 10826 | BLOCKED | False | True | surrun_5c6035d021ccae27dc1526e1 | UNDERPOWERED |
| sspec_72ccb72047e196a033b539ee | trade_date_block_bootstrap | 10827 | BLOCKED | False | True | surrun_7e3fd20fc41ecb576758a5b5 | UNDERPOWERED |
| sspec_72ccb72047e196a033b539ee | trade_date_block_bootstrap | 10828 | BLOCKED | False | True | surrun_96f4c26646a055b936c6cfa7 | UNDERPOWERED |
| sspec_72ccb72047e196a033b539ee | trade_date_block_bootstrap | 10829 | BLOCKED | False | True | surrun_dc9e66d6417a3212fff2fd7a | UNDERPOWERED |
| sspec_7ad93c904580af339b305b89 | trade_date_block_bootstrap | 10830 | BLOCKED | False | True | surrun_75e3677caec84139181ded75 | UNDERPOWERED |
| sspec_7ad93c904580af339b305b89 | trade_date_block_bootstrap | 10831 | BLOCKED | False | True | surrun_f07cf0f02d7195b7af5e0768 | UNDERPOWERED |
| sspec_7ad93c904580af339b305b89 | trade_date_block_bootstrap | 10832 | BLOCKED | False | True | surrun_72c83c58d9aa185e8c884a31 | UNDERPOWERED |
| sspec_660d0400eddcfa0c9ecee620 | trade_date_block_bootstrap | 10833 | BLOCKED | False | True | surrun_9722ad2d98442b7bd5107280 | UNDERPOWERED |
| sspec_660d0400eddcfa0c9ecee620 | trade_date_block_bootstrap | 10834 | BLOCKED | False | True | surrun_e36966a0cb099f469141f40e | UNDERPOWERED |
| sspec_660d0400eddcfa0c9ecee620 | trade_date_block_bootstrap | 10835 | BLOCKED | False | True | surrun_99228ffddeaa7fb88a88fee7 | UNDERPOWERED |
| sspec_c14388826d27968e6f2805ea | trade_date_block_bootstrap | 10836 | BLOCKED | False | True | surrun_33a9513cd6e959c1b6c80e66 | UNDERPOWERED |
| sspec_c14388826d27968e6f2805ea | trade_date_block_bootstrap | 10837 | BLOCKED | False | True | surrun_130b4e941d861cf0318d55c8 | UNDERPOWERED |
| sspec_c14388826d27968e6f2805ea | trade_date_block_bootstrap | 10838 | BLOCKED | False | True | surrun_aec5ce5815431904c38f9ee4 | UNDERPOWERED |
| sspec_5928c9c877f6b48943be0e18 | trade_date_block_bootstrap | 10839 | BLOCKED | False | True | surrun_2d2ef60c87057913aa7f714f | UNDERPOWERED |
| sspec_5928c9c877f6b48943be0e18 | trade_date_block_bootstrap | 10840 | BLOCKED | False | True | surrun_e6dd1f5491b8e897435b00e9 | UNDERPOWERED |
| sspec_5928c9c877f6b48943be0e18 | trade_date_block_bootstrap | 10841 | BLOCKED | False | True | surrun_c55530e6729c96b1bb912f29 | UNDERPOWERED |
| sspec_341f0539ee4b783cd52a891e | trade_date_block_bootstrap | 10842 | BLOCKED | False | True | surrun_e371c8d422c3513ac6b53544 | UNDERPOWERED |
| sspec_341f0539ee4b783cd52a891e | trade_date_block_bootstrap | 10843 | BLOCKED | False | True | surrun_b32273482eec954a80dd41d2 | UNDERPOWERED |
| sspec_341f0539ee4b783cd52a891e | trade_date_block_bootstrap | 10844 | BLOCKED | False | True | surrun_b960e7e365abe8cbd328c82a | UNDERPOWERED |
| sspec_e844231ca55c9c5668d4f1a0 | trade_date_block_bootstrap | 10845 | BLOCKED | False | True | surrun_e39252f3d932edaf04b3b64d | UNDERPOWERED |
| sspec_e844231ca55c9c5668d4f1a0 | trade_date_block_bootstrap | 10846 | BLOCKED | False | True | surrun_4402013162eb61e3741b3f6e | UNDERPOWERED |
| sspec_e844231ca55c9c5668d4f1a0 | trade_date_block_bootstrap | 10847 | BLOCKED | False | True | surrun_b72708bca20998aa0d7879d0 | UNDERPOWERED |
| sspec_5f2d607558658bc4dcca2682 | trade_date_block_bootstrap | 10848 | BLOCKED | False | True | surrun_d89327adb76db7b86ded0d7b | UNDERPOWERED |
| sspec_5f2d607558658bc4dcca2682 | trade_date_block_bootstrap | 10849 | BLOCKED | False | True | surrun_ede28c1e45a1a4d77f621037 | UNDERPOWERED |
| sspec_5f2d607558658bc4dcca2682 | trade_date_block_bootstrap | 10850 | BLOCKED | False | True | surrun_ba2e8b428e0dee1467d75d47 | UNDERPOWERED |
| sspec_c298bbf82f016129aa6a8d5d | trade_date_block_bootstrap | 10851 | BLOCKED | False | True | surrun_5882feefbc87f1b030b48062 | UNDERPOWERED |
| sspec_c298bbf82f016129aa6a8d5d | trade_date_block_bootstrap | 10852 | BLOCKED | False | True | surrun_6975ecfa00ced22f87479b35 | UNDERPOWERED |
| sspec_c298bbf82f016129aa6a8d5d | trade_date_block_bootstrap | 10853 | BLOCKED | False | True | surrun_e1d457be3f574ef4967062d0 | UNDERPOWERED |
| sspec_615957e589b327ad9c219a0e | trade_date_block_bootstrap | 10854 | BLOCKED | False | True | surrun_8a856a64ee045fd98ea2be7a | UNDERPOWERED |
| sspec_615957e589b327ad9c219a0e | trade_date_block_bootstrap | 10855 | BLOCKED | False | True | surrun_e1c01477b44b8a4f400de0fb | UNDERPOWERED |
| sspec_615957e589b327ad9c219a0e | trade_date_block_bootstrap | 10856 | BLOCKED | False | True | surrun_b21cdc3ac6c85705ded90a39 | UNDERPOWERED |
| sspec_575988f1b3a222120b8ad483 | trade_date_block_bootstrap | 10857 | BLOCKED | False | True | surrun_70c17b59b1649ef2620cc4f0 | UNDERPOWERED |
| sspec_575988f1b3a222120b8ad483 | trade_date_block_bootstrap | 10858 | BLOCKED | False | True | surrun_10d6c2fdc7fbc966bc54e1bf | UNDERPOWERED |
| sspec_575988f1b3a222120b8ad483 | trade_date_block_bootstrap | 10859 | BLOCKED | False | True | surrun_24f7d19edc295f5211ebd0a1 | UNDERPOWERED |
| sspec_c850eb8de037fdd42d6d9bd1 | trade_date_block_bootstrap | 10860 | BLOCKED | False | True | surrun_f89937b9768468a83f694186 | UNDERPOWERED |
| sspec_c850eb8de037fdd42d6d9bd1 | trade_date_block_bootstrap | 10861 | BLOCKED | False | True | surrun_44c17e333c78ee0f004f9e4a | UNDERPOWERED |
| sspec_c850eb8de037fdd42d6d9bd1 | trade_date_block_bootstrap | 10862 | BLOCKED | False | True | surrun_6c9c4f3efa2eafc0299d8f55 | UNDERPOWERED |
| sspec_ac8ffcd655f016d13f7639d1 | trade_date_block_bootstrap | 10863 | BLOCKED | False | True | surrun_353109caa7d16b5357dae973 | UNDERPOWERED |
| sspec_ac8ffcd655f016d13f7639d1 | trade_date_block_bootstrap | 10864 | BLOCKED | False | True | surrun_a8cf3f65fe3dab8bd402852c | UNDERPOWERED |
| sspec_ac8ffcd655f016d13f7639d1 | trade_date_block_bootstrap | 10865 | BLOCKED | False | True | surrun_1ec0d441200a95ae90f03069 | UNDERPOWERED |
| sspec_417d40d5149c0952f4d6b237 | trade_date_block_bootstrap | 10866 | BLOCKED | False | True | surrun_77ffb47d011cdba0a840ef5b | UNDERPOWERED |
| sspec_417d40d5149c0952f4d6b237 | trade_date_block_bootstrap | 10867 | BLOCKED | False | True | surrun_789331dd2908b5d9fe5338aa | UNDERPOWERED |
| sspec_417d40d5149c0952f4d6b237 | trade_date_block_bootstrap | 10868 | BLOCKED | False | True | surrun_7b367d994145811ea67c1256 | UNDERPOWERED |
| sspec_4c04b3d54a8eba6e4eda6442 | trade_date_block_bootstrap | 10869 | BLOCKED | False | True | surrun_fc5de9ff6fa94a903f361949 | UNDERPOWERED |
| sspec_4c04b3d54a8eba6e4eda6442 | trade_date_block_bootstrap | 10870 | BLOCKED | False | True | surrun_7987d661c96af337e4eb479e | UNDERPOWERED |
| sspec_4c04b3d54a8eba6e4eda6442 | trade_date_block_bootstrap | 10871 | BLOCKED | False | True | surrun_c30e66ab73a283e40a4bd0eb | UNDERPOWERED |
| sspec_8cfbe34372d380ea293c6180 | trade_date_block_bootstrap | 10872 | BLOCKED | False | True | surrun_0c0f37d02a0dbcb075f94898 | UNDERPOWERED |
| sspec_8cfbe34372d380ea293c6180 | trade_date_block_bootstrap | 10873 | BLOCKED | False | True | surrun_e0aadcca230891cae973d111 | UNDERPOWERED |
| sspec_8cfbe34372d380ea293c6180 | trade_date_block_bootstrap | 10874 | BLOCKED | False | True | surrun_2bb1f9b79b3050d21bf8b6c3 | UNDERPOWERED |
| sspec_33e6978062420536604b589f | trade_date_block_bootstrap | 10875 | BLOCKED | False | True | surrun_8a2cf6b330b2b2665f0e3e17 | UNDERPOWERED |
| sspec_33e6978062420536604b589f | trade_date_block_bootstrap | 10876 | BLOCKED | False | True | surrun_a6b3750666bac4749b7be09c | UNDERPOWERED |
| sspec_33e6978062420536604b589f | trade_date_block_bootstrap | 10877 | BLOCKED | False | True | surrun_c16b2bdad388225dac66b633 | UNDERPOWERED |
| sspec_39aa4e0ad7853e043ef650c5 | trade_date_block_bootstrap | 10878 | BLOCKED | False | True | surrun_65e26592761207209af59a3a | UNDERPOWERED |
| sspec_39aa4e0ad7853e043ef650c5 | trade_date_block_bootstrap | 10879 | BLOCKED | False | True | surrun_7bae474051c0ea5258456579 | UNDERPOWERED |
| sspec_39aa4e0ad7853e043ef650c5 | trade_date_block_bootstrap | 10880 | BLOCKED | False | True | surrun_6d81b09cfe28bfbf37b97ea9 | UNDERPOWERED |
| sspec_9f2098ad4b76e48651eb98fc | trade_date_block_bootstrap | 10881 | BLOCKED | False | True | surrun_4bf946596bfd9b1c4d2d35a0 | UNDERPOWERED |
| sspec_9f2098ad4b76e48651eb98fc | trade_date_block_bootstrap | 10882 | BLOCKED | False | True | surrun_89c873b1b5234766c07591e1 | UNDERPOWERED |
| sspec_9f2098ad4b76e48651eb98fc | trade_date_block_bootstrap | 10883 | BLOCKED | False | True | surrun_b7a3658f0a54dcd65f637b8f | UNDERPOWERED |
| sspec_af6bfd804bff3b2a11043f54 | trade_date_block_bootstrap | 10884 | BLOCKED | False | True | surrun_9c4b0016b5480b432eadcef8 | UNDERPOWERED |
| sspec_af6bfd804bff3b2a11043f54 | trade_date_block_bootstrap | 10885 | BLOCKED | False | True | surrun_199a3af7583f3a5b385e5425 | UNDERPOWERED |
| sspec_af6bfd804bff3b2a11043f54 | trade_date_block_bootstrap | 10886 | BLOCKED | False | True | surrun_dfb9e9b517959da93cb7c57f | UNDERPOWERED |
| sspec_a593dbc474b2e81188e14a04 | trade_date_block_bootstrap | 10887 | BLOCKED | False | True | surrun_d25eaa63560734a092a72a2c | UNDERPOWERED |
| sspec_a593dbc474b2e81188e14a04 | trade_date_block_bootstrap | 10888 | BLOCKED | False | True | surrun_9cf60e59e53fd98ad4d15d85 | UNDERPOWERED |
| sspec_a593dbc474b2e81188e14a04 | trade_date_block_bootstrap | 10889 | BLOCKED | False | True | surrun_b5ec5cd9f3fd05daa71608e7 | UNDERPOWERED |
| sspec_420d57a91dacb91c9ad406e1 | trade_date_block_bootstrap | 10890 | BLOCKED | False | True | surrun_4ad6353baf8a8fffb98abfd8 | UNDERPOWERED |
| sspec_420d57a91dacb91c9ad406e1 | trade_date_block_bootstrap | 10891 | BLOCKED | False | True | surrun_05f827a222506ea55da74d11 | UNDERPOWERED |
| sspec_420d57a91dacb91c9ad406e1 | trade_date_block_bootstrap | 10892 | BLOCKED | False | True | surrun_f55e6ee1b78f4de5d96f4673 | UNDERPOWERED |
| sspec_0ae0a2c8a5072f41b9586423 | trade_date_block_bootstrap | 10893 | BLOCKED | False | True | surrun_55c9df0af8f79fff85199a4a | UNDERPOWERED |
| sspec_0ae0a2c8a5072f41b9586423 | trade_date_block_bootstrap | 10894 | BLOCKED | False | True | surrun_a1e6bd4f917e460ab122bdba | UNDERPOWERED |
| sspec_0ae0a2c8a5072f41b9586423 | trade_date_block_bootstrap | 10895 | BLOCKED | False | True | surrun_1d0e520ab3016ee9e30cf7cc | UNDERPOWERED |
| sspec_5009501499364fe94e7207ea | trade_date_block_bootstrap | 10896 | BLOCKED | False | True | surrun_7c35cfb1257ff19afbb96882 | UNDERPOWERED |
| sspec_5009501499364fe94e7207ea | trade_date_block_bootstrap | 10897 | BLOCKED | False | True | surrun_b875883c3897aa2dad0dbb6c | UNDERPOWERED |
| sspec_5009501499364fe94e7207ea | trade_date_block_bootstrap | 10898 | BLOCKED | False | True | surrun_8feba8c8cee59e138ec2514a | UNDERPOWERED |
| sspec_b2c643ab396aa79e06278f1b | trade_date_block_bootstrap | 10899 | BLOCKED | False | True | surrun_c29def0cbf13f7bbdfcfd481 | UNDERPOWERED |
| sspec_b2c643ab396aa79e06278f1b | trade_date_block_bootstrap | 10900 | BLOCKED | False | True | surrun_a9d0a45553951c2923482624 | UNDERPOWERED |
| sspec_b2c643ab396aa79e06278f1b | trade_date_block_bootstrap | 10901 | BLOCKED | False | True | surrun_2564d627ec092f9f373740b3 | UNDERPOWERED |
| sspec_daca54b0be689e1553a605e0 | trade_date_block_bootstrap | 10902 | BLOCKED | False | True | surrun_a810be8bcf5fc05518827540 | UNDERPOWERED |
| sspec_daca54b0be689e1553a605e0 | trade_date_block_bootstrap | 10903 | BLOCKED | False | True | surrun_1d7b97773acc8d9330d98934 | UNDERPOWERED |
| sspec_daca54b0be689e1553a605e0 | trade_date_block_bootstrap | 10904 | BLOCKED | False | True | surrun_3277b916f96fb2c984dbab35 | UNDERPOWERED |
| sspec_cd094fc62c80c70ed9be7778 | trade_date_block_bootstrap | 10905 | BLOCKED | False | True | surrun_aad646a8a09d29726fb25a60 | UNDERPOWERED |
| sspec_cd094fc62c80c70ed9be7778 | trade_date_block_bootstrap | 10906 | BLOCKED | False | True | surrun_244edbc9856dc1123057e239 | UNDERPOWERED |
| sspec_cd094fc62c80c70ed9be7778 | trade_date_block_bootstrap | 10907 | BLOCKED | False | True | surrun_05ddf205a066d9a2037cce14 | UNDERPOWERED |
| sspec_e4de6c01c8194505f5b42faa | trade_date_block_bootstrap | 10908 | BLOCKED | False | True | surrun_816a7bee325c79d42d61eaf5 | UNDERPOWERED |
| sspec_e4de6c01c8194505f5b42faa | trade_date_block_bootstrap | 10909 | BLOCKED | False | True | surrun_236851d7edbfdd70660ac235 | UNDERPOWERED |
| sspec_e4de6c01c8194505f5b42faa | trade_date_block_bootstrap | 10910 | BLOCKED | False | True | surrun_0a615ab64d510c7788453a47 | UNDERPOWERED |
| sspec_07a3d409ac7142f1af3c95dc | trade_date_block_bootstrap | 10911 | BLOCKED | False | True | surrun_363e6d8cbc23d5e7ab06a3f9 | UNDERPOWERED |
| sspec_07a3d409ac7142f1af3c95dc | trade_date_block_bootstrap | 10912 | BLOCKED | False | True | surrun_239c784909c23e2e12907386 | UNDERPOWERED |
| sspec_07a3d409ac7142f1af3c95dc | trade_date_block_bootstrap | 10913 | BLOCKED | False | True | surrun_3d96892975f34a40f20da209 | UNDERPOWERED |
| sspec_1d6835a599361698f2b73809 | trade_date_block_bootstrap | 10914 | BLOCKED | False | True | surrun_47d13ca29cab5a47af77f69f | UNDERPOWERED |
| sspec_1d6835a599361698f2b73809 | trade_date_block_bootstrap | 10915 | BLOCKED | False | True | surrun_2636c75d2241a6b17805793e | UNDERPOWERED |
| sspec_1d6835a599361698f2b73809 | trade_date_block_bootstrap | 10916 | BLOCKED | False | True | surrun_0c98873b24fc7cb9324bb112 | UNDERPOWERED |
| sspec_e79a366792fb3bb2fa9ebe97 | trade_date_block_bootstrap | 10917 | BLOCKED | False | True | surrun_3c9dd3d08d1378f78b9fb2f9 | UNDERPOWERED |
| sspec_e79a366792fb3bb2fa9ebe97 | trade_date_block_bootstrap | 10918 | BLOCKED | False | True | surrun_c8afba6e73b531e8a1bfee36 | UNDERPOWERED |
| sspec_e79a366792fb3bb2fa9ebe97 | trade_date_block_bootstrap | 10919 | BLOCKED | False | True | surrun_6b59c96a246414f2b1f1e6cc | UNDERPOWERED |
| sspec_ac0401f29a4f9684119b2910 | trade_date_block_bootstrap | 10920 | BLOCKED | False | True | surrun_031bd09d6611c4271b481d5d | UNDERPOWERED |
| sspec_ac0401f29a4f9684119b2910 | trade_date_block_bootstrap | 10921 | BLOCKED | False | True | surrun_65c591c6f665b7a48bd679e7 | UNDERPOWERED |
| sspec_ac0401f29a4f9684119b2910 | trade_date_block_bootstrap | 10922 | BLOCKED | False | True | surrun_d70625cbf374e2f2a92a0b46 | UNDERPOWERED |
| sspec_9facdedd053634452d17f373 | trade_date_block_bootstrap | 10923 | BLOCKED | False | True | surrun_fa6d483a2b13380d2d2a15e6 | UNDERPOWERED |
| sspec_9facdedd053634452d17f373 | trade_date_block_bootstrap | 10924 | BLOCKED | False | True | surrun_0481d8bfbb888ec2348cde24 | UNDERPOWERED |
| sspec_9facdedd053634452d17f373 | trade_date_block_bootstrap | 10925 | BLOCKED | False | True | surrun_bb6ea20259bd0fa840ee27c1 | UNDERPOWERED |
| sspec_23341861e5b3b2389b1f1fc4 | trade_date_block_bootstrap | 10926 | BLOCKED | False | True | surrun_f13cd6c599b2a6c41e453243 | UNDERPOWERED |
| sspec_23341861e5b3b2389b1f1fc4 | trade_date_block_bootstrap | 10927 | BLOCKED | False | True | surrun_dd76f3cbdbd272846e97173a | UNDERPOWERED |
| sspec_23341861e5b3b2389b1f1fc4 | trade_date_block_bootstrap | 10928 | BLOCKED | False | True | surrun_78ec151246efc795400808a1 | UNDERPOWERED |
| sspec_1e0f13d7ec8645f8496d6d84 | trade_date_block_bootstrap | 10929 | BLOCKED | False | True | surrun_bae37d37dc36f6225b518926 | UNDERPOWERED |
| sspec_1e0f13d7ec8645f8496d6d84 | trade_date_block_bootstrap | 10930 | BLOCKED | False | True | surrun_12203187be5088746bd5a0d6 | UNDERPOWERED |
| sspec_1e0f13d7ec8645f8496d6d84 | trade_date_block_bootstrap | 10931 | BLOCKED | False | True | surrun_dee1c1c0c19a41588094c9c3 | UNDERPOWERED |
| sspec_591b6b5d749f72821cb96b7e | trade_date_block_bootstrap | 10932 | BLOCKED | False | True | surrun_35ef708ae7600587a0619808 | UNDERPOWERED |
| sspec_591b6b5d749f72821cb96b7e | trade_date_block_bootstrap | 10933 | BLOCKED | False | True | surrun_a7db8603bc1fba23c1600d6e | UNDERPOWERED |
| sspec_591b6b5d749f72821cb96b7e | trade_date_block_bootstrap | 10934 | BLOCKED | False | True | surrun_9ade73d6ebd1870033c1c38c | UNDERPOWERED |
| sspec_59e66484f4bb184d90bf3898 | trade_date_block_bootstrap | 10935 | BLOCKED | False | True | surrun_1d7c9eafda6f829039d61aee | UNDERPOWERED |
| sspec_59e66484f4bb184d90bf3898 | trade_date_block_bootstrap | 10936 | BLOCKED | False | True | surrun_89c0e5b8ec64815aa52304fc | UNDERPOWERED |
| sspec_59e66484f4bb184d90bf3898 | trade_date_block_bootstrap | 10937 | BLOCKED | False | True | surrun_af26c117c2276e991373e273 | UNDERPOWERED |
| sspec_d786109ea94d49258684c7e6 | trade_date_block_bootstrap | 10938 | BLOCKED | False | True | surrun_618195deb9937656eb441317 | UNDERPOWERED |
| sspec_d786109ea94d49258684c7e6 | trade_date_block_bootstrap | 10939 | BLOCKED | False | True | surrun_8e260c2de9591c7fb2390cac | UNDERPOWERED |
| sspec_d786109ea94d49258684c7e6 | trade_date_block_bootstrap | 10940 | BLOCKED | False | True | surrun_ebafab211b3bb735a146ab05 | UNDERPOWERED |
| sspec_bfb335e68a4e1c8420e18daf | trade_date_block_bootstrap | 10941 | BLOCKED | False | True | surrun_ce0d76e45768d5147d0d0794 | UNDERPOWERED |
| sspec_bfb335e68a4e1c8420e18daf | trade_date_block_bootstrap | 10942 | BLOCKED | False | True | surrun_7b9b4d96a48274402e6b0194 | UNDERPOWERED |
| sspec_bfb335e68a4e1c8420e18daf | trade_date_block_bootstrap | 10943 | BLOCKED | False | True | surrun_400b2aaefeae60b2fd10aae6 | UNDERPOWERED |
| sspec_b9b84430f273e368089a1c68 | trade_date_block_bootstrap | 10944 | BLOCKED | False | True | surrun_480e9fce777793df0f298448 | UNDERPOWERED |
| sspec_b9b84430f273e368089a1c68 | trade_date_block_bootstrap | 10945 | BLOCKED | False | True | surrun_d01d430ce43d99624095c413 | UNDERPOWERED |
| sspec_b9b84430f273e368089a1c68 | trade_date_block_bootstrap | 10946 | BLOCKED | False | True | surrun_5e32341e297ed1b2f86df918 | UNDERPOWERED |
| sspec_06b2dafa18a5e2f1bf59857a | trade_date_block_bootstrap | 10947 | BLOCKED | False | True | surrun_0226aa813befd810ea00bcaa | UNDERPOWERED |
| sspec_06b2dafa18a5e2f1bf59857a | trade_date_block_bootstrap | 10948 | BLOCKED | False | True | surrun_7b92d2803a16fab88e7c4bca | UNDERPOWERED |
| sspec_06b2dafa18a5e2f1bf59857a | trade_date_block_bootstrap | 10949 | BLOCKED | False | True | surrun_be3abbd9a148ef12307cd605 | UNDERPOWERED |
| sspec_f51256c420e3f4c5d4efe3cd | trade_date_block_bootstrap | 10950 | BLOCKED | False | True | surrun_6dd0f3e225122938b6fbbcb8 | UNDERPOWERED |
| sspec_f51256c420e3f4c5d4efe3cd | trade_date_block_bootstrap | 10951 | BLOCKED | False | True | surrun_935483cdec34aa111cca0e50 | UNDERPOWERED |
| sspec_f51256c420e3f4c5d4efe3cd | trade_date_block_bootstrap | 10952 | BLOCKED | False | True | surrun_28f60017351cf1f715dbb956 | UNDERPOWERED |
| sspec_04700db185f0c6daad6cb3c2 | trade_date_block_bootstrap | 10953 | BLOCKED | False | True | surrun_071305fa62c3042705ac549c | UNDERPOWERED |
| sspec_04700db185f0c6daad6cb3c2 | trade_date_block_bootstrap | 10954 | BLOCKED | False | True | surrun_474eeca79e0b83e5319f58d9 | UNDERPOWERED |
| sspec_04700db185f0c6daad6cb3c2 | trade_date_block_bootstrap | 10955 | BLOCKED | False | True | surrun_0ccd6bc1b09a3e3da6df517e | UNDERPOWERED |
| sspec_a4078255986f31a6098cade6 | trade_date_block_bootstrap | 10956 | BLOCKED | False | True | surrun_e551f599564248d4068cd262 | UNDERPOWERED |
| sspec_a4078255986f31a6098cade6 | trade_date_block_bootstrap | 10957 | BLOCKED | False | True | surrun_f543ffc3357a658e0acd7371 | UNDERPOWERED |
| sspec_a4078255986f31a6098cade6 | trade_date_block_bootstrap | 10958 | BLOCKED | False | True | surrun_af73dd5e96ba46768b70694c | UNDERPOWERED |
| sspec_c7d1edcfbe2dc633b7019e51 | trade_date_block_bootstrap | 10959 | BLOCKED | False | True | surrun_c0eecb72b15a1b05ebc1ae66 | UNDERPOWERED |
| sspec_c7d1edcfbe2dc633b7019e51 | trade_date_block_bootstrap | 10960 | BLOCKED | False | True | surrun_1362596e1abc0a4e6c3c0c2d | UNDERPOWERED |
| sspec_c7d1edcfbe2dc633b7019e51 | trade_date_block_bootstrap | 10961 | BLOCKED | False | True | surrun_f53f236299bf5da6b6dbf742 | UNDERPOWERED |
| sspec_307dde451cbbad8eec5af21b | trade_date_block_bootstrap | 10962 | BLOCKED | False | True | surrun_83e5f9d64a85630378ab13b2 | UNDERPOWERED |
| sspec_307dde451cbbad8eec5af21b | trade_date_block_bootstrap | 10963 | BLOCKED | False | True | surrun_7267e283bbc2cdc7652a96fd | UNDERPOWERED |
| sspec_307dde451cbbad8eec5af21b | trade_date_block_bootstrap | 10964 | BLOCKED | False | True | surrun_ecab06c8951d82f76fa718f4 | UNDERPOWERED |
| sspec_a12d8aa54c9448e28c59dc1a | trade_date_block_bootstrap | 10965 | BLOCKED | False | True | surrun_ad06b0b8ff32b7b7d642ca55 | UNDERPOWERED |
| sspec_a12d8aa54c9448e28c59dc1a | trade_date_block_bootstrap | 10966 | BLOCKED | False | True | surrun_08fcaad62d96ef21fe237f7e | UNDERPOWERED |
| sspec_a12d8aa54c9448e28c59dc1a | trade_date_block_bootstrap | 10967 | BLOCKED | False | True | surrun_b92cd57c31e86df1251c89d3 | UNDERPOWERED |
| sspec_7193d2d27a54308e250de2c9 | trade_date_block_bootstrap | 10968 | BLOCKED | False | True | surrun_ecad229030e3f6e76f4aca38 | UNDERPOWERED |
| sspec_7193d2d27a54308e250de2c9 | trade_date_block_bootstrap | 10969 | BLOCKED | False | True | surrun_8c35c8a6184bc37e56218006 | UNDERPOWERED |
| sspec_7193d2d27a54308e250de2c9 | trade_date_block_bootstrap | 10970 | BLOCKED | False | True | surrun_d3d0d6e39efcfb6fddfc24bd | UNDERPOWERED |
| sspec_bd962a893b60363f33d88d25 | trade_date_block_bootstrap | 10971 | BLOCKED | False | True | surrun_8d0908505e7951cb00b2d878 | UNDERPOWERED |
| sspec_bd962a893b60363f33d88d25 | trade_date_block_bootstrap | 10972 | BLOCKED | False | True | surrun_4b56fac4faf73e7c2987cc19 | UNDERPOWERED |
| sspec_bd962a893b60363f33d88d25 | trade_date_block_bootstrap | 10973 | BLOCKED | False | True | surrun_e3ab0be7f3efd570f627d12a | UNDERPOWERED |
| sspec_47a1c2aa87504926b01084c7 | trade_date_block_bootstrap | 10974 | BLOCKED | False | True | surrun_f841cd04c2334ec2a8f63d87 | UNDERPOWERED |
| sspec_47a1c2aa87504926b01084c7 | trade_date_block_bootstrap | 10975 | BLOCKED | False | True | surrun_48264c01e8d524baf3b080ed | UNDERPOWERED |
| sspec_47a1c2aa87504926b01084c7 | trade_date_block_bootstrap | 10976 | BLOCKED | False | True | surrun_29ac46089d5d1c39e1cdf352 | UNDERPOWERED |
| sspec_64f050bdf662b01329d2c031 | trade_date_block_bootstrap | 10977 | BLOCKED | False | True | surrun_2a9aa4e08e49b391bb54809b | UNDERPOWERED |
| sspec_64f050bdf662b01329d2c031 | trade_date_block_bootstrap | 10978 | BLOCKED | False | True | surrun_bf40cdf1570ac7813d2f0e71 | UNDERPOWERED |
| sspec_64f050bdf662b01329d2c031 | trade_date_block_bootstrap | 10979 | BLOCKED | False | True | surrun_4da27e5d530ff9a8d5ddf6cc | UNDERPOWERED |
| sspec_12f70e2e5ce5c1257b485c40 | trade_date_block_bootstrap | 10980 | BLOCKED | False | True | surrun_a7aff32995e4c11ff7a09ec4 | UNDERPOWERED |
| sspec_12f70e2e5ce5c1257b485c40 | trade_date_block_bootstrap | 10981 | BLOCKED | False | True | surrun_dbab5f253504759d81b69f9b | UNDERPOWERED |
| sspec_12f70e2e5ce5c1257b485c40 | trade_date_block_bootstrap | 10982 | BLOCKED | False | True | surrun_6e50b23a315eff9a0ee114b5 | UNDERPOWERED |
| sspec_8e3ab2a35800038d67f3a309 | trade_date_block_bootstrap | 10983 | BLOCKED | False | True | surrun_02bb1a6fe82cedb02e6836ce | UNDERPOWERED |
| sspec_8e3ab2a35800038d67f3a309 | trade_date_block_bootstrap | 10984 | BLOCKED | False | True | surrun_88c05769316dbb7331b26be2 | UNDERPOWERED |
| sspec_8e3ab2a35800038d67f3a309 | trade_date_block_bootstrap | 10985 | BLOCKED | False | True | surrun_5264ab04bc86ae7daf7c67d2 | UNDERPOWERED |
| sspec_7ab597d4b06cdfb3eff89b47 | trade_date_block_bootstrap | 10986 | BLOCKED | False | True | surrun_86506f8ab4f7ae558e7ebde4 | UNDERPOWERED |
| sspec_7ab597d4b06cdfb3eff89b47 | trade_date_block_bootstrap | 10987 | BLOCKED | False | True | surrun_c2f60d2032e5c5d4497edd87 | UNDERPOWERED |
| sspec_7ab597d4b06cdfb3eff89b47 | trade_date_block_bootstrap | 10988 | BLOCKED | False | True | surrun_9f0a5acb53eb7340e1dfd1d1 | UNDERPOWERED |
| sspec_2e6d829119d863c0ea676fad | trade_date_block_bootstrap | 10989 | BLOCKED | False | True | surrun_5569675212f26aa1ee0e450a | UNDERPOWERED |
| sspec_2e6d829119d863c0ea676fad | trade_date_block_bootstrap | 10990 | BLOCKED | False | True | surrun_913edcf169d0e6a8bcd402b9 | UNDERPOWERED |
| sspec_2e6d829119d863c0ea676fad | trade_date_block_bootstrap | 10991 | BLOCKED | False | True | surrun_a1dc71d3ff40a571e189ecdd | UNDERPOWERED |
| sspec_2fdc71ed9e0d2f4c54fadb7f | trade_date_block_bootstrap | 10992 | BLOCKED | False | True | surrun_4f5970d0f2929a3413aa51fb | UNDERPOWERED |
| sspec_2fdc71ed9e0d2f4c54fadb7f | trade_date_block_bootstrap | 10993 | BLOCKED | False | True | surrun_6d75065444105282b1aadb3a | UNDERPOWERED |
| sspec_2fdc71ed9e0d2f4c54fadb7f | trade_date_block_bootstrap | 10994 | BLOCKED | False | True | surrun_5364a8fe11b8587b99379ebe | UNDERPOWERED |
| sspec_26a958b1758bf3ba7740286a | trade_date_block_bootstrap | 10995 | BLOCKED | False | True | surrun_15bc9ac99b728f9dd8cb8feb | UNDERPOWERED |
| sspec_26a958b1758bf3ba7740286a | trade_date_block_bootstrap | 10996 | BLOCKED | False | True | surrun_703785975abe9843b3c9508f | UNDERPOWERED |
| sspec_26a958b1758bf3ba7740286a | trade_date_block_bootstrap | 10997 | BLOCKED | False | True | surrun_b269944531c341748001b818 | UNDERPOWERED |
| sspec_6a674d0b92a02a4da79178da | trade_date_block_bootstrap | 10998 | BLOCKED | False | True | surrun_61d30699744f8b905171c4bc | UNDERPOWERED |
| sspec_6a674d0b92a02a4da79178da | trade_date_block_bootstrap | 10999 | BLOCKED | False | True | surrun_cc1bcfe73d38fc89d17aa862 | UNDERPOWERED |
| sspec_6a674d0b92a02a4da79178da | trade_date_block_bootstrap | 11000 | BLOCKED | False | True | surrun_fbbc7d45af91e0e198337b9e | UNDERPOWERED |
| sspec_02d4c2d8fd2c64493f2cfcf1 | trade_date_block_bootstrap | 11001 | BLOCKED | False | True | surrun_b2f052c4df58ec308ad5903a | UNDERPOWERED |
| sspec_02d4c2d8fd2c64493f2cfcf1 | trade_date_block_bootstrap | 11002 | BLOCKED | False | True | surrun_6daaa7f545c455489015b623 | UNDERPOWERED |
| sspec_02d4c2d8fd2c64493f2cfcf1 | trade_date_block_bootstrap | 11003 | BLOCKED | False | True | surrun_498b3629a22d2fff1e19b89a | UNDERPOWERED |
| sspec_d0ae270919495c98929455ab | trade_date_block_bootstrap | 11004 | BLOCKED | False | True | surrun_c3a62d39c2561f89cd458df0 | UNDERPOWERED |
| sspec_d0ae270919495c98929455ab | trade_date_block_bootstrap | 11005 | BLOCKED | False | True | surrun_b532f1f240401abb03663251 | UNDERPOWERED |
| sspec_d0ae270919495c98929455ab | trade_date_block_bootstrap | 11006 | BLOCKED | False | True | surrun_f8d55c5b0dfef9b5d9985682 | UNDERPOWERED |
| sspec_4ec8fddb8af0145752fc7ca3 | trade_date_block_bootstrap | 11007 | BLOCKED | False | True | surrun_805f26f2a50d044c5c83d220 | UNDERPOWERED |
| sspec_4ec8fddb8af0145752fc7ca3 | trade_date_block_bootstrap | 11008 | BLOCKED | False | True | surrun_92bdc1ab8dbd67648527297a | UNDERPOWERED |
| sspec_4ec8fddb8af0145752fc7ca3 | trade_date_block_bootstrap | 11009 | BLOCKED | False | True | surrun_c04a787ce2545b16e96929d3 | UNDERPOWERED |
| sspec_009090848943c0de95a47341 | trade_date_block_bootstrap | 11010 | BLOCKED | False | True | surrun_e814ed3aa45e24bc13e280f5 | UNDERPOWERED |
| sspec_009090848943c0de95a47341 | trade_date_block_bootstrap | 11011 | BLOCKED | False | True | surrun_ce2c23c3f403656bac78c9fd | UNDERPOWERED |
| sspec_009090848943c0de95a47341 | trade_date_block_bootstrap | 11012 | BLOCKED | False | True | surrun_995aa85e1197e7bc6a76178f | UNDERPOWERED |
| sspec_5e4046c2eb6f28e0f5371613 | trade_date_block_bootstrap | 11013 | BLOCKED | False | True | surrun_966e8666e440dd52b580ef1f | UNDERPOWERED |
| sspec_5e4046c2eb6f28e0f5371613 | trade_date_block_bootstrap | 11014 | BLOCKED | False | True | surrun_62de5a98f5032fa9786a85fa | UNDERPOWERED |
| sspec_5e4046c2eb6f28e0f5371613 | trade_date_block_bootstrap | 11015 | BLOCKED | False | True | surrun_e7ffad8a0cf7feb456061e26 | UNDERPOWERED |
| sspec_f218192064c3697829ae5ae7 | trade_date_block_bootstrap | 11016 | BLOCKED | False | True | surrun_2f6884848ec19fda0ba3e37e | UNDERPOWERED |
| sspec_f218192064c3697829ae5ae7 | trade_date_block_bootstrap | 11017 | BLOCKED | False | True | surrun_d56b36d520fa036cde386aa4 | UNDERPOWERED |
| sspec_f218192064c3697829ae5ae7 | trade_date_block_bootstrap | 11018 | BLOCKED | False | True | surrun_6e803880b151ca78bdbbd8bb | UNDERPOWERED |
| sspec_e3a5a2018e3b6e5bbc811569 | trade_date_block_bootstrap | 11019 | BLOCKED | False | True | surrun_ae4c4b11c85728cafe0776e4 | UNDERPOWERED |
| sspec_e3a5a2018e3b6e5bbc811569 | trade_date_block_bootstrap | 11020 | BLOCKED | False | True | surrun_7633ee6d2b52c3dd0a96d80f | UNDERPOWERED |
| sspec_e3a5a2018e3b6e5bbc811569 | trade_date_block_bootstrap | 11021 | BLOCKED | False | True | surrun_a66004bd32a2751436f700ae | UNDERPOWERED |
| sspec_5ce1327071aea3730850cc90 | trade_date_block_bootstrap | 11022 | BLOCKED | False | True | surrun_647051767a950b2bf80202d4 | UNDERPOWERED |
| sspec_5ce1327071aea3730850cc90 | trade_date_block_bootstrap | 11023 | BLOCKED | False | True | surrun_05439a22732216214a4b0008 | UNDERPOWERED |
| sspec_5ce1327071aea3730850cc90 | trade_date_block_bootstrap | 11024 | BLOCKED | False | True | surrun_860a332964453c06bb02d0e1 | UNDERPOWERED |
| sspec_cb2f0cb548f47610400c0246 | trade_date_block_bootstrap | 11025 | BLOCKED | False | True | surrun_b3d9f12815a7d86d63eeaf2f | UNDERPOWERED |
| sspec_cb2f0cb548f47610400c0246 | trade_date_block_bootstrap | 11026 | BLOCKED | False | True | surrun_ab78f22033be3b1703bc6417 | UNDERPOWERED |
| sspec_cb2f0cb548f47610400c0246 | trade_date_block_bootstrap | 11027 | BLOCKED | False | True | surrun_54deee11493a793007bb45f2 | UNDERPOWERED |
| sspec_60255b9607d91b315fa18998 | trade_date_block_bootstrap | 11028 | BLOCKED | False | True | surrun_37820f5f58ec06586ac445a5 | UNDERPOWERED |
| sspec_60255b9607d91b315fa18998 | trade_date_block_bootstrap | 11029 | BLOCKED | False | True | surrun_2f2f3612971fbd5af9542b90 | UNDERPOWERED |
| sspec_60255b9607d91b315fa18998 | trade_date_block_bootstrap | 11030 | BLOCKED | False | True | surrun_f6f234ef6aa4ec123124f10d | UNDERPOWERED |
| sspec_b90e5b137dbdc9cd50f11b6f | trade_date_block_bootstrap | 11031 | BLOCKED | False | True | surrun_da44d8d73436fba80fffa473 | UNDERPOWERED |
| sspec_b90e5b137dbdc9cd50f11b6f | trade_date_block_bootstrap | 11032 | BLOCKED | False | True | surrun_c38aafcc4614368b8cf87d05 | UNDERPOWERED |
| sspec_b90e5b137dbdc9cd50f11b6f | trade_date_block_bootstrap | 11033 | BLOCKED | False | True | surrun_e19f5670c51f78980284abc4 | UNDERPOWERED |
| sspec_f93cebb5da9ea1917e9bd437 | trade_date_block_bootstrap | 11034 | BLOCKED | False | True | surrun_5be69c5e4e9c51687b6bea69 | UNDERPOWERED |
| sspec_f93cebb5da9ea1917e9bd437 | trade_date_block_bootstrap | 11035 | BLOCKED | False | True | surrun_823f15e1e0a33dcdcc4d8490 | UNDERPOWERED |
| sspec_f93cebb5da9ea1917e9bd437 | trade_date_block_bootstrap | 11036 | BLOCKED | False | True | surrun_1954f62c4c397a59a02a32e6 | UNDERPOWERED |
| sspec_1312fb9e82b3a2c651d7aab6 | trade_date_block_bootstrap | 11037 | BLOCKED | False | True | surrun_71b4f8440c28f22384326681 | UNDERPOWERED |
| sspec_1312fb9e82b3a2c651d7aab6 | trade_date_block_bootstrap | 11038 | BLOCKED | False | True | surrun_fc0b7adfe5c59490f2791a4a | UNDERPOWERED |
| sspec_1312fb9e82b3a2c651d7aab6 | trade_date_block_bootstrap | 11039 | BLOCKED | False | True | surrun_e4b305aa2da06955cd1672a6 | UNDERPOWERED |
| sspec_e6eb9f2669d4c44c0b917529 | trade_date_block_bootstrap | 11040 | BLOCKED | False | True | surrun_c3afa001c5712f9289baff90 | UNDERPOWERED |
| sspec_e6eb9f2669d4c44c0b917529 | trade_date_block_bootstrap | 11041 | BLOCKED | False | True | surrun_1c85e80cd633dc03de87b083 | UNDERPOWERED |
| sspec_e6eb9f2669d4c44c0b917529 | trade_date_block_bootstrap | 11042 | BLOCKED | False | True | surrun_a4db66d89b842f7482e488ee | UNDERPOWERED |
| sspec_72abd692a99dd3745248b741 | trade_date_block_bootstrap | 11043 | BLOCKED | False | True | surrun_f85109786839e097dbca2716 | UNDERPOWERED |
| sspec_72abd692a99dd3745248b741 | trade_date_block_bootstrap | 11044 | BLOCKED | False | True | surrun_9f208146df9dce46349d8993 | UNDERPOWERED |
| sspec_72abd692a99dd3745248b741 | trade_date_block_bootstrap | 11045 | BLOCKED | False | True | surrun_472ed7e2589600fcb92c2049 | UNDERPOWERED |
| sspec_00627f348df014c2af1ba8bb | trade_date_block_bootstrap | 11046 | BLOCKED | False | True | surrun_73f79fed1e11518255b352fc | UNDERPOWERED |
| sspec_00627f348df014c2af1ba8bb | trade_date_block_bootstrap | 11047 | BLOCKED | False | True | surrun_4cddcfe34d59a203bf9f2e04 | UNDERPOWERED |
| sspec_00627f348df014c2af1ba8bb | trade_date_block_bootstrap | 11048 | BLOCKED | False | True | surrun_27b60a18596f63a009d78637 | UNDERPOWERED |
| sspec_9ab3b0dabedc16e1d1665eae | trade_date_block_bootstrap | 11049 | BLOCKED | False | True | surrun_8ee2ae459f66aafc8a00bbd7 | UNDERPOWERED |
| sspec_9ab3b0dabedc16e1d1665eae | trade_date_block_bootstrap | 11050 | BLOCKED | False | True | surrun_d5af80dc4d3d786d2977f2e6 | UNDERPOWERED |
| sspec_9ab3b0dabedc16e1d1665eae | trade_date_block_bootstrap | 11051 | BLOCKED | False | True | surrun_0512123483c319943e945523 | UNDERPOWERED |
| sspec_0970761026880cf10ffb959e | trade_date_block_bootstrap | 11052 | BLOCKED | False | True | surrun_ae37334d6c70fecb725b469d | UNDERPOWERED |
| sspec_0970761026880cf10ffb959e | trade_date_block_bootstrap | 11053 | BLOCKED | False | True | surrun_c5dfbda65e6153c8841c064e | UNDERPOWERED |
| sspec_0970761026880cf10ffb959e | trade_date_block_bootstrap | 11054 | BLOCKED | False | True | surrun_d01efdd2148485d4a6f24efc | UNDERPOWERED |
| sspec_2960375e303e1437425b86e1 | trade_date_block_bootstrap | 11055 | BLOCKED | False | True | surrun_84d77d62faa7be331b4066a9 | UNDERPOWERED |
| sspec_2960375e303e1437425b86e1 | trade_date_block_bootstrap | 11056 | BLOCKED | False | True | surrun_38c7d8d959ad3b29b428bc0f | UNDERPOWERED |
| sspec_2960375e303e1437425b86e1 | trade_date_block_bootstrap | 11057 | BLOCKED | False | True | surrun_a75be98ccf277e286269afae | UNDERPOWERED |
| sspec_06748cbab50a85b355c5a62b | trade_date_block_bootstrap | 11058 | BLOCKED | False | True | surrun_11de6d3ca4212f26411ea3bb | UNDERPOWERED |
| sspec_06748cbab50a85b355c5a62b | trade_date_block_bootstrap | 11059 | BLOCKED | False | True | surrun_59c36e50d771d0c4c79dd970 | UNDERPOWERED |
| sspec_06748cbab50a85b355c5a62b | trade_date_block_bootstrap | 11060 | BLOCKED | False | True | surrun_42435d62fa29910f0ac8fdcf | UNDERPOWERED |
| sspec_d6d2c7ca067491cf6ff5fe1a | trade_date_block_bootstrap | 11061 | BLOCKED | False | True | surrun_a5135fd77ba6899d091ba1cc | UNDERPOWERED |
| sspec_d6d2c7ca067491cf6ff5fe1a | trade_date_block_bootstrap | 11062 | BLOCKED | False | True | surrun_74bfb8d7ba6780813a8292a3 | UNDERPOWERED |
| sspec_d6d2c7ca067491cf6ff5fe1a | trade_date_block_bootstrap | 11063 | BLOCKED | False | True | surrun_7cf08dd65a03c2e9749262d2 | UNDERPOWERED |
| sspec_fe20b5938195485f7c61bdd3 | trade_date_block_bootstrap | 11064 | BLOCKED | False | True | surrun_71cbf1a426bf826a0167298d | UNDERPOWERED |
| sspec_fe20b5938195485f7c61bdd3 | trade_date_block_bootstrap | 11065 | BLOCKED | False | True | surrun_a5d1d246322497b41df28b5f | UNDERPOWERED |
| sspec_fe20b5938195485f7c61bdd3 | trade_date_block_bootstrap | 11066 | BLOCKED | False | True | surrun_26ca3cb74e513f751206c9a9 | UNDERPOWERED |
| sspec_a3d0e453d45a113ed040690d | trade_date_block_bootstrap | 11067 | BLOCKED | False | True | surrun_dcf8dadbef15e170a32e8e6d | UNDERPOWERED |
| sspec_a3d0e453d45a113ed040690d | trade_date_block_bootstrap | 11068 | BLOCKED | False | True | surrun_4627e641f1e6c9720b031de6 | UNDERPOWERED |
| sspec_a3d0e453d45a113ed040690d | trade_date_block_bootstrap | 11069 | BLOCKED | False | True | surrun_155140ec16042aa0ae8461f5 | UNDERPOWERED |
| sspec_79de468011b2905b326c7583 | trade_date_block_bootstrap | 11070 | BLOCKED | False | True | surrun_cffd2cd12324b87052761f2d | UNDERPOWERED |
| sspec_79de468011b2905b326c7583 | trade_date_block_bootstrap | 11071 | BLOCKED | False | True | surrun_26f486e7c98238d561411763 | UNDERPOWERED |
| sspec_79de468011b2905b326c7583 | trade_date_block_bootstrap | 11072 | BLOCKED | False | True | surrun_f7ad467d775c5bee7ac588e1 | UNDERPOWERED |
| sspec_827ce07b25d95a62679fea13 | trade_date_block_bootstrap | 11073 | BLOCKED | False | True | surrun_b2da9ede3946e12eb10c63d2 | UNDERPOWERED |
| sspec_827ce07b25d95a62679fea13 | trade_date_block_bootstrap | 11074 | BLOCKED | False | True | surrun_8ec1535f2995e8fd7bcc7ab9 | UNDERPOWERED |
| sspec_827ce07b25d95a62679fea13 | trade_date_block_bootstrap | 11075 | BLOCKED | False | True | surrun_3ee24e8e025522a97e2ad09f | UNDERPOWERED |
| sspec_0af6d7c90cc243f35b395d07 | trade_date_block_bootstrap | 11076 | BLOCKED | False | True | surrun_831c7d5681dd118e317ca3aa | UNDERPOWERED |
| sspec_0af6d7c90cc243f35b395d07 | trade_date_block_bootstrap | 11077 | BLOCKED | False | True | surrun_45e7167690d61ff2e4c4b6d6 | UNDERPOWERED |
| sspec_0af6d7c90cc243f35b395d07 | trade_date_block_bootstrap | 11078 | BLOCKED | False | True | surrun_9e2c766fa17140e0187ffad9 | UNDERPOWERED |
| sspec_8996fc26a21e74fd750567f4 | trade_date_block_bootstrap | 11079 | BLOCKED | False | True | surrun_f579c7a6a688436b9809d42f | UNDERPOWERED |
| sspec_8996fc26a21e74fd750567f4 | trade_date_block_bootstrap | 11080 | BLOCKED | False | True | surrun_f02aff7c491d558d58f454f2 | UNDERPOWERED |
| sspec_8996fc26a21e74fd750567f4 | trade_date_block_bootstrap | 11081 | BLOCKED | False | True | surrun_fbc535fcb9276cd25c54057d | UNDERPOWERED |
| sspec_4366258cb4ecd00e9c35fd4c | trade_date_block_bootstrap | 11082 | BLOCKED | False | True | surrun_8951760e3d7a1b1c5bd125de | UNDERPOWERED |
| sspec_4366258cb4ecd00e9c35fd4c | trade_date_block_bootstrap | 11083 | BLOCKED | False | True | surrun_58932ec5781d798c7925350c | UNDERPOWERED |
| sspec_4366258cb4ecd00e9c35fd4c | trade_date_block_bootstrap | 11084 | BLOCKED | False | True | surrun_09edd68e636521ba1a71a9b6 | UNDERPOWERED |
| sspec_639bdfb95714fb09e2ed4d6b | trade_date_block_bootstrap | 11085 | BLOCKED | False | True | surrun_edd075e375f3854b8ea15c86 | UNDERPOWERED |
| sspec_639bdfb95714fb09e2ed4d6b | trade_date_block_bootstrap | 11086 | BLOCKED | False | True | surrun_2fe258572cd001ea58b9b536 | UNDERPOWERED |
| sspec_639bdfb95714fb09e2ed4d6b | trade_date_block_bootstrap | 11087 | BLOCKED | False | True | surrun_75a0f465395b188d6f81ea5d | UNDERPOWERED |
| sspec_a78da21d358b646ce861e42e | trade_date_block_bootstrap | 11088 | BLOCKED | False | True | surrun_7f7dbbe5b89616834aa1791b | UNDERPOWERED |
| sspec_a78da21d358b646ce861e42e | trade_date_block_bootstrap | 11089 | BLOCKED | False | True | surrun_cd041972806d56518234f294 | UNDERPOWERED |
| sspec_a78da21d358b646ce861e42e | trade_date_block_bootstrap | 11090 | BLOCKED | False | True | surrun_c138fd45e9674592fc62ffd4 | UNDERPOWERED |
| sspec_16cc672b15138b0ddfc82b65 | trade_date_block_bootstrap | 11091 | BLOCKED | False | True | surrun_7e98b83d8c142604cfabfe16 | UNDERPOWERED |
| sspec_16cc672b15138b0ddfc82b65 | trade_date_block_bootstrap | 11092 | BLOCKED | False | True | surrun_271e429a542aff654100ddf8 | UNDERPOWERED |
| sspec_16cc672b15138b0ddfc82b65 | trade_date_block_bootstrap | 11093 | BLOCKED | False | True | surrun_5c55b96f9ad3522d4abb9835 | UNDERPOWERED |
| sspec_8e899c10d0e54a0096d9b8a9 | trade_date_block_bootstrap | 11094 | BLOCKED | False | True | surrun_002994fa8fd2811894887160 | UNDERPOWERED |
| sspec_8e899c10d0e54a0096d9b8a9 | trade_date_block_bootstrap | 11095 | BLOCKED | False | True | surrun_b5baf5dc0306fe0d22afb627 | UNDERPOWERED |
| sspec_8e899c10d0e54a0096d9b8a9 | trade_date_block_bootstrap | 11096 | BLOCKED | False | True | surrun_725ddf07ae5a5796ce5b1b32 | UNDERPOWERED |
| sspec_b57116d359e6ab5127347d1e | trade_date_block_bootstrap | 11097 | BLOCKED | False | True | surrun_3f8fa566772266748b3092c1 | UNDERPOWERED |
| sspec_b57116d359e6ab5127347d1e | trade_date_block_bootstrap | 11098 | BLOCKED | False | True | surrun_0dbe1bd4c0875e085c019fb2 | UNDERPOWERED |
| sspec_b57116d359e6ab5127347d1e | trade_date_block_bootstrap | 11099 | BLOCKED | False | True | surrun_b8f5eb5e0014340378833bc6 | UNDERPOWERED |
| sspec_95b6778754f0fdbce91e7612 | trade_date_block_bootstrap | 11100 | BLOCKED | False | True | surrun_b68ab711f1c902e55523a2fd | UNDERPOWERED |
| sspec_95b6778754f0fdbce91e7612 | trade_date_block_bootstrap | 11101 | BLOCKED | False | True | surrun_3af368035e998269261c6165 | UNDERPOWERED |
| sspec_95b6778754f0fdbce91e7612 | trade_date_block_bootstrap | 11102 | BLOCKED | False | True | surrun_a945774daeb7b8f249e965d1 | UNDERPOWERED |
| sspec_65871ccbf1b720b9adea6f02 | trade_date_block_bootstrap | 11103 | BLOCKED | False | True | surrun_11a0b2368407f9fd70a77ef7 | UNDERPOWERED |
| sspec_65871ccbf1b720b9adea6f02 | trade_date_block_bootstrap | 11104 | BLOCKED | False | True | surrun_32f8d436a38a62f05d80fba9 | UNDERPOWERED |
| sspec_65871ccbf1b720b9adea6f02 | trade_date_block_bootstrap | 11105 | BLOCKED | False | True | surrun_5d6846d9b72f1631cff5656f | UNDERPOWERED |
| sspec_038ec2aae72d221d1a4b978e | trade_date_block_bootstrap | 11106 | BLOCKED | False | True | surrun_f9ce16cc59cec917acd1080b | UNDERPOWERED |
| sspec_038ec2aae72d221d1a4b978e | trade_date_block_bootstrap | 11107 | BLOCKED | False | True | surrun_5cd95eabbf2bed948ae40202 | UNDERPOWERED |
| sspec_038ec2aae72d221d1a4b978e | trade_date_block_bootstrap | 11108 | BLOCKED | False | True | surrun_d1240c70a05c5472078d2656 | UNDERPOWERED |
| sspec_51427d9e9e56b14b1e2bd340 | trade_date_block_bootstrap | 11109 | BLOCKED | False | True | surrun_d38215738251f062dc75c4f7 | UNDERPOWERED |
| sspec_51427d9e9e56b14b1e2bd340 | trade_date_block_bootstrap | 11110 | BLOCKED | False | True | surrun_f3c5fae42de44230efc0ac01 | UNDERPOWERED |
| sspec_51427d9e9e56b14b1e2bd340 | trade_date_block_bootstrap | 11111 | BLOCKED | False | True | surrun_2ffb7ebf46690c4e0e2fdb42 | UNDERPOWERED |
| sspec_e3553e20303b2066d4b291c3 | trade_date_block_bootstrap | 11112 | BLOCKED | False | True | surrun_cb61194d14c231c8951e00fb | UNDERPOWERED |
| sspec_e3553e20303b2066d4b291c3 | trade_date_block_bootstrap | 11113 | BLOCKED | False | True | surrun_2f9e377769873d6bc83b3a00 | UNDERPOWERED |
| sspec_e3553e20303b2066d4b291c3 | trade_date_block_bootstrap | 11114 | BLOCKED | False | True | surrun_dd34d62db748d8376ab7ed5b | UNDERPOWERED |
| sspec_11e48e92c22b6c92b5269508 | trade_date_block_bootstrap | 11115 | BLOCKED | False | True | surrun_8a3a470980e63f6262e042b2 | UNDERPOWERED |
| sspec_11e48e92c22b6c92b5269508 | trade_date_block_bootstrap | 11116 | BLOCKED | False | True | surrun_322e72d049c8c5da24541ffe | UNDERPOWERED |
| sspec_11e48e92c22b6c92b5269508 | trade_date_block_bootstrap | 11117 | BLOCKED | False | True | surrun_c1d2ad2b457ac63878494af5 | UNDERPOWERED |
| sspec_552a07f2154c04e2049e189a | trade_date_block_bootstrap | 11118 | BLOCKED | False | True | surrun_8ac028699b01cfcd6ee36590 | UNDERPOWERED |
| sspec_552a07f2154c04e2049e189a | trade_date_block_bootstrap | 11119 | BLOCKED | False | True | surrun_60830b4b99151a6596d93b3a | UNDERPOWERED |
| sspec_552a07f2154c04e2049e189a | trade_date_block_bootstrap | 11120 | BLOCKED | False | True | surrun_a609ee3ad6f2bae658acb8d7 | UNDERPOWERED |
| sspec_7a07ad20f277d529a78e14d8 | trade_date_block_bootstrap | 11121 | BLOCKED | False | True | surrun_d608b6c58d412fe90fb32195 | UNDERPOWERED |
| sspec_7a07ad20f277d529a78e14d8 | trade_date_block_bootstrap | 11122 | BLOCKED | False | True | surrun_08bd071b30b27bdd05634e0a | UNDERPOWERED |
| sspec_7a07ad20f277d529a78e14d8 | trade_date_block_bootstrap | 11123 | BLOCKED | False | True | surrun_c4c16427baa1907121eeca7b | UNDERPOWERED |
| sspec_60b3f72735a53d7fa5cc9020 | trade_date_block_bootstrap | 11124 | BLOCKED | False | True | surrun_1af2d6826a08eaa5b7054d96 | UNDERPOWERED |
| sspec_60b3f72735a53d7fa5cc9020 | trade_date_block_bootstrap | 11125 | BLOCKED | False | True | surrun_6756384c83fcaa0c3b961039 | UNDERPOWERED |
| sspec_60b3f72735a53d7fa5cc9020 | trade_date_block_bootstrap | 11126 | BLOCKED | False | True | surrun_917f8dc7df70f04375382ec0 | UNDERPOWERED |
| sspec_8eaaaf1f4d25df4c7c3c811a | trade_date_block_bootstrap | 11127 | BLOCKED | False | True | surrun_07e1a4a28f47779a3de80638 | UNDERPOWERED |
| sspec_8eaaaf1f4d25df4c7c3c811a | trade_date_block_bootstrap | 11128 | BLOCKED | False | True | surrun_c69d269f2abf8e0f58413aa1 | UNDERPOWERED |
| sspec_8eaaaf1f4d25df4c7c3c811a | trade_date_block_bootstrap | 11129 | BLOCKED | False | True | surrun_65c9e00f55aeb02023155038 | UNDERPOWERED |
| sspec_a37e8e165dbd5de0eb5157ae | trade_date_block_bootstrap | 11130 | BLOCKED | False | True | surrun_49548f9283b676aa0d3cd5a7 | UNDERPOWERED |
| sspec_a37e8e165dbd5de0eb5157ae | trade_date_block_bootstrap | 11131 | BLOCKED | False | True | surrun_e043f00801d09bb61d4997c7 | UNDERPOWERED |
| sspec_a37e8e165dbd5de0eb5157ae | trade_date_block_bootstrap | 11132 | BLOCKED | False | True | surrun_518f0f0ecd7e1594fe8a31ad | UNDERPOWERED |
| sspec_bcc42ab9f3cd42d0104c4c95 | trade_date_block_bootstrap | 11133 | BLOCKED | False | True | surrun_ca21125068b88e485ab2e508 | UNDERPOWERED |
| sspec_bcc42ab9f3cd42d0104c4c95 | trade_date_block_bootstrap | 11134 | BLOCKED | False | True | surrun_79eaf2038278dfb6c5a59e6c | UNDERPOWERED |
| sspec_bcc42ab9f3cd42d0104c4c95 | trade_date_block_bootstrap | 11135 | BLOCKED | False | True | surrun_50abfc8f02f83bc78fa775b4 | UNDERPOWERED |
| sspec_c45cd85d0a99bca875f57f32 | trade_date_block_bootstrap | 11136 | BLOCKED | False | True | surrun_4b3f0a525ee1c43096eb264f | UNDERPOWERED |
| sspec_c45cd85d0a99bca875f57f32 | trade_date_block_bootstrap | 11137 | BLOCKED | False | True | surrun_3e5adea3631406be73643732 | UNDERPOWERED |
| sspec_c45cd85d0a99bca875f57f32 | trade_date_block_bootstrap | 11138 | BLOCKED | False | True | surrun_ccd5c7d898c5daa5a2cd75c9 | UNDERPOWERED |
| sspec_f260a67e6c160427683ad1d0 | trade_date_block_bootstrap | 11139 | BLOCKED | False | True | surrun_3381428a5e4b54e9e2bea20f | UNDERPOWERED |
| sspec_f260a67e6c160427683ad1d0 | trade_date_block_bootstrap | 11140 | BLOCKED | False | True | surrun_74f0a62c54fc7d594802ab98 | UNDERPOWERED |
| sspec_f260a67e6c160427683ad1d0 | trade_date_block_bootstrap | 11141 | BLOCKED | False | True | surrun_776d13eaf8ae411d55b825e2 | UNDERPOWERED |
| sspec_37c7f6459057a9045ac9035e | trade_date_block_bootstrap | 11142 | BLOCKED | False | True | surrun_3641adb9ec8850a1ca2300bc | UNDERPOWERED |
| sspec_37c7f6459057a9045ac9035e | trade_date_block_bootstrap | 11143 | BLOCKED | False | True | surrun_da958865846149fcd08eb3d2 | UNDERPOWERED |
| sspec_37c7f6459057a9045ac9035e | trade_date_block_bootstrap | 11144 | BLOCKED | False | True | surrun_567c16fe1d3d2cd56c6a845a | UNDERPOWERED |
| sspec_d2aeac8ec5d9bf87bb716b74 | trade_date_block_bootstrap | 11145 | BLOCKED | False | True | surrun_d268ed4f99f04fd37307134a | UNDERPOWERED |
| sspec_d2aeac8ec5d9bf87bb716b74 | trade_date_block_bootstrap | 11146 | BLOCKED | False | True | surrun_5670bf550ea7c69c10fbaa56 | UNDERPOWERED |
| sspec_d2aeac8ec5d9bf87bb716b74 | trade_date_block_bootstrap | 11147 | BLOCKED | False | True | surrun_8f95e743e5742dead70d7d81 | UNDERPOWERED |
| sspec_448496edfe67a7da2ed3b399 | trade_date_block_bootstrap | 11148 | BLOCKED | False | True | surrun_400bebca3c0cb883c1754dbd | UNDERPOWERED |
| sspec_448496edfe67a7da2ed3b399 | trade_date_block_bootstrap | 11149 | BLOCKED | False | True | surrun_578860786406ec0aab1d574b | UNDERPOWERED |
| sspec_448496edfe67a7da2ed3b399 | trade_date_block_bootstrap | 11150 | BLOCKED | False | True | surrun_c2352fce83dc2e8d5fcca382 | UNDERPOWERED |
| sspec_6701b69418a43a53c84f8e3a | trade_date_block_bootstrap | 11151 | BLOCKED | False | True | surrun_8c81d49345c46712ab5c46b2 | UNDERPOWERED |
| sspec_6701b69418a43a53c84f8e3a | trade_date_block_bootstrap | 11152 | BLOCKED | False | True | surrun_23655da5b25e6eb6c78c3ea7 | UNDERPOWERED |
| sspec_6701b69418a43a53c84f8e3a | trade_date_block_bootstrap | 11153 | BLOCKED | False | True | surrun_55a449b8203f19973a060d45 | UNDERPOWERED |
| sspec_b171816beb62a09b0d49f611 | trade_date_block_bootstrap | 11154 | BLOCKED | False | True | surrun_0c801ebf4b77ee18a9ee4f4d | UNDERPOWERED |
| sspec_b171816beb62a09b0d49f611 | trade_date_block_bootstrap | 11155 | BLOCKED | False | True | surrun_e96ac18aa1572d6fd538afbc | UNDERPOWERED |
| sspec_b171816beb62a09b0d49f611 | trade_date_block_bootstrap | 11156 | BLOCKED | False | True | surrun_71a8d62337414daa6ef3b224 | UNDERPOWERED |
| sspec_4d0cfac3ea2558d66fbd4e99 | trade_date_block_bootstrap | 11157 | BLOCKED | False | True | surrun_5333827517755382391d34f2 | UNDERPOWERED |
| sspec_4d0cfac3ea2558d66fbd4e99 | trade_date_block_bootstrap | 11158 | BLOCKED | False | True | surrun_1c271cf0bce8c0b66746786e | UNDERPOWERED |
| sspec_4d0cfac3ea2558d66fbd4e99 | trade_date_block_bootstrap | 11159 | BLOCKED | False | True | surrun_53d35bb05f8d89eb931e5c74 | UNDERPOWERED |
| sspec_30195e4c44d85efc01457875 | trade_date_block_bootstrap | 11160 | BLOCKED | False | True | surrun_89f97aa1faa1e3845d4ec40d | UNDERPOWERED |
| sspec_30195e4c44d85efc01457875 | trade_date_block_bootstrap | 11161 | BLOCKED | False | True | surrun_e95bf2c4997099ae8dadfd7e | UNDERPOWERED |
| sspec_30195e4c44d85efc01457875 | trade_date_block_bootstrap | 11162 | BLOCKED | False | True | surrun_5e93123f0b136281152a05fb | UNDERPOWERED |
| sspec_a205568209c2fcabcafd503b | trade_date_block_bootstrap | 11163 | BLOCKED | False | True | surrun_3f294dd170705dbc541de12b | UNDERPOWERED |
| sspec_a205568209c2fcabcafd503b | trade_date_block_bootstrap | 11164 | BLOCKED | False | True | surrun_b37fa2528f2fc15bfcc89871 | UNDERPOWERED |
| sspec_a205568209c2fcabcafd503b | trade_date_block_bootstrap | 11165 | BLOCKED | False | True | surrun_aa31b671f6cfdb3b894bce91 | UNDERPOWERED |
| sspec_dd5dcc912cf4431f08c6278d | trade_date_block_bootstrap | 11166 | BLOCKED | False | True | surrun_e2568ff45cf2de2db32dd680 | UNDERPOWERED |
| sspec_dd5dcc912cf4431f08c6278d | trade_date_block_bootstrap | 11167 | BLOCKED | False | True | surrun_ed098c3d7613e892a9f160db | UNDERPOWERED |
| sspec_dd5dcc912cf4431f08c6278d | trade_date_block_bootstrap | 11168 | BLOCKED | False | True | surrun_26b62281e39b8025f33a315c | UNDERPOWERED |
| sspec_c4f83d7236bfb8c23cc81c4e | trade_date_block_bootstrap | 11169 | BLOCKED | False | True | surrun_cb7be44186e0b1009edf0a11 | UNDERPOWERED |
| sspec_c4f83d7236bfb8c23cc81c4e | trade_date_block_bootstrap | 11170 | BLOCKED | False | True | surrun_caa79edda77d6bc829603277 | UNDERPOWERED |
| sspec_c4f83d7236bfb8c23cc81c4e | trade_date_block_bootstrap | 11171 | BLOCKED | False | True | surrun_f0d463f625c4b87d562d02b9 | UNDERPOWERED |
| sspec_359b3427cab6452abc9e95df | trade_date_block_bootstrap | 11172 | BLOCKED | False | True | surrun_943ed5f777d60d59ceda7309 | UNDERPOWERED |
| sspec_359b3427cab6452abc9e95df | trade_date_block_bootstrap | 11173 | BLOCKED | False | True | surrun_a83a088b172b22907134581b | UNDERPOWERED |
| sspec_359b3427cab6452abc9e95df | trade_date_block_bootstrap | 11174 | BLOCKED | False | True | surrun_b2250ccd032cfd4b9857ed58 | UNDERPOWERED |
| sspec_512658d7802ea840d5a6a683 | trade_date_block_bootstrap | 11175 | BLOCKED | False | True | surrun_befbda5337932a4b12655394 | UNDERPOWERED |
| sspec_512658d7802ea840d5a6a683 | trade_date_block_bootstrap | 11176 | BLOCKED | False | True | surrun_12999315d18402baba1f1830 | UNDERPOWERED |
| sspec_512658d7802ea840d5a6a683 | trade_date_block_bootstrap | 11177 | BLOCKED | False | True | surrun_b147a6e951e224da81ecdb4c | UNDERPOWERED |
| sspec_a87cad813815f7514f2e41b8 | trade_date_block_bootstrap | 11178 | BLOCKED | False | True | surrun_37eae51b1c7e68d54871ece1 | UNDERPOWERED |
| sspec_a87cad813815f7514f2e41b8 | trade_date_block_bootstrap | 11179 | BLOCKED | False | True | surrun_4bd71b96b3129c81a7c7e8e1 | UNDERPOWERED |
| sspec_a87cad813815f7514f2e41b8 | trade_date_block_bootstrap | 11180 | BLOCKED | False | True | surrun_d4acc31b4272f84db02516cd | UNDERPOWERED |
| sspec_17c44a30fdadd35e3b669bdb | trade_date_block_bootstrap | 11181 | BLOCKED | False | True | surrun_790b13d2959bb2ea2b48fa84 | UNDERPOWERED |
| sspec_17c44a30fdadd35e3b669bdb | trade_date_block_bootstrap | 11182 | BLOCKED | False | True | surrun_650686200e255f8261262a51 | UNDERPOWERED |
| sspec_17c44a30fdadd35e3b669bdb | trade_date_block_bootstrap | 11183 | BLOCKED | False | True | surrun_6e3ca5f01345cf204a25216d | UNDERPOWERED |
| sspec_f136b38bd075254fb0cd5179 | trade_date_block_bootstrap | 11184 | BLOCKED | False | True | surrun_632ef5e9be317c80af71ca10 | UNDERPOWERED |
| sspec_f136b38bd075254fb0cd5179 | trade_date_block_bootstrap | 11185 | BLOCKED | False | True | surrun_6537ea84bb310938a13ec5ae | UNDERPOWERED |
| sspec_f136b38bd075254fb0cd5179 | trade_date_block_bootstrap | 11186 | BLOCKED | False | True | surrun_2af1da4fcc404b646966bfb5 | UNDERPOWERED |
| sspec_7a5fa340986da0095166a261 | trade_date_block_bootstrap | 11187 | BLOCKED | False | True | surrun_4f2ce1efb54bdffdbe34bf23 | UNDERPOWERED |
| sspec_7a5fa340986da0095166a261 | trade_date_block_bootstrap | 11188 | BLOCKED | False | True | surrun_93605a843a7e201c3a432fb6 | UNDERPOWERED |
| sspec_7a5fa340986da0095166a261 | trade_date_block_bootstrap | 11189 | BLOCKED | False | True | surrun_8378d1217630d9a3d7f456d1 | UNDERPOWERED |
| sspec_88d5a298d593652e8b9f6f0c | trade_date_block_bootstrap | 11190 | BLOCKED | False | True | surrun_e1e5494392b26839ca7cb016 | UNDERPOWERED |
| sspec_88d5a298d593652e8b9f6f0c | trade_date_block_bootstrap | 11191 | BLOCKED | False | True | surrun_76a7511c00b6d6e085cfcdb9 | UNDERPOWERED |
| sspec_88d5a298d593652e8b9f6f0c | trade_date_block_bootstrap | 11192 | BLOCKED | False | True | surrun_b79cf9857e37bddcf9708848 | UNDERPOWERED |
| sspec_5a1ecd95d4a899bbc9c11bb7 | trade_date_block_bootstrap | 11193 | BLOCKED | False | True | surrun_ae9abd55c1b91ee202fbee15 | UNDERPOWERED |
| sspec_5a1ecd95d4a899bbc9c11bb7 | trade_date_block_bootstrap | 11194 | BLOCKED | False | True | surrun_12c74c66e04ab381d4bdd6de | UNDERPOWERED |
| sspec_5a1ecd95d4a899bbc9c11bb7 | trade_date_block_bootstrap | 11195 | BLOCKED | False | True | surrun_3dd78e2fe5d099bb34ee17ab | UNDERPOWERED |

## Machinery Inventory

- `SurrogateStudyRun` schema and deterministic serialization live in `src/alpha_system/governance/surrogate_run.py`.
- `surrogate_flag` is threaded through `TrialLedgerRecord`; true surrogate trials are excluded from production variant/family counts.
- `alpha governance surrogate-calibrate` runs seeded surrogate calibrations in caller-supplied isolated namespaces.
- Real-data calibration over the kill-shot StudySpec remains a coordinator runbook step before FUTSUB-P28 kill-shot resume.
