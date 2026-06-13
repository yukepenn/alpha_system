# Real-Data Surrogate Calibration: sspec_c237c6a8ce40c2585836fae0

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
- Isolated namespace: `/home/yuke_zhang/alpha_data/alpha_system/rigor_p05_surrogate_v5_liq_c237c6`.

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
| sspec_186366ce8fc5106f8952e9af | trade_date_block_shuffle | 10200 | BLOCKED | False | True | surrun_0026c587b57b020de78f78b2 | UNDERPOWERED |
| sspec_186366ce8fc5106f8952e9af | trade_date_block_shuffle | 10201 | BLOCKED | False | True | surrun_5e9147c43f03b696759a7a64 | UNDERPOWERED |
| sspec_186366ce8fc5106f8952e9af | trade_date_block_shuffle | 10202 | BLOCKED | False | True | surrun_fdbf966518b806c0a77237c5 | UNDERPOWERED |
| sspec_abb0800d67aca97257b98174 | trade_date_block_shuffle | 10203 | BLOCKED | False | True | surrun_9c6d59420ff4511d6e1b2684 | UNDERPOWERED |
| sspec_abb0800d67aca97257b98174 | trade_date_block_shuffle | 10204 | BLOCKED | False | True | surrun_942a0e9f42e5de770bec83db | UNDERPOWERED |
| sspec_abb0800d67aca97257b98174 | trade_date_block_shuffle | 10205 | BLOCKED | False | True | surrun_4a34cfbc61f6efb796de41f6 | UNDERPOWERED |
| sspec_5388a9a9355da05b81c2e0f5 | trade_date_block_shuffle | 10206 | BLOCKED | False | True | surrun_6fd96b1500125b10fb375bc0 | UNDERPOWERED |
| sspec_5388a9a9355da05b81c2e0f5 | trade_date_block_shuffle | 10207 | BLOCKED | False | True | surrun_729beac51dc9f696abe23bd8 | UNDERPOWERED |
| sspec_5388a9a9355da05b81c2e0f5 | trade_date_block_shuffle | 10208 | BLOCKED | False | True | surrun_be68e82a91e755dd5df60e4f | UNDERPOWERED |
| sspec_f55efbd79a11c18c54b39e61 | trade_date_block_shuffle | 10209 | BLOCKED | False | True | surrun_f584d1bc1dee99b8d2f4bf89 | UNDERPOWERED |
| sspec_f55efbd79a11c18c54b39e61 | trade_date_block_shuffle | 10210 | BLOCKED | False | True | surrun_5cd89cb3e9919bbc8b3bb993 | UNDERPOWERED |
| sspec_f55efbd79a11c18c54b39e61 | trade_date_block_shuffle | 10211 | BLOCKED | False | True | surrun_aa399d10042d73e7005fdd03 | UNDERPOWERED |
| sspec_21b47c6532352f1d8c30c156 | trade_date_block_shuffle | 10212 | BLOCKED | False | True | surrun_d2b1d0bc73e0f5f731c92d16 | UNDERPOWERED |
| sspec_21b47c6532352f1d8c30c156 | trade_date_block_shuffle | 10213 | BLOCKED | False | True | surrun_a424d8d6be7391c15dc4289e | UNDERPOWERED |
| sspec_21b47c6532352f1d8c30c156 | trade_date_block_shuffle | 10214 | BLOCKED | False | True | surrun_2274ed20b6e7b6c5276890d8 | UNDERPOWERED |
| sspec_2c3079c514c26522ec9f2f14 | trade_date_block_shuffle | 10215 | BLOCKED | False | True | surrun_a4b7f864a932773633f9d152 | UNDERPOWERED |
| sspec_2c3079c514c26522ec9f2f14 | trade_date_block_shuffle | 10216 | BLOCKED | False | True | surrun_b1900dd4a7b75fe7a591bd8c | UNDERPOWERED |
| sspec_2c3079c514c26522ec9f2f14 | trade_date_block_shuffle | 10217 | BLOCKED | False | True | surrun_3cdb3cde486b3438853534fa | UNDERPOWERED |
| sspec_04e3ec49a39c1fa70257a198 | trade_date_block_shuffle | 10218 | BLOCKED | False | True | surrun_a6a3d826fbcc1a1ecba9badc | UNDERPOWERED |
| sspec_04e3ec49a39c1fa70257a198 | trade_date_block_shuffle | 10219 | BLOCKED | False | True | surrun_f3e0762abb3f564696d5c564 | UNDERPOWERED |
| sspec_04e3ec49a39c1fa70257a198 | trade_date_block_shuffle | 10220 | BLOCKED | False | True | surrun_14916be0fd36b2e8f41d4b0a | UNDERPOWERED |
| sspec_30fafe9c23cc3db43b14ddf4 | trade_date_block_shuffle | 10221 | BLOCKED | False | True | surrun_8433dac463a4d76fec1b3376 | UNDERPOWERED |
| sspec_30fafe9c23cc3db43b14ddf4 | trade_date_block_shuffle | 10222 | BLOCKED | False | True | surrun_ef63ef7dfd5d7c6286ff10e7 | UNDERPOWERED |
| sspec_30fafe9c23cc3db43b14ddf4 | trade_date_block_shuffle | 10223 | BLOCKED | False | True | surrun_2d819cd6a03819f4b09a877c | UNDERPOWERED |
| sspec_64a62f51bcf69fbd6d5ae3e5 | trade_date_block_shuffle | 10224 | BLOCKED | False | True | surrun_dcfb4e3914987b75030d6095 | UNDERPOWERED |
| sspec_64a62f51bcf69fbd6d5ae3e5 | trade_date_block_shuffle | 10225 | BLOCKED | False | True | surrun_0cacf21ddb9340d39d4a09ca | UNDERPOWERED |
| sspec_64a62f51bcf69fbd6d5ae3e5 | trade_date_block_shuffle | 10226 | BLOCKED | False | True | surrun_9f955aaf12ab1c20e8072315 | UNDERPOWERED |
| sspec_05c47eec02cc292eee93e6e4 | trade_date_block_shuffle | 10227 | BLOCKED | False | True | surrun_620a9aa4e2577150d6cff024 | UNDERPOWERED |
| sspec_05c47eec02cc292eee93e6e4 | trade_date_block_shuffle | 10228 | BLOCKED | False | True | surrun_36773c74def20d348630080a | UNDERPOWERED |
| sspec_05c47eec02cc292eee93e6e4 | trade_date_block_shuffle | 10229 | BLOCKED | False | True | surrun_093624095b00e4b8ac698827 | UNDERPOWERED |
| sspec_ddf3a3a474adecf0f9592cd0 | trade_date_block_shuffle | 10230 | BLOCKED | False | True | surrun_103b6bd604b95983b3618110 | UNDERPOWERED |
| sspec_ddf3a3a474adecf0f9592cd0 | trade_date_block_shuffle | 10231 | BLOCKED | False | True | surrun_650b6ceadb0204e2f1127a64 | UNDERPOWERED |
| sspec_ddf3a3a474adecf0f9592cd0 | trade_date_block_shuffle | 10232 | BLOCKED | False | True | surrun_df5ef64f52fc7df409f4bcfa | UNDERPOWERED |
| sspec_0d4af57026259b33808ca5aa | trade_date_block_shuffle | 10233 | BLOCKED | False | True | surrun_a70e843752e01db39029c656 | UNDERPOWERED |
| sspec_0d4af57026259b33808ca5aa | trade_date_block_shuffle | 10234 | BLOCKED | False | True | surrun_e455f2d81725220cf30db9a2 | UNDERPOWERED |
| sspec_0d4af57026259b33808ca5aa | trade_date_block_shuffle | 10235 | BLOCKED | False | True | surrun_3877a2019611e4174d14df12 | UNDERPOWERED |
| sspec_cb615fa2438d459f66c234ea | trade_date_block_shuffle | 10236 | BLOCKED | False | True | surrun_e8c2bce377773c247b8ea78f | UNDERPOWERED |
| sspec_cb615fa2438d459f66c234ea | trade_date_block_shuffle | 10237 | BLOCKED | False | True | surrun_07b50c099808bb151c90bce6 | UNDERPOWERED |
| sspec_cb615fa2438d459f66c234ea | trade_date_block_shuffle | 10238 | BLOCKED | False | True | surrun_6c7ac1aa9cca2dc4c7ef9af8 | UNDERPOWERED |
| sspec_21c9105862a0460faa28b12b | trade_date_block_shuffle | 10239 | BLOCKED | False | True | surrun_ffd62284a44ffd299ed00410 | UNDERPOWERED |
| sspec_21c9105862a0460faa28b12b | trade_date_block_shuffle | 10240 | BLOCKED | False | True | surrun_8cec695a54cd92bfee3a63ee | UNDERPOWERED |
| sspec_21c9105862a0460faa28b12b | trade_date_block_shuffle | 10241 | BLOCKED | False | True | surrun_29d298a25c30d43a46947141 | UNDERPOWERED |
| sspec_a850d4fdf70255eddd718338 | trade_date_block_shuffle | 10242 | BLOCKED | False | True | surrun_db41ba507da6b7e091d3cc97 | UNDERPOWERED |
| sspec_a850d4fdf70255eddd718338 | trade_date_block_shuffle | 10243 | BLOCKED | False | True | surrun_91c5e5bceb06f36c872b128f | UNDERPOWERED |
| sspec_a850d4fdf70255eddd718338 | trade_date_block_shuffle | 10244 | BLOCKED | False | True | surrun_b99a13f194b1d7163111789c | UNDERPOWERED |
| sspec_c0247dfd070d3bcbc84d2a1e | trade_date_block_shuffle | 10245 | BLOCKED | False | True | surrun_327900857b851080ad2ab4c8 | UNDERPOWERED |
| sspec_c0247dfd070d3bcbc84d2a1e | trade_date_block_shuffle | 10246 | BLOCKED | False | True | surrun_e3b362c71e154622bcf8abc8 | UNDERPOWERED |
| sspec_c0247dfd070d3bcbc84d2a1e | trade_date_block_shuffle | 10247 | BLOCKED | False | True | surrun_6bbddd411362c6eb4a1386ac | UNDERPOWERED |
| sspec_3fa57dd69f1d1681b2c627bb | trade_date_block_shuffle | 10248 | BLOCKED | False | True | surrun_67566a5777c25f66626ece8a | UNDERPOWERED |
| sspec_3fa57dd69f1d1681b2c627bb | trade_date_block_shuffle | 10249 | BLOCKED | False | True | surrun_35ac4a909c69870a0aacef4d | UNDERPOWERED |
| sspec_3fa57dd69f1d1681b2c627bb | trade_date_block_shuffle | 10250 | BLOCKED | False | True | surrun_2022959729f99aef9b77f241 | UNDERPOWERED |
| sspec_3c6feed90e9b81eb45bda321 | trade_date_block_shuffle | 10251 | BLOCKED | False | True | surrun_c62fc7428703ed370d4bbecf | UNDERPOWERED |
| sspec_3c6feed90e9b81eb45bda321 | trade_date_block_shuffle | 10252 | BLOCKED | False | True | surrun_b530390ddb64137788bc0327 | UNDERPOWERED |
| sspec_3c6feed90e9b81eb45bda321 | trade_date_block_shuffle | 10253 | BLOCKED | False | True | surrun_a62355ab94913675d19ac013 | UNDERPOWERED |
| sspec_07150b2dd72b23195b6df1fb | trade_date_block_shuffle | 10254 | BLOCKED | False | True | surrun_222abf742ac96e7362a935c9 | UNDERPOWERED |
| sspec_07150b2dd72b23195b6df1fb | trade_date_block_shuffle | 10255 | BLOCKED | False | True | surrun_8782b2667604dc268a8deff6 | UNDERPOWERED |
| sspec_07150b2dd72b23195b6df1fb | trade_date_block_shuffle | 10256 | BLOCKED | False | True | surrun_9cb0157304a22ae0f7e8a5f2 | UNDERPOWERED |
| sspec_9b19d724d359876bd4fc069a | trade_date_block_shuffle | 10257 | BLOCKED | False | True | surrun_5339816defff82d6c9619f56 | UNDERPOWERED |
| sspec_9b19d724d359876bd4fc069a | trade_date_block_shuffle | 10258 | BLOCKED | False | True | surrun_3cd0cf8e0a85562303fba58e | UNDERPOWERED |
| sspec_9b19d724d359876bd4fc069a | trade_date_block_shuffle | 10259 | BLOCKED | False | True | surrun_379c55c1b3a7ea0937e64a68 | UNDERPOWERED |
| sspec_fca8fad02351c94da2b9a107 | trade_date_block_shuffle | 10260 | BLOCKED | False | True | surrun_f4c192f0c1336229fedf1184 | UNDERPOWERED |
| sspec_fca8fad02351c94da2b9a107 | trade_date_block_shuffle | 10261 | BLOCKED | False | True | surrun_415bc3bef140958240bf20b8 | UNDERPOWERED |
| sspec_fca8fad02351c94da2b9a107 | trade_date_block_shuffle | 10262 | BLOCKED | False | True | surrun_7d876c060a8b8c3a98c99324 | UNDERPOWERED |
| sspec_1a6a825c5697207538903015 | trade_date_block_shuffle | 10263 | BLOCKED | False | True | surrun_90778f68f9833bb6d87a579e | UNDERPOWERED |
| sspec_1a6a825c5697207538903015 | trade_date_block_shuffle | 10264 | BLOCKED | False | True | surrun_6ec9fe6b76641f2a404d06d6 | UNDERPOWERED |
| sspec_1a6a825c5697207538903015 | trade_date_block_shuffle | 10265 | BLOCKED | False | True | surrun_d668ee67ac817cf7d9b4d1c9 | UNDERPOWERED |
| sspec_ac73dbd9b8aab366c7825c0b | trade_date_block_shuffle | 10266 | BLOCKED | False | True | surrun_a6e6dff8de42a809301e3b4e | UNDERPOWERED |
| sspec_ac73dbd9b8aab366c7825c0b | trade_date_block_shuffle | 10267 | BLOCKED | False | True | surrun_62db5569e35a94ca217755c9 | UNDERPOWERED |
| sspec_ac73dbd9b8aab366c7825c0b | trade_date_block_shuffle | 10268 | BLOCKED | False | True | surrun_10a0d44f2086d0eec236edbf | UNDERPOWERED |
| sspec_2ebf97e36be5f4ea57da9df8 | trade_date_block_shuffle | 10269 | BLOCKED | False | True | surrun_91c30809a4185af2bbfcdca8 | UNDERPOWERED |
| sspec_2ebf97e36be5f4ea57da9df8 | trade_date_block_shuffle | 10270 | BLOCKED | False | True | surrun_69c7075927b3a999ab8e715c | UNDERPOWERED |
| sspec_2ebf97e36be5f4ea57da9df8 | trade_date_block_shuffle | 10271 | BLOCKED | False | True | surrun_516b1717c3e0e625a15f236e | UNDERPOWERED |
| sspec_d2ac0ee91418667b6e4960ca | trade_date_block_shuffle | 10272 | BLOCKED | False | True | surrun_3aa4e333d8eb76985ad89d09 | UNDERPOWERED |
| sspec_d2ac0ee91418667b6e4960ca | trade_date_block_shuffle | 10273 | BLOCKED | False | True | surrun_5775be02117121469f82a112 | UNDERPOWERED |
| sspec_d2ac0ee91418667b6e4960ca | trade_date_block_shuffle | 10274 | BLOCKED | False | True | surrun_0ea82e4d4e9052473cb12c8b | UNDERPOWERED |
| sspec_d17d09c83e2c7d143ed0625c | trade_date_block_shuffle | 10275 | BLOCKED | False | True | surrun_f63df817677c03337f8dd301 | UNDERPOWERED |
| sspec_d17d09c83e2c7d143ed0625c | trade_date_block_shuffle | 10276 | BLOCKED | False | True | surrun_db7614ff90499bb890b64260 | UNDERPOWERED |
| sspec_d17d09c83e2c7d143ed0625c | trade_date_block_shuffle | 10277 | BLOCKED | False | True | surrun_4f4398d6acfcebdcbe167a53 | UNDERPOWERED |
| sspec_c886f447ae20c4abaf827d01 | trade_date_block_shuffle | 10278 | BLOCKED | False | True | surrun_a61695a1d61a0dda6bb13461 | UNDERPOWERED |
| sspec_c886f447ae20c4abaf827d01 | trade_date_block_shuffle | 10279 | BLOCKED | False | True | surrun_22000a8e9b748ca50e1a1ee2 | UNDERPOWERED |
| sspec_c886f447ae20c4abaf827d01 | trade_date_block_shuffle | 10280 | BLOCKED | False | True | surrun_b7fadad688c8f45026a641df | UNDERPOWERED |
| sspec_87aa803690b56992f819a009 | trade_date_block_shuffle | 10281 | BLOCKED | False | True | surrun_adb8c7a27f721029e65d3372 | UNDERPOWERED |
| sspec_87aa803690b56992f819a009 | trade_date_block_shuffle | 10282 | BLOCKED | False | True | surrun_82181e669c6ffad9684dc720 | UNDERPOWERED |
| sspec_87aa803690b56992f819a009 | trade_date_block_shuffle | 10283 | BLOCKED | False | True | surrun_b3df9adc1808524da1b424db | UNDERPOWERED |
| sspec_fcb62bbe8bc8d99a832d211d | trade_date_block_shuffle | 10284 | BLOCKED | False | True | surrun_4e04748e274342927b0fbd8a | UNDERPOWERED |
| sspec_fcb62bbe8bc8d99a832d211d | trade_date_block_shuffle | 10285 | BLOCKED | False | True | surrun_018c3cf29eea018370f70dcb | UNDERPOWERED |
| sspec_fcb62bbe8bc8d99a832d211d | trade_date_block_shuffle | 10286 | BLOCKED | False | True | surrun_ec5d0fa1b39e8b38f68db4d3 | UNDERPOWERED |
| sspec_d2f326af93df07560a9b8db3 | trade_date_block_shuffle | 10287 | BLOCKED | False | True | surrun_7b7dd7e376858235f43a3c8a | UNDERPOWERED |
| sspec_d2f326af93df07560a9b8db3 | trade_date_block_shuffle | 10288 | BLOCKED | False | True | surrun_28db0a3feb5dc74e5e601745 | UNDERPOWERED |
| sspec_d2f326af93df07560a9b8db3 | trade_date_block_shuffle | 10289 | BLOCKED | False | True | surrun_d70c643770982bdcb5637bcf | UNDERPOWERED |
| sspec_6ec1ab42c37a5f71362e9216 | trade_date_block_shuffle | 10290 | BLOCKED | False | True | surrun_211c9f57bb7050b062be0350 | UNDERPOWERED |
| sspec_6ec1ab42c37a5f71362e9216 | trade_date_block_shuffle | 10291 | BLOCKED | False | True | surrun_deeefee656f907a7833e2344 | UNDERPOWERED |
| sspec_6ec1ab42c37a5f71362e9216 | trade_date_block_shuffle | 10292 | BLOCKED | False | True | surrun_aa7ae6d1a6ef7d5eda2dae29 | UNDERPOWERED |
| sspec_8721bad2dcdde7bef4e0cfed | trade_date_block_shuffle | 10293 | BLOCKED | False | True | surrun_21d95a1d32647ce2380e5b6f | UNDERPOWERED |
| sspec_8721bad2dcdde7bef4e0cfed | trade_date_block_shuffle | 10294 | BLOCKED | False | True | surrun_a21ec9b3507ec318c403f53c | UNDERPOWERED |
| sspec_8721bad2dcdde7bef4e0cfed | trade_date_block_shuffle | 10295 | BLOCKED | False | True | surrun_20b2e97a5402acf8e255fc90 | UNDERPOWERED |
| sspec_28e61fdb46db16a86d67ae64 | trade_date_block_shuffle | 10296 | BLOCKED | False | True | surrun_9337cbd172ed763e8cee07f5 | UNDERPOWERED |
| sspec_28e61fdb46db16a86d67ae64 | trade_date_block_shuffle | 10297 | BLOCKED | False | True | surrun_2d043bc0aaab41e1f9527b4b | UNDERPOWERED |
| sspec_28e61fdb46db16a86d67ae64 | trade_date_block_shuffle | 10298 | BLOCKED | False | True | surrun_650e14f95eb5b320bae8e908 | UNDERPOWERED |
| sspec_caa754ddb6109aed20216758 | trade_date_block_shuffle | 10299 | BLOCKED | False | True | surrun_f0579cff0dafe7f6d14f14b4 | UNDERPOWERED |
| sspec_caa754ddb6109aed20216758 | trade_date_block_shuffle | 10300 | BLOCKED | False | True | surrun_fb67d96e452dad6e5c2704c2 | UNDERPOWERED |
| sspec_caa754ddb6109aed20216758 | trade_date_block_shuffle | 10301 | BLOCKED | False | True | surrun_6c81761737fa1016e7bcdece | UNDERPOWERED |
| sspec_72e29b3149b3f241fef8af82 | trade_date_block_shuffle | 10302 | BLOCKED | False | True | surrun_2e49cd9627ee61fcd88f34a6 | UNDERPOWERED |
| sspec_72e29b3149b3f241fef8af82 | trade_date_block_shuffle | 10303 | BLOCKED | False | True | surrun_81b1a714545bff7acff17097 | UNDERPOWERED |
| sspec_72e29b3149b3f241fef8af82 | trade_date_block_shuffle | 10304 | BLOCKED | False | True | surrun_1f655602f5fd448b97a0a7f4 | UNDERPOWERED |
| sspec_c37b26eba6e520e6744b85c4 | trade_date_block_shuffle | 10305 | BLOCKED | False | True | surrun_deed1e9323c3467dad8e960b | UNDERPOWERED |
| sspec_c37b26eba6e520e6744b85c4 | trade_date_block_shuffle | 10306 | BLOCKED | False | True | surrun_7970b1e92ae9a7085948688c | UNDERPOWERED |
| sspec_c37b26eba6e520e6744b85c4 | trade_date_block_shuffle | 10307 | BLOCKED | False | True | surrun_6ab05a7a0fc4b7abcea9d918 | UNDERPOWERED |
| sspec_81edb80e40b74e3e95cbe8b0 | trade_date_block_shuffle | 10308 | BLOCKED | False | True | surrun_a7d28600450f4ad2f0213513 | UNDERPOWERED |
| sspec_81edb80e40b74e3e95cbe8b0 | trade_date_block_shuffle | 10309 | BLOCKED | False | True | surrun_e919518b39e2ace4aca95446 | UNDERPOWERED |
| sspec_81edb80e40b74e3e95cbe8b0 | trade_date_block_shuffle | 10310 | BLOCKED | False | True | surrun_f5bbe568df41b15a1bda2e97 | UNDERPOWERED |
| sspec_3be755c64a80f104f27efb43 | trade_date_block_shuffle | 10311 | BLOCKED | False | True | surrun_db4989a551a57d4cb7142480 | UNDERPOWERED |
| sspec_3be755c64a80f104f27efb43 | trade_date_block_shuffle | 10312 | BLOCKED | False | True | surrun_d501c4e39423735d3e04a2a9 | UNDERPOWERED |
| sspec_3be755c64a80f104f27efb43 | trade_date_block_shuffle | 10313 | BLOCKED | False | True | surrun_4c32086379f5778d9f4d5dd3 | UNDERPOWERED |
| sspec_1d42f25d84cb70bff806e8b5 | trade_date_block_shuffle | 10314 | BLOCKED | False | True | surrun_438ad68f97aa3aedc1d3d49e | UNDERPOWERED |
| sspec_1d42f25d84cb70bff806e8b5 | trade_date_block_shuffle | 10315 | BLOCKED | False | True | surrun_71057fcbb74ccef2f7984eea | UNDERPOWERED |
| sspec_1d42f25d84cb70bff806e8b5 | trade_date_block_shuffle | 10316 | BLOCKED | False | True | surrun_fc69997b9f0e58db29c2310a | UNDERPOWERED |
| sspec_d9725acf9fdcfb8bddadb32c | trade_date_block_shuffle | 10317 | BLOCKED | False | True | surrun_040ec0e1d47892808b3aef32 | UNDERPOWERED |
| sspec_d9725acf9fdcfb8bddadb32c | trade_date_block_shuffle | 10318 | BLOCKED | False | True | surrun_728f0bd9b7d0bbb21814f787 | UNDERPOWERED |
| sspec_d9725acf9fdcfb8bddadb32c | trade_date_block_shuffle | 10319 | BLOCKED | False | True | surrun_27988b877223eae354f2d4cc | UNDERPOWERED |
| sspec_809d509103d8505412f9f6d9 | trade_date_block_shuffle | 10320 | BLOCKED | False | True | surrun_dc3b1bd1938ff55eb8cb7fc9 | UNDERPOWERED |
| sspec_809d509103d8505412f9f6d9 | trade_date_block_shuffle | 10321 | BLOCKED | False | True | surrun_dcec8238b500b64cfbab229a | UNDERPOWERED |
| sspec_809d509103d8505412f9f6d9 | trade_date_block_shuffle | 10322 | BLOCKED | False | True | surrun_dac969f209bd47af370f6b8e | UNDERPOWERED |
| sspec_35912f604fd3ad171b8b48ed | trade_date_block_shuffle | 10323 | BLOCKED | False | True | surrun_ed18b08541149e6ee4811507 | UNDERPOWERED |
| sspec_35912f604fd3ad171b8b48ed | trade_date_block_shuffle | 10324 | BLOCKED | False | True | surrun_c9c83b25de539d983a634fce | UNDERPOWERED |
| sspec_35912f604fd3ad171b8b48ed | trade_date_block_shuffle | 10325 | BLOCKED | False | True | surrun_4e3808313b415b29ca0573b1 | UNDERPOWERED |
| sspec_5bd27a691f2c763e23e0ac5d | trade_date_block_shuffle | 10326 | BLOCKED | False | True | surrun_bf6c964ea0dc17a28acbd254 | UNDERPOWERED |
| sspec_5bd27a691f2c763e23e0ac5d | trade_date_block_shuffle | 10327 | BLOCKED | False | True | surrun_262caa74c9d36c33717e2c42 | UNDERPOWERED |
| sspec_5bd27a691f2c763e23e0ac5d | trade_date_block_shuffle | 10328 | BLOCKED | False | True | surrun_f7707cb4fb00478c5447234a | UNDERPOWERED |
| sspec_d876e1a6bb6d66cf9163f018 | trade_date_block_shuffle | 10329 | BLOCKED | False | True | surrun_5c48372bc83125523f5fc93c | UNDERPOWERED |
| sspec_d876e1a6bb6d66cf9163f018 | trade_date_block_shuffle | 10330 | BLOCKED | False | True | surrun_192f7969a8da157185e74edd | UNDERPOWERED |
| sspec_d876e1a6bb6d66cf9163f018 | trade_date_block_shuffle | 10331 | BLOCKED | False | True | surrun_11e8474ef73f0f88832c1939 | UNDERPOWERED |
| sspec_d5264bc5f5af602643535981 | trade_date_block_shuffle | 10332 | BLOCKED | False | True | surrun_2dff92fd81b572672e0405b4 | UNDERPOWERED |
| sspec_d5264bc5f5af602643535981 | trade_date_block_shuffle | 10333 | BLOCKED | False | True | surrun_e9623023e1aff22401f7a437 | UNDERPOWERED |
| sspec_d5264bc5f5af602643535981 | trade_date_block_shuffle | 10334 | BLOCKED | False | True | surrun_ddfd33b01e1f6ac344c6e0cb | UNDERPOWERED |
| sspec_b70f9ffb4c8891e3b7fb9da7 | trade_date_block_shuffle | 10335 | BLOCKED | False | True | surrun_a487413c61b93e8ff0f19e8c | UNDERPOWERED |
| sspec_b70f9ffb4c8891e3b7fb9da7 | trade_date_block_shuffle | 10336 | BLOCKED | False | True | surrun_aa4d5bae3c8d85c1d9efddc0 | UNDERPOWERED |
| sspec_b70f9ffb4c8891e3b7fb9da7 | trade_date_block_shuffle | 10337 | BLOCKED | False | True | surrun_dfd62ae1c1ca8e1dbfb9b3c1 | UNDERPOWERED |
| sspec_b678936ebffc4eb9371805c3 | trade_date_block_shuffle | 10338 | BLOCKED | False | True | surrun_3ede35e683079693cb484f43 | UNDERPOWERED |
| sspec_b678936ebffc4eb9371805c3 | trade_date_block_shuffle | 10339 | BLOCKED | False | True | surrun_8585d18da77150168e561dc8 | UNDERPOWERED |
| sspec_b678936ebffc4eb9371805c3 | trade_date_block_shuffle | 10340 | BLOCKED | False | True | surrun_46c568f4d0b1391379841907 | UNDERPOWERED |
| sspec_1b145fdde9ee6101806e1356 | trade_date_block_shuffle | 10341 | BLOCKED | False | True | surrun_0d54aa830a9107e2d069ddcc | UNDERPOWERED |
| sspec_1b145fdde9ee6101806e1356 | trade_date_block_shuffle | 10342 | BLOCKED | False | True | surrun_46b44f1764e4934025813385 | UNDERPOWERED |
| sspec_1b145fdde9ee6101806e1356 | trade_date_block_shuffle | 10343 | BLOCKED | False | True | surrun_cfd2563a504e8bd777ec7d92 | UNDERPOWERED |
| sspec_09ab9383bb4ac63fb644b9cd | trade_date_block_shuffle | 10344 | BLOCKED | False | True | surrun_4f53d4d487ef13e7509537ce | UNDERPOWERED |
| sspec_09ab9383bb4ac63fb644b9cd | trade_date_block_shuffle | 10345 | BLOCKED | False | True | surrun_b552503fffc6262341cab14d | UNDERPOWERED |
| sspec_09ab9383bb4ac63fb644b9cd | trade_date_block_shuffle | 10346 | BLOCKED | False | True | surrun_0100cdfe9296cb47423ff243 | UNDERPOWERED |
| sspec_b0099321ed5b03adf399a8ad | trade_date_block_shuffle | 10347 | BLOCKED | False | True | surrun_7ef699c4ff1338de14a45f0f | UNDERPOWERED |
| sspec_b0099321ed5b03adf399a8ad | trade_date_block_shuffle | 10348 | BLOCKED | False | True | surrun_5087fa31015e32af54878afc | UNDERPOWERED |
| sspec_b0099321ed5b03adf399a8ad | trade_date_block_shuffle | 10349 | BLOCKED | False | True | surrun_11a77e6e875df2d2b74e177a | UNDERPOWERED |
| sspec_7dda7e7fd6242f54de62c1df | trade_date_block_shuffle | 10350 | BLOCKED | False | True | surrun_c697f2ece51c0d3ca084c6d7 | UNDERPOWERED |
| sspec_7dda7e7fd6242f54de62c1df | trade_date_block_shuffle | 10351 | BLOCKED | False | True | surrun_867a23835c1fbf3bd40bb3ab | UNDERPOWERED |
| sspec_7dda7e7fd6242f54de62c1df | trade_date_block_shuffle | 10352 | BLOCKED | False | True | surrun_376c925de6d6ae8706a2af79 | UNDERPOWERED |
| sspec_bb268319371895d086b6c4b7 | trade_date_block_shuffle | 10353 | BLOCKED | False | True | surrun_baae14d7a8500da7d74e008c | UNDERPOWERED |
| sspec_bb268319371895d086b6c4b7 | trade_date_block_shuffle | 10354 | BLOCKED | False | True | surrun_764b365aa0c0eadebc43f71d | UNDERPOWERED |
| sspec_bb268319371895d086b6c4b7 | trade_date_block_shuffle | 10355 | BLOCKED | False | True | surrun_82624c94b63ab71fa9e58a27 | UNDERPOWERED |
| sspec_e74476332df1a2949e777f3d | trade_date_block_shuffle | 10356 | BLOCKED | False | True | surrun_713bbb28311c739e9f998c27 | UNDERPOWERED |
| sspec_e74476332df1a2949e777f3d | trade_date_block_shuffle | 10357 | BLOCKED | False | True | surrun_a56fdc163afcd0f4b0a1889f | UNDERPOWERED |
| sspec_e74476332df1a2949e777f3d | trade_date_block_shuffle | 10358 | BLOCKED | False | True | surrun_3d28f7fcf21f5fd80f4fa74e | UNDERPOWERED |
| sspec_ddc9de0c5f54323e43a39d73 | trade_date_block_shuffle | 10359 | BLOCKED | False | True | surrun_26dc3035b04196b70dbb4a89 | UNDERPOWERED |
| sspec_ddc9de0c5f54323e43a39d73 | trade_date_block_shuffle | 10360 | BLOCKED | False | True | surrun_9a7cf65912f707de8d67739b | UNDERPOWERED |
| sspec_ddc9de0c5f54323e43a39d73 | trade_date_block_shuffle | 10361 | BLOCKED | False | True | surrun_8634ea3ee0956b1000ecf8e8 | UNDERPOWERED |
| sspec_77e79d650fc14b8ab88d5049 | trade_date_block_shuffle | 10362 | BLOCKED | False | True | surrun_ea890d054c17b7995e4c2a16 | UNDERPOWERED |
| sspec_77e79d650fc14b8ab88d5049 | trade_date_block_shuffle | 10363 | BLOCKED | False | True | surrun_24cf22b0ed1608037e4953de | UNDERPOWERED |
| sspec_77e79d650fc14b8ab88d5049 | trade_date_block_shuffle | 10364 | BLOCKED | False | True | surrun_139ed0555d1736c44b1d2ae9 | UNDERPOWERED |
| sspec_33fce059c40aa2b6925d3d77 | trade_date_block_shuffle | 10365 | BLOCKED | False | True | surrun_68494aac436bcfa7ec16be83 | UNDERPOWERED |
| sspec_33fce059c40aa2b6925d3d77 | trade_date_block_shuffle | 10366 | BLOCKED | False | True | surrun_d9611da076ec03e2f87a41a9 | UNDERPOWERED |
| sspec_33fce059c40aa2b6925d3d77 | trade_date_block_shuffle | 10367 | BLOCKED | False | True | surrun_269355b5347bf6468479a222 | UNDERPOWERED |
| sspec_74ecbfeb27ea193b58fbcf7a | trade_date_block_shuffle | 10368 | BLOCKED | False | True | surrun_425fb2d798047c85de0b5577 | UNDERPOWERED |
| sspec_74ecbfeb27ea193b58fbcf7a | trade_date_block_shuffle | 10369 | BLOCKED | False | True | surrun_70aca03e4c1e21e1d81fc974 | UNDERPOWERED |
| sspec_74ecbfeb27ea193b58fbcf7a | trade_date_block_shuffle | 10370 | BLOCKED | False | True | surrun_1989c3b84d3962482ce99483 | UNDERPOWERED |
| sspec_eb6e883867ef0bcf6caa7ea0 | trade_date_block_shuffle | 10371 | BLOCKED | False | True | surrun_5c2af76287456fbfa77b3184 | UNDERPOWERED |
| sspec_eb6e883867ef0bcf6caa7ea0 | trade_date_block_shuffle | 10372 | BLOCKED | False | True | surrun_af8a51533f00e79e260534d1 | UNDERPOWERED |
| sspec_eb6e883867ef0bcf6caa7ea0 | trade_date_block_shuffle | 10373 | BLOCKED | False | True | surrun_a51910a3f3b0c9c5c4bae35f | UNDERPOWERED |
| sspec_39056dc8e349ef61860a12ef | trade_date_block_shuffle | 10374 | BLOCKED | False | True | surrun_f3b5dc3283724627311f0c74 | UNDERPOWERED |
| sspec_39056dc8e349ef61860a12ef | trade_date_block_shuffle | 10375 | BLOCKED | False | True | surrun_07ca6612668ec0a0ca5381eb | UNDERPOWERED |
| sspec_39056dc8e349ef61860a12ef | trade_date_block_shuffle | 10376 | BLOCKED | False | True | surrun_de521faafdaab9d2fc144713 | UNDERPOWERED |
| sspec_2019bf333c27491214c06bec | trade_date_block_shuffle | 10377 | BLOCKED | False | True | surrun_6016ae095715bf375e87daf5 | UNDERPOWERED |
| sspec_2019bf333c27491214c06bec | trade_date_block_shuffle | 10378 | BLOCKED | False | True | surrun_b3e3f308db21dcf05452ce00 | UNDERPOWERED |
| sspec_2019bf333c27491214c06bec | trade_date_block_shuffle | 10379 | BLOCKED | False | True | surrun_ea8740bb7d59ae827d521311 | UNDERPOWERED |
| sspec_902fe2e261aeca394476c654 | trade_date_block_shuffle | 10380 | BLOCKED | False | True | surrun_bd127fdfa95dd9649d9b6d76 | UNDERPOWERED |
| sspec_902fe2e261aeca394476c654 | trade_date_block_shuffle | 10381 | BLOCKED | False | True | surrun_2f043dfa7c6f8b7e5fcfd09b | UNDERPOWERED |
| sspec_902fe2e261aeca394476c654 | trade_date_block_shuffle | 10382 | BLOCKED | False | True | surrun_551712183b7c33ede1776347 | UNDERPOWERED |
| sspec_754e4a365bbdfcd447e5cb7e | trade_date_block_shuffle | 10383 | BLOCKED | False | True | surrun_3c6f8c6b1cfd33812522cfbd | UNDERPOWERED |
| sspec_754e4a365bbdfcd447e5cb7e | trade_date_block_shuffle | 10384 | BLOCKED | False | True | surrun_147817314eed6993c802f909 | UNDERPOWERED |
| sspec_754e4a365bbdfcd447e5cb7e | trade_date_block_shuffle | 10385 | BLOCKED | False | True | surrun_10cae7ea7d96de6d81e0ec5d | UNDERPOWERED |
| sspec_6470b2f1421eb6ece96e6fde | trade_date_block_shuffle | 10386 | BLOCKED | False | True | surrun_40c45bc2eaede9438e0d0080 | UNDERPOWERED |
| sspec_6470b2f1421eb6ece96e6fde | trade_date_block_shuffle | 10387 | BLOCKED | False | True | surrun_c975e9a0e5e2745124023539 | UNDERPOWERED |
| sspec_6470b2f1421eb6ece96e6fde | trade_date_block_shuffle | 10388 | BLOCKED | False | True | surrun_a64af4f671390f98abc364b7 | UNDERPOWERED |
| sspec_609da1456836e92dbd115cdf | trade_date_block_shuffle | 10389 | BLOCKED | False | True | surrun_7c1937f2f7f4c7f66ef770da | UNDERPOWERED |
| sspec_609da1456836e92dbd115cdf | trade_date_block_shuffle | 10390 | BLOCKED | False | True | surrun_1345bbb6052db2e33c1b1945 | UNDERPOWERED |
| sspec_609da1456836e92dbd115cdf | trade_date_block_shuffle | 10391 | BLOCKED | False | True | surrun_bae5771fee51fe428655bafe | UNDERPOWERED |
| sspec_c8da1a619406d5fc3640e44d | trade_date_block_shuffle | 10392 | BLOCKED | False | True | surrun_29a1bfda6bdae73051d1292e | UNDERPOWERED |
| sspec_c8da1a619406d5fc3640e44d | trade_date_block_shuffle | 10393 | BLOCKED | False | True | surrun_eef8d7244aec0324e0e4e9f0 | UNDERPOWERED |
| sspec_c8da1a619406d5fc3640e44d | trade_date_block_shuffle | 10394 | BLOCKED | False | True | surrun_4e10861f3b4ef7968e84e0b9 | UNDERPOWERED |
| sspec_354dedf2168616750d27e6e3 | trade_date_block_shuffle | 10395 | BLOCKED | False | True | surrun_d9e7c84c619639423b306351 | UNDERPOWERED |
| sspec_354dedf2168616750d27e6e3 | trade_date_block_shuffle | 10396 | BLOCKED | False | True | surrun_97952450d05eff97aca82a7c | UNDERPOWERED |
| sspec_354dedf2168616750d27e6e3 | trade_date_block_shuffle | 10397 | BLOCKED | False | True | surrun_3fa92b4d34a4436f508dbfd4 | UNDERPOWERED |
| sspec_6f6664bb324f991a702cb6e4 | trade_date_block_shuffle | 10398 | BLOCKED | False | True | surrun_d858a6b95ad95485b9e0545a | UNDERPOWERED |
| sspec_6f6664bb324f991a702cb6e4 | trade_date_block_shuffle | 10399 | BLOCKED | False | True | surrun_4caa1b7398e62e96b4ff9ddb | UNDERPOWERED |
| sspec_6f6664bb324f991a702cb6e4 | trade_date_block_shuffle | 10400 | BLOCKED | False | True | surrun_a7b4aafb5fe2ca49b3e568c3 | UNDERPOWERED |
| sspec_8e35c1b1d7df13139d7c1ead | trade_date_block_shuffle | 10401 | BLOCKED | False | True | surrun_148d588b848a39c16faf03d1 | UNDERPOWERED |
| sspec_8e35c1b1d7df13139d7c1ead | trade_date_block_shuffle | 10402 | BLOCKED | False | True | surrun_f604e6a855d5d993f4ed0a40 | UNDERPOWERED |
| sspec_8e35c1b1d7df13139d7c1ead | trade_date_block_shuffle | 10403 | BLOCKED | False | True | surrun_a371f3328dbad3116342ae92 | UNDERPOWERED |
| sspec_394e0bad380d820aeb30c38e | trade_date_block_shuffle | 10404 | BLOCKED | False | True | surrun_2aca622597a745b99838379c | UNDERPOWERED |
| sspec_394e0bad380d820aeb30c38e | trade_date_block_shuffle | 10405 | BLOCKED | False | True | surrun_fec97fe3399c5ec5cdf697a5 | UNDERPOWERED |
| sspec_394e0bad380d820aeb30c38e | trade_date_block_shuffle | 10406 | BLOCKED | False | True | surrun_27d93fdfdb96aa7372bc9911 | UNDERPOWERED |
| sspec_9cfdad261b45e300fae589c2 | trade_date_block_shuffle | 10407 | BLOCKED | False | True | surrun_b4ecc9a5ad81f2093866216d | UNDERPOWERED |
| sspec_9cfdad261b45e300fae589c2 | trade_date_block_shuffle | 10408 | BLOCKED | False | True | surrun_ffed5023ecbde4fa7f7254b6 | UNDERPOWERED |
| sspec_9cfdad261b45e300fae589c2 | trade_date_block_shuffle | 10409 | BLOCKED | False | True | surrun_be5b2a31c11adae38c298fe3 | UNDERPOWERED |
| sspec_e2969532bad0c415bdcdde8d | trade_date_block_shuffle | 10410 | BLOCKED | False | True | surrun_afb02411a771f936fb05ac4c | UNDERPOWERED |
| sspec_e2969532bad0c415bdcdde8d | trade_date_block_shuffle | 10411 | BLOCKED | False | True | surrun_190b107c19c5c3e6ba47af5e | UNDERPOWERED |
| sspec_e2969532bad0c415bdcdde8d | trade_date_block_shuffle | 10412 | BLOCKED | False | True | surrun_2367230b7ba70efdb2b15e32 | UNDERPOWERED |
| sspec_eac636d3590c41a3d1ddb673 | trade_date_block_shuffle | 10413 | BLOCKED | False | True | surrun_313f529cb79c25519505240d | UNDERPOWERED |
| sspec_eac636d3590c41a3d1ddb673 | trade_date_block_shuffle | 10414 | BLOCKED | False | True | surrun_73bf6d2c6f766f55e29069e7 | UNDERPOWERED |
| sspec_eac636d3590c41a3d1ddb673 | trade_date_block_shuffle | 10415 | BLOCKED | False | True | surrun_60547113786180e9dae4eda4 | UNDERPOWERED |
| sspec_ab299006e49b47c8f49e20fd | trade_date_block_shuffle | 10416 | BLOCKED | False | True | surrun_5ea0d7b07585b3dacaf504f8 | UNDERPOWERED |
| sspec_ab299006e49b47c8f49e20fd | trade_date_block_shuffle | 10417 | BLOCKED | False | True | surrun_242b9a7a95974a1da9471ec7 | UNDERPOWERED |
| sspec_ab299006e49b47c8f49e20fd | trade_date_block_shuffle | 10418 | BLOCKED | False | True | surrun_016e1e7b76b41760802fbea7 | UNDERPOWERED |
| sspec_ae6f5d73a533924661b9b21f | trade_date_block_shuffle | 10419 | BLOCKED | False | True | surrun_a64d1b49debe4a44ee7d596f | UNDERPOWERED |
| sspec_ae6f5d73a533924661b9b21f | trade_date_block_shuffle | 10420 | BLOCKED | False | True | surrun_7412a3a3a435efc4bbf9083e | UNDERPOWERED |
| sspec_ae6f5d73a533924661b9b21f | trade_date_block_shuffle | 10421 | BLOCKED | False | True | surrun_84175dae9dd4ab4f18becd9f | UNDERPOWERED |
| sspec_f71c38f2c8f6d72080bb7280 | trade_date_block_shuffle | 10422 | BLOCKED | False | True | surrun_f15b31d82569bb72641ebf2c | UNDERPOWERED |
| sspec_f71c38f2c8f6d72080bb7280 | trade_date_block_shuffle | 10423 | BLOCKED | False | True | surrun_4ef93e99f4ccc609d0432732 | UNDERPOWERED |
| sspec_f71c38f2c8f6d72080bb7280 | trade_date_block_shuffle | 10424 | BLOCKED | False | True | surrun_e386f55f71e10c735575802d | UNDERPOWERED |
| sspec_d4e5d00971e14494d88fe8bb | trade_date_block_shuffle | 10425 | BLOCKED | False | True | surrun_fa3d2d658aa063cdbf49a120 | UNDERPOWERED |
| sspec_d4e5d00971e14494d88fe8bb | trade_date_block_shuffle | 10426 | BLOCKED | False | True | surrun_8f4bde30e5497d456c868dd6 | UNDERPOWERED |
| sspec_d4e5d00971e14494d88fe8bb | trade_date_block_shuffle | 10427 | BLOCKED | False | True | surrun_e19974672551b88cda521fd1 | UNDERPOWERED |
| sspec_3f7bfd35ea00bc2f4c8ab216 | trade_date_block_shuffle | 10428 | BLOCKED | False | True | surrun_2670eef1d06b95d95808af33 | UNDERPOWERED |
| sspec_3f7bfd35ea00bc2f4c8ab216 | trade_date_block_shuffle | 10429 | BLOCKED | False | True | surrun_506bd637b81a22913d832798 | UNDERPOWERED |
| sspec_3f7bfd35ea00bc2f4c8ab216 | trade_date_block_shuffle | 10430 | BLOCKED | False | True | surrun_2f8e9908083ffbea75c20b1a | UNDERPOWERED |
| sspec_aede76ccf55b93d831fa28df | trade_date_block_shuffle | 10431 | BLOCKED | False | True | surrun_49577135e43df4cb83a7363d | UNDERPOWERED |
| sspec_aede76ccf55b93d831fa28df | trade_date_block_shuffle | 10432 | BLOCKED | False | True | surrun_c7d558558675ef7f648ff19b | UNDERPOWERED |
| sspec_aede76ccf55b93d831fa28df | trade_date_block_shuffle | 10433 | BLOCKED | False | True | surrun_05c769278001c5b9bf23773e | UNDERPOWERED |
| sspec_2ee7653ba6e3c835c8da217f | trade_date_block_shuffle | 10434 | BLOCKED | False | True | surrun_c3f7a7371eef48841a1a06be | UNDERPOWERED |
| sspec_2ee7653ba6e3c835c8da217f | trade_date_block_shuffle | 10435 | BLOCKED | False | True | surrun_3f5379e6b693438bc0954053 | UNDERPOWERED |
| sspec_2ee7653ba6e3c835c8da217f | trade_date_block_shuffle | 10436 | BLOCKED | False | True | surrun_1996c3aa24f43c8e33d428c9 | UNDERPOWERED |
| sspec_ef9bd7515011e9b1229ba215 | trade_date_block_shuffle | 10437 | BLOCKED | False | True | surrun_0219a9f3797a9df539b0dec9 | UNDERPOWERED |
| sspec_ef9bd7515011e9b1229ba215 | trade_date_block_shuffle | 10438 | BLOCKED | False | True | surrun_3afaf2c91cd0bed13477c278 | UNDERPOWERED |
| sspec_ef9bd7515011e9b1229ba215 | trade_date_block_shuffle | 10439 | BLOCKED | False | True | surrun_60063943cbf68c395592f169 | UNDERPOWERED |
| sspec_17c27adb161c73150fa58d57 | trade_date_block_shuffle | 10440 | BLOCKED | False | True | surrun_0f4cb577577121558f2763c7 | UNDERPOWERED |
| sspec_17c27adb161c73150fa58d57 | trade_date_block_shuffle | 10441 | BLOCKED | False | True | surrun_a8c0c1a775a92f5745a21b86 | UNDERPOWERED |
| sspec_17c27adb161c73150fa58d57 | trade_date_block_shuffle | 10442 | BLOCKED | False | True | surrun_e6299632714b4be9a308e737 | UNDERPOWERED |
| sspec_f1faf2df354c116a1903f645 | trade_date_block_shuffle | 10443 | BLOCKED | False | True | surrun_62ba83c3fdab64fa7cb54d22 | UNDERPOWERED |
| sspec_f1faf2df354c116a1903f645 | trade_date_block_shuffle | 10444 | BLOCKED | False | True | surrun_56a0f525a494883dbe57047a | UNDERPOWERED |
| sspec_f1faf2df354c116a1903f645 | trade_date_block_shuffle | 10445 | BLOCKED | False | True | surrun_670c62c4a729067799e0027a | UNDERPOWERED |
| sspec_1d45680b9034a8c700ff54b1 | trade_date_block_shuffle | 10446 | BLOCKED | False | True | surrun_abe42b6a24f2fff362ad0314 | UNDERPOWERED |
| sspec_1d45680b9034a8c700ff54b1 | trade_date_block_shuffle | 10447 | BLOCKED | False | True | surrun_3d699ba2296dcfb175737545 | UNDERPOWERED |
| sspec_1d45680b9034a8c700ff54b1 | trade_date_block_shuffle | 10448 | BLOCKED | False | True | surrun_39150662e97da8b4dc045d85 | UNDERPOWERED |
| sspec_8057ffa61a36f67e9e6307af | trade_date_block_shuffle | 10449 | BLOCKED | False | True | surrun_ae786d715ca9048173f9e84c | UNDERPOWERED |
| sspec_8057ffa61a36f67e9e6307af | trade_date_block_shuffle | 10450 | BLOCKED | False | True | surrun_4608fd558262ee78222e56e8 | UNDERPOWERED |
| sspec_8057ffa61a36f67e9e6307af | trade_date_block_shuffle | 10451 | BLOCKED | False | True | surrun_34d329c9de9d86c91093a3be | UNDERPOWERED |
| sspec_a8203d45deee12d65e4ec641 | trade_date_block_shuffle | 10452 | BLOCKED | False | True | surrun_d2226a086724459989e1d44a | UNDERPOWERED |
| sspec_a8203d45deee12d65e4ec641 | trade_date_block_shuffle | 10453 | BLOCKED | False | True | surrun_de0003dd20be281827928473 | UNDERPOWERED |
| sspec_a8203d45deee12d65e4ec641 | trade_date_block_shuffle | 10454 | BLOCKED | False | True | surrun_49f8714ec78482f8d97c66f3 | UNDERPOWERED |
| sspec_b3eec8ad6c4b112b3bd80a85 | trade_date_block_shuffle | 10455 | BLOCKED | False | True | surrun_8f0f34a124fe5c43deeb08fd | UNDERPOWERED |
| sspec_b3eec8ad6c4b112b3bd80a85 | trade_date_block_shuffle | 10456 | BLOCKED | False | True | surrun_7eff3075064135a2a479df3a | UNDERPOWERED |
| sspec_b3eec8ad6c4b112b3bd80a85 | trade_date_block_shuffle | 10457 | BLOCKED | False | True | surrun_2292dca918f4dfe41f4dc5e0 | UNDERPOWERED |
| sspec_adb4a00400ed2741e8e3b8d5 | trade_date_block_shuffle | 10458 | BLOCKED | False | True | surrun_7f0172be90d28e099656c74f | UNDERPOWERED |
| sspec_adb4a00400ed2741e8e3b8d5 | trade_date_block_shuffle | 10459 | BLOCKED | False | True | surrun_8092fb3d5caebb679f8d43af | UNDERPOWERED |
| sspec_adb4a00400ed2741e8e3b8d5 | trade_date_block_shuffle | 10460 | BLOCKED | False | True | surrun_78a4ea04020320a4b98406cb | UNDERPOWERED |
| sspec_d0c40d9ac5a8647f613bdeea | trade_date_block_shuffle | 10461 | BLOCKED | False | True | surrun_9e3e217f2517463c025781cc | UNDERPOWERED |
| sspec_d0c40d9ac5a8647f613bdeea | trade_date_block_shuffle | 10462 | BLOCKED | False | True | surrun_94cea03a0ec76c2e8d36afc1 | UNDERPOWERED |
| sspec_d0c40d9ac5a8647f613bdeea | trade_date_block_shuffle | 10463 | BLOCKED | False | True | surrun_c97ddecfc42cdc823e427b40 | UNDERPOWERED |
| sspec_b24e20c46d7d64092278d903 | trade_date_block_shuffle | 10464 | BLOCKED | False | True | surrun_bc59324671b438fe6c4d0524 | UNDERPOWERED |
| sspec_b24e20c46d7d64092278d903 | trade_date_block_shuffle | 10465 | BLOCKED | False | True | surrun_a40f23dba589113945ae73a9 | UNDERPOWERED |
| sspec_b24e20c46d7d64092278d903 | trade_date_block_shuffle | 10466 | BLOCKED | False | True | surrun_ebd4758953b01c536c9a780b | UNDERPOWERED |
| sspec_110149bdceeea19e9dceefcf | trade_date_block_shuffle | 10467 | BLOCKED | False | True | surrun_390d6458edaf9e542686e889 | UNDERPOWERED |
| sspec_110149bdceeea19e9dceefcf | trade_date_block_shuffle | 10468 | BLOCKED | False | True | surrun_ca2c78178eb5307f3c429544 | UNDERPOWERED |
| sspec_110149bdceeea19e9dceefcf | trade_date_block_shuffle | 10469 | BLOCKED | False | True | surrun_fa0e0144cecd07469fe1bb7e | UNDERPOWERED |
| sspec_2322292e7077f8d14ec28437 | trade_date_block_shuffle | 10470 | BLOCKED | False | True | surrun_cc81a7ffcca4f0641164c61c | UNDERPOWERED |
| sspec_2322292e7077f8d14ec28437 | trade_date_block_shuffle | 10471 | BLOCKED | False | True | surrun_39de7725bfdff246f3dd8994 | UNDERPOWERED |
| sspec_2322292e7077f8d14ec28437 | trade_date_block_shuffle | 10472 | BLOCKED | False | True | surrun_be19fe5f4f7cbf85ed247f8e | UNDERPOWERED |
| sspec_04208fd0f968d503db6b928d | trade_date_block_shuffle | 10473 | BLOCKED | False | True | surrun_558b1407e5a914a7bcf2bd51 | UNDERPOWERED |
| sspec_04208fd0f968d503db6b928d | trade_date_block_shuffle | 10474 | BLOCKED | False | True | surrun_864e0eab0ce0bfbb2c6f8739 | UNDERPOWERED |
| sspec_04208fd0f968d503db6b928d | trade_date_block_shuffle | 10475 | BLOCKED | False | True | surrun_4a4afcef13c345817d117534 | UNDERPOWERED |
| sspec_07962b3c7cdd5285b7a90b8e | trade_date_block_shuffle | 10476 | BLOCKED | False | True | surrun_5ff612e799b75b1a3aa3c1b9 | UNDERPOWERED |
| sspec_07962b3c7cdd5285b7a90b8e | trade_date_block_shuffle | 10477 | BLOCKED | False | True | surrun_2d4da01131adbcce8a55acf9 | UNDERPOWERED |
| sspec_07962b3c7cdd5285b7a90b8e | trade_date_block_shuffle | 10478 | BLOCKED | False | True | surrun_e3bc78cd3ebad2815cf6c6f6 | UNDERPOWERED |
| sspec_f8c1786bccab51f017ec0e51 | trade_date_block_shuffle | 10479 | BLOCKED | False | True | surrun_430e4b4d0a32b9c75344671f | UNDERPOWERED |
| sspec_f8c1786bccab51f017ec0e51 | trade_date_block_shuffle | 10480 | BLOCKED | False | True | surrun_b7b2134336afaabf620b6968 | UNDERPOWERED |
| sspec_f8c1786bccab51f017ec0e51 | trade_date_block_shuffle | 10481 | BLOCKED | False | True | surrun_6bca7b297cdfa1d65e668e59 | UNDERPOWERED |
| sspec_5807b332c4c741464c2dc06e | trade_date_block_shuffle | 10482 | BLOCKED | False | True | surrun_b976295c36d86f45d4014eb3 | UNDERPOWERED |
| sspec_5807b332c4c741464c2dc06e | trade_date_block_shuffle | 10483 | BLOCKED | False | True | surrun_f8680337894ea4380a166bf5 | UNDERPOWERED |
| sspec_5807b332c4c741464c2dc06e | trade_date_block_shuffle | 10484 | BLOCKED | False | True | surrun_5ef41a0ea829ad31c5cab30a | UNDERPOWERED |
| sspec_02aa1be0dbafd34c64a6076c | trade_date_block_shuffle | 10485 | BLOCKED | False | True | surrun_fe5f6587141948c07b0f3979 | UNDERPOWERED |
| sspec_02aa1be0dbafd34c64a6076c | trade_date_block_shuffle | 10486 | BLOCKED | False | True | surrun_099539d9e9aa320106c26d8b | UNDERPOWERED |
| sspec_02aa1be0dbafd34c64a6076c | trade_date_block_shuffle | 10487 | BLOCKED | False | True | surrun_3334ba33e070b0af65338fe4 | UNDERPOWERED |
| sspec_29d1efb36981ab31ef6fbc58 | trade_date_block_shuffle | 10488 | BLOCKED | False | True | surrun_be67ff66c7f8fcb521d5bdaf | UNDERPOWERED |
| sspec_29d1efb36981ab31ef6fbc58 | trade_date_block_shuffle | 10489 | BLOCKED | False | True | surrun_497b44279971393c97e337ed | UNDERPOWERED |
| sspec_29d1efb36981ab31ef6fbc58 | trade_date_block_shuffle | 10490 | BLOCKED | False | True | surrun_b79abda8867909326b294c4e | UNDERPOWERED |
| sspec_e5566b9e10f04ce8be8d2cb4 | trade_date_block_shuffle | 10491 | BLOCKED | False | True | surrun_cdc29cc78ce41c43b6624c5e | UNDERPOWERED |
| sspec_e5566b9e10f04ce8be8d2cb4 | trade_date_block_shuffle | 10492 | BLOCKED | False | True | surrun_6c49e974dc36a0a49863d84e | UNDERPOWERED |
| sspec_e5566b9e10f04ce8be8d2cb4 | trade_date_block_shuffle | 10493 | BLOCKED | False | True | surrun_ff226691c302b3653e051f65 | UNDERPOWERED |
| sspec_7595bde76e8919c10e6c3e55 | trade_date_block_shuffle | 10494 | BLOCKED | False | True | surrun_bcf6adf3071f6e6f8dd0488a | UNDERPOWERED |
| sspec_7595bde76e8919c10e6c3e55 | trade_date_block_shuffle | 10495 | BLOCKED | False | True | surrun_5c5380037f4ae4d056a3f527 | UNDERPOWERED |
| sspec_7595bde76e8919c10e6c3e55 | trade_date_block_shuffle | 10496 | BLOCKED | False | True | surrun_1f3c968fd38fc8cc0946d456 | UNDERPOWERED |
| sspec_5c0eb83a23aebfc9cf7e41d0 | trade_date_block_shuffle | 10497 | BLOCKED | False | True | surrun_353cde4d4b84eaa5ea7d10b0 | UNDERPOWERED |
| sspec_5c0eb83a23aebfc9cf7e41d0 | trade_date_block_shuffle | 10498 | BLOCKED | False | True | surrun_01a83e257393bcca1ea879c9 | UNDERPOWERED |
| sspec_5c0eb83a23aebfc9cf7e41d0 | trade_date_block_shuffle | 10499 | BLOCKED | False | True | surrun_bf8e3f0606c382803701043d | UNDERPOWERED |
| sspec_052cf9ee1b5ff7e9316677e6 | trade_date_block_shuffle | 10500 | BLOCKED | False | True | surrun_0c9e2ab0ba4b442d5e3d0bd4 | UNDERPOWERED |
| sspec_052cf9ee1b5ff7e9316677e6 | trade_date_block_shuffle | 10501 | BLOCKED | False | True | surrun_2fddbb837361c6e9d5224318 | UNDERPOWERED |
| sspec_052cf9ee1b5ff7e9316677e6 | trade_date_block_shuffle | 10502 | BLOCKED | False | True | surrun_062be68ea164e52ababef0b4 | UNDERPOWERED |
| sspec_83c30348db61cd4766c3bff4 | trade_date_block_shuffle | 10503 | BLOCKED | False | True | surrun_326895a160c397bd51538b56 | UNDERPOWERED |
| sspec_83c30348db61cd4766c3bff4 | trade_date_block_shuffle | 10504 | BLOCKED | False | True | surrun_78c24e43e9efa552ecd7407f | UNDERPOWERED |
| sspec_83c30348db61cd4766c3bff4 | trade_date_block_shuffle | 10505 | BLOCKED | False | True | surrun_cef3f1de553439e5cc3ffa51 | UNDERPOWERED |
| sspec_2ed84100bebce0f3bde43c4a | trade_date_block_shuffle | 10506 | BLOCKED | False | True | surrun_e0453f187db1438e2bcdfa36 | UNDERPOWERED |
| sspec_2ed84100bebce0f3bde43c4a | trade_date_block_shuffle | 10507 | BLOCKED | False | True | surrun_5e905ea2c10c925d013b1252 | UNDERPOWERED |
| sspec_2ed84100bebce0f3bde43c4a | trade_date_block_shuffle | 10508 | BLOCKED | False | True | surrun_0732514b9d28ffbaa66cc0a1 | UNDERPOWERED |
| sspec_40b4f9aa123444157b924c10 | trade_date_block_shuffle | 10509 | BLOCKED | False | True | surrun_76eeb929eac122460d5b5589 | UNDERPOWERED |
| sspec_40b4f9aa123444157b924c10 | trade_date_block_shuffle | 10510 | BLOCKED | False | True | surrun_d54dab815a6541cb78a01faa | UNDERPOWERED |
| sspec_40b4f9aa123444157b924c10 | trade_date_block_shuffle | 10511 | BLOCKED | False | True | surrun_304d0f2867841a07046acea5 | UNDERPOWERED |
| sspec_164096c781a02562639d3dc6 | trade_date_block_shuffle | 10512 | BLOCKED | False | True | surrun_ef1228174c344462c9b673fe | UNDERPOWERED |
| sspec_164096c781a02562639d3dc6 | trade_date_block_shuffle | 10513 | BLOCKED | False | True | surrun_943b8f53406cf4f9c5b389b8 | UNDERPOWERED |
| sspec_164096c781a02562639d3dc6 | trade_date_block_shuffle | 10514 | BLOCKED | False | True | surrun_fd0352fede4d79f074ddb7b8 | UNDERPOWERED |
| sspec_96dd5b855fd22a10b9a570cf | trade_date_block_shuffle | 10515 | BLOCKED | False | True | surrun_a6722d5b0e14565a742e61b7 | UNDERPOWERED |
| sspec_96dd5b855fd22a10b9a570cf | trade_date_block_shuffle | 10516 | BLOCKED | False | True | surrun_5f5837cc49ca67be13dfe3bd | UNDERPOWERED |
| sspec_96dd5b855fd22a10b9a570cf | trade_date_block_shuffle | 10517 | BLOCKED | False | True | surrun_887dd75a164f801bd9fb72bd | UNDERPOWERED |
| sspec_d1fb71f61e8abd8fd45dc747 | trade_date_block_shuffle | 10518 | BLOCKED | False | True | surrun_45ef48b9a470a4787cd761ac | UNDERPOWERED |
| sspec_d1fb71f61e8abd8fd45dc747 | trade_date_block_shuffle | 10519 | BLOCKED | False | True | surrun_52cc073540bfc764a9f78a7f | UNDERPOWERED |
| sspec_d1fb71f61e8abd8fd45dc747 | trade_date_block_shuffle | 10520 | BLOCKED | False | True | surrun_d3bf140832efdf8e45058550 | UNDERPOWERED |
| sspec_c71283e94471ff7ca49035f5 | trade_date_block_shuffle | 10521 | BLOCKED | False | True | surrun_69c9dd349e03be51280429a0 | UNDERPOWERED |
| sspec_c71283e94471ff7ca49035f5 | trade_date_block_shuffle | 10522 | BLOCKED | False | True | surrun_028755d098d63121805347a1 | UNDERPOWERED |
| sspec_c71283e94471ff7ca49035f5 | trade_date_block_shuffle | 10523 | BLOCKED | False | True | surrun_b8846d3f67fe7a825a35581e | UNDERPOWERED |
| sspec_ee70d232a0194368ca134607 | trade_date_block_shuffle | 10524 | BLOCKED | False | True | surrun_fb56a70de6167bd618353d9b | UNDERPOWERED |
| sspec_ee70d232a0194368ca134607 | trade_date_block_shuffle | 10525 | BLOCKED | False | True | surrun_1d03501751587985d35f9b7d | UNDERPOWERED |
| sspec_ee70d232a0194368ca134607 | trade_date_block_shuffle | 10526 | BLOCKED | False | True | surrun_1419b5b5601c9078982f1d88 | UNDERPOWERED |
| sspec_cf7b281007393c141d0c8de2 | trade_date_block_shuffle | 10527 | BLOCKED | False | True | surrun_48ec51ea009dd778b4798291 | UNDERPOWERED |
| sspec_cf7b281007393c141d0c8de2 | trade_date_block_shuffle | 10528 | BLOCKED | False | True | surrun_0a8600a965169a5135379e4f | UNDERPOWERED |
| sspec_cf7b281007393c141d0c8de2 | trade_date_block_shuffle | 10529 | BLOCKED | False | True | surrun_0358dd0098f3cf5224c385d3 | UNDERPOWERED |
| sspec_74e21ea3e1cf81fa757e6ceb | trade_date_block_shuffle | 10530 | BLOCKED | False | True | surrun_e2e403ed4e1a7c05def152d9 | UNDERPOWERED |
| sspec_74e21ea3e1cf81fa757e6ceb | trade_date_block_shuffle | 10531 | BLOCKED | False | True | surrun_710d5792d81a7a6be6eec4a1 | UNDERPOWERED |
| sspec_74e21ea3e1cf81fa757e6ceb | trade_date_block_shuffle | 10532 | BLOCKED | False | True | surrun_e1859c9efeca03547a60eaa2 | UNDERPOWERED |
| sspec_5ba3e409a2e1532a310a7030 | trade_date_block_shuffle | 10533 | BLOCKED | False | True | surrun_78111a0ae1f2f66daea9b7a4 | UNDERPOWERED |
| sspec_5ba3e409a2e1532a310a7030 | trade_date_block_shuffle | 10534 | BLOCKED | False | True | surrun_d3ef001f1feb0a653d917383 | UNDERPOWERED |
| sspec_5ba3e409a2e1532a310a7030 | trade_date_block_shuffle | 10535 | BLOCKED | False | True | surrun_af2cc46084a30e2d132d2df4 | UNDERPOWERED |
| sspec_fc8deb1fca3b12e8ba85cb25 | trade_date_block_shuffle | 10536 | BLOCKED | False | True | surrun_4bb49a2d83ccf7c32e3b12d5 | UNDERPOWERED |
| sspec_fc8deb1fca3b12e8ba85cb25 | trade_date_block_shuffle | 10537 | BLOCKED | False | True | surrun_f4c5c8c78183eb07c264db41 | UNDERPOWERED |
| sspec_fc8deb1fca3b12e8ba85cb25 | trade_date_block_shuffle | 10538 | BLOCKED | False | True | surrun_b22889cd738e4e7c850aa9f5 | UNDERPOWERED |
| sspec_d28894b236877b2f4a7e506d | trade_date_block_shuffle | 10539 | BLOCKED | False | True | surrun_c2800245d623a837679e07ea | UNDERPOWERED |
| sspec_d28894b236877b2f4a7e506d | trade_date_block_shuffle | 10540 | BLOCKED | False | True | surrun_d45da9f3771cf27728501303 | UNDERPOWERED |
| sspec_d28894b236877b2f4a7e506d | trade_date_block_shuffle | 10541 | BLOCKED | False | True | surrun_9b150bb2506116c2a2db9bf7 | UNDERPOWERED |
| sspec_4dc02697c7337f70a86414c8 | trade_date_block_shuffle | 10542 | BLOCKED | False | True | surrun_b549051656b688ab55b66014 | UNDERPOWERED |
| sspec_4dc02697c7337f70a86414c8 | trade_date_block_shuffle | 10543 | BLOCKED | False | True | surrun_ca6c9d0eeaa67adfa15850d1 | UNDERPOWERED |
| sspec_4dc02697c7337f70a86414c8 | trade_date_block_shuffle | 10544 | BLOCKED | False | True | surrun_ae7a6b3b21985005c3d3ac3c | UNDERPOWERED |
| sspec_7e89938f0cfbe29b4b97e992 | trade_date_block_shuffle | 10545 | BLOCKED | False | True | surrun_22c9b823ccb46f23f2b8d2f8 | UNDERPOWERED |
| sspec_7e89938f0cfbe29b4b97e992 | trade_date_block_shuffle | 10546 | BLOCKED | False | True | surrun_9ed3ac86bd63acadbf55dd74 | UNDERPOWERED |
| sspec_7e89938f0cfbe29b4b97e992 | trade_date_block_shuffle | 10547 | BLOCKED | False | True | surrun_b46aa203f15e5023d5c01c7b | UNDERPOWERED |
| sspec_ef66f8041030a4b41c45a19b | trade_date_block_shuffle | 10548 | BLOCKED | False | True | surrun_8b07be54d2c789ec12b308e8 | UNDERPOWERED |
| sspec_ef66f8041030a4b41c45a19b | trade_date_block_shuffle | 10549 | BLOCKED | False | True | surrun_ae237e1e9fc9d98d84fe1e58 | UNDERPOWERED |
| sspec_ef66f8041030a4b41c45a19b | trade_date_block_shuffle | 10550 | BLOCKED | False | True | surrun_8ec116bf94f3d67b269355dd | UNDERPOWERED |
| sspec_067e488423dfec12353e07dd | trade_date_block_shuffle | 10551 | BLOCKED | False | True | surrun_797aee7c1e701cbf707656ca | UNDERPOWERED |
| sspec_067e488423dfec12353e07dd | trade_date_block_shuffle | 10552 | BLOCKED | False | True | surrun_1e9701d14c8df1d097854f3b | UNDERPOWERED |
| sspec_067e488423dfec12353e07dd | trade_date_block_shuffle | 10553 | BLOCKED | False | True | surrun_739f8db948599ff015138dc0 | UNDERPOWERED |
| sspec_1b09ce1e013ce197b6e4e002 | trade_date_block_shuffle | 10554 | BLOCKED | False | True | surrun_563a177046c034afa6a387de | UNDERPOWERED |
| sspec_1b09ce1e013ce197b6e4e002 | trade_date_block_shuffle | 10555 | BLOCKED | False | True | surrun_2dfbe8647f12ae8a90112010 | UNDERPOWERED |
| sspec_1b09ce1e013ce197b6e4e002 | trade_date_block_shuffle | 10556 | BLOCKED | False | True | surrun_55e5877f02b3024207e28f03 | UNDERPOWERED |
| sspec_4ae7d2e32d83c6011139b625 | trade_date_block_shuffle | 10557 | BLOCKED | False | True | surrun_cfbb9da69149d3485c43a98b | UNDERPOWERED |
| sspec_4ae7d2e32d83c6011139b625 | trade_date_block_shuffle | 10558 | BLOCKED | False | True | surrun_6531ffdcf9851a69b0c5fde3 | UNDERPOWERED |
| sspec_4ae7d2e32d83c6011139b625 | trade_date_block_shuffle | 10559 | BLOCKED | False | True | surrun_45f9e68897628cf8f82de5bb | UNDERPOWERED |
| sspec_21c8a263cc97beb02ac32969 | trade_date_block_shuffle | 10560 | BLOCKED | False | True | surrun_e8f231dab545f641ee4a2d44 | UNDERPOWERED |
| sspec_21c8a263cc97beb02ac32969 | trade_date_block_shuffle | 10561 | BLOCKED | False | True | surrun_913cbb403fd388dc93980719 | UNDERPOWERED |
| sspec_21c8a263cc97beb02ac32969 | trade_date_block_shuffle | 10562 | BLOCKED | False | True | surrun_e233681c7c41864f64df60fc | UNDERPOWERED |
| sspec_aa2b07899713e16242243041 | trade_date_block_shuffle | 10563 | BLOCKED | False | True | surrun_f8b4db1a08c8202a10701a35 | UNDERPOWERED |
| sspec_aa2b07899713e16242243041 | trade_date_block_shuffle | 10564 | BLOCKED | False | True | surrun_746497a936385c17abc749c5 | UNDERPOWERED |
| sspec_aa2b07899713e16242243041 | trade_date_block_shuffle | 10565 | BLOCKED | False | True | surrun_25d65dac479f89b727b063a3 | UNDERPOWERED |
| sspec_ad97188a76423bbc2679ba08 | trade_date_block_shuffle | 10566 | BLOCKED | False | True | surrun_245fbb96c09361aba030ab22 | UNDERPOWERED |
| sspec_ad97188a76423bbc2679ba08 | trade_date_block_shuffle | 10567 | BLOCKED | False | True | surrun_c8e38daa7384c8d624146024 | UNDERPOWERED |
| sspec_ad97188a76423bbc2679ba08 | trade_date_block_shuffle | 10568 | BLOCKED | False | True | surrun_041d011b51863a731bec27c3 | UNDERPOWERED |
| sspec_d3bab2c1a6cda92abeb5c2d8 | trade_date_block_shuffle | 10569 | BLOCKED | False | True | surrun_d0cdac8f735bfd3eb4c72efb | UNDERPOWERED |
| sspec_d3bab2c1a6cda92abeb5c2d8 | trade_date_block_shuffle | 10570 | BLOCKED | False | True | surrun_2d788c8cfb16c689cbb446dc | UNDERPOWERED |
| sspec_d3bab2c1a6cda92abeb5c2d8 | trade_date_block_shuffle | 10571 | BLOCKED | False | True | surrun_47960a4e6db575212f1c3ba4 | UNDERPOWERED |
| sspec_f9822cbdf44fe9740f30534b | trade_date_block_shuffle | 10572 | BLOCKED | False | True | surrun_e565db63fb34dc2a09bd2434 | UNDERPOWERED |
| sspec_f9822cbdf44fe9740f30534b | trade_date_block_shuffle | 10573 | BLOCKED | False | True | surrun_9edcb3dc6c9ffbbb5cbad273 | UNDERPOWERED |
| sspec_f9822cbdf44fe9740f30534b | trade_date_block_shuffle | 10574 | BLOCKED | False | True | surrun_09f053a7b8d96e3f50ee34e5 | UNDERPOWERED |
| sspec_7842b503d31dcce000f60970 | trade_date_block_shuffle | 10575 | BLOCKED | False | True | surrun_04cfcae763633567b035cbc6 | UNDERPOWERED |
| sspec_7842b503d31dcce000f60970 | trade_date_block_shuffle | 10576 | BLOCKED | False | True | surrun_9907990e20644bc0c04d279e | UNDERPOWERED |
| sspec_7842b503d31dcce000f60970 | trade_date_block_shuffle | 10577 | BLOCKED | False | True | surrun_e73963f264987f6dc69460b1 | UNDERPOWERED |
| sspec_5c9ea306c49bd4a1ec8a9089 | trade_date_block_shuffle | 10578 | BLOCKED | False | True | surrun_6ab6b2194870c8e5c71dc455 | UNDERPOWERED |
| sspec_5c9ea306c49bd4a1ec8a9089 | trade_date_block_shuffle | 10579 | BLOCKED | False | True | surrun_f694901a0d0e727b34f22318 | UNDERPOWERED |
| sspec_5c9ea306c49bd4a1ec8a9089 | trade_date_block_shuffle | 10580 | BLOCKED | False | True | surrun_152372e5564314bd5fa0a827 | UNDERPOWERED |
| sspec_4d8d7758f58baf634eb6021e | trade_date_block_shuffle | 10581 | BLOCKED | False | True | surrun_8ccd9e96eb479abb47e4fe7a | UNDERPOWERED |
| sspec_4d8d7758f58baf634eb6021e | trade_date_block_shuffle | 10582 | BLOCKED | False | True | surrun_111d0a275aacfa3d12c7bdfb | UNDERPOWERED |
| sspec_4d8d7758f58baf634eb6021e | trade_date_block_shuffle | 10583 | BLOCKED | False | True | surrun_26ae1ce4e9afaf55d144a0da | UNDERPOWERED |
| sspec_0b40edf4516ecf1821419b13 | trade_date_block_shuffle | 10584 | BLOCKED | False | True | surrun_bfa67e2902a0081e8ba2ca20 | UNDERPOWERED |
| sspec_0b40edf4516ecf1821419b13 | trade_date_block_shuffle | 10585 | BLOCKED | False | True | surrun_5fa65e489778b9ce7cc6cc19 | UNDERPOWERED |
| sspec_0b40edf4516ecf1821419b13 | trade_date_block_shuffle | 10586 | BLOCKED | False | True | surrun_be635c8a8c73290e4a25cb01 | UNDERPOWERED |
| sspec_826617ba3ab69d8dca62b979 | trade_date_block_shuffle | 10587 | BLOCKED | False | True | surrun_7ac343d4507c7d177a4fb27a | UNDERPOWERED |
| sspec_826617ba3ab69d8dca62b979 | trade_date_block_shuffle | 10588 | BLOCKED | False | True | surrun_a6074217506a8fb30527e70b | UNDERPOWERED |
| sspec_826617ba3ab69d8dca62b979 | trade_date_block_shuffle | 10589 | BLOCKED | False | True | surrun_caf1616f152d33f89e31306e | UNDERPOWERED |
| sspec_cbe5c88a0a16fcf8a76b84d6 | trade_date_block_shuffle | 10590 | BLOCKED | False | True | surrun_50223e80574af11195906b01 | UNDERPOWERED |
| sspec_cbe5c88a0a16fcf8a76b84d6 | trade_date_block_shuffle | 10591 | BLOCKED | False | True | surrun_726b5745861d5e103609bbc7 | UNDERPOWERED |
| sspec_cbe5c88a0a16fcf8a76b84d6 | trade_date_block_shuffle | 10592 | BLOCKED | False | True | surrun_eb316bf0b38e9f28e6e6a223 | UNDERPOWERED |
| sspec_319e858af7072a237e8dc7bc | trade_date_block_shuffle | 10593 | BLOCKED | False | True | surrun_2e696c6753d99e0127c4c5d7 | UNDERPOWERED |
| sspec_319e858af7072a237e8dc7bc | trade_date_block_shuffle | 10594 | BLOCKED | False | True | surrun_ad9a1486acf432082ebc7a49 | UNDERPOWERED |
| sspec_319e858af7072a237e8dc7bc | trade_date_block_shuffle | 10595 | BLOCKED | False | True | surrun_fad6d6da285d182871a6c709 | UNDERPOWERED |
| sspec_846c085c370f172adecc1497 | trade_date_block_shuffle | 10596 | BLOCKED | False | True | surrun_00f0f89420a72191a8ca7324 | UNDERPOWERED |
| sspec_846c085c370f172adecc1497 | trade_date_block_shuffle | 10597 | BLOCKED | False | True | surrun_054ed5b7732836b6e9b8cb6f | UNDERPOWERED |
| sspec_846c085c370f172adecc1497 | trade_date_block_shuffle | 10598 | BLOCKED | False | True | surrun_1e4c76921b198a61b56131cc | UNDERPOWERED |
| sspec_fe5fba941c4a57a9043a1e53 | trade_date_block_shuffle | 10599 | BLOCKED | False | True | surrun_f6b4700f4596cfdfbe0e89ea | UNDERPOWERED |
| sspec_fe5fba941c4a57a9043a1e53 | trade_date_block_shuffle | 10600 | BLOCKED | False | True | surrun_2dd1c763af88bebe808ba7b5 | UNDERPOWERED |
| sspec_fe5fba941c4a57a9043a1e53 | trade_date_block_shuffle | 10601 | BLOCKED | False | True | surrun_b953149ad1251236206ebf95 | UNDERPOWERED |
| sspec_13ea42ec55291487bf5f6eff | trade_date_block_shuffle | 10602 | BLOCKED | False | True | surrun_f1e2ee0f5577134595fa3e8b | UNDERPOWERED |
| sspec_13ea42ec55291487bf5f6eff | trade_date_block_shuffle | 10603 | BLOCKED | False | True | surrun_0d8cf89bb785a507f13df954 | UNDERPOWERED |
| sspec_13ea42ec55291487bf5f6eff | trade_date_block_shuffle | 10604 | BLOCKED | False | True | surrun_c5a20da5b90e7a01ae60da21 | UNDERPOWERED |
| sspec_3b5c823842b62761e9089f4b | trade_date_block_shuffle | 10605 | BLOCKED | False | True | surrun_d6c03082a21c067ed7a37414 | UNDERPOWERED |
| sspec_3b5c823842b62761e9089f4b | trade_date_block_shuffle | 10606 | BLOCKED | False | True | surrun_53e2c79560ba688e59ef74f9 | UNDERPOWERED |
| sspec_3b5c823842b62761e9089f4b | trade_date_block_shuffle | 10607 | BLOCKED | False | True | surrun_4aed2d3e1197ae08e8a57ac9 | UNDERPOWERED |
| sspec_b452cf5a31e24967eead6013 | trade_date_block_shuffle | 10608 | BLOCKED | False | True | surrun_3ec0638b7db6570d481e0202 | UNDERPOWERED |
| sspec_b452cf5a31e24967eead6013 | trade_date_block_shuffle | 10609 | BLOCKED | False | True | surrun_1382026769d135941c8ed09d | UNDERPOWERED |
| sspec_b452cf5a31e24967eead6013 | trade_date_block_shuffle | 10610 | BLOCKED | False | True | surrun_b515991337a340294c3e8635 | UNDERPOWERED |
| sspec_f7bb920147cf52502e3c97a1 | trade_date_block_shuffle | 10611 | BLOCKED | False | True | surrun_c0a40b33769bf2bb94cfeee4 | UNDERPOWERED |
| sspec_f7bb920147cf52502e3c97a1 | trade_date_block_shuffle | 10612 | BLOCKED | False | True | surrun_0e369fbaa7b4e8203ab8dbd7 | UNDERPOWERED |
| sspec_f7bb920147cf52502e3c97a1 | trade_date_block_shuffle | 10613 | BLOCKED | False | True | surrun_d22db5d30e4c83101b5f0410 | UNDERPOWERED |
| sspec_24c31450a01e00016f123a36 | trade_date_block_shuffle | 10614 | BLOCKED | False | True | surrun_d41b8b559f608be09664ab67 | UNDERPOWERED |
| sspec_24c31450a01e00016f123a36 | trade_date_block_shuffle | 10615 | BLOCKED | False | True | surrun_30dfc648642efacc0f884227 | UNDERPOWERED |
| sspec_24c31450a01e00016f123a36 | trade_date_block_shuffle | 10616 | BLOCKED | False | True | surrun_2e70da160993f1191022749d | UNDERPOWERED |
| sspec_9824aede42ef1384d9d2c702 | trade_date_block_shuffle | 10617 | BLOCKED | False | True | surrun_043c056c8744b9690e14f0ba | UNDERPOWERED |
| sspec_9824aede42ef1384d9d2c702 | trade_date_block_shuffle | 10618 | BLOCKED | False | True | surrun_88738136a9fbfee73e96ae5e | UNDERPOWERED |
| sspec_9824aede42ef1384d9d2c702 | trade_date_block_shuffle | 10619 | BLOCKED | False | True | surrun_9bde4654cc6cd159fa8c6421 | UNDERPOWERED |
| sspec_f7172b69599ff0eecfa1c4cd | trade_date_block_shuffle | 10620 | BLOCKED | False | True | surrun_04b18ac908534af1403f7565 | UNDERPOWERED |
| sspec_f7172b69599ff0eecfa1c4cd | trade_date_block_shuffle | 10621 | BLOCKED | False | True | surrun_23f712a7e3b98547974b4279 | UNDERPOWERED |
| sspec_f7172b69599ff0eecfa1c4cd | trade_date_block_shuffle | 10622 | BLOCKED | False | True | surrun_6da6b93e9a69bbad8e83750e | UNDERPOWERED |
| sspec_437ae10c3a8a1a36d133c1cc | trade_date_block_shuffle | 10623 | BLOCKED | False | True | surrun_9eae5c22bb79e10614878f83 | UNDERPOWERED |
| sspec_437ae10c3a8a1a36d133c1cc | trade_date_block_shuffle | 10624 | BLOCKED | False | True | surrun_f60b6649e411516f0c202380 | UNDERPOWERED |
| sspec_437ae10c3a8a1a36d133c1cc | trade_date_block_shuffle | 10625 | BLOCKED | False | True | surrun_5fd70450cdb60cb7e494567c | UNDERPOWERED |
| sspec_cbd8ab82ff5228e6140767f6 | trade_date_block_shuffle | 10626 | BLOCKED | False | True | surrun_f256be0589271dc1bfc6a723 | UNDERPOWERED |
| sspec_cbd8ab82ff5228e6140767f6 | trade_date_block_shuffle | 10627 | BLOCKED | False | True | surrun_c3d48849de45de02caf93507 | UNDERPOWERED |
| sspec_cbd8ab82ff5228e6140767f6 | trade_date_block_shuffle | 10628 | BLOCKED | False | True | surrun_3129561a1125eb6dc6180eb8 | UNDERPOWERED |
| sspec_7ccfdc13442fa25b5a64620f | trade_date_block_shuffle | 10629 | BLOCKED | False | True | surrun_d5b73635f9a96572785aa907 | UNDERPOWERED |
| sspec_7ccfdc13442fa25b5a64620f | trade_date_block_shuffle | 10630 | BLOCKED | False | True | surrun_ffcd6eac9820f3d2cba5b679 | UNDERPOWERED |
| sspec_7ccfdc13442fa25b5a64620f | trade_date_block_shuffle | 10631 | BLOCKED | False | True | surrun_1d3323fc53e57befbf0ee745 | UNDERPOWERED |
| sspec_5f30e440e1f00e2fc4fad420 | trade_date_block_shuffle | 10632 | BLOCKED | False | True | surrun_9e2e6a58831b5534905c0fd4 | UNDERPOWERED |
| sspec_5f30e440e1f00e2fc4fad420 | trade_date_block_shuffle | 10633 | BLOCKED | False | True | surrun_b63db94ca11468e114d912f5 | UNDERPOWERED |
| sspec_5f30e440e1f00e2fc4fad420 | trade_date_block_shuffle | 10634 | BLOCKED | False | True | surrun_3d7c8150da4430654658bbdb | UNDERPOWERED |
| sspec_5fb73ff1f5c96181be68e9c7 | trade_date_block_shuffle | 10635 | BLOCKED | False | True | surrun_61f1651cc1d0f3cdafec1adc | UNDERPOWERED |
| sspec_5fb73ff1f5c96181be68e9c7 | trade_date_block_shuffle | 10636 | BLOCKED | False | True | surrun_2be3a18faabec87aab3faf0a | UNDERPOWERED |
| sspec_5fb73ff1f5c96181be68e9c7 | trade_date_block_shuffle | 10637 | BLOCKED | False | True | surrun_f3073f45c4edea8442c7e86b | UNDERPOWERED |
| sspec_b315a7883c40b3d90df7ffe2 | trade_date_block_shuffle | 10638 | BLOCKED | False | True | surrun_24c46818536fce7b17c8cbdc | UNDERPOWERED |
| sspec_b315a7883c40b3d90df7ffe2 | trade_date_block_shuffle | 10639 | BLOCKED | False | True | surrun_600fc031cf782960cc72cd94 | UNDERPOWERED |
| sspec_b315a7883c40b3d90df7ffe2 | trade_date_block_shuffle | 10640 | BLOCKED | False | True | surrun_546532d1dfcbe392f8d46b87 | UNDERPOWERED |
| sspec_f178b5fc336630aabb18cba6 | trade_date_block_shuffle | 10641 | BLOCKED | False | True | surrun_59e7741a96c60d8399954905 | UNDERPOWERED |
| sspec_f178b5fc336630aabb18cba6 | trade_date_block_shuffle | 10642 | BLOCKED | False | True | surrun_03814041c2085f62eee90204 | UNDERPOWERED |
| sspec_f178b5fc336630aabb18cba6 | trade_date_block_shuffle | 10643 | BLOCKED | False | True | surrun_e8fd98532e8b9129d5a336f0 | UNDERPOWERED |
| sspec_7a064e20e01d96552cd3b575 | trade_date_block_shuffle | 10644 | BLOCKED | False | True | surrun_3744fd8441833e41c2d448ec | UNDERPOWERED |
| sspec_7a064e20e01d96552cd3b575 | trade_date_block_shuffle | 10645 | BLOCKED | False | True | surrun_218230ee2fa0a73131455277 | UNDERPOWERED |
| sspec_7a064e20e01d96552cd3b575 | trade_date_block_shuffle | 10646 | BLOCKED | False | True | surrun_7ae58c8df4afce0fbd24fcdb | UNDERPOWERED |
| sspec_e04b733f5a9c767d38996311 | trade_date_block_shuffle | 10647 | BLOCKED | False | True | surrun_60b99c81dcb9df6ccdda5453 | UNDERPOWERED |
| sspec_e04b733f5a9c767d38996311 | trade_date_block_shuffle | 10648 | BLOCKED | False | True | surrun_0f68ff537f08814e4c9785b4 | UNDERPOWERED |
| sspec_e04b733f5a9c767d38996311 | trade_date_block_shuffle | 10649 | BLOCKED | False | True | surrun_f8586d626d08d455b428d4f7 | UNDERPOWERED |
| sspec_5c7adec822a3855808bf44ff | trade_date_block_shuffle | 10650 | BLOCKED | False | True | surrun_5497af12dcc04abdcb5887a3 | UNDERPOWERED |
| sspec_5c7adec822a3855808bf44ff | trade_date_block_shuffle | 10651 | BLOCKED | False | True | surrun_001631c18c83856e7987f247 | UNDERPOWERED |
| sspec_5c7adec822a3855808bf44ff | trade_date_block_shuffle | 10652 | BLOCKED | False | True | surrun_7aea526123b89aa05ee56a57 | UNDERPOWERED |
| sspec_4549cf48a90f373099de3990 | trade_date_block_shuffle | 10653 | BLOCKED | False | True | surrun_f933e54c9d4dc368ce221ab2 | UNDERPOWERED |
| sspec_4549cf48a90f373099de3990 | trade_date_block_shuffle | 10654 | BLOCKED | False | True | surrun_070320d1d3cc6ecf5b199b8a | UNDERPOWERED |
| sspec_4549cf48a90f373099de3990 | trade_date_block_shuffle | 10655 | BLOCKED | False | True | surrun_09417903869fd6ad8df46480 | UNDERPOWERED |
| sspec_ebc5f04290686a0b7d5fb1ea | trade_date_block_shuffle | 10656 | BLOCKED | False | True | surrun_e51ec934d3c6345467b90bcf | UNDERPOWERED |
| sspec_ebc5f04290686a0b7d5fb1ea | trade_date_block_shuffle | 10657 | BLOCKED | False | True | surrun_5006ae4eaa234206c20ff519 | UNDERPOWERED |
| sspec_ebc5f04290686a0b7d5fb1ea | trade_date_block_shuffle | 10658 | BLOCKED | False | True | surrun_2609cbbcaeb6fe2228f73664 | UNDERPOWERED |
| sspec_df8a5e8e794403861efa45ad | trade_date_block_shuffle | 10659 | BLOCKED | False | True | surrun_eb00b935ca1bbd56cbea4cc7 | UNDERPOWERED |
| sspec_df8a5e8e794403861efa45ad | trade_date_block_shuffle | 10660 | BLOCKED | False | True | surrun_0f5cdffbf99a70d0638fadc6 | UNDERPOWERED |
| sspec_df8a5e8e794403861efa45ad | trade_date_block_shuffle | 10661 | BLOCKED | False | True | surrun_b04d942b9188c029ece46635 | UNDERPOWERED |
| sspec_c4ff2b42e9bdc1a8999ed8ed | trade_date_block_shuffle | 10662 | BLOCKED | False | True | surrun_57fcfb64c8449d04ce737fa3 | UNDERPOWERED |
| sspec_c4ff2b42e9bdc1a8999ed8ed | trade_date_block_shuffle | 10663 | BLOCKED | False | True | surrun_850508bbb8a6adf760908ee0 | UNDERPOWERED |
| sspec_c4ff2b42e9bdc1a8999ed8ed | trade_date_block_shuffle | 10664 | BLOCKED | False | True | surrun_2057e4e7d81d3f5b2f724775 | UNDERPOWERED |
| sspec_3bea96d053d0700e4a775133 | trade_date_block_shuffle | 10665 | BLOCKED | False | True | surrun_ada97e962c87d9d22252ca1e | UNDERPOWERED |
| sspec_3bea96d053d0700e4a775133 | trade_date_block_shuffle | 10666 | BLOCKED | False | True | surrun_c37c5f66767bc7d12c0bfe39 | UNDERPOWERED |
| sspec_3bea96d053d0700e4a775133 | trade_date_block_shuffle | 10667 | BLOCKED | False | True | surrun_92053a8302961d79549981a5 | UNDERPOWERED |
| sspec_f54131bec342de90e6dd27ea | trade_date_block_shuffle | 10668 | BLOCKED | False | True | surrun_bab3278675019fb1df52d94c | UNDERPOWERED |
| sspec_f54131bec342de90e6dd27ea | trade_date_block_shuffle | 10669 | BLOCKED | False | True | surrun_e4a32812e6971edec930f0b0 | UNDERPOWERED |
| sspec_f54131bec342de90e6dd27ea | trade_date_block_shuffle | 10670 | BLOCKED | False | True | surrun_733911f0f25fc4fb1efb8bbf | UNDERPOWERED |
| sspec_33dad16e1943a1636f17ac3f | trade_date_block_shuffle | 10671 | BLOCKED | False | True | surrun_4f0306b6c9acf33a552f45b5 | UNDERPOWERED |
| sspec_33dad16e1943a1636f17ac3f | trade_date_block_shuffle | 10672 | BLOCKED | False | True | surrun_df159516f682fd0b208bb3bf | UNDERPOWERED |
| sspec_33dad16e1943a1636f17ac3f | trade_date_block_shuffle | 10673 | BLOCKED | False | True | surrun_7979f0767f71ceba49ed1320 | UNDERPOWERED |
| sspec_fa3df10158e87c00b0321202 | trade_date_block_shuffle | 10674 | BLOCKED | False | True | surrun_316845060abee0e66684b925 | UNDERPOWERED |
| sspec_fa3df10158e87c00b0321202 | trade_date_block_shuffle | 10675 | BLOCKED | False | True | surrun_2c6d08345db50f771af388b7 | UNDERPOWERED |
| sspec_fa3df10158e87c00b0321202 | trade_date_block_shuffle | 10676 | BLOCKED | False | True | surrun_470be472b2b6ba6369c035ff | UNDERPOWERED |
| sspec_6013249328b6960d331e506a | trade_date_block_shuffle | 10677 | BLOCKED | False | True | surrun_629225bcd463be0787468a3e | UNDERPOWERED |
| sspec_6013249328b6960d331e506a | trade_date_block_shuffle | 10678 | BLOCKED | False | True | surrun_9223862747eafed2289ec2fe | UNDERPOWERED |
| sspec_6013249328b6960d331e506a | trade_date_block_shuffle | 10679 | BLOCKED | False | True | surrun_25ca6db4f320d496a379f50e | UNDERPOWERED |
| sspec_22c344106162dcc8aadd8f69 | trade_date_block_shuffle | 10680 | BLOCKED | False | True | surrun_6683c1603c72324958659d6a | UNDERPOWERED |
| sspec_22c344106162dcc8aadd8f69 | trade_date_block_shuffle | 10681 | BLOCKED | False | True | surrun_14f9684cf41bc7654dbbd168 | UNDERPOWERED |
| sspec_22c344106162dcc8aadd8f69 | trade_date_block_shuffle | 10682 | BLOCKED | False | True | surrun_6a13f86346969aa6a65e7e71 | UNDERPOWERED |
| sspec_95715cc5345c37578406e84f | trade_date_block_shuffle | 10683 | BLOCKED | False | True | surrun_2bd307c7cab8d88e9c396e1a | UNDERPOWERED |
| sspec_95715cc5345c37578406e84f | trade_date_block_shuffle | 10684 | BLOCKED | False | True | surrun_7d3150b760b3554cc9e9e712 | UNDERPOWERED |
| sspec_95715cc5345c37578406e84f | trade_date_block_shuffle | 10685 | BLOCKED | False | True | surrun_406f068543d358bedae8e9fa | UNDERPOWERED |
| sspec_3a6f48077629523800703448 | trade_date_block_shuffle | 10686 | BLOCKED | False | True | surrun_72e7a085c8c795aa3f694975 | UNDERPOWERED |
| sspec_3a6f48077629523800703448 | trade_date_block_shuffle | 10687 | BLOCKED | False | True | surrun_ba976ab1d099e72904ec3c9b | UNDERPOWERED |
| sspec_3a6f48077629523800703448 | trade_date_block_shuffle | 10688 | BLOCKED | False | True | surrun_54f44f00490a58eb61527327 | UNDERPOWERED |
| sspec_6ef0f5713fcdf2e014fbc972 | trade_date_block_shuffle | 10689 | BLOCKED | False | True | surrun_ca4919a4c13814be0dd50601 | UNDERPOWERED |
| sspec_6ef0f5713fcdf2e014fbc972 | trade_date_block_shuffle | 10690 | BLOCKED | False | True | surrun_756bd7cf0c16a6a2ce9bc6fe | UNDERPOWERED |
| sspec_6ef0f5713fcdf2e014fbc972 | trade_date_block_shuffle | 10691 | BLOCKED | False | True | surrun_6a82d2e6538ff8b28d166aa5 | UNDERPOWERED |
| sspec_9c85e9c30267a55df954b441 | trade_date_block_shuffle | 10692 | BLOCKED | False | True | surrun_5e7adae07365101bc4bafb21 | UNDERPOWERED |
| sspec_9c85e9c30267a55df954b441 | trade_date_block_shuffle | 10693 | BLOCKED | False | True | surrun_4776e82e527a117ea3675707 | UNDERPOWERED |
| sspec_9c85e9c30267a55df954b441 | trade_date_block_shuffle | 10694 | BLOCKED | False | True | surrun_07922fc81ed1f4ed7bd0844b | UNDERPOWERED |
| sspec_4667304d4ec8ebbd7a44da28 | trade_date_block_shuffle | 10695 | BLOCKED | False | True | surrun_33c457e8418a8f265bff1c8a | UNDERPOWERED |
| sspec_4667304d4ec8ebbd7a44da28 | trade_date_block_shuffle | 10696 | BLOCKED | False | True | surrun_1226bf09743ef6548403af88 | UNDERPOWERED |
| sspec_4667304d4ec8ebbd7a44da28 | trade_date_block_shuffle | 10697 | BLOCKED | False | True | surrun_8a0b12081d13e19b3bdff36a | UNDERPOWERED |
| sspec_9dba492eb43ed4a52cba1e46 | trade_date_block_shuffle | 10698 | BLOCKED | False | True | surrun_3d275b5b1295aa9a4bf7a16e | UNDERPOWERED |
| sspec_9dba492eb43ed4a52cba1e46 | trade_date_block_shuffle | 10699 | BLOCKED | False | True | surrun_df48f50e8e2ef0bf2257e24b | UNDERPOWERED |
| sspec_9dba492eb43ed4a52cba1e46 | trade_date_block_shuffle | 10700 | BLOCKED | False | True | surrun_c8b440855dfa44922c18729a | UNDERPOWERED |
| sspec_2ed4b14723030813e3983022 | trade_date_block_shuffle | 10701 | BLOCKED | False | True | surrun_5a43749196f833196065b04e | UNDERPOWERED |
| sspec_2ed4b14723030813e3983022 | trade_date_block_shuffle | 10702 | BLOCKED | False | True | surrun_4523fcbaba6f9c140153396a | UNDERPOWERED |
| sspec_2ed4b14723030813e3983022 | trade_date_block_shuffle | 10703 | BLOCKED | False | True | surrun_5d7f4fe78592c3645e0435bc | UNDERPOWERED |
| sspec_ded43c2c99f2a2087c341083 | trade_date_block_shuffle | 10704 | BLOCKED | False | True | surrun_18c9e1486be34da1deea272f | UNDERPOWERED |
| sspec_ded43c2c99f2a2087c341083 | trade_date_block_shuffle | 10705 | BLOCKED | False | True | surrun_6cb07d9c37599e89b37d767a | UNDERPOWERED |
| sspec_ded43c2c99f2a2087c341083 | trade_date_block_shuffle | 10706 | BLOCKED | False | True | surrun_8e9f5505dd64556a7e37b88c | UNDERPOWERED |
| sspec_138892cda61ac9eea9160d8f | trade_date_block_shuffle | 10707 | BLOCKED | False | True | surrun_42f8d1bad517cbdac3b71de2 | UNDERPOWERED |
| sspec_138892cda61ac9eea9160d8f | trade_date_block_shuffle | 10708 | BLOCKED | False | True | surrun_cd1df87dd6ab303487e37055 | UNDERPOWERED |
| sspec_138892cda61ac9eea9160d8f | trade_date_block_shuffle | 10709 | BLOCKED | False | True | surrun_14cd9228e015ce87920e855d | UNDERPOWERED |
| sspec_09ad1d10d032d170c54a3957 | trade_date_block_shuffle | 10710 | BLOCKED | False | True | surrun_331e9815921090eb95c3f14b | UNDERPOWERED |
| sspec_09ad1d10d032d170c54a3957 | trade_date_block_shuffle | 10711 | BLOCKED | False | True | surrun_46a464ee054aaceccf0a49d0 | UNDERPOWERED |
| sspec_09ad1d10d032d170c54a3957 | trade_date_block_shuffle | 10712 | BLOCKED | False | True | surrun_604592d438353121ee32e81e | UNDERPOWERED |
| sspec_15a32e69c66f64d3239fe190 | trade_date_block_shuffle | 10713 | BLOCKED | False | True | surrun_c1f6cab993fec583357dabe2 | UNDERPOWERED |
| sspec_15a32e69c66f64d3239fe190 | trade_date_block_shuffle | 10714 | BLOCKED | False | True | surrun_8a84ab77f456587207d04335 | UNDERPOWERED |
| sspec_15a32e69c66f64d3239fe190 | trade_date_block_shuffle | 10715 | BLOCKED | False | True | surrun_cfa48e93f976d0d7cf28c197 | UNDERPOWERED |
| sspec_31bd5fb5846b2fc0b718bb0f | trade_date_block_shuffle | 10716 | BLOCKED | False | True | surrun_2c432187eb52174b6e60025f | UNDERPOWERED |
| sspec_31bd5fb5846b2fc0b718bb0f | trade_date_block_shuffle | 10717 | BLOCKED | False | True | surrun_2660dc4d0414e71973fa8715 | UNDERPOWERED |
| sspec_31bd5fb5846b2fc0b718bb0f | trade_date_block_shuffle | 10718 | BLOCKED | False | True | surrun_bd6f563a02aaffa3e01d0a1b | UNDERPOWERED |
| sspec_ba1f201f247d5159cce6fede | trade_date_block_shuffle | 10719 | BLOCKED | False | True | surrun_022e716acc6cddc0a97df4b7 | UNDERPOWERED |
| sspec_ba1f201f247d5159cce6fede | trade_date_block_shuffle | 10720 | BLOCKED | False | True | surrun_ac38542f7c497acd58ce39ae | UNDERPOWERED |
| sspec_ba1f201f247d5159cce6fede | trade_date_block_shuffle | 10721 | BLOCKED | False | True | surrun_f30f2cff9b339fb8d6b22cc8 | UNDERPOWERED |
| sspec_26a64853e17e97b272655504 | trade_date_block_shuffle | 10722 | BLOCKED | False | True | surrun_825d253bdc665091778b16ef | UNDERPOWERED |
| sspec_26a64853e17e97b272655504 | trade_date_block_shuffle | 10723 | BLOCKED | False | True | surrun_3ea4b504b4da2c0131a54c53 | UNDERPOWERED |
| sspec_26a64853e17e97b272655504 | trade_date_block_shuffle | 10724 | BLOCKED | False | True | surrun_f78081d65b87078e56f7de3b | UNDERPOWERED |
| sspec_11544caf95b6c1532aba6dc9 | trade_date_block_shuffle | 10725 | BLOCKED | False | True | surrun_0e8bb6c3f58b54e643965442 | UNDERPOWERED |
| sspec_11544caf95b6c1532aba6dc9 | trade_date_block_shuffle | 10726 | BLOCKED | False | True | surrun_e66ca0ab66c5a9d0d83f5d82 | UNDERPOWERED |
| sspec_11544caf95b6c1532aba6dc9 | trade_date_block_shuffle | 10727 | BLOCKED | False | True | surrun_dd2602350f6a4da84f902beb | UNDERPOWERED |
| sspec_8e4e1cf3a5a60f638ead0554 | trade_date_block_shuffle | 10728 | BLOCKED | False | True | surrun_bdd39634ddecc9befc71dc47 | UNDERPOWERED |
| sspec_8e4e1cf3a5a60f638ead0554 | trade_date_block_shuffle | 10729 | BLOCKED | False | True | surrun_bcff923dd71de14e79788e6e | UNDERPOWERED |
| sspec_8e4e1cf3a5a60f638ead0554 | trade_date_block_shuffle | 10730 | BLOCKED | False | True | surrun_090e1ab92848771f53bb4aa7 | UNDERPOWERED |
| sspec_c6274ed832946f7e4c7057ba | trade_date_block_shuffle | 10731 | BLOCKED | False | True | surrun_847c3cf4b46d38acdb02440e | UNDERPOWERED |
| sspec_c6274ed832946f7e4c7057ba | trade_date_block_shuffle | 10732 | BLOCKED | False | True | surrun_3139846af0ca2ef6f36fdf4e | UNDERPOWERED |
| sspec_c6274ed832946f7e4c7057ba | trade_date_block_shuffle | 10733 | BLOCKED | False | True | surrun_ade272b7b0b897a3a9f84888 | UNDERPOWERED |
| sspec_627f99bd374e017a1432b718 | trade_date_block_shuffle | 10734 | BLOCKED | False | True | surrun_84acd7631957979a5bd5d93c | UNDERPOWERED |
| sspec_627f99bd374e017a1432b718 | trade_date_block_shuffle | 10735 | BLOCKED | False | True | surrun_d42393c6aeed5bd90701723f | UNDERPOWERED |
| sspec_627f99bd374e017a1432b718 | trade_date_block_shuffle | 10736 | BLOCKED | False | True | surrun_58aff2f4fb3edc40cb385685 | UNDERPOWERED |
| sspec_e35511839516ef6c71ce543e | trade_date_block_shuffle | 10737 | BLOCKED | False | True | surrun_f29ed070fbc48a32ac475ba3 | UNDERPOWERED |
| sspec_e35511839516ef6c71ce543e | trade_date_block_shuffle | 10738 | BLOCKED | False | True | surrun_496d327a7c669dd61a79ecaa | UNDERPOWERED |
| sspec_e35511839516ef6c71ce543e | trade_date_block_shuffle | 10739 | BLOCKED | False | True | surrun_22c64fc5bfaa872263134f46 | UNDERPOWERED |
| sspec_883e0cdb95b7cc71aae0e4fa | trade_date_block_shuffle | 10740 | BLOCKED | False | True | surrun_5e7fecd31cd5b4b6eeb78bb4 | UNDERPOWERED |
| sspec_883e0cdb95b7cc71aae0e4fa | trade_date_block_shuffle | 10741 | BLOCKED | False | True | surrun_29414791749ea61096c3985c | UNDERPOWERED |
| sspec_883e0cdb95b7cc71aae0e4fa | trade_date_block_shuffle | 10742 | BLOCKED | False | True | surrun_7faeaebde3a93fa45bf810e2 | UNDERPOWERED |
| sspec_d269f007b8f7a869fb0ba831 | trade_date_block_shuffle | 10743 | BLOCKED | False | True | surrun_54606c1c68c2f62d66ddfc6f | UNDERPOWERED |
| sspec_d269f007b8f7a869fb0ba831 | trade_date_block_shuffle | 10744 | BLOCKED | False | True | surrun_9b7afcb71791ee84a8e70fc6 | UNDERPOWERED |
| sspec_d269f007b8f7a869fb0ba831 | trade_date_block_shuffle | 10745 | BLOCKED | False | True | surrun_749404753768f3f3cf72bef2 | UNDERPOWERED |
| sspec_52b0336f61f1a3eda7b12e06 | trade_date_block_shuffle | 10746 | BLOCKED | False | True | surrun_5dfdf5c1a809aae412eb834e | UNDERPOWERED |
| sspec_52b0336f61f1a3eda7b12e06 | trade_date_block_shuffle | 10747 | BLOCKED | False | True | surrun_7a3f803cf9e0dbbf7d11f564 | UNDERPOWERED |
| sspec_52b0336f61f1a3eda7b12e06 | trade_date_block_shuffle | 10748 | BLOCKED | False | True | surrun_5f4b629153b622e22d3064f3 | UNDERPOWERED |
| sspec_80b992bd736902213801e2de | trade_date_block_shuffle | 10749 | BLOCKED | False | True | surrun_8b68617ae2df5b8103975b6d | UNDERPOWERED |
| sspec_80b992bd736902213801e2de | trade_date_block_shuffle | 10750 | BLOCKED | False | True | surrun_c636d7c8faed420f502860a8 | UNDERPOWERED |
| sspec_80b992bd736902213801e2de | trade_date_block_shuffle | 10751 | BLOCKED | False | True | surrun_928ab7d67e2c1490195d7c33 | UNDERPOWERED |
| sspec_363fd6e38ae46e2753764e05 | trade_date_block_shuffle | 10752 | BLOCKED | False | True | surrun_f2e024aa44ae63cfe064ed76 | UNDERPOWERED |
| sspec_363fd6e38ae46e2753764e05 | trade_date_block_shuffle | 10753 | BLOCKED | False | True | surrun_4f657104153f0ac8ba438220 | UNDERPOWERED |
| sspec_363fd6e38ae46e2753764e05 | trade_date_block_shuffle | 10754 | BLOCKED | False | True | surrun_2b4446ccc632788eeece90f3 | UNDERPOWERED |
| sspec_55c049acb884c61b3e63eb2c | trade_date_block_shuffle | 10755 | BLOCKED | False | True | surrun_2ba6a04e078a9142cf6933ae | UNDERPOWERED |
| sspec_55c049acb884c61b3e63eb2c | trade_date_block_shuffle | 10756 | BLOCKED | False | True | surrun_4c40c5bc04e487b3588fa534 | UNDERPOWERED |
| sspec_55c049acb884c61b3e63eb2c | trade_date_block_shuffle | 10757 | BLOCKED | False | True | surrun_d7dc824f4229165a3f1ebc1c | UNDERPOWERED |
| sspec_62b071de89a66f775837d83e | trade_date_block_shuffle | 10758 | BLOCKED | False | True | surrun_60140ece2c80a4e0360e97aa | UNDERPOWERED |
| sspec_62b071de89a66f775837d83e | trade_date_block_shuffle | 10759 | BLOCKED | False | True | surrun_990d257572b24146acf7a9ba | UNDERPOWERED |
| sspec_62b071de89a66f775837d83e | trade_date_block_shuffle | 10760 | BLOCKED | False | True | surrun_a975cfbb838e7e66e2c41e35 | UNDERPOWERED |
| sspec_c766b4ae7d8b985f3e4dd022 | trade_date_block_shuffle | 10761 | BLOCKED | False | True | surrun_d3c20aafba33c83d7baa4ec8 | UNDERPOWERED |
| sspec_c766b4ae7d8b985f3e4dd022 | trade_date_block_shuffle | 10762 | BLOCKED | False | True | surrun_ffa9fc262172a11be20c69df | UNDERPOWERED |
| sspec_c766b4ae7d8b985f3e4dd022 | trade_date_block_shuffle | 10763 | BLOCKED | False | True | surrun_204135dd658db821d34c69ae | UNDERPOWERED |
| sspec_f5ad0171efc937933acf3983 | trade_date_block_shuffle | 10764 | BLOCKED | False | True | surrun_c8e828589a0de12021d9465b | UNDERPOWERED |
| sspec_f5ad0171efc937933acf3983 | trade_date_block_shuffle | 10765 | BLOCKED | False | True | surrun_d207d73d2f3ac2cbf65b8ee9 | UNDERPOWERED |
| sspec_f5ad0171efc937933acf3983 | trade_date_block_shuffle | 10766 | BLOCKED | False | True | surrun_5fd09c5186ffdae53c512bb3 | UNDERPOWERED |
| sspec_90092d5e12acd11cd044c760 | trade_date_block_shuffle | 10767 | BLOCKED | False | True | surrun_2c19e8948bca0f707c55054b | UNDERPOWERED |
| sspec_90092d5e12acd11cd044c760 | trade_date_block_shuffle | 10768 | BLOCKED | False | True | surrun_0bfc202fa86fd078e37e050c | UNDERPOWERED |
| sspec_90092d5e12acd11cd044c760 | trade_date_block_shuffle | 10769 | BLOCKED | False | True | surrun_11b34bbb628f36abf2d3e8dd | UNDERPOWERED |
| sspec_53520c1599d90ff4aafb8fe6 | trade_date_block_shuffle | 10770 | BLOCKED | False | True | surrun_35f782d8b68dc4d94588f463 | UNDERPOWERED |
| sspec_53520c1599d90ff4aafb8fe6 | trade_date_block_shuffle | 10771 | BLOCKED | False | True | surrun_c47f6702b1d8cdc8921a31bf | UNDERPOWERED |
| sspec_53520c1599d90ff4aafb8fe6 | trade_date_block_shuffle | 10772 | BLOCKED | False | True | surrun_71238659ace07afd8ca70255 | UNDERPOWERED |
| sspec_5ef23f24a1af7883f8526c08 | trade_date_block_shuffle | 10773 | BLOCKED | False | True | surrun_643490b1cb407236ebdf09f3 | UNDERPOWERED |
| sspec_5ef23f24a1af7883f8526c08 | trade_date_block_shuffle | 10774 | BLOCKED | False | True | surrun_e168f6641bf361e69d84f155 | UNDERPOWERED |
| sspec_5ef23f24a1af7883f8526c08 | trade_date_block_shuffle | 10775 | BLOCKED | False | True | surrun_561a75c998fcec2226a1acb6 | UNDERPOWERED |
| sspec_68bf5553d2f1ba89b39a726c | trade_date_block_shuffle | 10776 | BLOCKED | False | True | surrun_7f4945924616d7c02a659f79 | UNDERPOWERED |
| sspec_68bf5553d2f1ba89b39a726c | trade_date_block_shuffle | 10777 | BLOCKED | False | True | surrun_7c3c852b177313303034034b | UNDERPOWERED |
| sspec_68bf5553d2f1ba89b39a726c | trade_date_block_shuffle | 10778 | BLOCKED | False | True | surrun_f159f530df54a3ef3074492c | UNDERPOWERED |
| sspec_444ef93bbd1a8a9c3bd4a684 | trade_date_block_shuffle | 10779 | BLOCKED | False | True | surrun_2a340ece08d8f4d1e69cdbff | UNDERPOWERED |
| sspec_444ef93bbd1a8a9c3bd4a684 | trade_date_block_shuffle | 10780 | BLOCKED | False | True | surrun_478156441c1991c2101a6c7b | UNDERPOWERED |
| sspec_444ef93bbd1a8a9c3bd4a684 | trade_date_block_shuffle | 10781 | BLOCKED | False | True | surrun_c33bdbd990700d304af40aca | UNDERPOWERED |
| sspec_3284e561e225c9e203fc58dd | trade_date_block_shuffle | 10782 | BLOCKED | False | True | surrun_1ed680cc921980ae1119f14a | UNDERPOWERED |
| sspec_3284e561e225c9e203fc58dd | trade_date_block_shuffle | 10783 | BLOCKED | False | True | surrun_d02572d98773182aed606b8f | UNDERPOWERED |
| sspec_3284e561e225c9e203fc58dd | trade_date_block_shuffle | 10784 | BLOCKED | False | True | surrun_b1bb658f3d4c3217bcadf6b1 | UNDERPOWERED |
| sspec_4468e6432d92e8db6c27cd6b | trade_date_block_shuffle | 10785 | BLOCKED | False | True | surrun_5c4d811d1d1368864741afdc | UNDERPOWERED |
| sspec_4468e6432d92e8db6c27cd6b | trade_date_block_shuffle | 10786 | BLOCKED | False | True | surrun_96a51384dc1b3665b5dc201d | UNDERPOWERED |
| sspec_4468e6432d92e8db6c27cd6b | trade_date_block_shuffle | 10787 | BLOCKED | False | True | surrun_b4274f2f1c27a1c331725a1e | UNDERPOWERED |
| sspec_9037ec5a2706bd265ab7c0f6 | trade_date_block_shuffle | 10788 | BLOCKED | False | True | surrun_51d948bbd3c378758be8e84a | UNDERPOWERED |
| sspec_9037ec5a2706bd265ab7c0f6 | trade_date_block_shuffle | 10789 | BLOCKED | False | True | surrun_a037ba31ce70b1f89c388cad | UNDERPOWERED |
| sspec_9037ec5a2706bd265ab7c0f6 | trade_date_block_shuffle | 10790 | BLOCKED | False | True | surrun_d740bb2e6a666f20026780be | UNDERPOWERED |
| sspec_164fc38457af9855db79f079 | trade_date_block_shuffle | 10791 | BLOCKED | False | True | surrun_5f1203c00c99bfdb8a4f6fd4 | UNDERPOWERED |
| sspec_164fc38457af9855db79f079 | trade_date_block_shuffle | 10792 | BLOCKED | False | True | surrun_a035c535ca699755bda8c560 | UNDERPOWERED |
| sspec_164fc38457af9855db79f079 | trade_date_block_shuffle | 10793 | BLOCKED | False | True | surrun_259571d282f56d575f10d16c | UNDERPOWERED |
| sspec_b10990ebba5a3326dade5cb9 | trade_date_block_shuffle | 10794 | BLOCKED | False | True | surrun_bf167ee841a4102b3410fa22 | UNDERPOWERED |
| sspec_b10990ebba5a3326dade5cb9 | trade_date_block_shuffle | 10795 | BLOCKED | False | True | surrun_b28b5cb1e7788d978ee0941b | UNDERPOWERED |
| sspec_b10990ebba5a3326dade5cb9 | trade_date_block_shuffle | 10796 | BLOCKED | False | True | surrun_38a59cde8898e3bfc0ee9acc | UNDERPOWERED |
| sspec_e19d3c23f01ddd6e83fded22 | trade_date_block_shuffle | 10797 | BLOCKED | False | True | surrun_41480fe0fe8a6903e998c79d | UNDERPOWERED |
| sspec_e19d3c23f01ddd6e83fded22 | trade_date_block_shuffle | 10798 | BLOCKED | False | True | surrun_1d8011ea9dc8a1ddee63e0a6 | UNDERPOWERED |
| sspec_e19d3c23f01ddd6e83fded22 | trade_date_block_shuffle | 10799 | BLOCKED | False | True | surrun_ea0a38f71bb6b5af0d35301e | UNDERPOWERED |
| sspec_de3e699a403c2177c40d9cc8 | trade_date_block_shuffle | 10800 | BLOCKED | False | True | surrun_28c83fdced991274f21cac5a | UNDERPOWERED |
| sspec_de3e699a403c2177c40d9cc8 | trade_date_block_shuffle | 10801 | BLOCKED | False | True | surrun_a6cd4e7015e9b5e72154eb0a | UNDERPOWERED |
| sspec_de3e699a403c2177c40d9cc8 | trade_date_block_shuffle | 10802 | BLOCKED | False | True | surrun_8f1103051a0dd5ac0867c2a7 | UNDERPOWERED |
| sspec_5621afc74ef50911ec282e47 | trade_date_block_shuffle | 10803 | BLOCKED | False | True | surrun_fc6575f000d5325ac6bf7fa8 | UNDERPOWERED |
| sspec_5621afc74ef50911ec282e47 | trade_date_block_shuffle | 10804 | BLOCKED | False | True | surrun_296ea4c069201931052885af | UNDERPOWERED |
| sspec_5621afc74ef50911ec282e47 | trade_date_block_shuffle | 10805 | BLOCKED | False | True | surrun_ba1efe183c51afd33448ff75 | UNDERPOWERED |
| sspec_1902c7977a0f0121448b112e | trade_date_block_shuffle | 10806 | BLOCKED | False | True | surrun_b1a066ed87587dfd7c27264e | UNDERPOWERED |
| sspec_1902c7977a0f0121448b112e | trade_date_block_shuffle | 10807 | BLOCKED | False | True | surrun_6af54828ede4f25e841802f8 | UNDERPOWERED |
| sspec_1902c7977a0f0121448b112e | trade_date_block_shuffle | 10808 | BLOCKED | False | True | surrun_0816968d49eb79cf5612942b | UNDERPOWERED |
| sspec_4bb2ca612fdf7ee2e712d648 | trade_date_block_shuffle | 10809 | BLOCKED | False | True | surrun_eb6dd743929ba271ddbc8699 | UNDERPOWERED |
| sspec_4bb2ca612fdf7ee2e712d648 | trade_date_block_shuffle | 10810 | BLOCKED | False | True | surrun_61517d18cab59705ed945137 | UNDERPOWERED |
| sspec_4bb2ca612fdf7ee2e712d648 | trade_date_block_shuffle | 10811 | BLOCKED | False | True | surrun_487d333e698d82d6f6b0d8b3 | UNDERPOWERED |
| sspec_123591b05b9a912fe8970cfb | trade_date_block_shuffle | 10812 | BLOCKED | False | True | surrun_44de88edc062000f8792f550 | UNDERPOWERED |
| sspec_123591b05b9a912fe8970cfb | trade_date_block_shuffle | 10813 | BLOCKED | False | True | surrun_61b8251b9a5f5cc83e1d1838 | UNDERPOWERED |
| sspec_123591b05b9a912fe8970cfb | trade_date_block_shuffle | 10814 | BLOCKED | False | True | surrun_aa7de48be76251ecd32c9367 | UNDERPOWERED |
| sspec_8fdef93acef82e49081fcb1f | trade_date_block_shuffle | 10815 | BLOCKED | False | True | surrun_613c45e271c8e72dd002cefe | UNDERPOWERED |
| sspec_8fdef93acef82e49081fcb1f | trade_date_block_shuffle | 10816 | BLOCKED | False | True | surrun_3fb6dc1b0ecfa4f6cfeb1e27 | UNDERPOWERED |
| sspec_8fdef93acef82e49081fcb1f | trade_date_block_shuffle | 10817 | BLOCKED | False | True | surrun_9147861589e9bdb219a03096 | UNDERPOWERED |
| sspec_429edfce8d1bb00a65230c60 | trade_date_block_shuffle | 10818 | BLOCKED | False | True | surrun_02072e07bfa1dca2eb18062e | UNDERPOWERED |
| sspec_429edfce8d1bb00a65230c60 | trade_date_block_shuffle | 10819 | BLOCKED | False | True | surrun_ca2f3e126c67ee41d294011a | UNDERPOWERED |
| sspec_429edfce8d1bb00a65230c60 | trade_date_block_shuffle | 10820 | BLOCKED | False | True | surrun_55446e03aab36e6a527024aa | UNDERPOWERED |
| sspec_8545f86193efb04e1f5b5b0a | trade_date_block_shuffle | 10821 | BLOCKED | False | True | surrun_aa86cfb4e7529a0b840ca147 | UNDERPOWERED |
| sspec_8545f86193efb04e1f5b5b0a | trade_date_block_shuffle | 10822 | BLOCKED | False | True | surrun_efc9f0ba3bd7d7d5276ad155 | UNDERPOWERED |
| sspec_8545f86193efb04e1f5b5b0a | trade_date_block_shuffle | 10823 | BLOCKED | False | True | surrun_e05ea3ccf229eba5e4346305 | UNDERPOWERED |
| sspec_5c5fb27f9b4b3670ce46c331 | trade_date_block_shuffle | 10824 | BLOCKED | False | True | surrun_7d1192d657c77af8a0a8f727 | UNDERPOWERED |
| sspec_5c5fb27f9b4b3670ce46c331 | trade_date_block_shuffle | 10825 | BLOCKED | False | True | surrun_658b2c91914e9a982a7f2dae | UNDERPOWERED |
| sspec_5c5fb27f9b4b3670ce46c331 | trade_date_block_shuffle | 10826 | BLOCKED | False | True | surrun_bf4efaf99812de86e757b168 | UNDERPOWERED |
| sspec_3ef04e631e7b0b4d493441aa | trade_date_block_shuffle | 10827 | BLOCKED | False | True | surrun_8e07b0cb132d62d6bbdfc956 | UNDERPOWERED |
| sspec_3ef04e631e7b0b4d493441aa | trade_date_block_shuffle | 10828 | BLOCKED | False | True | surrun_f322fd70110bc94b4f2b0c52 | UNDERPOWERED |
| sspec_3ef04e631e7b0b4d493441aa | trade_date_block_shuffle | 10829 | BLOCKED | False | True | surrun_b2c7732d6c54710ed06102eb | UNDERPOWERED |
| sspec_2b4b71e12ac5786625d178c6 | trade_date_block_shuffle | 10830 | BLOCKED | False | True | surrun_5202975da4ae0507274c0332 | UNDERPOWERED |
| sspec_2b4b71e12ac5786625d178c6 | trade_date_block_shuffle | 10831 | BLOCKED | False | True | surrun_064fc9f11829cb87007df962 | UNDERPOWERED |
| sspec_2b4b71e12ac5786625d178c6 | trade_date_block_shuffle | 10832 | BLOCKED | False | True | surrun_ebd046c1a4fb3b9fcdd35b0d | UNDERPOWERED |
| sspec_9a7cf74fc9908ec06106675b | trade_date_block_shuffle | 10833 | BLOCKED | False | True | surrun_0ebb85bd81000710be0f1707 | UNDERPOWERED |
| sspec_9a7cf74fc9908ec06106675b | trade_date_block_shuffle | 10834 | BLOCKED | False | True | surrun_1c3797a176f437784d4f6bb1 | UNDERPOWERED |
| sspec_9a7cf74fc9908ec06106675b | trade_date_block_shuffle | 10835 | BLOCKED | False | True | surrun_7a55b6e7f389865bfdc4bea9 | UNDERPOWERED |
| sspec_bbcb2109b27996474c1f91e3 | trade_date_block_shuffle | 10836 | BLOCKED | False | True | surrun_c947c8e2fdd24b49a00b504a | UNDERPOWERED |
| sspec_bbcb2109b27996474c1f91e3 | trade_date_block_shuffle | 10837 | BLOCKED | False | True | surrun_4b8af39639aee6d32751baae | UNDERPOWERED |
| sspec_bbcb2109b27996474c1f91e3 | trade_date_block_shuffle | 10838 | BLOCKED | False | True | surrun_7ad76f6fd7099b951bda7c49 | UNDERPOWERED |
| sspec_c985c172eecc2c0f6d2db98b | trade_date_block_shuffle | 10839 | BLOCKED | False | True | surrun_32308991599b059dfd673a8e | UNDERPOWERED |
| sspec_c985c172eecc2c0f6d2db98b | trade_date_block_shuffle | 10840 | BLOCKED | False | True | surrun_df2dd75d673f7b13f3720ddd | UNDERPOWERED |
| sspec_c985c172eecc2c0f6d2db98b | trade_date_block_shuffle | 10841 | BLOCKED | False | True | surrun_91979e7a85fc29fb8692f21b | UNDERPOWERED |
| sspec_3e363698c3a9734e4dc152e6 | trade_date_block_shuffle | 10842 | BLOCKED | False | True | surrun_f8b53a0d2cf8cbe2591ca244 | UNDERPOWERED |
| sspec_3e363698c3a9734e4dc152e6 | trade_date_block_shuffle | 10843 | BLOCKED | False | True | surrun_f452af0e0284e41e707533a8 | UNDERPOWERED |
| sspec_3e363698c3a9734e4dc152e6 | trade_date_block_shuffle | 10844 | BLOCKED | False | True | surrun_9337dd4f2b16f26f4bbdb631 | UNDERPOWERED |
| sspec_11b260927df9d314f8f0b48c | trade_date_block_shuffle | 10845 | BLOCKED | False | True | surrun_8f18a7091b9043bc42cd34df | UNDERPOWERED |
| sspec_11b260927df9d314f8f0b48c | trade_date_block_shuffle | 10846 | BLOCKED | False | True | surrun_032bd9dd131fe5c663131853 | UNDERPOWERED |
| sspec_11b260927df9d314f8f0b48c | trade_date_block_shuffle | 10847 | BLOCKED | False | True | surrun_97392d94a6a080ad12d37379 | UNDERPOWERED |
| sspec_186366ce8fc5106f8952e9af | trade_date_block_bootstrap | 10848 | BLOCKED | False | True | surrun_ff9c02ca7cd5dfa311af6af9 | UNDERPOWERED |
| sspec_186366ce8fc5106f8952e9af | trade_date_block_bootstrap | 10849 | BLOCKED | False | True | surrun_9b73eddf3d67ad32f77a3f6a | UNDERPOWERED |
| sspec_186366ce8fc5106f8952e9af | trade_date_block_bootstrap | 10850 | BLOCKED | False | True | surrun_ed46bd2c76e16245e64df095 | UNDERPOWERED |
| sspec_abb0800d67aca97257b98174 | trade_date_block_bootstrap | 10851 | BLOCKED | False | True | surrun_ec780676474c6f5b604c3249 | UNDERPOWERED |
| sspec_abb0800d67aca97257b98174 | trade_date_block_bootstrap | 10852 | BLOCKED | False | True | surrun_43a3a78645553f2e63213320 | UNDERPOWERED |
| sspec_abb0800d67aca97257b98174 | trade_date_block_bootstrap | 10853 | BLOCKED | False | True | surrun_bd55b8f11ca2f07f9bcb8c9e | UNDERPOWERED |
| sspec_5388a9a9355da05b81c2e0f5 | trade_date_block_bootstrap | 10854 | BLOCKED | False | True | surrun_ec9631bd781b7986565d35a9 | UNDERPOWERED |
| sspec_5388a9a9355da05b81c2e0f5 | trade_date_block_bootstrap | 10855 | BLOCKED | False | True | surrun_d05d4bbf55c6e1af4518a84c | UNDERPOWERED |
| sspec_5388a9a9355da05b81c2e0f5 | trade_date_block_bootstrap | 10856 | BLOCKED | False | True | surrun_a5bc1a84f65dc9164a342399 | UNDERPOWERED |
| sspec_f55efbd79a11c18c54b39e61 | trade_date_block_bootstrap | 10857 | BLOCKED | False | True | surrun_3b032d3fe88f8d5582230264 | UNDERPOWERED |
| sspec_f55efbd79a11c18c54b39e61 | trade_date_block_bootstrap | 10858 | BLOCKED | False | True | surrun_b089f77568b6619ba595e6bd | UNDERPOWERED |
| sspec_f55efbd79a11c18c54b39e61 | trade_date_block_bootstrap | 10859 | BLOCKED | False | True | surrun_31f70af813e581d4b7edf2f5 | UNDERPOWERED |
| sspec_21b47c6532352f1d8c30c156 | trade_date_block_bootstrap | 10860 | BLOCKED | False | True | surrun_9672b57dc50f971eb44292eb | UNDERPOWERED |
| sspec_21b47c6532352f1d8c30c156 | trade_date_block_bootstrap | 10861 | BLOCKED | False | True | surrun_1843aa6c871e5242fa6c6a52 | UNDERPOWERED |
| sspec_21b47c6532352f1d8c30c156 | trade_date_block_bootstrap | 10862 | BLOCKED | False | True | surrun_4577de9bd77cbc75ed2380bc | UNDERPOWERED |
| sspec_2c3079c514c26522ec9f2f14 | trade_date_block_bootstrap | 10863 | BLOCKED | False | True | surrun_97e46abefbdbf66933d4e9a4 | UNDERPOWERED |
| sspec_2c3079c514c26522ec9f2f14 | trade_date_block_bootstrap | 10864 | BLOCKED | False | True | surrun_3932be6f121972aa7c1a5062 | UNDERPOWERED |
| sspec_2c3079c514c26522ec9f2f14 | trade_date_block_bootstrap | 10865 | BLOCKED | False | True | surrun_11e38b996e300bcb7d8d76ae | UNDERPOWERED |
| sspec_04e3ec49a39c1fa70257a198 | trade_date_block_bootstrap | 10866 | BLOCKED | False | True | surrun_f16a660602c5778ebaf5c883 | UNDERPOWERED |
| sspec_04e3ec49a39c1fa70257a198 | trade_date_block_bootstrap | 10867 | BLOCKED | False | True | surrun_362e67739310b75fdc919687 | UNDERPOWERED |
| sspec_04e3ec49a39c1fa70257a198 | trade_date_block_bootstrap | 10868 | BLOCKED | False | True | surrun_9edd23ed6009a755b6f94310 | UNDERPOWERED |
| sspec_30fafe9c23cc3db43b14ddf4 | trade_date_block_bootstrap | 10869 | BLOCKED | False | True | surrun_66a2da6e7523524b26d4b53d | UNDERPOWERED |
| sspec_30fafe9c23cc3db43b14ddf4 | trade_date_block_bootstrap | 10870 | BLOCKED | False | True | surrun_b586e1e17c0b6588244871cb | UNDERPOWERED |
| sspec_30fafe9c23cc3db43b14ddf4 | trade_date_block_bootstrap | 10871 | BLOCKED | False | True | surrun_de3fda51755f58d84f926b9e | UNDERPOWERED |
| sspec_64a62f51bcf69fbd6d5ae3e5 | trade_date_block_bootstrap | 10872 | BLOCKED | False | True | surrun_32d34ece05f3d3bcad969a1d | UNDERPOWERED |
| sspec_64a62f51bcf69fbd6d5ae3e5 | trade_date_block_bootstrap | 10873 | BLOCKED | False | True | surrun_19bbfefff9763e11c5c7f1df | UNDERPOWERED |
| sspec_64a62f51bcf69fbd6d5ae3e5 | trade_date_block_bootstrap | 10874 | BLOCKED | False | True | surrun_648c2fbd74546ab58904c170 | UNDERPOWERED |
| sspec_05c47eec02cc292eee93e6e4 | trade_date_block_bootstrap | 10875 | BLOCKED | False | True | surrun_deb457f5f7e7c5c62b27d083 | UNDERPOWERED |
| sspec_05c47eec02cc292eee93e6e4 | trade_date_block_bootstrap | 10876 | BLOCKED | False | True | surrun_1227ac01037043659af04e93 | UNDERPOWERED |
| sspec_05c47eec02cc292eee93e6e4 | trade_date_block_bootstrap | 10877 | BLOCKED | False | True | surrun_17821cdf3ac90494e30da0f7 | UNDERPOWERED |
| sspec_ddf3a3a474adecf0f9592cd0 | trade_date_block_bootstrap | 10878 | BLOCKED | False | True | surrun_c5bae436f8ab27d8cb84bff9 | UNDERPOWERED |
| sspec_ddf3a3a474adecf0f9592cd0 | trade_date_block_bootstrap | 10879 | BLOCKED | False | True | surrun_7758642d533d538859347968 | UNDERPOWERED |
| sspec_ddf3a3a474adecf0f9592cd0 | trade_date_block_bootstrap | 10880 | BLOCKED | False | True | surrun_6c277d41a7e80ec647d8499d | UNDERPOWERED |
| sspec_0d4af57026259b33808ca5aa | trade_date_block_bootstrap | 10881 | BLOCKED | False | True | surrun_867859731376645b644afd05 | UNDERPOWERED |
| sspec_0d4af57026259b33808ca5aa | trade_date_block_bootstrap | 10882 | BLOCKED | False | True | surrun_4334c711f360ec9259fd3c43 | UNDERPOWERED |
| sspec_0d4af57026259b33808ca5aa | trade_date_block_bootstrap | 10883 | BLOCKED | False | True | surrun_095b2d9a203299d2068d887e | UNDERPOWERED |
| sspec_cb615fa2438d459f66c234ea | trade_date_block_bootstrap | 10884 | BLOCKED | False | True | surrun_95ee17876f253cc016822242 | UNDERPOWERED |
| sspec_cb615fa2438d459f66c234ea | trade_date_block_bootstrap | 10885 | BLOCKED | False | True | surrun_e805c9e2db301aaef92c889e | UNDERPOWERED |
| sspec_cb615fa2438d459f66c234ea | trade_date_block_bootstrap | 10886 | BLOCKED | False | True | surrun_4665ba09fc1549692d5df7b3 | UNDERPOWERED |
| sspec_21c9105862a0460faa28b12b | trade_date_block_bootstrap | 10887 | BLOCKED | False | True | surrun_a11afb41a9bd7d97efb6067a | UNDERPOWERED |
| sspec_21c9105862a0460faa28b12b | trade_date_block_bootstrap | 10888 | BLOCKED | False | True | surrun_76fb0d83b10f63bd6f7bc0c7 | UNDERPOWERED |
| sspec_21c9105862a0460faa28b12b | trade_date_block_bootstrap | 10889 | BLOCKED | False | True | surrun_f6e9e64a29d4b63a97d9351d | UNDERPOWERED |
| sspec_a850d4fdf70255eddd718338 | trade_date_block_bootstrap | 10890 | BLOCKED | False | True | surrun_b33141f596d02bb2fd8ea5df | UNDERPOWERED |
| sspec_a850d4fdf70255eddd718338 | trade_date_block_bootstrap | 10891 | BLOCKED | False | True | surrun_e79313cbe6533870c5a1cc28 | UNDERPOWERED |
| sspec_a850d4fdf70255eddd718338 | trade_date_block_bootstrap | 10892 | BLOCKED | False | True | surrun_a655e9cdbc4011a554ee2fb4 | UNDERPOWERED |
| sspec_c0247dfd070d3bcbc84d2a1e | trade_date_block_bootstrap | 10893 | BLOCKED | False | True | surrun_f3588cfe8f835efeb00d3f05 | UNDERPOWERED |
| sspec_c0247dfd070d3bcbc84d2a1e | trade_date_block_bootstrap | 10894 | BLOCKED | False | True | surrun_06b6610846efced58455a5fd | UNDERPOWERED |
| sspec_c0247dfd070d3bcbc84d2a1e | trade_date_block_bootstrap | 10895 | BLOCKED | False | True | surrun_a8ce41159e133a725ae318ce | UNDERPOWERED |
| sspec_3fa57dd69f1d1681b2c627bb | trade_date_block_bootstrap | 10896 | BLOCKED | False | True | surrun_04386fcda4e47f1a451d2075 | UNDERPOWERED |
| sspec_3fa57dd69f1d1681b2c627bb | trade_date_block_bootstrap | 10897 | BLOCKED | False | True | surrun_721c7039378f954a8ca7b57a | UNDERPOWERED |
| sspec_3fa57dd69f1d1681b2c627bb | trade_date_block_bootstrap | 10898 | BLOCKED | False | True | surrun_a53408f58627b342154c4526 | UNDERPOWERED |
| sspec_3c6feed90e9b81eb45bda321 | trade_date_block_bootstrap | 10899 | BLOCKED | False | True | surrun_8824ad0edb99daddf010d3a1 | UNDERPOWERED |
| sspec_3c6feed90e9b81eb45bda321 | trade_date_block_bootstrap | 10900 | BLOCKED | False | True | surrun_b7be75af3261b5977755c34d | UNDERPOWERED |
| sspec_3c6feed90e9b81eb45bda321 | trade_date_block_bootstrap | 10901 | BLOCKED | False | True | surrun_e17876afb41341a591c825f4 | UNDERPOWERED |
| sspec_07150b2dd72b23195b6df1fb | trade_date_block_bootstrap | 10902 | BLOCKED | False | True | surrun_5041f36fcb5e2507307a8019 | UNDERPOWERED |
| sspec_07150b2dd72b23195b6df1fb | trade_date_block_bootstrap | 10903 | BLOCKED | False | True | surrun_5337ffc74ad8c90670ab3764 | UNDERPOWERED |
| sspec_07150b2dd72b23195b6df1fb | trade_date_block_bootstrap | 10904 | BLOCKED | False | True | surrun_dc5987ac94cdd7f2139f82ad | UNDERPOWERED |
| sspec_9b19d724d359876bd4fc069a | trade_date_block_bootstrap | 10905 | BLOCKED | False | True | surrun_c049459d79b53196312dad9c | UNDERPOWERED |
| sspec_9b19d724d359876bd4fc069a | trade_date_block_bootstrap | 10906 | BLOCKED | False | True | surrun_2cc9786fee9f509820117ef4 | UNDERPOWERED |
| sspec_9b19d724d359876bd4fc069a | trade_date_block_bootstrap | 10907 | BLOCKED | False | True | surrun_335ca4b9a57e4a9f978b19f3 | UNDERPOWERED |
| sspec_fca8fad02351c94da2b9a107 | trade_date_block_bootstrap | 10908 | BLOCKED | False | True | surrun_7b629ba201a07fac6655a631 | UNDERPOWERED |
| sspec_fca8fad02351c94da2b9a107 | trade_date_block_bootstrap | 10909 | BLOCKED | False | True | surrun_f833c0d54d470f5b8137adb8 | UNDERPOWERED |
| sspec_fca8fad02351c94da2b9a107 | trade_date_block_bootstrap | 10910 | BLOCKED | False | True | surrun_b63294f6a31a765f32c00969 | UNDERPOWERED |
| sspec_1a6a825c5697207538903015 | trade_date_block_bootstrap | 10911 | BLOCKED | False | True | surrun_204df984096c79d691f0374d | UNDERPOWERED |
| sspec_1a6a825c5697207538903015 | trade_date_block_bootstrap | 10912 | BLOCKED | False | True | surrun_0b41e8cec3f228178cb2b5e1 | UNDERPOWERED |
| sspec_1a6a825c5697207538903015 | trade_date_block_bootstrap | 10913 | BLOCKED | False | True | surrun_b18e93463fc682ed46d0ea9e | UNDERPOWERED |
| sspec_ac73dbd9b8aab366c7825c0b | trade_date_block_bootstrap | 10914 | BLOCKED | False | True | surrun_9e74c74aa417c60674a0c178 | UNDERPOWERED |
| sspec_ac73dbd9b8aab366c7825c0b | trade_date_block_bootstrap | 10915 | BLOCKED | False | True | surrun_9b6da81612ee81e5e806f201 | UNDERPOWERED |
| sspec_ac73dbd9b8aab366c7825c0b | trade_date_block_bootstrap | 10916 | BLOCKED | False | True | surrun_8f14eda5addac953eac1bc2a | UNDERPOWERED |
| sspec_2ebf97e36be5f4ea57da9df8 | trade_date_block_bootstrap | 10917 | BLOCKED | False | True | surrun_ef3a49af80fb4a774dbc5274 | UNDERPOWERED |
| sspec_2ebf97e36be5f4ea57da9df8 | trade_date_block_bootstrap | 10918 | BLOCKED | False | True | surrun_127a15c0522d8b2f734496fb | UNDERPOWERED |
| sspec_2ebf97e36be5f4ea57da9df8 | trade_date_block_bootstrap | 10919 | BLOCKED | False | True | surrun_d610a1f00d7933cfee2d10b0 | UNDERPOWERED |
| sspec_d2ac0ee91418667b6e4960ca | trade_date_block_bootstrap | 10920 | BLOCKED | False | True | surrun_5da6c952d437f58f5f005832 | UNDERPOWERED |
| sspec_d2ac0ee91418667b6e4960ca | trade_date_block_bootstrap | 10921 | BLOCKED | False | True | surrun_cc48d284e9a5aecf7d1de680 | UNDERPOWERED |
| sspec_d2ac0ee91418667b6e4960ca | trade_date_block_bootstrap | 10922 | BLOCKED | False | True | surrun_1d5a9d2196eb5c7e2a1235ff | UNDERPOWERED |
| sspec_d17d09c83e2c7d143ed0625c | trade_date_block_bootstrap | 10923 | BLOCKED | False | True | surrun_8eead5042e2dc5d0fc5faea9 | UNDERPOWERED |
| sspec_d17d09c83e2c7d143ed0625c | trade_date_block_bootstrap | 10924 | BLOCKED | False | True | surrun_6cea59b7cd10b281ebc62180 | UNDERPOWERED |
| sspec_d17d09c83e2c7d143ed0625c | trade_date_block_bootstrap | 10925 | BLOCKED | False | True | surrun_eca5cec61f816ee07355659f | UNDERPOWERED |
| sspec_c886f447ae20c4abaf827d01 | trade_date_block_bootstrap | 10926 | BLOCKED | False | True | surrun_6506fd75b4207c7d3a9d7f08 | UNDERPOWERED |
| sspec_c886f447ae20c4abaf827d01 | trade_date_block_bootstrap | 10927 | BLOCKED | False | True | surrun_7e928afcdcd917a379f1ac7a | UNDERPOWERED |
| sspec_c886f447ae20c4abaf827d01 | trade_date_block_bootstrap | 10928 | BLOCKED | False | True | surrun_8af1d46c9233896095095a9e | UNDERPOWERED |
| sspec_87aa803690b56992f819a009 | trade_date_block_bootstrap | 10929 | BLOCKED | False | True | surrun_08ff6f7c96ce326f1e0fd940 | UNDERPOWERED |
| sspec_87aa803690b56992f819a009 | trade_date_block_bootstrap | 10930 | BLOCKED | False | True | surrun_fc9722c6bff2f41e6bc695ab | UNDERPOWERED |
| sspec_87aa803690b56992f819a009 | trade_date_block_bootstrap | 10931 | BLOCKED | False | True | surrun_c4554cddf0c7432a9dadcf46 | UNDERPOWERED |
| sspec_fcb62bbe8bc8d99a832d211d | trade_date_block_bootstrap | 10932 | BLOCKED | False | True | surrun_cd4a61113ec4983e3104680a | UNDERPOWERED |
| sspec_fcb62bbe8bc8d99a832d211d | trade_date_block_bootstrap | 10933 | BLOCKED | False | True | surrun_05b23e48cfac3a04bca19b8b | UNDERPOWERED |
| sspec_fcb62bbe8bc8d99a832d211d | trade_date_block_bootstrap | 10934 | BLOCKED | False | True | surrun_220c781f423529fef86e161a | UNDERPOWERED |
| sspec_d2f326af93df07560a9b8db3 | trade_date_block_bootstrap | 10935 | BLOCKED | False | True | surrun_de54634ff793b674b309a233 | UNDERPOWERED |
| sspec_d2f326af93df07560a9b8db3 | trade_date_block_bootstrap | 10936 | BLOCKED | False | True | surrun_d4314a273624e2fb5fa11b7d | UNDERPOWERED |
| sspec_d2f326af93df07560a9b8db3 | trade_date_block_bootstrap | 10937 | BLOCKED | False | True | surrun_e1f72c9e4cfecfc30ca87738 | UNDERPOWERED |
| sspec_6ec1ab42c37a5f71362e9216 | trade_date_block_bootstrap | 10938 | BLOCKED | False | True | surrun_70983b85bd25811cd6b0b750 | UNDERPOWERED |
| sspec_6ec1ab42c37a5f71362e9216 | trade_date_block_bootstrap | 10939 | BLOCKED | False | True | surrun_db016a525f32191af87662dd | UNDERPOWERED |
| sspec_6ec1ab42c37a5f71362e9216 | trade_date_block_bootstrap | 10940 | BLOCKED | False | True | surrun_84a7f7c197928c2ddcaf8ae1 | UNDERPOWERED |
| sspec_8721bad2dcdde7bef4e0cfed | trade_date_block_bootstrap | 10941 | BLOCKED | False | True | surrun_f22af16297cbb05a56dbad7d | UNDERPOWERED |
| sspec_8721bad2dcdde7bef4e0cfed | trade_date_block_bootstrap | 10942 | BLOCKED | False | True | surrun_ac6819f5229740d6f1b15c11 | UNDERPOWERED |
| sspec_8721bad2dcdde7bef4e0cfed | trade_date_block_bootstrap | 10943 | BLOCKED | False | True | surrun_d2141df9720afd4e4a9d7734 | UNDERPOWERED |
| sspec_28e61fdb46db16a86d67ae64 | trade_date_block_bootstrap | 10944 | BLOCKED | False | True | surrun_b1fdfa1f7dc13f82b6f54ce2 | UNDERPOWERED |
| sspec_28e61fdb46db16a86d67ae64 | trade_date_block_bootstrap | 10945 | BLOCKED | False | True | surrun_96a49865939d6faa3f6ca2db | UNDERPOWERED |
| sspec_28e61fdb46db16a86d67ae64 | trade_date_block_bootstrap | 10946 | BLOCKED | False | True | surrun_b589092e7c95a16495eedbf4 | UNDERPOWERED |
| sspec_caa754ddb6109aed20216758 | trade_date_block_bootstrap | 10947 | BLOCKED | False | True | surrun_f234a47337b3ecc85e7ef228 | UNDERPOWERED |
| sspec_caa754ddb6109aed20216758 | trade_date_block_bootstrap | 10948 | BLOCKED | False | True | surrun_d06fedbcdb3a88a9dcff2297 | UNDERPOWERED |
| sspec_caa754ddb6109aed20216758 | trade_date_block_bootstrap | 10949 | BLOCKED | False | True | surrun_0ca3cb3caabb54c57844a3bc | UNDERPOWERED |
| sspec_72e29b3149b3f241fef8af82 | trade_date_block_bootstrap | 10950 | BLOCKED | False | True | surrun_c4b674adb4577ade81008db2 | UNDERPOWERED |
| sspec_72e29b3149b3f241fef8af82 | trade_date_block_bootstrap | 10951 | BLOCKED | False | True | surrun_7b6ad90361de23ba722ed778 | UNDERPOWERED |
| sspec_72e29b3149b3f241fef8af82 | trade_date_block_bootstrap | 10952 | BLOCKED | False | True | surrun_d2791560d7f68c4108d1a103 | UNDERPOWERED |
| sspec_c37b26eba6e520e6744b85c4 | trade_date_block_bootstrap | 10953 | BLOCKED | False | True | surrun_1009065bdd79822a9421db82 | UNDERPOWERED |
| sspec_c37b26eba6e520e6744b85c4 | trade_date_block_bootstrap | 10954 | BLOCKED | False | True | surrun_e3b7a2e2b2f2f2fa672badae | UNDERPOWERED |
| sspec_c37b26eba6e520e6744b85c4 | trade_date_block_bootstrap | 10955 | BLOCKED | False | True | surrun_0c404ccb92f6fad2ffbbd3a0 | UNDERPOWERED |
| sspec_81edb80e40b74e3e95cbe8b0 | trade_date_block_bootstrap | 10956 | BLOCKED | False | True | surrun_0fdcea174e605c00b9152590 | UNDERPOWERED |
| sspec_81edb80e40b74e3e95cbe8b0 | trade_date_block_bootstrap | 10957 | BLOCKED | False | True | surrun_f1251ffb7c17eb1f817dde22 | UNDERPOWERED |
| sspec_81edb80e40b74e3e95cbe8b0 | trade_date_block_bootstrap | 10958 | BLOCKED | False | True | surrun_e6b83b6adb09e83a5bf88f8a | UNDERPOWERED |
| sspec_3be755c64a80f104f27efb43 | trade_date_block_bootstrap | 10959 | BLOCKED | False | True | surrun_ebf3a8d57b85962033e32853 | UNDERPOWERED |
| sspec_3be755c64a80f104f27efb43 | trade_date_block_bootstrap | 10960 | BLOCKED | False | True | surrun_fd0f117242d1fe04dce9b58c | UNDERPOWERED |
| sspec_3be755c64a80f104f27efb43 | trade_date_block_bootstrap | 10961 | BLOCKED | False | True | surrun_f3ad9d2c7138e8f5b8fcbb12 | UNDERPOWERED |
| sspec_1d42f25d84cb70bff806e8b5 | trade_date_block_bootstrap | 10962 | BLOCKED | False | True | surrun_d43c7c26a089eb660dd47ea0 | UNDERPOWERED |
| sspec_1d42f25d84cb70bff806e8b5 | trade_date_block_bootstrap | 10963 | BLOCKED | False | True | surrun_0ce9f0911fad18a9dc37a5b9 | UNDERPOWERED |
| sspec_1d42f25d84cb70bff806e8b5 | trade_date_block_bootstrap | 10964 | BLOCKED | False | True | surrun_bb0ac8fb63615e046b468445 | UNDERPOWERED |
| sspec_d9725acf9fdcfb8bddadb32c | trade_date_block_bootstrap | 10965 | BLOCKED | False | True | surrun_50dcc8ae96ca34ca78667f7f | UNDERPOWERED |
| sspec_d9725acf9fdcfb8bddadb32c | trade_date_block_bootstrap | 10966 | BLOCKED | False | True | surrun_416b236e427d7a537c75017d | UNDERPOWERED |
| sspec_d9725acf9fdcfb8bddadb32c | trade_date_block_bootstrap | 10967 | BLOCKED | False | True | surrun_32ed47f7a8ca663f3ece7e8c | UNDERPOWERED |
| sspec_809d509103d8505412f9f6d9 | trade_date_block_bootstrap | 10968 | BLOCKED | False | True | surrun_70eede218d42e8f190d61487 | UNDERPOWERED |
| sspec_809d509103d8505412f9f6d9 | trade_date_block_bootstrap | 10969 | BLOCKED | False | True | surrun_a9d8f5c08083ea36e4f96900 | UNDERPOWERED |
| sspec_809d509103d8505412f9f6d9 | trade_date_block_bootstrap | 10970 | BLOCKED | False | True | surrun_e2fe24590a64fb2498c2f6ee | UNDERPOWERED |
| sspec_35912f604fd3ad171b8b48ed | trade_date_block_bootstrap | 10971 | BLOCKED | False | True | surrun_5cc88a4095e746dd7c8adedf | UNDERPOWERED |
| sspec_35912f604fd3ad171b8b48ed | trade_date_block_bootstrap | 10972 | BLOCKED | False | True | surrun_e9f54a8236fd7f785d7b2410 | UNDERPOWERED |
| sspec_35912f604fd3ad171b8b48ed | trade_date_block_bootstrap | 10973 | BLOCKED | False | True | surrun_48fee7d5514b10c201342b05 | UNDERPOWERED |
| sspec_5bd27a691f2c763e23e0ac5d | trade_date_block_bootstrap | 10974 | BLOCKED | False | True | surrun_4e02e3fbea19a7b42664bff9 | UNDERPOWERED |
| sspec_5bd27a691f2c763e23e0ac5d | trade_date_block_bootstrap | 10975 | BLOCKED | False | True | surrun_7293f0bbd3dc702d8f79ca19 | UNDERPOWERED |
| sspec_5bd27a691f2c763e23e0ac5d | trade_date_block_bootstrap | 10976 | BLOCKED | False | True | surrun_44d99a3e8c5111341e334c02 | UNDERPOWERED |
| sspec_d876e1a6bb6d66cf9163f018 | trade_date_block_bootstrap | 10977 | BLOCKED | False | True | surrun_a61a2a91ee882983a737c323 | UNDERPOWERED |
| sspec_d876e1a6bb6d66cf9163f018 | trade_date_block_bootstrap | 10978 | BLOCKED | False | True | surrun_7cbdb4e5283244dff681bc2c | UNDERPOWERED |
| sspec_d876e1a6bb6d66cf9163f018 | trade_date_block_bootstrap | 10979 | BLOCKED | False | True | surrun_ba9c9e47d1e4f319387de845 | UNDERPOWERED |
| sspec_d5264bc5f5af602643535981 | trade_date_block_bootstrap | 10980 | BLOCKED | False | True | surrun_e8cb44f855981b34c808a6b6 | UNDERPOWERED |
| sspec_d5264bc5f5af602643535981 | trade_date_block_bootstrap | 10981 | BLOCKED | False | True | surrun_4ba42c4b30f2dfd82875af74 | UNDERPOWERED |
| sspec_d5264bc5f5af602643535981 | trade_date_block_bootstrap | 10982 | BLOCKED | False | True | surrun_eec5b13b4ffe54a1bdb02ac9 | UNDERPOWERED |
| sspec_b70f9ffb4c8891e3b7fb9da7 | trade_date_block_bootstrap | 10983 | BLOCKED | False | True | surrun_87efb67f04c667efe7cd915e | UNDERPOWERED |
| sspec_b70f9ffb4c8891e3b7fb9da7 | trade_date_block_bootstrap | 10984 | BLOCKED | False | True | surrun_f37aa0aa66e028fb8161c634 | UNDERPOWERED |
| sspec_b70f9ffb4c8891e3b7fb9da7 | trade_date_block_bootstrap | 10985 | BLOCKED | False | True | surrun_2e03a548ada67209a3ec9c08 | UNDERPOWERED |
| sspec_b678936ebffc4eb9371805c3 | trade_date_block_bootstrap | 10986 | BLOCKED | False | True | surrun_0b3d8b54ca29f41350caa254 | UNDERPOWERED |
| sspec_b678936ebffc4eb9371805c3 | trade_date_block_bootstrap | 10987 | BLOCKED | False | True | surrun_8787f7148f4c18d7e86ca3fc | UNDERPOWERED |
| sspec_b678936ebffc4eb9371805c3 | trade_date_block_bootstrap | 10988 | BLOCKED | False | True | surrun_47bafbf1451badff6b6f0034 | UNDERPOWERED |
| sspec_1b145fdde9ee6101806e1356 | trade_date_block_bootstrap | 10989 | BLOCKED | False | True | surrun_574bbc9106eca8e6aeddb0ff | UNDERPOWERED |
| sspec_1b145fdde9ee6101806e1356 | trade_date_block_bootstrap | 10990 | BLOCKED | False | True | surrun_63dd654eecc1dd8e75a30742 | UNDERPOWERED |
| sspec_1b145fdde9ee6101806e1356 | trade_date_block_bootstrap | 10991 | BLOCKED | False | True | surrun_dd7f2d08cd88c42ce34e4b2d | UNDERPOWERED |
| sspec_09ab9383bb4ac63fb644b9cd | trade_date_block_bootstrap | 10992 | BLOCKED | False | True | surrun_b1a363f94eb561e6bee4a6b4 | UNDERPOWERED |
| sspec_09ab9383bb4ac63fb644b9cd | trade_date_block_bootstrap | 10993 | BLOCKED | False | True | surrun_574bb576e2461670b5a56a4b | UNDERPOWERED |
| sspec_09ab9383bb4ac63fb644b9cd | trade_date_block_bootstrap | 10994 | BLOCKED | False | True | surrun_ee6ce92d30a2ff5dc69681d0 | UNDERPOWERED |
| sspec_b0099321ed5b03adf399a8ad | trade_date_block_bootstrap | 10995 | BLOCKED | False | True | surrun_2ff297890e04420d414ffe7d | UNDERPOWERED |
| sspec_b0099321ed5b03adf399a8ad | trade_date_block_bootstrap | 10996 | BLOCKED | False | True | surrun_636aca4ec5a5b4d6697468b5 | UNDERPOWERED |
| sspec_b0099321ed5b03adf399a8ad | trade_date_block_bootstrap | 10997 | BLOCKED | False | True | surrun_3f5934b55c53d5cb5e418401 | UNDERPOWERED |
| sspec_7dda7e7fd6242f54de62c1df | trade_date_block_bootstrap | 10998 | BLOCKED | False | True | surrun_728265ff174bf6891d34cdc1 | UNDERPOWERED |
| sspec_7dda7e7fd6242f54de62c1df | trade_date_block_bootstrap | 10999 | BLOCKED | False | True | surrun_9b4bb2b54cb6f10fd48e0966 | UNDERPOWERED |
| sspec_7dda7e7fd6242f54de62c1df | trade_date_block_bootstrap | 11000 | BLOCKED | False | True | surrun_3962d60966c73d67ea11f8b4 | UNDERPOWERED |
| sspec_bb268319371895d086b6c4b7 | trade_date_block_bootstrap | 11001 | BLOCKED | False | True | surrun_ad6fc3eed8b1e624d261ce2f | UNDERPOWERED |
| sspec_bb268319371895d086b6c4b7 | trade_date_block_bootstrap | 11002 | BLOCKED | False | True | surrun_052ac6e3bce8a6f4546860d3 | UNDERPOWERED |
| sspec_bb268319371895d086b6c4b7 | trade_date_block_bootstrap | 11003 | BLOCKED | False | True | surrun_8ad2cbd189e3f6b3768280bb | UNDERPOWERED |
| sspec_e74476332df1a2949e777f3d | trade_date_block_bootstrap | 11004 | BLOCKED | False | True | surrun_1afba70f4ec4fe1a4e73c525 | UNDERPOWERED |
| sspec_e74476332df1a2949e777f3d | trade_date_block_bootstrap | 11005 | BLOCKED | False | True | surrun_83e974b06c4d5d004ae85fff | UNDERPOWERED |
| sspec_e74476332df1a2949e777f3d | trade_date_block_bootstrap | 11006 | BLOCKED | False | True | surrun_0cbdb81fbc225109a675d952 | UNDERPOWERED |
| sspec_ddc9de0c5f54323e43a39d73 | trade_date_block_bootstrap | 11007 | BLOCKED | False | True | surrun_c6429f3c5dc610a1c13b24b3 | UNDERPOWERED |
| sspec_ddc9de0c5f54323e43a39d73 | trade_date_block_bootstrap | 11008 | BLOCKED | False | True | surrun_4cbb09bef9409e16026de7f6 | UNDERPOWERED |
| sspec_ddc9de0c5f54323e43a39d73 | trade_date_block_bootstrap | 11009 | BLOCKED | False | True | surrun_d7684570e27ec67b31c2436a | UNDERPOWERED |
| sspec_77e79d650fc14b8ab88d5049 | trade_date_block_bootstrap | 11010 | BLOCKED | False | True | surrun_1f03b7f6ac63ac87ad30af42 | UNDERPOWERED |
| sspec_77e79d650fc14b8ab88d5049 | trade_date_block_bootstrap | 11011 | BLOCKED | False | True | surrun_090adbc5196a9aeeb044cc4d | UNDERPOWERED |
| sspec_77e79d650fc14b8ab88d5049 | trade_date_block_bootstrap | 11012 | BLOCKED | False | True | surrun_1d1cf15ce9fbe42866f9d66f | UNDERPOWERED |
| sspec_33fce059c40aa2b6925d3d77 | trade_date_block_bootstrap | 11013 | BLOCKED | False | True | surrun_266a2fb56ee5b188b8816690 | UNDERPOWERED |
| sspec_33fce059c40aa2b6925d3d77 | trade_date_block_bootstrap | 11014 | BLOCKED | False | True | surrun_dcf8a0103b7b447f4102961f | UNDERPOWERED |
| sspec_33fce059c40aa2b6925d3d77 | trade_date_block_bootstrap | 11015 | BLOCKED | False | True | surrun_d25381690d665e4344608b60 | UNDERPOWERED |
| sspec_74ecbfeb27ea193b58fbcf7a | trade_date_block_bootstrap | 11016 | BLOCKED | False | True | surrun_f9c23fd26b09b311a240a8cc | UNDERPOWERED |
| sspec_74ecbfeb27ea193b58fbcf7a | trade_date_block_bootstrap | 11017 | BLOCKED | False | True | surrun_f4e20d8d8b0dc8a589bb1963 | UNDERPOWERED |
| sspec_74ecbfeb27ea193b58fbcf7a | trade_date_block_bootstrap | 11018 | BLOCKED | False | True | surrun_93b2dd93de0cd99c896e3546 | UNDERPOWERED |
| sspec_eb6e883867ef0bcf6caa7ea0 | trade_date_block_bootstrap | 11019 | BLOCKED | False | True | surrun_f9a9b5c788550705c42b8311 | UNDERPOWERED |
| sspec_eb6e883867ef0bcf6caa7ea0 | trade_date_block_bootstrap | 11020 | BLOCKED | False | True | surrun_75544b46b386550cbd2b6638 | UNDERPOWERED |
| sspec_eb6e883867ef0bcf6caa7ea0 | trade_date_block_bootstrap | 11021 | BLOCKED | False | True | surrun_77b6c615c2a3e9f1f1bf3425 | UNDERPOWERED |
| sspec_39056dc8e349ef61860a12ef | trade_date_block_bootstrap | 11022 | BLOCKED | False | True | surrun_9bc2bf13fb7a6787ce7b71cf | UNDERPOWERED |
| sspec_39056dc8e349ef61860a12ef | trade_date_block_bootstrap | 11023 | BLOCKED | False | True | surrun_a50c6e854e625c6cb9681f08 | UNDERPOWERED |
| sspec_39056dc8e349ef61860a12ef | trade_date_block_bootstrap | 11024 | BLOCKED | False | True | surrun_cf3ebbcf822bb20665229b3c | UNDERPOWERED |
| sspec_2019bf333c27491214c06bec | trade_date_block_bootstrap | 11025 | BLOCKED | False | True | surrun_f1aaf26931ecfafbe6953a5e | UNDERPOWERED |
| sspec_2019bf333c27491214c06bec | trade_date_block_bootstrap | 11026 | BLOCKED | False | True | surrun_bdf2f1825caf7a724591f9d7 | UNDERPOWERED |
| sspec_2019bf333c27491214c06bec | trade_date_block_bootstrap | 11027 | BLOCKED | False | True | surrun_c1bfff9cb874e00887891ae2 | UNDERPOWERED |
| sspec_902fe2e261aeca394476c654 | trade_date_block_bootstrap | 11028 | BLOCKED | False | True | surrun_c288fe0d6239ee1cdaca1a1d | UNDERPOWERED |
| sspec_902fe2e261aeca394476c654 | trade_date_block_bootstrap | 11029 | BLOCKED | False | True | surrun_b8cd16f2278b1e11eb5ba901 | UNDERPOWERED |
| sspec_902fe2e261aeca394476c654 | trade_date_block_bootstrap | 11030 | BLOCKED | False | True | surrun_bda10b19a70d1b25f7459d6d | UNDERPOWERED |
| sspec_754e4a365bbdfcd447e5cb7e | trade_date_block_bootstrap | 11031 | BLOCKED | False | True | surrun_b9c4ba5310c03e47a306a7f5 | UNDERPOWERED |
| sspec_754e4a365bbdfcd447e5cb7e | trade_date_block_bootstrap | 11032 | BLOCKED | False | True | surrun_e917c3ae10ee1d0422b7f6a9 | UNDERPOWERED |
| sspec_754e4a365bbdfcd447e5cb7e | trade_date_block_bootstrap | 11033 | BLOCKED | False | True | surrun_fc5d89d7f0f0eb4581bc7d2e | UNDERPOWERED |
| sspec_6470b2f1421eb6ece96e6fde | trade_date_block_bootstrap | 11034 | BLOCKED | False | True | surrun_55f6be4b7fd6e3ca8c6e9a63 | UNDERPOWERED |
| sspec_6470b2f1421eb6ece96e6fde | trade_date_block_bootstrap | 11035 | BLOCKED | False | True | surrun_05a34d0a62b697d463cb9e0d | UNDERPOWERED |
| sspec_6470b2f1421eb6ece96e6fde | trade_date_block_bootstrap | 11036 | BLOCKED | False | True | surrun_1f3d22a7302af0764aa5440b | UNDERPOWERED |
| sspec_609da1456836e92dbd115cdf | trade_date_block_bootstrap | 11037 | BLOCKED | False | True | surrun_61a1ad5eddceb1fbedd663df | UNDERPOWERED |
| sspec_609da1456836e92dbd115cdf | trade_date_block_bootstrap | 11038 | BLOCKED | False | True | surrun_ecf8dd7ed2a4e137074a2708 | UNDERPOWERED |
| sspec_609da1456836e92dbd115cdf | trade_date_block_bootstrap | 11039 | BLOCKED | False | True | surrun_bae6d71c6d027dc9ad7b1400 | UNDERPOWERED |
| sspec_c8da1a619406d5fc3640e44d | trade_date_block_bootstrap | 11040 | BLOCKED | False | True | surrun_36124f5f034064a46f20cb0a | UNDERPOWERED |
| sspec_c8da1a619406d5fc3640e44d | trade_date_block_bootstrap | 11041 | BLOCKED | False | True | surrun_ab52f16e8c3c888289c4e9f9 | UNDERPOWERED |
| sspec_c8da1a619406d5fc3640e44d | trade_date_block_bootstrap | 11042 | BLOCKED | False | True | surrun_6dd270c46ef2b5e1966e8f23 | UNDERPOWERED |
| sspec_354dedf2168616750d27e6e3 | trade_date_block_bootstrap | 11043 | BLOCKED | False | True | surrun_3ac22c1dee1307f1d98e6159 | UNDERPOWERED |
| sspec_354dedf2168616750d27e6e3 | trade_date_block_bootstrap | 11044 | BLOCKED | False | True | surrun_701287338c03d273e4f95814 | UNDERPOWERED |
| sspec_354dedf2168616750d27e6e3 | trade_date_block_bootstrap | 11045 | BLOCKED | False | True | surrun_bd7b16ef417514cd00099b09 | UNDERPOWERED |
| sspec_6f6664bb324f991a702cb6e4 | trade_date_block_bootstrap | 11046 | BLOCKED | False | True | surrun_c026cf98617f6b99923895ba | UNDERPOWERED |
| sspec_6f6664bb324f991a702cb6e4 | trade_date_block_bootstrap | 11047 | BLOCKED | False | True | surrun_1ba13a875ee0b7cd2a21e97e | UNDERPOWERED |
| sspec_6f6664bb324f991a702cb6e4 | trade_date_block_bootstrap | 11048 | BLOCKED | False | True | surrun_ca6eae0f18fe3e44e4b9368a | UNDERPOWERED |
| sspec_8e35c1b1d7df13139d7c1ead | trade_date_block_bootstrap | 11049 | BLOCKED | False | True | surrun_af38e431135c6875d94fdb34 | UNDERPOWERED |
| sspec_8e35c1b1d7df13139d7c1ead | trade_date_block_bootstrap | 11050 | BLOCKED | False | True | surrun_a0ec2c8ed67313c5c6db08a4 | UNDERPOWERED |
| sspec_8e35c1b1d7df13139d7c1ead | trade_date_block_bootstrap | 11051 | BLOCKED | False | True | surrun_5c6e52360a7e5bf3cfc3bbb2 | UNDERPOWERED |
| sspec_394e0bad380d820aeb30c38e | trade_date_block_bootstrap | 11052 | BLOCKED | False | True | surrun_8b7193134acfc3e79f4aed14 | UNDERPOWERED |
| sspec_394e0bad380d820aeb30c38e | trade_date_block_bootstrap | 11053 | BLOCKED | False | True | surrun_5df1aa36b0c55ffe528eaf66 | UNDERPOWERED |
| sspec_394e0bad380d820aeb30c38e | trade_date_block_bootstrap | 11054 | BLOCKED | False | True | surrun_cede4adaa7d024e3326d4530 | UNDERPOWERED |
| sspec_9cfdad261b45e300fae589c2 | trade_date_block_bootstrap | 11055 | BLOCKED | False | True | surrun_6ed5e2f620522efb1ff5ef8f | UNDERPOWERED |
| sspec_9cfdad261b45e300fae589c2 | trade_date_block_bootstrap | 11056 | BLOCKED | False | True | surrun_6bc00a9d0a027bc0944f1a7e | UNDERPOWERED |
| sspec_9cfdad261b45e300fae589c2 | trade_date_block_bootstrap | 11057 | BLOCKED | False | True | surrun_b48f170f41b23c9057794c22 | UNDERPOWERED |
| sspec_e2969532bad0c415bdcdde8d | trade_date_block_bootstrap | 11058 | BLOCKED | False | True | surrun_8784f9bb78c5337de7de2be1 | UNDERPOWERED |
| sspec_e2969532bad0c415bdcdde8d | trade_date_block_bootstrap | 11059 | BLOCKED | False | True | surrun_3e0204f01ff626bd51996b05 | UNDERPOWERED |
| sspec_e2969532bad0c415bdcdde8d | trade_date_block_bootstrap | 11060 | BLOCKED | False | True | surrun_e7d3e93933083ae3f30da63e | UNDERPOWERED |
| sspec_eac636d3590c41a3d1ddb673 | trade_date_block_bootstrap | 11061 | BLOCKED | False | True | surrun_f3a9736305db188f451cd328 | UNDERPOWERED |
| sspec_eac636d3590c41a3d1ddb673 | trade_date_block_bootstrap | 11062 | BLOCKED | False | True | surrun_0bd5bcd877cd83ebac13f83a | UNDERPOWERED |
| sspec_eac636d3590c41a3d1ddb673 | trade_date_block_bootstrap | 11063 | BLOCKED | False | True | surrun_9e4fb0426a575cb72e08fbcf | UNDERPOWERED |
| sspec_ab299006e49b47c8f49e20fd | trade_date_block_bootstrap | 11064 | BLOCKED | False | True | surrun_76933f7bcfbcdab88c7b8029 | UNDERPOWERED |
| sspec_ab299006e49b47c8f49e20fd | trade_date_block_bootstrap | 11065 | BLOCKED | False | True | surrun_01e30df9828ad30549a4dffd | UNDERPOWERED |
| sspec_ab299006e49b47c8f49e20fd | trade_date_block_bootstrap | 11066 | BLOCKED | False | True | surrun_d8167c3b2acb74291731eef2 | UNDERPOWERED |
| sspec_ae6f5d73a533924661b9b21f | trade_date_block_bootstrap | 11067 | BLOCKED | False | True | surrun_ec3c914a67fde9adf31a4ddc | UNDERPOWERED |
| sspec_ae6f5d73a533924661b9b21f | trade_date_block_bootstrap | 11068 | BLOCKED | False | True | surrun_f38a0d9e8db7bc6295793ceb | UNDERPOWERED |
| sspec_ae6f5d73a533924661b9b21f | trade_date_block_bootstrap | 11069 | BLOCKED | False | True | surrun_60482d506587d4237c5f52a9 | UNDERPOWERED |
| sspec_f71c38f2c8f6d72080bb7280 | trade_date_block_bootstrap | 11070 | BLOCKED | False | True | surrun_dfed3d898f60abc9e234b6e5 | UNDERPOWERED |
| sspec_f71c38f2c8f6d72080bb7280 | trade_date_block_bootstrap | 11071 | BLOCKED | False | True | surrun_67e3bdfc5a0edc059e4cc66f | UNDERPOWERED |
| sspec_f71c38f2c8f6d72080bb7280 | trade_date_block_bootstrap | 11072 | BLOCKED | False | True | surrun_927e46ce7dc1de76414aecd5 | UNDERPOWERED |
| sspec_d4e5d00971e14494d88fe8bb | trade_date_block_bootstrap | 11073 | BLOCKED | False | True | surrun_941eb187ff1132a4f86b7d79 | UNDERPOWERED |
| sspec_d4e5d00971e14494d88fe8bb | trade_date_block_bootstrap | 11074 | BLOCKED | False | True | surrun_e0d39ea34139fd16a1b4df1f | UNDERPOWERED |
| sspec_d4e5d00971e14494d88fe8bb | trade_date_block_bootstrap | 11075 | BLOCKED | False | True | surrun_957ecbf5b5245b0dd4f64db5 | UNDERPOWERED |
| sspec_3f7bfd35ea00bc2f4c8ab216 | trade_date_block_bootstrap | 11076 | BLOCKED | False | True | surrun_4d43755825f30a1e4c7c0ccf | UNDERPOWERED |
| sspec_3f7bfd35ea00bc2f4c8ab216 | trade_date_block_bootstrap | 11077 | BLOCKED | False | True | surrun_693736534df7f2bf7a873560 | UNDERPOWERED |
| sspec_3f7bfd35ea00bc2f4c8ab216 | trade_date_block_bootstrap | 11078 | BLOCKED | False | True | surrun_e64afbfdc49b24bd3cce4a3e | UNDERPOWERED |
| sspec_aede76ccf55b93d831fa28df | trade_date_block_bootstrap | 11079 | BLOCKED | False | True | surrun_859b87a4238c1a029a7947db | UNDERPOWERED |
| sspec_aede76ccf55b93d831fa28df | trade_date_block_bootstrap | 11080 | BLOCKED | False | True | surrun_540ab11148f94eec4dbdf297 | UNDERPOWERED |
| sspec_aede76ccf55b93d831fa28df | trade_date_block_bootstrap | 11081 | BLOCKED | False | True | surrun_52ede9dea2f0804c34696e75 | UNDERPOWERED |
| sspec_2ee7653ba6e3c835c8da217f | trade_date_block_bootstrap | 11082 | BLOCKED | False | True | surrun_e6a005e29be14a7628d2b836 | UNDERPOWERED |
| sspec_2ee7653ba6e3c835c8da217f | trade_date_block_bootstrap | 11083 | BLOCKED | False | True | surrun_e66ba6beb64e8d84c092a2b7 | UNDERPOWERED |
| sspec_2ee7653ba6e3c835c8da217f | trade_date_block_bootstrap | 11084 | BLOCKED | False | True | surrun_f228d5a1cdd1f20dbbe8b4c3 | UNDERPOWERED |
| sspec_ef9bd7515011e9b1229ba215 | trade_date_block_bootstrap | 11085 | BLOCKED | False | True | surrun_ed508a42fa415a79af5a7bb2 | UNDERPOWERED |
| sspec_ef9bd7515011e9b1229ba215 | trade_date_block_bootstrap | 11086 | BLOCKED | False | True | surrun_911a4f15369bf21458f8e251 | UNDERPOWERED |
| sspec_ef9bd7515011e9b1229ba215 | trade_date_block_bootstrap | 11087 | BLOCKED | False | True | surrun_b44cf1c31a65b96e9a16a565 | UNDERPOWERED |
| sspec_17c27adb161c73150fa58d57 | trade_date_block_bootstrap | 11088 | BLOCKED | False | True | surrun_2e0b181f5e5c4cc3a1789022 | UNDERPOWERED |
| sspec_17c27adb161c73150fa58d57 | trade_date_block_bootstrap | 11089 | BLOCKED | False | True | surrun_5f89aa917ea4d1ef8fce4723 | UNDERPOWERED |
| sspec_17c27adb161c73150fa58d57 | trade_date_block_bootstrap | 11090 | BLOCKED | False | True | surrun_d2da679c90da47d40794f5d9 | UNDERPOWERED |
| sspec_f1faf2df354c116a1903f645 | trade_date_block_bootstrap | 11091 | BLOCKED | False | True | surrun_db04e3e91274bc7b894f1b23 | UNDERPOWERED |
| sspec_f1faf2df354c116a1903f645 | trade_date_block_bootstrap | 11092 | BLOCKED | False | True | surrun_056687b422938452d5b0b716 | UNDERPOWERED |
| sspec_f1faf2df354c116a1903f645 | trade_date_block_bootstrap | 11093 | BLOCKED | False | True | surrun_9f17606415243338681e6b6e | UNDERPOWERED |
| sspec_1d45680b9034a8c700ff54b1 | trade_date_block_bootstrap | 11094 | BLOCKED | False | True | surrun_077bed822edacf5b01984ca5 | UNDERPOWERED |
| sspec_1d45680b9034a8c700ff54b1 | trade_date_block_bootstrap | 11095 | BLOCKED | False | True | surrun_cb8692ee5897ce243567a11c | UNDERPOWERED |
| sspec_1d45680b9034a8c700ff54b1 | trade_date_block_bootstrap | 11096 | BLOCKED | False | True | surrun_47702e975ce84b1f78f41841 | UNDERPOWERED |
| sspec_8057ffa61a36f67e9e6307af | trade_date_block_bootstrap | 11097 | BLOCKED | False | True | surrun_6f1e3e32ac8504339a2ad06a | UNDERPOWERED |
| sspec_8057ffa61a36f67e9e6307af | trade_date_block_bootstrap | 11098 | BLOCKED | False | True | surrun_32a2a4f9049dce0e7a68d7ab | UNDERPOWERED |
| sspec_8057ffa61a36f67e9e6307af | trade_date_block_bootstrap | 11099 | BLOCKED | False | True | surrun_75f8106ed15c559f45230ac7 | UNDERPOWERED |
| sspec_a8203d45deee12d65e4ec641 | trade_date_block_bootstrap | 11100 | BLOCKED | False | True | surrun_89177b5708a1091f6e025351 | UNDERPOWERED |
| sspec_a8203d45deee12d65e4ec641 | trade_date_block_bootstrap | 11101 | BLOCKED | False | True | surrun_773d42c2c36f3f079c997730 | UNDERPOWERED |
| sspec_a8203d45deee12d65e4ec641 | trade_date_block_bootstrap | 11102 | BLOCKED | False | True | surrun_698c89d636d76ba7eeca00fc | UNDERPOWERED |
| sspec_b3eec8ad6c4b112b3bd80a85 | trade_date_block_bootstrap | 11103 | BLOCKED | False | True | surrun_39ec108dff626375eb3d651e | UNDERPOWERED |
| sspec_b3eec8ad6c4b112b3bd80a85 | trade_date_block_bootstrap | 11104 | BLOCKED | False | True | surrun_0ddbf42d28d1e792dd369b3b | UNDERPOWERED |
| sspec_b3eec8ad6c4b112b3bd80a85 | trade_date_block_bootstrap | 11105 | BLOCKED | False | True | surrun_c4f9ec6b9d2f631f2160f493 | UNDERPOWERED |
| sspec_adb4a00400ed2741e8e3b8d5 | trade_date_block_bootstrap | 11106 | BLOCKED | False | True | surrun_90634b46fae2e9a3bd156bc4 | UNDERPOWERED |
| sspec_adb4a00400ed2741e8e3b8d5 | trade_date_block_bootstrap | 11107 | BLOCKED | False | True | surrun_4763282d6a64a0b81592ca1b | UNDERPOWERED |
| sspec_adb4a00400ed2741e8e3b8d5 | trade_date_block_bootstrap | 11108 | BLOCKED | False | True | surrun_6e75a7a4324df3ebc59a1343 | UNDERPOWERED |
| sspec_d0c40d9ac5a8647f613bdeea | trade_date_block_bootstrap | 11109 | BLOCKED | False | True | surrun_7d46accf1a0fbea79c8b958f | UNDERPOWERED |
| sspec_d0c40d9ac5a8647f613bdeea | trade_date_block_bootstrap | 11110 | BLOCKED | False | True | surrun_aa807a1b33510cac0f80dd4d | UNDERPOWERED |
| sspec_d0c40d9ac5a8647f613bdeea | trade_date_block_bootstrap | 11111 | BLOCKED | False | True | surrun_221439e94d84ceb79fb9795a | UNDERPOWERED |
| sspec_b24e20c46d7d64092278d903 | trade_date_block_bootstrap | 11112 | BLOCKED | False | True | surrun_aa64d82792f27d9e3f3175fe | UNDERPOWERED |
| sspec_b24e20c46d7d64092278d903 | trade_date_block_bootstrap | 11113 | BLOCKED | False | True | surrun_53a1252eb5b7c0c7bcefe774 | UNDERPOWERED |
| sspec_b24e20c46d7d64092278d903 | trade_date_block_bootstrap | 11114 | BLOCKED | False | True | surrun_f17b2c6d1774b4c63fd4515c | UNDERPOWERED |
| sspec_110149bdceeea19e9dceefcf | trade_date_block_bootstrap | 11115 | BLOCKED | False | True | surrun_0eb0d74f8cdf1ed14adde112 | UNDERPOWERED |
| sspec_110149bdceeea19e9dceefcf | trade_date_block_bootstrap | 11116 | BLOCKED | False | True | surrun_74e2775023b6e9f91cb5230f | UNDERPOWERED |
| sspec_110149bdceeea19e9dceefcf | trade_date_block_bootstrap | 11117 | BLOCKED | False | True | surrun_a3e45167a52c1b81cedf6e5a | UNDERPOWERED |
| sspec_2322292e7077f8d14ec28437 | trade_date_block_bootstrap | 11118 | BLOCKED | False | True | surrun_a8fdd55d78187544836292b9 | UNDERPOWERED |
| sspec_2322292e7077f8d14ec28437 | trade_date_block_bootstrap | 11119 | BLOCKED | False | True | surrun_60873330e419fc7a19679c0f | UNDERPOWERED |
| sspec_2322292e7077f8d14ec28437 | trade_date_block_bootstrap | 11120 | BLOCKED | False | True | surrun_482df11258a175ad84265760 | UNDERPOWERED |
| sspec_04208fd0f968d503db6b928d | trade_date_block_bootstrap | 11121 | BLOCKED | False | True | surrun_3c1ce97fb09f08475840f51a | UNDERPOWERED |
| sspec_04208fd0f968d503db6b928d | trade_date_block_bootstrap | 11122 | BLOCKED | False | True | surrun_4ab1fbfc16bf8745b398315e | UNDERPOWERED |
| sspec_04208fd0f968d503db6b928d | trade_date_block_bootstrap | 11123 | BLOCKED | False | True | surrun_5d37c5b4b7b5f89f03b37ab0 | UNDERPOWERED |
| sspec_07962b3c7cdd5285b7a90b8e | trade_date_block_bootstrap | 11124 | BLOCKED | False | True | surrun_3f581319ad6869175266eaee | UNDERPOWERED |
| sspec_07962b3c7cdd5285b7a90b8e | trade_date_block_bootstrap | 11125 | BLOCKED | False | True | surrun_219caeb71ad0df9ecd9e2066 | UNDERPOWERED |
| sspec_07962b3c7cdd5285b7a90b8e | trade_date_block_bootstrap | 11126 | BLOCKED | False | True | surrun_7888cbbf091015896958f37a | UNDERPOWERED |
| sspec_f8c1786bccab51f017ec0e51 | trade_date_block_bootstrap | 11127 | BLOCKED | False | True | surrun_5be7df9c08f5b3af4625be55 | UNDERPOWERED |
| sspec_f8c1786bccab51f017ec0e51 | trade_date_block_bootstrap | 11128 | BLOCKED | False | True | surrun_309239fd8ba12280cf4773a7 | UNDERPOWERED |
| sspec_f8c1786bccab51f017ec0e51 | trade_date_block_bootstrap | 11129 | BLOCKED | False | True | surrun_e8f5deaa59b7df7e3a7a29d8 | UNDERPOWERED |
| sspec_5807b332c4c741464c2dc06e | trade_date_block_bootstrap | 11130 | BLOCKED | False | True | surrun_ab17ecdeff040d34175d3bbf | UNDERPOWERED |
| sspec_5807b332c4c741464c2dc06e | trade_date_block_bootstrap | 11131 | BLOCKED | False | True | surrun_2e6678b6343e9f5c98b4f280 | UNDERPOWERED |
| sspec_5807b332c4c741464c2dc06e | trade_date_block_bootstrap | 11132 | BLOCKED | False | True | surrun_0734f655ae754486a0caf964 | UNDERPOWERED |
| sspec_02aa1be0dbafd34c64a6076c | trade_date_block_bootstrap | 11133 | BLOCKED | False | True | surrun_734ea1bd36a391c409f1578f | UNDERPOWERED |
| sspec_02aa1be0dbafd34c64a6076c | trade_date_block_bootstrap | 11134 | BLOCKED | False | True | surrun_89b46cb626604206b54b0130 | UNDERPOWERED |
| sspec_02aa1be0dbafd34c64a6076c | trade_date_block_bootstrap | 11135 | BLOCKED | False | True | surrun_cd192ab9ae8af2810af88e10 | UNDERPOWERED |
| sspec_29d1efb36981ab31ef6fbc58 | trade_date_block_bootstrap | 11136 | BLOCKED | False | True | surrun_f25b8f083302a68eba410f40 | UNDERPOWERED |
| sspec_29d1efb36981ab31ef6fbc58 | trade_date_block_bootstrap | 11137 | BLOCKED | False | True | surrun_07d41aade4b83e262d1755ac | UNDERPOWERED |
| sspec_29d1efb36981ab31ef6fbc58 | trade_date_block_bootstrap | 11138 | BLOCKED | False | True | surrun_c92234bcc38b038ccd3d8a1d | UNDERPOWERED |
| sspec_e5566b9e10f04ce8be8d2cb4 | trade_date_block_bootstrap | 11139 | BLOCKED | False | True | surrun_7af50d17c879bad4c24f11fe | UNDERPOWERED |
| sspec_e5566b9e10f04ce8be8d2cb4 | trade_date_block_bootstrap | 11140 | BLOCKED | False | True | surrun_c555ef4543bdfdcd8cf7aa49 | UNDERPOWERED |
| sspec_e5566b9e10f04ce8be8d2cb4 | trade_date_block_bootstrap | 11141 | BLOCKED | False | True | surrun_fd02164ba8e5f85e25c0392f | UNDERPOWERED |
| sspec_7595bde76e8919c10e6c3e55 | trade_date_block_bootstrap | 11142 | BLOCKED | False | True | surrun_79bfc945249f802c0fbd4255 | UNDERPOWERED |
| sspec_7595bde76e8919c10e6c3e55 | trade_date_block_bootstrap | 11143 | BLOCKED | False | True | surrun_ef3a552dc51ab3fa64dcc016 | UNDERPOWERED |
| sspec_7595bde76e8919c10e6c3e55 | trade_date_block_bootstrap | 11144 | BLOCKED | False | True | surrun_a464c4a4b1ce3b4feeca2a9d | UNDERPOWERED |
| sspec_5c0eb83a23aebfc9cf7e41d0 | trade_date_block_bootstrap | 11145 | BLOCKED | False | True | surrun_6fa60d703c3d0a38f4dc3f44 | UNDERPOWERED |
| sspec_5c0eb83a23aebfc9cf7e41d0 | trade_date_block_bootstrap | 11146 | BLOCKED | False | True | surrun_c6736134d91770182e99af1f | UNDERPOWERED |
| sspec_5c0eb83a23aebfc9cf7e41d0 | trade_date_block_bootstrap | 11147 | BLOCKED | False | True | surrun_1c052ecfa74e830a5130d17c | UNDERPOWERED |
| sspec_052cf9ee1b5ff7e9316677e6 | trade_date_block_bootstrap | 11148 | BLOCKED | False | True | surrun_76ccc7e0638d29c753af5093 | UNDERPOWERED |
| sspec_052cf9ee1b5ff7e9316677e6 | trade_date_block_bootstrap | 11149 | BLOCKED | False | True | surrun_b42fb50d87081f6fc127a845 | UNDERPOWERED |
| sspec_052cf9ee1b5ff7e9316677e6 | trade_date_block_bootstrap | 11150 | BLOCKED | False | True | surrun_5bdf151f442ede6bb3babdc7 | UNDERPOWERED |
| sspec_83c30348db61cd4766c3bff4 | trade_date_block_bootstrap | 11151 | BLOCKED | False | True | surrun_22202aabd7ce7073233d0510 | UNDERPOWERED |
| sspec_83c30348db61cd4766c3bff4 | trade_date_block_bootstrap | 11152 | BLOCKED | False | True | surrun_890a495e9b4ef24358165746 | UNDERPOWERED |
| sspec_83c30348db61cd4766c3bff4 | trade_date_block_bootstrap | 11153 | BLOCKED | False | True | surrun_7a35d5e9442249256e87cf1d | UNDERPOWERED |
| sspec_2ed84100bebce0f3bde43c4a | trade_date_block_bootstrap | 11154 | BLOCKED | False | True | surrun_dcd16a257ea091e9800437ce | UNDERPOWERED |
| sspec_2ed84100bebce0f3bde43c4a | trade_date_block_bootstrap | 11155 | BLOCKED | False | True | surrun_5656d04ef4c2b0421cf888c3 | UNDERPOWERED |
| sspec_2ed84100bebce0f3bde43c4a | trade_date_block_bootstrap | 11156 | BLOCKED | False | True | surrun_c0f9c9cfd66414f95c5e8fe8 | UNDERPOWERED |
| sspec_40b4f9aa123444157b924c10 | trade_date_block_bootstrap | 11157 | BLOCKED | False | True | surrun_b0e51df0eb18e4a7549a4f8d | UNDERPOWERED |
| sspec_40b4f9aa123444157b924c10 | trade_date_block_bootstrap | 11158 | BLOCKED | False | True | surrun_68362d194b1d205b51aeccec | UNDERPOWERED |
| sspec_40b4f9aa123444157b924c10 | trade_date_block_bootstrap | 11159 | BLOCKED | False | True | surrun_27a802b8f3759b70c3109b81 | UNDERPOWERED |
| sspec_164096c781a02562639d3dc6 | trade_date_block_bootstrap | 11160 | BLOCKED | False | True | surrun_7531d5b3a53c7295b1ccb156 | UNDERPOWERED |
| sspec_164096c781a02562639d3dc6 | trade_date_block_bootstrap | 11161 | BLOCKED | False | True | surrun_4e78d3876e6fb6f40b926754 | UNDERPOWERED |
| sspec_164096c781a02562639d3dc6 | trade_date_block_bootstrap | 11162 | BLOCKED | False | True | surrun_ecd64a4c6352c40829ef03fd | UNDERPOWERED |
| sspec_96dd5b855fd22a10b9a570cf | trade_date_block_bootstrap | 11163 | BLOCKED | False | True | surrun_8042cfda83ecd1144ff90eba | UNDERPOWERED |
| sspec_96dd5b855fd22a10b9a570cf | trade_date_block_bootstrap | 11164 | BLOCKED | False | True | surrun_3096f1abf15fba9aaff2be33 | UNDERPOWERED |
| sspec_96dd5b855fd22a10b9a570cf | trade_date_block_bootstrap | 11165 | BLOCKED | False | True | surrun_2c239ac559e7390a2d6a4444 | UNDERPOWERED |
| sspec_d1fb71f61e8abd8fd45dc747 | trade_date_block_bootstrap | 11166 | BLOCKED | False | True | surrun_b4116756076c3803f816fe8e | UNDERPOWERED |
| sspec_d1fb71f61e8abd8fd45dc747 | trade_date_block_bootstrap | 11167 | BLOCKED | False | True | surrun_f0e887cb755abd42e9fa10ca | UNDERPOWERED |
| sspec_d1fb71f61e8abd8fd45dc747 | trade_date_block_bootstrap | 11168 | BLOCKED | False | True | surrun_c92f42693052e5addb4c25c3 | UNDERPOWERED |
| sspec_c71283e94471ff7ca49035f5 | trade_date_block_bootstrap | 11169 | BLOCKED | False | True | surrun_85cdca99d0c289f972cb5e5b | UNDERPOWERED |
| sspec_c71283e94471ff7ca49035f5 | trade_date_block_bootstrap | 11170 | BLOCKED | False | True | surrun_b2d47f13dab6764ecd6160e1 | UNDERPOWERED |
| sspec_c71283e94471ff7ca49035f5 | trade_date_block_bootstrap | 11171 | BLOCKED | False | True | surrun_1b2d0e865aed1e54e975ccd7 | UNDERPOWERED |
| sspec_ee70d232a0194368ca134607 | trade_date_block_bootstrap | 11172 | BLOCKED | False | True | surrun_d568952a8cc6aa604f5478cf | UNDERPOWERED |
| sspec_ee70d232a0194368ca134607 | trade_date_block_bootstrap | 11173 | BLOCKED | False | True | surrun_a745676781acfa3cbc04ca36 | UNDERPOWERED |
| sspec_ee70d232a0194368ca134607 | trade_date_block_bootstrap | 11174 | BLOCKED | False | True | surrun_dfc8257aceb25f981f0a3b34 | UNDERPOWERED |
| sspec_cf7b281007393c141d0c8de2 | trade_date_block_bootstrap | 11175 | BLOCKED | False | True | surrun_ff91b1dda0234990795cfdd6 | UNDERPOWERED |
| sspec_cf7b281007393c141d0c8de2 | trade_date_block_bootstrap | 11176 | BLOCKED | False | True | surrun_b929ba54e63cc5913860a12a | UNDERPOWERED |
| sspec_cf7b281007393c141d0c8de2 | trade_date_block_bootstrap | 11177 | BLOCKED | False | True | surrun_d0d664c034dc109ef097652f | UNDERPOWERED |
| sspec_74e21ea3e1cf81fa757e6ceb | trade_date_block_bootstrap | 11178 | BLOCKED | False | True | surrun_164b72411cb443a8588128bf | UNDERPOWERED |
| sspec_74e21ea3e1cf81fa757e6ceb | trade_date_block_bootstrap | 11179 | BLOCKED | False | True | surrun_a27f75a28afe17484f48271f | UNDERPOWERED |
| sspec_74e21ea3e1cf81fa757e6ceb | trade_date_block_bootstrap | 11180 | BLOCKED | False | True | surrun_a6b3ec31fb6e7db8cde7b841 | UNDERPOWERED |
| sspec_5ba3e409a2e1532a310a7030 | trade_date_block_bootstrap | 11181 | BLOCKED | False | True | surrun_58f0ee4172e4398a548bc77e | UNDERPOWERED |
| sspec_5ba3e409a2e1532a310a7030 | trade_date_block_bootstrap | 11182 | BLOCKED | False | True | surrun_00e23f01f14e8dea6de03954 | UNDERPOWERED |
| sspec_5ba3e409a2e1532a310a7030 | trade_date_block_bootstrap | 11183 | BLOCKED | False | True | surrun_352778f0f7cda4536a89d517 | UNDERPOWERED |
| sspec_fc8deb1fca3b12e8ba85cb25 | trade_date_block_bootstrap | 11184 | BLOCKED | False | True | surrun_25b4f2de5adcdc7a236253e6 | UNDERPOWERED |
| sspec_fc8deb1fca3b12e8ba85cb25 | trade_date_block_bootstrap | 11185 | BLOCKED | False | True | surrun_ab5ce698742168d4f86b55d5 | UNDERPOWERED |
| sspec_fc8deb1fca3b12e8ba85cb25 | trade_date_block_bootstrap | 11186 | BLOCKED | False | True | surrun_f82be4377a671d0ce610ea1f | UNDERPOWERED |
| sspec_d28894b236877b2f4a7e506d | trade_date_block_bootstrap | 11187 | BLOCKED | False | True | surrun_08ac0263c9e59afbfe990ede | UNDERPOWERED |
| sspec_d28894b236877b2f4a7e506d | trade_date_block_bootstrap | 11188 | BLOCKED | False | True | surrun_d1fe50815b1cef3c45a69cd6 | UNDERPOWERED |
| sspec_d28894b236877b2f4a7e506d | trade_date_block_bootstrap | 11189 | BLOCKED | False | True | surrun_81a26a5ecb3360797a7b8b14 | UNDERPOWERED |
| sspec_4dc02697c7337f70a86414c8 | trade_date_block_bootstrap | 11190 | BLOCKED | False | True | surrun_00b0bb7653065d3400547e28 | UNDERPOWERED |
| sspec_4dc02697c7337f70a86414c8 | trade_date_block_bootstrap | 11191 | BLOCKED | False | True | surrun_2ac603dcee579d7897ff8353 | UNDERPOWERED |
| sspec_4dc02697c7337f70a86414c8 | trade_date_block_bootstrap | 11192 | BLOCKED | False | True | surrun_73ddf153f518de5d9b1580c9 | UNDERPOWERED |
| sspec_7e89938f0cfbe29b4b97e992 | trade_date_block_bootstrap | 11193 | BLOCKED | False | True | surrun_ac13e8e338cc361486e42965 | UNDERPOWERED |
| sspec_7e89938f0cfbe29b4b97e992 | trade_date_block_bootstrap | 11194 | BLOCKED | False | True | surrun_44ef9bc66980dae32d3bfc81 | UNDERPOWERED |
| sspec_7e89938f0cfbe29b4b97e992 | trade_date_block_bootstrap | 11195 | BLOCKED | False | True | surrun_30fdd49fd8cc85164cd6c2df | UNDERPOWERED |
| sspec_ef66f8041030a4b41c45a19b | trade_date_block_bootstrap | 11196 | BLOCKED | False | True | surrun_f4c0e76454b2735d531298f7 | UNDERPOWERED |
| sspec_ef66f8041030a4b41c45a19b | trade_date_block_bootstrap | 11197 | BLOCKED | False | True | surrun_6105ed891240398b0af14039 | UNDERPOWERED |
| sspec_ef66f8041030a4b41c45a19b | trade_date_block_bootstrap | 11198 | BLOCKED | False | True | surrun_670f357da9395c7f153042d8 | UNDERPOWERED |
| sspec_067e488423dfec12353e07dd | trade_date_block_bootstrap | 11199 | BLOCKED | False | True | surrun_cc23d265643f83d84d9a2679 | UNDERPOWERED |
| sspec_067e488423dfec12353e07dd | trade_date_block_bootstrap | 11200 | BLOCKED | False | True | surrun_212b3dc7788df404f98f7651 | UNDERPOWERED |
| sspec_067e488423dfec12353e07dd | trade_date_block_bootstrap | 11201 | BLOCKED | False | True | surrun_2a6ae2e228545514dc3bd2c6 | UNDERPOWERED |
| sspec_1b09ce1e013ce197b6e4e002 | trade_date_block_bootstrap | 11202 | BLOCKED | False | True | surrun_3f9cdec29282621d1bee13dc | UNDERPOWERED |
| sspec_1b09ce1e013ce197b6e4e002 | trade_date_block_bootstrap | 11203 | BLOCKED | False | True | surrun_a25cd28df1225c71bf06b2aa | UNDERPOWERED |
| sspec_1b09ce1e013ce197b6e4e002 | trade_date_block_bootstrap | 11204 | BLOCKED | False | True | surrun_db01580a05dd489db2ce6186 | UNDERPOWERED |
| sspec_4ae7d2e32d83c6011139b625 | trade_date_block_bootstrap | 11205 | BLOCKED | False | True | surrun_fcc0015dfca4a4ab792ed8fe | UNDERPOWERED |
| sspec_4ae7d2e32d83c6011139b625 | trade_date_block_bootstrap | 11206 | BLOCKED | False | True | surrun_97759202da9d514135fbb1e6 | UNDERPOWERED |
| sspec_4ae7d2e32d83c6011139b625 | trade_date_block_bootstrap | 11207 | BLOCKED | False | True | surrun_c8deae0f92acde7d011e99e3 | UNDERPOWERED |
| sspec_21c8a263cc97beb02ac32969 | trade_date_block_bootstrap | 11208 | BLOCKED | False | True | surrun_07438002ac78ba1316adb7c5 | UNDERPOWERED |
| sspec_21c8a263cc97beb02ac32969 | trade_date_block_bootstrap | 11209 | BLOCKED | False | True | surrun_a96478495efe1f198815ba4e | UNDERPOWERED |
| sspec_21c8a263cc97beb02ac32969 | trade_date_block_bootstrap | 11210 | BLOCKED | False | True | surrun_f071819747c1c964f1625aa7 | UNDERPOWERED |
| sspec_aa2b07899713e16242243041 | trade_date_block_bootstrap | 11211 | BLOCKED | False | True | surrun_0b97940b8ed214bc8d3db8d0 | UNDERPOWERED |
| sspec_aa2b07899713e16242243041 | trade_date_block_bootstrap | 11212 | BLOCKED | False | True | surrun_0513976f20d0f02d1e04e706 | UNDERPOWERED |
| sspec_aa2b07899713e16242243041 | trade_date_block_bootstrap | 11213 | BLOCKED | False | True | surrun_54cb8eef61c06bb66ba458be | UNDERPOWERED |
| sspec_ad97188a76423bbc2679ba08 | trade_date_block_bootstrap | 11214 | BLOCKED | False | True | surrun_965706ba2c83a18ecab18411 | UNDERPOWERED |
| sspec_ad97188a76423bbc2679ba08 | trade_date_block_bootstrap | 11215 | BLOCKED | False | True | surrun_9d5185d1a14bfb11546a7966 | UNDERPOWERED |
| sspec_ad97188a76423bbc2679ba08 | trade_date_block_bootstrap | 11216 | BLOCKED | False | True | surrun_328985d84464e4a0e17577ed | UNDERPOWERED |
| sspec_d3bab2c1a6cda92abeb5c2d8 | trade_date_block_bootstrap | 11217 | BLOCKED | False | True | surrun_8b0e437f58259da4e1896c9c | UNDERPOWERED |
| sspec_d3bab2c1a6cda92abeb5c2d8 | trade_date_block_bootstrap | 11218 | BLOCKED | False | True | surrun_31592f8a2f98de58cbbbdc1f | UNDERPOWERED |
| sspec_d3bab2c1a6cda92abeb5c2d8 | trade_date_block_bootstrap | 11219 | BLOCKED | False | True | surrun_9c411312b0cfa85c9c7332f1 | UNDERPOWERED |
| sspec_f9822cbdf44fe9740f30534b | trade_date_block_bootstrap | 11220 | BLOCKED | False | True | surrun_20f15e007f6d2d97a8b1f18f | UNDERPOWERED |
| sspec_f9822cbdf44fe9740f30534b | trade_date_block_bootstrap | 11221 | BLOCKED | False | True | surrun_77d1e2a5c01d1784f1bbee13 | UNDERPOWERED |
| sspec_f9822cbdf44fe9740f30534b | trade_date_block_bootstrap | 11222 | BLOCKED | False | True | surrun_32a06cd20be22bd8c547d84c | UNDERPOWERED |
| sspec_7842b503d31dcce000f60970 | trade_date_block_bootstrap | 11223 | BLOCKED | False | True | surrun_f73511f381a9e4afbb40e55b | UNDERPOWERED |
| sspec_7842b503d31dcce000f60970 | trade_date_block_bootstrap | 11224 | BLOCKED | False | True | surrun_bc77d94235ca4e6e44560c52 | UNDERPOWERED |
| sspec_7842b503d31dcce000f60970 | trade_date_block_bootstrap | 11225 | BLOCKED | False | True | surrun_6b57e287399ca6013ba20dde | UNDERPOWERED |
| sspec_5c9ea306c49bd4a1ec8a9089 | trade_date_block_bootstrap | 11226 | BLOCKED | False | True | surrun_895d6e7ce1f01e008a780df8 | UNDERPOWERED |
| sspec_5c9ea306c49bd4a1ec8a9089 | trade_date_block_bootstrap | 11227 | BLOCKED | False | True | surrun_bdf83bf246522e9219586ed6 | UNDERPOWERED |
| sspec_5c9ea306c49bd4a1ec8a9089 | trade_date_block_bootstrap | 11228 | BLOCKED | False | True | surrun_697cbca7c5e8b81005ddfcc6 | UNDERPOWERED |
| sspec_4d8d7758f58baf634eb6021e | trade_date_block_bootstrap | 11229 | BLOCKED | False | True | surrun_a09b5fad78a50cfe06650676 | UNDERPOWERED |
| sspec_4d8d7758f58baf634eb6021e | trade_date_block_bootstrap | 11230 | BLOCKED | False | True | surrun_c9cfac9b7eedc9b46ed553bf | UNDERPOWERED |
| sspec_4d8d7758f58baf634eb6021e | trade_date_block_bootstrap | 11231 | BLOCKED | False | True | surrun_52f722b2b399eb97e91e35ba | UNDERPOWERED |
| sspec_0b40edf4516ecf1821419b13 | trade_date_block_bootstrap | 11232 | BLOCKED | False | True | surrun_7f0b4db949436ceec6a5b32b | UNDERPOWERED |
| sspec_0b40edf4516ecf1821419b13 | trade_date_block_bootstrap | 11233 | BLOCKED | False | True | surrun_244bf97a78e7933351e5bd1d | UNDERPOWERED |
| sspec_0b40edf4516ecf1821419b13 | trade_date_block_bootstrap | 11234 | BLOCKED | False | True | surrun_04526f787536848cad3a1818 | UNDERPOWERED |
| sspec_826617ba3ab69d8dca62b979 | trade_date_block_bootstrap | 11235 | BLOCKED | False | True | surrun_397e74df0682f55e9681ee14 | UNDERPOWERED |
| sspec_826617ba3ab69d8dca62b979 | trade_date_block_bootstrap | 11236 | BLOCKED | False | True | surrun_865f29dfd79c1dce7f4f7cd1 | UNDERPOWERED |
| sspec_826617ba3ab69d8dca62b979 | trade_date_block_bootstrap | 11237 | BLOCKED | False | True | surrun_52f5681dd788ee677b414f83 | UNDERPOWERED |
| sspec_cbe5c88a0a16fcf8a76b84d6 | trade_date_block_bootstrap | 11238 | BLOCKED | False | True | surrun_efcf9ca6ad79b66395a1a2dd | UNDERPOWERED |
| sspec_cbe5c88a0a16fcf8a76b84d6 | trade_date_block_bootstrap | 11239 | BLOCKED | False | True | surrun_2e25bce46f69f1aa9f85a4eb | UNDERPOWERED |
| sspec_cbe5c88a0a16fcf8a76b84d6 | trade_date_block_bootstrap | 11240 | BLOCKED | False | True | surrun_1f8ab1e2cb97847e52544e25 | UNDERPOWERED |
| sspec_319e858af7072a237e8dc7bc | trade_date_block_bootstrap | 11241 | BLOCKED | False | True | surrun_cdd515002956f153e42d25ca | UNDERPOWERED |
| sspec_319e858af7072a237e8dc7bc | trade_date_block_bootstrap | 11242 | BLOCKED | False | True | surrun_bb3383e0ec01b98ef97042d8 | UNDERPOWERED |
| sspec_319e858af7072a237e8dc7bc | trade_date_block_bootstrap | 11243 | BLOCKED | False | True | surrun_4b4b326231c27dc853c0a2c6 | UNDERPOWERED |
| sspec_846c085c370f172adecc1497 | trade_date_block_bootstrap | 11244 | BLOCKED | False | True | surrun_7f682fd05ac23ee7aef01c78 | UNDERPOWERED |
| sspec_846c085c370f172adecc1497 | trade_date_block_bootstrap | 11245 | BLOCKED | False | True | surrun_2af2e6c8fca88dd852fbb4c0 | UNDERPOWERED |
| sspec_846c085c370f172adecc1497 | trade_date_block_bootstrap | 11246 | BLOCKED | False | True | surrun_adc3f027f4973ed9ed3f8245 | UNDERPOWERED |
| sspec_fe5fba941c4a57a9043a1e53 | trade_date_block_bootstrap | 11247 | BLOCKED | False | True | surrun_76e2d1f6c1a73892744d4b03 | UNDERPOWERED |
| sspec_fe5fba941c4a57a9043a1e53 | trade_date_block_bootstrap | 11248 | BLOCKED | False | True | surrun_752a0ec31c8bcd7fd1f6bec1 | UNDERPOWERED |
| sspec_fe5fba941c4a57a9043a1e53 | trade_date_block_bootstrap | 11249 | BLOCKED | False | True | surrun_9a255ac3671db1f76f85f86c | UNDERPOWERED |
| sspec_13ea42ec55291487bf5f6eff | trade_date_block_bootstrap | 11250 | BLOCKED | False | True | surrun_8251e3c2998b19d55abc3954 | UNDERPOWERED |
| sspec_13ea42ec55291487bf5f6eff | trade_date_block_bootstrap | 11251 | BLOCKED | False | True | surrun_88b9541db752729ece2ac2c2 | UNDERPOWERED |
| sspec_13ea42ec55291487bf5f6eff | trade_date_block_bootstrap | 11252 | BLOCKED | False | True | surrun_6348e6d93c94457ce49e43f3 | UNDERPOWERED |
| sspec_3b5c823842b62761e9089f4b | trade_date_block_bootstrap | 11253 | BLOCKED | False | True | surrun_a439d3b0b2949cc1f3cab5cd | UNDERPOWERED |
| sspec_3b5c823842b62761e9089f4b | trade_date_block_bootstrap | 11254 | BLOCKED | False | True | surrun_91b00bee719bd88b2688f6b3 | UNDERPOWERED |
| sspec_3b5c823842b62761e9089f4b | trade_date_block_bootstrap | 11255 | BLOCKED | False | True | surrun_2c2b11ebb9b41b25191fb435 | UNDERPOWERED |
| sspec_b452cf5a31e24967eead6013 | trade_date_block_bootstrap | 11256 | BLOCKED | False | True | surrun_7fbde9ba583d8183b473293f | UNDERPOWERED |
| sspec_b452cf5a31e24967eead6013 | trade_date_block_bootstrap | 11257 | BLOCKED | False | True | surrun_1de6d7de1d304530b44952ad | UNDERPOWERED |
| sspec_b452cf5a31e24967eead6013 | trade_date_block_bootstrap | 11258 | BLOCKED | False | True | surrun_01c5bbb9415846c2968b1efb | UNDERPOWERED |
| sspec_f7bb920147cf52502e3c97a1 | trade_date_block_bootstrap | 11259 | BLOCKED | False | True | surrun_472ac4f0e7decb24aff62bf8 | UNDERPOWERED |
| sspec_f7bb920147cf52502e3c97a1 | trade_date_block_bootstrap | 11260 | BLOCKED | False | True | surrun_0aaf67159d0f2653d85a391a | UNDERPOWERED |
| sspec_f7bb920147cf52502e3c97a1 | trade_date_block_bootstrap | 11261 | BLOCKED | False | True | surrun_06a7948915edd51381c5eff7 | UNDERPOWERED |
| sspec_24c31450a01e00016f123a36 | trade_date_block_bootstrap | 11262 | BLOCKED | False | True | surrun_e8d78c7992042b14a092d6c4 | UNDERPOWERED |
| sspec_24c31450a01e00016f123a36 | trade_date_block_bootstrap | 11263 | BLOCKED | False | True | surrun_eec41b003029c54ec486630d | UNDERPOWERED |
| sspec_24c31450a01e00016f123a36 | trade_date_block_bootstrap | 11264 | BLOCKED | False | True | surrun_e750b60a0acfe04c2ff51a8d | UNDERPOWERED |
| sspec_9824aede42ef1384d9d2c702 | trade_date_block_bootstrap | 11265 | BLOCKED | False | True | surrun_795c065162a4459308a8dead | UNDERPOWERED |
| sspec_9824aede42ef1384d9d2c702 | trade_date_block_bootstrap | 11266 | BLOCKED | False | True | surrun_a29dd62b4f56b1c7a1f1420b | UNDERPOWERED |
| sspec_9824aede42ef1384d9d2c702 | trade_date_block_bootstrap | 11267 | BLOCKED | False | True | surrun_7e61162c4c3fa4ff6bc8a81e | UNDERPOWERED |
| sspec_f7172b69599ff0eecfa1c4cd | trade_date_block_bootstrap | 11268 | BLOCKED | False | True | surrun_cfbb3bbfd822923e121865cc | UNDERPOWERED |
| sspec_f7172b69599ff0eecfa1c4cd | trade_date_block_bootstrap | 11269 | BLOCKED | False | True | surrun_9fecac9764a5d800739d012d | UNDERPOWERED |
| sspec_f7172b69599ff0eecfa1c4cd | trade_date_block_bootstrap | 11270 | BLOCKED | False | True | surrun_79518916a330448183f199ce | UNDERPOWERED |
| sspec_437ae10c3a8a1a36d133c1cc | trade_date_block_bootstrap | 11271 | BLOCKED | False | True | surrun_120a900b178d9f7a029043c0 | UNDERPOWERED |
| sspec_437ae10c3a8a1a36d133c1cc | trade_date_block_bootstrap | 11272 | BLOCKED | False | True | surrun_cbc3fa39a1066533b811d8f3 | UNDERPOWERED |
| sspec_437ae10c3a8a1a36d133c1cc | trade_date_block_bootstrap | 11273 | BLOCKED | False | True | surrun_56d9110abddf01475ba76c3a | UNDERPOWERED |
| sspec_cbd8ab82ff5228e6140767f6 | trade_date_block_bootstrap | 11274 | BLOCKED | False | True | surrun_3359624576f3a834d5614476 | UNDERPOWERED |
| sspec_cbd8ab82ff5228e6140767f6 | trade_date_block_bootstrap | 11275 | BLOCKED | False | True | surrun_5461e651c29c4e5acdd01047 | UNDERPOWERED |
| sspec_cbd8ab82ff5228e6140767f6 | trade_date_block_bootstrap | 11276 | BLOCKED | False | True | surrun_5c554fd1f155dd56697fef55 | UNDERPOWERED |
| sspec_7ccfdc13442fa25b5a64620f | trade_date_block_bootstrap | 11277 | BLOCKED | False | True | surrun_a280dc14878ee007770e0b81 | UNDERPOWERED |
| sspec_7ccfdc13442fa25b5a64620f | trade_date_block_bootstrap | 11278 | BLOCKED | False | True | surrun_469ca4cc214441408b22904d | UNDERPOWERED |
| sspec_7ccfdc13442fa25b5a64620f | trade_date_block_bootstrap | 11279 | BLOCKED | False | True | surrun_1be33add3c32c9f455aae33b | UNDERPOWERED |
| sspec_5f30e440e1f00e2fc4fad420 | trade_date_block_bootstrap | 11280 | BLOCKED | False | True | surrun_963b9d22b3d174ec89e605a2 | UNDERPOWERED |
| sspec_5f30e440e1f00e2fc4fad420 | trade_date_block_bootstrap | 11281 | BLOCKED | False | True | surrun_7227f74f5acc5e899e82f0ba | UNDERPOWERED |
| sspec_5f30e440e1f00e2fc4fad420 | trade_date_block_bootstrap | 11282 | BLOCKED | False | True | surrun_089d52da01ddd22e0b8ee194 | UNDERPOWERED |
| sspec_5fb73ff1f5c96181be68e9c7 | trade_date_block_bootstrap | 11283 | BLOCKED | False | True | surrun_7e8c35ba119f3758751cdd86 | UNDERPOWERED |
| sspec_5fb73ff1f5c96181be68e9c7 | trade_date_block_bootstrap | 11284 | BLOCKED | False | True | surrun_75e176002eff1034429422c5 | UNDERPOWERED |
| sspec_5fb73ff1f5c96181be68e9c7 | trade_date_block_bootstrap | 11285 | BLOCKED | False | True | surrun_38db7ec05bf5dc298681cfba | UNDERPOWERED |
| sspec_b315a7883c40b3d90df7ffe2 | trade_date_block_bootstrap | 11286 | BLOCKED | False | True | surrun_765963103313f1687409b97a | UNDERPOWERED |
| sspec_b315a7883c40b3d90df7ffe2 | trade_date_block_bootstrap | 11287 | BLOCKED | False | True | surrun_7963f531813084d423ec173c | UNDERPOWERED |
| sspec_b315a7883c40b3d90df7ffe2 | trade_date_block_bootstrap | 11288 | BLOCKED | False | True | surrun_180bd73a42e829cc909b6c6c | UNDERPOWERED |
| sspec_f178b5fc336630aabb18cba6 | trade_date_block_bootstrap | 11289 | BLOCKED | False | True | surrun_aed792c4bc5be312657bf0bf | UNDERPOWERED |
| sspec_f178b5fc336630aabb18cba6 | trade_date_block_bootstrap | 11290 | BLOCKED | False | True | surrun_b1d0633cd360a970bb770c55 | UNDERPOWERED |
| sspec_f178b5fc336630aabb18cba6 | trade_date_block_bootstrap | 11291 | BLOCKED | False | True | surrun_5ff19aaa717333e6c9e0824c | UNDERPOWERED |
| sspec_7a064e20e01d96552cd3b575 | trade_date_block_bootstrap | 11292 | BLOCKED | False | True | surrun_86ad27ea0d250b16d7a21bca | UNDERPOWERED |
| sspec_7a064e20e01d96552cd3b575 | trade_date_block_bootstrap | 11293 | BLOCKED | False | True | surrun_0659fb04f8ec461d71321874 | UNDERPOWERED |
| sspec_7a064e20e01d96552cd3b575 | trade_date_block_bootstrap | 11294 | BLOCKED | False | True | surrun_aa966b6c9a47d2d785339e49 | UNDERPOWERED |
| sspec_e04b733f5a9c767d38996311 | trade_date_block_bootstrap | 11295 | BLOCKED | False | True | surrun_1f8ac0d36cb7723f0ebbdd06 | UNDERPOWERED |
| sspec_e04b733f5a9c767d38996311 | trade_date_block_bootstrap | 11296 | BLOCKED | False | True | surrun_c6c149e7686c2d6459e606ea | UNDERPOWERED |
| sspec_e04b733f5a9c767d38996311 | trade_date_block_bootstrap | 11297 | BLOCKED | False | True | surrun_68cdb60fb1994dc0c31650d5 | UNDERPOWERED |
| sspec_5c7adec822a3855808bf44ff | trade_date_block_bootstrap | 11298 | BLOCKED | False | True | surrun_d2556a088bb6165cf66d7a95 | UNDERPOWERED |
| sspec_5c7adec822a3855808bf44ff | trade_date_block_bootstrap | 11299 | BLOCKED | False | True | surrun_434567e2b3144ea08e663c4d | UNDERPOWERED |
| sspec_5c7adec822a3855808bf44ff | trade_date_block_bootstrap | 11300 | BLOCKED | False | True | surrun_9ba76e49721f236a115b514c | UNDERPOWERED |
| sspec_4549cf48a90f373099de3990 | trade_date_block_bootstrap | 11301 | BLOCKED | False | True | surrun_d78a137e0a7869b11357e6c5 | UNDERPOWERED |
| sspec_4549cf48a90f373099de3990 | trade_date_block_bootstrap | 11302 | BLOCKED | False | True | surrun_e8fa4c0a02319d5d45871658 | UNDERPOWERED |
| sspec_4549cf48a90f373099de3990 | trade_date_block_bootstrap | 11303 | BLOCKED | False | True | surrun_4ee3745aefb0d999a50c6afb | UNDERPOWERED |
| sspec_ebc5f04290686a0b7d5fb1ea | trade_date_block_bootstrap | 11304 | BLOCKED | False | True | surrun_c817cf71b97b470a889fc614 | UNDERPOWERED |
| sspec_ebc5f04290686a0b7d5fb1ea | trade_date_block_bootstrap | 11305 | BLOCKED | False | True | surrun_3afb1b36e78489f4d26f521d | UNDERPOWERED |
| sspec_ebc5f04290686a0b7d5fb1ea | trade_date_block_bootstrap | 11306 | BLOCKED | False | True | surrun_be7ffc515ae841f26971db20 | UNDERPOWERED |
| sspec_df8a5e8e794403861efa45ad | trade_date_block_bootstrap | 11307 | BLOCKED | False | True | surrun_ebc3ac2cdd2c808140de94a1 | UNDERPOWERED |
| sspec_df8a5e8e794403861efa45ad | trade_date_block_bootstrap | 11308 | BLOCKED | False | True | surrun_1b762cca2cf50df7c86538f5 | UNDERPOWERED |
| sspec_df8a5e8e794403861efa45ad | trade_date_block_bootstrap | 11309 | BLOCKED | False | True | surrun_2f6ca4edfa94e8d742bb1378 | UNDERPOWERED |
| sspec_c4ff2b42e9bdc1a8999ed8ed | trade_date_block_bootstrap | 11310 | BLOCKED | False | True | surrun_706195f53d3dfe9925a4201b | UNDERPOWERED |
| sspec_c4ff2b42e9bdc1a8999ed8ed | trade_date_block_bootstrap | 11311 | BLOCKED | False | True | surrun_800652f2e5da12a8ee12e30d | UNDERPOWERED |
| sspec_c4ff2b42e9bdc1a8999ed8ed | trade_date_block_bootstrap | 11312 | BLOCKED | False | True | surrun_b6a6814cef3c6789619464cc | UNDERPOWERED |
| sspec_3bea96d053d0700e4a775133 | trade_date_block_bootstrap | 11313 | BLOCKED | False | True | surrun_e6e2579bb41c082774777136 | UNDERPOWERED |
| sspec_3bea96d053d0700e4a775133 | trade_date_block_bootstrap | 11314 | BLOCKED | False | True | surrun_890c0097a30e9db9df8e417e | UNDERPOWERED |
| sspec_3bea96d053d0700e4a775133 | trade_date_block_bootstrap | 11315 | BLOCKED | False | True | surrun_ec9a7d4d414779852b42400b | UNDERPOWERED |
| sspec_f54131bec342de90e6dd27ea | trade_date_block_bootstrap | 11316 | BLOCKED | False | True | surrun_bdc65c06c3068063dce20237 | UNDERPOWERED |
| sspec_f54131bec342de90e6dd27ea | trade_date_block_bootstrap | 11317 | BLOCKED | False | True | surrun_5064d56475b1ca53d335a714 | UNDERPOWERED |
| sspec_f54131bec342de90e6dd27ea | trade_date_block_bootstrap | 11318 | BLOCKED | False | True | surrun_a8ff89ebe02f31c70981f7e9 | UNDERPOWERED |
| sspec_33dad16e1943a1636f17ac3f | trade_date_block_bootstrap | 11319 | BLOCKED | False | True | surrun_c56f56a78b483066083de23a | UNDERPOWERED |
| sspec_33dad16e1943a1636f17ac3f | trade_date_block_bootstrap | 11320 | BLOCKED | False | True | surrun_3e1965bbcdf5fb477ab1a2fd | UNDERPOWERED |
| sspec_33dad16e1943a1636f17ac3f | trade_date_block_bootstrap | 11321 | BLOCKED | False | True | surrun_4ef0ecf8a7154c77ee3d1562 | UNDERPOWERED |
| sspec_fa3df10158e87c00b0321202 | trade_date_block_bootstrap | 11322 | BLOCKED | False | True | surrun_7b23608767e4d4b28746ef25 | UNDERPOWERED |
| sspec_fa3df10158e87c00b0321202 | trade_date_block_bootstrap | 11323 | BLOCKED | False | True | surrun_5576fc337d857f7d0069a3d1 | UNDERPOWERED |
| sspec_fa3df10158e87c00b0321202 | trade_date_block_bootstrap | 11324 | BLOCKED | False | True | surrun_2ad5443f8ecacef4710fda02 | UNDERPOWERED |
| sspec_6013249328b6960d331e506a | trade_date_block_bootstrap | 11325 | BLOCKED | False | True | surrun_a7722ceab6a37faa83783f84 | UNDERPOWERED |
| sspec_6013249328b6960d331e506a | trade_date_block_bootstrap | 11326 | BLOCKED | False | True | surrun_e343eca36760c69dd7d51292 | UNDERPOWERED |
| sspec_6013249328b6960d331e506a | trade_date_block_bootstrap | 11327 | BLOCKED | False | True | surrun_23701768ee90db6c92fd47ff | UNDERPOWERED |
| sspec_22c344106162dcc8aadd8f69 | trade_date_block_bootstrap | 11328 | BLOCKED | False | True | surrun_f1f6dc2aab235559e36f7cba | UNDERPOWERED |
| sspec_22c344106162dcc8aadd8f69 | trade_date_block_bootstrap | 11329 | BLOCKED | False | True | surrun_5f09c6d8fc580fb8c29f1968 | UNDERPOWERED |
| sspec_22c344106162dcc8aadd8f69 | trade_date_block_bootstrap | 11330 | BLOCKED | False | True | surrun_3d95de1af4393a3cea30e8b9 | UNDERPOWERED |
| sspec_95715cc5345c37578406e84f | trade_date_block_bootstrap | 11331 | BLOCKED | False | True | surrun_e732a82fc5a15446eb5dad7a | UNDERPOWERED |
| sspec_95715cc5345c37578406e84f | trade_date_block_bootstrap | 11332 | BLOCKED | False | True | surrun_7e1989bcecfa03a7877c628a | UNDERPOWERED |
| sspec_95715cc5345c37578406e84f | trade_date_block_bootstrap | 11333 | BLOCKED | False | True | surrun_a342142829f6b5b8c0f7cb9e | UNDERPOWERED |
| sspec_3a6f48077629523800703448 | trade_date_block_bootstrap | 11334 | BLOCKED | False | True | surrun_a06f6b561cea71b03a24cd21 | UNDERPOWERED |
| sspec_3a6f48077629523800703448 | trade_date_block_bootstrap | 11335 | BLOCKED | False | True | surrun_00b01a71464103d877ca5aa6 | UNDERPOWERED |
| sspec_3a6f48077629523800703448 | trade_date_block_bootstrap | 11336 | BLOCKED | False | True | surrun_482d56c9a9fb451eb91d168a | UNDERPOWERED |
| sspec_6ef0f5713fcdf2e014fbc972 | trade_date_block_bootstrap | 11337 | BLOCKED | False | True | surrun_96e7a5ed911bffa6229d09ef | UNDERPOWERED |
| sspec_6ef0f5713fcdf2e014fbc972 | trade_date_block_bootstrap | 11338 | BLOCKED | False | True | surrun_07d2282770fd8c95b83f52af | UNDERPOWERED |
| sspec_6ef0f5713fcdf2e014fbc972 | trade_date_block_bootstrap | 11339 | BLOCKED | False | True | surrun_6e427791eb13ec909ae825a8 | UNDERPOWERED |
| sspec_9c85e9c30267a55df954b441 | trade_date_block_bootstrap | 11340 | BLOCKED | False | True | surrun_ae66d98ef28ebbd99b0e6f25 | UNDERPOWERED |
| sspec_9c85e9c30267a55df954b441 | trade_date_block_bootstrap | 11341 | BLOCKED | False | True | surrun_501c9ddc08ca723d236060b5 | UNDERPOWERED |
| sspec_9c85e9c30267a55df954b441 | trade_date_block_bootstrap | 11342 | BLOCKED | False | True | surrun_b29947d515bb23a23039bcaa | UNDERPOWERED |
| sspec_4667304d4ec8ebbd7a44da28 | trade_date_block_bootstrap | 11343 | BLOCKED | False | True | surrun_a8acbdbd6a7743b0783cd945 | UNDERPOWERED |
| sspec_4667304d4ec8ebbd7a44da28 | trade_date_block_bootstrap | 11344 | BLOCKED | False | True | surrun_f9c6280891688ff46900aabf | UNDERPOWERED |
| sspec_4667304d4ec8ebbd7a44da28 | trade_date_block_bootstrap | 11345 | BLOCKED | False | True | surrun_37f4ded39b2f5ba028eacffe | UNDERPOWERED |
| sspec_9dba492eb43ed4a52cba1e46 | trade_date_block_bootstrap | 11346 | BLOCKED | False | True | surrun_54f0638a22d747eb6dcfee09 | UNDERPOWERED |
| sspec_9dba492eb43ed4a52cba1e46 | trade_date_block_bootstrap | 11347 | BLOCKED | False | True | surrun_6f8d892d9272a335e0022f3e | UNDERPOWERED |
| sspec_9dba492eb43ed4a52cba1e46 | trade_date_block_bootstrap | 11348 | BLOCKED | False | True | surrun_4d3e2845b5348ef232159a1c | UNDERPOWERED |
| sspec_2ed4b14723030813e3983022 | trade_date_block_bootstrap | 11349 | BLOCKED | False | True | surrun_58ac85df777152249c0f4188 | UNDERPOWERED |
| sspec_2ed4b14723030813e3983022 | trade_date_block_bootstrap | 11350 | BLOCKED | False | True | surrun_c80d876be63fe5bf5e873e8d | UNDERPOWERED |
| sspec_2ed4b14723030813e3983022 | trade_date_block_bootstrap | 11351 | BLOCKED | False | True | surrun_4aac7e94a4e909d1579c1682 | UNDERPOWERED |
| sspec_ded43c2c99f2a2087c341083 | trade_date_block_bootstrap | 11352 | BLOCKED | False | True | surrun_0bf3277603c1bb1673feff70 | UNDERPOWERED |
| sspec_ded43c2c99f2a2087c341083 | trade_date_block_bootstrap | 11353 | BLOCKED | False | True | surrun_195bcb75c4cb65c66af0750a | UNDERPOWERED |
| sspec_ded43c2c99f2a2087c341083 | trade_date_block_bootstrap | 11354 | BLOCKED | False | True | surrun_a43e955f7023511b97a1eee3 | UNDERPOWERED |
| sspec_138892cda61ac9eea9160d8f | trade_date_block_bootstrap | 11355 | BLOCKED | False | True | surrun_03972458b7422eb6a94c3ae0 | UNDERPOWERED |
| sspec_138892cda61ac9eea9160d8f | trade_date_block_bootstrap | 11356 | BLOCKED | False | True | surrun_3184f13a71dd6b5710a1d780 | UNDERPOWERED |
| sspec_138892cda61ac9eea9160d8f | trade_date_block_bootstrap | 11357 | BLOCKED | False | True | surrun_49f3c83de1b8c84fc0fcbbaf | UNDERPOWERED |
| sspec_09ad1d10d032d170c54a3957 | trade_date_block_bootstrap | 11358 | BLOCKED | False | True | surrun_920f1fed3495c25b85c48e27 | UNDERPOWERED |
| sspec_09ad1d10d032d170c54a3957 | trade_date_block_bootstrap | 11359 | BLOCKED | False | True | surrun_aa53a614eadd0863814c2982 | UNDERPOWERED |
| sspec_09ad1d10d032d170c54a3957 | trade_date_block_bootstrap | 11360 | BLOCKED | False | True | surrun_959ba14c65d6f3a0db7fc3d3 | UNDERPOWERED |
| sspec_15a32e69c66f64d3239fe190 | trade_date_block_bootstrap | 11361 | BLOCKED | False | True | surrun_bd2cf33668257e401d3dc4cd | UNDERPOWERED |
| sspec_15a32e69c66f64d3239fe190 | trade_date_block_bootstrap | 11362 | BLOCKED | False | True | surrun_da2fcc2bd8afc60541cac30f | UNDERPOWERED |
| sspec_15a32e69c66f64d3239fe190 | trade_date_block_bootstrap | 11363 | BLOCKED | False | True | surrun_77079b9cceb499937b61322d | UNDERPOWERED |
| sspec_31bd5fb5846b2fc0b718bb0f | trade_date_block_bootstrap | 11364 | BLOCKED | False | True | surrun_9be62e8b4f47d63c22fba866 | UNDERPOWERED |
| sspec_31bd5fb5846b2fc0b718bb0f | trade_date_block_bootstrap | 11365 | BLOCKED | False | True | surrun_3ae250424420c53532e3ff43 | UNDERPOWERED |
| sspec_31bd5fb5846b2fc0b718bb0f | trade_date_block_bootstrap | 11366 | BLOCKED | False | True | surrun_66480644dca144c5cbaef0aa | UNDERPOWERED |
| sspec_ba1f201f247d5159cce6fede | trade_date_block_bootstrap | 11367 | BLOCKED | False | True | surrun_59c381173214e3b9268c5fbf | UNDERPOWERED |
| sspec_ba1f201f247d5159cce6fede | trade_date_block_bootstrap | 11368 | BLOCKED | False | True | surrun_ae7c5a5f357f700b82452dca | UNDERPOWERED |
| sspec_ba1f201f247d5159cce6fede | trade_date_block_bootstrap | 11369 | BLOCKED | False | True | surrun_057b26577701195a332df10b | UNDERPOWERED |
| sspec_26a64853e17e97b272655504 | trade_date_block_bootstrap | 11370 | BLOCKED | False | True | surrun_67d24b0e1ac4d7c1fa35fc14 | UNDERPOWERED |
| sspec_26a64853e17e97b272655504 | trade_date_block_bootstrap | 11371 | BLOCKED | False | True | surrun_c47c143ffbdbdf7d736dbbbe | UNDERPOWERED |
| sspec_26a64853e17e97b272655504 | trade_date_block_bootstrap | 11372 | BLOCKED | False | True | surrun_714ab4850e5edb7d453ee2c7 | UNDERPOWERED |
| sspec_11544caf95b6c1532aba6dc9 | trade_date_block_bootstrap | 11373 | BLOCKED | False | True | surrun_b085ff3f8bdf65be3c01be67 | UNDERPOWERED |
| sspec_11544caf95b6c1532aba6dc9 | trade_date_block_bootstrap | 11374 | BLOCKED | False | True | surrun_25451cd3fe263edd132df932 | UNDERPOWERED |
| sspec_11544caf95b6c1532aba6dc9 | trade_date_block_bootstrap | 11375 | BLOCKED | False | True | surrun_7699835364a3dab1d0e3962a | UNDERPOWERED |
| sspec_8e4e1cf3a5a60f638ead0554 | trade_date_block_bootstrap | 11376 | BLOCKED | False | True | surrun_0ed17f7f1b091db71fb3166c | UNDERPOWERED |
| sspec_8e4e1cf3a5a60f638ead0554 | trade_date_block_bootstrap | 11377 | BLOCKED | False | True | surrun_5dbd42be1b210ff9cc46a8cd | UNDERPOWERED |
| sspec_8e4e1cf3a5a60f638ead0554 | trade_date_block_bootstrap | 11378 | BLOCKED | False | True | surrun_8066e825e2a01d3cf3b09a46 | UNDERPOWERED |
| sspec_c6274ed832946f7e4c7057ba | trade_date_block_bootstrap | 11379 | BLOCKED | False | True | surrun_6ddf886b3d41df99def67c10 | UNDERPOWERED |
| sspec_c6274ed832946f7e4c7057ba | trade_date_block_bootstrap | 11380 | BLOCKED | False | True | surrun_9f120be06cff584f7745b4d5 | UNDERPOWERED |
| sspec_c6274ed832946f7e4c7057ba | trade_date_block_bootstrap | 11381 | BLOCKED | False | True | surrun_944f29887263b5d52a8ddfe3 | UNDERPOWERED |
| sspec_627f99bd374e017a1432b718 | trade_date_block_bootstrap | 11382 | BLOCKED | False | True | surrun_0bced84fa3caf82e91d40531 | UNDERPOWERED |
| sspec_627f99bd374e017a1432b718 | trade_date_block_bootstrap | 11383 | BLOCKED | False | True | surrun_900c292ca248f4bedb3266a9 | UNDERPOWERED |
| sspec_627f99bd374e017a1432b718 | trade_date_block_bootstrap | 11384 | BLOCKED | False | True | surrun_04b15aa7236156aad51349ed | UNDERPOWERED |
| sspec_e35511839516ef6c71ce543e | trade_date_block_bootstrap | 11385 | BLOCKED | False | True | surrun_47739ef722e5527da3210e55 | UNDERPOWERED |
| sspec_e35511839516ef6c71ce543e | trade_date_block_bootstrap | 11386 | BLOCKED | False | True | surrun_93a7a13dccc7bedd2df0dcfa | UNDERPOWERED |
| sspec_e35511839516ef6c71ce543e | trade_date_block_bootstrap | 11387 | BLOCKED | False | True | surrun_6c0e9252dc0cc75918502c9d | UNDERPOWERED |
| sspec_883e0cdb95b7cc71aae0e4fa | trade_date_block_bootstrap | 11388 | BLOCKED | False | True | surrun_c68e2d1558983f4f1697ed2c | UNDERPOWERED |
| sspec_883e0cdb95b7cc71aae0e4fa | trade_date_block_bootstrap | 11389 | BLOCKED | False | True | surrun_526c9ae3dcaa694440815bdd | UNDERPOWERED |
| sspec_883e0cdb95b7cc71aae0e4fa | trade_date_block_bootstrap | 11390 | BLOCKED | False | True | surrun_2b1a9ea9d99f6817253a7b79 | UNDERPOWERED |
| sspec_d269f007b8f7a869fb0ba831 | trade_date_block_bootstrap | 11391 | BLOCKED | False | True | surrun_b6ae16fef741701805422642 | UNDERPOWERED |
| sspec_d269f007b8f7a869fb0ba831 | trade_date_block_bootstrap | 11392 | BLOCKED | False | True | surrun_ea687a1c5c54f68f8f844826 | UNDERPOWERED |
| sspec_d269f007b8f7a869fb0ba831 | trade_date_block_bootstrap | 11393 | BLOCKED | False | True | surrun_33d119396f804bb0f442ccaf | UNDERPOWERED |
| sspec_52b0336f61f1a3eda7b12e06 | trade_date_block_bootstrap | 11394 | BLOCKED | False | True | surrun_71dafaca0437306e6ac4997a | UNDERPOWERED |
| sspec_52b0336f61f1a3eda7b12e06 | trade_date_block_bootstrap | 11395 | BLOCKED | False | True | surrun_04bd8105f753aa9df0b7992e | UNDERPOWERED |
| sspec_52b0336f61f1a3eda7b12e06 | trade_date_block_bootstrap | 11396 | BLOCKED | False | True | surrun_41c2c1fa9b8c07e8c7348560 | UNDERPOWERED |
| sspec_80b992bd736902213801e2de | trade_date_block_bootstrap | 11397 | BLOCKED | False | True | surrun_bacfc431cff05a536f557006 | UNDERPOWERED |
| sspec_80b992bd736902213801e2de | trade_date_block_bootstrap | 11398 | BLOCKED | False | True | surrun_fe8d6fb057918986e211c59a | UNDERPOWERED |
| sspec_80b992bd736902213801e2de | trade_date_block_bootstrap | 11399 | BLOCKED | False | True | surrun_7694bcadca1a3c6653673fc0 | UNDERPOWERED |
| sspec_363fd6e38ae46e2753764e05 | trade_date_block_bootstrap | 11400 | BLOCKED | False | True | surrun_0d0630f902818f87a36be2ce | UNDERPOWERED |
| sspec_363fd6e38ae46e2753764e05 | trade_date_block_bootstrap | 11401 | BLOCKED | False | True | surrun_81b4a438b3f53984d55f0929 | UNDERPOWERED |
| sspec_363fd6e38ae46e2753764e05 | trade_date_block_bootstrap | 11402 | BLOCKED | False | True | surrun_3b06654b8e94603450407c31 | UNDERPOWERED |
| sspec_55c049acb884c61b3e63eb2c | trade_date_block_bootstrap | 11403 | BLOCKED | False | True | surrun_afdb798d8128d832b5102763 | UNDERPOWERED |
| sspec_55c049acb884c61b3e63eb2c | trade_date_block_bootstrap | 11404 | BLOCKED | False | True | surrun_838fa79ab3c9bba604c39723 | UNDERPOWERED |
| sspec_55c049acb884c61b3e63eb2c | trade_date_block_bootstrap | 11405 | BLOCKED | False | True | surrun_d00e70851168599137145ce9 | UNDERPOWERED |
| sspec_62b071de89a66f775837d83e | trade_date_block_bootstrap | 11406 | BLOCKED | False | True | surrun_b514065efdbd4a771b8cab35 | UNDERPOWERED |
| sspec_62b071de89a66f775837d83e | trade_date_block_bootstrap | 11407 | BLOCKED | False | True | surrun_ce33d42833e4a42d9f649d1b | UNDERPOWERED |
| sspec_62b071de89a66f775837d83e | trade_date_block_bootstrap | 11408 | BLOCKED | False | True | surrun_c35eb22b2e8c07ee5cca43d5 | UNDERPOWERED |
| sspec_c766b4ae7d8b985f3e4dd022 | trade_date_block_bootstrap | 11409 | BLOCKED | False | True | surrun_b309a9e60d5693b2be28cc6c | UNDERPOWERED |
| sspec_c766b4ae7d8b985f3e4dd022 | trade_date_block_bootstrap | 11410 | BLOCKED | False | True | surrun_569af6bd4cd81f470ac112f2 | UNDERPOWERED |
| sspec_c766b4ae7d8b985f3e4dd022 | trade_date_block_bootstrap | 11411 | BLOCKED | False | True | surrun_b02d7e479bad5eabe7872a9a | UNDERPOWERED |
| sspec_f5ad0171efc937933acf3983 | trade_date_block_bootstrap | 11412 | BLOCKED | False | True | surrun_c12a6fc13296e2ddad90e3a2 | UNDERPOWERED |
| sspec_f5ad0171efc937933acf3983 | trade_date_block_bootstrap | 11413 | BLOCKED | False | True | surrun_dcd10103236065b1969c503a | UNDERPOWERED |
| sspec_f5ad0171efc937933acf3983 | trade_date_block_bootstrap | 11414 | BLOCKED | False | True | surrun_fbbd3c8b046affd58833df91 | UNDERPOWERED |
| sspec_90092d5e12acd11cd044c760 | trade_date_block_bootstrap | 11415 | BLOCKED | False | True | surrun_1974fbaf5039eeb7c3a93129 | UNDERPOWERED |
| sspec_90092d5e12acd11cd044c760 | trade_date_block_bootstrap | 11416 | BLOCKED | False | True | surrun_7990f68e87a1c331b9f55f17 | UNDERPOWERED |
| sspec_90092d5e12acd11cd044c760 | trade_date_block_bootstrap | 11417 | BLOCKED | False | True | surrun_801e12be2beddef0aa59e047 | UNDERPOWERED |
| sspec_53520c1599d90ff4aafb8fe6 | trade_date_block_bootstrap | 11418 | BLOCKED | False | True | surrun_224c7456cce5715028d31594 | UNDERPOWERED |
| sspec_53520c1599d90ff4aafb8fe6 | trade_date_block_bootstrap | 11419 | BLOCKED | False | True | surrun_b7f8cd36c23595c93c35cf56 | UNDERPOWERED |
| sspec_53520c1599d90ff4aafb8fe6 | trade_date_block_bootstrap | 11420 | BLOCKED | False | True | surrun_810e5ceeecef3c5a22aed67f | UNDERPOWERED |
| sspec_5ef23f24a1af7883f8526c08 | trade_date_block_bootstrap | 11421 | BLOCKED | False | True | surrun_b92ea1e4dacb551988ce38cd | UNDERPOWERED |
| sspec_5ef23f24a1af7883f8526c08 | trade_date_block_bootstrap | 11422 | BLOCKED | False | True | surrun_3b6a3496d00cb6030b6aeb28 | UNDERPOWERED |
| sspec_5ef23f24a1af7883f8526c08 | trade_date_block_bootstrap | 11423 | BLOCKED | False | True | surrun_3fb247dfde7adbf2b673fef6 | UNDERPOWERED |
| sspec_68bf5553d2f1ba89b39a726c | trade_date_block_bootstrap | 11424 | BLOCKED | False | True | surrun_d1c7037d9076e17923557025 | UNDERPOWERED |
| sspec_68bf5553d2f1ba89b39a726c | trade_date_block_bootstrap | 11425 | BLOCKED | False | True | surrun_d61a4d0bdc417c15fe9ef583 | UNDERPOWERED |
| sspec_68bf5553d2f1ba89b39a726c | trade_date_block_bootstrap | 11426 | BLOCKED | False | True | surrun_8c8128d5f4e39be9af5e3721 | UNDERPOWERED |
| sspec_444ef93bbd1a8a9c3bd4a684 | trade_date_block_bootstrap | 11427 | BLOCKED | False | True | surrun_beb1dbe8ebc0cb07649de565 | UNDERPOWERED |
| sspec_444ef93bbd1a8a9c3bd4a684 | trade_date_block_bootstrap | 11428 | BLOCKED | False | True | surrun_32c2f06e4459103d133a1296 | UNDERPOWERED |
| sspec_444ef93bbd1a8a9c3bd4a684 | trade_date_block_bootstrap | 11429 | BLOCKED | False | True | surrun_c2699fbe9fcccbe5c6836070 | UNDERPOWERED |
| sspec_3284e561e225c9e203fc58dd | trade_date_block_bootstrap | 11430 | BLOCKED | False | True | surrun_3d2e5171c3726365827a6a28 | UNDERPOWERED |
| sspec_3284e561e225c9e203fc58dd | trade_date_block_bootstrap | 11431 | BLOCKED | False | True | surrun_48fe0a60bc20b4d8a4cc1e49 | UNDERPOWERED |
| sspec_3284e561e225c9e203fc58dd | trade_date_block_bootstrap | 11432 | BLOCKED | False | True | surrun_1bcaedfeac5b8b35e56d9261 | UNDERPOWERED |
| sspec_4468e6432d92e8db6c27cd6b | trade_date_block_bootstrap | 11433 | BLOCKED | False | True | surrun_fbf621b3faae5e174fe7a270 | UNDERPOWERED |
| sspec_4468e6432d92e8db6c27cd6b | trade_date_block_bootstrap | 11434 | BLOCKED | False | True | surrun_616cda3a6688dbf0d3eedfef | UNDERPOWERED |
| sspec_4468e6432d92e8db6c27cd6b | trade_date_block_bootstrap | 11435 | BLOCKED | False | True | surrun_5e76dde33c2a36ecf55d9f44 | UNDERPOWERED |
| sspec_9037ec5a2706bd265ab7c0f6 | trade_date_block_bootstrap | 11436 | BLOCKED | False | True | surrun_33281fc97ca2f711248c3470 | UNDERPOWERED |
| sspec_9037ec5a2706bd265ab7c0f6 | trade_date_block_bootstrap | 11437 | BLOCKED | False | True | surrun_2038cec4b1ad5e1018a743ae | UNDERPOWERED |
| sspec_9037ec5a2706bd265ab7c0f6 | trade_date_block_bootstrap | 11438 | BLOCKED | False | True | surrun_fba39accff5b31a3ec14faf5 | UNDERPOWERED |
| sspec_164fc38457af9855db79f079 | trade_date_block_bootstrap | 11439 | BLOCKED | False | True | surrun_6b803164fb70c1a906904464 | UNDERPOWERED |
| sspec_164fc38457af9855db79f079 | trade_date_block_bootstrap | 11440 | BLOCKED | False | True | surrun_bb9f47d50aa340cfe628eba7 | UNDERPOWERED |
| sspec_164fc38457af9855db79f079 | trade_date_block_bootstrap | 11441 | BLOCKED | False | True | surrun_c9072c464bdd498012f4413f | UNDERPOWERED |
| sspec_b10990ebba5a3326dade5cb9 | trade_date_block_bootstrap | 11442 | BLOCKED | False | True | surrun_d09547fc150cd923809ba40a | UNDERPOWERED |
| sspec_b10990ebba5a3326dade5cb9 | trade_date_block_bootstrap | 11443 | BLOCKED | False | True | surrun_8ef7549315f3c6bcb91df26d | UNDERPOWERED |
| sspec_b10990ebba5a3326dade5cb9 | trade_date_block_bootstrap | 11444 | BLOCKED | False | True | surrun_21944d3ef8bf9d37da2c1aca | UNDERPOWERED |
| sspec_e19d3c23f01ddd6e83fded22 | trade_date_block_bootstrap | 11445 | BLOCKED | False | True | surrun_13e32b10bff04f4b4a862562 | UNDERPOWERED |
| sspec_e19d3c23f01ddd6e83fded22 | trade_date_block_bootstrap | 11446 | BLOCKED | False | True | surrun_09bf4c28702e51e1c80a891d | UNDERPOWERED |
| sspec_e19d3c23f01ddd6e83fded22 | trade_date_block_bootstrap | 11447 | BLOCKED | False | True | surrun_ecaf275ce9f363f982881673 | UNDERPOWERED |
| sspec_de3e699a403c2177c40d9cc8 | trade_date_block_bootstrap | 11448 | BLOCKED | False | True | surrun_f7b9e27f4f88068e9a7c1533 | UNDERPOWERED |
| sspec_de3e699a403c2177c40d9cc8 | trade_date_block_bootstrap | 11449 | BLOCKED | False | True | surrun_f2965b10b18bffc032dee2d0 | UNDERPOWERED |
| sspec_de3e699a403c2177c40d9cc8 | trade_date_block_bootstrap | 11450 | BLOCKED | False | True | surrun_956e71bb964ffb10b7369023 | UNDERPOWERED |
| sspec_5621afc74ef50911ec282e47 | trade_date_block_bootstrap | 11451 | BLOCKED | False | True | surrun_157bf3a9b89d4f4c2ea44b46 | UNDERPOWERED |
| sspec_5621afc74ef50911ec282e47 | trade_date_block_bootstrap | 11452 | BLOCKED | False | True | surrun_407d45b9a56a7b7ec84ee74c | UNDERPOWERED |
| sspec_5621afc74ef50911ec282e47 | trade_date_block_bootstrap | 11453 | BLOCKED | False | True | surrun_4079cefc1b5525921f5990bd | UNDERPOWERED |
| sspec_1902c7977a0f0121448b112e | trade_date_block_bootstrap | 11454 | BLOCKED | False | True | surrun_4d182f47afe6f6c851116a33 | UNDERPOWERED |
| sspec_1902c7977a0f0121448b112e | trade_date_block_bootstrap | 11455 | BLOCKED | False | True | surrun_de91a1d100804ec6d967b029 | UNDERPOWERED |
| sspec_1902c7977a0f0121448b112e | trade_date_block_bootstrap | 11456 | BLOCKED | False | True | surrun_ce83524b2691c17d3f488d33 | UNDERPOWERED |
| sspec_4bb2ca612fdf7ee2e712d648 | trade_date_block_bootstrap | 11457 | BLOCKED | False | True | surrun_52f9225ad75cbc8ece8f544d | UNDERPOWERED |
| sspec_4bb2ca612fdf7ee2e712d648 | trade_date_block_bootstrap | 11458 | BLOCKED | False | True | surrun_b1efdf0adad9ca8873049054 | UNDERPOWERED |
| sspec_4bb2ca612fdf7ee2e712d648 | trade_date_block_bootstrap | 11459 | BLOCKED | False | True | surrun_4345dddc1b9e9db37c6f65b8 | UNDERPOWERED |
| sspec_123591b05b9a912fe8970cfb | trade_date_block_bootstrap | 11460 | BLOCKED | False | True | surrun_ef0fcb6c065ebce6adfcb835 | UNDERPOWERED |
| sspec_123591b05b9a912fe8970cfb | trade_date_block_bootstrap | 11461 | BLOCKED | False | True | surrun_afe1561e024c1dc8dade2924 | UNDERPOWERED |
| sspec_123591b05b9a912fe8970cfb | trade_date_block_bootstrap | 11462 | BLOCKED | False | True | surrun_9a62f4f0d2939bf3adc45b05 | UNDERPOWERED |
| sspec_8fdef93acef82e49081fcb1f | trade_date_block_bootstrap | 11463 | BLOCKED | False | True | surrun_dc6c3974dc12c096ef574808 | UNDERPOWERED |
| sspec_8fdef93acef82e49081fcb1f | trade_date_block_bootstrap | 11464 | BLOCKED | False | True | surrun_f6d873a59ae85d5ae47d093f | UNDERPOWERED |
| sspec_8fdef93acef82e49081fcb1f | trade_date_block_bootstrap | 11465 | BLOCKED | False | True | surrun_87abfd0498de2d6cd3294066 | UNDERPOWERED |
| sspec_429edfce8d1bb00a65230c60 | trade_date_block_bootstrap | 11466 | BLOCKED | False | True | surrun_dae41ec57655654fed4f4a9e | UNDERPOWERED |
| sspec_429edfce8d1bb00a65230c60 | trade_date_block_bootstrap | 11467 | BLOCKED | False | True | surrun_1b75b2e55c9f30a9a6d39fe2 | UNDERPOWERED |
| sspec_429edfce8d1bb00a65230c60 | trade_date_block_bootstrap | 11468 | BLOCKED | False | True | surrun_ea8f0f144838706382cd20ec | UNDERPOWERED |
| sspec_8545f86193efb04e1f5b5b0a | trade_date_block_bootstrap | 11469 | BLOCKED | False | True | surrun_81292d77b614438aaef95c0a | UNDERPOWERED |
| sspec_8545f86193efb04e1f5b5b0a | trade_date_block_bootstrap | 11470 | BLOCKED | False | True | surrun_54667fd552d6bfd95b9486e5 | UNDERPOWERED |
| sspec_8545f86193efb04e1f5b5b0a | trade_date_block_bootstrap | 11471 | BLOCKED | False | True | surrun_a3db1f8ae46f9c19027b5f34 | UNDERPOWERED |
| sspec_5c5fb27f9b4b3670ce46c331 | trade_date_block_bootstrap | 11472 | BLOCKED | False | True | surrun_da10364ec12a65a564828ecd | UNDERPOWERED |
| sspec_5c5fb27f9b4b3670ce46c331 | trade_date_block_bootstrap | 11473 | BLOCKED | False | True | surrun_848e04cbc3631bc10e948f9f | UNDERPOWERED |
| sspec_5c5fb27f9b4b3670ce46c331 | trade_date_block_bootstrap | 11474 | BLOCKED | False | True | surrun_7c68d21e549dfd5fa450b933 | UNDERPOWERED |
| sspec_3ef04e631e7b0b4d493441aa | trade_date_block_bootstrap | 11475 | BLOCKED | False | True | surrun_2630fbf274364c51a0f1fb68 | UNDERPOWERED |
| sspec_3ef04e631e7b0b4d493441aa | trade_date_block_bootstrap | 11476 | BLOCKED | False | True | surrun_6791ab157af0f83ca9d83f01 | UNDERPOWERED |
| sspec_3ef04e631e7b0b4d493441aa | trade_date_block_bootstrap | 11477 | BLOCKED | False | True | surrun_61f9ad31244351cc5d038bd1 | UNDERPOWERED |
| sspec_2b4b71e12ac5786625d178c6 | trade_date_block_bootstrap | 11478 | BLOCKED | False | True | surrun_3dccef8131db065d463e1e95 | UNDERPOWERED |
| sspec_2b4b71e12ac5786625d178c6 | trade_date_block_bootstrap | 11479 | BLOCKED | False | True | surrun_d5f4c01e91854b9158fb8bd2 | UNDERPOWERED |
| sspec_2b4b71e12ac5786625d178c6 | trade_date_block_bootstrap | 11480 | BLOCKED | False | True | surrun_a8fd594037136f91bf339ebd | UNDERPOWERED |
| sspec_9a7cf74fc9908ec06106675b | trade_date_block_bootstrap | 11481 | BLOCKED | False | True | surrun_dcd0c03d55b4508736edbc7b | UNDERPOWERED |
| sspec_9a7cf74fc9908ec06106675b | trade_date_block_bootstrap | 11482 | BLOCKED | False | True | surrun_30923bb43f07db16f7833057 | UNDERPOWERED |
| sspec_9a7cf74fc9908ec06106675b | trade_date_block_bootstrap | 11483 | BLOCKED | False | True | surrun_1c71b7b15bc9de2b1b8820c3 | UNDERPOWERED |
| sspec_bbcb2109b27996474c1f91e3 | trade_date_block_bootstrap | 11484 | BLOCKED | False | True | surrun_bb50c51ba6b75ef5e47481f8 | UNDERPOWERED |
| sspec_bbcb2109b27996474c1f91e3 | trade_date_block_bootstrap | 11485 | BLOCKED | False | True | surrun_505e2ab3950292d526dbe1e3 | UNDERPOWERED |
| sspec_bbcb2109b27996474c1f91e3 | trade_date_block_bootstrap | 11486 | BLOCKED | False | True | surrun_9ff917be272985aab530533b | UNDERPOWERED |
| sspec_c985c172eecc2c0f6d2db98b | trade_date_block_bootstrap | 11487 | BLOCKED | False | True | surrun_0e45c2457a76dcab3cde5a03 | UNDERPOWERED |
| sspec_c985c172eecc2c0f6d2db98b | trade_date_block_bootstrap | 11488 | BLOCKED | False | True | surrun_56998257e18117846749a364 | UNDERPOWERED |
| sspec_c985c172eecc2c0f6d2db98b | trade_date_block_bootstrap | 11489 | BLOCKED | False | True | surrun_36704225effe9e811b33807e | UNDERPOWERED |
| sspec_3e363698c3a9734e4dc152e6 | trade_date_block_bootstrap | 11490 | BLOCKED | False | True | surrun_0fd000a63faf3c8365a0f2de | UNDERPOWERED |
| sspec_3e363698c3a9734e4dc152e6 | trade_date_block_bootstrap | 11491 | BLOCKED | False | True | surrun_b1e699669be00e83e502b43c | UNDERPOWERED |
| sspec_3e363698c3a9734e4dc152e6 | trade_date_block_bootstrap | 11492 | BLOCKED | False | True | surrun_882b46ae3ea03c3338044f50 | UNDERPOWERED |
| sspec_11b260927df9d314f8f0b48c | trade_date_block_bootstrap | 11493 | BLOCKED | False | True | surrun_3c9f36c54532df95f420d538 | UNDERPOWERED |
| sspec_11b260927df9d314f8f0b48c | trade_date_block_bootstrap | 11494 | BLOCKED | False | True | surrun_623f99ddc7e72757f73a850c | UNDERPOWERED |
| sspec_11b260927df9d314f8f0b48c | trade_date_block_bootstrap | 11495 | BLOCKED | False | True | surrun_0abbeb008af6797afd818e02 | UNDERPOWERED |

## Machinery Inventory

- `SurrogateStudyRun` schema and deterministic serialization live in `src/alpha_system/governance/surrogate_run.py`.
- `surrogate_flag` is threaded through `TrialLedgerRecord`; true surrogate trials are excluded from production variant/family counts.
- `alpha governance surrogate-calibrate` runs seeded surrogate calibrations in caller-supplied isolated namespaces.
- Real-data calibration over the kill-shot StudySpec remains a coordinator runbook step before FUTSUB-P28 kill-shot resume.
